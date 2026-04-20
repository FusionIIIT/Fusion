from django.db import models
from datetime import date, timedelta
from django.utils import timezone
from decimal import Decimal


# Sequential approval chain constants
BUDGET_THRESHOLD_IWD_ADMIN = Decimal("25000.00")  # Reference threshold (legacy)
BUDGET_THRESHOLD_HOD = Decimal("250000.00")      # Reference threshold (legacy)
# All budgets now follow sequential approval: IWD Admin → HOD/Dean → Director


class Requests(models.Model):
	"""
	Main request model for IWD Module.
	
	Sequential approval routing rules (ALL budgets):
	- Step 1: IWD Admin approves (always required)
	- Step 2: HOD/Dean approves (always required)
	- Step 3: Director approves (always required)
	- Only after all three approve can work proceed
	"""
	name = models.CharField(max_length=200)
	description = models.CharField(max_length=1000)
	area = models.CharField(max_length=200)
	requestCreatedBy = models.CharField(max_length=200)
	engineerProcessed = models.IntegerField(default=0)
	iwdAdminApproval = models.IntegerField(default=0)
	directorApproval = models.IntegerField(default=0)
	deanProcessed = models.IntegerField(default=0)  # HOD/Dean approval
	status = models.CharField(max_length=200)
	issuedWorkOrder = models.IntegerField(default=0)
	workCompleted = models.IntegerField(default=0)
	billGenerated = models.IntegerField(default=0)
	billProcessed = models.IntegerField(default=0)
	billSettled = models.IntegerField(default=0)
	activeProposal = models.IntegerField(null = True)
	creationTime = models.DateTimeField(auto_now_add=True, null=True, blank=True)
	
	# SLA & Timeout tracking
	estimated_budget = models.DecimalField(
		max_digits=15, 
		decimal_places=2, 
		null=True, 
		blank=True,
		help_text="Estimated budget from engineer's proposal"
	)
	isPriority = models.BooleanField(default=False, help_text="Escalated/urgent request")
	iwdAdminApprovalDeadline = models.DateTimeField(
		null=True, 
		blank=True,
		help_text="SLA deadline for IWD Admin approval"
	)
	hodApprovalDeadline = models.DateTimeField(
		null=True, 
		blank=True,
		help_text="SLA deadline for HOD/Dean approval"
	)
	directorApprovalDeadline = models.DateTimeField(
		null=True, 
		blank=True,
		help_text="SLA deadline for Director approval"
	)
	nextApprover = models.CharField(
		max_length=100, 
		default="IWD Admin",
		help_text="Next role in approval chain based on budget"
	)

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


# ===== INVENTORY MODELS (UC-30, BR-022, WF-08) =====

class InventoryItem(models.Model):
	"""
	Tracks stock items managed by IWD-Admin.
	
	From Problem Statement: "The IWD-Admin manages inventory, ensuring essential
	materials and tools are available for engineers. They monitor stock levels
	before approving purchases, maintain an audit trail of inventory movements,
	and track the usage of purchased materials."
	"""
	name = models.CharField(max_length=255)
	description = models.TextField(blank=True, default="")
	unit = models.CharField(max_length=50, help_text="e.g., pieces, kg, meters")
	quantity_available = models.IntegerField(default=0, help_text="Current stock level")
	reorder_level = models.IntegerField(
		default=10,
		help_text="Minimum stock level before procurement is triggered"
	)
	location = models.CharField(
		max_length=200,
		blank=True,
		default="",
		help_text="Storage location (e.g., Electrical Store, Civil Store)"
	)
	last_updated = models.DateTimeField(auto_now=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"{self.name} ({self.quantity_available} {self.unit})"

	@property
	def is_low_stock(self):
		return self.quantity_available <= self.reorder_level

	@property
	def needs_procurement(self):
		return self.quantity_available <= 0


class InventoryTransaction(models.Model):
	"""
	Logs every inventory movement — issue, receipt, or adjustment.
	Maintains audit trail as required by the problem statement.
	"""
	TRANSACTION_TYPES = [
		('issue', 'Issue'),
		('receipt', 'Receipt'),
		('adjustment', 'Adjustment'),
	]

	item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='transactions')
	transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
	quantity = models.IntegerField(help_text="Positive for receipt, negative for issue")
	request = models.ForeignKey(
		Requests, on_delete=models.SET_NULL,
		null=True, blank=True,
		help_text="IWD request this transaction is associated with"
	)
	performed_by = models.CharField(max_length=200)
	remarks = models.TextField(blank=True, default="")
	timestamp = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"{self.transaction_type}: {self.item.name} x{self.quantity}"


# ===== FEEDBACK MODEL (UC-31, BR-024, WF-10) =====

class Feedback(models.Model):
	"""
	Post-completion feedback from campus employees.
	
	From Problem Statement: "The module includes real-time tracking and feedback
	collection, allowing campus employees to rate the resolution process and
	report any post-repair issues."
	
	BR-024: Post-repair feedback can reopen a case.
	"""
	RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

	request = models.ForeignKey(Requests, on_delete=models.CASCADE, related_name='feedbacks')
	submitted_by = models.CharField(max_length=200)
	rating = models.IntegerField(
		choices=RATING_CHOICES,
		help_text="1 (Poor) to 5 (Excellent)"
	)
	comments = models.TextField(blank=True, default="")
	created_at = models.DateTimeField(auto_now_add=True)
	reopened = models.BooleanField(
		default=False,
		help_text="True if this feedback triggered a reopen"
	)

	def __str__(self):
		return f"Feedback for Request {self.request_id} by {self.submitted_by} - {self.rating}/5"


# ===== SLA ESCALATION MODEL (UC-29, BR-023, WF-09) =====

class SLAEscalation(models.Model):
	"""
	Records SLA escalation events.
	
	From Problem Statement: "The module integrates an escalation mechanism for
	urgent repairs, allowing engineers to flag critical issues (e.g., electrical
	failures, plumbing breakdowns) for fast-track approval by department heads
	or the director."
	"""
	request = models.ForeignKey(Requests, on_delete=models.CASCADE, related_name='escalations')
	escalated_from = models.CharField(
		max_length=100,
		help_text="Role that missed the SLA deadline"
	)
	escalated_to = models.CharField(
		max_length=100,
		help_text="Role the request is escalated to"
	)
	reason = models.TextField(help_text="Reason for escalation")
	created_at = models.DateTimeField(auto_now_add=True)
	resolved = models.BooleanField(default=False)

	def __str__(self):
		return f"Escalation: Request {self.request_id} from {self.escalated_from} to {self.escalated_to}"

