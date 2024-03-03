from django.conf.urls import url

from . import views

app_name = 'otheracademic'

urlpatterns = [

    url(r'^$', views.otheracademic, name='otheracademic'),
    url(r'^leaveform/$', views.leave_form_submit, name='leave_form_submit'),
    url(r'^leaveApproveForm/$', views.leaveApproveForm, name='leaveApproveForm'),
    url(r'^leaveStatus/$', views.leaveStatus, name='leaveStatus'),
    # url(r'^approve_leave/<int:leave_id>/$', views.approve_leave, name='approve_leave'),
    # url(r'^reject_leave/<int:leave_id>/$', views.reject_leave, name='reject_leave'),
    url(r'^approve_leave/(?P<leave_id>\d+)/$', views.approve_leave, name='approve_leave'),
    url(r'^reject_leave/(?P<leave_id>\d+)/$', views.reject_leave, name='reject_leave'),
    url(r'^graduateseminar/$', views.graduateseminar, name='graduateseminar'),
    url(r'^graduate_form_submit/$', views.graduate_form_submit, name='graduate_form_submit'),
    url(r'^graduate_status/$', views.graduate_status, name='graduate_status'),
    url(r'^bonafide/$', views.bonafide, name='bonafide'),
    url(r'^bonafide_form_submit/$', views.bonafide_form_submit, name='bonafide_form_submit'),
    url(r'^bonafideApproveForm/$', views.bonafideApproveForm, name='bonafideApproveForm'),
    url(r'^approve_bonafide/(?P<leave_id>\d+)/$', views.approve_bonafide, name='approve_bonafide'),
    url(r'^reject_bonafide/(?P<leave_id>\d+)/$', views.reject_bonafide, name='reject_bonafide'),
    url(r'^bonafideStatus/$', views.bonafideStatus, name='bonafideStatus'),
    url(r'^upload_file/(?P<entry_id>\d+)/$', views.upload_file, name='upload_file'),
    url(r'^assistantship/$', views.assistantship, name='assistantship'),
     url(r'^submitform/$', views.assistantship_form_submission, name='assistantship_form_submission'),
     url(r'^approveform/$', views.assistantship_form_approval, name='assistantship_approval'),
      url(r'^noduesverification/$', views.nodues, name='nodues'),
]
