"""
RBAC Security Module for Visitor Hostel
Implements role-based access control and data filtering
"""

from functools import wraps
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.db.models import Q
from applications.visitor_hostel.logging_config import vh_logger

# ============================================================
# ROLE DEFINITIONS & PERMISSIONS
# ============================================================

class VHUserRole:
    """Visitor Hostel user role definitions"""
    VH_INCHARGE = 'VhIncharge'
    VH_CARETAKER = 'VhCaretaker'
    STUDENT = 'student'
    FACULTY = 'faculty'
    STAFF = 'staff'
    ADMIN = 'admin'

class VHPermission:
    """Visitor Hostel permission definitions"""
    # Booking permissions
    VIEW_ALL_BOOKINGS = 'view_all_bookings'
    VIEW_OWN_BOOKINGS = 'view_own_bookings'
    CREATE_BOOKING = 'create_booking'
    CONFIRM_BOOKING = 'confirm_booking'
    MODIFY_BOOKING = 'modify_booking'
    CANCEL_BOOKING = 'cancel_booking'
    
    # Room management permissions
    VIEW_ROOMS = 'view_rooms'
    MANAGE_ROOMS = 'manage_rooms'
    
    # Billing permissions
    VIEW_BILLS = 'view_bills'
    GENERATE_BILLS = 'generate_bills'
    SETTLE_BILLS = 'settle_bills'
    
    # Inventory permissions
    VIEW_INVENTORY = 'view_inventory'
    MANAGE_INVENTORY = 'manage_inventory'
    
    # Reports permissions
    VIEW_REPORTS = 'view_reports'
    GENERATE_REPORTS = 'generate_reports'

# ============================================================
# PERMISSION MATRIX
# ============================================================

ROLE_PERMISSIONS = {
    VHUserRole.VH_INCHARGE: [
        VHPermission.VIEW_ALL_BOOKINGS,
        VHPermission.CREATE_BOOKING,
        VHPermission.CONFIRM_BOOKING,
        VHPermission.MODIFY_BOOKING,
        VHPermission.CANCEL_BOOKING,
        VHPermission.VIEW_ROOMS,
        VHPermission.MANAGE_ROOMS,
        VHPermission.VIEW_BILLS,
        VHPermission.GENERATE_BILLS,
        VHPermission.SETTLE_BILLS,
        VHPermission.VIEW_INVENTORY,
        VHPermission.MANAGE_INVENTORY,
        VHPermission.VIEW_REPORTS,
        VHPermission.GENERATE_REPORTS,
    ],
    VHUserRole.VH_CARETAKER: [
        VHPermission.VIEW_ALL_BOOKINGS,
        VHPermission.CREATE_BOOKING,
        VHPermission.MODIFY_BOOKING,
        VHPermission.VIEW_ROOMS,
        VHPermission.VIEW_BILLS,
        VHPermission.GENERATE_BILLS,
        VHPermission.VIEW_INVENTORY,
        VHPermission.MANAGE_INVENTORY,
        VHPermission.VIEW_REPORTS,
    ],
    VHUserRole.FACULTY: [
        VHPermission.VIEW_OWN_BOOKINGS,
        VHPermission.CREATE_BOOKING,
        VHPermission.MODIFY_BOOKING,  # Only own bookings
        VHPermission.CANCEL_BOOKING,  # Only own bookings
        VHPermission.VIEW_ROOMS,
        VHPermission.VIEW_BILLS,  # Only own bills
    ],
    VHUserRole.STUDENT: [
        VHPermission.VIEW_OWN_BOOKINGS,
        VHPermission.CREATE_BOOKING,
        VHPermission.MODIFY_BOOKING,  # Only own bookings
        VHPermission.CANCEL_BOOKING,  # Only own bookings
        VHPermission.VIEW_ROOMS,
        VHPermission.VIEW_BILLS,  # Only own bills
    ],
    VHUserRole.STAFF: [
        VHPermission.VIEW_OWN_BOOKINGS,
        VHPermission.CREATE_BOOKING,
        VHPermission.MODIFY_BOOKING,  # Only own bookings
        VHPermission.CANCEL_BOOKING,  # Only own bookings
        VHPermission.VIEW_ROOMS,
        VHPermission.VIEW_BILLS,  # Only own bills
    ]
}

# ============================================================
# ROLE DETECTION UTILITIES
# ============================================================

def get_user_vh_roles(user):
    """
    Get visitor hostel roles for a user
    Returns list of roles
    """
    if not user or not user.is_authenticated:
        return []
    
    roles = []
    
    # Check VH-specific designations
    vh_designations = user.holds_designations.values_list('designation__name', flat=True)
    
    if VHUserRole.VH_INCHARGE in vh_designations:
        roles.append(VHUserRole.VH_INCHARGE)
    if VHUserRole.VH_CARETAKER in vh_designations:
        roles.append(VHUserRole.VH_CARETAKER)
    
    # Check general user types
    if user.is_superuser or user.is_staff:
        roles.append(VHUserRole.ADMIN)
    
    # Check user profile for student/faculty/staff
    if hasattr(user, 'extrainfo'):
        user_type = getattr(user.extrainfo, 'user_type', '').lower()
        if user_type == 'student':
            roles.append(VHUserRole.STUDENT)
        elif user_type == 'faculty':
            roles.append(VHUserRole.FACULTY)
        elif user_type == 'staff':
            roles.append(VHUserRole.STAFF)
    
    # Default role assignment if no specific role found
    if not roles:
        roles.append(VHUserRole.STUDENT)  # Default to student
    
    return roles

def get_user_permissions(user):
    """
    Get all permissions for a user based on their roles
    """
    roles = get_user_vh_roles(user)
    permissions = set()
    
    for role in roles:
        role_perms = ROLE_PERMISSIONS.get(role, [])
        permissions.update(role_perms)
    
    return list(permissions)

def has_permission(user, permission):
    """
    Check if user has specific permission
    """
    user_permissions = get_user_permissions(user)
    return permission in user_permissions

def is_vh_staff(user):
    """Check if user is VH staff (Incharge or Caretaker)"""
    roles = get_user_vh_roles(user)
    return (VHUserRole.VH_INCHARGE in roles or 
            VHUserRole.VH_CARETAKER in roles or 
            VHUserRole.ADMIN in roles)

def is_vh_incharge(user):
    """Check if user is VH Incharge"""
    roles = get_user_vh_roles(user)
    return (VHUserRole.VH_INCHARGE in roles or 
            VHUserRole.ADMIN in roles)

# ============================================================
# DRF PERMISSION CLASSES
# ============================================================

class VHBasePermission(BasePermission):
    """Base permission class for Visitor Hostel"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return True

class VHStaffPermission(VHBasePermission):
    """Permission for VH Staff only (Incharge/Caretaker)"""
    
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return is_vh_staff(request.user)

class VHInchargePermission(VHBasePermission):
    """Permission for VH Incharge only"""
    
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return is_vh_incharge(request.user)

class VHBookingPermission(VHBasePermission):
    """Permission for booking-related operations"""
    
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        
        action = getattr(view, 'action', None) or request.method.lower()
        
        if action in ['get', 'list']:
            return has_permission(request.user, VHPermission.VIEW_ALL_BOOKINGS) or \
                   has_permission(request.user, VHPermission.VIEW_OWN_BOOKINGS)
        elif action in ['post', 'create']:
            return has_permission(request.user, VHPermission.CREATE_BOOKING)
        elif action in ['put', 'patch', 'update']:
            return has_permission(request.user, VHPermission.MODIFY_BOOKING)
        elif action in ['delete', 'cancel']:
            return has_permission(request.user, VHPermission.CANCEL_BOOKING)
        
        return False

class VHInventoryPermission(VHBasePermission):
    """Permission for inventory-related operations"""
    
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        
        action = getattr(view, 'action', None) or request.method.lower()
        
        if action in ['get', 'list']:
            return has_permission(request.user, VHPermission.VIEW_INVENTORY)
        else:
            return has_permission(request.user, VHPermission.MANAGE_INVENTORY)

# ============================================================
# DATA FILTERING UTILITIES
# ============================================================

class VHDataFilter:
    """Utility class for filtering data based on user roles"""
    
    @staticmethod
    def filter_bookings_for_user(queryset, user):
        """
        Filter booking queryset based on user permissions
        """
        if not user or not user.is_authenticated:
            return queryset.none()
        
        # VH Staff can see all bookings
        if is_vh_staff(user):
            return queryset
        
        # Regular users can only see their own bookings
        return queryset.filter(intender=user)
    
    @staticmethod
    def filter_bills_for_user(queryset, user):
        """
        Filter bill queryset based on user permissions
        """
        if not user or not user.is_authenticated:
            return queryset.none()
        
        # VH Staff can see all bills
        if is_vh_staff(user):
            return queryset
        
        # Regular users can only see their own bills
        return queryset.filter(booking__intender=user)
    
    @staticmethod
    def can_access_booking(booking, user):
        """
        Check if user can access specific booking
        """
        if not user or not user.is_authenticated:
            return False
        
        # VH Staff can access all bookings
        if is_vh_staff(user):
            return True
        
        # Users can only access their own bookings
        return booking.intender == user
    
    @staticmethod
    def can_modify_booking(booking, user):
        """
        Check if user can modify specific booking
        """
        if not VHDataFilter.can_access_booking(booking, user):
            return False
        
        # VH Incharge can modify any booking
        if is_vh_incharge(user):
            return True
        
        # VH Caretaker can modify non-confirmed bookings
        if is_vh_staff(user):
            return booking.status in ['Pending', 'Forward']
        
        # Regular users can only modify their own pending bookings
        return (booking.intender == user and 
                booking.status in ['Pending', 'Forward'] and
                has_permission(user, VHPermission.MODIFY_BOOKING))

# ============================================================
# SECURITY DECORATORS
# ============================================================

def require_vh_permission(permission):
    """
    Decorator to require specific VH permission
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(self, request, *args, **kwargs):
            if not request.user or not request.user.is_authenticated:
                vh_logger.log_security_event('unauthenticated_access_attempt', None, {
                    'path': request.path,
                    'method': request.method
                })
                return Response({
                    'error': 'Authentication required'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            if not has_permission(request.user, permission):
                vh_logger.log_security_event('unauthorized_access_attempt', request.user, {
                    'permission_required': permission,
                    'user_permissions': get_user_permissions(request.user),
                    'path': request.path
                })
                return Response({
                    'error': 'Insufficient permissions'
                }, status=status.HTTP_403_FORBIDDEN)
            
            return view_func(self, request, *args, **kwargs)
        return wrapped_view
    return decorator

def require_vh_staff(view_func):
    """
    Decorator to require VH staff access
    """
    @wraps(view_func)
    def wrapped_view(self, request, *args, **kwargs):
        if not request.user or not request.user.is_authenticated:
            return Response({
                'error': 'Authentication required'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not is_vh_staff(request.user):
            vh_logger.log_security_event('staff_access_denied', request.user, {
                'path': request.path,
                'user_roles': get_user_vh_roles(request.user)
            })
            return Response({
                'error': 'VH staff access required'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return view_func(self, request, *args, **kwargs)
    return wrapped_view

def require_vh_incharge(view_func):
    """
    Decorator to require VH Incharge access
    """
    @wraps(view_func)
    def wrapped_view(self, request, *args, **kwargs):
        if not request.user or not request.user.is_authenticated:
            return Response({
                'error': 'Authentication required'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not is_vh_incharge(request.user):
            vh_logger.log_security_event('incharge_access_denied', request.user, {
                'path': request.path,
                'user_roles': get_user_vh_roles(request.user)
            })
            return Response({
                'error': 'VH Incharge access required'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return view_func(self, request, *args, **kwargs)
    return wrapped_view

# ============================================================
# SECURITY AUDIT UTILITIES
# ============================================================

def log_access_attempt(user, action, resource_type, resource_id=None, success=True):
    """Log access attempts for security auditing"""
    vh_logger.log_security_event('access_attempt', user, {
        'action': action,
        'resource_type': resource_type,
        'resource_id': resource_id,
        'success': success,
        'user_roles': get_user_vh_roles(user) if user else []
    })

def validate_booking_access(user, booking_id, action='view'):
    """
    Validate and log booking access attempts
    Returns (allowed: bool, booking: BookingDetail or None)
    """
    from applications.visitor_hostel.models import BookingDetail
    
    try:
        booking = BookingDetail.objects.get(id=booking_id)
    except BookingDetail.DoesNotExist:
        log_access_attempt(user, action, 'booking', booking_id, False)
        return False, None
    
    allowed = VHDataFilter.can_access_booking(booking, user)
    log_access_attempt(user, action, 'booking', booking_id, allowed)
    
    return allowed, booking if allowed else None