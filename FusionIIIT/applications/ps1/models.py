from django.db import models
from django.contrib.auth.models import User
from applications.globals.models import Staff,ExtraInfo,DepartmentInfo
from applications.filetracking.models import File
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

class IndentFile(models.Model):
    
    file_info=models.OneToOneField(File, on_delete=models.CASCADE,primary_key=True)
    item_name=models.CharField(max_length=250,blank=False) # Apple pro vision 3.0
    quantity= models.IntegerField(blank=False)
    present_stock=models.IntegerField(blank=False)
    estimated_cost=models.IntegerField(null=True, blank=False)
    purpose=models.CharField(max_length=250,blank=False )
    specification=models.CharField(max_length=250)
    item_type=models.CharField(max_length=250)
    item_subtype = models.CharField(max_length=250,blank=False,default='computers')
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


class Constants:
    Locations = (
        ('SR1', 'LHTC'),
        ('SR2', 'Computer Center'),
        ('SR3', 'Panini Hostel'),
        ('SR4', 'Lab complex'),
        ('SR5', 'Admin Block'),
    )

class StockEntry(models.Model):

    item_id=models.OneToOneField(IndentFile, on_delete=models.CASCADE,primary_key=True)
    dealing_assistant_id=models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    vendor=models.CharField(max_length=250, blank=False)
    current_stock=models.IntegerField(blank=False)
    recieved_date = models.DateField(blank=False)
    bill=models.FileField(blank=False)
    location = models.CharField(max_length=100 ,choices=Constants.Locations,default='SR1')
    class Meta:
        db_table = 'StockEntry'

# Individual Stock Item 
class StockItem(models.Model):
    # this represents the id of the StockEntry instance (StockEntryId_id)

    # this StockEntryId will never ever change onces StockItem instance is created and will therefore be used for obtaining the grade,indentfile etc. details.

    StockEntryId = models.ForeignKey(StockEntry,on_delete=models.CASCADE)
    nomenclature = models.CharField(max_length=100, unique=True)  # Unique identifier for each StockItem
    inUse = models.BooleanField(default=True)

    # as department is going to be a variable field here I have to add a Department fiedl for making our job a bit easir and same goes for location as well. Redundancy Hurts :).

    department = models.ForeignKey(
        DepartmentInfo, on_delete=models.CASCADE, null=True, blank=True)
    location = models.CharField(max_length=100,choices=Constants.Locations,default='SR1')
    isTransferred = models.BooleanField(default=False)

    class Meta: 
        db_table = 'StockItem'

    def save(self, *args, **kwargs):
        # Generate nomenclature when saving the StockItem instance
        if not self.nomenclature:
            # Construct nomenclature using StockEntry primary key and a sequential number
            max_existing_number = StockItem.objects.filter(StockEntryId=self.StockEntryId_id).count()
            new_number = max_existing_number + 1
            self.nomenclature = f"{self.StockEntryId.item_id}_{new_number}"
        super().save(*args, **kwargs)


# this table will be used to keep a track of all the stockTransfer things.
class StockTransfer(models.Model):
    indent_file=models.ForeignKey(IndentFile, on_delete=models.CASCADE)

    src_dept= models.ForeignKey(
        DepartmentInfo, on_delete=models.CASCADE, null=True, blank=True, related_name='dept_src_transfers')
    dest_dept=  models.ForeignKey(
        DepartmentInfo, on_delete=models.CASCADE, null=True, blank=True, related_name='dept_dest_transfers')
    
    stockItem= models.ForeignKey(StockItem,on_delete=models.CASCADE)
    src_location = models.CharField(max_length=100,choices=Constants.Locations,default='SR1')
    dest_location = models.CharField(max_length=100,choices=Constants.Locations,default='SR2')
    dateTime = models.DateTimeField(default=timezone.now)

    class Meta :
        db_table = 'StockTransfer'
    

@receiver(post_save, sender=StockEntry)
def create_stock_items(sender, instance, created, **kwargs):
    if created:
        # Automatically create 'n' number of StockItem instances based on current_stock of StockEntry
        # instance is stockEntry 
        current_stock = int(instance.current_stock)
        for _ in range(current_stock):
            StockItem.objects.create(StockEntryId=instance,location=instance.location,department=instance.item_id.file_info.uploader.department)

