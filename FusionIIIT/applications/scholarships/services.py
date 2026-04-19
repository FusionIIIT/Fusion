from decimal import Decimal, InvalidOperation
import logging
import math

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from .models import (
    Application, Mcm, Director_gold, Director_silver, Proficiency_dm,
    Release, ScholarshipApplication, McmApplication, SingleParentApplication, MeritListRecord
)
from .selectors import get_active_releases

logger = logging.getLogger(__name__)

STATUS = {
    "PENDING": "pending",
    "REVERTED": "reverted",
    "VERIFIED": "verified",
    "APPROVED": "approved",
    "REJECTED": "rejected",
}

def validate_application_window(student, award):
    active_releases = get_active_releases(student.batch, student.programme)
    if not active_releases.filter(award=award).exists():
        raise ValidationError("The application window for this award is closed or not applicable to your batch.")


def check_duplicate_application(student, award):
    if Application.objects.filter(student=student, award=award).exists():
        raise ValidationError("You have already submitted an application for this award.")


def check_scholarship_eligibility(student, scholarship_type):
    """
    Check if student is eligible for a scholarship.
    Returns: (is_eligible: bool, reasons: list)
    """
    reasons = []

    # Check backlogs
    try:
        from applications.academic_procedures.models import course_registration
        backlog_count = course_registration.objects.filter(
            student_id=student,
            registration_type='Backlog'
        ).count()
        max_allowed = getattr(scholarship_type, 'max_backlogs', 0)
        if backlog_count > max_allowed:
            reasons.append(f"Has {backlog_count} backlogs (max allowed: {max_allowed})")
    except Exception:
        pass

    # Check category eligibility
    try:
        if scholarship_type and scholarship_type.applicable_categories:
            valid_categories = [c.strip() for c in scholarship_type.applicable_categories.split(',') if c.strip()]
            if valid_categories and student.category not in valid_categories:
                reasons.append(f"Category {student.category} not eligible for this scholarship")
    except AttributeError:
        pass

    # Check programme eligibility via M2M
    try:
        if scholarship_type and hasattr(scholarship_type, 'applicable_programmes') and scholarship_type.applicable_programmes.exists():
            from applications.programme_curriculum.models import Programme
            student_programme = Programme.objects.filter(name__icontains=student.programme).first()
            if student_programme and student_programme not in scholarship_type.applicable_programmes.all():
                reasons.append("Programme not eligible for this scholarship")
    except Exception:
        pass

    # Check minimum CGPA
    try:
        if scholarship_type and getattr(scholarship_type, 'minimum_cgpa', None):
            student_cgpa = student.cpi
            if student_cgpa < scholarship_type.minimum_cgpa:
                reasons.append(f"CGPA {student_cgpa} below minimum {scholarship_type.minimum_cgpa}")
    except AttributeError:
        pass

    # Check dues clearance
    try:
        from applications.academic_procedures.models import Dues
        dues = Dues.objects.get(student_id=student)
        total_dues = (dues.mess_due or 0) + (dues.hostel_due or 0) + (dues.library_due or 0) + (dues.academic_due or 0)
        if total_dues > 0:
            reasons.append(f"Has pending dues: Rs.{total_dues}")
    except Exception:
        pass

    # Check fee payment status
    try:
        from applications.academic_procedures.models import FeePayments
        latest_payment = FeePayments.objects.filter(student_id=student).order_by('-semester_id').first()
        if latest_payment and latest_payment.fee_paid < latest_payment.actual_fee:
            reasons.append("Fee payment incomplete for latest semester")
    except Exception:
        pass

    return (len(reasons) == 0, reasons)


def get_category_students(category, batch=None, programme=None):
    from applications.academic_information.models import Student
    qs = Student.objects.filter(category=category)
    if batch:
        qs = qs.filter(batch=batch)
    if programme:
        qs = qs.filter(programme=programme)
    return qs


def get_students_without_backlogs(batch, programme=None):
    try:
        from applications.academic_information.models import Student
        from applications.academic_procedures.models import course_registration
        qs = Student.objects.filter(batch=batch)
        if programme:
            qs = qs.filter(programme=programme)
        return qs.annotate(
            backlog_count=Count('course_registration', filter=Q(course_registration__registration_type='Backlog'))
        ).filter(backlog_count=0)
    except Exception:
        from applications.academic_information.models import Student
        return Student.objects.filter(batch=batch)


def get_course_toppers(course_id, grade='A', limit=10):
    try:
        from applications.online_cms.models import Student_grades
        return Student_grades.objects.filter(course_id=course_id, grade=grade, verified=True)[:limit]
    except Exception:
        return []


def calculate_student_cgpa(student):
    try:
        return float(student.cpi) if student.cpi else None
    except (AttributeError, TypeError):
        return None


def generate_merit_list(batch, academic_year, semester, programme=None):
    try:
        from applications.academic_information.models import Student
        students = Student.objects.filter(batch=batch)
        if programme:
            students = students.filter(programme=programme)
        merit_data = []
        for student in students:
            cgpa = calculate_student_cgpa(student)
            if cgpa is not None:
                is_eligible, _ = check_scholarship_eligibility(student, None)
                merit_data.append({
                    'student_id': str(student.id) if student.id else '',
                    'cgpa': cgpa,
                    'rank': 0,
                    'eligible_for_scholarships': is_eligible,
                    'programme': student.programme,
                    'batch': student.batch,
                    'category': student.category,
                })
        merit_data.sort(key=lambda x: x['cgpa'], reverse=True)
        for i, entry in enumerate(merit_data, 1):
            entry['rank'] = i
        return merit_data
    except Exception:
        return []



def _normalize_branch(programme):
    value = (programme or '').strip().lower()

    if 'b.des' in value or 'design' in value:
        return 'B.Des'
    if 'cse' in value or 'computer science' in value:
        return 'B.Tech CSE'
    if 'ece' in value or 'electronics' in value:
        return 'B.Tech ECE'
    if 'ee' in value or 'electrical' in value:
        return 'B.Tech EE'
    if 'sm' in value or 'smart manufacturing' in value:
        return 'B.Tech SM'
    if 'me' in value or 'mechanical' in value:
        return 'B.Tech ME'

    return (programme or '').strip()

def _to_decimal(value, default=Decimal('0')):
    try:
        if value is None or value == '':
            return default
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return default

def _to_income(value):
    if value is None:
        return 10**12
    text = ''.join(ch for ch in str(value) if ch.isdigit())
    if not text:
        return 10**12
    try:
        return int(text)
    except ValueError:
        return 10**12

BATCH_BRANCH_STRENGTH = {
    "2023": {
        "B.Tech CSE": 275, "B.Tech ECE": 140, "B.Tech ME": 73, "B.Tech SM": 70, "B.Des": 66, "B.Tech EE": 0
    },
    "2024": {
        "B.Tech CSE": 277, "B.Tech ECE": 138, "B.Tech ME": 68, "B.Tech SM": 69, "B.Des": 66, "B.Tech EE": 0
    },
    "2025": {
        "B.Tech CSE": 275, "B.Tech ECE": 137, "B.Tech ME": 69, "B.Tech SM": 69, "B.Des": 66, "B.Tech EE": 0
    },
    "2026": {
        "B.Tech CSE": 275, "B.Tech ECE": 137, "B.Tech ME": 69, "B.Tech SM": 69, "B.Des": 66, "B.Tech EE": 0
    }
}

@transaction.atomic
def generate_mcm_merit_list(batch=None):
    """
    Simplified Merit List Generation with Tie-Handling:
    1. Filter: Approved MCM applications for selected batch.
    2. Group: By normalized Branch (CSE, ECE, EE, ME, SM, B.Des).
    3. Sort:
       - 2023-2025: CPI (desc) -> SPI (desc) -> Income (asc)
       - 2026: Rank (asc)
    4. Selection: Top 10% of TOTAL BRANCH STRENGTH (min 1).
    5. Tie-Break: If students have IDENTICAL merit values (CPI/SPI/Inc or Rank), include all.
    6. Storage: Store in merit_list table.
    """
    try:
        queryset = McmApplication.objects.filter(status=STATUS["APPROVED"])
        if batch:
            queryset = queryset.filter(batch=str(batch).strip())

        applications = list(queryset)

        if batch:
            MeritListRecord.objects.filter(batch=str(batch).strip()).delete()
        else:
            MeritListRecord.objects.all().delete()

        if not applications:
            return {
                'generated_count': 0,
                'message': 'No approved applications found to generate merit list.',
                'entries': []
            }

        grouped = {}
        for app in applications:
            app_batch = str(app.batch or '').strip()
            branch = _normalize_branch(app.programme)
            if not branch:
                continue
            grouped.setdefault((app_batch, branch), []).append(app)

        selected_records = []

        for (app_batch, branch), group_apps in grouped.items():
            processed_data = []
            is_2026 = app_batch == '2026'

            # Get Strength and Quota
            batch_data = BATCH_BRANCH_STRENGTH.get(app_batch, {})
            strength = batch_data.get(branch, 0)
            quota = max(1, math.floor(0.10 * strength))

            for app in group_apps:
                if is_2026:
                    try:
                        rank_str = str(app.jee_uceed_rank or '').strip()
                        if not rank_str: continue
                        rank_val = int(''.join(ch for ch in rank_str if ch.isdigit()))
                        processed_data.append({
                            'app': app,
                            'merit_val': rank_val,
                            'time': app.submitted_at or timezone.now()
                        })
                    except (ValueError, TypeError): continue
                else:
                    cpi_val = _to_decimal(app.current_cpi, None)
                    spi_val = _to_decimal(app.current_spi, None)
                    if cpi_val is None: continue
                    processed_data.append({
                        'app': app,
                        'cpi': cpi_val,
                        'spi': spi_val or Decimal('0'),
                        'income': _to_income(app.annual_income),
                        'time': app.submitted_at or timezone.now()
                    })

            if not processed_data:
                continue

            # Sort Group
            if is_2026:
                processed_data.sort(key=lambda x: (x['merit_val'], x['time'].timestamp()))
            else:
                processed_data.sort(key=lambda x: (
                    -float(x['cpi']),
                    -float(x['spi']),
                    x['income'],
                    x['time'].timestamp()
                ))

            # Select based on Quota (fixed 10% of strength)
            top_n = min(len(processed_data), quota)
            
            selected_entries = processed_data[:top_n]
            
            # Tie Handling: Check if subsequent students have EXACT same merit values as the last selected
            if len(processed_data) > top_n:
                cutoff = processed_data[top_n - 1]
                for extra in processed_data[top_n:]:
                    is_tie = False
                    if is_2026:
                        is_tie = (extra['merit_val'] == cutoff['merit_val'])
                    else:
                        is_tie = (
                            extra['cpi'] == cutoff['cpi'] and
                            extra['spi'] == cutoff['spi'] and
                            extra['income'] == cutoff['income']
                        )
                    
                    if is_tie:
                        selected_entries.append(extra)
                    else:
                        break

            for entry in selected_entries:
                app = entry['app']
                merit_score = Decimal(str(entry.get('merit_val'))) if is_2026 else entry.get('cpi')
                selected_records.append({
                    'batch': app_batch,
                    'branch': branch,
                    'full_name': (app.student_full_name or '').strip(),
                    'roll_no': str(app.roll_no or '').strip(),
                    'cpi': merit_score
                })

        MeritListRecord.objects.bulk_create([
            MeritListRecord(**rec) for rec in selected_records
        ])

        return {
            'generated_count': len(selected_records),
            'message': 'Merit list generated successfully',
            'entries': selected_records,
        }
    except Exception as e:
        logger.exception("MCM merit list failure")
        return {
            'generated_count': 0,
            'message': f"Error during generation: {str(e)}",
            'entries': []
        }



def auto_populate_application_data(student):
    data = {
        'student_id': str(student.id) if student.id else '',
        'batch': student.batch,
        'programme': student.programme,
        'category': student.category,
        'cgpa': calculate_student_cgpa(student),
    }
    try:
        extra_info = student.id
        data.update({
            'phone': str(extra_info.phone_no) if extra_info.phone_no else None,
            'address': extra_info.address,
            'department': extra_info.department.name if extra_info.department else None,
        })
    except AttributeError:
        data.update({'phone': None, 'address': None, 'department': None})
    return data


def get_eligible_students_for_scholarship(scholarship_type):
    try:
        from applications.academic_information.models import Student
        qs = Student.objects.all()
        if hasattr(scholarship_type, 'applicable_programmes') and scholarship_type.applicable_programmes.exists():
            programme_names = list(scholarship_type.applicable_programmes.values_list('name', flat=True))
            qs = qs.filter(programme__in=programme_names)
        if hasattr(scholarship_type, 'applicable_categories') and scholarship_type.applicable_categories:
            valid_cats = [c.strip() for c in scholarship_type.applicable_categories.split(',') if c.strip()]
            if valid_cats:
                qs = qs.filter(category__in=valid_cats)
        result = []
        for student in qs:
            is_eligible, reasons = check_scholarship_eligibility(student, scholarship_type)
            student_data = auto_populate_application_data(student)
            student_data['eligibility_status'] = 'ELIGIBLE' if is_eligible else 'NOT_ELIGIBLE'
            if not is_eligible:
                student_data['ineligibility_reasons'] = reasons
            result.append(student_data)
        return result
    except Exception:
        return []


# ========== EXTENDED SCHOLARSHIP APPLICATION SERVICES ==========

@transaction.atomic
def create_extended_scholarship_application(student, scholarship_type_id, academic_year, semester, remarks='', document=None):
    """Create a full-lifecycle scholarship application with eligibility pre-check."""
    try:
        from .models import ExtendedScholarshipType
        scholarship_type = ExtendedScholarshipType.objects.get(id=scholarship_type_id)
    except Exception:
        return None, ["Invalid scholarship type."]

    if not scholarship_type.is_active:
        return None, ["This scholarship is no longer active."]

    is_eligible, reasons = check_scholarship_eligibility(student, scholarship_type)
    if not is_eligible:
        return None, reasons

    if ScholarshipApplication.objects.filter(
        student=student, scholarship_type=scholarship_type,
        academic_year=academic_year, semester=semester
    ).exists():
        return None, ["You have already applied for this scholarship this semester."]

    application = ScholarshipApplication.objects.create(
        student=student,
        scholarship_type=scholarship_type,
        academic_year=academic_year,
        semester=semester,
        category_at_application=student.category,
        remarks=remarks,
        supporting_documents=document,
    )
    return application, []


@transaction.atomic
def process_application_status_change(application, new_status, reviewer_user, review_remarks='', amount_approved=None, transaction_reference=''):
    """Update the status of a ScholarshipApplication and log the reviewer."""
    valid_transitions = {
        'PENDING': ['UNDER_REVIEW', 'APPROVED', 'REJECTED'],
        'UNDER_REVIEW': ['APPROVED', 'REJECTED'],
        'APPROVED': ['DISBURSED'],
        'REJECTED': [],
        'DISBURSED': [],
    }
    allowed = valid_transitions.get(application.status, [])
    if new_status not in allowed:
        raise ValidationError(f"Cannot transition from '{application.status}' to '{new_status}'.")

    from applications.globals.models import ExtraInfo
    try:
        reviewer = ExtraInfo.objects.get(user=reviewer_user)
        application.reviewed_by = reviewer
    except ExtraInfo.DoesNotExist:
        pass

    application.status = new_status
    application.review_date = timezone.now()
    application.review_remarks = review_remarks
    if amount_approved is not None:
        application.amount_approved = amount_approved
    if transaction_reference:
        application.transaction_reference = transaction_reference
    if new_status == 'DISBURSED':
        application.disbursement_date = timezone.now()
    application.save()

    # Trigger notification
    try:
        from notification.views import scholarship_portal_notif
        action_map = {
            'APPROVED': 'Accept_Scholarship',
            'REJECTED': 'Reject_Scholarship',
            'DISBURSED': 'Disburse_Scholarship',
        }
        notif_type = action_map.get(new_status)
        if notif_type:
            scholarship_portal_notif(
                sender=reviewer_user,
                recipient=application.student.id.user,
                type=notif_type
            )
    except Exception:
        pass

    return application


# ========== LEGACY SUBMISSION SERVICES ==========

@transaction.atomic
def submit_mcm_application(*, student, award, mcm_data, income_certificate):
    validate_application_window(student, award)
    check_duplicate_application(student, award)

    total_income = (int(mcm_data.get('income_father', 0)) +
                    int(mcm_data.get('income_mother', 0)) +
                    int(mcm_data.get('income_other', 0)))

    application = Application.objects.create(student=student, award=award)
    Mcm.objects.create(
        application=application, student=student,
        brother_name=mcm_data.get('brother_name'),
        brother_occupation=mcm_data.get('brother_occupation'),
        sister_name=mcm_data.get('sister_name'),
        sister_occupation=mcm_data.get('sister_occupation'),
        income_father=mcm_data.get('income_father', 0),
        income_mother=mcm_data.get('income_mother', 0),
        income_other=mcm_data.get('income_other', 0),
        annual_income=total_income,
        father_occ=mcm_data.get('father_occ'),
        mother_occ=mcm_data.get('mother_occ'),
        income_certificate=income_certificate
    )
    return application


@transaction.atomic
def submit_medal_application(*, student, award, model_class, data, document):
    validate_application_window(student, award)
    check_duplicate_application(student, award)

    application = Application.objects.create(student=student, award=award)
    base_data = {
        'application': application, 'student': student,
        'correspondence_address': data.get('correspondence_address'),
        'financial_assistance': data.get('financial_assistance'),
        'grand_total': data.get('grand_total', 0.0),
        'nearest_policestation': data.get('nearest_policestation'),
        'nearest_railwaystation': data.get('nearest_railwaystation'),
        'relevant_document': document
    }
    if model_class == Director_gold:
        base_data['academic_achievements'] = data.get('academic_achievements', '')
    elif model_class.__name__ == 'Proficiency_dm':
        base_data['title_of_project'] = data.get('title_of_project', '')
    model_class.objects.create(**base_data)
    return application


def update_application_status(*, application, status, remarks, user):
    if status not in ['APPROVED', 'REJECTED']:
        raise ValidationError("Invalid status. Must be APPROVED or REJECTED.")
    application.status = status
    application.remarks = remarks
    application.save()
    try:
        from notification.views import scholarship_portal_notif
        action_str = f"{status.capitalize()}_{application.award.award_type}"
        scholarship_portal_notif(user, application.student.id.user, action_str)
    except Exception:
        pass
    return application






