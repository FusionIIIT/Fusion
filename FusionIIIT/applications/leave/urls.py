from django.conf.urls import url

from . import views

app_name = 'leave'

urlpatterns = [

    url(r'^', views.leave, name='leave'),

]
