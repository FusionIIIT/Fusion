from django.db import models
from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation


class File(models.Model):
    """
    This is file table which contains the all the files created by user
    """
    uploader = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE, related_name='uploaded_files')
    designation = models.ForeignKey(Designation, on_delete=models.CASCADE, null=True, related_name='upload_designation')
    subject = models.CharField(max_length=100, null=True, blank=True)
    description = models.CharField(max_length=400, null=True, blank=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    upload_file = models.FileField(blank=True)
    is_read = models.BooleanField(default = False)


    class Meta:
        db_table = 'File'

    #def __str__(self):
        #return str(self.ref_id)


class Tracking(models.Model):
    """
    This is File Tracing Table which contains the status of each indivisual file created by the user 
    """
    file_id = models.ForeignKey(File, on_delete=models.CASCADE, null=True)
    current_id = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    current_design = models.ForeignKey(HoldsDesignation, null=True, on_delete=models.CASCADE)
        # receiver_id = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE, related_name='receiver_id')
    # receive_design = models.ForeignKey(HoldsDesignation, null=True, on_delete=models.CASCADE, related_name='rec_design')
    receiver_id = models.ForeignKey(User,null = True, on_delete=models.CASCADE, related_name='receiver_id')
    receive_design = models.ForeignKey(Designation, null=True, on_delete=models.CASCADE, related_name='rec_design')

    receive_date = models.DateTimeField(auto_now_add=True)
    forward_date = models.DateTimeField(auto_now_add=True)
    remarks = models.CharField(max_length=250, null=True, blank=True)
    upload_file = models.FileField(blank=True)
    is_read = models.BooleanField(default = False)

    class Meta:
        db_table = 'Tracking'
