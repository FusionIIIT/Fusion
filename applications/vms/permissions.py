"""
VMS Permissions — role-based access control for the Visitor Management System.

Covers:
  BR-011  Host authority validation
  BR-013  Access zone restrictions (visitor-side)
  BR-021  Area access control on scan
  BR-035  Blacklist removal authority
  BR-043  VIP approval bypass permission
  BR-057  Super admin configuration access
"""

from rest_framework.permissions import BasePermission

from .models import AccessZone, HostAuthority


# ---------------------------------------------------------------------------
# BR-011: Host must have sufficient authority to approve
# ---------------------------------------------------------------------------
class HasHostApprovalAuthority(BasePermission):
    """Only hosts with department-level or higher authority may approve visits."""

    message = "Insufficient authority level to approve visitor requests."

    def has_permission(self, request, view):
        authority = HostAuthority.objects.filter(user=request.user).first()
        if authority is None:
            return False
        return authority.authority_level in (
            HostAuthority.LEVEL_DEPARTMENT,
            HostAuthority.LEVEL_ADMIN,
            HostAuthority.LEVEL_SUPER,
        )


# ---------------------------------------------------------------------------
# BR-035: Only authorised admins can remove blacklist entries
# ---------------------------------------------------------------------------
class CanRemoveBlacklist(BasePermission):
    """Only admin-level or super-admin users may remove blacklist entries."""

    message = "Only authorised administrators can remove blacklist entries."

    def has_permission(self, request, view):
        authority = HostAuthority.objects.filter(user=request.user).first()
        if authority is None:
            return False
        return authority.authority_level in (
            HostAuthority.LEVEL_ADMIN,
            HostAuthority.LEVEL_SUPER,
        )


# ---------------------------------------------------------------------------
# BR-043: VIP approval bypass
# ---------------------------------------------------------------------------
class CanBypassVIPApproval(BasePermission):
    """Only hosts explicitly authorised for VIP bypass may skip approval."""

    message = "Not authorised for VIP approval bypass."

    def has_permission(self, request, view):
        authority = HostAuthority.objects.filter(user=request.user).first()
        if authority is None:
            return False
        return authority.can_approve_vip


# ---------------------------------------------------------------------------
# Admin or super-admin (used for blacklist add, config writes, exports, etc.)
# ---------------------------------------------------------------------------
class IsVmsAdmin(BasePermission):
    """Admin-level or super-admin users may perform privileged VMS actions."""

    message = "VMS administrator privileges required."

    def has_permission(self, request, view):
        authority = HostAuthority.objects.filter(user=request.user).first()
        if authority is None:
            return False
        return authority.authority_level in (
            HostAuthority.LEVEL_ADMIN,
            HostAuthority.LEVEL_SUPER,
        )


# ---------------------------------------------------------------------------
# BR-057: Super admin only
# ---------------------------------------------------------------------------
class IsSuperAdmin(BasePermission):
    """Restrict access to super-admin users only."""

    message = "Super Admin access required."

    def has_permission(self, request, view):
        authority = HostAuthority.objects.filter(user=request.user).first()
        if authority is None:
            return False
        return authority.authority_level == HostAuthority.LEVEL_SUPER


# ---------------------------------------------------------------------------
# BR-013 / BR-021: Zone access checking (utility, not a DRF permission)
# ---------------------------------------------------------------------------
def check_zone_access(visitor_pass, zone_name: str) -> tuple[bool, str]:
    """
    Verify a visitor is authorised for the given zone.
    Returns (allowed, message).
    """
    zone = AccessZone.objects.filter(name=zone_name, active=True).first()
    if zone is None:
        return False, f"Zone '{zone_name}' not found or inactive."

    if zone.is_restricted:
        authorized_zones = [z.strip().lower() for z in visitor_pass.authorized_zones.split(",")]
        if zone_name.lower() not in authorized_zones and "all" not in authorized_zones:
            return False, f"Visitor not authorized for restricted zone '{zone_name}'."

    if zone.requires_vip and not visitor_pass.is_vip_pass:
        return False, f"Zone '{zone_name}' requires VIP access."

    return True, "Access permitted."


def check_area_access_on_scan(visit, zone_name: str) -> tuple[bool, str]:
    """
    BR-021: On scan, confirm visitor has authorization for the current location.
    """
    visitor_pass = getattr(visit, "visitor_pass", None)
    if visitor_pass is None:
        return False, "No pass issued for this visit."
    return check_zone_access(visitor_pass, zone_name)
