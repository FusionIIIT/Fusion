from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation
from applications.establishment.models import (
    Cpda_application,
    Cpda_tracking,
    CpdaBalance,
    Cpda_bill,
    Ltc_application,
    Ltc_tracking,
    Ltc_eligible_user,
    Dependent,
    Ltc_to_avail,
    Ltc_availed,
    Appraisal,
    CoursesInstructed,
    NewCoursesOffered,
    ThesisResearchSupervision,
    SponsoredProjects,
    AppraisalRequest,
)
from .serializers import (
    CpdaApplicationSerializer,
    CpdaBalanceSerializer,
    LtcApplicationSerializer,
    LtcEligibleUserSerializer,
    AppraisalSerializer,
)


def _is_establishment_admin(user):
    from applications.establishment.models import Establishment_variables
    est_var = Establishment_variables.objects.select_related('est_admin').first()
    return bool(est_var and est_var.est_admin == user)


# ===========================================================================
# CPDA APIs
# ===========================================================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cpda_balance_api(request):
    """Returns the CPDA balance for the authenticated faculty/staff."""
    balance, _ = CpdaBalance.objects.get_or_create(user=request.user, defaults={'cpda_balance': 300000})
    serializer = CpdaBalanceSerializer(balance)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def cpda_applications_api(request):
    """
    GET: List CPDA applications for current user (or all if establishment admin).
    POST: Submit a new CPDA advance request with atomic tracking record.
    """
    if request.method == 'GET':
        if _is_establishment_admin(request.user):
            apps = Cpda_application.objects.all().select_related('applicant').order_by('-request_timestamp')
        else:
            apps = Cpda_application.objects.filter(applicant=request.user).order_by('-request_timestamp')
        serializer = CpdaApplicationSerializer(apps, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        data = request.data
        purpose = data.get('purpose', '').strip()
        requested_advance = data.get('requested_advance')
        pf_number = data.get('pf_number', '')

        if not purpose or requested_advance is None:
            return Response(
                {'error': 'Purpose and requested_advance are required fields.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            advance_int = int(requested_advance)
            if advance_int <= 0:
                raise ValueError
        except ValueError:
            return Response(
                {'error': 'requested_advance must be a positive integer.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            cpda_app = Cpda_application.objects.create(
                applicant=request.user,
                pf_number=pf_number,
                purpose=purpose,
                requested_advance=advance_int,
                status='requested'
            )
            Cpda_tracking.objects.create(
                application=cpda_app,
                review_status='to_assign'
            )

        serializer = CpdaApplicationSerializer(cpda_app)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ===========================================================================
# LTC APIs
# ===========================================================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ltc_eligibility_api(request):
    """Returns LTC eligibility and remaining quota for the authenticated user."""
    try:
        eligible_user = Ltc_eligible_user.objects.get(user=request.user)
    except Ltc_eligible_user.DoesNotExist:
        return Response(
            {'detail': 'LTC eligibility profile not configured for this user.'},
            status=status.HTTP_404_NOT_FOUND
        )
    serializer = LtcEligibleUserSerializer(eligible_user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def ltc_applications_api(request):
    """
    GET: List LTC applications for the current user (or all if admin).
    POST: Submit an LTC request with associated dependents.
    """
    if request.method == 'GET':
        if _is_establishment_admin(request.user):
            apps = Ltc_application.objects.all().select_related('applicant').order_by('-request_timestamp')
        else:
            apps = Ltc_application.objects.filter(applicant=request.user).order_by('-request_timestamp')
        serializer = LtcApplicationSerializer(apps, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        data = request.data
        required_fields = [
            'pf_number', 'basic_pay', 'leave_start', 'leave_end',
            'family_departure_date', 'purpose', 'is_hometown_or_elsewhere',
            'phone_number', 'travel_mode', 'requested_advance'
        ]
        for f in required_fields:
            if f not in data:
                return Response({'error': f"'{f}' is a required field."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            ltc_app = Ltc_application.objects.create(
                applicant=request.user,
                pf_number=data.get('pf_number'),
                basic_pay=data.get('basic_pay'),
                leave_start=data.get('leave_start'),
                leave_end=data.get('leave_end'),
                family_departure_date=data.get('family_departure_date'),
                leave_nature=data.get('leave_nature', ''),
                purpose=data.get('purpose'),
                is_hometown_or_elsewhere=data.get('is_hometown_or_elsewhere'),
                phone_number=data.get('phone_number'),
                address_during_leave=data.get('address_during_leave', ''),
                travel_mode=data.get('travel_mode'),
                requested_advance=data.get('requested_advance'),
                status='requested'
            )
            Ltc_tracking.objects.create(
                application=ltc_app,
                review_status='to_assign'
            )

            # Optional dependents list
            dependents_data = data.get('dependents_list', [])
            for dep in dependents_data:
                Dependent.objects.create(
                    ltc=ltc_app,
                    name=dep.get('name', ''),
                    age=dep.get('age'),
                    depend=dep.get('depend', '')
                )

        serializer = LtcApplicationSerializer(ltc_app)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ===========================================================================
# Appraisal APIs
# ===========================================================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def appraisal_list_api(request):
    """List appraisal records for the current user."""
    appraisals = (
        Appraisal.objects.filter(applicant=request.user)
        .prefetch_related('applicant_courses', 'applicants_offered_new_courses', 'appraisal_tracking')
        .order_by('-timestamp')
    )
    serializer = AppraisalSerializer(appraisals, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def appraisal_detail_api(request, pk):
    """Retrieve full details for a specific appraisal application."""
    appraisal = get_object_or_404(
        Appraisal.objects.prefetch_related(
            'applicant_courses',
            'applicants_offered_new_courses',
            'applicants_supervised_stud',
            'applicant_sponsored_projects',
            'appraisal_tracking'
        ),
        pk=pk
    )
    if appraisal.applicant != request.user and not _is_establishment_admin(request.user):
        return Response({'detail': 'Not authorized to view this appraisal.'}, status=status.HTTP_403_FORBIDDEN)

    serializer = AppraisalSerializer(appraisal)
    return Response(serializer.data, status=status.HTTP_200_OK)
