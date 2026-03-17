"""
REST API views for the Placement Cell Management System (PCMS).
Provides ViewSet-based endpoints for companies, job postings, applications, offers, and announcements.
"""
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q

from applications.globals.models import ExtraInfo, HoldsDesignation
from applications.academic_information.models import Student
from applications.placement_cell.models import (
    Company, JobPosting, JobApplication, InterviewSchedule,
    InterviewPanel, JobOffer, Announcement, PlacementPolicy
)
from applications.placement_cell.api.serializers import (
    CompanySerializer, CompanyListSerializer,
    JobPostingSerializer, JobPostingListSerializer,
    JobApplicationSerializer,
    InterviewScheduleSerializer, InterviewPanelSerializer,
    JobOfferSerializer,
    AnnouncementSerializer,
    PlacementPolicySerializer,
)
from applications.placement_cell.utils import (
    check_eligibility, check_duplicate_application,
    check_placement_policy, get_placement_statistics,
    get_student_application_summary,
)


def _is_tpo_or_chairman(user):
    """Check if user is TPO or Placement Chairman."""
    return HoldsDesignation.objects.filter(
        Q(working=user, designation__name="placement officer") |
        Q(working=user, designation__name="placement chairman")
    ).exists()


def _is_student(user):
    """Check if user is a student."""
    return HoldsDesignation.objects.filter(
        Q(working=user, designation__name="student")
    ).exists()


class CompanyViewSet(viewsets.ModelViewSet):
    """API endpoint for Company CRUD."""
    permission_classes = [IsAuthenticated]
    serializer_class = CompanySerializer
    queryset = Company.objects.all()

    def get_queryset(self):
        if _is_tpo_or_chairman(self.request.user):
            return Company.objects.all()
        return Company.objects.filter(approval_status='APPROVED')

    def get_serializer_class(self):
        if self.action == 'list':
            return CompanyListSerializer
        return CompanySerializer

    def perform_create(self, serializer):
        serializer.save(registered_by=self.request.user)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        if not _is_tpo_or_chairman(request.user):
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        company = self.get_object()
        company.approval_status = 'APPROVED'
        company.approved_by = request.user
        company.save()
        return Response({'status': 'approved'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        if not _is_tpo_or_chairman(request.user):
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        company = self.get_object()
        company.approval_status = 'REJECTED'
        company.approved_by = request.user
        company.save()
        return Response({'status': 'rejected'})


class JobPostingViewSet(viewsets.ModelViewSet):
    """API endpoint for Job Posting CRUD."""
    permission_classes = [IsAuthenticated]
    serializer_class = JobPostingSerializer
    queryset = JobPosting.objects.all()

    def get_queryset(self):
        if _is_tpo_or_chairman(self.request.user):
            return JobPosting.objects.select_related('company').all()
        return JobPosting.objects.select_related('company').filter(is_active=True)

    def get_serializer_class(self):
        if self.action == 'list':
            return JobPostingListSerializer
        return JobPostingSerializer

    def perform_create(self, serializer):
        if not _is_tpo_or_chairman(self.request.user):
            raise PermissionError("Not authorized")
        serializer.save(posted_by=self.request.user)

    @action(detail=True, methods=['get'])
    def check_eligibility(self, request, pk=None):
        """Student checks eligibility for a posting."""
        posting = self.get_object()
        profile = get_object_or_404(ExtraInfo, user=request.user)
        try:
            student = Student.objects.get(id=profile)
        except Student.DoesNotExist:
            return Response({'error': 'Student profile not found'}, status=404)

        is_eligible, reasons = check_eligibility(student, posting)
        can_apply, policy_reason = check_placement_policy(student, posting)
        has_applied = check_duplicate_application(student, posting)

        return Response({
            'eligible': is_eligible,
            'reasons': reasons,
            'policy_check': can_apply,
            'policy_reason': policy_reason,
            'already_applied': has_applied,
        })

    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        """Student applies for a job."""
        posting = self.get_object()
        profile = get_object_or_404(ExtraInfo, user=request.user)
        try:
            student = Student.objects.get(id=profile)
        except Student.DoesNotExist:
            return Response({'error': 'Student profile not found'}, status=404)

        if check_duplicate_application(student, posting):
            return Response({'error': 'Already applied'}, status=400)

        is_eligible, reasons = check_eligibility(student, posting)
        if not is_eligible:
            return Response({'error': 'Not eligible', 'reasons': reasons}, status=400)

        can_apply, policy_reason = check_placement_policy(student, posting)
        if not can_apply:
            return Response({'error': policy_reason}, status=400)

        application = JobApplication.objects.create(
            job_posting=posting,
            student=student,
            status='APPLIED',
        )
        return Response(
            JobApplicationSerializer(application).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['get'])
    def applications(self, request, pk=None):
        """TPO gets all applications for a posting."""
        if not _is_tpo_or_chairman(request.user):
            return Response({'error': 'Not authorized'}, status=403)
        posting = self.get_object()
        apps = posting.applications.select_related('student', 'student__id__user')
        return Response(JobApplicationSerializer(apps, many=True).data)


class JobApplicationViewSet(viewsets.ModelViewSet):
    """API endpoint for managing applications."""
    permission_classes = [IsAuthenticated]
    serializer_class = JobApplicationSerializer
    queryset = JobApplication.objects.all()

    def get_queryset(self):
        user = self.request.user
        if _is_tpo_or_chairman(user):
            return JobApplication.objects.all()
        profile = get_object_or_404(ExtraInfo, user=user)
        try:
            student = Student.objects.get(id=profile)
            return JobApplication.objects.filter(student=student)
        except Student.DoesNotExist:
            return JobApplication.objects.none()

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """TPO updates application status."""
        if not _is_tpo_or_chairman(request.user):
            return Response({'error': 'Not authorized'}, status=403)
        application = self.get_object()
        new_status = request.data.get('status')
        remarks = request.data.get('remarks', '')
        if new_status:
            application.status = new_status
            if remarks:
                application.remarks = remarks
            application.save()
        return Response(JobApplicationSerializer(application).data)


class JobOfferViewSet(viewsets.ModelViewSet):
    """API endpoint for managing offers."""
    permission_classes = [IsAuthenticated]
    serializer_class = JobOfferSerializer
    queryset = JobOffer.objects.all()

    def get_queryset(self):
        user = self.request.user
        if _is_tpo_or_chairman(user):
            return JobOffer.objects.all()
        profile = get_object_or_404(ExtraInfo, user=user)
        try:
            student = Student.objects.get(id=profile)
            return JobOffer.objects.filter(application__student=student)
        except Student.DoesNotExist:
            return JobOffer.objects.none()

    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        """Student accepts or rejects an offer."""
        offer = self.get_object()
        action_type = request.data.get('action')
        if offer.status != 'PENDING':
            return Response({'error': 'Offer already {}'.format(offer.status)}, status=400)

        from django.utils import timezone
        if action_type == 'accept':
            offer.status = 'ACCEPTED'
            offer.responded_at = timezone.now()
            offer.save()
            offer.application.status = 'OFFER_ACCEPTED'
            offer.application.save()
            return Response({'status': 'accepted'})
        elif action_type == 'reject':
            offer.status = 'REJECTED'
            offer.responded_at = timezone.now()
            offer.save()
            offer.application.status = 'OFFER_REJECTED'
            offer.application.save()
            return Response({'status': 'rejected'})
        return Response({'error': 'Invalid action'}, status=400)


class AnnouncementViewSet(viewsets.ModelViewSet):
    """API endpoint for announcements."""
    permission_classes = [IsAuthenticated]
    serializer_class = AnnouncementSerializer
    queryset = Announcement.objects.filter(is_active=True)

    def perform_create(self, serializer):
        if not _is_tpo_or_chairman(self.request.user):
            raise PermissionError("Not authorized")
        serializer.save(created_by=self.request.user)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def placement_stats_api(request):
    """Get placement statistics."""
    year = request.query_params.get('year')
    stats = get_placement_statistics(year=year)
    return Response(stats)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_application_summary_api(request):
    """Get current student's application summary."""
    profile = get_object_or_404(ExtraInfo, user=request.user)
    try:
        student = Student.objects.get(id=profile)
    except Student.DoesNotExist:
        return Response({'error': 'Student not found'}, status=404)

    summary = get_student_application_summary(student)
    # Remove queryset from summary for JSON serialization
    apps = JobApplicationSerializer(summary.pop('applications'), many=True).data
    summary['applications'] = apps
    return Response(summary)

