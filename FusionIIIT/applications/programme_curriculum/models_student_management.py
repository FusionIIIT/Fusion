# Student Management Models for Programme Curriculum

import secrets
import string
from datetime import datetime
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.utils import timezone


def get_current_academic_year():
    """
    Calculate current academic year based on date
    Logic: July 2025 - June 2026 = Academic Year 2025
    """
    current_date = datetime.now()
    if current_date.month >= 7:  # July onwards = current year
        return current_date.year
    else:  # January-June = previous year
        return current_date.year - 1


class BatchConfiguration(models.Model):
    """
    Model to store batch configuration and seat management
    """
    PROGRAMME_CHOICES = [
        ('B.Tech', 'Bachelor of Technology'),
        ('B.Des', 'Bachelor of Design'),
        ('M.Tech', 'Master of Technology'),
        ('M.Des', 'Master of Design'),
        ('PhD', 'Doctor of Philosophy'),
    ]
    
    DISCIPLINE_CHOICES = [
        ('Computer Science and Engineering', 'Computer Science and Engineering'),
        ('Electronics and Communication Engineering', 'Electronics and Communication Engineering'),
        ('Mechanical Engineering', 'Mechanical Engineering'),
        ('Smart Manufacturing', 'Smart Manufacturing'),
        ('Design', 'Design'),
    ]
    
    programme = models.CharField(max_length=50, choices=PROGRAMME_CHOICES)
    discipline = models.CharField(max_length=100, choices=DISCIPLINE_CHOICES)
    year = models.IntegerField(help_text="Academic year (e.g., 2025 for 2025-26)")
    total_seats = models.IntegerField(default=60)
    filled_seats = models.IntegerField(default=0, editable=False)
    available_seats = models.IntegerField(default=0, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['programme', 'discipline', 'year']
        verbose_name = 'Batch Configuration'
        verbose_name_plural = 'Batch Configurations'
        ordering = ['programme', 'discipline', 'year']
    
    def __str__(self):
        return f"{self.programme} - {self.discipline} ({self.year})"
    
    def calculate_seats(self):
        """Calculate filled and available seats based on curriculum assignment"""
        try:
            from applications.programme_curriculum.models import Batch
            batch = Batch.objects.filter(
                name=self.programme,
                discipline__name=self.discipline,
                year=self.year,
                running_batch=True
            ).first()
            
            if self.filled_seats != student_count:
                self.filled_seats = student_count
                self.available_seats = max(0, self.total_seats - self.filled_seats)
                self.save(update_fields=['filled_seats', 'available_seats'])
            
        except Exception as e:
            self.filled_seats = 0
            self.available_seats = self.total_seats


class StudentBatchUpload(models.Model):
    """
    Model to store student data uploaded via Excel or manual entry
    """
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]
    
    CATEGORY_CHOICES = [
        ('GEN', 'General'),
        ('OBC', 'Other Backward Class'),
        ('SC', 'Scheduled Caste'),
        ('ST', 'Scheduled Tribe'),
        ('EWS', 'Economically Weaker Section'),
    ]
    
    PWD_CHOICES = [
        ('YES', 'Yes'),
        ('NO', 'No'),
    ]
    
    PWD_CATEGORY_CHOICES = [
        ('Locomotor Disability', 'Locomotor Disability'),
        ('Visual Impairment', 'Visual Impairment'),
        ('Hearing Impairment', 'Hearing Impairment'),
        ('Speech and Language Disability', 'Speech and Language Disability'),
        ('Intellectual Disability', 'Intellectual Disability'),
        ('Autism Spectrum Disorder', 'Autism Spectrum Disorder'),
        ('Multiple Disabilities', 'Multiple Disabilities'),
        ('Any other (remarks)', 'Any other (remarks)'),
    ]
    
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
        ('Other', 'Other'),
    ]
    
    ADMISSION_MODE_CHOICES = [
        ('JEE Main', 'JEE Main'),
        ('JEE Advanced', 'JEE Advanced'),
        ('GATE', 'GATE'),
        ('DASA', 'DASA'),
        ('Foreign National', 'Foreign National'),
        ('Sponsored', 'Sponsored'),
        ('Any other (remarks)', 'Any other (remarks)'),
    ]
    
    INCOME_GROUP_CHOICES = [
        ('Below 1 Lakh', 'Below 1 Lakh'),
        ('1-2.5 Lakhs', '1-2.5 Lakhs'),
        ('2.5-5 Lakhs', '2.5-5 Lakhs'),
        ('5-8 Lakhs', '5-8 Lakhs'),
        ('Above 8 Lakhs', 'Above 8 Lakhs'),
    ]
    
    REPORTED_STATUS_CHOICES = [
        ('NOT_REPORTED', 'Not Reported'),
        ('REPORTED', 'Reported'),
        ('WITHDRAWAL', 'Withdrawal'),
    ]
    
    PROGRAMME_TYPE_CHOICES = [
        ('ug', 'Undergraduate'),
        ('pg', 'Postgraduate'),
        ('phd', 'PhD'),
    ]
    
    # Core identification fields
    jee_app_no = models.CharField(max_length=50, unique=True, blank=True, null=True, help_text="JEE App. No./CCMT Roll. No.")
    roll_number = models.CharField(max_length=20, unique=True, blank=True, null=True, help_text="Institute Roll Number")
    institute_email = models.EmailField(blank=True, null=True, help_text="Institute Email ID")
    
    # Personal information
    name = models.CharField(max_length=200, help_text="Full Name")
    father_name = models.CharField(max_length=200, help_text="Father's Name")
    mother_name = models.CharField(max_length=200, help_text="Mother's Name")
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    pwd = models.CharField(max_length=3, choices=PWD_CHOICES, default='NO', help_text="Person with Disability")
    minority = models.TextField(blank=True, null=True, help_text="Minority Status (e.g., Muslim, Christian, Sikh, Buddhist, Jain, Parsi, etc.)")
    blood_group = models.CharField(max_length=10, choices=BLOOD_GROUP_CHOICES, blank=True, null=True)
    blood_group_remarks = models.TextField(blank=True, null=True, help_text="Blood group remarks when 'Other' is selected")
    pwd_category = models.CharField(max_length=100, choices=PWD_CATEGORY_CHOICES, blank=True, null=True, help_text="Required when PWD is YES")
    pwd_category_remarks = models.TextField(blank=True, null=True, help_text="Required when PWD category is 'Any other (remarks)'")
    
    # Contact and address
    phone_number = models.CharField(max_length=15, blank=True, null=True, help_text="Mobile Number")
    personal_email = models.EmailField(blank=True, null=True, help_text="Personal Email ID")
    address = models.TextField(help_text="Full Address")
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True, default='India')
    nationality = models.CharField(max_length=100, blank=True, null=True, default='Indian')
    
    # Academic information
    branch = models.CharField(max_length=200, help_text="Discipline/Branch")
    specialization = models.CharField(max_length=200, blank=True, null=True, help_text="Specialization")
    date_of_birth = models.DateField(blank=True, null=True)
    ai_rank = models.IntegerField(blank=True, null=True, help_text="JEE AI Rank", db_column='jee_rank')
    category_rank = models.IntegerField(blank=True, null=True, help_text="Category Rank")
    income_group = models.CharField(max_length=30, choices=INCOME_GROUP_CHOICES, blank=True, null=True)
    income = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Annual family income")
    
    # Additional academic details
    tenth_marks = models.FloatField(blank=True, null=True, help_text="10th Class Marks (%)")
    twelfth_marks = models.FloatField(blank=True, null=True, help_text="12th Class Marks (%)")
    
    # Family information
    father_occupation = models.CharField(max_length=200, blank=True, null=True)
    father_mobile = models.CharField(max_length=15, blank=True, null=True)
    mother_occupation = models.CharField(max_length=200, blank=True, null=True)
    mother_mobile = models.CharField(max_length=15, blank=True, null=True)
    parent_email = models.EmailField(blank=True, null=True, help_text="Parent Email ID")
    aadhar_number = models.CharField(max_length=12, blank=True, null=True)
    
    # Allotment details
    allotted_category = models.CharField(max_length=50, blank=True, null=True)
    allotted_gender = models.CharField(max_length=50, blank=True, null=True)
    admission_mode = models.CharField(max_length=50, choices=ADMISSION_MODE_CHOICES, blank=True, null=True)
    admission_mode_remarks = models.TextField(blank=True, null=True, help_text="Required when admission mode is 'Any other (remarks)'")
    
    # System fields
    year = models.IntegerField(help_text="Academic Year", db_column='batch_year', default=get_current_academic_year)
    academic_year = models.CharField(max_length=20, help_text="Academic Year String (e.g., 2025-26)", db_column='academic_year', blank=True)
    programme_type = models.CharField(max_length=10, choices=PROGRAMME_TYPE_CHOICES)
    allocation_status = models.CharField(max_length=50, default='ALLOCATED', help_text="Allocation Status")
    reported_status = models.CharField(max_length=20, choices=REPORTED_STATUS_CHOICES, default='NOT_REPORTED')
    
    # Source tracking - Track where the student data came from
    source = models.CharField(
        max_length=50, 
        default='admin_upload',
        help_text='Source of student data (admin_upload, excel_upload, manual_entry, etc.)'
    )
    
    # Authentication - Map to existing user_account_id column instead of creating OneToOneField
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='student_profile', db_column='user_account_id')
    
    # Email password field - Store plain password temporarily for email notifications
    # This field is cleared after email is sent for security
    email_password = models.CharField(max_length=50, blank=True, null=True, help_text="Temporary storage for email notification")
    password_email_sent = models.BooleanField(default=False, help_text="Whether password email has been sent")
    password_generated_at = models.DateTimeField(blank=True, null=True, help_text="When password was generated")
    
    # Metadata - Map to existing columns
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_students', db_column='created_by_id')
    
    class Meta:
        verbose_name = 'Student Batch Upload'
        verbose_name_plural = 'Student Batch Uploads'
        ordering = ['roll_number', 'name']
        indexes = [
            models.Index(fields=['programme_type', 'year']),
            models.Index(fields=['branch']),
            models.Index(fields=['reported_status']),
            models.Index(fields=['jee_app_no']),
            models.Index(fields=['roll_number']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.roll_number or self.jee_app_no})"
    
    def get_programme_name(self):
        """Get the full programme name based on programme_type and branch"""
        if self.programme_type == 'ug':
            if 'design' in self.branch.lower():
                return 'B.Des'
            else:
                return 'B.Tech'
        elif self.programme_type == 'pg':
            if 'design' in self.branch.lower():
                return 'M.Des'
            else:
                return 'M.Tech'
        elif self.programme_type == 'phd':
            return 'PhD'
        return 'Unknown'
    
    def get_display_branch(self):
        """Get short display name for branch"""
        branch_lower = self.branch.lower()
        if 'computer' in branch_lower or 'cse' in branch_lower:
            return 'CSE'
        elif 'electronics' in branch_lower or 'ece' in branch_lower:
            return 'ECE'
        elif 'mechanical' in branch_lower or 'me' in branch_lower:
            return 'ME'
        elif 'smart' in branch_lower or 'manufacturing' in branch_lower:
            return 'SM'
        elif 'design' in branch_lower:
            return 'DES'
        return self.branch
    
    @property
    def first_name(self):
        """Get first name from full name"""
        if self.name:
            return self.name.split()[0]
        return ''
    
    @property
    def last_name(self):
        """Get last name from full name"""
        if self.name:
            name_parts = self.name.split()
            if len(name_parts) > 1:
                return ' '.join(name_parts[1:])
        return ''
    
    def clean_branch_name(self, branch_text):
        """Clean branch name by removing parenthetical content"""
        import re
        if not branch_text:
            return branch_text
        # Remove content in parentheses like "(4 Years, Bachelor of Technology)"
        cleaned = re.sub(r'\s*\([^)]*\)', '', branch_text)
        return cleaned.strip()
    
    def clean(self):
        """Validate conditional field requirements"""
        from django.core.exceptions import ValidationError
        
        # PWD Category validation
        if self.pwd == 'YES' and not self.pwd_category:
            raise ValidationError('PWD Category is required when PWD is YES')
        
        # PWD Category remarks validation
        if self.pwd_category == 'Any other (remarks)' and not self.pwd_category_remarks:
            raise ValidationError('PWD Category remarks are required when selecting "Any other (remarks)"')
        
        # Admission mode remarks validation
        if self.admission_mode == 'Any other (remarks)' and not self.admission_mode_remarks:
            raise ValidationError('Admission mode remarks are required when selecting "Any other (remarks)"')
            
        # Blood group remarks validation
        if self.blood_group == 'Other' and not self.blood_group_remarks:
            raise ValidationError('Blood group remarks are required when selecting "Other"')
    
    def save(self, *args, **kwargs):
        """Override save to automatically set academic_year string and normalize emails"""
        if not self.academic_year:
            year = self.year or get_current_academic_year()
            next_year = (year + 1) % 100
            self.academic_year = f"{year}-{next_year:02d}"
        
        if self.roll_number and not self.institute_email:
            self.institute_email = f"{self.roll_number.lower()}@iiitdmj.ac.in"
        
        # Normalize email addresses to lowercase
        if self.institute_email:
            self.institute_email = self.institute_email.lower()
        if self.personal_email:
            self.personal_email = self.personal_email.lower()
        if self.parent_email:
            self.parent_email = self.parent_email.lower()
            
        # Clean branch name
        if self.branch:
            self.branch = self.clean_branch_name(self.branch)
        
        super().save(*args, **kwargs)
    
    def create_user_account(self, password=None):
        """Create Django User account for this student"""
        from django.contrib.auth.models import User
        from django.db import IntegrityError
        import secrets
        import string
        
        if self.user:
            return self.user, None
        
        if not password:
            password = self.generate_secure_password()
        
        username = self.roll_number or self.jee_app_no
        email = (self.institute_email or self.personal_email or '').lower()
        
        try:
            existing_user = User.objects.filter(username=username).first()
            if existing_user:
                self.user = existing_user
                self.save()
                return existing_user, None
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=self.name.split()[0] if self.name else '',
                last_name=' '.join(self.name.split()[1:]) if len(self.name.split()) > 1 else '',
                is_active=True
            )
            
            self.user = user
            
            from django.utils import timezone
            self.email_password = password
            self.password_generated_at = timezone.now()
            self.password_email_sent = False
            self.save()
            
            return user, password
            
        except IntegrityError as e:
            if 'username' in str(e):
                existing_user = User.objects.filter(username=username).first()
                if existing_user:
                    self.user = existing_user
                    self.save()
                    return existing_user, None
            raise e
    
    def get_user_account(self):
        """Get the Django User account for this student"""
        return self.user
    
    def has_user_account(self):
        """Check if student has a Django User account"""
        return self.user is not None
    
    def update_user_password(self, new_password):
        """Update user password"""
        if self.user:
            self.user.set_password(new_password)
            self.user.save()
            return True
        return False
    
    @staticmethod
    def generate_secure_password(length=12):
        """Generate cryptographically secure password"""
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        special = "!@#$%"
        
        password = [
            secrets.choice(lowercase),
            secrets.choice(uppercase), 
            secrets.choice(digits),
            secrets.choice(special)
        ]
        
        all_chars = lowercase + uppercase + digits + special
        for _ in range(length - 4):
            password.append(secrets.choice(all_chars))
        
        secrets.SystemRandom().shuffle(password)
        return ''.join(password)
    
    def create_complete_student_profile(self):
        """Manually trigger complete student profile creation"""
        if self.reported_status != 'REPORTED':
            raise ValueError("Student must be in REPORTED status to create complete profile")
        
        if not self.roll_number:
            raise ValueError("Student must have a roll number to create complete profile")
        
        from .signals import create_django_user, create_extra_info, create_academic_student
        from django.db import transaction
        
        try:
            with transaction.atomic():
                user, password = create_django_user(self)
                extra_info = create_extra_info(self, user)
                academic_student = create_academic_student(self, extra_info)
                
                self.user = user
                self.save(update_fields=['user'])
                
                return {
                    'success': True,
                    'user': user,
                    'extra_info': extra_info,
                    'academic_student': academic_student,
                    'password': password
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def has_complete_profile(self):
        """
        Check if student has complete profile (User + ExtraInfo + Academic Student)
        """
        if not self.user:
            return False
        
        try:
            # Check if ExtraInfo exists
            extra_info = self.user.extrainfo
            
            # Check if Academic Student exists
            from applications.academic_information.models import Student
            academic_student = Student.objects.get(id=extra_info)
            
            return True
        except:
            return False
    
    def get_profile_status(self):
        """
        Get detailed status of student profile creation
        """
        status = {
            'has_user': bool(self.user),
            'has_extra_info': False,
            'has_academic_student': False,
            'is_complete': False
        }
        
        if self.user:
            try:
                extra_info = self.user.extrainfo
                status['has_extra_info'] = True
                
                # Check academic student
                from applications.academic_information.models import Student
                academic_student = Student.objects.get(id=extra_info)
                status['has_academic_student'] = True
                
                status['is_complete'] = True
            except:
                pass
        
        return status


class StudentStatusLog(models.Model):
    """
    Model to log changes in student status for audit purposes
    """
    student = models.ForeignKey(StudentBatchUpload, on_delete=models.CASCADE, related_name='status_logs')
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    old_reported_status = models.CharField(max_length=20)
    new_reported_status = models.CharField(max_length=20)
    change_reason = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Student Status Log'
        verbose_name_plural = 'Student Status Logs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.name} - {self.old_reported_status} → {self.new_reported_status} at {self.created_at}"


class UploadHistory(models.Model):
    """
    Model to track upload history and statistics
    """
    UPLOAD_TYPE_CHOICES = [
        ('excel', 'Excel Upload'),
        ('manual', 'Manual Entry'),
        ('bulk', 'Bulk Import'),
    ]
    
    upload_type = models.CharField(max_length=20, choices=UPLOAD_TYPE_CHOICES)
    programme_type = models.CharField(max_length=10, choices=StudentBatchUpload.PROGRAMME_TYPE_CHOICES)
    total_records = models.IntegerField(default=0)
    successful_records = models.IntegerField(default=0)
    failed_records = models.IntegerField(default=0)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    upload_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Upload History'
        verbose_name_plural = 'Upload History'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.upload_type} - {self.programme_type} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
    
    @property
    def success_rate(self):
        """Calculate success rate percentage"""
        if self.total_records == 0:
            return 0
        return round((self.successful_records / self.total_records) * 100, 2)


# Django Signal for Automatic Student Profile Creation
from django.db.models.signals import post_save
from django.dispatch import receiver

def create_student_profiles_automatically(students_list):
    """Create student profiles automatically"""
    from django.utils import timezone
    from applications.globals.models import ExtraInfo, DepartmentInfo
    from applications.programme_curriculum.models import Batch, Discipline, Curriculum, Programme
    from applications.academic_information.models import Student as AcademicStudent
    from applications.globals.models import Designation, HoldsDesignation
    import json
    
    results = []
    
    for student in students_list:
        try:
            if student.user:
                results.append({'success': True, 'student': student.name, 'skipped': True})
                continue
            
            user, password = student.create_user_account()
            if user:
                pass
                
            if student.roll_number and student.user:
                branch_field = student.branch or ''
                branch_upper = branch_field.upper()
                
                if 'COMPUTER SCIENCE' in branch_upper or 'CSE' in branch_upper:
                    dept_name = 'CSE'
                elif 'ELECTRONICS' in branch_upper or 'ECE' in branch_upper:
                    dept_name = 'ECE'
                elif 'DESIGN' in branch_upper:
                    dept_name = 'Design'
                else:
                    dept_name = 'CSE'
                
                department = DepartmentInfo.objects.get_or_create(name=dept_name)[0]
                
                extra_info, created = ExtraInfo.objects.get_or_create(
                    id=student.roll_number,
                    defaults={
                        'user': student.user,
                        'title': 'Mr.' if student.gender == 'Male' else 'Ms.',
                        'sex': 'M' if student.gender == 'Male' else 'F',
                        'user_type': 'student',
                        'department': department
                    }
                )
            
            if student.user and student.roll_number:
                from applications.academic_information.models import Student as AcademicStudent
                
                try:
                    extra_info = ExtraInfo.objects.get(id=student.roll_number)
                    
                    academic_student, created = AcademicStudent.objects.get_or_create(
                        id=extra_info,
                        defaults={
                            'programme': student.get_programme_name(),
                            'batch': student.year,
                            'cpi': 0.0,
                            'category': student.category or 'General',
                            'father_name': student.father_name or '',
                            'mother_name': student.mother_name or '',
                            'hall_no': 0,
                            'room_no': '',
                            'specialization': ''
                        }
                    )
                        
                except ExtraInfo.DoesNotExist:
                    pass
                except Exception as e:
                    pass
            
            if student.user:
                student_designation = Designation.objects.filter(name='student').first()
                if student_designation:
                    holds_designation, created = HoldsDesignation.objects.get_or_create(
                        user=student.user,
                        designation=student_designation,
                        defaults={'working': student.user}
                    )
            
            results.append({'success': True, 'student': student.name})
            
        except Exception as e:
            results.append({'success': False, 'student': student.name, 'error': str(e)})
    
    return results

@receiver(post_save, sender=StudentBatchUpload)
def auto_create_student_profile(sender, instance, created, **kwargs):
    """Automatically create student profile when status changes to REPORTED"""
    if instance.reported_status == 'REPORTED' and not instance.user:
        try:
            post_save.disconnect(auto_create_student_profile, sender=StudentBatchUpload)
            
            try:
                automation_result = create_student_profiles_automatically([instance])
            finally:
                post_save.connect(auto_create_student_profile, sender=StudentBatchUpload)
            
        except Exception as e:
            try:
                post_save.connect(auto_create_student_profile, sender=StudentBatchUpload)
            except:
                pass
