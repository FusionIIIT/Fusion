"""Whether a student has stopped (alumni, withdrawn, archived, left).

A stopped student is *locked*: their academic records are kept as they are
and nobody can change them. ``ExtraInfo.user_status`` holds the status; the
System Administrator writes ALUMNI / ARCHIVED / LEFT there directly, so the
value is compared after trimming and upper-casing.
"""
from typing import Dict, Iterable, Optional

from django.db.models import Q
from django.db.models.functions import Trim, Upper
from rest_framework import status
from rest_framework.exceptions import APIException

LOCKED_STATUSES = frozenset({'ALUMNI', 'WITHDRAWN', 'ARCHIVED', 'LEFT'})

# How many students an error names before it says "and N more".
_NAMED = 3


def normalise_status(value: Optional[str]) -> str:
    return (value or '').strip().upper()


def is_locked_status(value: Optional[str]) -> bool:
    return normalise_status(value) in LOCKED_STATUSES


def status_label(value: Optional[str]) -> str:
    """'ALUMNI' -> 'Alumni', for messages and reports."""
    return normalise_status(value).title()


def locked_roll_nos(roll_nos: Iterable[str]) -> Dict[str, str]:
    """The locked students among ``roll_nos``: roll number -> status."""
    rolls = {r for r in roll_nos if r}
    if not rolls:
        return {}
    from applications.globals.models import ExtraInfo

    return dict(
        ExtraInfo.objects.filter(id__in=rolls)
        .annotate(status_norm=Upper(Trim('user_status')))
        .filter(status_norm__in=LOCKED_STATUSES)
        .values_list('id', 'status_norm')
    )


def exclude_locked(students):
    """A ``Student`` queryset without the locked students."""
    return students.annotate(
        _status_norm=Upper(Trim('id__user_status'))
    ).exclude(Q(_status_norm__in=LOCKED_STATUSES))


class StudentLocked(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = 'student_locked'
    default_detail = 'This student has stopped; their records cannot be changed.'


def assert_unlocked(roll_nos: Iterable[str]) -> None:
    """Raise ``StudentLocked`` if any of ``roll_nos`` is locked."""
    locked = locked_roll_nos(roll_nos)
    if not locked:
        return
    rolls = sorted(locked)
    tail = ' Restore them in System Administrator first.'
    if len(rolls) == 1:
        roll = rolls[0]
        raise StudentLocked(
            '%s is %s; their records cannot be changed.%s'
            % (roll, status_label(locked[roll]), tail))
    named = ', '.join('%s (%s)' % (r, status_label(locked[r])) for r in rolls[:_NAMED])
    if len(rolls) > _NAMED:
        named = '%s and %d more' % (named, len(rolls) - _NAMED)
    raise StudentLocked('%s are stopped; their records cannot be changed.%s' % (named, tail))
