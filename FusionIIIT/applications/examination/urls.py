
from django.conf.urls import url
from django.urls import path, include
from . import views
from django.contrib import admin



urlpatterns = [
    url(r'^api/', include('applications.examination.api.urls'))
]
