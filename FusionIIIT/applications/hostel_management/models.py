import datetime
from django.db import models
from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo, Staff, Faculty
from applications.academic_information.models import Student
from django.utils import timezone


class HostelManagementConstants:
    ROOM_STATUS = (
        ('Booked', 'Booked'),
        ('CheckedIn', 'Checked In'),
        ('Available', 'Available'),
        ('UnderMaintenance', 'Under Maintenance'),
        )

    DAYS_OF_WEEK = (
            ('Monday', 'Monday'),
            ('Tuesday', 'Tuesday'),
            ('Wednesday', 'Wednesday'),
            ('Thursday', 'Thursday'),
            ('Friday', 'Friday'),
            ('Saturday', 'Saturday'),
            ('Sunday', 'Sunday')
        )

    BOOKING_STATUS = (
    ("Confirmed" , 'Confirmed'),
    ("Pending" , 'Pending'),
    ("Rejected" , 'Rejected'),
    ("Canceled" , 'Canceled'),
    ("CancelRequested" , 'Cancel Requested'),
    ("CheckedIn" , 'Checked In'),
    ("Complete", 'Complete'),
    ("Forward", 'Forward')
    )    


class Hall(models.Model):
    hall_id = models.CharField(max_length=10)
    hall_name = models.CharField(max_length=50)
    max_accomodation = models.IntegerField(default=0)
    number_students = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.hall_id 


class HallCaretaker(models.Model):
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE)
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.hall) + '  (' + str(self.staff.id.user.username) + ')'


class HallWarden(models.Model):
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.hall) + '  (' + str(self.faculty.id.user.username) + ')'
    

class GuestRoomDetail(models.Model):
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE)
    room_no = models.CharField(max_length=4, unique=True)
    room_status  = models.CharField(max_length=20, choices=HostelManagementConstants.ROOM_STATUS, default='Available')

    def __str__(self):
        return self.room_no


class GuestRoomBooking(models.Model):
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE)
    intender = models.ForeignKey(User, on_delete=models.CASCADE)
    guest_name = models.CharField(max_length=100)
    guest_phone = models.CharField(max_length=15)
    guest_email = models.CharField(max_length=40, blank=True)
    guest_address = models.TextField(blank=True)
    rooms_required =  models.IntegerField(default=1,null=True,blank=True)
    guest_room_id = models.ManyToManyField(GuestRoomDetail)
    total_guest = models.IntegerField(default=1)
    purpose = models.TextField()
    arrival_date = models.DateField(auto_now_add=False, auto_now=False)
    arrival_time = models.TimeField(auto_now_add=False, auto_now=False)
    departure_date = models.DateField(auto_now_add=False, auto_now=False)
    departure_time = models.TimeField(auto_now_add=False, auto_now=False)
    status = models.CharField(max_length=15, choices=HostelManagementConstants.BOOKING_STATUS ,default ="Pending")
    booking_date = models.DateField(auto_now_add=False, auto_now=False, default=timezone.now)
    nationality = models.CharField(max_length=20, blank=True)
    
    def __str__(self):
        return '%s ----> %s - %s' % (self.id, self.guest_name, self.status)


class StaffSchedule(models.Model):
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE)
    staff_id = models.ForeignKey(Staff, on_delete=models.ForeignKey)
    staff_type = models.CharField(max_length=100, default='Caretaker')
    day = models.CharField(max_length=15, choices=HostelManagementConstants.DAYS_OF_WEEK)
    start_time = models.TimeField(null=True,blank=True)
    end_time = models.TimeField(null=True,blank=True)

    def __str__(self):
        return str(self.staff_id) + str(self.start_time) + '->' + str(self.end_time)
    

class HostelNoticeBoard(models.Model):
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE)
    posted_by = models.ForeignKey(ExtraInfo, on_delete=models.ForeignKey)
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


class HallRoom(models.Model):
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE)
    room_no = models.CharField(max_length=4) 
    block_no = models.CharField(max_length=1)
    room_cap = models.IntegerField(default=3)
    room_occupied = models.IntegerField(default=0)

    def __str__(self):
        return str(self.hall) + str(self.block_no) + str(self.room_no) + str(self.room_cap) + str(self.room_occupied)


class WorkerReport(models.Model):
    worker_id = models.CharField(max_length=10)
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE)
    worker_name = models.CharField(max_length=50)
    year =  models.IntegerField(default=2020)
    month = models.IntegerField(default=1)
    absent = models.IntegerField(default= 0)
    total_day = models.IntegerField(default=31)
    remark = models.CharField(max_length=100)

    def str(self):
        return str(self.worker_name)+'->' + str(self.month) + '-' + str(self.absent)   