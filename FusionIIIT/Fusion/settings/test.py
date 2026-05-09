"""
Minimal test settings for running Fusion Dashboard tests
Uses PostgreSQL database (already connected in development)
"""
import os
from pathlib import Path
from Fusion.settings.common import *

# PostgreSQL test database - uses separate test database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'fusionlab_test_suite',
        'HOST': os.environ.get("DB_HOST", default='localhost'),
        'PORT': os.environ.get("DB_PORT", default='5433'),
        'USER': 'fusion_admin',
        'PASSWORD': 'hello123',
        'TEST': {
            'NAME': 'fusionlab_test_suite',
            'CHARSET': 'UTF8',
            'CREATE_DB': True,
        },
    }
}

# Keep standard migrations for PostgreSQL (not needed for in-memory DB)
# Tests will run migrations as part of setup

# Test security settings
SECRET_KEY = 'test-secret-key-for-testing-only-24-apr-2026'
DEBUG = True
ALLOWED_HOSTS = ['*', 'localhost', '127.0.0.1']

# Keep middleware but avoid test-only imports that are unavailable in this
# environment.
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Authentication backends for testing
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Allauth settings (required)
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_USERNAME_REQUIRED = False

# Celery disabled for testing
CELERY_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True

# Disable email sending in tests
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Use minimal URL configuration to avoid importing problematic modules
ROOT_URLCONF = 'Fusion.test_urls'

# Avoid WhiteNoise manifest lookup during tests; many views resolve static URLs
# while rendering error pages or shared templates.
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

print("Using minimal test settings (notifications app excluded)")
