#test_services.py
from django.test import TestCase
from django.contrib.auth.models import User
from applications.academic_information.models import Student
from applications.globals.models import ExtraInfo, Faculty
from ..models import Club_info
from ..services import ClubService


class ClubServiceTestCase(TestCase):
    """Test cases for ClubService"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create test extra info
        self.extra_info = ExtraInfo.objects.create(
            id='2020001',
            user=self.user,
            user_type='student'
        )
        
        # Create test student
        self.student = Student.objects.create(
            id=self.extra_info,
            cpi=8.5,
            programme='B.Tech'
        )
    
    def test_validate_student_exists(self):
        """Test that existing student is validated correctly"""
        result = ClubService._validate_student('2020001')
        self.assertIsNotNone(result)
        self.assertEqual(result.id, self.student.id)
    
    def test_validate_student_not_exists(self):
        """Test that non-existing student returns None"""
        result = ClubService._validate_student('9999999')
        self.assertIsNone(result)
    
    # Add more tests as needed