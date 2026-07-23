from django.conf.urls import url

from . import views

app_name = "placement"

urlpatterns = [
    url(r"^api/placement/$", views.placement_api, name="placement_api"),
    url(r"^api/placement/(?P<schedule_id>[0-9]+)/$", views.placement_detail_api, name="placement_detail_api"),
    url(r"^api/statistics/$", views.placement_statistics_api, name="placement_statistics_api"),
    url(r"^api/reports/$", views.placement_reports_api, name="placement_reports_api"),
    url(r"^api/reports/export/$", views.placement_reports_export_api, name="placement_reports_export_api"),
    url(r"^api/report-schedules/$", views.placement_report_schedules_api, name="placement_report_schedules_api"),
    url(r"^api/report-schedules/(?P<schedule_id>[0-9]+)/$", views.placement_report_schedule_detail_api, name="placement_report_schedule_detail_api"),
    url(r"^api/delete-statistics/(?P<record_id>[0-9]+)/$", views.delete_placement_statistics_api, name="delete_placement_statistics_api"),
    url(r"^api/higher-studies/$", views.higher_studies_api, name="higher_studies_api"),
    url(r"^api/higher-studies/(?P<record_id>[0-9]+)/$", views.higher_studies_detail_api, name="higher_studies_detail_api"),
    url(r"^api/registration/$", views.registration_api, name="registration_api"),
    url(r"^api/add-field/$", views.placement_fields_api, name="placement_fields_api"),
    url(r"^api/form-fields/$", views.form_fields_api, name="form_fields_api"),
    url(r"^api/profile/$", views.placement_profile_api, name="placement_profile_api"),
    url(r"^api/notification-preferences/$", views.notification_preferences_api, name="notification_preferences_api"),
    url(r"^api/apply-for-placement/$", views.apply_for_placement_api, name="apply_for_placement_api"),
    url(r"^api/apply-for-placement/(?P<schedule_id>[0-9]+)/$", views.withdraw_application_api, name="withdraw_application_api"),
    url(r"^api/my-applications/$", views.my_applications_api, name="my_applications_api"),
    url(r"^api/my-offers/$", views.my_offers_api, name="my_offers_api"),
    url(r"^api/offer/(?P<offer_id>[0-9]+)/$", views.offer_detail_api, name="offer_detail_api"),
    url(r"^api/offer/(?P<offer_id>[0-9]+)/respond/$", views.offer_respond_api, name="offer_respond_api"),
    url(r"^api/student-applications/(?P<identifier>[0-9]+)/$", views.student_applications_api, name="student_applications_api"),
    url(r"^api/application-detail/(?P<application_id>[0-9]+)/$", views.application_detail_api, name="application_detail_api"),
    url(r"^api/application-detail/(?P<application_id>[0-9]+)/interview/$", views.application_interview_schedule_api, name="application_interview_schedule_api"),
    url(r"^api/download-applications/(?P<schedule_id>[0-9]+)/$", views.download_applications_api, name="download_applications_api"),
    url(r"^api/nextround/(?P<schedule_id>[0-9]+)/$", views.next_round_api, name="next_round_api"),
    url(r"^api/timeline/(?P<schedule_id>[0-9]+)/$", views.timeline_api, name="timeline_api"),
    url(r"^api/calender/$", views.calendar_api, name="calendar_api"),
    url(r"^api/generate-cv/$", views.generate_cv_api, name="generate_cv_api"),
    url(r"^api/debared-students/$", views.debarred_students_api, name="debarred_students_api"),
    url(r"^api/debared-status/(?P<roll_no>[A-Za-z0-9]+)/$", views.debarred_status_api, name="debarred_status_api"),
    url(r"^api/send-notification/$", views.send_notification_api, name="send_notification_api"),
    url(r"^api/restrictions/$", views.restrictions_api, name="restrictions_api"),
    url(r"^api/restrictions/(?P<restriction_id>[0-9]+)/$", views.restriction_detail_api, name="restriction_detail_api"),
    url(r"^api/policies/$", views.placement_policies_api, name="placement_policies_api"),
    url(r"^api/policies/(?P<policy_id>[0-9]+)/$", views.placement_policy_detail_api, name="placement_policy_detail_api"),
    url(r"^api/alumni/profile/$", views.alumni_profile_api, name="alumni_profile_api"),
    url(r"^api/alumni/directory/$", views.alumni_directory_api, name="alumni_directory_api"),
    url(r"^api/alumni/verification/$", views.alumni_verification_list_api, name="alumni_verification_list_api"),
    url(r"^api/alumni/verification/(?P<profile_id>[0-9]+)/$", views.alumni_verification_detail_api, name="alumni_verification_detail_api"),
    url(r"^api/alumni/referrals/$", views.alumni_referrals_api, name="alumni_referrals_api"),
    url(r"^api/alumni/connections/$", views.alumni_connections_api, name="alumni_connections_api"),
    url(r"^api/alumni/connections/(?P<connection_id>[0-9]+)/$", views.alumni_connection_detail_api, name="alumni_connection_detail_api"),
    url(r"^api/alumni/sessions/$", views.alumni_sessions_api, name="alumni_sessions_api"),
    url(r"^api/alumni/sessions/(?P<session_id>[0-9]+)/$", views.alumni_session_detail_api, name="alumni_session_detail_api"),
    # PlacementAppeal API endpoints
    url(r"^api/placement-appeals/$", views.placement_appeal_list_create_api, name="placement_appeal_list_create_api"),
    url(r"^api/placement-appeals/(?P<pk>[0-9]+)/$", views.placement_appeal_detail_api, name="placement_appeal_detail_api"),
    # Placement Announcements API endpoints
    url(r"^api/announcements/$", views.placement_announcements_api, name="placement_announcements_api"),
    url(r"^api/announcements/(?P<announcement_id>[0-9]+)/$", views.placement_announcement_detail_api, name="placement_announcement_detail_api"),
    # Off-Campus Placements API endpoints
    url(r"^api/offcampus/$", views.offcampus_placements_api, name="offcampus_placements_api"),
    url(r"^api/offcampus/(?P<placement_id>[0-9]+)/$", views.offcampus_placement_detail_api, name="offcampus_placement_detail_api"),
    # Published-CPI student view + export API endpoints
    url(r"^api/cpi-batches/$", views.placement_cpi_batches_api, name="placement_cpi_batches_api"),
    url(r"^api/cpi-students/$", views.placement_cpi_students_api, name="placement_cpi_students_api"),
    # Branch (department) reference list for placement forms
    url(r"^api/branches/$", views.placement_branches_api, name="placement_branches_api"),
    # Free-form placement calendar events (Google-Calendar style)
    url(r"^api/calendar-events/$", views.placement_calendar_events_api, name="placement_calendar_events_api"),
    url(r"^api/calendar-events/(?P<event_id>[0-9]+)/$", views.placement_calendar_event_detail_api, name="placement_calendar_event_detail_api"),
]
