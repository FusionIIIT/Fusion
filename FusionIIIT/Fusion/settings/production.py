from Fusion.settings.common import *

DEBUG = True

SECRET_KEY = os.environ['SECRET_KEY']

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '172.27.16.216']

# password of sender
EMAIL_HOST_PASSWORD = os.environ['MAIL_PASSWORD']

# Database template for postgres

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'fusion',
        'HOST': 'localhost',
        'USER': 'admin',
        'PASSWORD': os.environ['DBPASS'],
    }
}