from django.conf.urls import url, include
from . import views


app_name = 'visitorhostel'

urlpatterns = [

    url(r'^', views.visitorhostel, name='visitorhostel'),

]