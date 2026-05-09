"""
PHC Test Suite
==============
Unit tests covering models, services, selectors, and API views.

Run with:
    python manage.py test applications.health_center.tests

Approach:
  - TestCase for DB-level tests (models, services, selectors)
  - APIClient-based tests for views (thin-view smoke tests)
"""

from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from ..models import (
    Admission,
    AllMedicine,
    AmbulanceRequest,
    Appointment,
    Complaint,
    Doctor,
    DoctorSchedule,
    StockEntry,
)
from .. import services, selectors


# ===========================================================================
# ── Helpers ─────────────────────────────────────────────────────────────────
# ===========================================================================

def make_user(username='patient1'):
    return User.objects.create_user(username=username, password='testpass')


def make_doctor(name='Dr. Test', phone='9999900001', spec='General', active=True) -> Doctor:
    return Doctor.objects.create(
        doctor_name=name,
        doctor_phone=phone,
        specialization=spec,
        active=active,
    )


def make_medicine(name='Paracetamol') -> AllMedicine:
    return AllMedicine.objects.create(medicine_name=name)


def make_stock(medicine=None, qty=100, supplier='SupplierA', days_until_expiry=60) -> StockEntry:
    if medicine is None:
        medicine = make_medicine()
    return StockEntry.objects.create(
        medicine=medicine,
        quantity=qty,
        supplier=supplier,
        expiry_date=date.today() + timedelta(days=days_until_expiry),
        date=date.today(),
    )


# ===========================================================================
# ── Model Tests ──────────────────────────────────────────────────────────────
# ===========================================================================

class DoctorModelTest(TestCase):
    def test_str_representation(self):
        doctor = make_doctor(name='Dr. A. Sharma')
        self.assertIn('Dr. A. Sharma', str(doctor))

    def test_default_active_true(self):
        doctor = Doctor.objects.create(
            doctor_name='Dr. B. Kumar',
            doctor_phone='9999900002',
            specialization='Cardiology',
        )
        self.assertTrue(doctor.active)


class AmbulanceRequestModelTest(TestCase):
    def test_end_date_nullable(self):
        user = make_user('ambuser')
        req = AmbulanceRequest.objects.create(
            user_id=user.username,
            reason='Emergency',
            start_date=date.today(),
        )
        self.assertIsNone(req.end_date)


class AdmissionModelTest(TestCase):
    def test_discharge_date_nullable(self):
        user = make_user('admuser')
        doctor = make_doctor(phone='9100000001')
        admit = Admission.objects.create(
            user_id=user.username,
            doctor_id=doctor.id,
            admission_date=date.today(),
            reason='Fever',
        )
        self.assertIsNone(admit.discharge_date)


class StockEntryReturnedFieldTest(TestCase):
    def test_returned_defaults_false(self):
        stock = make_stock()
        self.assertFalse(stock.returned)
        self.assertIsNone(stock.returned_date)


# ===========================================================================
# ── Selector Tests ───────────────────────────────────────────────────────────
# ===========================================================================

class SelectorTest(TestCase):
    def setUp(self):
        self.user = make_user('seluser')
        self.doctor = make_doctor(phone='9200000001')

    def test_get_active_doctors_excludes_inactive(self):
        inactive = make_doctor(name='Dr. Inactive', phone='9200000002', active=False)
        active_doctors = list(selectors.get_active_doctors())
        self.assertIn(self.doctor, active_doctors)
        self.assertNotIn(inactive, active_doctors)

    def test_get_expired_stock_entries(self):
        expired_stock = make_stock(days_until_expiry=-1)
        fresh_stock = make_stock(days_until_expiry=30)
        result = list(selectors.get_expired_stock_entries())
        self.assertIn(expired_stock, result)
        self.assertNotIn(fresh_stock, result)

    def test_get_all_admissions(self):
        doctor = make_doctor(phone='9200000003')
        Admission.objects.create(
            user_id=self.user.username,
            doctor_id=doctor.id,
            admission_date=date.today(),
            reason='Test admission',
        )
        admissions = list(selectors.get_all_admissions())
        self.assertEqual(len(admissions), 1)

    def test_get_appointments_for_patient(self):
        doctor = make_doctor(phone='9200000004')
        Appointment.objects.create(
            user_id=self.user.username,
            doctor=doctor,
            appointment_date=date.today(),
            description='Fever',
        )
        appts = list(selectors.get_appointments_for_patient(self.user.username))
        self.assertEqual(len(appts), 1)


# ===========================================================================
# ── Service Tests ────────────────────────────────────────────────────────────
# ===========================================================================

class DoctorServiceTest(TestCase):
    def test_create_doctor_success(self):
        doctor = services.create_doctor(
            doctor_name='Dr. New Doctor',
            doctor_phone='9876500001',
            specialization='Pediatrics',
        )
        self.assertTrue(doctor.active)
        self.assertEqual(doctor.specialization, 'Pediatrics')

    def test_create_doctor_missing_name_raises(self):
        with self.assertRaises(Exception):
            services.create_doctor(
                doctor_name='',
                doctor_phone='9876500002',
                specialization='Dermatology',
            )


class ScheduleServiceTest(TestCase):
    def setUp(self):
        self.doctor = make_doctor(phone='9300000001')

    def test_upsert_creates_schedule(self):
        sched = services.upsert_doctor_schedule(
            doctor_id=self.doctor.pk,
            day='Tuesday',
            from_time='10:00',
            to_time='13:00',
            room=3,
        )
        self.assertEqual(sched.day, 'Tuesday')

    def test_upsert_updates_existing_schedule(self):
        services.upsert_doctor_schedule(
            doctor_id=self.doctor.pk,
            day='Wednesday',
            from_time='08:00',
            to_time='11:00',
            room=1,
        )
        updated = services.upsert_doctor_schedule(
            doctor_id=self.doctor.pk,
            day='Wednesday',
            from_time='09:00',
            to_time='12:00',
            room=2,
        )
        self.assertEqual(updated.room, 2)
        self.assertEqual(
            DoctorSchedule.objects.filter(doctor_id=self.doctor, day='Wednesday').count(),
            1,
        )

    def test_delete_schedule(self):
        services.upsert_doctor_schedule(
            doctor_id=self.doctor.pk,
            day='Friday',
            from_time='14:00',
            to_time='17:00',
            room=4,
        )
        sched = DoctorSchedule.objects.get(doctor_id=self.doctor, day='Friday')
        services.delete_doctor_schedule(sched.pk)
        self.assertFalse(DoctorSchedule.objects.filter(pk=sched.pk).exists())


class StockServiceTest(TestCase):
    def test_add_new_stock(self):
        stock = services.add_stock_entry(
            medicine_name='Ibuprofen',
            quantity=50,
            supplier='MedCo',
            expiry_date=date.today() + timedelta(days=365),
        )
        self.assertEqual(stock.quantity, 50)
        self.assertFalse(stock.returned)

    def test_zero_quantity_raises(self):
        with self.assertRaises(ValidationError):
            services.add_stock_entry(
                medicine_name='Aspirin',
                quantity=0,
                supplier='S1',
                expiry_date=date.today() + timedelta(days=30),
            )

    def test_missing_supplier_raises(self):
        with self.assertRaises(ValidationError):
            services.add_stock_entry(
                medicine_name='Aspirin',
                quantity=10,
                supplier='',
                expiry_date=date.today() + timedelta(days=30),
            )

    def test_missing_expiry_raises(self):
        with self.assertRaises(ValidationError):
            services.add_stock_entry(
                medicine_name='Aspirin',
                quantity=10,
                supplier='S1',
                expiry_date=None,
            )


class ReturnExpiryServiceTest(TestCase):
    def test_return_stock_entry(self):
        stock = make_stock(days_until_expiry=-1)
        updated = services.return_expired_stock_entry(stock.pk)
        self.assertTrue(updated.returned)
        self.assertEqual(updated.returned_date, date.today())


class AdmissionServiceTest(TestCase):
    def setUp(self):
        self.user = make_user('admuser2')
        self.doctor = make_doctor(phone='9400000001')

    def test_create_admission_success(self):
        admission = services.create_admission(
            user_id=self.user.username,
            doctor_id=self.doctor.pk,
            admission_date=date.today(),
            reason='Fever requiring hospitalisation',
        )
        self.assertIsNone(admission.discharge_date)

    def test_discharge_patient(self):
        admission = services.create_admission(
            user_id=self.user.username,
            doctor_id=self.doctor.pk,
            admission_date=date.today() - timedelta(days=3),
            reason='Surgery',
        )
        discharged = services.discharge_patient_record(admission.pk)
        self.assertEqual(discharged.discharge_date, date.today())


class AmbulanceServiceTest(TestCase):
    def setUp(self):
        self.user = make_user('ambuser2')

    def test_end_ambulance_service(self):
        req = AmbulanceRequest.objects.create(
            user_id=self.user.username,
            reason='Transport',
            start_date=date.today(),
        )
        updated = services.end_ambulance_service(req.pk)
        self.assertEqual(updated.status, 'completed')


# ===========================================================================
# ── API View Tests (smoke tests) ─────────────────────────────────────────────
# ===========================================================================

class PatientDashboardAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('dashuser', password='pass')
        self.client.force_authenticate(user=self.user)
        import applications.health_center.api.views as v
        self._orig = v._is_patient
        v._is_patient = lambda u: True

    def tearDown(self):
        import applications.health_center.api.views as v
        v._is_patient = self._orig

    def test_dashboard_returns_200(self):
        resp = self.client.get('/healthcenter/api/phc/patient/dashboard/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for key in ('appointments', 'prescriptions', 'complaints', 'ambulance_requests', 'doctors'):
            self.assertIn(key, resp.data)


class AmbulanceAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('ambapi', password='pass')
        self.client.force_authenticate(user=self.user)
        import applications.health_center.api.views as v
        self._orig = v._is_patient
        v._is_patient = lambda u: True

    def tearDown(self):
        import applications.health_center.api.views as v
        v._is_patient = self._orig

    def test_create_ambulance_request(self):
        payload = {'reason': 'Emergency', 'start_date': str(date.today())}
        resp = self.client.post('/healthcenter/api/phc/patient/ambulance/', payload)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['reason'], 'Emergency')

    def test_create_missing_reason(self):
        payload = {'start_date': str(date.today())}
        resp = self.client.post('/healthcenter/api/phc/patient/ambulance/', payload)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cancel_ambulance_request(self):
        req = AmbulanceRequest.objects.create(
            user_id=self.user.username,
            reason='Test',
            start_date=date.today(),
        )
        resp = self.client.delete(f'/healthcenter/api/phc/patient/ambulance/{req.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        req.refresh_from_db()
        self.assertEqual(req.status, 'cancelled')


class CompoundAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.compounder = User.objects.create_user('comp1', password='pass')
        self.client.force_authenticate(user=self.compounder)
        import applications.health_center.api.views as v
        self._orig_c = v._is_compounder
        v._is_compounder = lambda u: True

    def tearDown(self):
        import applications.health_center.api.views as v
        v._is_compounder = self._orig_c

    def test_add_doctor(self):
        payload = {
            'doctor_name': 'Dr. Test Doctor',
            'doctor_phone': '9876510001',
            'specialization': 'General Medicine',
        }
        resp = self.client.post('/healthcenter/api/phc/compounder/doctor/', payload)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['specialization'], 'General Medicine')

    def test_add_stock(self):
        payload = {
            'medicine_name': 'Cetirizine',
            'quantity': 50,
            'supplier': 'PharmaCo',
            'expiry_date': str(date.today() + timedelta(days=365)),
            'threshold': 5,
        }
        resp = self.client.post('/healthcenter/api/phc/compounder/stock/', payload)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn('medicine_name', resp.data)

    def test_compounder_dashboard(self):
        resp = self.client.get('/healthcenter/api/phc/compounder/dashboard/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for key in ('complaints', 'stock', 'hospital_admissions', 'expired_batches'):
            self.assertIn(key, resp.data)

    def test_admit_and_discharge_patient(self):
        doctor = make_doctor(phone='9500000001')
        # Admit
        payload = {
            'user_id': 'patient1',
            'doctor_id': doctor.pk,
            'admission_date': str(date.today()),
            'reason': 'Viral fever',
        }
        resp = self.client.post('/healthcenter/api/phc/compounder/admission/', payload)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        admission_id = resp.data['id']
        self.assertIsNone(resp.data['discharge_date'])

        # Discharge (no body needed — defaults to today)
        resp2 = self.client.patch(f'/healthcenter/api/phc/compounder/admission/{admission_id}/')
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(resp2.data['discharge_date'])

    def test_unauthorized_user_gets_403_on_compounder_routes(self):
        import applications.health_center.api.views as v
        v._is_compounder = lambda u: False
        resp = self.client.get('/healthcenter/api/phc/compounder/dashboard/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        v._is_compounder = lambda u: True
