#urls.py

# complaint/urls.py
from django.urls import path
from .views import (
    CheckUser,
    UserComplaintView,
    CaretakerFeedbackView,
    SubmitFeedbackView,
    ComplaintDetailView,
)
from .views import (
    CaretakerLodgeView,
    CaretakerView,
    FeedbackCareView,
    ResolvePendingView,
    ComplaintDetailView,
    SearchComplaintView,
    SubmitFeedbackCaretakerView,
)
from .views import (
    ServiceProviderLodgeView,
    ServiceProviderView,
    FeedbackSuperView,
    CaretakerIdKnowMoreView,
    ServiceProviderComplaintDetailView,
    ServiceProviderResolvePendingView,
    ServiceProviderSubmitFeedbackView,
)

from django.urls import path
from .views import (
    RemoveWorkerView,
    ForwardCompaintView,
    DeleteComplaintView,
    ChangeStatusView,
    ChangeStatusSuperView,
    GenerateReportView,
    # Other imported views
)



app_name = "complaint"

urlpatterns = [
    path("", CheckUser.as_view(), name="complaint"),
    path("user/", UserComplaintView.as_view(), name="user-complaints"),
    path("user/caretakerfb/", CaretakerFeedbackView.as_view(), name="caretaker-feedback"),
    path("user/<int:complaint_id>/", SubmitFeedbackView.as_view(), name="submit-feedback"),
    path("user/detail/<int:detailcomp_id1>/", ComplaintDetailView.as_view(), name="detail"),
    # Other URL patterns
    path('caretaker/lodge/', CaretakerLodgeView.as_view()),  # Converted to DRF
    path('caretaker/', CaretakerView.as_view(), name='caretaker'),  # Converted to DRF
    path('caretaker/feedback/<int:feedcomp_id>/', FeedbackCareView.as_view()),  # Converted to DRF
    path('caretaker/pending/<int:cid>/', ResolvePendingView.as_view()),  # Converted to DRF
    path('caretaker/detail2/<int:detailcomp_id1>/', ComplaintDetailView.as_view()),  # Converted to DRF
    path('caretaker/search_complaint', SearchComplaintView.as_view()),  # Converted to DRF
    path('caretaker/<int:complaint_id>/feedback/', SubmitFeedbackCaretakerView.as_view()),  # Converted to DRF
        # ServiceProvider URLs
    path('service_provider/lodge/', ServiceProviderLodgeView.as_view()),
    path('service_provider/', ServiceProviderView.as_view()),
    path('service_provider/feedback/<int:feedcomp_id>/', FeedbackSuperView.as_view()),
    path('service_provider/caretaker_id_know_more/<int:caretaker_id>/', CaretakerIdKnowMoreView.as_view()),
    # The following URL is commented out as per the original code
    # path('service_provider/caretaker_id_know_more/<int:caretaker_id>/complaint_reassign_super/<int:iid>/', views.complaint_reassign_super, name='complaint_reassign_super'),
    path('service_provider/detail/<int:detailcomp_id1>/', ServiceProviderComplaintDetailView.as_view(), name='detail3'),
    path('service_provider/pending/<int:cid>/', ServiceProviderResolvePendingView.as_view()),
    path('service_provider/<int:complaint_id>/', ServiceProviderSubmitFeedbackView.as_view()),
    # CRUD task URLs
    path('caretaker/worker_id_know_more/<int:work_id>/removew/', RemoveWorkerView.as_view()),
    path('caretaker/<int:comp_id1>/', ForwardCompaintView.as_view(), name='assign_worker'),
    path('caretaker/deletecomplaint/<int:comp_id1>/', DeleteComplaintView.as_view()),
    path('caretaker/<int:complaint_id>/<str:status>/', ChangeStatusView.as_view()),
    path('service_provider/<int:complaint_id>/<str:status>/', ChangeStatusSuperView.as_view()),

    path('generate-report/', GenerateReportView.as_view(), name='generate-report-api'),
]