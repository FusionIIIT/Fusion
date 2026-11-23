"""Exam attendance sheet: the live roll list, instructors and programme scope."""
import datetime
import re
from typing import Dict, FrozenSet, List, Optional, Set

from django.db import transaction
from rest_framework.exceptions import APIException

from applications.academic_procedures.models import course_registration
from applications.globals.programme_scope import canonical_programme_name
from applications.programme_curriculum.models import CourseInstructor

PROGRAMME_ORDER = ('B.Tech', 'B.Des', 'M.Tech', 'M.Des', 'PhD')
_SESSION = re.compile(r'^(\d{4})-(\d{2})$')


def term_year(academic_year: str, semester_type: str) -> int:
    """The calendar year CourseInstructor.year holds for this term."""
    match = _SESSION.match(academic_year or '')
    if not match:
        raise ValueError('Malformed session: %r' % (academic_year,))
    first = int(match.group(1))
    if semester_type == 'Odd Semester':
        return first
    if semester_type == 'Even Semester':
        return first + 1
    raise ValueError('Unsupported semester type: %r' % (semester_type,))


def _offerings(course, academic_year, semester_type):
    return CourseInstructor.objects.filter(
        course_id=course, year=term_year(academic_year, semester_type),
        semester_type=semester_type)


def section_wise(course, academic_year, semester_type) -> bool:
    return any((o.section_label or '').strip() for o in
               _offerings(course, academic_year, semester_type))


def _registrations(course, academic_year, semester_type):
    return (course_registration.objects
            .filter(course_id=course, session=academic_year,
                    semester_type=semester_type)
            .select_related('student_id__id__user',
                            'student_id__batch_id__discipline',
                            'student_id__batch_id__curriculum__programme',
                            'course_instructor')
            .order_by('student_id_id', 'id'))


def _live_students(course, academic_year, semester_type):
    """(student, registration) per student, withdrawn ones left out."""
    seen = set()
    out = []
    for reg in _registrations(course, academic_year, semester_type):
        student = reg.student_id
        if student.id_id in seen:
            continue
        seen.add(student.id_id)
        if (student.id.user_status or '').upper() == 'WITHDRAWN':
            continue
        out.append((student, reg))
    return out


def roll_list(course, academic_year, semester_type) -> List[dict]:
    by_section = section_wise(course, academic_year, semester_type)
    rows = []
    for student, reg in _live_students(course, academic_year, semester_type):
        user = student.id.user
        batch = student.batch_id
        section = ''
        if by_section:
            offering = reg.course_instructor
            section = ((offering.section_label if offering else '')
                       or student.section or '').strip()
        rows.append({
            'sno': 0,
            'roll_no': student.id_id,
            'name': ('%s %s' % (user.first_name, user.last_name)).strip(),
            'discipline': (batch.discipline.acronym
                           if batch and batch.discipline else ''),
            'programme': canonical_programme_name(student.programme),
            'section': section,
        })

    def key(row):
        programme = row['programme']
        rank = (PROGRAMME_ORDER.index(programme)
                if programme in PROGRAMME_ORDER else len(PROGRAMME_ORDER))
        return (rank, programme, row['section'] == '', row['section'],
                row['roll_no'])

    rows.sort(key=key)
    for number, row in enumerate(rows, 1):
        row['sno'] = number
    return rows


def instructor_names(course, academic_year, semester_type) -> Dict:
    by_section = {}  # type: Dict[str, str]
    everyone = []  # type: List[str]
    offerings = (_offerings(course, academic_year, semester_type)
                 .select_related('instructor_id__id__user').order_by('id'))
    for offering in offerings:
        user = offering.instructor_id.id.user
        name = 'PROF. ' + ('%s %s' % (user.first_name, user.last_name)).strip().upper()
        if name not in everyone:
            everyone.append(name)
        section = (offering.section_label or '').strip()
        if section:
            by_section[section] = name
    return {'by_section': by_section, 'all': everyone}


def _category(batch):
    """Upper-cased programme category, or None when it cannot be resolved."""
    try:
        return batch.curriculum.programme.category.upper()
    except AttributeError:
        return None


def programme_categories(course, academic_year, semester_type) -> Set[Optional[str]]:
    """Categories of the live roll; None stands for a student with no category."""
    return {_category(student.batch_id) for student, _ in
            _live_students(course, academic_year, semester_type)}


def _in_scope(categories, scopes) -> bool:
    """Every student must have a resolvable category inside the scopes."""
    if scopes is None:
        return True
    allowed = {scope.upper() for scope in scopes}
    return bool(categories) and all(c in allowed for c in categories)


def course_in_scope(course, academic_year, semester_type,
                    scopes: Optional[FrozenSet[str]]) -> bool:
    if scopes is None:
        return True
    return _in_scope(
        programme_categories(course, academic_year, semester_type), scopes)


def courses_for(academic_year, semester_type, scopes) -> List[dict]:
    from applications.examination.models import ExamAttendancePlan
    from applications.programme_curriculum.models import Course

    term_year(academic_year, semester_type)  # refuses Summer / bad sessions
    term_regs = course_registration.objects.filter(
        session=academic_year, semester_type=semester_type)
    course_ids = set(term_regs.values_list('course_id', flat=True).distinct())
    categories = {}  # type: Dict[int, Set[Optional[str]]]
    if scopes is not None:
        pairs = (term_regs
                 .exclude(student_id__id__user_status__iexact='WITHDRAWN')
                 .values_list(
                     'course_id',
                     'student_id__batch_id__curriculum__programme__category')
                 .distinct())
        for course_id, category in pairs:
            categories.setdefault(course_id, set()).add(
                category.upper() if category else None)
    plans = {}
    for plan in ExamAttendancePlan.objects.filter(
            academic_year=academic_year, semester_type=semester_type,
            course_id__in=course_ids):
        plans.setdefault(plan.course_id, set()).add(plan.exam)
    result = []
    for course in Course.objects.filter(id__in=course_ids).order_by('code'):
        if not _in_scope(categories.get(course.id, set()), scopes):
            continue
        result.append({
            'id': course.id, 'code': course.code, 'name': course.name,
            'plans': [e for e in ('MID', 'END') if e in plans.get(course.id, ())],
        })
    return result


EXAM_NAMES = {'MID': 'Mid Sem', 'END': 'End Sem'}
_ROOM_REQUIRED = 'Room %d: room, date, start and end time are required.'


class PlanRefused(APIException):
    status_code = 400
    default_detail = 'Fix these, then save.'

    def __init__(self, errors):
        if isinstance(errors, str):
            errors = [errors]
        self.errors = list(errors)
        super().__init__('; '.join(self.errors))


class PlanChanged(APIException):
    status_code = 409
    default_detail = 'This plan changed.'


def validate_rooms(rooms: List[dict], roll_count: int) -> List[str]:
    if not rooms:
        return ['Add at least one room.']
    errors = []  # type: List[str]
    in_range = []  # (number, from, to) for rooms whose range is usable
    for n, r in enumerate(rooms, 1):
        if not (r.get('room') or '').strip() or not r.get('date') \
                or not r.get('start_time') or not r.get('end_time'):
            errors.append(_ROOM_REQUIRED % n)
        elif r['end_time'] <= r['start_time']:
            errors.append('Room %d: the exam must end after it starts.' % n)
        a, b = r.get('from_sno'), r.get('to_sno')
        if a is None or b is None or a < 1 or b < 1 or a > roll_count \
                or b > roll_count:
            errors.append('Room %d: S.No must be between 1 and %d.'
                          % (n, roll_count))
        elif a > b:
            errors.append('Room %d: from S.No must not be after to S.No.' % n)
        else:
            in_range.append((n, a, b))
    for i, (n, a, b) in enumerate(in_range):
        for m, c, d in in_range[i + 1:]:
            if a <= d and c <= b:
                errors.append('Rooms %d and %d overlap.' % (n, m))
    return errors


def parse_rooms(raw: List[dict]) -> List[dict]:
    rooms = []
    errors = []  # type: List[str]
    for n, item in enumerate(raw or [], 1):
        try:
            rooms.append({
                'from_sno': int(item['from_sno']),
                'to_sno': int(item['to_sno']),
                'room': str(item.get('room') or '').strip(),
                'date': datetime.date.fromisoformat(item['date']),
                'start_time': datetime.time.fromisoformat(item['start_time']),
                'end_time': datetime.time.fromisoformat(item['end_time']),
                'instructor_text': str(item.get('instructor_text') or '').strip(),
            })
        except (KeyError, TypeError, ValueError, AttributeError):
            errors.append(_ROOM_REQUIRED % n)
    if errors:
        raise PlanRefused(errors)
    return rooms


def _write_rooms(plan, rooms: List[dict]) -> None:
    from applications.examination.models import ExamAttendanceRoom

    plan.rooms.all().delete()
    ExamAttendanceRoom.objects.bulk_create([
        ExamAttendanceRoom(
            plan=plan, position=n, from_sno=r['from_sno'], to_sno=r['to_sno'],
            room=r['room'], date=r['date'], start_time=r['start_time'],
            end_time=r['end_time'], instructor_text=r['instructor_text'])
        for n, r in enumerate(rooms, 1)])


@transaction.atomic
def save_plan(course, academic_year, semester_type, exam, raw_rooms, user,
              updated_at: Optional[str]):
    from applications.examination.models import ExamAttendancePlan

    roll_count = len(roll_list(course, academic_year, semester_type))
    rooms = parse_rooms(raw_rooms)
    errors = validate_rooms(rooms, roll_count)
    if errors:
        raise PlanRefused(errors)
    plan = (ExamAttendancePlan.objects.select_for_update()
            .filter(course=course, academic_year=academic_year,
                    semester_type=semester_type, exam=exam).first())
    if plan is None:
        plan = ExamAttendancePlan(
            course=course, academic_year=academic_year,
            semester_type=semester_type, exam=exam)
    elif updated_at != plan.updated_at.isoformat():
        raise PlanChanged('Someone else saved this plan after you opened it. '
                          'Reload it, then make your changes again.')
    plan.roll_count = roll_count
    plan.updated_by = user
    plan.save()
    _write_rooms(plan, rooms)
    return plan


@transaction.atomic
def copy_plan(course, academic_year, semester_type, from_exam, to_exam, user,
              replace: bool):
    from applications.examination.models import ExamAttendancePlan

    if from_exam == to_exam:
        raise PlanRefused('Choose a different exam to copy to.')
    scope = dict(course=course, academic_year=academic_year,
                 semester_type=semester_type)
    source = ExamAttendancePlan.objects.filter(exam=from_exam, **scope).first()
    if source is None:
        raise PlanRefused('There is no %s plan to copy.'
                          % EXAM_NAMES.get(from_exam, from_exam))
    target = (ExamAttendancePlan.objects.select_for_update()
              .filter(exam=to_exam, **scope).first())
    if target is not None and not replace:
        raise PlanChanged('An %s plan already exists. Replace it?'
                          % EXAM_NAMES.get(to_exam, to_exam))
    if target is None:
        target = ExamAttendancePlan(exam=to_exam, **scope)
    target.roll_count = source.roll_count
    target.updated_by = user
    target.save()
    _write_rooms(target, [{
        'from_sno': r.from_sno, 'to_sno': r.to_sno, 'room': r.room,
        'date': r.date, 'start_time': r.start_time, 'end_time': r.end_time,
        'instructor_text': r.instructor_text} for r in source.rooms.all()])
    return target


def plan_body(plan) -> dict:
    return {
        'exam': plan.exam,
        'roll_count': plan.roll_count,
        'updated_at': plan.updated_at.isoformat(),
        'updated_by': plan.updated_by.username if plan.updated_by else None,
        'rooms': [{
            'from_sno': r.from_sno, 'to_sno': r.to_sno, 'room': r.room,
            'date': r.date.isoformat(),
            'start_time': r.start_time.strftime('%H:%M'),
            'end_time': r.end_time.strftime('%H:%M'),
            'instructor_text': r.instructor_text,
        } for r in plan.rooms.all()],
    }
