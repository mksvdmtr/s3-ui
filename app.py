from flask import Flask, render_template, redirect, request, session, url_for
import boto3
from botocore.exceptions import NoCredentialsError
from botocore.config import Config
import os, sys
from loguru import logger
from auth import ldap_authenticate

app = Flask(__name__)

try:
    app.secret_key = os.environ['APP_SECRET_KEY']
    bucket_name = os.environ['YC_BUCKET_NAME']
    access_key_id = os.environ['YC_ACCESS_KEY']
    secret_access_key = os.environ['YC_SECRET_ACCESS_KEY']
    url_expires = os.environ['URL_EXPIRES']
    key_prefixes = os.environ['KEY_PREFIXES']
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
    all_objects = []
    if 'projects' in session:
        try:
            for project in session['projects']:
                for key_prefix in key_prefixes.split(','):
                    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=f'{key_prefix}/{project}')
                    objects = response.get('Contents', [])
                    all_objects.extend(objects)

            filtered_objects = [obj for obj in all_objects if obj['Size'] > 0]
            return render_template('objects.html', filtered_objects=filtered_objects, bucket_name=bucket_name)
        except NoCredentialsError:
            return 'You are not logged in. <a href="/login">Login</a>'
    return 'You are not logged in. <a href="/login">Login</a>'

@app.route('/login', methods=['GET', 'POST'])

def login():
    message=''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        projects = ldap_authenticate(username, password)
    
        if projects:
            session['projects'] = projects
            message='Success'
            return redirect(url_for('list_objects'))
        else:
            message='Invalid credentials'

    return render_template('login.html', message=message)

@app.route('/logout')
def logout():
    session.pop('projects', None)
    return redirect(url_for('login'))

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
