from django.conf.urls import url, include
from . import views


app_name = 'mess'

urlpatterns = [

    url(r'^', views.mess, name='mess'),

]