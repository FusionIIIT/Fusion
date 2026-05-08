from django.urls import include, path

from . import views

app_name = "iwdModuleV2"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("", views.dashboard, name="IWD Dashboard"),

    path("api/", include("applications.iwdModuleV2.api.urls")),

    path("fetch-designations/", views.fetchDesignations, name="fetch-designations"),
    path("fetch-designations/", views.fetchDesignations, name="Fetch-Designations"),

    path("requests/", views.requestsView, name="requests"),
    path("requests/", views.requestsView, name="Requests view"),

    path("created-requests/", views.createdRequests, name="created-requests"),
    path("created-requests/", views.createdRequests, name="Created Requests view"),

    path("view-file/<int:id>/<str:url>/", views.view_file, name="view-file"),
    path("view_file/<int:id>/<str:url>/", views.view_file, name="View-File"),

    path("handle-engineer-process-requests/", views.handleEngineerProcessRequests, name="handle-engineer-process-requests"),
    path("handle-engineer-process-requests/", views.handleEngineerProcessRequests, name="Handle-Engineer-Process-Requests"),

    path("engineer-processed-requests/", views.engineerProcessedRequests, name="engineer-processed-requests"),
    path("engineer-processed-requests/", views.engineerProcessedRequests, name="Engineer-Processed-Requests view"),

    path("handle-dean-process-requests/", views.handleDeanProcessRequests, name="handle-dean-process-requests"),
    path("handle-dean-process-requests/", views.handleDeanProcessRequests, name="Handle-Dean-Process-Requests"),

    path("dean-processed-requests/", views.deanProcessedRequests, name="dean-processed-requests"),
    path("dean-processed-requests/", views.deanProcessedRequests, name="Dean-Processed-Requests view"),

    path("handle-director-approval-requests/", views.handleDirectorApprovalRequests, name="handle-director-approval-requests"),
    path("handle-director-approval-requests/", views.handleDirectorApprovalRequests, name="Handle-Director-Approval-Requests"),

    path("rejected-requests/", views.rejectedRequests, name="rejected-requests"),
    path("rejected-requests/", views.rejectedRequests, name="Rejected Requests view"),

    path("update-rejected-requests/", views.updateRejectedRequests, name="update-rejected-requests"),
    path("update-rejected-requests/", views.updateRejectedRequests, name="Update-Rejected-Requests"),

    path("handle-update-requests/", views.handleUpdateRequests, name="handle-update-requests"),
    path("handle-update-requests/", views.handleUpdateRequests, name="Handle-Update-Requests"),

    path("requests-status/", views.requestsStatus, name="requests-status"),
    path("requests-status/", views.requestsStatus, name="Requests-Status"),

    path("fetch-request/", views.fetchRequest, name="fetch-request"),
    path("fetch-request/", views.fetchRequest, name="Fetch-Request"),

    path("work-orders/", views.workOrder, name="work-orders"),
    path("work-orders/", views.workOrder, name="Work Order"),

    path("issue-work-order/", views.issueWorkOrder, name="issue-work-order"),
    path("issue-work-order/", views.issueWorkOrder, name="Issue Work Order"),

    path("requests-in-progress/", views.requestsInProgess, name="requests-in-progress"),
    path("requests-in-progress/", views.requestsInProgess, name="Requests In Progress"),

    path("work-completed/", views.workCompleted, name="work-completed"),
    path("work-completed/", views.workCompleted, name="Work Completed"),

    path("handle-bill-generated-requests/", views.handleBillGeneratedRequests, name="handle-bill-generated-requests"),
    path("handle-bill-generated-requests/", views.handleBillGeneratedRequests, name="Handle-Bill-Generated-Requests"),

    path("generated-bills/", views.generatedBillsView, name="generated-bills-view"),
    path("generated-bills/", views.generatedBillsView, name="Generated-Bills-View"),

    path("handle-processed-bills/", views.handleProcessedBills, name="handle-processed-bills"),
    path("handle-processed-bills/", views.handleProcessedBills, name="Handle-Processed-Bills"),

    path("audit-document/", views.auditDocument, name="audit-document"),
    path("audit-document/", views.auditDocument, name="Audit-Document"),

    path("audit-document-view/", views.auditDocumentView, name="audit-document-view"),
    path("audit-document-view/", views.auditDocumentView, name="Audit-Document-View"),

    path("settle-bills/", views.handleSettleBillRequests, name="handle-settle-bill-requests"),
    path("settle-bills/", views.handleSettleBillRequests, name="Handle-Settle-Bill-Requests"),

    path("settle-bills-view/", views.settleBillsView, name="settle-bills-view"),
    path("settle-bills-view/", views.settleBillsView, name="Settle-Bills-View"),

    path("budget/", views.budget, name="budget"),
    path("budget/", views.budget, name="Budget"),

    path("budget/view/", views.viewBudget, name="view-budget"),
    path("budget/view/", views.viewBudget, name="View-Budget"),

    path("budget/add/", views.addBudget, name="add-budget"),
    path("budget/add/", views.addBudget, name="Add-Budget"),

    path("budget/edit/", views.editBudget, name="edit-budget"),
    path("budget/edit/", views.editBudget, name="Edit-Budget"),
    path("budget/edit/", views.editBudget, name="Edit-Budget-View"),
]
