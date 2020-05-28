"""
WSGI config for Fusion project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
#from dj_static import Cling

# os.environ["DJANGO_SETTINGS_MODULE"] = "Fusion.settings"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Fusion.settings")

# application = Cling(get_wsgi_application())
application = get_wsgi_application()
