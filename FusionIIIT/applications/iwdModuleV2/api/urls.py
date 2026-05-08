from django.urls import path
from . import views

urlpatterns = [
	path('fetch-designations/', views.fetch_designations, name='fetch_designations'),
	path('create-request/', views.create_request, name='create_request'),
	path('create-proposal/', views.create_proposal, name='create_proposal'),
	path('created-requests/', views.created_requests, name='created_requests'),
	path('view-file/', views.view_file, name='view_file'),
	path('dean-pending-requests/', views.dean_pending_requests, name='dean_pending_requests'),
	path('dean-processed-requests/', views.dean_processed_requests, name='dean_processed_requests'),
	path('handle-director-approval/', views.handle_director_approval, name='handle_director_approval'),
	path('forward-request/', views.forward_request, name='handle_engineer_process_requests'),
	path('handle-dean-process-request/', views.handle_dean_process_request, name='handleDeanProcessRequests'),
	path('rejected-requests-view/', views.rejected_requests, name='rejectedRequests'),
	path('handle-update-requests/', views.handle_update_requests, name='handleUpdateRequests'),
	path('director-approved-requests/', views.director_approved_requests, name='issueWorkOrder'),
	path('issue-work-order/', views.issue_work_order, name='workOrder'),
	path('requests-in-progress/', views.requests_in_progress, name='requestsInProgress'),
	path('work-under-progress/', views.work_under_progress, name='workUnderProgress'),
	path('work-completed/', views.work_completed, name='workCompleted'),
	path('view-budget/', views.view_budget, name='viewBudget'),
	path('add-budget/', views.add_budget, name='addBudget'),
	path('edit-budget/', views.edit_budget, name='editBudget'),
	path('requests-status/', views.requests_status, name='requestsStatus'),
	path('audit-document-view/', views.audit_document_view, name='auditDocumentView'),
	path('audit-document/', views.handle_audit_document, name='auditDocument'),
	path('get-proposals/', views.get_proposals, name='getProposals'),
	path('get-items/', views.get_items, name='getItems'),
	path('handle-admin-approval/', views.handle_admin_approval, name='handleAdminApproval'),

	path('issued-work/', views.get_issued_work, name='activeWork'),
	path('add-vendor/', views.add_vendor, name="addVendor"),
	path('get-work/', views.get_work, name='getWork'),
	path('get-vendors/', views.get_vendors, name='getVendors'),

	path('handle-process-bills/', views.handle_process_bills, name='handleProcessedBills'),

	path('engineer-processed-requests/', views.engineer_processed_requests, name='engineerProcessedRequests'),
	path('handle-bill-generated-requests/', views.handleBillGeneratedRequests, name='handleBillGeneratedRequests'),
	path('generated-bills-view/', views.generatedBillsView, name='generatedBillsView'),
	path('generate-bill-pdf/', views.generate_bill_pdf, name='generateBillPdf'),
	path('settle-bills-view/', views.settle_bills_view, name='settleBillsView'),
	path('handle-settle-bill-request/', views.handle_settle_bill_requests, name='handleSettleBillRequest'),

	# ===== NEWLY IMPLEMENTED ENDPOINTS (UC-29, UC-30, UC-31) =====
	path('sla-dashboard/', views.sla_dashboard, name='slaDashboard'),
	
	# Inventory Management (UC-30)
	path('inventory-items/', views.list_inventory_items, name='listInventoryItems'),
	path('inventory-transactions/', views.inventory_transactions, name='inventoryTransactions'),
	path('issue-materials/', views.issue_materials, name='issueMaterials'),
	path('receive-materials/', views.receive_materials, name='receiveMaterials'),
	
	# Feedback & Reopening (UC-31)
	path('feedback-history/', views.feedback_history, name='feedbackHistory'),
	path('submit-feedback/', views.submit_feedback, name='submitFeedback'),
	path('reopen-request/', views.reopen_request, name='reopenRequest'),

	# SLA Monitoring extras
	path('sla-escalations/', views.sla_escalations, name='slaEscalations'),
]
