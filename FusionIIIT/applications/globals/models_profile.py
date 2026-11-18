"""Student profile records shown on the dashboard profile page.

Education, experience, skills, projects, courses, achievements,
publications, patents and bank details. They were defined in
placement_cell; globals now owns them, because globals serves the
profile (/api/profile/, /api/profile_update/, /api/profile_delete/ and
/api/profile/bank-details/).

The tables still have the names placement_cell gave them; renaming them
is a separate change.
"""

import datetime

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext as _


def validate_start_before_end(*, start_date, end_date, start_field='sdate', end_field='edate'):
    if start_date and end_date and start_date >= end_date:
        raise ValidationError({
            start_field: _('Start date must be earlier than end date.'),
            end_field: _('End date must be later than start date.'),
        })


class ProfileConstants:
    RESUME_TYPE = (
        ('ONGOING', 'Ongoing'),
        ('COMPLETED', 'Completed'),
    )

    ACHIEVEMENT_TYPE = (
        ('EDUCATIONAL', 'Educational'),
        ('OTHER', 'Other'),
    )


class Project(models.Model):
    unique_id = models.ForeignKey('academic_information.Student', on_delete=models.CASCADE)
    project_name = models.CharField(max_length=50, default='')
    project_status = models.CharField(max_length=20, choices=ProfileConstants.RESUME_TYPE,
                                      default='COMPLETED')
    summary = models.TextField(max_length=1000, default='', null=True, blank=True)
    project_link = models.CharField(max_length=200, default='', null=True, blank=True)
    sdate = models.DateField(_("Date"), default=datetime.date.today)
    edate = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'placement_cell_project'

    def clean(self):
        super().clean()
        validate_start_before_end(start_date=self.sdate, end_date=self.edate)

    def __str__(self):
        return '{} - {}'.format(self.unique_id.id, self.project_name)


class Skill(models.Model):
    skill = models.CharField(max_length=30, default='')

    class Meta:
        db_table = 'placement_cell_skill'

    def __str__(self):
        return self.skill


class Has(models.Model):
    skill_id = models.ForeignKey(Skill, on_delete=models.CASCADE)
    unique_id = models.ForeignKey('academic_information.Student', on_delete=models.CASCADE)
    skill_rating = models.IntegerField(
        default=80,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    class Meta:
        db_table = 'placement_cell_has'
        unique_together = (('skill_id', 'unique_id'),)

    def __str__(self):
        return '{} - {}'.format(self.unique_id.id, self.skill_id.skill)


class Education(models.Model):
    unique_id = models.ForeignKey('academic_information.Student', on_delete=models.CASCADE)
    degree = models.CharField(max_length=40, default='')
    grade = models.CharField(max_length=10, default='')
    institute = models.TextField(max_length=250, default='')
    stream = models.CharField(max_length=150, default='', null=True, blank=True)
    sdate = models.DateField(_("Date"), default=datetime.date.today)
    edate = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'placement_cell_education'

    def clean(self):
        super().clean()
        validate_start_before_end(start_date=self.sdate, end_date=self.edate)


class Experience(models.Model):
    unique_id = models.ForeignKey('academic_information.Student', on_delete=models.CASCADE)
    title = models.CharField(max_length=100, default='')
    status = models.CharField(max_length=20, choices=ProfileConstants.RESUME_TYPE,
                              default='COMPLETED')
    description = models.TextField(max_length=500, default='', null=True, blank=True)
    company = models.CharField(max_length=200, default='')
    location = models.CharField(max_length=200, default='')
    sdate = models.DateField(_("Date"), default=datetime.date.today)
    edate = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'placement_cell_experience'

    def clean(self):
        super().clean()
        validate_start_before_end(start_date=self.sdate, end_date=self.edate)

    def __str__(self):
        return '{} - {}'.format(self.unique_id.id, self.company)


class Course(models.Model):
    unique_id = models.ForeignKey('academic_information.Student', on_delete=models.CASCADE)
    course_name = models.CharField(max_length=100, default='')
    description = models.TextField(max_length=250, default='', null=True, blank=True)
    license_no = models.CharField(max_length=100, default='', null=True, blank=True)
    sdate = models.DateField(_("Date"), default=datetime.date.today)
    edate = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'placement_cell_course'

    def clean(self):
        super().clean()
        validate_start_before_end(start_date=self.sdate, end_date=self.edate)

    def __str__(self):
        return '{} - {}'.format(self.unique_id.id, self.course_name)


class Publication(models.Model):
    unique_id = models.ForeignKey('academic_information.Student', on_delete=models.CASCADE)
    publication_title = models.CharField(max_length=100, default='')
    description = models.TextField(max_length=250, default='', null=True, blank=True)
    publisher = models.TextField(max_length=250, default='')
    publication_date = models.DateField(_("Date"), default=datetime.date.today)

    class Meta:
        db_table = 'placement_cell_publication'

    def __str__(self):
        return '{} - {}'.format(self.unique_id.id, self.publication_title)


class Patent(models.Model):
    unique_id = models.ForeignKey('academic_information.Student', on_delete=models.CASCADE)
    patent_name = models.CharField(max_length=100, default='')
    description = models.TextField(max_length=250, default='', null=True, blank=True)
    patent_office = models.TextField(max_length=250, default='')
    patent_date = models.DateField()

    class Meta:
        db_table = 'placement_cell_patent'

    def __str__(self):
        return '{} - {}'.format(self.unique_id.id, self.patent_name)


class Achievement(models.Model):
    unique_id = models.ForeignKey('academic_information.Student', on_delete=models.CASCADE)
    achievement = models.CharField(max_length=100, default='')
    achievement_type = models.CharField(max_length=20, choices=ProfileConstants.ACHIEVEMENT_TYPE,
                                        default='OTHER')
    description = models.TextField(max_length=1000, default='', null=True, blank=True)
    issuer = models.CharField(max_length=200, default='')
    date_earned = models.DateField(_("Date"), default=datetime.date.today)

    class Meta:
        db_table = 'placement_cell_achievement'

    def __str__(self):
        return '{} - {}'.format(self.unique_id.id, self.achievement)


class StudentBankDetails(models.Model):
    """A student's own bank account details, for stipend/scholarship/refund
    disbursement. One record per student -- kept as its own model (like
    academic_procedures.ExaminerBankDetails) rather than folded into a list
    of profile sub-records, since it's a single set of sensitive fields, not
    a many-entries-over-time thing like Education/Experience/etc."""
    unique_id = models.OneToOneField('academic_information.Student', on_delete=models.CASCADE, related_name='bank_details')
    account_holder_name = models.CharField(max_length=200, default='')
    bank_name = models.CharField(max_length=200, default='')
    branch_name = models.CharField(max_length=200, default='', blank=True)
    account_number = models.CharField(max_length=30, default='')
    ifsc_code = models.CharField(max_length=20, default='')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'placement_cell_studentbankdetails'

    def __str__(self):
        return f"Bank details for {self.unique_id.id}"
