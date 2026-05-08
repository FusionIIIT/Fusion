# Quick Reference: Using Error Response Utilities

## TL;DR - Quick Examples

### ❌ DON'T DO THIS
```python
# Bad: Inconsistent format
return Response({'error': 'Something failed'})
return Response({'message': 'success'}, status=201)
return Response(serializer.errors)  # Raw serializer format
```

### ✅ DO THIS INSTEAD
```python
from helpers.error_response import error_response, success_response, serialize_serializer_errors

# Good: Always standardized
return error_response(
    message='Request validation failed',
    code='VALIDATION_ERROR',
    status_code=status.HTTP_400_BAD_REQUEST,
    details={'field': 'error details'}
)

return success_response(
    message='Request created successfully',
    data={'request_id': 123}
)
```

---

## Common Patterns

### Pattern 1: Validation Error with Serializer
```python
from helpers.error_response import serialize_serializer_errors

@api_view(['POST'])
def create_request(request):
    serializer = MySerializer(data=request.data)
    if not serializer.is_valid():
        error_msg, field_errors = serialize_serializer_errors(serializer)
        return error_response(
            message=error_msg,
            code='VALIDATION_ERROR',
            status_code=status.HTTP_400_BAD_REQUEST,
            details=field_errors
        )
    
    obj = serializer.save()
    return success_response(
        message='Successfully created',
        data={'id': obj.id},
        status_code=status.HTTP_201_CREATED
    )
```

### Pattern 2: Permission Check
```python
from helpers.error_response import error_response, APIPermissionError

@api_view(['POST'])
def approve_request(request):
    if not user_has_role(request.user, 'HOD'):
        return error_response(
            message='You do not have permission to approve requests',
            code='PERMISSION_DENIED',
            status_code=status.HTTP_403_FORBIDDEN,
            details={'required_role': 'HOD'}
        )
    
    # ... approval logic ...
    
    return success_response(message='Request approved')
```

### Pattern 3: Resource Not Found
```python
from helpers.error_response import APINotFoundError

@api_view(['GET'])
@handle_api_errors  # Decorator catches exceptions
def view_file(request):
    file_id = request.query_params.get('file_id')
    if not file_id:
        raise APINotFoundError('File ID is required')
    
    file_obj = get_object_or_404(File, id=file_id)
    
    # If not found, decorator catches ObjectDoesNotExist
    # and returns standardized 404
    
    return success_response(data={'file': FileSerializer(file_obj).data})
```

### Pattern 4: Invalid Input Format
```python
@api_view(['POST'])
def forward_request(request):
    designation= request.data.get('designation', '')
    
    if '|' not in designation:
        return error_response(
            message='Invalid designation format',
            code='INVALID_DESIGNATION_FORMAT',
            status_code=status.HTTP_400_BAD_REQUEST,
            details={'expected_format': '<role>|<username>'}
        )
    
    # ... rest of logic ...
```

---

## Available Error Utilities

### Functions

#### `error_response(message, code, status_code, details=None)`
Returns standardized error response
```python
error_response(
    message='Invalid request',
    code='INVALID_REQUEST',
    status_code=400,
    details={'field': 'value'}
)
```

#### `success_response(message, data=None, status_code=200)`
Returns standardized success response
```python
success_response(
    message='Request created',
    data={'id': 123, 'status': 'pending'},
    status_code=201
)
```

#### `serialize_serializer_errors(serializer)`
Converts Django serializer errors to friendly format
```python
error_msg, fields_dict = serialize_serializer_errors(serializer)
# error_msg = "Validation error: This field is required"
# fields_dict = {'name': 'This field is required', 'email': 'Enter valid email'}
```

### Decorator

#### `@handle_api_errors`
Catches exceptions and converts to standardized responses
```python
@api_view(['POST'])
@handle_api_errors
def my_endpoint(request):
    # Catches ObjectDoesNotExist -> 404
    # Catches DjangoValidationError -> 400
    # Catches ValueError -> 400
    # Catches Exception -> 500
    pass
```

### Custom Exceptions

Only the following custom exceptions are currently provided by
`helpers/error_response.py`.

#### `APIValidationError(message, code='VALIDATION_ERROR', details=None)`
400 error for validation issues
```python
raise APIValidationError('Email is invalid', details={'email': 'Invalid format'})
```

#### `APINotFoundError(message, code='NOT_FOUND', details=None)`
404 error for missing resources
```python
raise APINotFoundError('User not found', details={'user_id': 123})
```

#### `APIPermissionError(message, code='PERMISSION_DENIED', details=None)`
403 error for authorization issues
```python
raise APIPermissionError('Admin access required', details={'required_role': 'Admin'})
```

#### Authentication failures
401 error responses should be returned directly with `error_response(...)`
because `helpers/error_response.py` does not define an
`APIAuthenticationError` exception.
```python
return error_response(
    message='Token expired',
    code='AUTHENTICATION_FAILED',
    status_code=status.HTTP_401_UNAUTHORIZED
)
```

---

## Error Codes Reference

| Code | Status | Meaning | When to Use |
|------|--------|---------|------------|
| `VALIDATION_ERROR` | 400 | Data validation failed | Serializer errors, invalid field values |
| `INVALID_REQUEST_FIELDS` | 400 | Unexpected fields | Extra/unknown parameters in request |
| `INVALID_DESIGNATION_FORMAT` | 400 | Wrong format | Designation not "ROLE\|username" |
| `MISSING_RECEIVER_INFO` | 400 | Incomplete receiver data | Missing username or role |
| `INVALID_INPUT` | 400 | Generic invalid input | File parsing errors, type mismatches |
| `NOT_APPROVED` | 400 | Precondition not met | Can't forward before admin approval |
| `MISSING_FILE_ID` | 400 | Required param missing | file_id query param absent |
| `AUTHENTICATION_FAILED` | 401 | Not authenticated | Session expired, token invalid |
| `PERMISSION_DENIED` | 403 | User lacks role | No required designation |
| `DESIGNATION_NOT_HELD` | 403 | User doesn't have designation | Designation not assigned to user |
| `FILE_NOT_FOUND` | 404 | File doesn't exist | file_id doesn't match any file |
| `USER_NOT_FOUND` | 404 | User doesn't exist | username doesn't exist |
| `REQUEST_NOT_FOUND` | 404 | Request doesn't exist | request_id doesn't exist |
| `NOT_FOUND` | 404 | Generic not found | Generic resource not found |
| `INTERNAL_SERVER_ERROR` | 500 | Unexpected error | Unhandled exception |
| `SERVICE_ERROR` | 500 | Business logic error | Error from service layer |

---

## Import Paths

```python
from helpers.error_response import (
    # Functions
    error_response,
    success_response,
    serialize_serializer_errors,
    
    # Decorator
    handle_api_errors,
    
    # Exceptions
    APIValidationError,
    APINotFoundError,
    APIPermissionError,
)
```

---

## Common Mistakes & Fixes

### Mistake 1: Forgetting error code
```python
# ❌ Bad
return error_response(message='Error occurred')

# ✅ Good
return error_response(
    message='Error occurred',
    code='PROCESS_ERROR'
)
```

### Mistake 2: Using status code without message
```python
# ❌ Bad
return error_response(code='INVALID')

# ✅ Good
return error_response(
    message='Invalid input provided',
    code='INVALID_INPUT'
)
```

### Mistake 3: Leaking sensitive information
```python
# ❌ Bad - Shows internal details to users
return error_response(
    message=f'Database error: {str(exception)}',
    code='DB_ERROR'
)

# ✅ Good - Hides internal details
logger.error(f'DB error: {str(exception)}')
return error_response(
    message='An error occurred processing your request',
    code='INTERNAL_SERVER_ERROR'
)
```

### Mistake 4: Inconsistent status codes
```python
# ❌ Bad - HTTP 200 with error
return Response({'error': 'Failed'}, status=200)

# ✅ Good - Appropriate status
return error_response(
    message='Failed',
    code='PROCESS_FAILED',
    status_code=status.HTTP_400_BAD_REQUEST
)
```

### Mistake 5: Empty details object
```python
# ❌ Bad - Empty details not helpful
return error_response(message='Invalid', details={})

# ✅ Good - Details provides context
return error_response(
    message='Invalid designation format',
    code='INVALID_FORMAT',
    details={'expected_format': '<role>|<username>'}
)
```

---

## Testing Your Error Responses

```python
# In your tests:

def test_missing_field_error(self):
    response = self.client.post('/api/endpoint/', {})
    
    self.assertEqual(response.status_code, 400)
    data = response.json()
    
    # Verify standard format
    self.assertIn('error', data)
    self.assertIn('code', data)
    self.assertEqual(data['status'], 400)
    
    # Check specific error
    self.assertEqual(data['code'], 'VALIDATION_ERROR')
    self.assertIn('required', data['error'].lower())
```

---

## Performance Notes

- Error responses are lightweight (no unnecessary serialization)
- Decorator adds minimal overhead (~1ms)
- Serializer error flattening is efficient for typical request sizes
- Status codes reduce need for frontend custom parsing

---

## Questions?

Refer to:
- Full documentation: `ERROR_HANDLING.md`
- Test examples: `tests/test_error_responses.py`
- Implementation examples: `api/views.py`
- Frontend integration: `tests/test_frontend_integration.py`
