"""
Utility functions for the Placement Cell Management System (PCMS).
Includes eligibility checking, policy enforcement, and helper methods.
"""
import datetime
from django.utils import timezone
from django.db.models import Q

from applications.academic_information.models import Student
from applications.globals.models import ExtraInfo
from .models import (
    JobPosting, JobApplication, JobOffer, Has, Skill,
    StudentPlacement, PlacementPolicy, Constants
)


def check_eligibility(student, job_posting):
    """
    Validates whether a student is eligible to apply for a given job posting.
    Returns (is_eligible: bool, reasons: list[str])
    """
    reasons = []

    # 1. Check if student is debarred
    try:
        sp = StudentPlacement.objects.get(unique_id=student)
        if sp.debar == 'DEBAR':
            reasons.append("You are currently debarred from placement activities.")
            return False, reasons
    except StudentPlacement.DoesNotExist:
        pass

    # 2. Check CPI
    if job_posting.min_cpi and student.cpi < job_posting.min_cpi:
        reasons.append(
            "Minimum CPI required: {}. Your CPI: {}.".format(job_posting.min_cpi, student.cpi)
        )

    # 3. Check programme eligibility
    if job_posting.eligible_programmes:
        eligible_progs = [p.strip().upper() for p in job_posting.eligible_programmes.split(',')]
        student_prog = student.programme.upper() if student.programme else ''
        if student_prog and student_prog not in eligible_progs:
            reasons.append(
                "Your programme ({}) is not eligible. Eligible: {}.".format(
                    student.programme, job_posting.eligible_programmes
                )
            )

    # 4. Check branch/department eligibility
    if job_posting.eligible_branches:
        eligible_branches = [b.strip().upper() for b in job_posting.eligible_branches.split(',')]
        try:
            student_dept = student.id.department.name.upper() if student.id.department else ''
        except Exception:
            student_dept = ''

        # Also check specialization for M.Tech
        student_spec = student.specialization.upper() if student.specialization else ''

        if student_dept and student_dept not in eligible_branches:
            if not (student_spec and student_spec in eligible_branches):
                reasons.append(
                    "Your branch/department is not eligible. Eligible: {}.".format(
                        job_posting.eligible_branches
                    )
                )

    # 5. Check batch eligibility
    if job_posting.eligible_batch_from and student.batch < job_posting.eligible_batch_from:
        reasons.append(
            "Minimum batch year: {}. Your batch: {}.".format(
                job_posting.eligible_batch_from, student.batch
            )
        )
    if job_posting.eligible_batch_to and student.batch > job_posting.eligible_batch_to:
        reasons.append(
            "Maximum batch year: {}. Your batch: {}.".format(
                job_posting.eligible_batch_to, student.batch
            )
        )

    # 6. Check required skills
    if job_posting.required_skills.exists():
        student_skills = Has.objects.filter(unique_id=student).values_list('skill_id', flat=True)
        required_skill_ids = job_posting.required_skills.values_list('id', flat=True)
        missing_skills = set(required_skill_ids) - set(student_skills)
        if missing_skills:
            missing_names = Skill.objects.filter(id__in=missing_skills).values_list('skill', flat=True)
            reasons.append(
                "Missing required skills: {}.".format(', '.join(missing_names))
            )

    # 7. Check application deadline
    if job_posting.is_deadline_passed:
        reasons.append("Application deadline has passed.")

    # 8. Check if job is active
    if not job_posting.is_active:
        reasons.append("This job posting is no longer active.")

    is_eligible = len(reasons) == 0
    return is_eligible, reasons


def check_duplicate_application(student, job_posting):
    """
    Check if a student has already applied for this job posting.
    Returns True if duplicate exists.
    """
    return JobApplication.objects.filter(
        student=student, job_posting=job_posting
    ).exists()


def check_placement_policy(student, job_posting):
    """
    Enforce placement policies (e.g., max offers, dream company rules).
    Returns (can_apply: bool, reason: str)
    """
    active_policy = PlacementPolicy.objects.filter(is_active=True).first()
    if not active_policy:
        return True, ""

    # Check if student already has max offers accepted
    accepted_offers_count = JobOffer.objects.filter(
        application__student=student,
        status='ACCEPTED'
    ).count()

    if accepted_offers_count >= active_policy.max_offers_allowed:
        # Check dream company exception
        if active_policy.allow_dream_company and job_posting.ctc >= active_policy.dream_ctc_threshold:
            return True, ""
        return False, "You have already accepted {} offer(s). Maximum allowed: {}.".format(
            accepted_offers_count, active_policy.max_offers_allowed
        )

    return True, ""


def expire_pending_offers():
    """
    Utility to mark pending offers as expired if the deadline has passed.
    Should be called periodically (e.g., via celery task or management command).
    """
    expired = JobOffer.objects.filter(
        status='PENDING',
        response_deadline__lt=timezone.now()
    ).update(status='EXPIRED')
    return expired


def get_placement_statistics(year=None):
    """
    Generate aggregated placement statistics.
    Returns a dict with placement data.
    """
    from django.db.models import Avg, Count, Max, Min, Sum

    filters = {}
    if year:
        filters['application__job_posting__created_at__year'] = year

    offers = JobOffer.objects.filter(status='ACCEPTED', **filters)

    stats = {
        'total_offers': offers.count(),
        'avg_ctc': offers.aggregate(avg=Avg('ctc_offered'))['avg'] or 0,
        'max_ctc': offers.aggregate(max=Max('ctc_offered'))['max'] or 0,
        'min_ctc': offers.aggregate(min=Min('ctc_offered'))['min'] or 0,
        'total_ctc': offers.aggregate(total=Sum('ctc_offered'))['total'] or 0,
    }

    # Company-wise stats
    stats['company_wise'] = offers.values(
        'application__job_posting__company__name'
    ).annotate(
        count=Count('id'),
        avg_package=Avg('ctc_offered')
    ).order_by('-count')

    # Branch-wise stats
    stats['branch_wise'] = offers.values(
        'application__student__id__department__name'
    ).annotate(
        count=Count('id'),
        avg_package=Avg('ctc_offered')
    ).order_by('-count')

    # Programme-wise stats
    stats['programme_wise'] = offers.values(
        'application__student__programme'
    ).annotate(
        count=Count('id'),
        avg_package=Avg('ctc_offered')
    ).order_by('-count')

    return stats


def get_student_application_summary(student):
    """
    Get a summary of a student's placement applications.
    """
    applications = JobApplication.objects.filter(student=student).select_related(
        'job_posting', 'job_posting__company'
    )

    summary = {
        'total': applications.count(),
        'applied': applications.filter(status='APPLIED').count(),
        'shortlisted': applications.filter(status='SHORTLISTED').count(),
        'interview_scheduled': applications.filter(status='INTERVIEW_SCHEDULED').count(),
        'offer_extended': applications.filter(status='OFFER_EXTENDED').count(),
        'offer_accepted': applications.filter(status='OFFER_ACCEPTED').count(),
        'offer_rejected': applications.filter(status='OFFER_REJECTED').count(),
        'rejected': applications.filter(status='REJECTED').count(),
        'applications': applications,
    }
    return summary

