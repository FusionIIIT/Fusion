
from django.db import models
from applications.globals.models import ExtraInfo




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
    





# table for employee details
# Employee model
class Employee(models.Model):

    extra_info = models.OneToOneField(ExtraInfo, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=40, default='')
    middle_name = models.CharField(max_length=40, default='')
    last_name = models.CharField(max_length=40, default='')
    father_name = models.CharField(max_length=40, default='')
    mother_name = models.CharField(max_length=40, default='')
    hire_date = models.DateTimeField(max_length=6, null=True)
    religion = models.CharField(max_length=40, default='')
    category  = models.CharField(
        max_length=50, null=False, choices=Constants.CATEGORY)
    cast  = models.CharField(max_length=40, default='')
    home_state =   models.CharField(max_length=40, default='')
    home_district =  models.CharField(max_length=40, default='')
    identification_mark =  models.CharField(max_length=40, default='')
    height  =  models.IntegerField(default=0)
    date_of_joining =  models.DateTimeField(max_length=6, null=True)
    designation =  models.CharField(max_length=40, default='')
    blood_group =   models.CharField(max_length=1, choices=Constants.BLOOD_GROUP)

    def __str__(self):
        return self.first_name
    


    
# table for employee  confidential details
class EmpConfidentialDetails(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    aadhar_no = models.IntegerField(default=0)
    medical_certificate =  models.FileField(blank=True)
    age_certificate =  models.FileField(blank=True)
    cast_certificate =  models.FileField(blank=True)
    maritial_status = models.CharField(
        max_length=50, null=False, choices=Constants.MARITIAL_STATUS)
    bank_account_no = models.IntegerField(default=0)
    salary =  models.IntegerField(default=0)

# table for employee's dependent details
class EmpDependents(model.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    name = models.CharField(max_length=40, default='')
    gender = models.CharField(max_length=1, choices=Constants.GENDER_CHOICES)
    dob =  models.DateTimeField(max_length=6, null=True)
    relationship = models.CharField(max_length=40, default='')

# table for  details about employee training
class EmpTraining(models.Model):
      employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
      training_type =  models.CharField(max_length=40, default='')
      name =  models.CharField(max_length=40, default='')
      description =  models.CharField(max_length=40, default='')
      institute_name =  models.CharField(max_length=40, default='')
      from_date =  models.DateTimeField(max_length=6, null=True)
      to_date =  models.DateTimeField(max_length=6, null=True)
