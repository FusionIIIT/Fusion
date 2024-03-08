from django.db import models
from applications.globals.models import ExtraInfo
from django.core.validators import MaxValueValidator, MinValueValidator

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
    aadhar_no = models.BigIntegerField(default=0, max_length=12, 
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
    # award_name = models.CharField(max_length=100, default='')
    # award_type = models.CharField(max_length=100, default='')
    # achievement_date = models.CharField(max_length=100, default='')
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


class CPDAform(models.Model):
    id = models.AutoField(primary_key=True)
    employee_id = models.IntegerField(max_length=22,null=True)
    name = models.CharField(max_length=40,null=True)
    designation = models.CharField(max_length=40,null=True)
    pf_no = models.CharField(max_length=30,null=True)
    purpose = models.CharField(max_length=40,null=True)
    amount_required = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    adjusted_pda = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    achievements_uploaded_date = models.DateField(blank=True, null=True)
    submission_date = models.DateField(blank=True, null=True)
    recomm_hod_confirm = models.BooleanField(default=False)
    date_rspc_confirm = models.BooleanField(default=False)
    balance_available = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    advance_amount_pda = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    dealing_asstt_name = models.CharField(max_length=40, blank=True, null=True)
    ar_dr_name = models.CharField(max_length=40, blank=True, null=True)
    check_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    dealing_asstt_ia_name = models.CharField(max_length=40, blank=True, null=True)
    ar_dr_ia_name = models.CharField(max_length=40, blank=True, null=True)
    sanction_status = models.BooleanField(default=False)
    copy_to = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)


class LTCform(models.Model):
    id = models.AutoField(primary_key=True)
    employee_id = models.IntegerField(max_length=22,null=True)
    name = models.CharField(max_length=100, null=True)
    block_year = models.CharField(max_length=100, null=True)
    pf_no = models.IntegerField(max_length=22, null=True)
    basic_pay_salary = models.IntegerField(max_length=10, null=True)
    designation = models.CharField(max_length=50, null=True)
    department_info = models.CharField(max_length=20, null=True)
    leave_availability = models.BooleanField(default=False)
    leave_start_date = models.DateField(max_length=6, null=True, blank=True)
    leave_end_date = models.DateField(max_length=6, null=True, blank=True)
    date_of_leave_for_family = models.DateField(max_length=6, null=True, blank=True)
    nature_of_leave = models.TextField(null=True)
    purpose_of_leave = models.TextField(null=True)
    hometown_or_not = models.BooleanField(default=False, null=True)
    place_of_visit = models.CharField(max_length=100, null=True, blank=True)
    address_during_leave = models.TextField(null=True)
    mode_for_vacation = models.BooleanField(null=True)
    details_of_family_members_already_done = models.TextField(null=True)
    family_members_about_to_avail = models.CharField(max_length=100, null=True)
    details_of_family_members = models.TextField(null=True)
    details_of_dependents = models.TextField(null=True)
    amount_of_advance_required = models.IntegerField(null=True, blank=True)
    certified_family_dependents = models.TextField(null=True)
    certified_advance = models.TextField(null=True)
    adjusted_month = models.TextField(null=True)
    date = models.DateField(max_length=6, null=True)
    phone_number_for_contact = models.IntegerField(max_length=100, null=True)    
   

    
# class LTCform(models.Model):
#     id = models.AutoField(primary_key=True)
#     employee_id = models.IntegerField(max_length=22,null=True)
#     name = models.CharField(max_length=40, null=True)
#     block_year = models.IntegerField(null=True)
#     pf_no = models.IntegerField(null=True)
#     basic_pay_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True)
#     designation = models.CharField(max_length=40, null=True)
#     department_info = models.CharField(max_length=40, null=True)
#     leave_availability = models.BooleanField(null=True)
#     leave_start_date = models.DateField(null=True)
#     leave_end_date = models.DateField(null=True)
#     date_of_leave_for_family = models.DateField(null=True)
#     nature_of_leave = models.CharField(max_length=40, null=True)
#     purpose_of_leave = models.CharField(max_length=40, null=True)
#     hometown_or_not = models.BooleanField(null=True)
#     place_of_visit = models.CharField(max_length=40, null=True)
#     address_during_leave = models.CharField(max_length=80, null=True)
#     mode_for_vacation = models.BooleanField(null=True)
#     family_members_about_to_avail = models.CharField(max_length=40, null=True)
#     details_of_dependents = models.CharField(max_length=40, null=True)
#     amount_of_advance_required = models.DecimalField(max_digits=10, decimal_places=2, null=True)
#     certified_family_dependents = models.CharField(max_length=40, null=True)
#     certified_advance = models.CharField(max_length=40, null=True)
#     adjusted_month = models.CharField(max_length=40, null=True)
#     date = models.DateField(null=True)
#     phone_number_for_contact = models.CharField(max_length=40, null=True)
#     serialNumber = models.IntegerField(null=True)  # Field for serial number
#     fullName = models.CharField(max_length=40, null=True)  # Field for full name
#     age = models.IntegerField(null=True)  # Field for age
