"""Django Signals for Student Management"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db import transaction, IntegrityError
from django.utils import timezone
import logging

from .models_student_management import StudentBatchUpload, StudentStatusLog
from applications.globals.models import ExtraInfo, DepartmentInfo
from applications.academic_information.models import Student
from applications.programme_curriculum.models import Batch

logger = logging.getLogger(__name__)

@receiver(pre_save, sender=StudentBatchUpload)
def log_status_change(sender, instance, **kwargs):
    """Log status changes for audit purposes"""
    if instance.pk:
        try:
            old_instance = StudentBatchUpload.objects.get(pk=instance.pk)
            if old_instance.reported_status != instance.reported_status:
                StudentStatusLog.objects.create(
                    student=instance,
                    old_reported_status=old_instance.reported_status,
                    new_reported_status=instance.reported_status,
                    change_reason=f"Status changed from {old_instance.reported_status} to {instance.reported_status}",
                    created_at=timezone.now()
                )
        except StudentBatchUpload.DoesNotExist:
            pass



@receiver(post_save, sender=StudentBatchUpload)
def handle_withdrawal_status(sender, instance, created, **kwargs):
    """Handle when student status is changed to WITHDRAWAL"""
    if instance.reported_status == 'WITHDRAWAL':
        if instance.user:
            instance.user.is_active = False
            instance.user.save()


def create_django_user(student_upload):
    """Create Django User account for the student"""
    username = student_upload.roll_number
    existing_user = User.objects.filter(username=username).first()
    
    if existing_user:
        return existing_user, None
    
    password = StudentBatchUpload.generate_secure_password()
    
    user = User.objects.create_user(
        username=username,
        email=student_upload.institute_email or student_upload.personal_email,
        password=password,
        first_name=student_upload.first_name,
        last_name=student_upload.last_name,
        is_active=True
    )
    
    return user, password


def create_extra_info(student_upload, user):
    """Create ExtraInfo record for the student"""
    existing_extra_info = ExtraInfo.objects.filter(id=student_upload.roll_number).first()
    if existing_extra_info:
        return existing_extra_info
    
    department = get_department_for_branch(student_upload.branch)
    sex = 'M' if student_upload.gender == 'Male' else 'F' if student_upload.gender == 'Female' else 'O'
    
    extra_info = ExtraInfo.objects.create(
        id=student_upload.roll_number,
        user=user,
        title='Mr.' if student_upload.gender == 'Male' else 'Ms.',
        sex=sex,
        date_of_birth=student_upload.date_of_birth or timezone.now().date(),
        user_status='PRESENT',
        address=student_upload.address or '',
        phone_no=int(student_upload.phone_number) if student_upload.phone_number and student_upload.phone_number.isdigit() else 9999999999,
        user_type='student',
        department=department,
        about_me=f"Student from {student_upload.branch} batch {student_upload.year}",
        date_modified=timezone.now()
    )
    
    return extra_info


def create_academic_student(student_upload, extra_info):
    """Create Academic Student record"""
    existing_student = Student.objects.filter(id=extra_info).first()
    if existing_student:
        return existing_student
    
    batch = get_batch_for_student(student_upload)
    
    category_mapping = {
        'GEN': 'GEN',
        'General': 'GEN',
        'OBC': 'OBC',
        'SC': 'SC',
        'ST': 'ST',
        'EWS': 'GEN',
    }
    category = category_mapping.get(student_upload.category, 'GEN')
    
    academic_student = Student.objects.create(
        id=extra_info,
        programme=student_upload.get_programme_name(),
        batch=student_upload.year,
        batch_id=batch,
        cpi=0.0,
        category=category,
        father_name=student_upload.father_name or '',
        mother_name=student_upload.mother_name or '',
        hall_no=0,
        room_no='',
        specialization='None',
        curr_semester_no=1
    )
    
    return academic_student


def get_department_for_branch(branch):
    """Get department based on branch name"""
    branch_lower = branch.lower()
    
    department_mapping = {
        'computer': 'Computer Science and Engineering',
        'cse': 'Computer Science and Engineering',
        'electronics': 'Electronics and Communication Engineering', 
        'ece': 'Electronics and Communication Engineering',
        'mechanical': 'Mechanical Engineering',
        'me': 'Mechanical Engineering',
        'smart': 'Smart Manufacturing',
        'manufacturing': 'Smart Manufacturing',
        'design': 'Design',
    }
    
    for key, dept_name in department_mapping.items():
        if key in branch_lower:
            dept = DepartmentInfo.objects.filter(name=dept_name).first()
            if dept:
                return dept
    
    return DepartmentInfo.objects.first()


def get_batch_for_student(student_upload):
    """Get or create Batch for the student"""
    discipline_mapping = {
        'Computer Science and Engineering': 'Computer Science and Engineering',
        'Electronics and Communication Engineering': 'Electronics and Communication Engineering',
        'Mechanical Engineering': 'Mechanical Engineering',
        'Smart Manufacturing': 'Smart Manufacturing',
        'Design': 'Design',
    }
    
    branch_lower = student_upload.branch.lower()
    discipline_name = None
    
    for key, value in discipline_mapping.items():
        if key.lower() in branch_lower:
            discipline_name = value
            break
    
    if not discipline_name:
        if 'computer' in branch_lower or 'cse' in branch_lower:
            discipline_name = 'Computer Science and Engineering'
        elif 'electronics' in branch_lower or 'ece' in branch_lower:
            discipline_name = 'Electronics and Communication Engineering'
        elif 'mechanical' in branch_lower or 'me' in branch_lower:
            discipline_name = 'Mechanical Engineering'
        elif 'smart' in branch_lower or 'manufacturing' in branch_lower:
            discipline_name = 'Smart Manufacturing'
        elif 'design' in branch_lower:
            discipline_name = 'Design'
    
    from applications.programme_curriculum.models import Discipline
    
    try:
        discipline = Discipline.objects.filter(name=discipline_name).first()
        if discipline:
            batch = Batch.objects.filter(
                discipline=discipline,
                year=student_upload.year
            ).first()
            if batch:
                return batch
    except Exception as e:
        pass
    
    return None


def send_welcome_email(student_upload, password):
    """Send welcome email with login credentials"""
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        
        subject = f"Welcome to IIITDM Jabalpur - Login Credentials"
        message = f"""
Dear {student_upload.name},

Welcome to IIITDM Jabalpur! Your account has been successfully created.

Login Credentials:
Username: {student_upload.roll_number}
Password: {password}
Email: {student_upload.institute_email}

Please login to the student portal and change your password immediately.

Best regards,
Academic Section
IIITDM Jabalpur
"""
        
        email_to = student_upload.institute_email or student_upload.personal_email
        if email_to:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email_to],
                fail_silently=False,
            )
            
            student_upload.password_email_sent = True
            student_upload.email_password = ''
            student_upload.save(update_fields=['password_email_sent', 'email_password'])
        
    except Exception as e:
        pass
