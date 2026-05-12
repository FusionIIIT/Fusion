"""
Security Settings and Configuration for Visitor Hostel Module
Provides centralized security configuration
"""

from django.conf import settings
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated

# ============================================================
# AUTHENTICATION CONFIGURATION
# ============================================================

# Default authentication classes for VH APIs
VH_DEFAULT_AUTHENTICATION_CLASSES = [
    SessionAuthentication,
    TokenAuthentication,  # For API clients
]

# Default permission classes for VH APIs
VH_DEFAULT_PERMISSION_CLASSES = [
    IsAuthenticated,
]

# ============================================================
# SECURITY POLICIES
# ============================================================

class VHSecurityPolicy:
    """Security policy configuration for Visitor Hostel"""
    
    # Session security
    SESSION_TIMEOUT_MINUTES = 60  # Auto logout after 1 hour
    SESSION_RENEWAL_MINUTES = 15  # Renew session every 15 minutes of activity
    
    # API Rate limiting
    API_RATE_LIMIT_PER_MINUTE = 60  # 60 requests per minute per IP
    API_BURST_LIMIT = 200  # 200 requests in 5 minutes before blocking
    
    # Authentication requirements
    REQUIRE_AUTHENTICATION = True  # All endpoints require auth
    ALLOW_ANONYMOUS_HEALTH_CHECK = True  # Health endpoint can be anonymous
    
    # Data access policies
    USER_CAN_ONLY_VIEW_OWN_DATA = True  # Users see only their own bookings
    STAFF_CAN_VIEW_ALL_DATA = True  # Staff can see all data
    ADMIN_BYPASS_ALL_RESTRICTIONS = True  # Admin can bypass all restrictions
    
    # Audit logging
    LOG_ALL_API_REQUESTS = True  # Log every API request
    LOG_SECURITY_EVENTS = True  # Log security violations
    LOG_DATA_ACCESS = True  # Log data access patterns
    
    # Sensitive data handling
    MASK_SENSITIVE_DATA_FOR_NON_STAFF = True  # Hide phone, email for non-staff
    NEVER_EXPOSE_INTERNAL_ERRORS = True  # Never show stack traces
    
    # Business rule enforcement
    ENFORCE_BOOKING_OWNERSHIP = True  # Users can only modify their bookings
    ENFORCE_STATUS_TRANSITIONS = True  # Strict status transition rules
    ENFORCE_ROLE_BASED_OPERATIONS = True  # Role-based operation restrictions

# ============================================================
# MIDDLEWARE CONFIGURATION
# ============================================================

VH_SECURITY_MIDDLEWARE = [
    'applications.visitor_hostel.security.middleware.VHRateLimitingMiddleware',
    'applications.visitor_hostel.security.middleware.VHSecurityMiddleware',
    'applications.visitor_hostel.security.middleware.VHDataProtectionMiddleware',
]

# ============================================================
# PERMISSION MATRIX UTILITIES
# ============================================================

def get_required_permissions_for_endpoint(endpoint_name):
    """Get required permissions for specific endpoint"""
    
    permission_map = {
        # Booking endpoints
        'active_bookings': ['view_bookings'],
        'pending_bookings': ['view_all_bookings', 'staff_access'],
        'request_booking': ['create_booking'],
        'confirm_booking': ['confirm_booking', 'incharge_access'],
        'cancel_booking': ['cancel_booking'],
        'update_booking': ['modify_booking'],
        
        # Room endpoints
        'room_availability': ['view_rooms'],
        'edit_room_status': ['manage_rooms', 'staff_access'],
        
        # Inventory endpoints
        'inventory_list': ['view_inventory', 'staff_access'],
        'add_to_inventory': ['manage_inventory', 'staff_access'],
        'update_inventory': ['manage_inventory', 'staff_access'],
        
        # Billing endpoints
        'bill_generation': ['generate_bills', 'staff_access'],
        'settle_bill': ['settle_bills', 'incharge_access'],
        
        # Reports endpoints
        'booking_reports': ['view_reports', 'staff_access'],
        'inventory_reports': ['view_reports', 'staff_access'],
        'bill_between_dates': ['view_reports', 'staff_access'],
        
        # Management endpoints
        'detect_no_shows': ['view_reports', 'staff_access'],
        'detect_overstays': ['view_reports', 'staff_access'],
        'detect_due_checkouts': ['view_reports', 'staff_access'],
    }
    
    return permission_map.get(endpoint_name, [])

# ============================================================
# SECURITY HEADERS
# ============================================================

VH_SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';",
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
}

# ============================================================
# ERROR MESSAGES
# ============================================================

VH_ERROR_MESSAGES = {
    'AUTHENTICATION_REQUIRED': {
        'message': 'Authentication is required to access this resource',
        'code': 'AUTH_REQUIRED',
        'status': 401
    },
    'INSUFFICIENT_PERMISSIONS': {
        'message': 'You do not have sufficient permissions for this operation',
        'code': 'PERMISSION_DENIED',
        'status': 403
    },
    'ACCESS_DENIED': {
        'message': 'Access denied - you can only access your own data',
        'code': 'ACCESS_DENIED',
        'status': 403
    },
    'STAFF_ACCESS_REQUIRED': {
        'message': 'This operation requires VH staff access',
        'code': 'STAFF_ACCESS_REQUIRED',
        'status': 403
    },
    'INCHARGE_ACCESS_REQUIRED': {
        'message': 'This operation requires VH Incharge authorization',
        'code': 'INCHARGE_ACCESS_REQUIRED',
        'status': 403
    },
    'RATE_LIMIT_EXCEEDED': {
        'message': 'Too many requests. Please wait before trying again',
        'code': 'RATE_LIMIT_EXCEEDED',
        'status': 429
    },
    'IP_BLOCKED': {
        'message': 'Your IP has been temporarily blocked due to suspicious activity',
        'code': 'IP_BLOCKED',
        'status': 429
    },
    'BOOKING_ACCESS_DENIED': {
        'message': 'You cannot access this booking',
        'code': 'BOOKING_ACCESS_DENIED',
        'status': 403
    },
    'BOOKING_MODIFICATION_DENIED': {
        'message': 'You cannot modify this booking in its current state',
        'code': 'BOOKING_MODIFICATION_DENIED',
        'status': 403
    },
    'INTERNAL_ERROR': {
        'message': 'An internal error occurred. Please contact support if the problem persists',
        'code': 'INTERNAL_ERROR',
        'status': 500
    }
}

# ============================================================
# SECURITY VALIDATION FUNCTIONS
# ============================================================

def validate_security_configuration():
    """Validate security configuration on startup"""
    
    errors = []
    
    # Check if authentication is properly configured
    if not hasattr(settings, 'REST_FRAMEWORK'):
        errors.append("REST_FRAMEWORK setting not configured")
    
    # Check if logging is configured
    if not hasattr(settings, 'LOGGING'):
        errors.append("LOGGING setting not configured")
    
    # Check if security middleware is enabled
    middleware = getattr(settings, 'MIDDLEWARE', [])
    required_middleware = [
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
    ]
    
    for mw in required_middleware:
        if mw not in middleware:
            errors.append(f"Required middleware missing: {mw}")
    
    if errors:
        raise Exception(f"Security configuration errors: {errors}")
    
    return True

def get_security_context_for_user(user):
    """Get security context information for a user"""
    
    if not user or not user.is_authenticated:
        return {
            'authenticated': False,
            'roles': [],
            'permissions': [],
            'can_view_sensitive_data': False
        }
    
    from .rbac import get_user_vh_roles, get_user_permissions, is_vh_staff
    
    roles = get_user_vh_roles(user)
    permissions = get_user_permissions(user)
    
    return {
        'authenticated': True,
        'user_id': user.id,
        'username': user.username,
        'roles': roles,
        'permissions': permissions,
        'is_vh_staff': is_vh_staff(user),
        'can_view_sensitive_data': is_vh_staff(user),
        'can_modify_any_booking': is_vh_staff(user),
        'security_clearance': 'high' if is_vh_staff(user) else 'standard'
    }

# ============================================================
# DJANGO SETTINGS INTEGRATION
# ============================================================

def apply_vh_security_settings():
    """Apply VH security settings to Django configuration"""
    
    # Update REST_FRAMEWORK settings
    if hasattr(settings, 'REST_FRAMEWORK'):
        rest_framework = settings.REST_FRAMEWORK
    else:
        rest_framework = {}
    
    rest_framework.update({
        'DEFAULT_AUTHENTICATION_CLASSES': VH_DEFAULT_AUTHENTICATION_CLASSES,
        'DEFAULT_PERMISSION_CLASSES': VH_DEFAULT_PERMISSION_CLASSES,
        'DEFAULT_THROTTLE_CLASSES': [
            'rest_framework.throttling.AnonRateThrottle',
            'rest_framework.throttling.UserRateThrottle'
        ],
        'DEFAULT_THROTTLE_RATES': {
            'anon': '30/min',
            'user': '60/min'
        }
    })
    
    settings.REST_FRAMEWORK = rest_framework
    
    # Security headers
    if hasattr(settings, 'SECURE_CONTENT_TYPE_NOSNIFF'):
        settings.SECURE_CONTENT_TYPE_NOSNIFF = True
    if hasattr(settings, 'SECURE_BROWSER_XSS_FILTER'):
        settings.SECURE_BROWSER_XSS_FILTER = True
    if hasattr(settings, 'X_FRAME_OPTIONS'):
        settings.X_FRAME_OPTIONS = 'DENY'