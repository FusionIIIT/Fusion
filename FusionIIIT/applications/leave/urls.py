from django.conf.urls import url, include
from . import views


app_name = 'leave'

urlpatterns = [

    url(r'^', views.leave, name='leave'),

]