from django.conf.urls import url, include
from . import views


app_name = 'susil'

urlpatterns = [

    url(r'^$', views.index, name='index'),

    url(r'^login/', views.login, name='login'),

    url(r'^dashboard/', views.dashboard, name='dashboard'),

    url(r'^accounts/', include('allauth.urls')),
]