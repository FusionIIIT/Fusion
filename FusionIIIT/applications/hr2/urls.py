from django.conf.urls import url

from . import views

app_name = 'hr2'

urlpatterns = [

    url(r'^$', views.hr2_index, name='hr2'),
     url(r'^hradmin/$', views.hrAdmin, name='hradmin'),
]

