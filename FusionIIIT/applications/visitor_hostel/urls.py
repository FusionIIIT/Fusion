from django.conf.urls import url

from . import views

app_name = 'visitorhostel'

urlpatterns = [

    url(r'^', views.visitorhostel, name='visitorhostel'),

]
