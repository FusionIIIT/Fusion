"""
Error handling utilities for API responses.
Provides standardized error and success response formatting.
"""

from rest_framework.response import Response
from rest_framework import status as http_status


# ===== Custom Exception Classes =====

class APIValidationError(Exception):
    """Raised when API input validation fails."""
    pass


class APINotFoundError(Exception):
    """Raised when a requested resource is not found."""
    pass


class APIPermissionError(Exception):
    """Raised when a user lacks required permissions."""
    pass


# ===== Response Formatting Functions =====

def error_response(message, code=None, status_code=None, details=None):
    """
    Format an error response.

    Args:
        message (str): Human-readable error message
        code (str): Error code for client-side handling
        status_code (int): HTTP status code (default: 400)
        details (dict): Additional error details

    Returns:
        Response: DRF Response object with error data
    """
    if status_code is None:
        status_code = http_status.HTTP_400_BAD_REQUEST

    payload = {
        'error': message,
    }

    if code:
        payload['code'] = code

    if details:
        payload['details'] = details

    return Response(payload, status=status_code)


def success_response(message=None, data=None, status_code=None):
    """
    Format a success response.

    Args:
        message (str): Success message (optional)
        data (dict): Response data (optional)
        status_code (int): HTTP status code (default: 200)

    Returns:
        Response: DRF Response object with success data
    """
    if status_code is None:
        status_code = http_status.HTTP_200_OK

    payload = {}

    if message:
        payload['message'] = message

    if data:
        payload['data'] = data

    return Response(payload, status=status_code)


def serialize_serializer_errors(serializer):
    """
    Convert Django REST Framework serializer errors into a readable format.

    Args:
        serializer: DRF serializer with validation errors

    Returns:
        tuple: (error_message, error_details_dict)
    """
    errors = serializer.errors

    # Build error details dictionary
    error_details = {}
    for field, messages in errors.items():
        if isinstance(messages, list):
            error_details[field] = messages[0] if messages else 'Invalid value'
        else:
            error_details[field] = str(messages)

    # Create a generic error message
    error_message = 'Validation error'
    if error_details:
        first_field = next(iter(error_details))
        error_message = f"Validation error in '{first_field}'"

    return error_message, error_details


def handle_api_errors(func):
    """
    Decorator for handling common API errors.
    Can be applied to view functions for automatic error handling.

    Args:
        func: View function to wrap

    Returns:
        Wrapped function with error handling
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except APIValidationError as e:
            return error_response(
                message=str(e),
                code='VALIDATION_ERROR',
                status_code=http_status.HTTP_400_BAD_REQUEST
            )
        except APINotFoundError as e:
            return error_response(
                message=str(e),
                code='NOT_FOUND',
                status_code=http_status.HTTP_404_NOT_FOUND
            )
        except APIPermissionError as e:
            return error_response(
                message=str(e),
                code='PERMISSION_DENIED',
                status_code=http_status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            return error_response(
                message='An unexpected error occurred',
                code='INTERNAL_SERVER_ERROR',
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                details={'error': str(e)} if str(e) else None
            )

    return wrapper
