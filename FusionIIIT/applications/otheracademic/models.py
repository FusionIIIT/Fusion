from datetime import datetime

from applications.globals.models import ExtraInfo, HoldsDesignation, Designation
from django.db import models
from django import forms
from django.contrib.auth.models import User
from applications.academic_information.models import Student
from applications.programme_curriculum.models import Course as ProgrammeCourse
from django.core.exceptions import ValidationError


# ==================== SHARED TEXT CHOICES ====================

class LeaveTypeChoices(models.TextChoices):
    """Shared leave type choices for all leave models."""
    CASUAL = 'Casual', 'Casual'
    MEDICAL = 'Medical', 'Medical'


class LeaveTypePGChoices(models.TextChoices):
    """Extended leave type choices for PG students."""
    CASUAL = 'Casual', 'Casual'
    MEDICAL = 'Medical', 'Medical'
    VACATION = 'Vacation', 'Vacation'
    DUTY = 'Duty', 'Duty'


class LeaveStatusChoices(models.TextChoices):
    """Shared status choices for leave requests."""
    PENDING = 'Pending', 'Pending'
    APPROVED = 'Approved', 'Approved'
    REJECTED = 'Rejected', 'Rejected'


class BonafideStatusChoices(models.TextChoices):
    """Status choices for bonafide requests."""
    PENDING = 'Pending', 'Pending'
    APPROVED = 'Approved', 'Approved'
    REJECTED = 'Rejected', 'Rejected'


# ==================== MODELS ====================

class LeaveFormTable(models.Model):
    """UG student leave request model."""

    student_name = models.CharField(max_length=100)
    roll_no = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    date_from = models.DateField()
    date_to = models.DateField()
    date_of_application = models.DateField()
    upload_file = models.FileField(upload_to='leave_documents/', blank=True, null=True)
    address = models.CharField(max_length=100)
    purpose = models.TextField()
    leave_type = models.CharField(max_length=20, choices=LeaveTypeChoices.choices)
    stud_mobile_no = models.CharField(max_length=100, blank=True, null=True)
    parent_mobile_no = models.CharField(max_length=100, blank=True, null=True)
    leave_mobile_no = models.CharField(max_length=100, blank=True, null=True)
    curr_sem = models.IntegerField(blank=True, null=True)
    approved = models.BooleanField(default=False)
    rejected = models.BooleanField(default=False)
    hod = models.CharField(max_length=100)

    class Meta:
        db_table = 'LeaveFormTable'

    def clean(self):
        if self.date_from > self.date_to:
            raise ValidationError('The start date of leave cannot be later than the end date.')


class LeavePG(models.Model):
    """
    PG student leave request model.

    'leave_from' and 'leave_to' store the start and end date of the leave request.
    'date_of_application' stores the date when the leave request was applied.
    'related_document' stores any related documents or notes for the leave request.
    'place' stores the location where the leave is requested.
    'reason' stores the reason for the leave request.
    'leave_type' stores the type of leave from a dropdown.
    """

    student_name = models.CharField(max_length=100)
    programme = models.CharField(max_length=100)
    discipline = models.CharField(max_length=100)
    Semester = models.CharField(max_length=100)
    roll_no = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    date_from = models.DateField()
    date_to = models.DateField()
    date_of_application = models.DateField()
    upload_file = models.FileField(upload_to='leave_documents/', blank=True, null=True)
    address = models.CharField(max_length=100)
    purpose = models.TextField()
    leave_type = models.CharField(max_length=20, choices=LeaveTypePGChoices.choices)
    mobile_no = models.CharField(max_length=100)
    parent_mobile_no = models.CharField(max_length=100)
    alt_mobile_no = models.CharField(max_length=100)
    ta_approved = models.BooleanField(default=False)
    ta_rejected = models.BooleanField(default=False)
    thesis_approved = models.BooleanField(default=False)
    thesis_rejected = models.BooleanField(default=False)
    hod_approved = models.BooleanField(default=False)
    hod_rejected = models.BooleanField(default=False)
    hod = models.CharField(max_length=100)
    ta_supervisor = models.CharField(max_length=100)
    thesis_supervisor = models.CharField(max_length=100)

    class Meta:
        db_table = 'LeavePG'

    def clean(self):
        if self.date_from > self.date_to:
            raise ValidationError('The start date of leave cannot be later than the end date.')


class LeavePGUpdTable(models.Model):
    """
    PG Leave update table for tracking additional leave information.
    """

    student_name = models.CharField(max_length=100)
    roll_no = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    programme = models.CharField(max_length=100)
    discipline = models.CharField(max_length=100)
    Semester = models.CharField(max_length=100)
    date_from = models.DateField()
    date_to = models.DateField()
    date_of_application = models.DateField()
    upload_file = models.FileField(upload_to='leave_doc')
    address = models.CharField(max_length=100)
    purpose = models.TextField()
    leave_type = models.CharField(max_length=20, choices=LeaveTypePGChoices.choices)
    ta_supervisor = models.CharField(max_length=100)
    mobile_no = models.CharField(max_length=100)
    parent_mobile_no = models.CharField(max_length=100)
    alt_mobile_no = models.CharField(max_length=100)
    ta_approved = models.BooleanField()
    ta_rejected = models.BooleanField()
    hod_approved = models.BooleanField()
    hod_rejected = models.BooleanField()
    hod = models.CharField(max_length=100)

    class Meta:
        db_table = 'LeavePGUpdTable'


class GraduateSeminarFormTable(models.Model):
    """Graduate seminar form model."""

    roll_no = models.CharField(max_length=20)
    semester = models.CharField(max_length=100)
    date_of_seminar = models.DateField()

    class Meta:
        db_table = 'GraduateSeminarFormTable'


class BonafideFormTableUpdated(models.Model):
    """Bonafide application form model."""

    student_names = models.CharField(max_length=100)
    roll_nos = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    branch_types = models.CharField(max_length=50)
    semester_types = models.CharField(max_length=20)
    purposes = models.TextField()
    date_of_applications = models.DateField()
    approve = models.BooleanField(default=False)
    reject = models.BooleanField(default=False)
    download_file = models.FileField(upload_to='Bonafide', blank=True, null=True)

    class Meta:
        db_table = 'BonafideFormTableUpdated'

    @property
    def status(self):
        """Computed status based on approve/reject flags."""
        if self.approve:
            return BonafideStatusChoices.APPROVED
        elif self.reject:
            return BonafideStatusChoices.REJECTED
        return BonafideStatusChoices.PENDING
        


# class AssistantshipClaimFormStatusUpd(models.Model):
#     roll_no = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
#     student_name = models.CharField(max_length=100)
#     discipline = models.CharField(max_length=100)
#     dateFrom = models.DateField()
#     dateTo = models.DateField()
#     # month = models.CharField(max_length=50)
#     # year = models.CharField(max_length=50)
#     bank_account = models.CharField(max_length=100)
#     student_signature = models.FileField(upload_to='student_signatures/')  # Change to FileField
#     dateApplied = models.DateField()
#     ta_supervisor = models.CharField(max_length=100)
#     thesis_supervisor = models.CharField(max_length=100)
#     applicability = models.CharField(max_length=100)
   
#     TA_approved = models.BooleanField()
#     TA_rejected = models.BooleanField()
#     Ths_approved = models.BooleanField()
#     Ths_rejected = models.BooleanField()
#     HOD_approved = models.BooleanField()
#     HOD_rejected = models.BooleanField()
#     Acad_approved = models.BooleanField()
#     Acad_rejected = models.BooleanField()

#     class Meta:
#         db_table = 'AssistantshipClaimFormStausUpd'







class AssistantshipClaimFormStatusUpd(models.Model):
    roll_no = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    student_name = models.CharField(max_length=100)
    discipline = models.CharField(max_length=100)
    dateFrom = models.DateField()
    dateTo = models.DateField()

    bank_account = models.CharField(max_length=100)
    student_signature = models.CharField(max_length=255) 
    dateApplied = models.DateField()
    ta_supervisor = models.CharField(max_length=100)
    thesis_supervisor = models.CharField(max_length=100)
    hod = models.CharField(max_length=100)
    applicability = models.CharField(max_length=100)

    TA_approved = models.BooleanField()
    TA_rejected = models.BooleanField()
    Ths_approved = models.BooleanField()
    Ths_rejected = models.BooleanField()
    HOD_approved = models.BooleanField()
    HOD_rejected = models.BooleanField()
    Acad_approved = models.BooleanField(default=False)
    Acad_rejected = models.BooleanField(default=False)

    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    half_day_leave = models.IntegerField(default=0)
    full_day_leave = models.IntegerField(default=0)

    remark = models.TextField(default='')  # New field with an empty default value

    def clean(self):
        """Validate that end date is after start date."""
        if self.dateFrom and self.dateTo and self.dateTo <= self.dateFrom:
            raise ValidationError("End date must be later than start date")
        return super().clean()

    class Meta:
        db_table = 'AssistantshipClaimFormStausUpd'


class PGTAAssignment(models.Model):
    """Stores TA subject assignment for PG students by dept admin."""

    pg_student = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    subject = models.ForeignKey(ProgrammeCourse, on_delete=models.CASCADE)
    assigned_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'PGTAAssignment'
        constraints = [
            models.UniqueConstraint(
                fields=['pg_student', 'subject'],
                name='uniq_pg_ta_assignment_student_subject',
            )
        ]

    def __str__(self):
        return f"{self.pg_student_id} -> {self.subject.code}"


class PGFacultySupervisorAssignment(models.Model):
    """Stores faculty supervisor assignment for PG students by dept admin."""

    pg_student = models.OneToOneField(ExtraInfo, on_delete=models.CASCADE)
    faculty_supervisor = models.ForeignKey(User, on_delete=models.CASCADE)
    assigned_by = models.ForeignKey(
        User,
        related_name="pg_faculty_supervisor_assigned_by",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'PGFacultySupervisorAssignment'

    def __str__(self):
        return f"{self.pg_student_id} -> {self.faculty_supervisor.username}"


class PGTAAssignmentHistory(models.Model):
    """Immutable history of TA subject assignments."""

    pg_student = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    subject = models.ForeignKey(ProgrammeCourse, on_delete=models.CASCADE)
    assigned_by = models.ForeignKey(
        User,
        related_name="pg_ta_assignment_history_assigned_by",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'PGTAAssignmentHistory'


class PGFacultySupervisorAssignmentHistory(models.Model):
    """Immutable history of faculty supervisor assignments."""

    pg_student = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    faculty_supervisor = models.ForeignKey(User, on_delete=models.CASCADE)
    assigned_by = models.ForeignKey(
        User,
        related_name="pg_faculty_supervisor_assignment_history_assigned_by",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'PGFacultySupervisorAssignmentHistory'

    





class NoDues(models.Model):
    roll_no = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    library_clear = models.BooleanField(default=False)
    library_notclear = models.BooleanField(default=False)
    hostel_clear = models.BooleanField(default=False)
    hostel_notclear = models.BooleanField(default=False)
    mess_clear = models.BooleanField(default=False)
    mess_notclear = models.BooleanField(default=False)
    ece_clear = models.BooleanField(default=False)
    ece_notclear = models.BooleanField(default=False)
    physics_lab_clear = models.BooleanField(default=False)
    physics_lab_notclear = models.BooleanField(default=False)
    mechatronics_lab_clear = models.BooleanField(default=False)
    mechatronics_lab_notclear = models.BooleanField(default=False)
    cc_clear = models.BooleanField(default=False)
    cc_notclear = models.BooleanField(default=False)
    workshop_clear = models.BooleanField(default=False)
    workshop_notclear = models.BooleanField(default=False)
    signal_processing_lab_clear = models.BooleanField(default=False)
    signal_processing_lab_notclear = models.BooleanField(default=False)
    vlsi_clear = models.BooleanField(default=False)
    vlsi_notclear = models.BooleanField(default=False)
    design_studio_clear = models.BooleanField(default=False)
    design_studio_notclear = models.BooleanField(default=False)
    design_project_clear = models.BooleanField(default=False)
    design_project_notclear = models.BooleanField(default=False)
    bank_clear = models.BooleanField(default=False)
    bank_notclear = models.BooleanField(default=False)
    icard_dsa_clear = models.BooleanField(default=False)
    icard_dsa_notclear = models.BooleanField(default=False)
    account_clear = models.BooleanField(default=False)
    account_notclear = models.BooleanField(default=False)
    btp_supervisor_clear = models.BooleanField(default=False)
    btp_supervisor_notclear = models.BooleanField(default=False)
    discipline_office_clear = models.BooleanField(default=False)
    discipline_office_notclear = models.BooleanField(default=False)
    student_gymkhana_clear = models.BooleanField(default=False)
    student_gymkhana_notclear = models.BooleanField(default=False)
    alumni_clear = models.BooleanField(default=False)
    alumni_notclear = models.BooleanField(default=False)
    placement_cell_clear = models.BooleanField(default=False)
    placement_cell_notclear = models.BooleanField(default=False)
    # discipline_office_dsa_clear=models.BooleanField(default=False)
    # discipline_office_dsa_notclear=models.BooleanField(default=False)

    hostel_credential =  models.CharField(max_length=100)
    bank_credential =  models.CharField(max_length=100)
    btp_credential =  models.CharField(max_length=100)
    cse_credential =  models.CharField(max_length=100)
    design_credential =  models.CharField(max_length=100)
    acad_credential =  models.CharField(max_length=100)
    ece_credential =  models.CharField(max_length=100)
    library_credential =  models.CharField(max_length=100)
    me_credential =  models.CharField(max_length=100)
    mess_credential =  models.CharField(max_length=100)
    physics_credential =  models.CharField(max_length=100)
    discipline_credential =  models.CharField(max_length=100)

    acad_admin_float = models.BooleanField(default=False)

    class Meta:
        db_table = 'NoDues'

