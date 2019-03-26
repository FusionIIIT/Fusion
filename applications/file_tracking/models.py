from django.db import models

from applications.globals.models import ExtraInfo


class Constants:
    STATUS = (
        ('0', 'resolved'),
        ('1', 'notresolved'),
    )
    FILE_TYPE = (
        ('HardCopy', 'HardCopy'),
        ('SoftCopy', 'SoftCopy'),
    )


class File(models.Model):
    employee_id = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE, related_name='employee_id')
    subject = models.CharField(max_length=40)
    file_type = models.CharField(max_length=20, choices=Constants.FILE_TYPE)
    description = models.CharField(max_length=100)
    status = models.IntegerField(choices=Constants.STATUS, default=1)
    leave_flag = models.BooleanField(default=False)
    substitute_id = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE,
                                      related_name='substitute_id')
    upload_date = models.DateTimeField(auto_now=True)
    resolve_date = models.DateTimeField()


class Tracking(models.Model):
    file_id = models.ForeignKey(File, on_delete=models.CASCADE)
    current_id = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    receive_date = models.DateTimeField()
    forward_date = models.DateTimeField()
    remark = models.CharField(max_length=250)
    forward_flag = models.BooleanField(default=False)
