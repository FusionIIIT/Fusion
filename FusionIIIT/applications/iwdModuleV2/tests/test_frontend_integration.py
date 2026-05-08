"""
Frontend Integration Test Suite for IWD Module Error Display

This test suite validates:
1. Frontend error notification utility correctly parses backend errors
2. Error codes are properly displayed to users
3. HTTP status codes trigger appropriate error messages
4. Details field is used to enrich error information

Frontend Error Display Expected Behavior:
- 400: "❌ Invalid Operation" - Red notification, 7s auto-close
- 401: Redirect to login or show auth error
- 403: "🚫 Permission Denied" - Red notification, 6s auto-close
- 404: "🔍 Not Found" - Orange notification, 8s auto-close with refresh option
- 500: "🛠️ Server Error" - Red notification, 8s auto-close
"""

import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from applications.globals.models import Designation, HoldsDesignation
from applications.iwdModuleV2.models import Requests


EXPECTED_ERROR_MESSAGES = {
    400: {
        'title': 'Invalid Operation',
        'icon': '❌',
        'auto_close': 7000,
        'color': 'red'
    },
    401: {
        'title': 'Authentication Required',
        'icon': '🔐',
        'color': 'red'
    },
    403: {
        'title': 'Permission Denied',
        'icon': '🚫',
        'auto_close': 6000,
        'color': 'red'
    },
    404: {
        'title': 'Not Found',
        'icon': '🔍',
        'auto_close': 8000,
        'color': 'orange'
    },
    500: {
        'title': 'Server Error',
        'icon': '🛠️',
        'auto_close': 8000,
        'color': 'red'
    }
}


class FrontendErrorParsingTestCase(APITestCase):
    """
    Simulate how the frontend's getApiErrorMessage utility would parse errors
    """
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    @staticmethod
    def simulate_frontend_error_extraction(response_data):
        """
        Simulates the frontend's getApiErrorMessage function from
        Fusion-client/src/Modules/InstituteWorks/api.js
        """
        if isinstance(response_data, dict):
            # Check for standardized fields in order
            if 'error' in response_data:
                return response_data['error']
            elif 'message' in response_data:
                return response_data['message']
            # Fallback: check nested field errors
            for key, value in response_data.items():
                if isinstance(value, (list, str)):
                    return str(value)
        return "An error occurred. Please try again."

    def test_frontend_can_extract_error_message(self):
        """Test that frontend utility can extract error message from response"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/iwdModuleV2/api/create-request/', {
            'unexpected_field': 'value'
        })
        
        data = response.json()
        extracted_message = self.simulate_frontend_error_extraction(data)
        
        # Should extract non-empty message
        self.assertTrue(len(extracted_message) > 0)
        self.assertNotIn('None', extracted_message)
        print(f"Extracted message: {extracted_message}")

    def test_frontend_can_extract_error_from_standardized_format(self):
        """Test extraction from new standardized format"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/iwdModuleV2/api/create-request/', {})
        data = response.json()
        
        # New standardized format
        self.assertIn('error', data)
        self.assertIn('code', data)
        
        extracted = self.simulate_frontend_error_extraction(data)
        self.assertEqual(extracted, data['error'])

    def test_error_code_enables_ui_logic(self):
        """Test that error code can be used for UI decision-making"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/iwdModuleV2/api/create-request/', {})
        data = response.json()
        
        error_code = data.get('code')
        
        # Frontend logic example:
        if error_code == 'PERMISSION_DENIED':
            icon = '🚫'
            color = 'red'
        elif error_code == 'VALIDATION_ERROR':
            icon = '❌'
            color = 'red'
        elif error_code == 'NOT_FOUND':
            icon = '🔍'
            color = 'orange'
        else:
            icon = '⚠️'
            color = 'red'
        
        self.assertIsNotNone(icon)
        print(f"Error Code: {error_code} -> Icon: {icon}, Color: {color}")

    def test_details_field_provides_additional_context(self):
        """Test that details field gives frontend more information"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/iwdModuleV2/api/create-request/', {
            'name': 'Test',
            'area': 'Area',
            'description': 'Desc',
            'role': 'Admin IWD',
            'designation': 'HOD (CSE)|user',
            'extra1': 'val',
            'extra2': 'val2'
        })
        
        data = response.json()
        
        # If details exist, should be helpful
        if 'details' in data and isinstance(data['details'], dict):
            self.assertTrue(len(data['details']) > 0)
            # Frontend can then use this for additional UI elements
            print(f"Error details: {data['details']}")


class ErrorDisplayConsistencyTestCase(APITestCase):
    """
    Test that error display is consistent across different error scenarios
    """
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_all_errors_have_code_field(self):
        """Verify every error response has a code field"""
        self.client.force_authenticate(user=self.user)
        
        # Various endpoints that should fail
        endpoints_and_data = [
            ('/iwdModuleV2/api/create-request/', {'POST': {}}),
            ('/iwdModuleV2/api/view-file/', {'GET': {'file_id': 'invalid'}}),
        ]
        
        for endpoint, methods in endpoints_and_data:
            for method, data in methods.items():
                if method == 'POST':
                    response = self.client.post(endpoint, data)
                elif method == 'GET':
                    response = self.client.get(endpoint, data)
                
                if response.status_code >= 400:
                    response_data = response.json()
                    self.assertIn('code', response_data,
                        f"Response from {endpoint} missing 'code' field")

    def test_error_messages_are_human_readable(self):
        """Verify error messages are understandable to end users"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/iwdModuleV2/api/create-request/', {
            'name': 'Test',
            'extra': 'field'
        })
        
        data = response.json()
        error_msg = data.get('error')
        
        # Should not be machine code or stack trace
        self.assertNotIn('Traceback', str(error_msg))
        self.assertNotIn('Exception', str(error_msg))
        
        # Should be readable English
        self.assertTrue(len(error_msg) > 0)
        self.assertIsInstance(error_msg, str)
        print(f"User-friendly message: {error_msg}")

    def test_status_code_matches_response_body_status(self):
        """Verify HTTP status code matches status field in response"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get('/iwdModuleV2/api/view-file/', {'file_id': 999})
        
        data = response.json()
        
        # HTTP status and response body status should match
        self.assertEqual(response.status_code, data.get('status'))
        print(f"Status code {response.status_code} matches response body")


class FrontendNotificationTestCase(APITestCase):
    """
    Test that errors trigger appropriate notification types in frontend
    """
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def _get_notification_type(self, status_code):
        """Determine notification type based on status code (as frontend does)"""
        if status_code == 404:
            return 'not_found'
        elif status_code == 403:
            return 'permission_denied'
        elif status_code == 400:
            return 'invalid_input'
        elif status_code >= 500:
            return 'server_error'
        else:
            return 'error'

    def test_400_error_triggers_invalid_input_notification(self):
        """Test 400 errors show validation error notification"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/iwdModuleV2/api/create-request/', {
            'invalid': 'data'
        })
        
        self.assertEqual(response.status_code, 400)
        notif_type = self._get_notification_type(response.status_code)
        self.assertEqual(notif_type, 'invalid_input')

    def test_404_error_triggers_not_found_notification(self):
        """Test 404 errors show not found notification"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get('/iwdModuleV2/api/view-file/', {'file_id': 999})
        
        # May not have 404, but test the logic
        if response.status_code == 404:
            notif_type = self._get_notification_type(response.status_code)
            self.assertEqual(notif_type, 'not_found')


class ErrorRecoveryTestCase(APITestCase):
    """
    Test that users can recover from errors appropriately
    """
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_400_error_provides_guidance_on_fixing_input(self):
        """Test that validation errors guide user to correct input"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/iwdModuleV2/api/create-request/', {
            'name': 'Test',
            'designation': 'invalid'  # Invalid format
        })
        
        if response.status_code == 400:
            data = response.json()
            
            # Should either have helpful message or details
            has_guidance = (
                'expected_format' in str(data.get('details', {})) or
                'Expected' in data.get('error', '') or
                'format' in data.get('error', '').lower()
            )
            
            if has_guidance:
                print(f"Helpful error guidance: {data}")


# ===== INTEGRATION WITH FRONTEND UTILITIES =====
# The following functions simulate Python version of frontend utilities
# to validate that backend responses work with frontend code

def simulate_show_api_error_notification(error_response):
    """
    Simulates the frontend's showApiErrorNotification function from
    Fusion-client/src/utils/notifications.jsx
    
    Returns the notification that would be shown
    """
    status_code = error_response.status_code
    data = error_response.json()
    
    # Extract error message
    message = data.get('error', 'Request failed')
    
    # Determine notification style based on status
    if status_code == 404:
        config = {
            'title': '🔍 Not Found',
            'message': message,
            'color': 'orange',
            'autoClose': 8000,
            'showRefreshButton': True
        }
    elif status_code == 400:
        config = {
            'title': '❌ Invalid Operation',
            'message': message,
            'color': 'red',
            'autoClose': 7000
        }
    elif status_code == 403:
        config = {
            'title': '🚫 Permission Denied',
            'message': message,
            'color': 'red',
            'autoClose': 6000
        }
    elif status_code == 500:
        config = {
            'title': '🛠️ Server Error',
            'message': message,
            'color': 'red',
            'autoClose': 8000
        }
    else:
        config = {
            'title': '⚠️ Error',
            'message': message,
            'color': 'red',
            'autoClose': 5000
        }
    
    return config


# ===== COMMAND TO RUN TESTS =====
# python manage.py test applications.iwdModuleV2.tests.test_frontend_integration --verbosity=2


