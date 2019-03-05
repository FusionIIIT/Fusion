from django.conf.urls import url

from . import views

app_name = 'mess'

urlpatterns = [

    url(r'^$', views.mess, name='mess'),
    url(r'^place_order/', views.place_order, name='place_order'),
    url(r'^submit_mess_feedback/', views.submit_mess_feedback, name='submit_mess_feedback'),
    url(r'^mess_vacation_submit/', views.mess_vacation_submit, name='mess_vacation_submit'),
    url(r'^submit_mess_menu/', views.submit_mess_menu, name='submit_mess_menu'),
    url(r'^regsubmit/', views.regsubmit, name='regsubmit'),
    url(r'^start_mess_registration/', views.start_mess_registration, name='start_mess_registration'),
    url(r'^menudownload/', views.MenuPDF.as_view(), name='MenuPDF'),
    url(r'^menudownload1/', views.MenuPDF.as_view(), name='MenuPDF1'),
    # url(r'^(?P<ap_id>[0-9]+)/response/', views.response, name='response'),
    url(r'^response', views.menu_change_response, name='response'),
    url(r'^(?P<ap_id>[0-9]+)/response_vacation_food/', views.response_vacation_food, name='response_vacation_food'),
    url(r'^leave', views.mess_leave_request, name='mess_leave_request'),
    url(r'^invitation', views.invitation, name='invitation'),
    url(r'^minutes', views.minutes, name='minutes'),
    url(r'^place_request', views.place_request, name='place_request'),
    url(r'^rebate_response', views.rebate_response, name='rebate_response'),
    # url(r'^(?P<ap_id>[0-9]+)/rebate_response/', views.rebate_response, name='rebate_response'),
    url(r'^special_request_response', views.special_request_response, name='special_request_response'),
    # url(r'^(?P<ap_id>[0-9]+)/special_request_response/', views.special_request_response, name='special_request_response'),
    url(r'^update_cost', views.update_cost, name='update_cost'),
    url(r'^generate_mess_bill', views.generate_mess_bill, name='generate_mess_bill'),

]
