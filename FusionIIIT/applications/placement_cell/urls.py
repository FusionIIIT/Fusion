from django.conf.urls import url

from . import views

# app_name = 'placement'

urlpatterns = [

    url(r'^$', views.placement, name='placement'),
    url(r'^cv/(?P<username>[a-zA-Z0-9\.]{1,20})/$', views.cv, name="cv"),

]
