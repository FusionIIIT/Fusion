from django.urls import re_path as url

from . import views

urlpatterns = [
    # generic profile endpoint
    url(r'^profile/(?P<username>\w+)/', views.profile, name='profile-api'),
    # current user profile
    url(r'^profile/', views.profile, name='profile-api'),
]
