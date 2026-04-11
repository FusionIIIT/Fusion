"""
Custom Permission Classes for otheracademic API.
These can be used with DRF's permission_classes decorator to enforce authorization.
"""
from rest_framework.permissions import BasePermission
from ..permissions_helpers import (
    is_hod,
    is_ta_supervisor,
    is_thesis_supervisor,
    is_acad_admin,
    is_dean,
    is_director,
    can_approve_ug_leave,
    can_approve_pg_leave_hod,
    can_approve_pg_leave_ta,
    can_approve_pg_leave_thesis,
    can_approve_assistantship_hod,
    can_approve_assistantship_acad_admin,
    can_approve_assistantship_thesis,
    can_approve_assistantship_ta,
    can_approve_assistantship_dean,
    can_approve_assistantship_director,
    can_approve_bonafide,
    can_approve_graduate_seminar,
    can_manage_nodues,
)


class IsHOD(BasePermission):
    """
    Permission class to check if user is a Head of Department (HOD).
    
    Usage:
        permission_classes = [IsAuthenticated, IsHOD]
    """
    message = "Unauthorized: Only HODs can access this resource."
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and is_hod(request.user))


class IsTA_Supervisor(BasePermission):
    """Permission class to check if user is a TA Supervisor."""
    message = "Unauthorized: Only TA Supervisors can access this resource."
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and is_ta_supervisor(request.user))


class IsThesis_Supervisor(BasePermission):
    """Permission class to check if user is a Thesis Supervisor."""
    message = "Unauthorized: Only Thesis Supervisors can access this resource."
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and is_thesis_supervisor(request.user))


class IsAcadAdmin(BasePermission):
    """Permission class to check if user is an Academic Admin."""
    message = "Unauthorized: Only Academic Admins can access this resource."
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and is_acad_admin(request.user))


class IsDean(BasePermission):
    """Permission class to check if user is a Dean."""
    message = "Unauthorized: Only Deans can access this resource."
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and is_dean(request.user))


class IsDirector(BasePermission):
    """Permission class to check if user is a Director."""
    message = "Unauthorized: Only Directors can access this resource."
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and is_director(request.user))


class CanApprovePGLeaveHOD(BasePermission):
    """Permission class for PG leave approval at HOD level."""
    message = "Unauthorized: Only HODs can approve PG leaves."
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and can_approve_pg_leave_hod(request.user))


class CanApprovePGLeaveTA(BasePermission):
    """Permission class for PG leave approval at TA Supervisor level."""
    message = "Unauthorized: Only TA Supervisors can approve PG leaves."
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and can_approve_pg_leave_ta(request.user))


class CanApprovePGLeaveThesis(BasePermission):
    """Permission class for PG leave approval at Thesis Supervisor level."""
    message = "Unauthorized: Only Thesis Supervisors can approve PG leaves."
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and can_approve_pg_leave_thesis(request.user))


class CanApproveBonafide(BasePermission):
    """Permission class for bonafide approval."""
    message = "Unauthorized: Only admins can approve bonafide applications."
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and can_approve_bonafide(request.user))


class CanApproveAssistantshipHOD(BasePermission):
    """Permission class for assistantship approval at HOD level."""
    message = "Unauthorized: Only HODs can approve assistantships."
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and can_approve_assistantship_hod(request.user))


class CanApproveAssistantshipAcadAdmin(BasePermission):
    """Permission class for assistantship approval at Academic Admin level."""
    message = "Unauthorized: Only Academic Admins can approve assistantships."
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and can_approve_assistantship_acad_admin(request.user))


class CanApproveAssistantshipThesis(BasePermission):
    """Permission class for assistantship approval at Thesis Supervisor level."""
    message = "Unauthorized: Only Thesis Supervisors can approve assistantships."
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and can_approve_assistantship_thesis(request.user))


class CanApproveAssistantshipTA(BasePermission):
    """Permission class for assistantship approval at TA Supervisor level."""
    message = "Unauthorized: Only TA Supervisors can approve assistantships."
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and can_approve_assistantship_ta(request.user))


class CanApproveAssistantshipDean(BasePermission):
    """Permission class for assistantship approval at Dean level."""
    message = "Unauthorized: Only Deans can approve assistantships."
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and can_approve_assistantship_dean(request.user))


class CanApproveAssistantshipDirector(BasePermission):
    """Permission class for assistantship approval at Director level."""
    message = "Unauthorized: Only Directors can approve assistantships."
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and can_approve_assistantship_director(request.user))


class CanApproveGraduateSeminar(BasePermission):
    """Permission class for graduate seminar form approval."""
    message = "Unauthorized: Only HODs or Academic Admins can approve graduate seminar forms."
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and can_approve_graduate_seminar(request.user))


class CanManageNoDues(BasePermission):
    """Permission class for managing no dues records."""
    message = "Unauthorized: Only authorized admins can manage no dues records."
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and can_manage_nodues(request.user))
