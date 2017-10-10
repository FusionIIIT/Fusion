from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    url(r'addCourse/', views.add_course, name='addCourse'),
    url(r'^dropCourse/', views.drop_course, name='dropCourse'),
]
