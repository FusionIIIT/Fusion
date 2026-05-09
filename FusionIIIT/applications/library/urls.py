from django.urls import re_path as url

from . import views

app_name = 'library'

urlpatterns = [

    url(r'^library/$', views.libraryModule, name='libraryModule'),

]
