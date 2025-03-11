from flask import Flask, render_template, redirect, request, session, url_for
import boto3
from botocore.exceptions import NoCredentialsError
from botocore.config import Config
import os, sys
from loguru import logger
from flask_session import Session
from flask_oidc import OpenIDConnect
from redis_sentinel import get_redis_client

app = Flask(__name__)

try:
    app.secret_key = os.environ['APP_SECRET_KEY']
    YC_BUCKET_NAME = os.environ['YC_BUCKET_NAME']
    YC_ACCESS_KEY = os.environ['YC_ACCESS_KEY']
    YC_SECRET_ACCESS_KEY = os.environ['YC_SECRET_ACCESS_KEY']
    URL_EXPIRES = os.environ['URL_EXPIRES']
    KEY_PREFIXES = os.environ['KEY_PREFIXES']
    OIDC_CLIENT_ID = os.environ['OIDC_CLIENT_ID']
    OIDC_CLIENT_SECRET = os.environ['OIDC_CLIENT_SECRET']
    OIDC_AUTH_URI = os.environ['OIDC_AUTH_URI']
    OIDC_TOKEN_URI = os.environ['OIDC_TOKEN_URI']
    OIDC_REDIRECT_URIS = os.environ['OIDC_REDIRECT_URIS']
    OIDC_END_SESSION_ENDPOINT = os.environ['OIDC_END_SESSION_ENDPOINT']
    OIDC_ISSUER = os.environ['OIDC_ISSUER']
    OIDC_SCOPE = os.environ['OIDC_SCOPE']
except KeyError as e:
    logger.error("env not set: {}", e)
    sys.exit(1)

oidc_redirect_uris = OIDC_REDIRECT_URIS.split(',') if OIDC_REDIRECT_URIS else []
oidc_redirect_uris = [x.strip() for x in oidc_redirect_uris]

oidc_client_secrets_json = {
    "web": {
        "client_id": OIDC_CLIENT_ID,
        "client_secret": OIDC_CLIENT_SECRET,
        "auth_uri": OIDC_AUTH_URI,
        "token_uri": OIDC_TOKEN_URI,
        "redirect_uris": oidc_redirect_uris,
        "issuer": OIDC_ISSUER,
        "end_session_endpoint": OIDC_END_SESSION_ENDPOINT,
        "scope": OIDC_SCOPE
    }
}

app.config.update({
    'OIDC_CLIENT_SECRETS': oidc_client_secrets_json,
    'OIDC_ID_TOKEN_COOKIE_SECURE': True,
    'OIDC_USER_INFO_ENABLED': False,
    'SESSION_TYPE': 'redis',
    'SESSION_REDIS': get_redis_client()
})

server_session = Session(app)
oidc = OpenIDConnect(app)

s3_client = boto3.client(
    's3',
    endpoint_url='https://storage.yandexcloud.net',
    aws_access_key_id=YC_ACCESS_KEY,
    aws_secret_access_key=YC_SECRET_ACCESS_KEY,
    config=Config(signature_version='s3v4')
)

@app.route('/')
def list_objects():
    projects = []
    if oidc.user_loggedin:
        if session['oidc_auth_token']['userinfo']['group']:
            groups=session['oidc_auth_token']['userinfo']['group']
            prefix = 'g_s3_ui_'
            suffix = f'_ro'
            projects = [item.removeprefix(prefix).removesuffix(suffix) for item in groups]
            all_objects = []
            print(groups)
            print(projects)
            if projects:
                for project in projects:
                    for key_prefix in KEY_PREFIXES.split(','):
                        response = s3_client.list_objects_v2(Bucket=YC_BUCKET_NAME, Prefix=f'{key_prefix}/{project}')
                        objects = response.get('Contents', [])
                        all_objects.extend(objects)
                filtered_objects = [obj for obj in all_objects if obj['Size'] > 0]
                return render_template('objects.html', filtered_objects=filtered_objects, bucket_name=YC_BUCKET_NAME)
    else:
        return render_template('login.html')

@app.route('/login')
def login():
    return oidc.redirect_to_auth_server()

@app.route('/logout')
def logout():
    oidc.logout()
    session.clear()
    return redirect(url_for('list_objects'))

@app.route('/download')
def download_object():
    key = request.args.get('key')
    if not key:
        logger.error("Key parameter missing")
        return "Error: key parameter missing", 400
    try:
        url = s3_client.generate_presigned_url('get_object',
                                                Params={'Bucket': YC_BUCKET_NAME, 'Key': key},
                                                ExpiresIn=URL_EXPIRES)
        return redirect(url)
    except Exception as e:
        logger.error(f"Error generating temporary URL: {str(e)}")
        return f"Error generating temporary URL: {str(e)}", 500

if __name__ == '__main__':
    app.run()
