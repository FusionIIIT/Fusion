from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
from dateutil.relativedelta import relativedelta
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation, Faculty
from applications.globals.models import Constants as Global_Const

class Constants:
    STATUS = (
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('adjustments_pending', 'Adjustments Pending'),
        ('finished', 'Finished')
    )
    REVIEW_STATUS = (
        ('to_assign', 'To Assign'),
        ('under_review', 'Under Review'),
        ('reviewed', 'Reviewed')
    )
    LTC_TYPE = (
        ('hometown', 'Home Town'),
        ('elsewhere', 'Elsewhere')
    )
    LTC_TRAVEL = (
        ('rail', 'Rail'),
        ('road', 'Road')
    )
    LTC_LEAVE = (
        ('yes', 'Yes'),
        ('no', 'No')
    )
    MARITAL_STATUS = (
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed'),
        ('seperated', 'Seperated')
    )
    CATEGORY = (
        ('general', 'General'),
        ('obc', 'OBC'),
        ('sc', 'SC'),
        ('st', 'ST')
    )

class Establishment_variables(models.Model):
    est_admin = models.ForeignKey(User, on_delete=models.CASCADE)
 

class Cpda_application(models.Model):
    status = models.CharField(max_length=20, null=True, choices=Constants.STATUS)

    # CPDA Request fields
    applicant = models.ForeignKey(User, on_delete=models.CASCADE)
    pf_number = models.CharField(max_length=50, default='')
    purpose = models.CharField(max_length=500, default='', blank=True)
    requested_advance = models.IntegerField(blank=True)
    request_timestamp = models.DateTimeField(auto_now=True, null=True)

    # CPDA Adjustment fields
    adjustment_amount = models.IntegerField(blank=True, null=True, default='0')
    bills_attached = models.IntegerField( blank=True, null=True, default='-1')
    total_bills_amount = models.IntegerField( blank=True, null=True, default='0')
    ppa_register_page_no = models.IntegerField( blank=True, null=True, default='-1')
    adjustment_timestamp = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return 'cpda id ' + str(self.id) + ', applied by ' + self.applicant.username

    class Meta:
        db_table = 'Cpda Application'
        

class Cpda_tracking(models.Model):
    application = models.OneToOneField(Cpda_application, primary_key=True, related_name='tracking_info',on_delete=models.CASCADE)
    reviewer_id = models.ForeignKey(User, null = True, blank=True, on_delete=models.CASCADE)
    reviewer_design = models.ForeignKey(Designation, null=True, blank=True, on_delete=models.CASCADE)
    remarks = models.CharField(max_length=250, null=True, blank=True)
    review_status = models.CharField(max_length=20, null=True, choices=Constants.REVIEW_STATUS)

    def __str__(self):
        return 'cpda id ' + str(self.application.id) + ' tracking'

    class Meta:
        db_table = 'Cpda Tracking'


class Cpda_bill(models.Model):
    application = models.ForeignKey(Cpda_application, on_delete=models.CASCADE, null=True)
    bill = models.FileField(blank=True)

    def __str__(self):
        return 'cpda id ' + str(self.application.id) + ', bill id ' + str(self.id)

    class Meta:
        db_table = 'Cpda Bills'


class Ltc_application(models.Model):
    status = models.CharField(max_length=20, null=True, choices=Constants.STATUS)

    applicant = models.ForeignKey(User, on_delete=models.CASCADE)
    pf_number = models.CharField(max_length=50, default='')
    basic_pay = models.IntegerField(blank=True)

    is_leave_required = models.CharField(choices=Constants.LTC_LEAVE, max_length=50)
    leave_start = models.DateField()
    leave_end = models.DateField()
    family_departure_date = models.DateField()
    leave_nature = models.CharField(max_length=50, default='')
    purpose = models.CharField(max_length=500, default='', blank=True)
    is_hometown_or_elsewhere = models.CharField(choices=Constants.LTC_TYPE, max_length=50)
    phone_number = models.CharField(max_length=13, default='')
    address_during_leave = models.CharField(max_length=500, default='', blank=True)
    travel_mode = models.CharField(choices=Constants.LTC_TRAVEL, max_length=50)

    # details of family members that have already availed LTC
    ltc_availed = models.CharField(max_length=100, default='', blank=True)

    # details of family members who will avail LTC
    ltc_to_avail = models.CharField(max_length=200, default='', blank=True)

    # details of family members who are dependents of applicant
    dependents = models.CharField(max_length=500, default='', blank=True)

    requested_advance = models.IntegerField(blank=True)
    request_timestamp = models.DateTimeField(auto_now=True, null=True)
    review_timestamp = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return 'ltc id ' + str(self.id) + ', applied by ' + self.applicant.username

    class Meta:
        db_table = 'Ltc Application'


class Ltc_tracking(models.Model):
    application = models.OneToOneField(Ltc_application, primary_key=True, related_name='tracking_info',on_delete=models.CASCADE)
    reviewer_id = models.ForeignKey(User, null = True, blank=True, on_delete=models.CASCADE)
    reviewer_design = models.ForeignKey(Designation, null=True, blank=True, on_delete=models.CASCADE)
    remarks = models.CharField(max_length=250, null=True, blank=True)
    review_status = models.CharField(max_length=20, null=True, choices=Constants.REVIEW_STATUS)

    def __str__(self):
        return 'ltc id ' + str(self.application.id) + ' tracking'

    class Meta:
        db_table = 'Ltc Tracking'


class Ltc_eligible_user(models.Model):
    user = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE)
    date_of_joining = models.DateField(default='2005-04-01')
    current_block_size = models.IntegerField(default=4)

    total_ltc_allowed = models.IntegerField(default=2)
    hometown_ltc_allowed = models.IntegerField(default=1)
    elsewhere_ltc_allowed = models.IntegerField(default=1)

    hometown_ltc_availed = models.IntegerField(default=0)
    elsewhere_ltc_availed = models.IntegerField(default=0)

    def get_years_of_job(self):
        ret = relativedelta(datetime.today().date(), self.date_of_joining)
        return "{:.2f}".format(ret.years + ret.months/12 + ret.days/365)

    def total_ltc_remaining(self):
        return (self.total_ltc_allowed
            - self.hometown_ltc_availed 
            - self.elsewhere_ltc_availed)
    
    def hometown_ltc_remaining(self):
        return (self.hometown_ltc_allowed
            - self.hometown_ltc_availed)

    def elsewhere_ltc_remaining(self):
        return (self.elsewhere_ltc_allowed
            - self.elsewhere_ltc_availed)

    def __str__(self):
        return str(self.user.username) + ' - joined on ' + str(self.date_of_joining)
        

class Faculty_Info(models.Model): 
    faculty_user = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    pf_number = models.CharField(primary_key = True, max_length=50)
    joining_date = models.DateField()

    # THIS DESIGNATION MAPPING ALREADY EXISTS IN GLOBALS/HOLDS_DESIGNATION TABLE
    # TODO: find a way to use that table
    designation = models.ForeignKey(Designation, on_delete=models.CASCADE)
    joining_payscale = models.CharField(max_length=50)
    is_vacational = models.BooleanField(default=False)
    category = models.CharField(choices=Constants.CATEGORY, max_length=50, default='')
    pan_number = models.CharField(max_length=200, default='', blank=True, null=True)
    aadhar_number = models.CharField(max_length=200, default='', blank=True, null=True)
    local_address = models.CharField(max_length=200, default='', blank=True, null=True)
    marital_status = models.CharField(choices=Constants.MARITAL_STATUS, max_length=50, blank=True, null=True) 
    spouse_name = models.CharField(max_length=200, default='', blank=True, null=True)
    children_info = models.CharField(max_length=200, default='', blank=True, null=True)
    personal_email_id = models.EmailField(max_length=200, blank=True, null=True)
    is_archived = models.BooleanField(default=False)
    
    def __str__(self):
        return str(self.faculty_user.id.user.username) + ' info'

    class Meta:
        db_table = 'Faculty Information'
       