from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

class StockEntry(models.Model):
    stock_no = models.IntegerField(blank=False)
    name_of_particulars = models.CharField(max_length=50, blank=False)
    inventory_no = models.CharField(max_length=50, blank=False)
    quantity = models.IntegerField(blank=False)
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
    stock_no = models.OneToOneField(StockEntry, on_delete=models.CASCADE)
    inventory_no = models.CharField(max_length=50, blank=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE , related_name='current_user')
    is_current_user = models.BooleanField(default=True)
    remark = models.TextField()
    date_time = models.DateTimeField()

    class Meta:
        db_table = "ps2_transfer"

