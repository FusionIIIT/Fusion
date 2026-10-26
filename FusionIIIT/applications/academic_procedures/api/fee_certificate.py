"""The Paid / Unpaid Fee Certificate.

Built on the bonafide certificate: the same header, the same signatory, the
same reference numbering and the same record table. What differs is one line
of body text and a semester-wise fee table whose Paid / Unpaid column the
academic office sets before generating.
"""
import re
from decimal import Decimal
from io import BytesIO

from django.conf import settings
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Max
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from reportlab.lib import colors
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
from xml.sax.saxutils import escape

from applications.academic_procedures.models import BonafideCertificate, FeeStructure
from applications.globals.decorators import role_required

from .bonafide_certificate import (
    _certificate_reference,
    programme_category,
    _search_certificates,
    _student_queryset,
    build_certificate_context,
    ordinal,
    superscript_ordinal,
)

CERTIFICATE_TYPE = 'fee'

PURPOSE_CHOICES = (
    ('Scholarship', 'Scholarship'),
    ('Education Loan', 'Education Loan'),
    ('Bihar Student Credit Card', 'Bihar Student Credit Card'),
    ('Other', 'Other'),
)

PAID = 'Paid'
UNPAID = 'Unpaid'

#: Concession holders. EWS is not one: the waiver follows caste and disability.
CONCESSION_CATEGORIES = {'SC', 'ST'}


def _is_concession(student):
    return (student.category or '').strip().upper() in CONCESSION_CATEGORIES \
        or bool(student.is_pwd)


def indian_currency(amount):
    """1,05,250.00 — grouped in lakhs, which is what the certificate shows."""
    quantised = Decimal(amount).quantize(Decimal('0.01'))
    whole, _, fraction = f'{quantised:.2f}'.partition('.')
    sign, whole = ('-', whole[1:]) if whole.startswith('-') else ('', whole)
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        head = re.sub(r'(\d)(?=(\d\d)+$)', r'\1,', head)
        whole = f'{head},{tail}'
    return f'{sign}{whole}.{fraction}'


def fee_structure_for(student):
    """The structure for this student's category and session, or the newest
    earlier one. A batch's year is the session its fees were published for."""
    category = programme_category(student)
    batch = student.batch_id
    if not category or batch is None:
        return None
    rows = FeeStructure.objects.filter(programme_category__iexact=category,
                                       is_active=True)
    return (rows.filter(start_year__lte=batch.year).order_by('-start_year').first()
            or rows.order_by('-start_year').first())


def build_fee_rows(student, structure, current_semester, semesters=None):
    """One row per semester, with the status the office would expect.

    The first semester carries the one-time heads; every semester carries the
    recurring ones plus mess, which the published grand total leaves out.

    Semesters already behind the student default to Paid, the one they are in
    is left blank so it has to be chosen, and the rest default to Unpaid.
    """
    column = 'concession' if _is_concession(student) else 'general'
    total_semesters = semesters or structure.semester_count

    rows = []
    for index in range(1, total_semesters + 1):
        # Quantised, so a stored row reads the same however the heads were typed.
        amount = structure.semester_amount(column, index).quantize(Decimal('0.01'))
        if index < current_semester:
            payment_status = PAID
        elif index == current_semester:
            payment_status = ''
        else:
            payment_status = UNPAID
        rows.append({
            'semester': index,
            'label': f'{ordinal(index)} Semester',
            'amount': str(amount),
            'amount_display': indian_currency(amount),
            'status': payment_status,
        })
    return rows


def _clean_rows(submitted, expected):
    """Validate what came back from the form against what we offered."""
    by_semester = {}
    for row in submitted or []:
        try:
            by_semester[int(row.get('semester'))] = (row.get('status') or '').strip()
        except (TypeError, ValueError):
            continue

    cleaned, errors = [], []
    for row in expected:
        chosen = by_semester.get(row['semester'], '')
        if chosen not in (PAID, UNPAID):
            errors.append(f'Select Paid or Unpaid for the {row["label"]}.')
            continue
        cleaned.append({**row, 'status': chosen})
    return cleaned, errors


def _total(rows):
    return sum((Decimal(row['amount']) for row in rows), Decimal('0'))


def render_fee_pdf(context, purpose, reference_number, issued_on, rows,
                   notes=()):
    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        topMargin=3.5 * cm,
        rightMargin=1.5 * cm,
        bottomMargin=2 * cm,
        leftMargin=1.5 * cm,
        title='Fee Certificate',
        author=settings.BONAFIDE_INSTITUTE_NAME,
    )
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
        leading=17, alignment=TA_JUSTIFY,
    )
    bullet_style = ParagraphStyle(
        'Bullet', parent=body_style, fontName='Caladea-Bold', fontSize=11,
        leading=15, leftIndent=0.6 * cm, bulletIndent=0.1 * cm,
    )
    note_style = ParagraphStyle(
        'Note', parent=body_style, fontName='Carlito', fontSize=11,
        leftIndent=0.6 * cm, bulletIndent=0.1 * cm, leading=15,
    )
    cell_style = ParagraphStyle(
        # Room for the raised ordinal suffix, which overflows a tighter line.
        'Cell', fontName='Caladea', fontSize=11, leading=15,
        alignment=TA_JUSTIFY,
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
        f'<b>{superscript_ordinal(context["year_ordinal"])} Year</b> '
        f'({superscript_ordinal(context["semester_ordinal"])} Semester) '
        f'<b>{escape(context["programme"])}</b> in '
        f'<b>{escape(context["discipline"])}</b> '
        f'({escape(context["duration_text"])} course duration: '
        f'<b>{context["start_year"]}</b> to <b>{context["end_year"]}</b>) at '
        f'{escape(settings.BONAFIDE_INSTITUTE_NAME)}.'
    )
    # The short form, as the certificate shows it: "B.Tech", not the
    # expanded name the opening sentence uses.
    # Continues the same paragraph; the circular has no break after Jabalpur.
    first_text += (
        f' The fee details of <b>{escape(context["programme_short"])}</b> '
        f'Programme for the purpose of applying for <b>{escape(purpose)}</b> '
        f'are given below:'
    )

    table_rows = [[
        Paragraph(str(row['semester']), cell_style),
        Paragraph(superscript_ordinal(ordinal(row['semester'])) + ' Semester',
                  cell_style),
        Paragraph(escape(row['amount_display']), cell_style),
        Paragraph(escape(row['status']), cell_style),
    ] for row in rows]
    table_rows.append([
        Paragraph('Total', ParagraphStyle('TotalCell', parent=cell_style,
                                          alignment=TA_CENTER)),
        '',
        Paragraph(escape(indian_currency(_total(rows))), cell_style),
        '',
    ])

    fee_table = Table(table_rows,
                      colWidths=[1.1 * cm, 4.4 * cm, 3.4 * cm, 2.4 * cm],
                      hAlign='CENTER')
    fee_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        # The total spans the serial and semester columns, as on the original.
        ('SPAN', (0, len(rows)), (1, len(rows))),
    ]))

    story = [
        header,
        Spacer(1, 1.65 * cm),
        Paragraph('<u>TO WHOM SO EVER IT MAY CONCERN</u>', heading_style),
        Spacer(1, 1.25 * cm),
        Paragraph(first_text, body_style),
        Spacer(1, 0.4 * cm),
        Paragraph('Semester Wise Fee Details:', bullet_style, bulletText='•'),
        Spacer(1, 0.2 * cm),
        fee_table,
        Spacer(1, 0.45 * cm),
    ]
    # Printed from the structure, so rewording one needs no deploy.
    for note in notes or []:
        story.append(Paragraph(escape(note), note_style, bulletText='•'))
    story.extend([
        Spacer(1, 1.6 * cm),
        Paragraph(f'({escape(settings.BONAFIDE_SIGNATORY_NAME)})', signature_style),
    ])

    document.build(story)
    output.seek(0)
    return output


def _effective_purpose(certificate):
    if certificate.purpose == 'Other':
        return certificate.custom_purpose
    return certificate.purpose


def _certificate_filename(certificate):
    roll_number = certificate.student.id.user.username
    safe_roll_number = re.sub(r'[^A-Za-z0-9_-]', '_', roll_number)
    return f'{safe_roll_number}_Fee_Certificate_{certificate.pk:03d}.pdf'


def _certificates_queryset():
    return BonafideCertificate.objects.filter(
        certificate_type=CERTIFICATE_TYPE).select_related(
        'student__id__user', 'issued_by')


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@role_required(['acadadmin'])
def fee_student(request):
    roll_number = (request.query_params.get('roll_number') or '').strip().upper()
    if not roll_number:
        return Response({'error': 'roll_number is required.'},
                        status=status.HTTP_400_BAD_REQUEST)

    student = get_object_or_404(
        _student_queryset(), pk=roll_number,
        id__user__is_active=True, id__user_status='PRESENT',
    )
    context = build_certificate_context(student)
    context['programme_short'] = (student.programme or '').strip()
    structure = fee_structure_for(student)
    batch_label = programme_category(student) or 'unrecognised'
    rows, errors = [], list(context['validation_errors'])
    notes = []

    if structure is None:
        errors.append(
            f'No fee structure is recorded for {batch_label} programmes. '
            'Add one before issuing this certificate.')
    elif structure.semester_heads:
        rows = build_fee_rows(student, structure, context['semester'])
        notes = structure.notes

    issued_on = timezone.now().date()
    prefix = settings.BONAFIDE_REFERENCE_PREFIX.rstrip('/')
    next_serial = (BonafideCertificate.objects.aggregate(
        max_id=Max('pk'))['max_id'] or 0) + 1

    return Response({
        'student': {**context, 'is_ready': not errors,
                    'validation_errors': errors},
        'fee': {
            'rows': rows,
            'total_display': indian_currency(_total(rows)) if rows else '',
            'notes': list(notes),
            'is_concession': _is_concession(student),
        },
        'purposes': [{'value': value, 'label': label}
                     for value, label in PURPOSE_CHOICES],
        'certificate': {
            'signatory_name': settings.BONAFIDE_SIGNATORY_NAME,
            'signatory_title': settings.BONAFIDE_SIGNATORY_TITLE,
            'institute_name': settings.BONAFIDE_INSTITUTE_NAME,
            'issued_on': issued_on.strftime('%d.%m.%Y'),
            'reference_preview': (
                f'{prefix}/{issued_on.year}/{issued_on.month:02d}/'
                f'{context["roll_number"]}/{next_serial:03d}'),
        },
    })


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@role_required(['acadadmin'])
def generate_fee_pdf(request):
    student_id = request.data.get('student_id')
    purpose = request.data.get('purpose')
    custom_purpose = (request.data.get('custom_purpose') or '').strip()
    valid_purposes = dict(PURPOSE_CHOICES)

    if not student_id:
        return Response({'error': 'student_id is required.'},
                        status=status.HTTP_400_BAD_REQUEST)
    if purpose not in valid_purposes:
        return Response({'error': 'Select a valid certificate purpose.'},
                        status=status.HTTP_400_BAD_REQUEST)
    if purpose == 'Other' and not custom_purpose:
        return Response({'error': 'Enter the certificate purpose.'},
                        status=status.HTTP_400_BAD_REQUEST)
    if len(custom_purpose) > 150:
        return Response(
            {'error': 'The certificate purpose cannot exceed 150 characters.'},
            status=status.HTTP_400_BAD_REQUEST)

    effective_purpose = custom_purpose if purpose == 'Other' else purpose
    student = get_object_or_404(_student_queryset(), pk=student_id)
    context = build_certificate_context(student)
    context['programme_short'] = (student.programme or '').strip()
    if not context['is_ready']:
        return Response(
            {'error': 'Student data is incomplete.',
             'details': context['validation_errors']},
            status=status.HTTP_400_BAD_REQUEST)

    structure = fee_structure_for(student)
    if structure is None:
        return Response(
            {'error': 'No fee structure is recorded for this programme.'},
            status=status.HTTP_400_BAD_REQUEST)

    expected = build_fee_rows(student, structure, context['semester'])
    rows, errors = _clean_rows(request.data.get('rows'), expected)
    if errors:
        return Response({'error': 'Every semester needs a Paid or Unpaid mark.',
                         'details': errors},
                        status=status.HTTP_400_BAD_REQUEST)

    issued_on = timezone.now().date()
    prefix = settings.BONAFIDE_REFERENCE_PREFIX.rstrip('/')
    with transaction.atomic():
        certificate = BonafideCertificate.objects.create(
            student=student,
            certificate_type=CERTIFICATE_TYPE,
            purpose=purpose,
            custom_purpose=custom_purpose if purpose == 'Other' else '',
            fee_rows=rows,
            issued_by=request.user,
        )
        reference_number = (
            f'{prefix}/{issued_on.year}/{issued_on.month:02d}/'
            f'{context["roll_number"]}/{certificate.pk:03d}')
        certificate.reference_number = reference_number
        document = render_fee_pdf(
            context, effective_purpose, reference_number, issued_on, rows,
            notes=structure.notes)
        document_bytes = document.getvalue()
        certificate.pdf_content = document_bytes
        certificate.save(update_fields=['reference_number', 'pdf_content'])

    response = HttpResponse(document_bytes, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="{_certificate_filename(certificate)}"')
    response['X-Certificate-Reference'] = reference_number
    return response


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@role_required(['acadadmin'])
def fee_certificates(request):
    queryset = _search_certificates(
        _certificates_queryset(), (request.query_params.get('search') or '').strip())
    page = Paginator(queryset, 10).get_page(request.query_params.get('page') or 1)
    return Response({
        'count': page.paginator.count,
        'page': page.number,
        'num_pages': page.paginator.num_pages,
        'results': [{
            'id': certificate.pk,
            'reference_number': _certificate_reference(certificate),
            'roll_number': certificate.student.id.user.username,
            'name': certificate.student.id.user.get_full_name().strip(),
            'purpose': _effective_purpose(certificate),
            'issued_on': certificate.issued_at.strftime('%d.%m.%Y'),
            'issued_by': certificate.issued_by.get_full_name().strip(),
        } for certificate in page],
    })


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@role_required(['acadadmin'])
def fee_certificate_pdf(request, certificate_id):
    certificate = get_object_or_404(_certificates_queryset(), pk=certificate_id)
    if not certificate.pdf_content:
        return Response(
            {'error': 'The stored certificate is unavailable. Generate it again.'},
            status=status.HTTP_404_NOT_FOUND)
    response = HttpResponse(bytes(certificate.pdf_content),
                            content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="{_certificate_filename(certificate)}"')
    return response
