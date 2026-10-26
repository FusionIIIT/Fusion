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
import math
from collections import defaultdict

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)

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
    timeout_seconds = int(request.data.get('timeout_seconds', 60))

    if not academic_year:
        return Response(
            {'error': 'academic_year is required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        academic_year = int(academic_year)
    except (TypeError, ValueError):
        return Response(
            {'error': 'academic_year must be an integer.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    valid_sem = ('Odd Semester', 'Even Semester', 'Summer Term')
    if semester_type not in valid_sem:
        return Response(
            {'error': f'semester_type must be one of {valid_sem}.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        from applications.academic_procedures.solver.timetable_solver import (
            WholeCollegeTimetableSolver,
        )
        solver = WholeCollegeTimetableSolver(
            academic_year=academic_year,
            semester_type=semester_type,
        )
        result = solver.solve(timeout_seconds=timeout_seconds)
    except Exception as exc:
        logger.exception('Solver raised an unexpected exception: %s', exc)
        return Response(
            {'error': f'Solver internal error: {exc}'},
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
    """Return all TimetableVersion records, optionally filtered by academic_year."""
    from applications.academic_procedures.models import TimetableVersion

    qs = TimetableVersion.objects.all()
    academic_year = request.query_params.get('academic_year')
    if academic_year:
        qs = qs.filter(academic_year=int(academic_year))

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
                  faculty_ci_id, day_of_week
    """
    from applications.academic_procedures.models import TimetableSlot, TimetableVersion

    version_id = request.query_params.get('version_id')
    if not version_id:
        # Default to published version for current user
        published = (
            TimetableVersion.objects.filter(status='Published')
            .order_by('-academic_year', '-version_number')
            .first()
        )
        if not published:
            return Response([])
        version_id = published.id

    qs = TimetableSlot.objects.filter(version_id=int(version_id)).select_related(
        'curriculum__course_id',
        'curriculum_instructor__instructor_id__user',
        'classroom',
    )

    for param, field in [
        ('batch', 'batch'),
        ('programme', 'programme'),
        ('branch', 'branch'),
        ('section', 'section'),
        ('day_of_week', 'day_of_week'),
    ]:
        val = request.query_params.get(param)
        if val:
            qs = qs.filter(**{field: val})

    faculty_ci = request.query_params.get('faculty_ci_id')
    if faculty_ci:
        qs = qs.filter(curriculum_instructor_id=int(faculty_ci))

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

    Returns 200 on success, 409 on constraint violation, 404 if slot not found.
    """
    if not _is_acadadmin(request):
        return Response(
            {'error': 'Only acadadmin may override timetable slots.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    from applications.academic_procedures.models import TimetableSlot, Classroom

    slot_id = request.data.get('slot_id')
    new_day = request.data.get('new_day')
    new_hour = request.data.get('new_start_hour')
    new_room_id = request.data.get('new_room_id')
    lock = bool(request.data.get('lock', False))

    if not all([slot_id, new_day, new_hour, new_room_id]):
        return Response(
            {'error': 'slot_id, new_day, new_start_hour, new_room_id are required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        slot = TimetableSlot.objects.select_related(
            'curriculum', 'classroom', 'version',
        ).get(pk=int(slot_id))
    except TimetableSlot.DoesNotExist:
        return Response(
            {'error': f'Slot {slot_id} not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    new_day = int(new_day)
    new_hour = int(new_hour)

    # ── Validate constraints ───────────────────────────────────────────── #
    conflicts = []

    # Room availability
    room_clash = TimetableSlot.objects.filter(
        version=slot.version,
        classroom_id=new_room_id,
        day_of_week=new_day,
        start_hour=new_hour,
    ).exclude(pk=slot.pk)
    if room_clash.exists():
        conflicts.append({
            'type': 'ROOM_CLASH',
            'detail': f'Room {new_room_id} is already occupied at day={new_day} hour={new_hour}.',
        })

    # Faculty clash
    if slot.curriculum_instructor_id:
        fac_clash = TimetableSlot.objects.filter(
            version=slot.version,
            curriculum_instructor_id=slot.curriculum_instructor_id,
            day_of_week=new_day,
            start_hour=new_hour,
        ).exclude(pk=slot.pk)
        if fac_clash.exists():
            conflicts.append({
                'type': 'FACULTY_CLASH',
                'detail': (
                    f'Instructor has another class at day={new_day} hour={new_hour}.'
                ),
            })

    # Cohort clash
    cohort_clash = TimetableSlot.objects.filter(
        version=slot.version,
        batch=slot.batch,
        programme=slot.programme,
        branch=slot.branch,
        section=slot.section,
        day_of_week=new_day,
        start_hour=new_hour,
    ).exclude(pk=slot.pk)
    if cohort_clash.exists():
        conflicts.append({
            'type': 'COHORT_CLASH',
            'detail': (
                f'Cohort {slot.batch}/{slot.programme}/{slot.branch}/{slot.section} '
                f'has another class at day={new_day} hour={new_hour}.'
            ),
        })

    # Room capacity & type
    try:
        new_room = Classroom.objects.get(pk=new_room_id)
    except Classroom.DoesNotExist:
        return Response(
            {'error': f'Classroom {new_room_id} not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Estimate cohort size (fast approximation)
    from applications.academic_information.models import Student
    cohort_count = Student.objects.filter(
        batch=slot.batch,
        programme=slot.programme,
    ).count()
    eff_size = math.ceil(cohort_count * 1.10)
    if new_room.capacity < eff_size:
        conflicts.append({
            'type': 'CAPACITY',
            'detail': (
                f'Room {new_room_id} capacity ({new_room.capacity}) < '
                f'cohort size ({eff_size}).'
            ),
        })

    if conflicts:
        return Response(
            {'error': 'Constraint violations detected.', 'conflicts': conflicts},
            status=status.HTTP_409_CONFLICT,
        )

    # ── Apply move ─────────────────────────────────────────────────────── #
    slot.day_of_week = new_day
    slot.start_hour = new_hour
    slot.classroom_id = new_room_id
    slot.is_locked = lock
    slot.save(update_fields=['day_of_week', 'start_hour', 'classroom_id', 'is_locked'])

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
        version = TimetableVersion.objects.get(pk=int(version_id))
    except TimetableVersion.DoesNotExist:
        return Response(
            {'error': f'TimetableVersion {version_id} not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if version.status not in ('Draft', 'Approved', 'UnderReview'):
        return Response(
            {'error': f'Cannot publish a version with status={version.status}.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Archive currently published version for same term
    TimetableVersion.objects.filter(
        academic_year=version.academic_year,
        semester_type=version.semester_type,
        status='Published',
    ).update(status='Archived')

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
    from applications.academic_procedures.models import TimetableSlot, TimetableVersion
    from applications.academic_information.models import Student, Curriculum_Instructor
    from applications.globals.models import ExtraInfo

    # Find published version
    published = (
        TimetableVersion.objects.filter(status='Published')
        .order_by('-academic_year', '-version_number')
        .first()
    )
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
        slots_qs = slots_qs.filter(
            batch=stu.batch,
            programme=stu.programme,
            branch=getattr(stu.id.department, 'name', ''),
            section=stu.section or '',
        )
    elif extra.user_type == 'faculty':
        ci_ids = list(
            Curriculum_Instructor.objects.filter(instructor_id=extra)
            .values_list('pk', flat=True)
        )
        slots_qs = slots_qs.filter(curriculum_instructor_id__in=ci_ids)
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
    from applications.academic_procedures.models import TimetableSlot, TimetableVersion

    room_id = request.query_params.get('room_id')
    if not room_id:
        return Response({'error': 'room_id is required.'}, status=400)

    version_id = request.query_params.get('version_id')
    if not version_id:
        pub = (
            TimetableVersion.objects.filter(status='Published')
            .order_by('-academic_year', '-version_number')
            .first()
        )
        if not pub:
            return Response({'matrix': {}, 'message': 'No published timetable.'})
        version_id = pub.id

    slots = TimetableSlot.objects.filter(
        version_id=int(version_id),
        classroom_id=room_id,
    ).values('day_of_week', 'start_hour', 'curriculum__course_code')

    matrix: dict = defaultdict(dict)
    for s in slots:
        day = s['day_of_week']
        hour = s['start_hour']
        matrix[day][hour] = s['curriculum__course_code']

    # Fill unused slots with None
    for day in range(1, 6):
        for hour in [9, 10, 11, 12, 14, 15, 16, 17]:
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

    room, created = Classroom.objects.get_or_create(
        room_id=request.data['room_id'],
        defaults={
            'building': request.data['building'],
            'capacity': int(request.data['capacity']),
            'room_type': request.data['room_type'],
            'has_projector': bool(request.data.get('has_projector', True)),
            'is_active': bool(request.data.get('is_active', True)),
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

    for field in ('building', 'capacity', 'room_type', 'has_projector', 'is_active'):
        if field in request.data:
            setattr(room, field, request.data[field])
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
        curr = Curriculum.objects.get(pk=int(curriculum_id))
    except Curriculum.DoesNotExist:
        return Response({'error': f'Curriculum {curriculum_id} not found.'}, status=404)

    req, created = CourseWeeklyRequirement.objects.update_or_create(
        curriculum=curr,
        defaults={
            'lectures_per_week': int(request.data.get('lectures_per_week', 3)),
            'tutorials_per_week': int(request.data.get('tutorials_per_week', 1)),
            'practicals_per_week': int(request.data.get('practicals_per_week', 0)),
            'practical_block_size': int(request.data.get('practical_block_size', 2)),
            'preferred_room_type': request.data.get('preferred_room_type', 'any'),
        },
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

    basket, created = ElectiveBasket.objects.get_or_create(
        basket_code=request.data['basket_code'],
        defaults={
            'name': request.data['name'],
            'semester': int(request.data['semester']),
            'programme': request.data['programme'],
            'academic_year': int(request.data.get('academic_year', 2026)),
            'semester_type': request.data.get('semester_type', 'Odd Semester'),
        },
    )
    # Add curricula
    for entry in request.data.get('curricula', []):
        cur_id = entry.get('curriculum_id')
        max_seats = int(entry.get('max_seats', 60))
        try:
            curr = Curriculum.objects.get(pk=int(cur_id))
        except (Curriculum.DoesNotExist, TypeError, ValueError):
            continue
        ElectiveBasketCurriculum.objects.get_or_create(
            basket=basket, curriculum=curr,
            defaults={'max_seats': max_seats},
        )

    return Response({'id': basket.id, 'basket_code': basket.basket_code, 'created': created},
                    status=201 if created else 200)


# ═══════════════════════════════════════════════════════════════════════════ #
# FacultyPreference CRUD                                                       #
# ═══════════════════════════════════════════════════════════════════════════ #

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def faculty_preferences(request):
    from applications.academic_procedures.models import FacultyPreference
    from applications.globals.models import Faculty

    if request.method == 'GET':
        qs = FacultyPreference.objects.select_related('faculty__id__user')
        faculty_pk = request.query_params.get('faculty_id')
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
    faculty_pk = request.data.get('faculty_id')
    if not faculty_pk:
        # Default to own faculty profile
        try:
            from applications.globals.models import ExtraInfo
            extra = ExtraInfo.objects.get(user=request.user)
            fac = Faculty.objects.get(id=extra)
            faculty_pk = fac.id_id
        except Exception:
            return Response({'error': 'faculty_id is required.'}, status=400)

    try:
        fac = Faculty.objects.get(pk=faculty_pk)
    except Faculty.DoesNotExist:
        return Response({'error': f'Faculty {faculty_pk} not found.'}, status=404)

    required = ('day_of_week', 'start_hour', 'end_hour', 'preference_type')
    for f in required:
        if f not in request.data:
            return Response({'error': f'{f} is required.'}, status=400)

    pref = FacultyPreference.objects.create(
        faculty=fac,
        academic_year=int(request.data.get('academic_year', 2026)),
        semester_type=request.data.get('semester_type', 'Odd Semester'),
        day_of_week=int(request.data['day_of_week']),
        start_hour=int(request.data['start_hour']),
        end_hour=int(request.data['end_hour']),
        preference_type=request.data['preference_type'],
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

    version_id = request.query_params.get('version_id')
    if not version_id:
        return Response({'error': 'version_id is required.'}, status=400)

    logs = TimetableConflictLog.objects.filter(version_id=int(version_id))
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
