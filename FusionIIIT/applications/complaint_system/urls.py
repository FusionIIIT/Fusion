from django.conf.urls import url

from . import views

app_name = 'complaint'

urlpatterns = [

    url(r'^$', views.check, name='complaint'),
 #   url(r'^login/$', views.login1, name='complaint'),
    url(r'^user/$', views.user),
    url(r'^user/(?P<complaint_id>[0-9]+)/$', views.submitfeedback),
    url(r'^user/detail/(?P<detailcomp_id1>[0-9]+)/$', views.detail),
    url(r'^user/check_complaint/$', views.save_comp),
    url(r'^caretaker/$', views.caretaker),
    url(r'^caretaker/detail2/(?P<detailcomp_id1>[0-9]+)/$', views.detail2),
    url(r'^caretaker/search_complaint$', views.search_complaint),
    url(r'^supervisor/$', views.supervisor),
    url(r'^supervisor/detail3/(?P<detailcomp_id1>[0-9]+)/$', views.detail3),
    url(r'^caretaker/removew/(?P<work_id>[0-9]+)/$', views.removew),
    url(r'^caretaker/(?P<comp_id1>[0-9]+)/$', views.assign_worker),
    url(r'^caretaker/deletecomplaint/(?P<comp_id1>[0-9]+)/$', views.deletecomplaint),
    url(r'^home/(?P<comp_id>[0-9]+)/$', views.assign_worker),
    url(r'^caretaker/(?P<complaint_id>[0-9]+)/(?P<status>[0-9]+)/$', views.changestatus),


]
