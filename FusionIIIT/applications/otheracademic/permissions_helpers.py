"""
Permission helper functions for otheracademic module.
Provides utility functions to check user roles and designations.
Used by API views for authorization checks.
"""
from django.core.cache import cache
from applications.globals.models import HoldsDesignation, Designation, ExtraInfo


def get_user_designations(user):
    """
    Get all active designations held by user.
    Returns: QuerySet of HoldsDesignation objects
    """
    try:
        designations = HoldsDesignation.objects.filter(
            working=user
        ).select_related('designation')
        return designations
    except Exception:
        return HoldsDesignation.objects.none()


def has_designation(user, designation_name_contains):
    """
    Check if user has a designation matching the pattern (case-insensitive).
    
    Args:
        user: Django User object
        designation_name_contains: String to search for in designation name
    
    Returns: Boolean
    """
    try:
        designations = get_user_designations(user)
        return designations.filter(
            designation__name__icontains=designation_name_contains
        ).exists()
    except Exception:
        return False


def is_hod(user):
    """Check if user is a Head of Department (HOD)."""
    return has_designation(user, 'HOD')


def is_ta_supervisor(user):
    """Check if user is a TA Supervisor."""
    return has_designation(user, 'TA')


def is_thesis_supervisor(user):
    """Check if user is a Thesis Supervisor."""
    return has_designation(user, 'Thesis')


def is_acad_admin(user):
    """
    Check if user is Academic Admin.
    Matches: 'Academic Admin', 'acadadmin', 'Acad Admin', etc.
    """
    return (
        has_designation(user, 'Academic') or 
        has_designation(user, 'acadadmin')
    )


def is_dean(user):
    """
    Check if user is Dean or Dean Academic.
    Matches: 'Dean', 'Dean Academic', 'Dean Acad', etc.
    """
    return has_designation(user, 'Dean')


def is_director(user):
    """Check if user is Director."""
    return has_designation(user, 'Director')


def is_student(user):
    """Check if user is a student."""
    try:
        extra_info = ExtraInfo.objects.get(user=user)
        return extra_info.user_type == 'student'
    except ExtraInfo.DoesNotExist:
        return False


def is_faculty(user):
    """Check if user is faculty."""
    try:
        extra_info = ExtraInfo.objects.get(user=user)
        return extra_info.user_type == 'faculty'
    except ExtraInfo.DoesNotExist:
        return False


def is_staff(user):
    """Check if user is staff."""
    try:
        extra_info = ExtraInfo.objects.get(user=user)
        return extra_info.user_type == 'staff'
    except ExtraInfo.DoesNotExist:
        return False


def get_user_department(user):
    """
    Get department for a user.
    
    Returns: Department object or None
    """
    try:
        extra_info = ExtraInfo.objects.select_related('department').get(user=user)
        return extra_info.department
    except ExtraInfo.DoesNotExist:
        return None


def get_user_roll_no(user):
    """Get roll_no/registration number for user."""
    try:
        extra_info = ExtraInfo.objects.get(user=user)
        return extra_info.roll_no
    except ExtraInfo.DoesNotExist:
        return None


def is_hod_for_department(user, department):
    """
    Check if user is HOD for a specific department.
    
    Args:
        user: Django User object
        department: Department object or department name
    
    Returns: Boolean
    """
    if not is_hod(user):
        return False
    
    user_dept = get_user_department(user)
    if user_dept is None:
        return False
    
    if hasattr(department, 'id'):  # It's a Department object
        return user_dept.id == department.id
    else:  # It's a department name string
        return user_dept.name.lower() == str(department).lower()


def can_approve_ug_leave(user):
    """Check if user can approve UG (undergraduate) leaves - typically HOD."""
    return is_hod(user)


def can_approve_pg_leave_hod(user):
    """Check if user can approve PG leave at HOD level."""
    return is_hod(user)


def can_approve_pg_leave_ta(user):
    """Check if user can approve PG leave as TA Supervisor."""
    return is_ta_supervisor(user)


def can_approve_pg_leave_thesis(user):
    """Check if user can approve PG leave as Thesis Supervisor."""
    return is_thesis_supervisor(user)


def can_approve_assistantship_hod(user):
    """Check if user can approve assistantship at HOD level."""
    return is_hod(user)


def can_approve_assistantship_acad_admin(user):
    """Check if user can approve assistantship as Academic Admin."""
    return is_acad_admin(user)


def can_approve_assistantship_thesis(user):
    """Check if user can approve assistantship as Thesis Supervisor."""
    return is_thesis_supervisor(user)


def can_approve_assistantship_ta(user):
    """Check if user can approve assistantship as TA Supervisor."""
    return is_ta_supervisor(user)


def can_approve_assistantship_dean(user):
    """Check if user can approve assistantship as Dean."""
    return is_dean(user)


def can_approve_assistantship_director(user):
    """Check if user can approve assistantship as Director."""
    return is_director(user)


def can_approve_bonafide(user):
    """Check if user can approve bonafide applications - typically admin."""
    return is_acad_admin(user) or is_hod(user)


def can_approve_graduate_seminar(user):
    """Check if user can approve graduate seminar forms."""
    return is_hod(user) or is_acad_admin(user)


def can_manage_nodues(user):
    """Check if user can manage no dues records."""
    return is_hod(user) or is_acad_admin(user)


def get_all_roles(user):
    """Get all roles/designations for a user as a list of strings."""
    try:
        designations = get_user_designations(user)
        return [des.designation.name for des in designations]
    except Exception:
        return []


def has_any_role(user):
    """Check if user has any designated role (not just a student)."""
    return get_user_designations(user).exists()


def get_designation_by_name(name):
    """
    Get a Designation object by name.
    Returns: Designation object or None
    """
    try:
        return Designation.objects.get(name=name)
    except Designation.DoesNotExist:
        return None
