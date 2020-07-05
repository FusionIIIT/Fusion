# import
import datetime
from django.utils import timezone
from django import template
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.urls import reverse

from applications.academic_information.models import Student
from applications.globals.models import ExtraInfo, Faculty

register = template.Library()


# Class definations:


# # Class for various choices on the enumerations
class Constants:
    available = (
        ('On', 'On'),
        ('Off', 'Off'),
    )
    categoryCh = (
        ('Technical', 'Technical'),
        ('Sports', 'Sports'),
        ('Cultural', 'Cultural')
    )
    status = (
        ('open', 'Open'),
        ('confirmed', 'Confirmed'),
        ('rejected', 'Rejected')
    )
    fest = (
        ('Abhikalpan', 'Abhikalpan'),
        ('Gusto', 'Gusto'),
        ('Tarang', 'Tarang')
    )
    venue = (
        ('Classroom', (
            ('CR101', 'CR101'),
            ('CR102', 'CR102'),
        )),
        ('Lecturehall', (
            ('L101', 'L101'),
            ('L102', 'L102'),
        )),

    )


class Club_info(models.Model):
    club_name = models.CharField(max_length=50, null=False, primary_key=True)
    club_website = models.CharField(max_length=150, null=True, default="hello")
    category = models.CharField(
        max_length=50, null=False, choices=Constants.categoryCh)
    co_ordinator = models.ForeignKey(Student, on_delete=models.CASCADE, null=False, related_name='co_of')
    co_coordinator = models.ForeignKey(
        Student, on_delete=models.CASCADE, null=False, related_name='coco_of')
    faculty_incharge = models.ForeignKey(
        Faculty, on_delete=models.CASCADE, null=False, related_name='faculty_incharge_of')
    club_file = models.FileField(upload_to='gymkhana/club_poster', null=True)
    activity_calender = models.FileField(
        upload_to='gymkhana/activity_calender', null=True, default=" ")
    description = models.TextField(max_length=256, null=True)
    alloted_budget = models.IntegerField(null=True, default=0)
    spent_budget = models.IntegerField(null=True, default=0)
    avail_budget = models.IntegerField(null=True, default=0)
    status = models.CharField(
        max_length=50, choices=Constants.status, default='open')

    def __str__(self):
        return str(self.club_name)

    class Meta:
        db_table = 'Club_info'


class Form_available(models.Model):
    roll = models.CharField(default=2016001, max_length=7, primary_key=True)
    status = models.BooleanField(default=True, max_length=5)
    form_name = models.CharField(default='senate_registration', max_length=30)

    def __str__(self):
        return str(self.roll)

    class Meta:
        db_table = 'Form_available'

class Registration_form(models.Model):
    roll = models.CharField(max_length=7, default="2016001", primary_key=True)
    user_name = models.CharField(max_length=40, default="Student")
    branch = models.CharField(max_length=20, default='open')
    cpi = models.FloatField(max_length=3, default=6.0)
    programme = models.CharField(max_length=20, default='B.tech')

    def __str__(self):
        return str(self.roll)

    class Meta:
        db_table = 'Registration_form'


class Club_member(models.Model):
    id = models.AutoField(primary_key=True)
    member = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name='member_of')
    club = models.ForeignKey(Club_info, on_delete=models.CASCADE, related_name='this_club', null=False)
    description = models.TextField(max_length=256, null=True)
    status = models.CharField(
        max_length=50, choices=Constants.status, default='open')
    remarks = models.CharField(max_length=256, null=True)

    def __str__(self):
        return str(self.member.id)

    class Meta:
        db_table = 'Club_member'




class Core_team(models.Model):
    id = models.AutoField(primary_key=True)
    student_id = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name='applied_for')
    team = models.CharField(max_length=50, null=False)
    year = models.DateTimeField(max_length=6, null=True)
    fest_name = models.CharField(
        max_length=256, null=False, choices=Constants.fest)
    pda = models.TextField(max_length=256, null=False)
    remarks = models.CharField(max_length=256, null=True)

    def __str__(self):
        return str(self.student_id)

    class Meta:
        db_table = 'Core_team'


class Club_budget(models.Model):
    id = models.AutoField(primary_key=True)
    club = models.ForeignKey(Club_info,on_delete=models.CASCADE, max_length=50, null=False)
    budget_for = models.CharField(max_length=256, null=False)
    budget_amt = models.IntegerField(default=0, null=False)
    budget_file = models.FileField(upload_to='uploads/', null=False)
    description = models.TextField(max_length=256, null=False)
    status = models.CharField(
        max_length=50, choices=Constants.status, default='open')
    remarks = models.CharField(max_length=256, null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'Club_budget'


class Session_info(models.Model):
    id = models.AutoField(primary_key=True)
    club = models.ForeignKey(Club_info, on_delete=models.CASCADE,max_length=50, null=True)
    venue = models.CharField(max_length=50, null=False,
                             choices=Constants.venue)
    date = models.DateField(default=None, auto_now=False, null=False)
    start_time = models.TimeField(default=None, auto_now=False, null=False)
    end_time = models.TimeField(default=None, auto_now=False, null=True)
    session_poster = models.ImageField(upload_to='gymkhana/session_poster', null=True)
    details = models.TextField(max_length=256, null=True)
    status = models.CharField(
        max_length=50, choices=Constants.status, default='open')

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'Session_info'

class Event_info(models.Model):
    id = models.AutoField(primary_key=True)
    club = models.ForeignKey(Club_info, on_delete=models.CASCADE,max_length=50, null=True)
    event_name= models.CharField(max_length=256, null=False)
    venue = models.CharField(max_length=50, null=False,
                             choices=Constants.venue)
    incharge=models.CharField(max_length=256, null=False)
    date = models.DateField(default=None, auto_now=False, null=False)
    start_time = models.TimeField(default=None, auto_now=False, null=False)
    end_time = models.TimeField(default=None, auto_now=False, null=True)
    event_poster = models.FileField(upload_to='gymkhana/event_poster', blank=True)
    details = models.TextField(max_length=256, null=True)
    status = models.CharField(
        max_length=50, choices=Constants.status, default='open')

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'Event_info'            


class Club_report(models.Model):
    id = models.AutoField(primary_key=True)
    club = models.ForeignKey(Club_info, on_delete=models.CASCADE,max_length=50, null=False)
    incharge = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE,max_length=256, null=False)
    event_name = models.CharField(max_length=50, null=False)
    date = models.DateTimeField(
        max_length=50, default=timezone.now, blank=True)
    event_details = models.FileField(upload_to='uploads/', null=False)
    description = models.TextField(max_length=256, null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'Club_report'


class Fest_budget(models.Model):
    id = models.AutoField(primary_key=True)
    fest = models.CharField(max_length=50, null=False, choices=Constants.fest)
    budget_amt = models.IntegerField(default=0, null=False)
    budget_file = models.FileField(upload_to='uploads/', null=False)
    year = models.CharField(max_length=10, null=True)
    description = models.TextField(max_length=256, null=False)
    status = models.CharField(
        max_length=50, choices=Constants.status, default='open')
    remarks = models.CharField(max_length=256, null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'Fest_budget'


class Other_report(models.Model):
    id = models.AutoField(primary_key=True)
    incharge = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE,max_length=256, null=False)
    event_name = models.CharField(max_length=50, null=False)
    date = models.DateTimeField(
        max_length=50, default=timezone.now, blank=True)
    event_details = models.FileField(upload_to='uploads/', null=False)
    description = models.TextField(max_length=256, null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'Other_report'


class Change_office(models.Model):
    id = models.AutoField(primary_key=True)
    club = models.ForeignKey(Club_info, on_delete=models.CASCADE,max_length=50, null=False)
    co_ordinator = models.ForeignKey(User, on_delete=models.CASCADE,null=False, related_name='co_of')
    co_coordinator = models.ForeignKey(
        User, on_delete=models.CASCADE, null=False, related_name='coco_of')
    status = models.CharField(
        max_length=50, choices=Constants.status, default='open')
    date_request = models.DateTimeField(
        max_length=50, default=timezone.now, blank=True)
    date_approve = models.DateTimeField(max_length=50, blank=True)
    remarks = models.CharField(max_length=256, null=True)

    def __str__(self):
        return self.id

    class Meta:
        db_table = 'Change_office'


class Voting_polls(models.Model):
    
    title = models.CharField(max_length=200,null=False)
    description = models.CharField(max_length=5000,null=False)
    pub_date = models.DateTimeField(default=timezone.now)
    exp_date = models.DateTimeField(default=timezone.now)
    created_by = models.CharField(max_length=100,null=True)
    groups = models.CharField(max_length=500,default='{}')
    
    def groups_data(self):
        return self.groups

    def __str__(self):
        return self.title
    class Meta:
        ordering = ['-pub_date']

class Voting_choices(models.Model):

    poll_event = models.ForeignKey(Voting_polls, on_delete=models.CASCADE)
    title = models.CharField(max_length=200,null=False)
    description = models.CharField(max_length=500,default='')
    votes = models.IntegerField(default=0)

    def __str__(self):
        return self.title
    
    class Meta:
        get_latest_by = 'votes'

class Voting_voters(models.Model):
   
    poll_event = models.ForeignKey(Voting_polls, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=50, null=False)
    
    
    def __str__(self):
        return self.student_id

