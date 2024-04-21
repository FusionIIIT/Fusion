
from django.db import models
from datetime import date

from applications.globals.models import ExtraInfo


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
    doctor_name = models.CharField(choices=Constants.NAME_OF_DOCTOR, max_length=50)
    doctor_phone = models.CharField(max_length=15)
    specialization = models.CharField(max_length=100)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.doctor_name

class Pathologist(models.Model):
    pathologist_name = models.CharField(choices=Constants.NAME_OF_PATHOLOGIST, max_length=50)
    pathologist_phone = models.CharField(max_length=15)
    specialization = models.CharField(max_length=100)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.pathologist_name


class Complaint(models.Model):
    user_id = models.ForeignKey(ExtraInfo,on_delete=models.CASCADE)
    feedback = models.CharField(max_length=100, null=True, blank=False)                          #This is the feedback given by the compounder
    complaint = models.CharField(max_length=100, null=True, blank=False)                         #Here Complaint given by user cannot be NULL!
    date = models.DateField(auto_now=True)


class Stock(models.Model):
    medicine_name = models.CharField(max_length=100)
    quantity = models.IntegerField(default=0)
    threshold = models.IntegerField(default=10)
    # generic_name = models.CharField(max_length=80)


    def __str__(self):
        return self.medicine_name


class Medicine(models.Model):
    patient = models.ForeignKey(ExtraInfo,on_delete=models.CASCADE)
    medicine_id = models.ForeignKey(Stock,on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    days = models.IntegerField(default=0)
    times = models.IntegerField(default=0)

    def __str__(self):
        return self.medicine_id

class Hospital(models.Model):
    hospital_name=models.CharField(max_length=100)
    phone=models.CharField(max_length=10)
    def __str__(self):
        return self.hospital_name


class Expiry(models.Model):
    medicine_id=models.ForeignKey(Stock,on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    supplier=models.CharField(max_length=50)
    expiry_date=models.DateField()
    returned=models.BooleanField(default=False)
    return_date=models.DateField(null=True,blank=True)
    date=models.DateField(auto_now=True)
    def __str__(self):
        return self.medicine_id.medicine_name

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


class Counter(models.Model):
    count=models.IntegerField(default=0)
    fine=models.IntegerField(default=0)
    doc_count=models.IntegerField(default=0)
    patho_count=models.IntegerField(default=0)

    def doctor_count(self):
        self.doc_count+=1
        return ""
    def pathologist_count(self):
        self.doc_count+=1
        return ""
    def increment(self):
        self.count+=1
        return ""
    def increment_fine(self):
        self.fine+=1
        return ""
    def range_count(self):
        if self.count==0:
            dif=0
        elif self.count<=4:
            dif=self.doc_count-self.count
        elif self.count<=4:
            dif=self.count-self.doc_count
        elif self.count<=4:
            dif=self.patho_count-self.count
        else:
            dif=self.count-self.patho_count
        return range(dif)
    def empty_fine(self):
        self.count=0
        self.fine=0
        return ""
    def empty_count(self):
        self.count=0
        return ""

class Appointment(models.Model):
    user_id = models.ForeignKey(ExtraInfo,on_delete=models.CASCADE)
    doctor_id = models.ForeignKey(Doctor,on_delete=models.CASCADE)
    description = models.CharField(max_length=50)
    schedule = models.ForeignKey(Doctors_Schedule, on_delete=models.CASCADE,null=True, blank=True)
    date = models.DateField()

    def __str__(self):
        return self.description


class Prescription(models.Model):
    user_id = models.ForeignKey(ExtraInfo,on_delete=models.CASCADE)
    doctor_id = models.ForeignKey(Doctor, on_delete=models.CASCADE,null=True, blank=True)
    details = models.CharField(max_length=100)
    date = models.DateField()
    test = models.CharField(max_length=200, null=True, blank=True)
    file_id=models.IntegerField(default=0)
    # appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE,null=True, blank=True)

    def __str__(self):
        return self.details


class Prescribed_medicine(models.Model):
    prescription_id = models.ForeignKey(Prescription,on_delete=models.CASCADE)
    medicine_id = models.ForeignKey(Stock,on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    days = models.IntegerField(default=0)
    times = models.IntegerField(default=0)

    def __str__(self):
        return self.medicine_id.medicine_name


class Ambulance_request(models.Model):
    user_id = models.ForeignKey(ExtraInfo,on_delete=models.CASCADE)
    date_request = models.DateTimeField()
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    reason = models.CharField(max_length=50)

class Hospital_admit(models.Model):
    user_id = models.ForeignKey(ExtraInfo,on_delete=models.CASCADE)
    doctor_id = models.ForeignKey(Doctor, on_delete=models.CASCADE,null=True, blank=True)
    hospital_doctor = models.CharField(max_length=100)
    hospital_name = models.ForeignKey(Hospital,on_delete=models.CASCADE)
    admission_date = models.DateField()
    discharge_date = models.DateField(null=True, blank=True)
    reason = models.CharField(max_length=50)

class Announcements(models.Model):
    anno_id = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE, related_name='announcements_made')
    ann_date = models.DateTimeField(default="04-04-2021")
    message = models.CharField(max_length=200)
    batch = models.CharField(max_length=40,default="Year-1")
    department = models.CharField(max_length=40,default="ALL")
    programme = models.CharField(max_length=10)
    upload_announcement = models.FileField(upload_to='health_center/upload_announcement', null=True, default=" ")
    def __str__(self):
        return str(self.anno_id.user.username)


class SpecialRequest(models.Model):
    request_ann_maker = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE, related_name='special_requests_made')
    request_date = models.DateTimeField(default=date.today)
    brief = models.CharField(max_length=20, default='--')
    request_details = models.CharField(max_length=200)
    upload_request = models.FileField(blank=True)
    status = models.CharField(max_length=50,default='Pending')
    remarks = models.CharField(max_length=300, default="--")
    request_receiver = models.CharField(max_length=30, default="--")

    def __str__(self):
        return str(self.request_ann_maker.user.username)    

class medical_relief(models.Model):
    description = models.CharField(max_length=200)
    file = models.FileField(upload_to='medical_files/') 
    file_id=models.IntegerField(default=0)
    compounder_forward_flag = models.BooleanField(default=False)
    acc_admin_forward_flag = models.BooleanField(default=False)
    
