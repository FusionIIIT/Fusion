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
]
