from django.conf import settings
from django.db import models

# Create your models here.


class Building(models.Model):
    ON_SCHEDULE = 'OS'
    DELAYED = 'DL'
    STATUS_CHOICES = [
        (ON_SCHEDULE, 'On Schedule'),
        (DELAYED, 'Delayed'),
    ]
    name = models.CharField(max_length=100)
    dateIssued = models.DateField()
    dateConstructionStarted = models.DateField(null=True, blank=True)
    dateConstructionCompleted = models.DateField(null=True, blank=True)
    dateOperational = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=2, choices=STATUS_CHOICES, default=ON_SCHEDULE)
    area = models.IntegerField(null=True, blank=True)
    constructionCostEstimated = models.IntegerField(null=True, blank=True)
    constructionCostActual = models.IntegerField(null=True, blank=True)
    numRooms = models.IntegerField(null=True, blank=True)
    numWashrooms = models.IntegerField(null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    verified = models.BooleanField(default=False)

    def works(self):
        works_all = self.work_set.all()
        workList = [
            (Work.MAINTENANCE_WORK, 'Maintenance',
             works_all.filter(workType=Work.MAINTENANCE_WORK)),
            (Work.CONSTRUCTION_WORK, 'Construction',
             works_all.filter(workType=Work.CONSTRUCTION_WORK))
        ]
        return workList

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return self.name


class Work(models.Model):

    CONSTRUCTION_WORK = 'CW'
    MAINTENANCE_WORK = 'MW'
    WORK_CHOICES = [
        (CONSTRUCTION_WORK, 'Construction'),
        (MAINTENANCE_WORK, 'Maintenance'),
    ]

    ON_SCHEDULE = 'OS'
    DELAYED = 'DL'

    STATUS_CHOICES = [
        (ON_SCHEDULE, 'On Schedule'),
        (DELAYED, 'Delayed'),
    ]

    name = models.CharField(max_length=100)
    workType = models.CharField(
        max_length=2, choices=WORK_CHOICES, default=MAINTENANCE_WORK)
    building = models.ForeignKey(
        Building, on_delete=models.CASCADE, null=True, blank=True)
    contractorName = models.CharField(max_length=100)
    status = models.CharField(
        max_length=2, choices=STATUS_CHOICES, default=ON_SCHEDULE)
    dateIssued = models.DateField()
    dateStarted = models.DateField(null=True, blank=True)
    dateCompleted = models.DateField(null=True, blank=True)
    costEstimated = models.IntegerField(null=True, blank=True)
    costActual = models.IntegerField(null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    verified = models.BooleanField(default=False)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return self.name


class SubWork(models.Model):
    name = models.CharField(max_length=100)
    work = models.ForeignKey(Work, on_delete=models.CASCADE)
    dateIssued = models.DateField()
    dateStarted = models.DateField(null=True, blank=True)
    dateCompleted = models.DateField(null=True, blank=True)
    costEstimated = models.IntegerField(null=True, blank=True)
    costActual = models.IntegerField(null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return self.work.name + ' - ' + self.name


class InventoryType(models.Model):
    name = models.CharField(max_length=100)
    rate = models.IntegerField()
    manufacturer = models.CharField(max_length=100, null=True, blank=True)
    model = models.CharField(max_length=100, null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


class InventoryCommon(models.Model):

    inventoryType = models.ForeignKey(InventoryType, on_delete=models.CASCADE)
    building = models.ForeignKey(
        Building, on_delete=models.CASCADE, null=True, blank=True)
    work = models.ForeignKey(
        Work, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.IntegerField()
    dateOrdered = models.DateField()
    dateReceived = models.DateField(null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)

    def cost(self):
        return self.quantity * self.inventoryType.rate

    def __str__(self):
        return self.inventoryType.name

    class Meta:
        abstract = True
        ordering = ['-id']


class InventoryConsumable(InventoryCommon):
    presentQuantity = models.IntegerField()


class InventoryNonConsumable(InventoryCommon):
    serial_no = models.CharField(max_length=20)
    dateLastVerified = models.DateField()
    issued_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
