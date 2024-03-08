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
   url(r'dashboard/', views.dashboard, name='dashboard'),
    url(r'^cpda_form/(?P<id>\d+)/$', views.cpda_form,
        name='cpdaForm'),
    url(r'^view_cpda_form/(?P<id>\d+)/$', views.view_cpda_form,
    name='view_cpda_form'),


    url(r'^form_mangement_cpda/',views.form_mangement_cpda, name='form_mangement_cpda'),
    url(r'^form_mangement_cpda_hr/(?P<id>\d+)/$',views.form_mangement_cpda_hr, name='form_mangement_cpda_hr'),
    url(r'^form_mangement_cpda_get_hod/',views.form_mangement_cpda_get_hod, name='form_mangement_cpda_get_hod'),


    url(r'^form_mangement_cpda_hod/(?P<id>\d+)/$',views.form_mangement_cpda_hod, name='form_mangement_cpda_hod'),
    # url(r'^form_mangement_cpda_get_ar/',views.form_mangement_cpda_get_ar, name='form_mangement_cpda_get_ar'),

    # url(r'^form_mangement_cpda_director/(?P<id>\d+)/$',views.form_mangement_cpda_director, name='form_mangement_cpda_director'),
    url(r'^form_mangement_cpda_get_director/',views.form_mangement_cpda_get_director, name='form_mangement_cpda_get_director'),

    url(r'^ltc_form/(?P<id>\d+)/$', views.ltc_form,
        name='ltcForm'),
  
    url(r'^view_ltc_form/(?P<id>\d+)/$', views.view_ltc_form,
    name='view_ltc_form'),

    url(r'^form_mangement_ltc/',views.form_mangement_ltc, name='form_mangement_ltc'),
    url(r'^form_mangement_ltc_hr_/(?P<id>\d+)/$',views.form_mangement_ltc_hr, name='form_mangement_ltc_hr'),
    url(r'^form_mangement_ltc_get_hod/',views.form_mangement_ltc_get_hod, name='form_mangement_ltc_get_hod'),


    url(r'^form_mangement_ltc_hod/(?P<id>\d+)/$',views.form_mangement_ltc_hod, name='form_mangement_ltc_hod'),
    # url(r'^form_mangement_ltc_get_ar/',views.form_mangement_ltc_get_ar, name='form_mangement_ltc_get_ar'),
    # url(r'^form_mangement_ltc_director/(?P<id>\d+)/$',views.form_mangement_ltc_director, name='form_mangement_ltc_director'),
    url(r'^form_mangement_ltc_get_director/',views.form_mangement_ltc_get_director, name='form_mangement_ltc_get_director'),     



    
]
