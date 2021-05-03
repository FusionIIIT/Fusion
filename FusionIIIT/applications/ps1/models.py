from django.db import models
from django.contrib.auth.models import User
from applications.globals.models import Staff,ExtraInfo
from applications.filetracking.models import File

class IndentFile(models.Model):
    
    file_info=models.OneToOneField(File, on_delete=models.CASCADE,primary_key=True)
    item_name=models.CharField(max_length=250,blank=False)
    quantity= models.IntegerField(blank=False)
    present_stock=models.IntegerField(blank=False)
    estimated_cost=models.IntegerField(null=True, blank=False)
    purpose=models.CharField(max_length=250,blank=False )
    specification=models.CharField(max_length=250)
    indent_type=models.CharField(max_length=250)
    nature=models.BooleanField(default = False)
    indigenous= models.BooleanField(default = False)
    replaced =models.BooleanField(default = False)
    budgetary_head=models.CharField(max_length=250)
    expected_delivery=models.DateField(blank=False)
    sources_of_supply=models.CharField(max_length=250)
    head_approval=models.BooleanField(default=False)
    director_approval=models.BooleanField(default = False)
    financial_approval=models.BooleanField(default = False)
    purchased =models.BooleanField(default = False)

    class Meta:
        db_table = 'IndentFile'

class StockEntry(models.Model):

    item_id=models.OneToOneField(IndentFile, on_delete=models.CASCADE,primary_key=True)
    dealing_assistant_id=models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    vendor=models.CharField(max_length=250, blank=False)
    item_name=models.CharField(max_length=250, blank=False)
    current_stock=models.IntegerField(blank=False)
    recieved_date=models.DateField(blank=False)
    bill=models.FileField(blank=False)

    class Meta:
        db_table = 'StockEntry'