from Fusion.settings.common import *

DEBUG = True

SECRET_KEY = '=&w9due426k@l^ju1=s1)fj1rnpf0ok8xvjwx+62_nc-f12-8('

ALLOWED_HOSTS = []

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'fusionlab',
        # 'HOST': '172.27.16.216',
        # 'USER': 'fusion_admin',
        # 'PASSWORD': 'hello123',
        'HOST': 'localhost',
        'USER': 'Fusion',
        'PASSWORD': '123456',
    }
}

#DATABASES = {
 #   'default': {
 #        'ENGINE': 'django.db.backends.sqlite3',
 #       'NAME': os.path.join(BASE_DIR, 'fusion.db'),
 #   }
#}

if DEBUG:
    MIDDLEWARE += (
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    )
    INSTALLED_APPS += (
        'debug_toolbar',
        )
    INTERNAL_IPS = ('127.0.0.1',)
    DEBUG_TOOLBAR_CONFIG = {
        'INTERCEPT_REDIRECTS': False,
    }