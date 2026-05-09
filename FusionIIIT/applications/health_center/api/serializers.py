"""
Health Center API Serializers
==============================
Serialization layer for API requests/responses.

Responsibility:
  - Field-level validation only
  - No business logic
  - Nested serializers for related data
  - Read/Write serializers separated where needed
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator
from datetime import time, timedelta, date
from applications.globals.models import ExtraInfo

from ..models import (
    Doctor, DoctorSchedule, DoctorAttendance, HealthProfile, Appointment,
    Consultation, Prescription, PrescribedMedicine,
    Medicine, InventoryStock, Stock, Expiry, ReimbursementClaim, ClaimDocument,
    InventoryRequisition, LowStockAlert, AuditLog, ComplaintV2,
    HospitalAdmit, AmbulanceRecordsV2, AmbulanceLog, HealthAnnouncement,
)


# ===========================================================================
# ── DOCTOR AND SCHEDULE SERIALIZERS ──────────────────────────────────────
# ===========================================================================

class DoctorSerializer(serializers.ModelSerializer):
    """Read: Doctor information with validation"""
    id = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Doctor
        fields = ['id', 'doctor_name', 'doctor_phone', 'email', 'specialization', 'is_active']
    
    def validate_doctor_phone(self, value):
        """Validate phone number format"""
        if not value:
            raise serializers.ValidationError("Doctor phone number is required.")
        if len(value) < 10:
            raise serializers.ValidationError("Phone number must be at least 10 digits.")
        return value
    
    def validate_email(self, value):
        """Validate email format"""
        if value and '@' not in value:
            raise serializers.ValidationError("Invalid email format.")
        return value


class DoctorScheduleSerializer(serializers.ModelSerializer):
    """Read: Doctor's weekly schedule with validation"""
    id = serializers.IntegerField(read_only=True)
    doctor_detail = DoctorSerializer(source='doctor', read_only=True)
    day_label = serializers.CharField(source='get_day_of_week_display', read_only=True)
    
    class Meta:
        model = DoctorSchedule
        fields = [
            'id', 'doctor', 'doctor_detail', 'day_of_week', 'day_label',
            'start_time', 'end_time', 'room_number'
        ]
    
    def validate(self, data):
        """Validate that end_time is after start_time"""
        if data.get('start_time') and data.get('end_time'):
            if data['end_time'] <= data['start_time']:
                raise serializers.ValidationError(
                    "Schedule end time must be after start time."
                )
        return data


class DoctorAttendanceSerializer(serializers.ModelSerializer):
    """Read: Doctor's today's attendance status with validation"""
    id = serializers.IntegerField(read_only=True)
    doctor_detail = DoctorSerializer(source='doctor', read_only=True)
    status_label = serializers.CharField(source='get_status_display', read_only=True)
    marked_at = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = DoctorAttendance
        fields = [
            'id', 'doctor', 'doctor_detail', 'attendance_date', 'status',
            'status_label', 'marked_at', 'notes'
        ]
    
    def validate_attendance_date(self, value):
        """Validate attendance date is not in future"""
        if value > timezone.now().date():
            raise serializers.ValidationError("Attendance date cannot be in the future.")
        return value


class DoctorAvailabilitySerializer(serializers.Serializer):
    """
    Combined view of doctor's schedule + today's attendance.
    PHC-UC-01: View Doctor Schedule & Availability
    """
    # Doctor fields - flatten doctor data directly
    id = serializers.IntegerField(read_only=True)
    doctor_name = serializers.CharField(read_only=True)
    specialization = serializers.CharField(read_only=True)
    doctor_phone = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    doctor = DoctorSerializer(source='*', read_only=True)  # Nested doctor object for compatibility
    schedule = DoctorScheduleSerializer(many=True, source='schedules', read_only=True)
    todays_status = DoctorAttendanceSerializer(source='todays_attendance', required=False, read_only=True)
    is_available_today = serializers.SerializerMethodField()
    
    def get_is_available_today(self, obj):
        """Check if doctor is available today"""
        attendance = getattr(obj, 'todays_attendance', None)
        if not attendance:
            return False
        return attendance.status == 'PRESENT'


# ===========================================================================
# ── APPOINTMENT SERIALIZERS ──────────────────────────────────────────────
# ===========================================================================

class AppointmentSerializer(serializers.ModelSerializer):
    """Read: Appointment details"""
    doctor_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Appointment
        fields = ['id', 'appointment_date', 'appointment_time', 'appointment_type', 
                 'status', 'chief_complaint', 'doctor', 'doctor_name', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_doctor_name(self, obj):
        return obj.doctor.doctor_name if obj.doctor else obj.recorded_doctor_name


class AppointmentCreateSerializer(serializers.ModelSerializer):
    """Write: Create/update appointment"""
    
    class Meta:
        model = Appointment
        fields = ['appointment_date', 'appointment_time', 'appointment_type', 
                 'chief_complaint', 'doctor', 'status']
    
    def validate_appointment_date(self, value):
        """Validate appointment date is not in past"""
        if value < date.today():
            raise serializers.ValidationError("Appointment date cannot be in the past.")
        return value


# ===========================================================================
# ── CONSULTATION SERIALIZERS ─────────────────────────────────────────────
# ===========================================================================

class ConsultationSerializer(serializers.ModelSerializer):
    """Read: Consultation (medical visit) details with validation"""
    id = serializers.IntegerField(read_only=True)
    doctor_name = serializers.SerializerMethodField()
    patient_name = serializers.CharField(source='patient.user.get_full_name', read_only=True)
    patient_username = serializers.CharField(source='patient.user.username', read_only=True)
    patient_id = serializers.IntegerField(source='patient.user.id', read_only=True)
    consultation_date = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = Consultation
        fields = [
            'id', 'patient', 'patient_id', 'patient_name', 'patient_username', 'doctor', 'doctor_name', 'consultation_date',
            'blood_pressure_systolic', 'blood_pressure_diastolic', 'pulse_rate',
            'temperature', 'oxygen_saturation', 'weight', 'chief_complaint',
            'history_of_present_illness', 'examination_findings', 'provisional_diagnosis',
            'final_diagnosis', 'treatment_plan', 'advice', 'follow_up_date', 'ambulance_requested',
        ]
    
    def get_doctor_name(self, obj):
        return obj.doctor.doctor_name if obj.doctor else obj.recorded_doctor_name
    
    def validate_blood_pressure_systolic(self, value):
        """Validate systolic BP range"""
        if value and (value < 40 or value > 300):
            raise serializers.ValidationError(
                "Systolic blood pressure must be between 40 and 300 mmHg."
            )
        return value
    
    def validate_blood_pressure_diastolic(self, value):
        """Validate diastolic BP range"""
        if value and (value < 30 or value > 200):
            raise serializers.ValidationError(
                "Diastolic blood pressure must be between 30 and 200 mmHg."
            )
        return value
    
    def validate_pulse_rate(self, value):
        """Validate pulse rate range"""
        if value and (value < 30 or value > 200):
            raise serializers.ValidationError(
                "Pulse rate must be between 30 and 200 bpm."
            )
        return value
    
    def validate_temperature(self, value):
        """Validate temperature range"""
        if value and (value < 35 or value > 42):
            raise serializers.ValidationError(
                "Temperature must be between 35°C and 42°C."
            )
        return value
    
    def validate_oxygen_saturation(self, value):
        """Validate SpO2 range"""
        if value and (value < 70 or value > 100):
            raise serializers.ValidationError(
                "Oxygen saturation must be between 70% and 100%."
            )
        return value
    
    def validate_weight(self, value):
        """Validate weight range"""
        if value and (value < 20 or value > 300):
            raise serializers.ValidationError(
                "Weight must be between 20 kg and 300 kg."
            )
        return value


class ConsultationCreateSerializer(serializers.ModelSerializer):
    """Write: Create consultation with validation"""
    class Meta:
        model = Consultation
        fields = [
            'doctor', 'blood_pressure_systolic', 'blood_pressure_diastolic',
            'pulse_rate', 'temperature', 'oxygen_saturation', 'weight',
            'chief_complaint', 'history_of_present_illness', 'examination_findings',
            'provisional_diagnosis', 'final_diagnosis', 'treatment_plan',
            'advice', 'follow_up_date'
        ]
        extra_kwargs = {
            'doctor': {'required': True},
            'chief_complaint': {'required': True},
        }
    
    def validate_doctor(self, value):
        """Validate doctor exists and is active"""
        if not value.is_active:
            raise serializers.ValidationError("Selected doctor is not active.")
        return value
    
    def validate_chief_complaint(self, value):
        """Validate chief complaint"""
        if not value or not value.strip():
            raise serializers.ValidationError("Chief complaint is required.")
        if len(value) < 5:
            raise serializers.ValidationError("Chief complaint must be at least 5 characters.")
        return value


# ===========================================================================
# ── PRESCRIPTION AND MEDICINE SERIALIZERS ────────────────────────────────
# ===========================================================================

class MedicineSerializer(serializers.ModelSerializer):
    """Read: Medicine information with validation"""
    id = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Medicine
        fields = [
            'id', 'medicine_name', 'brand_name', 'generic_name', 'manufacturer_name',
            'unit', 'pack_size_label', 'reorder_threshold'
        ]
    
    def validate_medicine_name(self, value):
        """Validate medicine name"""
        if not value or not value.strip():
            raise serializers.ValidationError("Medicine name is required.")
        if len(value) < 2:
            raise serializers.ValidationError("Medicine name must be at least 2 characters.")
        return value
    
    def validate_reorder_threshold(self, value):
        """Validate reorder threshold"""
        if value and value <= 0:
            raise serializers.ValidationError("Reorder threshold must be greater than 0.")
        return value


class PrescribedMedicineSerializer(serializers.ModelSerializer):
    """Read: Individual medicine in prescription with validation"""
    id = serializers.IntegerField(read_only=True)
    medicine_detail = MedicineSerializer(source='medicine', read_only=True)
    is_revoked = serializers.BooleanField(read_only=True)
    # Convenience fields for frontend
    medicine_name = serializers.CharField(source='medicine.medicine_name', read_only=True)
    dosage = serializers.SerializerMethodField()
    frequency = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = PrescribedMedicine
        fields = [
            'id', 'medicine', 'medicine_detail', 'medicine_name', 'qty_prescribed', 'days', 'times_per_day',
            'dosage', 'frequency', 'duration', 'instructions', 'notes', 'is_revoked',
        ]
    
    def get_dosage(self, obj):
        """Get dosage as quantity with unit"""
        if obj.qty_prescribed and obj.medicine:
            unit = obj.medicine.unit or 'unit'
            return f"{obj.qty_prescribed} {unit}"
        return 'N/A'
    
    def get_frequency(self, obj):
        """Get frequency as times per day"""
        if obj.times_per_day:
            return f"{obj.times_per_day} times/day"
        return 'N/A'
    
    def get_duration(self, obj):
        """Get duration as days"""
        if obj.days:
            return f"{obj.days} days"
        return 'N/A'
    
    def validate_qty_prescribed(self, value):
        """Validate qty_prescribed"""
        if value and value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0.")
        return value
    
    def validate_days(self, value):
        """Validate number of days"""
        if value and value <= 0:
            raise serializers.ValidationError("Number of days must be greater than 0.")
        if value and value > 365:
            raise serializers.ValidationError("Prescription duration cannot exceed 365 days.")
        return value
    
    def validate_times_per_day(self, value):
        """Validate times per day"""
        if value and (value < 1 or value > 12):
            raise serializers.ValidationError("Times per day must be between 1 and 12.")
        return value


class PrescribedMedicineCreateSerializer(serializers.ModelSerializer):
    """Write: Add medicine to prescription with validation"""
    class Meta:
        model = PrescribedMedicine
        fields = ['medicine', 'qty_prescribed', 'days', 'times_per_day', 'instructions', 'notes']
        extra_kwargs = {
            'medicine': {'required': True},
            'qty_prescribed': {'required': True},
            'days': {'required': True},
            'times_per_day': {'required': True},
            'instructions': {'required': False},
            'notes': {'required': False},
        }
    
    def validate_medicine(self, value):
        """Validate medicine exists"""
        if not value:
            raise serializers.ValidationError("Medicine is required.")
        return value
    
    def validate_qty_prescribed(self, value):
        """Validate prescribed quantity"""
        if not value or value <= 0:
            raise serializers.ValidationError("Prescribed quantity must be greater than 0.")
        return value
    
    def validate_days(self, value):
        """Validate days"""
        if not value or value <= 0:
            raise serializers.ValidationError("Number of days must be greater than 0.")
        if value > 365:
            raise serializers.ValidationError("Prescription duration cannot exceed 365 days.")
        return value
    
    def validate_times_per_day(self, value):
        """Validate times per day"""
        if not value or value < 1 or value > 12:
            raise serializers.ValidationError("Times per day must be between 1 and 12.")
        return value


class PrescriptionSerializer(serializers.ModelSerializer):
    """Read: Complete prescription with medicines (FIFO-aware)"""
    id = serializers.IntegerField(read_only=True)
    doctor_name = serializers.SerializerMethodField()
    patient_name = serializers.SerializerMethodField()
    patient_username = serializers.CharField(source='patient.user.username', read_only=True)
    prescribed_medicines = PrescribedMedicineSerializer(many=True, read_only=True)
    issued_date = serializers.DateField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    total_medicines = serializers.SerializerMethodField()
    
    class Meta:
        model = Prescription
        fields = [
            'id', 'patient', 'patient_name', 'patient_username', 'doctor', 'doctor_name', 'issued_date',
            'status', 'status_display', 'details', 'special_instructions', 'test_recommended',
            'follow_up_suggestions', 'prescribed_medicines', 'total_medicines',
            'is_for_dependent', 'dependent_name', 'dependent_relation', 'created_at'
        ]
        read_only_fields = [
            'id', 'issued_date', 'created_at', 'prescribed_medicines'
        ]
    
    def get_patient_name(self, obj):
        """Get patient name safely, handling potential null relationships and empty strings"""
        try:
            if obj.patient and obj.patient.user:
                full_name = obj.patient.user.get_full_name().strip()
                if full_name:
                    return full_name
                return obj.patient.user.username  # fallback if first/last name empty
            return f"Patient {obj.patient.id}" if obj.patient else "Unknown Patient"
        except Exception as e:
            return f"Patient {obj.patient.id}" if obj.patient else "Unknown Patient"
    
    def get_doctor_name(self, obj):
        """Get doctor name safely, handling potential null relationships"""
        try:
            if obj.doctor:
                return obj.doctor.doctor_name
            return obj.recorded_doctor_name or "Unknown Doctor"
        except Exception as e:
            return "Unknown Doctor"
    
    def get_total_medicines(self, obj):
        """Count total non-revoked medicines in prescription"""
        return obj.prescribed_medicines.filter(is_revoked=False).count()




class PrescriptionCreateSerializer(serializers.Serializer):
    """Write: Create prescription with medicines and FIFO stock deduction"""
    consultation_id = serializers.IntegerField(required=True)
    doctor_id = serializers.IntegerField(required=True)
    medicines = PrescribedMedicineCreateSerializer(many=True, required=True)
    details = serializers.CharField(required=False, allow_blank=True, max_length=1000)
    special_instructions = serializers.CharField(required=False, allow_blank=True, max_length=1000)
    test_recommended = serializers.CharField(required=False, allow_blank=True, max_length=255)
    follow_up_suggestions = serializers.CharField(required=False, allow_blank=True, max_length=500)
    is_for_dependent = serializers.BooleanField(required=False, default=False)
    dependent_name = serializers.CharField(required=False, allow_blank=True, max_length=255)
    dependent_relation = serializers.CharField(required=False, allow_blank=True, max_length=100)
    
    def validate_consultation_id(self, value):
        """Validate consultation exists"""
        try:
            Consultation.objects.get(id=value)
        except Consultation.DoesNotExist:
            raise serializers.ValidationError("Consultation with this ID does not exist.")
        return value
    
    def validate_doctor_id(self, value):
        """Validate doctor exists and is active"""
        try:
            doctor = Doctor.objects.get(id=value, is_active=True)
        except Doctor.DoesNotExist:
            raise serializers.ValidationError("Selected doctor does not exist or is not active.")
        return value
    
    def validate_medicines(self, value):
        """Validate medicines list"""
        if not value or len(value) == 0:
            raise serializers.ValidationError("At least one medicine is required in prescription.")
        if len(value) > 50:
            raise serializers.ValidationError("Prescription cannot have more than 50 medicines.")
        return value


class PrescriptionUpdateSerializer(serializers.Serializer):
    """Write: Update prescription details and/or status (immutable medicines)"""
    details = serializers.CharField(required=False, allow_blank=True, max_length=1000)
    special_instructions = serializers.CharField(required=False, allow_blank=True, max_length=1000)
    test_recommended = serializers.CharField(required=False, allow_blank=True, max_length=255)
    follow_up_suggestions = serializers.CharField(required=False, allow_blank=True, max_length=500)
    status = serializers.ChoiceField(
        required=False, 
        choices=['ISSUED', 'DISPENSED', 'CANCELLED', 'COMPLETED']
    )
    
    def validate_status(self, value):
        """Validate status transitions"""
        # This validation is done at the service layer for more context
        # We just ensure it's a valid choice here
        return value


# ===========================================================================
# ── HEALTH PROFILE SERIALIZERS ───────────────────────────────────────────
# ===========================================================================

class HealthProfileSerializer(serializers.ModelSerializer):
    """Read/Write: Patient health profile with validation"""
    patient_name = serializers.CharField(source='patient.user.get_full_name', read_only=True)
    
    class Meta:
        model = HealthProfile
        fields = [
            'patient', 'patient_name', 'blood_group', 'height_cm', 'weight_kg', 'allergies',
            'chronic_conditions', 'current_medications', 'past_surgeries',
            'family_medical_history', 'has_insurance', 'insurance_provider',
            'insurance_policy_number', 'insurance_valid_until',
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relation',
        ]
    
    def validate_blood_group(self, value):
        """Validate blood group"""
        valid_blood_groups = ['O+', 'O-', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-']
        if value and value not in valid_blood_groups:
            raise serializers.ValidationError(
                f"Blood group must be one of: {', '.join(valid_blood_groups)}"
            )
        return value
    
    def validate_height_cm(self, value):
        """Validate height range"""
        if value and (value < 50 or value > 250):
            raise serializers.ValidationError(
                "Height must be between 50 cm and 250 cm."
            )
        return value
    
    def validate_weight_kg(self, value):
        """Validate weight range"""
        if value and (value < 20 or value > 300):
            raise serializers.ValidationError(
                "Weight must be between 20 kg and 300 kg."
            )
        return value
    
    def validate_emergency_contact_phone(self, value):
        """Validate emergency contact phone"""
        if value and len(value) < 10:
            raise serializers.ValidationError(
                "Emergency contact phone must be at least 10 digits."
            )
        return value
    
    def validate_insurance_valid_until(self, value):
        """Validate insurance expiry date"""
        if value:
            from datetime import date
            if value < date.today():
                raise serializers.ValidationError(
                    "Insurance expiry date cannot be in the past."
                )
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        has_insurance = data.get('has_insurance', False)
        insurance_provider = data.get('insurance_provider', '')
        insurance_policy_number = data.get('insurance_policy_number', '')
        
        if has_insurance:
            if not insurance_provider or not insurance_provider.strip():
                raise serializers.ValidationError(
                    "Insurance provider is required when has_insurance is True."
                )
            if not insurance_policy_number or not insurance_policy_number.strip():
                raise serializers.ValidationError(
                    "Insurance policy number is required when has_insurance is True."
                )
        
        return data


# ===========================================================================
# ── REIMBURSEMENT CLAIM SERIALIZERS ──────────────────────────────────────
# ===========================================================================

class ClaimDocumentSerializer(serializers.ModelSerializer):
    """Read: Document attached to claim"""
    class Meta:
        model = ClaimDocument
        fields = ['id', 'document_name', 'document_file', 'document_type', 'uploaded_at', 'verified']


class ReimbursementClaimSerializer(serializers.ModelSerializer):
    """Read: Reimbursement claim details with approver information"""
    # Patient/Claimant details
    patient_name = serializers.CharField(source='patient.user.get_full_name', read_only=True)
    patient_id = serializers.CharField(source='patient.user.username', read_only=True)
    
    # Creator details
    created_by_name = serializers.CharField(source='created_by.user.get_full_name', read_only=True, allow_null=True)
    created_by_id = serializers.CharField(source='created_by.user.username', read_only=True, allow_null=True)
    
    # Approval chain details
    phc_staff_name = serializers.SerializerMethodField()
    accounts_verified_by_name = serializers.SerializerMethodField()
    sanction_approved_by_name = serializers.SerializerMethodField()
    
    # Uploaded documents
    documents = ClaimDocumentSerializer(many=True, read_only=True)
    
    # Approval chain details
    phc_staff_name = serializers.SerializerMethodField()
    accounts_verified_by_name = serializers.SerializerMethodField()
    sanction_approved_by_name = serializers.SerializerMethodField()
    approval_history = serializers.SerializerMethodField()
    
    class Meta:
        model = ReimbursementClaim
        fields = [
            'id', 'patient', 'patient_name', 'patient_id',
            'claim_amount', 'expense_date', 'submission_date', 
            'description', 'status', 
            'created_by', 'created_by_name', 'created_by_id', 'created_at', 'updated_at',
            # Approval chain
            'phc_staff_review_date', 'phc_staff_remarks', 'phc_staff_approved', 'phc_staff_name',
            'accounts_verification_date', 'accounts_remarks', 'accounts_verified', 'accounts_verified_by_name',
            'sanction_required', 'approving_authority_date', 'approving_authority_remarks', 
            'is_sanctioned', 'sanction_approved_by_name',
            'payment_date', 'payment_reference',
            'is_rejected', 'rejection_reason',
            'prescription',
            # Attached documents
            'documents',
            
            # Formatted history for frontend
            'approval_history',
        ]
        read_only_fields = fields  # All fields are read-only for the auditor view
    
    def get_phc_staff_name(self, obj):
        """Get name of PHC staff who reviewed the claim"""
        # PHC staff review is typically done by compounder - we'll need to track this
        # For now, return placeholder if we don't have the specific user
        return "PHC Staff" if obj.phc_staff_approved else None
    
    def get_accounts_verified_by_name(self, obj):
        """Get name of accounts staff who verified the claim"""
        # Similar to above, we may need to add this field to the model
        return "Accounts Staff" if obj.accounts_verified else None
    
    def get_sanction_approved_by_name(self, obj):
        """Get name of authority who sanctioned the claim"""
        # Similar to above, we may need to add this field to the model
        return "Sanctioning Authority" if obj.is_sanctioned else None

    def get_approval_history(self, obj):
        history = []
        if obj.phc_staff_review_date:
            history.append({
                'action': 'APPROVED' if obj.phc_staff_approved else 'REJECTED',
                'reviewed_by': self.get_phc_staff_name(obj) or 'PHC Staff',
                'remarks': obj.phc_staff_remarks,
                'review_date': obj.phc_staff_review_date.strftime('%Y-%m-%d %H:%M')
            })
        if obj.accounts_verification_date:
            history.append({
                'action': 'VERIFIED' if obj.accounts_verified else 'REJECTED',
                'reviewed_by': self.get_accounts_verified_by_name(obj) or 'Accounts Staff',
                'remarks': obj.accounts_remarks,
                'review_date': obj.accounts_verification_date.strftime('%Y-%m-%d %H:%M')
            })
        if obj.approving_authority_date:
            history.append({
                'action': 'SANCTIONED' if obj.is_sanctioned else 'REJECTED',
                'reviewed_by': self.get_sanction_approved_by_name(obj) or 'Sanctioning Authority',
                'remarks': obj.approving_authority_remarks,
                'review_date': obj.approving_authority_date.strftime('%Y-%m-%d %H:%M')
            })
        return history


class ReimbursementClaimCreateSerializer(serializers.ModelSerializer):
    """Write: Submit reimbursement claim - validates 90-day window"""
    class Meta:
        model = ReimbursementClaim
        fields = ['prescription', 'claim_amount', 'expense_date', 'description']
        extra_kwargs = {
            'prescription': {'required': True, 'allow_null': False},
            'claim_amount': {'required': True},
            'expense_date': {'required': True},
            'description': {'required': True},
        }
    
    def validate_claim_amount(self, value):
        """Validate amount is positive"""
        if value <= 0:
            raise serializers.ValidationError("Claim amount must be greater than 0.")
        return value
    
    def validate_expense_date(self, value):
        """Validate expense_date is within 90 days and not in future"""
        from datetime import date, timedelta
        today = date.today()
        
        # Cannot be in the future
        if value > today:
            raise serializers.ValidationError("Expense date cannot be in the future.")
        
        # Must be within 90 days
        cutoff_date = today - timedelta(days=90)
        if value < cutoff_date:
            raise serializers.ValidationError(
                f"Expense date must be within 90 days. Please submit claims within 90 days of expense."
            )
        
        return value


class ReimbursementClaimUpdateSerializer(serializers.ModelSerializer):
    """Write: Update reimbursement claim - only allowed for submitted status"""
    class Meta:
        model = ReimbursementClaim
        fields = ['claim_amount', 'description']
    
    def validate_claim_amount(self, value):
        """Validate amount is positive"""
        if value <= 0:
            raise serializers.ValidationError("Claim amount must be greater than 0.")
        return value


class ClaimDocumentUploadSerializer(serializers.ModelSerializer):
    """Write: Upload document to claim"""
    class Meta:
        model = ClaimDocument
        fields = ['document_name', 'document_file', 'document_type']


class ProcessClaimSerializer(serializers.Serializer):
    """Write: Process claim (approval/rejection by staff)"""
    DECISION_CHOICES = [('APPROVE', 'Approve'), ('REJECT', 'Reject')]
    
    decision = serializers.ChoiceField(choices=DECISION_CHOICES)
    remarks = serializers.CharField(required=False, allow_blank=True, max_length=500)


# ===========================================================================
# ── STOCK & EXPIRY SERIALIZERS ──────────────────────────────────────────
# ===========================================================================

class ExpirySerializer(serializers.ModelSerializer):
    """Read/Write: Expiry batch entry for stock (FIFO management)"""
    batch_status = serializers.SerializerMethodField()
    available_qty = serializers.SerializerMethodField()
    stock = serializers.SerializerMethodField()
    
    class Meta:
        model = Expiry
        fields = [
            'id', 'stock', 'batch_no', 'qty', 'available_qty', 'expiry_date',
            'is_returned', 'returned_qty', 'return_reason', 'batch_status', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_stock(self, obj):
        """Get stock with nested medicine_detail"""
        stock = obj.stock
        return {
            'id': stock.id,
            'medicine_detail': MedicineSerializer(stock.medicine).data
        }
    
    def get_batch_status(self, obj):
        """Get readable status of batch"""
        if obj.is_returned:
            return 'Returned'
        return 'Active'
    
    def get_available_qty(self, obj):
        """Get available quantity (qty - returned_qty)"""
        return obj.qty - obj.returned_qty

    def validate_qty(self, value):
        """Validate quantity is positive"""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0.")
        return value

    def validate_expiry_date(self, value):
        """Validate expiry date is today or later"""
        from datetime import date
        if value < date.today():
            raise serializers.ValidationError("Expiry date cannot be in the past.")
        return value


class ExpiryCreateSerializer(serializers.Serializer):
    """Write: Create new Expiry batch for existing stock"""
    stock_id = serializers.IntegerField()
    batch_no = serializers.CharField(max_length=100)
    qty = serializers.IntegerField(validators=[MinValueValidator(1)])
    expiry_date = serializers.DateField()
    
    def validate_expiry_date(self, value):
        """Validate expiry date is today or later"""
        from datetime import date
        if value < date.today():
            raise serializers.ValidationError("Expiry date cannot be in the past.")
        return value
    
    def validate_qty(self, value):
        """Validate quantity is positive"""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0.")
        return value


class ExpiryUpdateSerializer(serializers.ModelSerializer):
    """Write: Update Expiry batch metadata (batch_no, qty, expiry_date)"""
    class Meta:
        model = Expiry
        fields = ['batch_no', 'qty', 'expiry_date']
    
    def validate_qty(self, value):
        """Validate quantity is positive"""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0.")
        return value
    
    def validate_expiry_date(self, value):
        """Validate expiry date is today or later"""
        from datetime import date
        if value < date.today():
            raise serializers.ValidationError("Expiry date cannot be in the past.")
        return value


class ExpiryReturnSerializer(serializers.Serializer):
    """Write: Mark Expiry batch as returned (only allowed if expired)"""
    returned_qty = serializers.IntegerField(default=None, required=False, allow_null=True)
    return_reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate_returned_qty(self, value):
        """Validate returned_qty if provided"""
        if value is not None and value <= 0:
            raise serializers.ValidationError("Returned quantity must be greater than 0.")
        return value


class StockSerializer(serializers.ModelSerializer):
    """Read: Stock with nested Expiry batches (FIFO sorted)"""
    medicine_detail = MedicineSerializer(source='medicine', read_only=True)
    expiry_batches = ExpirySerializer(many=True, read_only=True)
    total_qty = serializers.SerializerMethodField()
    
    class Meta:
        model = Stock
        fields = [
            'id', 'medicine', 'medicine_detail', 'total_qty',
            'expiry_batches', 'last_updated', 'created_at'
        ]
        read_only_fields = ['id', 'total_qty', 'last_updated', 'created_at']
    
    def get_total_qty(self, obj):
        """Calculate total available quantity from active batches"""
        active_batches = obj.expiry_batches.filter(is_returned=False)
        total = sum(batch.qty - batch.returned_qty for batch in active_batches)
        return total


class StockCreateSerializer(serializers.Serializer):
    """Write: Create Stock + Expiry batch (atomic operation)"""
    medicine_id = serializers.IntegerField()
    qty = serializers.IntegerField(validators=[MinValueValidator(1)])
    expiry_date = serializers.DateField()
    batch_no = serializers.CharField(max_length=100)

    def validate_expiry_date(self, value):
        """Validate expiry date is today or later"""
        from datetime import date
        if value < date.today():
            raise serializers.ValidationError("Expiry date cannot be in the past.")
        return value


class StockUpdateSerializer(serializers.ModelSerializer):
    """Write: Update Stock metadata (not quantities, use Expiry for that)"""
    class Meta:
        model = Stock
        fields = []  # Stock only has auto-managed fields, can't update directly
        


# ===========================================================================
# ── INVENTORY SERIALIZERS ────────────────────────────────────────────────
# ===========================================================================

class InventoryStockSerializer(serializers.ModelSerializer):
    """Read: Inventory stock with medicine details"""
    medicine_detail = MedicineSerializer(source='medicine', read_only=True)
    days_until_expiry = serializers.SerializerMethodField()
    
    def get_days_until_expiry(self, obj):
        from datetime import date
        delta = obj.expiry_date - date.today()
        return delta.days
    
    class Meta:
        model = InventoryStock
        fields = [
            'id', 'medicine', 'medicine_detail', 'quantity_received', 'quantity_remaining',
            'supplier', 'date_received', 'expiry_date', 'batch_number', 'is_returned',
            'days_until_expiry',
        ]


class InventoryStockUpdateSerializer(serializers.Serializer):
    """Write: Update inventory stock"""
    medicine_id = serializers.IntegerField()
    quantity_change = serializers.IntegerField()  # Positive for addition, negative for deduction
    change_reason = serializers.CharField(max_length=200)


class LowStockAlertSerializer(serializers.ModelSerializer):
    """Read: Low-stock alerts"""
    medicine_detail = MedicineSerializer(source='medicine', read_only=True)
    
    class Meta:
        model = LowStockAlert
        fields = ['id', 'medicine', 'medicine_detail', 'current_stock',
                  'reorder_threshold', 'alert_triggered_at', 'acknowledged']


# ===========================================================================
# ── REQUISITION SERIALIZERS ──────────────────────────────────────────────
# ===========================================================================

class InventoryRequisitionSerializer(serializers.ModelSerializer):
    """Read: Inventory requisition"""
    medicine_detail = MedicineSerializer(source='medicine', read_only=True)
    created_by_name = serializers.CharField(source='created_by.user.get_full_name', read_only=True)
    
    class Meta:
        model = InventoryRequisition
        fields = [
            'id', 'medicine', 'medicine_detail', 'quantity_requested', 'quantity_fulfilled',
            'status', 'created_date', 'created_by', 'created_by_name', 'approved_date',
            'fulfilled_date',
        ]


class InventoryRequisitionCreateSerializer(serializers.ModelSerializer):
    """Write: Create inventory requisition"""
    class Meta:
        model = InventoryRequisition
        fields = ['medicine', 'quantity_requested']


class ApproveRequisitionSerializer(serializers.Serializer):
    """Write: Approve requisition"""
    approval_remarks = serializers.CharField(required=False, allow_blank=True, max_length=500)


class FulfillRequisitionSerializer(serializers.Serializer):
    """Write: Mark requisition as fulfilled"""
    quantity_fulfilled = serializers.IntegerField(min_value=1)


# ===========================================================================
# ── AUDIT LOG SERIALIZERS ────────────────────────────────────────────────
# ===========================================================================

class AuditLogSerializer(serializers.ModelSerializer):
    """Read: Audit log entry"""
    user_name = serializers.CharField(source='user.user.get_full_name', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'user_name', 'action_type', 'entity_type', 'entity_id',
            'action_details', 'timestamp', 'ip_address',
        ]


# ===========================================================================
# ── DASHBOARD SERIALIZERS ────────────────────────────────────────────────
# ===========================================================================

class DashboardStatsSerializer(serializers.Serializer):
    """Read: Dashboard statistics"""
    todays_appointments = serializers.IntegerField()
    pending_claims = serializers.IntegerField()
    low_stock_alerts = serializers.IntegerField()
    pending_requisitions = serializers.IntegerField()


class PatientSummarySerializer(serializers.Serializer):
    """Read: Patient summary info"""
    appointment_count = serializers.IntegerField()
    prescription_count = serializers.IntegerField()
    pending_claims = serializers.IntegerField()
    reimbursed_amount = serializers.DecimalField(max_digits=10, decimal_places=2)


# ===========================================================================
# ── COMPLAINT SERIALIZERS ────────────────────────────────────────────────
# ===========================================================================

class ComplaintSerializer(serializers.ModelSerializer):
    """Read: Complaint details with validation"""
    id = serializers.IntegerField(read_only=True)
    patient_name = serializers.CharField(source='patient.user.get_full_name', read_only=True)
    resolved_by_name = serializers.CharField(
        source='resolved_by.user.get_full_name', 
        read_only=True,
        required=False
    )
    category_label = serializers.CharField(source='get_category_display', read_only=True)
    status_label = serializers.CharField(source='get_status_display', read_only=True)
    created_date = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = ComplaintV2
        fields = [
            'id', 'patient', 'patient_name', 'title', 'description', 'category',
            'category_label', 'status', 'status_label', 'resolution_notes',
            'resolved_by', 'resolved_by_name', 'created_date', 'updated_at',
            'resolved_date'
        ]
    
    def validate_title(self, value):
        """Validate complaint title"""
        if not value or not value.strip():
            raise serializers.ValidationError("Complaint title is required.")
        if len(value) < 5:
            raise serializers.ValidationError("Title must be at least 5 characters.")
        if len(value) > 255:
            raise serializers.ValidationError("Title cannot exceed 255 characters.")
        return value
    
    def validate_description(self, value):
        """Validate complaint description"""
        if not value or not value.strip():
            raise serializers.ValidationError("Complaint description is required.")
        if len(value) < 10:
            raise serializers.ValidationError("Description must be at least 10 characters.")
        return value
    
    def validate_category(self, value):
        """Validate complaint category"""
        valid_categories = ['SERVICE', 'STAFF', 'FACILITIES', 'MEDICAL', 'OTHER']
        if value not in valid_categories:
            raise serializers.ValidationError(
                f"Category must be one of: {', '.join(valid_categories)}"
            )
        return value


class ComplaintCreateSerializer(serializers.ModelSerializer):
    """Write: Submit new complaint with validation"""
    class Meta:
        model = ComplaintV2
        fields = ['title', 'description', 'category']
        extra_kwargs = {
            'title': {'required': True},
            'description': {'required': True},
            'category': {'required': True},
        }
    
    def validate_title(self, value):
        """Validate title"""
        if not value or not value.strip():
            raise serializers.ValidationError("Title cannot be empty.")
        if len(value) < 5:
            raise serializers.ValidationError("Title must be at least 5 characters.")
        return value
    
    def validate_description(self, value):
        """Validate description"""
        if not value or not value.strip():
            raise serializers.ValidationError("Description cannot be empty.")
        if len(value) < 10:
            raise serializers.ValidationError("Description must be at least 10 characters.")
        return value


class ComplaintUpdateSerializer(serializers.ModelSerializer):
    """Write: Update complaint status (PHC staff only)"""
    class Meta:
        model = ComplaintV2
        fields = ['status', 'resolution_notes']
    
    def validate_status(self, value):
        """Validate status transition"""
        valid_statuses = ['SUBMITTED', 'IN_REVIEW', 'RESOLVED', 'CLOSED']
        if value not in valid_statuses:
            raise serializers.ValidationError(
                f"Status must be one of: {', '.join(valid_statuses)}"
            )
        return value
    
    def validate_resolution_notes(self, value):
        """Validate resolution notes when marking as resolved"""
        instance = self.instance
        if instance and value and len(value) < 5:
            raise serializers.ValidationError("Resolution notes must be at least 5 characters.")
        return value


class ComplaintRespondSerializer(serializers.Serializer):
    """Write: Compounder responds to complaint with resolution notes"""
    resolution_notes = serializers.CharField(
        required=True,
        min_length=10,
        max_length=2000,
        help_text="Response/resolution notes for the complaint (10-2000 characters)"
    )
    
    def validate_resolution_notes(self, value):
        """Validate resolution notes content"""
        if not value or not value.strip():
            raise serializers.ValidationError("Resolution notes cannot be empty.")
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Resolution notes must be at least 10 characters.")
        return value.strip()


# ===========================================================================
# ── HOSPITAL ADMISSION SERIALIZERS ───────────────────────────────────────
# ===========================================================================

class HospitalAdmitSerializer(serializers.ModelSerializer):
    """Read: Hospital admission details with validation"""
    id = serializers.IntegerField(read_only=True)
    patient_name = serializers.CharField(read_only=True)  # Denormalized from model
    referred_by_name = serializers.CharField(
        source='referred_by.doctor_name',
        read_only=True,
        required=False
    )
    admission_date = serializers.DateField()
    discharge_date = serializers.DateField(required=False, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    days_admitted = serializers.SerializerMethodField()
    
    class Meta:
        model = HospitalAdmit
        fields = [
            'id', 'patient', 'patient_name', 'hospital_id', 'hospital_name',
            'admission_date', 'discharge_date', 'days_admitted', 'reason',
            'summary', 'referred_by', 'referred_by_name', 'created_at', 'updated_at'
        ]
    
    def get_days_admitted(self, obj):
        """Calculate days admitted"""
        end_date = obj.discharge_date if obj.discharge_date else date.today()
        delta = end_date - obj.admission_date
        return delta.days
    
    def validate_hospital_id(self, value):
        """Validate hospital ID"""
        if not value or not value.strip():
            raise serializers.ValidationError("Hospital ID is required.")
        if len(value) < 2:
            raise serializers.ValidationError("Hospital ID must be at least 2 characters.")
        return value
    
    def validate_hospital_name(self, value):
        """Validate hospital name"""
        if not value or not value.strip():
            raise serializers.ValidationError("Hospital name is required.")
        if len(value) < 5:
            raise serializers.ValidationError("Hospital name must be at least 5 characters.")
        return value
    
    def validate_reason(self, value):
        """Validate admission reason"""
        if not value or not value.strip():
            raise serializers.ValidationError("Admission reason is required.")
        if len(value) < 10:
            raise serializers.ValidationError("Reason must be at least 10 characters.")
        return value
    
    def validate_admission_date(self, value):
        """Validate admission date"""
        if value > date.today():
            raise serializers.ValidationError("Admission date cannot be in the future.")
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        admission_date = data.get('admission_date')
        discharge_date = data.get('discharge_date')
        
        if admission_date and discharge_date:
            if discharge_date < admission_date:
                raise serializers.ValidationError(
                    "Discharge date must be after or equal to admission date."
                )
            # Check if stay is too long (more than 2 years)
            delta = discharge_date - admission_date
            if delta.days > 730:
                raise serializers.ValidationError(
                    "Hospital stay duration seems unusually long. Please verify dates."
                )
        
        return data


class HospitalAdmitCreateSerializer(serializers.ModelSerializer):
    """Write: Create hospital admission record"""
    class Meta:
        model = HospitalAdmit
        fields = ['hospital_id', 'hospital_name', 'admission_date', 'reason', 'referred_by']
        extra_kwargs = {
            'hospital_id': {'required': True},
            'hospital_name': {'required': True},
            'admission_date': {'required': True},
            'reason': {'required': True},
        }


class HospitalAdmitUpdateSerializer(serializers.ModelSerializer):
    """Write: Update hospital admission (add discharge info)"""
    class Meta:
        model = HospitalAdmit
        fields = ['discharge_date', 'summary']


# ===========================================================================
# ── AMBULANCE RECORDS SERIALIZERS ────────────────────────────────────────
# ===========================================================================

class AmbulanceRecordsSerializer(serializers.ModelSerializer):
    """Read: Ambulance records with validation"""
    id = serializers.IntegerField(read_only=True)
    status_label = serializers.CharField(source='get_status_display', read_only=True)
    is_available = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = AmbulanceRecordsV2
        fields = [
            'id', 'vehicle_type', 'registration_number', 'driver_name',
            'driver_contact', 'driver_license', 'status', 'status_label',
            'is_available', 'current_assignment', 'last_maintenance_date',
            'next_maintenance_due', 'is_active', 'notes', 'created_at', 'updated_at'
        ]
    
    def get_is_available(self, obj):
        """Check if ambulance is available for assignment"""
        return obj.status == 'AVAILABLE' and obj.is_active
    
    def validate_vehicle_type(self, value):
        """Validate vehicle type"""
        if not value or not value.strip():
            raise serializers.ValidationError("Vehicle type is required.")
        valid_types = ['Type A', 'Type B', 'Type C', 'Advanced', 'Basic']
        if value not in valid_types:
            raise serializers.ValidationError(
                f"Vehicle type must be one of: {', '.join(valid_types)}"
            )
        return value
    
    def validate_registration_number(self, value):
        """Validate registration number format"""
        if not value or not value.strip():
            raise serializers.ValidationError("Registration number is required.")
        if len(value) < 6:
            raise serializers.ValidationError("Registration number must be at least 6 characters.")
        # Basic validation for Indian registration format (e.g., MH02AB1234)
        # Allow flexible format
        return value
    
    def validate_driver_name(self, value):
        """Validate driver name"""
        if not value or not value.strip():
            raise serializers.ValidationError("Driver name is required.")
        if len(value) < 3:
            raise serializers.ValidationError("Driver name must be at least 3 characters.")
        return value
    
    def validate_driver_contact(self, value):
        """Validate driver contact number"""
        if not value or not value.strip():
            raise serializers.ValidationError("Driver contact is required.")
        if len(value) < 10:
            raise serializers.ValidationError("Contact must be at least 10 digits.")
        if len(value) > 15:
            raise serializers.ValidationError("Contact cannot exceed 15 characters.")
        return value
    
    def validate_last_maintenance_date(self, value):
        """Validate maintenance date"""
        if value and value > date.today():
            raise serializers.ValidationError("Last maintenance date cannot be in the future.")
        return value
    
    def validate_next_maintenance_due(self, value):
        """Validate next maintenance due date"""
        if value and value <= date.today():
            raise serializers.ValidationError("Next maintenance due date must be in the future.")
        return value


class AmbulanceRecordsCreateSerializer(serializers.ModelSerializer):
    """Write: Create ambulance record"""
    class Meta:
        model = AmbulanceRecordsV2
        fields = [
            'vehicle_type', 'registration_number', 'driver_name',
            'driver_contact', 'driver_license', 'last_maintenance_date',
            'next_maintenance_due', 'notes'
        ]
        extra_kwargs = {
            'vehicle_type': {'required': True},
            'registration_number': {'required': True},
            'driver_name': {'required': True},
            'driver_contact': {'required': True},
        }


class AmbulanceRecordsUpdateSerializer(serializers.ModelSerializer):
    """Write: Update ambulance record (status, assignment, notes)"""
    class Meta:
        model = AmbulanceRecordsV2
        fields = ['status', 'current_assignment', 'last_maintenance_date', 'notes', 'is_active']
    
    def validate_status(self, value):
        """Validate ambulance status"""
        valid_statuses = ['AVAILABLE', 'IN_SERVICE', 'MAINTENANCE', 'OUT_OF_SERVICE']
        if value and value not in valid_statuses:
            raise serializers.ValidationError(
                f"Status must be one of: {', '.join(valid_statuses)}"
            )
        return value


# ===========================================================================
# ── AMBULANCE USAGE LOG SERIALIZERS (PHC-UC-11) ───────────────────────────
# ===========================================================================

class AmbulanceLogSerializer(serializers.ModelSerializer):
    """Read: Full ambulance usage log entry with related fields (PHC-UC-11)."""
    ambulance_registration = serializers.CharField(
        source='ambulance.registration_number', read_only=True, allow_null=True
    )
    ambulance_type = serializers.CharField(
        source='ambulance.vehicle_type', read_only=True, allow_null=True
    )
    logged_by_name = serializers.CharField(
        source='logged_by.user.get_full_name', read_only=True, allow_null=True
    )

    class Meta:
        model = AmbulanceLog
        fields = [
            'id', 'ambulance', 'ambulance_registration', 'ambulance_type',
            'patient_name', 'destination', 'call_date', 'call_time',
            'purpose', 'contact_number',
            'logged_by', 'logged_by_name', 'created_at',
        ]
        read_only_fields = ['id', 'logged_by', 'created_at']


class AmbulanceLogCreateSerializer(serializers.ModelSerializer):
    """
    Write: Create a new ambulance usage log entry (PHC-UC-11).
    Required: patient_name, destination, call_date, call_time
    Optional: ambulance (vehicle FK), purpose, contact_number
    """
    class Meta:
        model = AmbulanceLog
        fields = [
            'ambulance', 'patient_name', 'destination',
            'call_date', 'call_time', 'purpose', 'contact_number',
        ]

    def validate_patient_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Patient name is required.")
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Patient name must be at least 2 characters.")
        return value.strip()

    def validate_destination(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Destination is required.")
        return value.strip()

    def validate_contact_number(self, value):
        if value and not value.strip().lstrip('+').replace('-', '').replace(' ', '').isdigit():
            raise serializers.ValidationError("Enter a valid contact number.")
        return value.strip() if value else value


# ===========================================================================
# ── TASK 18: REIMBURSEMENT WORKFLOW SERIALIZERS ───────────────────────
# ===========================================================================

class ReimbursementClaimForwardSerializer(serializers.Serializer):
    """Write: Forward reimbursement claim in workflow (Compounder action)
    
    State transitions:
      SUBMITTED → PHC_REVIEW (first forward)
      PHC_REVIEW → ACCOUNTS_REVIEW (second forward)
    """
    phc_notes = serializers.CharField(
        required=True,
        min_length=10,
        max_length=500,
        help_text="Compounder notes about the claim verification"
    )


class ReimbursementClaimApproveSerializer(serializers.Serializer):
    """Write: Approve reimbursement claim (Accounts staff action)
    
    State transition:
      ACCOUNTS_REVIEW → APPROVED
    """
    approval_notes = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,
        help_text="Optional approval notes from accounts staff"
    )


class ReimbursementClaimRejectSerializer(serializers.Serializer):
    """Write: Reject reimbursement claim (Accounts staff action)
    
    State transition:
      ACCOUNTS_REVIEW → REJECTED
    """
    rejection_reason = serializers.CharField(
        required=True,
        min_length=10,
        max_length=500,
        help_text="Reason for rejection"
    )


# ===========================================================================
# ── HEALTH ANNOUNCEMENTS (PHC-UC-12) ────────────────────────────────────────
# ===========================================================================

class HealthAnnouncementSerializer(serializers.ModelSerializer):
    """
    Read: Serialize announcement data for patients and portal display.
    Includes computed fields for expiry status.
    """
    created_by_name = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = HealthAnnouncement
        fields = [
            'id', 'title', 'content', 'category', 'priority',
            'is_active', 'is_expired',
            'created_by_name', 'created_at', 'expires_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_created_by_name(self, obj):
        if obj.created_by and obj.created_by.user:
            user = obj.created_by.user
            full_name = f"{user.first_name} {user.last_name}".strip()
            return full_name or user.username
        return 'PHC Staff'

    def get_is_expired(self, obj):
        if obj.expires_at:
            return timezone.now() > obj.expires_at
        return False


class HealthAnnouncementCreateSerializer(serializers.ModelSerializer):
    """
    Write: Create a new health announcement (PHC-UC-12).
    Required: title, content
    Optional: category, priority, expires_at
    """
    class Meta:
        model = HealthAnnouncement
        fields = ['title', 'content', 'category', 'priority', 'expires_at']

    def validate_title(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Title is required.")
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Title must be at least 5 characters.")
        return value.strip()

    def validate_content(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Content is required.")
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Content must be at least 10 characters.")
        return value.strip()

    def validate_priority(self, value):
        if value is None:
            return 0
        if value < 0 or value > 10:
            raise serializers.ValidationError("Priority must be between 0 and 10.")
        return value

    def validate_expires_at(self, value):
        if value and value <= timezone.now():
            raise serializers.ValidationError("Expiry date must be in the future.")
        return value
