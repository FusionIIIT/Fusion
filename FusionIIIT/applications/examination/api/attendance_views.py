"""Exam attendance sheet: courses, roll list, and saving or copying room plans."""
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import (
    api_view, authentication_classes, permission_classes)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from applications.examination.attendance_sheet import (
    PlanChanged, PlanRefused, copy_plan, course_in_scope, courses_for,
    instructor_names, plan_body, roll_list, save_plan, section_wise,
    term_year)
from applications.examination.models import ExamAttendancePlan
from applications.globals.decorators import role_required
from applications.globals.programme_scope import scopes_for
from applications.programme_curriculum.models import Course

ROLES = ['acadadmin', 'Acad UG', 'Acad PG', 'Acad Ph.D.']
EXAMS = ('MID', 'END')
NO_COURSE = 'No such course in your programmes for that term.'


class BadInput(Exception):
    pass


def _bad(message):
    return Response({'detail': message}, status=status.HTTP_400_BAD_REQUEST)


def _no_course():
    return Response({'detail': NO_COURSE}, status=status.HTTP_404_NOT_FOUND)


def _term(data):
    """(academic_year, semester_type), refusing malformed or Summer terms."""
    academic_year = data.get('academic_year')
    semester_type = data.get('semester_type')
    if semester_type not in ('Odd Semester', 'Even Semester'):
        raise BadInput('Semester type must be Odd Semester or Even Semester.')
    try:
        term_year(academic_year, semester_type)
    except ValueError:
        raise BadInput('Academic year must look like 2026-27.')
    return academic_year, semester_type


def _exam(data, key='exam'):
    exam = data.get(key)
    if exam not in EXAMS:
        raise BadInput('Exam must be MID or END.')
    return exam


def _course_id(data):
    value = data.get('course')
    if isinstance(value, bool):
        raise BadInput('Course must be a number.')
    try:
        return int(value)
    except (TypeError, ValueError):
        raise BadInput('Course must be a number.')


def _sheet_body(course, academic_year, semester_type, exam):
    plan = (ExamAttendancePlan.objects
            .filter(course=course, academic_year=academic_year,
                    semester_type=semester_type, exam=exam)
            .select_related('updated_by').first())
    return {
        'course': {'id': course.id, 'code': course.code, 'name': course.name},
        'academic_year': academic_year,
        'semester_type': semester_type,
        'exam': exam,
        'sectioned': section_wise(course, academic_year, semester_type),
        'students': roll_list(course, academic_year, semester_type),
        'instructors': instructor_names(course, academic_year, semester_type),
        'plan': plan_body(plan) if plan else None,
    }


def _course_in_reach(request, course_id, academic_year, semester_type):
    """The course, or None when it does not exist or is outside the user's programmes."""
    course = Course.objects.filter(id=course_id).first()
    if course is None or not course_in_scope(
            course, academic_year, semester_type, scopes_for(request.user)):
        return None
    return course


def _data(request):
    return request.data if hasattr(request.data, 'get') else {}


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
@role_required(ROLES)
def attendance_courses(request):
    try:
        academic_year, semester_type = _term(request.query_params)
    except BadInput as bad:
        return _bad(str(bad))
    return Response(courses_for(
        academic_year, semester_type, scopes_for(request.user)))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
@role_required(ROLES)
def attendance_sheet(request):
    params = request.query_params
    try:
        course_id = _course_id(params)
        academic_year, semester_type = _term(params)
        exam = _exam(params)
    except BadInput as bad:
        return _bad(str(bad))
    course = _course_in_reach(request, course_id, academic_year, semester_type)
    if course is None:
        return _no_course()
    return Response(_sheet_body(course, academic_year, semester_type, exam))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
@role_required(ROLES)
def attendance_save(request):
    data = _data(request)
    try:
        course_id = _course_id(data)
        academic_year, semester_type = _term(data)
        exam = _exam(data)
    except BadInput as bad:
        return _bad(str(bad))
    rooms = data.get('rooms')
    if rooms is not None and not isinstance(rooms, list):
        return _bad('Rooms must be a list.')
    course = _course_in_reach(request, course_id, academic_year, semester_type)
    if course is None:
        return _no_course()
    try:
        save_plan(course, academic_year, semester_type, exam, rooms,
                  request.user, data.get('updated_at'))
    except PlanRefused as refused:
        return Response({'detail': 'Fix these, then save.',
                         'errors': refused.errors},
                        status=status.HTTP_400_BAD_REQUEST)
    except PlanChanged as changed:
        return Response({'detail': str(changed.detail)},
                        status=status.HTTP_409_CONFLICT)
    return Response(_sheet_body(course, academic_year, semester_type, exam))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
@role_required(ROLES)
def attendance_copy(request):
    data = _data(request)
    try:
        course_id = _course_id(data)
        academic_year, semester_type = _term(data)
        from_exam = _exam(data, 'from_exam')
        to_exam = _exam(data, 'to_exam')
    except BadInput as bad:
        return _bad(str(bad))
    course = _course_in_reach(request, course_id, academic_year, semester_type)
    if course is None:
        return _no_course()
    try:
        copy_plan(course, academic_year, semester_type, from_exam, to_exam,
                  request.user, data.get('replace') is True)
    except PlanRefused as refused:
        return Response({'detail': 'Fix these, then save.',
                         'errors': refused.errors},
                        status=status.HTTP_400_BAD_REQUEST)
    except PlanChanged as changed:
        return Response({'detail': str(changed.detail), 'exists': True},
                        status=status.HTTP_409_CONFLICT)
    return Response(_sheet_body(course, academic_year, semester_type, to_exam))
