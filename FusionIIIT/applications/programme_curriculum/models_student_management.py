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
        """Calculate filled and available seats based on actual student count"""
        try:
            from django.db.models import Q
            
            # Create flexible query to match students
            discipline_q = Q()
            
            # Direct match
            discipline_q |= Q(branch__icontains=self.discipline)
            
            # Normalized discipline matching
            if self.discipline == 'Computer Science and Engineering':
                discipline_q |= Q(branch__icontains='Computer Science') | Q(branch__icontains='CSE')
            elif self.discipline == 'Electronics and Communication Engineering':
                discipline_q |= Q(branch__icontains='Electronics') | Q(branch__icontains='ECE')
            elif self.discipline == 'Mechanical Engineering':
                discipline_q |= Q(branch__icontains='Mechanical') | Q(branch__icontains='ME')
            elif self.discipline == 'Smart Manufacturing':
                discipline_q |= Q(branch__icontains='Smart Manufacturing') | Q(branch__icontains='SM')
            elif self.discipline == 'Design':
                discipline_q |= Q(branch__icontains='Design') | Q(branch__icontains='Des')
            
            # Count students matching this batch
            student_count = StudentBatchUpload.objects.filter(
                discipline_q,
                year=self.year
            ).count()
            
            self.filled_seats = student_count
            self.available_seats = max(0, self.total_seats - self.filled_seats)
            self.save(update_fields=['filled_seats', 'available_seats'])
            
        except Exception as e:
            print(f"Error calculating seats for batch {self.id}: {e}")
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
    
    REPORTED_STATUS_CHOICES = [
        ('NOT_REPORTED', 'Not Reported'),
        ('REPORTED', 'Reported'),
    ]
    
    PROGRAMME_TYPE_CHOICES = [
        ('ug', 'Undergraduate'),
        ('pg', 'Postgraduate'),
        ('phd', 'PhD'),
    ]
    
    # Core identification fields
    jee_app_no = models.CharField(max_length=50, unique=True, help_text="JEE Application Number")
    roll_number = models.CharField(max_length=20, unique=True, blank=True, null=True, help_text="Institute Roll Number")
    institute_email = models.EmailField(blank=True, null=True, help_text="Institute Email ID")
    
    # Personal information
    name = models.CharField(max_length=200, help_text="Full Name")
    father_name = models.CharField(max_length=200, help_text="Father's Name")
    mother_name = models.CharField(max_length=200, help_text="Mother's Name")
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    pwd = models.CharField(max_length=3, choices=PWD_CHOICES, default='NO', help_text="Person with Disability")
    
    # Contact and address
    phone_number = models.CharField(max_length=15, blank=True, null=True, help_text="Mobile Number")
    personal_email = models.EmailField(blank=True, null=True, help_text="Personal Email ID")
    address = models.TextField(help_text="Full Address")
    state = models.CharField(max_length=100, blank=True, null=True)
    
    # Academic information
    branch = models.CharField(max_length=200, help_text="Discipline/Branch")
    date_of_birth = models.DateField(blank=True, null=True)
    ai_rank = models.IntegerField(blank=True, null=True, help_text="JEE AI Rank", db_column='jee_rank')
    category_rank = models.IntegerField(blank=True, null=True, help_text="Category Rank")
    
    # Additional academic details
    tenth_marks = models.FloatField(blank=True, null=True, help_text="10th Class Marks (%)")
    twelfth_marks = models.FloatField(blank=True, null=True, help_text="12th Class Marks (%)")
    
    # Family information
    father_occupation = models.CharField(max_length=200, blank=True, null=True)
    father_mobile = models.CharField(max_length=15, blank=True, null=True)
    mother_occupation = models.CharField(max_length=200, blank=True, null=True)
    mother_mobile = models.CharField(max_length=15, blank=True, null=True)
    aadhar_number = models.CharField(max_length=12, blank=True, null=True)
    
    # Allotment details
    allotted_category = models.CharField(max_length=20, blank=True, null=True)
    allotted_gender = models.CharField(max_length=20, blank=True, null=True)
    
    # System fields
    year = models.IntegerField(help_text="Academic Year", db_column='batch_year', default=get_current_academic_year)
    academic_year = models.CharField(max_length=20, help_text="Academic Year String (e.g., 2025-26)", db_column='academic_year', blank=True)
    programme_type = models.CharField(max_length=10, choices=PROGRAMME_TYPE_CHOICES)
    allocation_status = models.CharField(max_length=50, default='ALLOCATED', help_text="Allocation Status")
    reported_status = models.CharField(max_length=20, choices=REPORTED_STATUS_CHOICES, default='NOT_REPORTED')
    
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
    
    def save(self, *args, **kwargs):
        """Override save to automatically set academic_year string"""
        if not self.academic_year:
            # Auto-generate academic year string (e.g., "2025-26")
            year = self.year or get_current_academic_year()
            next_year = (year + 1) % 100  # Get last 2 digits of next year
            self.academic_year = f"{year}-{next_year:02d}"
        super().save(*args, **kwargs)
    
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
    
    def save(self, *args, **kwargs):
        # Auto-generate institute email if roll number is provided
        if self.roll_number and not self.institute_email:
            self.institute_email = f"{self.roll_number.lower()}@iiitdmj.ac.in"
        
        # Normalize email addresses to lowercase for delivery consistency
        if self.institute_email:
            self.institute_email = self.institute_email.lower()
        if self.personal_email:
            self.personal_email = self.personal_email.lower()
        
        super().save(*args, **kwargs)
    
    def create_user_account(self, password=None):
        """
        Create Django User account for this student
        Password is ONLY stored in auth_user table, never in student table
        """
        from django.contrib.auth.models import User
        from django.db import IntegrityError
        import secrets
        import string
        
        if self.user:
            return self.user, None  # User already exists
        
        # Generate secure password if not provided
        if not password:
            password = self.generate_secure_password()
        
        # Create username (prefer roll_number, fallback to jee_app_no) - KEEP UPPERCASE
        username = self.roll_number or self.jee_app_no  # Keep original case (uppercase)
        email = (self.institute_email or self.personal_email or '').lower()  # FORCE LOWERCASE for email
        
        try:
            # Check if user already exists
            existing_user = User.objects.filter(username=username).first()
            if existing_user:
                # Link existing user to this student
                self.user = existing_user
                self.save()
                return existing_user, None  # Return None for password since it's existing user
            
            # Create new User with hashed password in auth_user table
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,  # Django automatically hashes this
                first_name=self.name.split()[0] if self.name else '',
                last_name=' '.join(self.name.split()[1:]) if len(self.name.split()) > 1 else '',
                is_active=True
            )
            
            # Link the user to this student
            self.user = user
            
            # Store password for email notification
            from django.utils import timezone
            self.email_password = password
            self.password_generated_at = timezone.now()
            self.password_email_sent = False
            self.save()
            
            return user, password  # Return user object and plain password for emailing
            
        except IntegrityError as e:
            # Handle duplicate username gracefully
            if 'username' in str(e):
                # Try to find and link existing user
                existing_user = User.objects.filter(username=username).first()
                if existing_user:
                    self.user = existing_user
                    self.save()
                    return existing_user, None
            # Re-raise if it's a different integrity error
            raise e
    
    def get_user_account(self):
        """Get the Django User account for this student"""
        return self.user
    
    def has_user_account(self):
        """Check if student has a Django User account"""
        return self.user is not None
    
    def update_user_password(self, new_password):
        """
        Update user password (stored only in auth_user table)
        """
        if self.user:
            self.user.set_password(new_password)  # Django handles hashing
            self.user.save()
            return True
        return False
    
    @staticmethod
    def generate_secure_password(length=8):
        """
        Generate cryptographically secure password
        """
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        special = "!@#$%"
        
        # Ensure password has at least one from each category
        password = [
            secrets.choice(lowercase),
            secrets.choice(uppercase), 
            secrets.choice(digits),
            secrets.choice(special)
        ]
        
        # Fill remaining length
        all_chars = lowercase + uppercase + digits + special
        for _ in range(length - 4):
            password.append(secrets.choice(all_chars))
        
        # Shuffle the password
        secrets.SystemRandom().shuffle(password)
        return ''.join(password)


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
