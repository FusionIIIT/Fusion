"""
Health Center Services
======================
Business logic layer for the PHC module.

Responsibility:
  - Implements business rules (PHC-BR-*)
  - Handles write operations (create, update, delete)
  - Custom exceptions for validation
  - No ORM queries here — use selectors.py instead

Architecture: Service Layer Pattern
"""

from datetime import date, timedelta
from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import (
    Doctor, DoctorSchedule, DoctorAttendance, HealthProfile,
    Appointment, Consultation, Prescription, PrescribedMedicine,
    Medicine, InventoryStock, ReimbursementClaim, ClaimDocument,
    InventoryRequisition, LowStockAlert, AuditLog, AttendanceStatusChoices,
    ReimbursementStatusChoices, RequisitionStatusChoices, BloodGroupChoices,
    Stock, Expiry, ComplaintV2, HospitalAdmit, AmbulanceRecordsV2, AmbulanceLog,
    HealthAnnouncement,
)


# ===========================================================================
# ── CUSTOM EXCEPTIONS ────────────────────────────────────────────────────
# ===========================================================================

class PHCServiceException(Exception):
    """Base exception for PHC service layer"""
    pass


class InvalidReimbursementSubmission(PHCServiceException):
    """Raised when reimbursement claim submission violates business rules"""
    pass


class InvalidStockUpdate(PHCServiceException):
    """Raised when inventory stock update is invalid"""
    pass


class DoctorNotAvailable(PHCServiceException):
    """Raised when doctor is not available"""
    pass


class InsufficientStock(PHCServiceException):
    """Raised when medicine stock is insufficient"""
    pass


class InvalidPrescription(PHCServiceException):
    """Raised when prescription data is invalid"""
    pass


class MedicineNotFound(PHCServiceException):
    """Raised when medicine is not found"""
    pass


# ===========================================================================
# ── DOCTOR AND APPOINTMENT SERVICES ──────────────────────────────────────
# ===========================================================================

def create_appointment(patient_id, doctor_id, appointment_date, appointment_time, 
                      appointment_type, chief_complaint):
    """
    Create a new appointment for a patient.
    Validates: Patient exists, Doctor exists, Date is in future
    """
    if appointment_date < date.today():
        raise ValidationError("Appointment date must be in the future")
    
    appointment = Appointment.objects.create(
        patient_id=patient_id,
        doctor_id=doctor_id,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        appointment_type=appointment_type,
        chief_complaint=chief_complaint,
    )
    
    # Log audit trail - PHC-BR-09
    log_audit_action(
        user_id=patient_id,
        action_type='CREATE',
        entity_type='Appointment',
        entity_id=appointment.id,
        details={'doctor_id': doctor_id, 'appointment_date': str(appointment_date)}
    )
    
    return appointment


def cancel_appointment(appointment_id, cancellation_reason):
    """Cancel an appointment - PHC-UC-04"""
    appointment = Appointment.objects.get(id=appointment_id)
    
    if appointment.status in ['COMPLETED', 'CANCELLED']:
        raise ValidationError(f"Cannot cancel appointment with status {appointment.status}")
    
    appointment.status = 'CANCELLED'
    appointment.cancelled_at = timezone.now()
    appointment.cancellation_reason = cancellation_reason
    appointment.save()
    
    # Log audit
    log_audit_action(
        user_id=appointment.patient_id,
        action_type='UPDATE',
        entity_type='Appointment',
        entity_id=appointment_id,
        details={'status': 'CANCELLED', 'reason': cancellation_reason}
    )
    
    return appointment


# ===========================================================================
# ── DOCTOR AVAILABILITY SERVICES - PHC-BR-01 ────────────────────────────
# ===========================================================================

def mark_doctor_attendance(doctor_id, attendance_date, status, marked_by_id):
    """
    Mark doctor's real-time attendance status for the day.
    PHC-UC-08: Mark Doctor Attendance
    PHC-BR-01: Doctor Availability Display Logic
    """
    if status not in [choice[0] for choice in AttendanceStatusChoices.choices]:
        raise ValidationError(f"Invalid status: {status}")
    
    attendance, created = DoctorAttendance.objects.update_or_create(
        doctor_id=doctor_id,
        attendance_date=attendance_date,
        defaults={
            'status': status,
            'marked_by_id': marked_by_id,
        }
    )
    
    # Log audit - PHC-BR-09
    action = 'CREATE' if created else 'UPDATE'
    log_audit_action(
        user_id=marked_by_id,
        action_type=action,
        entity_type='DoctorAttendance',
        entity_id=attendance.id,
        details={'doctor_id': doctor_id, 'status': status, 'date': str(attendance_date)}
    )
    
    return attendance


# ===========================================================================
# ── CONSULTATION AND PRESCRIPTION SERVICES ───────────────────────────────
# ===========================================================================

@transaction.atomic
def create_prescription_with_fifo_deduction(consultation_id, doctor_id, patient_id, medicines_data):
    """
    Create prescription with prescribed medicines.
    Implements FIFO stock deduction from Expiry batches.
    
    PHC-UC-06: Manage Patient Records (create prescription)
    PHC-WF-01: Prescription (FIFO medicine dispensing)
    
    Args:
        consultation_id: Consultation record ID
        doctor_id: Prescribing doctor ID
        patient_id: Patient ID
        medicines_data: [
            {'medicine_id': X, 'qty_prescribed': Y, 'days': Z, 'times_per_day': T, 'instructions': '...'}
        ]
    
    Returns:
        Prescription object with prescribed medicines
    
    Raises:
        MedicineNotFound: If medicine doesn't exist
        InsufficientStock: If total stock is insufficient
        InvalidPrescription: If prescription data is invalid
    """
    # Fetch consultation
    try:
        consultation = Consultation.objects.get(id=consultation_id)
    except Consultation.DoesNotExist:
        raise InvalidPrescription(f"Consultation with ID {consultation_id} not found")
    
    # Step 1: Validate all medicines exist and have sufficient stock
    insufficient_medicines = []
    medicine_stock_map = {}  # Map of medicine_id -> {medicine obj, total available qty}
    
    for med_data in medicines_data:
        medicine_id = med_data['medicine_id']
        qty_needed = med_data['qty_prescribed']
        
        try:
            medicine = Medicine.objects.get(id=medicine_id)
        except Medicine.DoesNotExist:
            raise MedicineNotFound(f"Medicine with ID {medicine_id} not found")
        
        # Get stock for this medicine
        try:
            stock = Stock.objects.get(medicine=medicine)
        except Stock.DoesNotExist:
            insufficient_medicines.append({
                'medicine_id': medicine_id,
                'medicine_name': medicine.medicine_name,
                'qty_needed': qty_needed,
                'qty_available': 0,
                'reason': 'No stock for this medicine'
            })
            continue
        
        # Calculate available quantity from non-returned active batches
        active_batches = stock.expiry_batches.filter(
            is_returned=False
        ).order_by('expiry_date')  # FIFO: earliest expiry first
        
        available_qty = sum(
            (batch.qty - batch.returned_qty) 
            for batch in active_batches
        )
        
        if available_qty < qty_needed:
            insufficient_medicines.append({
                'medicine_id': medicine_id,
                'medicine_name': medicine.medicine_name,
                'qty_needed': qty_needed,
                'qty_available': available_qty,
                'reason': f'Insufficient stock: need {qty_needed}, have {available_qty}'
            })
        else:
            medicine_stock_map[medicine_id] = {
                'medicine': medicine,
                'stock': stock,
                'available_qty': available_qty,
                'batches': list(active_batches)
            }
    
    # If any medicine has insufficient stock, raise error with details
    if insufficient_medicines:
        raise InsufficientStock(
            f"Insufficient stock for {len(insufficient_medicines)} medicine(s): "
            f"{insufficient_medicines}"
        )
    
    # Step 2: Create prescription
    prescription = Prescription.objects.create(
        consultation=consultation,
        patient_id=patient_id,
        doctor_id=doctor_id,
    )
    
    # Step 3: Create PrescribedMedicine records and deduct from Expiry batches (FIFO)
    for med_data in medicines_data:
        medicine_id = med_data['medicine_id']
        qty_to_dispense = med_data['qty_prescribed']
        
        medicine_info = medicine_stock_map[medicine_id]
        batches = medicine_info['batches']
        
        # Create PrescribedMedicine record
        prescribed_med = PrescribedMedicine.objects.create(
            prescription=prescription,
            medicine=medicine_info['medicine'],
            qty_prescribed=med_data['qty_prescribed'],
            days=med_data.get('days', 0),
            times_per_day=med_data.get('times_per_day', 1),
            instructions=med_data.get('instructions', ''),
            notes=med_data.get('notes', ''),
            qty_dispensed=0,  # Not dispensed yet
            is_dispensed=False,
        )
        
        # FIFO: Deduct from batches in order (earliest expiry first)
        remaining_qty = qty_to_dispense
        for batch in batches:
            if remaining_qty <= 0:
                break
            
            available_in_batch = batch.qty - batch.returned_qty
            qty_from_this_batch = min(remaining_qty, available_in_batch)
            
            # Update batch returned_qty to track deduction
            batch.returned_qty += qty_from_this_batch
            batch.save()
            
            remaining_qty -= qty_from_this_batch
            
            # Link this batch to the prescribed medicine (track which expiry was used)
            if qty_from_this_batch > 0:
                prescribed_med.expiry_used = batch
                prescribed_med.save()
    
    return prescription


@transaction.atomic
def create_prescription(consultation_id, doctor_id, patient_id, medicines_data):
    """
    Create prescription with prescribed medicines.
    PHC-UC-06: Manage Patient Records (create prescription)
    
    medicines_data: [
        {'medicine_id': X, 'quantity': Y, 'days': Z, 'times_per_day': T, 'instructions': '...'}
    ]
    """
    # Redirect to new FIFO-aware function
    return create_prescription_with_fifo_deduction(
        consultation_id, doctor_id, patient_id, medicines_data
    )


@transaction.atomic
def delete_prescription_with_stock_restoration(prescription_id):
    """
    Delete prescription and restore stock deductions.
    Implements reverse FIFO: Returns quantities to batches in reverse order.
    
    Task 13: Prescription DELETE & stock restoration
    
    Args:
        prescription_id: Prescription ID to delete
    
    Returns:
        Deleted prescription ID
    
    Raises:
        InvalidPrescription: If status is not "issued" (cannot delete dispensed)
        Prescription.DoesNotExist: If prescription not found
    """
    try:
        prescription = Prescription.objects.get(id=prescription_id)
    except Prescription.DoesNotExist:
        raise InvalidPrescription(f"Prescription with ID {prescription_id} not found")
    
    # Only allow deletion if status is "issued" (not dispensed or cancelled)
    if prescription.status != 'ISSUED':
        raise InvalidPrescription(
            f"Cannot delete prescription with status '{prescription.status}'. "
            f"Only 'ISSUED' prescriptions can be deleted."
        )
    
    # Get all PrescribedMedicine records for this prescription (in reverse order)
    prescribed_medicines = prescription.prescribed_medicines.all().order_by('-id')
    
    # Restore quantities to batches (reverse FIFO)
    for prescribed_med in prescribed_medicines:
        if prescribed_med.expiry_used:
            # Restore quantity to the batch
            batch = prescribed_med.expiry_used
            batch.returned_qty -= prescribed_med.qty_prescribed
            
            # Ensure returned_qty doesn't go negative (safety check)
            if batch.returned_qty < 0:
                batch.returned_qty = 0
            
            batch.save()
    
    # Delete the prescription (cascades to PrescribedMedicine records)
    prescription_id_backup = prescription.id
    prescription.delete()
    
    return prescription_id_backup


@transaction.atomic
def update_prescription_details(prescription_id, update_data):
    """
    Update prescription details and/or status.
    
    Task 13: Prescription PATCH - Update metadata only
    
    Args:
        prescription_id: Prescription ID to update
        update_data: Dict with allowed fields:
            - details: str
            - special_instructions: str
            - test_recommended: str
            - follow_up_suggestions: str
            - status: str (can transition from ISSUED to DISPENSED)
    
    Returns:
        Updated prescription object
    
    Raises:
        InvalidPrescription: If prescription not found or cannot be updated
    """
    try:
        prescription = Prescription.objects.get(id=prescription_id)
    except Prescription.DoesNotExist:
        raise InvalidPrescription(f"Prescription with ID {prescription_id} not found")
    
    # Update allowed fields
    if 'details' in update_data:
        prescription.details = update_data['details']
    
    if 'special_instructions' in update_data:
        prescription.special_instructions = update_data['special_instructions']
    
    if 'test_recommended' in update_data:
        prescription.test_recommended = update_data['test_recommended']
    
    if 'follow_up_suggestions' in update_data:
        prescription.follow_up_suggestions = update_data['follow_up_suggestions']
    
    # Handle status change (only ISSUED -> DISPENSED allowed)
    if 'status' in update_data:
        new_status = update_data['status']
        if prescription.status == 'ISSUED' and new_status == 'DISPENSED':
            prescription.status = new_status
        elif new_status != prescription.status:
            raise InvalidPrescription(
                f"Cannot transition prescription status from {prescription.status} to {new_status}. "
                f"Only ISSUED -> DISPENSED transitions are allowed."
            )
    
    prescription.save()
    return prescription


@transaction.atomic
def mark_prescription_dispensed(prescription_id, dispensed_by_id=None):
    """
    Mark prescription as DISPENSED.
    Transition: ISSUED → DISPENSED
    
    Task 20: Mark prescription as fully dispensed
    
    Args:
        prescription_id: Prescription ID to mark as dispensed
        dispensed_by_id: ID of person marking it as dispensed (optional, for audit)
    
    Returns:
        Updated prescription object
    
    Raises:
        InvalidPrescription: If prescription not in ISSUED status
    """
    try:
        prescription = Prescription.objects.get(id=prescription_id)
    except Prescription.DoesNotExist:
        raise InvalidPrescription(f"Prescription with ID {prescription_id} not found")
    
    # Validate prescription is in ISSUED status
    if prescription.status != 'ISSUED':
        raise InvalidPrescription(
            f"Cannot mark prescription as dispensed. "
            f"Current status is '{prescription.status}', expected 'ISSUED'"
        )
    
    # Transition to DISPENSED
    prescription.status = 'DISPENSED'
    prescription.save()
    
    # Log audit trail
    log_audit_action(
        user_id=dispensed_by_id or prescription.patient_id,
        action_type='UPDATE',
        entity_type='Prescription',
        entity_id=prescription.id,
        details={'status_change': 'ISSUED -> DISPENSED'}
    )
    
    return prescription


@transaction.atomic
def mark_expiry_batch_returned(batch_id, returned_qty, returned_by_id=None):
    """
    Mark an expiry batch as (partially or fully) returned.
    Updates Stock total accordingly.
    
    Task 20: Inventory batch return tracking
    PHC-BR-07: Inventory management
    
    Args:
        batch_id: Expiry batch ID to mark as returned
        returned_qty: Quantity being returned (can be partial)
        returned_by_id: ID of person processing the return (for audit)
    
    Returns:
        Updated Expiry batch object
    
    Raises:
        InvalidStockUpdate: If batch not found or quantity invalid
    """
    try:
        batch = Expiry.objects.get(id=batch_id)
    except Expiry.DoesNotExist:
        raise InvalidStockUpdate(f"Expiry batch with ID {batch_id} not found")
    
    # Validate return quantity
    if returned_qty <= 0:
        raise InvalidStockUpdate("Returned quantity must be greater than 0")
    
    available_qty = batch.qty - batch.returned_qty
    if returned_qty > available_qty:
        raise InvalidStockUpdate(
            f"Cannot return {returned_qty}u. Only {available_qty}u available "
            f"({batch.qty}u total - {batch.returned_qty}u already returned)"
        )
    
    # Update batch
    batch.returned_qty += returned_qty
    
    # Mark as completely returned if all qty is returned
    if batch.returned_qty >= batch.qty:
        batch.is_returned = True
    
    batch.save()
    
    # Update Stock total
    stock = batch.stock
    # Recalculate stock total from all non-returned quantities
    total_qty = sum(
        (b.qty - b.returned_qty)
        for b in stock.expiry_batches.all()
    )
    stock.total_qty = total_qty
    stock.save()
    
    # Log audit trail
    log_audit_action(
        user_id=returned_by_id or stock.medicine_id,
        action_type='UPDATE',
        entity_type='Expiry',
        entity_id=batch.id,
        details={
            'returned_qty': returned_qty,
            'batch_total': batch.qty,
            'new_total_stock': stock.total_qty
        }
    )
    
    return batch

# ===========================================================================
# ── REIMBURSEMENT CLAIM SERVICES - PHC-UC-04, PHC-WF-01 ──────────────────
# ===========================================================================

def validate_reimbursement_submission(patient_id, prescription_id, expense_date, 
                                     claim_amount, submission_window_days=30):
    """
    Validate reimbursement claim against business rules.
    
    * PHC-BR-04: Only employees can submit
    * PHC-BR-05: Must be linked to valid prescription
    * PHC-BR-06: Must be within submission window
    """
    from applications.globals.models import ExtraInfo
    
    # PHC-BR-04: Check if user is Employee
    patient = ExtraInfo.objects.get(id=patient_id)
    if patient.user_type != 'FACULTY' and patient.user_type != 'STAFF':
        raise InvalidReimbursementSubmission(
            "Only employees (Faculty/Staff) can submit reimbursement claims"
        )
    
    # PHC-BR-05: Check if prescription exists and belongs to patient
    try:
        prescription = Prescription.objects.get(id=prescription_id, patient_id=patient_id)
    except Prescription.DoesNotExist:
        raise InvalidReimbursementSubmission(
            "Prescription not found or does not belong to this patient"
        )
    
    # PHC-BR-06: Check submission window
    days_since_expense = (date.today() - expense_date).days
    if days_since_expense > submission_window_days:
        raise InvalidReimbursementSubmission(
            f"Claim must be submitted within {submission_window_days} days of expense. "
            f"This claim is {days_since_expense} days old."
        )
    
    return True


@transaction.atomic
def submit_reimbursement_claim(patient_id, prescription_id, claim_amount, 
                               expense_date, description):
    """
    Submit a reimbursement claim.
    Initiates workflow PHC-WF-01: Multi-stage approval process
    """
    # Validate submission
    validate_reimbursement_submission(patient_id, prescription_id, expense_date, claim_amount)
    
    claim = ReimbursementClaim.objects.create(
        patient_id=patient_id,
        prescription_id=prescription_id,
        claim_amount=claim_amount,
        expense_date=expense_date,
        description=description,
        status=ReimbursementStatusChoices.SUBMITTED,
        created_by_id=patient_id,
    )
    
    # Log audit - PHC-BR-09
    log_audit_action(
        user_id=patient_id,
        action_type='CREATE',
        entity_type='ReimbursementClaim',
        entity_id=claim.id,
        details={
            'amount': str(claim_amount),
            'expense_date': str(expense_date),
            'prescription_id': prescription_id,
        }
    )
    
    return claim


def process_claim_phc_stage(claim_id, phc_staff_id, approved, remarks):
    """
    PHC Staff review stage of reimbursement claim.
    PHC-WF-01 Node 2: PHC Staff Review
    """
    claim = ReimbursementClaim.objects.get(id=claim_id)
    
    if claim.status != ReimbursementStatusChoices.SUBMITTED:
        raise InvalidReimbursementSubmission(
            f"Can only process SUBMITTED claims, current status: {claim.status}"
        )
    
    claim.phc_staff_review_date = date.today()
    claim.phc_staff_approved = approved
    claim.phc_staff_remarks = remarks
    
    if approved:
        # PHC-BR-08: Evaluate Sanction Threshold here before Accounts Verification
        from decimal import Decimal
        SANCTION_THRESHOLD = Decimal('10000.00')
        if claim.claim_amount > SANCTION_THRESHOLD:
            claim.sanction_required = True
            claim.status = ReimbursementStatusChoices.SANCTION_REVIEW
        else:
            claim.sanction_required = False
            claim.status = ReimbursementStatusChoices.ACCOUNTS_VERIFICATION
    else:
        claim.status = ReimbursementStatusChoices.REJECTED
        claim.is_rejected = True
        claim.rejection_reason = remarks
    
    claim.save()
    
    # Log audit - PHC-BR-09
    log_audit_action(
        user_id=phc_staff_id,
        action_type='APPROVE' if approved else 'REJECT',
        entity_type='ReimbursementClaim',
        entity_id=claim_id,
        details={'action': 'PHC_REVIEW', 'approved': approved}
    )
    
    return claim


def process_claim_accounts_stage(claim_id, accounts_staff_id, verified, remarks):
    """
    Accounts & Audit verification stage.
    PHC-WF-01 Node 3: Accounts Verification
    """
    claim = ReimbursementClaim.objects.get(id=claim_id)
    
    if claim.status != ReimbursementStatusChoices.ACCOUNTS_VERIFICATION:
        raise InvalidReimbursementSubmission(
            f"Claim not in accounts verification stage"
        )
    
    claim.accounts_verification_date = date.today()
    claim.accounts_verified = verified
    claim.accounts_remarks = remarks
    
    if verified:
        # Re-ordered workflow: Sanction check happened prior; directly queue to final payment
        claim.status = ReimbursementStatusChoices.FINAL_PAYMENT
    else:
        claim.status = ReimbursementStatusChoices.REJECTED
        claim.is_rejected = True
        claim.rejection_reason = remarks
    
    claim.save()
    
    # Log audit - PHC-BR-09
    log_audit_action(
        user_id=accounts_staff_id,
        action_type='APPROVE' if verified else 'REJECT',
        entity_type='ReimbursementClaim',
        entity_id=claim_id,
        details={'action': 'ACCOUNTS_VERIFICATION', 'verified': verified}
    )
    
    return claim


# ===========================================================================
# ── INVENTORY SERVICES ───────────────────────────────────────────────────
# ===========================================================================

@transaction.atomic
def update_inventory_stock(medicine_id, quantity_change, change_reason):
    """
    Update inventory stock with audit trail.
    PHC-UC-09: Update Inventory Stock
    PHC-BR-07: Trigger low-stock alert if threshold breached
    PHC-BR-09: Log audit trail
    """
    medicine = Medicine.objects.get(id=medicine_id)
    
    # Get latest stock entry (by expiry date, FIFO for deductions)
    stock = InventoryStock.objects.filter(
        medicine=medicine,
        quantity_remaining__gt=0,
        expiry_date__gt=timezone.now().date(),
        is_returned=False,
    ).order_by('expiry_date').first()
    
    if not stock:
        raise InvalidStockUpdate(f"No available stock for {medicine.medicine_name}")
    
    new_quantity = stock.quantity_remaining + quantity_change
    
    if new_quantity < 0:
        raise InvalidStockUpdate(
            f"Cannot reduce stock below 0. Current: {stock.quantity_remaining}, "
            f"Requested reduction: {abs(quantity_change)}"
        )
    
    stock.quantity_remaining = new_quantity
    stock.save()
    
    # PHC-BR-07: Check for low-stock alert
    if new_quantity <= medicine.reorder_threshold:
        create_low_stock_alert(medicine_id, new_quantity)
    
    return stock


def create_low_stock_alert(medicine_id, current_stock):
    """
    Create low-stock alert when inventory falls below threshold.
    PHC-BR-07, PHC-UC-18: Trigger Low-Stock Alerts
    """
    medicine = Medicine.objects.get(id=medicine_id)
    
    # Check if alert already exists (unacknowledged)
    existing_alert = LowStockAlert.objects.filter(
        medicine_id=medicine_id,
        acknowledged=False,
    ).first()
    
    if existing_alert:
        return existing_alert
    
    alert = LowStockAlert.objects.create(
        medicine_id=medicine_id,
        current_stock=current_stock,
        reorder_threshold=medicine.reorder_threshold,
    )
    
    return alert


def create_requisition(medicine_id, quantity_requested, created_by_id):
    """
    Create inventory requisition.
    PHC-UC-10: Create Inventory Requisition
    PHC-WF-02: Requisition workflow
    """
    requisition = InventoryRequisition.objects.create(
        medicine_id=medicine_id,
        quantity_requested=quantity_requested,
        created_by_id=created_by_id,
    )
    
    # Log audit - PHC-BR-09
    log_audit_action(
        user_id=created_by_id,
        action_type='CREATE',
        entity_type='InventoryRequisition',
        entity_id=requisition.id,
        details={
            'medicine_id': medicine_id,
            'quantity': quantity_requested,
        }
    )
    
    return requisition


# ===========================================================================
# ── AUDIT LOGGING - PHC-BR-09 ────────────────────────────────────────────
# ===========================================================================

def log_audit_action(user_id, action_type, entity_type, entity_id, details, ip_address=None):
    """
    Log all sensitive actions to immutable audit trail.
    PHC-BR-09: Data Audit Trail Requirement
    """
    AuditLog.objects.create(
        user_id=user_id,
        action_type=action_type,
        entity_type=entity_type,
        entity_id=entity_id,
        action_details=details,
        ip_address=ip_address,
    )


# ===========================================================================
# ── COMPLAINT SERVICES ──────────────────────────────────────────────────
# ===========================================================================

@transaction.atomic
def resolve_complaint_with_notes(complaint_id, resolution_notes, resolved_by_id):
    """
    Resolve complaint and record resolution notes.
    Task 14: Compounder responds to complaint
    
    Args:
        complaint_id: Complaint ID to resolve
        resolution_notes: Resolution/response notes (10+ characters)
        resolved_by_id: ExtraInfo ID of compounder who resolved
    
    Returns:
        Updated complaint object with RESOLVED status
    
    Raises:
        InvalidPrescription: If complaint not found or cannot be resolved
    """
    from .models import ComplaintV2
    
    try:
        complaint = ComplaintV2.objects.get(id=complaint_id)
    except ComplaintV2.DoesNotExist:
        raise InvalidPrescription(f"Complaint with ID {complaint_id} not found")
    
    # Update complaint with resolution
    complaint.status = 'RESOLVED'
    complaint.resolution_notes = resolution_notes
    complaint.resolved_by_id = resolved_by_id
    complaint.resolved_date = timezone.now()
    complaint.save()
    
    # Log audit trail
    log_audit_action(
        user_id=resolved_by_id,
        action_type='UPDATE',
        entity_type='Complaint',
        entity_id=complaint.id,
        details={'status': 'RESOLVED', 'resolution_notes': resolution_notes[:100]}
    )
    
    return complaint


def update_complaint_patient(complaint_id, patient_id, update_data):
    """
    Update complaint (patient can update own non-resolved complaints).
    Task 14: Patient updates own complaint
    
    Args:
        complaint_id: Complaint ID
        patient_id: Patient ID (for ownership validation)
        update_data: Dict with 'title', 'description' (optional)
    
    Returns:
        Updated complaint object
    
    Raises:
        InvalidPrescription: If complaint not found, not owned, or already resolved
    """
    from .models import ComplaintV2
    
    try:
        complaint = ComplaintV2.objects.get(id=complaint_id)
    except ComplaintV2.DoesNotExist:
        raise InvalidPrescription(f"Complaint with ID {complaint_id} not found")
    
    # Verify ownership
    if complaint.patient_id != patient_id:
        raise InvalidPrescription(f"You do not have permission to update this complaint")
    
    # Check if resolved
    if complaint.status == 'RESOLVED':
        raise InvalidPrescription(f"Cannot update a resolved complaint")
    
    # Update allowed fields
    if 'title' in update_data:
        complaint.title = update_data['title']
    
    if 'description' in update_data:
        complaint.description = update_data['description']
    
    complaint.save()
    
    # Log audit
    log_audit_action(
        user_id=patient_id,
        action_type='UPDATE',
        entity_type='Complaint',
        entity_id=complaint.id,
        details=update_data
    )
    
    return complaint


# ===========================================================================
# ── HOSPITAL ADMISSION SERVICES ──────────────────────────────────────────
# ===========================================================================

@transaction.atomic
def create_hospital_admission(patient_id, admission_data):
    """
    Create hospital admission record.
    Task 15: Hospital admission CRUD
    
    Args:
        patient_id: ExtraInfo FK (patient)
        admission_data: Dict with hospital_id, hospital_name, admission_date, reason, referred_by
    
    Returns:
        HospitalAdmit instance
    
    Raises:
        ValidationError: If admission_date > today or invalid data
    """
    from applications.globals.models import ExtraInfo
    
    # Validate patient exists
    try:
        patient = ExtraInfo.objects.get(id=patient_id)
    except ExtraInfo.DoesNotExist:
        raise InvalidPrescription(f"Patient with ID {patient_id} not found")
    
    # Validate admission_date
    admission_date = admission_data.get('admission_date')
    if admission_date > date.today():
        raise InvalidPrescription("Admission date cannot be in the future")
    
    # Create admission record (patient_name auto-populated on save)
    admission = HospitalAdmit.objects.create(
        patient_id=patient_id,
        hospital_id=admission_data.get('hospital_id'),
        hospital_name=admission_data.get('hospital_name'),
        admission_date=admission_date,
        reason=admission_data.get('reason'),
        referred_by_id=admission_data.get('referred_by'),
    )
    
    # Log audit
    log_audit_action(
        user_id=patient_id,
        action_type='CREATE',
        entity_type='HospitalAdmit',
        entity_id=admission.id,
        details={'hospital_name': admission.hospital_name, 'reason': admission.reason}
    )
    
    return admission


@transaction.atomic
def discharge_patient(admission_id, discharge_data):
    """
    Discharge patient from hospital.
    Task 15: Hospital admission discharge
    
    Args:
        admission_id: HospitalAdmit PK
        discharge_data: Dict with discharge_date, summary
    
    Returns:
        Updated HospitalAdmit instance
    
    Raises:
        InvalidPrescription: If admission not found or discharge_date < admission_date
    """
    try:
        admission = HospitalAdmit.objects.get(id=admission_id)
    except HospitalAdmit.DoesNotExist:
        raise InvalidPrescription(f"Hospital admission with ID {admission_id} not found")
    
    # Validate discharge_date >= admission_date
    discharge_date = discharge_data.get('discharge_date')
    if discharge_date and discharge_date < admission.admission_date:
        raise InvalidPrescription("Discharge date must be after or equal to admission date")
    
    # Update discharge info
    admission.discharge_date = discharge_date
    admission.summary = discharge_data.get('summary', '')
    admission.save()
    
    # Log audit
    log_audit_action(
        user_id=admission.patient_id,
        action_type='UPDATE',
        entity_type='HospitalAdmit',
        entity_id=admission.id,
        details={'discharged': True, 'summary': admission.summary[:100]}
    )
    
    return admission


@transaction.atomic
def update_hospital_admission(admission_id, update_data):
    """
    Update hospital admission details.
    Task 15: Hospital admission update
    
    Args:
        admission_id: HospitalAdmit PK
        update_data: Dict with fields to update (reason, hospital_name, etc)
    
    Returns:
        Updated HospitalAdmit instance
    
    Raises:
        InvalidPrescription: If admission not found
    """
    try:
        admission = HospitalAdmit.objects.get(id=admission_id)
    except HospitalAdmit.DoesNotExist:
        raise InvalidPrescription(f"Hospital admission with ID {admission_id} not found")
    
    # Update allowed fields
    if 'reason' in update_data:
        admission.reason = update_data['reason']
    if 'hospital_name' in update_data:
        admission.hospital_name = update_data['hospital_name']
    if 'hospital_id' in update_data:
        admission.hospital_id = update_data['hospital_id']
    
    admission.save()
    
    # Log audit
    log_audit_action(
        user_id=admission.patient_id,
        action_type='UPDATE',
        entity_type='HospitalAdmit',
        entity_id=admission.id,
        details=update_data
    )
    
    return admission


# ===========================================================================# ── AMBULANCE RECORDS SERVICES ──────────────────────────────────────────
# ===========================================================================

@transaction.atomic
def create_ambulance_record(ambulance_data):
    """
    Create ambulance record.
    Task 16: Ambulance records CRUD (compounder only)
    
    Args:
        ambulance_data: Dict with vehicle_type, registration_number, driver_name,
                       driver_contact, driver_license, last_maintenance_date, etc
    
    Returns:
        AmbulanceRecordsV2 instance
    
    Raises:
        InvalidPrescription: If registration_number already exists
    """
    # Check for duplicate registration number
    if AmbulanceRecordsV2.objects.filter(
        registration_number=ambulance_data.get('registration_number')
    ).exists():
        raise InvalidPrescription(
            f"Ambulance with registration {ambulance_data.get('registration_number')} already exists"
        )
    
    # Create ambulance record
    ambulance = AmbulanceRecordsV2.objects.create(
        vehicle_type=ambulance_data.get('vehicle_type'),
        registration_number=ambulance_data.get('registration_number'),
        driver_name=ambulance_data.get('driver_name'),
        driver_contact=ambulance_data.get('driver_contact'),
        driver_license=ambulance_data.get('driver_license', ''),
        last_maintenance_date=ambulance_data.get('last_maintenance_date'),
        next_maintenance_due=ambulance_data.get('next_maintenance_due'),
        notes=ambulance_data.get('notes', ''),
    )
    
    # Log audit
    log_audit_action(
        user_id=None,  # System-generated (no user context)
        action_type='CREATE',
        entity_type='AmbulanceRecord',
        entity_id=ambulance.id,
        details={'registration': ambulance.registration_number, 'vehicle_type': ambulance.vehicle_type}
    )
    
    return ambulance


@transaction.atomic
def update_ambulance_record(ambulance_id, update_data):
    """
    Update ambulance record.
    Task 16: Ambulance records update
    
    Args:
        ambulance_id: AmbulanceRecordsV2 PK
        update_data: Dict with fields to update (status, assignment, notes, is_active, etc)
    
    Returns:
        Updated AmbulanceRecordsV2 instance
    
    Raises:
        InvalidPrescription: If ambulance not found
    """
    try:
        ambulance = AmbulanceRecordsV2.objects.get(id=ambulance_id)
    except AmbulanceRecordsV2.DoesNotExist:
        raise InvalidPrescription(f"Ambulance with ID {ambulance_id} not found")
    
    # Update allowed fields
    if 'status' in update_data:
        ambulance.status = update_data['status']
    if 'current_assignment' in update_data:
        ambulance.current_assignment = update_data['current_assignment']
    if 'notes' in update_data:
        ambulance.notes = update_data['notes']
    if 'is_active' in update_data:
        ambulance.is_active = update_data['is_active']
    if 'last_maintenance_date' in update_data:
        ambulance.last_maintenance_date = update_data['last_maintenance_date']
    if 'next_maintenance_due' in update_data:
        ambulance.next_maintenance_due = update_data['next_maintenance_due']
    
    ambulance.save()
    
    # Log audit — convert date objects to ISO strings for JSON serialization
    safe_details = {}
    for k, v in update_data.items():
        if isinstance(v, date):
            safe_details[k] = v.isoformat()
        else:
            safe_details[k] = v
    log_audit_action(
        user_id=None,
        action_type='UPDATE',
        entity_type='AmbulanceRecord',
        entity_id=ambulance.id,
        details=safe_details
    )
    
    return ambulance


# ===========================================================================# ── HEALTH PROFILE SERVICES ─────────────────────────────────────────────
# ===========================================================================

def create_or_update_health_profile(patient_id, profile_data):
    """
    Create or update patient health profile.
    """
    profile, created = HealthProfile.objects.update_or_create(
        patient_id=patient_id,
        defaults={
            'blood_group': profile_data.get('blood_group'),
            'height_cm': profile_data.get('height_cm'),
            'weight_kg': profile_data.get('weight_kg'),
            'allergies': profile_data.get('allergies', ''),
            'chronic_conditions': profile_data.get('chronic_conditions', ''),
            'current_medications': profile_data.get('current_medications', ''),
            'past_surgeries': profile_data.get('past_surgeries', ''),
            'family_medical_history': profile_data.get('family_medical_history', ''),
            'has_insurance': profile_data.get('has_insurance', False),
            'insurance_provider': profile_data.get('insurance_provider', ''),
            'insurance_policy_number': profile_data.get('insurance_policy_number', ''),
            'insurance_valid_until': profile_data.get('insurance_valid_until'),
            'emergency_contact_name': profile_data.get('emergency_contact_name', ''),
            'emergency_contact_phone': profile_data.get('emergency_contact_phone', ''),
            'emergency_contact_relation': profile_data.get('emergency_contact_relation', ''),
        }
    )
    
    # Log audit
    action = 'CREATE' if created else 'UPDATE'
    log_audit_action(
        user_id=patient_id,
        action_type=action,
        entity_type='HealthProfile',
        entity_id=profile.id,
        details=profile_data,
    )
    
    return profile


# ===========================================================================
# ── TASK 18: REIMBURSEMENT WORKFLOW TRANSITIONS ───────────────────────
# ===========================================================================

@transaction.atomic
def forward_reimbursement_claim(claim_id, compounder_id, phc_notes):
    """
    Task 18: Forward reimbursement claim in workflow.
    
    State transitions:
      SUBMITTED → PHC_REVIEW (first forward by compounder)
      PHC_REVIEW → ACCOUNTS_REVIEW (second forward by compounder)
    
    Args:
        claim_id: Reimbursement claim ID to transition
        compounder_id: ID of compounder performing the action
        phc_notes: Notes from compounder about the claim
    
    Returns:
        Updated ReimbursementClaim object
    
    Raises:
        InvalidPrescription: If claim not found or invalid state transition
    """
    try:
        claim = ReimbursementClaim.objects.get(id=claim_id)
    except ReimbursementClaim.DoesNotExist:
        raise InvalidPrescription(f"Reimbursement claim {claim_id} not found")
    
    # Validate current status for state machine
    if claim.status == 'SUBMITTED':
        # First transition: SUBMITTED → PHC_REVIEW
        claim.status = 'PHC_REVIEW'
    elif claim.status == 'PHC_REVIEW':
        # Second transition: PHC_REVIEW → ACCOUNTS_REVIEW
        claim.status = 'ACCOUNTS_REVIEW'
    else:
        raise InvalidPrescription(
            f"Cannot forward claim with status '{claim.status}'. "
            f"Only SUBMITTED or PHC_REVIEW claims can be forwarded."
        )
    
    # Store compounder notes
    claim.phc_notes = phc_notes
    claim.save()
    
    # Log audit trail
    log_audit_action(
        user_id=compounder_id,
        action_type='FORWARD',
        entity_type='ReimbursementClaim',
        entity_id=claim.id,
        details={'new_status': claim.status, 'notes': phc_notes}
    )
    
    return claim


@transaction.atomic
def approve_reimbursement_claim(claim_id, accounts_staff_id, approval_notes=''):
    """
    Task 18: Approve reimbursement claim (Accounts staff only).
    
    State transition:
      ACCOUNTS_REVIEW → APPROVED
    
    Args:
        claim_id: Reimbursement claim ID to approve
        accounts_staff_id: ID of accounts staff approving
        approval_notes: Optional approval notes
    
    Returns:
        Updated ReimbursementClaim object
    
    Raises:
        InvalidPrescription: If claim not in ACCOUNTS_REVIEW status
    """
    try:
        claim = ReimbursementClaim.objects.get(id=claim_id)
    except ReimbursementClaim.DoesNotExist:
        raise InvalidPrescription(f"Reimbursement claim {claim_id} not found")
    
    # Validate claim is in ACCOUNTS_REVIEW status
    if claim.status != 'ACCOUNTS_REVIEW':
        raise InvalidPrescription(
            f"Cannot approve claim with status '{claim.status}'. "
            f"Only ACCOUNTS_REVIEW claims can be approved."
        )
    
    # Transition to APPROVED
    claim.status = 'APPROVED'
    if 'approval_notes' in approval_notes or approval_notes:
        claim.phc_notes = approval_notes  # Store approval notes in existing field
    claim.save()
    
    # Log audit trail
    log_audit_action(
        user_id=accounts_staff_id,
        action_type='APPROVE',
        entity_type='ReimbursementClaim',
        entity_id=claim.id,
        details={'new_status': 'APPROVED', 'notes': approval_notes}
    )
    
    return claim


@transaction.atomic
def reject_reimbursement_claim(claim_id, accounts_staff_id, rejection_reason):
    """
    Task 18: Reject reimbursement claim (Accounts staff only).
    
    State transition:
      ACCOUNTS_REVIEW → REJECTED
    
    Args:
        claim_id: Reimbursement claim ID to reject
        accounts_staff_id: ID of accounts staff rejecting
        rejection_reason: Reason for rejection
    
    Returns:
        Updated ReimbursementClaim object
    
    Raises:
        InvalidPrescription: If claim not in ACCOUNTS_REVIEW status, or reason is empty
    """
    try:
        claim = ReimbursementClaim.objects.get(id=claim_id)
    except ReimbursementClaim.DoesNotExist:
        raise InvalidPrescription(f"Reimbursement claim {claim_id} not found")
    
    # Validate claim is in ACCOUNTS_REVIEW status
    if claim.status != 'ACCOUNTS_REVIEW':
        raise InvalidPrescription(
            f"Cannot reject claim with status '{claim.status}'. "
            f"Only ACCOUNTS_REVIEW claims can be rejected."
        )
    
    # Validate rejection reason is provided
    if not rejection_reason or not str(rejection_reason).strip():
        raise InvalidPrescription("Rejection reason is required when rejecting a claim")
    
    # Transition to REJECTED
    claim.status = 'REJECTED'
    claim.rejection_reason = rejection_reason
    claim.save()
    
    # Log audit trail
    log_audit_action(
        user_id=accounts_staff_id,
        action_type='REJECT',
        entity_type='ReimbursementClaim',
        entity_id=claim.id,
        details={'new_status': 'REJECTED', 'reason': rejection_reason}
    )
    
    return claim


# ===========================================================================
# ── COMPLAINT SERVICES - PHC-UC-11, PHC-UC-12 ──────────────────────────
# ===========================================================================

@transaction.atomic
def create_complaint(patient_id, title, description, category):
    """
    Create a patient complaint.
    
    Task 20: Complaint creation service
    PHC-UC-11: File Complaint
    
    Args:
        patient_id: Patient filing complaint
        title: Complaint title
        description: Detailed description
        category: Complaint category (SERVICE, STAFF, FACILITIES, MEDICAL, OTHER)
    
    Returns:
        Created ComplaintV2 object
    
    Raises:
        InvalidPrescription: If patient not found or invalid data
    """
    if not title or not title.strip():
        raise InvalidPrescription("Complaint title is required")
    
    if not description or not description.strip():
        raise InvalidPrescription("Complaint description is required")
    
    if category not in ['SERVICE', 'STAFF', 'FACILITIES', 'MEDICAL', 'OTHER']:
        raise InvalidPrescription(f"Invalid complaint category: {category}")
    
    complaint = ComplaintV2.objects.create(
        patient_id=patient_id,
        title=title.strip(),
        description=description.strip(),
        category=category,
        status='SUBMITTED',
    )
    
    # Log audit trail
    log_audit_action(
        user_id=patient_id,
        action_type='CREATE',
        entity_type='ComplaintV2',
        entity_id=complaint.id,
        details={'title': title, 'category': category}
    )
    
    return complaint


@transaction.atomic
def resolve_complaint(complaint_id, resolver_id, resolution_notes):
    """
    Resolve/close a complaint.
    Transition: SUBMITTED/IN_PROGRESS → RESOLVED
    
    Task 20: Complaint resolution service
    PHC-UC-12: Track Complaint Response
    
    Args:
        complaint_id: Complaint ID to resolve
        resolver_id: ID of staff resolving the complaint
        resolution_notes: Resolution details
    
    Returns:
        Updated ComplaintV2 object
    
    Raises:
        InvalidPrescription: If complaint not found or invalid state
    """
    try:
        complaint = ComplaintV2.objects.get(id=complaint_id)
    except ComplaintV2.DoesNotExist:
        raise InvalidPrescription(f"Complaint {complaint_id} not found")
    
    if complaint.status == 'CLOSED':
        raise InvalidPrescription("Cannot resolve a complaint that is already closed")
    
    if not resolution_notes or not str(resolution_notes).strip():
        raise InvalidPrescription("Resolution notes are required")
    
    # Transition to RESOLVED
    complaint.status = 'RESOLVED'
    complaint.resolution_notes = resolution_notes.strip()
    complaint.resolved_date = timezone.now()
    complaint.resolved_by_id = resolver_id
    complaint.save()
    
    # Log audit trail
    log_audit_action(
        user_id=resolver_id,
        action_type='UPDATE',
        entity_type='ComplaintV2',
        entity_id=complaint.id,
        details={'status': 'RESOLVED', 'notes': resolution_notes[:100]}
    )
    
    return complaint


# ===========================================================================
# ── CONSULTATION SERVICES ──────────────────────────────────────────────
# ===========================================================================

@transaction.atomic
def create_consultation(patient_id, doctor_id, appointment_id, chief_complaint, 
                       clinical_notes='', diagnosis=''):
    """
    Create a consultation record (follow-up from appointment).
    
    Task 20: Consultation creation service
    
    Args:
        patient_id: Patient for consultation
        doctor_id: Consulting doctor
        appointment_id: Associated appointment
        chief_complaint: Patient's complaint
        clinical_notes: Doctor's clinical notes
        diagnosis: Initial diagnosis
    
    Returns:
        Created Consultation object
    
    Raises:
        InvalidPrescription: If appointment not found or data invalid
    """
    try:
        appointment = Appointment.objects.get(id=appointment_id)
    except Appointment.DoesNotExist:
        raise InvalidPrescription(f"Appointment {appointment_id} not found")
    
    if not chief_complaint or not str(chief_complaint).strip():
        raise InvalidPrescription("Chief complaint is required")
    
    consultation = Consultation.objects.create(
        patient_id=patient_id,
        doctor_id=doctor_id,
        appointment_id=appointment_id,
        chief_complaint=chief_complaint.strip(),
        clinical_notes=clinical_notes.strip() if clinical_notes else '',
        diagnosis=diagnosis.strip() if diagnosis else '',
        ambulance_requested='no',
    )
    
    # Log audit trail
    log_audit_action(
        user_id=doctor_id,
        action_type='CREATE',
        entity_type='Consultation',
        entity_id=consultation.id,
        details={'patient_id': patient_id, 'chief_complaint': chief_complaint}
    )
    
    return consultation


# ===========================================================================
# ── INVENTORY REQUISITION SERVICES ─────────────────────────────────────
# ===========================================================================

@transaction.atomic
def approve_inventory_requisition(requisition_id, approved_by_id):
    """
    Approve an inventory requisition.
    Transition: SUBMITTED/CREATED → APPROVED

    PHC-WF-02: Inventory procurement workflow

    Args:
        requisition_id: Requisition ID to approve
        approved_by_id: ExtraInfo ID of staff approving

    Returns:
        Updated InventoryRequisition object

    Raises:
        InvalidStockUpdate: If requisition not found or invalid state
    """
    try:
        requisition = InventoryRequisition.objects.get(id=requisition_id)
    except InventoryRequisition.DoesNotExist:
        raise InvalidStockUpdate(f"Requisition {requisition_id} not found")

    if requisition.status not in ['CREATED', 'SUBMITTED']:
        raise InvalidStockUpdate(
            f"Cannot approve requisition with status '{requisition.status}'. "
            f"Only CREATED or SUBMITTED requisitions can be approved."
        )

    # Transition to APPROVED
    requisition.status = 'APPROVED'
    requisition.approved_date = timezone.now()
    requisition.approved_by_id = approved_by_id
    requisition.save()

    # Log audit trail (PHC-BR-09)
    log_audit_action(
        user_id=approved_by_id,
        action_type='UPDATE',
        entity_type='InventoryRequisition',
        entity_id=requisition.id,
        details={'status': 'APPROVED'}
    )

    # ── PHC-BR-11: Requisition Approval Notification ──────────────────────────
    # Notify the compounder that created the requisition.
    from notification.views import healthcare_center_notif
    try:
        medicine_name = requisition.medicine.medicine_name
        msg = f"Req #{requisition.id} ({medicine_name} x{requisition.quantity_requested}) has been approved."
        healthcare_center_notif(
            sender=requisition.approved_by.user if requisition.approved_by else None,
            recipient=requisition.created_by.user,
            type='req_approved',
            message=msg,
        )
    except Exception:
        pass  # Never let notification failure break the main transaction

    return requisition



@transaction.atomic
def reject_inventory_requisition(requisition_id, rejected_by_id, rejection_reason):
    """
    Reject an inventory requisition.
    Transition: CREATED/SUBMITTED → REJECTED
    
    Task 20: Inventory requisition rejection service
    
    Args:
        requisition_id: Requisition ID to reject
        rejected_by_id: ID of staff rejecting
        rejection_reason: Reason for rejection
    
    Returns:
        Updated InventoryRequisition object
    
    Raises:
        InvalidStockUpdate: If requisition not found or invalid state
    """
    try:
        requisition = InventoryRequisition.objects.get(id=requisition_id)
    except InventoryRequisition.DoesNotExist:
        raise InvalidStockUpdate(f"Requisition {requisition_id} not found")
    
    if requisition.status not in ['CREATED', 'SUBMITTED']:
        raise InvalidStockUpdate(
            f"Cannot reject requisition with status '{requisition.status}'. "
            f"Only CREATED or SUBMITTED requisitions can be rejected."
        )
    
    if not rejection_reason or not str(rejection_reason).strip():
        raise InvalidStockUpdate("Rejection reason is required")
    
    # Transition to REJECTED
    requisition.status = 'REJECTED'
    requisition.rejection_reason = rejection_reason.strip()
    requisition.save()
    
    # Log audit trail
    log_audit_action(
        user_id=rejected_by_id,
        action_type='UPDATE',
        entity_type='InventoryRequisition',
        entity_id=requisition.id,
        details={'status': 'REJECTED', 'reason': rejection_reason[:100]}
    )

    # ── PHC-BR-11: Requisition Rejection Notification ────────────────────────
    from notification.views import healthcare_center_notif
    try:
        medicine_name = requisition.medicine.medicine_name
        msg = f"Req #{requisition.id} ({medicine_name}) was rejected. Reason: {rejection_reason[:100]}"
        healthcare_center_notif(
            sender=None,
            recipient=requisition.created_by.user,
            type='req_rejected',
            message=msg,
        )
    except Exception:
        pass  # Never let notification failure break the main transaction

    return requisition


@transaction.atomic
def fulfill_inventory_requisition(requisition_id, fulfilled_by_id, quantity_fulfilled):
    """
    Mark an approved inventory requisition as fulfilled (PHC-UC-14).
    Transition: APPROVED → FULFILLED

    Called by PHC Staff after the ordered supplies have been physically received.

    Args:
        requisition_id: InventoryRequisition PK to close
        fulfilled_by_id: ExtraInfo ID of the staff member fulfilling
        quantity_fulfilled: Actual quantity received (may differ from requested)

    Returns:
        Updated InventoryRequisition with status FULFILLED

    Raises:
        InvalidStockUpdate: If requisition not found, wrong status, or qty invalid
    """
    try:
        requisition = InventoryRequisition.objects.get(id=requisition_id)
    except InventoryRequisition.DoesNotExist:
        raise InvalidStockUpdate(f"Requisition {requisition_id} not found")

    if requisition.status != 'APPROVED':
        raise InvalidStockUpdate(
            f"Cannot fulfill requisition with status '{requisition.status}'. "
            f"Only APPROVED requisitions can be marked as fulfilled."
        )

    if not quantity_fulfilled or int(quantity_fulfilled) < 1:
        raise InvalidStockUpdate("Quantity fulfilled must be at least 1")

    # Transition to FULFILLED
    requisition.status = 'FULFILLED'
    requisition.quantity_fulfilled = int(quantity_fulfilled)
    requisition.fulfilled_date = timezone.now().date()   # DateField, not DateTimeField
    try:
        from applications.globals.models import ExtraInfo
        requisition.fulfilled_by = ExtraInfo.objects.get(id=fulfilled_by_id)
    except Exception:
        pass  # gracefully skip if ExtraInfo not found
    requisition.save()

    # Log audit trail
    log_audit_action(
        user_id=fulfilled_by_id,
        action_type='UPDATE',
        entity_type='InventoryRequisition',
        entity_id=requisition.id,
        details={
            'status': 'FULFILLED',
            'quantity_requested': requisition.quantity_requested,
            'quantity_fulfilled': quantity_fulfilled,
        }
    )

    return requisition


# ===========================================================================
# ── PHC-UC-11: AMBULANCE USAGE LOG SERVICE ─────────────────────────────
# ===========================================================================

@transaction.atomic
def create_ambulance_log(log_data, logged_by_id):
    """
    Create a new ambulance usage log entry (PHC-UC-11).
    Enforces PHC-BR-09 by writing an immutable audit trail entry.

    Args:
        log_data: dict with keys — patient_name, destination, call_date,
                  call_time, ambulance (optional FK ID), purpose, contact_number
        logged_by_id: ExtraInfo ID of the PHC staff recording the entry

    Returns:
        new AmbulanceLog instance

    Raises:
        InvalidStockUpdate: if required fields are missing
    """
    from applications.globals.models import ExtraInfo

    patient_name = (log_data.get('patient_name') or '').strip()
    destination  = (log_data.get('destination') or '').strip()
    call_date    = log_data.get('call_date')
    call_time    = log_data.get('call_time')

    if not patient_name:
        raise InvalidStockUpdate('patient_name is required.')
    if not destination:
        raise InvalidStockUpdate('destination is required.')
    if not call_date:
        raise InvalidStockUpdate('call_date is required.')
    if not call_time:
        raise InvalidStockUpdate('call_time is required.')

    ambulance_obj = None
    ambulance_data = log_data.get('ambulance')
    if ambulance_data:
        if isinstance(ambulance_data, AmbulanceRecordsV2):
            ambulance_obj = ambulance_data
        else:
            try:
                ambulance_obj = AmbulanceRecordsV2.objects.get(id=ambulance_data)
            except AmbulanceRecordsV2.DoesNotExist:
                raise InvalidStockUpdate(f"Ambulance with id {ambulance_data} not found.")

    logged_by_obj = None
    try:
        logged_by_obj = ExtraInfo.objects.get(id=logged_by_id)
    except ExtraInfo.DoesNotExist:
        pass  # Gracefully allow log even if staff ExtraInfo not resolved

    entry = AmbulanceLog.objects.create(
        ambulance=ambulance_obj,
        patient_name=patient_name,
        destination=destination,
        call_date=call_date,
        call_time=call_time,
        purpose=log_data.get('purpose', ''),
        contact_number=log_data.get('contact_number', ''),
        logged_by=logged_by_obj,
    )

    # PHC-BR-09 S-LOG-AUDIT: Record the ambulance dispatch event
    log_audit_action(
        user_id=logged_by_id,
        action_type='CREATE',
        entity_type='AmbulanceLog',
        entity_id=entry.id,
        details={
            'patient_name': patient_name,
            'destination': destination,
            'call_date': str(call_date),
            'call_time': str(call_time),
            'ambulance_id': ambulance_obj.id if ambulance_obj else None,
        }
    )

    return entry


@transaction.atomic
def delete_ambulance_log(log_id, deleted_by_id):
    """
    Delete an ambulance log entry (PHC-UC-11 admin correction).
    Logs the deletion for PHC-BR-09 audit compliance.
    """
    try:
        entry = AmbulanceLog.objects.get(id=log_id)
    except AmbulanceLog.DoesNotExist:
        raise InvalidStockUpdate(f"Ambulance log entry #{log_id} not found.")

    entry_id = entry.id
    entry.delete()

    log_audit_action(
        user_id=deleted_by_id,
        action_type='DELETE',
        entity_type='AmbulanceLog',
        entity_id=entry_id,
        details={'reason': 'Deleted by PHC staff'}
    )


# ===========================================================================
# ── ANNOUNCEMENTS — PHC-UC-12 ─────────────────────────────────────────────
# ===========================================================================

def _notify_all_portal_users(sender_user, title):
    """
    Internal helper: broadcast a portal notification about a new announcement
    to every active Django user.

    Implements PHC-UC-17 (S-NOTIFY) for the announcement broadcast event.
    Wrapped in try/except so a notification failure never aborts the
    announcement creation transaction.
    """
    from django.contrib.auth import get_user_model
    from notification.views import healthcare_center_notif

    User = get_user_model()
    active_users = User.objects.filter(is_active=True)

    for user in active_users:
        try:
            healthcare_center_notif(
                sender=sender_user,
                recipient=user,
                type='new_announce',
                message=f"\U0001f4e2 Health Notice: {title}",
            )
        except Exception:
            pass  # Skip individuals that fail; never abort the broadcast


@transaction.atomic
def create_announcement(data, created_by_id, sender_user=None):
    """
    Create a new HealthAnnouncement and broadcast a portal notification
    to ALL active users (PHC-UC-12, PHC-UC-17).

    Args:
        data (dict): Validated data with keys: title, content, category,
                     priority (optional), expires_at (optional).
        created_by_id: ExtraInfo PK of the compounder creating this.
        sender_user: auth.User object of the creator (for notify.send sender).

    Returns:
        HealthAnnouncement instance

    Raises:
        InvalidStockUpdate: if required fields are not provided.
    """
    from applications.globals.models import ExtraInfo

    title   = (data.get('title') or '').strip()
    content = (data.get('content') or '').strip()

    if not title:
        raise InvalidStockUpdate('title is required for an announcement.')
    if not content:
        raise InvalidStockUpdate('content is required for an announcement.')

    created_by_obj = None
    if created_by_id:
        try:
            created_by_obj = ExtraInfo.objects.get(id=created_by_id)
        except ExtraInfo.DoesNotExist:
            pass

    announcement = HealthAnnouncement.objects.create(
        title=title,
        content=content,
        category=data.get('category', 'GENERAL'),
        priority=data.get('priority', 0),
        expires_at=data.get('expires_at'),
        created_by=created_by_obj,
        is_active=True,
    )

    # PHC-BR-09: Audit trail
    log_audit_action(
        user_id=created_by_id,
        action_type='CREATE',
        entity_type='HealthAnnouncement',
        entity_id=announcement.id,
        details={'title': title, 'category': announcement.category},
    )

    # PHC-UC-17: Broadcast portal notification to ALL users
    _notify_all_portal_users(sender_user=sender_user, title=title)

    return announcement


@transaction.atomic
def deactivate_announcement(announcement_id, deactivated_by_id):
    """
    Soft-delete a HealthAnnouncement by setting is_active=False (PHC-UC-12).
    Audit-logged per PHC-BR-09.

    Args:
        announcement_id: PK of the HealthAnnouncement to deactivate.
        deactivated_by_id: ExtraInfo PK of the staff member performing the action.
    """
    try:
        announcement = HealthAnnouncement.objects.get(id=announcement_id)
    except HealthAnnouncement.DoesNotExist:
        raise InvalidStockUpdate(f'Announcement #{announcement_id} not found.')

    announcement.is_active = False
    announcement.save(update_fields=['is_active', 'updated_at'])

    log_audit_action(
        user_id=deactivated_by_id,
        action_type='DELETE',
        entity_type='HealthAnnouncement',
        entity_id=announcement_id,
        details={'title': announcement.title, 'action': 'deactivated'},
    )

    return announcement
