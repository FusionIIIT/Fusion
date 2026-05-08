# IWD Module - Standardized Error Response Format

## Overview
All IWD module API endpoints now return errors in a consistent, easily-parsable format that enables robust frontend error handling and user-friendly displays.

## Error Response Format

### Standard Error Response
```json
{
    "error": "Human-readable error message describing what went wrong",
    "code": "ERROR_CODE",
    "status": 400,
    "details": {
        "additional": "context",
        "field_name": "error_details"
    }
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `error` | string | ✅ | Human-readable error message for display to users |
| `code` | string | ✅ | Machine-readable error code for programmatic handling |
| `status` | integer | ✅ | HTTP status code (mirrors HTTP response status) |
| `details` | object | ❌ | Additional error context (field errors, suggestions, etc.) |

## HTTP Status Codes & Error Codes

### 400 Bad Request
Used for validation errors, invalid input, and malformed requests

| Error Code | Description | Example |
|------------|-------------|---------|
| `VALIDATION_ERROR` | Request data fails validation | Missing required fields |
| `INVALID_REQUEST_FIELDS` | Unexpected fields in request | Extra/unknown parameters |
| `INVALID_DESIGNATION_FORMAT` | Designation format invalid | "user" instead of "ROLE\|username" |
| `MISSING_RECEIVER_INFO` | Receiver info incomplete | Missing username or role |
| `NOT_APPROVED` | Precondition not met | Can't forward before IWD Admin approval |

### 401 Unauthorized
User not authenticated

| Error Code | Description |
|------------|-------------|
| `AUTHENTICATION_FAILED` | User session invalid or expired |

### 403 Forbidden
User lacks required permissions

| Error Code | Description |
|------------|-------------|
| `PERMISSION_DENIED` | User doesn't have required role |
| `DESIGNATION_NOT_HELD` | User doesn't hold required designation |

### 404 Not Found
Resource not found

| Error Code | Description |
|------------|-------------|
| `FILE_NOT_FOUND` | File ID doesn't exist |
| `USER_NOT_FOUND` | User doesn't exist |
| `REQUEST_NOT_FOUND` | Request ID doesn't exist |

### 500 Internal Server Error
Unexpected server-side error

| Error Code | Description |
|------------|-------------|
| `INTERNAL_SERVER_ERROR` | Unexpected exception occurred |
| `SERVICE_ERROR` | Business logic service error |

## Success Response Format

```json
{
    "message": "Operation completed successfully",
    "data": {
        "request_id": 123,
        "status": "pending"
    }
}
```

## Examples

### Example 1: Invalid Designation Format
**Request:**
```json
POST /api/iwd/create_request/
{
    "name": "Repair Building",
    "area": "Academic Cell",
    "description": "Repair roof",
    "designation": "invalid_format"
}
```

**Response: 400**
```json
{
    "error": "Receiver designation format is invalid",
    "code": "INVALID_DESIGNATION_FORMAT",
    "status": 400,
    "details": {
        "expected_format": "<designation>|<username>"
    }
}
```

### Example 2: Permission Denied
**Request:**
```json
POST /api/iwd/approve_as_hod/
```

**Response: 403**
```json
{
    "error": "Current user is not allowed to create IWD requests",
    "code": "PERMISSION_DENIED",
    "status": 403,
    "details": {
        "available_designations": ["Student", "Faculty"],
        "allowed_sender_designations": [],
        "requested_role": "Admin IWD"
    }
}
```

### Example 3: Validation Error with Field Details
**Request:**
```json
POST /api/iwd/create_request/
{
    "area": "Academic",
    "description": "Repair",
    "name": "Test Request",
    "role": "Admin IWD",
    "designation": "HOD|invalid_user"
}
```

**Response: 400**
```json
{
    "error": "Validation error: This field is required",
    "code": "VALIDATION_ERROR",
    "status": 400,
    "details": {
        "estimated_budget": "This field is required",
        "area": "Ensure this field has at most 100 characters"
    }
}
```

## Frontend Integration

### JavaScript Error Handler Example
```javascript
// Fusion-client/src/Modules/InstituteWorks/api.js

export const handleApiError = (error) => {
  if (!axios.isAxiosError(error)) return "Request failed.";
  
  const { status, data } = error.response;
  
  // Use standardized format
  const errorMessage = data.error || data.message || "Request failed";
  const errorCode = data.code || "UNKNOWN_ERROR";
  const errorDetails = data.details || {};
  
  // Programmatic error handling based on code
  switch (errorCode) {
    case 'PERMISSION_DENIED':
      // Show red notification with permission icon
      showApiErrorNotification(error, "Access Denied");
      break;
    case 'VALIDATION_ERROR':
      // Show validation errors with field details
      showValidationErrors(errorDetails);
      break;
    case 'NOT_FOUND':
      // Show not found notification with refresh option
      showErrorNotification("Item not found", errorMessage);
      break;
    default:
      showErrorNotification("Error", errorMessage);
  }
};
```

### React Component Example
```jsx
import { notifications } from '@mantine/notifications';

const handleRequestError = (error) => {
  const { data, status } = error.response;
  
  notifications.show({
    title: getErrorTitle(data.code),
    message: data.error,
    color: getErrorColor(status),
    autoClose: getAutoCloseTime(status),
    icon: getErrorIcon(data.code)
  });
};
```

## Error Code Mapping for UI

```javascript
const ERROR_CODE_CONFIG = {
  'PERMISSION_DENIED': {
    icon: '🚫',
    color: 'red',
    autoClose: 6000,
    title: 'Access Denied'
  },
  'VALIDATION_ERROR': {
    icon: '❌',
    color: 'red', 
    autoClose: 7000,
    title: 'Invalid Input'
  },
  'NOT_FOUND': {
    icon: '🔍',
    color: 'orange',
    autoClose: 8000,
    title: 'Not Found'
  },
  'INVALID_DESIGNATION_FORMAT': {
    icon: '⚠️',
    color: 'red',
    autoClose: 7000,
    title: 'Invalid Format'
  }
};
```

## Migration Guide

### Old Format (DO NOT USE)
```json
// Bad: Inconsistent format
{"error": "message"}
{"message": "text"}
{"field_name": ["error1", "error2"]}  // Serializer errors
```

### New Format (USE THIS)
```json
// Good: Always standardized
{
  "error": "message",
  "code": "ERROR_CODE",
  "status": 400,
  "details": {}
}
```

## Backend Implementation

### Using Error Utilities

```python
from helpers.error_response import error_response, success_response, APIPermissionError

# Option 1: Direct response
@api_view(['POST'])
def my_endpoint(request):
    if not user_has_permission:
        return error_response(
            message='You do not have permission',
            code='PERMISSION_DENIED',
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    return success_response(message='Success')

# Option 2: Using decorator and exceptions
from helpers.error_response import handle_api_errors, APINotFoundError

@api_view(['GET'])
@handle_api_errors
def my_endpoint(request):
    obj = get_object_or_404(MyModel, id=request.query_params.get('id'))
    # If not found, decorator catches and returns standardized 404
    
    if not user_permission:
        raise APIPermissionError('You cannot access this')
    
    return success_response(data={'obj': obj})
```

### Serializer Error Handling

```python
from helpers.error_response import serialize_serializer_errors

@api_view(['POST'])
def create_object(request):
    serializer = MySerializer(data=request.data)
    if serializer.is_valid():
        obj = serializer.save()
        return success_response(message='Created', data={'id': obj.id})
    
    # Convert serializer errors to friendly format
    error_msg, field_errors = serialize_serializer_errors(serializer)
    return error_response(
        message=error_msg,
        code='VALIDATION_ERROR',
        status_code=status.HTTP_400_BAD_REQUEST,
        details=field_errors
    )
```

## Testing

### System Tests
```bash
python manage.py test applications.iwdModuleV2.tests.test_error_responses --verbosity=2
```

### Frontend Integration Tests
```bash
python manage.py test applications.iwdModuleV2.tests.test_frontend_integration --verbosity=2
```

### Manual Testing Checklist

- [ ] All error responses have `error`, `code`, and `status` fields
- [ ] Status field matches HTTP response status code
- [ ] Error messages are user-friendly (not stack traces)
- [ ] Error codes are consistent across same error types
- [ ] Details field provides helpful context
- [ ] Frontend successfully parses and displays errors
- [ ] Proper icons/colors shown based on error type
- [ ] Auto-close times vary appropriately by error severity

## Key Takeaways

✅ **Always** return standardized format with error, code, and status  
✅ **Always** use appropriate HTTP status codes  
✅ **Always** provide human-readable error messages  
✅ **Always** include error code for programmatic handling  
✅ **Check** that frontend can parse response with existing utilities  

❌ **Never** return raw code names or stack traces  
❌ **Never** use inconsistent error formats  
❌ **Never** omit HTTP status codes  
❌ **Never** return technical jargon without explanation
