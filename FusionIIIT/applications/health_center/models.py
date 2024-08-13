
from django.db import models
from datetime import date
from django.contrib.auth.models import User

from applications.globals.models import ExtraInfo
from applications.hr2.models import EmpDependents

# Create your models here.

class Constants:
    DAYS_OF_WEEK = (
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday')
    )
    
    NAME_OF_DOCTOR = (
        (0, 'Dr.Sharma'),
        (1, 'Dr.Vinay'),

    )
    
    NAME_OF_PATHOLOGIST = (
        (0, 'Dr.Ajay'),
        (1, 'Dr.Rahul'),

    )

class Doctor(models.Model):
    doctor_name = models.CharField(max_length=50)
    doctor_phone = models.CharField(max_length=15)
    specialization = models.CharField(max_length=100)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.doctor_name

class Pathologist(models.Model):
    pathologist_name = models.CharField(max_length=50)
    pathologist_phone = models.CharField(max_length=15)
    specialization = models.CharField(max_length=100)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.pathologist_name

# class Complaint(models.Model):
#     user_id = models.ForeignKey(ExtraInfo,on_delete=models.CASCADE)
#     feedback = models.CharField(max_length=100, null=True, blank=False)                          #This is the feedback given by the compounder
#     complaint = models.CharField(max_length=100, null=True, blank=False)                         #Here Complaint given by user cannot be NULL!
#     date = models.DateField(auto_now=True)

class All_Medicine(models.Model):
    medicine_name = models.CharField(max_length=1000,default="NOT_SET", null=True)
    brand_name = models.CharField(max_length=1000,default="NOT_SET", null=True)
    constituents = models.TextField(default="NOT_SET",  null=True)
    manufacturer_name = models.CharField(max_length=1000,default="NOT_SET", null=True)
    threshold = models.IntegerField(default=0, null=True)
    pack_size_label = models.CharField(max_length=1000,default="NOT_SET", null=True)

    def __str__(self):
        return self.brand_name
    
class Stock_entry(models.Model):
    medicine_id = models.ForeignKey(All_Medicine, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    supplier = models.CharField(max_length=50,default="NOT_SET")
    Expiry_date = models.DateField()
    date = models.DateField(auto_now=True)
    # generic_name = models.CharField(max_length=80)

    def __str__(self):
        return self.medicine_id.medicine_name
    

class Required_medicine(models.Model):
    medicine_id = models.ForeignKey(All_Medicine,on_delete = models.CASCADE)
    quantity = models.IntegerField()
    threshold = models.IntegerField()

class Present_Stock(models.Model):
    quantity = models.IntegerField(default=0)
    stock_id = models.ForeignKey(Stock_entry,on_delete=models.CASCADE)
    medicine_id = models.ForeignKey(All_Medicine, on_delete=models.CASCADE)
    Expiry_date =models.DateField()


    # generic_name = models.CharField(max_length=80)

    def __str__(self):
        return str(self.Expiry_date)

class Doctors_Schedule(models.Model):
    doctor_id = models.ForeignKey(Doctor,on_delete=models.CASCADE)
    # pathologist_id = models.ForeignKey(Pathologist,on_delete=models.CASCADE, default=0)
    day = models.CharField(choices=Constants.DAYS_OF_WEEK, max_length=10)
    from_time = models.TimeField(null=True,blank=True)  
    to_time = models.TimeField(null=True,blank=True)
    room = models.IntegerField()
    date = models.DateField(auto_now=True)
    
class Pathologist_Schedule(models.Model):
    # doctor_id = models.ForeignKey(Doctor,on_delete=models.CASCADE)
    pathologist_id = models.ForeignKey(Pathologist,on_delete=models.CASCADE)
    day = models.CharField(choices=Constants.DAYS_OF_WEEK, max_length=10)
    from_time = models.TimeField(null=True,blank=True)
    to_time = models.TimeField(null=True,blank=True)
    room = models.IntegerField()
    date = models.DateField(auto_now=True)

class All_Prescription(models.Model):
    user_id = models.CharField(max_length=15)
    doctor_id = models.ForeignKey(Doctor, on_delete=models.CASCADE,null=True, blank=True)
    details = models.TextField(null=True)
    date = models.DateField()
    suggestions = models.TextField(null=True)
    test = models.CharField(max_length=200, null=True, blank=True)
    file_id=models.IntegerField(default=0)
    is_dependent = models.BooleanField(default=False)
    dependent_name = models.CharField(max_length=30,default="SELF")
    dependent_relation = models.CharField(max_length=20,default="SELF")
    # appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE,null=True, blank=True)

    def __str__(self):
        return self.user_id

class Prescription_followup(models.Model):
    prescription_id=models.ForeignKey(All_Prescription,on_delete=models.CASCADE)
    details = models.TextField(null=True)
    date = models.DateField()
    test = models.CharField(max_length=200, null=True, blank=True)
    suggestions = models.TextField(null=True)
    Doctor_id = models.ForeignKey(Doctor,on_delete=models.CASCADE, null=True, blank=True)
    file_id=models.IntegerField(default=0)
class All_Prescribed_medicine(models.Model):
    prescription_id = models.ForeignKey(All_Prescription,on_delete=models.CASCADE)
    medicine_id = models.ForeignKey(All_Medicine,on_delete=models.CASCADE)
    stock = models.ForeignKey(Present_Stock,on_delete=models.CASCADE,null=True)
    prescription_followup_id = models.ForeignKey(Prescription_followup,on_delete=models.CASCADE,null=True)
    quantity = models.IntegerField(default=0)
    days = models.IntegerField(default=0)
    times = models.IntegerField(default=0)
    revoked = models.BooleanField(default=False)
    revoked_date = models.DateField(null=True)
    revoked_prescription = models.ForeignKey(Prescription_followup,on_delete=models.CASCADE,null=True,related_name="revoked_priscription")

    def __str__(self):
        return self.medicine_id.medicine_name
class Required_tabel_last_updated(models.Model):
    date=models.DateField()
class files(models.Model):
    file_data = models.BinaryField()

class medical_relief(models.Model):
    description = models.CharField(max_length=200)
    file = models.FileField(upload_to='medical_files/') 
    file_id=models.IntegerField(default=0)
    compounder_forward_flag = models.BooleanField(default=False)
    acc_admin_forward_flag = models.BooleanField(default=False)
    
    
class MedicalProfile(models.Model):
    user_id = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE, null=True) 
    date_of_birth = models.DateField()
    gender_choices = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    gender = models.CharField(max_length=1, choices=gender_choices)
    blood_type_choices = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]
    blood_type = models.CharField(max_length=3, choices=blood_type_choices)
    height = models.DecimalField(max_digits=5, decimal_places=2)  
    weight = models.DecimalField(max_digits=5, decimal_places=2)  

