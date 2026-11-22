"""Withdrawing a student, and re-admitting one withdrawn by mistake.

A withdrawn student is locked like an alumnus: their records stay as they are
and nobody can change them (student_lock.py). Only finished semesters are
kept, so a withdrawal waits until the semester it affects has nothing open:
no ungraded registration and no pending pre-registration or final
registration. The office clears those with its usual tools first.
"""
from typing import Dict, List, Optional

from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import APIException

from applications.academic_information.models import StudentStatusHistory
from applications.academic_information.student_status import normalise_status, status_label


class WithdrawalRefused(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'withdrawal_refused'

    def __init__(self, detail, blockers: Optional[Dict[str, list]] = None):
        super().__init__(detail)
        self.blockers = blockers


def withdrawal_blockers(student) -> Dict[str, List]:
    """What is still open in the student's current semester (or later):
    registrations without a grade, grades not yet verified (verification saves
    every row of the course, and a locked student's row would stop it for the
    whole class), pre-registration choices, and final registrations not yet
    verified."""
    from applications.academic_procedures.models import (
        FinalRegistration, InitialRegistration, course_registration,
    )
    from applications.examination.models import Student_grades

    current = student.curr_semester_no or 1
    submitted, verified = set(), set()
    for course_id, year, is_verified in Student_grades.objects.filter(
            roll_no=student.id_id).values_list('course_id_id', 'academic_year', 'verified'):
        submitted.add((course_id, year))
        if is_verified:
            verified.add((course_id, year))
    registrations = list(course_registration.objects.filter(
        student_id=student, semester_id__semester_no__gte=current,
    ).values_list('course_id_id', 'session', 'course_id__code', 'semester_id__semester_no'))
    ungraded = sorted({code for course_id, session, code, _ in registrations
                       if (course_id, session) not in submitted})
    unverified = sorted({code for course_id, session, code, _ in registrations
                         if (course_id, session) in submitted
                         and (course_id, session) not in verified})
    registered = {semester for *_, semester in registrations}
    # Choices for a later semester, or for the current one before the
    # student has been registered into it (a new batch, PG registering into
    # the semester they are in).
    pre = sorted({semester for semester in InitialRegistration.objects.filter(
        student_id=student, semester_id__semester_no__gte=current,
    ).values_list('semester_id__semester_no', flat=True)
        if semester > current or semester not in registered})
    final = sorted(set(FinalRegistration.objects.filter(
        student_id=student, verified=False, semester_id__semester_no__gte=current,
    ).values_list('semester_id__semester_no', flat=True)))
    return {'ungraded': ungraded, 'unverified': unverified,
            'pre_registration': pre, 'final_registration': final}


def _change(student, action, reason, user, expected, new_status, check=None):
    reason = (reason or '').strip()
    if not reason:
        raise WithdrawalRefused('A reason is required.')
    extra = type(student.id).objects.select_for_update().get(pk=student.id_id)
    current = normalise_status(extra.user_status) or 'PRESENT'
    if current != expected:
        raise WithdrawalRefused('%s is %s, not %s.' % (
            student.id_id, status_label(current), status_label(expected)))
    if check:
        check()
    type(extra).objects.filter(pk=extra.pk).update(user_status=new_status)
    return StudentStatusHistory.objects.create(
        student=student, action=action, previous_status=current, new_status=new_status,
        reason=reason, semester_no=student.curr_semester_no, performed_by=user)


@transaction.atomic
def withdraw(student, reason, user) -> StudentStatusHistory:
    def nothing_open():
        # Read under the row lock, so nothing slips in before the status changes.
        blockers = withdrawal_blockers(student)
        if any(blockers.values()):
            raise WithdrawalRefused(
                '%s still has an open semester. Clear these first, then withdraw.'
                % student.id_id, blockers)

    return _change(student, 'withdraw', reason, user, 'PRESENT', 'WITHDRAWN', nothing_open)


@transaction.atomic
def readmit(student, reason, user) -> StudentStatusHistory:
    return _change(student, 'readmit', reason, user, 'WITHDRAWN', 'PRESENT')
