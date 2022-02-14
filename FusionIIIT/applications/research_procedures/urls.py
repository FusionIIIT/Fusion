from django.urls import path
from django.conf.urls import url
from . import views

app_name="research_procedures"

urlpatterns = [
      url(r'^$', views.patent_registration, name='patent_registration'),
      url(r'^update$', views.patent_status_update, name='patent_status_update'),
]