from django.urls import path
from django.conf.urls import url
from . import views

app_name="research_procedures"#IPR module

urlpatterns = [
     url(r'^$', views.IPR, name='IPR'),
      url(r'^update$', views.update, name='status_update'),

    
]