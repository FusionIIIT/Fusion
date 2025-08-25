# Student Management Views for Programme Curriculum API
# Implements all the endpoints defined in urls.py

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

# Import academic_information models
from applications.academic_information.models import Student as AcademicStudent
from applications.globals.models import ExtraInfo, Designation, HoldsDesignation
from django.contrib.auth.models import User
from applications.programme_curriculum.models import (
    Programme, Curriculum, Batch, Discipline
)

# Email functionality - Import from existing password email system
from applications.programme_curriculum.views_password_email import send_password_email_smtp
from applications.programme_curriculum.models_password_email import PasswordEmailLog

# Create StudentBatchUpload model if it doesn't exist
# This model should be created in your models.py file
try:
    from applications.programme_curriculum.models_student_management import (
        StudentBatchUpload, BatchConfiguration, StudentStatusLog
    )
except ImportError:
    # Temporary model structure for development
    from django.db import models
    from django.contrib.auth.models import User
    
    # If models don't exist, you'll need to create them in models_student_management.py
    pass

def calculate_current_semester(academic_year, current_date=None):
    """
    Calculate the current semester for a student based on their academic year and current date.
    
    Academic Calendar:
    - August to December = Semester 1 (Odd)
    - January to May = Semester 2 (Even) 
    - June to July = Summer/Break (use previous semester)
    
    Args:
        academic_year: Student's academic year (e.g., 2025 for 2025-26 batch)
        current_date: Date to calculate semester for (defaults to today)
    
    Returns:
        int: Current semester number (1-8)
    """
    if current_date is None:
        current_date = timezone.now().date()
    
    current_year = current_date.year
    current_month = current_date.month
    
    # Calculate how many years the student has been studying
    years_completed = 0
    
    if current_month >= 8:  # August onwards
        # We're in the academic year that started this calendar year
        years_completed = current_year - academic_year
        semester_in_year = 1  # First semester of the academic year
    else:  # January to July
        # We're in the academic year that started last calendar year
        years_completed = current_year - academic_year - 1
        if current_month <= 5:  # January to May
            semester_in_year = 2  # Second semester of the academic year
        else:  # June to July (summer break)
            semester_in_year = 2  # Still count as semester 2
    
    # Calculate total semester number
    total_semester = (years_completed * 2) + semester_in_year
    
    # Ensure semester is within valid range (1-8 for undergraduate)
    total_semester = max(1, min(total_semester, 8))
    
    return total_semester

# =============================================================================
# BATCH OVERVIEW AND MANAGEMENT
# =============================================================================

@csrf_exempt
@require_http_methods(["GET"])
def admin_batches_overview(request):
    """
    Fetch batch overview data for admin dashboard
    URL: /programme_curriculum/api/admin_batches_overview/
    """
    try:
        current_year = datetime.now().year
        
        # Calculate academic year (academic year 2025-26 means year 2025)
        if datetime.now().month >= 7:  # July onwards is new academic year
            batch_year = current_year  # 2025-26 academic year = 2025
        else:
            batch_year = current_year - 1  # Before July, still in previous academic year
        
        # Get or create batch configurations for current academic year
        try:
            # Try to get existing batch configurations
            batch_configs = BatchConfiguration.objects.filter(year=batch_year)
            
            if not batch_configs.exists():
                # Create default batch configurations if none exist
                default_disciplines = [
                    ('Computer Science and Engineering', 'ug', 120),
                    ('Electronics and Communication Engineering', 'ug', 120),
                    ('Mechanical Engineering', 'ug', 120),
                    ('Smart Manufacturing', 'ug', 60),
                    ('Design', 'ug', 30),
                    ('Computer Science and Engineering', 'pg', 30),
                    ('Electronics and Communication Engineering', 'pg', 30),
                    ('Mechanical Engineering', 'pg', 30),
                    ('Smart Manufacturing', 'pg', 20),
                    ('Design', 'pg', 15),
                    ('Computer Science and Engineering', 'phd', 10),
                    ('Electronics and Communication Engineering', 'phd', 10),
                    ('Mechanical Engineering', 'phd', 10),
                    ('Smart Manufacturing', 'phd', 5),
                    ('Design', 'phd', 5),
                ]
                
                for discipline, prog_type, seats in default_disciplines:
                    # Determine programme name based on type and discipline
                    if prog_type == 'ug':
                        programme = 'B.Des' if discipline == 'Design' else 'B.Tech'
                    elif prog_type == 'pg':
                        programme = 'M.Des' if discipline == 'Design' else 'M.Tech'
                    else:
                        programme = 'PhD'
                    
                    BatchConfiguration.objects.create(
                        programme=programme,
                        discipline=discipline,
                        year=batch_year,
                        total_seats=seats
                    )
            
            batch_configs = BatchConfiguration.objects.filter(year=batch_year)
        
        except Exception as e:
            # If BatchConfiguration model doesn't exist, create mock data
            batch_configs = []
        
        # Update seat calculations for all batches
        for config in batch_configs:
            config.calculate_seats()
        
        # Helper function to serialize batch configuration with students
        def serialize_batch(config):
            # Get student list for this batch using improved matching
            try:
                from django.db.models import Q
                
                # Create flexible discipline query
                discipline_q = Q()
                
                # Direct match
                discipline_q |= Q(branch__icontains=config.discipline)
                
                # Also try matching against normalized discipline names
                if config.discipline == 'Computer Science and Engineering':
                    discipline_q |= Q(branch__icontains='Computer Science') | Q(branch__icontains='CSE')
                elif config.discipline == 'Electronics and Communication Engineering':
                    discipline_q |= Q(branch__icontains='Electronics') | Q(branch__icontains='ECE')
                elif config.discipline == 'Mechanical Engineering':
                    discipline_q |= Q(branch__icontains='Mechanical') | Q(branch__icontains='ME')
                elif config.discipline == 'Smart Manufacturing':
                    discipline_q |= Q(branch__icontains='Smart Manufacturing') | Q(branch__icontains='SM')
                elif config.discipline == 'Design':
                    discipline_q |= Q(branch__icontains='Design') | Q(branch__icontains='Des')
                
                # Get students matching this batch configuration
                # Filter by discipline, year, AND programme type
                programme_type_filter = 'ug'  # Default
                if config.programme.startswith('M.'):
                    programme_type_filter = 'pg'
                elif config.programme == 'PhD':
                    programme_type_filter = 'phd'
                
                students = StudentBatchUpload.objects.filter(
                    discipline_q,
                    year=config.year,
                    programme_type=programme_type_filter  # Add programme type filter
                ).order_by('roll_number')
                
                # Serialize student data
                student_list = []
                for student in students:
                    # Format status for display
                    status_display = student.reported_status
                    if status_display == 'NOT_REPORTED':
                        status_display_human = 'Not Reported'
                    elif status_display == 'REPORTED':
                        status_display_human = 'Reported'
                    else:
                        status_display_human = status_display
                    
                    student_list.append({
                        # Core identification fields
                        'id': student.id,
                        'name': student.name,
                        'roll_number': student.roll_number,
                        'rollNumber': student.roll_number,
                        'institute_email': student.institute_email,
                        'instituteEmail': student.institute_email,
                        'jee_app_no': student.jee_app_no,
                        'jeeAppNo': student.jee_app_no,
                        
                        # Personal information fields
                        'father_name': student.father_name,
                        'fatherName': student.father_name,
                        'father': student.father_name,
                        'mother_name': getattr(student, 'mother_name', ''),
                        'motherName': getattr(student, 'mother_name', ''),
                        'gender': getattr(student, 'gender', ''),
                        'category': student.category,
                        'pwd': student.pwd,
                        'date_of_birth': getattr(student, 'date_of_birth', ''),
                        'dateOfBirth': str(getattr(student, 'date_of_birth', '')),
                        
                        # Contact information fields
                        'phone_number': getattr(student, 'phone_number', ''),
                        'phoneNumber': getattr(student, 'phone_number', ''),
                        'personal_email': getattr(student, 'personal_email', ''),
                        'personalEmail': getattr(student, 'personal_email', ''),
                        'address': getattr(student, 'address', ''),
                        'state': getattr(student, 'state', ''),
                        
                        # Family information fields
                        'father_occupation': getattr(student, 'father_occupation', ''),
                        'fatherOccupation': getattr(student, 'father_occupation', ''),
                        'father_mobile': getattr(student, 'father_mobile', ''),
                        'fatherMobile': getattr(student, 'father_mobile', ''),
                        'mother_occupation': getattr(student, 'mother_occupation', ''),
                        'motherOccupation': getattr(student, 'mother_occupation', ''),
                        'mother_mobile': getattr(student, 'mother_mobile', ''),
                        'motherMobile': getattr(student, 'mother_mobile', ''),
                        
                        # Academic fields
                        'branch': student.branch,
                        'ai_rank': getattr(student, 'ai_rank', None),
                        'aiRank': getattr(student, 'ai_rank', None),
                        'category_rank': getattr(student, 'category_rank', None),
                        'categoryRank': getattr(student, 'category_rank', None),
                        'tenth_marks': getattr(student, 'tenth_marks', None),
                        'tenthMarks': getattr(student, 'tenth_marks', None),
                        'twelfth_marks': getattr(student, 'twelfth_marks', None),
                        'twelfthMarks': getattr(student, 'twelfth_marks', None),
                        
                        # Allotment details
                        'allotted_category': getattr(student, 'allotted_category', ''),
                        'allottedCategory': getattr(student, 'allotted_category', ''),
                        'allotted_gender': getattr(student, 'allotted_gender', ''),
                        'allottedGender': getattr(student, 'allotted_gender', ''),
                        
                        # Additional fields
                        'aadhar_number': getattr(student, 'aadhar_number', ''),
                        'aadharNumber': getattr(student, 'aadhar_number', ''),
                        
                        # Status fields
                        'reported_status': student.reported_status,
                        'reportedStatus': student.reported_status,
                        'status': student.reported_status,
                        'status_display': status_display_human,
                        'statusDisplay': status_display_human,
                        
                        # System fields
                        'year': getattr(student, 'year', ''),
                        'programme_type': getattr(student, 'programme_type', ''),
                        'programmeType': getattr(student, 'programme_type', ''),
                        'created_at': str(getattr(student, 'created_at', '')),
                        'createdAt': str(getattr(student, 'created_at', '')),
                        'updated_at': str(getattr(student, 'updated_at', '')),
                        'updatedAt': str(getattr(student, 'updated_at', '')),
                    })
                
                # Calculate actual filled seats
                filled_seats = students.count()
                available_seats = max(0, config.total_seats - filled_seats)
                
                return {
                    'id': config.id,
                    'programme': config.programme,
                    'discipline': config.discipline,
                    'displayBranch': get_display_branch_name(config.discipline),
                    'year': config.year,
                    'totalSeats': config.total_seats,
                    'filledSeats': filled_seats,
                    'availableSeats': available_seats,
                    'students': student_list
                }
            except Exception as e:
                # Fallback for missing models
                return {
                    'id': getattr(config, 'id', 1),
                    'programme': getattr(config, 'programme', 'B.Tech'),
                    'discipline': getattr(config, 'discipline', 'Computer Science and Engineering'),
                    'displayBranch': 'CSE',
                    'year': batch_year,
                    'totalSeats': getattr(config, 'total_seats', 60),
                    'filledSeats': 0,
                    'availableSeats': getattr(config, 'total_seats', 60),
                    'students': []
                }
        
        # Group batches by programme type
        ug_batches = []
        pg_batches = []
        phd_batches = []
        
        for config in batch_configs:
            batch_data = serialize_batch(config)
            
            # Categorize by programme
            programme = batch_data['programme']
            if programme.startswith('B.'):  # All Bachelor's programmes (B.Tech, B.Des, B.Arch, etc.)
                ug_batches.append(batch_data)
            elif programme.startswith('M.'):  # All Master's programmes (M.Tech, M.Des, etc.)
                pg_batches.append(batch_data)
            elif programme == 'PhD':
                phd_batches.append(batch_data)
        
        return JsonResponse({
            'success': True,
            'data': {
                'ug': ug_batches,
                'pg': pg_batches,
                'phd': phd_batches
            },
            'message': 'Batch overview data fetched successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to fetch batch overview: {str(e)}'
        }, status=500)

def get_display_branch_name(discipline):
    """Helper function to get display branch name"""
    branch_mappings = {
        'Computer Science and Engineering': 'CSE',
        'Electronics and Communication Engineering': 'ECE',
        'Mechanical Engineering': 'ME',
        'Smart Manufacturing': 'SM',
        'Design': 'DES'
    }
    return branch_mappings.get(discipline, discipline)

# =============================================================================
# EXCEL PROCESSING
# =============================================================================

@csrf_exempt
@require_http_methods(["POST"])
def process_excel_upload(request):
    """
    Process Excel file upload for student data
    URL: /programme_curriculum/api/process_excel_upload/
    """
    try:
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'message': 'No file uploaded'
            }, status=400)
        
        file = request.FILES['file']
        programme_type = request.POST.get('programme_type', 'ug')
        
        # Validate file type
        if not file.name.endswith(('.xlsx', '.xls')):
            return JsonResponse({
                'success': False,
                'message': 'Invalid file format. Please upload an Excel file (.xlsx or .xls)'
            }, status=400)
        
        # Read Excel file
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
        
        # Process and validate data
        valid_students = []
        invalid_students = []
        
        # Column mapping based on the exact Excel format provided
        column_mapping = {
            'sno': ['sno', 's.no', 'serial number', 's no'],
            'jee_app_no': ['jee main application number', 'jee app. no.', 'jee application number', 'jee main app number'],
            'roll_number': ['institute roll number', 'roll number', 'rollno', 'inst roll number'],
            'name': ['name', 'student name', 'full name'],
            'discipline': ['discipline', 'branch', 'department'],
            'gender': ['gender', 'sex'],
            'category': ['category', 'caste'],
            'pwd': ['pwd', 'disability', 'pwb'],
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

        # Normalize column names
        df.columns = df.columns.str.lower().str.strip()

        # Map columns
        mapped_data = {}
        for field, possible_columns in column_mapping.items():
            for col in possible_columns:
                if col in df.columns:
                    mapped_data[field] = col
                    break
        
        # Process each row
        for index, row in df.iterrows():
            try:
                student_data = {}
                
                # Extract data using mapped columns
                for field, excel_col in mapped_data.items():
                    if excel_col in df.columns:
                        value = row[excel_col]
                        if pd.notna(value):
                            student_data[field] = str(value).strip()
                
                # Validate required fields based on your Excel structure
                required_fields = ['name', 'discipline', 'roll_number', 'institute_email']
                missing_fields = [field for field in required_fields if not student_data.get(field)]
                
                # Additional validation for specific fields
                errors = []
                
                # Validate gender
                if student_data.get('gender'):
                    gender = student_data['gender'].lower()
                    if gender not in ['male', 'female', 'other']:
                        errors.append(f'Invalid gender: {student_data["gender"]}')
                
                # Validate PWD field
                if student_data.get('pwd'):
                    pwd = student_data['pwd'].upper()
                    if pwd not in ['YES', 'NO']:
                        errors.append(f'Invalid PWD value: {student_data["pwd"]}')
                
                # Validate email format
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
                    # Clean and format data before adding to valid students
                    # Use field names that match frontend expectations
                    cleaned_data = {
                        'Sno': student_data.get('sno', ''),
                        'Jee Main Application Number': student_data.get('jee_app_no', ''),
                        'Institute Roll Number': student_data.get('roll_number', ''),
                        'Name': student_data.get('name', ''),
                        'Discipline': student_data.get('discipline', ''),
                        'Gender': student_data.get('gender', ''),
                        'Category': student_data.get('category', ''),
                        'PWD': student_data.get('pwd', ''),
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
    """
    Check if student already exists based on specified fields
    Returns: (is_duplicate: bool, duplicate_info: str)
    """
    # Map frontend camelCase to backend snake_case
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
            # Convert frontend field name to backend field name
            backend_field = field_mapping.get(field, field.lower())
            student_value = student.get(field)
            
            if not student_value:
                continue
                
            # Check for existing student with this field value
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
    """
    Save batch of students from Excel processing with duplicate filtering
    URL: /programme_curriculum/api/save_students_batch/
    """
    try:
        data = json.loads(request.body)
        students = data.get('students', [])
        programme_type = data.get('programme_type', 'ug')
        
        # New parameters for duplicate handling
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

        # Get current academic year (academic year 2025-26 means year 2025)
        current_year = datetime.now().year
        # Academic year calculation: if it's before July, we're still in previous academic year
        if datetime.now().month >= 7:  # July onwards is new academic year
            batch_year = current_year  # 2025-26 academic year = 2025
        else:
            batch_year = current_year - 1  # Before July, still in previous academic year
        
        # Process batch allocation (remove atomic transaction to allow individual student processing)
        processed_students = process_batch_allocation(students, programme_type)
        
        for student_data in processed_students:
            try:
                # Use individual atomic blocks for each student to prevent cascade failures
                with transaction.atomic():
                    # Handle both Title Case (from Excel) and camelCase (from frontend) field names
                    student_name = student_data.get('Name') or student_data.get('name', 'Unknown')
                    
                    # Basic validation - check both possible field names
                    name = (student_data.get('Name') or student_data.get('name', '')).strip()
                    if not name:
                        validation_errors += 1
                        errors.append(f"Student at row has no name - skipping")
                        continue
                    
                    # Parse date of birth if provided - handle both field name formats
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
                    
                    # Map discipline to batch name and get/create batch - handle both field name formats
                    discipline_name = student_data.get('Discipline') or student_data.get('branch', '')
                    
                    batch_name = get_batch_name_from_discipline(discipline_name, programme_type)
                    
                    # Get or create the discipline
                    discipline_obj = get_or_create_discipline(discipline_name)
                    
                    # Get or create the batch
                    batch_obj = get_or_create_batch(batch_name, discipline_obj, batch_year)
                    
                    # Create StudentBatchUpload record (for upload tracking)
                    # Handle both Title Case (from Excel) and camelCase (from frontend) field names
                    student_upload = StudentBatchUpload.objects.create(
                        # Core identification - handle both field name formats
                        jee_app_no=student_data.get('Jee Main Application Number') or student_data.get('jeeAppNo', ''),
                        roll_number=student_data.get('Institute Roll Number') or student_data.get('rollNumber', ''),
                        institute_email=student_data.get('Institute Email ID') or student_data.get('instituteEmail', ''),
                        
                        # Personal information - handle both field name formats
                        name=student_data.get('Name') or student_data.get('name', ''),
                        father_name=student_data.get("Father's Name") or student_data.get('fname', ''),
                        mother_name=student_data.get("Mother's Name") or student_data.get('mname', ''),
                        gender=student_data.get('Gender') or student_data.get('gender', ''),
                        category=student_data.get('Category') or student_data.get('category', ''),
                        pwd=student_data.get('PWD') or student_data.get('pwd', 'NO'),
                        
                        # Contact information - handle both field name formats
                        phone_number=student_data.get('Mobile No') or student_data.get('phoneNumber', ''),
                        personal_email=student_data.get('Alternet Email ID') or student_data.get('email', ''),
                        address=student_data.get('Full Address') or student_data.get('address', ''),
                        state=student_data.get('State') or student_data.get('state', ''),
                        
                        # Academic information - handle both field name formats
                        branch=student_data.get('Discipline') or student_data.get('branch', ''),
                        date_of_birth=dob,
                        ai_rank=int(str((student_data.get('AI rank') or student_data.get('jeeRank', 0))).replace(',', '')) if (student_data.get('AI rank') or student_data.get('jeeRank')) and str((student_data.get('AI rank') or student_data.get('jeeRank', 0))).replace(',', '').isdigit() else None,
                        category_rank=int(str((student_data.get('Category Rank') or student_data.get('categoryRank', 0))).replace(',', '')) if (student_data.get('Category Rank') or student_data.get('categoryRank')) and str((student_data.get('Category Rank') or student_data.get('categoryRank', 0))).replace(',', '').isdigit() else None,
                        
                        # Family information - handle both field name formats
                        father_occupation=student_data.get("Father's Occupation") or student_data.get('fatherOccupation', ''),
                        father_mobile=student_data.get('Father Mobile Number') or student_data.get('fatherMobile', ''),
                        mother_occupation=student_data.get("Mother's Occupation") or student_data.get('motherOccupation', ''),
                        mother_mobile=student_data.get('Mother Mobile Number') or student_data.get('motherMobile', ''),
                        
                        # Allotment details - handle both field name formats
                        allotted_category=student_data.get('allottedcat') or student_data.get('allottedCategory', ''),
                        allotted_gender=student_data.get('Allotted Gender') or student_data.get('allottedGender', ''),
                        
                        # System fields
                        year=batch_year,
                        academic_year=f"{batch_year}-{str(batch_year + 1)[-2:]}",  # e.g., "2025-26"
                        programme_type=programme_type,
                        reported_status='NOT_REPORTED',
                        uploaded_by=request.user if request.user.is_authenticated else None
                    )
                    
                    # ✅ AUTOMATIC USER ACCOUNT CREATION with HASHED PASSWORD
                    # Only create if student has roll number (means they're confirmed)
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
                    
                    # Also create/update main Student record if roll number exists
                    if student_data.get('Institute Roll Number'):
                        create_or_update_main_student_record(student_data, batch_obj, batch_year)
                    
                    successful_uploads += 1
                    
            except Exception as e:
                failed_uploads += 1
                error_msg = f"Failed to save student {student_name}: {str(e)}"
                errors.append(error_msg)
        
        # Enhanced response with duplicate information
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
        
        # Create appropriate message based on results
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

def process_batch_allocation(students, programme_type):
    """Process batch allocation algorithm"""
    current_year = datetime.now().year
    batch_year = current_year if datetime.now().month >= 7 else current_year - 1
    display_year = batch_year 
    
    # Group students by branch
    branch_groups = {}
    
    for student in students:
        # Use the correct field names from Excel processing
        branch_field = student.get('Discipline', '') or student.get('branch', '')
        branch_code = get_branch_code(branch_field, programme_type)
        
        if branch_code not in branch_groups:
            branch_groups[branch_code] = []
        
        branch_groups[branch_code].append({
            **student,
            'branch_code': branch_code,
            'display_branch': get_display_branch_name(branch_field)
        })
    
    # Sort students within each branch by name
    for branch_code in branch_groups:
        branch_groups[branch_code].sort(key=lambda x: x.get('Name', '') or x.get('name', ''))
    
    # Allocate roll numbers
    processed_students = []
    branch_counters = {}
    
    for branch_code, students_in_branch in branch_groups.items():
        # Auto-generation logic commented out - using provided values from Excel/manual entry
        # # Find the next available sequence number for this branch and year
        # from applications.programme_curriculum.models_student_management import StudentBatchUpload
        
        # # Get the year suffix for roll number pattern matching
        # year_suffix = str(batch_year)[-2:]
        
        # # Find the highest sequence number for this branch and year
        # existing_students = StudentBatchUpload.objects.filter(
        #     roll_number__startswith=f"{year_suffix}{branch_code}"
        # ).order_by('-roll_number')
        
        # # Start counter from next available number
        # if existing_students.exists():
        #     try:
        #         # Get the last roll number and extract sequence
        #         last_roll = existing_students.first().roll_number
        #         last_sequence = int(last_roll[-3:])  # Last 3 digits
        #         branch_counters[branch_code] = last_sequence + 1
        #     except (ValueError, IndexError):
        #         branch_counters[branch_code] = 1
        # else:
        #     branch_counters[branch_code] = 1
        
        for student in students_in_branch:
            # Auto-generation commented out - using provided values from Excel/manual entry
            # Password generation removed - will be generated when status changes to REPORTED
            # roll_number = generate_roll_number(branch_code, batch_year, branch_counters[branch_code])
            # institute_email = generate_institute_email(roll_number)
            
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
            
            # branch_counters[branch_code] += 1  # Not needed when not auto-generating
    
    # Sort by roll number
    processed_students.sort(key=lambda x: x['roll_number'])
    
    return processed_students

def get_branch_code(branch_name, programme_type):
    """Get branch code for roll number generation"""
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
    """Generate roll number"""
    year_suffix = str(year)[-2:]
    sequence_str = str(sequence).zfill(3)
    return f"{year_suffix}{branch_code}{sequence_str}"

def generate_institute_email(roll_number):
    """Generate institute email"""
    return f"{roll_number.lower()}@iiitdmj.ac.in"

def generate_password():
    """Generate random password"""
    import random
    import string
    charset = string.ascii_letters + string.digits + "!@#$%"
    return ''.join(random.choice(charset) for _ in range(8))

def get_allocation_summary(students, programme_type):
    """Get allocation summary"""
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
    """
    Add single student manually
    URL: /programme_curriculum/api/add_single_student/
    """
    try:
        data = json.loads(request.body)
        programme_type = data.get('programme_type', 'ug')
        
        # Map frontend field names to backend field names
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
        
        # Apply field mapping but preserve rollNumber and instituteEmail
        mapped_data = {}
        for key, value in data.items():
            # Use mapped field name if exists, otherwise use original
            mapped_key = field_mapping.get(key, key)
            mapped_data[mapped_key] = value
            
            # Also preserve the original rollNumber and instituteEmail for process_batch_allocation
            if key in ['rollNumber', 'instituteEmail']:
                mapped_data[key] = value  # Keep original name too
        
        # Replace original data with mapped data
        data = mapped_data
        
        # Validate required fields - core fields that must be provided
        required_fields = ['name', 'father_name', 'mother_name', 'jee_app_no', 'branch', 'gender', 'category', 'pwd', 'address']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return JsonResponse({
                'success': False,
                'message': f'Missing required fields: {", ".join(missing_fields)}'
            }, status=400)
        
        # Process single student through batch allocation
        processed_students = process_batch_allocation([data], programme_type)
        
        if not processed_students:
            return JsonResponse({
                'success': False,
                'message': 'Failed to process student data'
            }, status=400)
        
        student_data = processed_students[0]
        
        # Check for duplicates before creating student
        jee_app_no = data.get('jee_app_no')
        if jee_app_no:
            existing_student = StudentBatchUpload.objects.filter(jee_app_no=jee_app_no).first()
            if existing_student:
                return JsonResponse({
                    'success': False,
                    'message': f'Student with JEE Application Number {jee_app_no} already exists (Roll Number: {existing_student.roll_number})'
                }, status=400)
        
        # Parse date of birth if provided
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
                # Core identification fields
                name=student_data.get('name'),
                jee_app_no=student_data.get('jee_app_no'),
                roll_number=student_data.get('roll_number'),
                institute_email=student_data.get('institute_email'),
                
                # Personal information fields
                father_name=student_data.get('father_name'),
                mother_name=student_data.get('mother_name'),
                gender=student_data.get('gender'),
                category=student_data.get('category'),
                pwd=student_data.get('pwd'),
                date_of_birth=dob or data.get('date_of_birth'),
                
                # Contact information fields (ALL Excel fields)
                phone_number=data.get('phone_number', '') or data.get('MobileNo', ''),
                personal_email=data.get('personal_email', '') or data.get('Alternet Email ID', ''),
                address=student_data.get('address'),
                state=data.get('state', '') or data.get('State', ''),
                
                # Family information fields (ALL Excel fields)
                father_occupation=data.get('father_occupation', '') or data.get("Father's Occupation", ''),
                father_mobile=data.get('father_mobile', '') or data.get('Father Mobile Number', ''),
                mother_occupation=data.get('mother_occupation', '') or data.get("Mother's Occupation", ''),
                mother_mobile=data.get('mother_mobile', '') or data.get('Mother Mobile Number', ''),
                
                # Academic fields (ALL Excel fields)
                branch=student_data.get('branch'),
                ai_rank=data.get('ai_rank') or data.get('AI rank'),
                category_rank=data.get('category_rank') or data.get('Category Rank'),
                
                # Allotment details (ALL Excel fields)
                allotted_category=data.get('allotted_category', '') or data.get('allottedcat', ''),
                allotted_gender=data.get('allotted_gender', '') or data.get('Allotted Gender', ''),
                
                # System fields
                year=student_data.get('year'),
                programme_type=programme_type,
                reported_status='NOT_REPORTED',
                academic_year=f"{student_data.get('year')}-{str(student_data.get('year') + 1)[-2:]}",  # e.g., "2025-26"
                allocation_status='ALLOCATED'
            )
            
            # User account creation removed - will be created when status changes to REPORTED
            # Only create user accounts when admin marks student as REPORTED
            auto_generated_password = None
            user_created = False
        
        return JsonResponse({
            'success': True,
            'data': {
                'student_id': student.id,
                'roll_number': student.roll_number or student_data.get('roll_number'),
                'institute_email': student.institute_email or student_data.get('institute_email'),
                'password': auto_generated_password,
                'user_created': user_created,
                'username': student.roll_number if user_created else None
            },
            'message': f'Student added successfully{" with auto-generated login credentials" if user_created else ""}'
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
    """
    Set total seats for a batch
    URL: /programme_curriculum/api/set_total_seats/
    """
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
        
        # Update or create batch configuration
        batch_config, created = BatchConfiguration.objects.update_or_create(
            programme=programme,
            discipline=discipline,
            year=year,
            defaults={'total_seats': total_seats}
        )
        
        # Recalculate seats
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
    URL: /programme_curriculum/api/update_student_status/
    """
    
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = JsonResponse({})
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'PUT, POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, X-CSRFToken, Authorization'
        return response
    
    try:
        # Parse JSON data
        data = json.loads(request.body)
        
        student_id = data.get('studentId')
        reported_status = data.get('reportedStatus')
        
        if not student_id or not reported_status:
            return JsonResponse({
                'success': False,
                'message': 'Missing required fields: studentId, reportedStatus'
            }, status=400)
        
        # Validate reported_status
        if reported_status not in ['REPORTED', 'NOT_REPORTED', 'PENDING']:
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
                    # Create User account and ensure password is available for email
                    
                    if not student.user:
                        # Create new user account with password
                        try:
                            user, password = student.create_user_account()
                            auto_generated_password = password
                            user_created = True
                            print(f"✅ User account created for {student.roll_number} with password: {password}")
                        except Exception as user_error:
                            print(f"❌ Error creating user account: {user_error}")
                            user_created = False
                    else:
                        # User exists, but ensure password is available for email
                        if not student.email_password:
                            # Generate password for email notification
                            auto_generated_password = student.generate_secure_password()
                            student.email_password = auto_generated_password
                            student.password_generated_at = timezone.now()
                            student.password_email_sent = False
                            student.save()
                            print(f"✅ Password generated for existing user {student.roll_number}: {auto_generated_password}")
                        else:
                            auto_generated_password = student.email_password
                            print(f"✅ Using existing password for {student.roll_number}")
                    
                    # Create ExtraInfo if not exists
                    if student.roll_number:
                        # Get or create appropriate department
                        from applications.globals.models import DepartmentInfo
                        
                        # Map branch/discipline to department using ONLY Excel branch field (NOT roll number)
                        # This ensures students can change disciplines while keeping same roll number
                        branch_field = student.branch or ''
                        branch_upper = branch_field.upper()
                        
                        # Map Excel branch to department and discipline names
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
                        elif 'DESIGN' in branch_upper or 'DES' in branch_upper:
                            dept_name = 'Design'  # Exact database name
                            discipline_name = 'Design'
                            discipline_acronym = 'Des.'  # Use existing acronym
                        else:
                            # Log unmapped branches for debugging
                            print(f"⚠️  Unmapped branch: '{branch_field}' for student {student.roll_number}")
                            # Default fallback
                            dept_name = 'CSE'
                            discipline_name = 'Computer Science and Engineering'
                        
                        # Get existing department by exact name match
                        try:
                            department = DepartmentInfo.objects.get(name=dept_name)
                        except DepartmentInfo.DoesNotExist:
                            # Create department if it doesn't exist (shouldn't happen with our mapping)
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
                        
                        # Create Academic Student if not exists
                        # FETCH from existing main tables instead of creating new ones
                        from applications.programme_curriculum.models import Batch, Discipline, Curriculum, Programme
                        from applications.globals.models import DepartmentInfo
                        
                        # FIND existing discipline based on department mapping
                        discipline = None
                        try:
                            # Special handling for Design discipline
                            if dept_name == 'Design':
                                discipline = Discipline.objects.filter(
                                    acronym='Des.',
                                    name='Design'
                                ).first()
                                
                                if not discipline:
                                    # Fallback: find any discipline with design in name
                                    discipline = Discipline.objects.filter(name__icontains='design').first()
                            else:
                                # Try to get the primary discipline (without programme details)
                                discipline = Discipline.objects.filter(
                                    acronym=dept_name,
                                    name__exact=discipline_name
                                ).first()
                            
                            if not discipline:
                                # Fallback: get any discipline with matching acronym (prefer shorter names)
                                disciplines = Discipline.objects.filter(acronym=dept_name).order_by('name')
                                discipline = disciplines.first()
                                
                        except Exception as e:
                            print(f"Error finding discipline: {e}")
                        
                        # Final fallback: create if not found (but not for Design)
                        if not discipline and dept_name != 'Design':
                            try:
                                discipline = Discipline.objects.create(
                                    name=discipline_name,
                                    acronym=dept_name
                                )
                            except Exception as e:
                                print(f"Error creating discipline: {e}")
                                # Use any existing discipline as last resort
                                discipline = Discipline.objects.filter(acronym=dept_name).first()
                        elif not discipline and dept_name == 'Design':
                            # For Design, use any existing Design discipline
                            discipline = Discipline.objects.filter(name__icontains='design').first()
                        
                        # FIND existing programme based on correct naming pattern
                        if student.programme_type == 'ug':
                            if 'design' in student.branch.lower():
                                programme_name = 'B.Des.'  # Design students get B.Des.
                            else:
                                programme_name = 'B.Tech'  # Other UG students get B.Tech
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
                            # For Design students, look for B.Des. specifically
                            if dept_name == 'Design':
                                programme = Programme.objects.filter(
                                    name='B.Des.',
                                    category=programme_category,
                                    discipline=discipline
                                ).first()
                            else:
                                # Try to find existing programme by department-specific name
                                programme_search_name = f"{programme_name} {dept_name}"
                                programme = Programme.objects.filter(
                                    name__icontains=programme_search_name,
                                    category=programme_category
                                ).first()
                                
                                if not programme:
                                    # Try broader search by department only
                                    programme = Programme.objects.filter(
                                        name__icontains=dept_name,
                                        category=programme_category
                                    ).first()
                            
                            if not programme:
                                # Create only if doesn't exist
                                programme = Programme.objects.get_or_create(
                                    name=programme_name,
                                    category=programme_category,
                                    defaults={'discipline': discipline}
                                )[0]
                        except Exception as e:
                            print(f"Error with programme: {e}")
                            programme = Programme.objects.get_or_create(
                                name=programme_name,
                                category=programme_category,
                                defaults={'discipline': discipline}
                            )[0]
                        
                        # FIND existing batch (look for department-specific batch)
                        batch_obj = None
                        try:
                            # First priority: Find batch by discipline and year
                            batch_obj = Batch.objects.filter(
                                year=student.year,
                                discipline=discipline,
                                running_batch=True
                            ).first()
                            
                            if not batch_obj:
                                # Create new batch with correct discipline
                                batch_obj = Batch.objects.create(
                                    name=programme_name,
                                    year=student.year,
                                    discipline=discipline,
                                    running_batch=True
                                )
                                print(f"Created new batch: {batch_obj.name} for {discipline.name}")
                                
                        except Exception as e:
                            print(f"Could not find/create batch: {e}")
                            # Fallback: create simple batch
                            batch_obj = Batch.objects.create(
                                name=programme_name,
                                year=student.year,
                                running_batch=True
                            )
                        
                        # Use discipline directly from Excel data (student.branch) - but shorten it
                        discipline_from_excel = student.branch or ''
                        
                        # Shorten the discipline names to fit database field limits (40 chars)
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
                            # Use first 35 characters as fallback
                            specialization = discipline_from_excel[:35]
                        
                        # ASSIGN CORRECT CURRICULUM TO BATCH BASED ON SPECIALIZATION
                        from applications.programme_curriculum.models import Curriculum
                        try:
                            # Map specialization to curriculum name
                            curriculum_mapping = {
                                'Computer Science and Engineering': 'CSE UG Curriculum',
                                'Electronics and Communication': 'ECE UG Curriculum', 
                                'Mechanical Engineering': 'ME UG Curriculum',
                                'Smart Manufacturing': 'SM UG Curriculum',
                                'Design': 'Design UG Curriculum'
                            }
                            
                            curriculum_name = curriculum_mapping.get(specialization)
                            if curriculum_name and batch_obj:
                                # Find correct curriculum
                                correct_curriculum = Curriculum.objects.filter(
                                    name=curriculum_name
                                ).first()
                                
                                if correct_curriculum:
                                    batch_obj.curriculum = correct_curriculum
                                    batch_obj.save()
                                    print(f"Assigned {curriculum_name} to batch for {specialization}")
                                    
                        except Exception as e:
                            print(f"Error assigning curriculum: {e}")
                        
                        # Calculate current semester based on academic year and current date
                        current_semester = calculate_current_semester(int(student.year))
                        
                        # Create Student record using correct model and field names with COMPLETE MAPPING
                        academic_student, created = AcademicStudent.objects.get_or_create(
                            id=extra_info,  # Use ExtraInfo instance, not string
                            defaults={
                                'batch_id': batch_obj,  # Use Batch instance, not ID
                                'specialization': specialization,  # Use shortened discipline name
                                'programme': programme_name,  # Add programme field
                                'batch': student.year,  # Map year to batch field for compatibility
                                'father_name': student.father_name or '',  # Map father name
                                'mother_name': student.mother_name or '',  # Map mother name
                                'category': student.category or '',  # Map category
                                'cpi': 0.0,  # Default CPI
                                'curr_semester_no': current_semester,  # Dynamic semester based on academic year
                                'hall_no': 0,  # Default hall
                                'room_no': '',  # Default room
                            }
                        )
                        
                        # IMPORTANT: Update ALL fields even if Student already existed
                        if not created:  # If record already existed, update ALL fields
                            academic_student.specialization = specialization
                            academic_student.batch_id = batch_obj  # Also ensure correct batch
                            academic_student.programme = programme_name  # Also update programme
                            academic_student.batch = student.year  # Update batch year
                            academic_student.father_name = student.father_name or ''  # Update father name
                            academic_student.mother_name = student.mother_name or ''  # Update mother name
                            academic_student.category = student.category or ''  # Update category
                            academic_student.curr_semester_no = current_semester  # Update semester based on current date
                            academic_student.save()
                            
                            # ALSO UPDATE BATCH CURRICULUM for existing students
                            try:
                                curriculum_mapping = {
                                    'Computer Science and Engineering': 'CSE UG Curriculum',
                                    'Electronics and Communication': 'ECE UG Curriculum', 
                                    'Mechanical Engineering': 'ME UG Curriculum',
                                    'Smart Manufacturing': 'SM UG Curriculum',
                                    'Design': 'Design UG Curriculum'
                                }
                                
                                curriculum_name = curriculum_mapping.get(specialization)
                                if curriculum_name and batch_obj:
                                    correct_curriculum = Curriculum.objects.filter(
                                        name=curriculum_name
                                    ).first()
                                    
                                    if correct_curriculum and batch_obj.curriculum != correct_curriculum:
                                        batch_obj.curriculum = correct_curriculum
                                        batch_obj.save()
                                        print(f"Updated curriculum for existing student {student.roll_number}: {curriculum_name}")
                                        
                            except Exception as e:
                                print(f"Error updating curriculum for existing student: {e}")
                        
                        # 🎯 CREATE STUDENT DESIGNATION (This is the missing piece!)
                        # This ensures the student gets proper designation_info and can access student modules
                        try:
                            if student.user:
                                # Get or create the 'student' designation
                                student_designation, created = Designation.objects.get_or_create(
                                    name='student',
                                    defaults={
                                        'full_name': 'Student',
                                        'type': 'Academic'
                                    }
                                )
                                
                                # Check if user already has student designation
                                existing_designation = HoldsDesignation.objects.filter(
                                    user=student.user,
                                    designation=student_designation
                                ).first()
                                
                                if not existing_designation:
                                    # Create HoldsDesignation record for the student
                                    holds_designation = HoldsDesignation.objects.create(
                                        user=student.user,
                                        working=student.user,
                                        designation=student_designation,
                                        held_at=timezone.now()
                                    )
                                    transfer_message_addition = f" | Student designation assigned"
                                else:
                                    transfer_message_addition = f" | Student designation already exists"
                                    
                                print(f"✅ Student designation setup complete for {student.roll_number}")
                                
                        except Exception as designation_error:
                            transfer_message_addition = f" | Designation error: {str(designation_error)}"
                            print(f"❌ Error creating student designation: {designation_error}")
                        
                        # 🔍 COMPREHENSIVE VALIDATION - Check for missing critical components
                        validation_warnings = []
                        try:
                            # 1. Verify ExtraInfo.student relationship exists (reverse FK)
                            if hasattr(extra_info, 'student') and extra_info.student:
                                print(f"✅ ExtraInfo.student relationship verified for {student.roll_number}")
                            else:
                                validation_warnings.append("Missing ExtraInfo.student relationship")
                            
                            # 2. Verify user.extrainfo exists
                            if hasattr(student.user, 'extrainfo') and student.user.extrainfo:
                                print(f"✅ User.extrainfo relationship verified for {student.roll_number}")
                            else:
                                validation_warnings.append("Missing User.extrainfo relationship")
                            
                            # 3. Verify batch has curriculum (critical for course registration)
                            if academic_student.batch_id and academic_student.batch_id.curriculum:
                                print(f"✅ Batch curriculum verified: {academic_student.batch_id.curriculum.name}")
                            else:
                                validation_warnings.append("Missing batch curriculum assignment")
                            
                            # 4. Verify academic student has proper semester number
                            if academic_student.curr_semester_no >= 1:
                                print(f"✅ Semester number verified: {academic_student.curr_semester_no}")
                            else:
                                validation_warnings.append("Invalid semester number")
                            
                            # 5. Verify designation access
                            designations = student.user.holds_designations.all()
                            if designations.filter(designation__name='student').exists():
                                print(f"✅ Student designation access verified")
                            else:
                                validation_warnings.append("Missing student designation access")
                            
                            # Add warnings to transfer message if any
                            if validation_warnings:
                                transfer_message_addition += f" | Validation warnings: {'; '.join(validation_warnings)}"
                                
                        except Exception as validation_error:
                            transfer_message_addition += f" | Validation check failed: {str(validation_error)}"
                        
                        transfer_success = True
                        transfer_message = f"Student successfully transferred to main academic tables. Roll: {student.roll_number}{transfer_message_addition}"
                        
                        # Send welcome email with login credentials using existing email system
                        # Send email if password exists (either newly generated or already stored)
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
                                
                                # Send email using existing system
                                email_sent, email_message = send_password_email_smtp(
                                    student_email=(student.institute_email or student.personal_email or '').lower(),  # FORCE LOWERCASE
                                    student_name=student.name,
                                    password=email_password,  # Use the available password
                                    roll_number=student.roll_number,
                                    student=student
                                )
                                
                                if email_sent:
                                    email_log.mark_as_sent(email_password)
                                    student.password_email_sent = True  # Mark as sent in student record
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
                        # COMPREHENSIVE CLEANUP: Remove all linked records
                        
                        # Step 1: Remove from AcademicStudent first (has foreign key to ExtraInfo)
                        try:
                            extra_info = ExtraInfo.objects.get(id=student.roll_number)
                            academic_student = AcademicStudent.objects.get(id=extra_info)
                            
                            # Store batch info before deletion for cleanup
                            batch_to_check = academic_student.batch_id
                            
                            academic_student.delete()
                            transfer_message += f"Removed AcademicStudent record for {student.roll_number}. "
                            
                            # Optional: Clean up empty batches (if no other students)
                            if batch_to_check:
                                remaining_students = AcademicStudent.objects.filter(batch_id=batch_to_check).count()
                                if remaining_students == 0:
                                    transfer_message += f"Batch {batch_to_check.name} now empty. "
                                    
                        except AcademicStudent.DoesNotExist:
                            transfer_message += f"No AcademicStudent record found for {student.roll_number}. "
                        except ExtraInfo.DoesNotExist:
                            transfer_message += f"No ExtraInfo record found for {student.roll_number}. "
                        
                        # Step 2: Remove from ExtraInfo
                        try:
                            extra_info = ExtraInfo.objects.get(id=student.roll_number)
                            extra_info.delete()
                            transfer_message += f"Removed ExtraInfo record for {student.roll_number}. "
                        except ExtraInfo.DoesNotExist:
                            transfer_message += f"No ExtraInfo record found for {student.roll_number}. "
                        
                        # Step 3: Remove User (only if it was created for this student)
                        if student.user:
                            try:
                                # Check if this user is only used by this student - KEEP UPPERCASE
                                username = student.roll_number if student.roll_number else f"temp_{student.jee_app_no}"
                                if student.user.username == username:
                                    user_to_delete = student.user
                                    student.user = None  # Clear the reference first
                                    student.save()
                                    user_to_delete.delete()
                                    transfer_message += f"Removed User account for {username}. "
                                else:
                                    # Just clear the reference if user is shared
                                    student.user = None
                                    student.save()
                                    transfer_message += f"Cleared User reference for {student.roll_number}. "
                            except Exception as e:
                                transfer_message += f"Error removing User: {str(e)}. "
                        
                        # Step 3.5: Remove Student Designation
                        try:
                            if student.user:
                                # Find and remove student designation
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
                        
                        # Step 4: Additional cleanup - check for any other references
                        try:
                            # Check if there are any other models that might reference this student
                            # This is a safety net for future-proofing
                            
                            # You can add more model checks here if needed
                            # For example: Grades, Attendance, etc.
                            
                            pass  # Placeholder for additional cleanup
                            
                        except Exception as e:
                            transfer_message += f"Additional cleanup warning: {str(e)}. "
                        
                        transfer_success = True
                        if not transfer_message:
                            transfer_message = f"Student {student.roll_number} successfully removed from main academic tables"
                    else:
                        transfer_message = "Revert skipped: No roll number assigned"
                        
            except Exception as e:
                transfer_message = f"Status updated but revert failed: {str(e)}"
        
        # Log the status change (optional)
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
            pass  # Log creation failure shouldn't break the main functionality
        
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
        
        response = JsonResponse(response_data, status=200)
        
        # Add CORS headers
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
    URL: /programme_curriculum/api/export_students/<str:programme_type>/
    """
    try:
        # Get students by programme type
        students = StudentBatchUpload.objects.filter(programme_type=programme_type).order_by('roll_number')
        
        if not students.exists():
            return JsonResponse({
                'success': False,
                'message': f'No students found for programme type: {programme_type}'
            }, status=404)
        
        # Create Excel file
        output = BytesIO()
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = f'{programme_type.upper()} Students'
        
        # Headers
        headers = [
            'S.No', 'JEE Application Number', 'Institute Roll Number', 'Name',
            'Discipline', 'Gender', 'Category', 'PWD', 'Mobile No',
            'Institute Email ID', 'Alternate Email ID', 'Father\'s Name',
            'Father\'s Occupation', 'Father Mobile Number', 'Mother\'s Name',
            'Mother\'s Occupation', 'Mother Mobile Number', 'Date of Birth',
            'AI Rank', 'Category Rank', 'Allotted Category', 'Allotted Gender',
            'State', 'Full Address', 'Reported Status'
        ]
        
        for col, header in enumerate(headers, 1):
            worksheet.cell(row=1, column=col, value=header)
        
        # Data rows
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
        
        # Create response
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
    URL: /programme_curriculum/api/upload_history/
    """
    try:
        # Get recent uploads grouped by date
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
    URL: /programme_curriculum/api/list_students/
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
            # Filter by batch (assuming batch_id relates to discipline)
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
                'reported_status': student.reported_status,
                'branch': student.branch,
                'year': student.year
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
    URL: /programme_curriculum/api/batches/create/
    """
    try:
        data = json.loads(request.body)
        
        programme = data.get('programme')
        discipline = data.get('discipline')
        year = data.get('year')
        # Accept both snake_case and camelCase
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
    URL: /programme_curriculum/api/batches/<int:batch_id>/update/
    """
    try:
        data = json.loads(request.body)
        
        try:
            batch = BatchConfiguration.objects.get(id=batch_id)
        except BatchConfiguration.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Batch not found'
            }, status=404)
        
        # Update fields - accept both snake_case and camelCase
        if 'programme' in data:
            batch.programme = data['programme']
        if 'discipline' in data:
            batch.discipline = data['discipline']
        if 'year' in data:
            batch.year = data['year']
        if 'total_seats' in data or 'totalSeats' in data:
            batch.total_seats = data.get('total_seats') or data.get('totalSeats')
        
        # Additional field mappings that frontend might send
        if 'displayBranch' in data:
            batch.discipline = data['displayBranch']
        
        batch.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Batch updated successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to update batch: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_batch(request, batch_id):
    """
    Delete batch
    URL: /programme_curriculum/api/batches/<int:batch_id>/delete/
    """
    try:
        print(f"Attempting to delete batch ID: {batch_id}")
        
        try:
            batch = BatchConfiguration.objects.get(id=batch_id)
            print(f"Found batch: {batch.programme} - {batch.discipline} - {batch.year}")
        except BatchConfiguration.DoesNotExist:
            print(f"Batch {batch_id} not found")
            return JsonResponse({
                'success': False,
                'message': 'Batch not found'
            }, status=404)
        
        # Check if batch has students - using improved field mapping to avoid cross-programme matching
        # First get all students in the year
        students_in_year = StudentBatchUpload.objects.filter(year=batch.year)
        
        # Then filter based on programme type to avoid cross-matching
        if batch.programme.upper() == 'PHD':
            # For PhD, look for students with PhD programme_type
            students_in_batch = students_in_year.filter(
                programme_type__icontains='phd'
            ).filter(
                branch__icontains=batch.discipline
            )
        elif batch.programme.upper() in ['UG', 'UNDERGRADUATE', 'BTECH']:
            # For UG, look for students with UG programme_type
            students_in_batch = students_in_year.filter(
                programme_type__icontains='ug'
            ).filter(
                branch__icontains=batch.discipline
            )
        else:
            # Default: use original logic for other programmes
            students_in_batch = students_in_year.filter(
                branch__icontains=batch.discipline
            )
        
        student_count = students_in_batch.count()
        
        print(f"Batch: {batch.programme} - {batch.discipline} - {batch.year}")
        print(f"Students found in batch: {student_count}")
        
        if student_count > 0:
            print(f"Cannot delete batch - has {student_count} students")
            return JsonResponse({
                'success': False,
                'message': f'Cannot delete batch with {student_count} enrolled students. Please delete students first.'
            }, status=400)
        
        print(f"Deleting batch {batch_id}")
        batch.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Batch deleted successfully'
        })
        
    except Exception as e:
        print(f"Error deleting batch {batch_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': f'Failed to delete batch: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def list_batches_with_status(request):
    """
    List all batches with status
    URL: /programme_curriculum/api/batches/list/
    """
    try:
        batches = BatchConfiguration.objects.all().order_by('programme', 'discipline', 'year')
        
        batch_list = []
        for batch in batches:
            batch.calculate_seats()  # Update seat calculations
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
    Update student status (CRUD version)
    URL: /programme_curriculum/api/students/<int:student_id>/update_status/
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
    URL: /programme_curriculum/api/batches/auto_generate_passwords/
    """
    try:
        data = json.loads(request.body)
        batch_id = data.get('batch_id')
        
        if not batch_id:
            return JsonResponse({
                'success': False,
                'message': 'Missing batch_id'
            }, status=400)
        
        # Get students in the batch
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
    """
    Get batch name based on discipline and programme type
    """
    if programme_type == 'ug':
        if 'design' in discipline_name.lower():
            return 'B.Des'
        else:
            return 'B.Tech'
    elif programme_type == 'pg':
        if 'design' in discipline_name.lower():
            return 'M.Des'
        else:
            return 'M.Tech'
    elif programme_type == 'phd':
        return 'Phd'
    return 'B.Tech'  # Default fallback

def get_or_create_discipline(discipline_name):
    """
    Get or create a Discipline object
    """
    from applications.programme_curriculum.models import Discipline
    
    # Normalize discipline name
    normalized_name = discipline_name.strip()
    
    # Try to find existing discipline
    discipline, created = Discipline.objects.get_or_create(
        name=normalized_name,
        defaults={
            'acronym': get_discipline_acronym(normalized_name)
        }
    )
    return discipline

def get_discipline_acronym(discipline_name):
    """
    Get acronym for discipline
    """
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
    
    # Default: create acronym from first letters
    words = discipline_name.split()
    return ''.join([word[0].upper() for word in words if word])[:5]

def get_or_create_batch(batch_name, discipline_obj, batch_year):
    """
    Get or create a Batch object
    """
    from applications.programme_curriculum.models import Batch
    
    batch, created = Batch.objects.get_or_create(
        name=batch_name,
        discipline=discipline_obj,
        year=batch_year,
        defaults={
            'running_batch': True
        }
    )
    return batch

def create_or_update_main_student_record(student_data, batch_obj, batch_year):
    """
    Create or update the main Student record in academic_information
    Note: student_data contains frontend field names (exact Excel column names)
    """
    try:
        roll_number = student_data.get('Institute Roll Number', '').strip()
        if not roll_number:
            return None
            
        # Check if user already exists
        try:
            user = User.objects.get(username=roll_number)
        except User.DoesNotExist:
            # Create new user
            full_name = student_data.get('Name', '')
            name_parts = full_name.split() if full_name else ['']
            user = User.objects.create_user(
                username=roll_number,
                first_name=name_parts[0] if name_parts else '',
                last_name=' '.join(name_parts[1:]) if len(name_parts) > 1 else '',
                email=student_data.get('Institute Email ID', ''),
                password='student123'  # Default password
            )
        
        # Get or create ExtraInfo
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
        
        # Parse and set date of birth
        if student_data.get('Date of Birth'):
            try:
                dob_str = str(student_data['Date of Birth'])
                if '/' in dob_str:
                    dob = datetime.strptime(dob_str, '%m/%d/%Y').date()
                    extra_info.date_of_birth = dob
                    extra_info.save()
            except:
                pass
        
        # Map category
        category_mapping = {
            'General': 'GEN',
            'GEN': 'GEN',
            'OBC': 'OBC', 
            'SC': 'SC',
            'ST': 'ST'
        }
        category = category_mapping.get(student_data.get('Category', 'GEN'), 'GEN')
        
        # Calculate current semester based on academic year and current date
        current_semester = calculate_current_semester(batch_year)
        
        # Get or create main Student record
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
        print(f"Error creating main student record for {student_data.get('Name', 'Unknown')}: {e}")
        return None


# =============================================================================
# INDIVIDUAL STUDENT CRUD OPERATIONS
# =============================================================================

@csrf_exempt
@require_http_methods(["GET"])
def get_student(request, student_id):
    """
    Get a single student by ID
    URL: /programme_curriculum/api/student/{id}/
    """
    try:
        student = StudentBatchUpload.objects.get(id=student_id)
        
        # Create response with both snake_case and camelCase for frontend compatibility
        student_data = {
            # Core identification
            'id': student.id,
            'jee_app_no': student.jee_app_no,
            'jeeAppNo': student.jee_app_no,
            'roll_number': student.roll_number,
            'rollNumber': student.roll_number,
            'institute_email': student.institute_email,
            'instituteEmail': student.institute_email,
            
            # Personal information
            'name': student.name,
            'father_name': student.father_name,
            'fatherName': student.father_name,
            'fname': student.father_name,  # Additional alias
            'mother_name': student.mother_name,
            'motherName': student.mother_name,
            'gender': student.gender,
            'category': student.category,
            'pwd': student.pwd,
            'date_of_birth': student.date_of_birth.isoformat() if student.date_of_birth else '',
            'dateOfBirth': student.date_of_birth.isoformat() if student.date_of_birth else '',
            
            # Contact information
            'phone_number': student.phone_number,
            'phoneNumber': student.phone_number,
            'mobile': student.phone_number,  # Additional alias
            'personal_email': student.personal_email,
            'personalEmail': student.personal_email,
            'address': student.address,
            'state': student.state,
            
            # Academic information
            'branch': student.branch,
            'ai_rank': student.ai_rank,
            'aiRank': student.ai_rank,
            'category_rank': student.category_rank,
            'categoryRank': student.category_rank,
            'tenth_marks': student.tenth_marks,
            'tenthMarks': student.tenth_marks,
            'twelfth_marks': student.twelfth_marks,
            'twelfthMarks': student.twelfth_marks,
            
            # Family information
            'father_occupation': student.father_occupation,
            'fatherOccupation': student.father_occupation,
            'father_mobile': student.father_mobile,
            'fatherMobile': student.father_mobile,
            'mother_occupation': student.mother_occupation,
            'motherOccupation': student.mother_occupation,
            'mother_mobile': student.mother_mobile,
            'motherMobile': student.mother_mobile,
            
            # Allotment details
            'allotted_category': student.allotted_category,
            'allottedCategory': student.allotted_category,
            'allotted_gender': student.allotted_gender,
            'allottedGender': student.allotted_gender,
            'aadhar_number': student.aadhar_number,
            'aadharNumber': student.aadhar_number,
            
            # System fields
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
    URL: /programme_curriculum/api/student/{id}/update/
    """
    try:
        student = StudentBatchUpload.objects.get(id=student_id)
        data = json.loads(request.body)
        
        # Field mapping from frontend camelCase to backend snake_case
        field_mapping = {
            'jeeAppNo': 'jee_app_no',
            'rollNumber': 'roll_number', 
            'instituteEmail': 'institute_email',
            'fatherName': 'father_name',
            'fname': 'father_name',
            'mname': 'mother_name',  # Add mname mapping
            'motherName': 'mother_name',
            'dateOfBirth': 'date_of_birth',
            'dob': 'date_of_birth',  # Add dob mapping
            'phoneNumber': 'phone_number',
            'mobile': 'phone_number',
            'personalEmail': 'personal_email',
            'email': 'personal_email',  # Add email mapping - THIS WAS MISSING!
            'aiRank': 'ai_rank',
            'jeeRank': 'ai_rank',  # Add jeeRank mapping
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
        
        # Check for duplicates before updating
        jee_app_no = data.get('jeeAppNo') or data.get('jee_app_no')
        roll_number = data.get('rollNumber') or data.get('roll_number')
        institute_email = data.get('instituteEmail') or data.get('institute_email')
        
        # Check JEE Application Number duplicate (excluding current student)
        if jee_app_no and jee_app_no != student.jee_app_no:
            if StudentBatchUpload.objects.filter(jee_app_no=jee_app_no).exclude(id=student_id).exists():
                return JsonResponse({
                    'success': False,
                    'message': f'JEE Application Number {jee_app_no} already exists for another student'
                }, status=400)
        
        # Check Roll Number duplicate (excluding current student)
        if roll_number and roll_number != student.roll_number:
            if StudentBatchUpload.objects.filter(roll_number=roll_number).exclude(id=student_id).exists():
                return JsonResponse({
                    'success': False,
                    'message': f'Roll Number {roll_number} already exists for another student'
                }, status=400)
        
        # Check Institute Email duplicate (excluding current student)
        if institute_email and institute_email != student.institute_email:
            if StudentBatchUpload.objects.filter(institute_email=institute_email).exclude(id=student_id).exists():
                return JsonResponse({
                    'success': False,
                    'message': f'Institute Email {institute_email} already exists for another student'
                }, status=400)
        
        # Update student fields
        for frontend_field, backend_field in field_mapping.items():
            if frontend_field in data:
                value = data[frontend_field]
                if hasattr(student, backend_field):
                    setattr(student, backend_field, value)
        
        # Handle direct field updates (snake_case from frontend)
        direct_fields = [
            'name', 'gender', 'category', 'pwd', 'address', 'state', 'branch'
        ]
        
        for field in direct_fields:
            if field in data:
                setattr(student, field, data[field])
        
        # Handle date of birth parsing - Fix for dob field mapping
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
        
        # Handle AI rank field mapping - Fix for jeeRank field
        jee_rank_value = data.get('jeeRank') or data.get('aiRank') or data.get('ai_rank')
        if jee_rank_value:
            try:
                student.ai_rank = int(str(jee_rank_value).replace(',', '')) if str(jee_rank_value).replace(',', '').isdigit() else None
            except (ValueError, TypeError) as e:
                student.ai_rank = None
        
        # Handle other rank fields (convert to int if provided)
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
        
        # Get the student record
        student = StudentBatchUpload.objects.get(id=student_id)
        student_name = student.name
        student_roll = student.roll_number
        
        # Store info before deletion
        deletion_info = {
            'id': student.id,
            'name': student_name,
            'roll_number': student_roll,
            'jee_app_no': student.jee_app_no,
            'deleted_by': getattr(request, 'user', None) and hasattr(request.user, 'username') and request.user.username or 'Unknown',
            'deleted_at': timezone.now().isoformat()
        }
        
        # Track what gets deleted for response
        deleted_records = {
            'student_batch_upload': False,
            'academic_student': False,
            'extra_info': False,
            'user_account': False
        }
        
        # Perform CASCADE DELETION in transaction with proper error handling
        try:
            with transaction.atomic():
                # 1. Delete from AcademicStudent (if exists)
                if student_roll:
                    try:
                        academic_student = AcademicStudent.objects.get(id__id=student_roll)
                        academic_student.delete()
                        deleted_records['academic_student'] = True
                        print(f"Deleted AcademicStudent record for {student_roll}")
                    except AcademicStudent.DoesNotExist:
                        print(f"No AcademicStudent record found for {student_roll}")
                
                # 2. Delete from ExtraInfo (if exists)
                if student_roll:
                    try:
                        extra_info = ExtraInfo.objects.get(id=student_roll)
                        extra_info.delete()
                        deleted_records['extra_info'] = True
                        print(f"Deleted ExtraInfo record for {student_roll}")
                    except ExtraInfo.DoesNotExist:
                        print(f"No ExtraInfo record found for {student_roll}")
                
                # 3. Store User reference and nullify it in StudentBatchUpload first
                user_to_delete = None
                if student.user:
                    user_to_delete = student.user
                    student.user = None  # Nullify the foreign key reference
                    student.save()  # Save to release the constraint
                    print(f"Nullified user reference for {student_roll}")
                elif student_roll:
                    # Try to find user by username - KEEP UPPERCASE  
                    try:
                        user_to_delete = User.objects.get(username=student_roll)  # Don't convert to lowercase
                    except User.DoesNotExist:
                        print(f"No User account found for {student_roll}")
                
                # 4. Delete from StudentBatchUpload
                student.delete()
                deleted_records['student_batch_upload'] = True
                print(f"Deleted StudentBatchUpload record for {student_roll}")
        
        except Exception as transaction_error:
            print(f"Transaction error during deletion: {transaction_error}")
            return JsonResponse({
                'success': False,
                'message': f'Failed to delete student records: {str(transaction_error)}'
            }, status=500)
        # Handle User deletion separately to avoid transaction conflicts
        if user_to_delete:
            try:
                # First clean up any remaining references using Django ORM instead of raw SQL
                try:
                    # Use the model's ORM methods instead of raw SQL
                    remaining_students = StudentBatchUpload.objects.filter(user=user_to_delete)
                    if remaining_students.exists():
                        remaining_students.update(user=None)
                        print(f"Cleaned up {remaining_students.count()} remaining user references")
                except Exception as cleanup_error:
                    print(f"Could not clean up remaining references: {cleanup_error}")
                
                # Now safely delete the user
                with transaction.atomic():
                    user_to_delete.delete()
                    deleted_records['user_account'] = True
                    print(f"Deleted User account for {student_roll}")
                    
            except Exception as user_deletion_error:
                print(f"Could not delete User account: {user_deletion_error}")
                # Don't fail the whole operation if user deletion fails
        
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
        print(f"Cascade delete student error: {error_details}")
        
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
        
        # Get students to transfer
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
        
        # Perform bulk transfer (simplified implementation)
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
