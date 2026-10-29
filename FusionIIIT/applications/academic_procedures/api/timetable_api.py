"""
Timetable API Views
===================
REST endpoints for the Whole-College Semester Timetable Generation System.

All endpoints live under /academic-procedures/api/timetable/…
and are registered in applications/academic_procedures/api/urls.py.

Endpoint summary
----------------
POST   /timetable/generate/              – Trigger full-college solver
GET    /timetable/versions/              – List TimetableVersion records
GET    /timetable/slots/                 – Filtered slot list (cohort/faculty)
POST   /timetable/slot/override/         – Move / override a single slot
PATCH  /timetable/version/<id>/publish/  – Publish a Draft/Approved version
GET    /timetable/my-schedule/           – Personalised schedule (WF-02)
GET    /timetable/room-utilization/      – Room heatmap
GET    /timetable/classrooms/            – List classrooms (CRUD seed)
POST   /timetable/classrooms/            – Create a classroom
GET    /timetable/classrooms/<room_id>/  – Single classroom detail
PATCH  /timetable/classrooms/<room_id>/  – Update classroom
GET    /timetable/weekly-requirements/   – List CourseWeeklyRequirement
POST   /timetable/weekly-requirements/   – Upsert CourseWeeklyRequirement
GET    /timetable/elective-baskets/      – List ElectiveBasket records
POST   /timetable/elective-baskets/      – Create ElectiveBasket
GET    /timetable/faculty-preferences/   – List FacultyPreference records
POST   /timetable/faculty-preferences/   – Create/update faculty preference
"""

from __future__ import annotations

import logging
from collections import defaultdict

from django.db import transaction
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from applications.academic_procedures.solver.timetable_solver import (
    DAYS, HOURS, STUDENT_PROGRAMME_ALIASES, WHOLE_BATCH_BRANCH,
    count_cohort_students, effective_cohort_size, eligible_room_types,
    student_programmes_for, valid_block_starts,
)

from applications.academic_procedures.api.timetable_validation import (
    MAX_TIMEOUT_SECONDS, POSITIVE_SMALLINT_MAX, PREFERRED_ROOM_TYPES,
    SEMESTER_TYPES, clean_classroom_fields, clean_room_id, clean_str,
    parse_bool, parse_int,
)
from applications.academic_procedures.api.timetable_workflow import plan_publication

logger = logging.getLogger(__name__)


def _bad_request(message):
    return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)

# ── Helper: get the designated role ─────────────────────────────────────────

def _has_role(request, *roles):
    """Return True if the logged-in user holds any of the given designation names."""
    from applications.globals.models import HoldsDesignation
    return HoldsDesignation.objects.filter(
        working=request.user,
        designation__name__in=roles,
    ).exists()


def _is_acadadmin(request):
    return _has_role(request, 'acadadmin', 'Associate Dean Academic Affairs', 'Dean Academic')


def _is_dean(request):
    return _has_role(request, 'Dean Academic', 'Associate Dean Academic Affairs')


def _is_faculty(request):
    return _has_role(request, 'faculty', 'Professor', 'Associate Professor', 'Assistant Professor')


def _can_view_unpublished(request):
    """Draft / review versions are internal to the academic office."""
    return _is_acadadmin(request) or _is_dean(request)


def _latest_published_version(request):
    """Latest published version, optionally narrowed by ?academic_year= and
    ?semester_type= (each term has its own published version).

    version_number restarts in every term, so it cannot rank versions of
    different terms; the most recently created one wins instead.
    Raises ValueError for a malformed academic_year.
    """
    from applications.academic_procedures.models import TimetableVersion

    qs = TimetableVersion.objects.filter(status='Published')
    academic_year = request.query_params.get('academic_year')
    semester_type = request.query_params.get('semester_type')
    if academic_year:
        qs = qs.filter(academic_year=parse_int(academic_year, 'academic_year'))
    if semester_type:
        qs = qs.filter(semester_type=semester_type)
    return qs.order_by('-academic_year', '-id').first()


def _resolve_version_id(request):
    """Return (version_id, error_response) for a ?version_id= query.

    Without a version_id the latest published version is used.  Anyone may
    read a published version; other versions need an academic-office role.
    """
    from applications.academic_procedures.models import TimetableVersion

    raw = request.query_params.get('version_id')
    if not raw:
        try:
            published = _latest_published_version(request)
        except ValueError as exc:
            return None, _bad_request(str(exc))
        return (published.id if published else None), None
    try:
        version_id = parse_int(raw, 'version_id')
    except ValueError as exc:
        return None, _bad_request(str(exc))
    version = TimetableVersion.objects.filter(pk=version_id).first()
    if version is None:
        return None, Response({'error': f'TimetableVersion {version_id} not found.'},
                              status=status.HTTP_404_NOT_FOUND)
    if version.status != 'Published' and not _can_view_unpublished(request):
        return None, Response({'error': 'This timetable version is not published.'},
                              status=status.HTTP_403_FORBIDDEN)
    return version_id, None


# ═══════════════════════════════════════════════════════════════════════════ #
# POST /timetable/generate/                                                   #
# ═══════════════════════════════════════════════════════════════════════════ #

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_timetable(request):
    """
    Trigger whole-college OR-Tools CP-SAT solver.

    Payload::

        {
          "academic_year": 2026,
          "semester_type": "Odd Semester",
          "timeout_seconds": 60        // optional, default 60
        }

    Returns 200 with version_id and metrics on success, 422 on infeasibility,
    400 on bad input, 403 on permission failure.
    """
    if not _is_acadadmin(request):
        return Response(
            {'error': 'Only acadadmin or Dean Academic may generate timetables.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    academic_year = request.data.get('academic_year')
    semester_type = request.data.get('semester_type', 'Odd Semester')

    if not academic_year:
        return Response(
            {'error': 'academic_year is required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        academic_year = parse_int(academic_year, 'academic_year', minimum=2000, maximum=2100)
        timeout_seconds = parse_int(
            request.data.get('timeout_seconds', 60), 'timeout_seconds',
            minimum=1, maximum=MAX_TIMEOUT_SECONDS,
        )
    except ValueError as exc:
        return _bad_request(str(exc))

    if semester_type not in SEMESTER_TYPES:
        return Response(
            {'error': f'semester_type must be one of {SEMESTER_TYPES}.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        from applications.academic_procedures.solver.timetable_solver import (
            WholeCollegeTimetableSolver,
        )
        solver = WholeCollegeTimetableSolver(
            academic_year=academic_year,
            semester_type=semester_type,
            created_by=request.user,
        )
        result = solver.solve(timeout_seconds=timeout_seconds)
    except Exception as exc:
        logger.exception('Solver raised an unexpected exception: %s', exc)
        return Response(
            {'error': 'Solver internal error; details are in the server log.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if result.status in ('OPTIMAL', 'FEASIBLE'):
        return Response({
            'status': 'success',
            'solver_status': result.status,
            'version_id': result.version_id,
            'slots_created': result.slots_created,
            'solve_time_sec': round(result.solve_time_sec, 2),
            'message': result.message,
        }, status=status.HTTP_200_OK)

    elif result.status == 'INFEASIBLE':
        return Response({
            'status': 'infeasible',
            'version_id': result.version_id,
            'message': result.message,
            'conflicts': result.conflicts,
        }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    elif result.status == 'TIMEOUT':
        # Not proven infeasible: the client should retry with more time.
        return Response({
            'status': 'timeout',
            'version_id': result.version_id,
            'message': result.message,
        }, status=status.HTTP_504_GATEWAY_TIMEOUT)

    else:
        return Response(
            {'status': 'error', 'message': result.message},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ═══════════════════════════════════════════════════════════════════════════ #
# GET /timetable/versions/                                                    #
# ═══════════════════════════════════════════════════════════════════════════ #

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_timetable_versions(request):
    """Return TimetableVersion records, optionally filtered by academic_year.

    Users outside the academic office only see published versions.
    """
    from applications.academic_procedures.models import TimetableVersion

    qs = TimetableVersion.objects.all()
    if not _can_view_unpublished(request):
        qs = qs.filter(status='Published')
    academic_year = request.query_params.get('academic_year')
    if academic_year:
        try:
            qs = qs.filter(academic_year=parse_int(academic_year, 'academic_year'))
        except ValueError as exc:
            return _bad_request(str(exc))

    data = [
        {
            'id': v.id,
            'academic_year': v.academic_year,
            'semester_type': v.semester_type,
            'version_number': v.version_number,
            'status': v.status,
            'slots_created': v.slots_created,
            'solve_time_seconds': v.solve_time_seconds,
            'created_at': v.created_at.isoformat(),
            'created_by': v.created_by.username if v.created_by else None,
            'remarks': v.remarks,
        }
        for v in qs.order_by('-academic_year', '-version_number')
    ]
    return Response(data)


# ═══════════════════════════════════════════════════════════════════════════ #
# GET /timetable/slots/                                                       #
# ═══════════════════════════════════════════════════════════════════════════ #

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_timetable_slots(request):
    """
    Return slots for a version, filtered by cohort or faculty.

    Query params: version_id, batch, programme, branch, section,
                  faculty_ci_id, day_of_week; without version_id,
                  academic_year / semester_type pick the published term.
    """
    from applications.academic_procedures.models import TimetableSlot

    version_id, error = _resolve_version_id(request)
    if error:
        return error
    if version_id is None:
        return Response([])

    qs = TimetableSlot.objects.filter(version_id=version_id).select_related(
        'curriculum__course_id',
        'curriculum_instructor__instructor_id__user',
        'classroom',
    )

    for param, field, is_int in [
        ('batch', 'batch', True),
        ('programme', 'programme', False),
        ('branch', 'branch', False),
        ('section', 'section', False),
        ('day_of_week', 'day_of_week', True),
    ]:
        val = request.query_params.get(param)
        if val:
            if is_int:
                try:
                    val = parse_int(val, param)
                except ValueError as exc:
                    return _bad_request(str(exc))
            qs = qs.filter(**{field: val})

    faculty_ci = request.query_params.get('faculty_ci_id')
    if faculty_ci:
        try:
            qs = qs.filter(curriculum_instructor_id=parse_int(faculty_ci, 'faculty_ci_id'))
        except ValueError as exc:
            return _bad_request(str(exc))

    data = []
    for slot in qs.order_by('day_of_week', 'start_hour'):
        instructor_name = ''
        if slot.curriculum_instructor and slot.curriculum_instructor.instructor_id:
            u = slot.curriculum_instructor.instructor_id.user
            instructor_name = u.get_full_name() or u.username

        data.append({
            'id': slot.id,
            'version_id': slot.version_id,
            'course_code': slot.curriculum.course_code,
            'course_name': slot.curriculum.course_id.course_name,
            'faculty': instructor_name,
            'classroom': slot.classroom_id,
            'classroom_type': slot.classroom.room_type,
            'batch': slot.batch,
            'programme': slot.programme,
            'branch': slot.branch,
            'section': slot.section,
            'day': slot.day_of_week,
            'start_time': slot.start_time,
            'end_time': slot.end_time,
            'slot_type': slot.slot_type,
            'is_locked': slot.is_locked,
        })

    return Response(data)


# ═══════════════════════════════════════════════════════════════════════════ #
# POST /timetable/slot/override/                                              #
# ═══════════════════════════════════════════════════════════════════════════ #

def _override_conflicts(slot, version, block, new_day, new_hours, new_room):
    """Hard-constraint violations a manual move would create (same rules as the solver)."""
    from applications.academic_procedures.models import (
        CourseWeeklyRequirement, ElectiveBasketCurriculum, TimetableSlot,
    )
    from applications.academic_information.models import Curriculum_Instructor, Student

    conflicts = []
    when = f'day={new_day} hour(s)={new_hours}'
    others = TimetableSlot.objects.filter(
        version=version, day_of_week=new_day, start_hour__in=new_hours,
    ).exclude(pk__in=[s.pk for s in block])

    if not new_room.is_active:
        conflicts.append({'type': 'ROOM_INACTIVE',
                          'detail': f'Room {new_room.room_id} is not active.'})

    if others.filter(classroom_id=new_room.room_id).exists():
        conflicts.append({'type': 'ROOM_CLASH',
                          'detail': f'Room {new_room.room_id} is already occupied at {when}.'})

    # Every instructor of this course, as a person, across all their courses.
    teachers = Curriculum_Instructor.objects.filter(
        curriculum_id=slot.curriculum_id,
    ).values('instructor_id')
    taught_by_them = Curriculum_Instructor.objects.filter(
        instructor_id__in=teachers,
    ).values('curriculum_id')
    if others.filter(curriculum_id__in=taught_by_them).exists():
        conflicts.append({'type': 'FACULTY_CLASH',
                          'detail': f'An instructor of this course has another class at {when}.'})

    # 'Common' spans all branches and '' spans all sections, as in the solver.
    same_students = Q(batch=slot.batch, programme=slot.programme)
    if slot.branch != WHOLE_BATCH_BRANCH:
        same_students &= Q(branch=slot.branch) | Q(branch=WHOLE_BATCH_BRANCH)
    if slot.section:
        same_students &= Q(section=slot.section) | Q(section='')
    if others.filter(same_students).exists():
        conflicts.append({
            'type': 'COHORT_CLASH',
            'detail': (
                f'Cohort {slot.batch}/{slot.programme}/{slot.branch}/{slot.section} '
                f'has another class at {when}.'
            ),
        })

    in_basket = ElectiveBasketCurriculum.objects.filter(
        curriculum_id=slot.curriculum_id,
        basket__academic_year=version.academic_year,
        basket__semester_type=version.semester_type,
    ).exists()
    if in_basket:
        conflicts.append({
            'type': 'ELECTIVE_BASKET',
            'detail': ('This course is in an elective basket whose courses must run '
                       'at the same hours; regenerate the timetable instead.'),
        })

    requirement = CourseWeeklyRequirement.objects.filter(curriculum_id=slot.curriculum_id).first()
    allowed_types = eligible_room_types(
        slot.slot_type, requirement.preferred_room_type if requirement else 'any',
    )
    if allowed_types and new_room.room_type not in allowed_types:
        conflicts.append({
            'type': 'ROOM_TYPE',
            'detail': f'{slot.slot_type} needs a room of type {allowed_types}, '
                      f'not {new_room.room_type}.',
        })

    cohort_sizes = count_cohort_students(
        Student.objects.filter(batch=slot.batch,
                               programme__in=student_programmes_for(slot.programme))
        .select_related('id__department')
    )
    needed = effective_cohort_size(
        cohort_sizes, slot.batch, slot.programme, slot.branch, slot.section,
    )
    if new_room.capacity < needed:
        conflicts.append({
            'type': 'CAPACITY',
            'detail': f'Room {new_room.room_id} capacity ({new_room.capacity}) < '
                      f'cohort size ({needed}).',
        })
    return conflicts


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def override_timetable_slot(request):
    """
    Validate and apply a manual slot move (WF-03).

    Payload::

        {
          "slot_id": 1420,
          "new_day": 3,
          "new_start_hour": 15,
          "new_room_id": "CR102",
          "lock": true
        }

    A slot that belongs to a multi-hour lab block moves the whole block, and
    ``new_start_hour`` is then the block's new first hour.

    Returns 200 on success, 409 on constraint violation, 404 if slot not found.
    """
    if not _is_acadadmin(request):
        return Response(
            {'error': 'Only acadadmin may override timetable slots.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    from applications.academic_procedures.models import (
        Classroom, TimetableSlot, TimetableVersion,
    )

    new_room_id = request.data.get('new_room_id')
    if not all([request.data.get('slot_id'), request.data.get('new_day'),
                request.data.get('new_start_hour'), new_room_id]):
        return Response(
            {'error': 'slot_id, new_day, new_start_hour, new_room_id are required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not isinstance(new_room_id, str):
        return _bad_request('new_room_id must be a string.')
    try:
        slot_id = parse_int(request.data.get('slot_id'), 'slot_id')
        new_day = parse_int(request.data.get('new_day'), 'new_day', choices=DAYS)
        new_hour = parse_int(request.data.get('new_start_hour'), 'new_start_hour',
                              choices=HOURS)
        lock = parse_bool(request.data.get('lock', False), 'lock')
    except ValueError as exc:
        return _bad_request(str(exc))

    # Validation and the move happen in one transaction with the version row
    # locked, so two concurrent overrides cannot both pass the clash checks.
    with transaction.atomic():
        try:
            slot = TimetableSlot.objects.select_related('curriculum').get(pk=slot_id)
        except TimetableSlot.DoesNotExist:
            return Response(
                {'error': f'Slot {slot_id} not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        version = TimetableVersion.objects.select_for_update().get(pk=slot.version_id)
        if version.status in ('Archived', 'Infeasible'):
            return _bad_request(f'Cannot edit a version with status={version.status}.')

        try:
            new_room = Classroom.objects.get(pk=new_room_id)
        except Classroom.DoesNotExist:
            return Response(
                {'error': f'Classroom {new_room_id} not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if slot.lab_block_id:
            block = list(TimetableSlot.objects.filter(
                version=version, lab_block_id=slot.lab_block_id,
            ).order_by('start_hour'))
        else:
            block = [slot]
        if new_hour not in valid_block_starts(len(block)):
            return _bad_request(
                f'A {len(block)}-hour block cannot start at {new_hour}:00 '
                f'(it would cross lunch or the end of the day).'
            )
        new_hours = [new_hour + offset for offset in range(len(block))]

        conflicts = _override_conflicts(slot, version, block, new_day, new_hours, new_room)
        if conflicts:
            return Response(
                {'error': 'Constraint violations detected.', 'conflicts': conflicts},
                status=status.HTTP_409_CONFLICT,
            )

        # ── Apply move ─────────────────────────────────────────────────── #
        for block_slot, hour in zip(block, new_hours):
            block_slot.day_of_week = new_day
            block_slot.start_hour = hour
            block_slot.classroom_id = new_room_id
            block_slot.is_locked = lock
            block_slot.save(update_fields=['day_of_week', 'start_hour', 'classroom_id', 'is_locked'])
        slot.refresh_from_db()

    return Response({
        'status': 'success',
        'slot_id': slot.id,
        'day': new_day,
        'start_time': slot.start_time,
        'classroom': new_room_id,
        'is_locked': lock,
    })


# ═══════════════════════════════════════════════════════════════════════════ #
# PATCH /timetable/version/<id>/publish/                                      #
# ═══════════════════════════════════════════════════════════════════════════ #

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def publish_timetable_version(request, version_id):
    """
    Promote a version to Published status (Dean Academic only).
    Archives the previously published version for the same term.
    """
    if not _is_dean(request):
        return Response(
            {'error': 'Only Dean Academic may publish timetable versions.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    from applications.academic_procedures.models import TimetableVersion

    try:
        term = TimetableVersion.objects.values('academic_year', 'semester_type').get(
            pk=int(version_id),
        )
    except TimetableVersion.DoesNotExist:
        return Response(
            {'error': f'TimetableVersion {version_id} not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Archive + publish run in one transaction holding row locks on every
    # version of the term, so two concurrent publishes of different versions
    # are serialised and the term never ends up with two published versions.
    with transaction.atomic():
        term_versions = {
            v.pk: v for v in TimetableVersion.objects.select_for_update()
            .filter(**term).order_by('pk')
        }
        version = term_versions.get(int(version_id))
        if version is None:  # deleted after the lookup above
            return Response(
                {'error': f'TimetableVersion {version_id} not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        error, archive_ids = plan_publication(
            version.pk,
            {pk: v.status for pk, v in term_versions.items()},
            version.slots.exists(),
        )
        if error:
            return _bad_request(error)
        TimetableVersion.objects.filter(pk__in=archive_ids).update(status='Archived')

        version.status = 'Published'
        version.publish_notes = request.data.get('publish_notes', '')
        version.save(update_fields=['status', 'publish_notes'])

    return Response({
        'status': 'success',
        'version_id': version.id,
        'message': f'Version {version.version_number} published for {version.semester_type} {version.academic_year}.',
    })


# ═══════════════════════════════════════════════════════════════════════════ #
# GET /timetable/my-schedule/  (WF-02)                                        #
# ═══════════════════════════════════════════════════════════════════════════ #

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_schedule(request):
    """
    Return the personalised 5-day weekly grid for the authenticated user.
    Identifies whether the user is a student or faculty from their profile.
    """
    from applications.academic_procedures.models import TimetableSlot
    from applications.academic_information.models import Student, Curriculum_Instructor
    from applications.globals.models import ExtraInfo

    # Find published version
    try:
        published = _latest_published_version(request)
    except ValueError as exc:
        return _bad_request(str(exc))
    if not published:
        return Response({'message': 'No published timetable available.', 'slots': []})

    try:
        extra = ExtraInfo.objects.get(user=request.user)
    except ExtraInfo.DoesNotExist:
        return Response({'error': 'User profile not found.'}, status=404)

    slots_qs = TimetableSlot.objects.filter(version=published).select_related(
        'curriculum__course_id',
        'curriculum_instructor__instructor_id__user',
        'classroom',
    )

    if extra.user_type == 'student':
        try:
            stu = Student.objects.get(id=extra)
        except Student.DoesNotExist:
            return Response({'slots': []})
        # Same matching as the solver's student_in_cohort: own branch and
        # whole-batch ('Common') classes, case-insensitive branch, plus the
        # (programme, branch) an aliased programme's courses are filed under.
        branch = getattr(stu.id.department, 'name', '')
        sections = ['', stu.section] if stu.section else ['']
        cohort = Q(programme=stu.programme) & (
            Q(branch__iexact=branch) | Q(branch=WHOLE_BATCH_BRANCH))
        alias = STUDENT_PROGRAMME_ALIASES.get(stu.programme)
        if alias:
            cohort |= Q(programme=alias[0], branch__iexact=alias[1])
        slots_qs = slots_qs.filter(cohort, batch=stu.batch, section__in=sections)
    elif extra.user_type == 'faculty':
        # The slot stores only the chief instructor, but the solver books every
        # instructor of a course for its hours, so match on the course.
        taught = Curriculum_Instructor.objects.filter(
            instructor_id=extra,
        ).values('curriculum_id')
        slots_qs = slots_qs.filter(curriculum_id__in=taught)
    else:
        return Response({'slots': []})

    data = []
    for slot in slots_qs.order_by('day_of_week', 'start_hour'):
        instructor_name = ''
        if slot.curriculum_instructor and slot.curriculum_instructor.instructor_id:
            u = slot.curriculum_instructor.instructor_id.user
            instructor_name = u.get_full_name() or u.username

        data.append({
            'course_code': slot.curriculum.course_code,
            'course_name': slot.curriculum.course_id.course_name,
            'faculty': instructor_name,
            'classroom': slot.classroom_id,
            'day': slot.day_of_week,
            'start_time': slot.start_time,
            'end_time': slot.end_time,
            'slot_type': slot.slot_type,
        })

    return Response({'version_id': published.id, 'slots': data})


# ═══════════════════════════════════════════════════════════════════════════ #
# GET /timetable/room-utilization/                                             #
# ═══════════════════════════════════════════════════════════════════════════ #

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def room_utilization(request):
    """
    Return a heatmap matrix (day × hour) for a given room in the latest
    published version.  Query params: room_id (required), version_id (optional).
    """
    from applications.academic_procedures.models import TimetableSlot

    room_id = request.query_params.get('room_id')
    if not room_id:
        return Response({'error': 'room_id is required.'}, status=400)

    version_id, error = _resolve_version_id(request)
    if error:
        return error
    if version_id is None:
        return Response({'matrix': {}, 'message': 'No published timetable.'})

    slots = TimetableSlot.objects.filter(
        version_id=version_id,
        classroom_id=room_id,
    ).values('day_of_week', 'start_hour', 'curriculum__course_code')

    matrix: dict = defaultdict(dict)
    for s in slots:
        day = s['day_of_week']
        hour = s['start_hour']
        matrix[day][hour] = s['curriculum__course_code']

    # Fill unused slots with None
    for day in DAYS:
        for hour in HOURS:
            if hour not in matrix[day]:
                matrix[day][hour] = None

    return Response({'room_id': room_id, 'version_id': version_id, 'matrix': matrix})


# ═══════════════════════════════════════════════════════════════════════════ #
# Classroom CRUD                                                               #
# ═══════════════════════════════════════════════════════════════════════════ #

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def classrooms(request):
    from applications.academic_procedures.models import Classroom

    if request.method == 'GET':
        data = list(Classroom.objects.values())
        return Response(data)

    if not _is_acadadmin(request):
        return Response({'error': 'Forbidden.'}, status=403)

    required = ('room_id', 'building', 'capacity', 'room_type')
    for f in required:
        if f not in request.data:
            return Response({'error': f'{f} is required.'}, status=400)

    try:
        room_id = clean_room_id(request.data['room_id'])
        fields = clean_classroom_fields(request.data, required_fields=required[1:])
    except ValueError as exc:
        return _bad_request(str(exc))

    room, created = Classroom.objects.get_or_create(
        room_id=room_id,
        defaults={
            'building': fields['building'],
            'capacity': fields['capacity'],
            'room_type': fields['room_type'],
            'has_projector': fields.get('has_projector', True),
            'is_active': fields.get('is_active', True),
        },
    )
    return Response(
        {'room_id': room.room_id, 'created': created},
        status=201 if created else 200,
    )


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def classroom_detail(request, room_id):
    from applications.academic_procedures.models import Classroom

    try:
        room = Classroom.objects.get(pk=room_id)
    except Classroom.DoesNotExist:
        return Response({'error': f'Classroom {room_id} not found.'}, status=404)

    if request.method == 'GET':
        return Response({
            'room_id': room.room_id, 'building': room.building,
            'capacity': room.capacity, 'room_type': room.room_type,
            'has_projector': room.has_projector, 'is_active': room.is_active,
        })

    if not _is_acadadmin(request):
        return Response({'error': 'Forbidden.'}, status=403)

    try:
        fields = clean_classroom_fields(request.data)
    except ValueError as exc:
        return _bad_request(str(exc))
    for field, value in fields.items():
        setattr(room, field, value)
    room.save()
    return Response({'status': 'updated', 'room_id': room.room_id})


# ═══════════════════════════════════════════════════════════════════════════ #
# CourseWeeklyRequirement CRUD                                                 #
# ═══════════════════════════════════════════════════════════════════════════ #

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def weekly_requirements(request):
    from applications.academic_procedures.models import CourseWeeklyRequirement
    from applications.academic_information.models import Curriculum

    if request.method == 'GET':
        data = list(CourseWeeklyRequirement.objects.values(
            'id', 'curriculum_id', 'lectures_per_week', 'tutorials_per_week',
            'practicals_per_week', 'practical_block_size', 'preferred_room_type',
        ))
        return Response(data)

    if not _is_acadadmin(request):
        return Response({'error': 'Forbidden.'}, status=403)

    curriculum_id = request.data.get('curriculum_id')
    if not curriculum_id:
        return Response({'error': 'curriculum_id is required.'}, status=400)

    try:
        curriculum_id = parse_int(curriculum_id, 'curriculum_id')
        # One cohort has len(DAYS) * len(HOURS) teaching hours per week.
        week = len(DAYS) * len(HOURS)
        defaults = {
            'lectures_per_week': parse_int(
                request.data.get('lectures_per_week', 3), 'lectures_per_week', 0, week),
            'tutorials_per_week': parse_int(
                request.data.get('tutorials_per_week', 1), 'tutorials_per_week', 0, week),
            'practicals_per_week': parse_int(
                request.data.get('practicals_per_week', 0), 'practicals_per_week', 0, week),
            'practical_block_size': parse_int(
                request.data.get('practical_block_size', 2), 'practical_block_size',
                choices=(2, 3)),
            'preferred_room_type': request.data.get('preferred_room_type', 'any'),
        }
    except ValueError as exc:
        return _bad_request(str(exc))
    if defaults['preferred_room_type'] not in PREFERRED_ROOM_TYPES:
        return _bad_request(f'preferred_room_type must be one of {PREFERRED_ROOM_TYPES}.')

    try:
        curr = Curriculum.objects.get(pk=curriculum_id)
    except Curriculum.DoesNotExist:
        return Response({'error': f'Curriculum {curriculum_id} not found.'}, status=404)

    req, created = CourseWeeklyRequirement.objects.update_or_create(
        curriculum=curr,
        defaults=defaults,
    )
    return Response({'id': req.id, 'curriculum_id': curr.curriculum_id, 'created': created},
                    status=201 if created else 200)


# ═══════════════════════════════════════════════════════════════════════════ #
# ElectiveBasket CRUD                                                          #
# ═══════════════════════════════════════════════════════════════════════════ #

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def elective_baskets(request):
    from applications.academic_procedures.models import (
        ElectiveBasket, ElectiveBasketCurriculum,
    )
    from applications.academic_information.models import Curriculum

    if request.method == 'GET':
        data = []
        for basket in ElectiveBasket.objects.prefetch_related('electivebasketcurriculum_set'):
            data.append({
                'id': basket.id,
                'basket_code': basket.basket_code,
                'name': basket.name,
                'semester': basket.semester,
                'programme': basket.programme,
                'academic_year': basket.academic_year,
                'semester_type': basket.semester_type,
                'curricula': list(
                    basket.electivebasketcurriculum_set.values(
                        'curriculum_id', 'max_seats',
                    )
                ),
            })
        return Response(data)

    if not _is_acadadmin(request):
        return Response({'error': 'Forbidden.'}, status=403)

    required = ('basket_code', 'name', 'semester', 'programme')
    for f in required:
        if f not in request.data:
            return Response({'error': f'{f} is required.'}, status=400)

    semester_type = request.data.get('semester_type', 'Odd Semester')
    if semester_type not in SEMESTER_TYPES:
        return _bad_request(f'semester_type must be one of {SEMESTER_TYPES}.')
    entries = request.data.get('curricula', [])
    if not isinstance(entries, list):
        return _bad_request('curricula must be a list.')
    try:
        basket_code = clean_str(request.data['basket_code'], 'basket_code', 20)
        name = clean_str(request.data['name'], 'name', 200)
        programme = clean_str(request.data['programme'], 'programme', 15)
        semester = parse_int(request.data['semester'], 'semester',
                             minimum=1, maximum=POSITIVE_SMALLINT_MAX)
        academic_year = parse_int(request.data.get('academic_year', 2026), 'academic_year',
                                  minimum=2000, maximum=2100)
        members = []
        for entry in entries:
            if not isinstance(entry, dict):
                raise ValueError('each curricula entry must be an object.')
            cur_id = parse_int(entry.get('curriculum_id'), 'curriculum_id')
            max_seats = parse_int(entry.get('max_seats', 60), 'max_seats',
                                  minimum=1, maximum=POSITIVE_SMALLINT_MAX)
            members.append((cur_id, max_seats))
    except ValueError as exc:
        return _bad_request(str(exc))

    # Unknown curricula are reported instead of silently skipped: a basket that
    # quietly loses a member would stop synchronising it.
    found = set(Curriculum.objects.filter(
        pk__in=[cur_id for cur_id, _ in members],
    ).values_list('pk', flat=True))
    unknown = [cur_id for cur_id, _ in members if cur_id not in found]
    if unknown:
        return Response({'error': f'Curricula not found: {unknown}.'}, status=404)

    with transaction.atomic():
        basket, created = ElectiveBasket.objects.get_or_create(
            basket_code=basket_code,
            defaults={
                'name': name,
                'semester': semester,
                'programme': programme,
                'academic_year': academic_year,
                'semester_type': semester_type,
            },
        )
        for cur_id, max_seats in members:
            ElectiveBasketCurriculum.objects.get_or_create(
                basket=basket, curriculum_id=cur_id,
                defaults={'max_seats': max_seats},
            )

    return Response({'id': basket.id, 'basket_code': basket.basket_code, 'created': created},
                    status=201 if created else 200)


# ═══════════════════════════════════════════════════════════════════════════ #
# FacultyPreference CRUD                                                       #
# ═══════════════════════════════════════════════════════════════════════════ #

def _own_faculty_pk(request):
    from applications.globals.models import Faculty
    faculty = Faculty.objects.filter(id__user=request.user).only('id').first()
    return faculty.pk if faculty else None


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def faculty_preferences(request):
    from applications.academic_procedures.models import FacultyPreference
    from applications.globals.models import Faculty

    is_admin = _is_acadadmin(request)
    own_faculty_pk = _own_faculty_pk(request)

    if request.method == 'GET':
        qs = FacultyPreference.objects.select_related('faculty__id__user')
        faculty_pk = request.query_params.get('faculty_id')
        if not is_admin:
            # Faculty see only their own preferences; others see none.
            faculty_pk = own_faculty_pk
            if faculty_pk is None:
                return Response([])
        if faculty_pk:
            qs = qs.filter(faculty_id=faculty_pk)
        data = [
            {
                'id': p.id,
                'faculty_id': p.faculty_id,
                'faculty_name': p.faculty.id.user.get_full_name(),
                'academic_year': p.academic_year,
                'semester_type': p.semester_type,
                'day_of_week': p.day_of_week,
                'start_hour': p.start_hour,
                'end_hour': p.end_hour,
                'preference_type': p.preference_type,
                'reason': p.reason,
            }
            for p in qs
        ]
        return Response(data)

    # POST – faculty can set their own preferences; acadadmin can set for anyone
    faculty_pk = request.data.get('faculty_id') or own_faculty_pk
    if not faculty_pk:
        return Response({'error': 'faculty_id is required.'}, status=400)
    if not is_admin and str(faculty_pk) != str(own_faculty_pk):
        return Response(
            {'error': 'You may only set your own preferences.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        fac = Faculty.objects.get(pk=faculty_pk)
    except (Faculty.DoesNotExist, ValueError):
        return Response({'error': f'Faculty {faculty_pk} not found.'}, status=404)

    required = ('day_of_week', 'start_hour', 'end_hour', 'preference_type')
    for f in required:
        if f not in request.data:
            return Response({'error': f'{f} is required.'}, status=400)

    semester_type = request.data.get('semester_type', 'Odd Semester')
    preference_type = request.data['preference_type']
    try:
        academic_year = parse_int(request.data.get('academic_year', 2026), 'academic_year',
                                   minimum=2000, maximum=2100)
        day_of_week = parse_int(request.data['day_of_week'], 'day_of_week', choices=DAYS)
        start_hour = parse_int(request.data['start_hour'], 'start_hour', choices=HOURS)
        end_hour = parse_int(request.data['end_hour'], 'end_hour', choices=HOURS)
    except ValueError as exc:
        return _bad_request(str(exc))
    if start_hour >= end_hour:
        return _bad_request('start_hour must be before end_hour.')
    if semester_type not in SEMESTER_TYPES:
        return _bad_request(f'semester_type must be one of {SEMESTER_TYPES}.')
    if preference_type not in ('Unavailable', 'Preferred'):
        return _bad_request("preference_type must be 'Unavailable' or 'Preferred'.")

    pref = FacultyPreference.objects.create(
        faculty=fac,
        academic_year=academic_year,
        semester_type=semester_type,
        day_of_week=day_of_week,
        start_hour=start_hour,
        end_hour=end_hour,
        preference_type=preference_type,
        reason=request.data.get('reason', ''),
    )
    return Response({'id': pref.id, 'status': 'created'}, status=201)


# ═══════════════════════════════════════════════════════════════════════════ #
# GET /timetable/conflict-log/                                                 #
# ═══════════════════════════════════════════════════════════════════════════ #

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def conflict_log(request):
    """Return conflict log entries for a given version_id."""
    from applications.academic_procedures.models import TimetableConflictLog

    if not _can_view_unpublished(request):
        return Response({'error': 'Forbidden.'}, status=403)

    version_id = request.query_params.get('version_id')
    if not version_id:
        return Response({'error': 'version_id is required.'}, status=400)
    try:
        version_id = parse_int(version_id, 'version_id')
    except ValueError as exc:
        return _bad_request(str(exc))

    logs = TimetableConflictLog.objects.filter(version_id=version_id)
    data = [
        {
            'id': l.id,
            'severity': l.severity,
            'error_code': l.error_code,
            'description': l.description,
            'curriculum_id_ref': l.curriculum_id_ref,
            'classroom_id_ref': l.classroom_id_ref,
            'created_at': l.created_at.isoformat(),
        }
        for l in logs
    ]
    return Response(data)
