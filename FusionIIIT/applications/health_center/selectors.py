"""
Health Center Selectors
=======================
Database query layer for the PHC module.

Responsibility:
  - Read-only database queries
  - Uses .objects, filters, annotations
  - No write operations
  - Clean, reusable query methods

Architecture: Selector Pattern
"""

from datetime import date, timedelta
from django.db.models import Q, F, Count, Sum, Prefetch
from django.utils import timezone

from .models import (
    Doctor, DoctorSchedule, DoctorAttendance, HealthProfile,
    Appointment, Consultation, Prescription, PrescribedMedicine,
    Medicine, Stock, Expiry, ComplaintV2, HospitalAdmit, AmbulanceRecordsV2,
    ReimbursementClaim, ClaimDocument, InventoryRequisition, LowStockAlert,
    AuditLog, AttendanceStatusChoices, InventoryStock,  # InventoryStock is proxy for Stock
)


# ===========================================================================
# ── DOCTOR AVAILABILITY SELECTORS - PHC-UC-01, PHC-BR-01 ───────────────
# ===========================================================================

# ===========================================================================
# ── CORE DOCTOR GETTERS ────────────────────────────────────────────────
# ===========================================================================

def get_doctor(doctor_id):
    """
    Get a single doctor by ID. Raises Doctor.DoesNotExist if not found.
    Task 19: Core getter with select_related for related data
    """
    return Doctor.objects.select_related(
        # Add any FKs if doctor has them
    ).get(id=doctor_id)


def get_all_doctors():
    """
    Get all active doctors.
    Task 19: Returns queryset of all doctors
    """
    return Doctor.objects.filter(is_active=True).order_by('doctor_name')


def get_doctor_schedule(doctor_id):
    """
    Get doctor's weekly schedule (master schedule).
    PHC-UC-01: View Doctor Schedule & Availability (part 1)
    """
    return DoctorSchedule.objects.filter(
        doctor_id=doctor_id,
        is_available=True,
    ).select_related('doctor').order_by('day_of_week')


def get_doctor_availability_for_today(doctor_id):
    """
    Get doctor's real-time availability status for today.
    PHC-UC-01: View Doctor Schedule & Availability (part 2 - real-time)
    PHC-BR-01: Overlays real-time status with master schedule
    """
    return DoctorAttendance.objects.filter(
        doctor_id=doctor_id,
        attendance_date=date.today(),
    ).select_related('doctor').first()


def get_all_schedules():
    """
    Get all doctor schedules.
    Task 19: Returns all schedules sorted by day and doctor
    """
    return DoctorSchedule.objects.select_related('doctor').order_by(
        'doctor__doctor_name', 'day_of_week'
    )


def get_schedule_by_id(schedule_id):
    """Get a single schedule entry by ID"""
    return DoctorSchedule.objects.select_related('doctor').filter(id=schedule_id).first()


def get_doctor_schedules(doctor_id):
    """
    Alternative name for get_doctor_schedule (Task 19 naming)
    Returns all schedules for a doctor
    """
    return get_doctor_schedule(doctor_id)


def get_all_doctors_with_availability():
    """
    Get all active doctors with their schedules and today's attendance.
    Returns: [Doctor with schedules and today's attendance status]
    PHC-UC-01: Patient browsing all doctor availability
    """
    doctors = Doctor.objects.filter(is_active=True).prefetch_related(
        Prefetch('schedules', queryset=DoctorSchedule.objects.filter(is_available=True))
    ).order_by('doctor_name')
    
    # Attach today's attendance for each doctor
    for doctor in doctors:
        doctor.todays_attendance = DoctorAttendance.objects.filter(
            doctor_id=doctor.id,
            attendance_date=date.today(),
        ).first()
    
    return doctors


def get_doctor_attendance(doctor_id, attendance_date=None):
    """
    Get doctor's attendance record for a specific date.
    If attendance_date is None, returns today's attendance.
    Task 19: Core getter for attendance data
    """
    if attendance_date is None:
        attendance_date = date.today()
    
    return DoctorAttendance.objects.filter(
        doctor_id=doctor_id,
        attendance_date=attendance_date,
    ).select_related('doctor').first()


def get_all_doctor_attendance(doctor_id):
    """
    Get all attendance records for a doctor.
    Task 19: Historical attendance tracking
    """
    return DoctorAttendance.objects.filter(
        doctor_id=doctor_id,
    ).select_related('doctor').order_by('-attendance_date')


def get_doctor_attendance_by_id(attendance_id):
    """Get a single attendance record by ID"""
    return DoctorAttendance.objects.select_related('doctor').filter(id=attendance_id).first()


# ===========================================================================
# ── APPOINTMENT SELECTORS ────────────────────────────────────────────────
# ===========================================================================

def get_appointment(appointment_id):
    """
    Get a single appointment by ID.
    Task 19: Core getter with select_related for doctor and patient
    """
    return Appointment.objects.select_related(
        'doctor', 'patient'
    ).filter(id=appointment_id).first()


def get_all_appointments(status=None):
    """
    Get all appointments, optionally filtered by status.
    Task 19: Returns queryset of all appointments
    """
    query = Appointment.objects.select_related('doctor', 'patient')
    
    if status:
        query = query.filter(status=status)
    
    return query.order_by('-appointment_date', '-appointment_time')


def get_patient_appointments(patient_id, status=None):
    """
    Get appointments for a patient, optionally filtered by status.
    """
    query = Appointment.objects.filter(patient_id=patient_id)
    
    if status:
        query = query.filter(status=status)
    
    return query.select_related('doctor').order_by('-appointment_date', '-appointment_time')


def get_future_appointments(patient_id):
    """Get upcoming appointments for a patient"""
    today = date.today()
    return Appointment.objects.filter(
        patient_id=patient_id,
        appointment_date__gte=today,
        status__in=['SCHEDULED', 'CHECKED_IN'],
    ).select_related('doctor').order_by('appointment_date', 'appointment_time')


def get_past_appointments(patient_id):
    """Get past completed appointments for a patient"""
    today = date.today()
    return Appointment.objects.filter(
        patient_id=patient_id,
        appointment_date__lt=today,
    ).select_related('doctor').order_by('-appointment_date', '-appointment_time')


# ===========================================================================
# ── MEDICAL HISTORY SELECTORS - PHC-UC-02, PHC-UC-03 ────────────────────
# ===========================================================================

def get_consultation(consultation_id):
    """
    Get a single consultation by ID with related data.
    Task 19: Core getter with select_related/prefetch_related
    """
    return Consultation.objects.select_related(
        'doctor', 'patient', 'appointment'
    ).prefetch_related(
        'prescription__prescribed_medicines__medicine'
    ).filter(id=consultation_id).first()


def get_all_consultations():
    """
    Get all consultations.
    Task 19: Returns queryset of all patient consultations
    """
    return Consultation.objects.select_related(
        'doctor', 'patient'
    ).order_by('-consultation_date')


def get_patient_medical_history(patient_id):
    """
    Get all medical records (consultations) for a patient.
    PHC-UC-02: View Medical History & Prescriptions
    Returns: List of consultations ordered by date
    """
    return Consultation.objects.filter(patient_id=patient_id).select_related(
        'doctor', 'patient'
    ).prefetch_related('prescription__prescribed_medicines').order_by('-consultation_date')


def get_patient_prescriptions(patient_id):
    """
    Get all prescriptions for a patient.
    PHC-UC-02: View Prescriptions
    """
    return Prescription.objects.filter(patient_id=patient_id).select_related(
        'doctor', 'consultation__appointment'
    ).prefetch_related('prescribed_medicines__medicine').order_by('-prescription_date')


def get_prescription_by_id(prescription_id):
    """
    Get a prescription by ID with all PrescribedMedicine nested (Task 19 naming).
    Returns prescription with medicine details for each prescribed item.
    """
    return Prescription.objects.filter(id=prescription_id).select_related(
        'doctor', 'patient', 'consultation'
    ).prefetch_related(
        'prescribed_medicines__medicine',
        'prescribed_medicines__expiry_used'
    ).first()


def get_prescription_detail(prescription_id):
    """Get detailed prescription with all medicines and instructions"""
    return get_prescription_by_id(prescription_id)


def get_patient_health_profile(patient_id):
    """Get patient's health profile (blood group, allergies, etc.)"""
    return HealthProfile.objects.filter(patient_id=patient_id).first()


# ===========================================================================
# ── REIMBURSEMENT CLAIM SELECTORS - PHC-UC-04, PHC-UC-05 ────────────────
# ===========================================================================

def get_patient_reimbursement_claims(patient_id):
    """
    Get all reimbursement claims submitted by an employee.
    PHC-UC-04: Apply for Reimbursement
    PHC-UC-05: Track Reimbursement Status
    """
    return ReimbursementClaim.objects.filter(patient_id=patient_id).select_related(
        'prescription__doctor', 'prescription__consultation'
    ).prefetch_related('documents').order_by('-submission_date')


def get_reimbursement_claim_detail(claim_id):
    """Get full details of a reimbursement claim with all documents"""
    return ReimbursementClaim.objects.filter(id=claim_id).select_related(
        'patient__user', 'prescription__doctor', 'prescription__consultation'
    ).prefetch_related('documents').first()


def get_claims_pending_review(role=None):
    """
    Get claims pending review/approval.
    Used by staff dashboard to show pending actions
    
    role: 'phc_staff', 'accounts', 'approving_authority'
    """
    from .models import ReimbursementStatusChoices
    
    if role == 'phc_staff':
        status_filter = ReimbursementStatusChoices.SUBMITTED
    elif role == 'accounts':
        status_filter = ReimbursementStatusChoices.ACCOUNTS_VERIFICATION
    elif role == 'approving_authority':
        status_filter = ReimbursementStatusChoices.SANCTION_REVIEW
    else:
        # Return all non-final statuses
        return ReimbursementClaim.objects.exclude(
            status__in=['REIMBURSED', 'REJECTED', 'WITHDRAWN']
        ).select_related('patient__user', 'prescription__doctor')
    
    return ReimbursementClaim.objects.filter(
        status=status_filter
    ).select_related('patient__user', 'prescription__doctor').order_by('-submission_date')


def get_claim_approval_history(claim_id):
    """
    Get audit trail of all approvals/actions on a claim.
    PHC-UC-05: Track Reimbursement Status
    """
    return AuditLog.objects.filter(
        entity_type='ReimbursementClaim',
        entity_id=claim_id,
    ).select_related('user').order_by('-timestamp')


# ===========================================================================
# ── INVENTORY SELECTORS - PHC-UC-11, PHC-UC-18 ───────────────────────────
# ===========================================================================

def get_all_medicines():
    """Get list of all medicines"""
    return Medicine.objects.all().order_by('medicine_name')


def get_medicine_detail(medicine_id):
    """Get medicine with current stock information"""
    medicine = Medicine.objects.get(id=medicine_id)
    medicine.current_stock = get_total_medicine_stock(medicine_id)
    return medicine


def get_stock_by_id(stock_id):
    """
    Get stock record by ID with related Expiry batches (Task 19).
    Returns stock with ALL expiry batches (active and returned).
    """
    return Stock.objects.filter(id=stock_id).prefetch_related(
        Prefetch('expiry_batches', queryset=Expiry.objects.order_by('expiry_date'))
    ).first()


def get_all_medicines_with_stock():
    """
    Get all medicines with their available stock quantities (Task 19).
    Returns medicines + total available quantities (non-expired, not returned).
    """
    medicines = Medicine.objects.prefetch_related(
        Prefetch(
            'stock__expiry_batches',
            queryset=Expiry.objects.filter(
                is_returned=False,
                expiry_date__gt=timezone.now().date(),
            ).order_by('expiry_date')
        )
    ).order_by('medicine_name')
    
    # Add available_qty to each medicine
    for medicine in medicines:
        medicine.available_qty = Expiry.objects.filter(
            stock__medicine=medicine,
            is_returned=False,
            expiry_date__gt=timezone.now().date(),
        ).aggregate(total=Sum('qty'))['total'] or 0
    
    return medicines


def get_expiry_batch(expiry_id):
    """Get a single expiry batch by ID with related stock & medicine."""
    return Expiry.objects.select_related('stock__medicine').filter(id=expiry_id).first()


def get_total_medicine_stock(medicine_id):
    """Get total current stock quantity for a medicine (FIFO method)"""
    total = Expiry.objects.filter(
        stock__medicine_id=medicine_id,
        is_returned=False,
        expiry_date__gt=timezone.now().date(),
    ).aggregate(total=Sum('qty'))['total'] or 0
    return total


def get_active_expiry_batches():
    """
    Get all active (non-returned) expiry batches sorted by date (FIFO) (Task 19).
    Returns batches that haven't been returned and aren't expired.
    """
    return Expiry.objects.filter(
        is_returned=False,
        expiry_date__gt=timezone.now().date(),
    ).select_related('stock__medicine').order_by('expiry_date')


def get_expired_batches():
    """
    Get all expired batches (expiry_date <= today) (Task 19).
    Returns expired batches for reporting or removal.
    """
    return Expiry.objects.filter(
        expiry_date__lte=timezone.now().date(),
    ).select_related('stock__medicine').order_by('expiry_date')


def get_inventory_stock_list():
    """
    Get all inventory stock with expiry information.
    PHC-UC-11: Create and Manage Inventory
    """
    return Expiry.objects.filter(
        is_returned=False,
        qty__gt=0,
        expiry_date__gt=timezone.now().date(),
    ).select_related('stock__medicine').order_by('expiry_date')


def get_expiring_medicines(days=30):
    """Get medicines expiring within N days"""
    expiry_limit = timezone.now().date() + timedelta(days=days)
    return InventoryStock.objects.filter(
        is_returned=False,
        quantity_remaining__gt=0,
        expiry_date__lte=expiry_limit,
        expiry_date__gte=timezone.now().date(),
    ).select_related('medicine').order_by('expiry_date')


def get_expired_medicines():
    """Get expired medicine stock entries"""
    return get_expired_batches()


# ===========================================================================
# ── LOW STOCK ALERTS - PHC-UC-18, PHC-BR-07 ──────────────────────────────
# ===========================================================================

def get_low_stock_alerts():
    """
    Get all active (unacknowledged) low-stock alerts.
    PHC-BR-07: Inventory Low-Stock Alert Trigger
    PHC-UC-18: Trigger Low-Stock Alerts
    """
    return LowStockAlert.objects.filter(
        acknowledged=False,
    ).select_related('medicine').order_by('-alert_triggered_at')


def get_medicine_low_stock_alert(medicine_id):
    """Check if there's an active low-stock alert for a medicine"""
    return LowStockAlert.objects.filter(
        medicine_id=medicine_id,
        acknowledged=False,
    ).first()


# ===========================================================================
# ── REQUISITION SELECTORS - PHC-UC-10, PHC-WF-02 ──────────────────────────
# ===========================================================================

def get_inventory_requisitions(status=None):
    """
    Get inventory requisitions, optionally filtered by status.
    PHC-UC-10: Create Inventory Requisition
    PHC-WF-02: Inventory Procurement Requisition workflow
    """
    query = InventoryRequisition.objects.all()
    
    if status:
        query = query.filter(status=status)
    
    return query.select_related(
        'medicine', 'created_by', 'approved_by', 'fulfilled_by'
    ).order_by('-created_date')


def get_pending_requisitions():
    """Get requisitions awaiting approval"""
    return InventoryRequisition.objects.filter(
        status__in=['CREATED', 'SUBMITTED']
    ).select_related('medicine', 'created_by').order_by('-created_date')


def get_requisition_detail(requisition_id):
    """Get full details of a requisition"""
    return InventoryRequisition.objects.filter(id=requisition_id).select_related(
        'medicine', 'created_by', 'approved_by', 'fulfilled_by'
    ).first()


# ===========================================================================
# ── PATIENT SEARCH SELECTORS - PHC-UC-06 ────────────────────────────────
# ===========================================================================

def search_patients(query_string):
    """
    Search for patients by name, email, or ID.
    PHC-UC-06: Manage Patient Records (search functionality)
    """
    from applications.globals.models import ExtraInfo
    
    return ExtraInfo.objects.filter(
        Q(user__first_name__icontains=query_string) |
        Q(user__last_name__icontains=query_string) |
        Q(user__email__icontains=query_string) |
        Q(id__icontains=query_string)
    ).select_related('user').order_by('user__first_name')


def get_patient_detail(patient_id):
    """Get detailed patient information with health profile"""
    from applications.globals.models import ExtraInfo
    
    patient = ExtraInfo.objects.get(id=patient_id)
    patient.health_profile = HealthProfile.objects.filter(patient_id=patient_id).first()
    patient.appointment_count = Appointment.objects.filter(patient_id=patient_id).count()
    patient.prescription_count = Prescription.objects.filter(patient_id=patient_id).count()
    return patient


# ===========================================================================
# ── AUDIT LOG SELECTORS - PHC-BR-09 ──────────────────────────────────────
# ===========================================================================

def get_audit_logs(entity_type=None, entity_id=None, limit=100):
    """
    Get audit logs with optional filtering.
    PHC-BR-09: Data Audit Trail Requirement
    """
    query = AuditLog.objects.all()
    
    if entity_type:
        query = query.filter(entity_type=entity_type)
    
    if entity_id:
        query = query.filter(entity_id=entity_id)
    
    return query.select_related('user').order_by('-timestamp')[:limit]


def get_user_action_history(user_id, limit=50):
    """Get action history for a specific user"""
    return AuditLog.objects.filter(user_id=user_id).order_by('-timestamp')[:limit]


# ===========================================================================
# ── DASHBOARD STATISTICS ────────────────────────────────────────────────
# ===========================================================================

def get_phc_dashboard_stats():
    """Get statistics for PHC staff dashboard"""
    today = date.today()
    
    return {
        'todays_appointments': Appointment.objects.filter(
            appointment_date=today,
        ).count(),
        'pending_claims': ReimbursementClaim.objects.exclude(
            status__in=['REIMBURSED', 'REJECTED']
        ).count(),
        'low_stock_alerts': LowStockAlert.objects.filter(acknowledged=False).count(),
        'pending_requisitions': InventoryRequisition.objects.filter(
            status__in=['CREATED', 'SUBMITTED']
        ).count(),
    }


def get_patient_summary(patient_id):
    """Get summary statistics for a patient"""
    return {
        'appointment_count': Appointment.objects.filter(patient_id=patient_id).count(),
        'prescription_count': Prescription.objects.filter(patient_id=patient_id).count(),
        'pending_claims': ReimbursementClaim.objects.filter(
            patient_id=patient_id,
        ).exclude(status__in=['REIMBURSED', 'REJECTED']).count(),
        'reimbursed_amount': ReimbursementClaim.objects.filter(
            patient_id=patient_id,
            status='REIMBURSED',
        ).aggregate(total=Sum('claim_amount'))['total'] or 0,
    }


# ===========================================================================
# ── COMPLAINT SELECTORS - PHC-UC-11, PHC-UC-12 ──────────────────────────
# ===========================================================================

def get_complaint(complaint_id):
    """
    Get a single complaint by ID with patient and resolver info.
    Task 19: Core getter for complaint tracking
    """
    return ComplaintV2.objects.select_related(
        'patient', 'resolved_by'
    ).filter(id=complaint_id).first()


def get_all_complaints(status=None):
    """
    Get all complaints, optionally filtered by status.
    Task 19: Returns queryset of all complaints
    """
    query = ComplaintV2.objects.select_related('patient', 'resolved_by')
    
    if status:
        query = query.filter(status=status)
    
    return query.order_by('-created_date')


def get_patient_complaints(patient_id):
    """
    Get all complaints filed by a patient.
    Task 19: Patient complaint history
    """
    return ComplaintV2.objects.filter(
        patient_id=patient_id
    ).select_related('resolved_by').order_by('-created_date')


def get_unresolved_complaints():
    """
    Get all unresolved complaints (not in CLOSED status).
    Task 19: For PHC staff dashboard
    """
    return ComplaintV2.objects.exclude(
        status__in=['RESOLVED', 'CLOSED']
    ).select_related('patient', 'resolved_by').order_by('-created_date')


# ===========================================================================
# ── HOSPITAL ADMISSION SELECTORS - PHC-UC-10, PHC-UC-15 ─────────────────
# ===========================================================================

def get_hospital_admission(admission_id):
    """
    Get a single hospital admission by ID.
    Task 19: Core getter for admission tracking
    """
    return HospitalAdmit.objects.select_related(
        'patient', 'referred_by'
    ).filter(id=admission_id).first()


def get_all_admissions(discharged_only=False):
    """
    Get all hospital admissions.
    If discharged_only=True, only return discharged patients.
    Task 19: Returns queryset of all admissions
    """
    query = HospitalAdmit.objects.select_related('patient', 'referred_by')
    
    if discharged_only:
        query = query.exclude(discharge_date__isnull=True)
    
    return query.order_by('-admission_date')


def get_patient_admissions(patient_id):
    """
    Get all hospital admissions for a patient.
    Task 19: Patient admission history
    """
    return HospitalAdmit.objects.filter(
        patient_id=patient_id
    ).select_related('referred_by').order_by('-admission_date')


def get_active_admissions():
    """
    Get all currently admitted patients (discharge_date is NULL).
    Task 19: For PHC staff dashboard
    """
    return HospitalAdmit.objects.filter(
        discharge_date__isnull=True
    ).select_related('patient', 'referred_by').order_by('-admission_date')


# ===========================================================================
# ── AMBULANCE SELECTORS - PHC-UC-16, PHC-WF-03 ────────────────────────────
# ===========================================================================

def get_ambulance(ambulance_id):
    """
    Get a single ambulance record by ID.
    Task 19: Core getter for ambulance lookup
    """
    return AmbulanceRecordsV2.objects.filter(id=ambulance_id).first()


def get_all_ambulances(status=None):
    """
    Get all ambulances, optionally filtered by status.
    Task 19: Returns queryset of all ambulances
    """
    query = AmbulanceRecordsV2.objects.all()
    
    if status:
        query = query.filter(status=status)
    
    return query.order_by('registration_number')


def get_available_ambulances():
    """
    Get all ambulances currently available for dispatch.
    Task 19: For PHC staff ambulance assignment
    """
    return AmbulanceRecordsV2.objects.filter(
        status='AVAILABLE',
        is_active=True
    ).order_by('registration_number')


def get_ambulance_by_registration(registration_number):
    """
    Get ambulance by registration number.
    Task 19: For quick lookup by plate number
    """
    return AmbulanceRecordsV2.objects.filter(
        registration_number=registration_number
    ).first()
