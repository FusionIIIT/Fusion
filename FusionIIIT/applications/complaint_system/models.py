# imports
from django.db import models
from django.utils import timezone
import uuid

from applications.globals.models import ExtraInfo

# Class definations:


class Constants:
    AREA = (
        ('hall-1', 'hall-1'),
        ('hall-3', 'hall-3'),
        ('hall-4', 'hall-4'),
        ('library', 'CC1'),
        ('computer center', 'CC2'),
        ('core_lab', 'core_lab'),
        ('LHTC', 'LHTC'),
        ('NR2', 'NR2'),
        ('NR3', 'NR3'),
        ('Admin building', 'Admin building'),
        ('Rewa_Residency', 'Rewa_Residency'),
        ('Maa Saraswati Hostel', 'Maa Saraswati Hostel'),
        ('Nagarjun Hostel', 'Nagarjun Hostel'),
        ('Panini Hostel', 'Panini Hostel'),

    )
    COMPLAINT_TYPE = (
        ('Electricity', 'Electricity'),
        ('carpenter', 'carpenter'),
        ('plumber', 'plumber'),
        ('garbage', 'garbage'),
        ('dustbin', 'dustbin'),
        ('internet', 'internet'),
        ('other', 'other'),
    )


class ComplaintPriority:
    URGENT = 'Urgent'
    STANDARD = 'Standard'
    LOW = 'Low'

    CHOICES = (
        (URGENT, URGENT),
        (STANDARD, STANDARD),
        (LOW, LOW),
    )


class VerificationStatus:
    PENDING = 'Pending'
    APPROVED = 'Approved'
    REJECTED = 'Rejected'

    CHOICES = (
        (PENDING, PENDING),
        (APPROVED, APPROVED),
        (REJECTED, REJECTED),
    )


class ComplaintStatus:
    PENDING = 0
    IN_PROGRESS = 1
    RESOLVED = 2
    CLOSED = 3
    ESCALATED = 4
    REOPENED = 5

    CHOICES = (
        (PENDING, 'Pending'),
        (IN_PROGRESS, 'In Progress'),
        (RESOLVED, 'Resolved'),
        (CLOSED, 'Closed'),
        (ESCALATED, 'Escalated'),
        (REOPENED, 'Reopened'),
    )


class Caretaker(models.Model):
    staff_id = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    area = models.CharField(choices=Constants.AREA, max_length=20, default='hall-3')
    rating = models.IntegerField(default=0)
    myfeedback = models.CharField(max_length=400, default='this is my feedback')
    # no_of_comps = models.CharField(max_length=1000)

    def __str__(self):
        return str(self.id) + '-' + str(self.area)

class SectionIncharge(models.Model):
    staff_id = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    work_type = models.CharField(choices=Constants.COMPLAINT_TYPE,
                                   max_length=20, default='Electricity')

    def __str__(self):
        return str(self.id) + '-' + self.work_type

class Workers(models.Model):
    secincharge_id = models.ForeignKey(SectionIncharge, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=50)
    age = models.CharField(max_length=10)
    phone = models.BigIntegerField(blank=True)
    worker_type = models.CharField(choices=Constants.COMPLAINT_TYPE,
                                   max_length=20, default='internet')

    def __str__(self):
        return str(self.id) + '-' + self.name


class StudentComplain(models.Model):
    complaint_ref = models.CharField(max_length=32, unique=True, blank=True)
    complainer = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    complaint_date = models.DateTimeField(default=timezone.now)
    submitted_at = models.DateTimeField(blank=True, null=True)
    is_draft = models.BooleanField(default=False)
    complaint_finish = models.DateField(blank=True, null=True)
    priority = models.CharField(max_length=20, choices=ComplaintPriority.CHOICES, default=ComplaintPriority.STANDARD)
    sla_deadline = models.DateTimeField(blank=True, null=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    closed_at = models.DateTimeField(blank=True, null=True)
    verification_status = models.CharField(max_length=20, choices=VerificationStatus.CHOICES, default=VerificationStatus.PENDING)
    complaint_type = models.CharField(choices=Constants.COMPLAINT_TYPE,
                                      max_length=20, default='internet')
    location = models.CharField(max_length=20, choices=Constants.AREA)
    specific_location = models.CharField(max_length=50, blank=True)
    details = models.CharField(max_length=100)
    status = models.IntegerField(choices=ComplaintStatus.CHOICES, default=ComplaintStatus.PENDING)
    remarks = models.CharField(max_length=300, default="Pending")
    flag = models.IntegerField(default='0')
    reason = models.CharField(max_length=100, blank=True, default="None")
    feedback = models.CharField(max_length=500, blank=True)
    worker_id = models.ForeignKey(Workers, blank=True, null=True,on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(Workers, blank=True, null=True, related_name='assigned_complaints', on_delete=models.SET_NULL)
    assigned_team = models.CharField(max_length=100, blank=True, default='')
    upload_complaint = models.FileField(blank=True)
    progress_attachment = models.FileField(blank=True, upload_to='complaint/progress/')
    comment = models.CharField(max_length=100,  default="None")
    progress_notes = models.TextField(blank=True, default='')
    estimated_resolution_time = models.DateTimeField(blank=True, null=True)
    is_escalated = models.IntegerField(default=0)  # 0=Not escalated, 1=Escalated
    escalation_reason = models.CharField(max_length=300, blank=True, default="")
    escalated_date = models.DateTimeField(blank=True, null=True)
    verification_source = models.CharField(max_length=20, blank=True, default='')
    verification_notes = models.TextField(blank=True, default='')
    reopen_requested = models.BooleanField(default=False)
    reopen_reason = models.CharField(max_length=300, blank=True, default='')
    reopen_requested_at = models.DateTimeField(blank=True, null=True)
    reopened_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    #upload_resolved = models.FileField(blank=True,null=True)

    def __str__(self):
        return str(self.complainer.user.username)

    def save(self, *args, **kwargs):
        if not self.complaint_ref:
            prefix = 'DRF' if self.is_draft else 'CMP'
            self.complaint_ref = f"{prefix}-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

        if self.sla_deadline and not self.complaint_finish:
            self.complaint_finish = self.sla_deadline.date()

        super().save(*args, **kwargs)


class ComplaintEvent(models.Model):
    complaint = models.ForeignKey(StudentComplain, related_name='events', on_delete=models.CASCADE)
    actor = models.ForeignKey(ExtraInfo, blank=True, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=50)
    from_status = models.IntegerField(blank=True, null=True)
    to_status = models.IntegerField(blank=True, null=True)
    note = models.TextField(blank=True, default='')
    metadata = models.JSONField(blank=True, default=dict)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('created_at', 'id')

    def __str__(self):
        return f"{self.complaint_id}:{self.action}:{self.created_at.isoformat()}"


class Supervisor(models.Model):
    sup_id = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    type = models.CharField(choices=Constants.COMPLAINT_TYPE, max_length=30,default='Electricity')
    area = models.CharField(max_length=30, blank=True, default='')

    def __str__(self):
        scope = self.area or 'all-areas'
        return str(self.sup_id) + '-' + str(self.type) + '-' + scope
