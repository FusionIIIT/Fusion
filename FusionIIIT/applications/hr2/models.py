
from django.db import models
from applications.globals.models import ExtraInfo




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
    category  = models.CharField(
        max_length=50, null=False, choices=Constants.CATEGORY)
    cast  = models.CharField(max_length=40, default='')
    home_state =   models.CharField(max_length=40, default='')
    home_district =  models.CharField(max_length=40, default='')
    height  =  models.IntegerField(default=0)
    date_of_joining =  models.DateTimeField(max_length=6, null=True)
    designation =  models.CharField(max_length=40, default='')
    blood_group =   models.CharField(max_length=50, choices=Constants.BLOOD_GROUP)

    def __str__(self):
        return self.extra_info.user.first_name
    


    
# table for employee  confidential details
class EmpConfidentialDetails(models.Model):
    """
    table for employee  confidential details
    """
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
class EmpDependents(models.Model):
    """Table for employee's dependent details """
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, default='')
    gender = models.CharField(max_length=50, choices=Constants.GENDER_CHOICES)
    dob =  models.DateField(max_length=6, null=True)
    relationship = models.CharField(max_length=40, default='')

# table for  details about employee training
class EmpTraining(models.Model):
    """table for  details about employee training"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    training_type =  models.CharField(max_length=40, default='')
    name =  models.CharField(max_length=40, default='')
    description =  models.CharField(max_length=100, default='')
    institute_name =  models.CharField(max_length=100, default='')
    from_date =  models.DateField(max_length=6, null=True)
    to_date =  models.DateField(max_length=6, null=True)



class ForeignService(models.Model):
    """
    This table contains details about deputation, lien 
    and other foreign services of employee
    """
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    start_date =  models.DateField(max_length=6, null=True)
    end_date =  models.DateField(max_length=6, null=True)
    job_title = models.CharField(max_length=50, default='')
    organisation = models.CharField(max_length=100, default='')
    description = models.CharField(max_length=300, default='')
    salary_source = models.CharField(max_length=100, default='')
    designation = models.CharField(max_length=100, default='')
    service_type = models.CharField(max_length=100, choices=Constants.FOREIGN_SERVICE)
    
    
    
