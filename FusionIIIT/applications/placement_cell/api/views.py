"""
REST API views for the Placement Cell Management System (PCMS).
Provides endpoints for:
  - User role checking
  - Placement schedule CRUD (legacy)
  - Student records, invitation status, debarred students
  - Placement statistics & records
  - CV data retrieval
  - Company, job posting, application, offer, announcement CRUD (PCMS)
  - Interview & policy management
  - Dashboard, reports, calendar, timeline
"""
import datetime
import logging

from datetime import date
from io import BytesIO

from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Max, Min, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response

from applications.globals.models import ExtraInfo, HoldsDesignation
from applications.academic_information.models import Student

from applications.placement_cell.models import (
    Achievement, ChairmanVisit, Course, Education, Experience, Conference,
    Has, NotifyStudent, Patent, PlacementRecord, Extracurricular, Reference,
    PlacementSchedule, PlacementStatus, Project, Publication, Interest,
    Skill, StudentPlacement, StudentRecord, Role, CompanyDetails,
    Company, JobPosting, JobApplication, InterviewSchedule,
    InterviewPanel, JobOffer, Announcement, PlacementPolicy,
    Coauthor, Coinventor,
)

from applications.placement_cell.api.serializers import (
    SkillSerializer, HasSerializer, EducationSerializer, CourseSerializer,
    ExperienceSerializer, ProjectSerializer, AchievementSerializer,
    PublicationSerializer, PatentSerializer, ReferenceSerializer,
    ConferenceSerializer, ExtracurricularSerializer, InterestSerializer,
    NotifyStudentSerializer, RoleSerializer, CompanyDetailsSerializer,
    PlacementScheduleSerializer, PlacementStatusSerializer,
    PlacementRecordSerializer, StudentRecordSerializer,
    StudentPlacementSerializer, ChairmanVisitSerializer,
    CompanySerializer, CompanyListSerializer,
    JobPostingSerializer, JobPostingListSerializer,
    JobApplicationSerializer,
    InterviewScheduleSerializer, InterviewPanelSerializer,
    JobOfferSerializer,
    AnnouncementSerializer,
    PlacementPolicySerializer,
)

from applications.placement_cell.utils import (
    check_eligibility, check_duplicate_application,
    check_placement_policy, get_placement_statistics,
    get_student_application_summary, expire_pending_offers,
)

logger = logging.getLogger('django.server')


# =============================================
# HELPER FUNCTIONS
# =============================================

def _is_tpo_or_chairman(user):
    """Check if user is TPO or Placement Chairman."""
    return HoldsDesignation.objects.filter(
        Q(working=user, designation__name="placement officer") |
        Q(working=user, designation__name="placement chairman")
    ).exists()


def _is_chairman(user):
    """Check if user is Placement Chairman."""
    return HoldsDesignation.objects.filter(
        Q(working=user, designation__name="placement chairman")
    ).exists()


def _is_officer(user):
    """Check if user is Placement Officer (TPO)."""
    return HoldsDesignation.objects.filter(
        Q(working=user, designation__name="placement officer")
    ).exists()


def _is_student(user):
    """Check if user is a student."""
    return HoldsDesignation.objects.filter(
        Q(working=user, designation__name="student")
    ).exists()


def _get_student(user):
    """Get the Student object for a user. Returns None if not a student."""
    try:
        profile = ExtraInfo.objects.get(user=user)
        return Student.objects.get(id=profile)
    except (ExtraInfo.DoesNotExist, Student.DoesNotExist):
        return None


def _check_invitation_date(placementstatus_qs):
    """Expire pending invitations past their deadline."""
    try:
        for ps in placementstatus_qs:
            if ps.invitation == 'PENDING':
                dt = ps.timestamp + datetime.timedelta(days=ps.no_of_days)
                if dt < datetime.datetime.now():
                    ps.invitation = 'IGNORE'
                    ps.save()
    except Exception as e:
        logger.error('Error checking invitation date: {}'.format(e))


# =============================================
# 1. ROLE & AUTH
# =============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def user_roles_api(request):
    """Return the user's placement roles."""
    user = request.user
    is_chairman_val = _is_chairman(user)
    is_officer_val = _is_officer(user)
    is_student_val = _is_student(user)

    role = 'other'
    if is_chairman_val:
        role = 'placement chairman'
    elif is_officer_val:
        role = 'placement officer'
    elif is_student_val:
        role = 'student'

    return Response({
        'role': role,
        'is_chairman': is_chairman_val,
        'is_officer': is_officer_val,
        'is_student': is_student_val,
    })


# =============================================
# 2. PLACEMENT SCHEDULE (Legacy)
# =============================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def placement_schedule_api(request):
    """
    GET: List all placement schedules.
         For students, includes their invitation status per schedule.
    POST: Create a new placement schedule (officer/chairman only).
    """
    user = request.user

    if request.method == 'GET':
        schedules = PlacementSchedule.objects.select_related('notify_id', 'role').all().order_by('-schedule_at')
        data = PlacementScheduleSerializer(schedules, many=True).data

        # For students, attach invitation status
        if _is_student(user):
            student = _get_student(user)
            if student:
                for item in data:
                    try:
                        ps = PlacementStatus.objects.get(
                            unique_id=student, notify_id=item['notify_id']
                        )
                        item['check'] = ps.invitation
                    except PlacementStatus.DoesNotExist:
                        item['check'] = 'PENDING'
        return Response(data)

    elif request.method == 'POST':
        if not _is_tpo_or_chairman(user):
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

        company_name = request.data.get('company_name', '')
        placement_date = request.data.get('placement_date')
        location = request.data.get('location', '')
        ctc = request.data.get('ctc', 0)
        time_val = request.data.get('time')
        placement_type = request.data.get('placement_type', 'PLACEMENT')
        role_offered = request.data.get('role', '')
        description = request.data.get('description', '')
        schedule_at = request.data.get('schedule_at')
        attached_file = request.FILES.get('attached_file')

        # Ensure CompanyDetails exists
        CompanyDetails.objects.get_or_create(company_name=company_name)

        # Ensure Role exists
        role_obj, _ = Role.objects.get_or_create(role=role_offered)

        # Create notification
        notify = NotifyStudent.objects.create(
            placement_type=placement_type,
            company_name=company_name,
            description=description,
            ctc=ctc,
            timestamp=timezone.now(),
        )

        # Create schedule
        schedule = PlacementSchedule.objects.create(
            notify_id=notify,
            title=company_name,
            description=description,
            placement_date=placement_date,
            attached_file=attached_file,
            role=role_obj,
            location=location,
            time=time_val,
            schedule_at=schedule_at or timezone.now(),
        )

        return Response(
            PlacementScheduleSerializer(schedule).data,
            status=status.HTTP_201_CREATED
        )


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def placement_schedule_detail_api(request, schedule_id):
    """
    PUT: Update invitation status (student accepts/declines).
    DELETE: Delete a placement schedule (officer/chairman only).
    """
    user = request.user

    if request.method == 'PUT':
        # Student updating invitation status
        student = _get_student(user)
        if not student:
            return Response({'error': 'Student profile not found'}, status=status.HTTP_404_NOT_FOUND)

        schedule = get_object_or_404(PlacementSchedule, id=schedule_id)
        invitation_action = request.data.get('invitation', '')

        try:
            ps = PlacementStatus.objects.get(
                unique_id=student, notify_id=schedule.notify_id
            )
        except PlacementStatus.DoesNotExist:
            ps = PlacementStatus.objects.create(
                unique_id=student,
                notify_id=schedule.notify_id,
                invitation='PENDING',
            )

        if invitation_action in ('ACCEPTED', 'REJECTED'):
            ps.invitation = invitation_action
            ps.timestamp = timezone.now()
            ps.save()
            return Response({'status': ps.invitation})

        return Response({'error': 'Invalid action. Use ACCEPTED or REJECTED.'}, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        if not _is_tpo_or_chairman(user):
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

        schedule = get_object_or_404(PlacementSchedule, id=schedule_id)
        try:
            schedule.notify_id.delete()  # Cascades to PlacementStatus
            schedule.delete()
            return Response({'status': 'deleted'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================
# 3. STUDENT RECORDS & CV
# =============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def student_records_api(request):
    """List all students with profile/placement info."""
    students = Student.objects.select_related('id', 'id__user', 'id__department').all()

    data = []
    for student in students:
        try:
            sp = StudentPlacement.objects.get(unique_id=student)
            debar = sp.debar
            placed = sp.placed_type
        except StudentPlacement.DoesNotExist:
            debar = 'NOT DEBAR'
            placed = 'NOT PLACED'

        data.append({
            'id': student.id.id,
            'name': '{} {}'.format(student.id.user.first_name, student.id.user.last_name),
            'roll_no': student.id.id,
            'department': student.id.department.name if student.id.department else '',
            'programme': student.programme or '',
            'batch': student.batch,
            'cpi': student.cpi,
            'debar': debar,
            'placed': placed,
        })

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def cv_data_api(request, username):
    """Get student CV data as JSON."""
    target_user = get_object_or_404(User, username=username)
    profile = get_object_or_404(ExtraInfo, user=target_user)
    student = get_object_or_404(Student, id=profile)

    skills = Has.objects.select_related('skill_id').filter(unique_id=student)
    education = Education.objects.filter(unique_id=student)
    references = Reference.objects.filter(unique_id=student)
    courses = Course.objects.filter(unique_id=student)
    experiences = Experience.objects.filter(unique_id=student)
    projects = Project.objects.filter(unique_id=student)
    achievements = Achievement.objects.filter(unique_id=student)
    extracurriculars = Extracurricular.objects.filter(unique_id=student)
    conferences = Conference.objects.filter(unique_id=student)
    publications = Publication.objects.filter(unique_id=student)
    patents = Patent.objects.filter(unique_id=student)

    return Response({
        'user': {
            'username': target_user.username,
            'first_name': target_user.first_name,
            'last_name': target_user.last_name,
            'email': target_user.email,
        },
        'profile': {
            'about_me': profile.about_me or '',
            'age': profile.age if hasattr(profile, 'age') else None,
            'address': profile.address or '',
            'phone_no': profile.phone_no or '',
            'department': profile.department.name if profile.department else '',
            'profile_picture': profile.profile_picture.url if profile.profile_picture else None,
        },
        'student': {
            'programme': student.programme or '',
            'batch': student.batch,
            'cpi': student.cpi,
            'specialization': student.specialization or '',
        },
        'skills': HasSerializer(skills, many=True).data,
        'education': EducationSerializer(education, many=True).data,
        'references': ReferenceSerializer(references, many=True).data,
        'courses': CourseSerializer(courses, many=True).data,
        'experiences': ExperienceSerializer(experiences, many=True).data,
        'projects': ProjectSerializer(projects, many=True).data,
        'achievements': AchievementSerializer(achievements, many=True).data,
        'extracurriculars': ExtracurricularSerializer(extracurriculars, many=True).data,
        'conferences': ConferenceSerializer(conferences, many=True).data,
        'publications': PublicationSerializer(publications, many=True).data,
        'patents': PatentSerializer(patents, many=True).data,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def generate_cv_api(request):
    """Generate PDF CV for download."""
    from xhtml2pdf import pisa
    from django.template.loader import render_to_string

    username = request.data.get('username', request.user.username)
    target_user = get_object_or_404(User, username=username)
    profile = get_object_or_404(ExtraInfo, user=target_user)
    student = get_object_or_404(Student, id=profile)

    # Which sections to include (default all)
    achievementcheck = request.data.get('achievementcheck', '1')
    educationcheck = request.data.get('educationcheck', '1')
    publicationcheck = request.data.get('publicationcheck', '1')
    patentcheck = request.data.get('patentcheck', '1')
    internshipcheck = request.data.get('internshipcheck', '1')
    projectcheck = request.data.get('projectcheck', '1')
    coursecheck = request.data.get('coursecheck', '1')
    skillcheck = request.data.get('skillcheck', '1')
    extracurricularcheck = request.data.get('extracurricularcheck', '1')
    conferencecheck = request.data.get('conferencecheck', '1')
    reference_list = request.data.getlist('reference_checkbox_list', [])

    skills = Has.objects.select_related('skill_id').filter(unique_id=student)
    education = Education.objects.filter(unique_id=student)
    references = Reference.objects.filter(id__in=reference_list) if reference_list else Reference.objects.none()
    courses = Course.objects.filter(unique_id=student)
    experiences = Experience.objects.filter(unique_id=student)
    projects = Project.objects.filter(unique_id=student)
    achievements = Achievement.objects.filter(unique_id=student)
    extracurriculars = Extracurricular.objects.filter(unique_id=student)
    conferences = Conference.objects.filter(unique_id=student)
    publications = Publication.objects.filter(unique_id=student)
    patents = Patent.objects.filter(unique_id=student)

    student_info = get_object_or_404(Student, id=target_user.username)
    batch = student_info.batch
    now = datetime.datetime.now()
    roll = min(now.year - batch, 4) if now.year - batch <= 4 else 4

    referencecheck = '1' if references.exists() else '0'

    context = {
        'pagesize': 'A4',
        'user': target_user,
        'profile': profile,
        'projects': projects,
        'skills': skills,
        'educations': education,
        'references': references,
        'courses': courses,
        'experiences': experiences,
        'achievements': achievements,
        'extracurriculars': extracurriculars,
        'publications': publications,
        'patents': patents,
        'conferences': conferences,
        'roll': roll,
        'referencecheck': referencecheck,
        'achievementcheck': achievementcheck,
        'educationcheck': educationcheck,
        'publicationcheck': publicationcheck,
        'patentcheck': patentcheck,
        'internshipcheck': internshipcheck,
        'projectcheck': projectcheck,
        'coursecheck': coursecheck,
        'skillcheck': skillcheck,
        'extracurricularcheck': extracurricularcheck,
        'conferencecheck': conferencecheck,
        'today': datetime.date.today(),
    }

    html = render_to_string('placementModule/cv.html', context)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode('UTF-8')), result)
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="cv_{}.pdf"'.format(username)
        return response
    return Response({'error': 'Failed to generate PDF'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================
# 4. INVITATION / APPLICATION STATUS
# =============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def student_applications_api(request, job_id):
    """Get students who applied/were invited for a specific placement schedule."""
    if not _is_tpo_or_chairman(request.user):
        return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

    statuses = PlacementStatus.objects.select_related(
        'unique_id', 'unique_id__id', 'unique_id__id__user', 'notify_id'
    ).filter(notify_id=job_id)

    return Response(PlacementStatusSerializer(statuses, many=True).data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def update_student_application_api(request, pk):
    """Update a student's application/invitation status."""
    if not _is_tpo_or_chairman(request.user):
        return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

    ps = get_object_or_404(PlacementStatus, id=pk)
    new_invitation = request.data.get('invitation')
    new_placed = request.data.get('placed')

    if new_invitation:
        ps.invitation = new_invitation
    if new_placed:
        ps.placed = new_placed
    ps.timestamp = timezone.now()
    ps.save()

    return Response(PlacementStatusSerializer(ps).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def invitation_status_api(request):
    """View invitation statuses with optional filters."""
    if not _is_tpo_or_chairman(request.user):
        return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

    placement_type = request.query_params.get('placement_type', '')
    company = request.query_params.get('company', '')
    student_name = request.query_params.get('student_name', '')
    roll = request.query_params.get('roll', '')
    page = request.query_params.get('page', 1)

    qs = PlacementStatus.objects.select_related(
        'unique_id', 'unique_id__id', 'unique_id__id__user', 'notify_id'
    )

    if placement_type:
        qs = qs.filter(notify_id__placement_type=placement_type)
    if company:
        qs = qs.filter(notify_id__company_name__icontains=company)
    if student_name:
        qs = qs.filter(
            unique_id__id__user__first_name__icontains=student_name
        )
    if roll:
        qs = qs.filter(unique_id__id__id__icontains=roll)

    qs = qs.order_by('-timestamp')

    paginator = Paginator(qs, 30)
    page_obj = paginator.get_page(page)

    return Response({
        'results': PlacementStatusSerializer(page_obj.object_list, many=True).data,
        'count': paginator.count,
        'num_pages': paginator.num_pages,
        'current_page': page_obj.number,
    })


# =============================================
# 5. PLACEMENT STATISTICS & RECORDS
# =============================================

@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def placement_statistics_api(request):
    """
    GET: Get placement records/statistics.
    POST: Add a new placement record (officer/chairman only).
    DELETE: Delete a placement record (officer/chairman only).
    """
    if request.method == 'GET':
        placement_type = request.query_params.get('placement_type', '')
        year = request.query_params.get('year', '')
        name = request.query_params.get('name', '')

        qs = PlacementRecord.objects.all()
        if placement_type:
            qs = qs.filter(placement_type=placement_type)
        if year:
            qs = qs.filter(year=year)
        if name:
            qs = qs.filter(name__icontains=name)

        data = PlacementRecordSerializer(qs.order_by('-year'), many=True).data

        # Add department-wise counts per year
        years = PlacementRecord.objects.filter(
            ~Q(placement_type="HIGHER STUDIES")
        ).values('year').annotate(Count('year')).order_by('-year')

        year_stats = []
        for y in years:
            student_records = StudentRecord.objects.select_related(
                'unique_id__id__department', 'record_id'
            ).filter(record_id__year=y['year'])

            cse = student_records.filter(unique_id__id__department__name='CSE').count()
            ece = student_records.filter(unique_id__id__department__name='ECE').count()
            me = student_records.filter(unique_id__id__department__name='ME').count()
            total = cse + ece + me

            year_stats.append({
                'year': y['year'],
                'total': total,
                'cse': cse,
                'ece': ece,
                'me': me,
            })

        return Response({
            'records': data,
            'year_stats': year_stats,
        })

    elif request.method == 'POST':
        if not _is_tpo_or_chairman(request.user):
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

        serializer = PlacementRecordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        if not _is_tpo_or_chairman(request.user):
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

        record_id = request.data.get('record_id')
        if not record_id:
            return Response({'error': 'record_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            PlacementRecord.objects.filter(id=record_id).delete()
            return Response({'status': 'deleted'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def manage_records_api(request):
    """
    GET: List student records with optional filters.
    POST: Add a student to a placement record.
    DELETE: Remove a student record.
    """
    if request.method == 'GET':
        qs = StudentRecord.objects.select_related(
            'unique_id', 'unique_id__id', 'unique_id__id__user',
            'unique_id__id__department', 'record_id'
        ).all()

        placement_type = request.query_params.get('placement_type', '')
        year = request.query_params.get('year', '')
        company = request.query_params.get('company', '')

        if placement_type:
            qs = qs.filter(record_id__placement_type=placement_type)
        if year:
            qs = qs.filter(record_id__year=year)
        if company:
            qs = qs.filter(record_id__name__icontains=company)

        return Response(StudentRecordSerializer(qs, many=True).data)

    elif request.method == 'POST':
        if not _is_tpo_or_chairman(request.user):
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

        serializer = StudentRecordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        if not _is_tpo_or_chairman(request.user):
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

        record_id = request.data.get('record_id')
        if not record_id:
            return Response({'error': 'record_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            StudentRecord.objects.filter(id=record_id).delete()
            return Response({'status': 'deleted'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================
# 6. DEBARRED STUDENTS
# =============================================

@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def debarred_students_api(request):
    """
    GET: List debarred students.
    POST: Debar a student (officer/chairman).
    DELETE: Undebar a student (officer/chairman).
    """
    if request.method == 'GET':
        debarred = StudentPlacement.objects.filter(debar='DEBAR').select_related(
            'unique_id', 'unique_id__id', 'unique_id__id__user'
        )
        return Response(StudentPlacementSerializer(debarred, many=True).data)

    elif request.method == 'POST':
        if not _is_tpo_or_chairman(request.user):
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

        roll_no = request.data.get('roll_no', '')
        if not roll_no:
            return Response({'error': 'roll_no is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            extra_info = ExtraInfo.objects.get(id=roll_no)
            student = Student.objects.get(id=extra_info)
        except (ExtraInfo.DoesNotExist, Student.DoesNotExist):
            return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)

        sp, created = StudentPlacement.objects.get_or_create(unique_id=student)
        sp.debar = 'DEBAR'
        sp.save()

        return Response({'status': 'debarred', 'roll_no': roll_no})

    elif request.method == 'DELETE':
        if not _is_tpo_or_chairman(request.user):
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

        roll_no = request.data.get('roll_no', '')
        if not roll_no:
            return Response({'error': 'roll_no is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            extra_info = ExtraInfo.objects.get(id=roll_no)
            student = Student.objects.get(id=extra_info)
            sp = StudentPlacement.objects.get(unique_id=student)
            sp.debar = 'NOT DEBAR'
            sp.save()
            return Response({'status': 'undebarred', 'roll_no': roll_no})
        except (ExtraInfo.DoesNotExist, Student.DoesNotExist, StudentPlacement.DoesNotExist):
            return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def debarred_status_api(request, roll_no):
    """Get debar status for a specific student."""
    try:
        extra_info = ExtraInfo.objects.get(id=roll_no)
        student = Student.objects.get(id=extra_info)
        sp = StudentPlacement.objects.get(unique_id=student)
        return Response({
            'roll_no': roll_no,
            'name': '{} {}'.format(extra_info.user.first_name, extra_info.user.last_name),
            'debar': sp.debar,
            'placed': sp.placed_type,
        })
    except StudentPlacement.DoesNotExist:
        return Response({
            'roll_no': roll_no,
            'name': '{} {}'.format(extra_info.user.first_name, extra_info.user.last_name),
            'debar': 'NOT DEBAR',
            'placed': 'NOT PLACED',
        })
    except (ExtraInfo.DoesNotExist, Student.DoesNotExist):
        return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)


# =============================================
# 7. FIELDS & RESTRICTIONS (TPO)
# =============================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def manage_fields_api(request):
    """Manage custom form fields (roles)."""
    if request.method == 'GET':
        roles = Role.objects.all()
        return Response(RoleSerializer(roles, many=True).data)

    elif request.method == 'POST':
        if not _is_tpo_or_chairman(request.user):
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

        role_name = request.data.get('role', '')
        if not role_name:
            return Response({'error': 'role is required'}, status=status.HTTP_400_BAD_REQUEST)

        role_obj, created = Role.objects.get_or_create(role=role_name)
        return Response(
            RoleSerializer(role_obj).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def form_fields_api(request):
    """Get form field configuration (roles, companies, skills)."""
    roles = Role.objects.all()
    companies = CompanyDetails.objects.all()
    skills = Skill.objects.all()

    return Response({
        'roles': RoleSerializer(roles, many=True).data,
        'companies': CompanyDetailsSerializer(companies, many=True).data,
        'skills': SkillSerializer(skills, many=True).data,
    })


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def restrictions_api(request):
    """Manage placement restrictions (policies)."""
    if request.method == 'GET':
        policies = PlacementPolicy.objects.all()
        return Response(PlacementPolicySerializer(policies, many=True).data)

    elif request.method == 'POST':
        if not _is_tpo_or_chairman(request.user):
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

        serializer = PlacementPolicySerializer(data=request.data)
        if serializer.is_valid():
            # Deactivate all existing policies first
            PlacementPolicy.objects.update(is_active=False)
            serializer.save(is_active=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =============================================
# 8. COMPANY REGISTRATION (Legacy)
# =============================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def company_registration_api(request):
    """
    GET: Get registered companies (legacy CompanyDetails).
    POST: Register a new company (legacy CompanyDetails).
    """
    if request.method == 'GET':
        companies = CompanyDetails.objects.all()
        return Response(CompanyDetailsSerializer(companies, many=True).data)

    elif request.method == 'POST':
        if not _is_tpo_or_chairman(request.user):
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

        company_name = request.data.get('company_name', '')
        if not company_name:
            return Response({'error': 'company_name is required'}, status=status.HTTP_400_BAD_REQUEST)

        obj, created = CompanyDetails.objects.get_or_create(company_name=company_name)
        return Response(
            CompanyDetailsSerializer(obj).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )


# =============================================
# 9. APPLY FOR PLACEMENT (Student)
# =============================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def apply_for_placement_api(request):
    """Student applies/responds to a placement schedule invitation."""
    user = request.user
    student = _get_student(user)
    if not student:
        return Response({'error': 'Student profile not found'}, status=status.HTTP_404_NOT_FOUND)

    notify_id = request.data.get('notify_id')
    invitation_response = request.data.get('invitation', 'ACCEPTED')

    if not notify_id:
        return Response({'error': 'notify_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        notify = NotifyStudent.objects.get(id=notify_id)
    except NotifyStudent.DoesNotExist:
        return Response({'error': 'Placement event not found'}, status=status.HTTP_404_NOT_FOUND)

    ps, created = PlacementStatus.objects.get_or_create(
        unique_id=student,
        notify_id=notify,
        defaults={'invitation': invitation_response}
    )

    if not created:
        ps.invitation = invitation_response
        ps.timestamp = timezone.now()
        ps.save()

    return Response(PlacementStatusSerializer(ps).data)


# =============================================
# 10. CALENDAR & TIMELINE
# =============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def calendar_events_api(request):
    """Get placement calendar events."""
    schedules = PlacementSchedule.objects.select_related('notify_id', 'role').all()
    events = []
    for s in schedules:
        events.append({
            'id': s.id,
            'title': s.title,
            'date': str(s.placement_date),
            'time': str(s.time) if s.time else '',
            'location': s.location,
            'description': s.description,
            'company_name': s.notify_id.company_name,
            'placement_type': s.notify_id.placement_type,
            'role': s.get_role,
        })
    return Response(events)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def timeline_api(request, job_id):
    """Get the placement timeline / history for a specific placement event."""
    try:
        notify = NotifyStudent.objects.get(id=job_id)
    except NotifyStudent.DoesNotExist:
        return Response({'error': 'Placement event not found'}, status=status.HTTP_404_NOT_FOUND)

    schedules = PlacementSchedule.objects.filter(notify_id=notify).order_by('placement_date')
    statuses = PlacementStatus.objects.select_related(
        'unique_id', 'unique_id__id', 'unique_id__id__user'
    ).filter(notify_id=notify)

    return Response({
        'event': NotifyStudentSerializer(notify).data,
        'schedules': PlacementScheduleSerializer(schedules, many=True).data,
        'statuses': PlacementStatusSerializer(statuses, many=True).data,
    })


# =============================================
# 11. NEXT ROUND & DOWNLOAD
# =============================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def next_round_api(request):
    """Create a next round schedule for an existing placement event."""
    if not _is_tpo_or_chairman(request.user):
        return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

    notify_id = request.data.get('notify_id')
    placement_date = request.data.get('placement_date')
    location = request.data.get('location', '')
    time_val = request.data.get('time')
    description = request.data.get('description', '')
    role_name = request.data.get('role', '')

    if not notify_id:
        return Response({'error': 'notify_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    notify = get_object_or_404(NotifyStudent, id=notify_id)
    role_obj, _ = Role.objects.get_or_create(role=role_name)

    schedule = PlacementSchedule.objects.create(
        notify_id=notify,
        title=notify.company_name,
        description=description,
        placement_date=placement_date,
        role=role_obj,
        location=location,
        time=time_val,
    )

    return Response(PlacementScheduleSerializer(schedule).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def download_applications_api(request, job_id):
    """Download applications as Excel for a specific placement event."""
    import xlwt

    if not _is_tpo_or_chairman(request.user):
        return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

    statuses = PlacementStatus.objects.select_related(
        'unique_id', 'unique_id__id', 'unique_id__id__user', 'notify_id'
    ).filter(notify_id=job_id)

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Applications')

    # Headers
    headers = ['S.No', 'Roll No', 'Student Name', 'Company', 'Invitation', 'Placed']
    for col, header in enumerate(headers):
        ws.write(0, col, header)

    for row, ps in enumerate(statuses, 1):
        ws.write(row, 0, row)
        ws.write(row, 1, ps.unique_id.id.id if ps.unique_id and ps.unique_id.id else '')
        try:
            name = '{} {}'.format(
                ps.unique_id.id.user.first_name,
                ps.unique_id.id.user.last_name
            )
        except Exception:
            name = ''
        ws.write(row, 2, name)
        ws.write(row, 3, ps.notify_id.company_name if ps.notify_id else '')
        ws.write(row, 4, ps.invitation)
        ws.write(row, 5, ps.placed)

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.ms-excel'
    )
    response['Content-Disposition'] = 'attachment; filename="applications_{}.xls"'.format(job_id)
    return response


# =============================================
# 12. CHAIRMAN VISITS
# =============================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def visits_api(request):
    """List/create chairman visits."""
    if request.method == 'GET':
        visits = ChairmanVisit.objects.all().order_by('-visiting_date')
        return Response(ChairmanVisitSerializer(visits, many=True).data)

    elif request.method == 'POST':
        if not _is_chairman(request.user):
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

        serializer = ChairmanVisitSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =============================================
# PCMS VIEWSETS (Company, Jobs, Applications, Offers, Announcements)
# These are carried forward from the existing api/views.py
# =============================================

class CompanyViewSet(viewsets.ModelViewSet):
    """API endpoint for Company CRUD."""
    permission_classes = [IsAuthenticated]
    serializer_class = CompanySerializer
    queryset = Company.objects.all()

    def get_queryset(self):
        if _is_tpo_or_chairman(self.request.user):
            return Company.objects.all()
        return Company.objects.filter(approval_status='APPROVED')

    def get_serializer_class(self):
        if self.action == 'list':
            return CompanyListSerializer
        return CompanySerializer

    def perform_create(self, serializer):
        serializer.save(registered_by=self.request.user)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        if not _is_tpo_or_chairman(request.user):
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        company = self.get_object()
        company.approval_status = 'APPROVED'
        company.approved_by = request.user
        company.save()
        return Response({'status': 'approved'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        if not _is_tpo_or_chairman(request.user):
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        company = self.get_object()
        company.approval_status = 'REJECTED'
        company.approved_by = request.user
        company.save()
        return Response({'status': 'rejected'})


class JobPostingViewSet(viewsets.ModelViewSet):
    """API endpoint for Job Posting CRUD."""
    permission_classes = [IsAuthenticated]
    serializer_class = JobPostingSerializer
    queryset = JobPosting.objects.all()

    def get_queryset(self):
        if _is_tpo_or_chairman(self.request.user):
            return JobPosting.objects.select_related('company').all()
        return JobPosting.objects.select_related('company').filter(is_active=True)

    def get_serializer_class(self):
        if self.action == 'list':
            return JobPostingListSerializer
        return JobPostingSerializer

    def perform_create(self, serializer):
        if not _is_tpo_or_chairman(self.request.user):
            raise PermissionError("Not authorized")
        serializer.save(posted_by=self.request.user)

    @action(detail=True, methods=['get'])
    def check_eligibility(self, request, pk=None):
        """Student checks eligibility for a posting."""
        posting = self.get_object()
        profile = get_object_or_404(ExtraInfo, user=request.user)
        try:
            student = Student.objects.get(id=profile)
        except Student.DoesNotExist:
            return Response({'error': 'Student profile not found'}, status=404)

        is_eligible, reasons = check_eligibility(student, posting)
        can_apply, policy_reason = check_placement_policy(student, posting)
        has_applied = check_duplicate_application(student, posting)

        return Response({
            'eligible': is_eligible,
            'reasons': reasons,
            'policy_check': can_apply,
            'policy_reason': policy_reason,
            'already_applied': has_applied,
        })

    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        """Student applies for a job."""
        posting = self.get_object()
        profile = get_object_or_404(ExtraInfo, user=request.user)
        try:
            student = Student.objects.get(id=profile)
        except Student.DoesNotExist:
            return Response({'error': 'Student profile not found'}, status=404)

        if check_duplicate_application(student, posting):
            return Response({'error': 'Already applied'}, status=400)

        is_eligible, reasons = check_eligibility(student, posting)
        if not is_eligible:
            return Response({'error': 'Not eligible', 'reasons': reasons}, status=400)

        can_apply, policy_reason = check_placement_policy(student, posting)
        if not can_apply:
            return Response({'error': policy_reason}, status=400)

        application = JobApplication.objects.create(
            job_posting=posting,
            student=student,
            status='APPLIED',
        )
        return Response(
            JobApplicationSerializer(application).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['get'])
    def applications(self, request, pk=None):
        """TPO gets all applications for a posting."""
        if not _is_tpo_or_chairman(request.user):
            return Response({'error': 'Not authorized'}, status=403)
        posting = self.get_object()
        apps = posting.applications.select_related('student', 'student__id__user')
        return Response(JobApplicationSerializer(apps, many=True).data)


class JobApplicationViewSet(viewsets.ModelViewSet):
    """API endpoint for managing applications."""
    permission_classes = [IsAuthenticated]
    serializer_class = JobApplicationSerializer
    queryset = JobApplication.objects.all()

    def get_queryset(self):
        user = self.request.user
        if _is_tpo_or_chairman(user):
            return JobApplication.objects.all()
        profile = get_object_or_404(ExtraInfo, user=user)
        try:
            student = Student.objects.get(id=profile)
            return JobApplication.objects.filter(student=student)
        except Student.DoesNotExist:
            return JobApplication.objects.none()

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """TPO updates application status."""
        if not _is_tpo_or_chairman(request.user):
            return Response({'error': 'Not authorized'}, status=403)
        application = self.get_object()
        new_status = request.data.get('status')
        remarks = request.data.get('remarks', '')
        if new_status:
            application.status = new_status
            if remarks:
                application.remarks = remarks
            application.save()
        return Response(JobApplicationSerializer(application).data)


class JobOfferViewSet(viewsets.ModelViewSet):
    """API endpoint for managing offers."""
    permission_classes = [IsAuthenticated]
    serializer_class = JobOfferSerializer
    queryset = JobOffer.objects.all()

    def get_queryset(self):
        user = self.request.user
        if _is_tpo_or_chairman(user):
            return JobOffer.objects.all()
        profile = get_object_or_404(ExtraInfo, user=user)
        try:
            student = Student.objects.get(id=profile)
            return JobOffer.objects.filter(application__student=student)
        except Student.DoesNotExist:
            return JobOffer.objects.none()

    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        """Student accepts or rejects an offer."""
        offer = self.get_object()
        action_type = request.data.get('action')
        if offer.status != 'PENDING':
            return Response({'error': 'Offer already {}'.format(offer.status)}, status=400)

        if action_type == 'accept':
            offer.status = 'ACCEPTED'
            offer.responded_at = timezone.now()
            offer.save()
            offer.application.status = 'OFFER_ACCEPTED'
            offer.application.save()

            # Update StudentPlacement
            student = offer.application.student
            sp, created = StudentPlacement.objects.get_or_create(unique_id=student)
            sp.placed_type = 'PLACED'
            sp.placement_date = datetime.date.today()
            sp.package = offer.ctc_offered
            sp.save()

            return Response({'status': 'accepted'})
        elif action_type == 'reject':
            offer.status = 'REJECTED'
            offer.responded_at = timezone.now()
            offer.save()
            offer.application.status = 'OFFER_REJECTED'
            offer.application.save()
            return Response({'status': 'rejected'})
        return Response({'error': 'Invalid action'}, status=400)


class AnnouncementViewSet(viewsets.ModelViewSet):
    """API endpoint for announcements."""
    permission_classes = [IsAuthenticated]
    serializer_class = AnnouncementSerializer
    queryset = Announcement.objects.filter(is_active=True)

    def perform_create(self, serializer):
        if not _is_tpo_or_chairman(self.request.user):
            raise PermissionError("Not authorized")
        serializer.save(created_by=self.request.user)


# =============================================
# PCMS FUNCTION-BASED VIEWS
# =============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def placement_stats_pcms_api(request):
    """Get PCMS placement statistics."""
    year = request.query_params.get('year')
    stats = get_placement_statistics(year=year)
    return Response(stats)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def my_application_summary_api(request):
    """Get current student's application summary."""
    profile = get_object_or_404(ExtraInfo, user=request.user)
    try:
        student = Student.objects.get(id=profile)
    except Student.DoesNotExist:
        return Response({'error': 'Student not found'}, status=404)

    summary = get_student_application_summary(student)
    # Remove queryset from summary for JSON serialization
    apps = JobApplicationSerializer(summary.pop('applications'), many=True).data
    summary['applications'] = apps
    return Response(summary)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def dashboard_api(request):
    """PCMS dashboard summary data."""
    user = request.user
    is_chairman_val = _is_chairman(user)
    is_officer_val = _is_officer(user)
    is_student_val = _is_student(user)

    data = {
        'is_chairman': is_chairman_val,
        'is_officer': is_officer_val,
        'is_student': is_student_val,
    }

    if is_student_val:
        student = _get_student(user)
        if student:
            active_postings = JobPosting.objects.filter(is_active=True).count()
            my_apps = JobApplication.objects.filter(student=student).count()
            my_offers_count = JobOffer.objects.filter(
                application__student=student, status='PENDING'
            ).count()
            announcements = Announcement.objects.filter(is_active=True)[:5]

            data.update({
                'active_postings': active_postings,
                'my_apps': my_apps,
                'my_offers_count': my_offers_count,
                'recent_announcements': AnnouncementSerializer(announcements, many=True).data,
            })
    elif is_officer_val or is_chairman_val:
        data.update({
            'total_companies': Company.objects.filter(approval_status='APPROVED').count(),
            'pending_companies': Company.objects.filter(approval_status='PENDING').count(),
            'active_postings': JobPosting.objects.filter(is_active=True).count(),
            'total_applications': JobApplication.objects.count(),
            'pending_offers': JobOffer.objects.filter(status='PENDING').count(),
            'accepted_offers': JobOffer.objects.filter(status='ACCEPTED').count(),
            'recent_applications': JobApplicationSerializer(
                JobApplication.objects.select_related(
                    'student__id__user', 'job_posting__company'
                ).order_by('-applied_at')[:10],
                many=True
            ).data,
        })

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def reports_api(request):
    """Generate placement reports and analytics."""
    year_filter = request.query_params.get('year')
    dept_filter = request.query_params.get('department')
    prog_filter = request.query_params.get('programme')
    job_type_filter = request.query_params.get('job_type')

    stats = get_placement_statistics(year=year_filter)

    offers_qs = JobOffer.objects.filter(status='ACCEPTED').select_related(
        'application__student__id__department',
        'application__student',
        'application__job_posting__company'
    )

    if year_filter:
        offers_qs = offers_qs.filter(application__job_posting__created_at__year=year_filter)
    if dept_filter:
        offers_qs = offers_qs.filter(application__student__id__department__name=dept_filter)
    if prog_filter:
        offers_qs = offers_qs.filter(application__student__programme=prog_filter)
    if job_type_filter:
        offers_qs = offers_qs.filter(application__job_posting__job_type=job_type_filter)

    companies_participated = Company.objects.filter(
        approval_status='APPROVED',
        job_postings__is_active=True
    ).distinct().count()

    total_students = Student.objects.count()
    placed_students = JobOffer.objects.filter(status='ACCEPTED').values(
        'application__student'
    ).distinct().count()

    placement_rate = (placed_students / total_students * 100) if total_students > 0 else 0

    return Response({
        'stats': stats,
        'offers': JobOfferSerializer(offers_qs, many=True).data,
        'companies_participated': companies_participated,
        'total_students': total_students,
        'placed_students': placed_students,
        'placement_rate': round(placement_rate, 2),
    })


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def policies_api(request):
    """Manage placement policies."""
    if request.method == 'GET':
        policies = PlacementPolicy.objects.all()
        return Response(PlacementPolicySerializer(policies, many=True).data)

    elif request.method == 'POST':
        if not _is_tpo_or_chairman(request.user):
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

        action_type = request.data.get('action', 'create')

        if action_type == 'create':
            serializer = PlacementPolicySerializer(data=request.data)
            if serializer.is_valid():
                PlacementPolicy.objects.update(is_active=False)
                serializer.save(is_active=True)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif action_type == 'toggle':
            policy_id = request.data.get('policy_id')
            try:
                policy = PlacementPolicy.objects.get(id=policy_id)
                if not policy.is_active:
                    PlacementPolicy.objects.update(is_active=False)
                    policy.is_active = True
                else:
                    policy.is_active = False
                policy.save()
                return Response(PlacementPolicySerializer(policy).data)
            except PlacementPolicy.DoesNotExist:
                return Response({'error': 'Policy not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)


# =============================================
# INTERVIEW MANAGEMENT
# =============================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def interviews_api(request):
    """List or create interview schedules."""
    if request.method == 'GET':
        interviews = InterviewSchedule.objects.select_related(
            'job_posting', 'job_posting__company'
        ).all().order_by('-date')
        return Response(InterviewScheduleSerializer(interviews, many=True).data)

    elif request.method == 'POST':
        if not _is_tpo_or_chairman(request.user):
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

        serializer = InterviewScheduleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def interview_detail_api(request, interview_id):
    """Get or update an interview schedule."""
    interview = get_object_or_404(InterviewSchedule, id=interview_id)

    if request.method == 'GET':
        panelists = InterviewPanel.objects.filter(
            interview=interview
        ).select_related('application', 'application__student', 'application__student__id__user')

        return Response({
            'interview': InterviewScheduleSerializer(interview).data,
            'panelists': InterviewPanelSerializer(panelists, many=True).data,
        })

    elif request.method == 'PUT':
        if not _is_tpo_or_chairman(request.user):
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

        serializer = InterviewScheduleSerializer(interview, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
