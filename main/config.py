import os, base64

SECRET_KEY = 'yekterces'
SQLALCHEMY_DATABASE_URI = 'mysql://root:shadow@localhost:3306/mfauth'
SQLALCHEMY_TRACK_MODIFICATIONS = False

MAIL_SERVER = 'smtp.mail.me.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USE_SSL = False
MAIL_USERNAME = 'temp'#base64.b64decode(os.environ.get('MAIL_USERNAME'))
MAIL_PASSWORD = 'temp'#base64.b64decode(os.environ.get('MAIL_PASSWORD'))

ADMINS = [MAIL_USERNAME]
