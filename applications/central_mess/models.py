import datetime

from django.db import models

from applications.academic_information.models import Student

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
    ('2', 'accepted')
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
    ('mess1', 'Non_veg_mess'),
    ('mess2', 'Veg_mess')
)


class Messinfo(models.Model):
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    mess_option = models.CharField(max_length=20, choices=MESS_OPTION,
                                   default='mess2')

    class Meta:
        unique_together = (('student_id', 'mess_option'),)

    def __str__(self):
        return '{} - {}'.format(self.student_id.id, self.mess_option)


class Mess_reg(models.Model):
    sem = models.IntegerField(default='1')
    start_reg = models.DateField(default=datetime.date.today)
    end_reg = models.DateField(default=datetime.date.today)



class Monthly_bill(models.Model):
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    month = models.CharField(max_length=20, choices=MONTHS)
    amount = models.IntegerField(default=2370)
    rebate_count = models.IntegerField(default=0)
    rebate_amount = models.IntegerField(default=0)
    nonveg_total_bill = models.IntegerField(default=0)
    total_bill = models.IntegerField(default=2370)


    class Meta:
        unique_together = (('student_id', 'month'),)

    def __str__(self):
        return '{} - {}'.format(self.student_id.id, self.month)



class Payments(models.Model):
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    sem = models.IntegerField()
    amount_paid = models.IntegerField(default=0)


    class Meta:
        unique_together = (('student_id', 'sem'),)

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



class Rebate(models.Model):
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    start_date = models.DateField(default=datetime.date.today)
    end_date = models.DateField(default=datetime.date.today)
    purpose = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS, default='1')
    app_date = models.DateField(default=datetime.date.today)
    leave_type = models.CharField(choices=LEAVE_TYPE, max_length=20, default="casual")

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
    status = models.CharField(max_length=20, choices=STATUS, default='1')
    item1 = models.CharField(max_length=50)
    item2 = models.CharField(max_length=50)
    app_date = models.DateField(default=datetime.date.today)

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
    reason = models.TextField()
    request = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS, default='1')
    app_date = models.DateField(default=datetime.date.today)

    def __str__(self):
        return '{} - {} - {} - {}'.format(self.id, self.dish, self.request, self.status)



class Feedback(models.Model):
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    fdate = models.DateField(default=datetime.date.today)
    description = models.TextField()
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPE)

    def __str__(self):
        return str(self.student_id.id)
