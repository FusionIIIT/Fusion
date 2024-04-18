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
    """
    Records information related to various Hall of Residences.

    'hall_id' and 'hall_name' store id and name of a Hall of Residence. 
    'max_accomodation' stores maximum accomodation limit of a Hall of Residence.
    'number_students' stores number of students currently residing in a Hall of Residence.
    """
    hall_id = models.CharField(max_length=10)
    hall_name = models.CharField(max_length=50)
    max_accomodation = models.IntegerField(default=0)
    number_students = models.PositiveIntegerField(default=0)
    assigned_batch = models.CharField(max_length=50, null=True, blank=True)
    TYPE_OF_SEATER_CHOICES = [
        ('single', 'Single Seater'),
        ('double', 'Double Seater'),
        ('triple', 'Triple Seater'),
    ]

    type_of_seater = models.CharField(max_length=50, choices=TYPE_OF_SEATER_CHOICES, default='single')
    def __str__(self):
        return self.hall_id 


class HallCaretaker(models.Model):
    """
    Records Caretakers of Hall of Residences.

    'hall' refers to related Hall of Residence.
    'staff' refers to related Staff details.
    """
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE)
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.hall) + '  (' + str(self.staff.id.user.username) + ')'


class HallWarden(models.Model):
    """
    Records Wardens of Hall of Residences.

    'hall' refers to related Hall of Residence.
    'faculty' refers to related Faculty details.
    """
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.hall) + '  (' + str(self.faculty.id.user.username) + ')'
    



class GuestRoomBooking(models.Model):
    """
    Records information related to booking of guest rooms in various Hall of Residences.

    'hall' refers to related Hall of Residence.
    'intender' refers to the related User who has done the booking.
    'guest_name','guest_phone','guest_email','guest_address' stores details of guests.
    'rooms_required' stores the number of rooms booked.
    'guest_room_id' refers to related guest room.
    'total_guest' stores the number of guests.
    'purpose' stores the purpose of stay of guests.
    'arrival_date','arrival_time' stores the arrival date and time of the guests.
    'departure_date','departure_time' stores the departure date and time of the guests.
    'status' stores the status of booking from the available options in 'BOOKING_STATUS'.
    'booking_date' stores the date of booking.
    'nationality' stores the nationality of the guests.
    """    
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE)
    intender = models.ForeignKey(User, on_delete=models.CASCADE)
    guest_name = models.CharField(max_length=255)
    guest_phone = models.CharField(max_length=255)
    guest_email = models.CharField(max_length=255, blank=True)
    guest_address = models.TextField(blank=True)
    rooms_required =  models.IntegerField(default=1, null=True, blank=True)
    guest_room_id = models.CharField(max_length=255, blank=True)
    total_guest = models.IntegerField(default=1)
    purpose = models.TextField()
    arrival_date = models.DateField(auto_now_add=False, auto_now=False)
    arrival_time = models.TimeField(auto_now_add=False, auto_now=False)
    departure_date = models.DateField(auto_now_add=False, auto_now=False)
    departure_time = models.TimeField(auto_now_add=False, auto_now=False)
    status = models.CharField(max_length=255, choices=HostelManagementConstants.BOOKING_STATUS ,default ="Pending")
    booking_date = models.DateField(auto_now_add=False, auto_now=False, default=timezone.now)
    nationality = models.CharField(max_length=255, blank=True)
    ROOM_TYPES = [
        ('single', 'Single'),
        ('double', 'Double'),
        ('triple', 'Triple'),
        # Add more room types as needed
    ]
    room_type = models.CharField(max_length=10, choices=ROOM_TYPES ,default='single')
    
    def __str__(self):
        return '%s ----> %s - %s' % (self.id, self.guest_name, self.status)



class StaffSchedule(models.Model):
    """
    Records schedule of staffs in various Hall of Residences.

    'hall_id' refers to the related Hall of Residence.
    'staff_type' stores the type of staff , default is 'Caretaker'.
    'day' stores the assigned  day of a schedule from the available choices in 'DAYS_OF_WEEK'.
    'start_time' stores the start time of a schedule.
    'end_time' stores the end time of a schedule.
    """    
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE)   
    staff_id = models.ForeignKey(Staff, on_delete=models.CASCADE)
    staff_type = models.CharField(max_length=100, default='Caretaker')
    day = models.CharField(max_length=15, choices=HostelManagementConstants.DAYS_OF_WEEK)
    start_time = models.TimeField(null=True,blank=True)
    end_time = models.TimeField(null=True,blank=True)

    def __str__(self):
        return str(self.staff_id) + str(self.start_time) + '->' + str(self.end_time)
    

class HostelNoticeBoard(models.Model):
    """
    Records notices of various Hall of Residences.

    'hall' refers to the related Hall of Residence.
    'posted_by' refers to information related to the user who posted it.
    'head_line' stores the headline of the notice.
    'content' stores any file uploaded by the user as a part of notice.
    'description' stores description of a notice.
    """    
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE)
    posted_by = models.ForeignKey(ExtraInfo, on_delete=models.ForeignKey)
    head_line = models.CharField(max_length=100)
    content = models.FileField(upload_to='hostel_management/', blank=True, null=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.head_line

class HostelStudentAttendence(models.Model):
    """
    Records attendance of students in various Hall of Residences.

    'hall' refers to the related Hall of Residence. 
    'student_id' refers to the related Student.
    'date' stores the date for which attendance is being taken.
    'present' stores whether the student was present on a particular date.
    """    
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE)
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField()
    present = models.BooleanField()
    
    def __str__(self):
        return str(self.student_id) + '->' + str(self.date) + '-' + str(self.present)


class HallRoom(models.Model):
    """
    Records information related to rooms in various Hall of Residences

    'hall' refers to the related Hall of Residence.
    'room_no' stores the room number.
    'block_no' stores the block number a room belongs to.
    'room_cap' stores the maximum occupancy limit of a room.
    'room_occupied' stores the current number of occupants of a room.
    """    
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE)
    room_no = models.CharField(max_length=4) 
    block_no = models.CharField(max_length=1)
    room_cap = models.IntegerField(default=3)
    room_occupied = models.IntegerField(default=0)

    def __str__(self):
        return str(self.hall) + str(self.block_no) + str(self.room_no) + str(self.room_cap) + str(self.room_occupied)


class WorkerReport(models.Model):
    """
    Records report of workers related to various Hall of Residences.

    'worker_id' stores the id of the worker. 
    'hall' refers to the related Hall of Residence.
    'worker_name' stores the name of the worker.
    'year' and 'month' stores year and month respectively.
    'absent' stores the number of days a worker was absent in a month.
    'total_day' stores the number of days in a month.
    'remark' stores remarks for a worker.
    """
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



class HostelInventory(models.Model):
    """
    Model to store hostel inventory information.
    """

    inventory_id = models.AutoField(primary_key=True)
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE)
    inventory_name = models.CharField(max_length=100)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.inventory_name
    

class HostelLeave(models.Model):
    student_name = models.CharField(max_length=100)
    roll_num = models.CharField(max_length=20)
    reason = models.TextField()
    phone_number = models.CharField(max_length=20, null=True,blank=True)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField()
    status = models.CharField(max_length=20, default='pending')
    remark = models.TextField(blank=True, null=True)
    file_upload = models.FileField(upload_to='hostel_management/', null=True, blank=True)

    def _str_(self):
        return f"{self.student_name}'s Leave"  

# changes

class HostelComplaint(models.Model):
    hall_name = models.CharField(max_length=100)
    student_name = models.CharField(max_length=100)
    roll_number = models.CharField(max_length=20)
    description = models.TextField()
    contact_number = models.CharField(max_length=15)

    def __str__(self):
        return f"Complaint from {self.student_name} in {self.hall_name}"
      
    
class HostelAllotment(models.Model):
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE)
    assignedCaretaker = models.ForeignKey(Staff, on_delete=models.CASCADE ,null=True)
    assignedWarden = models.ForeignKey(Faculty, on_delete=models.CASCADE ,null=True)
    assignedBatch=models.CharField(max_length=50)
    def __str__(self):
        return str(self.hall)+ str(self.assignedCaretaker)+str(self.assignedWarden) + str(self.assignedBatch)

class StudentDetails(models.Model):
    id = models.CharField(primary_key=True, max_length=20)
    first_name = models.CharField(max_length=100,blank=True,null=True)
    last_name = models.CharField(max_length=100,blank=True,null=True)
    programme = models.CharField(max_length=100,blank=True,null=True)
    batch = models.CharField(max_length=100,blank=True,null=True)
    room_num= models.CharField(max_length=20,blank=True,null=True)
    hall_no= models.CharField(max_length=20,blank=True,null=True)
    hall_id=models.CharField(max_length=20,blank=True,null=True)
    specialization = models.CharField(max_length=100,blank=True,null=True)
    parent_contact = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
      return self.first_name



class GuestRoom(models.Model):
    """
    'hall' foreign key: the hostel to which the room belongs
    'room' guest room number
    'vacant' boolean value to determine if the room is vacant
    'occupied_till', date field that tells the next time the room will be vacant, null if 'vacant' == True
    """
    ROOM_TYPES = [
        ('single', 'Single'),
        ('double', 'Double'),
        ('triple', 'Triple'),
    ]
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE)
    room = models.CharField(max_length=255)
    occupied_till = models.DateField(null=True, blank=True)
    vacant = models.BooleanField(default=True)
    room_type = models.CharField(max_length=10, choices=ROOM_TYPES ,default='single')
    @property
    def _vacant(self) -> bool:
        if self.occupied_till and self.occupied_till > timezone.now():
            self.vacant = False
        self.vacant = True

    

class HostelFine(models.Model):
    fine_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE,default=1)
    student_name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
    ]
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    reason = models.TextField()

    def __str__(self):
        return f"{self.student_name}'s Fine - {self.amount} - {self.status}"
    

class HostelTransactionHistory(models.Model):
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE)
    change_type = models.CharField(max_length=100)  # Example: 'Caretaker', 'Warden', 'Batch'
    previous_value = models.CharField(max_length=255)
    new_value = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.change_type} change in {self.hall} at {self.timestamp}"
    
class HostelHistory(models.Model):
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now)
    caretaker = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, related_name='caretaker_history')
    batch = models.CharField(max_length=50, null=True)
    warden = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, related_name='warden_history')

    def __str__(self):
        return f"History for {self.hall.hall_name} - {self.timestamp}"