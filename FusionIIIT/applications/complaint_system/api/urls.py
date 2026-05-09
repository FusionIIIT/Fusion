from django.conf.urls import url

from . import views

urlpatterns = [

    url(r'^user/detail/(?P<detailcomp_id1>[0-9]+)/$', views.complaint_details_api,name='complain-detail-get-api'),
    url(r'^studentcomplain/?$', views.student_complain_api, name='complain-detail2-get-api'),
    url(r'^newcomplain/?$', views.create_complain_api, name='complain-post-api'),
    url(r'^submitdraft/(?P<c_id>[0-9]+)/?$', views.submit_draft_api, name='complain-draft-submit-api'),
    url(r'^updatecomplain/(?P<c_id>[0-9]+)/?$', views.edit_complain_api, name='complain-put-api'),
    url(r'^removecomplain/(?P<c_id>[0-9]+)/?$', views.edit_complain_api, name='complain-delete-api'),
    url(r'^escalate/(?P<c_id>[0-9]+)/?$', views.escalate_complaint_api, name='complain-escalate-api'),
    url(r'^history/(?P<c_id>[0-9]+)/?$', views.complaint_history_api, name='complain-history-api'),
    url(r'^report-analytics/?$', views.report_analytics_api, name='complain-report-analytics-api'),
    url(r'^verify/(?P<c_id>[0-9]+)/?$', views.verify_complaint_api, name='complain-verify-api'),
    url(r'^feedback/(?P<c_id>[0-9]+)/?$', views.submit_feedback_api, name='complain-feedback-api'),
    url(r'^reopen/(?P<c_id>[0-9]+)/?$', views.reopen_complaint_api, name='complain-reopen-api'),
    url(r'^caretaker-action/(?P<c_id>[0-9]+)/?$', views.caretaker_action_api, name='complain-caretaker-action-api'),
    url(r'^bulk-action/?$', views.bulk_complaint_action_api, name='complain-bulk-action-api'),
    
    url(r'^workers/?$', views.worker_api, name='worker-get-api'),
    url(r'^addworker/?$', views.worker_api, name='worker-post-api'),
    url(r'^removeworker/(?P<w_id>[0-9]+)/?$', views.edit_worker_api, name='worker-delete-api'),
    url(r'^updateworker/(?P<w_id>[0-9]+)/?$', views.edit_worker_api, name='worker-put-api'),

    url(r'^caretakers/?$', views.caretaker_api, name='caretaker-get-api'),
    url(r'^addcaretaker/?$', views.caretaker_api, name='caretaker-post-api'),
    url(r'^removecaretaker/(?P<c_id>[0-9]+)/?$', views.edit_caretaker_api, name='caretaker-delete-api'),
    url(r'^updatecaretaker/(?P<c_id>[0-9]+)/?$', views.edit_caretaker_api, name='caretaker-put-api'),
    
    url(r'^supervisors/?$', views.supervisor_api, name='supervisor-get-api'),
    url(r'^addsupervisor/?$', views.supervisor_api, name='supervisor-post-api'),
    url(r'^removesupervisor/(?P<s_id>[0-9]+)/?$', views.edit_supervisor_api, name='supervisor-delete-api'),
    url(r'^updatesupervisor/(?P<s_id>[0-9]+)/?$', views.edit_supervisor_api, name='supervisor-put-api'),
    
]
