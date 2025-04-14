from django.conf.urls import url, include 

from django.conf.urls import url, include
from applications.hr2 import views
from applications.hr2.api import form_views


app_name = 'hr2'

urlpatterns = [
   
    url(r'^api/get_leave_balance', views.get_leave_balance, name='get_leave_balance'),
    url(r'^api/search_employees', views.search_employees, name='search_employees'),
    url(r'^api/get_form_initials', views.get_form_initials, name='get_form_initials'),
    url(r'^api/submit_leave_form', views.submit_leave_form, name='submit_leave_form'),
    url(r'^api/get_leave_requests', views.get_leave_requests, name='get_leave_requests'),
    url(r'^api/get_leave_form_by_id/(?P<form_id>\d+)/$', views.get_leave_form_by_id, name='get_leave_form_by_id'),
    url(r'^api/handle_leave_academic_responsibility/(?P<form_id>\d+)/$', views.handle_leave_academic_responsibility, name='handle_leave_academic_responsibility'),
    url(r'^api/handle_leave_administrative_responsibility/(?P<form_id>\d+)/$', views.handle_leave_administrative_responsibility, name='handle_leave_administrative_responsibility'),
    url(r'^api/get_leave_inbox', views.get_leave_inbox, name='get_leave_inbox'),
    url(r'^api/download_leave_form_pdf/(?P<form_id>\d+)/$', views.download_leave_form_pdf, name='download_leave_form_pdf'),
    url(r'^api/handle_leave_file/(?P<form_id>\d+)/$', views.handle_leave_file, name='handle_leave_file'),

    url(r'^api/admin_get_leave_balance/(?P<empid>\w+)/$', views.admin_get_leave_balance, name='admin_get_leave_balance'),
    url(r'^api/admin_get_all_leave_balances/$', views.admin_get_all_leave_balances, name='admin_get_all_leave_balances'),
    url(r'^api/admin_update_leave_balance/(?P<empid>\w+)/$', views.admin_update_leave_balance, name='admin_update_leave_balance'),
    url(r'^api/admin_get_leave_requests/(?P<empid>\w+)/$', views.admin_get_leave_requests, name='admin_get_leave_requests'),
    url(r'^api/hr_employees', views.get_hr_employees, name='get_hr_employees'),

    url(r'api/get_track_file/(?P<id>\d+)/$', views.track_file_react, name='track_file_react'),




    
    



]
