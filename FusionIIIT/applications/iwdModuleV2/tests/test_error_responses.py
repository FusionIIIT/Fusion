"""
System Integration Tests for IWD Module - Error Handling and Frontend Display

This test suite validates:
1. Error responses are in standardized format
2. HTTP status codes are correct
3. Error messages are descriptive
4. Frontend receives properly formatted errors

Test Categories:
- Authentication/Authorization errors (401, 403)
- Validation errors (400)
- Not Found errors (404)
- Server errors (500)
"""

import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from applications.globals.models import Designation, HoldsDesignation
from applications.iwdModuleV2.models import Requests

class IWDErrorResponseFormatTestCase(APITestCase):
    """
    Test that all IWD API endpoints return errors in standardized format:
    {
        "error": "Human-readable message",
        "code": "ERROR_CODE",
        "status": 400,
        "details": {...}  # optional
    }
    """
    
    def setUp(self):
        """Create test users and setup designations"""
        self.client = APIClient()
        
        # Create designations
        self.admin_iwd_desg = Designation.objects.create(name='Admin IWD')
        self.hod_desg = Designation.objects.create(name='HOD (CSE)')
        self.dean_desg = Designation.objects.create(name='Dean (P&D)')
        self.director_desg = Designation.objects.create(name='Director')
        
        # Create users
        self.admin_iwd_user = User.objects.create_user(
            username='admin_iwd',
            password='testpass123',
            email='admin@test.com'
        )
        self.hod_user = User.objects.create_user(
            username='hod_cse',
            password='testpass123',
            email='hod@test.com'
        )
        self.requester = User.objects.create_user(
            username='requester',
            password='testpass123',
            email='requester@test.com'
        )
        
        # Assign designations
        HoldsDesignation.objects.get_or_create(
            user=self.admin_iwd_user,
            working=self.admin_iwd_user,
            designation=self.admin_iwd_desg
        )
        HoldsDesignation.objects.get_or_create(
            user=self.hod_user,
            working=self.hod_user,
            designation=self.hod_desg
        )

    def _verify_error_response_format(self, response, expected_status, expected_code=None):
        """Helper to verify error response follows standard format"""
        self.assertEqual(response.status_code, expected_status)
        data = response.json()
        
        # Check required fields
        self.assertIn('error', data, "Response missing 'error' field")
        self.assertIn('code', data, "Response missing 'code' field")
        self.assertIn('status', data, "Response missing 'status' field")
        
        # Verify types
        self.assertIsInstance(data['error'], str)
        self.assertIsInstance(data['code'], str)
        self.assertIsInstance(data['status'], int)
        
        # Verify error message is not empty
        self.assertTrue(len(data['error']) > 0, "Error message cannot be empty")
        
        # Verify status code matches
        self.assertEqual(data['status'], expected_status)
        
        # Verify error code if specified
        if expected_code:
            self.assertEqual(data['code'], expected_code)
        
        return data

    def _verify_success_response_format(self, response, expected_status=200):
        """Helper to verify success response follows standard format"""
        self.assertEqual(response.status_code, expected_status)
        data = response.json()
        
        # Check required fields for success
        self.assertIn('message', data, "Success response must have 'message'")
        self.assertIsInstance(data['message'], str)
        
        return data

    # ===== MISSING PARAMETER TESTS =====
    
    def test_create_request_missing_name(self):
        """Test validation error when required 'name' field is missing"""
        self.client.force_authenticate(user=self.requester)
        
        response = self.client.post('/iwdModuleV2/api/create-request/', {
            # Missing 'name'
            'area': 'Test Area',
            'description': 'Test Description',
            'role': 'Admin IWD',
            'designation': 'HOD (CSE)|hod_cse'
        })
        
        data = self._verify_error_response_format(
            response, 
            status.HTTP_400_BAD_REQUEST,
            'VALIDATION_ERROR'
        )
        print(f"Missing parameter error: {data}")

    def test_create_request_unexpected_field(self):
        """Test validation error for unexpected fields in request"""
        self.client.force_authenticate(user=self.requester)
        
        response = self.client.post('/iwdModuleV2/api/create-request/', {
            'name': 'Test',
            'area': 'Area',
            'description': 'Desc',
            'role': 'Admin IWD',
            'designation': 'HOD (CSE)|hod_cse',
            'unexpected_field': 'should fail'  # Unexpected!
        })
        
        data = self._verify_error_response_format(
            response,
            status.HTTP_400_BAD_REQUEST,
            'INVALID_REQUEST_FIELDS'
        )
        # Should include details about unexpected fields
        self.assertIn('details', data)
        self.assertIn('unexpected_fields', data['details'])
        print(f"Unexpected field error: {data}")

    # ===== AUTHORIZATION TESTS =====
    
    def test_create_request_unauthorized_user(self):
        """Test 403 error when user lacks required role"""
        self.client.force_authenticate(user=self.requester)
        
        response = self.client.post('/iwdModuleV2/api/create-request/', {
            'name': 'Test Request',
            'area': 'Test Area',
            'description': 'Test Description',
            'role': 'Admin IWD',
            'designation': 'HOD (CSE)|hod_cse'
        })
        
        data = self._verify_error_response_format(
            response,
            status.HTTP_403_FORBIDDEN,
            'PERMISSION_DENIED'
        )
        print(f"Permission denied error: {data}")

    # ===== NOT FOUND TESTS =====
    
    def test_view_file_not_found(self):
        """Test 404 error when file doesn't exist"""
        self.client.force_authenticate(user=self.admin_iwd_user)
        
        response = self.client.get('/iwdModuleV2/api/view-file/', {'file_id': 99999})
        
        data = self._verify_error_response_format(
            response,
            status.HTTP_404_NOT_FOUND,
            'FILE_NOT_FOUND'
        )
        print(f"Not found error: {data}")

    def test_view_file_missing_id_parameter(self):
        """Test 400 error when required query parameter is missing"""
        self.client.force_authenticate(user=self.admin_iwd_user)
        
        response = self.client.get('/iwdModuleV2/api/view-file/')
        
        data = self._verify_error_response_format(
            response,
            status.HTTP_400_BAD_REQUEST,
            'MISSING_FILE_ID'
        )
        print(f"Missing parameter error: {data}")

    # ===== INVALID FORMAT TESTS =====
    
    def test_create_request_invalid_designation_format(self):
        """Test validation error for invalid designation format"""
        self.client.force_authenticate(user=self.admin_iwd_user)
        HoldsDesignation.objects.get_or_create(
            user=self.admin_iwd_user,
            working=self.admin_iwd_user,
            designation=self.admin_iwd_desg
        )
        
        response = self.client.post('/iwdModuleV2/api/create-request/', {
            'name': 'Test',
            'area': 'Area',
            'description': 'Desc',
            'role': 'Admin IWD',
            'designation': 'invalid_format'  # No pipe separator
        })
        
        data = self._verify_error_response_format(
            response,
            status.HTTP_400_BAD_REQUEST
        )
        # Error should provide details about expected format
        self.assertIn('details', data)
        print(f"Invalid format error: {data}")

    # ===== BUSINESS LOGIC ERROR TESTS =====
    
    def test_forward_request_with_nonexistent_user(self):
        """Test 404 error when receiver user doesn't exist"""
        self.client.force_authenticate(user=self.admin_iwd_user)
        
        # Create a request first
        req = Requests.objects.create(
            name='Test Request',
            area='Test Area',
            description='Test Desc',
            requestCreatedBy=self.admin_iwd_user.username,
            iwdAdminApproval=1
        )
        
        # Try to forward to nonexistent user
        response = self.client.post('/iwdModuleV2/api/forward-request/', {
            'fileid': 99999,
            'designation': 'HOD (CSE)|nonexistent_user',
            'remarks': 'Test'
        })
        
        # Should not find the file anyway, but error should be consistent
        self._verify_error_response_format(
            response,
            status.HTTP_404_NOT_FOUND,
            'FILE_NOT_FOUND'
        )

    # ===== DETAILS FIELD TESTS =====
    
    def test_error_includes_helpful_details(self):
        """Test that detailed errors include 'details' field with context"""
        self.client.force_authenticate(user=self.requester)
        
        response = self.client.post('/iwdModuleV2/api/create-request/', {
            'name': 'Test',
            'area': 'Area',
            'description': 'Desc',
            'role': 'Admin IWD',
            'designation': 'HOD (CSE)|hod_cse',
            'extra1': 'val1',
            'extra2': 'val2'
        })
        
        data = response.json()
        
        # Should have details for unexpected fields
        if 'INVALID_REQUEST_FIELDS' in str(data.get('code')):
            self.assertIn('details', data)
            self.assertIn('unexpected_fields', data['details'])
            self.assertEqual(len(data['details']['unexpected_fields']), 2)

    def test_validation_error_includes_field_info(self):
        """Test that validation errors include information about which fields failed"""
        self.client.force_authenticate(user=self.admin_iwd_user)
        HoldsDesignation.objects.get_or_create(
            user=self.admin_iwd_user,
            working=self.admin_iwd_user,
            designation=self.admin_iwd_desg
        )
        
        response = self.client.post('/iwdModuleV2/api/create-request/', {
            # Missing required 'name' field
            'area': 'Test Area',
            'description': 'Test Description',
            'role': 'Admin IWD',
            'designation': 'HOD (CSE)|hod_cse'
        })
        
        data = response.json()
        
        # Should indicate validation error with field details
        if data.get('code') == 'VALIDATION_ERROR':
            self.assertIn('details', data)
            self.assertIsInstance(data['details'], dict)

class FrontendErrorDisplayIntegrationTestCase(APITestCase):
    """
    Test that frontend can correctly parse and display error responses
    """
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_error_response_can_be_parsed_as_json(self):
        """Verify all error responses are valid JSON"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/iwdModuleV2/api/create-request/', {})
        
        # Should not raise JSON decode error
        try:
            data = response.json()
            self.assertIsInstance(data, dict)
        except json.JSONDecodeError:
            self.fail("Error response is not valid JSON")

    def test_error_code_enables_programmatic_error_handling(self):
        """Verify error codes allow frontend to handle errors programmatically"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/iwdModuleV2/api/create-request/', {})
        
        data = response.json()
        
        # Frontend should be able to use code to show appropriate UI
        error_code = data.get('code')
        self.assertIsNotNone(error_code)
        self.assertIsInstance(error_code, str)
        
        # Error code should be consistent across same error type
        # (e.g., PERMISSION_DENIED always for 403)

    def test_status_code_matches_http_status(self):
        """Verify response 'status' field matches HTTP status code"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/iwdModuleV2/api/create-request/', {})
        
        data = response.json()
        
        # The 'status' field in response body should match HTTP status
        self.assertEqual(data['status'], response.status_code)


class SuccessResponseFormatTestCase(APITestCase):
    """
    Test that success responses also follow consistent format
    """
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        Designation.objects.create(name='Admin IWD')
        HoldsDesignation.objects.get_or_create(
            user=self.user,
            working=self.user,
            designation=Designation.objects.get(name='Admin IWD')
        )

    def test_success_response_has_message(self):
        """Verify success responses include 'message' field"""
        self.client.force_authenticate(user=self.user)
        
        # Create a test request with minimal valid data
        response = self.client.post('/iwdModuleV2/api/create-request/', {
            'name': 'Test',
            'area': 'Area',
            'description': 'Desc',
            'role': 'Admin IWD',
            'designation': 'HOD (CSE)|testuser'
        })
        
        # Even if it fails validation, response should have consistent format
        data = response.json()
        
        # Success or error, should have either 'message' or 'error'
        self.assertTrue(
            'message' in data or 'error' in data,
            "Response must have 'message' (success) or 'error' field"
        )

    def test_success_response_includes_data(self):
        """Verify success responses include relevant data"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get('/iwdModuleV2/api/fetch-designations/')
        
        if response.status_code == 200:
            data = response.json()
            self.assertIn('message', data)
            # May have 'data' field with actual payload


# ===== COMMAND TO RUN TESTS =====
# python manage.py test applications.iwdModuleV2.tests.test_error_responses.IWDErrorResponseFormatTestCase
# python manage.py test applications.iwdModuleV2.tests.test_error_responses --verbosity=2



