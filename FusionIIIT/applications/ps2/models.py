from django.conf import settings
from django.db import models
from ..globals.models import User

class StockAdmin(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=255, blank=False)

class StockEntry(models.Model):
    name_of_particulars = models.CharField(max_length=50, blank=False)
    inventory_no = models.CharField(max_length=50, blank=False)
    rate = models.IntegerField(blank=False)
    amount = models.IntegerField(blank=False)
    supplier_name = models.CharField(max_length=50, blank=False)
    bill_no = models.IntegerField(blank=False)
    buy_date = models.DateField(blank=False)
    issued_date = models.DateField(blank=False)
    head_of_asset = models.CharField(max_length=50, blank=False)
    section = models.CharField(max_length=50, blank=True, null=True)
    floor = models.IntegerField(blank=True, null=True)
    receiver_name = models.CharField(max_length=50, blank=False)

    class Meta:
        db_table = 'ps2_stocks'

class TransferEntry(models.Model):
    item_id = models.IntegerField(blank=False)
    from_department = models.CharField(max_length=50, blank=False)
    from_location = models.IntegerField(blank=True, null=True)
    to_department = models.CharField(max_length=50, blank=False)
    to_location = models.IntegerField(blank=True, null=True)
    date = models.DateTimeField(blank=False)
    remark = models.CharField(max_length=200, blank=False)

    class Meta:
        db_table = 'ps2_transfer'