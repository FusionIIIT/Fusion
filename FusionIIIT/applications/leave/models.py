from django.contrib.auth.models import User
from django.db import models

from applications.globals.models import Designation, HoldsDesignation


class Constants:

    REPLACEMENT_TYPES = (
        ('academic', 'Academic Replacement'),
        ('administrative', 'Administrative Replacement')
    )

    LEAVE_PERMISSIONS = (
        ('sanc_auth', 'sanc_auth'),
        ('sanc_off', 'sanc_off'),
    )

    STATUS = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected')
    )

    MIGRATION_CHOICES = (
        ('revert', 'Revert Responsibilities'),
        ('transfer', 'Transfer Responsibilities')
    )


class LeaveType(models.Model):
    name = models.CharField(max_length=40, null=False)
    max_in_year = models.IntegerField(default=2)
    requires_proof = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.name}, Max: {self.max_in_year}'


class LeavesCount(models.Model):
    user = models.ForeignKey(User, related_name='leave_balance', on_delete=models.CASCADE)
    year = models.IntegerField(default=2015)
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    remaining_leaves = models.IntegerField(default=2)

    def save(self, *args, **kwargs):
        if self.year < 2015 or self.remaining_leaves < 2:
            raise ValueError('Year must be greater than 2015 and remaining leaves more than 0')
        super(LeavesCount, self).save(*args, **kwargs)

    def __str__(self):
        return '{} in {} has {} {}s'.format(self.user.username,
                                            self.year, self.remaining_leaves,
                                            self.leave_type)


# TODO: Add more fields, as required
class Leave(models.Model):
    applicant = models.ForeignKey(User, related_name='all_leaves',
                                  on_delete=models.CASCADE)
    purpose = models.CharField(max_length=500, default='', blank=True)
    status = models.CharField(max_length=20, default='pending', choices=Constants.STATUS)
    is_station = models.BooleanField(default=False)

    @property
    def is_station(self):
        return self.is_station

    def relacements_accepted(self):
        return not self.replace_segments.filter(status=False).exists()

    def generate_reqeusts(self):
        pass

    def __str__(self):
        return '{} applied for {} to {}, status: {}'.format(self.applicant.username,
                                                            self.start_date, self.end_date,
                                                            self.status)


# TODO: Add more fields
class ReplacementSegment(models.Model):
    leave = models.ForeignKey(Leave, related_name='replace_segments', on_delete=models.CASCADE)
    replacer = models.ForeignKey(User, on_delete=models.CASCADE)
    replacement_type = models.CharField(max_length=20, default='academic',
                                        choices=Constants.REPLACEMENT_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, default='pending', choices=Constants.STATUS)
    remark = models.CharField(max_length=50, default='', blank=True, null=True)


class LeaveSegment(models.Model):
    leave = models.ForeignKey(Leave, related_name='leave_segments', on_delete=models.CASCADE)
    leave_type = models.ForeignKey(LeaveType, on_delete=models.SET_NULL, null=True)
    start_date = models.DateField()
    start_half = models.BooleanField(default=False)
    end_date = models.DateField()
    end_half = models.BooleanField(default=False)


class LeaveRequest(models.Model):
    leave = models.ForeignKey(Leave, on_delete=models.CASCADE)
    requested_from = models.ForeignKey(User, on_delete=models.CASCADE)
    remark = models.CharField(max_length=50, blank=True, null=True)
    permission = models.CharField(max_length=20, default='sanc_auth',
                                  choices=Constants.LEAVE_PERMISSIONS)
    status = models.CharField(max_length=20, default='pending', choices=Constants.STATUS)

    def __str__(self):
        return '{} requested {}, {}'.format(self.leave.applicant.username,
                                            self.requested_from.username, self.permission)


class LeaveAdministrators(models.Model):
    """
    # Take care of `null` fields in back-end logic
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    authority = models.ForeignKey(Designation, null=True,
                                  related_name='sanc_authority_of', on_delete=models.SET_NULL)
    officer = models.ForeignKey(Designation, null=True,
                                related_name='sanc_officer_of', on_delete=models.SET_NULL)


class LeaveMigration(models.Model):
    type_migration = models.CharField(max_length=10, default='delete',
                                      choices=Constants.MIGRATION_CHOICES)
    date = models.DateField(null=False)
    replacee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='replacings')
    replacing_as = models.ForeignKey(HoldsDesignation, on_delete=models.CASCADE)

    def __str__(self):
        return '{} : {}, type => {}'.format(self.replacee.username, self.replacing_as.user.username,
                                            self.type_migration)
