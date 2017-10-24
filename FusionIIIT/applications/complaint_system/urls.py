from django.conf.urls import url

from . import views

app_name = 'complaint'

urlpatterns = [

    url(r'^', views.complaint, name='complaint'),

]
