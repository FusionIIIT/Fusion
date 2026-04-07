from rest_framework import permissions

from applications.globals.models import HoldsDesignation, ModuleAccess


class ModuleAccessHRPermission(permissions.BasePermission):
    """Allow access only to users with HR module access rights."""

    message = "User does not have HR module access."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        working_designations = request.user.holdsdesignation_set.select_related("designation").all()
        for hold in working_designations:
            designation_name = getattr(hold.designation, "name", None)
            if not designation_name:
                continue
            access = ModuleAccess.objects.filter(
                designation__iexact=designation_name.strip(),
                hr=True,
            ).exists()
            if access:
                return True

        return False
