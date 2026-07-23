from datetime import date

from django.contrib.auth.models import User
from django.core.serializers import serialize
from django.db.models import Q

from applications.academic_information.models import Student
from applications.globals.models import ExtraInfo, HoldsDesignation

from .models import (
    AlumniProfile,
    ChairmanVisit,
    CompanyDetails,
    NotifyStudent,
    PlacementRecord,
    PlacementSchedule,
    PlacementStatus,
    Reference,
    Role,
)


def get_profile_for_user(user):
    return ExtraInfo.objects.get(user=user)


def get_student_for_user(user):
    profile = get_profile_for_user(user)
    return Student.objects.get(id=profile.id)


def get_designation_queryset(user, designation_name):
    return HoldsDesignation.objects.filter(
        Q(working=user, designation__name=designation_name)
    )


def get_reference_list_json(student):
    reference_objects = Reference.objects.select_related("unique_id").filter(
        unique_id=student
    )
    return serialize("json", list(reference_objects))


def get_company_names_by_prefix(current_value):
    return list(
        CompanyDetails.objects.filter(
            Q(company_name__startswith=current_value)
        ).values_list("company_name", flat=True)
    )


def get_role_names_by_prefix(current_value):
    return list(
        Role.objects.filter(Q(role__startswith=current_value)).values_list(
            "role", flat=True
        )
    )


def get_upcoming_schedule_notify_ids():
    return PlacementSchedule.objects.select_related("notify_id").filter(
        Q(placement_date__gte=date.today())
    ).values_list("notify_id", flat=True)


def get_student_upcoming_placement_status(student):
    return PlacementStatus.objects.select_related("unique_id", "notify_id").filter(
        Q(unique_id=student, notify_id__in=get_upcoming_schedule_notify_ids())
    ).order_by("-timestamp")


def get_all_schedules():
    return PlacementSchedule.objects.select_related("notify_id").all()


def get_schedule_by_pk(schedule_id):
    return PlacementSchedule.objects.select_related("notify_id").get(pk=schedule_id)


def get_placement_status_by_pk(status_id):
    return PlacementStatus.objects.select_related("unique_id", "notify_id").get(
        pk=status_id
    )


def get_or_create_company_detail(company_name):
    company_detail = CompanyDetails.objects.filter(company_name=company_name).first()
    if company_detail is None:
        company_detail = CompanyDetails.objects.create(company_name=company_name)
    return company_detail


def get_or_create_role(role_name):
    role = Role.objects.filter(role=role_name).first()
    if role is None:
        role = Role.objects.create(role=role_name)
    return role


def get_all_notify_students():
    return NotifyStudent.objects.all()


def get_all_roles():
    return Role.objects.all()


def get_all_chairman_visits():
    return ChairmanVisit.objects.all()


def delete_placement_record_by_id(record_id):
    return PlacementRecord.objects.filter(id=record_id).delete()


def get_user_by_username(username):
    return User.objects.get(username=username)


def get_alumni_profile_for_user(user):
    return AlumniProfile.objects.filter(user=user).first()


def is_student(user):
    return get_designation_queryset(user, "student").exists()


def is_alumni(user):
    return get_designation_queryset(user, "alumni").exists()


def is_tpo(user):
    return get_designation_queryset(user, "placement officer").exists() or get_designation_queryset(user, "placement chairman").exists()


def get_student_published_cpi(student_extra_info):
    """Return a student's CPI from the latest *published* semester result.

    Computes the CPI from the examination module's announced results so the
    placement cell reflects officially published academic performance rather
    than the static ``Student.cpi`` snapshot. Returns ``None`` when the
    student's batch has no announced result yet (or anything goes wrong).
    """
    try:
        from applications.examination.models import ResultAnnouncement
        from applications.examination.api.views import calculate_cpi_for_student

        student_obj = Student.objects.select_related('id').get(id=student_extra_info)

        latest = (
            ResultAnnouncement.objects
            .filter(batch=student_obj.batch_id, announced=True)
            .order_by('-semester')
            .first()
        )
        if not latest:
            return None

        cpi_value, _, _ = calculate_cpi_for_student(
            student_obj, latest.semester, latest.semester_type
        )
        return cpi_value
    except Exception:
        return None


def batches_with_published_results():
    """Batches that have at least one announced result, newest first.

    Used to populate the batch filter for the published-CPI student view.
    """
    from applications.examination.models import ResultAnnouncement
    from applications.programme_curriculum.models import Batch

    batch_ids = (
        ResultAnnouncement.objects
        .filter(announced=True)
        .values_list('batch_id', flat=True)
        .distinct()
    )
    return (
        Batch.objects
        .filter(id__in=batch_ids)
        .select_related('discipline')
        .order_by('-year', 'name')
    )
