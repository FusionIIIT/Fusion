from django.conf.urls import url

from . import views

app_name = 'spacs'

urlpatterns = [

    url(r'^', views.spacs, name='spacs'),

]
