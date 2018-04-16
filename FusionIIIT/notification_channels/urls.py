from django.conf.urls import url

from .views import get_type_sorted_notifs, notifications, read_all, seen_all, get_unseen_count
from .views import mark_read

app_name = 'notifications'


urlpatterns = [
    url(r'^$', notifications, name='notifications'),
    url(r'^read/(?P<id>\d+)/$', mark_read, name='mark_read'),
    url(r'^read-all/(?P<notif_type>\w+)/$', read_all, name='read_all'),
    url(r'^seen-all/(?P<notif_type>\w+)/$', seen_all, name='seen_all'),
    url(r'^type-sorted-notifs/$', get_type_sorted_notifs, name='get_type_sorted_notifs'),
    url(r'^get-unseen-count/$', get_unseen_count, name='get_unseen_count'),
]
