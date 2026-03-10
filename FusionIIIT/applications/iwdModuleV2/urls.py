from django.urls import path, include
from . import views

app_name = "iwdModuleV2"

urlpatterns = [

    # Dashboard
    path("", views.dashboard, name="dashboard"),

    # API Versioning
    path("api/v1/iwd/", include("applications.iwdModuleV2.api.urls")),

    # Web views
    path("requests/", views.requestsView, name="requests"),
    path("created-requests/", views.createdRequests, name="created-requests"),

    path("engineer-processed-requests/", views.engineerProcessedRequests, name="engineer-processed-requests"),
    path("dean-processed-requests/", views.deanProcessedRequests, name="dean-processed-requests"),

    path("rejected-requests/", views.rejectedRequests, name="rejected-requests"),

    path("requests-status/", views.requestsStatus, name="requests-status"),

    path("work-orders/", views.workOrder, name="work-orders"),
    path("issue-work-order/", views.issueWorkOrder, name="issue-work-order"),

    path("requests-in-progress/", views.requestsInProgess, name="requests-in-progress"),
    path("work-completed/", views.workCompleted, name="work-completed"),

    path("budget/", views.budget, name="budget"),
    path("budget/view/", views.viewBudget, name="view-budget"),
    path("budget/add/", views.addBudget, name="add-budget"),
    path("budget/edit/", views.editBudget, name="edit-budget"),

    path("files/<int:id>/<str:url>/", views.view_file, name="view-file"),
]