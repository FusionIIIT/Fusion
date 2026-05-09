"""
Health Center Module Models
============================
Design: Database schema for Primary Health Center Management System
Based on artifacts: Use Cases, Business Rules, and Integration requirements

Architecture:
  - Models define schema, relationships, choices, validations
  - No business logic here — belongs in services.py
  - All choices defined as TextChoices/IntegerChoices for self-documentation
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from datetime import timedelta, date
from applications.globals.models import ExtraInfo, DepartmentInfo


# ===========================================================================
# ── CHOICES / CONSTANTS ──────────────────────────────────────────────────
# ===========================================================================

class UserTypeChoices(models.TextChoices):
    """User types in the PHC system"""
    PATIENT = 'PATIENT', 'Patient'
    PHC_STAFF = 'PHC_STAFF', 'PHC Staff'
    APPROVING_AUTHORITY = 'APPROVING_AUTHORITY', 'Approving Authority'
    ACCOUNTS_AUDIT = 'ACCOUNTS_AUDIT', 'Accounts & Audit'
    ADMIN = 'ADMIN', 'Administrator'


class StaffTypeChoices(models.TextChoices):
    """Types of medical staff"""
    DOCTOR = 'DOCTOR', 'Doctor'
    NURSE = 'NURSE', 'Nurse'
    PHARMACIST = 'PHARMACIST', 'Pharmacist'
    LAB_TECHNICIAN = 'LAB_TECHNICIAN', 'Lab Technician'
    COMPOUNDER = 'COMPOUNDER', 'Compounder'
    RECEPTIONIST = 'RECEPTIONIST', 'Receptionist'


class AppointmentStatusChoices(models.TextChoices):
    """Appointment status flow"""
    SCHEDULED = 'SCHEDULED', 'Scheduled'
    CHECKED_IN = 'CHECKED_IN', 'Checked In'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    COMPLETED = 'COMPLETED', 'Completed'
    CANCELLED = 'CANCELLED', 'Cancelled'
    NO_SHOW = 'NO_SHOW', 'No Show'


class AppointmentTypeChoices(models.TextChoices):
    """Types of appointments"""
    OPD = 'OPD', 'Out Patient Department'
    EMERGENCY = 'EMERGENCY', 'Emergency'
    FOLLOW_UP = 'FOLLOW_UP', 'Follow Up'
    VACCINATION = 'VACCINATION', 'Vaccination'
    LAB_TEST = 'LAB_TEST', 'Lab Test'
    WELLNESS_CHECK = 'WELLNESS_CHECK', 'Wellness Check'


class DayOfWeekChoices(models.TextChoices):
    """Days of the week"""
    MONDAY = 'MONDAY', 'Monday'
    TUESDAY = 'TUESDAY', 'Tuesday'
    WEDNESDAY = 'WEDNESDAY', 'Wednesday'
    THURSDAY = 'THURSDAY', 'Thursday'
    FRIDAY = 'FRIDAY', 'Friday'
    SATURDAY = 'SATURDAY', 'Saturday'
    SUNDAY = 'SUNDAY', 'Sunday'


class AttendanceStatusChoices(models.TextChoices):
    """Doctor attendance status - PHC-BR-01"""
    SCHEDULED = 'SCHEDULED', 'Scheduled'
    AVAILABLE = 'AVAILABLE', 'Available'
    DEPARTED = 'DEPARTED', 'Departed'
    ON_BREAK = 'ON_BREAK', 'On Break'


class ReimbursementStatusChoices(models.TextChoices):
    """Reimbursement claim status journey - PHC-BR-08"""
    DRAFT = 'DRAFT', 'Draft'
    SUBMITTED = 'SUBMITTED', 'Submitted'
    PHC_REVIEW = 'PHC_REVIEW', 'PHC Staff Review'
    ACCOUNTS_VERIFICATION = 'ACCOUNTS_VERIFICATION', 'Accounts Verification'
    SANCTION_REVIEW = 'SANCTION_REVIEW', 'Sanction Review Required'
    SANCTION_APPROVED = 'SANCTION_APPROVED', 'Sanctioned'
    FINAL_PAYMENT = 'FINAL_PAYMENT', 'Final Payment Processing'
    REIMBURSED = 'REIMBURSED', 'Reimbursed'
    REJECTED = 'REJECTED', 'Rejected'
    WITHDRAWN = 'WITHDRAWN', 'Withdrawn'


class RequisitionStatusChoices(models.TextChoices):
    """Inventory requisition status - PHC-WF-02"""
    CREATED = 'CREATED', 'Created'
    SUBMITTED = 'SUBMITTED', 'Submitted'
    APPROVED = 'APPROVED', 'Approved'
    REJECTED = 'REJECTED', 'Rejected'
    FULFILLED = 'FULFILLED', 'Fulfilled & Closed'


class BloodGroupChoices(models.TextChoices):
    """Blood group types"""
    A_POSITIVE = 'A+', 'A+'
    A_NEGATIVE = 'A-', 'A-'
    B_POSITIVE = 'B+', 'B+'
    B_NEGATIVE = 'B-', 'B-'
    AB_POSITIVE = 'AB+', 'AB+'
    AB_NEGATIVE = 'AB-', 'AB-'
    O_POSITIVE = 'O+', 'O+'
    O_NEGATIVE = 'O-', 'O-'


class PrescriptionStatusChoices(models.TextChoices):
    """Prescription status flow - PHC-BR-02"""
    ISSUED = 'ISSUED', 'Issued'
    DISPENSED = 'DISPENSED', 'Dispensed'
    CANCELLED = 'CANCELLED', 'Cancelled'
    COMPLETED = 'COMPLETED', 'Completed'


class ComplaintStatusChoices(models.TextChoices):
    """Complaint status flow - Task 4"""
    SUBMITTED = 'SUBMITTED', 'Submitted'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    RESOLVED = 'RESOLVED', 'Resolved'
    CLOSED = 'CLOSED', 'Closed'


class AmbulanceStatusChoices(models.TextChoices):
    """Ambulance availability status - Task 4"""
    AVAILABLE = 'AVAILABLE', 'Available'
    ASSIGNED = 'ASSIGNED', 'Assigned'
    IN_TRANSIT = 'IN_TRANSIT', 'In Transit'
    MAINTENANCE = 'MAINTENANCE', 'Maintenance'
    OUT_OF_SERVICE = 'OUT_OF_SERVICE', 'Out of Service'


# ===========================================================================
# ── DOCTOR AND SCHEDULE ──────────────────────────────────────────────────
# ===========================================================================

class Doctor(models.Model):
    """
    Doctor information.
    Links to medical staff record via ExtraInfo if available.
    """
    user = models.OneToOneField(ExtraInfo, on_delete=models.SET_NULL, null=True, blank=True, 
                                related_name='doctor_profile')
    doctor_name = models.CharField(max_length=255)
    doctor_phone = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    specialization = models.CharField(max_length=255)
    registration_number = models.CharField(max_length=100, blank=True)  # Medical council reg
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'health_center_doctor'
        ordering = ['doctor_name']

    def __str__(self):
        return f"Dr. {self.doctor_name} ({self.specialization})"


class DoctorSchedule(models.Model):
    """
    Doctor's weekly schedule master.
    Links doctor to available days and times.
    Used for PHC-UC-01: View Doctor Schedule & Availability
    """
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='schedules')
    day_of_week = models.CharField(max_length=20, choices=DayOfWeekChoices.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room_number = models.CharField(max_length=50, blank=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'health_center_doctor_schedule'
        unique_together = ('doctor', 'day_of_week')
        ordering = ['doctor', 'day_of_week']

    def __str__(self):
        return f"Dr. {self.doctor.doctor_name} - {self.day_of_week} ({self.start_time}-{self.end_time})"


class DoctorAttendance(models.Model):
    """
    Real-time doctor attendance status for current day.
    Updated by PHC staff (PHC-UC-08).
    Used for PHC-BR-01: Display master schedule + real-time status
    """
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='attendance_records')
    attendance_date = models.DateField()
    status = models.CharField(max_length=20, choices=AttendanceStatusChoices.choices)
    marked_by = models.ForeignKey(ExtraInfo, on_delete=models.SET_NULL, null=True, blank=True)  # PHC Staff
    marked_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'health_center_doctor_attendance'
        unique_together = ('doctor', 'attendance_date')
        ordering = ['-attendance_date']

    def __str__(self):
        return f"Dr. {self.doctor.doctor_name} - {self.attendance_date} ({self.status})"


# ===========================================================================
# ── PATIENT HEALTH PROFILE ───────────────────────────────────────────────
# ===========================================================================

class HealthProfile(models.Model):
    """
    Patient health profile and medical history summary.
    One-to-one with ExtraInfo (patient).
    Used for medical consultations and diagnostics.
    """
    patient = models.OneToOneField(ExtraInfo, on_delete=models.CASCADE, related_name='health_profile')
    
    # Blood group
    blood_group = models.CharField(max_length=5, choices=BloodGroupChoices.choices, blank=True)
    
    # Physical measurements
    height_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # cm
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # kg
    
    # Medical history flags
    allergies = models.TextField(blank=True, help_text="Comma-separated list of allergies")
    chronic_conditions = models.TextField(blank=True, help_text="e.g., Diabetes, Hypertension")
    current_medications = models.TextField(blank=True, help_text="Current medications being taken")
    past_surgeries = models.TextField(blank=True)
    family_medical_history = models.TextField(blank=True)
    
    # Insurance information
    has_insurance = models.BooleanField(default=False)
    insurance_provider = models.CharField(max_length=100, blank=True)
    insurance_policy_number = models.CharField(max_length=50, blank=True)
    insurance_valid_until = models.DateField(null=True, blank=True)
    
    # Emergency contact
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True)
    emergency_contact_relation = models.CharField(max_length=50, blank=True)
    
    # System metadata
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'health_center_health_profile'

    def __str__(self):
        return f"Health Profile - {self.patient.id} ({self.patient.user.get_full_name()})"


# ===========================================================================
# ── APPOINTMENTS AND CONSULTATIONS ───────────────────────────────────────
# ===========================================================================

class Appointment(models.Model):
    """
    Patient appointment with a doctor.
    Used for PHC-UC-01 (view availability), booking, cancellation.
    """
    patient = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE, related_name='phc_appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True, 
                              related_name='appointments')
    recorded_doctor_name = models.CharField(max_length=255, blank=True, help_text="Snapshot of doctor name preserved upon hard delete")
    
    appointment_type = models.CharField(max_length=20, choices=AppointmentTypeChoices.choices, 
                                       default=AppointmentTypeChoices.OPD)
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    
    chief_complaint = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=AppointmentStatusChoices.choices, 
                            default=AppointmentStatusChoices.SCHEDULED)
    
    # Timeline tracking
    created_at = models.DateTimeField(auto_now_add=True)
    checked_in_at = models.DateTimeField(null=True, blank=True)
    consultation_start = models.DateTimeField(null=True, blank=True)
    consultation_end = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)

    class Meta:
        db_table = 'health_center_appointment'
        ordering = ['-appointment_date', '-appointment_time']

    def __str__(self):
        return f"Apt #{self.id} - {self.patient.id} with Dr. {self.doctor.doctor_name if self.doctor else 'N/A'}"

    def save(self, *args, **kwargs):
        if self.doctor and not self.recorded_doctor_name:
            self.recorded_doctor_name = self.doctor.doctor_name
        super().save(*args, **kwargs)


class Consultation(models.Model):
    """
    Medical consultation record (visit record).
    Created by doctor/staff when patient visits.
    Links to prescription and vitals.
    Used for PHC-UC-02: Medical History, PHC-UC-06: Manage Patient Records
    """
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, 
                                      related_name='consultation', null=True, blank=True)
    patient = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE, related_name='consultations')
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)
    recorded_doctor_name = models.CharField(max_length=255, blank=True, help_text="Snapshot of doctor name preserved upon hard delete")
    
    consultation_date = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Vitals (PHC-BR-01 compliant)
    blood_pressure_systolic = models.IntegerField(null=True, blank=True)
    blood_pressure_diastolic = models.IntegerField(null=True, blank=True)
    pulse_rate = models.IntegerField(null=True, blank=True)
    temperature = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    oxygen_saturation = models.IntegerField(null=True, blank=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Clinical notes
    chief_complaint = models.TextField()
    history_of_present_illness = models.TextField(blank=True)
    examination_findings = models.TextField(blank=True)
    provisional_diagnosis = models.TextField(blank=True)
    final_diagnosis = models.TextField(blank=True)
    
    # Treatment plan
    treatment_plan = models.TextField(blank=True)
    advice = models.TextField(blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    
    # Ambulance request
    ambulance_requested = models.CharField(
        max_length=3, 
        choices=[('yes', 'Yes'), ('no', 'No')], 
        default='no'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'health_center_consultation'
        ordering = ['-consultation_date']

    def __str__(self):
        return f"Consultation #{self.id} - {self.patient.id} on {self.consultation_date.date()}"

    def save(self, *args, **kwargs):
        if self.doctor and not self.recorded_doctor_name:
            self.recorded_doctor_name = self.doctor.doctor_name
        super().save(*args, **kwargs)


# ===========================================================================
# ── PRESCRIPTIONS AND MEDICINES ──────────────────────────────────────────
# ===========================================================================

class Medicine(models.Model):
    """
    Master list of all available medicines.
    Inventory management, stock tracking.
    """
    medicine_name = models.CharField(max_length=255, unique=True)
    brand_name = models.CharField(max_length=255, blank=True)
    generic_name = models.CharField(max_length=255, blank=True)
    constituents = models.TextField(blank=True)
    manufacturer_name = models.CharField(max_length=255, blank=True)
    pack_size_label = models.CharField(max_length=100, blank=True)
    unit = models.CharField(max_length=50, default='tablets')  # tablets, ml, strips, etc.
    reorder_threshold = models.IntegerField(default=10, validators=[MinValueValidator(1)])  # PHC-BR-07
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'health_center_medicine'
        ordering = ['medicine_name']

    def __str__(self):
        return f"{self.medicine_name} ({self.brand_name})"


class Stock(models.Model):
    """
    Master stock entry for a medicine.
    Tracks total quantity and last update.
    Quantity is auto-calculated from Expiry batches (never edit directly).
    Used for PHC-UC-09, PHC-UC-11: Inventory management
    """
    medicine = models.OneToOneField(Medicine, on_delete=models.CASCADE, related_name='stock')
    total_qty = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'health_center_stock'
        ordering = ['medicine']

    def __str__(self):
        return f"{self.medicine.medicine_name} - Total: {self.total_qty}u"


class Expiry(models.Model):
    """
    Expiry batch entry for stock.
    One Stock can have many Expiry batches (1:M relationship).
    Implements FIFO logic: sorted by expiry_date for dispensing.
    Used for PHC-UC-09: Inventory management, PHC-WF-01: Prescription dispensing
    """
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='expiry_batches')
    batch_no = models.CharField(max_length=100)
    qty = models.IntegerField(validators=[MinValueValidator(1)])
    expiry_date = models.DateField()
    is_returned = models.BooleanField(default=False)
    returned_qty = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    return_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'health_center_expiry'
        ordering = ['expiry_date']  # FIFO: earliest expiry first
        unique_together = ('stock', 'batch_no')

    def __str__(self):
        status = "Returned" if self.is_returned else "Active"
        return f"{self.stock.medicine.medicine_name} - Batch {self.batch_no} ({self.qty}u, Exp: {self.expiry_date}, {status})"


# Legacy alias for backward compatibility
class InventoryStock(Stock):
    """
    DEPRECATED: Use Stock model instead.
    Kept for backward compatibility with existing code.
    """
    class Meta:
        proxy = True
        db_table = 'health_center_stock'  # Same table as Stock


class Prescription(models.Model):
    """
    Doctor prescription linked to consultation.
    Can have multiple medicines (PrescribedMedicine).
    Implements status workflow: issued → dispensed → completed/cancelled
    Used for PHC-UC-02: Medical History, PHC-UC-04: Reimbursement, PHC-WF-01: Prescription
    """
    consultation = models.OneToOneField(Consultation, on_delete=models.CASCADE, 
                                       related_name='prescription')
    patient = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE, related_name='prescriptions')
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)
    recorded_doctor_name = models.CharField(max_length=255, blank=True, help_text="Snapshot of doctor name preserved upon hard delete")
    
    issued_date = models.DateField(auto_now_add=True, db_index=True)  # Task 3: issued_date
    status = models.CharField(max_length=20, choices=PrescriptionStatusChoices.choices, 
                            default=PrescriptionStatusChoices.ISSUED, db_index=True)  # Task 3: status field
    
    # Prescription details
    details = models.TextField(blank=True)
    special_instructions = models.TextField(blank=True)
    test_recommended = models.CharField(max_length=255, blank=True)
    follow_up_suggestions = models.TextField(blank=True)
    
    # For dependents (family members) - optional
    is_for_dependent = models.BooleanField(default=False)
    dependent_name = models.CharField(max_length=255, blank=True)
    dependent_relation = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'health_center_prescription'
        ordering = ['-issued_date']

    def __str__(self):
        return f"Rx#{self.id} - {self.patient.id} ({self.issued_date}) [{self.status}]"

    def save(self, *args, **kwargs):
        if self.doctor and not self.recorded_doctor_name:
            self.recorded_doctor_name = self.doctor.doctor_name
        super().save(*args, **kwargs)

    # Backward compatibility aliases
    @property
    def prescription_date(self):
        """Backward compatibility for prescription_date → issued_date"""
        return self.issued_date


class PrescribedMedicine(models.Model):
    """
    Individual medicines in a prescription.
    Links medicine to prescription with dosage details.
    Tracks both prescribed quantity and dispensed quantity (for pharmacy management).
    Task 3: Includes qty_prescribed, qty_dispensed, notes, and expiry_used.
    """
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, 
                                    related_name='prescribed_medicines')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    
    # Dosage prescription
    qty_prescribed = models.IntegerField(validators=[MinValueValidator(1)])  # Task 3: qty_prescribed
    days = models.IntegerField(validators=[MinValueValidator(1)])
    times_per_day = models.IntegerField(validators=[MinValueValidator(1)])
    instructions = models.TextField(blank=True)  # e.g., "with food", "before sleep"
    notes = models.TextField(blank=True)  # Task 3: notes field
    
    # Dispensing tracking
    qty_dispensed = models.IntegerField(default=0, validators=[MinValueValidator(0)])  # Task 3: qty_dispensed
    is_dispensed = models.BooleanField(default=False)
    dispensed_date = models.DateField(null=True, blank=True)
    
    # Revocation tracking
    is_revoked = models.BooleanField(default=False)
    revoked_date = models.DateField(null=True, blank=True)
    
    # Stock/Expiry used for dispensing (references new model structure)
    expiry_used = models.ForeignKey(Expiry, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='prescribed_medicines')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'health_center_prescribed_medicine'
        ordering = ['prescription', 'created_at']

    def clean(self):
        """Validate that qty_dispensed <= qty_prescribed"""
        if self.qty_dispensed > self.qty_prescribed:
            raise ValidationError(
                f"Dispensed quantity ({self.qty_dispensed}) cannot exceed prescribed quantity ({self.qty_prescribed})"
            )

    def __str__(self):
        dispensed_str = f", Dispensed: {self.qty_dispensed}u" if self.is_dispensed else ""
        return f"{self.medicine.medicine_name} - Prescribed: {self.qty_prescribed}u × {self.times_per_day}x{self.days}d{dispensed_str}"



# ===========================================================================
# ── COMPLAINTS ───────────────────────────────────────────────────────────
# ===========================================================================

class ComplaintV2(models.Model):
    """
    Patient complaint tracking system.
    Used for PHC-UC-11: File Complaint, PHC-UC-12: Track Complaint Response
    Task 4: Core complaint management model
    """
    patient = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE, related_name='complaints')
    title = models.CharField(max_length=255)
    description = models.TextField()
    
    # Categorization
    COMPLAINT_CATEGORIES = [
        ('SERVICE', 'Service Quality'),
        ('STAFF', 'Staff Behavior'),
        ('FACILITIES', 'Facilities'),
        ('MEDICAL', 'Medical Care'),
        ('OTHER', 'Other'),
    ]
    category = models.CharField(max_length=20, choices=COMPLAINT_CATEGORIES)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=ComplaintStatusChoices.choices, 
                            default=ComplaintStatusChoices.SUBMITTED)
    
    created_date = models.DateTimeField(auto_now_add=True)
    resolved_date = models.DateTimeField(null=True, blank=True)
    
    # Resolution tracking
    resolution_notes = models.TextField(blank=True)
    resolved_by = models.ForeignKey(ExtraInfo, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='resolved_complaints')
    
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'health_center_complaint_v2'
        ordering = ['-created_date']

    def __str__(self):
        return f"Complaint#{self.id} - {self.title} [{self.status}]"


# ===========================================================================
# ── HOSPITAL ADMISSIONS ──────────────────────────────────────────────────
# ===========================================================================

class HospitalAdmit(models.Model):
    """
    Hospital admission tracking for patients referred from PHC.
    Uses for PHC-UC-10: Refer to Hospital, PHC-UC-15: Track Admission Status
    Task 4: Hospital referral and admission management
    """
    patient = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE, related_name='hospital_admissions')
    patient_name = models.CharField(max_length=255, blank=True)  # Denormalized for audit trail
    
    # Hospital information
    hospital_id = models.CharField(max_length=100)  # External hospital ID or name
    hospital_name = models.CharField(max_length=255)
    
    # Admission timing
    admission_date = models.DateField()
    discharge_date = models.DateField(null=True, blank=True)
    
    # Medical details
    reason = models.TextField()  # Reason for admission
    summary = models.TextField(blank=True)  # Discharge summary/notes
    
    # Referral details
    referred_by = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='referrals')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'health_center_hospital_admit'
        ordering = ['-admission_date']

    def save(self, *args, **kwargs):
        """Auto-populate patient_name for audit trail"""
        if self.patient and not self.patient_name:
            self.patient_name = self.patient.user.get_full_name()
        super().save(*args, **kwargs)

    def clean(self):
        """Validate that admission_date <= discharge_date"""
        if self.discharge_date and self.admission_date > self.discharge_date:
            raise ValidationError("Admission date must be before discharge date")

    def __str__(self):
        status = f"Discharged {self.discharge_date}" if self.discharge_date else "Admitted"
        return f"Admit#{self.id} - {self.hospital_name} ({status})"


# ===========================================================================
# ── AMBULANCE RECORDS ────────────────────────────────────────────────────
# ===========================================================================

class AmbulanceRecordsV2(models.Model):
    """
    Ambulance fleet management records.
    Task 4: CRUD-only operations by compounder (no patient-initiated requests).
    Implements PHC-UC-16: Manage Ambulance Records, PHC-WF-03: Ambulance Dispatch
    """
    # Vehicle information
    vehicle_type = models.CharField(max_length=50)  # e.g., "Type A", "Type B"
    registration_number = models.CharField(max_length=50, unique=True)
    
    # Driver information
    driver_name = models.CharField(max_length=255)
    driver_contact = models.CharField(max_length=15)
    driver_license = models.CharField(max_length=100, blank=True)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=AmbulanceStatusChoices.choices,
                            default=AmbulanceStatusChoices.AVAILABLE)
    
    # Current assignment (optional FK to a model that tracks dispatch)
    # For now, storing as CharField for flexibility
    current_assignment = models.CharField(max_length=255, blank=True, null=True)
    
    # Maintenance tracking
    last_maintenance_date = models.DateField(null=True, blank=True)
    next_maintenance_due = models.DateField(null=True, blank=True)
    
    # Operational details
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'health_center_ambulance_records_v2'
        ordering = ['registration_number']

    def __str__(self):
        return f"Ambulance {self.registration_number} ({self.vehicle_type}) - {self.status}"


# ===========================================================================
# ── AMBULANCE USAGE LOG ──────────────────────────────────────────────────
# ===========================================================================

class AmbulanceLog(models.Model):
    """
    Chronological log of every ambulance dispatch event.
    Implements PHC-UC-11: Log Ambulance Usage, PHC-BR-09: Data Audit Trail.

    This model is DISTINCT from AmbulanceRecordsV2 (which tracks the fleet).
    This model records who was transported, when, and where — forming an
    immutable operational log as required by PHC-BR-09 (S-LOG-AUDIT).
    """
    # Which vehicle was used (optional — log may exist before fleet record)
    ambulance = models.ForeignKey(
        AmbulanceRecordsV2,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usage_logs',
        help_text='The specific ambulance vehicle used for this trip (optional).'
    )

    # Dispatch details — required fields per PHC-UC-11 M2
    patient_name = models.CharField(
        max_length=255,
        help_text='Full name of the patient/caller being transported.'
    )
    destination = models.CharField(
        max_length=500,
        help_text='Destination hospital, clinic, or address.'
    )

    # Date and time of the call / dispatch
    call_date = models.DateField(help_text='Date the ambulance was dispatched.')
    call_time = models.TimeField(help_text='Time the ambulance was dispatched.')

    # Optional additional information
    purpose = models.TextField(
        blank=True,
        help_text='Brief description of the medical emergency or reason for dispatch.'
    )
    contact_number = models.CharField(
        max_length=15,
        blank=True,
        help_text='Contact number of the patient or caller.'
    )

    # Audit fields — PHC-BR-09
    logged_by = models.ForeignKey(
        ExtraInfo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ambulance_logs_created',
        help_text='PHC Staff member who created this log entry.'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'health_center_ambulance_log'
        ordering = ['-call_date', '-call_time']
        verbose_name = 'Ambulance Usage Log'
        verbose_name_plural = 'Ambulance Usage Logs'

    def __str__(self):
        return (
            f"AmbLog#{self.id} - {self.patient_name} → {self.destination} "
            f"on {self.call_date} at {self.call_time}"
        )


# ===========================================================================
# ── REIMBURSEMENT CLAIMS ─────────────────────────────────────────────────
# ===========================================================================

class ReimbursementClaim(models.Model):
    """
    Employee medical bill reimbursement claim.
    Implements PHC-UC-04, PHC-WF-01 (Multi-stage approval workflow)
    """
    patient = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE, 
                                related_name='reimbursement_claims')
    
    # Claim details
    prescription = models.ForeignKey(Prescription, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='reimbursement_claims')
    
    claim_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    expense_date = models.DateField(db_index=True)  # PHC-BR-06
    submission_date = models.DateField(auto_now_add=True)
    description = models.TextField()
    
    # Workflow status - PHC-BR-08
    status = models.CharField(max_length=30, choices=ReimbursementStatusChoices.choices,
                            default=ReimbursementStatusChoices.DRAFT, db_index=True)
    
    # Approval chain tracking
    phc_staff_review_date = models.DateField(null=True, blank=True)
    phc_staff_remarks = models.TextField(blank=True)
    phc_staff_approved = models.BooleanField(default=False)
    
    accounts_verification_date = models.DateField(null=True, blank=True)
    accounts_remarks = models.TextField(blank=True)
    accounts_verified = models.BooleanField(default=False)
    
    sanction_required = models.BooleanField(default=False)  # Based on amount
    approving_authority_date = models.DateField(null=True, blank=True)
    approving_authority_remarks = models.TextField(blank=True)
    is_sanctioned = models.BooleanField(default=False)
    
    payment_date = models.DateField(null=True, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)
    
    is_rejected = models.BooleanField(default=False)
    rejection_reason = models.TextField(blank=True)
    
    # Metadata
    created_by = models.ForeignKey(ExtraInfo, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='claims_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'health_center_reimbursement_claim'
        ordering = ['-submission_date']

    def __str__(self):
        return f"Claim#{self.id} - {self.patient.id} (₹{self.claim_amount}) - {self.status}"


class ClaimDocument(models.Model):
    """
    Supporting documents for reimbursement claim.
    Stores bills, prescriptions, receipts, etc.
    """
    claim = models.ForeignKey(ReimbursementClaim, on_delete=models.CASCADE, 
                             related_name='documents')
    
    document_name = models.CharField(max_length=255)
    document_file = models.FileField(upload_to='health_center/claims/%Y/%m/')
    document_type = models.CharField(max_length=100)  # e.g., "bill", "prescription", "receipt"
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # Verification
    verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(ExtraInfo, on_delete=models.SET_NULL, null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'health_center_claim_document'

    def __str__(self):
        return f"Doc - {self.claim.id} ({self.document_type})"


# ===========================================================================
# ── INVENTORY REQUISITIONS ───────────────────────────────────────────────
# ===========================================================================

class InventoryRequisition(models.Model):
    """
    Inventory requisition request for purchasing medicines.
    Implements PHC-WF-02: Procurement workflow
    """
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, 
                                related_name='requisitions')
    
    quantity_requested = models.IntegerField(validators=[MinValueValidator(1)])
    status = models.CharField(max_length=20, choices=RequisitionStatusChoices.choices,
                            default=RequisitionStatusChoices.CREATED)
    
    created_by = models.ForeignKey(ExtraInfo, on_delete=models.SET_NULL, null=True, blank=True)
    created_date = models.DateField(auto_now_add=True)
    
    # Approval by authority
    approved_by = models.ForeignKey(ExtraInfo, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='approved_requisitions')
    approved_date = models.DateField(null=True, blank=True)
    approval_remarks = models.TextField(blank=True)
    
    # Fulfillment tracking
    quantity_fulfilled = models.IntegerField(default=0)
    fulfilled_date = models.DateField(null=True, blank=True)
    fulfilled_by = models.ForeignKey(ExtraInfo, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='fulfilled_requisitions')
    
    rejection_reason = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'health_center_inventory_requisition'
        ordering = ['-created_date']

    def __str__(self):
        return f"Req#{self.id} - {self.medicine.medicine_name} (x{self.quantity_requested})"


# ===========================================================================
# ── SYSTEM ALERTS AND AUDIT ─────────────────────────────────────────────
# ===========================================================================

class LowStockAlert(models.Model):
    """
    Automatic alert when medicine stock falls below reorder threshold.
    Implements PHC-BR-07, PHC-UC-18: Low-Stock Alerts
    """
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, 
                                related_name='low_stock_alerts')
    
    current_stock = models.IntegerField()
    reorder_threshold = models.IntegerField()
    alert_triggered_at = models.DateTimeField(auto_now_add=True)
    acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(ExtraInfo, on_delete=models.SET_NULL, null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'health_center_low_stock_alert'
        ordering = ['-alert_triggered_at']

    def __str__(self):
        return f"Alert - {self.medicine.medicine_name} (Stock: {self.current_stock})"


class AuditLog(models.Model):
    """
    Immutable audit trail for all sensitive actions.
    Implements PHC-BR-09: Data Audit Trail Requirement
    """
    ACTION_TYPES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('APPROVE', 'Approve'),
        ('REJECT', 'Reject'),
        ('VIEW', 'View'),
    ]
    
    user = models.ForeignKey(ExtraInfo, on_delete=models.SET_NULL, null=True, blank=True)
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    entity_type = models.CharField(max_length=100)  # e.g., 'Prescription', 'ReimbursementClaim'
    entity_id = models.IntegerField()
    action_details = models.JSONField()  # Detailed change info
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = 'health_center_audit_log'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['entity_type', 'entity_id']),
        ]

    def __str__(self):
        return f"{self.action_type} - {self.entity_type}#{self.entity_id} by {self.user}"


# ===========================================================================
# ── HEALTH ANNOUNCEMENTS (PHC-UC-12) ────────────────────────────────────
# ===========================================================================

class HealthAnnouncement(models.Model):
    """
    Broadcasts health advisories, schedule changes, and emergency notices
    to all portal users.

    Implements PHC-UC-12: Broadcast Health Announcements
    PHC-BR-09: All create/deactivate events are audit-logged.
    PHC-WF-03: Announcement lifecycle — ACTIVE → INACTIVE (soft delete)
    """
    CATEGORY_CHOICES = [
        ('GENERAL',          'General'),
        ('HEALTH_ADVISORY',  'Health Advisory'),
        ('SCHEDULE_CHANGE',  'Schedule Change'),
        ('EMERGENCY',        'Emergency'),
        ('VACCINATION',      'Vaccination Drive'),
    ]

    title      = models.CharField(max_length=200)
    content    = models.TextField()
    category   = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='GENERAL')
    is_active  = models.BooleanField(default=True)
    # Higher priority announcements appear first
    priority   = models.IntegerField(default=0)
    created_by = models.ForeignKey(
        ExtraInfo, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_announcements',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Optional auto-expiry: announcement hidden after this datetime
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'health_center_announcement'
        ordering = ['-priority', '-created_at']

    def __str__(self):
        status = 'ACTIVE' if self.is_active else 'INACTIVE'
        return f"[{status}] {self.category}: {self.title}"
