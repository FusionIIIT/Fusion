import os
from Fusion.settings.common import *
from datetime import timedelta
import warnings

DEBUG = True

# WARNING: Use strong secret key in production. Generate with: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
if not os.environ.get('SECRET_KEY'):
    warnings.warn('SECRET_KEY not set in environment. Using development key. NEVER use in production!')
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-only-for-development-change-in-production')

# Development: Allow localhost only. Set ALLOWED_HOSTS in production via environment
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'fusionlab'),
        'USER': os.environ.get('DB_USER', 'fusion_admin'),
        'PASSWORD': os.environ.get('DB_PASSWORD', os.environ.get('POSTGRES_PASSWORD', 'postgres_default')),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

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
