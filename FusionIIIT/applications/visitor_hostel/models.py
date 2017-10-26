from django.contrib.auth.models import User
from django.db import models

# Create your models here.

VISITOR_CATEGORY = (
    ('A', 'A'),
    ('B', 'B'),
    ('C', 'C'),
    ('D', 'D'),
    )

ROOM_TYPE = (
    ('SingleBed', 'SingleBed'),
    ('Doublebed', 'DoubleBed'),
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


class Visitor(models.Model):
    visitor_id = models.AutoField(primary_key=True)
    visitor_name = models.CharField(max_length=40)
    visitor_email = models.CharField(max_length=40)
    visitor_phone = models.CharField(max_length=12)
    visitor_address = models.TextField()
    nationality = models.CharField(max_length=20)
    intender_id = models.OneToOneField(User, on_delete=models.CASCADE)


class Book_room(models.Model):
    br_id = models.AutoField(primary_key=True)
    visitor_id = models.ForeignKey(Visitor, on_delete=models.CASCADE)
    room_count = models.IntegerField(default=0)
    visitor_category = models.CharField(max_length=1, choices=VISITOR_CATEGORY)
    person_count = models.IntegerField(default=1)
    purpose = models.TextField()
    booking_from = models.DateField()
    Booking_to = models.DateField()
    status = models.BooleanField(default=False)
    remark = models.CharField(max_length=40)
    check_in = models.DateField()
    check_out = models.DateField()


class Visitor_bill(models.Model):
    visitor_id = models.ForeignKey(Visitor, on_delete=models.CASCADE)
    caretaker_id = models.OneToOneField(User, on_delete=models.CASCADE)
    meal_bill = models.IntegerField(default=0)
    room_bill = models.IntegerField(default=0)
    payment_status = models.BooleanField(default=False)


class Room(models.Model):
    room_id = models.AutoField(primary_key=True)
    room_type = models.CharField(max_length=12, choices=ROOM_TYPE)
    room_floor = models.CharField(max_length=12, choices=ROOM_FLOOR)
    room_status = models.CharField(max_length=12, choices=ROOM_STATUS)


class Visitor_room(models.Model):
    room_id = models.ForeignKey(Room, on_delete=models.CASCADE)
    visitor_id = models.ForeignKey(Visitor, on_delete=models.CASCADE)


class Meal(models.Model):
    visitor_id = models.ForeignKey(Visitor, on_delete=models.CASCADE)
    meal_date = models.DateField()
    morning_tea = models.BooleanField(default=False)
    eve_tea = models.BooleanField(default=False)
    breakfast = models.BooleanField(default=False)
    lunch = models.BooleanField(default=False)
    dinner = models.BooleanField(default=False)


class Inventory(models.Model):
    inventory_id = models.AutoField(primary_key=True)
    item_name = models.CharField(max_length=20)
    opening_stock = models.IntegerField(default=0)
    addition_stock = models.IntegerField(default=0)
    total_stock = models.IntegerField(default=0)
    serviceable = models.IntegerField(default=0)
    non_serviceable = models.IntegerField(default=0)
    inuse = models.IntegerField(default=0)
    total_usable = models.IntegerField(default=0)
    remark = models.TextField()
