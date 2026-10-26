"""Monthly assistantship sheet kept by a discipline's office staff.

One row per student per month, seeded from the student's admission record and
then edited by the staff. A month that is left pending is carried into the
next one, so the amount actually paid is this month's plus whatever is owed.
"""
from decimal import Decimal

from django.db import models

# Every discipline pays the same by default; the staff can override any row.
DEFAULT_AMOUNT = Decimal('37000.00')

STATUS_CHOICES = (
    ('pending', 'Pending'),
    ('cleared', 'Cleared'),
)

# Role name -> (short code used in the signature line, discipline names as the
# student records spell them). Names stay within 20 characters because that is
# what ExtraInfo.last_selected_role holds.
STAFF_DISCIPLINES = {
    'CSE Staff': ('CSE', ('Computer Science and Engineering',)),
    'ECE Staff': ('ECE', ('Electronics and Communication Engineering',)),
    'ME Staff': ('ME', ('Mechanical Engineering',)),
    'Design Staff': ('Design', ('Design',)),
    'Mechatronics Staff': ('Mechatronics', ('Mechatronics',)),
    'SM Staff': ('SM', ('Smart Manufacturing',)),
    'NS Staff': ('NS', ('Natural Sciences', 'Natural Science')),
    'Liberal Arts Staff': ('LA', ('Liberal Arts',)),
}


def staff_scope(role_names):
    """(code, discipline names) for the first department-staff role held."""
    for role in role_names:
        if role in STAFF_DISCIPLINES:
            return STAFF_DISCIPLINES[role]
    return None, ()


class AssistantshipRecord(models.Model):
    roll_number = models.CharField(max_length=20, db_index=True)
    discipline = models.CharField(max_length=100)
    year = models.PositiveIntegerField()
    month = models.PositiveSmallIntegerField()
    days = models.PositiveSmallIntegerField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2,
                                 null=True, blank=True)
    remark = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES,
                              default='pending')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('roll_number', 'year', 'month')
        ordering = ('-year', '-month', 'roll_number')

    def __str__(self):
        return '{} {}/{}'.format(self.roll_number, self.month, self.year)


class AssistantshipSignatory(models.Model):
    """Who the sheet is recommended by, remembered per discipline."""

    discipline = models.CharField(max_length=100, unique=True)
    recommended_by = models.CharField(max_length=150)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{}: {}'.format(self.discipline, self.recommended_by)


class AssistantshipExclusion(models.Model):
    """A student the office has taken off their discipline's sheet.

    The student record is untouched; only the assistantship listing skips
    them, so putting someone back is deleting one row.
    """

    roll_number = models.CharField(max_length=20, unique=True)
    discipline = models.CharField(max_length=100)
    removed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '{} off {}'.format(self.roll_number, self.discipline)
