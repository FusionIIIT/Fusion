import datetime
from django.db import models
from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo, Staff
from applications.academic_information.models import Student
from applications.complaint_system.models import Caretaker
from django.utils import timezone


class HostelManagementConstants:
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

    HALL_NO = (
        ('HALL-1','Hall-1'),
        ('HALL-3','Hall-3'),
        ('HALL-4','Hall-4'),
    )


class Hall(models.Model):
    hall_no = models.CharField(max_length=15, choices=HostelManagementConstants.HALL_NO, default='')
    max_accomodation = models.IntegerField(default=0)
    number_students = models.PositiveIntegerField(default=0)
    hall_caretaker = models.ForeignKey(Caretaker, on_delete=models.CASCADE)
    hall_warden = models.ForeignKey(Staff, on_delete=models.CASCADE)

    def __str__(self):
        return self.hall_no
    

class GuestRoomDetail(models.Model):
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE)
    room_no = models.CharField(max_length=4, unique=True)
    room_status  = models.CharField(max_length=20, choices=HostelManagementConstants.ROOM_STATUS, default='Available')

    def __str__(self):
        return self.room_no


class GuestRoomBooking(models.Model):
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE)
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    guest_name = models.CharField(max_length=100)
    guest_phone = models.CharField(max_length=15)
    guest_email = models.CharField(max_length=40, blank=True)
    guest_address = models.TextField(blank=True)
    number_of_rooms =  models.IntegerField(default=1,null=True,blank=True)
    total_guest = models.IntegerField(default=1)
    relation_with_student = models.CharField(max_length=50)
    purpose = models.TextField()
    arrival_date = models.DateField(auto_now_add=False, auto_now=False)
    arrival_time = models.TimeField(auto_now_add=False, auto_now=False)
    departure_date = models.DateField(auto_now_add=False, auto_now=False)
    departure_time = models.TimeField(auto_now_add=False, auto_now=False)
    status = models.CharField(max_length=15, choices=HostelManagementConstants.BOOKING_STATUS ,default ="Pending")
    booking_date = models.DateField(auto_now_add=False, auto_now=False, default=timezone.now)
    nationality = models.CharField(max_length=20, blank=True)
    
    def __str__(self):
        return '%s ----> %s - %s' % (self.id, self.guest_id, self.status)


class StaffSchedule(models.Model):
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE)
    staff_id = models.ForeignKey(Staff, on_delete=models.ForeignKey)
    day = models.IntegerField(choices=HostelManagementConstants.DAYS_OF_WEEK)
    start_time = models.TimeField(null=True,blank=True)
    end_time = models.TimeField(null=True,blank=True)

    def __str__(self):
        return str(self.staff_id) + str(self.start_time) + '->' + str(self.end_time)
    

class HostelNoticeBoard(models.Model):
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.ForeignKey)
    head_line = models.CharField(max_length=100)
    content = models.FileField(upload_to='hostel_management/', blank=True, null=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.head_line

class HostelStudentAttendence(models.Model):
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE)
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField()
    present = models.BooleanField()
    
    def __str__(self):
        return str(self.student_id) + '->' + str(self.date) + '-' + str(self.present)


    