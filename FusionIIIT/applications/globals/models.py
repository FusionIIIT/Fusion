import datetime

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Constants:
    # Class for various choices on the enumerations
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

    TITLE_CHOICES = (
        ("Mr.", "Mr."),
        ("Mrs.", "Mrs."),
        ("Ms.", "Ms."),
        ("Dr.", "Dr."),
        ("Professor", "Prof."),
        ("Shreemati", "Shreemati"),
        ("Shree", "Shree")
    )

    DESIGNATIONS = (
        ('academic', 'Academic Designation'),
        ('administrative', 'Administrative Designation')
    )


class Designation(models.Model):
    name = models.CharField(max_length=50, unique=True, blank=False, default='student')
    full_name = models.CharField(max_length=100, default='Computer Science and Engineering')

    type = models.CharField(max_length=30, default='academic', choices=Constants.DESIGNATIONS)

    def __str__(self):
        return self.name


class DepartmentInfo(models.Model):
    name = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return 'department: {}'.format(self.name)


class ExtraInfo(models.Model):
    id = models.CharField(max_length=20, primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=20, choices=Constants.TITLE_CHOICES, default='Dr.')
    sex = models.CharField(max_length=2, choices=Constants.SEX_CHOICES, default='M')
    date_of_birth = models.DateField(default=datetime.date(1970, 1, 1))
    address = models.TextField(max_length=1000, default="")
    phone_no = models.BigIntegerField(null=True, default=9999999999)
    user_type = models.CharField(max_length=20, choices=Constants.USER_CHOICES)
    department = models.ForeignKey(DepartmentInfo, on_delete=models.CASCADE, null=True, blank=True)
    profile_picture = models.ImageField(null=True, blank=True, upload_to='globals/profile_pictures')
    about_me = models.TextField(default='NA', max_length=1000, blank=True)

    @property
    def age(self):
        timedelta = timezone.now().date() - self.date_of_birth
        return int(timedelta.days / 365)

    @property
    def age(self):
        timedelta = timezone.localtime(timezone.now()).date() - self.date_of_birth
        return int(timedelta.days / 365)

    def __str__(self):
        return '{} - {}'.format(self.id, self.user.username)


class HoldsDesignation(models.Model):
    user = models.ForeignKey(User, related_name='holds_designations', on_delete=models.CASCADE)
    working = models.ForeignKey(User, related_name='current_designation', on_delete=models.CASCADE)
    designation = models.ForeignKey(Designation, related_name='designees', on_delete=models.CASCADE)
    held_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{} - {}'.format(self.user.username, self.designation)


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
