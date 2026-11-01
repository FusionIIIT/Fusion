from django.conf import settings
from django.db import models

from .storage import private_storage, upload_key

STATES = [('draft', 'Draft'), ('scheduled', 'Scheduled'), ('published', 'Published')]
TYPES = [('file', 'File'), ('text', 'Text'), ('link', 'Link')]


class Workspace(models.Model):
    course_id = models.PositiveIntegerField()
    year = models.PositiveIntegerField()
    semester_type = models.CharField(max_length=20)
    syllabus = models.TextField(blank=True)
    schedule = models.TextField(blank=True)

    class Meta:
        unique_together = ('course_id', 'year', 'semester_type')


class CourseRole(models.Model):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='roles')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=[('ta', 'TA'), ('observer', 'Observer')])
    may_announce = models.BooleanField(default=False)

    class Meta:
        unique_together = ('workspace', 'user', 'role')


class Material(models.Model):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=200)
    section = models.CharField(max_length=120, blank=True)
    kind = models.CharField(max_length=10, choices=TYPES)
    text = models.TextField(blank=True)
    link = models.URLField(blank=True)
    file = models.FileField(storage=private_storage, upload_to=upload_key, blank=True)
    release_at = models.DateTimeField(null=True, blank=True)
    state = models.CharField(max_length=12, choices=STATES, default='draft')


class Announcement(models.Model):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='announcements')
    title = models.CharField(max_length=200)
    body = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)


class Assignment(models.Model):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=200)
    instructions = models.TextField()
    submission_type = models.CharField(max_length=10, choices=TYPES)
    points_possible = models.DecimalField(max_digits=8, decimal_places=2)
    due_at = models.DateTimeField()
    release_at = models.DateTimeField(null=True, blank=True)
    file = models.FileField(storage=private_storage, upload_to=upload_key, blank=True)
    state = models.CharField(max_length=12, choices=STATES, default='draft')


class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    text = models.TextField(blank=True)
    link = models.URLField(blank=True)
    file = models.FileField(storage=private_storage, upload_to=upload_key, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    points = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    grader = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT, related_name='lms_grades')
    graded_at = models.DateTimeField(null=True)
    released = models.BooleanField(default=False)
    revision = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('assignment', 'student')


class GradeAudit(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.PROTECT, related_name='audit')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    at = models.DateTimeField(auto_now_add=True)
    old_values = models.JSONField(default=dict)
    new_values = models.JSONField(default=dict)
