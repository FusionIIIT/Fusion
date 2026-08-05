from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# --- Offer Detail and Respond APIs ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def offer_detail_api(request, offer_id):
    """Return offer details for a student (PlacementStatus)."""
    student = selectors.get_student_for_user(request.user)
    offer = PlacementStatus.objects.select_related('notify_id').filter(pk=offer_id, unique_id=student).first()
    if not offer:
        return Response({'detail': 'Offer not found.'}, status=status.HTTP_404_NOT_FOUND)
    notify = offer.notify_id
    schedule = PlacementSchedule.objects.select_related('role').filter(notify_id=notify).order_by('-id').first()
    response_deadline = offer.timestamp + datetime.timedelta(days=offer.no_of_days) if offer.timestamp else None
    data = {
        'id': offer.id,
        'schedule_id': schedule.id if schedule else None,
        'company_name': notify.company_name,
        'role': schedule.get_role if schedule else '',
        'ctc': str(notify.ctc),
        'invitation': offer.invitation,
        'response_deadline': response_deadline.isoformat() if response_deadline else None,
        'deadline_hours': offer.no_of_days * 24,
    }
    return Response(data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def offer_respond_api(request, offer_id):
    """Accept or decline an offer (PlacementStatus)."""
    student = selectors.get_student_for_user(request.user)
    offer = PlacementStatus.objects.select_related('notify_id').filter(pk=offer_id, unique_id=student).first()
    if not offer:
        return Response({'detail': 'Offer not found.'}, status=status.HTTP_404_NOT_FOUND)
    action = str(request.data.get('action', '')).upper()
    if offer.invitation != 'PENDING':
        return Response({'detail': 'This invitation has already been responded to.'}, status=status.HTTP_409_CONFLICT)
    deadline = offer.timestamp + datetime.timedelta(days=offer.no_of_days)
    current_time = timezone.now()
    if timezone.is_naive(deadline) and timezone.is_aware(current_time):
        current_time = timezone.make_naive(current_time)
    elif timezone.is_aware(deadline) and timezone.is_naive(current_time):
        current_time = timezone.make_aware(current_time)
    if current_time > deadline:
        offer.invitation = 'IGNORE'
        offer.save()
        return Response({'detail': 'This placement invitation has expired.'}, status=status.HTTP_403_FORBIDDEN)
    if action == 'ACCEPTED':
        # Only allow if no other accepted offer
        blocking_offer = PlacementStatus.objects.filter(unique_id=student, invitation='ACCEPTED').exclude(pk=offer.pk).exists()
        if blocking_offer:
            return Response({'detail': 'You already have an accepted offer and cannot accept another.'}, status=status.HTTP_409_CONFLICT)
        offer.invitation = 'ACCEPTED'
        offer.timestamp = timezone.now()
        offer.save()
        officer_recipients = User.objects.filter(
            current_designation__designation__name__in=['placement officer', 'placement chairman'],
        ).distinct()
        _send_placement_notifications(
            actor=request.user,
            recipients=list(officer_recipients),
            description='{} accepted the offer for {}.'.format(student.id.id, offer.notify_id.company_name),
        )
        return Response({'message': 'Offer accepted successfully.'}, status=status.HTTP_200_OK)
    elif action == 'REJECTED':
        offer.invitation = 'REJECTED'
        offer.timestamp = timezone.now()
        offer.save()
        officer_recipients = User.objects.filter(
            current_designation__designation__name__in=['placement officer', 'placement chairman'],
        ).distinct()
        _send_placement_notifications(
            actor=request.user,
            recipients=list(officer_recipients),
            description='{} declined the offer for {}.'.format(student.id.id, offer.notify_id.company_name),
        )
        return Response({'message': 'Offer declined successfully.'}, status=status.HTTP_200_OK)
    else:
        return Response({'detail': 'Invalid action.'}, status=status.HTTP_400_BAD_REQUEST)
from .serializers import (PlacementAppealSerializer,
                          PlacementAnnouncementSerializer,
                          PlacementAnnouncementWriteSerializer,
                          OffCampusPlacementSerializer,
                          OffCampusPlacementWriteSerializer,
                          PlacementCalendarEventSerializer)
from applications.placement_cell.models import PlacementAppeal

# PlacementAppeal API
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def placement_appeal_list_create_api(request):
    if request.method == 'GET':
        appeals = PlacementAppeal.objects.select_related(
            'student__id__user',
            'placement_status__notify_id',
        ).order_by('-created_at')
        if not _is_tpo_user(request.user):
            student = selectors.get_student_for_user(request.user)
            appeals = appeals.filter(student=student)
        return Response([_serialize_appeal(item) for item in appeals], status=status.HTTP_200_OK)

    student = selectors.get_student_for_user(request.user)
    placement_status = get_object_or_404(
        PlacementStatus.objects.select_related('notify_id'),
        pk=request.data.get('placement_status'),
        unique_id=student,
    )
    application = PlacementApplication.objects.filter(
        schedule__notify_id=placement_status.notify_id,
        student=student,
    ).first()
    if application is None or application.status != 'reject':
        return Response(
            {'detail': 'Appeals can only be raised after an application is rejected.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if PlacementAppeal.objects.filter(student=student, placement_status=placement_status).exists():
        return Response(
            {'detail': 'An appeal has already been submitted for this rejection.'},
            status=status.HTTP_409_CONFLICT,
        )
    reason = (request.data.get('reason') or '').strip()
    if not reason:
        return Response({'reason': ['This field is required.']}, status=status.HTTP_400_BAD_REQUEST)
    appeal = PlacementAppeal.objects.create(
        student=student,
        placement_status=placement_status,
        reason=reason,
    )
    officer_recipients = User.objects.filter(
        current_designation__designation__name__in=['placement officer', 'placement chairman'],
    ).distinct()
    _send_placement_notifications(
        actor=request.user,
        recipients=list(officer_recipients),
        description='{} submitted an appeal for {}.'.format(student.id.id, placement_status.notify_id.company_name),
    )
    return Response(_serialize_appeal(appeal), status=status.HTTP_201_CREATED)

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def placement_appeal_detail_api(request, pk):
    appeal = get_object_or_404(
        PlacementAppeal.objects.select_related(
            'student__id__user',
            'placement_status__notify_id',
        ),
        pk=pk,
    )
    is_tpo = _is_tpo_user(request.user)
    if not is_tpo:
        student = selectors.get_student_for_user(request.user)
        if appeal.student_id != student.id:
            return Response({'detail': 'Appeal not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(_serialize_appeal(appeal), status=status.HTTP_200_OK)

    if not is_tpo:
        return Response({'detail': 'Only TPO users can update appeals.'}, status=status.HTTP_403_FORBIDDEN)
    next_status = str(request.data.get('status') or '').lower()
    if next_status not in ['pending', 'reviewed', 'accepted', 'rejected']:
        return Response({'status': ['Invalid appeal status.']}, status=status.HTTP_400_BAD_REQUEST)
    appeal.status = next_status
    appeal.response = request.data.get('response', appeal.response)
    appeal.reviewed_at = timezone.now() if next_status != 'pending' else None
    appeal.save(update_fields=['status', 'response', 'reviewed_at'])
    _send_placement_notifications(
        actor=request.user,
        recipients=[appeal.student.id.user],
        description='Your placement appeal for {} has been updated to {}.'.format(
            appeal.placement_status.notify_id.company_name,
            next_status,
        ),
    )
    return Response(_serialize_appeal(appeal), status=status.HTTP_200_OK)
import os
import shutil
import datetime
import decimal
import zipfile
import xlwt
import logging
import json
from collections import defaultdict

from html import escape
from datetime import date
from io import BytesIO
from wsgiref.util import FileWrapper
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.core.validators import validate_email
from django.db.models import Count, Max, Prefetch, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import get_template, render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from django.utils.encoding import smart_str
from xhtml2pdf import pisa
from django.core import serializers
from notifications.signals import notify
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from applications.academic_information.models import Student
from notification.views import placement_cell_notif
from applications.globals.models import (DepartmentInfo, ExtraInfo,
                                        HoldsDesignation, Designation)
from .. import selectors, services

from ..models import (Achievement, ChairmanVisit, Course, Education, Experience, Conference,
                     Has, NotifyStudent, Patent, PlacementRecord, Extracurricular, Reference,
                     PlacementSchedule, PlacementStatus, Project, Publication,
                     Skill, StudentPlacement, StudentRecord, Role, CompanyDetails,
                     PlacementField, PlacementApplication, PlacementApplicationResponse,
                     PlacementRound, PlacementRestriction, PlacementPolicy, PlacementProfileDocument,
                     PlacementProfileAuditLog, PlacementNotificationPreference,
                     PlacementReportSchedule, AlumniConnection, AlumniMentorshipSession, AlumniProfile,
                     AlumniReferral, PlacementApplicationTimeline, PlacementInterviewSchedule,
                     PlacementAnnouncement, OffCampusPlacement, PlacementCalendarEvent)
'''
    @variables:
            user - logged in user
            profile - variable for extrainfo
            studentrecord - storing all fetched student record from database
            years - yearwise record of student placement
            records - all the record of placement record table
            tcse - all record of cse
            tece - all record of ece
            tme - all record of me
            tadd - all record of student
            form respective form object
            stuname - student name obtained from the form
            ctc - salary offered obtained from the form
            cname - company name obtained from the form
            rollno - roll no of student obtained from the form
            year - year of placement obtained from the form
            s - extra info data of the student obtained from the form
            p - placement data of the student obtained from the form
            placementrecord - placement record of the student obtained from the form
            pbirecord - pbi data of the student obtained from the form
            test_type - type of higher study test obtained from the form
            uname - name of universty obtained from the form
            test_score - score in the test obtained from the form
            higherrecord - higher study record of the student obtained from the form
            current - current user on a particular designation
            status - status of the sent invitation by placement cell regarding placement/pbi
            institute - institute for previous education obtained from the form
            degree - degree for previous education obtained from the form
            grade - grade for previous education obtained from the form
            stream - stream for previous education obtained from the form
            sdate - start date for previous education obtained from the form
            edate - end date for previous education obtained from the form
            education_obj - object variable of Education table
            about_me - about me data obtained from the form
            age - age data obtained from the form
            address - address obtained from the form
            contact - contact obtained from the form
            pic - picture obtained from the form
            skill - skill of the user obtained from the form
            skill_rating - rating of respective skill obtained from the form
            has_obj - object variable of Has table
            achievement - achievement of user obtained from the form
            achievement_type - type of achievement obtained from the form
            description - description of respective achievement obtained from the form
            issuer - certifier of respective achievement obtained from the form
            date_earned - date of the respective achievement obtained from the form
            achievement_obj - object variable of Achievement table
            publication_title - title of the publication obtained from the form
            description - description of respective publication obtained from the form
            publisher - publisher of respective publication obtained from the form
            publication_date - date of respective publication obtained from the form
            publication_obj - object variable of Publication table
            patent_name - name of patent obtained from the form
            description - description of respective patent obtained from the form
            patent_office - office of respective patent obtained from the form
            patent_date - date of respective patent obtained from the form
            patent_obj - object variable of Patent table
            course_name - name of the course obtained from the form
            description description of respective course obtained from the form
            license_no - license_no of respective course obtained from the form
            sdate - start date of respective course obtained from the form
            edate - end date of respective course obtained from the form
            course_obj - object variable of Course table
            project_name - name of project obtained from the form
            project_status - status of respective project obtained from the form
            summary - summery of the respective project obtained from the form
            project_link - link of the respective project obtained from the form
            sdate - start date of respective project obtained from the form
            edate - end date of respective project obtained from the form
            project_obj - object variable of Project table
            title - title of any kind of experience obtained from the form
            status - status of the respective experience obtained from the form
            company - company from which respective experience is gained as obtained from the form
            location - location of the respective experience obtained from the form
            description - description of respective experience obtained from the form
            sdate - start date of respective experience obtained from the form
            edate - end date of respective experience obtained from the form
            experience_obj - object variable of Experience table
            context - to sent the relevant context for html rendering
            company_name - name of visiting comapany obtained from the form
            location -location of visiting company obtained from the form
            description - description of respective company obtained from the form
            visiting_date - visiting date of respective company obtained from the form
            visit_obj -object variable of ChairmanVisit table
            notify - object of NotifyStudent table
            schedule - object variable of PlacementSchedule table
            q1 - all data of Has table
            q3 - all data of Student table
            st - all data of Student table
            spid - id of student to be debar
            sr - record from StudentPlacement of student having id=spid
            achievementcheck - checking for achievent to be shown in cv
            educationcheck - checking for education to be shown in cv
            publicationcheck - checking for publication to be shown in cv
            patentcheck - checking for patent to be shown in cv
            internshipcheck - checking for internship to be shown in cv
            projectcheck - checking for project to be shown in cv
            coursecheck - checking for course to be shown in cv
            skillcheck - checking for skill to be shown in cv
'''

logger = logging.getLogger('django.server')


def _today():
    return timezone.now().date()


# Ajax for the company name dropdown for CompanyName when filling AddSchedule


# Ajax for all the roles in the dropdown


def render_to_pdf(template_src, context_dict):
    """
    The function is used to generate the cv in the pdf format.
    Embeds the data into the predefined template.
    @param:
            template_src - template of cv to be rendered
            context_dict - data fetched from the dtatabase to be filled in the cv template
    @variables:
            template - stores the template
            html - html rendered pdf
            result - variable to store data in BytesIO
            pdf - storing encoded html of pdf version
    """
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(
        BytesIO(html.encode("UTF-8")),
        result,
        link_callback=_pdf_link_callback,
    )
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return HttpResponse('We had some errors<pre>%s</pre>' % escape(html))


def _pdf_link_callback(uri, rel):
    if uri.startswith(settings.MEDIA_URL):
        path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, '', 1))
    elif uri.startswith(settings.STATIC_URL) and getattr(settings, 'STATIC_ROOT', None):
        path = os.path.join(settings.STATIC_ROOT, uri.replace(settings.STATIC_URL, '', 1))
    else:
        path = uri

    if not os.path.isfile(path):
        return uri
    return path


def export_to_xls_std_records(qs):
    """
    The function is used to generate the file in the xls format.
    Embeds the data into the file.
    """
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="report.xls"'

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Report')

    # Sheet header, first row
    row_num = 0

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    columns = ['Roll No.', 'Name', 'CPI', 'Department', 'Discipline', 'Placed', 'Debarred' ]

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()

    for student in qs:
        row_num += 1

        row = []
        row.append(student.id.id)
        row.append(student.id.user.first_name+' '+student.id.user.last_name)
        row.append(student.cpi)
        row.append(student.programme)
        row.append(student.id.department.name)
        if student.studentplacement.placed_type == "PLACED":
            row.append('Yes')
        else:
            row.append('No')
        if student.studentplacement.placed_type == "DEBAR":
            row.append('Yes')
        else:
            row.append('No')

        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)

    wb.save(response)
    return response


def export_to_xls_invitation_status(qs):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="report.xls"'

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Report')

    # Sheet header, first row
    row_num = 0

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    columns = ['Roll No.', 'Name', 'Company', 'CTC', 'Invitation Status']

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()

    for student in qs:
        row_num += 1

        row = []
        row.append(student.unique_id.id.id)
        row.append(student.unique_id.id.user.first_name+' '+student.unique_id.id.user.last_name)
        row.append(student.notify_id.company_name)
        row.append(student.notify_id.ctc)
        row.append(student.invitation)

        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)

    wb.save(response)
    return response


def check_invitation_date(placementstatus):
    """
    The function is used to run before render of student placement view for ensuring that
    last date for RESPONSE is not passed
    @param:
            placementstatus - queryset containing placement status of particular student
    @variables:
            ps - individual PlacementStatus object
    """
    try:
        for ps in placementstatus:
            if ps.invitation=='PENDING':
                dt = ps.timestamp+datetime.timedelta(days=ps.no_of_days)
                if dt<datetime.datetime.now():
                    #print('---------- time limit is finished---------------- \n\n\n\n\n')
                    ps.invitation = 'IGNORE'
                    ps.save()
    except Exception as e:
        print('---------------------Error Occurred ---------------')
        print(e)

    return


#saves added details in PlacementSchedule table


def _normalize_placement_type(value):
    normalized = (value or '').strip().upper()
    mapping = {
        'PLACEMENT': 'PLACEMENT',
        'PBI': 'PBI',
        'INTERNSHIP': 'PBI',
        'HIGHER STUDIES': 'HIGHER STUDIES',
        'OTHER': 'OTHER',
    }
    return mapping.get(normalized, 'PLACEMENT')


def _parse_decimal(value, default='0'):
    try:
        return decimal.Decimal(str(value if value not in [None, ''] else default))
    except Exception:
        return decimal.Decimal(default)


def _parse_date(value):
    if not value:
        return None
    if isinstance(value, datetime.date):
        return value
    try:
        return datetime.datetime.strptime(str(value), '%Y-%m-%d').date()
    except Exception:
        return None


def _parse_time(value):
    if not value:
        return None
    if isinstance(value, datetime.time):
        return value
    text = str(value)
    for fmt in ('%H:%M:%S', '%H:%M'):
        try:
            return datetime.datetime.strptime(text, fmt).time()
        except Exception:
            continue
    return None


def _parse_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime.datetime):
        return value
    text = str(value).replace('T', ' ')
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'):
        try:
            return datetime.datetime.strptime(text, fmt)
        except Exception:
            continue
    return None


def _ensure_naive_datetime(value):
    if not value:
        return None
    if timezone.is_aware(value):
        return timezone.make_naive(value)
    return value


def _schedule_range_for_schedule(schedule):
    start_dt = _ensure_naive_datetime(schedule.schedule_at)
    end_dt = _ensure_naive_datetime(schedule.end_datetime)

    if not start_dt and schedule.placement_date and schedule.time:
        start_dt = datetime.datetime.combine(schedule.placement_date, schedule.time)
    elif not start_dt and schedule.placement_date:
        start_dt = datetime.datetime.combine(schedule.placement_date, datetime.time.min)

    if start_dt and not end_dt:
        end_dt = start_dt + datetime.timedelta(hours=1)

    return start_dt, end_dt


def _schedule_range_for_round(round_obj):
    start_dt = _ensure_naive_datetime(round_obj.start_datetime)
    end_dt = _ensure_naive_datetime(round_obj.end_datetime)

    if not start_dt and round_obj.test_date:
        start_dt = datetime.datetime.combine(round_obj.test_date, datetime.time.min)
        end_dt = datetime.datetime.combine(round_obj.test_date, datetime.time.max)
    elif start_dt and not end_dt:
        end_dt = start_dt + datetime.timedelta(hours=1)

    return start_dt, end_dt


def _ranges_overlap(start_a, end_a, start_b, end_b):
    if not start_a or not end_a or not start_b or not end_b:
        return False
    return start_a < end_b and start_b < end_a


def _collect_student_schedule_conflicts(applications, start_dt, end_dt, current_schedule_id):
    conflicts = []
    if not applications:
        return conflicts

    applications_by_student = defaultdict(list)
    for application in applications:
        applications_by_student[application.student_id].append(application)

    student_ids = list(applications_by_student.keys())
    other_applications = list(
        PlacementApplication.objects.select_related(
            'schedule__notify_id',
            'student__id__user',
        ).filter(
            student_id__in=student_ids,
        ).exclude(
            status__in=['reject', 'withdrawn'],
        ).exclude(
            schedule_id=current_schedule_id,
        )
    )
    applications_by_other_student = defaultdict(list)
    for other_application in other_applications:
        applications_by_other_student[other_application.student_id].append(
            other_application,
        )

    round_queryset = PlacementRound.objects.select_related('schedule__notify_id').filter(
        schedule_id__in=[item.schedule_id for item in other_applications],
    )
    rounds_by_schedule = defaultdict(list)
    for round_obj in round_queryset:
        rounds_by_schedule[round_obj.schedule_id].append(round_obj)

    for application in applications:
        student_label = (
            '{} ({})'.format(
                application.student.id.id,
                application.student.id.user.get_full_name().strip() or application.student.id.user.username,
            )
        )
        student_applications = applications_by_other_student.get(
            application.student_id,
            [],
        )

        for other_application in student_applications:
            schedule_start, schedule_end = _schedule_range_for_schedule(other_application.schedule)
            if _ranges_overlap(start_dt, end_dt, schedule_start, schedule_end):
                conflicts.append(
                    '{} has placement event conflict with {}.'.format(
                        student_label,
                        other_application.schedule.notify_id.company_name,
                    )
                )
                break

            round_conflict_found = False
            for round_obj in rounds_by_schedule.get(other_application.schedule_id, []):
                round_start, round_end = _schedule_range_for_round(round_obj)
                if _ranges_overlap(start_dt, end_dt, round_start, round_end):
                    conflicts.append(
                        '{} has interview conflict with {} - {}.'.format(
                            student_label,
                            other_application.schedule.notify_id.company_name,
                            round_obj.test_type or 'Round {}'.format(round_obj.round_no),
                        )
                    )
                    round_conflict_found = True
                    break
            if round_conflict_found:
                break

    return conflicts


def _get_field_ids_from_request(request):
    field_ids = request.data.getlist('fields') if hasattr(request.data, 'getlist') else []
    if not field_ids:
        raw_fields = request.data.get('fields')
        if isinstance(raw_fields, (list, tuple)):
            field_ids = list(raw_fields)
        elif raw_fields:
            if isinstance(raw_fields, str) and raw_fields.startswith('['):
                try:
                    parsed = json.loads(raw_fields)
                    field_ids = parsed if isinstance(parsed, list) else [parsed]
                except Exception:
                    field_ids = [item.strip() for item in raw_fields.split(',') if item.strip()]
            else:
                field_ids = [item.strip() for item in str(raw_fields).split(',') if item.strip()]
    cleaned = []
    for field_id in field_ids:
        try:
            cleaned.append(int(field_id))
        except Exception:
            continue
    return cleaned


def _ensure_studentplacement(student):
    return StudentPlacement.objects.get_or_create(unique_id=student)[0]


def _ensure_notification_preferences(student):
    return PlacementNotificationPreference.objects.get_or_create(student=student)[0]


def _log_profile_action(student, actor, action, details=None):
    PlacementProfileAuditLog.objects.create(
        student=student,
        actor=actor if getattr(actor, 'is_authenticated', False) else None,
        action=action,
        details=details or {},
    )


def _serialize_profile_document(document, request=None):
    url = document.document.url if document.document else None
    if url and request is not None:
        url = request.build_absolute_uri(url)
    return {
        'id': document.id,
        'name': document.name,
        'url': url,
        'uploaded_at': document.uploaded_at.isoformat() if document.uploaded_at else None,
    }


def _serialize_audit_log(entry):
    actor = None
    if entry.actor:
        actor = entry.actor.get_full_name().strip() or entry.actor.username
    return {
        'id': entry.id,
        'action': entry.action,
        'details': entry.details or {},
        'actor': actor,
        'created_at': entry.created_at.isoformat() if entry.created_at else None,
    }


def _serialize_profile(student):
    profile = student.id
    return {
        'first_name': profile.user.first_name or '',
        'last_name': profile.user.last_name or '',
        'email': profile.user.email or '',
        'phone_no': str(profile.phone_no or ''),
        'address': profile.address or '',
        'about_me': profile.about_me if profile.about_me != 'NA' else '',
        'branch': profile.department.name if profile.department else '',
        'cpi': float(student.cpi) if student.cpi is not None else None,
        'passout_year': student.batch,
        'programme': student.programme or '',
    }


def _sanitize_profile_payload(data):
    return {
        'first_name': strip_tags(str(data.get('first_name') or '')).strip(),
        'last_name': strip_tags(str(data.get('last_name') or '')).strip(),
        'email': str(data.get('email') or '').strip(),
        'phone_no': ''.join(ch for ch in str(data.get('phone_no') or '') if ch.isdigit()),
        'address': strip_tags(str(data.get('address') or '')).strip(),
        'about_me': strip_tags(str(data.get('about_me') or '')).strip(),
    }


def _profile_form_errors(data):
    errors = {}
    if not data['first_name']:
        errors['first_name'] = ['First name is required.']
    if not data['last_name']:
        errors['last_name'] = ['Last name is required.']
    if not data['email']:
        errors['email'] = ['Email address is required.']
    else:
        try:
            validate_email(data['email'])
        except ValidationError:
            errors['email'] = ['Enter a valid email address.']
    if len(data['phone_no']) < 10:
        errors['phone_no'] = ['Enter a valid 10-digit phone number.']
    if not data['address']:
        errors['address'] = ['Address is required.']
    if not data['about_me']:
        errors['about_me'] = ['About me is required.']
    return errors


def _profile_completion_errors(student):
    errors = dict(_profile_form_errors(_serialize_profile(student)))
    if not Education.objects.filter(unique_id=student).exists():
        errors['education'] = ['At least one education entry is required.']
    if not Project.objects.filter(unique_id=student).exists():
        errors['projects'] = ['At least one project entry is required.']
    if not Has.objects.filter(unique_id=student).exists():
        errors['skills'] = ['At least one skill entry is required.']
    if not PlacementProfileDocument.objects.filter(student=student).exists():
        errors['documents'] = ['At least one placement document (PDF/JPG/PNG) is required.']
    return errors


def _flatten_profile_errors(errors):
    flattened = []
    for messages_list in errors.values():
        flattened.extend(messages_list)
    return flattened


def _validate_profile_document(file_obj):
    if not file_obj:
        return
    filename = (file_obj.name or '').lower()
    allowed_extensions = ('.pdf', '.jpg', '.jpeg', '.png')
    if not filename.endswith(allowed_extensions):
        raise ValidationError('Only PDF, JPG, JPEG, and PNG documents are allowed.')
    if getattr(file_obj, 'size', 0) > 5 * 1024 * 1024:
        raise ValidationError('Document size must be 5MB or less.')


def _profile_validation_errors(student):
    return _flatten_profile_errors(_profile_completion_errors(student))


def _serialize_profile_eligibility_summary(student):
    schedules = PlacementSchedule.objects.select_related(
        'notify_id',
        'role',
    ).filter(
        placement_date__gte=_today(),
    ).order_by('placement_date', 'id')
    summary = []
    for schedule in schedules:
        eligibility = _schedule_eligibility(schedule, student)
        summary.append({
            'schedule_id': schedule.id,
            'company_name': schedule.notify_id.company_name,
            'role': schedule.get_role or '',
            'placement_date': schedule.placement_date.isoformat() if schedule.placement_date else None,
            'eligible': eligibility['eligible'],
            'reasons': eligibility['reasons'],
        })
    return {
        'eligible_count': sum(1 for item in summary if item['eligible']),
        'ineligible_count': sum(1 for item in summary if not item['eligible']),
        'jobs': summary[:10],
    }


def _is_report_admin(user):
    return bool(
        _is_tpo_user(user) or selectors.get_designation_queryset(user, "placement chairman")
    )


def _add_working_days(start, days):
    current = start
    remaining = days
    while remaining > 0:
        current += datetime.timedelta(days=1)
        if current.weekday() < 5:
            remaining -= 1
    return current


def _serialize_appeal(appeal):
    due_by = _add_working_days(appeal.created_at, 5) if appeal.created_at else None
    return {
        'id': appeal.id,
        'student': {
            'roll_no': appeal.student.id.id,
            'name': appeal.student.id.user.get_full_name().strip() or appeal.student.id.user.username,
            'email': appeal.student.id.user.email,
        },
        'placement_status': appeal.placement_status.id,
        'company_name': appeal.placement_status.notify_id.company_name,
        'reason': appeal.reason,
        'status': appeal.status,
        'response': appeal.response,
        'created_at': appeal.created_at.isoformat() if appeal.created_at else None,
        'reviewed_at': appeal.reviewed_at.isoformat() if appeal.reviewed_at else None,
        'due_by': due_by.isoformat() if due_by else None,
        'overdue': bool(due_by and appeal.status == 'pending' and timezone.now() > due_by),
    }


def _get_report_records(request):
    records = StudentRecord.objects.select_related(
        'record_id',
        'unique_id__id__user',
        'unique_id__id__department',
    ).filter(
        record_id__placement_type__in=['PLACEMENT', 'PBI'],
    )
    company = request.GET.get('company')
    if company:
        records = records.filter(record_id__name__icontains=company)
    ctc_min = request.GET.get('ctc_min')
    if ctc_min not in [None, '']:
        records = records.filter(record_id__ctc__gte=_parse_decimal(ctc_min))
    ctc_max = request.GET.get('ctc_max')
    if ctc_max not in [None, '']:
        records = records.filter(record_id__ctc__lte=_parse_decimal(ctc_max))
    year = request.GET.get('year')
    if year not in [None, '']:
        records = records.filter(record_id__year=year)
    department = request.GET.get('department') or request.GET.get('branch')
    if department:
        records = records.filter(unique_id__id__department__name__iexact=department)
    placement_type = request.GET.get('placement_type')
    if placement_type:
        records = records.filter(record_id__placement_type=placement_type)
    return records


def _serialize_student_record(student_record):
    return {
        'id': student_record.record_id.id,
        'first_name': '{} {}'.format(
            student_record.unique_id.id.user.first_name,
            student_record.unique_id.id.user.last_name,
        ).strip() or student_record.unique_id.id.user.username,
        'roll_no': student_record.unique_id.id.id,
        'placement_name': student_record.record_id.name,
        'batch': student_record.record_id.year,
        'branch': student_record.unique_id.id.department.name if student_record.unique_id.id.department else '',
        'ctc': str(student_record.record_id.ctc),
        'placement_type': student_record.record_id.placement_type,
    }


def _build_report_payload(request):
    records = _get_report_records(request)
    report_type = (request.GET.get('report_type') or 'custom').strip().lower()
    if report_type == 'batch':
        summary = records.values('record_id__year').annotate(
            count=Count('id'),
        ).order_by('-record_id__year')
        columns = ['batch', 'count']
        rows = [
            {'batch': item['record_id__year'], 'count': item['count']}
            for item in summary
        ]
    elif report_type == 'company':
        summary = records.values('record_id__name').annotate(
            count=Count('id'),
        ).order_by('record_id__name')
        columns = ['company', 'count']
        rows = [
            {'company': item['record_id__name'], 'count': item['count']}
            for item in summary
        ]
    elif report_type == 'branch':
        summary = records.values('unique_id__id__department__name').annotate(
            count=Count('id'),
        ).order_by('unique_id__id__department__name')
        columns = ['branch', 'count']
        rows = [
            {
                'branch': item['unique_id__id__department__name'] or 'Unassigned',
                'count': item['count'],
            }
            for item in summary
        ]
    else:
        columns = ['student_name', 'roll_no', 'company', 'batch', 'branch', 'ctc', 'placement_type']
        rows = [
            {
                'student_name': item['first_name'],
                'roll_no': item['roll_no'],
                'company': item['placement_name'],
                'batch': item['batch'],
                'branch': item['branch'],
                'ctc': item['ctc'],
                'placement_type': item['placement_type'],
            }
            for item in [_serialize_student_record(record) for record in records.order_by('-record_id__year', '-record_id__id')]
        ]
    return {
        'report_type': report_type,
        'columns': columns,
        'rows': rows,
        'filters': {
            key: request.GET.get(key)
            for key in ['company', 'ctc_min', 'ctc_max', 'year', 'department', 'branch', 'placement_type']
            if request.GET.get(key) not in [None, '']
        },
    }


def _build_report_pdf_response(payload):
    title_map = {
        'batch': 'Batch Placement Report',
        'company': 'Company Placement Report',
        'branch': 'Branch Placement Report',
        'custom': 'Custom Placement Report',
    }
    header_html = ''.join(
        f'<th style="padding:8px;border:1px solid #ccc;">{escape(str(column).replace("_", " ").title())}</th>'
        for column in payload['columns']
    )
    row_html = ''.join(
        '<tr>{}</tr>'.format(''.join(
            f'<td style="padding:8px;border:1px solid #ccc;">{escape(str(row.get(column, "")))}</td>'
            for column in payload['columns']
        ))
        for row in payload['rows']
    ) or '<tr><td style="padding:8px;border:1px solid #ccc;" colspan="{}">No records found.</td></tr>'.format(
        len(payload['columns']) or 1,
    )
    filter_html = ''.join(
        f'<li><strong>{escape(key.replace("_", " ").title())}:</strong> {escape(str(value))}</li>'
        for key, value in payload['filters'].items()
    ) or '<li>No filters applied.</li>'
    html = f"""
    <html>
      <body>
        <h2>{escape(title_map.get(payload['report_type'], 'Placement Report'))}</h2>
        <p>Generated on {escape(timezone.now().strftime('%Y-%m-%d %H:%M'))}</p>
        <h4>Filters</h4>
        <ul>{filter_html}</ul>
        <table cellspacing="0" cellpadding="0" style="border-collapse:collapse;width:100%;">
          <thead><tr>{header_html}</tr></thead>
          <tbody>{row_html}</tbody>
        </table>
      </body>
    </html>
    """
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode('utf-8')), result)
    if pdf.err:
        return Response({'detail': 'Could not generate PDF report.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    response = HttpResponse(result.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="placement_report.pdf"'
    return response


def _build_report_excel_response(payload):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="placement_report.xls"'
    workbook = xlwt.Workbook(encoding='utf-8')
    sheet = workbook.add_sheet('Report')
    header_style = xlwt.XFStyle()
    header_style.font.bold = True
    for idx, column in enumerate(payload['columns']):
        sheet.write(0, idx, str(column).replace('_', ' ').title(), header_style)
    for row_index, row in enumerate(payload['rows'], start=1):
        for col_index, column in enumerate(payload['columns']):
            sheet.write(row_index, col_index, str(row.get(column, '')))
    workbook.save(response)
    return response


def _serialize_report_schedule(item):
    return {
        'id': item.id,
        'name': item.name,
        'report_type': item.report_type,
        'frequency': item.frequency,
        'export_format': item.export_format,
        'filters': item.filters or {},
        'recipients': [entry.strip() for entry in (item.recipients or '').split(',') if entry.strip()],
        'is_active': item.is_active,
        'last_run_at': item.last_run_at.isoformat() if item.last_run_at else None,
        'created_at': item.created_at.isoformat() if item.created_at else None,
        'updated_at': item.updated_at.isoformat() if item.updated_at else None,
    }


def _coerce_decimal(value):
    try:
        return decimal.Decimal(str(value))
    except Exception:
        return None


def _matches_condition(actual, expected, condition):
    if actual is None:
        return False
    actual_value = str(actual).strip()
    expected_value = str(expected).strip()
    if condition == 'equals':
        return actual_value.lower() == expected_value.lower()
    if condition == 'not_equals':
        return actual_value.lower() != expected_value.lower()
    actual_decimal = _coerce_decimal(actual)
    expected_decimal = _coerce_decimal(expected)
    if actual_decimal is None or expected_decimal is None:
        return False
    if condition == 'gte':
        return actual_decimal >= expected_decimal
    if condition == 'gt':
        return actual_decimal > expected_decimal
    if condition == 'lte':
        return actual_decimal <= expected_decimal
    if condition == 'lt':
        return actual_decimal < expected_decimal
    return False


def _student_attribute_map(student):
    return {
        'cpi': student.cpi,
        'batch': student.batch,
        'passoutyr': student.batch,
        'department': student.id.department.name if student.id.department else '',
        'branch': student.id.department.name if student.id.department else '',
        'programme': student.programme,
        'gender': student.id.sex,
    }


def _schedule_eligibility(schedule, student, *, student_placement=None, restrictions=None):
    student_placement = student_placement or _ensure_studentplacement(student)
    reasons = []
    if student_placement.debar == 'DEBAR':
        reasons.append('Student is debarred.')

    student_attributes = _student_attribute_map(student)
    direct_checks = [
        ('cpi', schedule.cpi, 'gte', 'CPI requirement not met.'),
        ('passoutyr', schedule.passoutyr, 'equals', 'Passout year requirement not met.'),
        ('gender', schedule.gender, 'equals', 'Gender requirement not met.'),
    ]
    for attribute, expected, condition, message in direct_checks:
        if expected not in [None, ''] and not _matches_condition(student_attributes.get(attribute), expected, condition):
            reasons.append(message)

    if schedule.branch:
        allowed_branches = [item.strip().lower() for item in schedule.branch.split(',') if item.strip()]
        student_branch = str(student_attributes.get('branch') or '').strip().lower()
        if allowed_branches and student_branch not in allowed_branches:
            reasons.append('Branch requirement not met.')

    for restriction in (restrictions if restrictions is not None else PlacementRestriction.objects.all()):
        actual = student_attributes.get(restriction.criteria.lower())
        if actual is None:
            continue
        if not _matches_condition(actual, restriction.value, restriction.condition):
            reasons.append(restriction.description or '{} restriction not met.'.format(restriction.criteria))

    return {
        'eligible': len(reasons) == 0,
        'reasons': reasons,
    }


def _send_placement_notifications(*, actor, recipients, description):
    recipients = list(recipients)
    recipient_ids = [recipient.id for recipient in recipients if getattr(recipient, 'id', None)]
    student_map = {
        student.id.user_id: student
        for student in Student.objects.filter(id__user_id__in=recipient_ids).select_related('id__user')
    }
    preference_map = {
        preference.student_id: preference
        for preference in PlacementNotificationPreference.objects.filter(
            student_id__in=[student.pk for student in student_map.values()],
        )
    }

    for recipient in recipients:
        preference = None
        student = student_map.get(recipient.id)
        if student:
            preference = preference_map.get(student.pk)
            if preference is None:
                preference = _ensure_notification_preferences(student)
                preference_map[student.pk] = preference
        portal_enabled = True if preference is None else preference.enable_portal
        email_enabled = False if preference is None else preference.enable_email
        sms_enabled = False if preference is None else preference.enable_sms

        if portal_enabled:
            notify.send(
                sender=actor,
                recipient=recipient,
                verb=description,
                url='placement:placement',
                module='Placement Cell',
            )

        if email_enabled and recipient.email:
            send_mail(
                subject='Placement Cell Notification',
                message=description,
                from_email=getattr(settings, 'EMAIL_HOST_USER', None) or 'noreply@fusion.local',
                recipient_list=[recipient.email],
                fail_silently=True,
            )

        if sms_enabled:
            logger = logging.getLogger(__name__)
            logger.info('SMS notification queued for %s: %s', recipient.username, description)


def _application_stage_label(status_value):
    stage_map = {
        'pending': 'Under Review',
        'shortlisted': 'Shortlisted',
        'interview_scheduled': 'Interview Scheduled',
        'interview_completed': 'Interview Completed',
        'offer_released': 'Offer Released',
        'accept': 'Selected',
        'reject': 'Rejected',
        'withdrawn': 'Withdrawn',
    }
    return stage_map.get(status_value, 'Under Review')


def _create_application_timeline_entry(application, *, stage=None, remarks='', actor=None):
    return PlacementApplicationTimeline.objects.create(
        application=application,
        stage=stage or _application_stage_label(application.status),
        remarks=remarks or '',
        actor=actor,
    )


def _serialize_application_timeline(application):
    entries = [{
        'id': 'applied-{}'.format(application.id),
        'stage': 'Applied',
        'remarks': 'Application submitted',
        'actor': application.student.id.user.get_full_name().strip() or application.student.id.user.username,
        'created_at': application.created_at.isoformat() if application.created_at else None,
    }]
    entries.extend([{
        'id': item.id,
        'stage': item.stage,
        'remarks': item.remarks,
        'actor': item.actor.get_full_name().strip() if item.actor else '',
        'created_at': item.created_at.isoformat() if item.created_at else None,
    } for item in application.timeline_entries.select_related('actor').all()])
    return entries


def _serialize_application_interview(item):
    return {
        'id': item.id,
        'round_no': item.round_no,
        'title': item.title or 'Round {}'.format(item.round_no),
        'scheduled_at': item.scheduled_at.isoformat() if item.scheduled_at else None,
        'end_datetime': item.end_datetime.isoformat() if item.end_datetime else None,
        'mode': item.mode,
        'location': item.location,
        'meeting_link': item.meeting_link,
        'remarks': item.remarks,
        'feedback': item.remarks,
        'outcome': item.outcome,
        'is_active': item.is_active,
    }


def _ensure_placement_record_for_selection(application):
    student_record = StudentRecord.objects.filter(
        unique_id=application.student,
        record_id__name=application.schedule.notify_id.company_name,
        record_id__year=timezone.now().year,
        record_id__placement_type=application.schedule.notify_id.placement_type,
    ).select_related('record_id').first()
    if student_record:
        return student_record.record_id

    record = PlacementRecord.objects.create(
        placement_type=application.schedule.notify_id.placement_type,
        name=application.schedule.notify_id.company_name,
        ctc=application.schedule.notify_id.ctc,
        year=timezone.now().year,
        test_type=application.schedule.get_role or '',
        test_score=0,
    )
    StudentRecord.objects.get_or_create(record_id=record, unique_id=application.student)
    return record


def _serialize_tpo_application_detail(application, request=None):
    student_user = application.student.id.user
    offer = PlacementStatus.objects.filter(
        notify_id=application.schedule.notify_id,
        unique_id=application.student,
    ).first()
    responses = PlacementApplicationResponse.objects.select_related('field').filter(application=application)
    profile = application.student.id
    documents = PlacementProfileDocument.objects.filter(student=application.student).order_by('-uploaded_at', '-id')
    return {
        'id': application.id,
        'schedule_id': application.schedule_id,
        'status': application.status,
        'status_label': _application_stage_label(application.status),
        'remarks': application.remarks or '',
        'updated_at': application.updated_at.isoformat() if application.updated_at else None,
        'applied_at': application.created_at.isoformat() if application.created_at else None,
        'student': {
            'name': student_user.get_full_name().strip() or student_user.username,
            'roll_no': application.student.id.id,
            'email': student_user.email,
            'phone_no': str(profile.phone_no or ''),
            'address': profile.address or '',
            'about_me': profile.about_me if profile.about_me != 'NA' else '',
            'programme': application.student.programme or '',
            'branch': application.student.id.department.name if application.student.id.department else '',
            'cpi': application.student.cpi,
            'passout_year': application.student.batch,
        },
        'company': {
            'name': application.schedule.notify_id.company_name,
            'role': application.schedule.get_role or '',
            'ctc': str(application.schedule.notify_id.ctc),
            'placement_type': application.schedule.notify_id.placement_type,
        },
        'documents': [_serialize_profile_document(item, request=request) for item in documents],
        'resume': _serialize_profile_document(documents[0], request=request) if documents else None,
        'timeline': _serialize_application_timeline(application),
        'interviews': [
            _serialize_application_interview(item)
            for item in application.interview_schedules.all()
        ],
        'offer': {
            'id': offer.id,
            'invitation': offer.invitation,
            'timestamp': offer.timestamp.isoformat() if offer and offer.timestamp else None,
            'deadline_days': offer.no_of_days if offer else None,
        } if offer else None,
        'responses': [
            {
                'field': item.field.name if item.field else 'Response',
                'value': item.value,
            }
            for item in responses
        ],
    }


def _serialize_schedule(schedule, user, *, has_applied=False, eligibility=None):
    eligibility = eligibility or {'eligible': True, 'reasons': []}
    company = schedule.company
    application_fields = [{
        'field_id': field.id,
        'name': field.name,
        'type': field.type,
        'required': field.required,
    } for field in schedule.fields.all().order_by('name')]

    return {
        'id': str(schedule.id),
        'jobID': str(schedule.id),
        'company_name': schedule.notify_id.company_name,
        'location': schedule.location,
        'role_st': schedule.get_role or '',
        'placement_type': schedule.notify_id.placement_type,
        'schedule_at': schedule.schedule_at.isoformat() if schedule.schedule_at else '',
        'placement_date': schedule.placement_date.isoformat() if schedule.placement_date else '',
        'description': schedule.description or '',
        'ctc': str(schedule.notify_id.ctc),
        'check': has_applied,
        'time': schedule.time.isoformat() if schedule.time else '',
        'end_datetime': schedule.end_datetime.isoformat() if schedule.end_datetime else '',
        'attached_file_url': schedule.attached_file.url if schedule.attached_file else None,
        'eligible': eligibility['eligible'],
        'eligibility_reasons': eligibility['reasons'],
        'eligibility_criteria': [item.strip() for item in (schedule.eligibility or '').split(',') if item.strip()],
        'passout_year': schedule.passoutyr or '',
        'gender_requirement': schedule.gender or '',
        'cpi_requirement': schedule.cpi or '',
        'branch_requirement': schedule.branch or '',
        'company_details': {
            'description': company.description if company else '',
            'address': company.address if company else '',
            'website': company.website if company else '',
            'logo_url': company.logo.url if company and company.logo else None,
        },
        'application_fields': application_fields,
    }


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def placement_api(request):
    if request.method == 'GET':
        selected_role = cache.get('last_selected_role_{}'.format(request.user.id))
        has_student_designation = selectors.get_designation_queryset(
            request.user, "student"
        ).exists()
        has_tpo_designation = _is_tpo_user(request.user)
        is_student_view = selected_role == "student" and has_student_designation
        is_tpo_user = has_tpo_designation and not is_student_view
        schedules = PlacementSchedule.objects.select_related(
            'notify_id',
            'role',
            'company',
        ).prefetch_related(
            'fields',
        ).order_by('-placement_date', '-id')

        # Advanced search/filter
        company = request.GET.get('company')
        role = request.GET.get('role')
        location = request.GET.get('location')
        min_package = request.GET.get('min_package')
        max_package = request.GET.get('max_package')

        if company:
            schedules = schedules.filter(notify_id__company_name__icontains=company)
        if role:
            schedules = schedules.filter(role__role__icontains=role)
        if location:
            schedules = schedules.filter(location__icontains=location)
        if min_package:
            schedules = schedules.filter(notify_id__ctc__gte=min_package)
        if max_package:
            schedules = schedules.filter(notify_id__ctc__lte=max_package)

        if has_student_designation and not is_tpo_user:
            student = selectors.get_student_for_user(request.user)
            future_aspect = _ensure_studentplacement(student).future_aspect
            # Students should be able to see both placement and internship drives
            # on the placement schedule page. Higher studies remains separate.
            # The frontend exposes All / Active / Upcoming tabs, so students
            # need the full schedule list and the client can segment by date.
            if future_aspect == "HIGHER STUDIES":
                schedules = schedules.filter(notify_id__placement_type=future_aspect)
            else:
                schedules = schedules.filter(
                    notify_id__placement_type__in=["PLACEMENT", "PBI"]
                )
        schedules = list(schedules)
        data = []
        has_applied_schedule_ids = set()
        eligibility_by_schedule_id = {}

        if has_student_designation:
            try:
                student = selectors.get_student_for_user(request.user)
                student_placement = _ensure_studentplacement(student)
                restrictions = list(PlacementRestriction.objects.all())
                has_applied_schedule_ids = set(
                    PlacementApplication.objects.filter(
                        student=student,
                        schedule_id__in=[schedule.id for schedule in schedules],
                    ).exclude(status='withdrawn').values_list('schedule_id', flat=True),
                )
                for schedule in schedules:
                    eligibility_by_schedule_id[schedule.id] = _schedule_eligibility(
                        schedule,
                        student,
                        student_placement=student_placement,
                        restrictions=restrictions,
                    )
            except Exception:
                has_applied_schedule_ids = set()
                eligibility_by_schedule_id = {}

        for schedule in schedules:
            try:
                data.append(
                    _serialize_schedule(
                        schedule,
                        request.user,
                        has_applied=schedule.id in has_applied_schedule_ids,
                        eligibility=eligibility_by_schedule_id.get(
                            schedule.id,
                            {'eligible': True, 'reasons': []},
                        ),
                    ),
                )
            except Exception:
                continue
        return Response(data, status=status.HTTP_200_OK)

    if not _is_tpo_user(request.user):
        return Response(
            {'detail': 'Only TPO users can create placement schedules.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    company = None
    company_id = request.data.get('company_id')
    if company_id:
        company = CompanyDetails.objects.filter(id=company_id).first()
    company_name = request.data.get('company_name') or request.data.get('title')
    if company is None and company_name:
        company, _ = CompanyDetails.objects.get_or_create(company_name=company_name)

    role_name = request.data.get('role') or ''
    role = selectors.get_or_create_role(role_name) if role_name else None
    placement_date = _parse_date(request.data.get('placement_date')) or timezone.now().date()
    if placement_date < _today():
        return Response(
            {'placement_date': ['Placement date cannot be in the past.']},
            status=status.HTTP_400_BAD_REQUEST,
        )
    schedule_time = _parse_time(request.data.get('schedule_at')) or timezone.now().time()
    notify = NotifyStudent.objects.create(
        placement_type=_normalize_placement_type(request.data.get('placement_type')),
        company_name=company_name or '',
        ctc=_parse_decimal(request.data.get('ctc')),
        description=request.data.get('description') or '',
    )
    schedule = PlacementSchedule.objects.create(
        notify_id=notify,
        title=request.data.get('title') or notify.company_name,
        placement_date=placement_date,
        end_date=_parse_date(request.data.get('end_date')),
        location=request.data.get('location') or '',
        description=request.data.get('description') or '',
        eligibility=request.data.get('eligibility') or '',
        passoutyr=request.data.get('passoutyr') or '',
        gender=request.data.get('gender') or '',
        cpi=str(request.data.get('cpi') or ''),
        branch=request.data.get('branch') or '',
        time=schedule_time,
        role=role,
        attached_file=request.FILES.get('resume') or request.FILES.get('attached_file'),
        schedule_at=_parse_datetime(request.data.get('schedule_at')) or timezone.now(),
        end_datetime=_parse_datetime(request.data.get('end_datetime')),
        company=company,
    )
    field_ids = _get_field_ids_from_request(request)
    if field_ids:
        schedule.fields.set(PlacementField.objects.filter(id__in=field_ids))
    return Response(_serialize_schedule(schedule, request.user), status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def placement_detail_api(request, schedule_id):
    schedule = get_object_or_404(
        PlacementSchedule.objects.select_related('notify_id', 'role', 'company').prefetch_related('fields'),
        pk=schedule_id,
    )

    if request.method == 'GET':
        return Response(_serialize_schedule(schedule, request.user), status=status.HTTP_200_OK)

    if not _is_tpo_user(request.user):
        return Response(
            {'detail': 'Only TPO users can modify placement schedules.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    if request.method == 'DELETE':
        schedule.notify_id.delete()
        return Response({'message': 'Placement schedule deleted successfully.'}, status=status.HTTP_200_OK)

    notify = schedule.notify_id
    notify.placement_type = _normalize_placement_type(request.data.get('placement_type') or notify.placement_type)
    notify.company_name = request.data.get('company_name') or notify.company_name
    notify.ctc = _parse_decimal(request.data.get('ctc'), notify.ctc)
    notify.description = request.data.get('description') or notify.description
    notify.save()

    placement_date = _parse_date(request.data.get('placement_date'))
    if placement_date and placement_date < _today():
        return Response(
            {'placement_date': ['Placement date cannot be in the past.']},
            status=status.HTTP_400_BAD_REQUEST,
        )
    schedule.placement_date = placement_date or schedule.placement_date
    schedule.location = request.data.get('location') or schedule.location
    schedule.description = request.data.get('description') or schedule.description
    schedule.schedule_at = _parse_datetime(request.data.get('schedule_at')) or schedule.schedule_at
    schedule.end_datetime = _parse_datetime(request.data.get('end_date_time')) or schedule.end_datetime
    role_name = request.data.get('role')
    if role_name:
        schedule.role = selectors.get_or_create_role(role_name)
    time_value = _parse_time(request.data.get('schedule_at'))
    if time_value:
        schedule.time = time_value
    schedule.save()
    return Response({'message': 'Placement schedule updated successfully.'}, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def placement_statistics_api(request):
    if request.method != 'GET' and not _is_tpo_user(request.user):
        return Response(
            {'detail': 'Only TPO users can access placement statistics.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    if request.method == 'GET':
        records = StudentRecord.objects.select_related(
            'record_id',
            'unique_id__id__user',
            'unique_id__id__department',
        )
        company = request.GET.get('company')
        if company:
            records = records.filter(record_id__name__icontains=company)
        ctc_min = request.GET.get('ctc_min')
        if ctc_min not in [None, '']:
            records = records.filter(record_id__ctc__gte=_parse_decimal(ctc_min))
        ctc_max = request.GET.get('ctc_max')
        if ctc_max not in [None, '']:
            records = records.filter(record_id__ctc__lte=_parse_decimal(ctc_max))
        year = request.GET.get('year')
        if year not in [None, '']:
            records = records.filter(record_id__year=year)
        department = request.GET.get('department')
        if department:
            records = records.filter(unique_id__id__department__name__iexact=department)

        if request.GET.get('aggregate_by') == 'department':
            summary = records.values(
                'unique_id__id__department__name',
            ).annotate(
                count=Count('id'),
            ).order_by('unique_id__id__department__name')
            return Response([
                {
                    'department': item['unique_id__id__department__name'] or 'Unassigned',
                    'count': item['count'],
                }
                for item in summary
            ], status=status.HTTP_200_OK)

        rows = []
        for item in records.order_by('-record_id__year', '-record_id__id'):
            rows.append({
                'id': item.record_id.id,
                'first_name': '{} {}'.format(
                    item.unique_id.id.user.first_name,
                    item.unique_id.id.user.last_name,
                ).strip() or item.unique_id.id.user.username,
                'placement_name': item.record_id.name,
                'batch': item.record_id.year,
                'branch': item.unique_id.id.department.name if item.unique_id.id.department else '',
                'ctc': str(item.record_id.ctc),
            })
        return Response(rows, status=status.HTTP_200_OK)

    roll_no = request.data.get('roll_no')
    student = get_object_or_404(Student.objects.select_related('id__user', 'id__department'), pk=roll_no)
    record = PlacementRecord.objects.create(
        placement_type=_normalize_placement_type(request.data.get('placement_type')),
        name=request.data.get('company_name') or '',
        ctc=_parse_decimal(request.data.get('ctc')),
        year=int(request.data.get('year') or timezone.now().year),
        test_type=request.data.get('test_type') or '',
        test_score=int(request.data.get('test_score') or 0),
    )
    StudentRecord.objects.get_or_create(record_id=record, unique_id=student)
    return Response({'id': record.id}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def placement_reports_api(request):
    if not _is_report_admin(request.user):
        return Response({'detail': 'Only TPO and chairman users can access reports.'}, status=status.HTTP_403_FORBIDDEN)
    payload = _build_report_payload(request)
    payload['templates'] = [
        {'value': 'batch', 'label': 'Batch Summary'},
        {'value': 'company', 'label': 'Company Summary'},
        {'value': 'branch', 'label': 'Branch Summary'},
        {'value': 'custom', 'label': 'Custom Report'},
    ]
    return Response(payload, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def placement_reports_export_api(request):
    if not _is_report_admin(request.user):
        return Response({'detail': 'Only TPO and chairman users can export reports.'}, status=status.HTTP_403_FORBIDDEN)
    payload = _build_report_payload(request)
    export_format = (
        request.GET.get('export_format')
        or request.GET.get('download_format')
        or 'excel'
    ).lower()
    if export_format == 'pdf':
        return _build_report_pdf_response(payload)
    return _build_report_excel_response(payload)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def placement_report_schedules_api(request):
    if not _is_report_admin(request.user):
        return Response({'detail': 'Only TPO and chairman users can manage report schedules.'}, status=status.HTTP_403_FORBIDDEN)
    if request.method == 'GET':
        schedules = PlacementReportSchedule.objects.all()
        return Response([_serialize_report_schedule(item) for item in schedules], status=status.HTTP_200_OK)

    recipients = request.data.get('recipients') or []
    if isinstance(recipients, list):
        recipients = ', '.join([str(item).strip() for item in recipients if str(item).strip()])
    schedule = PlacementReportSchedule.objects.create(
        name=request.data.get('name') or 'Placement Report',
        report_type=request.data.get('report_type') or 'custom',
        frequency=request.data.get('frequency') or 'weekly',
        export_format=request.data.get('export_format') or 'excel',
        filters=request.data.get('filters') or {},
        recipients=recipients,
        is_active=bool(request.data.get('is_active', True)),
        created_by=request.user,
    )
    return Response(_serialize_report_schedule(schedule), status=status.HTTP_201_CREATED)


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def placement_report_schedule_detail_api(request, schedule_id):
    if not _is_report_admin(request.user):
        return Response({'detail': 'Only TPO and chairman users can manage report schedules.'}, status=status.HTTP_403_FORBIDDEN)
    schedule = get_object_or_404(PlacementReportSchedule, pk=schedule_id)
    if request.method == 'DELETE':
        schedule.delete()
        return Response({'message': 'Report schedule deleted successfully.'}, status=status.HTTP_200_OK)

    recipients = request.data.get('recipients', schedule.recipients)
    if isinstance(recipients, list):
        recipients = ', '.join([str(item).strip() for item in recipients if str(item).strip()])
    schedule.name = request.data.get('name', schedule.name)
    schedule.report_type = request.data.get('report_type', schedule.report_type)
    schedule.frequency = request.data.get('frequency', schedule.frequency)
    schedule.export_format = request.data.get('export_format', schedule.export_format)
    schedule.filters = request.data.get('filters', schedule.filters)
    schedule.recipients = recipients
    if 'is_active' in request.data:
        schedule.is_active = bool(request.data.get('is_active'))
    schedule.save()
    return Response(_serialize_report_schedule(schedule), status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def delete_placement_statistics_api(request, record_id):
    if not _is_tpo_user(request.user):
        return Response(
            {'detail': 'Only TPO users can delete placement statistics.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    PlacementRecord.objects.filter(pk=record_id).delete()
    return Response({'message': 'Record deleted successfully.'}, status=status.HTTP_200_OK)


def _serialize_higher_studies_record(student_record):
    student = student_record.unique_id
    user = student.id.user
    record = student_record.record_id
    return {
        'id': record.id,
        'student_record_id': student_record.id,
        'roll_no': student.id.id,
        'student_name': '{} {}'.format(
            user.first_name,
            user.last_name,
        ).strip() or user.username,
        'university': record.name,
        'test_type': record.test_type,
        'test_score': record.test_score,
        'year': record.year,
        'department': student.id.department.name if student.id.department else '',
    }


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def higher_studies_api(request):
    if not _is_tpo_user(request.user):
        return Response(
            {'detail': 'Only TPO users can access higher studies records.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    if request.method == 'GET':
        records = StudentRecord.objects.select_related(
            'record_id',
            'unique_id__id__user',
            'unique_id__id__department',
        ).filter(record_id__placement_type='HIGHER STUDIES')

        roll_no = request.GET.get('roll_no')
        if roll_no:
            records = records.filter(unique_id__id__id__iexact=roll_no)
        university = request.GET.get('university')
        if university:
            records = records.filter(record_id__name__icontains=university)
        test_type = request.GET.get('test_type')
        if test_type:
            records = records.filter(record_id__test_type__icontains=test_type)
        year = request.GET.get('year')
        if year not in [None, '']:
            records = records.filter(record_id__year=year)

        data = [
            _serialize_higher_studies_record(item)
            for item in records.order_by('-record_id__year', '-record_id__id')
        ]
        return Response(data, status=status.HTTP_200_OK)

    roll_no = request.data.get('roll_no') or request.data.get('roll')
    student = get_object_or_404(Student.objects.select_related('id__user', 'id__department'), pk=roll_no)
    record = PlacementRecord.objects.create(
        placement_type='HIGHER STUDIES',
        name=request.data.get('university') or request.data.get('company_name') or request.data.get('name') or '',
        ctc=0,
        year=int(request.data.get('year') or timezone.now().year),
        test_type=request.data.get('test_type') or '',
        test_score=int(request.data.get('test_score') or 0),
    )
    student_record, _ = StudentRecord.objects.get_or_create(record_id=record, unique_id=student)
    return Response(_serialize_higher_studies_record(student_record), status=status.HTTP_201_CREATED)


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def higher_studies_detail_api(request, record_id):
    if not _is_tpo_user(request.user):
        return Response(
            {'detail': 'Only TPO users can modify higher studies records.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    record = get_object_or_404(PlacementRecord, pk=record_id, placement_type='HIGHER STUDIES')

    if request.method == 'DELETE':
        record.delete()
        return Response({'message': 'Higher studies record deleted successfully.'}, status=status.HTTP_200_OK)

    record.name = request.data.get('university') or request.data.get('company_name') or record.name
    record.test_type = request.data.get('test_type') or record.test_type
    if request.data.get('test_score') not in [None, '']:
        record.test_score = int(request.data.get('test_score'))
    if request.data.get('year') not in [None, '']:
        record.year = int(request.data.get('year'))
    record.save()
    student_record = get_object_or_404(
        StudentRecord.objects.select_related('record_id', 'unique_id__id__user', 'unique_id__id__department'),
        record_id=record,
    )
    return Response(_serialize_higher_studies_record(student_record), status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def registration_api(request):
    if request.method == 'POST' and not _is_tpo_user(request.user):
        return Response(
            {'detail': 'Only TPO users can create company registrations.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    if request.method == 'GET':
        companies = CompanyDetails.objects.all().order_by('company_name')
        data = [{
            'id': company.id,
            'companyName': company.company_name,
            'description': company.description,
            'address': company.address,
            'website': company.website,
            'logo': company.logo.url if company.logo else None,
        } for company in companies]
        return Response(data, status=status.HTTP_200_OK)

    company = CompanyDetails.objects.create(
        company_name=request.data.get('companyName') or request.data.get('company_name') or '',
        description=request.data.get('description') or '',
        address=request.data.get('address') or '',
        website=request.data.get('website') or '',
        logo=request.FILES.get('logo'),
    )
    return Response({
        'id': company.id,
        'companyName': company.company_name,
        'description': company.description,
        'address': company.address,
        'website': company.website,
        'logo': company.logo.url if company.logo else None,
    }, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def placement_fields_api(request):
    if not _is_tpo_user(request.user):
        return Response(
            {'detail': 'Only TPO users can manage placement fields.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    if request.method == 'GET':
        fields = PlacementField.objects.all().order_by('name')
        data = [{
            'id': field.id,
            'name': field.name,
            'type': field.type,
            'required': field.required,
        } for field in fields]
        return Response(data, status=status.HTTP_200_OK)

    field = PlacementField.objects.create(
        name=request.data.get('name') or '',
        type=request.data.get('type') or 'text',
        required=bool(request.data.get('required')),
    )
    return Response({
        'id': field.id,
        'name': field.name,
        'type': field.type,
        'required': field.required,
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def form_fields_api(request):
    job_id = request.GET.get('jobId')
    schedule = PlacementSchedule.objects.filter(pk=job_id).first() if job_id else None
    queryset = schedule.fields.all() if schedule and schedule.fields.exists() else PlacementField.objects.all()
    data = [{
        'field_id': field.id,
        'id': field.id,
        'name': field.name,
        'type': field.type,
        'required': field.required,
    } for field in queryset.order_by('name')]
    return Response(data, status=status.HTTP_200_OK)


@api_view(['GET', 'POST', 'PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def placement_profile_api(request):
    student = selectors.get_student_for_user(request.user)

    if request.method == 'POST':
        file_obj = request.FILES.get('document')
        if not file_obj:
            return Response(
                {'document': ['Please choose a document to upload.']},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            _validate_profile_document(file_obj)
        except ValidationError as exc:
            return Response({'document': exc.messages}, status=status.HTTP_400_BAD_REQUEST)
        document = PlacementProfileDocument.objects.create(
            student=student,
            name=request.data.get('name') or file_obj.name,
            document=file_obj,
        )
        _log_profile_action(
            student,
            request.user,
            'document_uploaded',
            {'name': document.name},
        )
        return Response(_serialize_profile_document(document, request=request), status=status.HTTP_201_CREATED)

    if request.method == 'PUT':
        current_data = _serialize_profile(student)
        incoming_data = _sanitize_profile_payload(request.data)
        updated_data = dict(current_data)
        updated_data.update(incoming_data)
        field_errors = _profile_form_errors(updated_data)
        document_file = request.FILES.get('document')
        if document_file:
            try:
                _validate_profile_document(document_file)
            except ValidationError as exc:
                field_errors['document'] = exc.messages
        if field_errors:
            return Response(
                {
                    'detail': 'Placement profile could not be saved.',
                    'field_errors': field_errors,
                    'errors': _flatten_profile_errors(field_errors),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile = student.id
        changed_fields = {}
        for key in ['first_name', 'last_name', 'email']:
            previous_value = getattr(profile.user, key) or ''
            new_value = updated_data[key]
            if previous_value != new_value:
                changed_fields[key] = {'from': previous_value, 'to': new_value}
                setattr(profile.user, key, new_value)
        profile.user.save()

        profile_mapping = {
            'phone_no': int(updated_data['phone_no']),
            'address': updated_data['address'],
            'about_me': updated_data['about_me'],
        }
        for key, new_value in profile_mapping.items():
            previous_value = getattr(profile, key)
            previous_text = '' if previous_value is None else str(previous_value)
            current_text = str(new_value)
            if previous_text != current_text:
                changed_fields[key] = {'from': previous_text, 'to': current_text}
                setattr(profile, key, new_value)
        profile.save()

        if changed_fields:
            _log_profile_action(
                student,
                request.user,
                'profile_updated',
                {'changed_fields': changed_fields},
            )

        if document_file:
            document = PlacementProfileDocument.objects.create(
                student=student,
                name=request.data.get('name') or document_file.name,
                document=document_file,
            )
            _log_profile_action(
                student,
                request.user,
                'document_uploaded',
                {'name': document.name},
            )

        if changed_fields or document_file:
            _send_placement_notifications(
                actor=request.user,
                recipients=[request.user],
                description='Your placement profile has been updated.',
            )

    preferences = _ensure_notification_preferences(student)
    documents = PlacementProfileDocument.objects.filter(student=student)
    logs = PlacementProfileAuditLog.objects.filter(student=student)[:25]
    field_errors = _profile_completion_errors(student)
    validation_errors = _flatten_profile_errors(field_errors)
    return Response({
        'is_complete': len(validation_errors) == 0,
        'profile': _serialize_profile(student),
        'eligibility_summary': _serialize_profile_eligibility_summary(student),
        'field_errors': field_errors,
        'validation_errors': validation_errors,
        'documents': [_serialize_profile_document(item, request=request) for item in documents],
        'audit_logs': [_serialize_audit_log(item) for item in logs],
        'preferences': {
            'portal': preferences.enable_portal,
            'email': preferences.enable_email,
            'sms': preferences.enable_sms,
        },
    }, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def notification_preferences_api(request):
    student = selectors.get_student_for_user(request.user)
    preferences = _ensure_notification_preferences(student)

    if request.method == 'PUT':
        preferences.enable_portal = bool(request.data.get('portal', preferences.enable_portal))
        preferences.enable_email = bool(request.data.get('email', preferences.enable_email))
        preferences.enable_sms = bool(request.data.get('sms', preferences.enable_sms))
        preferences.save()
        _log_profile_action(
            student,
            request.user,
            'notification_preferences_updated',
            {
                'portal': preferences.enable_portal,
                'email': preferences.enable_email,
                'sms': preferences.enable_sms,
            },
        )

    return Response({
        'portal': preferences.enable_portal,
        'email': preferences.enable_email,
        'sms': preferences.enable_sms,
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def apply_for_placement_api(request):
    student = selectors.get_student_for_user(request.user)
    schedule = get_object_or_404(PlacementSchedule, pk=request.data.get('jobId'))
    requested_action = (
        request.data.get('invitation') or
        request.data.get('status') or
        'ACCEPTED'
    )
    requested_action = str(requested_action).upper()
    is_decline = requested_action in ['REJECT', 'REJECTED', 'DECLINE', 'DECLINED']
    student_placement = _ensure_studentplacement(student)
    if student_placement.debar == 'DEBAR':
        return Response(
            {'detail': 'Debarred students are not eligible to apply for placement activities.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    profile_errors = _profile_validation_errors(student)
    if profile_errors:
        return Response(
            {'detail': 'Placement profile is incomplete.', 'errors': profile_errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    eligibility = _schedule_eligibility(schedule, student)
    if not eligibility['eligible']:
        return Response(
            {'detail': 'You are not eligible for this job posting.', 'errors': eligibility['reasons']},
            status=status.HTTP_403_FORBIDDEN,
        )

    if is_decline:
        placement_status, _ = PlacementStatus.objects.get_or_create(
            notify_id=schedule.notify_id,
            unique_id=student,
        )
        placement_status.invitation = 'REJECTED'
        placement_status.timestamp = timezone.now()
        placement_status.no_of_days = 2
        placement_status.save()
        officer_recipients = User.objects.filter(
            current_designation__designation__name__in=['placement officer', 'placement chairman'],
        ).distinct()
        _send_placement_notifications(
            actor=request.user,
            recipients=officer_recipients,
            description='{} declined the offer for {}.'.format(student.id.id, schedule.notify_id.company_name),
        )
        return Response({'message': 'Invitation declined successfully.'}, status=status.HTTP_200_OK)

    active_application_count = PlacementApplication.objects.filter(
        student=student,
    ).exclude(status='withdrawn').count()
    application_limit = _max_active_application_limit()
    warning_threshold = max(application_limit - 2, 1)
    warning_message = None
    if active_application_count >= application_limit:
        return Response(
            {
                'detail': 'You can only have {} active applications at a time.'.format(
                    application_limit,
                ),
            },
            status=status.HTTP_403_FORBIDDEN,
        )
    elif active_application_count >= warning_threshold:
        warning_message = 'You have {} active applications. The limit is {}.'.format(
            active_application_count,
            application_limit,
        )

    application, created = PlacementApplication.objects.get_or_create(
        schedule=schedule,
        student=student,
        defaults={'status': 'pending'},
    )
    if not created:
        if application.status == 'withdrawn':
            return Response(
                {'detail': 'This application was withdrawn and cannot be submitted again.'},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(
            {'detail': 'You have already applied for this job.'},
            status=status.HTTP_409_CONFLICT,
        )

    responses = request.data.get('responses') or []
    if responses:
        PlacementApplicationResponse.objects.filter(application=application).delete()
        for item in responses:
            field = PlacementField.objects.filter(id=item.get('field_id')).first()
            PlacementApplicationResponse.objects.create(
                application=application,
                field=field,
                value=str(item.get('value') or ''),
            )
    _log_profile_action(
        student,
        request.user,
        'application_submitted',
        {'job_id': schedule.id, 'company_name': schedule.notify_id.company_name},
    )
    response_payload = {'message': 'Application submitted successfully.'}
    if warning_message:
        response_payload['warning'] = warning_message
    return Response(response_payload, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def withdraw_application_api(request, schedule_id):
    student = selectors.get_student_for_user(request.user)
    application = get_object_or_404(
        PlacementApplication.objects.select_related('schedule__notify_id'),
        schedule_id=schedule_id,
        student=student,
    )
    if application.status == 'withdrawn':
        return Response({'detail': 'Application already withdrawn.'}, status=status.HTTP_409_CONFLICT)

    application.status = 'withdrawn'
    application.withdrawn_at = timezone.now()
    application.save(update_fields=['status', 'withdrawn_at'])

    placement_status = PlacementStatus.objects.filter(
        notify_id=application.schedule.notify_id,
        unique_id=student,
        invitation__in=['PENDING', 'ACCEPTED'],
    ).first()
    if placement_status:
        placement_status.invitation = 'REJECTED'
        placement_status.timestamp = timezone.now()
        placement_status.no_of_days = 2
        placement_status.save(update_fields=['invitation', 'timestamp', 'no_of_days'])

    officer_recipients = User.objects.filter(
        current_designation__designation__name__in=['placement officer', 'placement chairman'],
    ).distinct()
    # Notify company if company user exists
    company_users = User.objects.filter(email=application.schedule.company.company_name + '@example.com') if application.schedule.company and application.schedule.company.company_name else []
    notification_recipients = list(officer_recipients) + list(company_users)
    notification_recipients.append(request.user)
    _send_placement_notifications(
        actor=request.user,
        recipients=notification_recipients,
        description='{} withdrew the application for {}.'.format(
            student.id.id,
            application.schedule.notify_id.company_name,
        ),
    )
    _log_profile_action(
        student,
        request.user,
        'application_withdrawn',
        {'job_id': application.schedule_id, 'company_name': application.schedule.notify_id.company_name},
    )
    return Response({'message': 'Application withdrawn successfully.'}, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def student_applications_api(request, identifier):
    if request.method == 'PUT':
        if not _is_tpo_user(request.user):
            return Response(
                {'detail': 'Only TPO users can update application status.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        application = get_object_or_404(PlacementApplication, pk=identifier)
        if application.status in ['accept', 'reject', 'withdrawn']:
            return Response(
                {'detail': 'Final application status cannot be changed.'},
                status=status.HTTP_409_CONFLICT,
            )
        status_value = request.data.get('status') or 'pending'
        allowed_statuses = [
            'pending',
            'shortlisted',
            'interview_scheduled',
            'interview_completed',
            'offer_released',
            'accept',
            'reject',
        ]
        next_status = status_value if status_value in allowed_statuses else 'pending'
        remarks = request.data.get('remarks') or ''
        application.status = next_status
        application.remarks = remarks
        application.save(update_fields=['status', 'remarks', 'updated_at'])
        student_user = application.student.id.user
        if application.status == 'accept':
            placement_status, _ = PlacementStatus.objects.get_or_create(
                notify_id=application.schedule.notify_id,
                unique_id=application.student,
            )
            placement_status.invitation = 'PENDING'
            placement_status.placed = 'PLACED'
            placement_status.timestamp = timezone.now()
            placement_status.no_of_days = 2
            placement_status.save()
            _ensure_placement_record_for_selection(application)
            _create_application_timeline_entry(
                application,
                stage='Selected',
                remarks=remarks or 'Congratulations! You have been selected.',
                actor=request.user,
            )
            _send_placement_notifications(
                actor=request.user,
                recipients=[student_user],
                description='You received an offer for {}. Please respond within 48 hours.'.format(
                    application.schedule.notify_id.company_name,
                ),
            )
        elif application.status == 'reject':
            placement_status, _ = PlacementStatus.objects.get_or_create(
                notify_id=application.schedule.notify_id,
                unique_id=application.student,
            )
            placement_status.invitation = 'REJECTED'
            placement_status.timestamp = timezone.now()
            placement_status.no_of_days = 2
            placement_status.save()
            _create_application_timeline_entry(
                application,
                stage='Rejected',
                remarks=remarks or 'Your application has been rejected.',
                actor=request.user,
            )
            _send_placement_notifications(
                actor=request.user,
                recipients=[student_user],
                description='Your application for {} has been rejected.'.format(
                    application.schedule.notify_id.company_name,
                ),
            )
        elif application.status == 'offer_released':
            placement_status, _ = PlacementStatus.objects.get_or_create(
                notify_id=application.schedule.notify_id,
                unique_id=application.student,
            )
            placement_status.invitation = 'PENDING'
            placement_status.timestamp = timezone.now()
            placement_status.no_of_days = 2
            placement_status.save()
            _create_application_timeline_entry(
                application,
                stage='Offer Released',
                remarks=remarks or 'Offer released. Please respond from your dashboard.',
                actor=request.user,
            )
            _send_placement_notifications(
                actor=request.user,
                recipients=[student_user],
                description='Offer released for {}. Please check your placement dashboard.'.format(
                    application.schedule.notify_id.company_name,
                ),
            )
        else:
            _create_application_timeline_entry(
                application,
                stage=_application_stage_label(application.status),
                remarks=remarks or 'Application status updated to {}.'.format(_application_stage_label(application.status)),
                actor=request.user,
            )
            _send_placement_notifications(
                actor=request.user,
                recipients=[student_user],
                description='Your application status for {} was updated to {}.'.format(
                    application.schedule.notify_id.company_name,
                    application.status,
                ),
            )
        return Response({'message': 'Application status updated successfully.'}, status=status.HTTP_200_OK)

    if request.method == 'DELETE':
        if not _is_tpo_user(request.user):
            return Response(
                {'detail': 'Only TPO users can delete applications.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        application = get_object_or_404(PlacementApplication, pk=identifier)
        student_user = application.student.id.user
        company_name = application.schedule.notify_id.company_name
        application.delete()
        _send_placement_notifications(
            actor=request.user,
            recipients=[student_user],
            description='Your application for {} was removed by the placement office.'.format(
                company_name,
            ),
        )
        return Response({'message': 'Application deleted successfully.'}, status=status.HTTP_200_OK)

    if not _is_tpo_user(request.user):
        return Response(
            {'detail': 'Only TPO users can view applicant lists.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    applications = PlacementApplication.objects.select_related(
        'student__id__user',
    ).filter(schedule_id=identifier).order_by('-created_at')
    students = []
    for app in applications:
        students.append({
            'id': app.id,
            'username': app.student.id.user.username,
            'name': '{} {}'.format(
                app.student.id.user.first_name,
                app.student.id.user.last_name,
            ).strip() or app.student.id.user.username,
            'roll_no': app.student.id.id,
            'email': app.student.id.user.email,
            'cpi': app.student.cpi,
            'status': app.status,
            'applied_at': app.created_at.isoformat() if app.created_at else None,
        })
    return Response({'students': students}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def download_applications_api(request, schedule_id):
    if not _is_tpo_user(request.user):
        return Response(
            {'detail': 'Only TPO users can export applicant data.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    applications = PlacementApplication.objects.select_related(
        'student__id__user',
    ).filter(schedule_id=schedule_id).order_by('-created_at')
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="applications_{}.xls"'.format(schedule_id)
    workbook = xlwt.Workbook(encoding='utf-8')
    worksheet = workbook.add_sheet('Applications')
    headers = ['Name', 'Roll No', 'Email', 'CPI', 'Status']
    header_style = xlwt.XFStyle()
    header_style.font.bold = True
    for index, header in enumerate(headers):
        worksheet.write(0, index, header, header_style)
    row_style = xlwt.XFStyle()
    for row_index, application in enumerate(applications, start=1):
        worksheet.write(row_index, 0, '{} {}'.format(application.student.id.user.first_name, application.student.id.user.last_name).strip() or application.student.id.user.username, row_style)
        worksheet.write(row_index, 1, application.student.id.id, row_style)
        worksheet.write(row_index, 2, application.student.id.user.email, row_style)
        worksheet.write(row_index, 3, application.student.cpi, row_style)
        worksheet.write(row_index, 4, application.status, row_style)
    workbook.save(response)
    return response


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def next_round_api(request, schedule_id):
    if not _is_tpo_user(request.user):
        return Response(
            {'detail': 'Only TPO users can schedule next rounds.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    schedule = get_object_or_404(PlacementSchedule, pk=schedule_id)
    start_datetime = _parse_datetime(request.data.get('start_datetime'))
    end_datetime = _parse_datetime(request.data.get('end_datetime'))

    if not start_datetime:
        return Response(
            {'detail': 'Interview start date and time are required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not end_datetime:
        end_datetime = start_datetime + datetime.timedelta(hours=1)

    if end_datetime <= start_datetime:
        return Response(
            {'detail': 'Interview end time must be after start time.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    application_ids = request.data.get('application_ids') or []
    applications = PlacementApplication.objects.select_related('student__id__user').filter(
        schedule=schedule,
    ).exclude(status__in=['reject', 'withdrawn', 'accept'])
    if application_ids:
        applications = applications.filter(id__in=application_ids)
    applications = list(applications)
    if not applications:
        return Response(
            {'detail': 'Select at least one valid candidate to schedule the next round.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    conflicts = _collect_student_schedule_conflicts(
        applications=applications,
        start_dt=start_datetime,
        end_dt=end_datetime,
        current_schedule_id=schedule.id,
    )
    if conflicts:
        return Response(
            {
                'detail': 'Selected interview time conflicts with student placement calendar.',
                'conflicts': conflicts,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    requested_round_no = request.data.get('round_no')
    if requested_round_no in [None, '']:
        existing_round_no = (
            PlacementRound.objects.filter(schedule=schedule)
            .aggregate(max_round=Max('round_no'))
            .get('max_round')
            or 0
        )
        round_no = existing_round_no + 1
    else:
        round_no = int(requested_round_no)

    feedback = request.data.get('feedback')
    description = (
        feedback
        if feedback not in [None, '']
        else request.data.get('description') or ''
    )

    round_obj = PlacementRound.objects.create(
        schedule=schedule,
        round_no=round_no,
        test_date=start_datetime.date(),
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        mode=request.data.get('mode') or '',
        location_link=request.data.get('location_link') or '',
        description=description,
        test_type=request.data.get('test_type') or '',
    )
    applications_to_update = []
    for application in applications:
        application.status = 'interview_scheduled'
        application.remarks = description or application.remarks
        applications_to_update.append(application)
        PlacementInterviewSchedule.objects.create(
            application=application,
            round_no=round_no,
            title=request.data.get('test_type') or 'Round {}'.format(round_no),
            scheduled_at=start_datetime,
            end_datetime=end_datetime,
            mode=request.data.get('mode') or '',
            location=request.data.get('location_link') or '',
            meeting_link=request.data.get('location_link') or '',
            remarks=description,
            created_by=request.user,
        )
        _create_application_timeline_entry(
            application,
            stage='Interview Scheduled',
            remarks=description or 'Interview round scheduled.',
            actor=request.user,
        )
    PlacementApplication.objects.bulk_update(applications_to_update, ['status', 'remarks'])

    recipients = [application.student.id.user for application in applications]
    if recipients:
        _send_placement_notifications(
            actor=request.user,
            recipients=recipients,
            description='Interview schedule updated for {}: {} on {}.'.format(
                schedule.notify_id.company_name,
                round_obj.test_type or 'Round {}'.format(round_obj.round_no),
                round_obj.start_datetime.isoformat() if round_obj.start_datetime else 'TBA',
            ),
        )
    return Response(
        {
            'id': round_obj.id,
            'scheduled_candidates': len(applications),
            'start_datetime': round_obj.start_datetime.isoformat() if round_obj.start_datetime else None,
            'end_datetime': round_obj.end_datetime.isoformat() if round_obj.end_datetime else None,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def timeline_api(request, schedule_id):
    rounds = list(PlacementRound.objects.filter(schedule_id=schedule_id).order_by('round_no', 'created_at'))
    student_data = selectors.get_designation_queryset(request.user, "student")
    application = None
    if student_data:
        student = selectors.get_student_for_user(request.user)
        application = PlacementApplication.objects.filter(schedule_id=schedule_id, student=student).first()

    data = []
    if application:
        timeline_entries = _serialize_application_timeline(application)
        for index, item in enumerate(timeline_entries):
            data.append({
                'round_no': index,
                'test_name': item['stage'],
                'test_date': item['created_at'],
                'description': item['remarks'],
            })
        if application.status == 'reject':
            return Response({'next_data': data}, status=status.HTTP_200_OK)
        if application.status == 'withdrawn':
            return Response({'next_data': data}, status=status.HTTP_200_OK)

        interviews = PlacementInterviewSchedule.objects.filter(application=application).order_by('scheduled_at', 'id')
        if interviews.exists():
            data.extend([{
                'round_no': max(item.round_no, len(data)),
                'test_name': item.title or 'Round {}'.format(item.round_no),
                'test_date': item.scheduled_at.isoformat() if item.scheduled_at else None,
                'start_datetime': item.scheduled_at.isoformat() if item.scheduled_at else None,
                'end_datetime': item.end_datetime.isoformat() if item.end_datetime else None,
                'mode': item.mode,
                'location_link': item.meeting_link or item.location,
                'description': item.remarks,
                'feedback': item.remarks,
                'outcome': item.outcome,
            } for item in interviews])
            return Response({'next_data': data}, status=status.HTTP_200_OK)

    if not rounds:
        if not data:
            data.append({
                'round_no': 0,
                'test_name': 'Application',
                'test_date': None,
                'description': 'To be updated',
            })
        return Response({'next_data': data}, status=status.HTTP_200_OK)

    data.extend([{
        'round_no': max(item.round_no, len(data)),
        'test_name': item.test_type or 'Round {}'.format(item.round_no),
        'test_date': item.start_datetime.isoformat() if item.start_datetime else (item.test_date.isoformat() if item.test_date else None),
        'start_datetime': item.start_datetime.isoformat() if item.start_datetime else None,
        'end_datetime': item.end_datetime.isoformat() if item.end_datetime else None,
        'mode': item.mode,
        'location_link': item.location_link,
        'description': item.description,
        'feedback': item.description,
    } for item in rounds])
    return Response({'next_data': data}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def my_applications_api(request):
    student = selectors.get_student_for_user(request.user)
    applications = PlacementApplication.objects.select_related(
        'schedule__notify_id',
        'schedule__role',
    ).prefetch_related(
        Prefetch(
            'interview_schedules',
            queryset=PlacementInterviewSchedule.objects.order_by('scheduled_at', 'id'),
            to_attr='prefetched_interviews',
        ),
    ).filter(student=student).order_by('-created_at')
    offer_map = {
        item.notify_id_id: item
        for item in PlacementStatus.objects.filter(
            unique_id=student,
            notify_id_id__in=[application.schedule.notify_id_id for application in applications],
        )
    }
    rows = []
    for application in applications:
        interviews = list(getattr(application, 'prefetched_interviews', []))
        next_round = interviews[-1] if interviews else None
        offer = offer_map.get(application.schedule.notify_id_id)
        rows.append({
            'application_id': application.id,
            'schedule_id': application.schedule_id,
            'company_name': application.schedule.notify_id.company_name,
            'role': application.schedule.get_role,
            'placement_type': application.schedule.notify_id.placement_type,
            'status': application.status,
            'status_label': application.status.replace('_', ' ').title(),
            'applied_at': application.created_at.isoformat() if application.created_at else None,
            'offer_id': offer.id if offer else None,
            'offer_status': offer.invitation if offer else None,
            'rounds': [
                {
                    'id': item.id,
                    'round_no': item.round_no,
                    'title': item.title or 'Round {}'.format(item.round_no),
                    'date': item.scheduled_at.isoformat() if item.scheduled_at else None,
                    'description': item.remarks,
                    'feedback': item.remarks,
                    'outcome': item.outcome,
                    'mode': item.mode,
                    'location': item.meeting_link or item.location,
                }
                for item in interviews
            ],
            'next_interview': {
                'round_no': next_round.round_no,
                'title': next_round.title or 'Round {}'.format(next_round.round_no),
                'date': next_round.scheduled_at.isoformat() if next_round.scheduled_at else None,
                'description': next_round.remarks,
                'feedback': next_round.remarks,
                'outcome': next_round.outcome,
            } if next_round else None,
            'can_withdraw': application.status not in ['withdrawn', 'reject', 'accept'],
            'can_raise_appeal': application.status == 'reject',
        })
    return Response({'applications': rows}, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def application_detail_api(request, application_id):
    application = get_object_or_404(
        PlacementApplication.objects.select_related(
            'student__id__user',
            'student__id__department',
            'schedule__notify_id',
            'schedule__role',
        ).prefetch_related(
            'timeline_entries__actor',
            'interview_schedules',
        ),
        pk=application_id,
    )

    if request.method == 'GET':
        if _is_tpo_user(request.user):
            return Response(_serialize_tpo_application_detail(application, request=request), status=status.HTTP_200_OK)

        student = selectors.get_student_for_user(request.user)
        if application.student_id != student.id:
            return Response({'detail': 'Application not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(_serialize_tpo_application_detail(application, request=request), status=status.HTTP_200_OK)

    if not _is_tpo_user(request.user):
        return Response({'detail': 'Only TPO users can update applicants.'}, status=status.HTTP_403_FORBIDDEN)

    if application.status in ['withdrawn']:
        return Response({'detail': 'Withdrawn applications cannot be updated.'}, status=status.HTTP_409_CONFLICT)

    next_status = request.data.get('status') or application.status
    remarks = request.data.get('remarks') or ''
    allowed_statuses = [
        'pending',
        'shortlisted',
        'interview_scheduled',
        'interview_completed',
        'offer_released',
        'accept',
        'reject',
    ]
    if next_status not in allowed_statuses:
        return Response({'status': ['Invalid application status.']}, status=status.HTTP_400_BAD_REQUEST)

    application.status = next_status
    application.remarks = remarks
    application.save(update_fields=['status', 'remarks', 'updated_at'])

    student_user = application.student.id.user
    stage_label = _application_stage_label(next_status)
    _create_application_timeline_entry(
        application,
        stage=stage_label,
        remarks=remarks or stage_label,
        actor=request.user,
    )

    if next_status == 'offer_released':
        placement_status, _ = PlacementStatus.objects.get_or_create(
            notify_id=application.schedule.notify_id,
            unique_id=application.student,
        )
        placement_status.invitation = 'PENDING'
        placement_status.timestamp = timezone.now()
        placement_status.no_of_days = 2
        placement_status.save()
        _send_placement_notifications(
            actor=request.user,
            recipients=[student_user],
            description='You received an offer for {}. Please respond within 48 hours.'.format(
                application.schedule.notify_id.company_name,
            ),
        )
    elif next_status == 'accept':
        placement_status, _ = PlacementStatus.objects.get_or_create(
            notify_id=application.schedule.notify_id,
            unique_id=application.student,
        )
        placement_status.invitation = 'PENDING'
        placement_status.placed = 'PLACED'
        placement_status.timestamp = timezone.now()
        placement_status.no_of_days = 2
        placement_status.save()
        _ensure_placement_record_for_selection(application)
        _send_placement_notifications(
            actor=request.user,
            recipients=[student_user],
            description='Congratulations! You have been selected for {}. Please review the offer in your dashboard.'.format(
                application.schedule.notify_id.company_name,
            ),
        )
    elif next_status == 'reject':
        _send_placement_notifications(
            actor=request.user,
            recipients=[student_user],
            description='Your application for {} has been rejected.'.format(
                application.schedule.notify_id.company_name,
            ),
        )
    else:
        _send_placement_notifications(
            actor=request.user,
            recipients=[student_user],
            description='Your application status for {} is now {}.'.format(
                application.schedule.notify_id.company_name,
                stage_label,
            ),
        )

    application.refresh_from_db()
    return Response(_serialize_tpo_application_detail(application, request=request), status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def application_interview_schedule_api(request, application_id):
    if not _is_tpo_user(request.user):
        return Response({'detail': 'Only TPO users can manage interviews.'}, status=status.HTTP_403_FORBIDDEN)

    application = get_object_or_404(
        PlacementApplication.objects.select_related('student__id__user', 'schedule__notify_id'),
        pk=application_id,
    )
    scheduled_at = _parse_datetime(request.data.get('scheduled_at'))
    if not scheduled_at:
        return Response({'scheduled_at': ['Interview date and time are required.']}, status=status.HTTP_400_BAD_REQUEST)

    end_datetime = _parse_datetime(request.data.get('end_datetime'))
    if not end_datetime:
        end_datetime = scheduled_at + datetime.timedelta(hours=1)

    requested_round_no = request.data.get('round_no')
    if requested_round_no in [None, '']:
        existing_round_no = (
            PlacementInterviewSchedule.objects.filter(application=application)
            .aggregate(max_round=Max('round_no'))
            .get('max_round')
            or 0
        )
        round_no = existing_round_no + 1
    else:
        round_no = int(requested_round_no)

    feedback = request.data.get('feedback')
    remarks = (
        feedback
        if feedback not in [None, '']
        else request.data.get('remarks') or ''
    )

    interview = PlacementInterviewSchedule.objects.create(
        application=application,
        round_no=round_no,
        title=request.data.get('title') or '',
        scheduled_at=scheduled_at,
        end_datetime=end_datetime,
        mode=request.data.get('mode') or '',
        location=request.data.get('location') or '',
        meeting_link=request.data.get('meeting_link') or '',
        remarks=remarks,
        outcome=request.data.get('outcome') or 'pending',
        is_active=bool(request.data.get('is_active', True)),
        created_by=request.user,
    )
    application.status = 'interview_scheduled'
    application.remarks = remarks or application.remarks
    application.save(update_fields=['status', 'remarks', 'updated_at'])
    _create_application_timeline_entry(
        application,
        stage='Interview Scheduled',
        remarks=remarks or 'Interview round scheduled.',
        actor=request.user,
    )
    _send_placement_notifications(
        actor=request.user,
        recipients=[application.student.id.user],
        description='Interview scheduled for {} on {}.'.format(
            application.schedule.notify_id.company_name,
            interview.scheduled_at.isoformat(),
        ),
    )
    return Response(_serialize_application_interview(interview), status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def my_offers_api(request):
    student = selectors.get_student_for_user(request.user)
    visible_offer_statuses = {'offer_released', 'accept'}
    offers = PlacementStatus.objects.select_related('notify_id').filter(
        unique_id=student,
    ).order_by('-timestamp', '-id')
    notify_ids = [offer.notify_id_id for offer in offers]
    schedules = PlacementSchedule.objects.select_related('role', 'notify_id').filter(
        notify_id_id__in=notify_ids,
    ).order_by('notify_id_id', '-id')
    schedule_map = {}
    for schedule in schedules:
        if schedule.notify_id_id not in schedule_map:
            schedule_map[schedule.notify_id_id] = schedule

    applications = PlacementApplication.objects.filter(
        student=student,
        schedule__notify_id_id__in=notify_ids,
    ).select_related('schedule__notify_id').order_by('schedule__notify_id_id', '-created_at')
    application_map = {}
    for application in applications:
        notify_id = application.schedule.notify_id_id
        if notify_id not in application_map:
            application_map[notify_id] = application

    rows = []
    for offer in offers:
        schedule = schedule_map.get(offer.notify_id_id)
        application = application_map.get(offer.notify_id_id)
        if application is None or application.status not in visible_offer_statuses:
            continue
        deadline = offer.response_date if offer.timestamp else None
        rows.append({
            'id': offer.id,
            'schedule_id': schedule.id if schedule else None,
            'company_name': offer.notify_id.company_name,
            'role': schedule.get_role if schedule else '',
            'ctc': str(offer.notify_id.ctc),
            'status': offer.invitation,
            'response_deadline': deadline.isoformat() if deadline else None,
            'expired': bool(deadline and timezone.now() > deadline),
        })
    return Response({'offers': rows}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def calendar_api(request):
    if not request.user.is_authenticated:
        return Response(
            {'detail': 'Authentication credentials were not provided.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    rounds = PlacementRound.objects.select_related('schedule__notify_id').all().order_by('test_date')
    schedule_data = [{
        'id': item.schedule.id,
        'company_name': item.schedule.notify_id.company_name,
        'round': item.round_no,
        'date': item.start_datetime.isoformat() if item.start_datetime else (item.test_date.isoformat() if item.test_date else item.schedule.placement_date.isoformat()),
        'end_datetime': item.end_datetime.isoformat() if item.end_datetime else None,
        'description': item.description,
        'type': item.test_type,
        'mode': item.mode,
        'location_link': item.location_link,
    } for item in rounds]
    if not schedule_data:
        schedules = PlacementSchedule.objects.select_related('notify_id').all()
        schedule_data = [{
            'id': item.id,
            'company_name': item.notify_id.company_name,
            'round': 0,
            'date': item.placement_date.isoformat(),
            'description': item.description,
            'type': item.notify_id.placement_type,
        } for item in schedules]
    return Response({'schedule_data': schedule_data}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def generate_cv_api(request):
    username = request.user.username
    profile = get_object_or_404(ExtraInfo, Q(user=request.user))
    student = get_object_or_404(Student, Q(id=profile.id))
    now = datetime.datetime.now()
    if int(str(profile.id)[:2]) == 20:
        roll = (1 + now.year - int(str(profile.id)[:4])) if now.month > 4 else (now.year - int(str(profile.id)[:4]))
    else:
        roll = (1 + now.year - int("20" + str(profile.id)[0:2])) if now.month > 4 else (now.year - int("20" + str(profile.id)[0:2]))

    def _flag(name):
        return '1' if request.data.get(name, True) else '0'

    reference = Reference.objects.filter(unique_id=student)
    profile_picture_url = profile.profile_picture.url if profile.profile_picture else ''
    profile_picture_path = profile.profile_picture.path if profile.profile_picture else ''
    context = {
        'pagesize': 'A4',
        'user': request.user,
        'references': reference,
        'profile': profile,
        'profile_picture': profile_picture_url,
        'profile_picture_path': profile_picture_path,
        'projects': Project.objects.filter(unique_id=student),
        'skills': Has.objects.select_related('skill_id').filter(unique_id=student),
        'educations': Education.objects.filter(unique_id=student),
        'courses': Course.objects.filter(unique_id=student),
        'experiences': Experience.objects.filter(unique_id=student),
        'referencecheck': '1' if reference.exists() and request.data.get('references', True) else '0',
        'achievements': Achievement.objects.filter(unique_id=student),
        'extracurriculars': Extracurricular.objects.filter(unique_id=student),
        'publications': Publication.objects.filter(unique_id=student),
        'patents': Patent.objects.filter(unique_id=student),
        'roll': roll,
        'achievementcheck': _flag('achievements'),
        'extracurricularcheck': _flag('extracurriculars'),
        'educationcheck': _flag('education'),
        'publicationcheck': _flag('publications'),
        'patentcheck': _flag('patents'),
        'conferencecheck': _flag('conferences'),
        'conferences': Conference.objects.filter(unique_id=student),
        'internshipcheck': _flag('experience'),
        'projectcheck': _flag('projects'),
        'coursecheck': _flag('courses'),
        'skillcheck': _flag('skills'),
        'today': datetime.date.today(),
    }
    pdf_response = render_to_pdf('placementModule/cv.html', context)
    if isinstance(pdf_response, HttpResponse):
        selected_sections = sorted(
            key for key, enabled in request.data.items() if str(enabled).lower() in ['true', '1', 'yes', 'on']
        ) if hasattr(request.data, 'items') else []
        PlacementProfileAuditLog.objects.create(
            student=student,
            actor=request.user,
            action='resume_downloaded',
            details={
                'filename': 'student_cv.pdf',
                'selected_sections': selected_sections,
            },
        )
        pdf_response['Content-Disposition'] = 'attachment; filename="student_cv.pdf"'
    return pdf_response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def debarred_students_api(request):
    if not _is_tpo_user(request.user):
        return Response(
            {'detail': 'Only TPO users can access debarred students.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    rows = []
    records = StudentPlacement.objects.select_related('unique_id__id__user').filter(debar='DEBAR')
    for item in records:
        rows.append({
            'id': item.unique_id.id.id,
            'roll_no': item.unique_id.id.id,
            'name': '{} {}'.format(item.unique_id.id.user.first_name, item.unique_id.id.user.last_name).strip() or item.unique_id.id.user.username,
            'description': item.debar_reason or '',
        })
    return Response(rows, status=status.HTTP_200_OK)


@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def debarred_status_api(request, roll_no):
    if not _is_tpo_user(request.user):
        return Response(
            {'detail': 'Only TPO users can manage debarred status.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    student = get_object_or_404(Student.objects.select_related('id__user', 'id__department'), pk=roll_no)
    student_placement = _ensure_studentplacement(student)

    if request.method == 'GET':
        return Response({
            'name': '{} {}'.format(student.id.user.first_name, student.id.user.last_name).strip() or student.id.user.username,
            'programme': student.programme,
            'year': student.batch,
            'department': student.id.department.name if student.id.department else '',
            'email': student.id.user.email,
            'description': student_placement.debar_reason or '',
        }, status=status.HTTP_200_OK)

    if request.method == 'DELETE':
        student_placement.debar = 'NOT DEBAR'
        student_placement.debar_reason = ''
        student_placement.save()
        _send_placement_notifications(
            actor=request.user,
            recipients=[student.id.user],
            description='Your placement debarment has been removed.',
        )
        return Response({'message': 'Student un-debarred successfully.'}, status=status.HTTP_200_OK)

    student_placement.debar = 'DEBAR'
    student_placement.debar_reason = request.data.get('reason') or ''
    student_placement.save()
    _send_placement_notifications(
        actor=request.user,
        recipients=[student.id.user],
        description='You have been debarred from placement activities. {}'.format(student_placement.debar_reason).strip(),
    )
    return Response({'message': 'Student debarred successfully.'}, status=status.HTTP_200_OK)


def _serialize_restriction(restriction):
    return {
        'id': restriction.id,
        'criteria': restriction.criteria,
        'condition': restriction.condition,
        'value': restriction.value,
        'description': restriction.description,
    }


def _serialize_policy(policy):
    return {
        'id': policy.id,
        'title': policy.title,
        'description': policy.description,
        'created_by': policy.created_by.get_full_name().strip() or policy.created_by.username if policy.created_by else '',
        'created_at': policy.created_at.isoformat() if policy.created_at else None,
        'updated_at': policy.updated_at.isoformat() if policy.updated_at else None,
    }


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def restrictions_api(request):
    if not _is_tpo_user(request.user):
        return Response(
            {'detail': 'Only TPO users can manage placement restrictions.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    if request.method == 'GET':
        data = [_serialize_restriction(item) for item in PlacementRestriction.objects.all().order_by('-id')]
        return Response(data, status=status.HTTP_200_OK)

    restriction = PlacementRestriction.objects.create(
        criteria=request.data.get('criteria') or '',
        condition=request.data.get('condition') or '',
        value=request.data.get('value') or '',
        description=request.data.get('description') or '',
    )
    return Response(_serialize_restriction(restriction), status=status.HTTP_201_CREATED)


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def restriction_detail_api(request, restriction_id):
    if not _is_tpo_user(request.user):
        return Response(
            {'detail': 'Only TPO users can manage placement restrictions.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    restriction = get_object_or_404(PlacementRestriction, pk=restriction_id)

    if request.method == 'DELETE':
        restriction.delete()
        return Response({'message': 'Restriction deleted successfully.'}, status=status.HTTP_200_OK)

    restriction.criteria = request.data.get('criteria') or restriction.criteria
    restriction.condition = request.data.get('condition') or restriction.condition
    restriction.value = request.data.get('value') or restriction.value
    restriction.description = request.data.get('description') or ''
    restriction.save()
    return Response(_serialize_restriction(restriction), status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def placement_policies_api(request):
    if not selectors.get_designation_queryset(request.user, "placement chairman").exists():
        return Response(
            {'detail': 'Only placement chairman users can manage placement policies.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    if request.method == 'GET':
        data = [_serialize_policy(item) for item in PlacementPolicy.objects.all()]
        return Response(data, status=status.HTTP_200_OK)

    title = (request.data.get('title') or '').strip()
    description = (request.data.get('description') or '').strip()

    errors = {}
    if not title:
        errors['title'] = ['This field is required.']
    if not description:
        errors['description'] = ['This field is required.']
    if errors:
        return Response(errors, status=status.HTTP_400_BAD_REQUEST)

    policy = PlacementPolicy.objects.create(
        title=title,
        description=description,
        created_by=request.user,
    )
    return Response(_serialize_policy(policy), status=status.HTTP_201_CREATED)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def placement_policy_detail_api(request, policy_id):
    if not selectors.get_designation_queryset(request.user, "placement chairman").exists():
        return Response(
            {'detail': 'Only placement chairman users can manage placement policies.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    policy = get_object_or_404(PlacementPolicy, pk=policy_id)
    title = (request.data.get('title') or '').strip()
    description = (request.data.get('description') or '').strip()

    errors = {}
    if not title:
        errors['title'] = ['This field is required.']
    if not description:
        errors['description'] = ['This field is required.']
    if errors:
        return Response(errors, status=status.HTTP_400_BAD_REQUEST)

    policy.title = title
    policy.description = description
    policy.save(update_fields=['title', 'description', 'updated_at'])
    return Response(_serialize_policy(policy), status=status.HTTP_200_OK)


def _ensure_alumni_designation(user):
    designation, _ = Designation.objects.get_or_create(
        name='alumni',
        defaults={'full_name': 'Alumni', 'type': 'administrative'},
    )
    HoldsDesignation.objects.get_or_create(
        user=user,
        working=user,
        designation=designation,
    )


def _is_tpo_user(user):
    return selectors.is_tpo(user)


def _max_active_application_limit():
    try:
        return max(int(getattr(settings, 'PLACEMENT_MAX_ACTIVE_APPLICATIONS', 10)), 1)
    except (TypeError, ValueError):
        return 10


def _serialize_alumni_profile(profile):
    extra = ExtraInfo.objects.filter(user=profile.user).select_related('department').first()
    return {
        'id': profile.id,
        'username': profile.user.username,
        'full_name': profile.user.get_full_name().strip() or profile.user.username,
        'email': profile.user.email,
        'graduation_year': profile.graduation_year,
        'degree': profile.degree,
        'current_company': profile.current_company,
        'current_designation': profile.current_designation,
        'linkedin_url': profile.linkedin_url,
        'verification_document': profile.verification_document.url if profile.verification_document else None,
        'verification_notes': profile.verification_notes,
        'status': profile.status,
        'topics': [item.strip() for item in (profile.topics or '').split(',') if item.strip()],
        'availability': profile.availability,
        'bio': profile.bio,
        'mentorship_enabled': profile.mentorship_enabled,
        'department': extra.department.name if extra and extra.department else '',
        'approved_at': profile.approved_at.isoformat() if profile.approved_at else None,
    }


def _serialize_referral(referral):
    return {
        'id': referral.id,
        'title': referral.title,
        'company': referral.company,
        'location': referral.location,
        'application_url': referral.application_url,
        'description': referral.description,
        'expires_at': referral.expires_at.isoformat() if referral.expires_at else None,
        'created_at': referral.created_at.isoformat() if referral.created_at else None,
        'alumni': _serialize_alumni_profile(referral.alumni),
    }


def _serialize_connection(connection):
    return {
        'id': connection.id,
        'status': connection.status,
        'message': connection.message,
        'created_at': connection.created_at.isoformat() if connection.created_at else None,
        'responded_at': connection.responded_at.isoformat() if connection.responded_at else None,
        'student': {
            'roll_no': connection.student.id.id,
            'name': connection.student.id.user.get_full_name().strip() or connection.student.id.user.username,
            'email': connection.student.id.user.email,
        },
        'alumni': _serialize_alumni_profile(connection.alumni),
    }


def _serialize_session(session):
    return {
        'id': session.id,
        'topic': session.topic,
        'agenda': session.agenda,
        'scheduled_at': session.scheduled_at.isoformat() if session.scheduled_at else None,
        'mode': session.mode,
        'meeting_link': session.meeting_link,
        'student_message': session.student_message,
        'alumni_message': session.alumni_message,
        'status': session.status,
        'student': {
            'roll_no': session.student.id.id,
            'name': session.student.id.user.get_full_name().strip() or session.student.id.user.username,
            'email': session.student.id.user.email,
        },
        'alumni': _serialize_alumni_profile(session.alumni),
    }


@api_view(['GET', 'POST', 'PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def alumni_profile_api(request):
    profile = AlumniProfile.objects.filter(user=request.user).first()

    if request.method == 'GET':
        return Response({
            'profile': _serialize_alumni_profile(profile) if profile else None,
            'can_access': bool(profile and profile.status == 'approved'),
            'is_tpo': _is_tpo_user(request.user),
        }, status=status.HTTP_200_OK)

    data = request.data
    if profile is None:
        graduation_year = data.get('graduation_year')
        if not graduation_year:
            return Response({'graduation_year': ['This field is required.']}, status=status.HTTP_400_BAD_REQUEST)
        profile = AlumniProfile.objects.create(
            user=request.user,
            graduation_year=int(graduation_year),
            degree=data.get('degree') or '',
            current_company=data.get('current_company') or '',
            current_designation=data.get('current_designation') or '',
            linkedin_url=data.get('linkedin_url') or '',
            verification_document=request.FILES.get('verification_document'),
            bio=data.get('bio') or '',
            topics=data.get('topics') or '',
            availability=data.get('availability') or '',
            mentorship_enabled=str(data.get('mentorship_enabled', '')).lower() in ['true', '1', 'yes', 'on'],
            verification_notes=data.get('verification_notes') or '',
            status='pending',
        )
        officer_recipients = User.objects.filter(
            current_designation__designation__name__in=['placement officer', 'placement chairman'],
        ).distinct()
        _send_placement_notifications(
            actor=request.user,
            recipients=officer_recipients,
            description='New alumni verification request submitted by {}.'.format(request.user.username),
        )
        return Response(_serialize_alumni_profile(profile), status=status.HTTP_201_CREATED)

    if profile.status == 'approved' or _is_tpo_user(request.user):
        profile.degree = data.get('degree', profile.degree)
        profile.current_company = data.get('current_company', profile.current_company)
        profile.current_designation = data.get('current_designation', profile.current_designation)
        profile.linkedin_url = data.get('linkedin_url', profile.linkedin_url)
        profile.bio = data.get('bio', profile.bio)
        profile.topics = data.get('topics', profile.topics)
        profile.availability = data.get('availability', profile.availability)
        if 'mentorship_enabled' in data:
            profile.mentorship_enabled = str(data.get('mentorship_enabled')).lower() in ['true', '1', 'yes', 'on']
        if request.FILES.get('verification_document'):
            profile.verification_document = request.FILES.get('verification_document')
            profile.status = 'pending'
        profile.save()
        return Response(_serialize_alumni_profile(profile), status=status.HTTP_200_OK)

    return Response(
        {'detail': 'Your alumni registration is awaiting approval.'},
        status=status.HTTP_403_FORBIDDEN,
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def alumni_directory_api(request):
    profiles = AlumniProfile.objects.filter(status='approved').order_by('-approved_at', '-id')
    if request.GET.get('mentors_only') in ['true', '1']:
        profiles = profiles.filter(mentorship_enabled=True)
    query = (request.GET.get('query') or '').strip()
    if query:
        profiles = profiles.filter(
            Q(user__username__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(current_company__icontains=query) |
            Q(topics__icontains=query)
        )
    return Response([_serialize_alumni_profile(item) for item in profiles], status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def alumni_verification_list_api(request):
    if not _is_tpo_user(request.user):
        return Response({'detail': 'Only TPO users can access this queue.'}, status=status.HTTP_403_FORBIDDEN)
    profiles = AlumniProfile.objects.select_related('user').all().order_by('status', '-created_at')
    return Response([_serialize_alumni_profile(item) for item in profiles], status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def alumni_verification_detail_api(request, profile_id):
    if not _is_tpo_user(request.user):
        return Response({'detail': 'Only TPO users can verify alumni.'}, status=status.HTTP_403_FORBIDDEN)
    profile = get_object_or_404(AlumniProfile, pk=profile_id)
    decision = str(request.data.get('status') or '').lower()
    if decision not in ['approved', 'rejected', 'pending']:
        return Response({'status': ['Invalid verification status.']}, status=status.HTTP_400_BAD_REQUEST)
    profile.status = decision
    profile.verification_notes = request.data.get('verification_notes', profile.verification_notes)
    profile.approved_by = request.user if decision == 'approved' else None
    profile.approved_at = timezone.now() if decision == 'approved' else None
    profile.save()
    if decision == 'approved':
        _ensure_alumni_designation(profile.user)
    _send_placement_notifications(
        actor=request.user,
        recipients=[profile.user],
        description='Your alumni verification request has been {}.'.format(decision),
    )
    return Response(_serialize_alumni_profile(profile), status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def alumni_referrals_api(request):
    if request.method == 'GET':
        queryset = AlumniReferral.objects.select_related('alumni__user').all()
        queryset = queryset.filter(Q(expires_at__isnull=True) | Q(expires_at__gte=_today()))
        return Response([_serialize_referral(item) for item in queryset], status=status.HTTP_200_OK)

    profile = get_object_or_404(AlumniProfile, user=request.user)
    if profile.status != 'approved':
        return Response({'detail': 'Approved alumni access is required.'}, status=status.HTTP_403_FORBIDDEN)
    referral = AlumniReferral.objects.create(
        alumni=profile,
        title=request.data.get('title') or '',
        company=request.data.get('company') or '',
        location=request.data.get('location') or '',
        application_url=request.data.get('application_url') or '',
        description=request.data.get('description') or '',
        expires_at=_parse_date(request.data.get('expires_at')),
    )
    recipients = User.objects.filter(current_designation__designation__name='student').distinct()
    _send_placement_notifications(
        actor=request.user,
        recipients=recipients,
        description='New alumni job referral posted: {} at {}.'.format(referral.title, referral.company),
    )
    return Response(_serialize_referral(referral), status=status.HTTP_201_CREATED)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def alumni_connections_api(request):
    if request.method == 'GET':
        if selectors.is_student(request.user):
            student = selectors.get_student_for_user(request.user)
            queryset = AlumniConnection.objects.select_related('alumni__user', 'student__id__user').filter(student=student)
        else:
            profile = get_object_or_404(AlumniProfile, user=request.user)
            queryset = AlumniConnection.objects.select_related('alumni__user', 'student__id__user').filter(alumni=profile)
        return Response([_serialize_connection(item) for item in queryset], status=status.HTTP_200_OK)

    if not selectors.is_student(request.user):
        return Response({'detail': 'Only students can initiate alumni connections.'}, status=status.HTTP_403_FORBIDDEN)
    student = selectors.get_student_for_user(request.user)
    alumni = get_object_or_404(AlumniProfile, pk=request.data.get('alumni_id'), status='approved')
    connection, created = AlumniConnection.objects.get_or_create(
        alumni=alumni,
        student=student,
        defaults={'message': request.data.get('message') or ''},
    )
    if not created:
        return Response({'detail': 'A connection request already exists.'}, status=status.HTTP_409_CONFLICT)
    _send_placement_notifications(
        actor=request.user,
        recipients=[alumni.user],
        description='{} requested to connect with you.'.format(student.id.id),
    )
    return Response(_serialize_connection(connection), status=status.HTTP_201_CREATED)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def alumni_connection_detail_api(request, connection_id):
    connection = get_object_or_404(AlumniConnection.objects.select_related('alumni__user', 'student__id__user'), pk=connection_id)
    if connection.alumni.user != request.user and not _is_tpo_user(request.user):
        return Response({'detail': 'You cannot update this connection.'}, status=status.HTTP_403_FORBIDDEN)
    next_status = str(request.data.get('status') or '').lower()
    if next_status not in ['connected', 'rejected', 'pending']:
        return Response({'status': ['Invalid connection status.']}, status=status.HTTP_400_BAD_REQUEST)
    connection.status = next_status
    connection.responded_by = request.user
    connection.responded_at = timezone.now()
    connection.save()
    _send_placement_notifications(
        actor=request.user,
        recipients=[connection.student.id.user],
        description='Your alumni connection request has been {}.'.format(next_status),
    )
    return Response(_serialize_connection(connection), status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def alumni_sessions_api(request):
    if request.method == 'GET':
        if selectors.is_student(request.user):
            student = selectors.get_student_for_user(request.user)
            queryset = AlumniMentorshipSession.objects.select_related('alumni__user', 'student__id__user').filter(student=student)
        else:
            profile = get_object_or_404(AlumniProfile, user=request.user)
            queryset = AlumniMentorshipSession.objects.select_related('alumni__user', 'student__id__user').filter(alumni=profile)
        return Response([_serialize_session(item) for item in queryset], status=status.HTTP_200_OK)

    if not selectors.is_student(request.user):
        return Response({'detail': 'Only students can request mentorship sessions.'}, status=status.HTTP_403_FORBIDDEN)
    student = selectors.get_student_for_user(request.user)
    alumni = get_object_or_404(AlumniProfile, pk=request.data.get('alumni_id'), status='approved', mentorship_enabled=True)
    session = AlumniMentorshipSession.objects.create(
        alumni=alumni,
        student=student,
        topic=request.data.get('topic') or '',
        agenda=request.data.get('agenda') or '',
        scheduled_at=_parse_datetime(request.data.get('scheduled_at')) or timezone.now(),
        mode=request.data.get('mode') or 'online',
        student_message=request.data.get('student_message') or '',
    )
    _send_placement_notifications(
        actor=request.user,
        recipients=[alumni.user],
        description='New mentorship session request from {} on {}.'.format(student.id.id, session.topic),
    )
    return Response(_serialize_session(session), status=status.HTTP_201_CREATED)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def alumni_session_detail_api(request, session_id):
    session = get_object_or_404(AlumniMentorshipSession.objects.select_related('alumni__user', 'student__id__user'), pk=session_id)
    if session.alumni.user != request.user and session.student.id.user != request.user and not _is_tpo_user(request.user):
        return Response({'detail': 'You cannot update this session.'}, status=status.HTTP_403_FORBIDDEN)
    if session.alumni.user == request.user or _is_tpo_user(request.user):
        session.status = request.data.get('status', session.status)
        session.alumni_message = request.data.get('alumni_message', session.alumni_message)
        session.meeting_link = request.data.get('meeting_link', session.meeting_link)
        session.mode = request.data.get('mode', session.mode)
        parsed_dt = _parse_datetime(request.data.get('scheduled_at'))
        if parsed_dt:
            session.scheduled_at = parsed_dt
    if session.student.id.user == request.user:
        session.student_message = request.data.get('student_message', session.student_message)
    session.save()
    recipients = [session.alumni.user, session.student.id.user]
    _send_placement_notifications(
        actor=request.user,
        recipients=recipients,
        description='Mentorship session "{}" has been updated.'.format(session.topic),
    )
    return Response(_serialize_session(session), status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def send_notification_api(request):
    send_to = request.data.get('sendTo')
    recipient = request.data.get('recipient')
    description = request.data.get('description') or request.data.get('type') or 'Placement Cell notification'

    if send_to == 'All':
        recipients = User.objects.filter(extrainfo__user_type='student')
    else:
        target_user = User.objects.filter(username=recipient).first()
        if target_user is None:
            target_user = User.objects.filter(extrainfo__id=recipient).first()
        if target_user is None:
            return Response(
                {'recipient': ['No user found for the supplied recipient.']},
                status=status.HTTP_404_NOT_FOUND,
            )
        recipients = [target_user]

    _send_placement_notifications(
        actor=request.user,
        recipients=recipients,
        description=description,
    )

    return Response({'message': 'Notification sent successfully.'}, status=status.HTTP_200_OK)


# --- Placement Announcements API ---
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def placement_announcements_api(request):
    """List placement announcements (any authenticated user) or post one (TPO only)."""
    if request.method == 'GET':
        announcements = PlacementAnnouncement.objects.all()
        return Response(PlacementAnnouncementSerializer(announcements, many=True).data)

    if not _is_tpo_user(request.user):
        return Response(
            {'detail': 'Only TPO users can post announcements.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    serializer = PlacementAnnouncementWriteSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    announcement = PlacementAnnouncement.objects.create(
        posted_by=request.user, **serializer.validated_data
    )
    return Response(
        PlacementAnnouncementSerializer(announcement).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def placement_announcement_detail_api(request, announcement_id):
    """Delete a placement announcement (TPO only)."""
    if not _is_tpo_user(request.user):
        return Response(
            {'detail': 'Only TPO users can delete announcements.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    PlacementAnnouncement.objects.filter(pk=announcement_id).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# --- Off-Campus Placements API ---
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def offcampus_placements_api(request):
    """List off-campus placement records or record a new one against a roll number (TPO only)."""
    if not _is_tpo_user(request.user):
        return Response(
            {'detail': 'Only TPO users can manage off-campus placements.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    if request.method == 'GET':
        placements = OffCampusPlacement.objects.select_related('student__user').all()
        return Response(OffCampusPlacementSerializer(placements, many=True).data)

    roll_no = str(request.data.get('roll_no', '')).strip()
    if not roll_no:
        return Response({'detail': 'roll_no is required.'}, status=status.HTTP_400_BAD_REQUEST)
    student = ExtraInfo.objects.filter(user__username=roll_no).select_related('user').first()
    if not student:
        return Response(
            {'detail': 'No student found with roll number {}.'.format(roll_no)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    payload = {key: value for key, value in request.data.items() if key != 'roll_no'}
    payload['student'] = student.pk
    serializer = OffCampusPlacementWriteSerializer(data=payload)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    placement = serializer.save(added_by=request.user)
    return Response(
        OffCampusPlacementSerializer(placement).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def offcampus_placement_detail_api(request, placement_id):
    """Delete an off-campus placement record (TPO only)."""
    if not _is_tpo_user(request.user):
        return Response(
            {'detail': 'Only TPO users can manage off-campus placements.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    OffCampusPlacement.objects.filter(pk=placement_id).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# --- Published-CPI student view + export API ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def placement_cpi_batches_api(request):
    """List batches that have an announced result (for the CPI batch filter)."""
    if not _is_tpo_user(request.user):
        return Response(
            {'detail': 'Only TPO and chairman users can view published CPI data.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    batches = selectors.batches_with_published_results()
    return Response(
        [
            {'id': batch.id, 'label': str(batch), 'year': batch.year}
            for batch in batches
        ]
    )


def _published_cpi_rows(batch_id):
    """Build per-student published-CPI rows for a batch (empty if not published).
    """
    from django.core.cache import cache
    from applications.examination.models import ResultAnnouncement
    from applications.examination.api.views import calculate_cpi_for_student

    latest = (
        ResultAnnouncement.objects
        .filter(batch_id=batch_id, announced=True)
        .order_by('-semester')
        .first()
    )
    if latest is None:
        return []

    students = list(
        Student.objects.filter(batch_id=batch_id).select_related('id__user')
    )
    if not students:
        return []

    extra_pks = [student.id_id for student in students]
    offcampus_map = {}
    for ocp in OffCampusPlacement.objects.filter(student_id__in=extra_pks):
        offcampus_map.setdefault(ocp.student_id, []).append(ocp.company_name)

    semester = latest.semester
    semester_type = latest.semester_type
    # Keep cache keys free of spaces/colons so they stay valid on memcached too.
    semester_slug = (semester_type or 'na').replace(' ', '-')
    key_by_pk = {
        student.pk: 'pc-cpi-v1-{}-{}-{}'.format(
            student.id.user.username, semester, semester_slug
        )
        for student in students
    }
    cached = cache.get_many(list(key_by_pk.values()))

    to_cache = {}
    rows = []
    for student in students:
        extra = student.id  # ExtraInfo
        key = key_by_pk[student.pk]
        if key in cached:
            cpi = cached[key]
        else:
            try:
                cpi_value, _, _ = calculate_cpi_for_student(
                    student, semester, semester_type
                )
            except Exception:
                cpi_value = None
            cpi = str(cpi_value) if cpi_value is not None else None
            if cpi is not None:
                to_cache[key] = cpi
        if cpi is None:
            continue
        rows.append(
            {
                'roll_no': extra.user.username,
                'student_name': '{} {}'.format(
                    extra.user.first_name, extra.user.last_name
                ).strip(),
                'email': extra.user.email,
                'cpi': cpi,
                'off_campus': offcampus_map.get(extra.pk, []),
            }
        )
    if to_cache:
        cache.set_many(to_cache, 60 * 60)
    return rows


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def placement_cpi_students_api(request):
    """Students of a batch with their published CPI and off-campus companies.

    Requires ``?batch_id=``; without it an empty list is returned. Pass
    ``?export=excel`` to download the same rows as an ``.xls`` workbook.
    Restricted to TPO and chairman users.
    """
    if not _is_tpo_user(request.user):
        return Response(
            {'detail': 'Only TPO and chairman users can view published CPI data.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    raw_batch_id = request.query_params.get('batch_id')
    if not raw_batch_id:
        return Response([])
    # Validate as an integer so it cannot be reflected into the response
    # (filename header) or reach the ORM filter as arbitrary input.
    try:
        batch_id = int(raw_batch_id)
    except (TypeError, ValueError):
        return Response(
            {'detail': 'batch_id must be an integer.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    rows = _published_cpi_rows(batch_id)

    if request.query_params.get('export') == 'excel':
        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = (
            'attachment; filename="published_cpi_batch_{}.xls"'.format(batch_id)
        )
        workbook = xlwt.Workbook(encoding='utf-8')
        worksheet = workbook.add_sheet('Published CPI')
        headers = ['Roll No', 'Name', 'Email', 'CPI', 'Off-Campus']
        header_style = xlwt.XFStyle()
        header_style.font.bold = True
        for index, header in enumerate(headers):
            worksheet.write(0, index, header, header_style)
        for row_index, row in enumerate(rows, start=1):
            worksheet.write(row_index, 0, row['roll_no'])
            worksheet.write(row_index, 1, row['student_name'])
            worksheet.write(row_index, 2, row['email'])
            worksheet.write(row_index, 3, row['cpi'])
            worksheet.write(row_index, 4, ', '.join(row['off_campus']))
        workbook.save(response)
        return response

    return Response(rows)


# --- Branch (department) reference list for placement forms ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def placement_branches_api(request):
    """Distinct academic department names that students actually belong to.

    Branch eligibility compares a schedule's branch against the student's
    department name, so the placement-event form populates its branch options
    from this list instead of a hard-coded one (which had drifted from the real
    department names and silently broke branch eligibility).
    """
    names = (
        Student.objects
        .exclude(id__department__isnull=True)
        .values_list('id__department__name', flat=True)
        .distinct()
    )
    branches = sorted({name for name in names if name})
    return Response(branches)


# --- Placement calendar events (free-form, Google-Calendar style) ---
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def placement_calendar_events_api(request):
    """List placement calendar events (any authenticated user) or add one (TPO)."""
    if request.method == 'GET':
        events = PlacementCalendarEvent.objects.all()
        return Response(PlacementCalendarEventSerializer(events, many=True).data)

    if not _is_tpo_user(request.user):
        return Response(
            {'detail': 'Only TPO users can add calendar events.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    serializer = PlacementCalendarEventSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    event = serializer.save(created_by=request.user)
    return Response(
        PlacementCalendarEventSerializer(event).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(['PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def placement_calendar_event_detail_api(request, event_id):
    """Update or delete a placement calendar event (TPO only)."""
    if not _is_tpo_user(request.user):
        return Response(
            {'detail': 'Only TPO users can manage calendar events.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    event = get_object_or_404(PlacementCalendarEvent, pk=event_id)

    if request.method == 'DELETE':
        event.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = PlacementCalendarEventSerializer(
        event, data=request.data, partial=request.method == 'PATCH'
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(serializer.data)

