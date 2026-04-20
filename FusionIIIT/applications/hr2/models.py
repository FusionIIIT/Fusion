from django.db import models
from applications.globals.models import ExtraInfo, Designation, DepartmentInfo, Faculty, Staff
# from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth.models import User
from datetime import date
from applications.filetracking.models import File

# ==================== EXISTING MODELS (KEPT FOR BACKWARD COMPATIBILITY) ====================

class Constants:
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

# Employee Table
class Employee(models.Model):
    id = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_details', primary_key=True)
    father_name = models.CharField(max_length=100)
    mother_name = models.CharField(max_length=100)
    religion = models.CharField(max_length=20, null=True, blank=True)
    CATEGORY_CHOICES = [
        ('General', 'General'),
        ('OBC', 'OBC'),
        ('SC', 'SC'),
        ('ST', 'ST'),
    ]
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    caste = models.CharField(max_length=50)
    home_state = models.CharField(max_length=50)
    home_district = models.CharField(max_length=50)
    full_address = models.TextField()
    date_of_joining = models.DateField()
    date_of_birth = models.DateField()
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
    ]
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES)
    phone_number = models.CharField(max_length=15)
    personal_email = models.EmailField()
    emergency_contact_number = models.CharField(max_length=15)
    emergency_contact_name = models.CharField(max_length=100)
    Employee_Type = [
        ('Faculty', 'Faculty'),
        ('Staff', 'Staff'),
        ('Other', 'Other'),
    ]
    employee_type = models.CharField(max_length=10, choices=Employee_Type, default='Faculty')

    def __str__(self):
        return f"{self.id.username} - Employee Details"

# Employee Confidential Table
class EmpConfidentialDetails(models.Model):
    id = models.AutoField(primary_key=True)
    empid = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='confidential_details')
    aadhar_number = models.CharField(max_length=12, unique=True)
    pan_number = models.CharField(max_length=10, unique=True)
    MARITAL_STATUS_CHOICES = [
        ('Single', 'Single'),
        ('Married', 'Married'),
        ('Divorced', 'Divorced'),
        ('Widowed', 'Widowed'),
    ]
    marital_status = models.CharField(max_length=10, choices=MARITAL_STATUS_CHOICES)
    personal_file_number = models.CharField(max_length=50, unique=True)
    bank_account_number = models.CharField(max_length=20, unique=True)
    ifsc_code = models.CharField(max_length=20, null=True)
    basic_pay = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Confidential Details of {self.empid.id.username}"

# Employee Dependents Table
class EmpDependents(models.Model):
    id = models.AutoField(primary_key=True)
    empid = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='dependents')
    name = models.CharField(max_length=100)
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    relation = models.CharField(max_length=50)
    contact_number = models.CharField(max_length=15)
    contact_email = models.EmailField(null=True, blank=True)
    date_of_birth = models.DateField()

    def __str__(self):
        return f"Dependent {self.name} of {self.empid.id.username}"

class ForeignService(models.Model):
    extra_info = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    start_date = models.DateField(max_length=6, null=True, blank=True)
    end_date = models.DateField(max_length=6, null=True, blank=True)
    job_title = models.CharField(max_length=50, default='')
    organisation = models.CharField(max_length=100, default='')
    description = models.CharField(max_length=300, default='')
    salary_source = models.CharField(max_length=100, default='')
    designation = models.CharField(max_length=100, default='')
    service_type = models.CharField(max_length=100, choices=Constants.FOREIGN_SERVICE)

    def __str__(self):
        return self.extra_info.user.first_name

class EmpAppraisalForm(models.Model):
    extra_info = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    year = models.DateField(max_length=6, null=True, blank=True)
    appraisal_form = models.FileField(upload_to='Hr2/appraisal_form', null=True, default=" ")

    def __str__(self):
        return self.extra_info.user.first_name

class WorkAssignemnt(models.Model):
    extra_info = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    start_date = models.DateField(max_length=6, null=True, blank=True)
    end_date = models.DateField(max_length=6, null=True, blank=True)
    job_title = models.CharField(max_length=50, default='')
    orders_copy = models.FileField(blank=True, null=True)

class LTCform(models.Model):
    id = models.AutoField(primary_key=True)
    employeeId = models.IntegerField()
    name = models.CharField(max_length=100, null=True)
    blockYear = models.TextField()
    pfNo = models.IntegerField()
    basicPaySalary = models.IntegerField(null=True)
    designation = models.CharField(max_length=50)
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
    submissionDate = models.DateField(null=True)
    phoneNumberForContact = models.BigIntegerField()
    approved = models.BooleanField(null=True)
    approvedDate = models.DateField(auto_now_add=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='LTC_created_by')
    approved_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='LTC_approved_by')

class CPDAAdvanceform(models.Model):
    id = models.AutoField(primary_key=True)
    employeeId = models.IntegerField(null=True)
    name = models.CharField(max_length=40, null=True)
    designation = models.CharField(max_length=40, null=True)
    pfNo = models.IntegerField(null=True)
    purpose = models.TextField(max_length=40, null=True)
    amountRequired = models.IntegerField(null=True)
    advanceDueAdjustment = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    submissionDate = models.DateField(blank=True, null=True)
    balanceAvailable = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    advanceAmountPDA = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    amountCheckedInPDA = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    approved = models.BooleanField(null=True)
    approvedDate = models.DateField(auto_now_add=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='CPDA_created_by')
    approved_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='CPDA_approved_by')

class CPDAReimbursementform(models.Model):
    id = models.AutoField(primary_key=True)
    employeeId = models.IntegerField(null=True)
    name = models.CharField(max_length=50)
    designation = models.CharField(max_length=50)
    pfNo = models.IntegerField()
    advanceTaken = models.IntegerField()
    purpose = models.TextField()
    adjustmentSubmitted = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    balanceAvailable = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    advanceDueAdjustment = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    advanceAmountPDA = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    amountCheckedInPDA = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    submissionDate = models.DateField(blank=True, null=True)
    approved = models.BooleanField(null=True)
    approvedDate = models.DateField(auto_now_add=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='CPDAR_created_by')
    approved_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='CPDAR_approved_by')

# Leave Application Table (old)
class LeaveForm(models.Model):
    STATUS_CHOICES = [
        ('Accepted', 'Accepted'),
        ('Pending', 'Pending'),
        ('Rejected', 'Rejected'),
    ]
    Application_type_choices = [
        ('Online', 'Online'),
        ('Offline', 'Offline'),
    ]

    id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_applications')
    name = models.CharField(max_length=40, null=True)
    designation = models.CharField(max_length=40, null=True)
    submissionDate = models.DateField(default=date.today)
    personalfileNo = models.CharField(max_length=50, null=True)
    departmentInfo = models.CharField(max_length=40, null=True)
    leaveStartDate = models.DateField(blank=True, null=True)
    leaveEndDate = models.DateField(blank=True, null=True)

    Noof_CasualLeave = models.IntegerField(default=0)
    Noof_specialCasualLeave = models.IntegerField(default=0)
    Noof_earnedLeave = models.IntegerField(default=0)
    Noof_commutedLeave = models.IntegerField(default=0)
    Noof_restrictedHoliday = models.IntegerField(default=0)
    Noof_vacationLeave = models.IntegerField(default=0)

    Noof_maternityLeave = models.IntegerField(default=0)
    Noof_childCareLeave = models.IntegerField(default=0)
    Noof_paternityLeave = models.IntegerField(default=0)
    Noof_halfPayLeave = models.IntegerField(default=0)

    LeavingStation = models.BooleanField(default=False)
    StationLeave_startdate = models.DateField(blank=True, null=True)
    StationLeave_enddate = models.DateField(blank=True, null=True)
    Address_During_StationLeave = models.TextField(null=True, blank=True)
    Purpose_of_leave = models.TextField(null=True, blank=True)

    AcademicResponsibility_user = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        related_name='academic_responsibility_user'
    )
    AcademicResponsibility_designation = models.ForeignKey(Designation, on_delete=models.CASCADE, null=True, related_name='leave_academic_responsibility_designation')
    AcademicResponsibility_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')

    AdministrativeResponsibility_user = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        related_name='administrative_responsibility_user'
    )
    AdministrativeResponsibility_designation = models.ForeignKey(Designation, on_delete=models.CASCADE, null=True, related_name='leave_administrative_responsibility_designation')
    AdministrativeResponsibility_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')

    Remarks = models.TextField(null=True, blank=True)

    approvedDate = models.DateField(auto_now_add=True, null=True)
    approved_by = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True, related_name='leave_approved_by')
    approved_by_designation = models.ForeignKey(Designation, on_delete=models.CASCADE, null=True, related_name='leave_approved_by_designation')

    first_recieved_by = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True, related_name='leave_first_recieved_by')
    first_recieved_designation = models.ForeignKey(Designation, on_delete=models.CASCADE, null=True, related_name='leave_first_recieved_designation')

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    attached_pdf = models.BinaryField(null=True, blank=True)
    attached_pdf_name = models.CharField(max_length=100, null=True, blank=True)
    file_id = models.IntegerField(null=True, blank=True)
    application_type = models.CharField(max_length=10, choices=Application_type_choices, default='Online')

    def __str__(self):
        return f"Leave Application {self.id} - {self.employee.id.username}"

class LeaveClaim(models.Model):
    STATUS_CHOICES = [
        ('Accepted', 'Accepted'),
        ('Pending', 'Pending'),
        ('Rejected', 'Rejected'),
    ]
    APPLICATION_TYPE_CHOICES = [
        ('Online', 'Online'),
        ('Offline', 'Offline'),
    ]

    id = models.AutoField(primary_key=True)
    leave_form = models.ForeignKey(LeaveForm, on_delete=models.CASCADE, related_name='leave_claims')
    claim_date = models.DateField(default=date.today)

    leaveStartDate = models.DateField(blank=True, null=True)
    leaveEndDate = models.DateField(blank=True, null=True)

    Noof_CasualLeave = models.IntegerField(default=0)
    Noof_specialCasualLeave = models.IntegerField(default=0)
    Noof_earnedLeave = models.IntegerField(default=0)
    Noof_commutedLeave = models.IntegerField(default=0)
    Noof_restrictedHoliday = models.IntegerField(default=0)
    Noof_vacationLeave = models.IntegerField(default=0)
    Noof_maternityLeave = models.IntegerField(default=0)
    Noof_childCareLeave = models.IntegerField(default=0)
    Noof_paternityLeave = models.IntegerField(default=0)
    Noof_halfPayLeave = models.IntegerField(default=0)

    remarks = models.TextField(null=True, blank=True)

    approvedDate = models.DateField(auto_now_add=True, null=True)
    approved_by = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        null=True,
        related_name='leave_claim_approved_by'
    )
    approved_by_designation = models.ForeignKey(
        Designation,
        on_delete=models.CASCADE,
        null=True,
        related_name='leave_claim_approved_by_designation'
    )

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    attached_pdf = models.BinaryField(null=True, blank=True)
    attached_pdf_name = models.CharField(max_length=100, null=True, blank=True)
    file_id = models.IntegerField(null=True, blank=True)
    application_type = models.CharField(max_length=10, choices=APPLICATION_TYPE_CHOICES, default='Online')

    def __str__(self):
        return f"Leave Claim {self.id} for Form {self.leave_form.id}"

    class Meta:
        verbose_name = "Leave Claim"
        verbose_name_plural = "Leave Claims"

class LeaveBalance(models.Model):
    empid = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='leave_balance', primary_key=True)
    casual_leave_taken = models.IntegerField(default=0)
    special_casual_leave_taken = models.IntegerField(default=0)
    earned_leave_taken = models.IntegerField(default=0)
    half_pay_leave_taken = models.IntegerField(default=0)
    maternity_leave_taken = models.IntegerField(default=0)
    child_care_leave_taken = models.IntegerField(default=0)
    paternity_leave_taken = models.IntegerField(default=0)
    leave_encashment_taken = models.IntegerField(default=0)
    restricted_holiday_taken = models.IntegerField(default=0)

    def __str__(self):
        return f"Leave Balance for {self.empid.id.username}"

class LeavePerYear(models.Model):
    empid = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='yearly_leave', primary_key=True)
    casual_leave = models.IntegerField(default=8)
    special_casual_leave = models.IntegerField(default=15)
    earned_leave = models.IntegerField(default=15)
    half_pay_leave = models.IntegerField(default=15)
    maternity_leave = models.IntegerField(default=180)
    child_care_leave = models.IntegerField(default=730)
    paternity_leave = models.IntegerField(default=15)
    leave_encashment = models.IntegerField(default=60)
    restricted_holiday = models.IntegerField(default=2)

    def __str__(self):
        return f"Yearly Leave Allotment for {self.empid.id.username}"

class Appraisalform(models.Model):
    id = models.AutoField(primary_key=True)
    employeeId = models.IntegerField(null=True)
    name = models.CharField(max_length=22)
    designation = models.CharField(max_length=50)
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
    submissionDate = models.DateField(max_length=6, null=True)
    approved = models.BooleanField(null=True)
    approvedDate = models.DateField(auto_now_add=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='Appraisal_created_by')
    approved_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='Appraisal_approved_by')


# ==================== NEW MODELS FOR REST API (DO NOT OVERLAP) ====================

class EmployeeCategory(models.Model):
    CATEGORY_TYPE = [
        ('TEACHING', 'Teaching'),
        ('NON_TEACHING', 'Non-Teaching'),
    ]
    name = models.CharField(max_length=100)
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPE)
    pay_level = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class EmployeeDetailsExtended(models.Model):
    MARITAL_STATUS = [
        ('SINGLE', 'Single'),
        ('MARRIED', 'Married'),
        ('WIDOWED', 'Widowed'),
        ('DIVORCED', 'Divorced'),
    ]
    EMPLOYEE_STATUS = [
        ('ACTIVE', 'Active'),
        ('ON_LEAVE', 'On Leave'),
        ('DEPUTATION', 'On Deputation'),
        ('SUSPENDED', 'Suspended'),
        ('RETIRED', 'Retired'),
        ('RESIGNED', 'Resigned'),
        ('TERMINATED', 'Terminated'),
    ]

    extra_info = models.OneToOneField(ExtraInfo, on_delete=models.CASCADE, related_name='employee_details_extended')
    category = models.ForeignKey(EmployeeCategory, on_delete=models.PROTECT)

    father_name = models.CharField(max_length=100, blank=True)
    mother_name = models.CharField(max_length=100, blank=True)
    spouse_name = models.CharField(max_length=100, blank=True)
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS, blank=True)

    pan_number = models.CharField(max_length=15, blank=True)
    aadhar_number = models.CharField(max_length=15, blank=True)
    passport_number = models.CharField(max_length=20, blank=True)

    date_of_joining = models.DateField(null=True, blank=True)
    date_of_superannuation = models.DateField(null=True, blank=True)
    appointment_type = models.CharField(max_length=50, blank=True)

    employee_status = models.CharField(max_length=20, choices=EMPLOYEE_STATUS, default='ACTIVE')

    bank_name = models.CharField(max_length=100, blank=True)
    bank_account = models.CharField(max_length=30, blank=True)
    ifsc_code = models.CharField(max_length=15, blank=True)

    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True)
    emergency_contact_relation = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.extra_info.user.username} - EmployeeDetailsExtended"

class ServiceHistory(models.Model):
    employee = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE, related_name='service_history')
    designation = models.ForeignKey(Designation, on_delete=models.PROTECT)
    department = models.ForeignKey(DepartmentInfo, on_delete=models.PROTECT)
    from_date = models.DateField()
    to_date = models.DateField(null=True, blank=True)
    pay_scale = models.CharField(max_length=50, blank=True)
    basic_pay = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ['-from_date']

class QualificationType(models.Model):
    name = models.CharField(max_length=100)
    level = models.IntegerField()  # 1=School, 2=UG, 3=PG, 4=Doctoral

    def __str__(self):
        return self.name

class EducationalQualification(models.Model):
    employee = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE, related_name='qualifications')
    qualification_type = models.ForeignKey(QualificationType, on_delete=models.PROTECT)
    degree = models.CharField(max_length=100)
    specialization = models.CharField(max_length=200, blank=True)
    institution = models.CharField(max_length=200)
    university = models.CharField(max_length=200, blank=True)
    year_of_passing = models.IntegerField()
    division_grade = models.CharField(max_length=50, blank=True)
    document = models.FileField(upload_to='hr/qualifications/', blank=True)

class ProfessionalQualification(models.Model):
    employee = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE, related_name='professional_qualifications')
    title = models.CharField(max_length=200)
    certifying_body = models.CharField(max_length=200)
    date_obtained = models.DateField()
    valid_until = models.DateField(null=True, blank=True)
    document = models.FileField(upload_to='hr/professional/', blank=True)

class PreviousExperience(models.Model):
    employee = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE, related_name='previous_experiences')
    organization = models.CharField(max_length=200)
    designation = models.CharField(max_length=100)
    from_date = models.DateField()
    to_date = models.DateField()
    experience_type = models.CharField(max_length=50)  # Teaching, Industry, Research
    description = models.TextField(blank=True)
    document = models.FileField(upload_to='hr/experience/', blank=True)

class LeaveType(models.Model):
    name = models.CharField(max_length=50)  # CL, EL, HPL, etc.
    code = models.CharField(max_length=10, unique=True)
    max_days_per_year = models.IntegerField(null=True, blank=True)
    carry_forward = models.BooleanField(default=False)
    max_carry_forward = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

class EmployeeLeaveBalance(models.Model):
    employee = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE, related_name='leave_balances_new')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT)
    year = models.IntegerField()
    opening_balance = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    accrued = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    availed = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    current_balance = models.DecimalField(max_digits=5, decimal_places=1, default=0)

    class Meta:
        unique_together = ['employee', 'leave_type', 'year']

class LeaveApplicationNew(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('FORWARDED', 'Forwarded'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('WITHDRAWN', 'Withdrawn'),
        ('CANCELLED', 'Cancelled'),
    ]

    LEAVE_TYPE_CHOICES = [
        ('Casual', 'Casual'),
        ('Restricted', 'Restricted'),
        ('Medical', 'Medical'),
        ('Earned', 'Earned'),
        ('Vacation', 'Vacation'),
        ('Sabbatical', 'Sabbatical'),
    ]

    employee = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE, related_name='leave_applications_new')
    employee_name = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)

    leave_type = models.CharField(max_length=30, choices=LEAVE_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    total_days = models.DecimalField(max_digits=5, decimal_places=1)
    reason = models.TextField()
    station_leave = models.CharField(
        max_length=12,
        choices=[('WITH', 'With Station Leave'), ('WITHOUT', 'Without Station Leave'), ('NOT_REQUIRED', 'Not Required')],
        blank=True,
    )
    is_half_day = models.BooleanField(default=False)
    half_day_slot = models.CharField(
        max_length=2,
        choices=[('AM', 'AM'), ('PM', 'PM')],
        blank=True,
    )

    contact_during_leave = models.CharField(max_length=15)
    address_during_leave = models.TextField()
    handover_to = models.CharField(max_length=100, blank=True)
    handover_notes = models.TextField(blank=True)
    nominee_status = models.CharField(
        max_length=20,
        choices=[('NOT_REQUIRED', 'Not Required'), ('PENDING', 'Pending'), ('ACCEPTED', 'Accepted'), ('DECLINED', 'Declined')],
        default='NOT_REQUIRED',
    )
    nominee_responded_at = models.DateTimeField(null=True, blank=True)

    medical_certificate = models.FileField(upload_to='hr/leave/', blank=True, null=True)
    attachment_file = models.FileField(upload_to='hr/leave/', blank=True, null=True)

    applied_date = models.DateField(auto_now_add=True)
    leave_balance_before = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    leave_balance_after = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    approval_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    current_approver_role = models.CharField(max_length=50, blank=True)
    remarks = models.TextField(blank=True)

    document_request_message = models.TextField(blank=True)
    document_request_status = models.CharField(
        max_length=20,
        choices=[('NOT_REQUESTED', 'Not Requested'), ('REQUESTED', 'Requested'), ('SUBMITTED', 'Submitted')],
        default='NOT_REQUESTED',
    )
    document_requested_at = models.DateTimeField(null=True, blank=True)
    document_submission = models.TextField(blank=True)
    document_submitted_at = models.DateTimeField(null=True, blank=True)

    cancel_status = models.CharField(
        max_length=20,
        choices=[('NOT_REQUESTED', 'Not Requested'), ('REQUESTED', 'Requested'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')],
        default='NOT_REQUESTED',
    )
    cancel_requested_at = models.DateTimeField(null=True, blank=True)
    cancel_decided_at = models.DateTimeField(null=True, blank=True)
    cancel_requested_by_role = models.CharField(max_length=50, blank=True)
    cancel_current_approver_role = models.CharField(max_length=50, blank=True)
    cancel_reason = models.TextField(blank=True)
    cancel_decision_remarks = models.TextField(blank=True)

    extension_status = models.CharField(
        max_length=20,
        choices=[('NOT_REQUESTED', 'Not Requested'), ('REQUESTED', 'Requested'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')],
        default='NOT_REQUESTED',
    )
    extension_requested_at = models.DateTimeField(null=True, blank=True)
    extension_decided_at = models.DateTimeField(null=True, blank=True)
    extension_requested_by_role = models.CharField(max_length=50, blank=True)
    extension_current_approver_role = models.CharField(max_length=50, blank=True)
    extension_reason = models.TextField(blank=True)
    extension_new_end_date = models.DateField(null=True, blank=True)
    extension_new_total_days = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    extension_decision_remarks = models.TextField(blank=True)

    resumption_status = models.CharField(
        max_length=20,
        choices=[('NOT_REQUESTED', 'Not Requested'), ('SUBMITTED', 'Submitted'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')],
        default='NOT_REQUESTED',
    )
    resumption_date = models.DateField(null=True, blank=True)
    resumption_reason = models.TextField(blank=True)
    resumption_submitted_at = models.DateTimeField(null=True, blank=True)
    resumption_decided_at = models.DateTimeField(null=True, blank=True)
    resumption_current_approver_role = models.CharField(max_length=50, blank=True)
    resumption_decision_remarks = models.TextField(blank=True)

    def __str__(self):
        return f"LeaveNew #{self.id} - {self.employee.user.username}"

class AppraisalPeriod(models.Model):
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    submission_deadline = models.DateField()
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class PerformanceAppraisalNew(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('REVIEWED', 'Reviewed'),
        ('APPROVED', 'Approved'),
        ('FINALIZED', 'Finalized'),
    ]

    employee = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE, related_name='appraisals_new')
    period = models.ForeignKey(AppraisalPeriod, on_delete=models.PROTECT)

    teaching_score = models.IntegerField(null=True, blank=True)
    research_score = models.IntegerField(null=True, blank=True)
    admin_score = models.IntegerField(null=True, blank=True)
    extension_score = models.IntegerField(null=True, blank=True)
    self_remarks = models.TextField(blank=True)

    reviewer_teaching_score = models.IntegerField(null=True, blank=True)
    reviewer_research_score = models.IntegerField(null=True, blank=True)
    reviewer_admin_score = models.IntegerField(null=True, blank=True)
    reviewer_extension_score = models.IntegerField(null=True, blank=True)
    reviewer = models.ForeignKey(ExtraInfo, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_performance_appraisals_new')
    reviewer_remarks = models.TextField(blank=True)

    final_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    final_grade = models.CharField(max_length=10, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')

    submitted_at = models.DateTimeField(null=True, blank=True)
    finalized_at = models.DateTimeField(null=True, blank=True)

class TrainingProgram(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    organizer = models.CharField(max_length=200)
    venue = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    max_participants = models.IntegerField(null=True, blank=True)
    is_mandatory = models.BooleanField(default=False)

class TrainingNomination(models.Model):
    STATUS_CHOICES = [
        ('NOMINATED', 'Nominated'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('ATTENDED', 'Attended'),
        ('COMPLETED', 'Completed'),
    ]
    employee = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE, related_name='training_nominations')
    program = models.ForeignKey(TrainingProgram, on_delete=models.CASCADE)
    nominated_by = models.ForeignKey(ExtraInfo, on_delete=models.SET_NULL, null=True, related_name='training_nominations_made')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NOMINATED')
    feedback = models.TextField(blank=True)
    certificate = models.FileField(upload_to='hr/training/', blank=True)

class PromotionApplication(models.Model):
    STATUS_CHOICES = [
        ('SUBMITTED', 'Submitted'),
        ('UNDER_REVIEW', 'Under Review'),
        ('COMMITTEE_STAGE', 'At Committee'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    employee = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE, related_name='promotion_applications')
    current_designation = models.ForeignKey(Designation, on_delete=models.PROTECT, related_name='current_for_promotions')
    applied_designation = models.ForeignKey(Designation, on_delete=models.PROTECT, related_name='applied_promotions')
    application_date = models.DateField()
    eligibility_date = models.DateField()
    api_score = models.IntegerField(null=True, blank=True)
    documents = models.FileField(upload_to='hr/promotions/', blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SUBMITTED')
    remarks = models.TextField(blank=True)
    approved_date = models.DateField(null=True, blank=True)
    effective_date = models.DateField(null=True, blank=True)

class EmployeeAttendance(models.Model):
    ATTENDANCE_STATUS = [
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('HALF_DAY', 'Half Day'),
        ('ON_LEAVE', 'On Leave'),
        ('ON_TOUR', 'On Tour'),
        ('WORK_FROM_HOME', 'WFH'),
    ]
    employee = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    status = models.CharField(max_length=20, choices=ATTENDANCE_STATUS)
    in_time = models.TimeField(null=True, blank=True)
    out_time = models.TimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)

    class Meta:
        unique_together = ['employee', 'date']

class FacultyWorkload(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='workloads')
    semester = models.CharField(max_length=20)
    year = models.IntegerField()
    lecture_hours = models.IntegerField(default=0)
    tutorial_hours = models.IntegerField(default=0)
    lab_hours = models.IntegerField(default=0)
    total_hours = models.IntegerField(default=0)
    total_students = models.IntegerField(default=0)
    phd_scholars = models.IntegerField(default=0)

    class Meta:
        unique_together = ['faculty', 'semester', 'year']

class LTCApplicationNew(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('FORWARDED', 'Forwarded'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('WITHDRAWN', 'Withdrawn'),
    ]

    employee = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE, related_name='ltc_applications_new')
    employee_name = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)

    ltc_block_year = models.IntegerField()
    travel_start_date = models.DateField()
    travel_end_date = models.DateField()
    destination = models.CharField(max_length=200)
    purpose_of_travel = models.TextField()

    family_members = models.TextField(blank=True)
    relationship_details = models.TextField(blank=True)

    travel_mode = models.CharField(max_length=50)
    ticket_number = models.CharField(max_length=100, blank=True)
    ticket_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    accommodation_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    other_expenses = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_amount_claimed = models.DecimalField(max_digits=10, decimal_places=2)

    tickets_upload = models.CharField(max_length=200, blank=True)
    bills_upload = models.CharField(max_length=200, blank=True)

    previous_ltc_used = models.BooleanField(default=False)
    last_ltc_date = models.DateField(null=True, blank=True)

    applied_date = models.DateField(auto_now_add=True)
    verified_by_hr = models.BooleanField(default=False)
    approval_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    accountant_status = models.CharField(max_length=20, blank=True)
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"LTCNew #{self.id} - {self.employee.user.username}"

class CPDAAdvanceNew(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('FORWARDED', 'Forwarded'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('WITHDRAWN', 'Withdrawn'),
    ]

    employee = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE, related_name='cpda_advances_new')
    employee_name = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)

    event_name = models.CharField(max_length=200)
    event_type = models.CharField(max_length=50)
    organized_by = models.CharField(max_length=200, blank=True)
    venue = models.CharField(max_length=200, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()

    registration_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    travel_expense = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    accommodation_expense = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    other_expenses = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    purpose_of_attending = models.TextField()
    benefits_to_institution = models.TextField()

    invitation_letter = models.CharField(max_length=200, blank=True)
    receipts = models.CharField(max_length=200, blank=True)
    certificates = models.CharField(max_length=200, blank=True)

    applied_date = models.DateField(auto_now_add=True)
    verified_by_hr = models.BooleanField(default=False)
    approval_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    accountant_processing_status = models.CharField(max_length=30, blank=True)
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"CPDAAdvanceNew #{self.id} - {self.employee.user.username}"

class CPDAReimbursementNew(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('FORWARDED', 'Forwarded'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    employee = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE, related_name='cpda_reimbursements_new')
    employee_name = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)

    event_name = models.CharField(max_length=200)
    event_type = models.CharField(max_length=50)
    organized_by = models.CharField(max_length=200, blank=True)
    venue = models.CharField(max_length=200, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()

    registration_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    travel_expense = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    accommodation_expense = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    other_expenses = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    purpose_of_attending = models.TextField()
    benefits_to_institution = models.TextField()

    invitation_letter = models.CharField(max_length=200, blank=True)
    receipts = models.CharField(max_length=200, blank=True)
    certificates = models.CharField(max_length=200, blank=True)

    applied_date = models.DateField(auto_now_add=True)
    verified_by_hr = models.BooleanField(default=False)
    approval_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    accountant_processing_status = models.CharField(max_length=30, blank=True)
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"CPDAReimbursementNew #{self.id} - {self.employee.user.username}"

class AppraisalFormNew(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('REVIEWED', 'Reviewed'),
        ('APPROVED', 'Approved'),
    ]

    employee = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE, related_name='appraisal_forms_new')
    employee_name = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    appraisal_year = models.CharField(max_length=20)

    self_summary = models.TextField()
    key_responsibilities = models.TextField()
    achievements = models.TextField()
    challenges_faced = models.TextField(blank=True)

    teaching_performance = models.TextField(blank=True)
    research_work = models.TextField(blank=True)
    publications = models.TextField(blank=True)
    projects_handled = models.TextField(blank=True)
    administrative_contributions = models.TextField(blank=True)

    trainings_attended = models.TextField(blank=True)
    certifications = models.TextField(blank=True)
    workshops = models.TextField(blank=True)

    goals_achieved = models.TextField()
    future_goals = models.TextField()

    supporting_documents = models.CharField(max_length=200, blank=True)

    reviewer_id = models.CharField(max_length=50, blank=True)
    reviewer_comments = models.TextField(blank=True)
    rating = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    remarks = models.TextField(blank=True)

    assigned_reviewer_role = models.CharField(max_length=20, blank=True)
    assigned_reviewer = models.ForeignKey(
        ExtraInfo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_appraisals_new',
    )
    assigned_by = models.ForeignKey(
        ExtraInfo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appraisal_assignments_made',
    )
    assigned_at = models.DateTimeField(null=True, blank=True)

    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"AppraisalNew #{self.id} - {self.employee.user.username}"