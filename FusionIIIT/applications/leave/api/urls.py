from django.conf.urls import url

from . import views

urlpatterns = [

    url(r'leavetype/$', views.leave_type_api,name='leave-type-api'),
    url(r'leavescount/$',views.leaves_count_api,name='leaves-count-api'),
    url(r'leave/$',views.leave_api,name='leave-api'),
    url(r'replacementsegment',views.replacement_segment_api,name='replacement-segment-api'),
    url(r'replacementsegmentoffline',views.replacement_segment_offline_api,name='replacement-segment-offline-api'),
    url(r'leavesegmentoffline',views.leave_segment_offline_api,name='leave-segment-offline-api'),
    url(r'leavesegment',views.leave_segment_api,name='leave-segment-api'),
    url(r'leaverequest',views.leave_request_api,name='leave-request-api'),
    url(r'leaveadministrators',views.leave_administrators_api,name='leave-administartor-api'),
    url(r'leavemigration',views.leave_migration_api,name='leave-migration-api'),
    url(r'restrictedholiday',views.restricted_holiday_api,name='restricted-holiday-api'),
    url(r'closedholiday',views.closed_holiday_api,name='closed-holiday-api'),
    url(r'vacationholiday',views.vacation_holiday_api,name='vacation-holiday-api'),
    url(r'leaveoffline',views.leave_offline_api,name='leave-offline-api'),
    url(r'editleavetype/(?P<c_id>[0-9]+)',views.edit_leave_type_api,name='edit-leave-type-api'),
    url(r'editleavecount/(?P<c_id>[0-9]+)',views.edit_leave_count_api,name='edit-leave-count-api'),
    url(r'editleave/(?P<c_id>[0-9]+)',views.edit_leave_api,name='edit-leave-api'),
    url(r'editreplacementsegment/(?P<c_id>[0-9]+)',views.edit_replacement_segment_api,name='edit-replacement-segment-api'),
    url(r'editreplacementsegmentoffline/(?P<c_id>[0-9]+)',views.edit_replacement_segment_offline_api,name='edit-replacement-segment-offline-api'),
    url(r'editleavesegment/(?P<c_id>[0-9]+)',views.edit_leave_segment_api,name='edit-leave-segment-api'),
    url(r'editleavesegmentoffline/(?P<c_id>[0-9]+)',views.edit_leave_segment_offline_api,name='edit-leave-segment-offline-api'),
    url(r'editleaverequest/(?P<c_id>[0-9]+)',views.edit_leave_request_api,name='edit-leave-request-api'),
    url(r'editleaveadministrators/(?P<c_id>[0-9]+)',views.edit_leave_administrators_api,name='edit-leave-administrators-api'),
    url(r'editleavemigration/(?P<c_id>[0-9]+)',views.edit_leave_migration_api,name='edit-leave-migration-api'),
    url(r'editrestrictedholiday/(?P<c_id>[0-9]+)',views.edit_restricted_holiday_api,name='edit-restricted-holiday-api'),
    url(r'editclosedholiday/(?P<c_id>[0-9]+)',views.edit_closed_holiday_api,name='edit-closed-holiday-api'),
    url(r'editvacationholiday/(?P<c_id>[0-9]+)',views.edit_vacation_holiday_api,name='edit-vacation-holiday-api'),
    url(r'editleaveoffline/(?P<c_id>[0-9]+)',views.edit_leave_offline_api,name='edit-leave-offline-api'),
    
]
