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
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1,*').split(',')

# Use SQLite for local development to avoid PostgreSQL setup
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
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

#############################################
# DJANGO DEBUG TOOLBAR :
#############################################
DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.history.HistoryPanel',
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
]

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
