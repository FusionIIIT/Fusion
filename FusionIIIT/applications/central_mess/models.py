import datetime
from django.contrib.auth.models import User
from django.db import models
from applications.academic_information.models import (Student, Holiday)

# Create your models here.
LEAVE_TYPE = (
    ('casual', 'Casual'),
    ('vacation', 'Vacation')
)

MEAL = (
    ('MB', 'Monday Breakfast'),
    ('ML', 'Monday Lunch'),
    ('MD', 'Monday Dinner'),
    ('TB', 'Tuesday Breakfast'),
    ('TL', 'Tuesday Lunch'),
    ('TD', 'Tuesday Dinner'),
    ('WB', 'Wednesday Breakfast'),
    ('WL', 'Wednesday Lunch'),
    ('WD', 'Wednesday Dinner'),
    ('THB', 'Thursday Breakfast'),
    ('THL', 'Thursday Lunch'),
    ('THD', 'Thursday Dinner'),
    ('FB', 'Friday Breakfast'),
    ('FL', 'Friday Lunch'),
    ('FD', 'Friday Dinner'),
    ('SB', 'Saturday Breakfast'),
    ('SL', 'Saturday Lunch'),
    ('SD', 'Saturday Dinner'),
    ('SUB', 'Sunday Breakfast'),
    ('SUL', 'Sunday Lunch'),
    ('SUD', 'Sunday Dinner')
)

STATUS = (
    ('0', 'rejected'),
    ('1', 'pending'),
    ('2', 'accepted'),
    ('3', 'escalated')
)

TIME = (
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
    ('21', '9 p.m.')
)

FEEDBACK_TYPE = (
    ('maintenance', 'Maintenance'),
    ('food', 'Food'),
    ('cleanliness', 'Cleanliness & Hygiene'),
    ('others', 'Others')
)

SPECIAL_REQUEST_TYPE = (
    ('medical', 'Medical'),
    ('event', 'Event'),
)

REQUEST_STATUS = (
    ('pending', 'Pending'),
    ('escalated', 'Escalated'),
    ('accept', 'Accepted'),
    ('reject', 'Rejected'),
    ('cancelled', 'Cancelled')
)

POLL_STATUS = (
    ('open', 'Open'),
    ('closed', 'Closed')
)

ANNOUNCEMENT_PRIORITY = (
    ('normal', 'Normal'),
    ('high', 'High'),
    ('urgent', 'Urgent'),
)

MONTHS = (
    ('Jan', 'January'),
    ('Feb', 'February'),
    ('Mar', 'March'),
    ('Apr', 'April'),
    ('May', 'May'),
    ('Jun', 'June'),
    ('Jul', 'July'),
    ('Aug', 'August'),
    ('Sep', 'September'),
    ('Oct', 'October'),
    ('Nov', 'November'),
    ('Dec', 'December')

)

INTERVAL = (
    ('Breakfast', 'Breakfast'),
    ('Lunch', 'Lunch'),
    ('Dinner', 'Dinner')
)

MESS_OPTION = (
    ('mess1', 'Veg_mess'),
    ('mess2', 'Non_veg_mess')
)


class Messinfo(models.Model):
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    mess_option = models.CharField(max_length=20, choices=MESS_OPTION,
                                   default='mess2')

    class Meta:
        unique_together = (('student_id', 'mess_option'),)

    def __str__(self):
        return '{} - {}'.format(self.student_id.id, self.mess_option)


class RegistrationRequest(models.Model):
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    mess_option = models.CharField(max_length=20, choices=MESS_OPTION)
    start_date = models.DateField()
    payment_date = models.DateField()
    amount = models.PositiveIntegerField(default=0)
    Txn_no = models.CharField(max_length=100)
    img = models.FileField(upload_to='central_mess/registration_receipts/',
                           blank=True, null=True)
    registration_remark = models.TextField(blank=True, default='')
    escalation_remark = models.TextField(blank=True, default='')
    warden_remark = models.TextField(blank=True, default='')
    override_conditions = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=REQUEST_STATUS,
                              default='pending')
    escalated_at = models.DateTimeField(blank=True, null=True)
    warden_decided_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return '{} - {}'.format(self.student_id.id, self.status)


class DeregistrationRequest(models.Model):
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    end_date = models.DateField()
    deregistration_remark = models.TextField(blank=True, default='')
    escalation_remark = models.TextField(blank=True, default='')
    warden_remark = models.TextField(blank=True, default='')
    override_conditions = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=REQUEST_STATUS,
                              default='pending')
    escalated_at = models.DateTimeField(blank=True, null=True)
    warden_decided_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return '{} - {}'.format(self.student_id.id, self.status)


class PaymentUpdateRequest(models.Model):
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    payment_date = models.DateField()
    amount = models.PositiveIntegerField(default=0)
    Txn_no = models.CharField(max_length=100)
    img = models.FileField(upload_to='central_mess/payment_updates/',
                           blank=True, null=True)
    update_remark = models.TextField(blank=True, default='')
    escalation_remark = models.TextField(blank=True, default='')
    warden_remark = models.TextField(blank=True, default='')
    override_conditions = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=REQUEST_STATUS,
                              default='pending')
    escalated_at = models.DateTimeField(blank=True, null=True)
    warden_decided_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return '{} - {}'.format(self.student_id.id, self.status)


class Mess_reg(models.Model):
    sem = models.IntegerField(default='1')
    start_reg = models.DateField(default=datetime.date.today)
    end_reg = models.DateField(default=datetime.date.today)


class MessBillBase(models.Model):
    bill_amount = models.PositiveIntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)


def current_month():
    return datetime.datetime.now().strftime("%B")


def current_year():
    return datetime.datetime.now().strftime("%Y")


class Monthly_bill(models.Model):
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    month = models.CharField(max_length=20, default=current_month)
    year = models.IntegerField(default=current_year)
    amount = models.IntegerField(default=0)
    rebate_count = models.IntegerField(default=0)
    rebate_amount = models.IntegerField(default=0)
    nonveg_total_bill = models.IntegerField(default=0)
    total_bill = models.IntegerField(default=0)

    class Meta:
        unique_together = (('student_id', 'month', 'year'),)

    def __str__(self):
        return '{} - {} - {}'.format(self.student_id.id, self.month, self.year)


class Payments(models.Model):
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    sem = models.IntegerField()
    year = models.IntegerField(default=current_year)
    amount_paid = models.IntegerField(default=0)
    payment_date = models.DateField(blank=True, null=True)
    payment_month = models.CharField(max_length=20, blank=True, default='')
    payment_year = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=REQUEST_STATUS,
                              default='accept')
    Txn_no = models.CharField(max_length=100, blank=True, default='')

    class Meta:
        unique_together = (('student_id', 'sem', 'year'),)

    def __str__(self):
        return '{} - {}'.format(self.student_id.id, self.sem)


class Menu(models.Model):
    mess_option = models.CharField(max_length=20, choices=MESS_OPTION,
                                   default='mess2')
    meal_time = models.CharField(max_length=20, choices=MEAL)
    dish = models.CharField(max_length=200)

    def __str__(self):
        return '{} - {} - {}'.format(self.mess_option,
                                     self.meal_time, self.dish)


class MenuPoll(models.Model):
    question = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    mess_option = models.CharField(max_length=20, choices=MESS_OPTION)
    meal_time = models.CharField(max_length=20, choices=MEAL,
                                 blank=True, null=True)
    poll_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=POLL_STATUS,
                              default='open')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                   blank=True, null=True,
                                   related_name='menu_polls_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return '{} - {}'.format(self.mess_option, self.question)


class MenuPollOption(models.Model):
    poll = models.ForeignKey(MenuPoll, on_delete=models.CASCADE,
                             related_name='options')
    option_text = models.CharField(max_length=200)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ('display_order', 'id')
        unique_together = (('poll', 'option_text'),)

    def __str__(self):
        return '{} - {}'.format(self.poll_id, self.option_text)


class MenuPollVote(models.Model):
    poll = models.ForeignKey(MenuPoll, on_delete=models.CASCADE,
                             related_name='votes')
    option = models.ForeignKey(MenuPollOption, on_delete=models.CASCADE,
                               related_name='votes')
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (('poll', 'student_id'),)

    def __str__(self):
        return '{} - {}'.format(self.poll_id, self.student_id.id)


class MessAnnouncement(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(max_length=20,
                                choices=ANNOUNCEMENT_PRIORITY,
                                default='normal')
    publish_date = models.DateField(default=datetime.date.today)
    expiry_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                   blank=True, null=True,
                                   related_name='mess_announcements_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-publish_date', '-created_at')

    def __str__(self):
        return '{} - {}'.format(self.title, self.publish_date)


class Rebate(models.Model):
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    start_date = models.DateField(default=datetime.date.today)
    end_date = models.DateField(default=datetime.date.today)
    purpose = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS, default='1')
    app_date = models.DateField(default=datetime.date.today)
    leave_type = models.CharField(choices=LEAVE_TYPE, max_length=20, default="casual")
    rebate_remark = models.TextField(blank=True, default='')
    escalation_remark = models.TextField(blank=True, default='')
    warden_remark = models.TextField(blank=True, default='')
    override_conditions = models.TextField(blank=True, default='')
    escalated_at = models.DateTimeField(blank=True, null=True)
    warden_decided_at = models.DateTimeField(blank=True, null=True)
    # leave_document = models.FileField(upload_to='central_mess/')

    def __str__(self):
        return str(self.student_id.id)


class Vacation_food(models.Model):
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    start_date = models.DateField(default=datetime.date.today)
    end_date = models.DateField(default=datetime.date.today)
    purpose = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS, default='1')
    app_date = models.DateField(default=datetime.date.today)

    def __str__(self):
        return str(self.student_id.id)


class Nonveg_menu(models.Model):
    dish = models.CharField(max_length=20)
    price = models.IntegerField()
    order_interval = models.CharField(max_length=20, choices=INTERVAL,
                                      default='Breakfast')

    def __str__(self):
        return '{} - {}'.format(self.dish, self.price)


class Nonveg_data(models.Model):
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    order_date = models.DateField(default=datetime.date.today)
    order_interval = models.CharField(max_length=20, choices=INTERVAL,
                                      default='Breakfast')
    dish = models.ForeignKey(Nonveg_menu, on_delete=models.CASCADE)
    app_date = models.DateField(default=datetime.date.today)

    def __str__(self):
        return str(self.student_id.id)


class Special_request(models.Model):
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    start_date = models.DateField(default=datetime.date.today)
    end_date = models.DateField(default=datetime.date.today)
    request = models.TextField()
    request_type = models.CharField(max_length=20,
                                    choices=SPECIAL_REQUEST_TYPE,
                                    default='event')
    status = models.CharField(max_length=20, choices=STATUS, default='1')
    item1 = models.CharField(max_length=50)
    item2 = models.CharField(max_length=50)
    semester = models.PositiveSmallIntegerField(default=1)
    app_date = models.DateField(default=datetime.date.today)
    supporting_document = models.FileField(
        upload_to='central_mess/special_requests/',
        blank=True,
        null=True,
    )
    special_request_remark = models.TextField(blank=True, default='')
    escalation_remark = models.TextField(blank=True, default='')
    warden_remark = models.TextField(blank=True, default='')
    override_conditions = models.TextField(blank=True, default='')
    escalated_at = models.DateTimeField(blank=True, null=True)
    warden_decided_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return str(self.student_id.id)


class Mess_meeting(models.Model):
    meet_date = models.DateField()
    agenda = models.TextField()
    venue = models.TextField()
    meeting_time = models.CharField(max_length=20, choices=TIME)

    def __str__(self):
        return '{} - {}'.format(self.meet_date, self.agenda)


class Mess_minutes(models.Model):
    meeting_date = models.OneToOneField(Mess_meeting, on_delete=models.CASCADE)
    mess_minutes = models.FileField(upload_to='central_mess/')

    def __str__(self):
        return '{} - {}'.format(self.meeting_date.meet_date, self.mess_minutes)


class Menu_change_request(models.Model):
    dish = models.ForeignKey(Menu, on_delete=models.CASCADE)
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    reason = models.TextField()
    request = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS, default='1')
    app_date = models.DateField(default=datetime.date.today)

    def __str__(self):
        return '{} - {} - {} - {}'.format(self.id, self.dish, self.request, self.status)


class Feedback(models.Model):
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    mess = models.CharField(max_length=10, choices=MESS_OPTION, default='mess1')
    mess_rating = models.PositiveSmallIntegerField(default='5')
    fdate = models.DateField(default=datetime.date.today)
    description = models.TextField()
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPE)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return str(self.student_id.id)

class RefundCancellation(models.Model):
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    amount = models.IntegerField(default=0)
    reason = models.TextField()
    warden_approved = models.BooleanField(default=False)
    finance_processed = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student_id} - {self.amount}"

class VacationSurvey(models.Model):
    caretaker = models.ForeignKey(User, on_delete=models.CASCADE)
    start_date = models.DateField(default=datetime.date.today)
    end_date = models.DateField(default=datetime.date.today)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Survey {self.id} for vacation: {self.start_date} to {self.end_date}"


class VacationSurveyResponse(models.Model):
    survey = models.ForeignKey(VacationSurvey, on_delete=models.CASCADE, related_name='responses')
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    attending = models.BooleanField(default=False)
    details = models.TextField(blank=True, null=True)
    response_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Response {self.id} by {self.student.id} for Survey {self.survey.id}"
