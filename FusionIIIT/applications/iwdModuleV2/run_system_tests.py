#!/usr/bin/env python
"""
System Testing Script for IWD Module Error Handling

This script runs comprehensive tests to validate:
1. Backend error responses are standardized
2. Frontend can parse and display errors correctly
3. All endpoints handle errors properly
4. HTTP status codes are appropriate

Usage:
    python setup_tests.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Fusion.settings.development')
sys.path.insert(0, os.path.dirname(__file__))

django.setup()

from django.core.management import call_command
from django.test.utils import get_runner
from django.conf import settings

def run_error_response_tests():
    """Run error response format validation tests"""
    print("=" * 70)
    print("RUNNING ERROR RESPONSE FORMAT TESTS")
    print("=" * 70)
    
    call_command(
        'test',
        'applications.iwdModuleV2.tests.test_error_responses',
        verbosity=2,
        failfast=False
    )

def run_frontend_integration_tests():
    """Run frontend error parsing and display tests"""
    print("\n" + "=" * 70)
    print("RUNNING FRONTEND INTEGRATION TESTS")
    print("=" * 70)
    
    call_command(
        'test',
        'applications.iwdModuleV2.tests.test_frontend_integration',
        verbosity=2,
        failfast=False
    )

def run_all_tests():
    """Run all IWD module tests"""
    print("\n" + "=" * 70)
    print("RUNNING ALL IWD MODULE TESTS")
    print("=" * 70)
    
    call_command(
        'test',
        'applications.iwdModuleV2',
        verbosity=2,
        failfast=False
    )

def print_test_guide():
    """Print testing guide"""
    guide = """
╔════════════════════════════════════════════════════════════════════════╗
║                   IWD MODULE SYSTEM TESTING GUIDE                      ║
╚════════════════════════════════════════════════════════════════════════╝

ERROR HANDLING VALIDATION - CHECKLIST
=====================================

Backend Error Responses:
  ✓ All errors have 'error', 'code', and 'status' fields
  ✓ HTTP status codes match response body 'status' field
  ✓ Error messages are human-readable (no stack traces)
  ✓ Error codes are machine-readable and consistent
  ✓ Details field provides helpful context
  ✓ Success responses have 'message' field
  ✓ Validation errors include field details

Error Code Coverage:
  ✓ VALIDATION_ERROR (400) - Missing/invalid fields
  ✓ INVALID_REQUEST_FIELDS (400) - Extra/unexpected fields
  ✓ INVALID_DESIGNATION_FORMAT (400) - Wrong format
  ✓ PERMISSION_DENIED (403) - User lacks role
  ✓ DESIGNATION_NOT_HELD (400) - User doesn't have designation
  ✓ FILE_NOT_FOUND (404) - File doesn't exist
  ✓ USER_NOT_FOUND (404) - User doesn't exist
  ✓ NOT_APPROVED (400) - Prerequisites not met

Frontend Error Display:
  ✓ Properly parses error responses
  ✓ Extracts error message for display
  ✓ Uses error code for UI logic
  ✓ Shows appropriate icons/colors based on status
  ✓ Implements correct auto-close times
  ✓ Handles details field for additional info

RUNNING TESTS
=============

1. Error Response Format Tests:
   ```
   python manage.py test applications.iwdModuleV2.tests.test_error_responses -v2
   ```

2. Frontend Integration Tests:
   ```
   python manage.py test applications.iwdModuleV2.tests.test_frontend_integration -v2
   ```

3. All IWD Tests:
   ```
   python manage.py test applications.iwdModuleV2 -v2
   ```

4. Specific Test Class:
   ```
   python manage.py test applications.iwdModuleV2.tests.test_error_responses.IWDErrorResponseFormatTestCase -v2
   ```

5. Specific Test Method:
   ```
   python manage.py test applications.iwdModuleV2.tests.test_error_responses.IWDErrorResponseFormatTestCase.test_create_request_missing_name -v2
   ```

MANUAL SYSTEM TESTING
====================

1. Start Backend:
   ```
   .\env\Scripts\python.exe manage.py runserver 8000
   ```

2. Start Frontend:
   ```
   cd Fusion-client
   npm run dev
   ```

3. Test Error Scenarios:
   a) Missing required field
      - Submit request without 'name'
      - Should see: "Validation error: This field is required"
      - Icon: ❌ (red notification)

   b) Invalid designation format
      - Use designation value: "invalid_format"
      - Should see: "Receiver designation format is invalid"
      - Icon: ⚠️ (red notification)

   c) User without permission
      - Login as non-admin user
      - Try to approve request
      - Should see: "Permission Denied" with 🚫 icon

   d) User not found
      - Use designation: "ROLE|nonexistent_user"
      - Should see: "Receiver user does not exist"
      - Icon: 🔍 (orange notification)

TROUBLESHOOTING
===============

Q: Tests failing with import errors?
A: Ensure all dependencies are installed:
   pip install -r requirements.txt

Q: Database errors during tests?
A: Django creates a test database automatically
   If issues persist, try:
   python manage.py migrate --run-syncdb

Q: Frontend not showing proper errors?
A: Check browser console (F12) for:
   - Network tab: Verify response has error, code, status
   - Console tab: Check if error handler is catching exceptions

Q: Unsure if error format is standard?
A: Compare responses to examples in ERROR_HANDLING.md
   All must have: error, code, status (and optionally details)

VALIDATION CHECKLIST
====================

Before marking system testing complete:

Backend:
  [ ] Run all error response tests - all passing
  [ ] Verify error codes match documentation
  [ ] Check error messages are user-friendly
  [ ] Confirm status codes are HTTP-correct
  [ ] Details field works when present

Frontend:
  [ ] Test missing required field error display
  [ ] Test invalid format error display
  [ ] Test permission denied (403) display
  [ ] Test not found (404) display
  [ ] Test server error (500) display
  [ ] Verify icons appear correctly
  [ ] Verify notification colors are correct
  [ ] Verify auto-close timing works

Integration:
  [ ] Create request - error handling works
  [ ] Approve request - error handling works
  [ ] Forward request - error handling works
  [ ] File operations - error handling works

USEFUL COMMANDS
===============

# Run tests with coverage
python manage.py test applications.iwdModuleV2 --cov

# Run specific test with verbose output
python manage.py test applications.iwdModuleV2.tests.test_error_responses.IWDErrorResponseFormatTestCase -v3

# Debug specific endpoint
python -c "
from django.test import Client
c = Client()
response = c.post('/api/iwd/create_request/', {})
print(response.json())
"
"""
    print(guide)

if __name__ == '__main__':
    print_test_guide()
    
    try:
        response = input("\nRun error response tests? (y/n): ")
        if response.lower() == 'y':
            run_error_response_tests()
        
        response = input("\nRun frontend integration tests? (y/n): ")
        if response.lower() == 'y':
            run_frontend_integration_tests()
        
        response = input("\nRun all IWD tests? (y/n): ")
        if response.lower() == 'y':
            run_all_tests()
            
    except KeyboardInterrupt:
        print("\n\nTesting cancelled.")
        sys.exit(0)
