from django.conf.urls import url
from rest_framework.routers import DefaultRouter

from applications.placement_cell.api import views as api_views

# ViewSet router
router = DefaultRouter()
router.register(r'companies', api_views.CompanyViewSet, basename='company')
router.register(r'job-postings', api_views.JobPostingViewSet, basename='jobposting')
router.register(r'job-applications', api_views.JobApplicationViewSet, basename='jobapplication')
router.register(r'job-offers', api_views.JobOfferViewSet, basename='joboffer')
router.register(r'announcements', api_views.AnnouncementViewSet, basename='announcement')

urlpatterns = [
    # 1. Role & Auth
    url(r'^roles/$', api_views.user_roles_api, name='user_roles_api'),

    # 2. Placement Schedule (Legacy)
    url(r'^placement/$', api_views.placement_schedule_api, name='placement_schedule_api'),
    url(r'^placement/(?P<schedule_id>\d+)/$', api_views.placement_schedule_detail_api, name='placement_schedule_detail_api'),

    # 3. Student Records & CV
    url(r'^student-records/$', api_views.student_records_api, name='student_records_api'),
    url(r'^cv/(?P<username>[\w.@+-]+)/$', api_views.cv_data_api, name='cv_data_api'),
    url(r'^generate-cv/$', api_views.generate_cv_api, name='generate_cv_api'),

    # 4. Invitation / Application Status
    url(r'^student-applications/(?P<job_id>\d+)/$', api_views.student_applications_api, name='student_applications_api'),
    url(r'^student-applications-update/(?P<pk>\d+)/$', api_views.update_student_application_api, name='update_student_application_api'),
    url(r'^invitation-status/$', api_views.invitation_status_api, name='invitation_status_api'),

    # 5. Statistics & Records
    url(r'^statistics/$', api_views.placement_statistics_api, name='placement_statistics_api'),
    url(r'^delete-statistics/$', api_views.placement_statistics_api, name='placement_statistics_delete_api'),
    url(r'^manage-records/$', api_views.manage_records_api, name='manage_records_api'),

    # 6. Debarred Students
    url(r'^debared-students/$', api_views.debarred_students_api, name='debarred_students_api'),
    url(r'^debared-status/(?P<roll_no>[\w.@+-]+)/$', api_views.debarred_status_api, name='debarred_status_api'),

    # 7. Fields & Restrictions
    url(r'^add-field/$', api_views.manage_fields_api, name='manage_fields_api'),
    url(r'^form-fields/$', api_views.form_fields_api, name='form_fields_api'),
    url(r'^restrictions/$', api_views.restrictions_api, name='restrictions_api'),

    # 8. Company Registration (Legacy)
    url(r'^registration/$', api_views.company_registration_api, name='company_registration_api'),

    # 9. Apply for Placement
    url(r'^apply-for-placement/$', api_views.apply_for_placement_api, name='apply_for_placement_api'),

    # 10. Calendar & Timeline
    url(r'^calender/$', api_views.calendar_events_api, name='calendar_events_api'),
    url(r'^timeline/(?P<job_id>\d+)/$', api_views.timeline_api, name='timeline_api'),

    # 11. Next Round & Download
    url(r'^nextround/$', api_views.next_round_api, name='next_round_api'),
    url(r'^download-applications/(?P<job_id>\d+)/$', api_views.download_applications_api, name='download_applications_api'),

    # 12. Chairman Visits
    url(r'^visits/$', api_views.visits_api, name='visits_api'),

    # 13. PCMS Dashboard & Reports
    url(r'^dashboard/$', api_views.dashboard_api, name='dashboard_api'),
    url(r'^reports/$', api_views.reports_api, name='reports_api'),
    url(r'^pcms-stats/$', api_views.placement_stats_pcms_api, name='placement_stats_pcms_api'),
    url(r'^my-summary/$', api_views.my_application_summary_api, name='my_application_summary_api'),

    # 14. Policies
    url(r'^policies/$', api_views.policies_api, name='policies_api'),

    # 15. Interviews
    url(r'^interviews/$', api_views.interviews_api, name='interviews_api'),
    url(r'^interviews/(?P<interview_id>\d+)/$', api_views.interview_detail_api, name='interview_detail_api'),
]

urlpatterns += router.urls
