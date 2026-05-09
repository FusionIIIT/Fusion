"""
Test API Endpoints for Prescription Creation Form
==================================================
Tests the new consultation and doctor filtering endpoints

Run with: python manage.py test health_center.test_api_endpoints -v 2
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from applications.globals.models import ExtraInfo
from ..models import Doctor, Consultation, Appointment
import json


class ConsultationAPITestCase(TestCase):
    """Test ConsultationView API endpoints"""
    
    def setUp(self):
        """Create test data"""
        # Create test users
        self.admin_user = User.objects.create_user(
            username='admin_doctor',
            password='testpass123',
            first_name='Test',
            last_name='Admin'
        )
        self.admin_extrainfo = ExtraInfo.objects.create(
            user=self.admin_user,
            role='ADMIN',  # PHC staff
            id_number='ADM001'
        )
        
        self.patient_user = User.objects.create_user(
            username='patient_test',
            password='testpass123',
            first_name='Patient',
            last_name='Name'
        )
        self.patient_extrainfo = ExtraInfo.objects.create(
            user=self.patient_user,
            role='STUDENT',
            id_number='STU001'
        )
        
        # Create test doctors
        self.doctor1 = Doctor.objects.create(
            doctor_name='Dr. Sharma',
            specialization='Cardiology',
            email='sharma@hospital.com',
            is_active=True
        )
        
        self.doctor2 = Doctor.objects.create(
            doctor_name='Dr. Patel',
            specialization='Orthopaedics',
            email='patel@hospital.com',
            is_active=True
        )
        
        self.doctor_inactive = Doctor.objects.create(
            doctor_name='Dr. Inactive',
            specialization='General',
            email='inactive@hospital.com',
            is_active=False
        )
        
        # Create test consultations
        now = timezone.now()
        self.recent_consultation = Consultation.objects.create(
            patient=self.patient_extrainfo,
            doctor=self.doctor1,
            chief_complaint='Chest pain',
            consultation_date=now,
            blood_pressure_systolic=120,
            blood_pressure_diastolic=80,
            ambulance_requested='no',
        )
        
        old_consultation = Consultation.objects.create(
            patient=self.patient_extrainfo,
            doctor=self.doctor2,
            chief_complaint='Back pain',
            consultation_date=now - timedelta(days=10),
            ambulance_requested='no',
            blood_pressure_systolic=120,
            blood_pressure_diastolic=80,
        )
        
        self.client = Client()
    
    def test_consultations_list_without_auth(self):
        """Test that unauthorized access is denied"""
        response = self.client.get('/api/phc/compounder/consultations/')
        self.assertEqual(response.status_code, 401)
    
    def test_consultations_list_with_auth(self):
        """Test consultation list with authentication"""
        self.client.login(username='admin_doctor', password='testpass123')
        response = self.client.get('/api/phc/compounder/consultations/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
    
    def test_consultations_list_response_format(self):
        """Test response format includes required fields"""
        self.client.login(username='admin_doctor', password='testpass123')
        response = self.client.get('/api/phc/compounder/consultations/')
        
        data = response.json()
        self.assertGreater(len(data), 0)
        
        # Check first consultation has required fields
        consultation = data[0]
        self.assertIn('id', consultation)
        self.assertIn('value', consultation)
        self.assertIn('label', consultation)
        self.assertIn('patient_name', consultation)
        self.assertIn('doctor_name', consultation)
        self.assertIn('specialization', consultation)
        self.assertIn('chief_complaint', consultation)
        self.assertIn('consultation_date', consultation)
    
    def test_consultations_days_filter(self):
        """Test filtering consultations by days"""
        self.client.login(username='admin_doctor', password='testpass123')
        
        # Get consultations from last 5 days (should exclude old_consultation)
        response = self.client.get('/api/phc/compounder/consultations/?days=5')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        # Should have at least 1 recent consultation
        self.assertGreaterEqual(len(data), 1)
        
        # All should be within last 5 days
        for consultation in data:
            self.assertIn('consultation_date', consultation)
    
    def test_consultations_doctor_filter(self):
        """Test filtering consultations by doctor"""
        self.client.login(username='admin_doctor', password='testpass123')
        
        response = self.client.get(f'/api/phc/compounder/consultations/?doctor_id={self.doctor1.id}')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        for consultation in data:
            self.assertEqual(consultation['doctor_id'], self.doctor1.id)


class DoctorAPITestCase(TestCase):
    """Test DoctorView API endpoints with filtering"""
    
    def setUp(self):
        """Create test data"""
        # Create test admin user
        self.admin_user = User.objects.create_user(
            username='admin_doctor',
            password='testpass123'
        )
        self.admin_extrainfo = ExtraInfo.objects.create(
            user=self.admin_user,
            role='ADMIN',
            id_number='ADM001'
        )
        
        # Create test doctors with various specializations
        self.cardiologist = Doctor.objects.create(
            doctor_name='Dr. Sharma',
            specialization='Cardiology',
            email='sharma@hospital.com',
            is_active=True
        )
        
        self.orthopedist = Doctor.objects.create(
            doctor_name='Dr. Patel',
            specialization='Orthopaedics',
            email='patel@hospital.com',
            is_active=True
        )
        
        self.general = Doctor.objects.create(
            doctor_name='Dr. Singh',
            specialization='General Medicine',
            email='singh@hospital.com',
            is_active=True
        )
        
        self.inactive_doctor = Doctor.objects.create(
            doctor_name='Dr. Inactive',
            specialization='General',
            email='inactive@hospital.com',
            is_active=False
        )
        
        self.client = Client()
    
    def test_doctors_list_without_auth(self):
        """Test that unauthorized access is denied"""
        response = self.client.get('/api/phc/compounder/doctors/')
        self.assertEqual(response.status_code, 401)
    
    def test_doctors_list_with_auth(self):
        """Test doctor list with authentication"""
        self.client.login(username='admin_doctor', password='testpass123')
        response = self.client.get('/api/phc/compounder/doctors/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIsInstance(data, list)
    
    def test_doctors_active_only_filter(self):
        """Test filtering only active doctors"""
        self.client.login(username='admin_doctor', password='testpass123')
        
        # Get all doctors
        response_all = self.client.get('/api/phc/compounder/doctors/?active_only=false')
        data_all = response_all.json()
        
        # Get active only (default)
        response_active = self.client.get('/api/phc/compounder/doctors/?active_only=true')
        data_active = response_active.json()
        
        # Active should be fewer or equal
        self.assertLessEqual(len(data_active), len(data_all))
        
        # All active should have is_active=true
        for doctor in data_active:
            self.assertTrue(doctor.get('is_active', True))
    
    def test_doctors_specialization_filter(self):
        """Test filtering doctors by specialization"""
        self.client.login(username='admin_doctor', password='testpass123')
        
        # Filter by 'Cardiology'
        response = self.client.get('/api/phc/compounder/doctors/?specialization=Cardiology')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertGreater(len(data), 0)
        
        # All should have Cardiology in specialization
        for doctor in data:
            self.assertIn('Cardiology', doctor.get('specialization', ''))
    
    def test_doctors_response_format(self):
        """Test response includes specialization field"""
        self.client.login(username='admin_doctor', password='testpass123')
        response = self.client.get('/api/phc/compounder/doctors/?active_only=true')
        
        data = response.json()
        self.assertGreater(len(data), 0)
        
        # Check doctor has specialization
        doctor = data[0]
        self.assertIn('specialization', doctor)
        self.assertIn('doctor_name', doctor)
        self.assertIn('is_active', doctor)
    
    def test_specific_doctor_retrieval(self):
        """Test retrieving specific doctor by ID"""
        self.client.login(username='admin_doctor', password='testpass123')
        
        response = self.client.get(f'/api/phc/compounder/doctors/{self.cardiologist.id}/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['id'], self.cardiologist.id)
        self.assertEqual(data['doctor_name'], 'Dr. Sharma')
        self.assertEqual(data['specialization'], 'Cardiology')


class PrescriptionFormDataTestCase(TestCase):
    """Test the complete data flow for prescription form"""
    
    def setUp(self):
        """Create realistic test data"""
        self.admin_user = User.objects.create_user(
            username='compounder',
            password='testpass123'
        )
        self.admin_extrainfo = ExtraInfo.objects.create(
            user=self.admin_user,
            role='ADMIN',
            id_number='COM001'
        )
        
        # Create multiple doctors with different specializations
        self.doctors = []
        specializations = ['Cardiology', 'Orthopaedics', 'General Medicine', 'Pediatrics']
        for i, spec in enumerate(specializations):
            doctor = Doctor.objects.create(
                doctor_name=f'Dr. Doctor{i+1}',
                specialization=spec,
                email=f'doc{i+1}@hospital.com',
                is_active=True
            )
            self.doctors.append(doctor)
        
        # Create patients and consultations
        self.consultations = []
        now = timezone.now()
        
        for i in range(10):
            patient_user = User.objects.create_user(
                username=f'patient{i}',
                password='testpass',
                first_name=f'Patient{i}',
                last_name=f'Test'
            )
            patient = ExtraInfo.objects.create(
                user=patient_user,
                role='STUDENT',
                id_number=f'PAT{i:03d}'
            )
            
            consultation = Consultation.objects.create(
                patient=patient,
                doctor=self.doctors[i % len(self.doctors)],
                chief_complaint=f'Complaint {i+1}',
                consultation_date=now - timedelta(days=i),
                blood_pressure_systolic=120,
                blood_pressure_diastolic=80,
                ambulance_requested='no',
            )
            self.consultations.append(consultation)
        
        self.client = Client()
    
    def test_form_dropdown_data_consistency(self):
        """Test that dropdown data is consistent between calls"""
        self.client.login(username='compounder', password='testpass123')
        
        # Get consultations
        consult_response = self.client.get('/api/phc/compounder/consultations/')
        consult_data = consult_response.json()
        
        # Get doctors
        doctor_response = self.client.get('/api/phc/compounder/doctors/?active_only=true')
        doctor_data = doctor_response.json()
        
        # Validate doctor IDs from consultations exist in doctors list
        doctor_ids = {d['id'] for d in doctor_data}
        for consultation in consult_data:
            if consultation['doctor_id']:
                self.assertIn(consultation['doctor_id'], doctor_ids)
    
    def test_filtered_data_performance(self):
        """Test that filters return reasonable data"""
        self.client.login(username='compounder', password='testpass123')
        
        # Get recent consultations
        response = self.client.get('/api/phc/compounder/consultations/?days=3')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(len(data), 0)
        
        # Get doctors by specialization
        response = self.client.get('/api/phc/compounder/doctors/?specialization=Cardiology&active_only=true')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(len(data), 0)
        
        # Verify correct specialization
        for doctor in data:
            self.assertIn('Cardiology', doctor['specialization'])
