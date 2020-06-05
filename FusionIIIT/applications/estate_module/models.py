from django.db import models

# Create your models here.


class Estate(models.Model):
    name = models.CharField(max_length=100)
    dateIssued = models.DateField()
    dateConstructionStarted = models.DateField(null=True, blank=True)
    dateConstructionCompleted = models.DateField(null=True, blank=True)
    dateOperational = models.DateField(null=True, blank=True)
    area = models.IntegerField(null=True, blank=True)
    constructionCostEstimated = models.IntegerField(null=True, blank=True)
    constructionCostActual = models.IntegerField(null=True, blank=True)
    numRooms = models.IntegerField(null=True, blank=True)
    numWashrooms = models.IntegerField(null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)

    def CW_List(self):
        return self.work_set.filter(workType='CW')

    def MW_List(self):
        return self.work_set.filter(workType='MW')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-id']


class WorkType(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Work(models.Model):

    CONSTRUCTION_WORK = 'CW'
    MAINTENANCE_WORK = 'MW'
    WORK_CHOICES = [
        (CONSTRUCTION_WORK, 'Construction'),
        (MAINTENANCE_WORK, 'Maintenance'),
    ]

    name = models.CharField(max_length=100)
    # workType = models.ForeignKey(WorkType, on_delete=models.CASCADE)
    workType = models.CharField(
        max_length=2, choices=WORK_CHOICES, default=MAINTENANCE_WORK)
    estate = models.ForeignKey(Estate, on_delete=models.CASCADE)
    contractorName = models.CharField(max_length=100)
    dateIssued = models.DateField()
    dateStarted = models.DateField(null=True, blank=True)
    dateCompleted = models.DateField(null=True, blank=True)
    costEstimated = models.IntegerField(null=True, blank=True)
    costActual = models.IntegerField(null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.estate.name + ' - ' + self.workType + ' - ' + self.name


class SubWork(models.Model):
    name = models.CharField(max_length=100)
    work = models.ForeignKey(Work, on_delete=models.CASCADE)
    dateIssued = models.DateField()
    dateStarted = models.DateField(null=True, blank=True)
    dateCompleted = models.DateField(null=True, blank=True)
    costEstimated = models.IntegerField(null=True, blank=True)
    costActual = models.IntegerField(null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)

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


class Inventory(models.Model):
    inventoryType = models.ForeignKey(InventoryType, on_delete=models.CASCADE)
    estate = models.ForeignKey(Estate, on_delete=models.CASCADE)
    work = models.ForeignKey(
        Work, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.IntegerField()
    dateOrdered = models.DateField()
    dateReceived = models.DateField(null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.inventoryType.name
