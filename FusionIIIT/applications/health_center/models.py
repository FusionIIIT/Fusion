from django.db import models

from applications.globals.models import ExtraInfo

# Create your models here.


class Constants:
    SPECIALIZATION = (
            ('0', 'Cardiology'),
            ('1', 'Oncology'),
            ('2', 'Gynaecology'),
            ('3', 'Radiology'),
            ('4', 'General Practitioner'),
            ('5', 'Primary Care Physician'),
            ('6', 'Opthomology'),
            ('7', 'Dental'),
    )
    DAYS_OF_WEEK = (
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday')
    )


class Doctor(models.Model):
    doctor_name = models.CharField(max_length=50)
    doctor_phone = models.CharField(max_length=10)
    specialization = models.CharField(max_length=10, choices=Constants.SPECIALIZATION)

    def __str__(self):
        return self.doctor_name


class Health_Card(models.Model):
    health_card = models.CharField(max_length=20, primary_key=True)
    user_id = models.ForeignKey(ExtraInfo)


class Complaint(models.Model):
    user_id = models.ForeignKey(ExtraInfo)
    feedback = models.CharField(max_length=100, null=True, blank=True)
    complaint = models.CharField(max_length=100)
    date = models.DateField(auto_now=True)


class Stock(models.Model):
    medicine_name = models.CharField(max_length=100)
    quantity = models.IntegerField(default=0)
    threshold = models.IntegerField(default=10)

    def __str__(self):
        return self.medicine_name


class Medicine(models.Model):
    patient = models.ForeignKey(ExtraInfo)
    medicine_id = models.ForeignKey(Stock)
    quantity = models.IntegerField(default=0)
    days = models.IntegerField(default=0)
    times = models.IntegerField(default=0)


class Stockinventory(models.Model):
    medicine_id = models.ForeignKey(Stock)
    date = models.DateTimeField(auto_now_add=True)
    quantity = models.IntegerField(default=0)

    def __str__(self):
        return self.medicine_id.medicine_name


class Schedule(models.Model):
    doctor_id = models.ForeignKey(Doctor)
    day = models.IntegerField(choices=Constants.DAYS_OF_WEEK)
    from_time = models.TimeField()
    to_time = models.TimeField()
    room = models.IntegerField()
    date = models.DateField(auto_now=True)


class Appointment(models.Model):
    user_id = models.ForeignKey(ExtraInfo)
    doctor_id = models.ForeignKey(Doctor)
    description = models.CharField(max_length=50)
    approval = models.NullBooleanField()
    schedule = models.ForeignKey(Schedule, null=True, blank=True)
    date = models.DateField()

    def __str__(self):
        return self.description


class Prescription(models.Model):
    user_id = models.ForeignKey(ExtraInfo)
    doctor_id = models.ForeignKey(Doctor, null=True, blank=True)
    feedback = models.CharField(max_length=100, null=True, blank=True)
    details = models.CharField(max_length=100)
    date = models.DateField()
    test = models.CharField(max_length=200, null=True, blank=True)
    test_file = models.FileField(upload_to='Administrator/health_center/', null=True, blank=True)
    appointment = models.ForeignKey(Appointment, null=True, blank=True)

    def __str__(self):
        return self.details


class Prescribed_medicine(models.Model):
    prescription_id = models.ForeignKey(Prescription)
    medicine_id = models.ForeignKey(Stock)
    quantity = models.IntegerField(default=0)
    days = models.IntegerField(default=0)
    times = models.IntegerField(default=0)

    def __str__(self):
        return self.medicine_id.medicine_name


class Ambulance_request(models.Model):
    user_id = models.ForeignKey(ExtraInfo)
    date_request = models.DateTimeField()
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    reason = models.CharField(max_length=50)


class Hospital_admit(models.Model):
    user_id = models.ForeignKey(ExtraInfo)
    doctor_id = models.ForeignKey(Doctor, null=True, blank=True)
    hospital_doctor = models.CharField(max_length=100)
    hospital_name = models.CharField(max_length=50)
    admission_date = models.DateField()
    discharge_date = models.DateField(null=True, blank=True)
    reason = models.CharField(max_length=50)
