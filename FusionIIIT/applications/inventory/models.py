from django.db import models
from django.contrib.auth.models import User


class Item(models.Model):
    ITEM_TYPE_CHOICES = [
        ('Consumable', 'Consumable'),
        ('Non-Consumable', 'Non-Consumable'),
    ]
    
    item_id = models.AutoField(primary_key=True)
    item_name = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField(default=0)
    type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES)
    unit = models.CharField(max_length=20)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.item_name


class DepartmentInfo(models.Model):
    subdepartment_id = models.AutoField(primary_key=True)
    subdepartment_name = models.CharField(max_length=100)
    department_name = models.CharField(max_length=100)
    admin = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.subdepartment_name


class Relationship(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    subdepartment = models.ForeignKey(DepartmentInfo, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('item', 'subdepartment')

    def __str__(self):
        return f"{self.item.item_name} in {self.subdepartment.subdepartment_name} - Quantity: {self.quantity}"


class Event(models.Model):
    EVENT_TYPE_CHOICES = [
        ('Addition', 'Addition'),
        ('Removal', 'Removal'),
        ('Transfer', 'Transfer'),
    ]

    event_id = models.AutoField(primary_key=True)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    in_subdepartment = models.ForeignKey(DepartmentInfo, on_delete=models.CASCADE, related_name='in_subdepartment')
    from_subdepartment = models.ForeignKey(DepartmentInfo, on_delete=models.CASCADE, related_name='from_subdepartment', blank=True, null=True)
    responsible_user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.event_type} - {self.item.item_name} - {self.quantity}"

