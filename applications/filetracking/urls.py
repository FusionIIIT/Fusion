from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static

from . import views

app_name = 'filetracking'

urlpatterns = [

    url(r'^$', views.filetracking, name='filetracking'),
    url(r'^drafts/$', views.drafts, name='drafts'),
    url(r'^outward/$', views.outward, name='outward'),
    url(r'^inward/$', views.inward, name='inward'),
    url(r'^delete/(?P<id>\d+)$',views.delete, name='delete'),
    url(r'^archive/$', views.archive, name='archive'),
    url(r'^finish/(?P<id>\d+)/$', views.finish, name='finish'),
    url(r'^forward/(?P<id>\d+)/$', views.forward, name='forward'),
    url(r'^ajax_dropdown/(?P<id>\d+)/$', views.AjaxDropdown, name='ajax_dropdown'),
    url(r'^ajax/$', views.AjaxDropdown1, name='ajax_dropdown1'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

