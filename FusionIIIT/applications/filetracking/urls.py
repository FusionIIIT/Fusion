from django.conf.urls import url, include

from .api import urls

app_name = 'filetracking'

# filetracking's own pages were replaced by the React app; only its API is served.
urlpatterns = [
    url(r'^api/', include(urls)),
]
