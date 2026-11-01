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
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
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

from applications.examination.api.views import calculate_cpi_for_student

CERTIFICATE_TYPE = 'pointer_conv'


def resolve_student_cpi(student):
    """The student's CPI as of their last term whose result is declared, a
    summer term included, as Grade Validation and the grade card count it.
    Returns (cpi, semester), or (0.0, None) when no result is out yet."""
    from applications.examination.api.views import result_declared_for
    from applications.online_cms.models import Student_grades

    term_order = {'Odd Semester': 0, 'Even Semester': 1, 'Summer Semester': 2}
    terms = sorted(
        set(Student_grades.objects.filter(roll_no=student.id_id)
            .values_list('semester', 'semester_type')),
        key=lambda t: (t[0] or 0, term_order.get(t[1], 3)),
        reverse=True,
    )
    for semester, semester_type in terms:
        if semester and result_declared_for(student, semester, semester_type):
            cpi, _, _ = calculate_cpi_for_student(student, semester, semester_type)
            return float(cpi or 0), semester
    return 0.0, None


CPI_PATTERN = re.compile(r'^(10(\.0{1,2})?|\d(\.\d{1,2})?)$')


def _valid_cpi(value):
    """A CPI as printed on the certificate: 0 to 10, at most two decimals."""
    return bool(CPI_PATTERN.match(value or ''))


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

    cpi_val, till_sem = resolve_student_cpi(student)
    if cpi_val and cpi_val > 0:
        cpi_str = f"{cpi_val:.2f}"
        if cpi_str.endswith('0'):
            cpi_str = f"{cpi_val:.1f}"
        cpi_display = cpi_str
    else:
        cpi_display = ''

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


def _reference_number(roll_number, issued_on, serial):
    """Numbered as the bonafide certificate is: the serial follows the roll
    number, IIITDMJ/AR/<year>/<month>/<roll>/<serial>."""
    prefix = settings.BONAFIDE_REFERENCE_PREFIX.rstrip('/')
    return (f'{prefix}/{issued_on.year}/{issued_on.month:02d}/'
            f'{roll_number}/{serial:03d}')


def render_pointer_conversion_pdf(
        context, cpi_text, min_cpi, reference_number, issued_on):
    """Laid out as the Academic section's Pointer Conversion format, in the
    same type as the bonafide and every other certificate: Caladea, at the
    bonafide's sizes, spacing and margins."""
    from reportlab.pdfbase.pdfmetrics import stringWidth
    from reportlab.platypus import ListFlowable, ListItem

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
        'Header', fontName='Caladea-Bold', fontSize=11, leading=15)
    heading_style = ParagraphStyle(
        'Heading', fontName='Caladea-Bold', fontSize=11, leading=15,
        alignment=TA_CENTER)
    body_style = ParagraphStyle(
        'Body', fontName='Caladea', fontSize=12, leading=20,
        alignment=TA_JUSTIFY)
    issued_style = ParagraphStyle(
        'Issued', parent=body_style, fontName='Caladea-Bold',
        leftIndent=0.7 * cm)
    detail_style = ParagraphStyle(
        'Detail', fontName='Caladea', fontSize=12, leading=20)
    signature_style = ParagraphStyle(
        'Signature', fontName='Caladea-Bold', fontSize=11, leading=15,
        alignment=TA_JUSTIFY)

    # The reference block sits at the right margin with its two lines
    # starting together, as the format prints them.
    right_lines = [escape(reference_number),
                   f'Date \u2013 {issued_on.strftime("%d.%m.%Y")}']
    right_width = max(stringWidth(line, 'Caladea-Bold', 11)
                      for line in right_lines) + 2
    reference_block = Table(
        [[Paragraph('<br/>'.join(right_lines), header_style)]],
        colWidths=[right_width], hAlign='RIGHT')
    reference_block.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    page_width = A4[0] - document.leftMargin - document.rightMargin
    header = Table(
        [[
            Paragraph(
                f'{escape(settings.BONAFIDE_SIGNATORY_NAME)}<br/>'
                f'{escape(settings.BONAFIDE_SIGNATORY_TITLE)}',
                header_style,
            ),
            reference_block,
        ]],
        colWidths=[page_width - right_width, right_width],
    )
    header.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))

    points = ListFlowable(
        [
            ListItem(Paragraph(
                'The graduation requirement for '
                f'<b>{escape(context["programme"])}</b> '
                f'({escape(context["programme_abbr"])}) programme at '
                'PDPM-IIITDM Jabalpur is a minimum CPI of '
                f'{escape(str(min_cpi))} out of the maximum of 10.0.',
                body_style)),
            ListItem(Paragraph(
                'Notionally, the CPI may be multiplied by a factor of 10 to '
                'obtain the numerical percentage.',
                body_style)),
        ],
        bulletType='1', bulletFormat='%s.', bulletFontName='Caladea',
        bulletFontSize=12, leftIndent=0.7 * cm, bulletDedent=0.6 * cm,
    )

    detail_rows = [
        [Paragraph(label, detail_style), Paragraph(':', detail_style),
         Paragraph(value, detail_style)]
        for label, value in (
            ('Name', f'{escape(context["salutation"])} {escape(context["name"])}'),
            ('Roll No.', escape(context['roll_number'])),
            ('Branch', escape(context['discipline'])),
            ('CPI', escape(str(cpi_text or '\u2026\u2026\u2026\u2026\u2026'))),
        )
    ]
    # The labels line up under the numbered points.
    details = Table(detail_rows, colWidths=[2.9 * cm, 0.5 * cm, 12 * cm],
                    hAlign='LEFT')
    details.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (0, -1), 0.7 * cm),
        ('LEFTPADDING', (1, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))

    story = [
        header,
        Spacer(1, 1.65 * cm),
        Paragraph('<u>TO WHOM SO EVER IT MAY CONCERN</u>', heading_style),
        Spacer(1, 1.25 * cm),
        Paragraph('This is to certify that:', body_style),
        Spacer(1, 0.2 * cm),
        points,
        Spacer(1, 0.9 * cm),
        Paragraph('Issued to :', issued_style),
        Spacer(1, 0.2 * cm),
        details,
        Spacer(1, 1.6 * cm),
        Paragraph(escape(settings.BONAFIDE_SIGNATORY_NAME), signature_style),
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
        student = _student_queryset().get(
            id__user__username=roll_number,
            id__user__is_active=True, id__user_status='PRESENT')
    except Student.DoesNotExist:
        return Response(
            {'error': f"No student found with roll number '{roll_number}'."},
            status=status.HTTP_404_NOT_FOUND,
        )

    context = build_pointer_conversion_context(student)
    now = timezone.now()
    next_serial = (BonafideCertificate.objects.aggregate(
        max_id=Max('pk'))['max_id'] or 0) + 1
    reference_preview = _reference_number(roll_number, now.date(), next_serial)

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

    student = get_object_or_404(
        _student_queryset(), pk=student_id,
        id__user__is_active=True, id__user_status='PRESENT')
    context = build_pointer_conversion_context(student)
    if not context['is_ready']:
        return Response({
            'error': 'Cannot issue certificate for student with incomplete data.',
            'details': context['validation_errors'],
        }, status=status.HTTP_400_BAD_REQUEST)

    cpi_text = str(request.data.get('cpi_text') or context['cpi_display']).strip()
    min_cpi = str(request.data.get('min_cpi') or context['min_cpi']).strip()
    errors = []
    if not _valid_cpi(cpi_text):
        errors.append('CPI must be a number from 0 to 10 with at most two decimals.')
    if not _valid_cpi(min_cpi):
        errors.append('Minimum CPI must be a number from 0 to 10 with at most two decimals.')
    if errors:
        return Response({'error': ' '.join(errors)}, status=status.HTTP_400_BAD_REQUEST)

    issued_on = timezone.now().date()
    roll_number = student.id.user.username

    with transaction.atomic():
        certificate = BonafideCertificate.objects.create(
            student=student,
            purpose='Pointer Conversion',
            custom_purpose='',
            certificate_type=CERTIFICATE_TYPE,
            issued_by=request.user,
            fee_rows={'cpi': cpi_text, 'min_cpi': min_cpi},
        )
        reference_number = _reference_number(
            roll_number, issued_on, certificate.pk)
        certificate.reference_number = reference_number
        certificate.save(update_fields=['reference_number'])
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
    page_number = request.query_params.get('page', 1)
    try:
        page_size = min(max(int(request.query_params.get('page_size', 20)), 1), 100)
    except (TypeError, ValueError):
        page_size = 20
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
