import math
import re
from io import BytesIO
from xml.sax.saxutils import escape

from django.conf import settings
from django.db import transaction
from django.db.models import Max
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
        'salutation': 'Ms.' if is_female else 'Mr.' if gender == 'M' else '',
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
        f'<b>Mr. {escape(context["father_name"])}</b> is a student of '
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

    filename_roll = re.sub(r'[^A-Za-z0-9_-]', '_', context['roll_number'])
    response = HttpResponse(
        document.getvalue(),
        content_type='application/pdf',
    )
    response['Content-Disposition'] = (
        f'attachment; filename="{filename_roll}_Bonafide_Certificate.pdf"')
    response['X-Certificate-Reference'] = reference_number
    return response
