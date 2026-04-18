from django.db import models
from applications.globals.models import ExtraInfo
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth.models import User

class Constants:
    # Class for various choices on the enumerations
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    DEPARTMENT = (
        ('CSE', 'CSE'),
        ('ME', 'Mechanical'),
        ('ECE', 'ECE'),
        ('DESIGN', 'DESIGN'),
    )
    CATEGORY = (
        ('SC', 'SC'),
        ('ST', 'ST'),
        ('OBC', 'OBC'),
        ('GENERAL', 'GENERAL'),
        ('PWD', 'PWD'),

    )
    MARITIAL_STATUS = (
        ('MARRIED', 'MARRIED'),
        ('UN-MARRIED', 'UN-MARRIED'),
        ('WIDOW', 'WIDOW'),

    )

    BLOOD_GROUP = (
        ('AB+', 'AB+'),
        ('O+', 'O+'),
        ('AB-', 'AB-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('O-', 'O-'),
        ('A+', 'A+'),
        ('A-', 'A-'),

    )
    FOREIGN_SERVICE = (
        ('LIEN', 'LIEN'),
        ('DEPUTATION', 'DEPUTATION'),
        ('OTHER', 'OTHER'),
    )


class BaseForm(models.Model):
    """Abstract base for HR form models that share common metadata.

    This helps reduce redundancy and ensures consistent common fields across
    multiple form types.
    """

    employeeId = models.IntegerField(null=True)
    name = models.CharField(max_length=100, null=True)
    designation = models.CharField(max_length=50, null=True)
    pfNo = models.IntegerField(null=True)
    submissionDate = models.DateField(blank=True, null=True)
    approved = models.BooleanField(null=True)
    approvedDate = models.DateField(auto_now_add=True, null=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        related_name='%(class)s_created_by',
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        related_name='%(class)s_approved_by',
    )

    class Meta:
        abstract = True


# Employee model
class Employee(models.Model):
    """
    table for employee details
    """
    extra_info = models.OneToOneField(ExtraInfo, on_delete=models.CASCADE)
    father_name = models.CharField(max_length=40, default='')
    mother_name = models.CharField(max_length=40, default='')
    religion = models.CharField(max_length=40, default='')
    category = models.CharField(max_length=50, null=False, choices=Constants.CATEGORY)
    cast = models.CharField(max_length=40, default='')
    home_state = models.CharField(max_length=40, default='')
    home_district = models.CharField(max_length=40, default='')
    date_of_joining = models.DateField(null=True, blank=True)
    designation = models.CharField(max_length=40, default='')
    blood_group = models.CharField(
        max_length=50, choices=Constants.BLOOD_GROUP)

    def __str__(self):
        return self.extra_info.user.first_name


# table for employee  confidential details
class EmpConfidentialDetails(models.Model):
    """
    table for employee  confidential details
    """
    extra_info = models.OneToOneField(ExtraInfo, on_delete=models.CASCADE)
    aadhar_no = models.BigIntegerField(default=0,
                              validators=[MaxValueValidator(999999999999),MinValueValidator(99999999999)])
                              
    maritial_status = models.CharField(
        max_length=50, null=False, choices=Constants.MARITIAL_STATUS)
    bank_account_no = models.IntegerField(default=0)
    salary = models.IntegerField(default=0)

    def __str__(self):
        return self.extra_info.user.first_name

# table for employee's dependent details


class EmpDependents(models.Model):
    """Table for employee's dependent details """
    extra_info = models.OneToOneField(ExtraInfo, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, default='')
    gender = models.CharField(max_length=50, choices=Constants.GENDER_CHOICES)
    dob = models.DateField(max_length=6, null=True)
    relationship = models.CharField(max_length=40, default='')

    def __str__(self):
        return self.extra_info.user.first_name


class ForeignService(models.Model):
    """
    This table contains details about deputation, lien 
    and other foreign services of employee
    """
    extra_info = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    start_date = models.DateField(max_length=6, null=True, blank=True)
    end_date = models.DateField(max_length=6, null=True, blank=True)
    job_title = models.CharField(max_length=50, default='')
    organisation = models.CharField(max_length=100, default='')
    description = models.CharField(max_length=300, default='')
    salary_source = models.CharField(max_length=100, default='')
    designation = models.CharField(max_length=100, default='')
    service_type = models.CharField(
        max_length=100, choices=Constants.FOREIGN_SERVICE)

    def __str__(self):
        return self.extra_info.user.first_name


class EmpAppraisalForm(models.Model):
    extra_info = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    year = models.DateField(max_length=6, null=True, blank=True)
    appraisal_form = models.FileField(
        upload_to='Hr2/appraisal_form', null=True, default=" ")

    def __str__(self):
        return self.extra_info.user.first_name


class WorkAssignemnt(models.Model):
    extra_info = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    start_date = models.DateField(max_length=6, null=True, blank=True)
    end_date = models.DateField(max_length=6, null=True, blank=True)
    job_title = models.CharField(max_length=50, default='')
    orders_copy = models.FileField(blank=True, null=True)

class LTCform(BaseForm):
    """LTC request with workflow (see hr2.workflow.ltc)."""

    WORKFLOW_STATUS_CHOICES = (
        ("submitted", "Submitted"),
        ("hr_approved", "Approved by HR"),
        ("hr_rejected", "Rejected by HR"),
        ("with_accountant", "With Accountant"),
    )
    workflow_status = models.CharField(
        max_length=40,
        choices=WORKFLOW_STATUS_CHOICES,
        default="submitted",
        db_index=True,
    )
    workflow_history = models.JSONField(blank=True, default=list)

    blockYear = models.TextField()
    basicPaySalary = models.IntegerField(null=True)
    departmentInfo = models.CharField(max_length=50)
    leaveRequired = models.BooleanField(default=False, null=True)
    leaveStartDate = models.DateField(null=True, blank=True)
    leaveEndDate = models.DateField(null=True, blank=True)
    dateOfDepartureForFamily = models.DateField(null=True, blank=True)
    natureOfLeave = models.TextField(null=True, blank=True)
    purposeOfLeave = models.TextField(null=True, blank=True)
    hometownOrNot = models.BooleanField(default=False)
    placeOfVisit = models.TextField(max_length=100, null=True, blank=True)
    addressDuringLeave = models.TextField(null=True)
    modeofTravel = models.TextField(max_length=10, null=True, blank=True)
    detailsOfFamilyMembersAlreadyDone = models.JSONField(null=True, blank=True)
    detailsOfFamilyMembersAboutToAvail = models.JSONField(max_length=100, null=True, blank=True)
    detailsOfDependents = models.JSONField(blank=True, null=True)
    amountOfAdvanceRequired = models.IntegerField(null=True, blank=True)
    certifiedThatFamilyDependents = models.BooleanField(blank=True, null=True)
    certifiedThatAdvanceTakenOn = models.DateField(null=True, blank=True)
    adjustedMonth = models.TextField(max_length=50, null=True, blank=True)
    phoneNumberForContact = models.BigIntegerField()



class CPDAAdvanceform(BaseForm):
    """CPDA advance request with explicit workflow status (see hr2.workflow.cpda_advance)."""

    WORKFLOW_STATUS_CHOICES = (
        ("submitted", "Submitted"),
        ("hod_verified", "Verified by HOD"),
        ("hod_not_verified", "Not verified by HOD"),
        ("forwarded_to_director", "Forwarded to Director"),
        ("director_approved", "Approved by Director"),
        ("director_rejected", "Rejected by Director"),
        ("accountant_processed", "Processed by Accountant"),
    )

    purpose = models.TextField(max_length=40, null=True)
    amountRequired = models.IntegerField(null=True)
    advanceDueAdjustment = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    balanceAvailable = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    advanceAmountPDA = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    amountCheckedInPDA = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    workflow_status = models.CharField(
        max_length=40,
        choices=WORKFLOW_STATUS_CHOICES,
        default="submitted",
        db_index=True,
    )
    workflow_history = models.JSONField(default=list, blank=True)

class LeaveForm(BaseForm):
    departmentInfo = models.CharField(max_length=40, null=True)
    natureOfLeave = models.TextField(max_length=40, null=True)
    leaveStartDate = models.DateField(blank=True, null=True)
    leaveEndDate = models.DateField(blank=True, null=True)
    purposeOfLeave = models.TextField(max_length=40, null=True)
    addressDuringLeave = models.TextField(max_length=40, blank=True, null=True)
    academicResponsibility = models.TextField(max_length=40, blank=True, null=True)
    addministrativeResponsibiltyAssigned = models.TextField(max_length=40, null=True)
    leave_pdf = models.BinaryField(null=True, blank=True)
    leave_pdf_file = models.FileField(
        upload_to='Hr2/leave_pdfs', null=True, blank=True
    )

class LeaveBalance(models.Model):
    """Per-type leave: available = allotted - used (synced into legacy *Leave columns on save)."""

    id = models.AutoField(primary_key=True)
    employeeId = models.OneToOneField(ExtraInfo, on_delete=models.CASCADE)
    casualLeave = models.IntegerField(default=0)
    casual_leave_allotted = models.PositiveIntegerField(default=15)
    casual_leave_used = models.PositiveIntegerField(default=0)
    specialCasualLeave = models.IntegerField(default=0)
    special_casual_leave_allotted = models.PositiveIntegerField(default=7)
    special_casual_leave_used = models.PositiveIntegerField(default=0)
    earnedLeave = models.IntegerField(default=0)
    earned_leave_allotted = models.PositiveIntegerField(default=30)
    earned_leave_used = models.PositiveIntegerField(default=0)
    commutedLeave = models.IntegerField(default=0)
    commuted_leave_allotted = models.PositiveIntegerField(default=0)
    commuted_leave_used = models.PositiveIntegerField(default=0)
    restrictedHoliday = models.IntegerField(default=0)
    restricted_holiday_allotted = models.PositiveIntegerField(default=2)
    restricted_holiday_used = models.PositiveIntegerField(default=0)
    stationLeave = models.IntegerField(default=0)
    station_leave_allotted = models.PositiveIntegerField(default=0)
    station_leave_used = models.PositiveIntegerField(default=0)
    vacationLeave = models.IntegerField(default=0)
    vacation_leave_allotted = models.PositiveIntegerField(default=0)
    vacation_leave_used = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        self.casualLeave = max(
            0, int(self.casual_leave_allotted or 0) - int(self.casual_leave_used or 0)
        )
        self.specialCasualLeave = max(
            0,
            int(self.special_casual_leave_allotted or 0)
            - int(self.special_casual_leave_used or 0),
        )
        self.earnedLeave = max(
            0, int(self.earned_leave_allotted or 0) - int(self.earned_leave_used or 0)
        )
        self.commutedLeave = max(
            0, int(self.commuted_leave_allotted or 0) - int(self.commuted_leave_used or 0)
        )
        self.restrictedHoliday = max(
            0,
            int(self.restricted_holiday_allotted or 0)
            - int(self.restricted_holiday_used or 0),
        )
        self.stationLeave = max(
            0, int(self.station_leave_allotted or 0) - int(self.station_leave_used or 0)
        )
        self.vacationLeave = max(
            0, int(self.vacation_leave_allotted or 0) - int(self.vacation_leave_used or 0)
        )
        super().save(*args, **kwargs)


class Appraisalform(BaseForm):
    """Faculty/staff appraisal with workflow (see hr2.workflow.appraisal)."""

    WORKFLOW_STATUS_CHOICES = (
        ("submitted", "Submitted"),
        ("hr_approved", "Approved by HR"),
        ("hr_rejected", "Rejected by HR"),
    )
    workflow_status = models.CharField(
        max_length=40,
        choices=WORKFLOW_STATUS_CHOICES,
        default="submitted",
        db_index=True,
    )
    workflow_history = models.JSONField(blank=True, default=list)

    disciplineInfo = models.CharField(max_length=22, null=True)
    specificFieldOfKnowledge = models.TextField(max_length=40, null=True)
    currentResearchInterests = models.TextField(max_length=40, null=True)
    coursesTaught = models.JSONField(max_length=100, null=True)
    newCoursesIntroduced = models.JSONField(max_length=100, null=True)
    newCoursesDeveloped = models.JSONField(max_length=100, null=True)
    otherInstructionalTasks = models.TextField(max_length=100, null=True)
    thesisSupervision = models.JSONField(max_length=100, null=True)
    sponsoredReseachProjects = models.JSONField(max_length=100, null=True)
    otherResearchElement = models.TextField(max_length=40, null=True)
    publication = models.TextField(max_length=40, null=True)
    referredConference = models.TextField(max_length=40, null=True)
    conferenceOrganised = models.TextField(max_length=40, null=True)
    membership = models.TextField(max_length=40, null=True)
    honours = models.TextField(max_length=40, null=True)
    editorOfPublications = models.TextField(max_length=40, null=True)
    expertLectureDelivered = models.TextField(max_length=40, null=True)
    membershipOfBOS = models.TextField(max_length=40, null=True)
    otherExtensionTasks = models.TextField(max_length=40, null=True)
    administrativeAssignment = models.TextField(max_length=40, null=True)
    serviceToInstitute = models.TextField(max_length=40, null=True)
    otherContribution = models.TextField(max_length=40, null=True)
    performanceComments = models.TextField(max_length=100, null=True)


class CPDAReimbursementform(BaseForm):
    advanceTaken = models.IntegerField()
    purpose = models.TextField()
    adjustmentSubmitted = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    balanceAvailable = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    advanceDueAdjustment = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    advanceAmountPDA = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    amountCheckedInPDA = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
