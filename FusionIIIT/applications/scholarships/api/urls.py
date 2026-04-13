from django.urls import path
from . import views

urlpatterns = [
    # Student Views
    path('student-profile/', views.StudentProfileLookupAPIView.as_view(), name='api-student-profile'),
    path('active-awards/', views.ActiveAwardsAPIView.as_view(), name='api-active-awards'),
    path('student/applications/', views.StudentApplicationsAPIView.as_view(), name='api-student-applications'),
    path('student/submit/mcm/', views.McmSubmissionAPIView.as_view(), name='api-submit-mcm'),
    path('student/submit/medal/', views.MedalSubmissionAPIView.as_view(), name='api-submit-medal'),

    # Convener Views (legacy MCM/medal)
    path('convener/application/<int:application_id>/review/', views.ConvenerActionAPIView.as_view(), name='api-convener-review'),

    # Scholarship Types
    path('types/', views.ScholarshipTypesAPIView.as_view(), name='api-scholarship-types'),

    # Scholarship Applications (full lifecycle)
    path('applications/', views.ScholarshipApplicationsAPIView.as_view(), name='api-scholarship-applications'),
    path('applications/<int:application_id>/approve/', views.ScholarshipApplicationApproveAPIView.as_view(), name='api-scholarship-application-approve'),

    # General Awards Management
    path('awards/', views.AwardsManagementAPIView.as_view(), name='api-awards-management'),
    path('awards/<int:award_id>/', views.AwardDetailAPIView.as_view(), name='api-award-detail'),

    # Merit Lists
    path('merit-list/', views.MeritListAPIView.as_view(), name='api-merit-list-all'),
    path('merit-list/<str:batch_id>/', views.MeritListAPIView.as_view(), name='api-merit-list'),
    path('generate-merit-list/', views.GenerateMeritListAPIView.as_view(), name='api-generate-merit-list'),
    path('convenor/mcm-merit-list/', views.ConvenorMcmMeritListAPIView.as_view(), name='api-convenor-mcm-merit-list'),

    # Eligibility and Statistics
    path('eligible-students/<int:scholarship_id>/', views.EligibleStudentsAPIView.as_view(), name='api-eligible-students'),
    path('check-eligibility/', views.StudentEligibilityCheckAPIView.as_view(), name='api-check-eligibility'),
    path('statistics/batch/', views.BatchStatisticsAPIView.as_view(), name='api-batch-statistics'),
    path('mcm-applications/', views.McmApplicationViewSet.as_view({'get': 'list', 'post': 'create'}), name='api-mcm-applications'),
    path('mcm-applications/<int:pk>/', views.McmApplicationViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update'}), name='api-mcm-application-detail'),
    path('single-parent-applications/', views.SingleParentApplicationViewSet.as_view({'get': 'list', 'post': 'create'}), name='api-single-parent-applications'),
    path('single-parent-applications/<int:pk>/', views.SingleParentApplicationViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update'}), name='api-single-parent-application-detail'),
]


