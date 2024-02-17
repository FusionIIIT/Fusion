
from django.conf.urls import url
from django.urls import path, include
from . import views
from django.contrib import admin

app_name = 'examination'

urlpatterns = [
    url(r'^api/', include('applications.examination.api.urls')),
    url(r'^$', views.exam, name='exam'),
    url(r'submit/', views.submit, name='submit'),
    url(r'verify/', views.verify, name='verify'),
    url(r'publish/', views.publish, name='publish'),
    url(r'notReady_publish/', views.notReady_publish, name='notReady_publish'),
    url(r'announcement/', views.announcement, name='announcement'),
    url(r'timetable/', views.timetable, name='timetable'),

]
