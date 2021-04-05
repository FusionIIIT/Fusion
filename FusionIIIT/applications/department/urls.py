from django.conf.urls import url

from . import views

app_name = 'dep'

urlpatterns = [

    url(r'^$', views.dep_main, name='dep'),
    url(r'^file_request/$', views.file_request, name='file_request'),
    url(r'^All_Students/(?P<bid>[0-9]+)/$', views.All_Students,name='All_Students')
]
