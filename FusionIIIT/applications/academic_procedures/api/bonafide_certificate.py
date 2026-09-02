import math
import re
from datetime import datetime
from io import BytesIO
from xml.sax.saxutils import escape

from django.conf import settings
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Max, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from applications.academic_information.models import Student
from applications.academic_procedures.models import BonafideCertificate
from applications.globals.decorators import role_required
from applications.globals.programme_scope import programme_display_name

NUMBER_WORDS = {
    1: 'One', 2: 'Two', 3: 'Three', 4: 'Four', 5: 'Five',
    6: 'Six', 7: 'Seven', 8: 'Eight', 9: 'Nine', 10: 'Ten',
}


def ordinal(value):
    value = int(value)
    suffix = (
        'th' if 10 <= value % 100 <= 20
        else {1: 'st', 2: 'nd', 3: 'rd'}.get(value % 10, 'th')
    )
    return f'{value}{suffix}'


def _student_name(student):
    return student.id.user.get_full_name().strip() or student.id.user.username


def _father_name(value):
    return re.sub(r'^(mr\.?|shri|sri)\s+', '', (value or '').strip(), flags=re.IGNORECASE)


def _programme_duration(student):
    batch = student.batch_id
    category = ''
    if batch and batch.curriculum and batch.curriculum.programme:
        category = (batch.curriculum.programme.category or '').upper()

    canonical = (student.programme or '').upper().replace('.', '')
    if not category:
        if canonical in {'BTECH', 'BDES'}:
            category = 'UG'
        elif canonical in {'MTECH', 'MDES'}:
            category = 'PG'
        elif canonical == 'PHD':
            category = 'PHD'

    durations = {
        'UG': settings.BONAFIDE_UG_DURATION_YEARS,
        'PG': settings.BONAFIDE_PG_DURATION_YEARS,
        'PHD': settings.BONAFIDE_PHD_DURATION_YEARS,
    }
    if category in durations:
        return durations[category]
    if batch and batch.curriculum and batch.curriculum.no_of_semester:
        return math.ceil(batch.curriculum.no_of_semester / 2)
    return None


def build_certificate_context(student):
    batch = student.batch_id
    name = _student_name(student)
    father_name = _father_name(student.father_name)
    gender = (student.id.sex or '').strip().upper()
    semester = student.curr_semester_no
    duration_years = _programme_duration(student)
    start_year = batch.year if batch else student.batch
    discipline = ''
    if batch and batch.discipline:
        discipline = batch.discipline.name
    elif student.id.department:
        discipline = student.id.department.name

    errors = []
    if not name:
        errors.append('Student name is unavailable.')
    if not father_name:
        errors.append("Father's name is unavailable.")
    if gender not in {'M', 'F'}:
        errors.append('Gender must be Male or Female.')
    if not batch:
        errors.append('The student is not linked to a batch.')
    if not discipline:
        errors.append('Discipline is unavailable.')
    if not semester or semester < 1:
        errors.append('Current semester is unavailable.')
    if not duration_years:
        errors.append('Course duration is unavailable from the assigned curriculum.')

    is_female = gender == 'F'
    year_number = math.ceil(semester / 2) if semester else None
    duration_word = NUMBER_WORDS.get(duration_years, str(duration_years)) if duration_years else ''
    programme = programme_display_name(student.programme)

    return {
        'student_id': student.pk,
        'name': name,
        'roll_number': student.id.user.username,
        'gender': 'Female' if is_female else 'Male' if gender == 'M' else '',
        'salutation': 'MS.' if is_female else 'MR.' if gender == 'M' else '',
        'relation': 'D/o' if is_female else 'S/o' if gender == 'M' else '',
        'pronoun': 'her' if is_female else 'his' if gender == 'M' else '',
        'father_name': father_name,
        'programme': programme,
        'discipline': discipline,
        'semester': semester,
        'semester_ordinal': ordinal(semester) if semester else '',
        'year_number': year_number,
        'year_ordinal': ordinal(year_number) if year_number else '',
        'duration_years': duration_years,
        'duration_text': f'{duration_word} {"year" if duration_years == 1 else "years"}',
        'start_year': start_year,
        'end_year': start_year + duration_years if start_year and duration_years else None,
        'batch_id': batch.id if batch else None,
        'batch_label': str(batch) if batch else str(student.batch),
        'is_ready': not errors,
        'validation_errors': errors,
    }


def render_bonafide_pdf(
        context, purpose, reference_number, issued_on,
        include_internship_note=False):
    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        topMargin=2.5 * cm,
        rightMargin=1.5 * cm,
        bottomMargin=2.5 * cm,
        leftMargin=1.5 * cm,
        title='Bonafide Certificate',
        author=settings.BONAFIDE_INSTITUTE_NAME,
    )
    header_style = ParagraphStyle(
        'Header', fontName='Helvetica-Bold', fontSize=11.5,
        leading=15, alignment=TA_LEFT,
    )
    header_right_style = ParagraphStyle(
        'HeaderRight', parent=header_style, alignment=TA_RIGHT,
    )
    heading_style = ParagraphStyle(
        'Heading', fontName='Helvetica-Bold', fontSize=13,
        leading=16, alignment=TA_CENTER,
    )
    body_style = ParagraphStyle(
        'Body', fontName='Helvetica', fontSize=11.5,
        leading=18, alignment=TA_JUSTIFY,
    )
    signature_style = ParagraphStyle(
        'Signature', fontName='Helvetica-Bold', fontSize=11.5,
        leading=15, alignment=TA_LEFT,
    )
    note_style = ParagraphStyle(
        'Note', fontName='Helvetica', fontSize=11.5,
        leading=18, alignment=TA_JUSTIFY,
    )

    header = Table(
        [[
            Paragraph(
                f'{escape(settings.BONAFIDE_SIGNATORY_NAME)}<br/>'
                f'{escape(settings.BONAFIDE_SIGNATORY_TITLE)}',
                header_style,
            ),
            Paragraph(
                f'{escape(reference_number)}<br/>'
                f'Date: {issued_on.strftime("%d.%m.%Y")}',
                header_right_style,
            ),
        ]],
        colWidths=[9 * cm, 9 * cm],
    )
    header.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))

    first_text = (
        'This is to certify that '
        f'<b>{escape(context["salutation"])} {escape(context["name"])}</b> '
        f'(Roll No. {escape(context["roll_number"])}) '
        f'{escape(context["relation"])} '
        f'<b>MR. {escape(context["father_name"])}</b> is a student of '
        f'<b>{escape(context["year_ordinal"])} Year</b> '
        f'({escape(context["semester_ordinal"])} Semester) '
        f'<b>{escape(context["programme"])}</b> in '
        f'<b>{escape(context["discipline"])}</b> '
        f'({escape(context["duration_text"])} course duration: '
        f'<b>{context["start_year"]}</b> to <b>{context["end_year"]}</b>) at '
        f'{escape(settings.BONAFIDE_INSTITUTE_NAME)}.'
    )
    second_text = (
        'This certificate is being issued to '
        f'<b>{escape(context["salutation"])} {escape(context["name"])}</b> '
        f'on {escape(context["pronoun"])} request for '
        f'<b>{escape(purpose)}</b>.'
    )

    story = [
        header,
        Spacer(1, 1.65 * cm),
        Paragraph('<u>TO WHOM SO EVER IT MAY CONCERN</u>', heading_style),
        Spacer(1, 1.25 * cm),
        Paragraph(first_text, body_style),
        Spacer(1, 0.9 * cm),
        Paragraph(second_text, body_style),
    ]
    if include_internship_note:
        story.extend([
            Spacer(1, 0.25 * cm),
            Paragraph(
                'Note: No objection certificate will be issued by the placement cell.',
                note_style,
            ),
        ])
    story.extend([
        Spacer(1, 1.6 * cm),
        Paragraph(f'({escape(settings.BONAFIDE_SIGNATORY_NAME)})', signature_style),
    ])

    document.build(story)
    output.seek(0)
    return output


def _student_queryset():
    return Student.objects.select_related(
        'id__user', 'id__department', 'batch_id__discipline',
        'batch_id__curriculum__programme',
    )


def _effective_purpose(certificate):
    if certificate.purpose == 'Other':
        return certificate.custom_purpose
    return certificate.purpose


def _certificate_filename(certificate):
    roll_number = certificate.student.id.user.username
    safe_roll_number = re.sub(r'[^A-Za-z0-9_-]', '_', roll_number)
    return f'{safe_roll_number}_Bonafide_Certificate_{certificate.pk:03d}.pdf'


def _certificate_reference(certificate):
    if certificate.reference_number:
        return certificate.reference_number
    prefix = settings.BONAFIDE_REFERENCE_PREFIX.rstrip('/')
    issued_on = certificate.issued_at.date()
    roll_number = certificate.student.id.user.username
    return (
        f'{prefix}/{issued_on.year}/{issued_on.month:02d}/'
        f'{roll_number}/{certificate.pk:03d}'
    )


def _certificate_pdf(certificate):
    if certificate.pdf_content:
        return bytes(certificate.pdf_content)

    context = build_certificate_context(certificate.student)
    if not context['is_ready']:
        return None
    document = render_bonafide_pdf(
        context,
        _effective_purpose(certificate),
        _certificate_reference(certificate),
        certificate.issued_at.date(),
        include_internship_note=certificate.purpose == 'Internship',
    )
    return document.getvalue()


def _search_certificates(queryset, search):
    if not search:
        return queryset

    for date_format in ('%d.%m.%Y', '%d-%m-%Y', '%Y-%m-%d'):
        try:
            issued_on = datetime.strptime(search, date_format).date()
            return queryset.filter(issued_at__date=issued_on)
        except ValueError:
            continue

    if search.isdigit():
        return queryset.filter(pk=int(search))

    fields = (
        'reference_number__icontains',
        'student__id__user__username__icontains',
        'student__id__user__first_name__icontains',
        'student__id__user__last_name__icontains',
        'purpose__icontains',
        'custom_purpose__icontains',
    )
    for term in search.split():
        conditions = Q()
        for field in fields:
            conditions |= Q(**{field: term})
        queryset = queryset.filter(conditions)
    return queryset


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@role_required(['acadadmin'])
def bonafide_student(request):
    roll_number = (request.query_params.get('roll_number') or '').strip().upper()
    if not roll_number:
        return Response(
            {'error': 'roll_number is required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    student = get_object_or_404(
        _student_queryset(),
        pk=roll_number,
        id__user__is_active=True,
        id__user_status='PRESENT',
    )
    context = build_certificate_context(student)
    issued_on = timezone.now().date()
    prefix = settings.BONAFIDE_REFERENCE_PREFIX.rstrip('/')
    next_serial = (
        BonafideCertificate.objects.aggregate(max_id=Max('pk'))['max_id'] or 0
    ) + 1

    return Response({
        'student': context,
        'purposes': [
            {'value': value, 'label': label}
            for value, label in BonafideCertificate.PURPOSE_CHOICES
        ],
        'certificate': {
            'signatory_name': settings.BONAFIDE_SIGNATORY_NAME,
            'signatory_title': settings.BONAFIDE_SIGNATORY_TITLE,
            'institute_name': settings.BONAFIDE_INSTITUTE_NAME,
            'issued_on': issued_on.strftime('%d.%m.%Y'),
            'reference_preview': (
                f'{prefix}/{issued_on.year}/{issued_on.month:02d}/'
                f'{context["roll_number"]}/{next_serial:03d}'
            ),
        },
    })


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@role_required(['acadadmin'])
def generate_bonafide_pdf(request):
    student_id = request.data.get('student_id')
    purpose = request.data.get('purpose')
    custom_purpose = (request.data.get('custom_purpose') or '').strip()
    valid_purposes = dict(BonafideCertificate.PURPOSE_CHOICES)
    if not student_id:
        return Response({'error': 'student_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
    if purpose not in valid_purposes:
        return Response({'error': 'Select a valid certificate purpose.'}, status=status.HTTP_400_BAD_REQUEST)
    if purpose == 'Other' and not custom_purpose:
        return Response(
            {'error': 'Enter the certificate purpose.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if len(custom_purpose) > 150:
        return Response(
            {'error': 'The certificate purpose cannot exceed 150 characters.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    effective_purpose = custom_purpose if purpose == 'Other' else purpose

    student = get_object_or_404(_student_queryset(), pk=student_id)
    context = build_certificate_context(student)
    if not context['is_ready']:
        return Response(
            {'error': 'Student data is incomplete.', 'details': context['validation_errors']},
            status=status.HTTP_400_BAD_REQUEST,
        )

    issued_on = timezone.now().date()
    prefix = settings.BONAFIDE_REFERENCE_PREFIX.rstrip('/')
    with transaction.atomic():
        certificate = BonafideCertificate.objects.create(
            student=student,
            purpose=purpose,
            custom_purpose=custom_purpose if purpose == 'Other' else '',
            issued_by=request.user,
        )
        reference_number = (
            f'{prefix}/{issued_on.year}/{issued_on.month:02d}/'
            f'{context["roll_number"]}/{certificate.pk:03d}'
        )
        certificate.reference_number = reference_number
        certificate.save(update_fields=['reference_number'])
        document = render_bonafide_pdf(
            context,
            effective_purpose,
            reference_number,
            issued_on,
            include_internship_note=purpose == 'Internship',
        )
        document_bytes = document.getvalue()
        certificate.pdf_content = document_bytes
        certificate.save(update_fields=['pdf_content'])

    response = HttpResponse(
        document_bytes,
        content_type='application/pdf',
    )
    response['Content-Disposition'] = (
        f'attachment; filename="{_certificate_filename(certificate)}"')
    response['X-Certificate-Reference'] = reference_number
    return response


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@role_required(['acadadmin'])
def bonafide_certificates(request):
    search = (request.query_params.get('search') or '').strip()
    try:
        page_size = int(request.query_params.get('page_size', 20))
    except (TypeError, ValueError):
        page_size = 20
    page_size = min(max(page_size, 1), 100)

    queryset = BonafideCertificate.objects.select_related(
        'student__id__user',
    ).order_by('-issued_at', '-pk')
    queryset = _search_certificates(queryset, search).distinct()
    page = Paginator(queryset, page_size).get_page(
        request.query_params.get('page', 1))

    results = []
    for certificate in page.object_list:
        results.append({
            'id': certificate.pk,
            'serial_number': f'{certificate.pk:03d}',
            'reference_number': _certificate_reference(certificate),
            'roll_number': certificate.student.id.user.username,
            'name': _student_name(certificate.student),
            'purpose': _effective_purpose(certificate),
            'issued_on': certificate.issued_at.strftime('%d.%m.%Y'),
        })

    return Response({
        'results': results,
        'count': page.paginator.count,
        'page': page.number,
        'page_size': page_size,
        'total_pages': page.paginator.num_pages,
    })


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@role_required(['acadadmin'])
def bonafide_certificate_pdf(request, certificate_id):
    certificate = get_object_or_404(
        BonafideCertificate.objects.select_related(
            'student__id__user', 'student__id__department',
            'student__batch_id__discipline',
            'student__batch_id__curriculum__programme',
        ),
        pk=certificate_id,
    )
    document_bytes = _certificate_pdf(certificate)
    if document_bytes is None:
        return Response(
            {
                'error': 'The certificate cannot be rendered because the '
                         'student record is now incomplete.'
            },
            status=status.HTTP_409_CONFLICT,
        )

    disposition = (
        'attachment'
        if request.query_params.get('download') in {'1', 'true', 'True'}
        else 'inline'
    )
    response = HttpResponse(document_bytes, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'{disposition}; filename="{_certificate_filename(certificate)}"')
    response['X-Certificate-Reference'] = _certificate_reference(certificate)
    return response
