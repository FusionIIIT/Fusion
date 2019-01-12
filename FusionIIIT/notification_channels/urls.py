from django.conf.urls import url

from notification_channels.views import notifications, read_all

app_name = 'notifications'


urlpatterns = [

    url(r'^$', notifications, name='notifications'),
    url(r'^/read-all/$', read_all, name='read_all'),

]
