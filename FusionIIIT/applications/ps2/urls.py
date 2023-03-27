from django.conf.urls import url

from . import views

app_name = 'ps2'

urlpatterns = [
    url(r'^$', views.ps2, name='ps2'),
    url(r'^addstock/$', views.addstock, name='addstock')
]