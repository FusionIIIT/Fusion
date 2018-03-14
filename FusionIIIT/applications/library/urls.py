from django.conf.urls import url

from . import views

app_name = 'library'

urlpatterns = [

    url(r'^library/', views.libraryModule, name='libraryModule'),

]
