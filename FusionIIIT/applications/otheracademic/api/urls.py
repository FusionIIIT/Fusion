from django.urls import path
from . import  views 

urlpatterns = [
    #Leave_Form URLS
    path('leave-form-submit/', views.LeaveFormSubmitView.as_view(), name='leave-form-submit'), 
    path('leave-pg-submit/', views.LeavePGSubmitView.as_view(), name='leave-pg-submit'), 
    path('fetch-pending-leaves/', views.FetchPendingLeaveRequests.as_view(), name='fetch-pending-leaves'),
    path('update-leave-status/', views.UpdateLeaveStatus.as_view(), name='update-leave-status'),
    path('fetch-pending-leaves-ta/', views.FetchPendingLeaveRequestsTA.as_view(), name='fetch-pending-leaves-ta'),
    path('update-leave-status-ta/', views.UpdateLeaveStatusTA.as_view(), name='update-leave-status-ta'),
    path('fetch-pending-leaves-thesis/', views.FetchPendingLeaveRequestsThesis.as_view(), name='fetch-pending-leaves-tesis'),
    path('update-leave-status-thesis/', views.UpdateLeaveStatusThesis.as_view(), name='update-leave-status-thesis'),
    path('get-leave-requests/', views.GetLeaveRequests.as_view(), name='get-leave-requests'),
    path('get-pg-leave-requests/', views.GetPGLeaveRequests.as_view(), name='get-pg-leave-requests'),

    #Bonafide_form URLs
    path('bonafide-form-submit/', views.BonafideFormSubmitView.as_view(), name='bonafide-form-submit'), 
    path('admin-bonafide-requests/',views.FetchPendingBonafideRequests.as_view(),name='admin-bonafide-requests'),
    path('admin-updates/',views.UpdateBonafideStatus.as_view(),name='admin-updates'),
    path('bonafide-status/',views.GetBonafideStatus.as_view(),name='bonafide-status'),

    #TA_Assiistantship URLs
    path('assistantship-form-submit/',views.AssistantshipFormSubmitView.as_view(),name='assistantship-form-submit'),
    path('deptadmin_update_assistantship_status/',views.DeptAdminUpdateAssistantshipStatus.as_view(),name='deptadmin_update_assistantship_status'),
    path('deptadmin_fetch_pending_assistantship_requests/',views.DeptAdminFetchPendingAssistantshipRequests.as_view(),name='fetch_pending_assistantship_requests'),
    path('hod_fetch_pending_assistantship_requests/',views.HodFetchPendingAssistantshipRequests.as_view(),name='hod_pending_assistantship_requests'),
    path('hod_update_assistantship_status/',views.HodUpdateAssistantshipStatus.as_view(),name='hod_update_assistantship_status'),
    path('acadadmin_fetch_pending_assistantship_requests/',views.AcadAdminFetchPendingAssistantshipRequests.as_view(),name='acadadmin_pending_assistantship_requests'),
    path('acadadmin_update_assistantship_status/',views.AcadAdminUpdateAssistantshipStatus.as_view(),name='acadadmin_update_assistantship_status'),
    path('get_assistantship_status/',views.GetAssistantshipStatus.as_view(),name='get_assistantship_status'),
]
