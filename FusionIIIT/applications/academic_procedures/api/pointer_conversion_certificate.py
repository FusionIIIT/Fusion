import os
from io import BytesIO
from xml.sax.saxutils import escape

from django.conf import settings
from django.core.paginator import Paginator
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from applications.academic_procedures.models import BonafideCertificate
from applications.globals.decorators import role_required
from applications.globals.programme_scope import (
    canonical_programme_name,
    programme_display_name,
)

from .bonafide_certificate import (
    _search_certificates,
    _student_name,
    _student_queryset,
    ordinal,
    register_certificate_fonts,
)

CERTIFICATE_TYPE = 'pointer_conv'


def build_pointer_conversion_context(student):
    batch = student.batch_id
    name = _student_name(student)
    gender = (student.id.sex or '').strip().upper()
    is_female = gender == 'F'
    salutation = 'Ms.' if is_female else 'Mr.'
    roll_number = student.id.user.username
    programme_full = programme_display_name(student.programme)
    programme_abbr = canonical_programme_name(student.programme)

    discipline = ''
    if batch and batch.discipline:
        discipline = batch.discipline.name
    elif student.id.department:
        discipline = student.id.department.name

    semester = student.curr_semester_no
    errors = []
    if not name:
        errors.append('Student name is unavailable.')
    if not roll_number:
        errors.append('Roll number is unavailable.')
    if not discipline:
        errors.append('Discipline is unavailable.')

    cpi_val = student.cpi
    if cpi_val and cpi_val > 0:
        cpi_str = str(cpi_val)
        if len(cpi_str.split('.')[-1]) > 2:
            cpi_display = f"{cpi_val:.2f}"
        else:
            cpi_display = cpi_str
    else:
        cpi_display = '……………'

    return {
        'student_id': student.pk,
        'name': name,
        'roll_number': roll_number,
        'gender': 'Female' if is_female else 'Male' if gender == 'M' else '',
        'salutation': salutation,
        'programme': programme_full,
        'programme_abbr': programme_abbr,
        'discipline': discipline,
        'semester': semester,
        'semester_ordinal': ordinal(semester) if semester else '',
        'cpi': cpi_val,
        'cpi_display': cpi_display,
        'min_cpi': '5.0',
        'is_ready': not errors,
        'validation_errors': errors,
    }


def render_pointer_conversion_pdf(
        context, cpi_text, min_cpi, reference_number, issued_on):
    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        topMargin=3.5 * cm,
        rightMargin=1.5 * cm,
        bottomMargin=2 * cm,
        leftMargin=1.5 * cm,
        title='Pointer Conversion Certificate',
        author=settings.BONAFIDE_INSTITUTE_NAME,
    )
    register_certificate_fonts()

    header_style = ParagraphStyle(
        'Header', fontName='Caladea-Bold', fontSize=11,
        leading=15, alignment=TA_JUSTIFY,
    )
    header_right_style = ParagraphStyle(
        'HeaderRight', parent=header_style, alignment=TA_RIGHT,
    )
    heading_style = ParagraphStyle(
        'Heading', fontName='Caladea-Bold', fontSize=11,
        leading=15, alignment=TA_CENTER,
    )
    body_style = ParagraphStyle(
        'Body', fontName='Caladea', fontSize=12,
        leading=20, alignment=TA_JUSTIFY,
    )
    detail_label_style = ParagraphStyle(
        'DetailLabel', fontName='Caladea-Bold', fontSize=12,
        leading=20,
    )
    detail_val_style = ParagraphStyle(
        'DetailVal', fontName='Caladea', fontSize=12,
        leading=20,
    )
    signature_style = ParagraphStyle(
        'Signature', fontName='Caladea-Bold', fontSize=11,
        leading=15, alignment=TA_JUSTIFY,
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
                f'Date – {issued_on.strftime("%d.%m.%Y")}',
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

    detail_rows = [
        [
            Paragraph('Name', detail_label_style),
            Paragraph(':', detail_label_style),
            Paragraph(f'{escape(context["salutation"])} {escape(context["name"])}', detail_val_style),
        ],
        [
            Paragraph('Roll No.', detail_label_style),
            Paragraph(':', detail_label_style),
            Paragraph(escape(context["roll_number"]), detail_val_style),
        ],
        [
            Paragraph('Branch', detail_label_style),
            Paragraph(':', detail_label_style),
            Paragraph(escape(context["discipline"]), detail_val_style),
        ],
        [
            Paragraph('CPI', detail_label_style),
            Paragraph(':', detail_label_style),
            Paragraph(escape(str(cpi_text)), detail_val_style),
        ],
    ]
    detail_table = Table(detail_rows, colWidths=[2.5 * cm, 0.6 * cm, 13 * cm])
    detail_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))

    story = [
        header,
        Spacer(1, 46),
        Paragraph('<u>TO WHOM SO EVER IT MAY CONCERN</u>', heading_style),
        Spacer(1, 36),
        Paragraph('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;This is to certify that:', body_style),
        Spacer(1, 14),
        Paragraph(
            f'1. The graduation requirement for {escape(context["programme"])} '
            f'({escape(context["programme_abbr"])}) programme at PDPM-IIITDM Jabalpur '
            f'is a minimum CPI of {escape(str(min_cpi))} out of the maximum of 10.0.',
            body_style,
        ),
        Spacer(1, 12),
        Paragraph(
            '2. Notionally, the CPI may be multiplied by a factor of 10 to obtain the numerical percentage.',
            body_style,
        ),
        Spacer(1, 24),
        Paragraph('<b>Issued to :</b>', body_style),
        Spacer(1, 12),
        detail_table,
        Spacer(1, 46),
        Paragraph(
            f'{escape(settings.BONAFIDE_SIGNATORY_NAME)}<br/>'
            f'{escape(settings.BONAFIDE_SIGNATORY_TITLE)}',
            signature_style,
        ),
    ]

    document.build(story)
    return output


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
@role_required(['acadadmin'])
def pointer_conversion_student(request):
    roll_number = (request.query_params.get('roll_number') or '').strip().upper()
    if not roll_number:
        return Response(
            {'error': 'A roll number is required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        student = _student_queryset().get(id__user__username=roll_number)
    except Exception:
        return Response(
            {'error': f"No student found with roll number '{roll_number}'."},
            status=status.HTTP_404_NOT_FOUND,
        )

    context = build_pointer_conversion_context(student)
    now = timezone.now()
    prefix = settings.BONAFIDE_REFERENCE_PREFIX.rstrip('/')
    reference_preview = f'{prefix}/{now.year}/{now.month:02d}/{roll_number}'

    certificate_meta = {
        'signatory_name': settings.BONAFIDE_SIGNATORY_NAME,
        'signatory_title': settings.BONAFIDE_SIGNATORY_TITLE,
        'reference_preview': reference_preview,
        'issued_on': now.strftime('%d.%m.%Y'),
        'institute_name': settings.BONAFIDE_INSTITUTE_NAME,
    }

    return Response({
        'student': context,
        'certificate': certificate_meta,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
@role_required(['acadadmin'])
def generate_pointer_conversion_pdf(request):
    student_id = request.data.get('student_id')
    if not student_id:
        return Response({'error': 'student_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

    student = get_object_or_404(_student_queryset(), pk=student_id)
    context = build_pointer_conversion_context(student)
    if not context['is_ready']:
        return Response({
            'error': 'Cannot issue certificate for student with incomplete data.',
            'details': context['validation_errors'],
        }, status=status.HTTP_400_BAD_REQUEST)

    cpi_text = request.data.get('cpi_text')
    if not cpi_text:
        cpi_text = context['cpi_display']
    cpi_text = str(cpi_text).strip()

    min_cpi = request.data.get('min_cpi')
    if not min_cpi:
        min_cpi = context['min_cpi']
    min_cpi = str(min_cpi).strip()

    issued_on = timezone.now().date()
    prefix = settings.BONAFIDE_REFERENCE_PREFIX.rstrip('/')
    roll_number = student.id.user.username
    reference_number = f'{prefix}/{issued_on.year}/{issued_on.month:02d}/{roll_number}'

    with transaction.atomic():
        certificate = BonafideCertificate.objects.create(
            student=student,
            purpose='Pointer Conversion',
            custom_purpose='',
            certificate_type=CERTIFICATE_TYPE,
            reference_number=reference_number,
            issued_by=request.user,
            fee_rows={'cpi': cpi_text, 'min_cpi': min_cpi},
        )
        pdf_bytes = render_pointer_conversion_pdf(
            context, cpi_text, min_cpi, reference_number, issued_on
        ).getvalue()
        certificate.pdf_content = pdf_bytes
        certificate.save(update_fields=['pdf_content'])

    filename = f'{roll_number}_Pointer_Conversion_Certificate.pdf'
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response['X-Certificate-Reference'] = reference_number
    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
@role_required(['acadadmin'])
def pointer_conversion_certificates(request):
    """List previously issued pointer conversion certificates."""
    page_number = int(request.query_params.get('page', 1))
    page_size = min(int(request.query_params.get('page_size', 20)), 100)
    search = (request.query_params.get('search') or '').strip()

    queryset = BonafideCertificate.objects.filter(
        certificate_type=CERTIFICATE_TYPE
    ).select_related('student__id__user', 'issued_by')

    queryset = _search_certificates(queryset, search)
    paginator = Paginator(queryset, page_size)
    page = paginator.get_page(page_number)

    results = []
    for cert in page.object_list:
        student = cert.student
        results.append({
            'id': cert.pk,
            'reference_number': cert.reference_number or f'CERT-{cert.pk:04d}',
            'roll_number': student.id.user.username,
            'student_name': _student_name(student),
            'issued_on': cert.issued_at.strftime('%d.%m.%Y'),
            'issued_by': cert.issued_by.get_full_name() or cert.issued_by.username,
            'purpose': cert.purpose,
        })

    return Response({
        'count': paginator.count,
        'page': page.number,
        'page_size': page_size,
        'total_pages': paginator.num_pages,
        'results': results,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
@role_required(['acadadmin'])
def pointer_conversion_certificate_pdf(request, certificate_id):
    cert = get_object_or_404(
        BonafideCertificate.objects.select_related('student__id__user'),
        pk=certificate_id, certificate_type=CERTIFICATE_TYPE,
    )
    if not cert.pdf_content:
        context = build_pointer_conversion_context(cert.student)
        cpi_data = cert.fee_rows or {}
        cpi_text = cpi_data.get('cpi') if isinstance(cpi_data, dict) else context['cpi_display']
        min_cpi = cpi_data.get('min_cpi') if isinstance(cpi_data, dict) else context['min_cpi']
        pdf_bytes = render_pointer_conversion_pdf(
            context, cpi_text, min_cpi, cert.reference_number, cert.issued_at.date()
        ).getvalue()
        cert.pdf_content = pdf_bytes
        cert.save(update_fields=['pdf_content'])
    else:
        pdf_bytes = bytes(cert.pdf_content)

    filename = f'{cert.student.id.user.username}_Pointer_Conversion_Certificate.pdf'
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response['X-Certificate-Reference'] = cert.reference_number or f'CERT-{cert.pk:04d}'
    return response
