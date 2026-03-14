from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

# Main resources
router.register("requests", views.RequestViewSet, basename="requests")
router.register("budgets", views.BudgetViewSet, basename="budgets")
router.register("vendors", views.VendorViewSet, basename="vendors")
router.register("work", views.WorkViewSet, basename="work")

urlpatterns = router.urls + [

    # Request workflows
    path("requests/<int:pk>/forward/", views.forward_request, name="forward-request"),
    path("requests/<int:pk>/director-approval/", views.handle_director_approval, name="director-approval"),
    path("requests/<int:pk>/admin-approval/", views.handle_admin_approval, name="admin-approval"),
    path("requests/<int:pk>/dean-process/", views.handle_dean_process_request, name="dean-process"),

    # Status endpoints
    path("requests-status/", views.requests_status, name="requests-status"),
    path("rejected-requests/", views.rejected_requests, name="rejected-requests"),

    # Work progress
    path("work/issued/", views.get_issued_work, name="issued-work"),
    path("work/progress/", views.work_under_progress, name="work-under-progress"),
    path("work/completed/", views.work_completed, name="work-completed"),

    # Vendor & proposal endpoints
    path("proposals/", views.get_proposals, name="proposals"),
    path("items/", views.get_items, name="items"),

    # Budget APIs
    path("budget/add/", views.add_budget, name="add-budget"),
    path("budget/edit/", views.edit_budget, name="edit-budget"),
    path("budget/view/", views.view_budget, name="view-budget"),

    # Audit APIs
    path("audit/", views.handle_audit_document, name="audit-document"),
    path("audit/view/", views.audit_document_view, name="audit-document-view"),

    # Billing APIs
    path("bills/process/", views.handle_process_bills, name="process-bills"),
    path("bills/generated/", views.generatedBillsView, name="generated-bills"),
    path("bills/settle/", views.settle_bills_view, name="settle-bills"),
    path("bills/settle-request/", views.handle_settle_bill_requests, name="settle-bills-request"),

]