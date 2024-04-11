from django.conf.urls import url
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
]
