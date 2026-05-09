"""
Minimal URL configuration for Django tests
"""
from django.conf.urls import include, url

# Keep the globals namespace available so shared error pages and redirects can
# resolve reverse() calls during test execution.
urlpatterns = [
	url(r'^', include('applications.globals.urls')),
]
