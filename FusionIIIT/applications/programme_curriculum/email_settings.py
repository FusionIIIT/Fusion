# Email Configuration for Password Management
# Add these settings to your Django settings.py file

# Email Backend Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# SMTP Configuration (Update with your actual email server details)
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 465
EMAIL_USE_SSL = True  # Use SSL for port 465
EMAIL_USE_TLS = False  # Don't use TLS when using SSL

# Email Authentication (Use environment variables for security)
EMAIL_HOST_USER = 'vikrantkrd@gmail.com'  # Change to your email
EMAIL_HOST_PASSWORD = ''    # Use app password for Gmail

# Default From Email
DEFAULT_FROM_EMAIL = 'FUSION Portal <fusion@iiitdmj.ac.in>'
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Email timeout settings
EMAIL_TIMEOUT = 30

# Custom settings for FUSION Portal
FUSION_PORTAL_URL = 'http://fusion.iiitdmj.ac.in/'
ACADEMIC_OFFICE_EMAIL = 'academic@iiitdmj.ac.in'

# Security settings for email
EMAIL_RATE_LIMIT = 700  # emails per hour per user
EMAIL_BULK_LIMIT = 700  # bulk emails per operation

# For development, you can use console backend to see emails in terminal
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# For testing, you can use file backend to save emails to files
# EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
# EMAIL_FILE_PATH = '/tmp/app-messages'  # change this to a proper location

# Environment Variables Setup Instructions:
"""
For production, set these environment variables instead of hardcoding:

export EMAIL_HOST_USER="academic@iiitdmj.ac.in"
export EMAIL_HOST_PASSWORD="your_secure_app_password"
export FUSION_PORTAL_URL="https://fusion.iiitdmj.ac.in"

Then in settings.py use:

import os
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'academic@iiitdmj.ac.in')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
FUSION_PORTAL_URL = os.environ.get('FUSION_PORTAL_URL', 'https://fusion.iiitdmj.ac.in')
"""

# Gmail App Password Instructions:
"""
To get Gmail App Password:
1. Enable 2-Factor Authentication on your Gmail account
2. Go to Google Account settings → Security
3. Under "Signing in to Google", select "App passwords"
4. Generate a new app password for "Mail"
5. Use this 16-character password in EMAIL_HOST_PASSWORD
"""

# Email Template Default Values
EMAIL_TEMPLATE_DEFAULTS = {
    'INITIAL_PASSWORD': {
        'subject': 'FUSION Portal - Login Credentials - {{roll_number}}',
        'sender_name': 'Academic Office',
        'institute_name': 'IIITDM Jabalpur',
        'portal_name': 'FUSION Portal'
    }
}

# Logging configuration for email debugging
import logging

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'email_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/email.log',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'password_email': {
            'handlers': ['email_file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
