import re
from io import BytesIO
from xml.sax.saxutils import escape

from django.conf import settings
from django.core.paginator import Paginator
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

from .bonafide_certificate import (
    _certificate_reference,
    _father_name,
    _search_certificates,
    _student_name,
    _student_queryset,
    build_certificate_context,
    superscript_ordinal,
)

CERTIFICATE_TYPE = 'medium_of_instruction'


def medium_of_instruction_context(student):
    """The bonafide context, worded as the Medium of Instruction format has it:
    "Mr."/"Ms." rather than capitals, and the programme abbreviated with a
    closing stop ("B.Tech.")."""
    context = build_certificate_context(student)
    context['salutation'] = context['salutation'].capitalize()
    programme = (student.programme or '').strip()
    context['programme_short'] = (
        f'{programme}.' if '.' in programme and not programme.endswith('.')
        else programme)
    return context


def render_medium_of_instruction_pdf(context, reference_number, issued_on):
    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        topMargin=2.5 * cm,
        rightMargin=1.5 * cm,
        bottomMargin=2.5 * cm,
        leftMargin=1.5 * cm,
        title='Medium of Instruction Certificate',
        author=settings.BONAFIDE_INSTITUTE_NAME,
    )
    header_style = ParagraphStyle(
        'Header',
        fontName='Helvetica-Bold',
        fontSize=13.5,
        leading=18,
        alignment=TA_LEFT,
    )
    header_right_style = ParagraphStyle(
        'HeaderRight',
        parent=header_style,
        alignment=TA_RIGHT,
    )
    heading_style = ParagraphStyle(
        'Heading',
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        alignment=TA_CENTER,
    )
    body_style = ParagraphStyle(
        'Body',
        fontName='Helvetica',
        fontSize=13.5,
        leading=22,
        alignment=TA_JUSTIFY,
    )
    signature_style = ParagraphStyle(
        'Signature',
        fontName='Helvetica-Bold',
        fontSize=13.5,
        leading=18,
        alignment=TA_LEFT,
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

    # Worded as the Academic section's Medium of Instruction format.
    first_text = (
        'This is to certify that '
        f'<b>{escape(context["salutation"])} {escape(context["name"])}</b> '
        f'(Roll No. {escape(context["roll_number"])}), '
        f'{escape(context["relation"])} Mr. {escape(context["father_name"])}, '
        f'is a student of {superscript_ordinal(context["year_ordinal"])} Year '
        f'({superscript_ordinal(context["semester_ordinal"])} Semester) '
        f'<b>{escape(context["programme_short"])}</b> programme from '
        f'<b>{escape(context["discipline"])}</b> discipline. '
        'Institute provides education mode of instruction to the students '
        'in English only.'
    )

    story = [
        header,
        Spacer(1, 1.65 * cm),
        Paragraph('<u>TO WHOM SO EVER IT MAY CONCERN</u>', heading_style),
        Spacer(1, 1.25 * cm),
        Paragraph(first_text, body_style),
        Spacer(1, 1.65 * cm),
        Paragraph(f'({escape(settings.BONAFIDE_SIGNATORY_NAME)})', signature_style),
    ]

    document.build(story)
    output.seek(0)
    return output


def _certificate_filename(certificate):
    roll_number = certificate.student.id.user.username
    safe_roll_number = re.sub(r'[^A-Za-z0-9_-]', '_', roll_number)
    return f'{safe_roll_number}_Medium_of_Instruction_Certificate_{certificate.pk:03d}.pdf'


def _certificate_pdf(certificate):
    if certificate.pdf_content:
        return bytes(certificate.pdf_content)

    context = medium_of_instruction_context(certificate.student)
    if not context['is_ready']:
        return None
    document = render_medium_of_instruction_pdf(
        context,
        _certificate_reference(certificate),
        certificate.issued_at.date(),
    )
    return document.getvalue()


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@role_required(['acadadmin'])
def medium_of_instruction_student(request):
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
    context = medium_of_instruction_context(student)
    issued_on = timezone.now().date()
    prefix = settings.BONAFIDE_REFERENCE_PREFIX.rstrip('/')
    next_serial = (
        BonafideCertificate.objects.aggregate(max_id=Max('pk'))['max_id'] or 0
    ) + 1

    return Response({
        'student': context,
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
def generate_medium_of_instruction_pdf(request):
    student_id = request.data.get('student_id')
    if not student_id:
        return Response({'error': 'student_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

    student = get_object_or_404(_student_queryset(), pk=student_id)
    context = medium_of_instruction_context(student)
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
            certificate_type=CERTIFICATE_TYPE,
            purpose='Medium of Instruction',
            custom_purpose='',
            issued_by=request.user,
        )
        reference_number = (
            f'{prefix}/{issued_on.year}/{issued_on.month:02d}/'
            f'{context["roll_number"]}/{certificate.pk:03d}'
        )
        certificate.reference_number = reference_number
        certificate.save(update_fields=['reference_number'])
        document = render_medium_of_instruction_pdf(
            context,
            reference_number,
            issued_on,
        )
        document_bytes = document.getvalue()
        certificate.pdf_content = document_bytes
        certificate.save(update_fields=['pdf_content'])

    response = HttpResponse(
        document_bytes,
        content_type='application/pdf',
    )
    response['Content-Disposition'] = (
        f'attachment; filename="{_certificate_filename(certificate)}"'
    )
    response['X-Certificate-Reference'] = reference_number
    return response


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@role_required(['acadadmin'])
def medium_of_instruction_certificates(request):
    search = (request.query_params.get('search') or '').strip()
    try:
        page_size = int(request.query_params.get('page_size', 20))
    except (TypeError, ValueError):
        page_size = 20
    page_size = min(max(page_size, 1), 100)

    queryset = BonafideCertificate.objects.filter(
        certificate_type=CERTIFICATE_TYPE,
    ).select_related(
        'student__id__user',
    ).order_by('-issued_at', '-pk')
    queryset = _search_certificates(queryset, search).distinct()
    page = Paginator(queryset, page_size).get_page(
        request.query_params.get('page', 1)
    )

    results = []
    for certificate in page.object_list:
        results.append({
            'id': certificate.pk,
            'serial_number': f'{certificate.pk:03d}',
            'reference_number': _certificate_reference(certificate),
            'roll_number': certificate.student.id.user.username,
            'name': _student_name(certificate.student),
            'purpose': 'Medium of Instruction',
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
def medium_of_instruction_certificate_pdf(request, certificate_id):
    certificate = get_object_or_404(
        BonafideCertificate.objects.filter(
            certificate_type=CERTIFICATE_TYPE,
        ).select_related(
            'student__id__user',
            'student__id__department',
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
        f'{disposition}; filename="{_certificate_filename(certificate)}"'
    )
    response['X-Certificate-Reference'] = _certificate_reference(certificate)
    return response
