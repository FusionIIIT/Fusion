"""
Shared test fixtures and helper utilities for PHC module tests.
================================================================
Provides factory functions to create test users with proper ExtraInfo
records, doctors, medicines, stock, and other test data.

Role mapping (as checked by decorators.py):
  - is_patient:     user_type in ['STUDENT', 'FACULTY', 'STAFF']
  - is_employee:    user_type in ['FACULTY', 'STAFF']
  - is_compounder:  user_type == 'ADMIN'
  - is_auditor:     user_type == 'AUDITOR'
"""

from datetime import date, time, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient, APITestCase

from applications.globals.models import ExtraInfo, DepartmentInfo
from ..models import (
    Doctor, DoctorSchedule, DoctorAttendance,
    Medicine, Stock, Expiry,
    Consultation, Prescription, PrescribedMedicine,
    ReimbursementClaim, ClaimDocument, InventoryRequisition,
    ComplaintV2, HospitalAdmit, AmbulanceRecordsV2,
    LowStockAlert, AuditLog, HealthProfile,
    AttendanceStatusChoices, ReimbursementStatusChoices,
    RequisitionStatusChoices, ComplaintStatusChoices,
    AmbulanceStatusChoices, DayOfWeekChoices,
)


# ===========================================================================
# ── URL Prefix ─────────────────────────────────────────────────────────────
# ===========================================================================

API_BASE = '/healthcenter/api/phc'


# ===========================================================================
# ── User Factory Functions ─────────────────────────────────────────────────
# ===========================================================================

_user_counter = 0

def _next_id():
    global _user_counter
    _user_counter += 1
    return _user_counter


def create_patient_user(username=None, user_type='STUDENT'):
    """Create a patient. Decorators expect UPPERCASE: STUDENT/FACULTY/STAFF."""
    username = username or f'patient_{_next_id()}'
    user = User.objects.create_user(username=username, password='testpass123')
    extra = ExtraInfo.objects.create(
        id=f'{username}_id',
        user=user,
        user_type=user_type,
    )
    return user, extra


def create_faculty_user(username=None):
    """FACULTY role — can submit reimbursements."""
    return create_patient_user(username=username or f'faculty_{_next_id()}', user_type='FACULTY')


def create_staff_user(username=None):
    """STAFF role — can submit reimbursements."""
    return create_patient_user(username=username or f'staff_{_next_id()}', user_type='STAFF')


def create_compounder_user(username=None):
    """ADMIN role = PHC staff / compounder."""
    username = username or f'compounder_{_next_id()}'
    user = User.objects.create_user(username=username, password='testpass123')
    extra = ExtraInfo.objects.create(
        id=f'{username}_id',
        user=user,
        user_type='ADMIN',
    )
    return user, extra


def create_auditor_user(username=None):
    """AUDITOR role."""
    username = username or f'auditor_{_next_id()}'
    user = User.objects.create_user(username=username, password='testpass123')
    extra = ExtraInfo.objects.create(
        id=f'{username}_id',
        user=user,
        user_type='AUDITOR',
    )
    return user, extra


# ===========================================================================
# ── Model Factory Functions ────────────────────────────────────────────────
# ===========================================================================

_phone_counter = 9000000000

def _next_phone():
    global _phone_counter
    _phone_counter += 1
    return str(_phone_counter)


def create_doctor(name='Dr. Test', phone=None, spec='General Medicine', active=True):
    return Doctor.objects.create(
        doctor_name=name,
        doctor_phone=phone or _next_phone(),
        specialization=spec,
        is_active=active,
    )


def create_schedule(doctor, day='MONDAY', start='09:00', end='13:00', room='101'):
    return DoctorSchedule.objects.create(
        doctor=doctor,
        day_of_week=day,
        start_time=start,
        end_time=end,
        room_number=room,
    )


def create_attendance(doctor, att_status='AVAILABLE', att_date=None, marked_by=None):
    return DoctorAttendance.objects.create(
        doctor=doctor,
        attendance_date=att_date or date.today(),
        status=att_status,
        marked_by=marked_by,
    )


def create_medicine(name=None, threshold=10):
    name = name or f'Medicine_{_next_id()}'
    return Medicine.objects.create(medicine_name=name, reorder_threshold=threshold)


def create_stock(medicine, total_qty=100):
    return Stock.objects.create(medicine=medicine, total_qty=total_qty)


def create_expiry(stock, batch_no=None, qty=50, days_until_expiry=180):
    batch_no = batch_no or f'BATCH_{_next_id()}'
    return Expiry.objects.create(
        stock=stock, batch_no=batch_no, qty=qty,
        expiry_date=date.today() + timedelta(days=days_until_expiry),
    )


def create_consultation(patient_extra, doctor, complaint='Fever'):
    return Consultation.objects.create(
        patient=patient_extra, doctor=doctor, chief_complaint=complaint,
    )


def create_prescription(consultation, patient_extra, doctor):
    return Prescription.objects.create(
        consultation=consultation, patient=patient_extra, doctor=doctor,
    )


def create_reimbursement_claim(patient_extra, amount=5000, days_ago=10,
                                 claim_status='SUBMITTED', prescription=None):
    return ReimbursementClaim.objects.create(
        patient=patient_extra,
        prescription=prescription,
        claim_amount=Decimal(str(amount)),
        expense_date=date.today() - timedelta(days=days_ago),
        description='Medical expenses for treatment',
        status=claim_status,
        created_by=patient_extra,
    )


def create_complaint(patient_extra, title='Test Complaint', category='SERVICE'):
    return ComplaintV2.objects.create(
        patient=patient_extra, title=title,
        description='Description of the complaint', category=category,
    )


def create_ambulance(reg_no=None, vehicle_type='Type A'):
    reg_no = reg_no or f'KA-{_next_id():04d}'
    return AmbulanceRecordsV2.objects.create(
        vehicle_type=vehicle_type, registration_number=reg_no,
        driver_name='Driver Test', driver_contact='9876543210',
    )


def create_hospital_admit(patient_extra, hospital_name='City Hospital'):
    return HospitalAdmit.objects.create(
        patient=patient_extra, hospital_id='HOSP001',
        hospital_name=hospital_name, admission_date=date.today(),
        reason='Treatment required',
    )


def create_requisition(medicine, compounder_extra, qty=100, req_status='CREATED'):
    return InventoryRequisition.objects.create(
        medicine=medicine, quantity_requested=qty,
        status=req_status, created_by=compounder_extra,
    )


# ===========================================================================
# ── Base Test Class ────────────────────────────────────────────────────────
# ===========================================================================

class PHCBaseAPITestCase(APITestCase):
    """Base class with shared test data for all PHC API tests."""

    @classmethod
    def setUpTestData(cls):
        cls.patient_user, cls.patient_extra = create_patient_user('test_patient', 'STUDENT')
        cls.faculty_user, cls.faculty_extra = create_faculty_user('test_faculty')
        cls.staff_user, cls.staff_extra = create_staff_user('test_staff')
        cls.compounder_user, cls.compounder_extra = create_compounder_user('test_compounder')
        cls.auditor_user, cls.auditor_extra = create_auditor_user('test_auditor')

        cls.doctor = create_doctor(name='Dr. Sharma', phone='9100000001')
        cls.doctor_inactive = create_doctor(name='Dr. Inactive', phone='9100000002', active=False)
        cls.schedule = create_schedule(cls.doctor, day='MONDAY')

        cls.medicine = create_medicine('Paracetamol')
        cls.stock = create_stock(cls.medicine, total_qty=100)
        cls.expiry_batch1 = create_expiry(cls.stock, 'BATCH-A', qty=60, days_until_expiry=30)
        cls.expiry_batch2 = create_expiry(cls.stock, 'BATCH-B', qty=40, days_until_expiry=180)

    def setUp(self):
        self.client = APIClient()

    def auth_as_patient(self):
        self.client.force_authenticate(user=self.patient_user)

    def auth_as_faculty(self):
        self.client.force_authenticate(user=self.faculty_user)

    def auth_as_staff(self):
        self.client.force_authenticate(user=self.staff_user)

    def auth_as_compounder(self):
        self.client.force_authenticate(user=self.compounder_user)

    def auth_as_auditor(self):
        self.client.force_authenticate(user=self.auditor_user)

    def auth_as_none(self):
        self.client.force_authenticate(user=None)
