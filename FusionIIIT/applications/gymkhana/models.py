# import
from datetime import datetime, timedelta

from django import template
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from applications.academic_information.models import Student
from applications.globals.models import ExtraInfo, Faculty

register = template.Library()
# Class definations:


# # Class for various choices on the enumerations
class Constants:
	categoryCh = (
		('Technical','Technical'),
		('Sports','Sports'),
		('Cultural','Cultural')
		)
	status = (
		('open','Open'),
		('confirmed','Confirmed'),
		('rejected','Rejected')
		)
	fest = (
		('Abhikalpan','Abhikalpan'),
		('Gusto','Gusto'),
		('Tarang','Tarang')
		)

class Club_info(models.Model):
	club_name = models.CharField(max_length=50,null=False,primary_key=True)
	category = models.CharField(max_length=50, null=False, choices = Constants.categoryCh)
	co_ordinator = models.ForeignKey(Student, null=False, related_name='co_of')
	co_coordinator = models.ForeignKey(Student, null=False, related_name='coco_of')
	faculty_incharge = models.ForeignKey(Faculty, null=False, related_name='faculty_incharge_of')	
	club_file = models.FileField(upload_to='uploads/',null=True)
	activity_calender = models.FileField(upload_to='uploads/',null=True, default= " ")
	description = models.TextField(max_length=256, null=True)
	alloted_budget=models.IntegerField(null=True, default = 0)
	spent_budget = models.IntegerField(null=True, default = 0)
	avail_budget=models.IntegerField(null=True, default = 0)
	status = models.CharField(max_length=50, choices = Constants.status, default = 'open')

	def __str__(self):
		return str(self.club_name)

	class Meta:
		db_table = 'Club_info'

class Club_member(models.Model):
	id = models.AutoField(max_length=20, primary_key=True)
	member = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='member_of')
	club = models.ForeignKey(Club_info, related_name='this_club', null=False)
	description = models.TextField(max_length=256, null=True)
	status = models.CharField(max_length=50, choices = Constants.status, default = 'open')
	remarks = models.CharField(max_length=256, null=True)
	
	def __str__(self):
		return str(self.member.id)

	class Meta:
		db_table = 'Club_member'

class Core_team(models.Model):
	id = models.AutoField(max_length=20,primary_key=True)
	student_id = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='applied_for')
	team = models.CharField(max_length=50, null=False)
	year = models.DateTimeField(max_length=6, null=True)
	fest_name = models.CharField(max_length=256, null=False,choices=Constants.fest)
	pda = models.TextField(max_length=256, null=False)
	remarks = models.CharField(max_length=256, null=True)

	def __str__(self):
		return str(self.student_id)

	class Meta:
		db_table = 'Core_team'

class Club_budget(models.Model):
	id = models.AutoField(max_length=20,primary_key=True)
	club = models.ForeignKey(Club_info,max_length=50,null=False)
	budget_for = models.CharField(max_length=256, null=False)
	budget_amt = models.IntegerField(default = 0, null=False)
	budget_file = models.FileField(upload_to='uploads/',null=False)
	description = models.TextField(max_length=256, null=False)
	status = models.CharField(max_length=50, choices=Constants.status, default='open')
	remarks = models.CharField(max_length=256, null=True)

	def __str__(self):
		return str(self.id)

	class Meta:
		db_table = 'Club_budget'

class Session_info(models.Model):
	id = models.AutoField(max_length=20,primary_key=True)
	club = models.ForeignKey(Club_info, max_length=50,null=True)
	venue = models.CharField(max_length=50,null=False)
	date = models.DateTimeField(default=datetime.now()+ timedelta(days=1),max_length=50, blank = True)
	details = models.TextField(max_length=256, null=True)

	def __str__(self):
		return str(self.id)

	class Meta:
		db_table = 'Session_info'

class Club_report(models.Model):
	id = models.AutoField(max_length=20,primary_key=True)
	club = models.ForeignKey(Club_info,max_length=50,null=False)
	incharge = models.ForeignKey(ExtraInfo,max_length=256,null=False)
	event_name = models.CharField(max_length=50,null=False)
	date = models.DateTimeField(max_length=50,default=datetime.now()+ timedelta(days=1), blank = True)
	event_details = models.FileField(upload_to='uploads/',null=False)
	description = models.TextField(max_length=256, null=True)

	def __str__(self):
		return str(self.id)

	class Meta:
		db_table = 'Club_report'

class Fest_budget(models.Model):
	id = models.AutoField(max_length=20,primary_key=True)
	fest = models.CharField(max_length=50,null=False, choices=Constants.fest)
	budget_amt = models.IntegerField(default = 0, null=False)
	budget_file = models.FileField(upload_to='uploads/',null=False)
	year = models.CharField(max_length=10,null=True)
	description = models.TextField(max_length=256, null=False)
	status = models.CharField(max_length=50, choices=Constants.status, default='open')
	remarks = models.CharField(max_length=256, null=True)

	def __str__(self):
		return str(self.id)

	class Meta:
		db_table = 'Fest_budget'

class Other_report(models.Model):
	id = models.AutoField(max_length=20,primary_key=True)
	incharge = models.ForeignKey(ExtraInfo,max_length=256,null=False)
	event_name = models.CharField(max_length=50,null=False)
	date = models.DateTimeField(max_length=50,default=datetime.now()+ timedelta(days=1), blank = True)
	event_details = models.FileField(upload_to='uploads/',null=False)
	description = models.TextField(max_length=256, null=True)
	
	def __str__(self):
		return str(self.id)

	class Meta:
		db_table = 'Other_report'

class Change_office(models.Model):
	id = models.AutoField(max_length=20,primary_key=True)
	club = models.ForeignKey(Club_info, max_length=50,null=False)
	co_ordinator = models.ForeignKey(User, null=False, related_name='co_of')
	co_coordinator = models.ForeignKey(User, null=False, related_name='coco_of')
	status = models.CharField(max_length=50, choices=Constants.status, default='open')
	date_request = models.DateTimeField(max_length=50,default=datetime.now()+ timedelta(days=1), blank = True)
	date_approve = models.DateTimeField(max_length=50, blank = True)
	remarks = models.CharField(max_length=256, null=True)

	def __str__(self):
		return self.id

	class Meta:
		db_table = 'Change_office'
