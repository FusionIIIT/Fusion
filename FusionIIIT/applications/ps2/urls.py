from django.conf.urls import url
from . import views
app_name = 'ps2'

urlpatterns = [
    url(r'^$', views.homepage, name='homepage'),    
    url(r'^add/$', views.add, name='add'),
]