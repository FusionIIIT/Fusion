from django.conf.urls import url

from . import views

app_name = 'healthcenter'

urlpatterns = [

    url(r'^', views.healthcenter, name='healthcenter'),

]
