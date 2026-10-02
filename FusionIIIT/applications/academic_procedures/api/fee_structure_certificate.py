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
from reportlab.lib.enums import TA_CENTER, TA_LEFT
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

from applications.academic_procedures.models import BonafideCertificate
from applications.globals.decorators import role_required

from .bonafide_certificate import (
    _search_certificates,
    _student_queryset,
    build_certificate_context,
)
from .demand_letter import financial_year_for
from .fee_certificate import _is_concession, fee_structure_for, indian_currency

CERTIFICATE_TYPE = 'fee_structure'

ONE_TIME_LABEL = 'One-time payment is paid only once at the time of admission'


def session_semesters(semester):
    odd = semester if semester % 2 else semester - 1
    return odd, odd + 1


def build_structure_rows(student, structure, odd_semester):
    column = 'concession' if _is_concession(student) else 'general'
    even_semester = odd_semester + 1
    rows = []
    for heads in (structure.tuition_hostel_heads, structure.semester_heads):
        for head in heads or []:
            sem1 = structure._amount(head, column, odd_semester)
            sem2 = structure._amount(head, column, even_semester)
            rows.append({
                'label': head.get('head', ''),
                'sem1': str(sem1.quantize(Decimal('0.01'))),
                'sem2': str(sem2.quantize(Decimal('0.01'))),
                'total': str((sem1 + sem2).quantize(Decimal('0.01'))),
            })

    mess = Decimal(structure.mess_advance_per_semester or 0).quantize(Decimal('0.01'))
    rows.append({
        'label': 'Mess Advance',
        'sem1': str(mess), 'sem2': str(mess),
        'total': str((mess * 2).quantize(Decimal('0.01'))),
    })

    one_time_sem1 = Decimal('0')
    if odd_semester == 1:
        one_time_sem1 = sum(
            (structure._amount(head, column, odd_semester)
             for head in structure.one_time_heads or []),
            Decimal('0'),
        )
    rows.append({
        'label': ONE_TIME_LABEL,
        'sem1': str(one_time_sem1.quantize(Decimal('0.01'))),
        'sem2': '0.00',
        'total': str(one_time_sem1.quantize(Decimal('0.01'))),
    })
    return rows


def _column_total(rows, key):
    return sum((Decimal(row[key]) for row in rows), Decimal('0'))


def render_fee_structure_pdf(context, structure, odd_semester, academic_year_label,
                             rows, reference_number, issued_on):
    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        topMargin=2.5 * cm,
        rightMargin=1.5 * cm,
        bottomMargin=2.5 * cm,
        leftMargin=1.5 * cm,
        title='Fee Structure Certificate',
        author=settings.BONAFIDE_INSTITUTE_NAME,
    )
    header_style = ParagraphStyle(
        'Header', fontName='Helvetica-Bold', fontSize=12, leading=16,
    )
    header_right_style = ParagraphStyle(
        'HeaderRight', parent=header_style, alignment=2,
    )
    label_style = ParagraphStyle(
        'Label', fontName='Helvetica-Bold', fontSize=12, leading=18,
    )
    value_style = ParagraphStyle(
        'Value', fontName='Helvetica', fontSize=12, leading=18,
    )
    note_style = ParagraphStyle(
        'Note', fontName='Helvetica-Bold', fontSize=12, leading=16,
    )
    cell_style = ParagraphStyle(
        'Cell', fontName='Helvetica', fontSize=12, leading=15, alignment=TA_LEFT,
    )
    cell_center_style = ParagraphStyle(
        'CellCenter', parent=cell_style, alignment=TA_CENTER,
    )
    cell_bold_style = ParagraphStyle(
        'CellBold', parent=cell_style, fontName='Helvetica-Bold',
    )
    signature_style = ParagraphStyle(
        'Signature', fontName='Helvetica-Bold', fontSize=12,
        leading=16, alignment=TA_LEFT,
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
                f'Date: {issued_on.strftime("%d/%m/%Y")}',
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

    def label_cell(text):
        return Paragraph(text, label_style)

    def value_cell(text):
        return Paragraph(escape(str(text)), value_style)

    details = Table(
        [
            [label_cell('Name:'), value_cell(context['name']), '', ''],
            [label_cell("Father's Name:"),
             value_cell(f'Mr. {context["father_name"]}'), '', ''],
            [label_cell('Roll No:'), value_cell(context['roll_number']),
             label_cell('Branch:'), value_cell(context['discipline'])],
            [label_cell('Semester:'), value_cell(context['semester_ordinal']),
             label_cell('Programme:'), value_cell(context['programme_short'])],
            [label_cell('Financial Year:'), value_cell(academic_year_label), '', ''],
        ],
        colWidths=[3.3 * cm, 2.3 * cm, 3.3 * cm, 9.1 * cm],
    )
    details.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('SPAN', (1, 0), (3, 0)),
        ('SPAN', (1, 1), (3, 1)),
        ('SPAN', (1, 4), (3, 4)),
    ]))

    table_rows = [[
        Paragraph(str(index), cell_center_style),
        Paragraph(escape(row['label']), cell_style),
        Paragraph(escape(indian_currency(Decimal(row['sem1']))), cell_style),
        Paragraph(escape(indian_currency(Decimal(row['sem2']))), cell_style),
        Paragraph(escape(indian_currency(Decimal(row['total']))), cell_style),
    ] for index, row in enumerate(rows, start=1)]
    table_rows.append([
        Paragraph('Total (Rs)', cell_bold_style), '',
        Paragraph(escape(indian_currency(_column_total(rows, 'sem1'))), cell_bold_style),
        Paragraph(escape(indian_currency(_column_total(rows, 'sem2'))), cell_bold_style),
        Paragraph(escape(indian_currency(_column_total(rows, 'total'))), cell_bold_style),
    ])

    structure_table = Table(
        [[
            Paragraph('S.No.', cell_bold_style),
            Paragraph('Fee Head(s)', cell_bold_style),
            Paragraph('Semester-I', cell_bold_style),
            Paragraph('Semester-II', cell_bold_style),
            Paragraph('Total', cell_bold_style),
        ]] + table_rows,
        colWidths=[1.8 * cm, 6.2 * cm, 2.7 * cm, 3.3 * cm, 3 * cm], hAlign='LEFT',
    )
    structure_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('SPAN', (0, len(rows) + 1), (1, len(rows) + 1)),
    ]))

    story = [
        header,
        Spacer(1, 1 * cm),
        details,
        Spacer(1, 0.6 * cm),
        Paragraph('<u>Details Break-up:</u>', note_style),
        Spacer(1, 0.3 * cm),
        structure_table,
        Spacer(1, 1.6 * cm),
        Paragraph(f'({escape(settings.BONAFIDE_SIGNATORY_NAME)})', signature_style),
    ]

    document.build(story)
    output.seek(0)
    return output


def _certificate_filename(certificate):
    roll_number = certificate.student.id.user.username
    safe_roll_number = re.sub(r'[^A-Za-z0-9_-]', '_', roll_number)
    return f'{safe_roll_number}_Fee_Structure_Certificate_{certificate.pk:03d}.pdf'


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
def fee_structure_certificate_student(request):
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
    errors = list(context['validation_errors'])

    rows = []
    academic_year_label = ''
    if structure is None:
        batch_label = context.get('programme') or 'unrecognised'
        errors.append(
            f'No fee structure is recorded for {batch_label} programmes. '
            'Add one before issuing this certificate.')
    elif context['semester']:
        odd_semester, _ = session_semesters(context['semester'])
        rows = build_structure_rows(student, structure, odd_semester)
        _, academic_year_label = financial_year_for(student, odd_semester)

    issued_on = timezone.now().date()
    prefix = settings.BONAFIDE_REFERENCE_PREFIX.rstrip('/')
    next_serial = (BonafideCertificate.objects.aggregate(
        max_id=Max('pk'))['max_id'] or 0) + 1

    return Response({
        'student': {**context, 'is_ready': not errors, 'validation_errors': errors},
        'structure': {
            'rows': rows,
            'academic_year_label': academic_year_label,
            'total_display': (
                indian_currency(_column_total(rows, 'total')) if rows else ''
            ),
        },
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
def generate_fee_structure_pdf(request):
    student_id = request.data.get('student_id')
    if not student_id:
        return Response({'error': 'student_id is required.'},
                        status=status.HTTP_400_BAD_REQUEST)

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

    odd_semester, _ = session_semesters(context['semester'])
    rows = build_structure_rows(student, structure, odd_semester)
    _, academic_year_label = financial_year_for(student, odd_semester)

    issued_on = timezone.now().date()
    prefix = settings.BONAFIDE_REFERENCE_PREFIX.rstrip('/')
    with transaction.atomic():
        certificate = BonafideCertificate.objects.create(
            student=student,
            certificate_type=CERTIFICATE_TYPE,
            purpose=f'Fee Structure {academic_year_label}',
            fee_rows=rows,
            issued_by=request.user,
        )
        reference_number = (
            f'{prefix}/{issued_on.year}/{issued_on.month:02d}/'
            f'{context["roll_number"]}/{certificate.pk:03d}')
        certificate.reference_number = reference_number
        document = render_fee_structure_pdf(
            context, structure, odd_semester, academic_year_label, rows,
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
def fee_structure_certificates(request):
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
def fee_structure_certificate_pdf(request, certificate_id):
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
