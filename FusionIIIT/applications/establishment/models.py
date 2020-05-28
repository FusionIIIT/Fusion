from django.db import models
from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation

class Constants:
    STATUS = (
        ('draft', 'Draft'),
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('adjustments_pending', 'Adjustments Pending'),
        ('finished', 'Finished')
    )
class CPDA_application(models.Model):
    # application_id = models.CharField(max_length=50, default='')
    status = models.CharField(max_length=20, null=True, choices=Constants.STATUS)

    # CPDA Request fields
    applicant = models.ForeignKey(User, on_delete=models.CASCADE)
    pf_number = models.CharField(max_length=50, default='')
    purpose = models.CharField(max_length=500, default='', blank=True)
    requested_advance = models.IntegerField(default='')
    extra_info = models.CharField(max_length=200, blank=True, null=True, default='')
    request_timestamp = models.DateTimeField(auto_now=True, null=True)

    # CPDA Adjustment fields
    adjustment_amount = models.IntegerField(default='')
    bills_attached = models.IntegerField(default='', blank=True)
    total_bills_amount = models.IntegerField(default='')
    ppa_register_page_no = models.IntegerField(default='', blank=True)
    adjustment_timestamp = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        db_table = 'CPDA Application'


class CPDA_tracking(models.Model):
    application_id = models.ForeignKey(CPDA_application, on_delete=models.CASCADE, null=True)
    current_id = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    current_design = models.ForeignKey(HoldsDesignation, null=True, on_delete=models.CASCADE)
    forward_to = models.ForeignKey(User,null = True, on_delete=models.CASCADE)
    forward_design = models.ForeignKey(Designation, null=True, on_delete=models.CASCADE)
    remarks = models.CharField(max_length=250, null=True, blank=True)

    class Meta:
        db_table = 'CPDA Tracking'

