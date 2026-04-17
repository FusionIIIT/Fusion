from django.conf.urls import url
from django.urls import path
from . import views


app_name = 'hr2_refactored'

urlpatterns = [
    # LTC form
    url('ltc/', views.LTC.as_view(), name='LTC_form'),
    #  cpda advance form
    url('cpdaadv/', views.CPDAAdvance.as_view(), name='CPDAAdvance_form'),
    #  appraisal form
    url('appraisal/', views.Appraisal.as_view(), name='Appraisal_form'),
    # cpda reimbursement form
    url('cpdareim/', views.CPDAReimbursement.as_view(),
        name='CPDAReimbursement_form'),
    # leave PDF download (must be registered before generic leave/)
    url(r'^leave/pdf/(?P<form_id>\d+)/$', views.LeaveFormPdfDownload.as_view(), name='leave_form_pdf'),
    # leave form initials for frontend prefill
    url(r'^leave/form-initials/$', views.LeaveFormInitials.as_view(), name='leave_form_initials'),
    url(r'^leave/balance/$', views.CheckLeaveBalance.as_view(), name='leave_balance_alias'),
    #  leave form (exact path only)
    url(r'^leave/$', views.Leave.as_view(), name='Leave_form'),
    url('formManagement/', views.FormManagement.as_view(), name='formManagement'),
    url('tracking/', views.TrackProgress.as_view(), name='tracking'),
    url('formFetch/', views.FormFetch.as_view(), name='fetch_form'),
    #  create for GetForms
    url('getForms/', views.GetFormHistory.as_view(), name='getForms'),
    url('leaveBalance/', views.CheckLeaveBalance.as_view(), name='leaveBalance'),
    url('leaveBalance/all/', views.AllEmployeeLeaveBalances.as_view(), name='leaveBalance_all'),
    url('allLeaveBalances/', views.AllEmployeeLeaveBalances.as_view(), name='allLeaveBalances'),
    url('getDesignations/', views.DropDown.as_view(), name="designations"),
    url('getOutbox/', views.GetOutbox.as_view(), name='outbox'),
    url('getArchive/', views.ViewArchived.as_view(), name='archive'),
    url('getuserbyid/', views.UserById.as_view(), name='userById'),
    url('get_my_details/', views.GetMyDetails.as_view(), name='get_my_details'),
    url('search_employee/', views.SearchEmployee.as_view(), name='search_employee'),
]
