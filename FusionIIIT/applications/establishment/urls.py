from django.conf.urls import url
from . import views

app_name = 'establishment'

urlpatterns = [
    url(r'^$', views.establishment, name='establishment')
]