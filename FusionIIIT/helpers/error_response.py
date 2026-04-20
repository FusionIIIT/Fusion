"""
Standardized error response handling for REST APIs.

This module provides utilities for consistent error formatting and handling
across all API endpoints. All API endpoints should use these utilities to
ensure the frontend receives errors in the expected format.

Error Response Format:
{
    "error": "Human-readable error message",
    "code": "ERROR_CODE",  # optional, for programmatic handling
    "details": {},  # optional, additional context
    "status": 400  # HTTP status code
}

Success Response Format:
{
    "message": "Success message",
    "data": {}  # optional payload
}
"""

from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist, ValidationError as DjangoValidationError
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class APIException(Exception):
    """Base exception for API errors, can be caught and converted to response."""
    def __init__(self, message, code=None, status_code=None, details=None):
        self.message = message
        self.code = code or 'ERROR'
        self.status_code = status_code or status.HTTP_400_BAD_REQUEST
        self.details = details or {}
        super().__init__(self.message)


class APIValidationError(APIException):
    """Raised when request data validation fails."""
    def __init__(self, message, code='VALIDATION_ERROR', details=None):
        super().__init__(
            message, 
            code=code, 
            status_code=status.HTTP_400_BAD_REQUEST, 
            details=details
        )


class APINotFoundError(APIException):
    """Raised when a requested resource is not found."""
    def __init__(self, message, code='NOT_FOUND', details=None):
        super().__init__(
            message,
            code=code,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details
        )


class APIPermissionError(APIException):
    """Raised when user lacks required permissions."""
    def __init__(self, message, code='PERMISSION_DENIED', details=None):
        super().__init__(
            message,
            code=code,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details
        )


class APIAuthenticationError(APIException):
    """Raised when authentication fails."""
    def __init__(self, message, code='AUTHENTICATION_FAILED', details=None):
        super().__init__(
            message,
            code=code,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
        )


def error_response(
    message,
    code='ERROR',
    status_code=status.HTTP_400_BAD_REQUEST,
    details=None
):
    """
    Create a standardized error response.
    
    Args:
        message (str): Human-readable error message
        code (str): Machine-readable error code
        status_code (int): HTTP status code
        details (dict): Additional error context
        
    Returns:
        Response: DRF Response object with standardized format
    """
    payload = {
        'error': message,
        'code': code,
        'status': status_code,
    }
    
    if details:
        payload['details'] = details
    
    return Response(payload, status=status_code)


def success_response(
    message='Success',
    data=None,
    status_code=status.HTTP_200_OK
):
    """
    Create a standardized success response.
    
    Args:
        message (str): Success message
        data (dict): Response payload
        status_code (int): HTTP status code
        
    Returns:
        Response: DRF Response object with standardized format
    """
    payload = {
        'message': message,
    }
    
    if data:
        payload['data'] = data
    
    return Response(payload, status=status_code)


def serialize_serializer_errors(serializer):
    """
    Convert Django serializer errors to human-readable format.
    
    Django serializer.errors returns:
    {
        'field_name': ['Error message 1', 'Error message 2'],
        'nested': {
            'subfield': ['Error message']
        }
    }
    
    Convert to:
    {
        'field_name': 'Error message 1',
        'nested.subfield': 'Error message'
    }
    
    Args:
        serializer: DRF serializer with errors
        
    Returns:
        tuple: (error_message, details_dict)
    """
    def flatten_errors(errors, prefix=''):
        """Recursively flatten nested error dict."""
        flat = {}
        for field, field_errors in errors.items():
            full_field = f"{prefix}.{field}" if prefix else field
            
            if isinstance(field_errors, dict):
                flat.update(flatten_errors(field_errors, full_field))
            elif isinstance(field_errors, list):
                # Take first error message for display
                if field_errors:
                    flat[full_field] = field_errors[0]
            else:
                flat[full_field] = str(field_errors)
        
        return flat
    
    flattened = flatten_errors(serializer.errors)
    
    # Create human-readable message
    if flattened:
        first_field = next(iter(flattened.keys()))
        first_error = flattened[first_field]
        message = f"Validation error: {first_error}"
    else:
        message = "Validation failed"
    
    return message, flattened


def handle_api_errors(view_func):
    """
    Decorator to handle common API exceptions and convert them to proper responses.
    
    Catches:
    - APIException: Custom API exceptions
    - ObjectDoesNotExist: Model not found
    - DjangoValidationError: Django validation errors
    - ValueError: Invalid input values
    - Exception: Unexpected errors (logs as 500)
    
    Usage:
        @api_view(['GET'])
        @handle_api_errors
        def my_view(request):
            # Your code here, raise APINotFoundError, APIPermissionError, etc.
            raise APIPermissionError("You cannot access this resource")
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        
        except APIException as e:
            return error_response(
                message=e.message,
                code=e.code,
                status_code=e.status_code,
                details=e.details
            )
        
        except ObjectDoesNotExist as e:
            return error_response(
                message=f"Resource not found: {str(e)}",
                code='NOT_FOUND',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        except DjangoValidationError as e:
            details = {'raw_message': str(e.message) if hasattr(e, 'message') else str(e)}
            return error_response(
                message="Validation failed",
                code='VALIDATION_ERROR',
                status_code=status.HTTP_400_BAD_REQUEST,
                details=details
            )
        
        except ValueError as e:
            return error_response(
                message=f"Invalid input: {str(e)}",
                code='INVALID_INPUT',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        except Exception as e:
            logger.error(f"Unexpected error in {view_func.__name__}: {str(e)}", exc_info=True)
            return error_response(
                message="An unexpected error occurred. Please try again later.",
                code='INTERNAL_SERVER_ERROR',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                details={'error_type': type(e).__name__}
            )
    
    return wrapper
