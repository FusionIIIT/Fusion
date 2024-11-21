from django.db import models

class Item(models.Model):
    ITEM_TYPE_CHOICES = [
        ('Consumable', 'Consumable'),
        ('Non-Consumable', 'Non-Consumable'),
    ]
    
    item_id = models.AutoField(primary_key=True)
    item_name = models.CharField(max_length=100)  # e.g., computer
    quantity = models.PositiveIntegerField(default=0)
    type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES)
    unit = models.CharField(max_length=50)
    department = models.ForeignKey('DepartmentInfo', on_delete=models.CASCADE, related_name='items')

    def __str__(self):
        return self.item_name


class DepartmentInfo(models.Model):
    department_id = models.AutoField(primary_key=True)
    department_name = models.CharField(max_length=100)
    item_name = models.CharField(max_length=100)  # e.g., computer
    quantity = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.department_name

class SectionInfo(models.Model):
    section_id = models.AutoField(primary_key=True)
    section_name = models.CharField(max_length=100)
    item_name = models.CharField(max_length=100)  # e.g., computer
    quantity = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.section_name
