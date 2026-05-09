from .development import *

# The filetracking app is mid-migration; disabling DB serialization avoids
# setup-time crashes while focused API/security tests run.
DATABASES['default'].setdefault('TEST', {})
DATABASES['default']['TEST']['SERIALIZE'] = False

DEBUG = True
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
