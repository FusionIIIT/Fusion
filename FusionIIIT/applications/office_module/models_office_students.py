import datetime

from django.db import models
from django.utils.translation import gettext as _

from applications.globals.models import ExtraInfo


class Constants:

    APPROVAL_TYPE = (
        ('APPROVED', 'Approved'),
        ('PENDING', 'Pending'),
    )

    HALL_NO = (
        ('HALL-1-BOYS', 'hall-1-boys'),
        ('HALL-1-GIRLS', 'hall-1-girls'),
        ('HALL-3', 'hall-3'),
        ('HALL-4', 'hall-4'),
    )

    CLUB_TYPE = (
        ('TECHNICAL', 'technical'),
        ('CULTURAL', 'cultural'),
        ('SPORTS', 'sports'),
    )

    PROGRAM = (
        ('BTECH','btech'),
        ('BDES','bdes'),
        ('MTECH','mtech'),
        ('MDES','mdes'),
        ('PHD','phd')
    )
    YEARS = (
        ('FIRST-YEAR', 'first-year'),
        ('SECOND-YEAR', 'second-year'),
        ('THIRD-YEAR', 'third-year'),
        ('FOURTH-YEAR', 'fourth-year')
    )
    GENDER = (
        ('MALE', 'male'),
        ('FEMALE', 'female')
    )



class DeanS_approve_committes(models.Model):
    id = models.AutoField(primary_key=True)
    convener=models.ForeignKey(ExtraInfo, on_delete=models.CASCADE ,related_name='convener')
    faculty_incharge=models.ForeignKey(ExtraInfo, on_delete=models.CASCADE ,related_name='facultyincharge')
    date_approved=models.DateField(null=True, blank=True)
    description=models.CharField(max_length=200)

    def __str__(self):
        return self.convener + '-' + self.dateofapproval

class hostel_guestroom_approval(models.Model):
    id = models.AutoField(primary_key=True)
    intender=models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    hall_no=models.CharField(max_length=16, choices=Constants.HALL_NO ,default='')
    arrival_date=models.DateField(_("Date"), default=datetime.date.today)
    departure_date=models.DateField(null=True, blank=True)
    status=models.CharField(max_length=20, choices=Constants.APPROVAL_TYPE ,default='Pending')

    def __str__(self):
        return self.hall_no + '-' + self.status


class hostel_allotment(models.Model):
    id = models.AutoField(primary_key=True)
    program = models.CharField(max_length=30, choices=Constants.PROGRAM, default='')
    year = models.IntegerField(default=2016)
    gender = models.CharField(max_length=10, choices=Constants.GENDER, default='')
    hall_no = models.CharField(max_length=15, choices=Constants.HALL_NO, default='')
    number_students = models.PositiveIntegerField(default=0)
    remark = models.CharField(max_length=200)

    class Meta:
        db_table = "hostel_allotment"

class hostel_capacity(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=15, choices=Constants.HALL_NO, default='')
    current_capacity = models.PositiveIntegerField(default=0)
    total_capacity = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "hostel_capacity"

class Budget(models.Model):
    id=models.AutoField(primary_key=True)
    budget_type=models.CharField(max_length=20)
    club_type=models.CharField(max_length=20, choices=Constants.CLUB_TYPE, default='')
    budget_allocated=models.PositiveIntegerField(default=0)
    budget_expenditure=models.PositiveIntegerField(default=0)
    budget_available=models.PositiveIntegerField(default=0)
    # def __str__(self):
    #         return self.budget_type + '-' + self.budget_allocated
