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
    url(r'^regadd/', views.regadd, name='regadd'),
    url(r'^menudownload/', views.MenuPDF.as_view(), name='MenuPDF'),
    url(r'^menudownload1/', views.MenuPDF.as_view(), name='MenuPDF1'),
    # url(r'^(?P<ap_id>[0-9]+)/response/', views.response, name='response'),
    url(r'^response', views.response, name='response'),
    url(r'^(?P<ap_id>[0-9]+)/processvacafood/', views.processvacafood, name='processvacafood'),
    url(r'^leave', views.leaverequest, name='leaverequest'),
    url(r'^invitation', views.invitation, name='invitation'),
    url(r'^minutes', views.minutes, name='minutes'),
    url(r'^place_request', views.place_request, name='place_request'),
    url(r'^rebate_response', views.rebate_response, name='rebate_response'),
    # url(r'^(?P<ap_id>[0-9]+)/rebate_response/', views.rebate_response, name='rebate_response'),
    url(r'^responsespl', views.responsespl, name='responsespl'),
    # url(r'^(?P<ap_id>[0-9]+)/responsespl/', views.responsespl, name='responsespl'),
    url(r'^updatecost', views.updatecost, name='updatecost'),
    url(r'^billgenerate', views.billgenerate, name='billgenerate'),

]
