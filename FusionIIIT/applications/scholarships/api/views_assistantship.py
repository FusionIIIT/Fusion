"""Assistantship sheet for a discipline's office staff.

The staff sees only their own discipline's PG and PhD students. Rows are
seeded from the admission record and stored per month; a month left pending
is carried into the next, so the payable amount is this month's plus the dues.
"""
import calendar
import json
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from applications.globals.access import _user_from_request
from applications.globals.models import Faculty, HoldsDesignation
from applications.scholarships.models_assistantship import (
    DEFAULT_AMOUNT, AssistantshipExclusion, AssistantshipRecord,
    AssistantshipSignatory, staff_scope,
)
from applications.programme_curriculum.models_student_management import (
    PhdStudentBatchUpload, StudentBatchUpload,
)


def _roles(user):
    return list(
        HoldsDesignation.objects.filter(user=user)
        .values_list('designation__name', flat=True)
    )


def _scope_or_none(request):
    """Discipline for the staff role the user has switched to."""
    user = _user_from_request(request)
    if user is None:
        return None, None, None
    held = _roles(user)
    # Someone holding more than one staff role sees the one the sidebar
    # switcher has selected, so the switch actually changes the sheet.
    selected = getattr(getattr(user, 'extrainfo', None), 'last_selected_role', None)
    ordered = ([selected] if selected in held else []) + held
    code, disciplines = staff_scope(ordered)
    if not code:
        return user, None, None
    return user, code, disciplines


def _previous_month(year, month):
    return (year - 1, 12) if month == 1 else (year, month - 1)


def _students(disciplines):
    """PG and PhD students of the discipline, the ones an assistantship pays."""
    removed = set(AssistantshipExclusion.objects
                  .filter(discipline=disciplines[0])
                  .values_list('roll_number', flat=True))
    pg = StudentBatchUpload.objects.filter(
        programme_type__iexact='pg', branch__in=disciplines).exclude(
        roll_number__in=removed)
    phd = PhdStudentBatchUpload.objects.filter(
        discipline__in=disciplines).exclude(roll_number__in=removed)
    rows = []
    for rec in list(pg) + list(phd):
        rows.append({
            'roll_no': rec.roll_number or '',
            'student_name': rec.name or '',
            'joining_date': rec.joining_date.isoformat() if rec.joining_date else '',
            'account_no': rec.bank_account_no or '',
            'ifsc_code': rec.ifsc_code or '',
            'bank_name': rec.bank_name or '',
        })
    rows.sort(key=lambda r: r['roll_no'])
    return rows


def _student_record(roll_number):
    return (StudentBatchUpload.objects.filter(roll_number=roll_number).first()
            or PhdStudentBatchUpload.objects.filter(roll_number=roll_number).first())


@csrf_exempt
@require_http_methods(["GET"])
def assistantship_sheet(request):
    user, code, disciplines = _scope_or_none(request)
    if user is None:
        return JsonResponse({"success": False, "message": "Authentication required"},
                            status=401)
    if not code:
        return JsonResponse(
            {"success": False, "message": "Only department staff can open this"},
            status=403)

    try:
        year = int(request.GET.get('year'))
        month = int(request.GET.get('month'))
    except (TypeError, ValueError):
        return JsonResponse({"success": False, "message": "Pick a month and year"},
                            status=400)
    if not 1 <= month <= 12:
        return JsonResponse({"success": False, "message": "Month must be 1 to 12"},
                            status=400)

    days_in_month = calendar.monthrange(year, month)[1]
    prev_year, prev_month = _previous_month(year, month)

    saved = {r.roll_number: r for r in AssistantshipRecord.objects.filter(
        discipline=disciplines[0], year=year, month=month)}
    previous = {r.roll_number: r for r in AssistantshipRecord.objects.filter(
        discipline=disciplines[0], year=prev_year, month=prev_month)}

    rows = []
    for student in _students(disciplines):
        roll = student['roll_no']
        row = saved.get(roll)
        prev = previous.get(roll)
        amount = row.amount if row and row.amount is not None else DEFAULT_AMOUNT
        # An unpaid month rolls forward, so this month settles both.
        arrears = (prev.amount or Decimal('0')) if prev and prev.status == 'pending' \
            else Decimal('0')
        rows.append(dict(
            student,
            days=row.days if row and row.days is not None else days_in_month,
            amount=str(amount),
            remark=(row.remark if row else '') or '',
            status=row.status if row else 'pending',
            last_month_status=prev.status if prev else '',
            arrears=str(arrears),
            payable=str(amount + arrears),
        ))

    signatory = AssistantshipSignatory.objects.filter(
        discipline=disciplines[0]).first()
    faculty = sorted(
        {'{} {}'.format(f.id.user.first_name, f.id.user.last_name).strip()
         for f in Faculty.objects.select_related('id__user')
         if f.id and f.id.user}
    )

    return JsonResponse({
        'success': True,
        'discipline': disciplines[0],
        'discipline_code': code,
        'year': year,
        'month': month,
        'month_name': calendar.month_name[month],
        'days_in_month': days_in_month,
        'default_amount': str(DEFAULT_AMOUNT),
        'recommended_by': signatory.recommended_by if signatory else '',
        'faculty': faculty,
        'rows': rows,
        'total': str(sum(Decimal(r['payable']) for r in rows)) if rows else '0',
    })


@csrf_exempt
@require_http_methods(["POST", "PUT"])
def assistantship_save(request):
    user, code, disciplines = _scope_or_none(request)
    if user is None:
        return JsonResponse({"success": False, "message": "Authentication required"},
                            status=401)
    if not code:
        return JsonResponse(
            {"success": False, "message": "Only department staff can save this"},
            status=403)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"success": False, "message": "Invalid request data"},
                            status=400)

    try:
        year = int(data.get('year'))
        month = int(data.get('month'))
    except (TypeError, ValueError):
        return JsonResponse({"success": False, "message": "Pick a month and year"},
                            status=400)

    allowed = {r['roll_no'] for r in _students(disciplines)}
    days_in_month = calendar.monthrange(year, month)[1]
    errors = {}
    cleaned = []

    for row in data.get('rows') or []:
        roll = (row.get('roll_no') or '').strip()
        if roll not in allowed:
            errors[roll or '(blank)'] = 'Not a student of this discipline'
            continue
        try:
            days = int(row.get('days'))
        except (TypeError, ValueError):
            errors[roll] = 'Days must be a whole number'
            continue
        if not 0 <= days <= days_in_month:
            errors[roll] = 'Days must be between 0 and {}'.format(days_in_month)
            continue
        try:
            amount = Decimal(str(row.get('amount')))
        except (InvalidOperation, TypeError):
            errors[roll] = 'Amount must be a number'
            continue
        if amount < 0:
            errors[roll] = 'Amount cannot be negative'
            continue
        status = (row.get('status') or 'pending').strip().lower()
        if status not in ('pending', 'cleared'):
            errors[roll] = 'Status must be pending or cleared'
            continue
        cleaned.append((roll, days, amount, (row.get('remark') or '').strip(),
                        status, (row.get('joining_date') or '').strip()))

    if errors:
        return JsonResponse(
            {"success": False, "errors": errors,
             "message": "Please fix the highlighted rows"}, status=400)

    with transaction.atomic():
        for roll, days, amount, remark, status, joining in cleaned:
            AssistantshipRecord.objects.update_or_create(
                roll_number=roll, year=year, month=month,
                defaults={'discipline': disciplines[0], 'days': days,
                          'amount': amount, 'remark': remark, 'status': status},
            )
            # The joining date lives on the student, not on the month.
            student = _student_record(roll)
            if student is not None:
                value = joining or None
                if str(student.joining_date or '') != (value or ''):
                    student.joining_date = value
                    student.save(update_fields=['joining_date'])

    return JsonResponse({"success": True, "saved": len(cleaned)})


@csrf_exempt
@require_http_methods(["POST", "PUT"])
def assistantship_signatory(request):
    user, code, disciplines = _scope_or_none(request)
    if user is None:
        return JsonResponse({"success": False, "message": "Authentication required"},
                            status=401)
    if not code:
        return JsonResponse(
            {"success": False, "message": "Only department staff can save this"},
            status=403)
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"success": False, "message": "Invalid request data"},
                            status=400)

    name = (data.get('recommended_by') or '').strip()
    if not name:
        return JsonResponse({"success": False, "message": "Pick a faculty member"},
                            status=400)

    AssistantshipSignatory.objects.update_or_create(
        discipline=disciplines[0], defaults={'recommended_by': name})
    return JsonResponse({"success": True, "recommended_by": name})


@csrf_exempt
@require_http_methods(["POST", "DELETE"])
def assistantship_remove(request):
    """Take a student off this discipline's sheet, leaving their record be."""
    user, code, disciplines = _scope_or_none(request)
    if user is None:
        return JsonResponse({"success": False, "message": "Authentication required"},
                            status=401)
    if not code:
        return JsonResponse(
            {"success": False, "message": "Only department staff can do this"},
            status=403)
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"success": False, "message": "Invalid request data"},
                            status=400)

    roll = (data.get('roll_no') or '').strip()
    if roll not in {r['roll_no'] for r in _students(disciplines)}:
        return JsonResponse(
            {"success": False,
             "message": "That student is not on this discipline's sheet"},
            status=400)

    AssistantshipExclusion.objects.get_or_create(
        roll_number=roll, defaults={'discipline': disciplines[0]})
    return JsonResponse({"success": True, "removed": roll})
