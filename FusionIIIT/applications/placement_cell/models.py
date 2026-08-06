# imports
import datetime

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext as _

from applications.academic_information.models import Student
from applications.globals.models import ExtraInfo

User = get_user_model()

# Class definations:


def validate_start_before_end(*, start_date, end_date, start_field='sdate', end_field='edate'):
    if start_date and end_date and start_date >= end_date:
        raise ValidationError({
            start_field: _('Start date must be earlier than end date.'),
            end_field: _('End date must be later than start date.'),
        })


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


class Project(models.Model):
    unique_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    project_name = models.CharField(max_length=50, default='')
    project_status = models.CharField(max_length=20, choices=Constants.RESUME_TYPE,
                                      default='COMPLETED')
    summary = models.TextField(max_length=1000, default='', null=True, blank=True)
    project_link = models.CharField(max_length=200, default='', null=True, blank=True)
    sdate = models.DateField(_("Date"), default=datetime.date.today)
    edate = models.DateField(null=True, blank=True)

    def clean(self):
        super().clean()
        validate_start_before_end(start_date=self.sdate, end_date=self.edate)

    def __str__(self):
        return '{} - {}'.format(self.unique_id.id, self.project_name)


class Skill(models.Model):
    skill = models.CharField(max_length=30, default='')

    def __str__(self):
        return self.skill


class Has(models.Model):
    skill_id = models.ForeignKey(Skill, on_delete=models.CASCADE)
    unique_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    skill_rating = models.IntegerField(
        default=80,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

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
        super().clean()
        validate_start_before_end(start_date=self.sdate, end_date=self.edate)


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

    def clean(self):
        super().clean()
        validate_start_before_end(start_date=self.sdate, end_date=self.edate)

    def __str__(self):
        return '{} - {}'.format(self.unique_id.id, self.company)


class Course(models.Model):
    unique_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    course_name = models.CharField(max_length=100, default='')
    description = models.TextField(max_length=250, default='', null=True, blank=True)
    license_no = models.CharField(max_length=100, default='', null=True, blank=True)
    sdate = models.DateField(_("Date"), default=datetime.date.today)
    edate = models.DateField(null=True, blank=True)

    def clean(self):
        super().clean()
        validate_start_before_end(start_date=self.sdate, end_date=self.edate)

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

    class Meta:
        indexes = [
            models.Index(fields=['placement_type']),
            models.Index(fields=['company_name']),
        ]

    @property
    def get_placement_schedule_object(self):
        return PlacementSchedule.objects.filter(notify_id=self.id).first()


class Role(models.Model):
    role = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.role

class CompanyDetails(models.Model):
    company_name = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(max_length=1000, default='', blank=True)
    address = models.TextField(max_length=1000, default='', blank=True)
    website = models.CharField(max_length=255, default='', blank=True)
    logo = models.ImageField(
        upload_to='documents/placement/company_logos',
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.company_name


class PlacementField(models.Model):
    FIELD_TYPES = (
        ('text', 'Text'),
        ('number', 'Number'),
        ('decimal', 'Decimal'),
        ('date', 'Date'),
        ('time', 'Time'),
    )

    name = models.CharField(max_length=100, unique=True)
    type = models.CharField(max_length=20, choices=FIELD_TYPES, default='text')
    required = models.BooleanField(default=False)

    def __str__(self):
        return self.name


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
        indexes = [
            models.Index(fields=['unique_id', 'invitation']),
            models.Index(fields=['unique_id', 'timestamp']),
        ]

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
        indexes = [
            models.Index(fields=['unique_id', 'record_id']),
        ]

    def __str__(self):
        return '{} - {}'.format(self.unique_id.id, self.record_id.name)


class ChairmanVisit(models.Model):
    company_name = models.CharField(max_length=100, default='')
    location = models.CharField(max_length=100, default='')
    visiting_date = models.DateField(_("Date"), default=datetime.date.today)
    start_date = models.DateField(_("Start Date"), default=datetime.date.today)
    end_date = models.DateField(_("End Date"), null=True, blank=True)
    description = models.TextField(max_length=1000, default='', null=True, blank=True)
    timestamp = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()
        validate_start_before_end(
            start_date=self.start_date,
            end_date=self.end_date,
            start_field='start_date',
            end_field='end_date',
        )

    def save(self, *args, **kwargs):
        if self.start_date and not self.visiting_date:
            self.visiting_date = self.start_date
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.company_name


class PlacementSchedule(models.Model):
    notify_id = models.ForeignKey(NotifyStudent, on_delete=models.CASCADE)
    title = models.CharField(max_length=100, default='')
    placement_date = models.DateField(_("Date"), default=datetime.date.today)
    end_date = models.DateField(_("Date"), null=True, blank=True)
    location = models.CharField(max_length=100, default='')
    description = models.TextField(max_length=500, default='', null=True, blank=True)
    eligibility = models.TextField(max_length=1000, default='', blank=True)
    passoutyr = models.CharField(max_length=20, default='', blank=True)
    gender = models.CharField(max_length=20, default='', blank=True)
    cpi = models.CharField(max_length=20, default='', blank=True)
    branch = models.CharField(max_length=100, default='', blank=True)
    time = models.TimeField()
    role = models.ForeignKey(Role, on_delete=models.CASCADE, null=True, blank=True)
    attached_file = models.FileField(upload_to='documents/placement/schedule', null=True, blank=True)
    schedule_at = models.DateTimeField(auto_now_add=False, auto_now=False, default=timezone.now, blank=True, null=True)
    end_datetime = models.DateTimeField(blank=True, null=True)
    company = models.ForeignKey(CompanyDetails, on_delete=models.SET_NULL, null=True, blank=True)
    fields = models.ManyToManyField(PlacementField, blank=True)

    def __str__(self):
        return '{} - {}'.format(self.notify_id.company_name, self.placement_date)

    class Meta:
        indexes = [
            models.Index(fields=['placement_date']),
            models.Index(fields=['schedule_at']),
            models.Index(fields=['notify_id', 'placement_date']),
        ]

    @property
    def get_role(self):
        try:
            return self.role.role
        except:
            return ''


class StudentPlacement(models.Model):
    unique_id = models.OneToOneField(Student, primary_key=True, on_delete=models.CASCADE)
    debar = models.CharField(max_length=20, choices=Constants.DEBAR_TYPE, default='NOT DEBAR')
    debar_reason = models.TextField(max_length=1000, default='', blank=True)
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


class PlacementApplication(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('shortlisted', 'Shortlisted'),
        ('interview_scheduled', 'Interview Scheduled'),
        ('interview_completed', 'Interview Completed'),
        ('offer_released', 'Offer Released'),
        ('accept', 'Accept'),
        ('reject', 'Reject'),
        ('withdrawn', 'Withdrawn'),
    )

    schedule = models.ForeignKey(PlacementSchedule, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    remarks = models.TextField(max_length=1000, default='', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    withdrawn_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = (('schedule', 'student'),)
        indexes = [
            models.Index(fields=['student', 'created_at']),
            models.Index(fields=['schedule', 'created_at']),
            models.Index(fields=['student', 'status']),
            models.Index(fields=['schedule', 'status']),
        ]

    def __str__(self):
        return '{} - {}'.format(self.student.id.id, self.schedule.id)


class PlacementApplicationResponse(models.Model):
    application = models.ForeignKey(PlacementApplication, on_delete=models.CASCADE)
    field = models.ForeignKey(PlacementField, on_delete=models.CASCADE, null=True, blank=True)
    value = models.TextField(max_length=5000, default='', blank=True)

    def __str__(self):
        return '{} - {}'.format(self.application.id, self.field_id)


class PlacementRound(models.Model):
    schedule = models.ForeignKey(PlacementSchedule, on_delete=models.CASCADE)
    round_no = models.IntegerField(default=0)
    test_date = models.DateField(null=True, blank=True)
    start_datetime = models.DateTimeField(null=True, blank=True)
    end_datetime = models.DateTimeField(null=True, blank=True)
    mode = models.CharField(max_length=30, default='', blank=True)
    location_link = models.CharField(max_length=255, default='', blank=True)
    description = models.TextField(max_length=1000, default='', blank=True)
    test_type = models.CharField(max_length=100, default='', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('round_no', 'created_at')
        indexes = [
            models.Index(fields=['schedule', 'round_no']),
            models.Index(fields=['schedule', 'start_datetime']),
        ]

    def __str__(self):
        return '{} - {}'.format(self.schedule.id, self.round_no)


class PlacementApplicationTimeline(models.Model):
    application = models.ForeignKey(PlacementApplication, on_delete=models.CASCADE, related_name='timeline_entries')
    stage = models.CharField(max_length=100, default='')
    remarks = models.TextField(max_length=1000, default='', blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('created_at', 'id')
        indexes = [
            models.Index(fields=['application', 'created_at']),
        ]

    def __str__(self):
        return '{} - {}'.format(self.application.id, self.stage)


class PlacementInterviewSchedule(models.Model):
    OUTCOME_CHOICES = (
        ('pending', 'Pending'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('selected', 'Selected'),
    )

    application = models.ForeignKey(PlacementApplication, on_delete=models.CASCADE, related_name='interview_schedules')
    round_no = models.IntegerField(default=1)
    title = models.CharField(max_length=100, default='', blank=True)
    scheduled_at = models.DateTimeField()
    end_datetime = models.DateTimeField(null=True, blank=True)
    mode = models.CharField(max_length=30, default='', blank=True)
    location = models.CharField(max_length=255, default='', blank=True)
    meeting_link = models.CharField(max_length=255, default='', blank=True)
    remarks = models.TextField(max_length=1000, default='', blank=True)
    outcome = models.CharField(max_length=20, choices=OUTCOME_CHOICES, default='pending')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-scheduled_at', '-id')
        indexes = [
            models.Index(fields=['application', 'scheduled_at']),
            models.Index(fields=['application', 'round_no']),
        ]

    def __str__(self):
        return '{} - {}'.format(self.application.id, self.title or self.round_no)


class PlacementRestriction(models.Model):
    criteria = models.CharField(max_length=50)
    condition = models.CharField(max_length=50)
    value = models.CharField(max_length=255)
    description = models.TextField(max_length=1000, default='', blank=True)

    def __str__(self):
        return '{} - {}'.format(self.criteria, self.condition)


class PlacementPolicy(models.Model):
    title = models.CharField(max_length=150)
    description = models.TextField(max_length=3000)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-updated_at', '-id')

    def __str__(self):
        return self.title


class PlacementProfileDocument(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, default='Supporting Document')
    document = models.FileField(upload_to='documents/placement/profile_documents')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-uploaded_at', '-id')
        indexes = [
            models.Index(fields=['student', 'uploaded_at']),
        ]

    def __str__(self):
        return '{} - {}'.format(self.student.id.id, self.name)


class PlacementProfileAuditLog(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    actor = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=100)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at', '-id')

    def __str__(self):
        return '{} - {}'.format(self.student.id.id, self.action)


class PlacementNotificationPreference(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE)
    enable_portal = models.BooleanField(default=True)
    enable_email = models.BooleanField(default=True)
    enable_sms = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{}'.format(self.student.id.id)


class PlacementAppeal(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    placement_status = models.ForeignKey(PlacementStatus, on_delete=models.CASCADE)
    reason = models.TextField(max_length=2000)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    response = models.TextField(max_length=2000, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = (('student', 'placement_status'),)

    def __str__(self):
        return f"Appeal by {self.student.id} for {self.placement_status.id}"


class PlacementReportSchedule(models.Model):
    FREQUENCY_CHOICES = (
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    )

    REPORT_TYPE_CHOICES = (
        ('batch', 'Batch Summary'),
        ('company', 'Company Summary'),
        ('branch', 'Branch Summary'),
        ('custom', 'Custom Report'),
    )

    FORMAT_CHOICES = (
        ('excel', 'Excel'),
        ('pdf', 'PDF'),
    )

    name = models.CharField(max_length=120)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES, default='custom')
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='weekly')
    export_format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default='excel')
    filters = models.JSONField(default=dict, blank=True)
    recipients = models.TextField(max_length=500, default='', blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    last_run_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-updated_at', '-id')

    def __str__(self):
        return self.name


class AlumniProfile(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    graduation_year = models.IntegerField()
    degree = models.CharField(max_length=100, default='', blank=True)
    current_company = models.CharField(max_length=150, default='', blank=True)
    current_designation = models.CharField(max_length=150, default='', blank=True)
    linkedin_url = models.URLField(blank=True, default='')
    verification_document = models.FileField(
        upload_to='documents/placement/alumni_verification',
        null=True,
        blank=True,
    )
    verification_notes = models.TextField(max_length=1000, default='', blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    topics = models.TextField(max_length=1000, default='', blank=True)
    availability = models.CharField(max_length=200, default='', blank=True)
    bio = models.TextField(max_length=1500, default='', blank=True)
    mentorship_enabled = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_alumni_profiles',
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-updated_at', '-id')

    def __str__(self):
        return '{} - {}'.format(self.user.username, self.status)


class AlumniMentorshipSession(models.Model):
    STATUS_CHOICES = (
        ('requested', 'Requested'),
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    alumni = models.ForeignKey(AlumniProfile, on_delete=models.CASCADE, related_name='sessions')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='alumni_sessions')
    topic = models.CharField(max_length=150)
    agenda = models.TextField(max_length=1500, default='', blank=True)
    scheduled_at = models.DateTimeField()
    mode = models.CharField(max_length=50, default='online', blank=True)
    meeting_link = models.CharField(max_length=300, default='', blank=True)
    student_message = models.TextField(max_length=1500, default='', blank=True)
    alumni_message = models.TextField(max_length=1500, default='', blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('scheduled_at', '-id')

    def __str__(self):
        return '{} - {}'.format(self.alumni.user.username, self.student.id.id)


class AlumniReferral(models.Model):
    alumni = models.ForeignKey(AlumniProfile, on_delete=models.CASCADE, related_name='referrals')
    title = models.CharField(max_length=150)
    company = models.CharField(max_length=150)
    location = models.CharField(max_length=150, default='', blank=True)
    application_url = models.URLField(blank=True, default='')
    description = models.TextField(max_length=2000)
    expires_at = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at', '-id')

    def __str__(self):
        return '{} - {}'.format(self.company, self.title)


class AlumniConnection(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('connected', 'Connected'),
        ('rejected', 'Rejected'),
    )

    alumni = models.ForeignKey(AlumniProfile, on_delete=models.CASCADE, related_name='connections')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='alumni_connections')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(max_length=1000, default='', blank=True)
    responded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alumni_connection_responses',
    )
    responded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('alumni', 'student'),)
        ordering = ('-created_at', '-id')

    def __str__(self):
        return '{} - {}'.format(self.alumni.user.username, self.student.id.id)


class PlacementAnnouncement(models.Model):
    """A placement-cell announcement broadcast to all roles, postable by the TPO."""

    title = models.CharField(max_length=300)
    body = models.TextField()
    posted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='placement_announcements',
    )
    posted_at = models.DateTimeField(auto_now_add=True)
    is_pinned = models.BooleanField(default=False)

    class Meta:
        ordering = ('-is_pinned', '-posted_at')

    def __str__(self):
        return self.title


class OffCampusPlacement(models.Model):
    """An off-campus offer recorded by the TPO against a student roll number."""

    PLACEMENT = 'placement'
    INTERNSHIP = 'internship'
    TYPE_CHOICES = (
        (PLACEMENT, 'Placement'),
        (INTERNSHIP, 'Internship'),
    )

    student = models.ForeignKey(
        ExtraInfo,
        on_delete=models.CASCADE,
        related_name='offcampus_placements',
    )
    company_name = models.CharField(max_length=255)
    role = models.CharField(max_length=200)
    offer_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=PLACEMENT)
    ctc = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stipend = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    offer_date = models.DateField()
    notes = models.TextField(blank=True)
    added_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='added_offcampus_placements',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-offer_date', '-id')

    def __str__(self):
        return '{} - {} ({})'.format(
            self.student.user.username, self.company_name, self.offer_type
        )


class PlacementCalendarEvent(models.Model):
    """A free-form calendar entry the placement cell can add by clicking a date.

    These are separate from drive schedules/rounds: the TPO can drop any note,
    deadline or event onto the placement calendar (interview slots, info
    sessions, document deadlines, etc.). Students only ever read them.
    """

    EVENT = 'event'
    DRIVE = 'drive'
    TEST = 'test'
    INTERVIEW = 'interview'
    DEADLINE = 'deadline'
    OTHER = 'other'
    CATEGORY_CHOICES = (
        (EVENT, 'Event'),
        (DRIVE, 'Drive'),
        (TEST, 'Online Test'),
        (INTERVIEW, 'Interview'),
        (DEADLINE, 'Deadline'),
        (OTHER, 'Other'),
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start = models.DateTimeField()
    end = models.DateTimeField(null=True, blank=True)
    all_day = models.BooleanField(default=False)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default=EVENT)
    location = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='placement_calendar_events',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('start', 'id')

    def __str__(self):
        return self.title
