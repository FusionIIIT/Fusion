from django.core.exceptions import ValidationError
from django.utils import timezone

from . import selectors
from .models import (
    ChairmanVisit,
    NotifyStudent,
    PlacementRecord,
    PlacementSchedule,
    PlacementStatus,
)


def _today():
    return timezone.now().date()


def update_invitation_status(status_id, invitation):
    return (
        PlacementStatus.objects.select_related("unique_id", "notify_id")
        .filter(pk=status_id, invitation="PENDING")
        .update(invitation=invitation, timestamp=timezone.now())
    )


def delete_invitation_status(status_id):
    selectors.get_placement_status_by_pk(status_id).delete()


def delete_schedule(schedule_id):
    placement_schedule = selectors.get_schedule_by_pk(schedule_id)
    NotifyStudent.objects.get(pk=placement_schedule.notify_id.id).delete()
    placement_schedule.delete()


def create_schedule_and_notification(
    *,
    placement_type,
    company_name,
    ctc,
    description,
    placement_date,
    location,
    time,
    role_name,
    attached_file=None,
    timestamp=None,
):
    company = selectors.get_or_create_company_detail(company_name)
    role = selectors.get_or_create_role(role_name)
    placement_date_value = placement_date
    if hasattr(placement_date_value, "date"):
        placement_date_value = placement_date_value.date()
    if placement_date_value and placement_date_value < _today():
        raise ValidationError("Placement date cannot be in the past.")

    notify = NotifyStudent.objects.create(
        placement_type=placement_type,
        company_name=company_name,
        description=description,
        ctc=ctc,
        timestamp=timestamp or timezone.now(),
    )
    schedule = PlacementSchedule.objects.create(
        notify_id=notify,
        title=company_name,
        description=description,
        placement_date=placement_date,
        attached_file=attached_file,
        role=role,
        location=location,
        time=time,
        company=company,
    )
    notify.save()
    schedule.save()
    return notify, schedule


def create_placement_record(
    *,
    placement_type,
    student_name,
    ctc,
    year,
    test_type,
    test_score,
):
    record = PlacementRecord.objects.create(
        placement_type=placement_type,
        name=student_name,
        ctc=ctc,
        year=year,
        test_type=test_type,
        test_score=test_score,
    )
    record.save()
    return record


def create_chairman_visit(
    *,
    company_name,
    location,
    visiting_date,
    description,
    timestamp,
    start_date=None,
    end_date=None,
):
    record = ChairmanVisit.objects.create(
        company_name=company_name,
        location=location,
        visiting_date=visiting_date,
        start_date=start_date or visiting_date,
        end_date=end_date,
        description=description,
        timestamp=timestamp,
    )
    record.save()
    return record
