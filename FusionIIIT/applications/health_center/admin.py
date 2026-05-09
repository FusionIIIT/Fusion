"""
Health Center Admin Configuration
====================================
Registers all health center models in the Django admin interface.
"""

from django.contrib import admin

from .models import (
    Doctor,
    DoctorSchedule,
    DoctorAttendance,
    HealthProfile,
    Appointment,
    Consultation,
    Medicine,
    Stock,
    Expiry,
    Prescription,
    PrescribedMedicine,
    ComplaintV2,
    HospitalAdmit,
    AmbulanceRecordsV2,
    ReimbursementClaim,
    ClaimDocument,
    InventoryRequisition,
    LowStockAlert,
    AuditLog,
)


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('id', 'doctor_name', 'specialization', 'is_active')
    search_fields = ('doctor_name', 'specialization')
    list_filter = ('is_active',)
    ordering = ('doctor_name',)


@admin.register(DoctorSchedule)
class DoctorScheduleAdmin(admin.ModelAdmin):
    list_display = ('id', 'doctor', 'day_of_week', 'start_time', 'end_time')
    list_filter = ('day_of_week',)
    ordering = ('doctor', 'day_of_week')


@admin.register(DoctorAttendance)
class DoctorAttendanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'doctor', 'attendance_date', 'status')
    list_filter = ('status', 'attendance_date')
    ordering = ('-attendance_date',)


@admin.register(HealthProfile)
class HealthProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'blood_group')
    search_fields = ('patient__user__first_name', 'patient__user__last_name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'doctor', 'appointment_date', 'status')
    list_filter = ('status', 'appointment_date', 'appointment_type')
    search_fields = ('patient__user__first_name', 'doctor__doctor_name')
    readonly_fields = ('created_at',)
    ordering = ('-appointment_date',)


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'doctor', 'consultation_date')
    list_filter = ('consultation_date',)
    search_fields = ('patient__user__first_name', 'doctor__doctor_name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-consultation_date',)


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('id', 'medicine_name', 'brand_name', 'unit', 'reorder_threshold')
    search_fields = ('medicine_name', 'brand_name', 'generic_name')
    ordering = ('medicine_name',)


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('id', 'medicine', 'total_qty', 'last_updated')
    search_fields = ('medicine__medicine_name',)
    readonly_fields = ('created_at', 'last_updated')
    ordering = ('medicine',)


@admin.register(Expiry)
class ExpiryAdmin(admin.ModelAdmin):
    list_display = ('id', 'stock', 'batch_no', 'qty', 'expiry_date', 'is_returned')
    list_filter = ('is_returned', 'expiry_date')
    search_fields = ('stock__medicine__medicine_name', 'batch_no')
    readonly_fields = ('created_at',)
    ordering = ('expiry_date',)  # FIFO: earliest expiry first


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'doctor', 'issued_date', 'status')
    list_filter = ('status', 'issued_date')
    search_fields = ('patient__user__first_name', 'doctor__doctor_name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-issued_date',)


@admin.register(PrescribedMedicine)
class PrescribedMedicineAdmin(admin.ModelAdmin):
    list_display = ('id', 'prescription', 'medicine', 'qty_prescribed', 'qty_dispensed', 'is_dispensed')
    list_filter = ('is_dispensed', 'is_revoked', 'created_at')
    search_fields = ('prescription__patient__user__first_name', 'medicine__medicine_name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(ComplaintV2)
class ComplaintV2Admin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'title', 'category', 'status', 'created_date')
    list_filter = ('status', 'category', 'created_date')
    search_fields = ('patient__user__first_name', 'patient__user__last_name', 'title')
    readonly_fields = ('created_date', 'updated_at')
    ordering = ('-created_date',)


@admin.register(HospitalAdmit)
class HospitalAdmitAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'hospital_name', 'admission_date', 'discharge_date', 'referred_by')
    list_filter = ('admission_date', 'discharge_date')
    search_fields = ('patient__user__first_name', 'hospital_name', 'reason')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-admission_date',)


@admin.register(AmbulanceRecordsV2)
class AmbulanceRecordsV2Admin(admin.ModelAdmin):
    list_display = ('id', 'registration_number', 'vehicle_type', 'driver_name', 'status', 'is_active')
    list_filter = ('status', 'is_active', 'vehicle_type')
    search_fields = ('registration_number', 'driver_name', 'driver_contact')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('registration_number',)


@admin.register(ReimbursementClaim)
class ReimbursementClaimAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'claim_amount', 'status', 'submission_date')
    list_filter = ('status', 'submission_date')
    search_fields = ('patient__user__first_name', 'patient__user__last_name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-submission_date',)


@admin.register(ClaimDocument)
class ClaimDocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'claim', 'document_type', 'uploaded_at', 'verified')
    list_filter = ('document_type', 'verified', 'uploaded_at')
    ordering = ('-uploaded_at',)


@admin.register(InventoryRequisition)
class InventoryRequisitionAdmin(admin.ModelAdmin):
    list_display = ('id', 'medicine', 'quantity_requested', 'status', 'created_date')
    list_filter = ('status', 'created_date')
    search_fields = ('medicine__medicine_name',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_date',)


@admin.register(LowStockAlert)
class LowStockAlertAdmin(admin.ModelAdmin):
    list_display = ('id', 'medicine', 'current_stock', 'acknowledged')
    list_filter = ('acknowledged', 'alert_triggered_at')
    search_fields = ('medicine__medicine_name',)
    readonly_fields = ('alert_triggered_at',)
    ordering = ('-alert_triggered_at',)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'action_type', 'entity_type', 'timestamp')
    list_filter = ('action_type', 'entity_type', 'timestamp')
    search_fields = ('user__user__first_name', 'entity_type')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)

