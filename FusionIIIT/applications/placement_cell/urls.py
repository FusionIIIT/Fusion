from django.conf.urls import url

from . import views

app_name = 'placement'

urlpatterns = [

    url(r'^', views.placement, name='placement'),

]
