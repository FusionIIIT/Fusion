"""Semester drops: a student skips one semester and goes on with their batch.

For a dropped semester the student takes part in nothing: no pre-registration,
final registration, PG/PhD or Swayam registration, add request or allocation,
and the semester's lists and reports leave them out. The semester's courses
are added later by the office by hand, and recorded as Backlog.

As with a withdrawal, only an empty semester is dropped: the office first
clears that semester's registrations with its usual tools.
"""
import re
from typing import Dict, Optional, Set

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import APIException

from applications.academic_information.models import SemesterDrop

_SESSION = re.compile(r'^(\d{4})-(\d{2})$')


class DropRefused(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'drop_refused'

    def __init__(self, detail, blockers: Optional[Dict] = None):
        super().__init__(detail)
        self.blockers = blockers


def live_drops():
    return SemesterDrop.objects.filter(cancelled_at__isnull=True)


def live_drop_semesters(student) -> Set[int]:
    return set(live_drops().filter(student=student).values_list('semester_no', flat=True))


def not_dropped_q(prefix: str, semester_no) -> Q:
    """Rows whose student has no live drop for ``semester_no``. ``prefix``
    leads to the Student: ``'student_id__'`` from a registration, ``''`` from
    Student itself."""
    dropped = live_drops().filter(semester_no=semester_no).values('student_id')
    return ~Q(**{prefix + 'pk__in': dropped})


def drop_blockers(student, semester_no) -> Dict:
    """What the semester still holds: course registrations (any), and
    pre-registration or final registration rows."""
    from applications.academic_procedures.models import (
        FinalRegistration, InitialRegistration, course_registration,
    )
    in_semester = dict(student_id=student, semester_id__semester_no=semester_no)
    return {
        'registrations': sorted(set(course_registration.objects.filter(**in_semester)
                                    .values_list('course_id__code', flat=True))),
        'pre_registration': InitialRegistration.objects.filter(**in_semester).exists(),
        'final_registration': FinalRegistration.objects.filter(**in_semester).exists(),
    }


def _reason(reason):
    reason = (reason or '').strip()
    if not reason:
        raise DropRefused('A reason is required.')
    return reason


def _check_session(academic_year):
    match = _SESSION.match((academic_year or '').strip())
    if not match or (int(match.group(1)) + 1) % 100 != int(match.group(2)):
        raise DropRefused("Academic year '%s' is not a session such as 2025-26."
                          % (academic_year or ''))
    return match.group(0)


def _lock(student):
    # One change at a time per student, so the checks below hold.
    type(student).objects.select_for_update().get(pk=student.pk)


@transaction.atomic
def record_drop(student, semester_no, academic_year, reason, user) -> SemesterDrop:
    from applications.programme_curriculum.models import Semester

    reason = _reason(reason)
    academic_year = _check_session(academic_year)
    try:
        semester_no = int(semester_no)
    except (TypeError, ValueError):
        raise DropRefused("Semester '%s' is not a number." % semester_no)
    if not Semester.objects.filter(curriculum=student.batch_id.curriculum,
                                   semester_no=semester_no).exists():
        raise DropRefused('%s has no semester %s in their curriculum.'
                          % (student.id_id, semester_no))
    _lock(student)
    if live_drops().filter(student=student, semester_no=semester_no).exists():
        raise DropRefused('%s has already dropped semester %s.' % (student.id_id, semester_no))
    blockers = drop_blockers(student, semester_no)
    if any(blockers.values()):
        raise DropRefused('Semester %s of %s is not empty. Clear these first, then drop it.'
                          % (semester_no, student.id_id), blockers)
    return SemesterDrop.objects.create(
        student=student, semester_no=semester_no, academic_year=academic_year,
        reason=reason, recorded_by=user)


@transaction.atomic
def cancel_drop(student, drop_id, reason, user) -> SemesterDrop:
    reason = _reason(reason)
    _lock(student)
    drop = live_drops().filter(student=student, pk=drop_id).first()
    if drop is None:
        raise DropRefused('%s has no such live semester drop.' % student.id_id)
    drop.cancelled_by, drop.cancelled_at, drop.cancel_reason = user, timezone.now(), reason
    drop.save(update_fields=['cancelled_by', 'cancelled_at', 'cancel_reason'])
    return drop
