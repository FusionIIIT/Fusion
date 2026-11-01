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
    year = models.IntegerField(default=2019)
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    remaining_leaves = models.FloatField(default=2.0)

    def save(self, *args, **kwargs):
        if self.year < 2018 or self.remaining_leaves < 0:
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
    # ELM lifecycle metadata. The legacy status field remains for existing screens.
    elm_state = models.CharField(max_length=40, blank=True, default='')
    station_leave = models.BooleanField(default=False)
    station_details = models.CharField(max_length=500, blank=True, default='')
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


class ELMPolicy(models.Model):
    """Versioned ELM policy. Only published records are effective for new decisions."""
    CATEGORIES = (('CL', 'Casual Leave'), ('RH', 'Restricted Holiday'),
                  ('SCL', 'Special Casual Leave'), ('EL', 'Earned Leave'),
                  ('COL', 'Commuted Leave'), ('VL', 'Vacation Leave'))
    category = models.CharField(max_length=3, choices=CATEGORIES)
    annual_entitlement = models.DecimalField(max_digits=7, decimal_places=2)
    eligible_faculty = models.BooleanField(default=True)
    eligible_staff = models.BooleanField(default=True)
    carry_forward = models.BooleanField(default=False)
    counts_continuous_days = models.BooleanField(default=False)
    requires_medical_evidence = models.BooleanField(default=False)
    requires_substitute = models.BooleanField(default=False)
    published = models.BooleanField(default=False)
    effective_from = models.DateField(null=True, blank=True)
    effective_to = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('category', '-created_at')

    def __str__(self):
        return '{} policy ({})'.format(self.category, 'published' if self.published else 'draft')


class ELMCalendar(models.Model):
    """Versioned holiday/RH/vacation date set; unpublished edits do not become effective."""
    name = models.CharField(max_length=100)
    year = models.PositiveIntegerField()
    published = models.BooleanField(default=False)
    effective_from = models.DateField(null=True, blank=True)
    effective_to = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class ELMCalendarDate(models.Model):
    TYPES = (('closed', 'Closed holiday'), ('restricted', 'Restricted holiday'),
             ('vacation', 'Vacation'))
    calendar = models.ForeignKey(ELMCalendar, related_name='dates', on_delete=models.CASCADE)
    date = models.DateField()
    date_type = models.CharField(max_length=12, choices=TYPES)

    class Meta:
        unique_together = (('calendar', 'date', 'date_type'),)


class ELMRouteConfiguration(models.Model):
    """Explicit administrator-configured approval route for a unit/category."""
    unit = models.ForeignKey('globals.DepartmentInfo', null=True, blank=True,
                             on_delete=models.CASCADE)
    category = models.CharField(max_length=3, choices=ELMPolicy.CATEGORIES)
    step = models.PositiveSmallIntegerField()
    designation = models.ForeignKey(Designation, on_delete=models.CASCADE)
    is_unit_head = models.BooleanField(default=False)
    is_director_self_sanction = models.BooleanField(default=False)
    is_resumption_verifier = models.BooleanField(default=False)
    is_establishment = models.BooleanField(default=False)
    reminder_after_hours = models.PositiveIntegerField(null=True, blank=True)
    escalate_after_hours = models.PositiveIntegerField(null=True, blank=True)
    published = models.BooleanField(default=False)

    class Meta:
        ordering = ('step',)
        unique_together = (('unit', 'category', 'step', 'published',
                            'is_unit_head', 'is_director_self_sanction',
                            'is_resumption_verifier'),)


class ELMWorkflowTask(models.Model):
    TASKS = (('substitute', 'Substitute response'), ('unit_head', 'Unit Head review'),
             ('establishment', 'Establishment routing'), ('sanction', 'Final sanction'),
             ('cancellation', 'Cancellation review'), ('resumption', 'Resumption verification'))
    STATUSES = (('pending', 'Pending'), ('accepted', 'Accepted'), ('declined', 'Declined'),
                ('recommended', 'Recommended'), ('not_recommended', 'Not recommended'),
                ('approved', 'Approved'), ('rejected', 'Rejected'), ('superseded', 'Superseded'))
    leave = models.ForeignKey(Leave, related_name='elm_tasks', on_delete=models.CASCADE)
    change_request = models.ForeignKey('ELMChangeRequest', null=True, blank=True,
        related_name='tasks', on_delete=models.CASCADE)
    task_type = models.CharField(max_length=20, choices=TASKS)
    route_step = models.PositiveSmallIntegerField(null=True, blank=True)
    assignee = models.ForeignKey(User, related_name='elm_tasks', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUSES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    reminder_after_hours = models.PositiveIntegerField(null=True, blank=True)
    escalate_after_hours = models.PositiveIntegerField(null=True, blank=True)
    last_reminder_at = models.DateTimeField(null=True, blank=True)
    last_escalation_at = models.DateTimeField(null=True, blank=True)
    remark = models.TextField(blank=True, default='')


class ELMAccountTransaction(models.Model):
    user = models.ForeignKey(User, related_name='elm_account_transactions', on_delete=models.CASCADE)
    category = models.CharField(max_length=3, choices=ELMPolicy.CATEGORIES)
    year = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    reason = models.CharField(max_length=40)
    leave = models.ForeignKey(Leave, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    reference = models.CharField(max_length=200, blank=True, default='')


class ELMChangeRequest(models.Model):
    TYPES = (('cancel', 'Cancellation'), ('extension', 'Extension'), ('resumption', 'Resumption'))
    STATUSES = (('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'),
                ('verified', 'Verified'))
    leave = models.ForeignKey(Leave, related_name='elm_changes', on_delete=models.CASCADE)
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE)
    change_type = models.CharField(max_length=12, choices=TYPES)
    status = models.CharField(max_length=12, choices=STATUSES, default='pending')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    actual_return_date = models.DateField(null=True, blank=True)
    details = models.TextField(blank=True, default='')
    evidence_reference = models.CharField(max_length=200, blank=True, default='')
    medical_evidence = models.FileField(upload_to='leave/elm_change_evidence/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)


class ELMYearEndRun(models.Model):
    year = models.PositiveIntegerField(unique=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    exceptions = models.TextField(blank=True, default='')


class ELMActionLog(models.Model):
    ACTIONS = (('reminder', 'SLA reminder'), ('escalation', 'SLA escalation'),
               ('year_end_exception', 'Year-end exception'))
    task = models.ForeignKey(ELMWorkflowTask, null=True, blank=True,
                             related_name='action_logs', on_delete=models.SET_NULL)
    action = models.CharField(max_length=30, choices=ACTIONS)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class LeaveOffline(models.Model):
    applicant = models.ForeignKey(User, related_name='all_leaves_offline',on_delete=models.CASCADE)
    leave_user_select = models.ForeignKey(User, on_delete=models.CASCADE,null=True)
    purpose = models.CharField(max_length=500, default='', blank=True)
    timestamp = models.DateTimeField(auto_now=True, null=True)
    application_date = models.DateField()
    #is_station = models.BooleanField(default=False)

    def get_current_leave_balance(self):
        curr_year = timezone.now().year
        balances = self.applicant.leave_balance.filter(year=curr_year)
        return balances

    def generate_requests(self):
        pass

    def __str__(self):
        return '{} applied, status: {}'.format(self.applicant.username,
                                               'succeed')


# TODO: Add more fields
class ReplacementSegmentOffline(models.Model):
    leave = models.ForeignKey(LeaveOffline, related_name='replace_segments_offline', on_delete=models.CASCADE)
    replacer = models.ForeignKey(User, related_name='rep_requests_offline', on_delete=models.CASCADE)
    replacement_type = models.CharField(max_length=20, default='academic',
                                        choices=Constants.REPLACEMENT_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()


class LeaveSegmentOffline(models.Model):
    leave = models.ForeignKey(LeaveOffline, related_name='segments_offline', on_delete=models.CASCADE)
    leave_type = models.ForeignKey(LeaveType, on_delete=models.SET_NULL, null=True, default=None)
    document = models.FileField(upload_to='leave/leave_documents/', null=True)
    start_date = models.DateField()
    start_half = models.BooleanField(default=False)
    end_date = models.DateField()
    end_half = models.BooleanField(default=False)
    address = models.CharField(max_length=500, default='', blank=True, null=True)
