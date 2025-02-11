from flask import Flask, render_template_string, redirect, request
import boto3
from botocore.exceptions import NoCredentialsError
from botocore.config import Config
import os, sys
from loguru import logger


app = Flask(__name__)

try:
    bucket_name = os.environ['YC_BUCKET_NAME']
    access_key_id = os.environ['YC_ACCESS_KEY']
    secret_access_key = os.environ['YC_SECRET_ACCESS_KEY']
    url_expires = os.environ['URL_EXPIRES']
except KeyError as e:
    logger.error("env not set: {}", e)
    sys.exit(1)

s3_client = boto3.client(
    's3',
    endpoint_url='https://storage.yandexcloud.net',
    aws_access_key_id=access_key_id,
    aws_secret_access_key=secret_access_key,
    config=Config(signature_version='s3v4')
)

@app.route('/')
def list_objects():
    try:
        prefix = request.args.get('prefix', '')
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        objects = response.get('Contents', [])
        filtered_objects = [obj for obj in objects if obj['Size'] > 0]

        html_content = '''
        <!doctype html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title></title>
        </head>
        <body>
            <h2>{{ bucket_name }}</h2>
            <ul>
                {% for obj in filtered_objects %}
                    <li>
                        <a href="/download?key={{ obj['Key'] }}">{{ obj['Key'] }}</a>
                    </li>
                {% endfor %}
            </ul>
        </body>
        </html>
        '''

        return render_template_string(html_content, filtered_objects=filtered_objects, bucket_name=bucket_name)
    except NoCredentialsError:
        return "Error: Invalid credentials", 403

@app.route('/download')
def download_object():
    key = request.args.get('key')
    if not key:
        return "Error: key parameter missing", 400

    try:
        url = s3_client.generate_presigned_url('get_object',
                                                Params={'Bucket': bucket_name, 'Key': key},
                                                ExpiresIn=url_expires)
        return redirect(url)
    except Exception as e:
        return f"Error generating temporary URL: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)
