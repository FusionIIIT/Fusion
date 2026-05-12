"""
Visitor Hostel Module Logging Configuration
Provides comprehensive logging for error tracking and debugging in production
"""

import logging
import os
import json
from datetime import datetime
from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

# ============================================================
# LOGGING CONFIGURATION
# ============================================================

class VisitorHostelLogger:
    """Centralized logger for Visitor Hostel module"""
    
    def __init__(self):
        self.logger = logging.getLogger('visitor_hostel')
        if not self.logger.handlers:
            self._configure_logger()
    
    def _configure_logger(self):
        """Configure logger with file and console handlers"""
        self.logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
        
        # Create logs directory if it doesn't exist
        log_dir = os.path.join(settings.BASE_DIR, 'logs', 'visitor_hostel')
        os.makedirs(log_dir, exist_ok=True)
        
        # File handler for errors
        error_handler = logging.FileHandler(
            os.path.join(log_dir, 'errors.log')
        )
        error_handler.setLevel(logging.ERROR)
        
        # File handler for general logs
        info_handler = logging.FileHandler(
            os.path.join(log_dir, 'info.log')
        )
        info_handler.setLevel(logging.INFO)
        
        # Console handler for development
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG if settings.DEBUG else logging.WARNING)
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(module)s:%(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Set formatters
        error_handler.setFormatter(detailed_formatter)
        info_handler.setFormatter(detailed_formatter)
        console_handler.setFormatter(simple_formatter)
        
        # Add handlers to logger
        self.logger.addHandler(error_handler)
        self.logger.addHandler(info_handler)
        self.logger.addHandler(console_handler)
    
    def log_api_request(self, request, view_name, user=None):
        """Log API request details"""
        user_info = 'Anonymous'
        if user and user.is_authenticated:
            user_info = f"{user.username} (ID: {user.id})"
        
        self.logger.info(
            f"API Request | {view_name} | {request.method} {request.path} | "
            f"User: {user_info} | IP: {self._get_client_ip(request)}"
        )
    
    def log_api_error(self, request, view_name, error, user=None):
        """Log API error with context"""
        user_info = 'Anonymous'
        if user and user.is_authenticated:
            user_info = f"{user.username} (ID: {user.id})"
        
        error_context = {
            'view': view_name,
            'method': request.method,
            'path': request.path,
            'user': user_info,
            'ip': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'timestamp': datetime.now().isoformat()
        }
        
        self.logger.error(
            f"API Error | {view_name} | {error} | Context: {json.dumps(error_context)}"
        )
    
    def log_business_rule_violation(self, rule_id, description, context, user=None):
        """Log business rule violations"""
        user_info = 'System'
        if user and user.is_authenticated:
            user_info = f"{user.username} (ID: {user.id})"
        
        self.logger.warning(
            f"Business Rule Violation | {rule_id} | {description} | "
            f"User: {user_info} | Context: {json.dumps(context)}"
        )
    
    def log_security_event(self, event_type, user=None, details=None, request=None):
        """Log security-related events for auditing"""
        user_info = 'Anonymous'
        if user and user.is_authenticated:
            user_info = f"{user.username} (ID: {user.id})"
        
        ip = self._get_client_ip(request) if request else details.get('ip_address') if details else None
        details_str = f" | Details: {details}" if details else ""
        
        self.logger.warning(
            f"Security Event | {event_type} | User: {user_info} | IP: {ip or 'Unknown'}{details_str}"
        )
    
    def log_access_denied(self, request, user, required_permission):
        """Log access denied events"""
        self.log_security_event('access_denied', user, {
            'path': request.path,
            'method': request.method,
            'required_permission': required_permission
        }, request)
    
    def log_booking_operation(self, operation, booking_id, user, details=None):
        """Log booking operations for audit trail"""
        self.logger.info(
            f"Booking Operation | {operation} | Booking ID: {booking_id} | "
            f"User: {user.username} (ID: {user.id}) | Details: {details or 'None'}"
        )
    
    def log_room_operation(self, operation, room_info, user, details=None):
        """Log room-related operations"""
        self.logger.info(
            f"Room Operation | {operation} | Room: {room_info} | "
            f"User: {user.username} (ID: {user.id}) | Details: {details or 'None'}"
        )
    
    def log_bill_operation(self, operation, booking_id, amount, user, details=None):
        """Log billing operations for financial audit"""
        self.logger.info(
            f"Bill Operation | {operation} | Booking ID: {booking_id} | "
            f"Amount: {amount} | User: {user.username} (ID: {user.id}) | "
            f"Details: {details or 'None'}"
        )
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'Unknown')

# Global logger instance
vh_logger = VisitorHostelLogger()

# ============================================================
# MIDDLEWARE FOR REQUEST LOGGING
# ============================================================

class VisitorHostelLoggingMiddleware(MiddlewareMixin):
    """Middleware to log all visitor hostel API requests"""
    
    def process_request(self, request):
        # Only log visitor hostel requests
        if '/visitorhostel/api' in request.path:
            request._vh_start_time = datetime.now()
            vh_logger.log_api_request(
                request, 
                self._get_view_name(request),
                getattr(request, 'user', None)
            )
    
    def process_exception(self, request, exception):
        # Log exceptions in visitor hostel views
        if '/visitorhostel/api' in request.path:
            vh_logger.log_api_error(
                request,
                self._get_view_name(request),
                exception,
                getattr(request, 'user', None)
            )
    
    def _get_view_name(self, request):
        """Extract view name from request path"""
        path_parts = request.path.split('/')
        if len(path_parts) >= 3:
            return path_parts[-2] if path_parts[-1] == '' else path_parts[-1]
        return 'Unknown'

# ============================================================
# DECORATOR FOR ERROR HANDLING
# ============================================================

def log_errors(operation_name):
    """Decorator to log errors in service functions"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                vh_logger.logger.debug(f"Operation successful: {operation_name}")
                return result
            except Exception as e:
                vh_logger.logger.error(
                    f"Operation failed: {operation_name} | Error: {str(e)} | "
                    f"Args: {args} | Kwargs: {kwargs}"
                )
                raise
        return wrapper
    return decorator

# ============================================================
# ERROR RESPONSE UTILITIES
# ============================================================

def create_error_response(message, status_code=400, error_code=None, details=None):
    """Create standardized error response"""
    response_data = {
        'success': False,
        'error': message,
        'timestamp': datetime.now().isoformat()
    }
    
    if error_code:
        response_data['error_code'] = error_code
    
    if details and settings.DEBUG:
        response_data['details'] = details
    
    return JsonResponse(response_data, status=status_code)

def handle_api_exception(request, exception, view_name):
    """Handle API exceptions with proper logging and response"""
    vh_logger.log_api_error(request, view_name, exception, getattr(request, 'user', None))
    
    # Return user-friendly error based on exception type
    if 'permission' in str(exception).lower():
        return create_error_response(
            'You do not have permission to perform this action.',
            status_code=403,
            error_code='PERMISSION_DENIED'
        )
    elif 'validation' in str(exception).lower():
        return create_error_response(
            'Please check your input and try again.',
            status_code=400,
            error_code='VALIDATION_ERROR'
        )
    elif 'not found' in str(exception).lower():
        return create_error_response(
            'The requested resource was not found.',
            status_code=404,
            error_code='NOT_FOUND'
        )
    else:
        return create_error_response(
            'An unexpected error occurred. Our team has been notified.',
            status_code=500,
            error_code='INTERNAL_ERROR',
            details=str(exception) if settings.DEBUG else None
        )