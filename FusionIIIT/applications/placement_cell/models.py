# imports
import datetime

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext as _

# Class definations:


class Constants:
    RESUME_TYPE = (
        ('ONGOING', 'Ongoing'),
        ('COMPLETED', 'Completed'),
    )
    ACHIEVEMENT_TYPE = (
        ('EDUCATIONAL', 'Educational'),
        ('OTHER', 'Other'),
    )
    INVITATION_TYPE = (
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('PENDING', 'Pending'),
    )
    PLACEMENT_TYPE = (
        ('PLACEMENT', 'Placement'),
        ('PBI', 'PBI'),
        ('HIGHER STUDIES', 'Higher Studies'),
        ('OTHER', 'Other'),
    )
    PLACED_TYPE = (
        ('ON CAMPUS', 'On Campus'),
        ('PPO', 'PPO'),
        ('OFF CAMPUS', 'Off Campus'),
    )
    DEBAR_TYPE = (
        ('DEBAR', 'Debar'),
        ('NOT DEBAR', 'Not Debar'),
    )


class Project(models.Model):
    unique_id = models.ForeignKey(User, on_delete=models.CASCADE)
    project_name = models.CharField(max_length=40, default='')
    project_status = models.CharField(max_length=20, choices=Constants.RESUME_TYPE,
                                      default='COMPLETED')
    summary = models.CharField(max_length=500, default='')
    project_link = models.CharField(max_length=200, default='')
    sdate = models.DateField(_("Date"), default=datetime.date.today)
    edate = models.DateField(null=True, blank=True)


class Language(models.Model):
    language = models.CharField(max_length=20, default='')


class Know(models.Model):
    language_id = models.ForeignKey(Language, on_delete=models.CASCADE)
    unique_id = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('language_id', 'unique_id'),)


class Skill(models.Model):
    skill = models.CharField(max_length=30, default='')


class Has(models.Model):
    skill_id = models.ForeignKey(Skill, on_delete=models.CASCADE)
    unique_id = models.ForeignKey(User, on_delete=models.CASCADE)
    skill_rating = models.IntegerField(default='80')

    class Meta:
        unique_together = (('skill_id', 'unique_id'),)


class Education(models.Model):
    unique_id = models.ForeignKey(User, on_delete=models.CASCADE)
    degree = models.CharField(max_length=40, default='')
    grade = models.CharField(max_length=10, default='')
    institute = models.CharField(max_length=250, default='')
    stream = models.CharField(max_length=150, default='')
    sdate = models.DateField(_("Date"), default=datetime.date.today)
    edate = models.DateField(_("Date"), default=datetime.date.today)


class Experience(models.Model):
    unique_id = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100, default='')
    status = models.CharField(max_length=20, choices=Constants.RESUME_TYPE,
                              default='COMPLETED')
    description = models.CharField(max_length=500, default='')
    company = models.CharField(max_length=200, default='')
    location = models.CharField(max_length=200, default='')
    sdate = models.DateField(_("Date"), default=datetime.date.today)
    edate = models.DateField(null=True, blank=True)


class Course(models.Model):
    unique_id = models.ForeignKey(User, on_delete=models.CASCADE)
    course_name = models.CharField(max_length=100, default='')
    description = models.CharField(max_length=250, default='')
    license_no = models.IntegerField(default='')
    sdate = models.DateField(_("Date"), default=datetime.date.today)
    edate = models.DateField(null=True, blank=True)


class Publication(models.Model):
    unique_id = models.ForeignKey(User, on_delete=models.CASCADE)
    publication_title = models.CharField(max_length=100, default='')
    description = models.CharField(max_length=250, default='')
    publisher = models.CharField(max_length=250, default='')
    publication_date = models.DateField(_("Date"), default=datetime.date.today)


class Coauthor(models.Model):
    publication_id = models.ForeignKey(Publication, on_delete=models.CASCADE)
    coauthor_name = models.CharField(max_length=100, default='')


class Patent(models.Model):
    unique_id = models.ForeignKey(User, on_delete=models.CASCADE)
    patent_name = models.CharField(max_length=100, default='')
    description = models.CharField(max_length=250, default='')
    patent_office = models.CharField(max_length=250, default='')
    patent_date = models.DateField()


class Coinventor(models.Model):
    patent_id = models.ForeignKey(Patent, on_delete=models.CASCADE)
    coinventor_name = models.CharField(max_length=100, default='')


class Interest(models.Model):
    unique_id = models.ForeignKey(User, on_delete=models.CASCADE)
    interest = models.CharField(max_length=100, default='')


class Achievement(models.Model):
    unique_id = models.ForeignKey(User, on_delete=models.CASCADE)
    achievement = models.CharField(max_length=100, default='')
    achievement_type = models.CharField(max_length=20, choices=Constants.ACHIEVEMENT_TYPE,
                                        default='OTHER')
    description = models.CharField(max_length=250, default='')
    issuer = models.CharField(max_length=200, default='')
    date_earned = models.DateField(_("Date"), default=datetime.date.today)


class MessageOfficer(models.Model):
    message = models.CharField(max_length=100, default='')
    timestamp = models.DateTimeField(auto_now=True)


class NotifyStudent(models.Model):
    placement_type = models.CharField(max_length=20, choices=Constants.PLACEMENT_TYPE,
                                      default='PLACEMENT')
    company_name = models.CharField(max_length=100, default='')
    ctc = models.DecimalField(default='0.0', decimal_places='2', max_digits='5')
    description = models.CharField(max_length=1000, default='')


class PlacementStatus(models.Model):
    notify_id = models.ForeignKey(NotifyStudent, on_delete=models.CASCADE)
    unique_id = models.ForeignKey(User, on_delete=models.CASCADE)
    invitation = models.CharField(max_length=20, choices=Constants.INVITATION_TYPE,
                                  default='PENDING')
    placed = models.CharField(max_length=20, choices=Constants.INVITATION_TYPE,
                              default='PENDING')
    timestamp = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (('notify_id', 'unique_id'),)


class PlacementRecord(models.Model):
    placement_type = models.CharField(max_length=20, choices=Constants.PLACEMENT_TYPE,
                                      default='PLACEMENT')
    name = models.CharField(max_length=100, default='')
    ctc = models.DecimalField(default='0.0', decimal_places='2', max_digits='5')
    year = models.IntegerField(default='0')
    test_score = models.IntegerField(default='0')
    test_type = models.CharField(max_length=30, default='')


class StudentRecord(models.Model):
    record_id = models.ForeignKey(PlacementRecord, on_delete=models.CASCADE)
    unique_id = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('record_id', 'unique_id'),)


class ChairmanVisit(models.Model):
    company_name = models.CharField(max_length=100, default='')
    location = models.CharField(max_length=100, default='')
    visiting_date = models.DateField(_("Date"), default=datetime.date.today)
    description = models.CharField(max_length=1000, default='')
    timestamp = models.DateTimeField(auto_now=True)


class ContactCompany(models.Model):
    company_name = models.CharField(max_length=100, default='')
    hr_mail = models.CharField(max_length=100, default='')
    reference = models.CharField(max_length=1000, default='')
    description = models.CharField(max_length=500, default='')
    timestamp = models.DateTimeField(auto_now=True)


class PlacementSchedule(models.Model):
    notify_id = models.ForeignKey(NotifyStudent, on_delete=models.CASCADE)
    title = models.CharField(max_length=100, default='')
    placement_date = models.DateField(_("Date"), default=datetime.date.today)
    location = models.CharField(max_length=100, default='')
    description = models.CharField(max_length=500, default='')
    time = models.TimeField()


class StudentPlacement(models.Model):
    unique_id = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE)
    debar = models.CharField(max_length=20, choices=Constants.DEBAR_TYPE, default='NOT DEBAR')
    future_aspect = models.CharField(max_length=20, choices=Constants.PLACEMENT_TYPE,
                                     default='PLACEMENT')
    placed_type = models.CharField(max_length=20, choices=Constants.PLACED_TYPE,
                                   default='PLACEMENT')
    placement_date = models.DateField(_("Date"), default=datetime.date.today)
    package = models.DecimalField(default='0.0', decimal_places='2', max_digits='5')
