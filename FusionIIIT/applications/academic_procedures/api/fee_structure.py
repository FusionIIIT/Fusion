"""Maintaining the published fee structure.

Everything the circular contains is data here — the heads, their amounts, the
column headings, the number of semesters and the footnotes — so a fee revision
is a screen edit rather than a deploy.
"""
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from applications.academic_procedures.models import FeeStructure
from applications.globals.decorators import role_required

SECTIONS = ('one_time_heads', 'semester_heads', 'tuition_hostel_heads')

#: What the screen shows in the Name column; the long form is the tab label.
SHORT_NAMES = {'UG': 'UG', 'PG': 'PG', 'PHD': 'Ph.D.'}

#: Only the starting point for a new session — every one of these is editable,
#: and the office may add or remove rows.
DEFAULT_HEADS = {
    'one_time_heads': [
        'Admission', 'Grade Card', 'Provisional Certificate',
        'Alumni Association Subscription', 'I Card', 'Career Development Fund',
        "Student's Welfare", 'Caution Money (Refundable)',
    ],
    'semester_heads': [
        'Gymkhana Fee', 'Examination Fee', 'Registration Fee',
        'Medical Insurance + PHC', 'Internet and computer Charge',
    ],
    'tuition_hostel_heads': ['Tuition Fee', 'Hostel Fees'],
}

DEFAULT_SEMESTERS = {'UG': 8, 'PG': 4, 'PHD': 10}


def _blank_heads(section):
    return [{'head': head, 'general': '', 'concession': ''}
            for head in DEFAULT_HEADS[section]]


def _clean_amount(value):
    """A head's amount: a number, a per-semester list, or NIL as printed."""
    if isinstance(value, list):
        return [_clean_amount(item) for item in value]
    text = str(value if value is not None else '').strip()
    if text.upper() in ('', 'NIL', '-'):
        return text.upper() if text else ''
    try:
        return str(Decimal(text.replace(',', '')))
    except InvalidOperation as exc:
        raise ValueError(f'{value!r} is not an amount.') from exc


def _clean_heads(rows, label):
    cleaned = []
    for row in rows or []:
        head = (row.get('head') or '').strip()
        if not head:
            continue                      # a blank row is one they abandoned
        cleaned.append({
            'head': head[:120],
            'general': _clean_amount(row.get('general')),
            'concession': _clean_amount(row.get('concession')),
        })
    if not cleaned:
        raise ValueError(f'{label} needs at least one head.')
    return cleaned


def _serialise(structure):
    sections = {section: getattr(structure, section) for section in SECTIONS}
    totals = {
        section: {
            column: str(structure.section_total(section, column))
            for column in ('general', 'concession')
        }
        for section in SECTIONS
    }
    grand_total = [
        {
            'semester': semester,
            # A+B+C as the circular prints it; mess is section D on its own.
            'general': str(structure.semester_amount('general', semester, False)),
            'concession': str(
                structure.semester_amount('concession', semester, False)),
        }
        for semester in range(1, structure.semester_count + 1)
    ]
    return {
        'id': structure.pk,
        'programme_category': structure.programme_category,
        'name': SHORT_NAMES.get(structure.programme_category,
                                structure.programme_category),
        'long_name': structure.get_programme_category_display(),
        'start_year': structure.start_year,
        'academic_year': structure.academic_year,
        'semester_count': structure.semester_count,
        'general_label': structure.general_label,
        'concession_label': structure.concession_label,
        'mess_advance_per_semester': str(structure.mess_advance_per_semester),
        'notes': structure.notes,
        'is_active': structure.is_active,
        **sections,
        'section_totals': totals,
        # Computed here so the printed certificate and the screen cannot differ.
        'grand_total': grand_total,
        'updated_at': structure.updated_at.strftime('%d.%m.%Y'),
    }


def _apply(structure, data):
    category = (data.get('programme_category') or '').strip().upper()
    if category not in dict(FeeStructure.CATEGORY_CHOICES):
        raise ValueError('Select UG, PG or PhD.')

    try:
        start_year = int(data.get('start_year'))
    except (TypeError, ValueError) as exc:
        raise ValueError('Enter the starting year of the session.') from exc
    if not 1900 < start_year < 2200:
        raise ValueError('Enter the starting year of the session.')

    try:
        semester_count = int(data.get('semester_count')
                             or DEFAULT_SEMESTERS.get(category, 8))
    except (TypeError, ValueError) as exc:
        raise ValueError('Enter how many semesters the programme runs.') from exc
    if not 1 <= semester_count <= 20:
        raise ValueError('A programme runs between 1 and 20 semesters.')

    structure.programme_category = category
    structure.start_year = start_year
    structure.semester_count = semester_count
    structure.general_label = (data.get('general_label')
                               or 'Gen/OBC/EWS').strip()[:40]
    structure.concession_label = (data.get('concession_label')
                                  or 'PWD/SC/ST').strip()[:40]
    structure.mess_advance_per_semester = _clean_amount(
        data.get('mess_advance_per_semester') or 0) or 0
    structure.notes = [str(note).strip() for note in (data.get('notes') or [])
                       if str(note).strip()]
    structure.is_active = bool(data.get('is_active', True))

    labels = {'one_time_heads': 'One-time payment',
              'semester_heads': 'Semester fees (academic)',
              'tuition_hostel_heads': 'Semester fees (tuition and hostel)'}
    for section in SECTIONS:
        setattr(structure, section, _clean_heads(data.get(section), labels[section]))
    return structure


def _duplicate(category, start_year, exclude_pk=None):
    rows = FeeStructure.objects.filter(programme_category=category,
                                       start_year=start_year)
    if exclude_pk:
        rows = rows.exclude(pk=exclude_pk)
    return rows.exists()


@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@role_required(['acadadmin'])
def fee_structures(request):
    if request.method == 'GET':
        return Response({'results': [_serialise(row) for row
                                     in FeeStructure.objects.all()]})

    structure = FeeStructure()
    try:
        _apply(structure, request.data)
    except ValueError as exc:
        return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    if _duplicate(structure.programme_category, structure.start_year):
        return Response(
            {'error': f'{structure.programme_category} already has a structure '
                      f'for {structure.academic_year}.'},
            status=status.HTTP_400_BAD_REQUEST)
    structure.save()
    return Response(_serialise(structure), status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@role_required(['acadadmin'])
def fee_structure_detail(request, structure_id):
    structure = get_object_or_404(FeeStructure, pk=structure_id)

    if request.method == 'GET':
        return Response(_serialise(structure))

    if request.method == 'DELETE':
        structure.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    try:
        _apply(structure, request.data)
    except ValueError as exc:
        return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    if _duplicate(structure.programme_category, structure.start_year,
                  exclude_pk=structure.pk):
        return Response(
            {'error': f'{structure.programme_category} already has a structure '
                      f'for {structure.academic_year}.'},
            status=status.HTTP_400_BAD_REQUEST)
    structure.save()
    return Response(_serialise(structure))


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@role_required(['acadadmin'])
def replicate_fee_structure(request, structure_id):
    """Copy a session's structure into a new one, so only changes are typed."""
    source = get_object_or_404(FeeStructure, pk=structure_id)
    try:
        start_year = int(request.data.get('start_year'))
    except (TypeError, ValueError):
        return Response({'error': 'Enter the starting year of the new session.'},
                        status=status.HTTP_400_BAD_REQUEST)

    if _duplicate(source.programme_category, start_year):
        return Response(
            {'error': f'{source.programme_category} already has a structure for '
                      f'{start_year}-{str(start_year + 1)[-2:]}.'},
            status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        copy = FeeStructure.objects.get(pk=source.pk)
        copy.pk = None
        copy.start_year = start_year
        copy.save()
    return Response(_serialise(copy), status=status.HTTP_201_CREATED)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@role_required(['acadadmin'])
def fee_structure_template(request):
    """A blank structure with the usual heads already listed."""
    category = (request.query_params.get('programme_category') or 'UG').upper()
    return Response({
        'programme_category': category,
        'semester_count': DEFAULT_SEMESTERS.get(category, 8),
        'general_label': 'Gen/OBC/EWS',
        'concession_label': 'PWD/SC/ST',
        'mess_advance_per_semester': '',
        'notes': [
            'The above fee structure includes Mess Advance Fee of Rs. ____/- '
            '(per semester).',
            '*Note: The above fee structure etc. may be changed any time by '
            'the Institute',
        ],
        **{section: _blank_heads(section) for section in SECTIONS},
    })
