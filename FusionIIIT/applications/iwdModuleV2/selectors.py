"""Read-only query helpers for iwdModuleV2.

Keep `.objects` usage centralized here so views/services remain thin.
"""

from .models import Bills
from .models import Item
from .models import Proposal
from .models import Requests
from .models import Vendor
from .models import WorkOrder


def get_request_by_id(request_id):
    return Requests.objects.filter(id=request_id).first()


def list_requests_for_status(**filters):
    return Requests.objects.filter(**filters).order_by("-creationTime")


def list_director_approved_pending_work_orders():
    return Requests.objects.filter(directorApproval=1, issuedWorkOrder=0).order_by("-creationTime")


def get_active_proposal_for_request(request_obj):
    if not request_obj or not request_obj.activeProposal:
        return None
    return Proposal.objects.filter(id=request_obj.activeProposal).first()


def list_items_for_proposal(proposal_id):
    return Item.objects.filter(proposal=proposal_id).order_by("id")


def list_vendors_for_work_order(work_order_id):
    return Vendor.objects.filter(work=work_order_id).order_by("-id")


def get_latest_bill_for_request(request_id):
    return Bills.objects.filter(vendor__work__request_id=request_id).order_by("-id").first()


def get_work_order_by_request(request_id):
    return WorkOrder.objects.filter(request_id=request_id).first()
