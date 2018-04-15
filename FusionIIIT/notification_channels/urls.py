from django.conf.urls import url

from .views import get_type_sorted_notifs, notifications, read_all, seen_all

app_name = 'notifications'


urlpatterns = [
    url(r'^$', notifications, name='notifications'),
    url(r'^read-all/(?P<notif_type>\w+)/$', read_all, name='read_all'),
    url(r'^seen-all/(?P<notif_type>\w+)/$', seen_all, name='seen_all'),
    url(r'^type-sorted-notifs/$', get_type_sorted_notifs, name='get_type_sorted_notifs'),
]
