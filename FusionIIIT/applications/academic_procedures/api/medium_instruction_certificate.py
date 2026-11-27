import re
from io import BytesIO
from xml.sax.saxutils import escape

from django.conf import settings
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from applications.academic_information.models import Student
from applications.academic_procedures.models import BonafideCertificate
from applications.academic_procedures.api.bonafide_certificate import (
    build_certificate_context,
    register_certificate_fonts,
)
from applications.globals.decorators import role_required


def _student_queryset():
    return Student.objects.select_related(
        'id__user',
        'id__department',
        'batch_id__discipline',
        'batch_id__curriculum__programme',
    )


def _render_medium_instruction_pdf(context, reference_number, issued_on):
    register_certificate_fonts()
    output = BytesIO()

    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        topMargin=3.5 * cm,
        rightMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2 * cm,
        title='Medium of Instruction Certificate',
        author=settings.BONAFIDE_INSTITUTE_NAME,
    )

    header_style = ParagraphStyle(
        'MediumHeader', fontName='Caladea-Bold', fontSize=11,
        leading=15, alignment=TA_RIGHT,
    )
    heading_style = ParagraphStyle(
        'MediumHeading', fontName='Caladea-Bold', fontSize=14,
        leading=20, alignment=TA_CENTER,
    )
    body_style = ParagraphStyle(
        'MediumBody', fontName='Caladea', fontSize=12,
        leading=20, alignment=TA_JUSTIFY,
    )
    signature_style = ParagraphStyle(
        'MediumSignature', fontName='Caladea-Bold', fontSize=11,
        leading=16, alignment=TA_RIGHT,
    )

    heading = 'TO WHOM SO EVER IT MAY CONCERN'
    body = (
        f'This is to certify that {escape(str(context["name"]))} '
        f'(Roll No. {escape(str(context["roll_number"]))}), '
        f'{escape(str(context["relation"]))} '
        f'{escape(str(context["father_name"]))}, '
        f'was a student of the B.Tech. programme in '
        f'{escape(str(context["discipline"]))} discipline. '
        f'The institute provides education to students '
        f'with English as the medium of instruction.'
    )

    story = [
        Paragraph(f'Reference No.: {escape(str(reference_number))}', header_style),
        Paragraph(f'Date: {issued_on.strftime("%d.%m.%Y")}', header_style),
        Spacer(1, 2 * cm),
        Paragraph(heading, heading_style),
        Spacer(1, 1 * cm),
        Paragraph(body, body_style),
        Spacer(1, 3 * cm),
        Paragraph('Assistant Registrar', signature_style),
    ]

    document.build(story)
    return output.getvalue()


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@role_required(['acadadmin'])
def generate_medium_instruction_certificate(request):
    student_id = request.data.get('student_id')

    if not student_id:
        return Response(
            {'error': 'student_id is required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    student = get_object_or_404(_student_queryset(), pk=student_id)
    context = build_certificate_context(student)

    if not context['is_ready']:
        return Response(
            {
                'error': 'Student data is incomplete.',
                'details': context['validation_errors'],
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    issued_on = timezone.now().date()
    prefix = settings.BONAFIDE_REFERENCE_PREFIX.rstrip('/')

    with transaction.atomic():
        certificate = BonafideCertificate.objects.create(
            student=student,
            certificate_type='medium_instruction',
            purpose='Other',
            custom_purpose='Medium of Instruction Certificate',
            issued_by=request.user,
        )

        reference_number = (
            f'{prefix}/MOI/{issued_on.year}/{issued_on.month:02d}/'
            f'{context["roll_number"]}/{certificate.pk:03d}'
        )

        pdf_bytes = _render_medium_instruction_pdf(
            context, reference_number, issued_on
        )
        certificate.reference_number = reference_number
        certificate.pdf_content = pdf_bytes
        certificate.save(update_fields=['reference_number', 'pdf_content'])

    safe_roll_number = re.sub(
        r'[^A-Za-z0-9_-]', '_', str(context['roll_number'])
    )
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="{safe_roll_number}_Medium_Instruction.pdf"'
    )
    response['X-Certificate-Reference'] = reference_number
    return response
