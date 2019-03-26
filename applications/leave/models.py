from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from applications.globals.models import Designation


class Constants:

    REPLACEMENT_TYPES = (
        ('academic', 'Academic Replacement'),
        ('administrative', 'Administrative Replacement')
    )

    LEAVE_PERMISSIONS = (
        ('intermediary', 'Intermediary Staff'),
        ('sanc_auth', 'Leave Sanctioning Authority'),
        ('sanc_off', 'Leave Sanctioning Officer'),
    )

    STATUS = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('forwarded', 'Forwarded'),
        ('auto rejected', 'Auto Rejected')
    )

    MIGRATION_CHOICES = (
        ('revert', 'Revert Responsibilities'),
        ('transfer', 'Transfer Responsibilities')
    )

#@python_2_unicode_compatible
class LeaveType(models.Model):
    name = models.CharField(max_length=40, null=False)
    max_in_year = models.IntegerField(default=2)
    requires_proof = models.BooleanField(default=False)
    authority_forwardable = models.BooleanField(default=False)
    for_faculty = models.BooleanField(default=True)
    for_staff = models.BooleanField(default=True)
    for_student = models.BooleanField(default=False)
    requires_address = models.BooleanField(default=False)
    
    #@property
    #def is_station(self):
    #    return self.name == 'Station'

    def __str__(self):
        return f'{self.name}, Max: {self.max_in_year}'


class LeavesCount(models.Model):
    user = models.ForeignKey(User, related_name='leave_balance', on_delete=models.CASCADE)
    year = models.IntegerField(default=2015)
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    remaining_leaves = models.FloatField(default=2.0)

    def save(self, *args, **kwargs):
        if self.year < 2015 or self.remaining_leaves < 0:
            raise ValueError('Year must be greater than 2018 and remaining leaves more than 0')
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
    timestamp = models.DateTimeField(auto_now=True, null=True)
    extra_info = models.CharField(max_length=200, blank=True, null=True, default='')
    #is_station = models.BooleanField(default=False)

    @property
    def to_forward(self):
        for segment in self.segments.all():
            if segment.leave_type.authority_forwardable:
                return True
        return False

    def relacements_accepted(self):
        return not self.replace_segments.filter(status='pending').exists()

    def generate_requests(self):
        pass

    def get_current_leave_balance(self):
        curr_year = timezone.now().year
        balances = self.applicant.leave_balance.filter(year=curr_year)
        return balances

    @property
    def yet_not_started(self):
        #for segment in self.segments.all():
        #    today = timezone.now().date()
        #    if segment.start_date <= today:
        #        return False
        return True

    def __str__(self):
        return '{} applied, status: {}'.format(self.applicant.username,
                                               self.status)


# TODO: Add more fields
class ReplacementSegment(models.Model):
    leave = models.ForeignKey(Leave, related_name='replace_segments', on_delete=models.CASCADE)
    replacer = models.ForeignKey(User, related_name='rep_requests', on_delete=models.CASCADE)
    replacement_type = models.CharField(max_length=20, default='academic',
                                        choices=Constants.REPLACEMENT_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, default='pending', choices=Constants.STATUS)
    remark = models.CharField(max_length=50, default='', blank=True, null=True)


class LeaveSegment(models.Model):
    leave = models.ForeignKey(Leave, related_name='segments', on_delete=models.CASCADE)
    leave_type = models.ForeignKey(LeaveType, on_delete=models.SET_NULL, null=True, default=None)
    document = models.FileField(upload_to='leave/leave_documents/', null=True)
    start_date = models.DateField()
    start_half = models.BooleanField(default=False)
    end_date = models.DateField()
    end_half = models.BooleanField(default=False)
    address = models.CharField(max_length=500, default='', blank=True, null=True)


class LeaveRequest(models.Model):
    leave = models.ForeignKey(Leave, related_name='leave_requests', on_delete=models.CASCADE)
    requested_from = models.ForeignKey(User, related_name='all_leave_requests',
                                       on_delete=models.CASCADE)
    remark = models.CharField(max_length=50, blank=True, null=True)
    permission = models.CharField(max_length=20, default='sanc_auth',
                                  choices=Constants.LEAVE_PERMISSIONS)
    status = models.CharField(max_length=20, default='pending', choices=Constants.STATUS)

    @property
    def by_student(self):
        return self.leave.applicant.extrainfo.usertype == 'student'

    def __str__(self):
        return '{} requested {}, {}'.format(self.leave.applicant.username,
                                            self.requested_from.username, self.permission)


class LeaveAdministrators(models.Model):
    """
    # Take care of `null` fields in back-end logic
    """
    user = models.OneToOneField(User, related_name='leave_admins', on_delete=models.CASCADE)
    authority = models.ForeignKey(Designation, null=True,
                                  related_name='sanc_authority_of', on_delete=models.SET_NULL)
    officer = models.ForeignKey(Designation, null=True,
                                related_name='sanc_officer_of', on_delete=models.SET_NULL)

    @property
    def is_one_level(self):
        return self.authority == self.officer

    def __str__(self):
        return f'{self.user}, auth: {self.authority}, off: {self.officer}'


class LeaveMigration(models.Model):
    leave = models.ForeignKey(Leave, related_name='all_migrations', on_delete=models.CASCADE)
    type_migration = models.CharField(max_length=10, default='transfer',
                                      choices=Constants.MIGRATION_CHOICES)
    on_date = models.DateField(null=False)
    replacee = models.ForeignKey(User, on_delete=models.CASCADE,
                                 related_name='replacee_migrations')
    replacer = models.ForeignKey(User, related_name='replacer_migrations',
                                 on_delete=models.CASCADE)
    replacement_type = models.CharField(max_length=20, default='academic',
                                        choices=Constants.REPLACEMENT_TYPES)

    def __str__(self):
        return '{} : {}, type => {}'.format(self.replacee.username, self.replacer.username,
                                            self.type_migration)

class RestrictedHoliday(models.Model):
    date = models.DateField()

class ClosedHoliday(models.Model):
    date = models.DateField()

class VacationHoliday(models.Model):
    date = models.DateField()
