from Fusion.settings.common import *

DEBUG = True

SECRET_KEY = '=&w9due426k@l^ju1=s1)fj1rnpf0ok8xvjwx+62_nc-f12-8('

ALLOWED_HOSTS = []

DATABASES = {
     'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'fusionlab',
        'HOST': 'localhost',
        'USER': 'postgres',
        'PASSWORD': 'Postgre@123',
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
        'django_extensions',
        )

    
    ###############################
    # DJANGO_EXTENSIONS SETTINGS: #
    ###############################
    INTERNAL_IPS = [
        '127.0.0.1',
    ]

    ###############################
    # DJANGO_EXTENSIONS SETTINGS: #
    ###############################
    SHELL_PLUS = "ipython"

    SHELL_PLUS_PRINT_SQL = True

    DEBUG_TOOLBAR_CONFIG = {
        'INTERCEPT_REDIRECTS': False,
    }
