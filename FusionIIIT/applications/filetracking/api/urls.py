#from django.conf.urls import url
from django.urls import re_path as url
from . import views
from .views import MyOwnView


app_name = 'filetracking'

urlpatterns = [
    

    url('composefile/', views.filetracking, name = 'compose_file'),
    url('drafts/', views.fileview, name = 'draft'),
    
]