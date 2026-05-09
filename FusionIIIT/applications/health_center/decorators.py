"""
Health Center RBAC Decorators
==============================
Role-based access control decorators for PHC module.

Task 21: Permission decorators for role-based access control

Roles:
  - PATIENT: Student/Faculty/Staff viewing own records
  - COMPOUNDER: PHC staff (ADMIN role) managing prescriptions, stock
  - EMPLOYEE: Faculty/Staff submitting reimbursement claims
  - ACCOUNTS_STAFF: Accounts department approving reimbursement claims

Pattern: Decorators check permissions and return 403 if unauthorized
"""

from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from applications.globals.models import ExtraInfo


# ===========================================================================
# ── PERMISSION HELPER FUNCTIONS ────────────────────────────────────────
# ===========================================================================

def get_user_extra_info(user):
    """
    Get ExtraInfo for a user. Returns None if not found.
    Task 21: Centralized helper for user role lookups
    """
    try:
        return ExtraInfo.objects.get(user=user)
    except ExtraInfo.DoesNotExist:
        return None


def is_patient(user):
    """
    Check if user is a patient (STUDENT, FACULTY, STAFF role).
    Task 21: Patient role check
    """
    extra_info = get_user_extra_info(user)
    if not extra_info:
        return False
    return getattr(extra_info, 'user_type', '').upper() in ['STUDENT', 'FACULTY', 'STAFF']


def is_compounder(user):
    """
    Check if user is PHC staff (compounder) - ADMIN role.
    Task 21: Compounder/PHC staff role check
    """
    extra_info = get_user_extra_info(user)
    if not extra_info:
        return False
    # PHC staff typically have ADMIN role
    return extra_info.user_type == 'ADMIN'


def is_employee(user):
    """
    Check if user is an employee (FACULTY or STAFF).
    Task 21: Employee role check for reimbursement submissions
    
    Employees can submit reimbursement claims
    """
    extra_info = get_user_extra_info(user)
    if not extra_info:
        return False
    return getattr(extra_info, 'user_type', '').upper() in ['FACULTY', 'STAFF']


def is_accounts_staff(user):
    """
    Check if user is accounts/finance staff.
    Task 21: Accounts staff role check
    
    Accounts staff can approve/verify reimbursement claims
    Uses department information from ExtraInfo
    """
    extra_info = get_user_extra_info(user)
    if not extra_info:
        return False
    
    # Check if user belongs to Accounts/Finance department
    if hasattr(extra_info, 'department_info'):
        # If department_info is set, check if it's accounts
        try:
            dept = extra_info.department_info
            if dept and hasattr(dept, 'department_name'):
                return 'ACCOUNT' in dept.department_name.upper() or 'FINANCE' in dept.department_name.upper()
        except:
            pass
    
    # Alternative: check if user comment contains accounts designation
    # For now, use a simple check: ADMIN role can also be accounts staff
    return extra_info.user_type == 'ADMIN'


def is_auditor(user):
    """
    Check if user is an auditor.
    Task: Auditor role check for reimbursement claim approval
    
    Auditors can approve/reject reimbursement claims.
    Checks using ExtraInfo.user_type from globals app.
    """
    import logging
    import traceback
    logger = logging.getLogger(__name__)
    
    try:
        from applications.globals.models import ExtraInfo
        
        # Debug: log the user making the request
        print(f"\n[IS_AUDITOR DEBUG] User object: {user}")
        print(f"[IS_AUDITOR DEBUG] User type: {type(user)}")
        print(f"[IS_AUDITOR DEBUG] User username: {user.username}")
        print(f"[IS_AUDITOR DEBUG] User is_authenticated: {user.is_authenticated}")
        
        logger.info(f"[IS_AUDITOR] Checking user: {user.username}, is_authenticated: {user.is_authenticated}")
        
        # Get user's ExtraInfo
        extra_info = ExtraInfo.objects.get(user=user)
        
        print(f"[IS_AUDITOR DEBUG] ExtraInfo user_type: {extra_info.user_type}")
        logger.info(f"[IS_AUDITOR] Found ExtraInfo, user_type: {extra_info.user_type}")
        
        # Check if user_type is AUDITOR
        result = extra_info.user_type == 'AUDITOR'
        print(f"[IS_AUDITOR DEBUG] Is auditor? {result}")
        logger.info(f"[IS_AUDITOR] Result: {result}")
        return result
    except Exception as e:
        print(f"\n[IS_AUDITOR DEBUG ERROR] {str(e)}")
        print(f"[IS_AUDITOR DEBUG TRACEBACK]\n{traceback.format_exc()}")
        logger.error(f"[IS_AUDITOR] Error checking auditor status: {str(e)}")
        logger.error(f"[IS_AUDITOR] Traceback: {traceback.format_exc()}")
        return False


def is_doctor(user):
    """
    Check if user is a doctor.
    Task 21: Doctor role check
    """
    from .models import Doctor
    try:
        return Doctor.objects.filter(user__user=user).exists()
    except:
        return False


def is_phc_staff(request):
    """
    Check if user is PHC staff (compounder).
    Wrapper function that takes request instead of user object.
    Used directly in APIView methods.
    """
    return is_compounder(request.user)


# ===========================================================================
# ── RBAC DECORATORS ──────────────────────────────────────────────────────
# ===========================================================================

def require_patient(view_func):
    """
    Decorator: Ensure user is a patient (STUDENT, FACULTY, STAFF).
    Task 21: @require_patient decorator
    
    Usage:
        @require_patient
        def get(self, request):
            ...
    
    Returns: 403 Forbidden if user is not a patient
    """
    @wraps(view_func)
    def wrapper(self, request, *args, **kwargs):
        if not is_patient(request.user):
            return Response(
                {'detail': 'Permission denied. Patient role required.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return view_func(self, request, *args, **kwargs)
    return wrapper


def require_compounder(view_func):
    """
    Decorator: Ensure user is PHC staff (compounder).
    Task 21: @require_compounder decorator
    
    Usage:
        @require_compounder
        def post(self, request):
            ...
    
    Returns: 403 Forbidden if user is not compounder
    """
    @wraps(view_func)
    def wrapper(self, request, *args, **kwargs):
        if not is_compounder(request.user):
            return Response(
                {'detail': 'Permission denied. Compounder role required.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return view_func(self, request, *args, **kwargs)
    return wrapper


def require_employee(view_func):
    """
    Decorator: Ensure user is an employee (FACULTY or STAFF).
    Task 21: @require_employee decorator
    
    Usage:
        @require_employee
        def post(self, request):
            ...
    
    Returns: 403 Forbidden if user is not an employee
    """
    @wraps(view_func)
    def wrapper(self, request, *args, **kwargs):
        if not is_employee(request.user):
            return Response(
                {'detail': 'Permission denied. Employee role required.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return view_func(self, request, *args, **kwargs)
    return wrapper


def require_accounts_staff(view_func):
    """
    Decorator: Ensure user is accounts/finance staff.
    Task 21: @require_accounts_staff decorator
    
    Usage:
        @require_accounts_staff
        def patch(self, request):
            ...
    
    Returns: 403 Forbidden if user is not accounts staff
    """
    @wraps(view_func)
    def wrapper(self, request, *args, **kwargs):
        if not is_accounts_staff(request.user):
            return Response(
                {'detail': 'Permission denied. Accounts staff role required.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return view_func(self, request, *args, **kwargs)
    return wrapper


def require_doctor(view_func):
    """
    Decorator: Ensure user is a doctor.
    Task 21: @require_doctor decorator
    
    Usage:
        @require_doctor
        def post(self, request):
            ...
    
    Returns: 403 Forbidden if user is not a doctor
    """
    @wraps(view_func)
    def wrapper(self, request, *args, **kwargs):
        if not is_doctor(request.user):
            return Response(
                {'detail': 'Permission denied. Doctor role required.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return view_func(self, request, *args, **kwargs)
    return wrapper


def require_patient_or_compounder(view_func):
    """
    Decorator: Ensure user is either patient or compounder.
    Task 21: Combined role decorator
    
    Usage:
        @require_patient_or_compounder
        def get(self, request):
            ...
    
    Returns: 403 Forbidden if user is neither patient nor compounder
    """
    @wraps(view_func)
    def wrapper(self, request, *args, **kwargs):
        if not (is_patient(request.user) or is_compounder(request.user)):
            return Response(
                {'detail': 'Permission denied. Patient or Compounder role required.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return view_func(self, request, *args, **kwargs)
    return wrapper


def require_any_role(*roles):
    """
    Decorator factory: Ensure user has any of the specified roles.
    Task 21: Flexible role checking decorator
    
    Usage:
        @require_any_role('patient', 'compounder')
        def get(self, request):
            ...
    
    Valid role names: 'patient', 'compounder', 'employee', 'accounts_staff', 'doctor'
    Returns: 403 Forbidden if user doesn't have any of the roles
    """
    role_checkers = {
        'patient': is_patient,
        'compounder': is_compounder,
        'employee': is_employee,
        'accounts_staff': is_accounts_staff,
        'doctor': is_doctor,
    }
    
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            # Check if user has any of the required roles
            has_role = False
            for role in roles:
                if role in role_checkers:
                    if role_checkers[role](request.user):
                        has_role = True
                        break
            
            if not has_role:
                return Response(
                    {'detail': f'Permission denied. One of these roles required: {", ".join(roles)}'},
                    status=status.HTTP_403_FORBIDDEN
                )
            return view_func(self, request, *args, **kwargs)
        return wrapper
    return decorator


# ===========================================================================
# ── HELPER FOR MANUAL PERMISSION CHECKS ────────────────────────────────────
# ===========================================================================

def check_permission(request, permission_func, error_message=None):
    """
    Helper function for manual permission checks inside view methods.
    Task 21: Used in views that don't use decorators
    
    Usage:
        def post(self, request):
            check_result = check_permission(request, is_compounder)
            if not check_result:
                return Response(
                    {'detail': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
    
    Args:
        request: HTTP request object
        permission_func: Permission check function (is_patient, is_compounder, etc)
        error_message: Custom error message (optional)
    
    Returns: True if permission granted, False otherwise
    """
    return permission_func(request.user)
