from django.urls import path
from . import views

app_name = 'hr_api'

urlpatterns = [
    # Employee
    path('employees/', views.EmployeeListView.as_view(), name='employee-list'),
    path('employees/<int:employee_id>/', views.EmployeeDetailView.as_view(), name='employee-detail'),

    # Leave
    path('leave-applications/', views.LeaveApplicationListCreateView.as_view(), name='leave-list-create'),
    path('leave-applications/<int:pk>/', views.LeaveApplicationDetailView.as_view(), name='leave-detail'),
    path('leave-balance/', views.LeaveBalanceView.as_view(), name='leave-balance'),
    path('leave-balance/<int:employee_id>/', views.LeaveBalanceView.as_view(), name='leave-balance-other'),
    path('leave-applications/<int:pk>/responsibility/<str:responsibility_type>/', views.LeaveResponsibilityView.as_view(), name='leave-responsibility'),
    path('leave-applications/<int:pk>/request-document/', views.LeaveDocumentRequestView.as_view(), name='leave-request-document'),
    path('leave-applications/<int:pk>/submit-document/', views.LeaveDocumentSubmitView.as_view(), name='leave-submit-document'),
    path('leave-applications/<int:pk>/download/', views.LeaveApplicationDownloadView.as_view(), name='leave-download'),
    path('leave-applications/<int:pk>/withdraw/', views.LeaveApplicationWithdrawView.as_view(), name='leave-withdraw'),
    path('leave-applications/<int:pk>/cancel-request/', views.LeaveApplicationCancelRequestView.as_view(), name='leave-cancel-request'),
    path('leave-applications/<int:pk>/cancel-decision/<str:decision>/', views.LeaveApplicationCancelDecisionView.as_view(), name='leave-cancel-decision'),
    path('leave-applications/<int:pk>/extension-request/', views.LeaveApplicationExtensionRequestView.as_view(), name='leave-extension-request'),
    path('leave-applications/<int:pk>/extension-decision/<str:decision>/', views.LeaveApplicationExtensionDecisionView.as_view(), name='leave-extension-decision'),
    path('leave-applications/<int:pk>/resumption/', views.LeaveResumptionSubmitView.as_view(), name='leave-resumption'),
    path('leave-applications/<int:pk>/resumption-decision/<str:decision>/', views.LeaveResumptionDecisionView.as_view(), name='leave-resumption-decision'),
    path('leave-applications/<int:pk>/<str:decision>/', views.LeaveApproveRejectView.as_view(), name='leave-decision'),
    path('leave-nominee/', views.LeaveNomineeDashboardView.as_view(), name='leave-nominee-dashboard'),
    path('leave-nominee/<int:pk>/', views.LeaveNomineeDecisionView.as_view(), name='leave-nominee-decision'),

    # Attendance
    path('attendance/', views.AttendanceView.as_view(), name='attendance'),

    # Appraisal
    path('appraisal-periods/', views.AppraisalPeriodListView.as_view(), name='appraisal-periods'),
    path('appraisals/', views.AppraisalListView.as_view(), name='appraisals'),

    # Training
    path('training-programs/', views.TrainingProgramListView.as_view(), name='training-programs'),
    path('training-nominations/', views.TrainingNominationView.as_view(), name='training-nominations'),

    # Promotion
    path('promotions/', views.PromotionApplicationView.as_view(), name='promotions'),

    # Faculty Workload
    path('workload/', views.FacultyWorkloadView.as_view(), name='workload'),
    # Add these to the urlpatterns list

    path('ltc/', views.LTCApplicationListCreateView.as_view(), name='ltc-list-create'),
    path('ltc/<int:pk>/', views.LTCApplicationDetailView.as_view(), name='ltc-detail'),
    path('ltc/<int:pk>/download/', views.LTCApplicationDownloadView.as_view(), name='ltc-download'),
    path('ltc/<int:pk>/withdraw/', views.LTCApplicationWithdrawView.as_view(), name='ltc-withdraw'),
    path('ltc/<int:pk>/<str:decision>/', views.LTCApproveRejectView.as_view(), name='ltc-decision'),

    path('cpda-advances/', views.CPDAAdvanceListCreateView.as_view(), name='cpda-advance-list'),
    path('cpda-advances/<int:pk>/', views.CPDAAdvanceDetailView.as_view(), name='cpda-advance-detail'),
    path('cpda-advances/<int:pk>/download/', views.CPDAAdvanceDownloadView.as_view(), name='cpda-advance-download'),
    path('cpda-advances/<int:pk>/withdraw/', views.CPDAAdvanceWithdrawView.as_view(), name='cpda-advance-withdraw'),
    path('cpda-advances/<int:pk>/<str:decision>/', views.CPDAAdvanceApproveRejectView.as_view(), name='cpda-advance-decision'),

    path('cpda-reimbursements/', views.CPDAReimbursementListCreateView.as_view(), name='cpda-reimbursement-list'),
    path('cpda-reimbursements/<int:pk>/', views.CPDAReimbursementDetailView.as_view(), name='cpda-reimbursement-detail'),
    path('cpda-reimbursements/<int:pk>/<str:decision>/', views.CPDAReimbursementApproveRejectView.as_view(), name='cpda-reimbursement-decision'),

    path('appraisal-forms/', views.AppraisalFormListCreateView.as_view(), name='appraisal-form-list'),
    path('appraisal-forms/<int:pk>/', views.AppraisalFormDetailView.as_view(), name='appraisal-form-detail'),
    path('appraisal-forms/<int:pk>/download/', views.AppraisalFormDownloadView.as_view(), name='appraisal-form-download'),
    path('appraisal-forms/<int:pk>/review/', views.AppraisalReviewView.as_view(), name='appraisal-form-review'),
    path('appraisal-forms/<int:pk>/assign/', views.AppraisalAssignView.as_view(), name='appraisal-form-assign'),
]