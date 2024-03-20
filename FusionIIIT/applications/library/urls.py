from django.conf.urls import url
from django.urls import path, include

from . import views

app_name = 'library'

urlpatterns = [
    url(r'^library/$', views.libraryModule, name='libraryModule'),
    url(r'^api/', include('applications.library.api.urls')),
]
