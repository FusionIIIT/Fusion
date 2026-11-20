from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation
from applications.establishment.models import Establishment_variables


def initial_checks(request):
    return {}


def is_admin(request):
    """Function to check if the user is establishment admin."""
    est_var = Establishment_variables.objects.select_related('est_admin').first()
    return bool(est_var and request.user == est_var.est_admin)


def is_eligible(request):
    return True


def is_hod(request):
    """Function to check if the user holds an 'HOD' designation."""
    user_dsg = list(HoldsDesignation.objects.filter(user=request.user).select_related('designation'))
    for item in user_dsg:
        if item.designation and "HOD" in item.designation.name:
            return True
    return False


def is_faculty(request):
    try:
        user = ExtraInfo.objects.get(user=request.user)
        return user.user_type == 'faculty'
    except ExtraInfo.DoesNotExist:
        return False


def is_staff(request):
    try:
        user = ExtraInfo.objects.get(user=request.user)
        return user.user_type == 'staff'
    except ExtraInfo.DoesNotExist:
        return False


def is_registrar(request):
    """Function to check if the user has designation 'Registrar'."""
    user_dsg = list(HoldsDesignation.objects.filter(user=request.user).select_related('designation'))
    for item in user_dsg:
        if item.designation and "Registrar" in item.designation.name:
            return True
    return False


def is_director(request):
    """Function to check if the user has designation 'Director'."""
    user_dsg = list(HoldsDesignation.objects.filter(user=request.user).select_related('designation'))
    for item in user_dsg:
        if item.designation and "Director" in item.designation.name:
            return True
    return False


def is_cpda(dictx):
    """Function to check if the application is CPDA."""
    for key in dictx.keys():
        if 'cpda' in key:
            return True
    return False


def is_ltc(dictx):
    """Function to check if the application is LTC."""
    for key in dictx.keys():
        if 'ltc' in key:
            return True
    return False


def is_appraisal(dictx):
    """Function to check if the application is Appraisal."""
    for key in dictx.keys():
        if 'appraisal' in key:
            return True
    return False
