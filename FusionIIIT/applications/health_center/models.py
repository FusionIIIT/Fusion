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

    TIME = (
            ('0', '12 a.m.'),
            ('1', '1 a.m.'),
            ('2', '2 a.m.'),
            ('3', '3 a.m.'),
            ('4', '4 a.m.'),
            ('5', '5 a.m.'),
            ('6', '6 a.m.'),
            ('7', '7 a.m.'),
            ('8', '8 a.m.'),
            ('9', '9 a.m.'),
            ('10', '10 a.m.'),
            ('11', '11 a.m.'),
            ('12', '12 p.m.'),
            ('13', '1 p.m.'),
            ('14', '2 p.m.'),
            ('15', '3 p.m.'),
            ('16', '4 p.m.'),
            ('17', '5 p.m.'),
            ('18', '6 p.m.'),
            ('19', '7 p.m.'),
            ('20', '8 p.m.'),
            ('21', '9 p.m.'),
            ('22', '10 p.m.'),
            ('23', '11 p.m.'),
            )


class Doctor(models.Model):
    doctor_name = models.CharField(max_length=50)
    doctor_phone = models.CharField(max_length=10)
    specialization = models.CharField(max_length=10, choices=Constants.SPECIALIZATION)


class Health_Card(models.Model):
    health_card = models.CharField(max_length=20, primary_key=True)
    user_id = models.ForeignKey(ExtraInfo)


class Prescription(models.Model):
    user_id = models.ForeignKey(ExtraInfo)
    doctor_id = models.ForeignKey(Doctor)
    feedback = models.CharField(max_length=100)
    details = models.CharField(max_length=100)
    date = models.DateField()
    extra_meds = models.CharField(max_length=100)


class Complaint(models.Model):
    user_id = models.ForeignKey(ExtraInfo)
    feedback = models.CharField(max_length=100)
    complaint = models.CharField(max_length=100)


class Stock(models.Model):
    medicine_name = models.CharField(max_length=100)
    quantity = models.IntegerField(default=0)


class Stockinventory(models.Model):
    medicine_id = models.ForeignKey(Stock)
    date = models.DateTimeField(auto_now_add=True)
    quantity = models.IntegerField(default=0)


class Prescribed_medicine(models.Model):
    prescription_id = models.ForeignKey(Prescription)
    medicine_id = models.ForeignKey(Stock)


class Appointment(models.Model):
    user_id = models.ForeignKey(ExtraInfo)
    doctor_id = models.ForeignKey(Doctor)
    description = models.CharField(max_length=50)
    approval = models.BooleanField()
    appointment_date_time = models.DateTimeField()


class Ambulance_request(models.Model):
    user_id = models.ForeignKey(ExtraInfo)
    doctor_id = models.ForeignKey(Doctor)
    date_request = models.DateTimeField()
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.CharField(max_length=50)


class Hospital_admit(models.Model):
    user_id = models.ForeignKey(ExtraInfo)
    doctor_id = models.ForeignKey(Doctor)
    hospital_name = models.CharField(max_length=50)
    admission_date = models.DateField()
    discharge_date = models.DateField()
    reason = models.CharField(max_length=50)
