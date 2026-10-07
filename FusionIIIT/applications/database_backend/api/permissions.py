from rest_framework.permissions import BasePermission
from applications.globals.models import ModuleAccess, HoldsDesignation
import logging

logger = logging.getLogger(__name__)


class IsDatabaseAccessAllowed(BasePermission):
    """
    Custom permission to check if user has access to the database module.

    Access is granted if:
    1. User is authenticated
    2. User has a designation with database module enabled in ModuleAccess

    This prevents unauthorized users (e.g., students) from accessing sensitive
    database information like student records, grades, and registrations.
    """

    message = "You do not have permission to access the database module."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        try:
            user_designations = HoldsDesignation.objects.filter(
                working=request.user
            ).values_list('designation__name', flat=True).distinct()

            if not user_designations:
                logger.warning(
                    f"User {request.user.username} attempted database access but has no designations"
                )
                return False

            has_access = ModuleAccess.objects.filter(
                designation__in=user_designations,
                database=True
            ).exists()

            if not has_access:
                logger.warning(
                    f"User {request.user.username} with designations {list(user_designations)} "
                    f"attempted database access without permission"
                )

            return has_access

        except Exception as e:
            logger.error(
                f"Error checking database access for user {request.user.username}: {str(e)}",
                exc_info=True
            )
            return False
