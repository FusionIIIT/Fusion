from django.db import models
from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation

class Constants:
    STATUS = (
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('adjustments_pending', 'Adjustments Pending'),
        ('finished', 'Finished')
    )
    REVIEW_STATUS = (
        ('to_assign', 'To Assign'),
        ('under_review', 'Under Review'),
        ('reviewed', 'Reviewed')
    )


class Establishment_variables(models.Model):
    est_admin = models.ForeignKey(User, on_delete=models.CASCADE)


class Cpda_application(models.Model):
    status = models.CharField(max_length=20, null=True, choices=Constants.STATUS)

    # CPDA Request fields
    applicant = models.ForeignKey(User, on_delete=models.CASCADE)
    pf_number = models.CharField(max_length=50, default='')
    purpose = models.CharField(max_length=500, default='', blank=True)
    requested_advance = models.IntegerField(blank=True)
    request_timestamp = models.DateTimeField(auto_now=True, null=True)

    # CPDA Adjustment fields
    adjustment_amount = models.IntegerField(blank=True, null=True, default='0')
    bills_attached = models.IntegerField( blank=True, null=True, default='-1')
    total_bills_amount = models.IntegerField( blank=True, null=True, default='0')
    ppa_register_page_no = models.IntegerField( blank=True, null=True, default='-1')
    adjustment_timestamp = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return 'cpda id ' + str(self.id) + ', applied by ' + self.applicant.username

    class Meta:
        db_table = 'Cpda Application'
        

class Cpda_tracking(models.Model):
    application = models.OneToOneField(Cpda_application, primary_key=True, related_name='tracking_info',on_delete=models.CASCADE)
    # current_id : application is currently with
    # current_id = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    # current_design = models.ForeignKey(HoldsDesignation, null=True, on_delete=models.CASCADE)
    # forward_to : application will be forwarded to
    reviewer_id = models.ForeignKey(User, null = True, blank=True, on_delete=models.CASCADE)
    reviewer_design = models.ForeignKey(Designation, null=True, blank=True, on_delete=models.CASCADE)
    remarks = models.CharField(max_length=250, null=True, blank=True)
    review_status = models.CharField(max_length=20, null=True, choices=Constants.REVIEW_STATUS)

    def __str__(self):
        return 'cpda id ' + str(self.application.id) + ' tracking'

    class Meta:
        db_table = 'Cpda Tracking'


class Cpda_bill(models.Model):
    application = models.ForeignKey(Cpda_application, on_delete=models.CASCADE, null=True)
    bill = models.FileField(blank=True)

    def __str__(self):
        return 'cpda id ' + str(self.application.id) + ', bill id ' + str(self.id)

    class Meta:
        db_table = 'Cpda Bills'