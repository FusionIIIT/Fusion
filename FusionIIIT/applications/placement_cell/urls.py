from django.conf.urls import url, include
from . import views

app_name = 'placement'

urlpatterns = [
    url(r'^$', views.placement, name='placement'),
    url(r'^get_reference_list/$', views.get_reference_list, name='get_reference_list'),
    url(r'^checking_roles/$', views.checking_roles, name='checking_roles'),
    url(r'^companyname_dropdown/$', views.company_name_dropdown, name='companyname_dropdown'),
    url(r'^student_records/invitation_status$', views.invitation_status, name='invitation_status'),
    url(r'^student_records/delete_invitation_status$', views.delete_invitation_status, name='delete_invitation_status'),
    url(r'^student_records/$', views.student_records, name='student_records'),
    url(r'^manage_records/$', views.manage_records, name='manage_records'),
    url(r'^statistics/$', views.placement_statistics, name='placement_statistics'),
  
    url(r'^delete_placement_statistics/$', views.delete_placement_statistics, name='delete_placement_statistics'),
    url(r'^cv/(?P<username>[a-zA-Z0-9\.]{1,20})/$', views.cv, name="cv"),


    #added new url
    url(r'^add_placement_schedule/$', views.add_placement_schedule, name='add_placement_schedule'),
    url(r'^placement_schedule_save/$', views.placement_schedule_save, name='placement_schedule_save'),
    url(r'^delete_placement_record/$', views.delete_placement_record, name='delete_placement_record'),
    url(r'^add_placement_record/$', views.add_placement_record, name='add_placement_record'),
    url(r'^placement_record_save/$', views.placement_record_save, name='placement_record_save'),
    url(r'^add_placement_visit/$', views.add_placement_visit, name='add_placement_visit'),
    url(r'^placement_visit_save/$', views.placement_visit_save, name='placement_visit_save'),

    # ---- PCMS New URLs ----

    # Dashboard
    url(r'^pcms/$', views.pcms_dashboard, name='pcms_dashboard'),

    # Company Management
    url(r'^companies/$', views.company_list, name='company_list'),
    url(r'^companies/register/$', views.register_company, name='register_company'),
    url(r'^companies/(?P<company_id>\d+)/$', views.company_detail, name='company_detail'),
    url(r'^companies/(?P<company_id>\d+)/approve/$', views.approve_company, name='approve_company'),

    # Job Posting Management
    url(r'^jobs/$', views.job_posting_list, name='job_posting_list'),
    url(r'^jobs/create/$', views.create_job_posting, name='create_job_posting'),
    url(r'^jobs/(?P<posting_id>\d+)/$', views.job_posting_detail, name='job_posting_detail'),
    url(r'^jobs/(?P<posting_id>\d+)/edit/$', views.edit_job_posting, name='edit_job_posting'),
    url(r'^jobs/(?P<posting_id>\d+)/toggle/$', views.toggle_job_posting, name='toggle_job_posting'),

    # Application Management
    url(r'^jobs/(?P<posting_id>\d+)/apply/$', views.apply_for_job, name='apply_for_job'),
    url(r'^my-applications/$', views.my_applications, name='my_applications'),
    url(r'^jobs/(?P<posting_id>\d+)/applications/$', views.manage_applications, name='manage_applications'),
    url(r'^jobs/(?P<posting_id>\d+)/bulk-shortlist/$', views.bulk_shortlist, name='bulk_shortlist'),

    # Interview Management
    url(r'^jobs/(?P<posting_id>\d+)/schedule-interview/$', views.schedule_interview, name='schedule_interview'),
    url(r'^interviews/(?P<interview_id>\d+)/$', views.interview_detail, name='interview_detail'),

    # Offer Management
    url(r'^applications/(?P<application_id>\d+)/extend-offer/$', views.extend_offer, name='extend_offer'),
    url(r'^my-offers/$', views.my_offers, name='my_offers'),
    url(r'^offers/(?P<offer_id>\d+)/respond/$', views.respond_to_offer, name='respond_to_offer'),
    url(r'^offers/$', views.all_offers, name='all_offers'),

    # Reports & Analytics
    url(r'^reports/$', views.placement_reports, name='placement_reports'),

    # Announcements
    url(r'^announcements/$', views.announcement_list, name='announcement_list'),
    url(r'^announcements/create/$', views.create_announcement, name='create_announcement'),
    url(r'^announcements/(?P<announcement_id>\d+)/$', views.announcement_detail, name='announcement_detail'),
    url(r'^announcements/(?P<announcement_id>\d+)/delete/$', views.delete_announcement, name='delete_announcement'),

    # Placement Policies
    url(r'^policies/$', views.manage_policies, name='manage_policies'),

    # REST API
    url(r'^api/', include('applications.placement_cell.api.urls')),
]
