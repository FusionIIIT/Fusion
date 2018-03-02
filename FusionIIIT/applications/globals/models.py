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
        ('compounder', 'compounder'),
        ('faculty', 'faculty')
    )

    RATING_CHOICES = (
            (1, 1),
            (2, 2),
            (3, 3),
            (4, 4),
            (5, 5),
        )

    MODULES = (
            ("academic_information", "Academic"),
            ("central_mess", "Central Mess"),
            ("complaint_system", "Complaint System"),
            ("eis", "Employee Imformation System"),
            ("file_tracking", "File Tracking System"),
            ("health_center", "Health Center"),
            ("leave", "Leave"),
            ("online_cms", "Online Course Management System"),
            ("placement_cell", "Placement Cell"),
            ("scholarships", "Scholarships"),
            ("visitor_hostel", "Visitor Hostel"),
            ("other", "Other"),
        )

    ISSUE_TYPES = (
            ("feature_request", "Feature Request"),
            ("bug_report", "Bug Report"),
            ("security_issue", "Security Issue"),
            ("ui_issue", "User Interface Issue"),
            ("other", "Other than the ones listed"),
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
    phone_no = models.BigIntegerField()
    user_type = models.CharField(max_length=20, choices=Constants.USER_CHOICES)
    designation = models.ForeignKey(Designation, on_delete=models.CASCADE,
                                    related_name='holds_designation', null=True)
    department = models.ForeignKey(DepartmentInfo, on_delete=models.CASCADE, null=True, blank=True)
    profile_picture = models.ImageField(null=True, blank=True)
    about_me = models.TextField(default='', max_length=1000, blank=True)

    def __str__(self):
        return '{} - {}'.format(self.id, self.user.username)


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


""" Feedback and bug report models start"""


class Feedback(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="fusion_feedback")
    rating = models.IntegerField(choices=Constants.RATING_CHOICES)
    feedback = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username + ": " + str(self.rating)


def Issue_image_directory(instance, filename):
    return 'issues/{0}/images/{1}'.format(instance.user.username, filename)


class IssueImage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=Issue_image_directory)


class Issue(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reported_issues")
    report_type = models.CharField(max_length=63, choices=Constants.ISSUE_TYPES)
    module = models.CharField(max_length=63, choices=Constants.MODULES)
    closed = models.BooleanField(default=False)
    text = models.TextField()
    title = models.CharField(max_length=255)
    images = models.ManyToManyField(IssueImage, blank=True)
    support = models.ManyToManyField(User, blank=True)
    timestamp = models.DateTimeField(auto_now=True)
    added_on = models.DateTimeField(auto_now_add=True)


""" End of feedback and bug report models"""
