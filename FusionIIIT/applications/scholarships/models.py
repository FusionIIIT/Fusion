from django.db import models
from applications.academic_information.models import Student

class AwardTypeChoices(models.TextChoices):
    MCM = 'MCM', 'Merit-cum-Means Scholarship'
    CONVENER = 'CONVENER', 'Convener Award'
    DIRECTOR_GOLD = 'DIRECTOR_GOLD', 'Director Gold Medal'
    DIRECTOR_SILVER = 'DIRECTOR_SILVER', 'Director Silver Medal'
    PROFICIENCY = 'PROFICIENCY', 'Proficiency Medal'

class ApplicationStatusChoices(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    APPROVED = 'APPROVED', 'Approved'
    REJECTED = 'REJECTED', 'Rejected'

class Award_and_scholarship(models.Model):
    award_name = models.CharField(max_length=100, unique=True)
    catalog = models.TextField(help_text="Description and eligibility criteria")
    award_type = models.CharField(max_length=50, choices=AwardTypeChoices.choices, default=AwardTypeChoices.MCM)

    class Meta:
        db_table = 'spacs_award_catalog'

    def __str__(self):
        return self.award_name

class Release(models.Model):
    award = models.ForeignKey(Award_and_scholarship, on_delete=models.CASCADE, related_name='releases')
    startdate = models.DateField()
    enddate = models.DateField()
    batch = models.CharField(max_length=20, help_text="e.g., UG1, UG2, 2021")
    programme = models.CharField(max_length=50, help_text="e.g., B.Tech, M.Tech")
    notif_visible = models.BooleanField(default=True)

    class Meta:
        db_table = 'spacs_release'

    def __str__(self):
        return f"{self.award.award_name} ({self.batch} - {self.programme})"

class Application(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='scholarship_applications')
    award = models.ForeignKey(Award_and_scholarship, on_delete=models.CASCADE)
    applied_flag = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=ApplicationStatusChoices.choices, default=ApplicationStatusChoices.PENDING)
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'spacs_application'
        unique_together = ('student', 'award')

    def __str__(self):
        return f"{self.student.id} - {self.award.award_name}"

class Mcm(models.Model):
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='mcm_details')
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    brother_name = models.CharField(max_length=100, blank=True, null=True)
    brother_occupation = models.CharField(max_length=100, blank=True, null=True)
    sister_name = models.CharField(max_length=100, blank=True, null=True)
    sister_occupation = models.CharField(max_length=100, blank=True, null=True)
    income_father = models.IntegerField(default=0)
    income_mother = models.IntegerField(default=0)
    income_other = models.IntegerField(default=0)
    annual_income = models.IntegerField(default=0, help_text="Calculated total income")
    father_occ = models.CharField(max_length=100, blank=True, null=True)
    mother_occ = models.CharField(max_length=100, blank=True, null=True)
    income_certificate = models.FileField(upload_to='scholarships/income_certs/')

    class Meta:
        db_table = 'spacs_mcm'

class BaseMedalDetails(models.Model):
    correspondence_address = models.TextField()
    financial_assistance = models.TextField(blank=True, null=True)
    grand_total = models.FloatField(default=0.0)
    nearest_policestation = models.CharField(max_length=100)
    nearest_railwaystation = models.CharField(max_length=100)

    class Meta:
        abstract = True

class Director_gold(BaseMedalDetails):
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='gold_details')
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    relevant_document = models.FileField(upload_to='scholarships/gold_docs/')
    academic_achievements = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'spacs_director_gold'

class Director_silver(BaseMedalDetails):
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='silver_details')
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    relevant_document = models.FileField(upload_to='scholarships/silver_docs/')

    class Meta:
        db_table = 'spacs_director_silver'

class Proficiency_dm(BaseMedalDetails):
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='proficiency_details')
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    relevant_document = models.FileField(upload_to='scholarships/proficiency_docs/')
    title_of_project = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        db_table = 'spacs_proficiency_dm'

class Previous_winner(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    award = models.ForeignKey(Award_and_scholarship, on_delete=models.CASCADE)
    year = models.IntegerField()

    class Meta:
        db_table = 'spacs_previous_winner'


# ========== EXTENDED SCHOLARSHIP MODELS ==========

class ExtendedScholarshipType(models.Model):
    """Comprehensive scholarship type with full eligibility criteria and programme/batch targeting"""
    CATEGORY_CHOICES = [
        ('MERIT', 'Merit-based'),
        ('NEED', 'Need-based'),
        ('CATEGORY', 'Category-based'),
        ('SPORTS', 'Sports'),
        ('CULTURAL', 'Cultural'),
        ('RESEARCH', 'Research'),
        ('EXTERNAL', 'External/Government'),
    ]

    name = models.CharField(max_length=200, unique=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    frequency = models.CharField(max_length=20, default='Annual')
    eligibility_criteria = models.TextField()
    max_backlogs = models.IntegerField(default=0)
    applicable_categories = models.CharField(max_length=50, blank=True, help_text="Comma-separated: GEN,SC,ST,OBC")
    minimum_cgpa = models.FloatField(null=True, blank=True)
    maximum_income = models.IntegerField(null=True, blank=True, help_text="Maximum annual family income for need-based")
    applicable_programmes = models.ManyToManyField(
        'programme_curriculum.Programme', blank=True, related_name='scholarship_types'
    )
    applicable_batches = models.ManyToManyField(
        'programme_curriculum.Batch', blank=True, related_name='scholarship_types'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'spacs_extended_scholarship_type'

    def __str__(self):
        return f"{self.name} ({self.category})"


class ScholarshipApplication(models.Model):
    """Full lifecycle scholarship application linked to ExtendedScholarshipType"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('UNDER_REVIEW', 'Under Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('DISBURSED', 'Disbursed'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='extended_scholarship_applications')
    scholarship_type = models.ForeignKey(ExtendedScholarshipType, on_delete=models.CASCADE, related_name='applications')
    academic_year = models.CharField(max_length=9, help_text="Format: 2024-25")
    semester = models.IntegerField()
    category_at_application = models.CharField(max_length=10, blank=True)
    application_date = models.DateTimeField(auto_now_add=True)
    supporting_documents = models.FileField(upload_to='scholarships/documents/', null=True, blank=True)
    remarks = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    reviewed_by = models.ForeignKey(
        'globals.ExtraInfo', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reviewed_scholarship_applications'
    )
    review_date = models.DateTimeField(null=True, blank=True)
    review_remarks = models.TextField(blank=True)
    amount_approved = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    disbursement_date = models.DateTimeField(null=True, blank=True)
    transaction_reference = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'spacs_scholarship_application'
        unique_together = ['student', 'scholarship_type', 'academic_year', 'semester']

    def __str__(self):
        return f"{self.student} - {self.scholarship_type.name} ({self.academic_year})"


class Award(models.Model):
    """General institutional awards (academic, sports, cultural, etc.)"""
    AWARD_CATEGORY = [
        ('ACADEMIC', 'Academic Excellence'),
        ('RESEARCH', 'Research'),
        ('SPORTS', 'Sports'),
        ('CULTURAL', 'Cultural'),
        ('INNOVATION', 'Innovation'),
        ('LEADERSHIP', 'Leadership'),
        ('COMMUNITY', 'Community Service'),
    ]

    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=AWARD_CATEGORY)
    description = models.TextField()
    criteria = models.TextField()
    prize_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    certificate_provided = models.BooleanField(default=True)
    applicable_programmes = models.ManyToManyField(
        'programme_curriculum.Programme', blank=True, related_name='awards'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'spacs_general_award'

    def __str__(self):
        return f"{self.name} ({self.category})"


class AwardRecipient(models.Model):
    """Record of students who received general awards"""
    award = models.ForeignKey(Award, on_delete=models.CASCADE, related_name='recipients')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='award_receipts')
    academic_year = models.CharField(max_length=9)
    award_date = models.DateField()
    citation = models.TextField(blank=True)
    certificate_issued = models.BooleanField(default=False)
    awarded_by = models.ForeignKey(
        'globals.ExtraInfo', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='awarded_recipients'
    )

    class Meta:
        db_table = 'spacs_award_recipient'
        unique_together = ['award', 'student', 'academic_year']

    def __str__(self):
        return f"{self.student} - {self.award.name} ({self.academic_year})"


class MeritList(models.Model):
    """Batch-wise generated merit list"""
    batch = models.CharField(max_length=20)
    programme = models.CharField(max_length=50, null=True, blank=True)
    academic_year = models.CharField(max_length=9)
    semester = models.IntegerField()
    generated_date = models.DateTimeField(auto_now_add=True)
    generated_by = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'spacs_merit_list'
        unique_together = ['batch', 'programme', 'academic_year', 'semester']

    def __str__(self):
        return f"Merit List - {self.batch} {self.programme} ({self.academic_year} S{self.semester})"


class MeritListEntry(models.Model):
    """Individual student entry in a merit list"""
    merit_list = models.ForeignKey(MeritList, on_delete=models.CASCADE, related_name='entries')
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    rank = models.IntegerField()
    cgpa = models.FloatField(null=True, blank=True)
    total_credits = models.IntegerField(null=True, blank=True)
    eligible_for_scholarships = models.BooleanField(default=False)
    remarks = models.TextField(blank=True)

    class Meta:
        db_table = 'spacs_merit_list_entry'
        unique_together = ['merit_list', 'student']
        ordering = ['rank']

    def __str__(self):
        return f"Rank {self.rank}: {self.student.id}"


class ScholarshipEligibilityLog(models.Model):
    """Audit log for eligibility checks"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    scholarship = models.ForeignKey(Award_and_scholarship, on_delete=models.CASCADE)
    checked_date = models.DateTimeField(auto_now_add=True)
    is_eligible = models.BooleanField()
    reasons = models.TextField(blank=True)
    cgpa_at_check = models.FloatField(null=True, blank=True)
    backlog_count = models.IntegerField(default=0)
    dues_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = 'spacs_eligibility_log'

    def __str__(self):
        return f"{self.student.id} - {self.scholarship.award_name} - {'Eligible' if self.is_eligible else 'Not Eligible'}"


class NotificationLog(models.Model):
    """Log of scholarship-related notifications sent to students"""
    recipient_student = models.ForeignKey(Student, on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=50)
    related_application = models.ForeignKey(Application, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    sent_date = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        db_table = 'spacs_notification_log'

    def __str__(self):
        return f"{self.notification_type} to {self.recipient_student.id}"

class McmApplication(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        REVERTED = 'reverted', 'Reverted'
        VERIFIED = 'verified', 'Verified'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    # Base Data
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='mcm_latest_applications')
    email = models.EmailField(max_length=255, blank=True, null=True)
    student_full_name = models.CharField(max_length=255)
    roll_no = models.CharField(max_length=50)
    batch = models.CharField(max_length=50)
    programme = models.CharField(max_length=100)
    mobile_no = models.CharField(max_length=20)
    father_name = models.CharField(max_length=255)
    mother_name = models.CharField(max_length=255)
    category = models.CharField(max_length=50)
    current_cpi = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    current_spi = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    jee_uceed_rank = models.CharField(max_length=100, blank=True, null=True)
    annual_income = models.CharField(max_length=100)
    postal_address = models.TextField()

    # Link Fields
    father_income_certificate_link = models.URLField(max_length=500, blank=True, null=True)
    mother_income_certificate_link = models.URLField(max_length=500, blank=True, null=True)
    caste_certificate_link = models.URLField(max_length=500, blank=True, null=True)
    jee_uceed_scorecard_link = models.URLField(max_length=500, blank=True, null=True)
    undertaking_form_link = models.URLField(max_length=500, blank=True, null=True)
    questionnaire_cum_application_link = models.URLField(max_length=500, blank=True, null=True)
    form_ab_link = models.URLField(max_length=500, blank=True, null=True)
    form_d_link = models.URLField(max_length=500, blank=True, null=True)
    declaration_yes = models.CharField(max_length=10, default='Yes')

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    revert_reason = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'mcm_applications'

    def __str__(self):
        return f"{self.student_full_name} ({self.roll_no}) - {self.status}"

class SingleParentApplication(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        REVERTED = 'reverted', 'Reverted'
        VERIFIED = 'verified', 'Verified'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='single_parent_applications')

    # Basic details
    email = models.EmailField(max_length=255, blank=True, null=True)
    student_full_name = models.CharField(max_length=255)
    roll_no = models.CharField(max_length=50)
    batch = models.CharField(max_length=50)
    programme = models.CharField(max_length=100)

    # Contact details
    mobile_no = models.CharField(max_length=20)
    postal_address = models.TextField()

    # Family details
    father_name = models.CharField(max_length=255)
    mother_name = models.CharField(max_length=255)
    category = models.CharField(max_length=50)
    current_cpi = models.DecimalField(max_digits=4, decimal_places=2)

    # Required uploads
    caste_certificate = models.URLField(max_length=500, blank=True, null=True)
    undertaking_form = models.URLField(max_length=500, blank=True, null=True)
    death_certificate = models.URLField(max_length=500, blank=True, null=True)
    affidavit_no_earning_member = models.URLField(max_length=500, blank=True, null=True)

    declaration_yes = models.CharField(max_length=10, default='Yes')

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    revert_reason = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'single_parent_application'

    def __str__(self):
        return f"{self.student_full_name} ({self.roll_no}) - {self.status}"




class MeritListRecord(models.Model):
    batch = models.CharField(max_length=50)
    branch = models.CharField(max_length=100)
    full_name = models.CharField(max_length=255)
    roll_no = models.CharField(max_length=50)
    cpi = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)


    class Meta:
        db_table = 'merit_list'

    def __str__(self):
        return f"{self.roll_no} - {self.batch} - {self.branch}"





