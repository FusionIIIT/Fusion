import re
from datetime import datetime
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

from applications.academic_procedures.models import BonafideCertificate, DemandLetterBankAccounts
from applications.globals.decorators import role_required

from .bonafide_certificate import (
    _search_certificates,
    _student_queryset,
    build_certificate_context,
    ordinal,
)
from .fee_certificate import _is_concession, fee_structure_for, indian_currency

CERTIFICATE_TYPE = 'demand'


def _programme_short(student):
    return (student.programme or '').strip().upper().replace('.', '-')


def _discipline_with_acronym(student):
    batch = student.batch_id
    if batch and batch.discipline:
        name = batch.discipline.name
        acronym = batch.discipline.acronym
        return f'{name} ({acronym})' if acronym else name
    return ''


def semester_choices(structure):
    if not structure:
        return []
    return [{'value': i, 'label': f'{ordinal(i)} Semester'}
            for i in range(1, structure.semester_count + 1)]


def financial_year_for(student, semester):
    batch = student.batch_id
    if not batch or not semester:
        return None, ''
    start = batch.year + (semester - 1) // 2
    return start, f'{start}-{str(start + 1)[-2:]}'


def build_demand_row(student, structure, semester):
    column = 'concession' if _is_concession(student) else 'general'
    academic_fee = structure.semester_amount(
        column, semester, with_mess=False).quantize(Decimal('0.01'))
    mess_fee = Decimal(structure.mess_advance_per_semester or 0).quantize(Decimal('0.01'))
    category_label = (structure.concession_label if _is_concession(student)
                      else structure.general_label)
    return {
        'programme_short': _programme_short(student),
        'batch_year': student.batch_id.year if student.batch_id else None,
        'category_label': category_label,
        'academic_fee': str(academic_fee),
        'academic_fee_display': indian_currency(academic_fee),
        'mess_fee': str(mess_fee),
        'mess_fee_display': indian_currency(mess_fee),
        'total_display': indian_currency(academic_fee + mess_fee),
    }


BANK_FIELDS = ('name', 'number', 'ifsc', 'bank_branch', 'account_type')


def _bank_account(account):
    return {field: (account or {}).get(field, '') for field in BANK_FIELDS}


def _bank_details():
    accounts = DemandLetterBankAccounts.load()
    return {
        'academic': _bank_account(accounts.academic_fee_account),
        'mess': _bank_account(accounts.mess_fee_account),
    }


def _bank_account_missing(account):
    return not all((account or {}).get(field) for field in ('name', 'number', 'ifsc'))


def render_demand_letter_pdf(context, semester, academic_year_label, due_date,
                             demand, bank, reference_number, issued_on):
    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        topMargin=3.5 * cm,
        rightMargin=1.5 * cm,
        bottomMargin=2 * cm,
        leftMargin=1.5 * cm,
        title='Demand Letter',
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
    sub_heading_style = ParagraphStyle(
        'SubHeading', fontName='Caladea-Bold', fontSize=11,
        leading=15, alignment=TA_CENTER,
    )
    cell_style = ParagraphStyle(
        'Cell', fontName='Caladea', fontSize=11, leading=14, alignment=TA_JUSTIFY,
    )
    cell_bold_style = ParagraphStyle(
        'CellBold', parent=cell_style, fontName='Caladea-Bold',
    )
    cell_center_style = ParagraphStyle(
        'CellCenter', parent=cell_style, alignment=TA_CENTER,
    )
    cell_bold_right_style = ParagraphStyle(
        'CellBoldRight', parent=cell_bold_style, alignment=TA_RIGHT,
    )
    bank_label_style = ParagraphStyle(
        'BankLabel', fontName='Caladea-Bold', fontSize=11, leading=14,
        alignment=TA_JUSTIFY,
    )
    bank_value_style = ParagraphStyle(
        'BankValue', fontName='Caladea', fontSize=11, leading=14,
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

    body_text = (
        'This is certify that '
        f'<b>{escape(context["salutation"])} {escape(context["name"])}</b> '
        f'(Roll No. {escape(context["roll_number"])}) '
        f'{escape(context["relation"])} '
        f'<b>MR. {escape(context["father_name"])}</b> is a bonafide student of '
        f'<b>{escape(context["year_ordinal"])} year</b> '
        f'({escape(context["semester_ordinal"])} Semester) of '
        f'<b>{escape(context["programme"])}</b> Programme in '
        f'<b>{escape(context["discipline_with_acronym"])}</b> at '
        f'{escape(settings.BONAFIDE_INSTITUTE_NAME)}. '
        'The Date of fees submission as detailed below for Semester '
        f'<b>{escape(ordinal(semester))}</b>, <b>{escape(academic_year_label)}</b> '
        f'is on or before <b>{due_date.strftime("%B %d, %Y")}</b>.'
    )

    fee_rows = [[
        Paragraph(escape(str(demand['batch_year'] or '')), cell_style),
        Paragraph(escape(demand['category_label']), cell_style),
        Paragraph('Academic Fee', cell_style),
        Paragraph(escape(f"{demand['academic_fee_display']}/-"), cell_style),
    ], [
        '', '',
        Paragraph('Mess Fee', cell_style),
        Paragraph(escape(f"{demand['mess_fee_display']}/-"), cell_style),
    ], [
        Paragraph('Total Rs. =', cell_bold_right_style), '', '',
        Paragraph(escape(f"{demand['total_display']}/-"), cell_bold_style),
    ]]
    fee_header = [
        Paragraph(escape(demand['programme_short']), cell_bold_style),
        Paragraph('Category', cell_bold_style),
        Paragraph('Fee', cell_bold_style),
        Paragraph('Amount', cell_bold_style),
    ]
    fee_table = Table(
        [fee_header] + fee_rows,
        colWidths=[3 * cm, 3.5 * cm, 4 * cm, 3.5 * cm], hAlign='LEFT',
    )
    fee_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('SPAN', (0, 1), (0, 2)),
        ('SPAN', (1, 1), (1, 2)),
        ('SPAN', (0, 3), (2, 3)),
    ]))

    def bank_block(details):
        rows = [
            [Paragraph('Account<br/>Name', bank_label_style),
             Paragraph(escape(details['name']), bank_value_style)],
            [Paragraph('Account<br/>Number', bank_label_style),
             Paragraph(escape(details['number']), bank_value_style)],
            [Paragraph('IFSC', bank_label_style),
             Paragraph(escape(details['ifsc']), bank_value_style)],
            [Paragraph('Bank &<br/>Branch', bank_label_style),
             Paragraph(escape(details['bank_branch']), bank_value_style)],
            [Paragraph('Account<br/>Type', bank_label_style),
             Paragraph(escape(details['account_type']), bank_value_style)],
        ]
        table = Table(rows, colWidths=[2.3 * cm, 5.7 * cm])
        table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        return table

    bank_side_by_side = Table(
        [[
            Paragraph('Academic Fee', sub_heading_style),
            Paragraph('Mess Fee', sub_heading_style),
        ], [
            bank_block(bank['academic']),
            bank_block(bank['mess']),
        ]],
        colWidths=[9 * cm, 9 * cm],
    )
    bank_side_by_side.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))

    story = [
        header,
        Spacer(1, 1.2 * cm),
        Paragraph('<u>TO WHOM SO EVER IT MAY CONCERN</u>', heading_style),
        Spacer(1, 1 * cm),
        Paragraph(body_text, body_style),
        Spacer(1, 0.5 * cm),
        fee_table,
        Spacer(1, 0.4 * cm),
        Paragraph(
            'The above mentioned fee is to be paid through online mode only, '
            'Institute bank details are as follows:', body_style,
        ),
        Spacer(1, 0.4 * cm),
        Paragraph('<u>Bank A/c Details for Transferring Fee</u>', sub_heading_style),
        Spacer(1, 0.3 * cm),
        bank_side_by_side,
        Spacer(1, 1.3 * cm),
        Paragraph(f'({escape(settings.BONAFIDE_SIGNATORY_NAME)})', signature_style),
    ]

    document.build(story)
    output.seek(0)
    return output


def _certificate_filename(certificate):
    roll_number = certificate.student.id.user.username
    safe_roll_number = re.sub(r'[^A-Za-z0-9_-]', '_', roll_number)
    return f'{safe_roll_number}_Demand_Letter_{certificate.pk:03d}.pdf'


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


def _certificates_queryset():
    return BonafideCertificate.objects.filter(
        certificate_type=CERTIFICATE_TYPE).select_related(
        'student__id__user', 'issued_by')


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@role_required(['acadadmin'])
def demand_letter_student(request):
    roll_number = (request.query_params.get('roll_number') or '').strip().upper()
    if not roll_number:
        return Response({'error': 'roll_number is required.'},
                        status=status.HTTP_400_BAD_REQUEST)

    student = get_object_or_404(
        _student_queryset(), pk=roll_number,
        id__user__is_active=True, id__user_status='PRESENT',
    )
    context = build_certificate_context(student)
    structure = fee_structure_for(student)
    errors = list(context['validation_errors'])

    if structure is None:
        batch_label = context.get('programme') or 'unrecognised'
        errors.append(
            f'No fee structure is recorded for {batch_label} programmes. '
            'Add one before issuing this certificate.')

    bank = _bank_details()
    if _bank_account_missing(bank['academic']) or _bank_account_missing(bank['mess']):
        errors.append(
            'The institute bank account details have not been set up yet. '
            'Add them before issuing this certificate.')

    semester_param = request.query_params.get('semester')
    default_semester = context['semester'] or 1
    try:
        semester = int(semester_param) if semester_param else default_semester
    except (TypeError, ValueError):
        semester = default_semester
    if structure and not (1 <= semester <= structure.semester_count):
        semester = min(max(default_semester, 1), structure.semester_count)

    demand = build_demand_row(student, structure, semester) if structure else None
    _, academic_year_label = financial_year_for(student, semester)

    issued_on = timezone.now().date()
    prefix = settings.BONAFIDE_REFERENCE_PREFIX.rstrip('/')
    next_serial = (BonafideCertificate.objects.aggregate(
        max_id=Max('pk'))['max_id'] or 0) + 1

    return Response({
        'student': {
            **context, 'is_ready': not errors, 'validation_errors': errors,
            'discipline_with_acronym': _discipline_with_acronym(student),
        },
        'semesters': semester_choices(structure),
        'selected_semester': semester,
        'academic_year_label': academic_year_label,
        'demand': demand,
        'bank': bank,
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
def generate_demand_letter_pdf(request):
    student_id = request.data.get('student_id')
    semester_raw = request.data.get('semester')
    due_date_raw = (request.data.get('due_date') or '').strip()

    if not student_id:
        return Response({'error': 'student_id is required.'},
                        status=status.HTTP_400_BAD_REQUEST)
    try:
        semester = int(semester_raw)
    except (TypeError, ValueError):
        return Response({'error': 'Select a valid semester.'},
                        status=status.HTTP_400_BAD_REQUEST)
    try:
        due_date = datetime.strptime(due_date_raw, '%Y-%m-%d').date()
    except ValueError:
        return Response({'error': 'Select a valid due date.'},
                        status=status.HTTP_400_BAD_REQUEST)

    student = get_object_or_404(_student_queryset(), pk=student_id)
    context = build_certificate_context(student)
    if not context['is_ready']:
        return Response(
            {'error': 'Student data is incomplete.',
             'details': context['validation_errors']},
            status=status.HTTP_400_BAD_REQUEST)
    context['discipline_with_acronym'] = _discipline_with_acronym(student)

    structure = fee_structure_for(student)
    if structure is None:
        return Response(
            {'error': 'No fee structure is recorded for this programme.'},
            status=status.HTTP_400_BAD_REQUEST)
    if not (1 <= semester <= structure.semester_count):
        return Response(
            {'error': 'Semester is outside the published fee structure.'},
            status=status.HTTP_400_BAD_REQUEST)

    bank = _bank_details()
    if _bank_account_missing(bank['academic']) or _bank_account_missing(bank['mess']):
        return Response(
            {'error': 'The institute bank account details have not been '
                      'set up yet.'},
            status=status.HTTP_400_BAD_REQUEST)

    demand = build_demand_row(student, structure, semester)
    _, academic_year_label = financial_year_for(student, semester)

    issued_on = timezone.now().date()
    prefix = settings.BONAFIDE_REFERENCE_PREFIX.rstrip('/')
    with transaction.atomic():
        certificate = BonafideCertificate.objects.create(
            student=student,
            certificate_type=CERTIFICATE_TYPE,
            purpose=f'{ordinal(semester)} Semester Fee Demand',
            fee_rows=[{
                **demand,
                'semester': semester,
                'academic_year': academic_year_label,
                'due_date': due_date.isoformat(),
            }],
            issued_by=request.user,
        )
        reference_number = (
            f'{prefix}/{issued_on.year}/{issued_on.month:02d}/'
            f'{context["roll_number"]}/{certificate.pk:03d}')
        certificate.reference_number = reference_number
        document = render_demand_letter_pdf(
            context, semester, academic_year_label, due_date, demand, bank,
            reference_number, issued_on)
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
def demand_letters(request):
    queryset = _search_certificates(
        _certificates_queryset(), (request.query_params.get('search') or '').strip())
    page = Paginator(queryset, 10).get_page(request.query_params.get('page') or 1)
    return Response({
        'count': page.paginator.count,
        'page': page.number,
        'total_pages': page.paginator.num_pages,
        'results': [{
            'id': certificate.pk,
            'serial_number': f'{certificate.pk:03d}',
            'reference_number': _certificate_reference(certificate),
            'roll_number': certificate.student.id.user.username,
            'name': certificate.student.id.user.get_full_name().strip(),
            'purpose': certificate.purpose,
            'issued_on': certificate.issued_at.strftime('%d.%m.%Y'),
        } for certificate in page],
    })


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@role_required(['acadadmin'])
def demand_letter_pdf(request, certificate_id):
    certificate = get_object_or_404(_certificates_queryset(), pk=certificate_id)
    if not certificate.pdf_content:
        return Response(
            {'error': 'The stored certificate is unavailable. Generate it again.'},
            status=status.HTTP_404_NOT_FOUND)
    disposition = (
        'attachment'
        if request.query_params.get('download') in {'1', 'true', 'True'}
        else 'inline'
    )
    response = HttpResponse(bytes(certificate.pdf_content),
                            content_type='application/pdf')
    response['Content-Disposition'] = (
        f'{disposition}; filename="{_certificate_filename(certificate)}"')
    return response
