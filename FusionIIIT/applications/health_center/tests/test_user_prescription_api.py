"""
Test User-Based Prescription Creation API
==========================================
Tests for the new user_id-based prescription API endpoint.

Test Cases:
1. User endpoint returns all active users
2. User endpoint filters by search
3. Prescription creation with valid user_id
4. Prescription creation fails with invalid user_id
5. Prescription creation fails when user has no consultation
6. Prescription uses user's latest consultation
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from applications.globals.models import ExtraInfo, DepartmentInfo
from applications.health_center.models import (
    Doctor, Consultation, Medicine, Stock, Expiry, Prescription
)
from rest_framework.test import APIClient
from rest_framework import status


class CompounderUserAPITestCase(TestCase):
    """Test the CompounderUserView API endpoint"""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data for all test methods"""
        # Create a department
        cls.dept = DepartmentInfo.objects.create(
            dept_id="CS",
            dept_name="Computer Science"
        )
        
        # Create test users with ExtraInfo
        cls.user1 = User.objects.create_user(
            username='rahul',
            first_name='Rahul',
            last_name='Sharma',
            email='rahul@test.com',
            is_active=True
        )
        ExtraInfo.objects.create(
            id='rahul_extra',
            user=cls.user1,
            user_type='STUDENT',
            department=cls.dept
        )
        
        cls.user2 = User.objects.create_user(
            username='priya',
            first_name='Priya',
            last_name='Patel',
            email='priya@test.com',
            is_active=True
        )
        ExtraInfo.objects.create(
            id='priya_extra',
            user=cls.user2,
            user_type='STUDENT',
            department=cls.dept
        )
        
        # Create inactive user
        cls.user_inactive = User.objects.create_user(
            username='inactive_user',
            first_name='Inactive',
            last_name='User',
            email='inactive@test.com',
            is_active=False
        )
        
        # Create a PHC staff user (for authorization)
        cls.phc_staff = User.objects.create_user(
            username='compounder',
            first_name='Comp',
            last_name='Ounder',
            email='comp@test.com',
            is_active=True
        )
        ExtraInfo.objects.create(
            id='compounder_extra',
            user=cls.phc_staff,
            user_type='PHC_STAFF',
            department=cls.dept
        )
    
    def setUp(self):
        """Set up for each test"""
        self.client = APIClient()
        # Authenticate as PHC staff
        self.client.force_authenticate(user=self.phc_staff)
    
    def test_user_list_returns_active_users(self):
        """Test that user endpoint returns only active users"""
        response = self.client.get('/api/phc/compounder/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # rahul, priya, compounder (active users)
        
        usernames = [user['username'] for user in response.data]
        self.assertIn('rahul', usernames)
        self.assertIn('priya', usernames)
        self.assertNotIn('inactive_user', usernames)
    
    def test_user_list_format(self):
        """Test that user response has correct format"""
        response = self.client.get('/api/phc/compounder/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        user_data = response.data[0]
        self.assertIn('id', user_data)
        self.assertIn('value', user_data)
        self.assertIn('label', user_data)
        self.assertIn('username', user_data)
        self.assertIn('full_name', user_data)
        self.assertIn('email', user_data)
    
    def test_user_list_search_filter(self):
        """Test user search by username"""
        response = self.client.get('/api/phc/compounder/users/?search=rahul')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], 'rahul')
    
    def test_user_list_search_by_name(self):
        """Test user search by first/last name"""
        response = self.client.get('/api/phc/compounder/users/?search=priya')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], 'priya')
    
    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated users cannot access API"""
        client = APIClient()
        response = client.get('/api/phc/compounder/users/')
        # Should be 401 or 403
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


class UserPrescriptionCreationTestCase(TestCase):
    """Test prescription creation with user_id"""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data"""
        # Create department
        cls.dept = DepartmentInfo.objects.create(
            dept_id="CS",
            dept_name="Computer Science"
        )
        
        # Create patient user
        cls.patient_user = User.objects.create_user(
            username='patient1',
            first_name='Patient',
            last_name='One',
            email='patient@test.com',
            is_active=True
        )
        cls.patient_profile = ExtraInfo.objects.create(
            id='patient1_extra',
            user=cls.patient_user,
            user_type='STUDENT',
            department=cls.dept
        )
        
        # Create PHC staff user
        cls.phc_staff = User.objects.create_user(
            username='compounder',
            first_name='Comp',
            last_name='Ounder',
            email='comp@test.com',
            is_active=True
        )
        ExtraInfo.objects.create(
            id='compounder_extra',
            user=cls.phc_staff,
            user_type='PHC_STAFF',
            department=cls.dept
        )
        
        # Create doctor
        cls.doctor = Doctor.objects.create(
            doctor_name='Dr. Sharma',
            specialization='General Medicine',
            is_active=True
        )
        
        # Create medicine
        cls.medicine = Medicine.objects.create(
            medicine_name='Paracetamol',
            brand_name='Crocin',
            unit='tablets'
        )
        
        # Create stock
        cls.stock = Stock.objects.create(
            medicine_detail=cls.medicine,
            qty_in_hand=100
        )
        
        # Create expiry batch
        cls.expiry = Expiry.objects.create(
            stock=cls.stock,
            batch_no='BATCH001',
            qty=100,
            expiry_date=timezone.now() + timedelta(days=30)
        )
        
        # Create consultation for patient
        cls.consultation = Consultation.objects.create(
            patient=cls.patient_profile,
            doctor=cls.doctor,
            chief_complaint='Headache',
            consultation_date=timezone.now(),
            ambulance_requested='no'
        )
    
    def setUp(self):
        """Set up for each test"""
        self.client = APIClient()
        self.client.force_authenticate(user=self.phc_staff)
    
    def test_prescription_creation_with_user_id(self):
        """Test that prescription can be created with user_id"""
        payload = {
            'user_id': self.patient_user.id,
            'doctor_id': self.doctor.id,
            'medicines': [
                {
                    'medicine': self.medicine.id,
                    'qty_prescribed': 10,
                    'days': 5,
                    'times_per_day': 2,
                    'instructions': 'After food',
                    'notes': 'Test note'
                }
            ],
            'details': 'Test prescription',
            'special_instructions': 'Take with water'
        }
        
        response = self.client.post('/api/phc/compounder/prescription/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
    
    def test_prescription_fails_with_invalid_user_id(self):
        """Test that prescription creation fails with invalid user_id"""
        payload = {
            'user_id': 9999,
            'doctor_id': self.doctor.id,
            'medicines': [
                {
                    'medicine': self.medicine.id,
                    'qty_prescribed': 10,
                    'days': 5,
                    'times_per_day': 2
                }
            ]
        }
        
        response = self.client.post('/api/phc/compounder/prescription/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('not found', response.data['detail'].lower())
    
    def test_prescription_fails_without_consultation(self):
        """Test that prescription fails when user has no consultation"""
        # Create a new user without consultation
        user_no_consult = User.objects.create_user(
            username='no_consult_user',
            first_name='NoConsult',
            last_name='User'
        )
        ExtraInfo.objects.create(
            id='no_consult_extra',
            user=user_no_consult,
            user_type='STUDENT',
            department=self.dept
        )
        
        payload = {
            'user_id': user_no_consult.id,
            'doctor_id': self.doctor.id,
            'medicines': [
                {
                    'medicine': self.medicine.id,
                    'qty_prescribed': 10,
                    'days': 5,
                    'times_per_day': 2
                }
            ]
        }
        
        response = self.client.post('/api/phc/compounder/prescription/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('consultation', response.data['detail'].lower())
    
    def test_prescription_uses_latest_consultation(self):
        """Test that prescription uses user's latest consultation"""
        # Create another older consultation
        old_consultation = Consultation.objects.create(
            patient=self.patient_profile,
            doctor=self.doctor,
            chief_complaint='Old complaint',
            consultation_date=timezone.now() - timedelta(days=5),
            ambulance_requested='no'
        )
        
        payload = {
            'user_id': self.patient_user.id,
            'doctor_id': self.doctor.id,
            'medicines': [
                {
                    'medicine': self.medicine.id,
                    'qty_prescribed': 10,
                    'days': 5,
                    'times_per_day': 2
                }
            ]
        }
        
        response = self.client.post('/api/phc/compounder/prescription/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify prescription is linked to latest consultation (self.consultation)
        prescription = Prescription.objects.get(id=response.data['id'])
        self.assertEqual(prescription.consultation.id, self.consultation.id)
    
    def test_missing_user_id_validation(self):
        """Test that missing user_id returns error"""
        payload = {
            'doctor_id': self.doctor.id,
            'medicines': []
        }
        
        response = self.client.post('/api/phc/compounder/prescription/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_missing_doctor_id_validation(self):
        """Test that missing doctor_id returns error"""
        payload = {
            'user_id': self.patient_user.id,
            'medicines': []
        }
        
        response = self.client.post('/api/phc/compounder/prescription/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_missing_medicines_validation(self):
        """Test that missing medicines returns error"""
        payload = {
            'user_id': self.patient_user.id,
            'doctor_id': self.doctor.id
        }
        
        response = self.client.post('/api/phc/compounder/prescription/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


if __name__ == '__main__':
    import unittest
    unittest.main()
