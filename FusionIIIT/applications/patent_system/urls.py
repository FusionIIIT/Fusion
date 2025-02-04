# applications/patent_system/urls.py
from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^applicant$', views.applicant_view, name='applicant'),
]
