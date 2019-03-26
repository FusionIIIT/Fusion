import datetime

from django.db import models

from applications.academic_information.models import (Course, Grades,
                                                      Instructor, Meeting, Spi,
                                                      Student)
from applications.academic_procedures.models import Thesis
from applications.filetracking.models import Tracking
from applications.globals.models import (DepartmentInfo, Designation,
                                         ExtraInfo, Faculty, HoldsDesignation,
                                         Staff)
from applications.leave.models import Leave

from .models_office_students import *


class Constants:
    DAY_CHOICES = (
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
    )
    ACTION = (
        ('forward', 'forwarded'),
        ('revert', 'revert'),
        ('accept', 'accept'),
        ('reject', 'reject')

    )
    STATUS = (
        ('0', 'unseen'),
        ('1', 'seen')
    )
    APPROVAL = (
        ('0', 'reject'),
        ('1', 'accept')
    )
    APPROVAL_TYPE = (
        ('APPROVED', 'Approved'),
        ('PENDING', 'Pending'),
    )

    HALL_NO = (
        ('HALL-1','hall-1'),
        ('HALL-3','hall-3'),
        ('HALL-4','hall-4'),
    )
    DEPARTMENT=(
		('civil','civil'),
		('electrical','electrical')
	)

    BUILDING=(
		('corelab','corelab'),
		('computer center','computer center'),
		('hostel','hostel'),
		('mess','mess'),
		('library','library'),
		('cc','cc')
	)

    STATUS_CHOICES = (
        ('Forward', 'FORWARD'),
        ('Accept', 'ACCEPT')
    )



    PROJECT_TYPE = (
        ('SRes', 'Sponsored Research'),
        ('Consultancy', 'Consultancy'),
        ('Testing', 'Testing')
    )

    RESPONSE_TYPE = (
        ('Approve', 'Approve'),
        ('Disapprove', 'Disapprove'),
        ('Pending' , 'Pending')
    )

    RESPONSE_TYPE1 = (
        ('Forwarded', 'Forwarded'),
        ('Pending' , 'Pending')
    )

    TICK_TYPE = (
        ('NO', 'YES'),
        ('NO', 'NO')
    )

    PROJECT_OPERATED = (
        ('PI', 'Only by PI'),
        ('any', 'Either PI or CO-PI')
    )


    TRAVEL_CHOICES = (
        ('road', 'ROAD'),
        ('rail', 'RAIL')
      )

    TICK_TYPE = (
        ('Computer Graphics', 'Computer Graphics'),
        ('Machine Learning', 'Machine Learning'),
        ('Image Processing','Image Processing'),
        ('Data Structure','Data Structure')
    )

    APPROVAL_TYPE = (
        ('APPROVED', 'Approved'),
        ('PENDING', 'Pending'),
    )



PURCHASE_STATUS = (

    ('0', "Pending"),
    ('1', "Approve"),
    ('2', "Items Ordered"),
    ('3', "Items Puchased"),
    ('4', "Items Delivered"),

)

APPROVE_TAG = (

    ('0', "Pending"),
    ('1', "Approve"),
)


PURCHASE_TYPE = (

    ('0', "Amount < 25000"),
    ('1', "25000<Amount<250000"),

    ('2', "250000<Amount < 2500000"),
    ('3', "Amount>2500000"),

)

NATURE_OF_ITEM1 = (
    ('0', "Non-consumable"),
    ('1', "Consumable"),

)
NATURE_OF_ITEM2 = (
    ('0', "Equipment"),
    ('1', "Machinery"),
    ('2', "Furniture"),
    ('3', "Fixture"),

)

ITEM_TYPE = (
    ('0', "Non-consumable"),
    ('1', "Consumable"),

)



class Assistantship(models.Model):
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    instructor_id = models.ForeignKey(Instructor, on_delete=models.CASCADE)
    file = models.FileField(upload_to='documents/',blank=True,null=True)
    action = models.IntegerField(default=0)
    comments = models.CharField(null=True,blank=True,max_length=150);
    class Meta:
        db_table = 'Assistantship'
        unique_together = ('student_id','instructor_id')
    def __str__(self):
        return '{} - {}'.format(self.student_id, self.instructor_id)



class Project_Registration(models.Model):
    PI_id = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    project_title = models.CharField(max_length=200)
    sponsored_agency = models.CharField(max_length=100)
    CO_PI = models.CharField(max_length=100 ,null=True)
    start_date = models.DateField(null=True,blank=True)
    duration = models.CharField(default='0', max_length=100)
    agreement = models.CharField(choices=Constants.TICK_TYPE,
                                      max_length=10, default='NO')
    amount_sanctioned = models.IntegerField(default=0)
    project_type = models.CharField(choices=Constants.PROJECT_TYPE,
                                 max_length=25)
    project_operated = models.CharField(choices=Constants.PROJECT_OPERATED,
                                    max_length=50,default='me')
    remarks = models.CharField(max_length=200)
    fund_recieved_date = models.DateField(null=True,blank=True)
    HOD_response = models.CharField(choices=Constants.RESPONSE_TYPE1,
                                 max_length=10, default='Pending')
    DRSPC_response = models.CharField(choices=Constants.RESPONSE_TYPE,
                                 max_length=10, default='Pending')
    applied_date=models.DateField(null=True,blank=True)
    description=models.CharField(max_length=200,null=True)


    def __str__(self):
        return self.project_title



class Project_Extension(models.Model):
    project_id = models.ForeignKey(Project_Registration, on_delete=models.CASCADE)
    date = models.DateField()
    extended_duration = models.CharField(max_length=300)
    extension_details = models.CharField(max_length=300)
    HOD_response = models.CharField(choices=Constants.RESPONSE_TYPE1,
                                    max_length=10, default='Pending')
    DRSPC_response = models.CharField(choices=Constants.RESPONSE_TYPE,
                                      max_length=10, default='Pending')

    def __str__(self):
        return str(self.project_id)



class Project_Closure(models.Model):
    project_id = models.ForeignKey(Project_Registration, on_delete=models.CASCADE)
    completion_date = models.DateField()
   # extended_duration = models.CharField(max_length=200, blank=True, null=True)
    expenses_dues = models.CharField(choices=Constants.TICK_TYPE,
                                    max_length=10, default='Pending')
    expenses_dues_description = models.CharField(max_length=200,blank=True, null=True)
    payment_dues = models.CharField(choices=Constants.TICK_TYPE,
                                     max_length=10, default='Pending')
    payment_dues_description = models.CharField(max_length=200, blank=True, null=True)
    salary_dues = models.CharField(choices=Constants.TICK_TYPE,
                                     max_length=10, default='Pending')
    salary_dues_description = models.CharField(max_length=200, blank=True, null=True)
    advances_dues = models.CharField(choices=Constants.TICK_TYPE,
                                     max_length=10, default='Pending')
    advances_description = models.CharField(max_length=200, blank=True, null=True)
    others_dues = models.CharField(choices=Constants.TICK_TYPE,
                                     max_length=10, default='Pending')
    other_dues_description = models.CharField(max_length=200, blank=True, null=True)
    overhead_deducted = models.CharField(choices=Constants.TICK_TYPE,
                                     max_length=10, default='Pending')
    overhead_description = models.CharField(max_length=200, blank=True, null=True)
    HOD_response = models.CharField(choices=Constants.RESPONSE_TYPE1,
                                    max_length=10, default='Pending')
    DRSPC_response = models.CharField(choices=Constants.RESPONSE_TYPE,
                                      max_length=10, default='Pending')
    remarks=models.CharField(max_length=300,null=True)
    extended_duration=models.CharField(default='0', max_length=100,null=True)


    def __str__(self):
        return str(self.project_id)

class Project_Reallocation(models.Model):
    project_id = models.ForeignKey(Project_Registration, on_delete=models.CASCADE)
    date = models.DateField()
    previous_budget_head = models.CharField(max_length=300)
    previous_amount = models.IntegerField(default=0)
    pf_no = models.CharField(max_length=100,null=True)
    new_budget_head = models.CharField(max_length=300)
    new_amount = models.IntegerField(default=0)
    transfer_reason = models.CharField(max_length=300)
    HOD_response = models.CharField(choices=Constants.RESPONSE_TYPE1,
                                    max_length=10, default='Pending')
    DRSPC_response = models.CharField(choices=Constants.RESPONSE_TYPE,
                                      max_length=10, default='Pending')


    def __str__(self):
        return str(self.project_id)




class Member(models.Model):
	member_id = models.ForeignKey(Faculty)
	meeting_id = models.ForeignKey(Meeting)

	class Meta:
		db_table = 'Member'
		unique_together = (('member_id', 'meeting_id'))

	def __str__(self):
			return str(self.member_id)


class Registrar(models.Model):
    file_name = models.CharField(max_length=50)
    date = models.DateField()
    purpose = models.CharField(max_length=100)
    status = models.CharField(max_length=1, choices=Constants.STATUS, default=0)
    file = models.FileField()


class Requisitions(models.Model):
	userid=models.ForeignKey(ExtraInfo,on_delete=models.CASCADE)
	req_date=models.DateTimeField(auto_now_add=True)
	title=models.CharField(max_length=50)
	department=models.CharField(max_length=50,choices=Constants.DEPARTMENT)
	building=models.CharField(max_length=50,choices=Constants.BUILDING)
	description=models.CharField(max_length=200)
	assign_date=models.DateTimeField(auto_now_add=True,null=True)
	assign_title=models.CharField(max_length=50,null=True)
	assign_description = models.CharField(max_length=200,null=True)
	estimate=models.FileField(upload_to='documents/',blank=True,null=True)
	tag=models.IntegerField(default=0)                           # 0: ongoing  1: completed

	def __str__(self):
		return str(self.id)

class Filemovement(models.Model):
	rid=models.ForeignKey(Requisitions,on_delete=models.CASCADE)
	sentby=models.ForeignKey(HoldsDesignation,on_delete=models.CASCADE,related_name='sent_by')
	receivedby=models.ForeignKey(HoldsDesignation,on_delete=models.CASCADE,related_name='received_by')
	date=models.DateTimeField(auto_now_add=True)
	remarks=models.CharField(max_length=200,null=True)
	actionby_receiver=models.CharField(max_length=50,choices=Constants.ACTION)

class vendor(models.Model):
    vendor_name = models.CharField(max_length=100)
    vendor_address = models.CharField(max_length=200)
    vendor_item = models.CharField(max_length=200)

    class Meta:
        db_table = 'vendor'


class apply_for_purchase(models.Model):
    indentor_name = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE,related_name='indentor_name')
    # designation = models.ForeignKey(Designation, on_delete=models.CASCADE)
    inspecting_authority = models.CharField(max_length=200, default='0')
    expected_purchase_date = models.DateField()
    order_date = models.DateField(default=datetime.date.today)
    purchase_status = models.IntegerField(choices=PURCHASE_STATUS, default=0)
    # purchase_officer = models.ForeignKey(Staff, on_delete=models.CASCADE, default='0')
    amount = models.IntegerField(default='0')
    purchase_date = models.DateField(default='2018-06-01')

    registrar_approve_tag = models.IntegerField(choices=APPROVE_TAG, default=0)
    accounts_approve_tag = models.IntegerField(choices=APPROVE_TAG, default=0)

    purchase_type = models.IntegerField(choices=PURCHASE_TYPE, default=0)
    purpose = models.CharField(max_length=200, default=0)

    budgetary_head = models.CharField(max_length=200, default=0)
    invoice = models.FileField(default=0)
    nature_of_item1 = models.IntegerField(choices=NATURE_OF_ITEM1, default=0)
    nature_of_item2 = models.IntegerField(choices=NATURE_OF_ITEM2, default=0)

    item_name = models.CharField(max_length=100, default=0)
    expected_cost = models.IntegerField(default=0)
    quantity = models.IntegerField(default=0)

    class Meta:
        db_table = 'apply_for_purchase'

class stock(models.Model):
    item_name = models.CharField(max_length=100)
    quantity = models.IntegerField(default='0')

    item_type = models.IntegerField(choices=ITEM_TYPE, default='0')

    class Meta:
        db_table = 'stock'


class purchase_commitee(models.Model) :
    local_comm_mem1 = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE,related_name='local_comm_mem1')
    local_comm_mem2 = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE,related_name='local_comm_mem2')
    local_comm_mem3 = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE,related_name='local_comm_mem3')
    approve_mem1 = models.IntegerField(choices=APPROVE_TAG, default ='0')
    approve_mem2 = models.IntegerField(choices=APPROVE_TAG, default ='0')
    approve_mem3 = models.IntegerField(choices=APPROVE_TAG, default ='0')

    class Meta:
        db_table = 'purchase_commitee'


class quotations(models.Model) :
    quotation1 = models.FileField()
    quotation2 = models.FileField()
    quotation3 = models.FileField()

    class Meta:
        db_table = 'quotations'


class Registrar_File(models.Model):
    file_id = models.ForeignKey(Tracking, on_delete=models.CASCADE)
    status = models.IntegerField(choices=Constants.STATUS, default=0)
    approval = models.IntegerField(choices=Constants.APPROVAL, default=0)
    section_name = models.CharField(max_length=50)
    section_type = models.CharField(max_length=20)



class registrar_create_doc(models.Model):
    file_name = models.CharField(max_length=50)
    purpose =  models.CharField(max_length=100)
    Description = models.CharField(max_length=200)
    file=models.FileField()

class registrar_director_section(models.Model):
    file_name = models.CharField(max_length=50)
    date = models.DateField()
    purpose = models.CharField(max_length=100)
    status = models.CharField(max_length=1,choices=Constants.STATUS, default=0)


class registrar_purchase_sales_section(models.Model):
    file_name = models.CharField(max_length=50)
    member1 = models.CharField(max_length=50)
    member2 = models.CharField(max_length=50)
    member3 = models.CharField(max_length=50)
    date = models.DateField()
    purpose = models.CharField(max_length=100)
    status = models.IntegerField(choices=Constants.STATUS, default=0)
    file = models.FileField()

class registrar_finance_section(models.Model):
        file_name = models.CharField(max_length=50)
        date = models.DateField()
        purpose = models.CharField(max_length=100)
        status = models.IntegerField(choices=Constants.STATUS)
        file = models.FileField()


class registrar_establishment_section(models.Model):
    person_name = models.CharField(max_length=50)
    person_mail_id = models.CharField(max_length=50,default="xyz")
    date = models.DateField()
    duration = models.IntegerField()
    post = models.CharField(max_length=100)
    file = models.FileField()

class registrar_general_section(models.Model):
    file_name = models.CharField(max_length=50)
    date = models.DateField()
    amount = models.IntegerField()
    status = models.IntegerField(choices=Constants.STATUS, default=0)
    file = models.ForeignKey(registrar_create_doc, on_delete=models.CASCADE)


class LTC(models.Model):
    name = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    designation = models.ForeignKey(Designation, on_delete=models.CASCADE)
    department = models.ForeignKey(DepartmentInfo, on_delete=models.CASCADE)
    date_request = models.DateField()
    leave = models.ForeignKey(Leave, on_delete=models.CASCADE)
    travel_mode = models.CharField(max_length=10, choices=Constants.TRAVEL_CHOICES, default='ROAD')
    advance = models.IntegerField(default=0)
    family_details = models.TextField(max_length=500)

    class Meta:
        db_table = 'LTC'

    def __str__(self):
        return str(self.id)


class CPDA(models.Model):
    name = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    designation = models.ForeignKey(Designation, on_delete=models.CASCADE)
    PF_no = models.CharField(max_length=100)
    purpose = models.CharField(max_length=100)
    amoutn = models.IntegerField(default=0)
    class Meta:
        db_table = 'CPDA'

    def __str__(self):
        return str(self.id)


class Auto_fair_claim(models.Model):
    name = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    purpose = models.CharField(max_length=100)
    amount = models.IntegerField(default=0)
    auto_reg_no = models.CharField(max_length=50)
    auto_contact = models.IntegerField(default=0)
    bill =  models.FileField(upload_to='hod/')
    date = models.DateField();
    class Meta:
        db_table = 'auto_fair_claim'


class Teaching_credits1(models.Model):
    roll_no = models.CharField(max_length=100,primary_key=True)
    name = models.CharField(max_length=100)
    programme = models.CharField(max_length=100)
    branch = models.CharField(max_length=100)
    course1 = models.CharField(choices=Constants.TICK_TYPE,
                                      max_length=100, default='NO')
    course2 = models.CharField(choices=Constants.TICK_TYPE,
                                      max_length=100, default='NO')
    course3 = models.CharField(choices=Constants.TICK_TYPE,
                                      max_length=100, default='NO')
    tag = models.IntegerField(default=0)
    class Meta:
        db_table = 'Teaching_credits1'
    def __str__(self):
        return str(self.roll_no)


class Assigned_Teaching_credits(models.Model):
    roll_no = models.ForeignKey(Teaching_credits1, on_delete=models.CASCADE)
    assigned_course = models.CharField(max_length=100,default='NO')
    class Meta:
        db_table = 'Assigned_Teaching_credits'


class Lab(models.Model):
    lab = models.CharField(max_length=10)
    lab_instructor = models.CharField(max_length=30)
    day = models.CharField(max_length=10,choices=Constants.DAY_CHOICES, default='Monday')
    s_time = models.CharField(max_length=6, default='0:00')
    e_time = models.CharField(max_length=6, default='0:00')
    class Meta:
        db_table = 'Lab'

    def __str__(self):
        return str(self.lab)

class TA_assign(models.Model):
    roll_no = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE, related_name='TA_id')
    lab = models.ForeignKey(Lab, on_delete=models.CASCADE)
    balance = models.IntegerField(default=2)
    class Meta:
        db_table = 'TA_assign'

    def __str__(self):
        return str(self.id)
