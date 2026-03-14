from django.conf.urls import url , include
from django.conf import settings
from django.conf.urls.static import static

from . import views

app_name = 'mess'

urlpatterns = [

    url(r'^$', views.mess, name='mess'),
    url(r'^menurequest/', views.menu_change_request, name='menu_change_request'),
    # url(r'^placeorder/', views.place_order, name='placeorder'),
    url(r'^addleavet/', views.add_leave_manager, name='addleavet'),
    url(r'^submitmessfeedback/', views.submit_mess_feedback, name='submitmessfeedback'),
    url(r'^messvacationsubmit/', views.mess_vacation_submit, name='messvacationsubmit'),
    url(r'^messmenusubmit/', views.submit_mess_menu, name='messmenusubmit'),
    url(r'^regsubmit/', views.regsubmit, name='regsubmit'),
    url(r'^startmessregistration/', views.start_mess_registration, name='startmessregistration'),
    url(r'^closemessregistration/', views.closeRegistration, name='closemessregistration'),
    url(r'^menudownload/', views.MenuPDF.as_view(), name='MenuPDF'),
    url(r'^menudownload1/', views.MenuPDF1.as_view(), name='MenuPDF1'),
    # url(r'^(?P<ap_id>[0-9]+)/response/', views.response, name='response'),
    url(r'^response', views.menu_change_response, name='response'),
    url(r'^(?P<ap_id>[0-9]+)/responsevacationfood/', views.response_vacation_food, name='responsevacationfood'),
    url(r'^leave', views.mess_leave_request, name='messleaverequest'),
    url(r'^invitation', views.invitation, name='invitation'),
    url(r'^minutes', views.minutes, name='minutes'),
    url(r'^placerequest', views.place_request, name='placerequest'),
    url(r'^addmesscommittee', views.submit_mess_committee, name='addmesscommittee'),
    url(r'^removemesscommittee', views.remove_mess_committee, name='removemesscommittee'),
    url(r'^rebateresponse', views.rebate_response, name='rebateresponse'),
    url(r'^specialrequestresponse', views.special_request_response, name='specialrequestresponse'),
    url(r'^updatecost', views.update_cost, name='updatecost'),
    # url(r'^getnonvegorder', views.get_nonveg_order, name='getnonvegorder'),
    url(r'^getleave', views.get_leave_data, name='getleave'),
    url(r'^generatemessbill', views.generate_mess_bill, name='generatemessbill'),
    url(r'^acceptleave', views.accept_vacation_leaves, name='acceptleave'),
    url(r'^selectmessconvener', views.select_mess_convener, name='selectmessconvener'),
    url(r'^billdownload', views.BillPDFStudent.as_view(), name='BillPDFStudent'),
    url("info-form", views.mess_info, name="info"),
    url(r'^updatemenuu', views.update_menu1, name='update_menu1'),
    url(r'^updatemenu', views.update_menu2, name='update_menu2'),

    url(r'^api', include('applications.central_mess.api.urls')),
    
    url(r'^registeredstudent', views.searchAddOrRemoveStudent, name='registeredstudent'),
    url(r'^registrationRequest', views.reg_request, name='reg_request'),
    url(r'^updatePaymentReq', views.update_payment, name='update_payment'),
    url(r'^respond_to_updatePayment', views.respond_to_update_payment, name='response_to_update_payment'),
    url(r'^respond_to_reg_req',views.respond_to_reg, name='reg_response'),
    url(r'^deregistrationRequest', views.de_reg_request, name='deregistrationRequest'),
    url(r'^updatesemdates', views.update_semdates, name='updatesemdates'),
    url(r'^updateBill', views.update_bill, name='updateBill'),
    url(r'^updatemonthlybill',views.update_bill_excel,name="update_bill"),
  
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)