import datetime
from django.db import models
from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo, Staff
from applications.academic_information.models import Student
from applications.complaint_system.models import Caretaker
from django.utils import timezone


class Constants:
    ROOM_STATUS = (
        ('Booked', 'Booked'),
        ('CheckedIn', 'CheckedIn'),
        ('Available', 'Available'),
        ('UnderMaintenance', 'UnderMaintenance'),
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

    BOOKING_STATUS = (
    ("Confirmed" , 'Confirmed'),
    ("Pending" , 'Pending'),
    ("Rejected" , 'Rejected'),
    ("Canceled" , 'Canceled'),
    ("CancelRequested" , 'CancelRequested'),
    ("CheckedIn" , 'CheckedIn'),
    ("Complete", 'Complete'),
    ("Forward", 'Forward')
    )

class GuestRoomDetail(models.Model):
    room_no = models.CharField(max_length=4, unique=True)
    room_status  = models.CharField(max_length=20, choices=Constants.ROOM_STATUS, default='Available')

    def __str__(self):
        return self.room_no


class GuestDetails(models.Model):
    guest_phone = models.CharField(max_length=15)
    guest_name = models.CharField(max_length=40)
    guest_email = models.CharField(max_length=40, blank=True)
    guest_address = models.TextField(blank=True)
    nationality = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return '{} - {}'.format(self.id, self.guest_name)


class GuestRoomBooking(models.Model):
    caretaker = models.ForeignKey(Caretaker, on_delete=models.CASCADE)
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    guest_id = models.ForeignKey(GuestDetails, on_delete=models.CASCADE)
    room_id = models.ManyToManyField(GuestRoomDetail)
    number_of_rooms =  models.IntegerField(default=1,null=True,blank=True)
    total_guest = models.IntegerField(default=1)
    relation_with_student = models.CharField(max_length=50)
    purpose = models.TextField(default="Hi!")
    booking_from = models.DateField()
    booking_upto = models.DateField()
    total_days = models.IntegerField(default=1)
    status = models.CharField(max_length=15, choices=Constants.BOOKING_STATUS ,default ="Pending")
    booking_date = models.DateField(auto_now_add=False, auto_now=False, default=timezone.now)
    
    def __str__(self):
        return '%s ----> %s - %s' % (self.id, self.guest_id, self.status)


class StaffSchedule(models.Model):
    staff_id = models.ForeignKey(Staff, on_delete=models.ForeignKey)
    day = models.IntegerField(choices=Constants.DAYS_OF_WEEK)
    start_time = models.TimeField(null=True,blank=True)
    end_time = models.TimeField(null=True,blank=True)
    date = models.DateField(auto_now=True)

    def __str__(self):
        return str(self.staff_id) + str(self.start_time) + '->' + str(self.end_time)
    

class HostelNoticeBoard(models.Model):
    user = models.ForeignKey(User, on_delete=models.ForeignKey)
    head_line = models.CharField(max_length=100)
    content = models.FileField(upload_to='hostel_management/', blank=True, null=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.head_line

class HostelStudentAttendence(models.Model):
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField()
    present = models.BooleanField()
    
    def __str__(self):
        return str(self.student_id) + '->' + str(self.date) + '-' + str(self.present)


    