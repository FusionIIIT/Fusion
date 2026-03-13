from django.db import models
from datetime import date


class Requests(models.Model):
	name = models.CharField(max_length=200)
	description = models.CharField(max_length=1000)
	area = models.CharField(max_length=200)
	requestCreatedBy = models.CharField(max_length=200)
	engineerProcessed = models.IntegerField(default=0)
	iwdAdminApproval = models.IntegerField(default=0)
	directorApproval = models.IntegerField(default=0)
	deanProcessed = models.IntegerField(default=0)
	status = models.CharField(max_length=200)
	issuedWorkOrder = models.IntegerField(default=0)
	workCompleted = models.IntegerField(default=0)
	billGenerated = models.IntegerField(default=0)
	billProcessed = models.IntegerField(default=0)
	billSettled = models.IntegerField(default=0)
	activeProposal = models.IntegerField(null = True)
	creationTime = models.DateTimeField(auto_now_add=True, null=True, blank=True)

class WorkOrder(models.Model):
	request_id = models.ForeignKey(Requests, on_delete=models.CASCADE)
	name = models.CharField(max_length=200)
	date = models.DateField(default=date.today)
	estimate_budget = models.DecimalField(default=0, max_digits=10, decimal_places=2)
	alloted_time = models.CharField(max_length=200)
	start_date = models.DateField()
	completion_date = models.DateField(null=True, blank=True)
	work_issuer = models.CharField(max_length=200, default="")
	amount_spent = models.DecimalField(default = 0, max_digits=10, decimal_places=2)
class Vendor(models.Model):
	'''
		heads up, vendor is not supposed to identify a unique vendor
		primarily it is for storing a set of items purchased from a particular vendor for a particular request
	'''
	work = models.ForeignKey(WorkOrder, on_delete=models.CASCADE)
	name = models.CharField(max_length=200)
	itemdata = models.FileField(null=True, blank=True, upload_to='iwd/vendors/')
	finalbill = models.BooleanField(default=False)
	total_amount = models.DecimalField(default=0, max_digits=10, decimal_places=2)
	contact_number = models.CharField(max_length=20, blank=True, null=True)
	email_address = models.CharField(null=True, blank=True, max_length=200)

class Bills(models.Model):
	vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, null=True, blank=True)
	file = models.FileField(upload_to='iwd/bills/', null=True, blank=True)
	audit = models.BooleanField(default=False)
	settle = models.BooleanField(default=False)
	total_amount = models.DecimalField(default=0, max_digits=10, decimal_places=2)
	'''
		two types of bills are there currently
		1st kind is partial bill (billtype == 0)
		2nd kind is final bill (billtype == 1)
		- once a final bill is uploaded, no more bill uploads for that particular vendor is permitted
	'''
	billtype = models.IntegerField(default=0)
class BillItems(models.Model):
	bill = models.ForeignKey(Bills, on_delete=models.CASCADE)
	name = models.CharField(max_length=100)
	description = models.CharField(max_length=100)
	quantity = models.IntegerField(default=0)
	price = models.DecimalField(default=0, max_digits=10, decimal_places=2)
class Budget(models.Model):
	name = models.CharField(max_length=200)
	budgetIssued = models.IntegerField(default=0)
    
class Proposal(models.Model):
	request = models.ForeignKey(Requests, on_delete=models.CASCADE, related_name='proposals')
	created_by = models.CharField(max_length=200) #models.ForeignKey(User, on_delete=models.CASCADE)
	proposal_budget = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
	supporting_documents = models.FileField(upload_to='iwd/proposals/', null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')], default='Pending')
class Item(models.Model):
	proposal = models.ForeignKey('Proposal', on_delete=models.CASCADE, related_name='items')
	name = models.CharField(default = " ", max_length=255)
	description = models.TextField(default = " ")
	unit = models.CharField(default = " ", max_length=50)
	price_per_unit = models.DecimalField(default = 0, max_digits=10, decimal_places=2)
	quantity = models.IntegerField(default = 0)
	total_price = models.DecimalField(default = 0, max_digits=10, decimal_places=2)
	docs = models.FileField(upload_to='iwd/items/', null=True, blank=True)

