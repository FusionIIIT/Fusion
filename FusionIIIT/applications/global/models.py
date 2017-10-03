# imports
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
        ('faculty', 'faculty')
    )


class Designation(models.Model):
    name = models.CharField(max_length=20, unique=True, blank=False, default='student')

    def __str__(self):
        return self.name


class DepartmentInfo(models.Model):
    name = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return 'department: {}'.format(self.name)


class ExtraInfo(models.Model):
    id = models.CharField(max_length=20, primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    sex = models.CharField(max_length=2, choices=Constants.SEX_CHOICES, default='M')
    age = models.IntegerField(default=18)
    address = models.TextField(max_length=1000, default="")
    phone_no = models.IntegerField(default=15)
    user_type = models.CharField(max_length=20, choices=Constants.USER_CHOICES)
    designation = models.ForeignKey(Designation, on_delete=models.CASCADE,
                                    related_name='holds_designation', null=True)
    department = models.ForeignKey(DepartmentInfo, on_delete=models.CASCADE, null=True)
    profile_picture = models.ImageField(null=True, blank=True)
    about_me = models.TextField(default='', max_length=1000, blank=True)

    def __str__(self):
        return '{} - {}'.format(self.user_type, self.user.username)


# TODO : Remove from here and use from academics app
class Student(models.Model):
    id = models.OneToOneField(ExtraInfo, on_delete=models.CASCADE, primary_key=True)
    cpi = models.IntegerField(default=0)
    father_name = models.CharField(max_length=40, default='')
    mother_name = models.CharField(max_length=40, default='')
    hall = models.IntegerField(default=1)
    room_no = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return str(self.id)


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
