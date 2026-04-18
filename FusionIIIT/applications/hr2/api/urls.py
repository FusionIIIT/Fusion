from django.conf.urls import url
from django.urls import path
from . import views


app_name = 'hr2_refactored'

urlpatterns = [
    # ==================================================================
    # NEW REST-style endpoints (must come BEFORE generic prefix patterns)
    # ==================================================================

    # --- Generic form-type endpoints (cpda_adv, ltc, leave, appraisal) ---
    path('<str:form_type_slug>/requests', views.FormTypeRequests.as_view(), name='form_type_requests'),
    path('<str:form_type_slug>/inbox', views.FormTypeInbox.as_view(), name='form_type_inbox'),
    path('<str:form_type_slug>/archive', views.FormTypeArchive.as_view(), name='form_type_archive'),
    path('<str:form_type_slug>/track/<int:file_id>', views.FormTypeTrack.as_view(), name='form_type_track'),
    path('<str:form_type_slug>/form/<int:form_id>', views.FormTypeFormDetail.as_view(), name='form_type_form_detail'),

    # --- CPDA Claim (nested path: cpda/claim/...) ---
    path('cpda/claim/requests', views.CpdaClaimRequests.as_view(), name='cpda_claim_requests'),
    path('cpda/claim/inbox', views.CpdaClaimInbox.as_view(), name='cpda_claim_inbox'),
    path('cpda/claim/archive', views.CpdaClaimArchive.as_view(), name='cpda_claim_archive'),
    path('cpda/claim/track/<int:file_id>', views.CpdaClaimTrack.as_view(), name='cpda_claim_track'),
    path('cpda/claim/submit', views.CpdaClaimSubmit.as_view(), name='cpda_claim_submit'),

    # --- Leave-specific endpoints ---
    path('leave/submit', views.LeaveSubmit.as_view(), name='leave_submit'),
    path('leave/handle/<int:file_id>/', views.LeaveFileHandle.as_view(), name='leave_file_handle'),
    path('leave/academic/<int:file_id>/', views.LeaveAcademicResponsibility.as_view(), name='leave_academic'),
    path('leave/administrative/<int:file_id>/', views.LeaveAdministrativeResponsibility.as_view(), name='leave_administrative'),
    path('leave/offline', views.OfflineLeaveForm.as_view(), name='leave_offline'),
    path('leave/all-balances', views.AllEmployeeLeaveBalances.as_view(), name='leave_all_balances_new'),
    path('leave/create', views.LeaveSubmit.as_view(), name='leave_create'),

    # --- Appraisal-specific ---
    path('appraisal/submit', views.AppraisalSubmit.as_view(), name='appraisal_submit'),

    # --- LTC-specific ---
    path('ltc/create', views.LtcCreate.as_view(), name='ltc_create'),

    # --- Search & generic ---
    path('search_employees', views.SearchEmployeesView.as_view(), name='search_employees_new'),
    path('formtrack/<int:file_id>', views.FormTrackGeneric.as_view(), name='formtrack_generic'),
    path('employee/<int:employee_id>', views.EmployeeDetail.as_view(), name='employee_detail'),
    path('admin/leave/<int:user_id>', views.AdminLeaveRequests.as_view(), name='admin_leave_requests'),

    # ==================================================================
    # EXISTING endpoints (preserved as-is)
    # ==================================================================

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
    # Responsibility management (HR-UC-026, HR-UC-027)
    url('responsibility/action/', views.ResponsibilityAction.as_view(), name='responsibility_action'),
]
