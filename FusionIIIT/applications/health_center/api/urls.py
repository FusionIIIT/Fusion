"""
Health Center API URL Configuration
====================================
API routing for PHC module endpoints.

Routes registered under:
  /api/phc/...

Patient routes    → /api/phc/patient/...
Staff routes      → /api/phc/staff/...
"""

from django.urls import path
from .views import (
    DoctorAvailabilityView,
    AppointmentView,
    MedicalHistoryView,
    ReimbursementClaimView,
    ReimbursementView,
    CompounderReimbursementView,
    CompounderReimbursementWorkflowView,
    AccountsReimbursementApprovalView,
    AuditorReimbursementView,
    AuditorPingView,
    AuditorDebugView,
    ClaimDocumentUploadView,
    HealthProfileView,
    StaffClaimProcessingView,
    InventoryView,
    LowStockAlertsView,
    DashboardView,
    CompounderDoctorView,
    CompounderDoctorScheduleView,
    PatientScheduleView,
    CompounderAttendanceView,
    CompounderMedicineView,
    CompounderStockView,
    CompounderExpiryView,
    CompounderPrescriptionView,
    CompounderConsultationView,
    CompounderConsultationFormView,
    CompounderUserView,
    PatientPrescriptionView,
    PatientComplaintView,
    CompounderComplaintView,
    CompounderHospitalAdmitView,
    CompounderAmbulanceView,
    CompounderAmbulanceLogView,
    CompounderInventoryRequisitionView,
    AnnouncementView,
    SystemReportView,
    # AuthorityInventoryRequisitionView,  # TODO: Uncomment when approving authority module is integrated
)

app_name = 'phc_api'

urlpatterns = [
    # ── PATIENT: Doctor Availability ──────────────────────────────
    path('patient/doctor-availability/', DoctorAvailabilityView.as_view(), name='doctor-availability'),
    path('patient/doctor-availability/<int:doctor_id>/', DoctorAvailabilityView.as_view(), name='doctor-detail'),
    
    path('patient/appointments/', AppointmentView.as_view(), name='appointments-list'),
    path('patient/appointments/<int:pk>/', AppointmentView.as_view(), name='appointment-detail'),
    
    # ── PATIENT: Doctor Schedules (Public Read-Only) ────────────
    path('schedule/', PatientScheduleView.as_view(), name='patient-schedule-list'),
    path('schedule/<int:doctor_id>/', PatientScheduleView.as_view(), name='patient-schedule-doctor'),
    
    # ── PATIENT: Medical Records ──────────────────────────────────────
    path('patient/medical-history/', MedicalHistoryView.as_view(), name='medical-history'),
    
    path('patient/health-profile/', HealthProfileView.as_view(), name='health-profile'),
    
    # ── PATIENT: Reimbursement ───────────────────────────────────────
    path('patient/reimbursement-claims/', ReimbursementClaimView.as_view(), name='claims-list'),
    path('patient/reimbursement-claims/<int:pk>/', ReimbursementClaimView.as_view(), name='claim-detail'),
    path('patient/reimbursement-claims/<int:claim_id>/documents/', 
         ClaimDocumentUploadView.as_view(), name='claim-document-upload'),
        # ── TASK 17: EMPLOYEE REIMBURSEMENT ENDPOINTS ──────────────────────
    path('reimbursement/', ReimbursementView.as_view(), name='reimbursement-list'),
    path('reimbursement/<int:claim_id>/', ReimbursementView.as_view(), name='reimbursement-detail'),
    
    # ── COMPOUNDER REIMBURSEMENT VIEW (ADMIN ACCESS) ──────────────────
    path('compounder/reimbursement/', CompounderReimbursementView.as_view(), name='compounder-reimbursement-list'),
    path('compounder/reimbursement/<int:claim_id>/', CompounderReimbursementView.as_view(), name='compounder-reimbursement-detail'),
    
    # ── TASK 18: REIMBURSEMENT WORKFLOW ENDPOINTS ─────────────────────
    path('compounder/reimbursement/<int:claim_id>/forward/', CompounderReimbursementWorkflowView.as_view(), name='compounder-reimbursement-forward'),
    path('accounts/reimbursement/<int:claim_id>/approve/', AccountsReimbursementApprovalView.as_view(), name='accounts-reimbursement-approve'),
    path('accounts/reimbursement/<int:claim_id>/reject/', AccountsReimbursementApprovalView.as_view(), name='accounts-reimbursement-reject'),
    
    # ── AUDITOR: GET REIMBURSEMENT CLAIMS ─────────────────────────────
    path('auditor/ping/', AuditorPingView.as_view(), name='auditor-ping'),
    path('auditor/debug/', AuditorDebugView.as_view(), name='auditor-debug'),
    path('auditor/reimbursement-claims/', AuditorReimbursementView.as_view(), name='auditor-reimbursement-list'),
    path('auditor/reimbursement-claims/<int:claim_id>/', AuditorReimbursementView.as_view(), name='auditor-reimbursement-detail'),
    path('auditor/reimbursement-claims/<int:claim_id>/approve/', AuditorReimbursementView.as_view(), name='auditor-reimbursement-approve'),
    path('auditor/reimbursement-claims/<int:claim_id>/reject/', AuditorReimbursementView.as_view(), name='auditor-reimbursement-reject'),
    
        # ── DASHBOARD ─────────────────────────────────────────────────────
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    
    # ── STAFF: Claims Processing ──────────────────────────────────────
    path('staff/claims/', StaffClaimProcessingView.as_view(), name='staff-claims'),
    path('staff/claims/<int:claim_id>/process/', StaffClaimProcessingView.as_view(), name='staff-claim-process'),
    
    # ── STAFF: Inventory ──────────────────────────────────────────────
    path('staff/inventory/', InventoryView.as_view(), name='inventory-list'),
    path('staff/inventory/update/', InventoryView.as_view(), name='inventory-update'),
    path('staff/low-stock-alerts/', LowStockAlertsView.as_view(), name='low-stock-alerts'),
    
    # ── COMPOUNDER: Doctor Management ──────────────────────────────
    path('compounder/doctors/', CompounderDoctorView.as_view(), name='compounder-doctors'),
    path('compounder/doctors/<int:doctor_id>/', CompounderDoctorView.as_view(), name='compounder-doctor-detail'),
    
    # ── COMPOUNDER: Doctor Schedule ────────────────────────────────
    path('compounder/schedule/', CompounderDoctorScheduleView.as_view(), name='compounder-schedule-list'),
    path('compounder/schedule/<int:schedule_id>/', CompounderDoctorScheduleView.as_view(), name='compounder-schedule-detail'),
    
    # ── COMPOUNDER: Doctor Attendance ──────────────────────────────
    path('compounder/attendance/', CompounderAttendanceView.as_view(), name='compounder-attendance-list'),
    path('compounder/attendance/<int:attendance_id>/', CompounderAttendanceView.as_view(), name='compounder-attendance-detail'),
        # ── COMPOUNDER: Medicine List (for stock selection dropdown) ──
    path('compounder/medicine/', CompounderMedicineView.as_view(), name='compounder-medicine-list'),
        # ── COMPOUNDER: Stock Management ────────────────────────────────
    path('compounder/stock/', CompounderStockView.as_view(), name='compounder-stock-list'),
    path('compounder/stock/<int:stock_id>/', CompounderStockView.as_view(), name='compounder-stock-detail'),
    
    # ── COMPOUNDER: Expiry Batch Management ─────────────────────────
    path('compounder/expiry/', CompounderExpiryView.as_view(), name='compounder-expiry-list'),
    path('compounder/expiry/<int:expiry_id>/', CompounderExpiryView.as_view(), name='compounder-expiry-detail'),
    path('compounder/expiry/<int:expiry_id>/return/', CompounderExpiryView.as_view(), name='compounder-expiry-return'),
    
    # ── COMPOUNDER: Prescription Management ─────────────────────────
    path('compounder/prescription/', CompounderPrescriptionView.as_view(), name='compounder-prescription-list'),
    path('compounder/prescription/<int:prescription_id>/', CompounderPrescriptionView.as_view(), name='compounder-prescription-detail'),
    
    # ── COMPOUNDER: Consultation Selection ──────────────────────────
    path('compounder/consultations/', CompounderConsultationView.as_view(), name='compounder-consultations-list'),
    path('compounder/consultation/', CompounderConsultationFormView.as_view(), name='compounder-consultation-create'),
    path('compounder/consultation/<int:consultation_id>/', CompounderConsultationFormView.as_view(), name='compounder-consultation-delete'),
    
    # ── COMPOUNDER: User Selection ─────────────────────────────────
    path('compounder/users/', CompounderUserView.as_view(), name='compounder-users-list'),
    
    # ── PATIENT: Prescription Read-Only ────────────────────────────────
    path('patient/prescriptions/', PatientPrescriptionView.as_view(), name='patient-prescriptions-list'),
    path('patient/prescription/<int:prescription_id>/', PatientPrescriptionView.as_view(), name='patient-prescription-detail'),
    
    # ── PATIENT: Complaint Management ──────────────────────────────────
    path('complaint/', PatientComplaintView.as_view(), name='patient-complaint-list'),
    path('complaint/<int:complaint_id>/', PatientComplaintView.as_view(), name='patient-complaint-detail'),
    
    # ── COMPOUNDER: Complaint Management ────────────────────────────
    path('compounder/complaint/', CompounderComplaintView.as_view(), name='compounder-complaint-list'),
    path('compounder/complaint/<int:complaint_id>/', CompounderComplaintView.as_view(), name='compounder-complaint-detail'),
    path('compounder/complaint/<int:complaint_id>/respond/', CompounderComplaintView.as_view(), name='compounder-complaint-respond'),
    
    # ── COMPOUNDER: Hospital Admission Management ──────────────────
    path('compounder/hospital-admit/', CompounderHospitalAdmitView.as_view(), name='compounder-hospital-list'),
    path('compounder/hospital-admit/<int:admission_id>/', CompounderHospitalAdmitView.as_view(), name='compounder-hospital-detail'),
    path('compounder/hospital-admit/<int:admission_id>/discharge/', CompounderHospitalAdmitView.as_view(), name='compounder-hospital-discharge'),
    
    # ── COMPOUNDER: Ambulance Fleet Management ────────────────────
    path('compounder/ambulance/', CompounderAmbulanceView.as_view(), name='compounder-ambulance-list'),
    path('compounder/ambulance/<int:ambulance_id>/', CompounderAmbulanceView.as_view(), name='compounder-ambulance-detail'),

    # ── COMPOUNDER: PHC-UC-11 — Ambulance Usage Log ───────────────
    # Records every dispatch event (patient_name, destination, date, time).
    # Enforces PHC-BR-09 audit trail via create_ambulance_log() service.
    path('compounder/ambulance-log/', CompounderAmbulanceLogView.as_view(), name='compounder-ambulance-log-list'),
    path('compounder/ambulance-log/<int:log_id>/', CompounderAmbulanceLogView.as_view(), name='compounder-ambulance-log-detail'),
    
    # ── COMPOUNDER: Inventory Requisitions ──────────────────────────
    path('compounder/requisition/', CompounderInventoryRequisitionView.as_view(), name='compounder-requisition-list'),
    path('compounder/requisition/<int:pk>/', CompounderInventoryRequisitionView.as_view(), name='compounder-requisition-detail'),
    # PHC-UC-14: Mark Requisition as Fulfilled
    path('compounder/requisition/<int:pk>/fulfill/', CompounderInventoryRequisitionView.as_view(), name='compounder-requisition-fulfill'),
    
    # ── PHC-UC-16: Approve Inventory Requisition (AUTHORITY — COMMENTED OUT) ──
    #
    # STATUS: IMPLEMENTED — COMMENTED OUT (Cross-module boundary pending)
    #
    # These routes are ready to activate once the Approving Authority role is
    # defined in the institute-wide globals/admin module.
    #
    # WHEN INTEGRATING:
    #   1. Uncomment AuthorityInventoryRequisitionView in views.py.
    #   2. Update _is_authority() in that class with the correct role check.
    #   3. Uncomment PHC-BR-11 notification blocks in services.py.
    #   4. Uncomment the three paths below.
    #
    # path('authority/requisition/', AuthorityInventoryRequisitionView.as_view(), name='authority-requisition-list'),
    # path('authority/requisition/<int:pk>/', AuthorityInventoryRequisitionView.as_view(), name='authority-requisition-detail'),
    # path('authority/requisition/<int:pk>/<str:action>/', AuthorityInventoryRequisitionView.as_view(), name='authority-requisition-action'),

    # ── PHC-UC-12: Health Announcements (all authenticated users can read) ──
    # PHC-UC-17: Portal notification broadcast wired inside service layer.
    path('announcements/', AnnouncementView.as_view(), name='announcements-list'),
    path('announcements/<int:announcement_id>/', AnnouncementView.as_view(), name='announcements-detail'),

    # ── PHC-UC-13: System Reports (Compounder only) ──
    path('compounder/reports/', SystemReportView.as_view(), name='system-reports'),
]
