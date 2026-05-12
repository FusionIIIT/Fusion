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


BOOKING_SOURCE = (
    ('online', 'Online'),
    ('telephonic', 'Telephonic'),
    ('walkin', 'Walk-in'),
)

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
    
    # UC-VH-006: Offline booking fields
    is_offline = models.BooleanField(default=False, help_text="True if booking was made offline (telephonic/walk-in)")
    booking_source = models.CharField(max_length=10, choices=BOOKING_SOURCE, default='online', help_text="Source of booking")
    intender_name = models.CharField(max_length=100, blank=True, help_text="Name of person making offline booking")
    intender_phone = models.CharField(max_length=15, blank=True, help_text="Phone of person making offline booking")
    intender_email = models.CharField(max_length=100, blank=True, help_text="Email of person making offline booking")
    intender_relation = models.CharField(max_length=50, blank=True, help_text="Relation to visitor")

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
    extra_charges = models.IntegerField(default=0)
    payment_mode = models.CharField(
        max_length=20,
        choices=(('online', 'Online'), ('offline', 'Offline')),
        blank=True,
        null=True,
    )
    transaction_id = models.CharField(max_length=120, blank=True, null=True)
    payment_screenshot = models.FileField(
        upload_to='visitor_hostel/payments/screenshots/',
        blank=True,
        null=True,
    )
    offline_bill_id = models.CharField(max_length=120, blank=True, null=True)
    offline_bill_photo = models.FileField(
        upload_to='visitor_hostel/payments/offline_bills/',
        blank=True,
        null=True,
    )
    project_number = models.CharField(max_length=120, blank=True, null=True)
    payment_status = models.BooleanField(default=False)
    bill_date = models.DateField(default=timezone.now, blank=True)

    def __str__(self):
        return '%s ----> %s - %s id is %s' % (self.booking.id, self.meal_bill, self.room_bill, self.payment_status)


REPLENISHMENT_STATUS = (
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('ordered', 'Ordered'),
    ('received', 'Received'),
)

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
    
    # UC-VH-011: Threshold management fields
    threshold_quantity = models.IntegerField(default=5, help_text="Minimum quantity before alert (BR-VH-007)")
    is_critical = models.BooleanField(default=False, help_text="Auto-set when quantity < threshold")
    last_threshold_alert = models.DateTimeField(null=True, blank=True, help_text="Last alert sent")
    unit = models.CharField(max_length=20, default='pieces', help_text="Unit of measurement")
    category = models.CharField(max_length=50, blank=True, help_text="Item category (cleaning, maintenance, etc.)")
    
    # Replenishment tracking
    pending_replenishment = models.BooleanField(default=False, help_text="Has pending replenishment request")
    last_replenishment_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return '{} - {} ({} {})'.format(self.id, self.item_name, self.quantity, self.unit)
    
    @property
    def is_below_threshold(self):
        """BR-VH-007: Check if item quantity is below threshold"""
        return self.quantity < self.threshold_quantity
    
    @property 
    def available_quantity(self):
        """Calculate actual available quantity"""
        return max(0, self.quantity - self.inuse)
    
    def save(self, *args, **kwargs):
        """Auto-update is_critical flag when quantity changes"""
        self.is_critical = self.is_below_threshold
        super().save(*args, **kwargs)


class InventoryBill(models.Model):
    item_name = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    bill_number = models.CharField(max_length=40)
    cost = models.IntegerField(default=0)
    # VhIncharge requirement: Bill photo for inventory replenishment
    bill_photo = models.ImageField(upload_to='inventory_bills/', null=True, blank=True, help_text="Bill photo is required for inventory replenishment")

    def __str__(self):
        return str(self.bill_number)


class ReplenishmentRequest(models.Model):
    """UC-VH-011: Replenishment approval workflow (BR-VH-016)"""
    inventory_item = models.ForeignKey(Inventory, on_delete=models.CASCADE, related_name='replenishment_requests')
    requested_by = models.ForeignKey(User, related_name='inventory_requests', on_delete=models.CASCADE, help_text="Caretaker who requested")
    approved_by = models.ForeignKey(User, related_name='inventory_approvals', on_delete=models.CASCADE, null=True, blank=True, help_text="VhIncharge who approved")
    
    # Request details
    requested_quantity = models.IntegerField(help_text="Quantity requested for replenishment")
    current_quantity = models.IntegerField(help_text="Current stock when request was made")
    urgency = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], default='medium')
    justification = models.TextField(help_text="Reason for replenishment request")
    
    # Approval details
    status = models.CharField(max_length=20, choices=REPLENISHMENT_STATUS, default='pending')
    approved_quantity = models.IntegerField(null=True, blank=True, help_text="Quantity approved by VhIncharge")
    approval_remarks = models.TextField(blank=True, help_text="VhIncharge remarks")
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True, help_text="When reviewed by VhIncharge")
    
    # Purchase tracking
    vendor_info = models.TextField(blank=True, help_text="Vendor details for purchase")
    actual_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    delivery_date = models.DateField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.inventory_item.item_name} - {self.requested_quantity} {self.inventory_item.unit} ({self.status})"
    
    @property
    def is_pending_approval(self):
        """BR-VH-016: Check if request needs VhIncharge approval"""
        return self.status == 'pending'
    
    @property
    def days_pending(self):
        """Calculate how many days request has been pending"""
        if self.status == 'pending':
            return (timezone.now().date() - self.created_at.date()).days
        return 0


ALERT_STATUS = (
    ('pending', 'Pending'),
    ('acknowledged', 'Acknowledged'),
    ('resolved', 'Resolved'),
)

ALERT_TYPE = (
    ('no_show', 'No-Show'),
    ('due_checkout', 'Due Checkout'),
)


class CheckInCheckOutAlert(models.Model):
    """BR-VH-010: Alert system for no-shows and due check-outs"""
    booking = models.ForeignKey(BookingDetail, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE, help_text="Type of alert: no_show or due_checkout")
    status = models.CharField(max_length=20, choices=ALERT_STATUS, default='pending', help_text="Alert status: pending, acknowledged, resolved")
    
    # Timing information
    created_at = models.DateTimeField(auto_now_add=True, help_text="When alert was created")
    acknowledged_at = models.DateTimeField(null=True, blank=True, help_text="When alert was acknowledged by staff")
    resolved_at = models.DateTimeField(null=True, blank=True, help_text="When alert was resolved")
    
    # Alert details
    message = models.TextField(help_text="Alert message describing the situation")
    severity = models.CharField(max_length=10, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], default='medium', help_text="Alert severity level")
    
    # Staff interaction
    acknowledged_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, 
                                        related_name='acknowledged_vh_alerts',
                                        help_text="Staff member who acknowledged the alert")
    acknowledgment_remarks = models.TextField(blank=True, help_text="Remarks when acknowledging the alert")
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['booking', 'alert_type', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_alert_type_display()} Alert for Booking {self.booking.id} - {self.get_status_display()}"
