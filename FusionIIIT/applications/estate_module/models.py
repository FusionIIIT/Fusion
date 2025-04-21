from django.conf import settings
from django.db import models

# Create your models here.


class Building(models.Model):
    """
    Details of the building
    @fields-
        name: name of the building
        dateIssued: date when the building was issued
        dateConstructionStarted: date when construction of building was started
        dateComstructionCompleted: date when construction of building was completed
        dateOperational: date when building became operational
        status: status of the building if it's work is on time or delayed
        area: total area of the building
        constructionCostEstimated: estimated cost of construction of building
        constructionCostActual: actual cost of construction of building
        numRooms: number of rooms in building
        numWashrooms: number of washrooms in building
        remarks: remarks for the building
        verified: tells building is verified or not
    """
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

    """
        Tells about the works
        @fields-
            name: name for the work
            workType: type of the work
            building: in which building work is done
            contractorName: nsme of the contractor who is doing the work
            status: status of the work
            dateIssued: date when the work was issued
            dateStarted: date when work was started
            dateCompleted: date when work was completed
            costEstimated: estimated cost of the work
            costActual: actual cost of the work
            remarks: remarks for the work
            verified: work is verified or not
    """

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
    """
        Details about the subWork
        @field-
            name: name of the subWork
            work: work under which the subWork is going
            dateIssued: date when the subwork was issued
            dateStarted: date when the subwork was started
            dateCompleted: date when the subwork was completed
            costEstimated: estimated cost of subwork
            costActual: actual cost of subwork
            remarks: remarks for the subWork
    """
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
    """
        Details about different type of inventory
        @fields-
            name: name of the inventory
            rate: rate of the item in inventory
            manufacturer: manufacturer of the item present in inventory
            model: model of the item present in inventory
            remarks: remarks for the item present in inventory
    """
    name = models.CharField(max_length=100)
    rate = models.IntegerField()
    manufacturer = models.CharField(max_length=100, null=True, blank=True)
    model = models.CharField(max_length=100, null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


class InventoryCommon(models.Model):
    """
        Details about the common inventory
        @field-
            inventoryType: type of inventory
            building: building where inventory is present
            work: work associated with inventory
            quantity: quantity of the inventory
            dateOrdered: ordered date
            dateRecieved: recieved date
            remarks: remarks for the inventory
    """

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
    """
        Details about consumable inventory
        @fields-
            presentQuantity: presentQuantity of the item present in inventory
    """
    presentQuantity = models.IntegerField()


class InventoryNonConsumable(InventoryCommon):
    """
        Details about non-consumable inventory
        @fields-
            serial_no: serial no of inventory
            dateLastVerified: date when inventory was last verified
            issued_to: details about user which has consumed the inventory
    """
    serial_no = models.CharField(max_length=20)
    dateLastVerified = models.DateField()
    issued_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
