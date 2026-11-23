"""Exam attendance sheet: the live roll list, instructors and programme scope."""
import re
from typing import Dict, FrozenSet, List, Optional, Set

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
