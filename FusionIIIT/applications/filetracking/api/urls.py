from django.conf.urls import url
from . import views  

urlpatterns = [
    url(r'^file/$', views.create_file, name='create_file'),
    url(r'^file/(?P<file_id>\d+)/$', views.view_file, name='view_file'),
    url(r'^file/(?P<file_id>\d+)/$', views.delete_file, name='delete_file'),
    url(r'^inbox/$', views.view_inbox, name='view_inbox'),
    url(r'^outbox/$', views.view_outbox, name='view_outbox'),
    url(r'^history/(?P<file_id>\d+)/$', views.view_history, name='view_history'),
    url(r'^file/(?P<file_id>\d+)/$', views.forward_file, name='forward_file'),
    url(r'^designations/(?P<username>\w+)/$', views.get_designations, name='get_designations'),
]
