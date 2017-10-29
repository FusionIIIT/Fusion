from django.conf.urls import url

from . import views

app_name = 'phc'

urlpatterns = [

    url(r'^', views.phc, name='phc'),

]
