from django.db import models
from django.contrib.auth.models import User
from applications.globals.models import Staff,ExtraInfo
from applications.filetracking.models import File

class IndentFile(models.Model):
    
    file_info=models.OneToOneField(File, on_delete=models.CASCADE,primary_key=True)
    item_name=models.CharField(max_length=250,blank=False) # Apple pro vision 3.0
    quantity= models.IntegerField(blank=False)
    present_stock=models.IntegerField(blank=False)
    estimated_cost=models.IntegerField(null=True, blank=False)
    purpose=models.CharField(max_length=250,blank=False )
    specification=models.CharField(max_length=250)
    grade = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C')],default='A')
    item_type=models.CharField(max_length=250)
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


# class IndentFile2(models.Model):

#     file_info = models.OneToOneField(
#         File, on_delete=models.CASCADE, primary_key=True)
#     title=models.CharField(max_length=250,blank=False,default="")
#     budgetary_head = models.CharField(max_length=250)
#     expected_delivery = models.DateField(blank=False)
#     sources_of_supply = models.CharField(max_length=250)
#     head_approval = models.BooleanField(default=False)
#     director_approval = models.BooleanField(default=False)
#     financial_approval = models.BooleanField(default=False)
#     procured = models.BooleanField(default=False)
#     description = models.CharField(max_length=250,blank=False,default="")

#     class Meta:
#         db_table = 'IndentFile2'


# class Item(models.Model):
#     item_id = models.AutoField(primary_key=True)
#     indent_file_id = models.ForeignKey(
#         IndentFile2, on_delete=models.CASCADE, null=True, blank=False)
#     file_info = models.OneToOneField(
#         File, on_delete=models.CASCADE)
#     item_name = models.CharField(max_length=250, blank=False)
#     quantiy = models.IntegerField(blank=False)
#     present_stock = models.IntegerField(blank=False)
#     estimated_cost = models.IntegerField(null=True, blank=False)
#     purpose = models.CharField(max_length=250, blank=False)
#     specification = models.CharField(max_length=250)
#     item_type = models.CharField(max_length=250)
#     nature = models.BooleanField(default=False)
#     indigenous = models.BooleanField(default=False)
#     replaced = models.BooleanField(default=False)
#     purchased = models.BooleanField(default=False)

#     class Meta:
#         db_table = 'Item'


class Constants:
    Locations = (
        ('H1', 'Vashistha Hostel'),
        ('H4', 'Vivekananda Hostel'),
        ('H3', 'AryaBhatta Hostel'),
        ('SR1', 'Storage Room 1'),
        ('SR2', 'Storage Room 2'),
        ('SR3', 'Storage Room 3'),
        ('SR4', 'Storage Room 4'),
        ('SR5', 'Storage Room 5'),
    )

class StockEntry(models.Model):

    item_id=models.OneToOneField(IndentFile, on_delete=models.CASCADE,primary_key=True)
    dealing_assistant_id=models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    vendor=models.CharField(max_length=250, blank=False)
    itemType=models.CharField(max_length=250, blank=False,default='Computers')
    current_stock=models.IntegerField(blank=False)
    recieved_date=models.DateField(blank=False)
    bill=models.FileField(blank=False)
    location = models.CharField(max_length=100 ,choices=Constants.Locations,default='SR1')
    class Meta:
        db_table = 'StockEntry'

# Individual Stock Item
class StockItem(models.Model):
    StockEntryId = models.OneToOneField(StockEntry,on_delete=models.CASCADE)
    
    class Meta: 
        db_table = 'StockItem'