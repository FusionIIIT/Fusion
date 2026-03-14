from django.db import models
from datetime import date
from django.contrib.auth.models import User
from applications.filetracking.models import File


class RequestStatus(models.TextChoices):
    CREATED = "CREATED", "Created"
    ENGINEER_PROCESSED = "ENGINEER_PROCESSED", "Engineer Processed"
    ADMIN_APPROVED = "ADMIN_APPROVED", "Admin Approved"
    DIRECTOR_APPROVED = "DIRECTOR_APPROVED", "Director Approved"
    DEAN_PROCESSED = "DEAN_PROCESSED", "Dean Processed"
    WORK_ORDER_ISSUED = "WORK_ORDER_ISSUED", "Work Order Issued"
    WORK_COMPLETED = "WORK_COMPLETED", "Work Completed"
    BILL_GENERATED = "BILL_GENERATED", "Bill Generated"
    BILL_PROCESSED = "BILL_PROCESSED", "Bill Processed"
    BILL_SETTLED = "BILL_SETTLED", "Bill Settled"


class ProposalStatus(models.TextChoices):
    PENDING = "Pending", "Pending"
    APPROVED = "Approved", "Approved"
    REJECTED = "Rejected", "Rejected"


class BillType(models.IntegerChoices):
    PARTIAL = 0, "Partial"
    FINAL = 1, "Final"


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        self.is_active = False
        self.save()


class Request(BaseModel):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=1000)
    area = models.CharField(max_length=200)
    requestCreatedBy = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_requests", db_index=True)
    status = models.CharField(max_length=50, choices=RequestStatus.choices, default=RequestStatus.CREATED)
    activeProposal = models.IntegerField(null=True, blank=True)


class WorkOrder(BaseModel):
    request = models.ForeignKey(Request, on_delete=models.CASCADE, db_index=True)
    name = models.CharField(max_length=200)
    date = models.DateField(default=date.today)
    estimate_budget = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    alloted_time = models.CharField(max_length=200)
    start_date = models.DateField()
    completion_date = models.DateField(null=True, blank=True)
    work_issuer = models.CharField(max_length=200)
    amount_spent = models.DecimalField(default=0, max_digits=10, decimal_places=2)


class Vendor(BaseModel):
    work = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, db_index=True)
    name = models.CharField(max_length=200)
    itemdata = models.FileField(null=True, blank=True, upload_to='iwd/vendors/')
    finalbill = models.BooleanField(default=False)
    total_amount = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    email_address = models.CharField(null=True, blank=True, max_length=200)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["work", "name"], name="unique_vendor_per_work")
        ]


class Bills(BaseModel):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, db_index=True)
    file = models.FileField(upload_to='iwd/bills/', null=True, blank=True)
    audit = models.BooleanField(default=False)
    settle = models.BooleanField(default=False)
    total_amount = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    billtype = models.IntegerField(choices=BillType.choices, default=BillType.PARTIAL)

    def clean(self):
        if self.billtype == BillType.FINAL:
            exists = Bills.objects.filter(vendor=self.vendor, billtype=BillType.FINAL).exclude(id=self.id).exists()
            if exists:
                raise ValueError("Final bill already exists for this vendor.")


class BillItems(BaseModel):
    bill = models.ForeignKey(Bills, on_delete=models.CASCADE, db_index=True)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=100)
    quantity = models.IntegerField(default=0)
    price = models.DecimalField(default=0, max_digits=10, decimal_places=2)


class Budget(BaseModel):
    request = models.ForeignKey(Request, on_delete=models.CASCADE, db_index=True)
    name = models.CharField(max_length=200)
    budgetIssued = models.BooleanField(default=False)


class Proposal(BaseModel):
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='proposals', db_index=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    proposal_budget = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    supporting_documents = models.FileField(upload_to='iwd/proposals/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=ProposalStatus.choices, default=ProposalStatus.PENDING)


class Item(BaseModel):
    proposal = models.ForeignKey('Proposal', on_delete=models.CASCADE, related_name='items', db_index=True)
    name = models.CharField(default=" ", max_length=255)
    description = models.TextField(default=" ")
    unit = models.CharField(default=" ", max_length=50)
    price_per_unit = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=0)
    total_price = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    docs = models.FileField(upload_to='iwd/items/', null=True, blank=True)

    def save(self, *args, **kwargs):
        self.total_price = self.price_per_unit * self.quantity
        super().save(*args, **kwargs)