from rest_framework import permissions
from django.shortcuts import get_object_or_404
from applications.academic_information.models import ExtraInfo
from applications.globals.models import User


class IsFacultyStaffOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow faculty and staff to edit it.
    """

    def has_permission(self, request, view):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        #only faculty and staff are able to make post request 
        return not request.user.holds_designations.filter(designation__name='student').exists()
