from django.contrib import admin

from .models import BillItems
from .models import Bills
from .models import Budget
from .models import Item
from .models import Proposal
from .models import Requests
from .models import Vendor
from .models import WorkOrder


@admin.register(Requests)
class RequestsAdmin(admin.ModelAdmin):
	list_display = ("id", "name", "requestCreatedBy", "status", "creationTime")
	list_filter = ("iwdAdminApproval", "directorApproval", "deanProcessed", "issuedWorkOrder")
	search_fields = ("name", "area", "requestCreatedBy")


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
	list_display = ("id", "request", "created_by", "proposal_budget", "status", "created_at")
	list_filter = ("status",)
	search_fields = ("created_by",)


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
	list_display = ("id", "proposal", "name", "quantity", "price_per_unit", "total_price")
	search_fields = ("name",)


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
	list_display = ("id", "request_id", "name", "estimate_budget", "start_date", "completion_date")
	search_fields = ("name", "work_issuer")


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
	list_display = ("id", "work", "name", "contact_number", "email_address", "total_amount")
	search_fields = ("name", "contact_number", "email_address")


@admin.register(Bills)
class BillsAdmin(admin.ModelAdmin):
	list_display = ("id", "vendor", "audit", "settle", "total_amount", "billtype")
	list_filter = ("audit", "settle", "billtype")


@admin.register(BillItems)
class BillItemsAdmin(admin.ModelAdmin):
	list_display = ("id", "bill", "name", "quantity", "price")
	search_fields = ("name",)


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
	list_display = ("id", "name", "budgetIssued")
	search_fields = ("name",)
