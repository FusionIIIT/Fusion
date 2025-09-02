import json
import pandas as pd
import openpyxl
import random
import string
from io import BytesIO
from datetime import datetime, date
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction, connection
from django.db.models import Q, Count
from django.conf import settings
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from applications.academic_information.models import Student as AcademicStudent
from applications.globals.models import ExtraInfo, Designation, HoldsDesignation
from django.contrib.auth.models import User
from applications.programme_curriculum.models import (
    Programme, Curriculum, Batch, Discipline
)

from applications.programme_curriculum.views_password_email import send_password_email_smtp
from applications.programme_curriculum.models_password_email import PasswordEmailLog

try:
    from applications.programme_curriculum.models_student_management import (
        StudentBatchUpload, BatchConfiguration, StudentStatusLog
    )
except ImportError:
    from django.db import models
    from django.contrib.auth.models import User
    pass

def get_batch_year_from_academic_year(academic_year):
    if isinstance(academic_year, str):
        if '-' in academic_year:
            return int(academic_year.split('-')[0])
        else:
            return int(academic_year)
    return int(academic_year)

def get_academic_year_from_batch_year(batch_year):
    batch_year = int(batch_year)
    next_year = batch_year + 1
    return f"{batch_year}-{str(next_year)[-2:]}"

def calculate_batch_filled_seats(batch):
    """
    Centralized function to calculate filled seats for a batch using priority-based algorithm.
    """
    try:
        from applications.academic_information.models import Student
        direct_count = Student.objects.filter(batch_id=batch).count()
        if direct_count > 0:
            return direct_count
        else:
            discipline_name = batch.discipline.name if batch.discipline else ''
            discipline_acronym = batch.discipline.acronym if batch.discipline else ''
            discipline_count = Student.objects.filter(
                batch=batch.year,
                id__department__name__in=[discipline_acronym, discipline_name.split()[0] if discipline_name else '']
            ).count() if discipline_name else 0
            if discipline_count > 0:
                return discipline_count
            else:
                if batch.name and batch.year:
                    programme_count = Student.objects.filter(
                        programme__icontains=batch.name.split()[0] if batch.name else '',
                        batch=batch.year,
                        id__department__name__in=[discipline_acronym] if discipline_acronym else []
                    ).count()
                    return programme_count
                else:
                    return 0
                    
    except Exception as e:
        return 0

def normalize_year_input(year_input):
    try:
        if isinstance(year_input, str):
            if '-' in year_input:
                parts = year_input.split('-')
                if len(parts) != 2:
                    raise ValueError(f"Invalid academic year format: {year_input}")
                batch_year = int(parts[0])
                second_year = int(parts[1])
                if second_year != (batch_year + 1) % 100:
                    raise ValueError(f"Invalid academic year format: {year_input}")
                academic_year = year_input
            else:
                batch_year = int(year_input)
                academic_year = get_academic_year_from_batch_year(batch_year)
        else:
            batch_year = int(year_input)
            academic_year = get_academic_year_from_batch_year(batch_year)
        
        return batch_year, academic_year
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid year format: {year_input}. Expected formats: 2025, '2025', or '2025-26'")

def get_current_academic_year():
    current_year = datetime.now().year
    if datetime.now().month >= 7:
        batch_year = current_year
    else:
        batch_year = current_year - 1
    
    academic_year = get_academic_year_from_batch_year(batch_year)
    return batch_year, academic_year

def calculate_current_semester(academic_year, current_date=None):
    if current_date is None:
        current_date = timezone.now().date()
    
    current_year = current_date.year
    current_month = current_date.month
    
    years_completed = 0
    
    if current_month >= 8:
        years_completed = current_year - academic_year
        semester_in_year = 1
    else:
        years_completed = current_year - academic_year - 1
        if current_month <= 5:
            semester_in_year = 2
        else:
            semester_in_year = 2
    
    total_semester = (years_completed * 2) + semester_in_year
    total_semester = max(1, min(total_semester, 8))
    
    return total_semester

@csrf_exempt
@require_http_methods(["GET"])
def admin_batches_overview(request):
    request.GET = request.GET.copy()
    request.GET['format'] = 'nested'
    return admin_batches_unified(request)

def get_display_branch_name(discipline):
    branch_mappings = {
        'Computer Science and Engineering': 'CSE',
        'Electronics and Communication Engineering': 'ECE',
        'Mechanical Engineering': 'ME',
        'Smart Manufacturing': 'SM',
        'Design': 'DES'
    }
    return branch_mappings.get(discipline, discipline)

@csrf_exempt
@require_http_methods(["POST"])
def process_excel_upload(request):
    try:
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'message': 'No file uploaded'
            }, status=400)
        
        file = request.FILES['file']
        programme_type = request.POST.get('programme_type', 'ug')
        selected_year = request.POST.get('academic_year')
        if selected_year:
            try:
                # Normalize ANY year input to get both formats
                batch_year, academic_year = normalize_year_input(selected_year)
            except ValueError as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Invalid year format: {str(e)}'
                }, status=400)
        else:
            batch_year, academic_year = get_current_academic_year()
  
        from applications.programme_curriculum.models import Curriculum, Batch
        
        available_curriculums = Curriculum.objects.filter(working_curriculum=True)
        if not available_curriculums.exists():
            return JsonResponse({
                'success': False,
                'message': f'❌ CURRICULUM REQUIRED: No working curriculums found. Please create a curriculum first before uploading student data.',
                'validation_error': 'missing_curriculum'
            }, status=400)
        
        existing_batches = Batch.objects.filter(year=batch_year, running_batch=True)
        if not existing_batches.exists():
            return JsonResponse({
                'success': False,
                'message': f'No active batches found for academic year {academic_year} (batch year {batch_year}). Please create batches with assigned curriculums first before uploading student data.',
                'validation_error': 'missing_batch',
                'academic_year': academic_year,
                'batch_year': batch_year
            }, status=400)
        
        batches_without_curriculum = existing_batches.filter(curriculum__isnull=True)
        if batches_without_curriculum.exists():
            batch_names = [f"{batch.name} {batch.discipline.acronym}" for batch in batches_without_curriculum]
            return JsonResponse({
                'success': False,
                'message': f'The following batches for {academic_year} exist but have no curriculum assigned: {", ".join(batch_names)}. Please assign curriculums to all batches first.',
                'validation_error': 'batch_missing_curriculum',
                'batches_without_curriculum': batch_names,
                'academic_year': academic_year
            }, status=400)
        
        if not file.name.endswith(('.xlsx', '.xls')):
            return JsonResponse({
                'success': False,
                'message': 'Invalid file format. Please upload an Excel file (.xlsx or .xls)'
            }, status=400)
        
        try:
            if file.name.endswith('.xlsx'):
                df = pd.read_excel(file, engine='openpyxl')
            else:
                df = pd.read_excel(file, engine='xlrd')
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error reading Excel file: {str(e)}'
            }, status=400)
        
        valid_students = []
        invalid_students = []
        
        column_mapping = {
            'sno': ['sno', 's.no', 'serial number', 's no'],
            'jee_app_no': ['jee main application number', 'jee app. no.', 'jee application number', 'jee main app number'],
            'roll_number': ['institute roll number', 'roll number', 'rollno', 'inst roll number'],
            'name': ['name', 'student name', 'full name'],
            'discipline': ['discipline', 'branch', 'department'],
            'gender': ['gender', 'sex'],
            'category': ['category', 'caste'],
            'pwd': ['pwd', 'disability', 'pwb'],
            'minority': ['minority', 'minority status'],
            'phone_number': ['mobileno', 'mobile', 'phone', 'mobile no'],
            'institute_email': ['institute email id', 'institute email', 'inst email id'],
            'personal_email': ['alternet email id', 'alternate email id', 'email', 'personal email'],
            'father_name': ['father\'s name', 'father name', 'fathers name'],
            'father_occupation': ['father\'s occupation', 'father occupation', 'fathers occupation'],
            'father_mobile': ['father mobile number', 'father mobile', 'fathers mobile'],
            'mother_name': ['mother\'s name', 'mother name', 'mothers name'],
            'mother_occupation': ['mother\'s occupation', 'mother occupation', 'mothers occupation'],
            'mother_mobile': ['mother mobile number', 'mother mobile', 'mothers mobile'],
            'date_of_birth': ['date of birth', 'dob', 'birth date'],
            'ai_rank': ['ai rank', 'jee rank', 'all india rank'],
            'category_rank': ['category rank', 'cat rank'],
            'allotted_category': ['allottedcat', 'allotted category', 'alloted category'],
            'allotted_gender': ['allotted gender', 'alloted gender'],
            'state': ['state'],
            'address': ['full address', 'address', 'complete address']
        }

        df.columns = df.columns.str.lower().str.strip()

        mapped_data = {}
        for field, possible_columns in column_mapping.items():
            for col in possible_columns:
                if col in df.columns:
                    mapped_data[field] = col
                    break
        
        for index, row in df.iterrows():
            try:
                student_data = {}

                for field, excel_col in mapped_data.items():
                    if excel_col in df.columns:
                        value = row[excel_col]
                        if pd.notna(value):
                            # Normalize minority values
                            if field == 'minority':
                                value_upper = str(value).strip().upper()
                                if value_upper in ['APPLICABLE']:
                                    student_data[field] = 'Applicable'
                                elif value_upper in ['NOT APPLICABLE', 'N/A', 'NA']:
                                    student_data[field] = 'Not Applicable'
                                else:
                                    student_data[field] = str(value).strip()
                            # Fix serial number to start from 1
                            elif field == 'sno':
                                student_data[field] = str(index + 1)  # Force serial number to be 1-based
                            else:
                                student_data[field] = str(value).strip()

                required_fields = ['name', 'discipline', 'roll_number', 'institute_email']
                missing_fields = [field for field in required_fields if not student_data.get(field)]

                errors = []
                
                if student_data.get('gender'):
                    gender = student_data['gender'].lower()
                    if gender not in ['male', 'female', 'other']:
                        errors.append(f'Invalid gender: {student_data["gender"]}')

                if student_data.get('pwd'):
                    pwd = student_data['pwd'].upper()
                    if pwd not in ['YES', 'NO']:
                        errors.append(f'Invalid PWD value: {student_data["pwd"]}')

                if student_data.get('minority'):
                    minority = student_data['minority'].upper()
                    if minority not in ['APPLICABLE', 'NOT APPLICABLE']:
                        errors.append(f'Invalid Minority value: {student_data["minority"]}')

                if student_data.get('institute_email'):
                    email = student_data['institute_email']
                    if '@' not in email:
                        errors.append(f'Invalid institute email format: {email}')
                
                # Validate phone numbers (basic check)
                for phone_field in ['phone_number', 'father_mobile', 'mother_mobile']:
                    if student_data.get(phone_field):
                        phone = student_data[phone_field].replace(' ', '').replace('-', '')
                        if not phone.isdigit() or len(phone) != 10:
                            errors.append(f'Invalid {phone_field}: {student_data[phone_field]}')
                
                if missing_fields or errors:
                    error_msg = []
                    if missing_fields:
                        error_msg.append(f'Missing required fields: {", ".join(missing_fields)}')
                    if errors:
                        error_msg.extend(errors)
                    
                    invalid_students.append({
                        'row': index + 2,  # Excel row number (1-indexed + header)
                        'error': '; '.join(error_msg),
                        'data': student_data
                    })
                else:

                    cleaned_data = {
                        'Sno': student_data.get('sno', ''),
                        'Jee Main Application Number': student_data.get('jee_app_no', ''),
                        'Institute Roll Number': student_data.get('roll_number', ''),
                        'Name': student_data.get('name', ''),
                        'Discipline': student_data.get('discipline', ''),
                        'Gender': student_data.get('gender', ''),
                        'Category': student_data.get('category', ''),
                        'PWD': student_data.get('pwd', ''),
                        'Minority': student_data.get('minority', ''),
                        'Mobile No': student_data.get('phone_number', ''),
                        'Institute Email ID': student_data.get('institute_email', ''),
                        'Alternet Email ID': student_data.get('personal_email', ''),
                        'Father\'s Name': student_data.get('father_name', ''),
                        'Father\'s Occupation': student_data.get('father_occupation', ''),
                        'Father Mobile Number': student_data.get('father_mobile', ''),
                        'Mother\'s Name': student_data.get('mother_name', ''),
                        'Mother\'s Occupation': student_data.get('mother_occupation', ''),
                        'Mother Mobile Number': student_data.get('mother_mobile', ''),
                        'Date of Birth': student_data.get('date_of_birth', ''),
                        'AI rank': student_data.get('ai_rank', ''),
                        'Category Rank': student_data.get('category_rank', ''),
                        'allottedcat': student_data.get('allotted_category', ''),
                        'Allotted Gender': student_data.get('allotted_gender', ''),
                        'State': student_data.get('state', ''),
                        'Full Address': student_data.get('address', '')
                    }
                    valid_students.append(cleaned_data)
                    
            except Exception as e:
                invalid_students.append({
                    'row': index + 2,
                    'error': f'Error processing row: {str(e)}',
                    'data': {}
                })
        
        return JsonResponse({
            'success': True,
            'valid_students': valid_students,
            'invalid_students': invalid_students,
            'valid_records': len(valid_students),
            'invalid_records': len(invalid_students),
            'total_records': len(df),
            'message': f'Excel file processed successfully. {len(valid_students)} valid records, {len(invalid_students)} invalid records.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to process Excel file: {str(e)}'
        }, status=500)

# =============================================================================
# STUDENT BATCH OPERATIONS
# =============================================================================

@csrf_exempt
@require_http_methods(["POST"])
def check_student_duplicate(student, duplicate_check_fields):

    field_mapping = {
        'jeeAppNo': 'jee_app_no',
        'rollNumber': 'roll_number',
        'instituteEmail': 'institute_email',
        'fname': 'father_name',
        'personalEmail': 'personal_email',
        'mobile': 'mobile_number'
    }
    
    try:
        for field in duplicate_check_fields:
            backend_field = field_mapping.get(field, field.lower())
            student_value = student.get(field)
            
            if not student_value:
                continue

            if backend_field == 'jee_app_no':
                existing = StudentBatchUpload.objects.filter(jee_app_no=student_value).first()
                if existing:
                    return True, f"JEE Application Number {student_value} already exists for {existing.name}"
                    
            elif backend_field == 'roll_number':
                existing = StudentBatchUpload.objects.filter(roll_number=student_value).first()
                if existing:
                    return True, f"Roll Number {student_value} already exists for {existing.name}"
                    
            elif backend_field == 'institute_email':
                existing = StudentBatchUpload.objects.filter(institute_email=student_value).first()
                if existing:
                    return True, f"Institute Email {student_value} already exists for {existing.name}"
                    
            elif backend_field == 'personal_email':
                existing = StudentBatchUpload.objects.filter(personal_email=student_value).first()
                if existing:
                    return True, f"Personal Email {student_value} already exists for {existing.name}"
                    
            elif backend_field == 'mobile_number':
                existing = StudentBatchUpload.objects.filter(mobile_number=student_value).first()
                if existing:
                    return True, f"Mobile Number {student_value} already exists for {existing.name}"
        
        return False, ""
        
    except Exception as e:
        return False, ""


@csrf_exempt
@require_http_methods(["POST"])
def save_students_batch(request):
    try:
        data = json.loads(request.body)
        students = data.get('students', [])
        programme_type = data.get('programme_type', 'ug')
        selected_year = data.get('academic_year')
        if selected_year:
            try:
                # Normalize ANY year input to get both formats
                batch_year, academic_year = normalize_year_input(selected_year)
            except ValueError as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Invalid year format: {str(e)}'
                }, status=400)
        else:
            batch_year, academic_year = get_current_academic_year()
        
        from applications.programme_curriculum.models import Curriculum, Batch

        available_curriculums = Curriculum.objects.filter(working_curriculum=True)
        if not available_curriculums.exists():
            return JsonResponse({
                'success': False,
                'message': f'❌ CURRICULUM REQUIRED: No working curriculums found. Please create a curriculum first before saving student data.',
                'validation_error': 'missing_curriculum'
            }, status=400)
        
        existing_batches = Batch.objects.filter(year=batch_year, running_batch=True)
        if not existing_batches.exists():
            return JsonResponse({
                'success': False,
                'message': f'❌ BATCH REQUIRED: No active batches found for academic year {academic_year} (batch year {batch_year}). Please create batches with assigned curriculums first before saving student data.',
                'validation_error': 'missing_batch',
                'academic_year': academic_year,
                'batch_year': batch_year
            }, status=400)

        batches_without_curriculum = existing_batches.filter(curriculum__isnull=True)
        if batches_without_curriculum.exists():
            batch_names = [f"{batch.name} {batch.discipline.acronym}" for batch in batches_without_curriculum]
            return JsonResponse({
                'success': False,
                'message': f'The following batches for {academic_year} exist but have no curriculum assigned: {", ".join(batch_names)}. Please assign curriculums to all batches first.',
                'validation_error': 'batch_missing_curriculum',
                'batches_without_curriculum': batch_names,
                'academic_year': academic_year
            }, status=400)
        
        skip_duplicates = data.get('skip_duplicates', False)
        duplicate_check_fields = data.get('duplicate_check_fields', ['jeeAppNo', 'rollNumber', 'instituteEmail'])
        
        if not students:
            return JsonResponse({
                'success': False,
                'message': 'No student data provided'
            }, status=400)

        # Initialize counters
        successful_uploads = 0
        failed_uploads = 0
        skipped_duplicates = 0
        validation_errors = 0
        errors = []
        
        # Filter out duplicates if requested
        if skip_duplicates:
            filtered_students = []
            duplicate_students = []
            
            for student in students:
                is_duplicate, duplicate_info = check_student_duplicate(student, duplicate_check_fields)
                
                if is_duplicate:
                    skipped_duplicates += 1
                    duplicate_students.append({
                        'student': student,
                        'duplicate_reason': duplicate_info
                    })
                else:
                    filtered_students.append(student)
            
            students = filtered_students

        # Process batch allocation (remove atomic transaction to allow individual student processing)
        processed_students = process_batch_allocation(students, programme_type, batch_year)
        
        for student_data in processed_students:
            try:
                with transaction.atomic():
                    student_name = student_data.get('Name') or student_data.get('name', 'Unknown')
                    name = (student_data.get('Name') or student_data.get('name', '')).strip()
                    if not name:
                        validation_errors += 1
                        errors.append(f"Student at row has no name - skipping")
                        continue
                    
                    dob = None
                    dob_value = student_data.get('Date of Birth') or student_data.get('dob')
                    if dob_value:
                        try:
                            dob_str = str(dob_value)
                            if '/' in dob_str:
                                dob = datetime.strptime(dob_str, '%m/%d/%Y').date()
                            elif '-' in dob_str:
                                dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
                        except Exception as dob_error:
                            dob = None
                    
                    discipline_name = student_data.get('Discipline') or student_data.get('branch', '')
                    
                    batch_name = get_batch_name_from_discipline(discipline_name, programme_type)
                    
                    discipline_obj = get_or_create_discipline(discipline_name)
                    
                    try:
                        batch_obj = Batch.objects.get(
                            name=batch_name, 
                            discipline=discipline_obj, 
                            year=batch_year,
                            running_batch=True
                        )
                    except Batch.DoesNotExist:
                        name_year_matches = Batch.objects.filter(name=batch_name, year=batch_year, running_batch=True)
                        discipline_year_matches = Batch.objects.filter(discipline=discipline_obj, year=batch_year, running_batch=True)
                        existing_batches = Batch.objects.filter(year=batch_year, running_batch=True)
                        
                        error_msg = f"No active batch exists for {batch_name} with discipline '{discipline_obj.name}' in Year-{batch_year}. Please create the batch via Admin Batch Management first."
                        failed_uploads += 1
                        errors.append({
                            'student': student_data.get('Name', 'Unknown'),
                            'roll_number': student_data.get('Institute Roll Number', ''),
                            'error': error_msg,
                            'validation_error': 'missing_batch',
                            'required_batch': f"{batch_name} {discipline_obj.name} {batch_year}",
                            'required_action': f'Create batch for {batch_name} {discipline_obj.name} Year-{batch_year} via Admin Batch Management first'
                        })
                        continue
                    
                    student_upload = StudentBatchUpload.objects.create(
                        # Core identification - handle both field name formats
                        jee_app_no=student_data.get('Jee Main Application Number') or student_data.get('jeeAppNo', ''),
                        roll_number=student_data.get('Institute Roll Number') or student_data.get('rollNumber', ''),
                        institute_email=student_data.get('Institute Email ID') or student_data.get('instituteEmail', ''),
                        
                        name=student_data.get('Name') or student_data.get('name', ''),
                        father_name=student_data.get("Father's Name") or student_data.get('fname', ''),
                        mother_name=student_data.get("Mother's Name") or student_data.get('mname', ''),
                        gender=student_data.get('Gender') or student_data.get('gender', ''),
                        category=student_data.get('Category') or student_data.get('category', ''),
                        pwd=student_data.get('PWD') or student_data.get('pwd', 'NO'),
                        minority=student_data.get('Minority') or student_data.get('minority', 'Not Applicable'),

                        phone_number=student_data.get('Mobile No') or student_data.get('phoneNumber', ''),
                        personal_email=student_data.get('Alternet Email ID') or student_data.get('email', ''),
                        address=student_data.get('Full Address') or student_data.get('address', ''),
                        state=student_data.get('State') or student_data.get('state', ''),

                        branch=student_data.get('Discipline') or student_data.get('branch', ''),
                        date_of_birth=dob,
                        ai_rank=int(str((student_data.get('AI rank') or student_data.get('jeeRank', 0))).replace(',', '')) if (student_data.get('AI rank') or student_data.get('jeeRank')) and str((student_data.get('AI rank') or student_data.get('jeeRank', 0))).replace(',', '').isdigit() else None,
                        category_rank=int(str((student_data.get('Category Rank') or student_data.get('categoryRank', 0))).replace(',', '')) if (student_data.get('Category Rank') or student_data.get('categoryRank')) and str((student_data.get('Category Rank') or student_data.get('categoryRank', 0))).replace(',', '').isdigit() else None,

                        father_occupation=student_data.get("Father's Occupation") or student_data.get('fatherOccupation', ''),
                        father_mobile=student_data.get('Father Mobile Number') or student_data.get('fatherMobile', ''),
                        mother_occupation=student_data.get("Mother's Occupation") or student_data.get('motherOccupation', ''),
                        mother_mobile=student_data.get('Mother Mobile Number') or student_data.get('motherMobile', ''),

                        allotted_category=student_data.get('allottedcat') or student_data.get('allottedCategory', ''),
                        allotted_gender=student_data.get('Allotted Gender') or student_data.get('allottedGender', ''),

                        year=batch_year,
                        academic_year=academic_year,  # Use the normalized academic year
                        programme_type=programme_type,
                        reported_status='NOT_REPORTED',
                        source='excel_upload',  # Track that this came from Excel upload
                        uploaded_by=request.user if request.user.is_authenticated else None
                    )
                    
                    # AUTOMATIC USER ACCOUNT CREATION with HASHED PASSWORD
                    if student_upload.roll_number:
                        try:
                            user_account, plain_password = student_upload.create_user_account()
                            if user_account and plain_password:
                                # Store password for potential emailing (temporarily)
                                student_data['auto_generated_password'] = plain_password
                                student_data['user_created'] = True
                            else:
                                student_data['user_created'] = False
                        except Exception as user_error:
                            student_data['user_created'] = False
                    else:
                        student_data['user_created'] = False

                    if student_data.get('Institute Roll Number'):
                        create_or_update_main_student_record(student_data, batch_obj, batch_year)
                    
                    successful_uploads += 1
                    
            except Exception as e:
                failed_uploads += 1
                error_msg = f"Failed to save student {student_name}: {str(e)}"
                errors.append(error_msg)

        total_processed = successful_uploads + failed_uploads + validation_errors
        response_data = {
            'success': True,
            'data': {
                'successful_uploads': successful_uploads,
                'failed_uploads': failed_uploads,
                'skipped_duplicates': skipped_duplicates,
                'validation_errors': validation_errors,
                'total_processed': total_processed,
                'original_count': len(data.get('students', []))
            },
            'students': processed_students,
            'summary': get_allocation_summary(processed_students, programme_type),
            'errors': errors
        }
        
        messages = []
        if successful_uploads > 0:
            messages.append(f'{successful_uploads} students uploaded successfully')
        if skipped_duplicates > 0:
            messages.append(f'{skipped_duplicates} duplicates skipped')
        if failed_uploads > 0:
            messages.append(f'{failed_uploads} uploads failed')
        if validation_errors > 0:
            messages.append(f'{validation_errors} validation errors')
            
        response_data['message'] = '. '.join(messages) + '.'
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to save students batch: {str(e)}'
        }, status=500)

def process_batch_allocation(students, programme_type, batch_year=None):
    """Process batch allocation algorithm"""
    if batch_year is None:
        current_year = datetime.now().year
        batch_year = current_year if datetime.now().month >= 7 else current_year - 1
    
    display_year = batch_year 

    branch_groups = {}
    
    for student in students:
        branch_field = student.get('Discipline', '') or student.get('branch', '')
        branch_code = get_branch_code(branch_field, programme_type)
        
        if branch_code not in branch_groups:
            branch_groups[branch_code] = []
        
        branch_groups[branch_code].append({
            **student,
            'branch_code': branch_code,
            'display_branch': get_display_branch_name(branch_field)
        })

    for branch_code in branch_groups:
        branch_groups[branch_code].sort(key=lambda x: x.get('Name', '') or x.get('name', ''))
    
    # Allocate roll numbers
    processed_students = []
    branch_counters = {}
    
    for branch_code, students_in_branch in branch_groups.items():
        for student in students_in_branch:
            processed_students.append({
                **student,
                # Use provided roll number and email from Excel/manual entry with correct field names
                'roll_number': student.get('Institute Roll Number', '') or student.get('rollNumber', ''),
                'institute_email': student.get('Institute Email ID', '') or student.get('instituteEmail', ''),
                'year': display_year,
                'programme': programme_type.upper(),
                'allocation_date': timezone.now().isoformat(),
                'status': 'ALLOCATED',
                'reported_status': 'NOT_REPORTED'  # Password will be generated when this changes to REPORTED
            })
            
    
    processed_students.sort(key=lambda x: x['roll_number'])
    
    return processed_students

def get_branch_code(branch_name, programme_type):
    branch_lower = branch_name.lower()
    
    if programme_type == 'ug':
        if 'computer' in branch_lower or 'cse' in branch_lower:
            return 'BCS'
        elif 'electronics' in branch_lower or 'ece' in branch_lower:
            return 'BEC'
        elif 'mechanical' in branch_lower or 'me' in branch_lower:
            return 'BME'
        elif 'smart' in branch_lower or 'manufacturing' in branch_lower:
            return 'BSM'
        elif 'design' in branch_lower:
            return 'BDS'
    elif programme_type == 'pg':
        if 'computer' in branch_lower or 'cse' in branch_lower:
            return 'MCS'
        elif 'electronics' in branch_lower or 'ece' in branch_lower:
            return 'MEC'
        elif 'mechanical' in branch_lower or 'me' in branch_lower:
            return 'MME'
        elif 'smart' in branch_lower or 'manufacturing' in branch_lower:
            return 'MSM'
        elif 'design' in branch_lower:
            return 'MDS'
    elif programme_type == 'phd':
        if 'computer' in branch_lower or 'cse' in branch_lower:
            return 'PCS'
        elif 'electronics' in branch_lower or 'ece' in branch_lower:
            return 'PEC'
        elif 'mechanical' in branch_lower or 'me' in branch_lower:
            return 'PME'
        elif 'smart' in branch_lower or 'manufacturing' in branch_lower:
            return 'PSM'
        elif 'design' in branch_lower:
            return 'PDS'
    
    return 'UNK'  # Unknown

def generate_roll_number(branch_code, year, sequence):
    year_suffix = str(year)[-2:]
    sequence_str = str(sequence).zfill(3)
    return f"{year_suffix}{branch_code}{sequence_str}"

def generate_institute_email(roll_number):
    return f"{roll_number.lower()}@iiitdmj.ac.in"

def generate_password():
    import random
    import string
    charset = string.ascii_letters + string.digits + "!@#$%"
    return ''.join(random.choice(charset) for _ in range(8))

def get_allocation_summary(students, programme_type):
    branch_counts = {}
    for student in students:
        branch = student.get('branch_code', 'Unknown')
        branch_counts[branch] = branch_counts.get(branch, 0) + 1
    
    return {
        'total_students': len(students),
        'branch_counts': branch_counts,
        'programme': programme_type.upper(),
        'allocation_date': timezone.now().isoformat()
    }

# =============================================================================
# SINGLE STUDENT OPERATIONS
# =============================================================================

@csrf_exempt
@require_http_methods(["POST"])
def add_single_student(request):
    try:
        data = json.loads(request.body)
        programme_type = data.get('programme_type', 'ug')
        selected_year = data.get('academic_year')
        if selected_year:
            try:
                batch_year, academic_year = normalize_year_input(selected_year)
            except ValueError as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Invalid year format: {str(e)}'
                }, status=400)
        else:
            batch_year, academic_year = get_current_academic_year()
        
        from applications.programme_curriculum.models import Curriculum, Batch
        
        available_curriculums = Curriculum.objects.filter(working_curriculum=True)
        if not available_curriculums.exists():
            return JsonResponse({
                'success': False,
                'message': f'❌ CURRICULUM REQUIRED: No working curriculums found. Please create a curriculum first before adding student.',
                'validation_error': 'missing_curriculum'
            }, status=400)
        
        existing_batches = Batch.objects.filter(year=batch_year, running_batch=True)
        if not existing_batches.exists():
            return JsonResponse({
                'success': False,
                'message': f'❌ BATCH REQUIRED: No active batches found for academic year {academic_year} (batch year {batch_year}). Please create batches with assigned curriculums first before adding student.',
                'validation_error': 'missing_batch',
                'academic_year': academic_year,
                'batch_year': batch_year
            }, status=400)

        batches_without_curriculum = existing_batches.filter(curriculum__isnull=True)
        if batches_without_curriculum.exists():
            batch_names = [f"{batch.name} {batch.discipline.acronym}" for batch in batches_without_curriculum]
            return JsonResponse({
                'success': False,
                'message': f'❌ CURRICULUM ASSIGNMENT REQUIRED: The following batches for {academic_year} exist but have no curriculum assigned: {", ".join(batch_names)}. Please assign curriculums to all batches first.',
                'validation_error': 'batch_missing_curriculum',
                'batches_without_curriculum': batch_names,
                'academic_year': academic_year
            }, status=400)

        field_mapping = {
            'fname': 'father_name',
            'mname': 'mother_name',
            'jeeAppNo': 'jee_app_no',
            'phoneNumber': 'phone_number',
            'email': 'personal_email',
            'dob': 'date_of_birth',
            'aadharNumber': 'aadhar_number',
            'tenthMarks': 'tenth_marks',
            'twelfthMarks': 'twelfth_marks',
            'jeeRank': 'ai_rank',
            'categoryRank': 'category_rank',
            'allottedGender': 'allotted_gender',
            'allottedCategory': 'allotted_category',
            'fatherOccupation': 'father_occupation',
            'fatherMobile': 'father_mobile',
            'motherOccupation': 'mother_occupation',
            'motherMobile': 'mother_mobile',
            # DON'T map these - process_batch_allocation needs original names
            # 'rollNumber': 'roll_number',
            # 'instituteEmail': 'institute_email'
        }

        mapped_data = {}
        for key, value in data.items():
            mapped_key = field_mapping.get(key, key)
            mapped_data[mapped_key] = value

            if key in ['rollNumber', 'instituteEmail']:
                mapped_data[key] = value  # Keep original name too

        data = mapped_data

        required_fields = ['name', 'father_name', 'mother_name', 'jee_app_no', 'branch', 'gender', 'category', 'pwd', 'address']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return JsonResponse({
                'success': False,
                'message': f'Missing required fields: {", ".join(missing_fields)}'
            }, status=400)

        processed_students = process_batch_allocation([data], programme_type, batch_year)
        
        if not processed_students:
            return JsonResponse({
                'success': False,
                'message': 'Failed to process student data'
            }, status=400)
        
        student_data = processed_students[0]

        jee_app_no = data.get('jee_app_no')
        if jee_app_no:
            existing_student = StudentBatchUpload.objects.filter(jee_app_no=jee_app_no).first()
            if existing_student:
                return JsonResponse({
                    'success': False,
                    'message': f'Student with JEE Application Number {jee_app_no} already exists (Roll Number: {existing_student.roll_number})'
                }, status=400)

        dob = None
        if data.get('date_of_birth'):
            try:
                dob_str = str(data['date_of_birth'])
                if '/' in dob_str:
                    dob = datetime.strptime(dob_str, '%m/%d/%Y').date()
                elif '-' in dob_str:
                    dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
            except Exception:
                dob = None
        
        # Save to database with ALL Excel-equivalent fields for complete synchronization
        with transaction.atomic():
            student = StudentBatchUpload.objects.create(
                name=student_data.get('name'),
                jee_app_no=student_data.get('jee_app_no'),
                roll_number=student_data.get('roll_number'),
                institute_email=student_data.get('institute_email'),

                father_name=student_data.get('father_name'),
                mother_name=student_data.get('mother_name'),
                gender=student_data.get('gender'),
                category=student_data.get('category'),
                pwd=student_data.get('pwd'),
                minority=data.get('minority', 'Not Applicable'),
                date_of_birth=dob or data.get('date_of_birth'),

                phone_number=data.get('phone_number', '') or data.get('MobileNo', ''),
                personal_email=data.get('personal_email', '') or data.get('Alternet Email ID', ''),
                address=student_data.get('address'),
                state=data.get('state', '') or data.get('State', ''),

                father_occupation=data.get('father_occupation', '') or data.get("Father's Occupation", ''),
                father_mobile=data.get('father_mobile', '') or data.get('Father Mobile Number', ''),
                mother_occupation=data.get('mother_occupation', '') or data.get("Mother's Occupation", ''),
                mother_mobile=data.get('mother_mobile', '') or data.get('Mother Mobile Number', ''),

                branch=student_data.get('branch'),
                ai_rank=data.get('ai_rank') or data.get('AI rank'),
                category_rank=data.get('category_rank') or data.get('Category Rank'),

                allotted_category=data.get('allotted_category', '') or data.get('allottedcat', ''),
                allotted_gender=data.get('allotted_gender', '') or data.get('Allotted Gender', ''),

                year=batch_year, 
                programme_type=programme_type,
                reported_status='NOT_REPORTED',
                academic_year=academic_year,
                allocation_status='ALLOCATED',
                source='manual_entry'
            )
            
            # Automatically transfer manual entries to main academic tables
            auto_generated_password = None
            user_created = False
            transfer_success = False
            
            try:
                from django.http import HttpRequest
                from django.contrib.auth.models import AnonymousUser
                
                # Create a mock request for the status update function
                mock_request = HttpRequest()
                mock_request.method = 'PUT'
                mock_request._body = json.dumps({
                    'studentId': student.id,
                    'reportedStatus': 'REPORTED'
                }).encode('utf-8')
                mock_request.user = request.user if hasattr(request, 'user') else AnonymousUser()

                from django.test import RequestFactory
                factory = RequestFactory()
                update_request = factory.put(
                    '/api/students/status/',
                    data=json.dumps({
                        'studentId': student.id,
                        'reportedStatus': 'REPORTED'
                    }),
                    content_type='application/json'
                )
                update_request.user = request.user if hasattr(request, 'user') else AnonymousUser()
                
                # Call update_student_status function directly
                status_response = update_student_status(update_request)
                
                if status_response.status_code == 200:
                    response_data = json.loads(status_response.content)
                    if response_data.get('success'):
                        transfer_success = True
                        auto_generated_password = response_data.get('password')
                        user_created = response_data.get('user_created', False)
                
            except Exception as transfer_error:
                transfer_success = False
        
        # Build success message
        success_message = f'Student added successfully'
        if transfer_success:
            success_message += f' and transferred to main academic tables'
            if user_created:
                success_message += f' with auto-generated login credentials'
        
        return JsonResponse({
            'success': True,
            'data': {
                'student_id': student.id,
                'roll_number': student.roll_number or student_data.get('roll_number'),
                'institute_email': student.institute_email or student_data.get('institute_email'),
                'password': auto_generated_password,
                'user_created': user_created,
                'username': student.roll_number if user_created else None,
                'transferred_to_academic': transfer_success
            },
            'message': success_message
        })
        
    except json.JSONDecodeError as e:
        return JsonResponse({
            'success': False,
            'message': f'Invalid JSON data: {str(e)}'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to add student: {str(e)}'
        }, status=500)

# =============================================================================
# SEAT MANAGEMENT
# =============================================================================

@csrf_exempt
@require_http_methods(["PUT"])
def set_total_seats(request):
    try:
        data = json.loads(request.body)
        
        programme = data.get('programme')
        discipline = data.get('discipline')
        year = data.get('year')
        total_seats = data.get('total_seats')
        
        if not all([programme, discipline, year, total_seats]):
            return JsonResponse({
                'success': False,
                'message': 'Missing required fields: programme, discipline, year, total_seats'
            }, status=400)

        batch_config, created = BatchConfiguration.objects.update_or_create(
            programme=programme,
            discipline=discipline,
            year=year,
            defaults={'total_seats': total_seats}
        )

        batch_config.calculate_seats()
        
        return JsonResponse({
            'success': True,
            'message': f'Total seats updated to {total_seats} for {programme} - {discipline}',
            'data': {
                'programme': programme,
                'discipline': discipline,
                'year': year,
                'total_seats': total_seats,
                'filled_seats': batch_config.filled_seats,
                'available_seats': batch_config.available_seats
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to update total seats: {str(e)}'
        }, status=500)

# =============================================================================
# STUDENT STATUS MANAGEMENT
# =============================================================================

@csrf_exempt
@require_http_methods(["PUT", "POST", "OPTIONS"])
def update_student_status(request):
    """
    Update student reported status
    """
    if request.method == 'OPTIONS':
        response = JsonResponse({})
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'PUT, POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, X-CSRFToken, Authorization'
        return response
    
    try:
        data = json.loads(request.body)
        
        student_id = data.get('studentId')
        reported_status = data.get('reportedStatus')
        
        if not student_id or not reported_status:
            return JsonResponse({
                'success': False,
                'message': 'Missing required fields: studentId, reportedStatus'
            }, status=400)
        
        # Validate reported_status
        if reported_status not in ['REPORTED', 'NOT_REPORTED', 'WITHDRAWAL', 'PENDING']:
            return JsonResponse({
                'success': False,
                'message': 'Invalid reportedStatus. Must be REPORTED, NOT_REPORTED, or PENDING'
            }, status=400)
        
        try:
            student = StudentBatchUpload.objects.get(id=student_id)
        except StudentBatchUpload.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Student not found'
            }, status=404)
        
        old_status = student.reported_status
        student.reported_status = reported_status
        student.save()
        
        # Auto-transfer to main tables when status becomes REPORTED
        # OR remove from main tables when status becomes NOT_REPORTED
        transfer_success = False
        transfer_message = ""
        user_created = False
        auto_generated_password = None
        
        if reported_status == 'REPORTED' and old_status != 'REPORTED':
            try:
                # Simple transfer to main tables
                from applications.globals.models import ExtraInfo, DepartmentInfo
                from applications.academic_information.models import Student as AcademicStudent
                from applications.programme_curriculum.models import Batch, Curriculum
                from django.db import transaction
                
                with transaction.atomic():
                    
                    if not student.user:
                        try:
                            user, password = student.create_user_account()
                            auto_generated_password = password
                            user_created = True
                        except Exception as user_error:
                            user_created = False
                    else:
                        if not student.email_password:
                            auto_generated_password = student.generate_secure_password()
                            student.email_password = auto_generated_password
                            student.password_generated_at = timezone.now()
                            student.password_email_sent = False
                            student.save()
                        else:
                            auto_generated_password = student.email_password
                    
                    # Create ExtraInfo if not exists
                    if student.roll_number:
                        from applications.globals.models import DepartmentInfo
                        branch_field = student.branch or ''
                        branch_upper = branch_field.upper()

                        if 'COMPUTER SCIENCE' in branch_upper or 'CSE' in branch_upper:
                            dept_name = 'CSE'
                            discipline_name = 'Computer Science and Engineering'
                        elif 'ELECTRONICS' in branch_upper or 'ECE' in branch_upper:
                            dept_name = 'ECE'
                            discipline_name = 'Electronics and Communication Engineering'
                        elif 'MECHANICAL' in branch_upper or 'ME' in branch_upper:
                            dept_name = 'ME'
                            discipline_name = 'Mechanical Engineering'
                        elif 'SMART MANUFACTURING' in branch_upper or 'SMART' in branch_upper or 'SM' in branch_upper:
                            dept_name = 'SM'
                            discipline_name = 'Smart Manufacturing'
                        elif 'DESIGN' in branch_upper or 'DES' in branch_upper or 'B.DES' in branch_upper:
                            dept_name = 'Design'  # Exact database name
                            discipline_name = 'Design'
                            discipline_acronym = 'Des.'  # Use existing acronym
                        else:
                            # Default fallback
                            dept_name = 'CSE'
                            discipline_name = 'Computer Science and Engineering'

                        try:
                            department = DepartmentInfo.objects.get(name=dept_name)
                        except DepartmentInfo.DoesNotExist:
                            department = DepartmentInfo.objects.create(name=dept_name)
                        
                        extra_info, created = ExtraInfo.objects.get_or_create(
                            id=student.roll_number,
                            defaults={
                                'user': student.user,
                                'title': 'Mr.' if student.gender == 'Male' else ('Ms.' if student.gender == 'Female' else 'Mr.'),
                                'sex': 'M' if student.gender == 'Male' else ('F' if student.gender == 'Female' else 'O'),
                                'date_of_birth': student.date_of_birth or timezone.now().date(),
                                'address': student.address or '',
                                'phone_no': int(student.phone_number) if student.phone_number and student.phone_number.isdigit() else 9999999999,
                                'user_type': 'student',  # CRITICAL: Must be 'student' for proper access
                                'department': department
                            }
                        )
                        
                        # IMPORTANT: Update ALL fields even if ExtraInfo already existed
                        if not created:  # If record already existed, update ALL relevant fields
                            extra_info.department = department
                            extra_info.user = student.user  # Also ensure user is set
                            extra_info.title = 'Mr.' if student.gender == 'Male' else ('Ms.' if student.gender == 'Female' else 'Mr.')
                            extra_info.sex = 'M' if student.gender == 'Male' else ('F' if student.gender == 'Female' else 'O')
                            extra_info.date_of_birth = student.date_of_birth or extra_info.date_of_birth
                            extra_info.address = student.address or extra_info.address
                            if student.phone_number and student.phone_number.isdigit():
                                extra_info.phone_no = int(student.phone_number)
                            extra_info.user_type = 'student'  # CRITICAL: Ensure user_type is always 'student'
                            extra_info.save()

                        # FETCH from existing main tables instead of creating new ones
                        from applications.programme_curriculum.models import Batch, Discipline, Curriculum, Programme
                        from applications.globals.models import DepartmentInfo
                        
                        # FIND existing discipline based on department mapping
                        discipline = None
                        try:
                            if dept_name == 'Design':
                                discipline = Discipline.objects.filter(
                                    acronym='Des.',
                                    name='Design'
                                ).first()
                                
                                if not discipline:
                                    discipline = Discipline.objects.filter(name__icontains='design').first()
                            else:
                                discipline = Discipline.objects.filter(
                                    acronym=dept_name,
                                    name__exact=discipline_name
                                ).first()
                            
                            if not discipline:
                                disciplines = Discipline.objects.filter(acronym=dept_name).order_by('name')
                                discipline = disciplines.first()
                                
                        except Exception as e:
                            pass

                        if not discipline and dept_name != 'Design':
                            try:
                                discipline = Discipline.objects.create(
                                    name=discipline_name,
                                    acronym=dept_name
                                )
                            except Exception as e:
                                discipline = Discipline.objects.filter(acronym=dept_name).first()
                        elif not discipline and dept_name == 'Design':
                            discipline = Discipline.objects.filter(name__icontains='design').first()
                        
                        # FIND existing programme based on correct naming pattern
                        if student.programme_type == 'ug':
                            if 'design' in student.branch.lower():
                                programme_name = 'B.Des'  # Match the actual batch name in database
                            else:
                                programme_name = 'B.Tech'
                            programme_category = 'UG'
                        elif student.programme_type == 'pg':
                            programme_name = 'M.Tech' 
                            programme_category = 'PG'
                        else:
                            programme_name = 'Ph.D'
                            programme_category = 'PhD'
                            
                        # FIND existing programme (look for existing ones first)
                        programme = None
                        try:
                            if dept_name == 'Design':
                                programme = Programme.objects.filter(
                                    name='B.Des',  # Match the actual batch name in database
                                    category=programme_category,
                                    discipline=discipline
                                ).first()
                            else:
                                programme_search_name = f"{programme_name} {dept_name}"
                                programme = Programme.objects.filter(
                                    name__icontains=programme_search_name,
                                    category=programme_category
                                ).first()
                                
                                if not programme:
                                    programme = Programme.objects.filter(
                                        name__icontains=dept_name,
                                        category=programme_category
                                    ).first()
                            
                            if not programme:
                                programme = Programme.objects.get_or_create(
                                    name=programme_name,
                                    category=programme_category,
                                    defaults={'discipline': discipline}
                                )[0]
                        except Exception as e:
                            programme = Programme.objects.get_or_create(
                                name=programme_name,
                                category=programme_category,
                                defaults={'discipline': discipline}
                            )[0]

                        from applications.programme_curriculum.models import Curriculum

                        discipline_from_excel = student.branch or ''
                        
                        # Map discipline for specialization field (shortened for 40 char limit)
                        if 'Computer Science' in discipline_from_excel or 'CSE' in discipline_from_excel:
                            specialization = 'Computer Science and Engineering'
                        elif 'Electronics' in discipline_from_excel or 'ECE' in discipline_from_excel:
                            specialization = 'Electronics and Communication'
                        elif 'Mechanical' in discipline_from_excel or 'ME' in discipline_from_excel:
                            specialization = 'Mechanical Engineering'
                        elif 'Smart Manufacturing' in discipline_from_excel or 'SM' in discipline_from_excel:
                            specialization = 'Smart Manufacturing'
                        elif 'Design' in discipline_from_excel:
                            specialization = 'Design'
                        else:
                            specialization = discipline_from_excel[:35]  # Fallback
                        
                        try:
                            batch_obj = Batch.objects.filter(
                                name=programme_name,    
                                year=student.year,   
                                discipline=discipline,  
                                running_batch=True
                            ).first()
                            
                            if batch_obj:
                                pass
                            else:
                                batch_obj = Batch.objects.filter(
                                    year=student.year,
                                    discipline=discipline,
                                    running_batch=True
                                ).first()
                                
                                if batch_obj:
                                    pass
                                else:
                                    # Enhanced error message
                                    error_msg = f"❌ BATCH NOT FOUND: No existing batch found for {programme_name} {discipline.name} Year-{student.year}. Please create the batch first via Admin Batch Management."
                                    
                                    return JsonResponse({
                                        'success': False,
                                        'message': error_msg,
                                        'error_code': 'BATCH_NOT_FOUND',
                                        'required_action': f'Create batch for {programme_name} {discipline.name} Year-{student.year} via Admin Batch Management first'
                                    }, status=400)
                                
                        except Exception as e:
                            return JsonResponse({
                                'success': False,
                                'message': f'Error finding batch: {str(e)}',
                                'error_code': 'BATCH_MATCHING_ERROR',
                                'required_action': 'Check batch configuration and try again'
                            }, status=500)

                        current_semester = calculate_current_semester(int(student.year))

                        academic_student, created = AcademicStudent.objects.get_or_create(
                            id=extra_info, 
                            defaults={
                                'batch_id': batch_obj, 
                                'specialization': specialization,
                                'programme': programme_name,
                                'batch': student.year,  
                                'father_name': student.father_name or '',  
                                'mother_name': student.mother_name or '', 
                                'category': student.category or '',  
                                'cpi': 0.0,  
                                'curr_semester_no': current_semester,  
                                'hall_no': 0,  
                                'room_no': '',
                            }
                        )
                        
                        # IMPORTANT: Update ALL fields even if Student already existed
                        if not created:
                            academic_student.specialization = specialization
                            academic_student.batch_id = batch_obj  
                            academic_student.programme = programme_name 
                            academic_student.batch = student.year 
                            academic_student.father_name = student.father_name or ''  
                            academic_student.mother_name = student.mother_name or '' 
                            academic_student.category = student.category or ''  
                            academic_student.curr_semester_no = current_semester 
                            academic_student.save()
                            
                            # BATCH CURRICULUM IS ALREADY ASSIGNED VIA FORM - NO NEED TO MODIFY
                            try:
                                pass
                                    
                            except Exception as e:
                                pass
                        
                        # CREATE STUDENT DESIGNATION
                        try:
                            if student.user:
                                student_designation, created = Designation.objects.get_or_create(
                                    name='student',
                                    defaults={
                                        'full_name': 'Student',
                                        'type': 'Academic'
                                    }
                                )

                                existing_designation = HoldsDesignation.objects.filter(
                                    user=student.user,
                                    designation=student_designation
                                ).first()
                                
                                if not existing_designation:
                                    holds_designation = HoldsDesignation.objects.create(
                                        user=student.user,
                                        working=student.user,
                                        designation=student_designation,
                                        held_at=timezone.now()
                                    )
                                    transfer_message_addition = f" | Student designation assigned"
                                else:
                                    transfer_message_addition = f" | Student designation already exists"
                                    
                        except Exception as designation_error:
                            transfer_message_addition = f" | Designation error: {str(designation_error)}"
                        
                        # COURSE REGISTRATION - MANUAL PROCESS

                        course_registration_message = " | Course registration: Manual process (to be done by academic admin)"

                        transfer_message_addition += course_registration_message
                        
                        # COMPREHENSIVE VALIDATION - Check for missing critical components
                        validation_warnings = []
                        try:
                            if hasattr(extra_info, 'student') and extra_info.student:
                                pass
                            else:
                                validation_warnings.append("Missing ExtraInfo.student relationship")

                            if hasattr(student.user, 'extrainfo') and student.user.extrainfo:
                                pass
                            else:
                                validation_warnings.append("Missing User.extrainfo relationship")

                            if academic_student.batch_id and academic_student.batch_id.curriculum:
                                pass
                            else:
                                validation_warnings.append("Missing batch curriculum assignment")

                            if academic_student.curr_semester_no >= 1:
                                pass
                            else:
                                validation_warnings.append("Invalid semester number")

                            designations = student.user.holds_designations.all()
                            if designations.filter(designation__name='student').exists():
                                pass
                            else:
                                validation_warnings.append("Missing student designation access")

                            if validation_warnings:
                                transfer_message_addition += f" | Validation warnings: {'; '.join(validation_warnings)}"
                                
                        except Exception as validation_error:
                            transfer_message_addition += f" | Validation check failed: {str(validation_error)}"
                        
                        transfer_success = True

                        curriculum_status = ""
                        if batch_obj and batch_obj.curriculum:
                            curriculum_status = f" | ✅ Batch: {batch_obj.name} {batch_obj.discipline.acronym} {batch_obj.year} | Curriculum: {batch_obj.curriculum.name}"
                        elif batch_obj:
                            curriculum_status = f" | ⚠️ Batch: {batch_obj.name} {batch_obj.discipline.acronym} {batch_obj.year} | NO CURRICULUM ASSIGNED - Please assign via Batch Form!"
                        else:
                            curriculum_status = f" | ❌ NO BATCH FOUND - Critical error!"
                        
                        transfer_message = f"Student successfully transferred to main academic tables. Roll: {student.roll_number}{curriculum_status}{transfer_message_addition}"
                        
                        # Send welcome email with login credentials using existing email system
                        email_password = auto_generated_password or student.email_password
                        if email_password and not student.password_email_sent:
                            try:
                                # Create email log entry
                                email_log = PasswordEmailLog.objects.create(
                                    student=student,
                                    sent_to_email=student.institute_email or student.personal_email,
                                    sent_by=request.user if hasattr(request, 'user') and request.user.is_authenticated else None,
                                    email_status='PENDING'
                                )

                                email_sent, email_message = send_password_email_smtp(
                                    student_email=(student.institute_email or student.personal_email or '').lower(), 
                                    student_name=student.name,
                                    password=email_password, 
                                    roll_number=student.roll_number,
                                    student=student
                                )
                                
                                if email_sent:
                                    email_log.mark_as_sent(email_password)
                                    student.password_email_sent = True  
                                    student.save()
                                    transfer_message += f" | Email sent to {student.institute_email or student.personal_email}"
                                else:
                                    email_log.mark_as_failed(email_message)
                                    transfer_message += f" | Email failed: {email_message}"
                                    
                            except Exception as email_error:
                                transfer_message += f" | Email error: {str(email_error)}"
                    else:
                        transfer_message = "Transfer skipped: No roll number assigned"
                        
            except Exception as e:
                transfer_message = f"Status updated but transfer failed: {str(e)}"
        
        # REVERT: Remove from main tables when status becomes NOT_REPORTED
        elif reported_status in ['NOT_REPORTED', 'PENDING'] and old_status == 'REPORTED':
            try:
                from applications.globals.models import ExtraInfo
                from applications.academic_information.models import Student as AcademicStudent
                from django.db import transaction
                
                with transaction.atomic():
                    if student.roll_number:
                        try:
                            extra_info = ExtraInfo.objects.get(id=student.roll_number)
                            academic_student = AcademicStudent.objects.get(id=extra_info)

                            batch_to_check = academic_student.batch_id
                            
                            academic_student.delete()
                            transfer_message += f"Removed AcademicStudent record for {student.roll_number}. "

                            if batch_to_check:
                                remaining_students = AcademicStudent.objects.filter(batch_id=batch_to_check).count()
                                if remaining_students == 0:
                                    transfer_message += f"Batch {batch_to_check.name} now empty. "
                                    
                        except AcademicStudent.DoesNotExist:
                            transfer_message += f"No AcademicStudent record found for {student.roll_number}. "
                        except ExtraInfo.DoesNotExist:
                            transfer_message += f"No ExtraInfo record found for {student.roll_number}. "

                        try:
                            extra_info = ExtraInfo.objects.get(id=student.roll_number)
                            extra_info.delete()
                            transfer_message += f"Removed ExtraInfo record for {student.roll_number}. "
                        except ExtraInfo.DoesNotExist:
                            transfer_message += f"No ExtraInfo record found for {student.roll_number}. "

                        if student.user:
                            try:
                                username = student.roll_number if student.roll_number else f"temp_{student.jee_app_no}"
                                if student.user.username == username:
                                    user_to_delete = student.user
                                    student.user = None  # Clear the reference first
                                    student.save()
                                    user_to_delete.delete()
                                    transfer_message += f"Removed User account for {username}. "
                                else:
                                    student.user = None
                                    student.save()
                                    transfer_message += f"Cleared User reference for {student.roll_number}. "
                            except Exception as e:
                                transfer_message += f"Error removing User: {str(e)}. "
                        
                        try:
                            if student.user:
                                student_designation = Designation.objects.get(name='student')
                                holds_designation = HoldsDesignation.objects.filter(
                                    user=student.user,
                                    designation=student_designation
                                ).first()
                                
                                if holds_designation:
                                    holds_designation.delete()
                                    transfer_message += f"Removed student designation for {student.roll_number}. "
                                else:
                                    transfer_message += f"No student designation found for {student.roll_number}. "
                                    
                        except Designation.DoesNotExist:
                            transfer_message += f"Student designation type does not exist. "
                        except Exception as designation_error:
                            transfer_message += f"Error removing designation: {str(designation_error)}. "

                        try:  
                            pass 

                        except Exception as e:
                            transfer_message += f"Additional cleanup warning: {str(e)}. "
                        
                        transfer_success = True
                        if not transfer_message:
                            transfer_message = f"Student {student.roll_number} successfully removed from main academic tables"
                    else:
                        transfer_message = "Revert skipped: No roll number assigned"
                        
            except Exception as e:
                transfer_message = f"Status updated but revert failed: {str(e)}"
        
        # Log the status change
        try:
            from django.contrib.auth.models import User
            user = None
            if hasattr(request, 'user') and request.user.is_authenticated:
                user = request.user
            
            StudentStatusLog.objects.create(
                student=student,
                changed_by=user,
                old_reported_status=old_status,
                new_reported_status=reported_status,
                change_reason=f'Status updated from {old_status} to {reported_status}',
                ip_address=request.META.get('REMOTE_ADDR', 'unknown')
            )
        except Exception:
            pass
        
        # Prepare descriptive response message
        if reported_status == 'REPORTED' and old_status != 'REPORTED':
            main_message = f'Student status updated to {reported_status} and transferred to main academic system'
        elif reported_status in ['NOT_REPORTED', 'PENDING'] and old_status == 'REPORTED':
            main_message = f'Student status reverted to {reported_status} and removed from main academic system'
        else:
            main_message = f'Student status updated to {reported_status}'
        
        response_data = {
            'success': True,
            'message': main_message,
            'data': {
                'student_id': student.id,
                'roll_number': student.roll_number,
                'old_status': old_status,
                'new_status': reported_status,
                'transfer_success': transfer_success,
                'transfer_message': transfer_message,
                'user_created': user_created,
                'password_generated': auto_generated_password if auto_generated_password else None,
                'email_address': student.institute_email or student.personal_email,
                'username': student.roll_number if user_created else None
            }
        }
        
        # Update batch seat calculations after status change
        try:
            from applications.programme_curriculum.models_student_management import BatchConfiguration
            from django.db.models import Q

            discipline_q = Q()
            if student.branch:
                branch_upper = student.branch.upper()
                if 'COMPUTER SCIENCE' in branch_upper or 'CSE' in branch_upper:
                    discipline_q = Q(discipline='Computer Science and Engineering')
                elif 'ELECTRONICS' in branch_upper or 'ECE' in branch_upper:
                    discipline_q = Q(discipline='Electronics and Communication Engineering')
                elif 'DESIGN' in branch_upper:
                    discipline_q = Q(discipline='Design')
                elif 'MECHANICAL' in branch_upper:
                    discipline_q = Q(discipline='Mechanical Engineering')
                elif 'SMART' in branch_upper:
                    discipline_q = Q(discipline='Smart Manufacturing')
            
            # Update seat calculations for matching batches
            if discipline_q:
                matching_batches = BatchConfiguration.objects.filter(
                    discipline_q,
                    year=student.year
                )
                for batch in matching_batches:
                    batch.calculate_seats()
        except Exception as e:
            pass
        
        response = JsonResponse(response_data, status=200)

        response['Access-Control-Allow-Origin'] = '*'
        return response
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to update student status: {str(e)}'
        }, status=500)

# =============================================================================
# EXPORT FUNCTIONALITY
# =============================================================================

@csrf_exempt
@require_http_methods(["GET"])
def export_students(request, programme_type):
    """
    Export student data to Excel
    """
    try:
        students = StudentBatchUpload.objects.filter(programme_type=programme_type).order_by('roll_number')
        
        if not students.exists():
            return JsonResponse({
                'success': False,
                'message': f'No students found for programme type: {programme_type}'
            }, status=404)

        output = BytesIO()
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = f'{programme_type.upper()} Students'

        headers = [
            'S.No', 'JEE Application Number', 'Institute Roll Number', 'Name',
            'Discipline', 'Gender', 'Category', 'PWD', 'Minority', 'Mobile No',
            'Institute Email ID', 'Alternate Email ID', 'Father\'s Name',
            'Father\'s Occupation', 'Father Mobile Number', 'Mother\'s Name',
            'Mother\'s Occupation', 'Mother Mobile Number', 'Date of Birth',
            'AI Rank', 'Category Rank', 'Allotted Category', 'Allotted Gender',
            'State', 'Full Address', 'Reported Status'
        ]
        
        for col, header in enumerate(headers, 1):
            worksheet.cell(row=1, column=col, value=header)

        for row, student in enumerate(students, 2):
            data = [
                row - 1,  # S.No
                student.jee_app_no,
                student.roll_number,
                student.name,
                student.branch,
                student.gender,
                student.category,
                student.pwd,
                getattr(student, 'minority', 'Not Applicable'),
                student.phone_number,
                student.institute_email,
                student.personal_email,
                student.father_name,
                getattr(student, 'father_occupation', ''),
                getattr(student, 'father_mobile', ''),
                student.mother_name,
                getattr(student, 'mother_occupation', ''),
                getattr(student, 'mother_mobile', ''),
                student.date_of_birth.strftime('%d/%m/%Y') if student.date_of_birth else '',
                student.ai_rank,
                student.category_rank,
                getattr(student, 'allotted_category', ''),
                getattr(student, 'allotted_gender', ''),
                getattr(student, 'state', ''),
                student.address,
                student.reported_status
            ]
            
            for col, value in enumerate(data, 1):
                worksheet.cell(row=row, column=col, value=value)
        
        workbook.save(output)
        output.seek(0)

        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{programme_type}_students_{datetime.now().strftime("%Y%m%d")}.xlsx"'
        
        return response
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to export student data: {str(e)}'
        }, status=500)

# =============================================================================
# UPLOAD HISTORY
# =============================================================================

@csrf_exempt
@require_http_methods(["GET"])
def upload_history(request):
    """
    Get upload history
    """
    try:
        from django.db.models import Count
        
        history = StudentBatchUpload.objects.values('created_at__date', 'programme_type').annotate(
            count=Count('id')
        ).order_by('-created_at__date')
        
        return JsonResponse({
            'success': True,
            'data': list(history),
            'message': 'Upload history fetched successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to fetch upload history: {str(e)}'
        }, status=500)

# =============================================================================
# STUDENT LISTING
# =============================================================================

@csrf_exempt
@require_http_methods(["GET"])
def list_students(request):
    """
    List students with filters
    """
    try:
        programme_type = request.GET.get('programme_type')
        batch_id = request.GET.get('batch_id')
        year = request.GET.get('year')
        
        students = StudentBatchUpload.objects.all()
        
        if programme_type:
            students = students.filter(programme_type=programme_type)
        
        if year:
            students = students.filter(year=year)
        
        if batch_id:
            students = students.filter(id=batch_id)
        
        students = students.order_by('roll_number')
        
        student_list = []
        for student in students:
            student_list.append({
                'id': student.id,
                'name': student.name,
                'roll_number': student.roll_number,
                'institute_email': student.institute_email,
                'father_name': student.father_name,
                'category': student.category,
                'pwd': student.pwd,
                'minority': getattr(student, 'minority', 'Not Applicable'),
                'reported_status': student.reported_status,
                'branch': student.branch,
                'year': student.year,
                'source': getattr(student, 'source', 'unknown')  # Include source field
            })
        
        return JsonResponse({
            'success': True,
            'data': student_list,
            'total': len(student_list),
            'message': 'Students listed successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to list students: {str(e)}'
        }, status=500)

# =============================================================================
# BATCH CRUD OPERATIONS
# =============================================================================

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
@require_http_methods(["POST"])
def create_batch(request):
    """
    Create new batch
    """
    try:
        data = json.loads(request.body)
        
        programme = data.get('programme')
        discipline = data.get('discipline')
        year = data.get('year')
        total_seats = data.get('total_seats') or data.get('totalSeats')
        
        if not all([programme, discipline, year, total_seats]):
            missing_fields = []
            if not programme: missing_fields.append('programme')
            if not discipline: missing_fields.append('discipline') 
            if not year: missing_fields.append('year')
            if not total_seats: missing_fields.append('total_seats/totalSeats')
            
            return JsonResponse({
                'success': False,
                'message': f'Missing required fields: {", ".join(missing_fields)}'
            }, status=400)

        from applications.programme_curriculum.models import Curriculum

        available_curriculums = Curriculum.objects.filter(working_curriculum=True)
        if not available_curriculums.exists():
            return JsonResponse({
                'success': False,
                'message': f'❌ CURRICULUM REQUIRED: No working curriculums found. Please create a curriculum first before creating batches. Batches must have an assigned curriculum.',
                'validation_error': 'missing_curriculum'
            }, status=400)
        
        from applications.programme_curriculum.models import Discipline
        
        try:
            discipline_obj = Discipline.objects.get(id=discipline)
        except Discipline.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': f'Invalid discipline ID: {discipline}'
            }, status=400)

        existing_batch = Batch.objects.filter(
            name=programme,
            discipline=discipline_obj,
            year=year,
            running_batch=True
        ).first()
        
        if existing_batch:
            return JsonResponse({
                'success': False,
                'message': f'❌ DUPLICATE BATCH: A batch "{existing_batch.name} {existing_batch.discipline.acronym} {existing_batch.year}" already exists. Only one batch per discipline per year is allowed.',
                'existing_batch': {
                    'id': existing_batch.id,
                    'name': existing_batch.name,
                    'discipline': existing_batch.discipline.acronym,
                    'year': existing_batch.year,
                    'curriculum': existing_batch.curriculum.name if existing_batch.curriculum else None
                },
                'validation_error': 'duplicate_batch'
            }, status=400)
        
        # Validate data types
        try:
            year = int(year)
            total_seats = int(total_seats)
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'message': 'Year and total_seats must be integers'
            }, status=400)
        
        # Check if batch already exists
        if BatchConfiguration.objects.filter(programme=programme, discipline=discipline, year=year).exists():
            return JsonResponse({
                'success': False,
                'message': 'Batch already exists for this programme, discipline, and year'
            }, status=400)
        
        batch = BatchConfiguration.objects.create(
            programme=programme,
            discipline=discipline,
            year=year,
            total_seats=total_seats
        )
        
        return JsonResponse({
            'success': True,
            'data': {
                'id': batch.id,
                'programme': batch.programme,
                'discipline': batch.discipline,
                'year': batch.year,
                'total_seats': batch.total_seats,
                'totalSeats': batch.total_seats  # Return both formats
            },
            'message': 'Batch created successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to create batch: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["PUT"])
def update_batch(request, batch_id):
    """
    Update existing batch
    """
    try:
        data = json.loads(request.body)
        
        try:
            batch = BatchConfiguration.objects.get(id=batch_id)
        except BatchConfiguration.DoesNotExist:
            # Try to find it in regular Batch model
            try:
                from applications.programme_curriculum.models import Batch
                regular_batch = Batch.objects.get(id=batch_id)
                
                # Create a corresponding BatchConfiguration if it doesn't exist
                batch_config = BatchConfiguration.objects.create(
                    programme=regular_batch.name,
                    discipline=regular_batch.discipline.name if regular_batch.discipline else "Unknown",
                    year=regular_batch.year,
                    total_seats=regular_batch.total_seats
                )
                batch_config.id = batch_id  # Force the same ID
                batch_config.save()
                batch = batch_config
                
            except:
                return JsonResponse({
                    'success': False,
                    'message': f'Batch with ID {batch_id} not found in any model'
                }, status=404)

        # Update fields
        if 'programme' in data:
            batch.programme = data['programme']
        if 'discipline' in data:
            batch.discipline = data['discipline']
        if 'year' in data:
            batch.year = data['year']
        if 'total_seats' in data or 'totalSeats' in data:
            new_total_seats = data.get('total_seats') or data.get('totalSeats')
            batch.total_seats = new_total_seats

        if 'displayBranch' in data:
            batch.discipline = data['displayBranch']
        
        batch.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Batch updated successfully',
            'batch': {
                'id': batch.id,
                'programme': batch.programme,
                'discipline': batch.discipline,
                'year': batch.year,
                'total_seats': batch.total_seats
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to update batch: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def list_batches_with_status(request):
    """
    List all batches with status
    """
    try:
        batches = BatchConfiguration.objects.all().order_by('programme', 'discipline', 'year')
        
        batch_list = []
        for batch in batches:
            batch_list.append({
                'id': batch.id,
                'programme': batch.programme,
                'discipline': batch.discipline,
                'year': batch.year,
                'total_seats': batch.total_seats,
                'filled_seats': batch.filled_seats,
                'available_seats': batch.available_seats
            })
        
        return JsonResponse({
            'success': True,
            'data': batch_list,
            'message': 'Batches listed successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to list batches: {str(e)}'
        }, status=500)

# =============================================================================
# STUDENT STATUS CRUD
# =============================================================================

@csrf_exempt
@require_http_methods(["PUT"])
def update_student_status_crud(request, student_id):
    """
    Update student status
    """
    try:
        data = json.loads(request.body)
        reported_status = data.get('reported_status')
        
        if not reported_status:
            return JsonResponse({
                'success': False,
                'message': 'Missing reported_status field'
            }, status=400)
        
        try:
            student = StudentBatchUpload.objects.get(id=student_id)
        except StudentBatchUpload.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Student not found'
            }, status=404)
        
        old_status = student.reported_status
        student.reported_status = reported_status
        student.save()

        try:
            from applications.programme_curriculum.models_student_management import BatchConfiguration
            from django.db.models import Q

            discipline_q = Q()
            if student.branch:
                branch_upper = student.branch.upper()
                if 'COMPUTER SCIENCE' in branch_upper or 'CSE' in branch_upper:
                    discipline_q = Q(discipline='Computer Science and Engineering')
                elif 'ELECTRONICS' in branch_upper or 'ECE' in branch_upper:
                    discipline_q = Q(discipline='Electronics and Communication Engineering')
                elif 'DESIGN' in branch_upper:
                    discipline_q = Q(discipline='Design')
                elif 'MECHANICAL' in branch_upper:
                    discipline_q = Q(discipline='Mechanical Engineering')
                elif 'SMART' in branch_upper:
                    discipline_q = Q(discipline='Smart Manufacturing')

            if discipline_q:
                matching_batches = BatchConfiguration.objects.filter(
                    discipline_q,
                    year=student.year
                )
                for batch in matching_batches:
                    batch.calculate_seats()
        except Exception as e:
            pass
        
        return JsonResponse({
            'success': True,
            'message': f'Student status updated from {old_status} to {reported_status}'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to update student status: {str(e)}'
        }, status=500)

# =============================================================================
# PASSWORD MANAGEMENT
# =============================================================================

@csrf_exempt
@require_http_methods(["POST"])
def auto_generate_passwords_for_batch(request):
    """
    Auto-generate passwords for a batch
    """
    try:
        data = json.loads(request.body)
        batch_id = data.get('batch_id')
        
        if not batch_id:
            return JsonResponse({
                'success': False,
                'message': 'Missing batch_id'
            }, status=400)

        try:
            batch = BatchConfiguration.objects.get(id=batch_id)
        except BatchConfiguration.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Batch not found'
            }, status=404)
        
        students = StudentBatchUpload.objects.filter(
            branch__icontains=batch.discipline,
            year=batch.year
        )
        
        updated_count = 0
        for student in students:
            if not hasattr(student, 'password') or not student.password:
                student.password = generate_password()
                student.save()
                updated_count += 1
        
        return JsonResponse({
            'success': True,
            'message': f'Generated passwords for {updated_count} students',
            'data': {
                'updated_count': updated_count,
                'total_students': students.count()
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to generate passwords: {str(e)}'
        }, status=500)

# =============================================================================
# HELPER FUNCTIONS FOR STUDENT MANAGEMENT
# =============================================================================

def get_batch_name_from_discipline(discipline_name, programme_type):
    if programme_type == 'ug':
        if 'design' in discipline_name.lower():
            batch_name = 'B.Des'
        else:
            batch_name = 'B.Tech'
    elif programme_type == 'pg':
        if 'design' in discipline_name.lower():
            batch_name = 'M.Des'
        else:
            batch_name = 'M.Tech'
    else:
        batch_name = programme_type.upper()
    
    return batch_name

def get_or_create_discipline(discipline_name):
    from applications.programme_curriculum.models import Discipline

    normalized_name = discipline_name.strip()
    discipline_lower = normalized_name.lower()

    discipline_mapping = {
        'computer science and engineering': 'Computer Science and Engineering',
        'electronics and communication engineering': 'Electronics and Communication Engineering', 
        'mechanical engineering': 'Mechanical Engineering',
        'smart manufacturing': 'Smart Manufacturing',
        'design': 'Design'
    }

    database_discipline_name = None
    for key, value in discipline_mapping.items():
        if key in discipline_lower:
            database_discipline_name = value
            break
    
    if not database_discipline_name:
        database_discipline_name = normalized_name
    
    try:
        discipline = Discipline.objects.get(name=database_discipline_name)
        return discipline
    except Discipline.DoesNotExist:
        # Create new discipline as fallback
        discipline = Discipline.objects.create(
            name=database_discipline_name,
            acronym=get_discipline_acronym(database_discipline_name)
        )
        return discipline

def get_discipline_acronym(discipline_name):

    discipline_mappings = {
        'Computer Science and Engineering': 'CSE',
        'Electronics and Communication Engineering': 'ECE',
        'Mechanical Engineering': 'ME',
        'Smart Manufacturing': 'SM',
        'Design': 'DES'
    }
    
    for full_name, acronym in discipline_mappings.items():
        if full_name.lower() in discipline_name.lower():
            return acronym

    words = discipline_name.split()
    return ''.join([word[0].upper() for word in words if word])[:5]

def validate_batch_exists(batch_name, discipline_obj, batch_year):

    from applications.programme_curriculum.models import Batch
    
    try:
        batch = Batch.objects.get(
            name=batch_name,
            discipline=discipline_obj,
            year=batch_year,
            running_batch=True
        )
        return batch, True
    except Batch.DoesNotExist:
        return None, False

def create_or_update_main_student_record(student_data, batch_obj, batch_year):

    try:
        roll_number = student_data.get('Institute Roll Number', '').strip()
        if not roll_number:
            return None

        try:
            user = User.objects.get(username=roll_number)
        except User.DoesNotExist:
            full_name = student_data.get('Name', '')
            name_parts = full_name.split() if full_name else ['']
            user = User.objects.create_user(
                username=roll_number,
                first_name=name_parts[0] if name_parts else '',
                last_name=' '.join(name_parts[1:]) if len(name_parts) > 1 else '',
                email=student_data.get('Institute Email ID', ''),
                password='student123'  # Default password
            )

        extra_info, created = ExtraInfo.objects.get_or_create(
            user=user,
            defaults={
                'id': roll_number,
                'user_type': 'student',
                'phone_no': student_data.get('Mobile No', ''),
                'address': student_data.get('Full Address', ''),
                'sex': 'M' if student_data.get('Gender', '').lower() == 'male' else 'F' if student_data.get('Gender', '').lower() == 'female' else 'O',
                'date_of_birth': None  # Will be set later if date parsing works
            }
        )

        if student_data.get('Date of Birth'):
            try:
                dob_str = str(student_data['Date of Birth'])
                if '/' in dob_str:
                    dob = datetime.strptime(dob_str, '%m/%d/%Y').date()
                    extra_info.date_of_birth = dob
                    extra_info.save()
            except:
                pass

        category_mapping = {
            'General': 'GEN',
            'GEN': 'GEN',
            'OBC': 'OBC', 
            'SC': 'SC',
            'ST': 'ST'
        }
        category = category_mapping.get(student_data.get('Category', 'GEN'), 'GEN')

        current_semester = calculate_current_semester(batch_year)

        academic_student, created = AcademicStudent.objects.get_or_create(
            id=extra_info,
            defaults={
                'programme': batch_obj.name,
                'batch': batch_year,
                'batch_id': batch_obj,
                'category': category,
                'father_name': student_data.get("Father's Name", ''),
                'mother_name': student_data.get("Mother's Name", ''),
                'cpi': 0.0,
                'curr_semester_no': current_semester  # Dynamic semester calculation
            }
        )
        
        return academic_student
        
    except Exception as e:
        return None


# =============================================================================
# INDIVIDUAL STUDENT CRUD OPERATIONS
# =============================================================================

@csrf_exempt
@require_http_methods(["GET"])
def get_student(request, student_id):
    """
    Get a single student by ID
    """
    try:
        student = StudentBatchUpload.objects.get(id=student_id)

        student_data = {
            # Core identification
            'id': student.id,
            'jee_app_no': student.jee_app_no,
            'jeeAppNo': student.jee_app_no,
            'roll_number': student.roll_number,
            'rollNumber': student.roll_number,
            'institute_email': student.institute_email,
            'instituteEmail': student.institute_email,

            'name': student.name,
            'father_name': student.father_name,
            'fatherName': student.father_name,
            'fname': student.father_name,  # Additional alias
            'mother_name': student.mother_name,
            'motherName': student.mother_name,
            'gender': student.gender,
            'category': student.category,
            'pwd': student.pwd,
            'minority': getattr(student, 'minority', 'Not Applicable'),
            'date_of_birth': student.date_of_birth.isoformat() if student.date_of_birth else '',
            'dateOfBirth': student.date_of_birth.isoformat() if student.date_of_birth else '',

            'phone_number': student.phone_number,
            'phoneNumber': student.phone_number,
            'mobile': student.phone_number,  # Additional alias
            'personal_email': student.personal_email,
            'personalEmail': student.personal_email,
            'address': student.address,
            'state': student.state,

            'branch': student.branch,
            'ai_rank': student.ai_rank,
            'aiRank': student.ai_rank,
            'category_rank': student.category_rank,
            'categoryRank': student.category_rank,
            'tenth_marks': student.tenth_marks,
            'tenthMarks': student.tenth_marks,
            'twelfth_marks': student.twelfth_marks,
            'twelfthMarks': student.twelfth_marks,

            'father_occupation': student.father_occupation,
            'fatherOccupation': student.father_occupation,
            'father_mobile': student.father_mobile,
            'fatherMobile': student.father_mobile,
            'mother_occupation': student.mother_occupation,
            'motherOccupation': student.mother_occupation,
            'mother_mobile': student.mother_mobile,
            'motherMobile': student.mother_mobile,

            'allotted_category': student.allotted_category,
            'allottedCategory': student.allotted_category,
            'allotted_gender': student.allotted_gender,
            'allottedGender': student.allotted_gender,
            'aadhar_number': student.aadhar_number,
            'aadharNumber': student.aadhar_number,

            'reported_status': student.reported_status,
            'reportedStatus': student.reported_status,
            'status': student.reported_status,  # Additional alias
            'year': student.year,
            'programme_type': student.programme_type,
            'programmeType': student.programme_type,
            'created_at': student.created_at.isoformat() if hasattr(student, 'created_at') and student.created_at else '',
            'createdAt': student.created_at.isoformat() if hasattr(student, 'created_at') and student.created_at else '',
            'updated_at': student.updated_at.isoformat() if hasattr(student, 'updated_at') and student.updated_at else '',
            'updatedAt': student.updated_at.isoformat() if hasattr(student, 'updated_at') and student.updated_at else '',
        }
        
        return JsonResponse({
            'success': True,
            'student': student_data,
            'message': f'Student {student.name} retrieved successfully'
        })
        
    except StudentBatchUpload.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': f'Student with ID {student_id} not found'
        }, status=404)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to retrieve student: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["PUT", "POST"])
def update_student(request, student_id):
    """
    Update a student by ID
    """
    try:
        student = StudentBatchUpload.objects.get(id=student_id)
        data = json.loads(request.body)

        field_mapping = {
            'jeeAppNo': 'jee_app_no',
            'rollNumber': 'roll_number', 
            'instituteEmail': 'institute_email',
            'fatherName': 'father_name',
            'fname': 'father_name',
            'mname': 'mother_name', 
            'motherName': 'mother_name',
            'dateOfBirth': 'date_of_birth',
            'dob': 'date_of_birth',
            'phoneNumber': 'phone_number',
            'mobile': 'phone_number',
            'personalEmail': 'personal_email',
            'email': 'personal_email', 
            'aiRank': 'ai_rank',
            'jeeRank': 'ai_rank',
            'categoryRank': 'category_rank',
            'tenthMarks': 'tenth_marks',
            'twelfthMarks': 'twelfth_marks',
            'fatherOccupation': 'father_occupation',
            'fatherMobile': 'father_mobile',
            'motherOccupation': 'mother_occupation',
            'motherMobile': 'mother_mobile',
            'allottedCategory': 'allotted_category',
            'allottedGender': 'allotted_gender',
            'aadharNumber': 'aadhar_number',
            'reportedStatus': 'reported_status',
            'programmeType': 'programme_type'
        }
        
        jee_app_no = data.get('jeeAppNo') or data.get('jee_app_no')
        roll_number = data.get('rollNumber') or data.get('roll_number')
        institute_email = data.get('instituteEmail') or data.get('institute_email')

        if jee_app_no and jee_app_no != student.jee_app_no:
            if StudentBatchUpload.objects.filter(jee_app_no=jee_app_no).exclude(id=student_id).exists():
                return JsonResponse({
                    'success': False,
                    'message': f'JEE Application Number {jee_app_no} already exists for another student'
                }, status=400)

        if roll_number and roll_number != student.roll_number:
            if StudentBatchUpload.objects.filter(roll_number=roll_number).exclude(id=student_id).exists():
                return JsonResponse({
                    'success': False,
                    'message': f'Roll Number {roll_number} already exists for another student'
                }, status=400)

        if institute_email and institute_email != student.institute_email:
            if StudentBatchUpload.objects.filter(institute_email=institute_email).exclude(id=student_id).exists():
                return JsonResponse({
                    'success': False,
                    'message': f'Institute Email {institute_email} already exists for another student'
                }, status=400)

        for frontend_field, backend_field in field_mapping.items():
            if frontend_field in data:
                value = data[frontend_field]
                if hasattr(student, backend_field):
                    setattr(student, backend_field, value)

        direct_fields = [
            'name', 'gender', 'category', 'pwd', 'minority', 'address', 'state', 'branch'
        ]
        
        for field in direct_fields:
            if field in data:
                setattr(student, field, data[field])

        dob_value = data.get('dob') or data.get('dateOfBirth') or data.get('date_of_birth')
        if dob_value:
            try:
                if isinstance(dob_value, str) and dob_value.strip():
                    if '/' in dob_value:
                        student.date_of_birth = datetime.strptime(dob_value, '%m/%d/%Y').date()
                    elif '-' in dob_value:
                        student.date_of_birth = datetime.strptime(dob_value, '%Y-%m-%d').date()
                else:
                    student.date_of_birth = dob_value
            except Exception as e:
                pass

        jee_rank_value = data.get('jeeRank') or data.get('aiRank') or data.get('ai_rank')
        if jee_rank_value:
            try:
                student.ai_rank = int(str(jee_rank_value).replace(',', '')) if str(jee_rank_value).replace(',', '').isdigit() else None
            except (ValueError, TypeError) as e:
                student.ai_rank = None

        rank_fields = ['category_rank', 'tenth_marks', 'twelfth_marks']
        for field in rank_fields:
            frontend_field = field
            if field == 'category_rank':
                frontend_field = 'categoryRank'
            elif field == 'tenth_marks':
                frontend_field = 'tenthMarks'
            elif field == 'twelfth_marks':
                frontend_field = 'twelfthMarks'
                
            value = data.get(frontend_field) or data.get(field)
            if value:
                try:
                    setattr(student, field, int(str(value).replace(',', '')) if str(value).replace(',', '').isdigit() else None)
                except (ValueError, TypeError):
                    setattr(student, field, None)
        
        # Update timestamp if field exists
        if hasattr(student, 'updated_at'):
            student.updated_at = timezone.now()
        
        student.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Student {student.name} updated successfully',
            'student_id': student.id
        })
        
    except StudentBatchUpload.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': f'Student with ID {student_id} not found'
        }, status=404)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data provided'
        }, status=400)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to update student: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["DELETE", "POST"])
def delete_student(request, student_id):
    """
    Delete a student from the batch upload table AND perform cascade deletion from main academic tables
    URL: /programme_curriculum/api/student/{id}/delete/
    
    This performs COMPLETE CASCADE DELETION:
    - Removes from StudentBatchUpload (source table)
    - Removes from AcademicStudent (main academic table) 
    - Removes from ExtraInfo (personal info table)
    - Removes from User (authentication table)
    """
    try:
        from applications.academic_information.models import Student as AcademicStudent
        from applications.globals.models import ExtraInfo
        from django.contrib.auth.models import User
        from django.db import transaction

        student = StudentBatchUpload.objects.get(id=student_id)
        student_name = student.name
        student_roll = student.roll_number

        deletion_info = {
            'id': student.id,
            'name': student_name,
            'roll_number': student_roll,
            'jee_app_no': student.jee_app_no,
            'deleted_by': getattr(request, 'user', None) and hasattr(request.user, 'username') and request.user.username or 'Unknown',
            'deleted_at': timezone.now().isoformat()
        }

        deleted_records = {
            'student_batch_upload': False,
            'academic_student': False,
            'extra_info': False,
            'user_account': False
        }
        
        # Perform CASCADE DELETION in transaction with proper error handling
        try:
            with transaction.atomic():
                if student_roll:
                    try:
                        academic_student = AcademicStudent.objects.get(id__id=student_roll)
                        academic_student.delete()
                        deleted_records['academic_student'] = True
                    except AcademicStudent.DoesNotExist:
                        pass

                if student_roll:
                    try:
                        extra_info = ExtraInfo.objects.get(id=student_roll)
                        extra_info.delete()
                        deleted_records['extra_info'] = True
                    except ExtraInfo.DoesNotExist:
                        pass

                user_to_delete = None
                if student.user:
                    user_to_delete = student.user
                    student.user = None 
                    student.save()
                elif student_roll: 
                    try:
                        user_to_delete = User.objects.get(username=student_roll)  
                    except User.DoesNotExist:
                        pass
                student.delete()
                deleted_records['student_batch_upload'] = True
        
        except Exception as transaction_error:
            return JsonResponse({
                'success': False,
                'message': f'Failed to delete student records: {str(transaction_error)}'
            }, status=500)
        # Handle User deletion separately to avoid transaction conflicts
        if user_to_delete:
            try:
                try:
                    remaining_students = StudentBatchUpload.objects.filter(user=user_to_delete)
                    if remaining_students.exists():
                        remaining_students.update(user=None)
                except Exception as cleanup_error:
                    pass

                with transaction.atomic():
                    user_to_delete.delete()
                    deleted_records['user_account'] = True
                    
            except Exception as user_deletion_error:
                pass
        
        # Build deletion summary
        deletion_summary = []
        if deleted_records['student_batch_upload']:
            deletion_summary.append("StudentBatchUpload")
        if deleted_records['academic_student']:
            deletion_summary.append("AcademicStudent")
        if deleted_records['extra_info']:
            deletion_summary.append("ExtraInfo")
        if deleted_records['user_account']:
            deletion_summary.append("User Account")
        
        return JsonResponse({
            'success': True,
            'message': f'Student {student_name} completely deleted from all systems',
            'cascade_deletion': True,
            'deleted_from': deletion_summary,
            'deleted_student': {
                'id': deletion_info['id'],
                'name': deletion_info['name'],
                'roll': deletion_info['roll_number']
            },
            'deletion_details': deleted_records
        }, status=200)
    
    except StudentBatchUpload.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': f'Student with ID {student_id} not found'
        }, status=404)
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        
        return JsonResponse({
            'success': False,
            'message': f'Failed to delete student: {str(e)}',
            'error_details': str(e)
        }, status=500)


# =============================================================================
# STUDENT TRANSFER TO MAIN TABLES
# =============================================================================

@csrf_exempt
@require_http_methods(["POST"])
def bulk_transfer_students(request):
    """
    Bulk transfer all reported students to main academic tables
    """
    try:
        data = json.loads(request.body)
        year_filter = data.get('year')

        queryset = StudentBatchUpload.objects.filter(
            reported_status='REPORTED',
            user__isnull=True  # Not yet transferred
        )
        
        if year_filter:
            queryset = queryset.filter(year=year_filter)
        
        total_count = queryset.count()
        
        if total_count == 0:
            return JsonResponse({
                'success': True,
                'message': 'No students found to transfer',
                'data': {
                    'total_processed': 0,
                    'success_count': 0,
                    'error_count': 0,
                    'errors': []
                }
            })

        return JsonResponse({
            'success': False,
            'message': 'Bulk transfer feature not yet implemented. Use individual status updates instead.',
            'data': {
                'total_processed': 0,
                'success_count': 0,
                'error_count': 0,
                'errors': ['Bulk transfer not implemented']
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Bulk transfer failed: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def manual_transfer_student(request):
    """
    Manually transfer a specific student to main academic tables
    """
    try:
        data = json.loads(request.body)
        student_id = data.get('studentId')
        
        if not student_id:
            return JsonResponse({
                'success': False,
                'message': 'Student ID is required'
            }, status=400)
        
        try:
            student = StudentBatchUpload.objects.get(id=student_id)
        except StudentBatchUpload.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Student not found'
            }, status=404)
        
        if student.reported_status != 'REPORTED':
            return JsonResponse({
                'success': False,
                'message': 'Student must have REPORTED status to be transferred'
            }, status=400)
        
        if student.user:
            return JsonResponse({
                'success': False,
                'message': 'Student already transferred to main tables'
            }, status=400)
        
        # Manual transfer not yet implemented - use status update API instead
        return JsonResponse({
            'success': False,
            'message': 'Manual transfer not yet implemented. Use the status update API to change student status to REPORTED for automatic transfer.',
            'data': {
                'student_id': student.id,
                'roll_number': student.roll_number,
                'suggestion': 'Use /programme_curriculum/api/update_student_status/ with status REPORTED'
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Transfer failed: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def check_transfer_status(request):
    """
    Check transfer status of students - how many are transferred vs pending
    """
    try:
        year = request.GET.get('year')
        
        queryset = StudentBatchUpload.objects.all()
        if year:
            queryset = queryset.filter(year=year)
        
        stats = {
            'total_students': queryset.count(),
            'reported_students': queryset.filter(reported_status='REPORTED').count(),
            'not_reported_students': queryset.filter(reported_status='NOT_REPORTED').count(),
            'transferred_students': queryset.filter(reported_status='REPORTED', user__isnull=False).count(),
            'pending_transfer': queryset.filter(reported_status='REPORTED', user__isnull=True).count(),
        }
        
        return JsonResponse({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to get transfer status: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_batch_students(request, batch_id):
    """
    Get students for a specific batch - ONLY from StudentBatchUpload table
    This is the primary source for upcoming batches admin management.
    When students are marked as REPORTED, they get transferred to academic_information tables.
    URL: /programme_curriculum/api/batches/{batch_id}/students/
    """
    try:
        from applications.programme_curriculum.models import Batch

        try:
            batch = Batch.objects.get(id=batch_id)
        except Batch.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': f'Batch with ID {batch_id} not found'
            }, status=404)

        students = StudentBatchUpload.objects.filter(
            year=batch.year,
            branch__icontains=batch.discipline.name
        ).order_by('roll_number')

        upload_students = []
        for student in students:
            upload_students.append({
                'id': student.id,
                'name': student.name,
                'roll_number': student.roll_number,
                'institute_email': student.institute_email,
                'jee_app_no': student.jee_app_no,

                'father_name': student.father_name,
                'mother_name': getattr(student, 'mother_name', ''),
                'gender': getattr(student, 'gender', ''),
                'category': student.category,
                'pwd': getattr(student, 'pwd', ''),
                'minority': getattr(student, 'minority', 'Not Applicable'),
                'date_of_birth': student.date_of_birth.isoformat() if student.date_of_birth else '',

                'phone_number': getattr(student, 'phone_number', ''),
                'personal_email': getattr(student, 'personal_email', ''),
                'address': getattr(student, 'address', ''),
                'state': getattr(student, 'state', ''),

                'branch': student.branch,
                'ai_rank': getattr(student, 'ai_rank', None),
                'category_rank': getattr(student, 'category_rank', None),
                'tenth_marks': getattr(student, 'tenth_marks', None),
                'twelfth_marks': getattr(student, 'twelfth_marks', None),

                'father_occupation': getattr(student, 'father_occupation', ''),
                'father_mobile': getattr(student, 'father_mobile', ''),
                'mother_occupation': getattr(student, 'mother_occupation', ''),
                'mother_mobile': getattr(student, 'mother_mobile', ''),
                'aadhar_number': getattr(student, 'aadhar_number', ''),

                'allotted_category': getattr(student, 'allotted_category', ''),
                'allotted_gender': getattr(student, 'allotted_gender', ''),

                'year': student.year,
                'academic_year': getattr(student, 'academic_year', ''),
                'programme_type': getattr(student, 'programme_type', ''),
                'allocation_status': getattr(student, 'allocation_status', ''),
                'reported_status': student.reported_status,
                'status_display': 'Reported' if student.reported_status == 'REPORTED' else 'Not Reported',
                'created_at': student.created_at.isoformat() if hasattr(student, 'created_at') else '',
                'updated_at': student.updated_at.isoformat() if hasattr(student, 'updated_at') else '',
                'source': getattr(student, 'source', 'unknown')  # Track actual source from model
            })
        
        response_data = {
            'success': True,
            'batch': {
                'id': batch.id,
                'name': batch.name,
                'discipline': batch.discipline.acronym,
                'year': batch.year,
                'curriculum': batch.curriculum.name if batch.curriculum else None
            },
            'students': upload_students, 
            'total_students': len(upload_students),
            'count': len(upload_students),

            'uploadStudents': upload_students, 
            'upload_students': upload_students,  
            'academicStudents': [],  
            'academic_students': [],  
            'combinedBeforeDedup': upload_students,
            'combined_before_dedup': upload_students,  
            'totalStudentsAfterDedup': len(upload_students), 
            'total_students_after_dedup': len(upload_students), 
            'totalCount': len(upload_students),  
            'total_count': len(upload_students), 

            'data': upload_students,
            'results': upload_students,
            'items': upload_students,
            'student_list': upload_students,
            'studentList': upload_students
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'message': f'Failed to fetch students: {str(e)}'
        }, status=500)


# =============================================================================
# BATCH SYNCHRONIZATION AND WORKFLOW ENFORCEMENT
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_batches_unified(request):
    """
    UNIFIED API for both 'Batches' tab and 'Upcoming Batches' tab
    Returns the same data structure for consistent frontend handling
    URL: /programme_curriculum/api/admin_batches/ 
    """
    try:
        from applications.programme_curriculum.models import Batch

        from applications.globals.models import ExtraInfo, HoldsDesignation
        user_details = ExtraInfo.objects.get(user=request.user)
        des = HoldsDesignation.objects.all().filter(user=request.user).first()

        if des and des.designation.name not in ['acadadmin', 'studentacadadmin']:
            return JsonResponse({
                'success': False,
                'message': 'Access denied. Only academic admins can view batch data.',
                'batches': []
            }, status=403)

        all_batches = Batch.objects.filter(running_batch=True).select_related(
            'discipline', 'curriculum'
        ).order_by('-year', 'discipline__name')
        
        unified_batches = []
        
        for batch in all_batches:
            # Use centralized filled seats calculation function
            actual_filled = calculate_batch_filled_seats(batch)

            if hasattr(batch, 'total_seats') and batch.total_seats:
                total_seats = batch.total_seats
            else:
                default_seats = {
                    'CSE': 300,
                    'ECE': 120, 
                    'ME': 120,
                    'SM': 60,
                    'Des.': 80,
                    'Design': 80
                }
                total_seats = default_seats.get(batch.discipline.acronym, 100)
                if hasattr(batch, 'total_seats'):
                    batch.total_seats = total_seats
                    batch.save()
            
            available_seats = max(0, total_seats - actual_filled)

            students_data = []
            if request.GET.get('include_students') == 'true':
                try:
                    students = StudentBatchUpload.objects.filter(
                        year=batch.year,
                        branch__icontains=batch.discipline.name
                    ).order_by('roll_number')
                    
                    for student in students:
                        students_data.append({
                            'id': student.id,
                            'name': student.name,
                            'roll_number': student.roll_number,
                            'institute_email': student.institute_email,
                            'reported_status': student.reported_status,
                            'status_display': 'Reported' if student.reported_status == 'REPORTED' else 'Not Reported'
                        })
                except Exception as e:
                    students_data = []

            unified_batch = {
                'id': batch.id,
                'name': batch.name,  
                'programme': batch.name, 

                'discipline': batch.discipline.acronym,  
                'disciplineName': batch.discipline.name, 
                'disciplineId': batch.discipline.id,

                'year': batch.year,
                'batchYear': batch.year,
                'academicYear': f"{batch.year}-{str(batch.year + 1)[-2:]}",

                'curriculum': batch.curriculum.name if batch.curriculum else None,
                'curriculumId': batch.curriculum.id if batch.curriculum else None,
                'curriculum_id': batch.curriculum.id if batch.curriculum else None, 
                'curriculumVersion': batch.curriculum.version if batch.curriculum else None,  
                'hasCurriculum': batch.curriculum is not None,

                'totalSeats': total_seats,
                'total_seats': total_seats,
                'filledSeats': actual_filled // 2,
                'filled_seats': actual_filled,  
                'availableSeats': available_seats,
                'available_seats': available_seats,  
                'student_count': actual_filled // 2, 

                'running_batch': batch.running_batch,
                'status': 'READY' if batch.curriculum else 'NEEDS_CURRICULUM',
                'canAcceptStudents': batch.curriculum is not None,

                'students': students_data,
                'studentCount': len(students_data),

                'displayBranch': batch.discipline.acronym,
                'fullDisciplineName': batch.discipline.name,
            }
            
            unified_batches.append(unified_batch)

        if request.GET.get('format') == 'nested':
            ug_batches = [b for b in unified_batches if b['name'].startswith('B.')]
            pg_batches = [b for b in unified_batches if b['name'].startswith('M.')]
            phd_batches = [b for b in unified_batches if b['name'] == 'PhD']
            
            return JsonResponse({
                'success': True,
                'data': {
                    'ug': ug_batches,
                    'pg': pg_batches,
                    'phd': phd_batches
                },
                'batches': unified_batches,
                'message': 'Batch data fetched successfully'
            })

        response_data = {
            'success': True,
            'batches': unified_batches,
            'total_batches': len(unified_batches),
            'message': 'Unified batch data fetched successfully'
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        import traceback
        
        return JsonResponse({
            'success': False,
            'message': f'Failed to fetch batch data: {str(e)}',
            'batches': [],
            'error_details': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def sync_batch_data(request):
    """
    Sync total seats and curriculum between 'Batches' tab and 'Upcoming Batches' tab
    URL: /programme_curriculum/api/batches/sync/
    """
    try:
        from applications.programme_curriculum.models import Batch
        from applications.academic_information.models import Student

        all_batches = Batch.objects.filter(running_batch=True).select_related(
            'discipline', 'curriculum'
        ).order_by('year', 'discipline__name')
        
        sync_results = []
        
        for batch in all_batches:
            # Use centralized filled seats calculation function
            actual_filled = calculate_batch_filled_seats(batch)

            if hasattr(batch, 'total_seats') and batch.total_seats:
                available_seats = max(0, batch.total_seats - actual_filled)
            else:

                default_seats = {
                    'CSE': 300,
                    'ECE': 120, 
                    'ME': 80,
                    'SM': 80,
                    'Des.': 80,
                }
                batch.total_seats = default_seats.get(batch.discipline.acronym, 100)
                batch.save()
                available_seats = max(0, batch.total_seats - actual_filled)
            
            sync_results.append({
                'batch_id': batch.id,
                'name': batch.name,
                'discipline': batch.discipline.acronym,
                'discipline_name': batch.discipline.name,
                'year': batch.year,
                'total_seats': batch.total_seats,
                'filled_seats': actual_filled,
                'available_seats': available_seats,
                'curriculum': batch.curriculum.name if batch.curriculum else None,
                'curriculum_id': batch.curriculum.id if batch.curriculum else None,
                'status': 'READY' if batch.curriculum else 'NEEDS_CURRICULUM'
            })
        
        return JsonResponse({
            'success': True,
            'message': 'Batch data synchronized successfully',
            'batches': sync_results,
            'total_batches': len(sync_results)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to sync batch data: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def validate_batch_prerequisites(request):
    """
    Validate that required batches exist before allowing student upload
    Enforces workflow: Batches must be created first, then students added
    URL: /programme_curriculum/api/batches/validate_prerequisites/
    """
    try:
        data = json.loads(request.body)
        academic_year = data.get('academic_year')  # e.g., 2025
        
        if not academic_year:
            return JsonResponse({
                'success': False,
                'message': 'Academic year is required'
            }, status=400)
        
        from applications.programme_curriculum.models import Batch, Discipline

        required_disciplines = ['Computer Science and Engineering', 'Electronics and Communication Engineering', 
                               'Mechanical Engineering', 'Smart Manufacturing', 'Design']
        
        missing_batches = []
        existing_batches = []
        
        for discipline_name in required_disciplines:
            try:
                discipline = Discipline.objects.filter(name=discipline_name).first()
                if discipline:
                    batch = Batch.objects.filter(
                        year=academic_year,
                        discipline=discipline,
                        running_batch=True
                    ).first()
                    
                    if batch:
                        existing_batches.append({
                            'discipline': discipline.name,
                            'acronym': discipline.acronym,
                            'batch_id': batch.id,
                            'curriculum_assigned': batch.curriculum is not None,
                            'curriculum_name': batch.curriculum.name if batch.curriculum else None,
                            'total_seats': getattr(batch, 'total_seats', 0)
                        })
                    else:
                        missing_batches.append({
                            'discipline': discipline.name,
                            'acronym': discipline.acronym,
                            'action_required': f'Create {discipline.acronym} batch for year {academic_year}'
                        })
            except Exception as e:
                pass

        can_upload_students = len(missing_batches) == 0
        
        return JsonResponse({
            'success': True,
            'can_upload_students': can_upload_students,
            'academic_year': academic_year,
            'existing_batches': existing_batches,
            'missing_batches': missing_batches,
            'message': 'All required batches exist' if can_upload_students else 'Some batches are missing',
            'workflow_status': 'READY' if can_upload_students else 'BATCHES_REQUIRED'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to validate prerequisites: {str(e)}'
        }, status=500)


# =============================================================================
# BATCH CURRICULUM STATUS CHECK
# =============================================================================

@csrf_exempt
@require_http_methods(["GET"])
def check_batches_curriculum_status(request):
    """
    Check curriculum assignment status for all batches
    Helps admins identify which batches need curriculum assignment
    URL: /programme_curriculum/api/batches/curriculum_status/
    """
    try:
        from applications.programme_curriculum.models import Batch

        batches = Batch.objects.filter(running_batch=True).select_related(
            'discipline', 'curriculum'
        ).order_by('-year', 'discipline__name')
        
        batch_status = []
        
        for batch in batches:
            student_count = StudentBatchUpload.objects.filter(
                year=batch.year,
                branch__icontains=batch.discipline.name
            ).count()

            reported_students = StudentBatchUpload.objects.filter(
                year=batch.year,
                branch__icontains=batch.discipline.name,
                reported_status='REPORTED'
            ).count()
            
            batch_info = {
                'batch_id': batch.id,
                'batch_name': batch.name,
                'discipline': batch.discipline.name,
                'discipline_acronym': batch.discipline.acronym,
                'year': batch.year,
                'total_seats': batch.total_seats,
                'student_count': student_count,
                'reported_students': reported_students,
                'has_curriculum': batch.curriculum is not None,
                'curriculum_name': batch.curriculum.name if batch.curriculum else None,
                'curriculum_id': batch.curriculum.id if batch.curriculum else None,
                'status': 'READY' if batch.curriculum else 'NEEDS_CURRICULUM',
                'warning': None if batch.curriculum else 'Curriculum assignment required before student upload/entry'
            }
            
            batch_status.append(batch_info)
        
        # Summary statistics
        summary = {
            'total_batches': len(batch_status),
            'batches_with_curriculum': len([b for b in batch_status if b['has_curriculum']]),
            'batches_without_curriculum': len([b for b in batch_status if not b['has_curriculum']]),
            'total_students': sum(b['student_count'] for b in batch_status),
            'reported_students': sum(b['reported_students'] for b in batch_status)
        }
        
        return JsonResponse({
            'success': True,
            'data': {
                'summary': summary,
                'batches': batch_status
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to check batch curriculum status: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def validate_student_upload_prerequisites(request):
    """
    Validate if all prerequisites are met for student data upload
    URL: /programme_curriculum/api/validate_student_upload_prerequisites/
    """
    try:
        academic_year_param = request.GET.get('academic_year')
        if academic_year_param:
            try:
                batch_year, academic_year = normalize_year_input(academic_year_param)
            except ValueError as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Invalid year format: {str(e)}'
                }, status=400)
        else:
            batch_year, academic_year = get_current_academic_year()
        
        from applications.programme_curriculum.models import Curriculum, Batch

        available_curriculums = Curriculum.objects.filter(working_curriculum=True)
        curriculum_check = {
            'exists': available_curriculums.exists(),
            'count': available_curriculums.count(),
            'status': 'PASS' if available_curriculums.exists() else 'FAIL',
            'message': f'Found {available_curriculums.count()} working curriculums' if available_curriculums.exists() 
                      else 'No working curriculums found - please create curriculums first'
        }

        existing_batches = Batch.objects.filter(year=batch_year, running_batch=True)
        batch_check = {
            'exists': existing_batches.exists(),
            'count': existing_batches.count(),
            'year': batch_year,
            'academic_year': academic_year,
            'status': 'PASS' if existing_batches.exists() else 'FAIL',
            'message': f'Found {existing_batches.count()} active batches for {academic_year}' if existing_batches.exists()
                      else f'No active batches found for {academic_year} - please create batches first'
        }

        batches_with_curriculum = existing_batches.filter(curriculum__isnull=False)
        batches_without_curriculum = existing_batches.filter(curriculum__isnull=True)
        
        curriculum_assignment_check = {
            'all_assigned': not batches_without_curriculum.exists(),
            'assigned_count': batches_with_curriculum.count(),
            'unassigned_count': batches_without_curriculum.count(),
            'status': 'PASS' if not batches_without_curriculum.exists() else 'FAIL',
            'message': f'All {batches_with_curriculum.count()} batches have curriculums assigned' if not batches_without_curriculum.exists()
                      else f'{batches_without_curriculum.count()} batches need curriculum assignment',
            'unassigned_batches': [f"{batch.name} {batch.discipline.acronym}" for batch in batches_without_curriculum]
        }
  
        overall_status = 'PASS' if (curriculum_check['status'] == 'PASS' and 
                                   batch_check['status'] == 'PASS' and 
                                   curriculum_assignment_check['status'] == 'PASS') else 'FAIL'
        
        validation_result = {
            'overall_status': overall_status,
            'can_upload_students': overall_status == 'PASS',
            'academic_year': academic_year,
            'batch_year': batch_year,
            'checks': {
                'curriculum_exists': curriculum_check,
                'batches_exist': batch_check,
                'curriculums_assigned': curriculum_assignment_check
            },
            'requirements': {
                'step_1': 'Create working curriculums',
                'step_2': 'Create batches for the academic year',
                'step_3': 'Assign curriculums to all batches',
                'step_4': 'Upload/enter student data'
            }
        }
        
        return JsonResponse({
            'success': True,
            'data': validation_result
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to validate prerequisites: {str(e)}'
        }, status=500)


# =============================================================================
# CURRICULUM REDUNDANCY CLEANUP UTILITIES
# =============================================================================

@csrf_exempt
@require_http_methods(["GET"])
def find_duplicate_curriculums(request):
    """
    Find duplicate curriculums that have the same name and programme
    URL: /programme_curriculum/api/find_duplicate_curriculums/
    """
    try:
        from applications.programme_curriculum.models import Curriculum
        from django.db.models import Count

        duplicates = (Curriculum.objects
                     .values('name', 'programme__name', 'programme__id')
                     .annotate(count=Count('id'))
                     .filter(count__gt=1, working_curriculum=True)
                     .order_by('name'))
        
        duplicate_details = []
        for dup in duplicates:
            curriculum_name = dup['name']
            programme_name = dup['programme__name']
            programme_id = dup['programme__id']
            count = dup['count']

            curricula = Curriculum.objects.filter(
                name=curriculum_name,
                programme__id=programme_id,
                working_curriculum=True
            ).order_by('version')
            
            curriculum_list = []
            for curr in curricula:
                batch_count = curr.batches.count()
                curriculum_list.append({
                    'id': curr.id,
                    'version': str(curr.version),
                    'latest_version': curr.latest_version,
                    'batch_count': batch_count,
                    'created_date': curr.id 
                })
            
            duplicate_details.append({
                'curriculum_name': curriculum_name,
                'programme_name': programme_name,
                'programme_id': programme_id,
                'duplicate_count': count,
                'curricula': curriculum_list
            })
        
        return JsonResponse({
            'success': True,
            'total_duplicate_groups': len(duplicate_details),
            'duplicates': duplicate_details
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to find duplicate curriculums: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def consolidate_duplicate_curriculums(request):
    """
    Consolidate duplicate curriculums by keeping the latest version and reassigning batches
    URL: /programme_curriculum/api/consolidate_duplicate_curriculums/
    """
    try:
        data = json.loads(request.body)
        curriculum_name = data.get('curriculum_name')
        programme_id = data.get('programme_id')
        keep_curriculum_id = data.get('keep_curriculum_id')
        
        if not all([curriculum_name, programme_id, keep_curriculum_id]):
            return JsonResponse({
                'success': False,
                'message': 'Missing required fields: curriculum_name, programme_id, keep_curriculum_id'
            }, status=400)
        
        from applications.programme_curriculum.models import Curriculum, Batch

        try:
            keep_curriculum = Curriculum.objects.get(id=keep_curriculum_id)
        except Curriculum.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': f'Curriculum with ID {keep_curriculum_id} not found'
            }, status=400)

        duplicate_curriculums = Curriculum.objects.filter(
            name=curriculum_name,
            programme__id=programme_id,
            working_curriculum=True
        ).exclude(id=keep_curriculum_id)

        reassigned_batches = 0
        for dup_curriculum in duplicate_curriculums:
            batches = dup_curriculum.batches.all()
            for batch in batches:
                batch.curriculum = keep_curriculum
                batch.save()
                reassigned_batches += 1

        duplicate_count = duplicate_curriculums.count()
        duplicate_curriculums.update(working_curriculum=False, latest_version=False)

        keep_curriculum.latest_version = True
        keep_curriculum.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Consolidated {duplicate_count} duplicate curriculums. Reassigned {reassigned_batches} batches to "{keep_curriculum.name} v{keep_curriculum.version}".',
            'kept_curriculum': {
                'id': keep_curriculum.id,
                'name': keep_curriculum.name,
                'version': str(keep_curriculum.version)
            },
            'removed_duplicates': duplicate_count,
            'reassigned_batches': reassigned_batches
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to consolidate curriculums: {str(e)}'
        }, status=500)


# =============================================================================
# BATCH REDUNDANCY CLEANUP UTILITIES
# =============================================================================

@csrf_exempt
@require_http_methods(["GET"])
def find_duplicate_batches(request):
    """
    Find duplicate batches that have the same programme+discipline+year combination
    URL: /programme_curriculum/api/find_duplicate_batches/
    """
    try:
        from applications.programme_curriculum.models import Batch
        from django.db.models import Count

        duplicates = (Batch.objects
                     .values('name', 'discipline__name', 'discipline__acronym', 'discipline__id', 'year')
                     .annotate(count=Count('id'))
                     .filter(count__gt=1, running_batch=True)
                     .order_by('year', 'discipline__name'))
        
        duplicate_details = []
        for dup in duplicates:
            programme_name = dup['name']
            discipline_name = dup['discipline__name']
            discipline_acronym = dup['discipline__acronym']
            discipline_id = dup['discipline__id']
            year = dup['year']
            count = dup['count']

            batches = Batch.objects.filter(
                name=programme_name,
                discipline__id=discipline_id,
                year=year,
                running_batch=True
            ).order_by('id')
            
            batch_list = []
            for batch in batches:
                try:
                    student_count = StudentBatchUpload.objects.filter(
                        year=batch.year,
                        branch__icontains=batch.discipline.name
                    ).count()
                except:
                    student_count = 0
                
                batch_list.append({
                    'id': batch.id,
                    'total_seats': batch.total_seats,
                    'student_count': student_count,
                    'curriculum': batch.curriculum.name if batch.curriculum else None,
                    'curriculum_id': batch.curriculum.id if batch.curriculum else None,
                    'created_order': batch.id 
                })
            
            duplicate_details.append({
                'programme_name': programme_name,
                'discipline_name': discipline_name,
                'discipline_acronym': discipline_acronym,
                'discipline_id': discipline_id,
                'year': year,
                'duplicate_count': count,
                'batches': batch_list
            })
        
        return JsonResponse({
            'success': True,
            'total_duplicate_groups': len(duplicate_details),
            'duplicates': duplicate_details
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to find duplicate batches: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def consolidate_duplicate_batches(request):
    """
    Consolidate duplicate batches by keeping one and reassigning students/data
    URL: /programme_curriculum/api/consolidate_duplicate_batches/
    """
    try:
        data = json.loads(request.body)
        programme_name = data.get('programme_name')
        discipline_id = data.get('discipline_id')
        year = data.get('year')
        keep_batch_id = data.get('keep_batch_id')
        
        if not all([programme_name, discipline_id, year, keep_batch_id]):
            return JsonResponse({
                'success': False,
                'message': 'Missing required fields: programme_name, discipline_id, year, keep_batch_id'
            }, status=400)
        
        from applications.programme_curriculum.models import Batch

        try:
            keep_batch = Batch.objects.get(id=keep_batch_id)
        except Batch.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': f'Batch with ID {keep_batch_id} not found'
            }, status=400)

        duplicate_batches = Batch.objects.filter(
            name=programme_name,
            discipline__id=discipline_id,
            year=year,
            running_batch=True
        ).exclude(id=keep_batch_id)

        reassigned_students = 0
        total_seats_added = 0
        
        for dup_batch in duplicate_batches:
            if dup_batch.total_seats > 0:
                keep_batch.total_seats += dup_batch.total_seats
                total_seats_added += dup_batch.total_seats

            if dup_batch.curriculum and not keep_batch.curriculum:
                keep_batch.curriculum = dup_batch.curriculum

            try:
                from applications.academic_information.models import Student
                students = Student.objects.filter(batch_id=dup_batch)
                for student in students:
                    student.batch_id = keep_batch
                    student.save()
                    reassigned_students += 1
            except:
                pass 
        
        keep_batch.save()

        duplicate_count = duplicate_batches.count()
        duplicate_batches.update(running_batch=False)
        
        return JsonResponse({
            'success': True,
            'message': f'Consolidated {duplicate_count} duplicate batches into "{keep_batch.name} {keep_batch.discipline.acronym} {keep_batch.year}". Added {total_seats_added} seats, reassigned {reassigned_students} students.',
            'kept_batch': {
                'id': keep_batch.id,
                'name': keep_batch.name,
                'discipline': keep_batch.discipline.acronym,
                'year': keep_batch.year,
                'total_seats': keep_batch.total_seats,
                'curriculum': keep_batch.curriculum.name if keep_batch.curriculum else None
            },
            'removed_duplicates': duplicate_count,
            'total_seats_added': total_seats_added,
            'reassigned_students': reassigned_students
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to consolidate batches: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def fix_stuck_reported_students(request):
    """
    Fix students that are stuck in REPORTED status and should be transferred to academic system
    """
    try:
        stuck_students = StudentBatchUpload.objects.filter(
            reported_status='REPORTED'
        ).exclude(
            Q(first_name__isnull=True) | Q(first_name='') |
            Q(last_name__isnull=True) | Q(last_name='') |
            Q(roll_number__isnull=True) | Q(roll_number='')
        )
        
        if not stuck_students.exists():
            return JsonResponse({
                'success': True,
                'message': 'No stuck students found',
                'data': {
                    'total_stuck': 0,
                    'fixed_count': 0,
                    'error_count': 0,
                    'errors': []
                }
            })
        
        fixed_count = 0
        errors = []
        
        with transaction.atomic():
            for student in stuck_students:
                try:
                    # Transfer student to academic system
                    transfer_result = transfer_student_to_academic_system(student)
                    
                    if transfer_result.get('success'):
                        # Update status to transferred
                        student.reported_status = 'TRANSFERRED'
                        student.save()
                        fixed_count += 1
                    else:
                        errors.append(f"Student {student.first_name} {student.last_name} ({student.roll_number}): {transfer_result.get('message', 'Unknown error')}")
                        
                except Exception as e:
                    errors.append(f"Student {student.first_name} {student.last_name} ({student.roll_number}): {str(e)}")
        
        return JsonResponse({
            'success': True,
            'message': f'Fixed {fixed_count} stuck students',
            'data': {
                'total_stuck': stuck_students.count(),
                'fixed_count': fixed_count,
                'error_count': len(errors),
                'errors': errors[:10]
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to fix stuck students: {str(e)}'
        }, status=500)


def transfer_student_to_academic_system(student):
    """
    Transfer a student from StudentBatchUpload to the academic_information.Student table
    This function handles the complete transfer process including User and ExtraInfo creation
    """
    try:
        from applications.academic_information.models import Student as AcademicStudent
        from applications.globals.models import ExtraInfo, Designation, HoldsDesignation
        from django.contrib.auth.models import User

        existing_academic_student = AcademicStudent.objects.filter(
            id__id=student.roll_number
        ).first()
        
        if existing_academic_student:
            return {
                'success': True,
                'message': 'Student already exists in academic system',
                'user_id': existing_academic_student.id.user.id,
                'extra_info_id': existing_academic_student.id.id,
                'academic_student_id': existing_academic_student.id.id
            }

        existing_user = User.objects.filter(username=student.roll_number).first()
        
        if existing_user:
            user = existing_user
        else:
            user = User.objects.create_user(
                username=student.roll_number,
                email=student.institute_email,
                first_name=student.first_name,
                last_name=student.last_name,
                password=student.password if student.password else 'changeme123'
            )

        existing_extra_info = ExtraInfo.objects.filter(id=student.roll_number).first()
        
        if existing_extra_info:
            extra_info = existing_extra_info
        else:
            extra_info = ExtraInfo.objects.create(
                id=student.roll_number,
                user=user,
                title='Mr' if student.gender == 'M' else 'Ms',
                sex='M' if student.gender == 'M' else 'F',
                date_of_birth=student.date_of_birth,
                user_type='student',
                address=student.permanent_address or '',
                phone_no=student.phone_number or '',
                department=student.batch.discipline if student.batch else None,
                profile_picture=None
            )

        academic_student = AcademicStudent.objects.create(
            id=extra_info,
            programme=student.programme,
            discipline=student.batch.discipline if student.batch else None,
            batch=student.batch,
            current_semester=calculate_current_semester(student.academic_year),
            current_year=student.academic_year,
            cpi=0.0,
            category=student.category or 'General',
            father_name=student.father_name or '',
            mother_name=student.mother_name or '',
            hall_no=0,
            room_no='',
            specialization=student.specialization or ''
        )

        student_designation = Designation.objects.filter(name='student').first()
        if student_designation:
            holds_designation, created = HoldsDesignation.objects.get_or_create(
                user=user,
                designation=student_designation,
                defaults={'working': user}
            )
        
        return {
            'success': True,
            'message': 'Student transferred successfully',
            'user_id': user.id,
            'extra_info_id': extra_info.id,
            'academic_student_id': academic_student.id.id
        }
        
    except Exception as e:
        import traceback
        return {
            'success': False,
            'message': f'Transfer failed: {str(e)}'
        }


@csrf_exempt
@require_http_methods(["POST"])
def sync_batches_to_configuration(request):
    """
    Sync batches from Batch model to BatchConfiguration model
    This ensures that all batches are available in the BatchConfiguration model
    """
    try:
        from applications.programme_curriculum.models import Batch
        
        synced_count = 0
        created_count = 0
        updated_count = 0
        
        for batch in Batch.objects.all():
            # Check if BatchConfiguration already exists with this ID
            try:
                batch_config = BatchConfiguration.objects.get(id=batch.id)
                # Update existing
                batch_config.programme = batch.name
                batch_config.discipline = batch.discipline.name if batch.discipline else "Unknown"
                batch_config.year = batch.year
                batch_config.total_seats = batch.total_seats
                batch_config.save()
                updated_count += 1
                
            except BatchConfiguration.DoesNotExist:
                # Create new
                batch_config = BatchConfiguration.objects.create(
                    programme=batch.name,
                    discipline=batch.discipline.name if batch.discipline else "Unknown",
                    year=batch.year,
                    total_seats=batch.total_seats
                )
                # Force the same ID to maintain consistency
                batch_config.id = batch.id
                batch_config.save()
                created_count += 1
            
            synced_count += 1
        
        return JsonResponse({
            'success': True,
            'message': f'Synced {synced_count} batches. Created: {created_count}, Updated: {updated_count}',
            'stats': {
                'total_synced': synced_count,
                'created': created_count,
                'updated': updated_count
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Sync failed: {str(e)}'
        }, status=500)
