"""
Request validation for the timetable API.

Kept free of Django imports so it can be unit-tested without a database.
Each helper raises ValueError with a message that is safe to show the client.
The choice lists mirror the model choices in ``academic_procedures.models``
(``test_timetable_validation`` checks they stay in sync).
"""

import re

SEMESTER_TYPES = ('Odd Semester', 'Even Semester', 'Summer Term')
ROOM_TYPES = (
    'Lecture Hall', 'Tutorial Room', 'Computer Lab', 'Hardware Lab',
    'Mechanical Workshop', 'Seminar Room',
)
# CourseWeeklyRequirement.PREFERRED_ROOM_TYPE_CHOICES has no 'Seminar Room'.
PREFERRED_ROOM_TYPES = (
    'any', 'Lecture Hall', 'Tutorial Room', 'Computer Lab', 'Hardware Lab',
    'Mechanical Workshop',
)
MAX_TIMEOUT_SECONDS = 600

# Column limits; values past them make the database raise (a 500) on save.
POSITIVE_INT_MAX = 2147483647       # PositiveIntegerField
POSITIVE_SMALLINT_MAX = 32767       # PositiveSmallIntegerField

# Classroom.room_id max_length, restricted to what the
# classrooms/<room_id>/ URL pattern ([\w-]+) can address.
ROOM_ID_PATTERN = re.compile(r'^[\w-]{1,20}$')


def parse_int(value, name, minimum=None, maximum=None, choices=None):
    """Parse a request value as an int.

    Accepts ints, integral floats (JSON may send 9.0) and digit strings.
    Rejects booleans and fractional numbers rather than truncating them.
    """
    if isinstance(value, bool):
        raise ValueError(f'{name} must be an integer.')
    if isinstance(value, float):
        if not value.is_integer():
            raise ValueError(f'{name} must be an integer.')
        value = int(value)
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValueError(f'{name} must be an integer.')
    if minimum is not None and number < minimum:
        raise ValueError(f'{name} must be >= {minimum}.')
    if maximum is not None and number > maximum:
        raise ValueError(f'{name} must be <= {maximum}.')
    if choices is not None and number not in choices:
        raise ValueError(f'{name} must be one of {list(choices)}.')
    return number


def parse_bool(value, name):
    """Accept JSON booleans and the usual form strings; bool('false') is True."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.strip().lower() in ('true', '1', 'yes'):
        return True
    if isinstance(value, str) and value.strip().lower() in ('false', '0', 'no', ''):
        return False
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    raise ValueError(f'{name} must be true or false.')


def clean_str(value, name, max_length):
    """A non-empty, stripped string that fits its column."""
    if not isinstance(value, (str, int)) or isinstance(value, bool):
        raise ValueError(f'{name} must be text.')
    text = str(value).strip()
    if not text:
        raise ValueError(f'{name} must not be empty.')
    if len(text) > max_length:
        raise ValueError(f'{name} must be at most {max_length} characters.')
    return text


def clean_room_id(value):
    if not isinstance(value, str) or not ROOM_ID_PATTERN.match(value):
        raise ValueError('room_id must be 1-20 letters, digits, "_" or "-".')
    return value


def clean_classroom_fields(data, required_fields=()):
    """Validated subset of the editable Classroom fields present in ``data``."""
    fields = {}
    if 'building' in data:
        fields['building'] = clean_str(data['building'], 'building', 100)
    if 'capacity' in data:
        fields['capacity'] = parse_int(data['capacity'], 'capacity',
                                       minimum=1, maximum=POSITIVE_INT_MAX)
    if 'room_type' in data:
        if data['room_type'] not in ROOM_TYPES:
            raise ValueError(f'room_type must be one of {ROOM_TYPES}.')
        fields['room_type'] = data['room_type']
    for flag in ('has_projector', 'is_active'):
        if flag in data:
            fields[flag] = parse_bool(data[flag], flag)
    missing = [f for f in required_fields if f not in fields]
    if missing:
        raise ValueError(f'{missing[0]} is required.')
    return fields
