from django.urls import path
from . import views
# TODO: handle-update-request should be available to the author before any review... new feature 
# TODO: update-rejected-request should be used to updated the request data for rejected requests
urlpatterns = [
    
    # fully implemented

    # path('dashboard/', views.dashboard, name='dashboard'),
    path('fetch-designations/', views.fetch_designations, name='fetch_designations'),
    path('create-request/', views.create_request, name='create_request'),
    path('created-requests/', views.created_requests, name='created_requests'),
    path('view-file/', views.view_file, name='viewFile'),
    path('dean-processed-requests/', views.dean_processed_requests, name='deanProcessedRequests'),
    path('handle-director-approval-requests/', views.handle_director_approval, name='handle_director_approval'),
    path('rejected-requests-view/', views.rejected_requests, name='rejectedRequests'),
    path('handle-update-requests/', views.handle_update_requests, name='handleUpdateRequests'),
    path('director-approved-requests/', views.director_approved_requests, name='issueWorkOrder'),
    path('issue-work-order/', views.issue_work_order, name='workOrder'),
    path('requests-in-progress/', views.requests_in_progress, name='requestsInProgress'),
    path('work-completed/', views.work_completed, name='workCompleted'),
    path('view-budget/', views.view_budget, name='viewBudget'),
    path('add-budget/', views.add_budget, name='addBudget'),
    path('edit-budget/', views.edit_budget, name='editBudget'),
    path('requests-status/', views.requests_status, name='requestsStatus'),
    
    # partially integrated on frontend

    path('engineer-processed-requests/', views.engineer_processed_requests, name='engineerProcessedRequests'),
    path('handle-engineer-process-requests/', views.handleEngineerProcessRequests, name='handleEngineerProcessRequests'),
    path('handle-dean-process-requests/', views.handle_dean_process_requests, name='handleDeanProcessRequests'),
    path('update-rejected-requests/', views.updateRejectedRequests, name='updateRejectedRequests'),
    path('get-all-requests/', views.getAllRequests, name='requestsStatus'),
    path('fetch-request/', views.fetchRequest, name='fetchRequest'),
    path('generate-final-bill/', views.generateFinalBill, name='generateFinalBill'),
    path('handle-bill-generated-requests/', views.handleBillGeneratedRequests, name='handleBillGeneratedRequests'),
    path('generated-bills-view/', views.generatedBillsView, name='generatedBillsView'),
    path('handle-processed-bills/', views.handleProcessedBills, name='handleProcessedBills'),
    path('audit-document-view/', views.audit_document_view, name='auditDocumentView'),
    path('audit-document/', views.audit_document, name='auditDocument'),
    path('settle-bills-view/', views.settle_bills_view, name='settleBillsView'),
    path('handle-settle-bill-request/', views.handle_settle_bill_requests, name='handleSettleBillRequest'),

    # Unsure about use or depricated

    path('work-order-form/', views.workOrderForm, name='workOrderForm'),
    path('work-order-form-view/', views.workOrderFormView, name='workOrderFormView'),
    path('page1-1/', views.page1_1, name='page1_1'),
    path('aes-form/', views.AESForm, name='AESForm'),
    path('page2-1/', views.page2_1, name='page2_1'),
    path('corrigendum-input/', views.corrigendumInput, name='corrigendumInput'),
    path('addendum-input/', views.addendumInput, name='addendumInput'),
    path('pre-bid-form/', views.PreBidForm, name='PreBidForm'),
    path('no-of-entries-technical-bid/', views.noOfEntriesTechnicalBid, name='noOfEntriesTechnicalBid'),
    path('technical-bid-form/', views.TechnicalBidForm, name='TechnicalBidForm'),
    path('no-of-entries-financial-bid/', views.noOfEntriesFinancialBid, name='noOfEntriesFinancialBid'),
    path('letter-of-intent/', views.letterOfIntent, name='letterOfIntent'),
    path('agreement-input/', views.AgreementInput, name='AgreementInput'),
    path('milestones-form/', views.milestonesForm, name='milestonesForm'),
    path('page3-1/', views.page3_1, name='page3_1'),
    path('extension-of-time-form/', views.ExtensionOfTimeForm, name='ExtensionOfTimeForm'),
    path('page1-view/', views.page1View, name='page1View'),
    path('page2-view/', views.page2View, name='page2View'),
    path('aes-view/', views.AESView, name='AESView'),
    path('financial-bid-view/', views.financialBidView, name='financialBidView'),
    path('technical-bid-view/', views.technicalBidView, name='technicalBidView'),
    path('pre-bid-details-view/', views.preBidDetailsView, name='preBidDetailsView'),
    path('corrigendum-view/', views.corrigendumView, name='corrigendumView'),
    path('addendum-view/', views.addendumView, name='addendumView'),
    path('letter-of-intent-view/', views.letterOfIntentView, name='letterOfIntentView'),
    path('agreement-view/', views.agreementView, name='agreementView'),
    path('milestone-view/', views.milestoneView, name='milestoneView'),
    path('page3-view/', views.page3View, name='page3View'),
    path('extension-form-view/', views.extensionFormView, name='extensionFormView'),
]

