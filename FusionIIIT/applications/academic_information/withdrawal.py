"""Withdrawing a student, and re-admitting one withdrawn by mistake.

A withdrawn student is locked like an alumnus: their records stay as they are
and nobody can change them (student_lock.py). Only finished semesters are
kept, so a withdrawal waits until the semester it affects has every course
graded and every grade verified; the office clears those first. Pending
pre-registration choices and unverified course allotments have no screen to
remove them, so the withdrawal removes them itself and notes it in the
history.
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


def _pending(student):
    """The student's registrations of their current semester or later, and
    their pending pre-registration and unverified final registration rows."""
    from applications.academic_procedures.models import (
        FinalRegistration, InitialRegistration, course_registration,
    )

    current = student.curr_semester_no or 1
    registrations = list(course_registration.objects.filter(
        student_id=student, semester_id__semester_no__gte=current,
    ).values_list('course_id_id', 'session', 'course_id__code', 'semester_id__semester_no'))
    # Choices of a semester the student never got into: nothing registered
    # and no allotment verified. Choices behind a registration are history.
    taken = {semester for *_, semester in registrations} | set(
        FinalRegistration.objects.filter(
            student_id=student, verified=True, semester_id__semester_no__gte=current,
        ).values_list('semester_id__semester_no', flat=True))
    choices = InitialRegistration.objects.filter(
        student_id=student, semester_id__semester_no__gte=current,
    ).exclude(semester_id__semester_no__in=taken)
    allotments = FinalRegistration.objects.filter(
        student_id=student, verified=False, semester_id__semester_no__gte=current)
    return registrations, choices, allotments


def withdrawal_blockers(student) -> Dict[str, List[dict]]:
    """What must be cleared before a withdrawal, in the student's current
    semester or later: registrations without a grade, and grades not yet
    verified (verification saves every row of the course, and a locked
    student's row would stop it for the whole class). Each item names the
    course, its semester and its session, so the office can find it."""
    from applications.examination.models import Student_grades

    submitted, verified = set(), set()
    for course_id, year, is_verified in Student_grades.objects.filter(
            roll_no=student.id_id).values_list('course_id_id', 'academic_year', 'verified'):
        submitted.add((course_id, year))
        if is_verified:
            verified.add((course_id, year))
    registrations, _, _ = _pending(student)

    def items(keep):
        rows = {(semester, code, session) for course_id, session, code, semester in registrations
                if keep((course_id, session))}
        return [{'code': code, 'semester': semester, 'session': session}
                for semester, code, session in sorted(rows, key=lambda r: (r[0], r[1], r[2] or ''))]

    return {'ungraded': items(lambda key: key not in submitted),
            'unverified': items(lambda key: key in submitted and key not in verified)}


def withdrawal_cleanup(student) -> Dict[str, List[int]]:
    """What the withdrawal removes itself, by semester: pre-registration
    choices not yet turned into a registration, and course allotments never
    verified. No screen removes these, and a withdrawn student takes up no
    seat."""
    _, choices, allotments = _pending(student)
    return {
        'pre_registration': sorted(set(choices.values_list('semester_id__semester_no', flat=True))),
        'final_registration': sorted(set(allotments.values_list('semester_id__semester_no',
                                                                flat=True))),
    }


def _removal_note(cleanup) -> str:
    sems = lambda nos: ', '.join('semester %s' % n for n in nos)  # noqa: E731
    parts = []
    if cleanup['pre_registration']:
        parts.append('pre-registration choices for ' + sems(cleanup['pre_registration']))
    if cleanup['final_registration']:
        parts.append('course allotment not verified for ' + sems(cleanup['final_registration']))
    return 'Removed: %s.' % '; '.join(parts) if parts else ''


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
    removed = {}

    def nothing_open():
        # Read under the row lock, so nothing slips in before the status changes.
        blockers = withdrawal_blockers(student)
        if any(blockers.values()):
            raise WithdrawalRefused(
                '%s still has an open semester. Clear these first, then withdraw.'
                % student.id_id, blockers)
        removed.update(withdrawal_cleanup(student))
        _, choices, allotments = _pending(student)
        choices.delete()
        allotments.delete()

    entry = _change(student, 'withdraw', reason, user, 'PRESENT', 'WITHDRAWN', nothing_open)
    note = _removal_note(removed)
    if note:
        entry.reason = '%s\n%s' % (entry.reason, note)
        entry.save(update_fields=['reason'])
    return entry


@transaction.atomic
def readmit(student, reason, user) -> StudentStatusHistory:
    return _change(student, 'readmit', reason, user, 'WITHDRAWN', 'PRESENT')
