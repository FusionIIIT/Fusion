# imports
import datetime

from django.contrib.auth.models import User
from django.db import models

# Class definations:


# # Class for various choices on the enumerations
class Constants:
    SEX_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other')
    )

    USER_CHOICES = (
        ('student', 'student'),
        ('staff', 'staff'),
        ('compounder', 'compounder'),
        ('faculty', 'faculty')
    )


class Designation(models.Model):
    name = models.CharField(max_length=30, unique=True, blank=False, default='student')

    def __str__(self):
        return self.name


class DepartmentInfo(models.Model):
    name = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return 'Discipline: {}'.format(self.name)


# TODO: Remove unnecessary null=True.
class ExtraInfo(models.Model):
    id = models.CharField(max_length=20, primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    sex = models.CharField(max_length=2, choices=Constants.SEX_CHOICES, default='M')
    date_of_birth = models.DateField(null=True)
    address = models.TextField(max_length=1000, default="")
    phone_no = models.BigIntegerField()
    user_type = models.CharField(max_length=20, choices=Constants.USER_CHOICES,
                                 default='student')
    department = models.ForeignKey(DepartmentInfo, on_delete=models.CASCADE,
                                   null=True, blank=True)
    profile_picture = models.ImageField(null=True, blank=True)
    about_me = models.TextField(default='', max_length=1000, blank=True, null=True)
    leave_sanc_auth = models.ForeignKey(Designation, on_delete=models.CASCADE,
                                        related_name='sanc_auth_of', null=True)
    leave_sanc_off = models.ForeignKey(Designation, on_delete=models.CASCADE,
                                       related_name='sanc_off_of', null=True)

    @property
    def age(self):
        timedelta = datetime.date.today() - self.date_of_birth
        return int(timedelta.days / 365)

    def __str__(self):
        return '{} - {}'.format(self.id, self.user.username)


class HoldsDesignation(models.Model):
    user = models.ForeignKey(User, related_name='holds_designation',
                             on_delete=models.CASCADE)
    working = models.ForeignKey(User, related_name='current_designations')
    designation = models.ForeignKey(Designation, related_name='designees',
                                    on_delete=models.CASCADE)
    held_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{} is {}'.format(self.user.username, self.designation)


# TODO : ADD additional staff related fields when needed
class Staff(models.Model):
    id = models.OneToOneField(ExtraInfo, on_delete=models.CASCADE, primary_key=True)

    def __str__(self):
        return str(self.id)


# TODO : ADD additional employee related fields when needed
class Faculty(models.Model):
    id = models.OneToOneField(ExtraInfo, on_delete=models.CASCADE, primary_key=True)

    def __str__(self):
        return str(self.id)
