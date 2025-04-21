from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from applications.globals.models import ExtraInfo

VISITOR_CATEGORY = (
    ('A', 'A'),
    ('B', 'B'),
    ('C', 'C'),
    ('D', 'D'),
    )

ROOM_TYPE = (
    ('SingleBed', 'SingleBed'),
    ('DoubleBed', 'DoubleBed'),
    ('VIP', 'VIP')
    )

ROOM_FLOOR = (
    ('GroundFloor', 'GroundFloor'),
    ('FirstFloor', 'FirstFloor'),
    ('SecondFloor', 'SecondFloor'),
    ('ThirdFloor', 'ThirdFloor'),
    )

ROOM_STATUS = (
    ('Booked', 'Booked'),
    ('CheckedIn', 'CheckedIn'),
    ('Available', 'Available'),
    ('UnderMaintenance', 'UnderMaintenance'),
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

BILL_TO_BE_SETTLED_BY = (
    ("Intender", "Intender"),
    ("Visitor", "Visitor"),
    ("ProjectNo", "ProjectNo"),
    ("Institute", "Institute")
    )


class VisitorDetail(models.Model):
    visitor_phone = models.CharField(max_length=15)
    visitor_name = models.CharField(max_length=40)
    visitor_email = models.CharField(max_length=40, blank=True)
    visitor_organization = models.CharField(max_length=100, blank=True)
    visitor_address = models.TextField(blank=True)
    nationality = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return '{} - {}'.format(self.id, self.visitor_name, self.visitor_email, self.visitor_organization, self.visitor_address, self.visitor_phone)


class RoomDetail(models.Model):
    visitor = models.ManyToManyField(VisitorDetail, blank=True)
    room_number  = models.CharField(max_length=4, unique=True)
    room_type = models.CharField(max_length=12, choices=ROOM_TYPE)
    room_floor = models.CharField(max_length=12, choices=ROOM_FLOOR)
    room_status  = models.CharField(max_length=20, choices=ROOM_STATUS, default='Available')

    def __str__(self):
        return '{} - {}'.format(self.id, self.room_number , self.room_type, self.room_status, self.room_floor)


class BookingDetail(models.Model):
    intender = models.ForeignKey(User, related_name='intender', on_delete=models.CASCADE)
    caretaker = models.ForeignKey(User, related_name='caretaker', default=1, on_delete=models.CASCADE)
    visitor_category = models.CharField(max_length=1, choices=VISITOR_CATEGORY, default='C')
    modified_visitor_category = models.CharField(max_length=1, choices=VISITOR_CATEGORY, default='C')
    person_count = models.IntegerField(default=1)
    purpose = models.TextField(default="Hi!")
    booking_from = models.DateField()
    booking_to = models.DateField()
    arrival_time = models.TextField(null=True, blank=True)
    departure_time = models.TextField(null=True, blank=True)
    forwarded_date = models.DateField(null=True, blank=True)
    confirmed_date = models.DateField(null=True, blank=True)
    check_in = models.DateField(null=True, blank=True)
    check_out = models.DateField(null=True, blank=True)
    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=BOOKING_STATUS ,default ="Pending")
    remark = models.CharField(max_length=40, blank=True, null=True)
    visitor = models.ManyToManyField(VisitorDetail)
    image = models.FileField(null=True, blank=True, upload_to='VhImage/')
    rooms = models.ManyToManyField(RoomDetail)
    number_of_rooms =  models.IntegerField(default=1,null=True,blank=True)
    number_of_rooms_alloted =  models.IntegerField(default=1,null=True,blank=True)
    booking_date = models.DateField(auto_now_add=False, auto_now=False, default=timezone.now)
    bill_to_be_settled_by = models.CharField(max_length=15, choices=BILL_TO_BE_SETTLED_BY ,default ="Intender")

    def __str__(self):
        return '%s ----> %s - %s id is %s and category is %s' % (self.id, self.visitor, self.status, self.id, self.visitor_category)


class MealRecord(models.Model):
    booking = models.ForeignKey(BookingDetail, on_delete=models.CASCADE)
    visitor = models.ForeignKey(VisitorDetail, on_delete=models.CASCADE)
    meal_date = models.DateField()
    morning_tea = models.IntegerField(default=0)
    eve_tea = models.IntegerField(default=0)
    breakfast = models.IntegerField(default=0)
    lunch = models.IntegerField(default=0)
    dinner = models.IntegerField(default=0)
    persons=models.IntegerField(default=0)


class Bill(models.Model):
    booking = models.OneToOneField(BookingDetail, on_delete=models.CASCADE)
    room = models.ManyToManyField(RoomDetail)
    caretaker = models.ForeignKey(User, on_delete=models.CASCADE)
    meal_bill = models.IntegerField(default=0)
    room_bill = models.IntegerField(default=0)
    payment_status = models.BooleanField(default=False)
    bill_date = models.DateField(default=timezone.now, blank=True)

    def __str__(self):
        return '%s ----> %s - %s id is %s' % (self.booking.id, self.meal_bill, self.room_bill, self.payment_status)


class Inventory(models.Model):
    item_name = models.CharField(max_length=20)
    quantity = models.IntegerField(default=0)
    consumable = models.BooleanField(default=False)
    opening_stock = models.IntegerField(default=0)
    addition_stock = models.IntegerField(default=0)
    total_stock = models.IntegerField(default=0)
    serviceable = models.IntegerField(default=0)
    non_serviceable = models.IntegerField(default=0)
    inuse = models.IntegerField(default=0)
    total_usable = models.IntegerField(default=0)
    remark = models.TextField(blank=True)

    def __str__(self):
        return '{} - {}'.format(self.id, self.item_name)


class InventoryBill(models.Model):
    item_name = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    bill_number = models.CharField(max_length=40)
    cost = models.IntegerField(default=0)

    def __str__(self):
        return str(self.bill_number)
