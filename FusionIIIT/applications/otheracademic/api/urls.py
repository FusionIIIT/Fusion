from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from applications.otheracademic import analytics_views, escalation_views

router = DefaultRouter()
router.register(r'analytics', analytics_views.AnalyticsDashboardViewSet, basename='analytics')
router.register(r'feedback', analytics_views.FeedbackViewSet, basename='feedback')
router.register(r'health-check', analytics_views.HealthCheckViewSet, basename='health-check')
router.register(r'escalations', escalation_views.NoDuesEscalationViewSet, basename='escalations')
router.register(r'audit-log', escalation_views.AuditLogViewSet, basename='audit-log')

urlpatterns = [
    # REST API Router for T22/T23/T24
    path('', include(router.urls)),
    
    #Leave_Form URLS
    path('leave-form-submit/', views.LeaveFormSubmitView.as_view(), name='leave-form-submit'), 
    path('leave-pg-submit/', views.LeavePGSubmitView.as_view(), name='leave-pg-submit'), 
    path('fetch-pending-leaves/', views.FetchPendingLeaveRequests.as_view(), name='fetch-pending-leaves'),
    path('update-leave-status/', views.UpdateLeaveStatus.as_view(), name='update-leave-status'),
    path('fetch-pending-leaves-ta/', views.FetchPendingLeaveRequestsTA.as_view(), name='fetch-pending-leaves-ta'),
    path('update-leave-status-ta/', views.UpdateLeaveStatusTA.as_view(), name='update-leave-status-ta'),
    path('fetch-pending-leaves-thesis/', views.FetchPendingLeaveRequestsThesis.as_view(), name='fetch-pending-leaves-thesis'),
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
    path('TA-supervisor-pending-requests/', views.TA_SupervisorFetchPendingAssistantshipRequests.as_view(), name='TA-supervisor-pending-requests'),
    path('TA-supervisor-assistantship-update/', views.TA_SupervisorUpdateAssistantshipStatus.as_view(), name='TA-supervisor-assistantship-update'),
    path('Ths-supervisor-assistantship-update/', views.Ths_SupervisorUpdateAssistantshipStatus.as_view(), name='Ths-supervisor-assistantship-update'),
    path('Ths-supervisor-pending-requests/', views.Ths_SupervisorFetchPendingAssistantshipRequests.as_view(), name='Ths-supervisor-pending-requests'),
    path('deptadmin-pending-requests/', views.HODFetchPendingAssistantshipRequests.as_view(), name='deptadmin-pending-requests'),
    path('deptadmin-update-status/', views.HODUpdateAssistantshipStatus.as_view(), name='deptadmin-update-status'),
    path('acadadmin-pending-requests/', views.AcadAdminFetchPendingAssistantshipRequests.as_view(), name='acadadmin-pending-requests'),
    path('acadadmin-update-status/', views.AcadAdminUpdateAssistantshipStatus.as_view(), name='acadadmin-update-status'),
    path('dean-pending-requests/', views.DeanAcadFetchPendingAssistantshipRequests.as_view(), name='dean-pending-requests'),
    path('dean-update-status/', views.DeanAcadUpdateAssistantshipStatus.as_view(), name='dean-update-status'),
    path('director-pending-requests/', views.DirectorFetchPendingAssistantshipRequests.as_view(), name='director-pending-requests'),
    path('director-update-status/', views.DirectorUpdateAssistantshipStatus.as_view(), name='director-update-status'),
    path('get_assistantship_status/', views.GetAssistantshipStatus.as_view(), name='get_assistantship_status'),
    
    # Graduate Seminar URLs
    path('graduate-form-submit/', views.GraduateSeminarFormSubmitView.as_view(), name='graduate-form-submit'),
    path('admin-graduate-requests/', views.FetchPendingGraduateSeminarRequests.as_view(), name='admin-graduate-requests'),
    path('update-graduate-status/', views.UpdateGraduateSeminarStatus.as_view(), name='update-graduate-status'),
    path('get-graduate-seminar-status/', views.GetGraduateSeminarStatus.as_view(), name='get-graduate-seminar-status'),
    
    # No Dues URLs
    path('get-nodues-records/', views.GetNoDuesRecords.as_view(), name='get-nodues-records'),
    path('update-nodues-status/', views.UpdateNoDuesStatus.as_view(), name='update-nodues-status'),
]