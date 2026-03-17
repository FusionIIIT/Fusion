import datetime
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext as _

from applications.academic_information.models import Student
from django.contrib.auth.models import User

# Class definations:


class Constants:
    RESUME_TYPE = (
        ('ONGOING', 'Ongoing'),
        ('COMPLETED', 'Completed'),
    )

    ACHIEVEMENT_TYPE = (
        ('EDUCATIONAL', 'Educational'),
        ('OTHER', 'Other'),
    )

    EVENT_TYPE = (
        ('SOCIAL', 'Social'),
        ('CULTURE', 'Culture'),
        ('SPORT', 'Sport'),
        ('OTHER', 'Other'),
    )

    INVITATION_TYPE = (
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('PENDING', 'Pending'),
        ('IGNORE', 'IGNORE'),
    )

    PLACEMENT_TYPE = (
        ('PLACEMENT', 'Placement'),
        ('PBI', 'PBI'),
        ('HIGHER STUDIES', 'Higher Studies'),
        ('OTHER', 'Other'),
    )

    PLACED_TYPE = (
        ('NOT PLACED', 'Not Placed'),
        ('PLACED', 'Placed'),
    )

    DEBAR_TYPE = (
        ('NOT DEBAR', 'Not Debar'),
        ('DEBAR', 'Debar'),
    )

    BTECH_DEP = (
        ('CSE', 'CSE'),
        ('ME','ME'),
        ('ECE','ECE'),
          ('SM','SM'),
    )

    BDES_DEP = (
        ('DESIGN', 'DESIGN'),
    )

    MTECH_DEP = (
        ('CSE', 'CSE'),
        ('CAD/CAM', 'CAD/CAM'),
        ('DESIGN', 'DESIGN'),
        ('MANUFACTURING', 'MANUFACTURING'),
        ('MECHATRONICS', 'MECHATRONICS'),
    )

    MDES_DEP = (
        ('DESIGN', 'DESIGN'),
    )

    PHD_DEP = (
        ('CSE', 'CSE'),
        ('ME','ME'),
        ('ECE','ECE'),
        ('DESIGN', 'DESIGN'),
        ('NS', 'NS'),
    )

    # ---- PCMS New Constants ----

    COMPANY_APPROVAL_STATUS = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )

    JOB_TYPE = (
        ('PLACEMENT', 'Placement'),
        ('INTERNSHIP', 'Internship'),
        ('PBI', 'PBI'),
    )

    APPLICATION_STATUS = (
        ('APPLIED', 'Applied'),
        ('SHORTLISTED', 'Shortlisted'),
        ('INTERVIEW_SCHEDULED', 'Interview Scheduled'),
        ('OFFER_EXTENDED', 'Offer Extended'),
        ('OFFER_ACCEPTED', 'Offer Accepted'),
        ('OFFER_REJECTED', 'Offer Rejected'),
        ('REJECTED', 'Rejected'),
    )

    INTERVIEW_MODE = (
        ('ONLINE', 'Online'),
        ('OFFLINE', 'Offline'),
    )

    OFFER_STATUS = (
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('EXPIRED', 'Expired'),
    )

    ANNOUNCEMENT_TYPE = (
        ('PLACEMENT_DRIVE', 'Placement Drive'),
        ('COMPANY_VISIT', 'Company Visit'),
        ('TRAINING_SESSION', 'Training Session'),
        ('WORKSHOP', 'Workshop'),
        ('INTERNSHIP', 'Internship Program'),
        ('GENERAL', 'General'),
    )


class Project(models.Model):
    unique_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    project_name = models.CharField(max_length=50, default='')
    project_status = models.CharField(max_length=20, choices=Constants.RESUME_TYPE,
                                      default='COMPLETED')
    summary = models.TextField(max_length=1000, default='', null=True, blank=True)
    project_link = models.CharField(max_length=200, default='', null=True, blank=True)
    sdate = models.DateField(_("Date"), default=datetime.date.today)
    edate = models.DateField(null=True, blank=True)

    def __str__(self):
        return '{} - {}'.format(self.unique_id.id, self.project_name)


class Skill(models.Model):
    skill = models.CharField(max_length=30, default='')

    def __str__(self):
        return self.skill


class Has(models.Model):
    skill_id = models.ForeignKey(Skill, on_delete=models.CASCADE)
    unique_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    skill_rating = models.IntegerField(default=80)

    class Meta:
        unique_together = (('skill_id', 'unique_id'),)

    def __str__(self):
        return '{} - {}'.format(self.unique_id.id, self.skill_id.skill)


class Education(models.Model):
    unique_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    degree = models.CharField(max_length=40, default='')
    grade = models.CharField(max_length=10, default='')
    institute = models.TextField(max_length=250, default='')
    stream = models.CharField(max_length=150, default='', null=True, blank=True)
    sdate = models.DateField(_("Date"), default=datetime.date.today)
    edate = models.DateField(null=True, blank=True)

    def clean(self):

        sdate = self.cleaned_data.get("startdate")
        stime = self.cleaned_data.get("starttime")
        print(sdate, "sdate")
        today = datetime.datetime.now() - datetime.timedelta(1)
        print(today, "today")
        k1 = stime.hour
        k2 = stime.minute
        k3 = stime.second
        x = time(k1, k2, k3)
        date = datetime.datetime.combine(sdate, x)
        edate = self.cleaned_data.get("enddate")
        etime = self.cleaned_data.get("endtime")
        k1 = etime.hour
        k2 = etime.minute
        k3 = etime.second
        end_date = datetime.datetime.combine(edate, datetime.time(k1, k2, k3))
        print(date, end_date)
        if(date < today):
            raise forms.ValidationError("Invalid quiz Start Date")
        elif(date > end_date):
            raise forms.ValidationError("Start Date but me before End Date")
        return self.cleaned_data


class Experience(models.Model):
    unique_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    title = models.CharField(max_length=100, default='')
    status = models.CharField(max_length=20, choices=Constants.RESUME_TYPE,
                              default='COMPLETED')
    description = models.TextField(max_length=500, default='', null=True, blank=True)
    company = models.CharField(max_length=200, default='')
    location = models.CharField(max_length=200, default='')
    sdate = models.DateField(_("Date"), default=datetime.date.today)
    edate = models.DateField(null=True, blank=True)

    def __str__(self):
        return '{} - {}'.format(self.unique_id.id, self.company)


class Course(models.Model):
    unique_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    course_name = models.CharField(max_length=100, default='')
    description = models.TextField(max_length=250, default='', null=True, blank=True)
    license_no = models.CharField(max_length=100, default='', null=True, blank=True)
    sdate = models.DateField(_("Date"), default=datetime.date.today)
    edate = models.DateField(null=True, blank=True)

    def __str__(self):
        return '{} - {}'.format(self.unique_id.id, self.course_name)


class Conference(models.Model):
    unique_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    conference_name = models.CharField(max_length=100, default='')
    description = models.TextField(max_length=250, default='', null=True, blank=True)
    sdate = models.DateField(_("Date"), default=datetime.date.today)
    edate = models.DateField(null=True, blank=True)

    def __str__(self):
        return '{} - {}'.format(self.unique_id.id, self.conference_name)


class Publication(models.Model):
    unique_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    publication_title = models.CharField(max_length=100, default='')
    description = models.TextField(max_length=250, default='', null=True, blank=True)
    publisher = models.TextField(max_length=250, default='')
    publication_date = models.DateField(_("Date"), default=datetime.date.today)

    def __str__(self):
        return '{} - {}'.format(self.unique_id.id, self.publication_title)


class Reference(models.Model):
    unique_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    reference_name = models.CharField(max_length=100, default='')
    post = models.CharField(max_length=100, default='', null=True, blank=True)
    email = models.CharField(max_length=50, default='')
    mobile_number = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return '{} - {}'.format(self.unique_id.id, self.reference_name)


class Coauthor(models.Model):
    publication_id = models.ForeignKey(Publication, on_delete=models.CASCADE)
    coauthor_name = models.CharField(max_length=100, default='')

    def __str__(self):
        return '{} - {}'.format(self.publication_id.publication_title, self.coauthor_name)


class Patent(models.Model):
    unique_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    patent_name = models.CharField(max_length=100, default='')
    description = models.TextField(max_length=250, default='', null=True, blank=True)
    patent_office = models.TextField(max_length=250, default='')
    patent_date = models.DateField()

    def __str__(self):
        return '{} - {}'.format(self.unique_id.id, self.patent_name)


class Coinventor(models.Model):
    patent_id = models.ForeignKey(Patent, on_delete=models.CASCADE)
    coinventor_name = models.CharField(max_length=100, default='')

    def __str__(self):
        return '{} - {}'.format(self.patent_id.patent_name, self.coinventor_name)


class Interest(models.Model):
    unique_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    interest = models.CharField(max_length=100, default='')

    def __str__(self):
        return '{} - {}'.format(self.unique_id.id, self.interest)


class Achievement(models.Model):
    unique_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    achievement = models.CharField(max_length=100, default='')
    achievement_type = models.CharField(max_length=20, choices=Constants.ACHIEVEMENT_TYPE,
                                        default='OTHER')
    description = models.TextField(max_length=1000, default='', null=True, blank=True)
    issuer = models.CharField(max_length=200, default='')
    date_earned = models.DateField(_("Date"), default=datetime.date.today)

    def __str__(self):
        return '{} - {}'.format(self.unique_id.id, self.achievement)

class Extracurricular(models.Model):
    unique_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    event_name = models.CharField(max_length=100, default='')
    event_type = models.CharField(max_length=20, choices=Constants.EVENT_TYPE,
                                        default='OTHER')
    description = models.TextField(max_length=1000, default='', null=True, blank=True)
    name_of_position = models.CharField(max_length=200, default='')
    date_earned = models.DateField(_("Date"), default=datetime.date.today)

    def __str__(self):
        return '{} - {}'.format(self.unique_id.id, self.event_name)


class MessageOfficer(models.Model):
    message = models.CharField(max_length=100, default='')
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.message


class NotifyStudent(models.Model):
    placement_type = models.CharField(max_length=20, choices=Constants.PLACEMENT_TYPE,
                                      default='PLACEMENT')
    company_name = models.CharField(max_length=100, default='')
    ctc = models.DecimalField(decimal_places=4, max_digits=10)
    description = models.TextField(max_length=1000, default='', null=True, blank=True)
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{} - {}'.format(self.company_name, self.placement_type)

    @property
    def get_placement_schedule_object(self):
        return PlacementSchedule.objects.filter(notify_id=self.id).first()


class Role(models.Model):
    role = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.role

class CompanyDetails(models.Model):
    company_name = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.company_name


class PlacementStatus(models.Model):
    notify_id = models.ForeignKey(NotifyStudent, on_delete=models.CASCADE)
    unique_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    invitation = models.CharField(max_length=20, choices=Constants.INVITATION_TYPE,
                                  default='PENDING')
    placed = models.CharField(max_length=20, choices=Constants.PLACED_TYPE,
                              default='NOT PLACED')
    timestamp = models.DateTimeField(auto_now=True)
    no_of_days = models.IntegerField(default=10, null=True, blank=True)

    class Meta:
        unique_together = (('notify_id', 'unique_id'),)

    @property
    def response_date(self):
        return self.timestamp+datetime.timedelta(days=self.no_of_days)

    def __str__(self):
        return '{} - {}'.format(self.unique_id.id, self.notify_id.company_name)


class PlacementRecord(models.Model):
    placement_type = models.CharField(max_length=20, choices=Constants.PLACEMENT_TYPE,
                                      default='PLACEMENT')
    name = models.CharField(max_length=100, default='')
    ctc = models.DecimalField(decimal_places=2, max_digits=5, default=0)
    year = models.IntegerField(default=0)
    test_score = models.IntegerField(default=0, null=True, blank=True)
    test_type = models.CharField(max_length=30, default='', null=True, blank=True)

    def __str__(self):
        return '{} - {}'.format(self.name, self.year)


class StudentRecord(models.Model):
    record_id = models.ForeignKey(PlacementRecord, on_delete=models.CASCADE)
    unique_id = models.ForeignKey(Student, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('record_id', 'unique_id'),)

    def __str__(self):
        return '{} - {}'.format(self.unique_id.id, self.record_id.name)


class ChairmanVisit(models.Model):
    company_name = models.CharField(max_length=100, default='')
    location = models.CharField(max_length=100, default='')
    visiting_date = models.DateField(_("Date"), default=datetime.date.today)
    description = models.TextField(max_length=1000, default='', null=True, blank=True)
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.company_name


class PlacementSchedule(models.Model):
    notify_id = models.ForeignKey(NotifyStudent, on_delete=models.CASCADE)
    title = models.CharField(max_length=100, default='')
    placement_date = models.DateField(_("Date"), default=datetime.date.today)
    location = models.CharField(max_length=100, default='')
    description = models.TextField(max_length=500, default='', null=True, blank=True)
    time = models.TimeField()
    role = models.ForeignKey(Role, on_delete=models.CASCADE, null=True, blank=True)
    attached_file = models.FileField(upload_to='documents/placement/schedule', null=True, blank=True)
    schedule_at = models.DateTimeField(auto_now_add=False, auto_now=False, default=timezone.now, blank=True, null=True)

    def __str__(self):
        return '{} - {}'.format(self.notify_id.company_name, self.placement_date)

    @property
    def get_role(self):
        try:
            return self.role.role
        except:
            return ''


class StudentPlacement(models.Model):
    unique_id = models.OneToOneField(Student, primary_key=True, on_delete=models.CASCADE)
    debar = models.CharField(max_length=20, choices=Constants.DEBAR_TYPE, default='NOT DEBAR')
    future_aspect = models.CharField(max_length=20, choices=Constants.PLACEMENT_TYPE,
                                     default='PLACEMENT')
    placed_type = models.CharField(max_length=20, choices=Constants.PLACED_TYPE,
                                   default='NOT PLACED')
    placement_date = models.DateField(_("Date"), default=datetime.date.today, null=True,
                                      blank=True)
    package = models.DecimalField(decimal_places=2, max_digits=5, null=True,
                                  blank=True)

    def __str__(self):
        return self.unique_id.id.id


# =============================================
# PCMS NEW MODELS
# =============================================

class Company(models.Model):
    """
    Represents a recruiting company registered on the placement system.
    Companies register and are subject to approval by the TPO.
    """
    name = models.CharField(max_length=200)
    website = models.URLField(max_length=300, blank=True, null=True)
    description = models.TextField(max_length=2000, blank=True, null=True)
    domain = models.CharField(max_length=200, blank=True, null=True,
                              help_text="Industry domain, e.g., IT, Finance, Manufacturing")
    contact_person_name = models.CharField(max_length=200, blank=True, null=True)
    contact_email = models.EmailField(max_length=200)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(max_length=500, blank=True, null=True)
    logo = models.ImageField(upload_to='placement/company_logos/', blank=True, null=True)
    approval_status = models.CharField(
        max_length=20,
        choices=Constants.COMPANY_APPROVAL_STATUS,
        default='PENDING'
    )
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approved_companies'
    )
    registered_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='registered_companies',
        help_text="The TPO/user who registered this company"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Companies"
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class JobPosting(models.Model):
    """
    Represents a job or internship opportunity posted by a company.
    TPO uploads postings on behalf of companies. Includes eligibility criteria.
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='job_postings')
    title = models.CharField(max_length=200, help_text="Job title / role name")
    description = models.TextField(max_length=3000)
    job_type = models.CharField(max_length=20, choices=Constants.JOB_TYPE, default='PLACEMENT')
    location = models.CharField(max_length=200, blank=True, null=True)
    ctc = models.DecimalField(decimal_places=2, max_digits=10, help_text="CTC / Stipend in LPA")
    bond_details = models.TextField(max_length=500, blank=True, null=True)

    # Eligibility criteria
    min_cpi = models.FloatField(default=0.0, help_text="Minimum CPI required")
    eligible_programmes = models.CharField(
        max_length=200, blank=True, null=True,
        help_text="Comma-separated: B.Tech,M.Tech,B.Des,M.Des,PhD"
    )
    eligible_branches = models.CharField(
        max_length=300, blank=True, null=True,
        help_text="Comma-separated: CSE,ECE,ME,SM,DESIGN"
    )
    eligible_batch_from = models.IntegerField(
        null=True, blank=True,
        help_text="Minimum batch year (e.g., 2022)"
    )
    eligible_batch_to = models.IntegerField(
        null=True, blank=True,
        help_text="Maximum batch year (e.g., 2026)"
    )
    required_skills = models.ManyToManyField(Skill, blank=True, related_name='required_for_jobs')
    backlog_allowed = models.BooleanField(default=False)

    # Deadlines & status
    application_deadline = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    posted_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='posted_jobs',
        help_text="TPO who posted this"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    attached_file = models.FileField(
        upload_to='documents/placement/job_postings/', null=True, blank=True
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return '{} - {}'.format(self.company.name, self.title)

    @property
    def is_deadline_passed(self):
        return timezone.now() > self.application_deadline

    @property
    def total_applications(self):
        return self.applications.count()


class JobApplication(models.Model):
    """
    Tracks a student's application to a specific job posting.
    Status moves through the pipeline: Applied → Shortlisted → Interview Scheduled → Offer Extended → Accepted/Rejected.
    """
    job_posting = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='applications')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='job_applications')
    status = models.CharField(
        max_length=30,
        choices=Constants.APPLICATION_STATUS,
        default='APPLIED'
    )
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resume_link = models.FileField(
        upload_to='documents/placement/resumes/', null=True, blank=True
    )
    remarks = models.TextField(max_length=500, blank=True, null=True,
                               help_text="Remarks by TPO or Company")

    class Meta:
        unique_together = (('job_posting', 'student'),)
        ordering = ['-applied_at']

    def __str__(self):
        return '{} applied for {} at {}'.format(
            self.student.id.user.username,
            self.job_posting.title,
            self.job_posting.company.name
        )


class InterviewSchedule(models.Model):
    """
    Tracks interview schedules for shortlisted students for a job posting.
    """
    job_posting = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='interviews')
    date = models.DateField()
    time_slot = models.TimeField()
    mode = models.CharField(max_length=10, choices=Constants.INTERVIEW_MODE, default='OFFLINE')
    venue_or_link = models.CharField(
        max_length=500, blank=True, null=True,
        help_text="Physical venue or online meeting link"
    )
    description = models.TextField(max_length=1000, blank=True, null=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_interviews'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'time_slot']

    def __str__(self):
        return 'Interview for {} on {}'.format(self.job_posting.title, self.date)


class InterviewPanel(models.Model):
    """
    Links shortlisted students to a specific interview schedule.
    """
    interview = models.ForeignKey(InterviewSchedule, on_delete=models.CASCADE, related_name='panelists')
    application = models.ForeignKey(JobApplication, on_delete=models.CASCADE, related_name='interview_panels')
    remarks = models.TextField(max_length=500, blank=True, null=True)
    result = models.CharField(
        max_length=20, blank=True, null=True,
        help_text="SELECTED / REJECTED / WAITLISTED"
    )

    class Meta:
        unique_together = (('interview', 'application'),)

    def __str__(self):
        return '{} - {}'.format(self.application.student.id.user.username, self.interview)


class JobOffer(models.Model):
    """
    Represents a job offer extended by a company to a student through the placement system.
    Students must accept/reject within a deadline.
    """
    application = models.OneToOneField(JobApplication, on_delete=models.CASCADE, related_name='offer')
    ctc_offered = models.DecimalField(decimal_places=2, max_digits=10)
    designation_offered = models.CharField(max_length=200, blank=True, null=True)
    joining_date = models.DateField(null=True, blank=True)
    offer_letter = models.FileField(
        upload_to='documents/placement/offer_letters/', null=True, blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=Constants.OFFER_STATUS,
        default='PENDING'
    )
    response_deadline = models.DateTimeField(
        help_text="Deadline for student to accept/reject"
    )
    extended_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-extended_at']

    def __str__(self):
        return 'Offer to {} from {}'.format(
            self.application.student.id.user.username,
            self.application.job_posting.company.name
        )

    @property
    def is_deadline_passed(self):
        return timezone.now() > self.response_deadline and self.status == 'PENDING'


class Announcement(models.Model):
    """
    Official announcements by TPO or Placement Chairman related to placement activities.
    """
    title = models.CharField(max_length=200)
    content = models.TextField(max_length=3000)
    announcement_type = models.CharField(
        max_length=30,
        choices=Constants.ANNOUNCEMENT_TYPE,
        default='GENERAL'
    )
    target_audience = models.CharField(
        max_length=200, blank=True, null=True,
        help_text="Comma-separated: ALL,B.Tech,M.Tech,CSE,ECE etc."
    )
    attached_file = models.FileField(
        upload_to='documents/placement/announcements/', null=True, blank=True
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='placement_announcements'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class PlacementPolicy(models.Model):
    """
    Configurable placement policies enforced by the system.
    E.g., max number of offers, dream company rules, etc.
    """
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(max_length=1000, blank=True, null=True)
    max_offers_allowed = models.IntegerField(
        default=1,
        help_text="Maximum active offers a student can hold at a time"
    )
    allow_dream_company = models.BooleanField(
        default=False,
        help_text="Allow students to apply to dream companies after being placed"
    )
    dream_ctc_threshold = models.DecimalField(
        decimal_places=2, max_digits=10, default=0,
        help_text="Minimum CTC (LPA) for dream company classification"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Placement Policies"

    def __str__(self):
        return self.name

