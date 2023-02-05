from django.conf.urls import url
from . import views
from django.urls import include,path
app_name = 'establishment'

urlpatterns = [
    url(r'^$', views.establishment, name='establishment'),
    url(r'cpda/', views.cpda, name='cpda'),
    url(r'ltc/', views.ltc, name='ltc'),
    url(r'appraisal/', views.appraisal, name='appraisal')
]