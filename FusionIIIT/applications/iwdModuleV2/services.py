"""Write-oriented business logic for iwdModuleV2."""

from decimal import Decimal
from decimal import InvalidOperation
from datetime import date, timedelta
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .models import Budget, Requests, WorkOrder, Proposal, Item, Vendor, Bills
from .models import BUDGET_THRESHOLD_IWD_ADMIN, BUDGET_THRESHOLD_HOD
from .selectors import get_latest_bill_for_request, get_request_by_id


# ===== SLA CONSTANTS =====
# SLA deadlines based on priority and budget
SLA_NORMAL_IWD_ADMIN = 2  # 2 days for IWD Admin approval
SLA_NORMAL_HOD = 5  # 5 days for HOD approval
SLA_NORMAL_DIRECTOR = 7  # 7 days for Director approval

SLA_PRIORITY_IWD_ADMIN = 1  # 1 day for urgent IWD Admin
SLA_PRIORITY_HOD = 2  # 2 days for urgent HOD
SLA_PRIORITY_DIRECTOR = 3  # 3 days for urgent Director


# ===== EXCEPTIONS =====
class ServiceError(Exception):
    """Base exception for service-level errors."""


class NotFoundError(ServiceError):
    """Raised when a requested entity is missing."""


class ValidationError(ServiceError):
    """Raised for invalid function inputs."""


class WorkflowError(ServiceError):
    """Raised when workflow preconditions are not satisfied."""


class SLAViolationError(ServiceError):
    """Raised when SLA deadline has passed."""


# ===== VALIDATION HELPERS =====
def _to_non_negative_decimal(value, field_name):
    """Convert and validate a non-negative decimal value."""
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError(f"{field_name} must be a valid decimal value")
    if parsed < 0:
        raise ValidationError(f"{field_name} must be non-negative")
    return parsed


def _validate_date_sequence(start_date, end_date, field_names=("start_date", "end_date")):
    """Validate that start_date <= end_date."""
    if start_date and end_date and start_date > end_date:
        raise ValidationError(
            f"{field_names[1]} ({end_date}) must be on or after {field_names[0]} ({start_date})"
        )


def _validate_positive_decimal(value, field_name):
    """Convert and validate a positive (> 0) decimal value."""
    validated = _to_non_negative_decimal(value, field_name)
    if validated <= 0:
        raise ValidationError(f"{field_name} must be greater than 0")
    return validated


def _validate_positive_integer(value, field_name):
    """Validate a positive integer."""
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field_name} must be a valid integer")
    if parsed <= 0:
        raise ValidationError(f"{field_name} must be greater than 0")
    return parsed


def _validate_string_field(value, field_name, max_length=None):
    """Validate a required string field."""
    if not value or not str(value).strip():
        raise ValidationError(f"{field_name} is required")
    stripped = str(value).strip()
    if max_length and len(stripped) > max_length:
        raise ValidationError(f"{field_name} must not exceed {max_length} characters")
    return stripped


def paginate_queryset(queryset, page_number, page_size=20):
    """Paginate a queryset. Returns (items, total_count, current_page, total_pages)."""
    if page_size < 1:
        raise ValidationError("page_size must be at least 1")
    paginator = Paginator(queryset, page_size)
    try:
        page_num = int(page_number) if page_number else 1
    except (ValueError, TypeError):
        page_num = 1
    
    try:
        page_obj = paginator.page(page_num)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    return (
        list(page_obj.object_list),
        paginator.count,
        page_obj.number,
        paginator.num_pages,
    )


# ===== BUDGET-BASED ROUTING =====
def determine_next_approver(request_id):
    """
    Determine who should approve next based on approval state (not budget).
    
    Sequential approval chain (all budgets follow same path):
    - Step 1: If iwdAdminApproval == 0 → "IWD Admin" (pending)
    - Step 2: If iwdAdminApproval == 1 and deanProcessed == 0 → "HOD" (pending)
    - Step 3: If deanProcessed == 1 and directorApproval == 0 → "Director" (pending)
    - If directorApproval == 1 → "Approved" (all steps complete)
    
    Args:
        request_id: ID of the request
        
    Returns:
        str: "IWD Admin", "HOD", "Director", or "Approved"
        
    Raises:
        NotFoundError: If request not found
    """
    request_obj = get_request_by_id(request_id)
    if not request_obj:
        raise NotFoundError(f"Request {request_id} not found")
    
    # Check approval chain in sequence
    if request_obj.iwdAdminApproval == 0:
        return "IWD Admin"
    elif request_obj.iwdAdminApproval == 1 and request_obj.deanProcessed == 0:
        return "HOD"
    elif request_obj.deanProcessed == 1 and request_obj.directorApproval == 0:
        return "Director"
    elif request_obj.directorApproval == 1:
        return "Approved"
    else:
        # Default fallback (shouldn't reach here in normal flow)
        return "IWD Admin"


def calculate_sla_deadline(is_priority=False, approver_level="IWD Admin"):
    """
    Calculate SLA deadline based on priority and approver level.
    
    Normal SLAs:
    - IWD Admin: 2 days
    - HOD: 5 days
    - Director: 7 days
    
    Priority SLAs (urgent):
    - IWD Admin: 1 day
    - HOD: 2 days
    - Director: 3 days
    
    Args:
        is_priority (bool): Whether this is a priority/urgent request
        approver_level (str): "IWD Admin", "HOD", or "Director"
        
    Returns:
        datetime: Deadline timestamp
        
    Raises:
        ValidationError: If approver_level is invalid
    """
    valid_levels = ["IWD Admin", "HOD", "Director"]
    if approver_level not in valid_levels:
        raise ValidationError(f"approver_level must be one of {valid_levels}")
    
    now = timezone.now()
    
    if is_priority:
        days_map = {
            "IWD Admin": SLA_PRIORITY_IWD_ADMIN,
            "HOD": SLA_PRIORITY_HOD,
            "Director": SLA_PRIORITY_DIRECTOR,
        }
    else:
        days_map = {
            "IWD Admin": SLA_NORMAL_IWD_ADMIN,
            "HOD": SLA_NORMAL_HOD,
            "Director": SLA_NORMAL_DIRECTOR,
        }
    
    days = days_map.get(approver_level, 0)
    return now + timedelta(days=days)


def check_sla_status(deadline):
    """
    Check SLA status for a deadline.
    
    Args:
        deadline (datetime): The SLA deadline
        
    Returns:
        dict: {
            "status": "pending" | "due_soon" | "overdue",
            "days_remaining": int,
            "exceeded": bool
        }
    """
    if not deadline:
        return {"status": "no_deadline", "days_remaining": None, "exceeded": False}
    
    now = timezone.now()
    time_delta = deadline - now
    days_remaining = time_delta.days
    
    if days_remaining < 0:
        return {"status": "overdue", "days_remaining": days_remaining, "exceeded": True}
    elif days_remaining <= 1:
        return {"status": "due_soon", "days_remaining": days_remaining, "exceeded": False}
    else:
        return {"status": "pending", "days_remaining": days_remaining, "exceeded": False}


# ===== REQUEST MANAGEMENT =====
def create_request_with_file(name, description, area, request_created_by, uploader_designation):
    """Create a new IWD request."""
    name = _validate_string_field(name, "name", max_length=200)
    description = _validate_string_field(description, "description", max_length=1000)
    area = _validate_string_field(area, "area", max_length=200)
    request_created_by = _validate_string_field(request_created_by, "requestCreatedBy", max_length=200)
    uploader_designation = _validate_string_field(uploader_designation, "uploader_designation", max_length=200)
    
    request_obj = Requests.objects.create(
        name=name,
        description=description,
        area=area,
        requestCreatedBy=request_created_by,
        status="Created",
        iwdAdminApproval=0,
        directorApproval=0,
    )
    return request_obj


def update_request_status(request_id, new_status, **field_updates):
    """Update request status and optional other fields."""
    request_obj = get_request_by_id(request_id)
    if not request_obj:
        raise NotFoundError(f"Request {request_id} not found")
    
    if new_status and not str(new_status).strip():
        raise ValidationError("Status cannot be empty")
    
    update_fields = ["status"] if new_status else []
    if new_status:
        request_obj.status = new_status
    
    for field_name, value in field_updates.items():
        if hasattr(request_obj, field_name):
            setattr(request_obj, field_name, value)
            update_fields.append(field_name)
        else:
            raise ValidationError(f"Request has no field '{field_name}'")
    
    if update_fields:
        request_obj.save(update_fields=update_fields)
    
    return request_obj


def reject_request(request_id, revert_admin_approval=True):
    """Reject a request and optionally revert admin approval."""
    request_obj = get_request_by_id(request_id)
    if not request_obj:
        raise NotFoundError(f"Request {request_id} not found")
    
    updates = {
        "directorApproval": -1,
        "status": "Rejected by the director",
        "activeProposal": None,
    }
    if revert_admin_approval:
        updates["iwdAdminApproval"] = 0
    
    Requests.objects.filter(id=request_id).update(**updates)
    request_obj.refresh_from_db()
    return request_obj


# ===== PROPOSAL MANAGEMENT =====
def create_proposal(request_id, created_by):
    """Create a new proposal for a request."""
    request_obj = get_request_by_id(request_id)
    if not request_obj:
        raise NotFoundError(f"Request {request_id} not found")
    
    created_by = _validate_string_field(created_by, "created_by")
    
    proposal = Proposal.objects.create(
        request=request_obj,
        created_by=created_by,
        status="Pending",
    )
    return proposal


def add_items_to_proposal(proposal_id, items_data):
    """Add multiple line items to a proposal and calculate total budget."""
    proposal = Proposal.objects.filter(id=proposal_id).first()
    if not proposal:
        raise NotFoundError(f"Proposal {proposal_id} not found")
    
    if not items_data:
        raise ValidationError("At least one item is required")
    
    total_budget = Decimal("0.00")
    created_items = []
    
    for item_data in items_data:
        name = _validate_string_field(item_data.get("name"), "item.name")
        description = _validate_string_field(item_data.get("description"), "item.description")
        unit = _validate_string_field(item_data.get("unit"), "item.unit")
        quantity = _validate_positive_integer(item_data.get("quantity"), "item.quantity")
        price_per_unit = _validate_positive_decimal(item_data.get("price_per_unit"), "item.price_per_unit")
        
        total_price = Decimal(quantity) * price_per_unit
        total_budget += total_price
        
        item = Item.objects.create(
            proposal=proposal,
            name=name,
            description=description,
            unit=unit,
            quantity=quantity,
            price_per_unit=price_per_unit,
            total_price=total_price,
            docs=item_data.get("docs"),
        )
        created_items.append(item)
    
    proposal.proposal_budget = total_budget
    proposal.save(update_fields=["proposal_budget"])
    
    return proposal, created_items


def deactivate_previous_proposals(request_id, new_proposal_id):
    """Deactivate all previous proposals for a request when a new one is activated."""
    request_obj = get_request_by_id(request_id)
    if not request_obj:
        raise NotFoundError(f"Request {request_id} not found")
    
    # Mark all other proposals as rejected
    Proposal.objects.filter(request=request_obj).exclude(id=new_proposal_id).update(status="Rejected")
    
    # Set the new proposal as active
    Requests.objects.filter(id=request_id).update(activeProposal=new_proposal_id)
    request_obj.refresh_from_db()
    return request_obj


def finalize_proposal_and_set_routing(request_id, proposal_id, is_priority=False):
    """
    Finalize proposal, set estimated_budget on request, and route to correct approver.
    This should be called after items have been added to the proposal.
    
    Args:
        request_id: ID of the request
        proposal_id: ID of the proposal
        is_priority: Whether this is a priority/urgent request
        
    Returns:
        Requests: Updated request object
        
    Raises:
        NotFoundError: If request or proposal not found
    """
    request_obj = get_request_by_id(request_id)
    if not request_obj:
        raise NotFoundError(f"Request {request_id} not found")
    
    proposal = Proposal.objects.filter(id=proposal_id).first()
    if not proposal:
        raise NotFoundError(f"Proposal {proposal_id} not found")
    
    if proposal.request_id != request_id:
        raise ValidationError("Proposal does not belong to this request")
    
    # Set estimated budget on request
    estimated_budget = proposal.proposal_budget
    request_obj.estimated_budget = estimated_budget
    request_obj.isPriority = is_priority
    
    # Sequential approval: ALL requests go IWD Admin → HOD → Director
    # Set all three SLA deadlines upfront regardless of budget
    request_obj.iwdAdminApprovalDeadline = calculate_sla_deadline(is_priority, "IWD Admin")
    request_obj.hodApprovalDeadline = calculate_sla_deadline(is_priority, "HOD")
    request_obj.directorApprovalDeadline = calculate_sla_deadline(is_priority, "Director")
    
    # Next approver is always IWD Admin (first step in sequential chain)
    request_obj.nextApprover = "IWD Admin"
    
    request_obj.save(update_fields=[
        'estimated_budget', 'isPriority', 'nextApprover',
        'iwdAdminApprovalDeadline', 'hodApprovalDeadline', 'directorApprovalDeadline'
    ])
    
    return request_obj


# ===== APPROVAL VALIDATION & ENFORCEMENT =====
def validate_iwd_admin_approval(request_id):
    """
    Validate that a request can be approved by IWD Admin (first step in sequential chain).
    Checks: iwdAdminApproval == 0 (not yet approved by IWD Admin)
    
    Args:
        request_id: ID of the request
        
    Returns:
        dict: {"valid": bool, "approver": str, "message": str}
        
    Raises:
        NotFoundError: If request not found
    """
    request_obj = get_request_by_id(request_id)
    if not request_obj:
        raise NotFoundError(f"Request {request_id} not found")
    
    proposal_id = request_obj.activeProposal

    if not proposal_id:
        return {
            "valid": False,
            "approver": "IWD Admin",
            "message": "No active proposal found"
        }

    proposal = Proposal.objects.filter(id=proposal_id).first()

    if not proposal:
        return {
            "valid": False,
            "approver": "IWD Admin",
            "message": "Invalid proposal"
        }

    if proposal.proposal_budget is None:
        return {
            "valid": False,
            "approver": "IWD Admin",
            "message": "Proposal budget not set"
        }

    budget = proposal.proposal_budget
    
    # IWD Admin can only approve if they haven't yet (state == 0)
    if request_obj.iwdAdminApproval != 0:
        return {
            "valid": False,
            "approver": "IWD Admin",
            "message": f"IWD Admin approval already done (status={request_obj.iwdAdminApproval}). Request is at next step."
        }
    
    return {
        "valid": True,
        "approver": "IWD Admin",
        "message": f"IWD Admin can approve this request (Step 1/3). Budget: Rs {budget}"
    }


def validate_hod_approval(request_id):
    """
    Validate that a request can be approved by HOD (second step in sequential chain).
    Checks: iwdAdminApproval == 1 (already approved by IWD Admin) AND deanProcessed == 0 (not yet by HOD/Dean)
    
    Args:
        request_id: ID of the request
        
    Returns:
        dict: {"valid": bool, "approver": str, "message": str}
        
    Raises:
        NotFoundError: If request not found
    """
    request_obj = get_request_by_id(request_id)
    if not request_obj:
        raise NotFoundError(f"Request {request_id} not found")
    
    if not request_obj.estimated_budget:
        return {
            "valid": False,
            "approver": "HOD",
            "message": "Estimated budget not set on request"
        }
    
    # HOD can only approve if IWD Admin has approved (iwdAdminApproval == 1)
    if request_obj.iwdAdminApproval != 1:
        return {
            "valid": False,
            "approver": "HOD",
            "message": f"IWD Admin has not approved yet (status={request_obj.iwdAdminApproval}). HOD approval is blocked until Step 1 is complete."
        }
    
    # HOD can only approve if they haven't yet (deanProcessed == 0)
    if request_obj.deanProcessed != 0:
        return {
            "valid": False,
            "approver": "HOD",
            "message": f"HOD/Dean approval already done (status={request_obj.deanProcessed}). Request is at next step."
        }
    
    return {
        "valid": True,
        "approver": "HOD",
        "message": f"HOD can approve this request (Step 2/3). Budget: Rs {request_obj.estimated_budget}"
    }


def validate_director_approval(request_id):
    """
    Validate that a request can be approved by Director (third step in sequential chain).
    Checks: deanProcessed == 1 (already approved by HOD/Dean) AND directorApproval == 0 (not yet by Director)
    
    Args:
        request_id: ID of the request
        
    Returns:
        dict: {"valid": bool, "approver": str, "message": str}
        
    Raises:
        NotFoundError: If request not found
    """
    request_obj = get_request_by_id(request_id)
    if not request_obj:
        raise NotFoundError(f"Request {request_id} not found")
    
    if not request_obj.estimated_budget:
        return {
            "valid": False,
            "approver": "Director",
            "message": "Estimated budget not set on request"
        }
    
    # Director can only approve if HOD/Dean has approved (deanProcessed == 1)
    if request_obj.deanProcessed != 1:
        return {
            "valid": False,
            "approver": "Director",
            "message": f"HOD/Dean has not approved yet (status={request_obj.deanProcessed}). Director approval is blocked until Step 2 is complete."
        }
    
    # Director can only approve if they haven't yet (directorApproval == 0)
    if request_obj.directorApproval != 0:
        return {
            "valid": False,
            "approver": "Director",
            "message": f"Director approval already done (status={request_obj.directorApproval}). All approvals are complete."
        }
    
    return {
        "valid": True,
        "approver": "Director",
        "message": f"Director can approve this request (Step 3/3). Budget: Rs {request_obj.estimated_budget}"
    }


def validate_approver_can_approve(request_id, approver_role):
    """
    Generic validation to check if an approver role can approve a request.
    
    Args:
        request_id: ID of the request
        approver_role: "IWD Admin", "HOD", or "Director"
        
    Returns:
        dict: {"valid": bool, "approver": str, "message": str}
        
    Raises:
        ValidationError: If approver_role is invalid
    """
    if approver_role == "IWD Admin":
        return validate_iwd_admin_approval(request_id)
    elif approver_role == "HOD":
        return validate_hod_approval(request_id)
    elif approver_role == "Director":
        return validate_director_approval(request_id)
    else:
        raise ValidationError(f"Invalid approver_role: {approver_role}")


# ===== WORK ORDER MANAGEMENT =====
def issue_work_order(request_id, work_issuer, name, start_date, completion_date=None, 
                     alloted_time=None, estimate_budget=None):
    """Issue a work order for an approved request."""
    request_obj = get_request_by_id(request_id)
    if not request_obj:
        raise NotFoundError(f"Request {request_id} not found")
    
    if request_obj.directorApproval != 1:
        raise WorkflowError("Director approval is required to issue a work order")
    
    if request_obj.issuedWorkOrder == 1:
        raise WorkflowError("Work order already issued for this request")
    
    work_issuer = _validate_string_field(work_issuer, "work_issuer")
    name = _validate_string_field(name, "name")
    
    # Validate dates
    start_date_obj = start_date if isinstance(start_date, date) else start_date
    if completion_date:
        completion_date_obj = completion_date if isinstance(completion_date, date) else completion_date
        _validate_date_sequence(start_date_obj, completion_date_obj, ("start_date", "completion_date"))
    
    # Use active proposal budget if estimate not provided
    if estimate_budget is None and request_obj.activeProposal:
        proposal = Proposal.objects.filter(id=request_obj.activeProposal).first()
        estimate_budget = proposal.proposal_budget if proposal else Decimal("0.00")
    else:
        estimate_budget = _to_non_negative_decimal(estimate_budget or 0, "estimate_budget")
    
    work_order = WorkOrder.objects.create(
        request_id=request_obj,
        name=name,
        work_issuer=work_issuer,
        start_date=start_date_obj,
        completion_date=completion_date,
        alloted_time=alloted_time or "",
        estimate_budget=estimate_budget,
    )
    
    # Update request
    Requests.objects.filter(id=request_id).update(
        issuedWorkOrder=1,
        status="Work Order issued"
    )
    
    return work_order


def mark_work_completed(request_id):
    """Mark work as completed."""
    request_obj = get_request_by_id(request_id)
    if not request_obj:
        raise NotFoundError(f"Request {request_id} not found")
    
    if request_obj.issuedWorkOrder != 1:
        raise WorkflowError("Work order must be issued before marking complete")
    
    request_obj.workCompleted = 1
    request_obj.status = "Work Completed"
    request_obj.save(update_fields=["workCompleted", "status"])
    return request_obj


# ===== VENDOR MANAGEMENT =====
def add_vendor_to_work_order(work_order_id, name, contact_number=None, email_address=None, 
                               total_amount=None):
    """Add a vendor to a work order."""
    work_order = WorkOrder.objects.filter(id=work_order_id).first()
    if not work_order:
        raise NotFoundError(f"Work order {work_order_id} not found")
    
    name = _validate_string_field(name, "name", max_length=200)
    total_amount = _to_non_negative_decimal(total_amount or 0, "total_amount")
    
    vendor = Vendor.objects.create(
        work=work_order,
        name=name,
        contact_number=contact_number or "",
        email_address=email_address or "",
        total_amount=total_amount,
    )
    return vendor


# ===== BILL MANAGEMENT =====
def record_bill_generated(request_id):
    """Mark bill as generated."""
    request_obj = get_request_by_id(request_id)
    if not request_obj:
        raise NotFoundError(f"Request {request_id} not found")
    
    if request_obj.workCompleted != 1:
        raise WorkflowError("Work must be completed before generating bill")
    
    request_obj.billGenerated = 1
    request_obj.status = "Bill Generated"
    request_obj.save(update_fields=["billGenerated", "status"])
    return request_obj


def process_bill(request_id, vendor_id=None, bill_file=None):
    """Process/submit a bill for audit."""
    request_obj = get_request_by_id(request_id)
    if not request_obj:
        raise NotFoundError(f"Request {request_id} not found")
    
    if request_obj.workCompleted != 1:
        raise WorkflowError("Work must be completed before processing bill")
    
    # Find vendor
    work_order = WorkOrder.objects.filter(request_id=request_id).first()
    if not work_order:
        raise NotFoundError(f"No work order found for request {request_id}")
    
    vendor = None
    if vendor_id:
        vendor = Vendor.objects.filter(id=vendor_id, work=work_order).first()
    if not vendor:
        vendor = Vendor.objects.filter(work=work_order).order_by('-id').first()
    if not vendor:
        raise NotFoundError(f"No vendor found for work order")
    
    # Create bill
    bill = Bills.objects.create(
        vendor=vendor,
        file=bill_file,
        total_amount=vendor.total_amount,
    )
    
    # Update request
    Requests.objects.filter(id=request_id).update(
        billProcessed=1,
        status="Final Bill Processed"
    )
    
    return bill


def mark_bill_audited(request_id):
    """Mark bill as audited."""
    request_obj = get_request_by_id(request_id)
    if not request_obj:
        raise NotFoundError(f"Request {request_id} not found")
    
    latest_bill = get_latest_bill_for_request(request_id)
    if not latest_bill:
        raise WorkflowError("No bill found for request")
    
    if request_obj.billProcessed != 1:
        raise WorkflowError("Bill must be processed before audit")
    
    latest_bill.audit = True
    latest_bill.save(update_fields=["audit"])
    
    request_obj.status = "Bill Audited"
    request_obj.save(update_fields=["status"])
    return request_obj


def settle_bill(request_id):
    """Settle/complete the final bill."""
    request_obj = get_request_by_id(request_id)
    if not request_obj:
        raise NotFoundError(f"Request {request_id} not found")
    
    latest_bill = get_latest_bill_for_request(request_id)
    if not latest_bill:
        raise WorkflowError("No bill found for request")
    
    if not latest_bill.audit:
        raise WorkflowError("Bill must be audited before settlement")
    
    if request_obj.status != "Bill Audited":
        raise WorkflowError("Request status must be 'Bill Audited' before settlement")
    
    latest_bill.settle = True
    latest_bill.save(update_fields=["settle"])
    
    request_obj.billSettled = 1
    request_obj.status = "Final Bill Settled"
    request_obj.save(update_fields=["billSettled", "status"])
    return request_obj


# ===== BUDGET MANAGEMENT =====
def create_budget(name, amount):
    """Create a new budget allocation."""
    name = _validate_string_field(name, "name", max_length=200)
    amount = _validate_positive_decimal(amount, "budgetIssued")
    
    budget = Budget.objects.create(name=name, budgetIssued=amount)
    return budget


def update_budget(budget_id, name=None, amount=None):
    """Update an existing budget."""
    budget_obj = Budget.objects.filter(id=budget_id).first()
    if not budget_obj:
        raise NotFoundError(f"Budget {budget_id} not found")
    
    update_fields = []
    if name is not None:
        budget_obj.name = _validate_string_field(name, "name", max_length=200)
        update_fields.append("name")
    
    if amount is not None:
        budget_obj.budgetIssued = _validate_positive_decimal(amount, "budgetIssued")
        update_fields.append("budgetIssued")
    
    if update_fields:
        budget_obj.save(update_fields=update_fields)
    
    return budget_obj


def delete_budget(budget_id):
    """Delete a budget allocation."""
    budget_obj = Budget.objects.filter(id=budget_id).first()
    if not budget_obj:
        raise NotFoundError(f"Budget {budget_id} not found")
    
    budget_obj.delete()
    return True


# ===== INVENTORY MANAGEMENT (UC-30, BR-022, WF-08) =====

def check_stock(item_id):
    """
    Check stock level for an inventory item.
    
    BR-022: Stock must be checked/issued before procurement is triggered.
    
    Args:
        item_id: ID of the InventoryItem
        
    Returns:
        dict: {
            "item_id": int,
            "name": str,
            "quantity_available": int,
            "reorder_level": int,
            "is_low_stock": bool,
            "needs_procurement": bool
        }
        
    Raises:
        NotFoundError: If item not found
    """
    from .models import InventoryItem
    
    item = InventoryItem.objects.filter(id=item_id).first()
    if not item:
        raise NotFoundError(f"Inventory item {item_id} not found")
    
    return {
        "item_id": item.id,
        "name": item.name,
        "quantity_available": item.quantity_available,
        "reorder_level": item.reorder_level,
        "unit": item.unit,
        "location": item.location,
        "is_low_stock": item.is_low_stock,
        "needs_procurement": item.needs_procurement,
    }


def issue_materials(item_id, quantity, performed_by, request_id=None, remarks=""):
    """
    Issue materials from inventory for a request.
    
    Deducts stock and creates an audit trail transaction.
    If stock is unavailable, raises an error (BR-022).
    
    Args:
        item_id: ID of the InventoryItem
        quantity: Number of units to issue (must be > 0)
        performed_by: Username of person issuing
        request_id: Optional IWD request ID this is for
        remarks: Optional notes
        
    Returns:
        tuple: (InventoryItem, InventoryTransaction)
        
    Raises:
        NotFoundError: If item not found
        ValidationError: If quantity invalid
        WorkflowError: If insufficient stock
    """
    from .models import InventoryItem, InventoryTransaction
    
    item = InventoryItem.objects.filter(id=item_id).first()
    if not item:
        raise NotFoundError(f"Inventory item {item_id} not found")
    
    quantity = _validate_positive_integer(quantity, "quantity")
    performed_by = _validate_string_field(performed_by, "performed_by")
    
    if item.quantity_available < quantity:
        raise WorkflowError(
            f"Insufficient stock for {item.name}. "
            f"Available: {item.quantity_available} {item.unit}, Requested: {quantity} {item.unit}"
        )
    
    # Deduct stock
    item.quantity_available -= quantity
    item.save(update_fields=["quantity_available"])
    
    # Create audit trail
    request_obj = None
    if request_id:
        request_obj = get_request_by_id(request_id)
    
    transaction = InventoryTransaction.objects.create(
        item=item,
        transaction_type="issue",
        quantity=-quantity,
        request=request_obj,
        performed_by=performed_by,
        remarks=remarks or f"Issued {quantity} {item.unit} of {item.name}",
    )
    
    return item, transaction


def receive_materials(item_id, quantity, performed_by, remarks=""):
    """
    Receive/add materials to inventory.
    
    Args:
        item_id: ID of the InventoryItem
        quantity: Number of units received (must be > 0)
        performed_by: Username
        remarks: Optional notes
        
    Returns:
        tuple: (InventoryItem, InventoryTransaction)
        
    Raises:
        NotFoundError: If item not found
        ValidationError: If quantity invalid
    """
    from .models import InventoryItem, InventoryTransaction
    
    item = InventoryItem.objects.filter(id=item_id).first()
    if not item:
        raise NotFoundError(f"Inventory item {item_id} not found")
    
    quantity = _validate_positive_integer(quantity, "quantity")
    performed_by = _validate_string_field(performed_by, "performed_by")
    
    # Add stock
    item.quantity_available += quantity
    item.save(update_fields=["quantity_available"])
    
    transaction = InventoryTransaction.objects.create(
        item=item,
        transaction_type="receipt",
        quantity=quantity,
        performed_by=performed_by,
        remarks=remarks or f"Received {quantity} {item.unit} of {item.name}",
    )
    
    return item, transaction


def create_inventory_item(name, description, unit, quantity_available=0,
                          reorder_level=10, location=""):
    """Create a new inventory item."""
    from .models import InventoryItem
    
    name = _validate_string_field(name, "name", max_length=255)
    unit = _validate_string_field(unit, "unit", max_length=50)
    
    if quantity_available is not None:
        try:
            quantity_available = int(quantity_available)
        except (TypeError, ValueError):
            raise ValidationError("quantity_available must be a valid integer")
        if quantity_available < 0:
            raise ValidationError("quantity_available must be non-negative")
    
    item = InventoryItem.objects.create(
        name=name,
        description=description or "",
        unit=unit,
        quantity_available=quantity_available or 0,
        reorder_level=reorder_level or 10,
        location=location or "",
    )
    return item


def get_low_stock_items():
    """
    Get all inventory items at or below reorder level.
    
    Returns:
        QuerySet of InventoryItem objects needing procurement
    """
    from .models import InventoryItem
    from django.db.models import F
    
    return InventoryItem.objects.filter(
        quantity_available__lte=F('reorder_level')
    ).order_by('quantity_available')


# ===== FEEDBACK & CLOSURE (UC-31, BR-024, WF-10) =====

def submit_feedback(request_id, submitted_by, rating, comments=""):
    """
    Submit feedback for a completed/settled request.
    
    BR-024: Post-repair feedback can reopen a case if rating <= 2.
    
    Args:
        request_id: ID of the request
        submitted_by: Username of person submitting
        rating: 1-5 rating
        comments: Optional text feedback
        
    Returns:
        tuple: (Feedback, bool) — feedback object and whether request was reopened
        
    Raises:
        NotFoundError: If request not found
        ValidationError: If rating invalid
        WorkflowError: If request not in completed/settled state
    """
    from .models import Feedback
    
    request_obj = get_request_by_id(request_id)
    if not request_obj:
        raise NotFoundError(f"Request {request_id} not found")
    
    # Request must be in a completed or settled state
    completed_statuses = [
        "Work Completed", "Bill Generated", "Final Bill Processed",
        "Bill Audited", "Final Bill Settled", "Resolved"
    ]
    if request_obj.status not in completed_statuses and request_obj.workCompleted != 1:
        raise WorkflowError(
            f"Feedback can only be submitted for completed requests. "
            f"Current status: {request_obj.status}"
        )
    
    submitted_by = _validate_string_field(submitted_by, "submitted_by")
    
    try:
        rating = int(rating)
    except (TypeError, ValueError):
        raise ValidationError("Rating must be an integer")
    if rating < 1 or rating > 5:
        raise ValidationError("Rating must be between 1 and 5")
    
    # No auto-reopen: reopening is a manual human decision via reopen_request()
    
    feedback = Feedback.objects.create(
        request=request_obj,
        submitted_by=submitted_by,
        rating=rating,
        comments=comments or "",
        reopened=False,
    )
    
    return feedback, False


def reopen_request(request_id, reason=""):
    """
    Manually reopen a completed request.
    
    Args:
        request_id: ID of the request
        reason: Reason for reopening
        
    Returns:
        Requests: Updated request object
        
    Raises:
        NotFoundError: If request not found
        WorkflowError: If request not in completed state
    """
    request_obj = get_request_by_id(request_id)
    if not request_obj:
        raise NotFoundError(f"Request {request_id} not found")
    
    if request_obj.workCompleted != 1:
        raise WorkflowError("Only completed requests can be reopened")
    
    request_obj.status = "Reopened"
    request_obj.workCompleted = 0
    request_obj.billGenerated = 0
    request_obj.billProcessed = 0
    request_obj.billSettled = 0
    request_obj.save(update_fields=[
        "status", "workCompleted", "billGenerated",
        "billProcessed", "billSettled"
    ])
    
    return request_obj


# ===== SLA ENGINE (UC-29, BR-023, WF-09) =====

def check_overdue_requests():
    """
    Find all requests that have passed their SLA deadline.
    
    Returns:
        list of dict: Each with request_id, approver_level, days_overdue, deadline
    """
    now = timezone.now()
    overdue = []
    
    # Check IWD Admin deadlines
    admin_overdue = Requests.objects.filter(
        iwdAdminApprovalDeadline__lt=now,
        iwdAdminApproval=0,
        status__in=["Created", "Pending", "Proposal created"]
    )
    for req in admin_overdue:
        days = (now - req.iwdAdminApprovalDeadline).days
        overdue.append({
            "request_id": req.id,
            "request_name": req.name,
            "approver_level": "IWD Admin",
            "days_overdue": days,
            "deadline": req.iwdAdminApprovalDeadline,
            "is_priority": req.isPriority,
        })
    
    # Check HOD deadlines
    hod_overdue = Requests.objects.filter(
        hodApprovalDeadline__lt=now,
        deanProcessed=0,
        iwdAdminApproval=1,
    )
    for req in hod_overdue:
        days = (now - req.hodApprovalDeadline).days
        overdue.append({
            "request_id": req.id,
            "request_name": req.name,
            "approver_level": "HOD",
            "days_overdue": days,
            "deadline": req.hodApprovalDeadline,
            "is_priority": req.isPriority,
        })
    
    # Check Director deadlines
    director_overdue = Requests.objects.filter(
        directorApprovalDeadline__lt=now,
        directorApproval=0,
        deanProcessed=1,
    )
    for req in director_overdue:
        days = (now - req.directorApprovalDeadline).days
        overdue.append({
            "request_id": req.id,
            "request_name": req.name,
            "approver_level": "Director",
            "days_overdue": days,
            "deadline": req.directorApprovalDeadline,
            "is_priority": req.isPriority,
        })
    
    return sorted(overdue, key=lambda x: x["days_overdue"], reverse=True)


def create_escalation(request_id, escalated_from, escalated_to, reason):
    """
    Create an SLA escalation record.
    
    Args:
        request_id: ID of the request
        escalated_from: Role that missed SLA (e.g., "IWD Admin")
        escalated_to: Role to escalate to (e.g., "Director")
        reason: Reason for escalation
        
    Returns:
        SLAEscalation object
        
    Raises:
        NotFoundError: If request not found
        ValidationError: If fields invalid
    """
    from .models import SLAEscalation
    
    request_obj = get_request_by_id(request_id)
    if not request_obj:
        raise NotFoundError(f"Request {request_id} not found")
    
    escalated_from = _validate_string_field(escalated_from, "escalated_from")
    escalated_to = _validate_string_field(escalated_to, "escalated_to")
    reason = _validate_string_field(reason, "reason")
    
    # Mark request as priority for fast-track
    if not request_obj.isPriority:
        request_obj.isPriority = True
        request_obj.save(update_fields=["isPriority"])
    
    escalation = SLAEscalation.objects.create(
        request=request_obj,
        escalated_from=escalated_from,
        escalated_to=escalated_to,
        reason=reason,
    )
    
    return escalation


def get_sla_dashboard_data():
    """
    Get SLA monitoring dashboard data.
    
    Returns:
        dict: {
            "total_active": int,
            "pending_count": int,
            "due_soon_count": int,
            "overdue_count": int,
            "overdue_requests": list,
            "escalation_count": int,
            "priority_count": int,
        }
    """
    from .models import SLAEscalation
    
    now = timezone.now()
    one_day = now + timedelta(days=1)
    
    # Active requests (not settled/rejected)
    active = Requests.objects.exclude(
        status__in=["Final Bill Settled", "Rejected by the director", "Rejected"]
    )
    total_active = active.count()
    
    # Overdue
    overdue_requests = check_overdue_requests()
    overdue_count = len(overdue_requests)
    
    # Due soon (within 1 day)
    due_soon_count = 0
    due_soon_count += Requests.objects.filter(
        iwdAdminApprovalDeadline__gt=now,
        iwdAdminApprovalDeadline__lte=one_day,
        iwdAdminApproval=0,
    ).count()
    due_soon_count += Requests.objects.filter(
        hodApprovalDeadline__gt=now,
        hodApprovalDeadline__lte=one_day,
        deanProcessed=0,
        iwdAdminApproval=1,
    ).count()
    due_soon_count += Requests.objects.filter(
        directorApprovalDeadline__gt=now,
        directorApprovalDeadline__lte=one_day,
        directorApproval=0,
        deanProcessed=1,
    ).count()
    
    # Pending (has deadline, not overdue, not due soon)
    pending_count = total_active - overdue_count - due_soon_count
    if pending_count < 0:
        pending_count = 0
    
    # Escalations
    escalation_count = SLAEscalation.objects.filter(resolved=False).count()
    
    # Priority requests
    priority_count = Requests.objects.filter(isPriority=True).exclude(
        status__in=["Final Bill Settled", "Rejected by the director", "Rejected"]
    ).count()
    
    return {
        "total_active": total_active,
        "pending_count": pending_count,
        "due_soon_count": due_soon_count,
        "overdue_count": overdue_count,
        "overdue_requests": overdue_requests[:20],  # Top 20 most overdue
        "escalation_count": escalation_count,
        "priority_count": priority_count,
    }

