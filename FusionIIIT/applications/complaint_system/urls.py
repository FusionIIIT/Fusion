from django.conf.urls import url, include
from . import views


app_name = 'complaint'

urlpatterns = [

    url(r'^', views.complaint, name='complaint'),

]