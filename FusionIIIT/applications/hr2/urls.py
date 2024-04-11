from django.conf.urls import url

from . import views

app_name = 'hr2'

urlpatterns = [

    url(r'^$', views.service_book, name='hr2'),
    url(r'^hradmin/$', views.hr_admin, name='hradmin'),
    url(r'^edit/(?P<id>\d+)/$', views.edit_employee_details,
        name='editEmployeeDetails'),
    url(r'^viewdetails/(?P<id>\d+)/$',
        views.view_employee_details, name='viewEmployeeDetails'),
    url(r'^editServiceBook/(?P<id>\d+)/$',
        views.edit_employee_servicebook, name='editServiceBook'),
    url(r'^administrativeProfile/$', views.administrative_profile,
        name='administrativeProfile'),
    url(r'^addnew/$', views.add_new_user, name='addnew'),
    url(r'^ltc_form/(?P<id>\d+)/$', views.ltc_form,
        name='ltcForm'),
    
    url(r'^view_ltc_form/(?P<id>\d+)/$', views.view_ltc_form,
        name='view_ltc_form'),
    url(r'^form_mangement_ltc/',views.form_mangement_ltc, name='form_mangement_ltc'),
    url(r'dashboard/', views.dashboard, name='dashboard'),
    url(r'^form_mangement_ltc_hr/(?P<id>\d+)/$',views.form_mangement_ltc_hr, name='form_mangement_ltc_hr'),
    url(r'^form_mangement_ltc_hod/',views.form_mangement_ltc_hod, name='form_mangement_ltc_hod'),
    url(r'^search_employee/', views.search_employee, name='search_employee'),
    url(r'^track_file/(?P<id>\d+)/$', views.track_file, name='track_file'),
    url('form_view_ltc/(?P<id>\d+)/$', views.form_view_ltc, name='form_view_ltc'),
    url('file_handle/', views.file_handle, name='file_handle'),
    url('file_handle_cpda/', views.file_handle_cpda, name='file_handle_cpda'),

    url(r'^cpda_form/(?P<id>\d+)/$', views.cpda_form,name='cpdaForm'),
    url(r'^view_cpda_form/(?P<id>\d+)/$', views.view_cpda_form,name='view_cpda_form'),
    url(r'^form_mangement_cpda/',views.form_mangement_cpda, name='form_mangement_cpda'),
    url(r'^form_mangement_cpda_hr/(?P<id>\d+)/$',views.form_mangement_cpda_hr, name='form_mangement_cpda_hr'),
    url(r'^form_mangement_cpda_hod/',views.form_mangement_cpda_hod, name='form_mangement_cpda_hod'),
    url('form_view_cpda/(?P<id>\d+)/$', views.form_view_cpda, name='form_view_cpda'),


    url(r'^leave_form/(?P<id>\d+)/$', views.leave_form,name='leaveForm'),
    url(r'^view_leave_form/(?P<id>\d+)/$', views.view_leave_form,name='view_leave_form'),
    url(r'^form_mangement_leave/',views.form_mangement_leave, name='form_mangement_leave'),
    url(r'^form_mangement_leave_hr/(?P<id>\d+)/$',views.form_mangement_leave_hr, name='form_mangement_leave_hr'),
    url(r'^form_mangement_leave_hod/',views.form_mangement_leave_hod, name='form_mangement_leave_hod'),
    url('form_view_leave/(?P<id>\d+)/$', views.form_view_leave, name='form_view_leave'),



    url(r'^appraisal_form/(?P<id>\d+)/$', views.appraisal_form,name='appraisalForm'),
    url(r'^view_appraisal_form/(?P<id>\d+)/$', views.view_appraisal_form,name='view_appraisal_form'),
    url(r'^form_mangement_appraisal/',views.form_mangement_appraisal, name='form_mangement_appraisal'),
    url(r'^form_mangement_appraisal_hr/(?P<id>\d+)/$',views.form_mangement_appraisal_hr, name='form_mangement_appraisal_hr'),
    url(r'^form_mangement_appraisal_hod/',views.form_mangement_appraisal_hod, name='form_mangement_appraisal_hod'),
    url('form_view_appraisal/(?P<id>\d+)/$', views.form_view_appraisal, name='form_view_appraisal'),
























]
