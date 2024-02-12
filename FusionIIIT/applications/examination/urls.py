
from django.conf.urls import url
from django.urls import path, include
from . import views
from django.contrib import admin

app_name = 'examination'

urlpatterns = [
    path('',views.exam,name='exam'),
    path('submit/',views.submit,name='submit'),
    path('verify/',views.verify,name='verify'),
    path('publish/',views.publish,name='publish'),
    path('notReady_publish/',views.notReady_publish,name='notReady_publish'),
 
]
