from decimal import Decimal
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from applications.iwdModuleV2.models_iwd import (
    MaintenanceComplaint,
    RepairEstimate,
    InventoryStock,
    MaterialIssueRecord,
    PhysicalVerification,
    FinalBillRecord,
    ComplaintFeedback,
    IWDAuditTrail,
)
from applications.iwdModuleV2.workflow_engine import (
    IWDStates,
    IWDRoles,
    CostBands,
    WorkflowEngine,
)


def log_audit_trail(complaint, user, role, action, prev_state, new_state, remarks=""):
    """BR-IWD-013: Persist actor, action, previous/new state, and remarks."""
    return IWDAuditTrail.objects.create(
        complaint=complaint,
        actor=user if isinstance(user, User) else None,
        actor_role=role,
        action=action,
        previous_state=prev_state,
        new_state=new_state,
        remarks=remarks,
    )


def assign_engineer_automatically(category):
    """
    BR-IWD-002: Automatic engineer assignment using workload distribution and expertise.
    """
    engineers = User.objects.filter(groups__name__icontains="engineer")
    if not engineers.exists():
        engineers = User.objects.filter(is_staff=True)
    if not engineers.exists():
        return None

    # Workload count
    best_engineer = None
    min_workload = None
    for eng in engineers:
        active_count = MaintenanceComplaint.objects.filter(
            assigned_engineer=eng, is_resolved=False
        ).count()
        if min_workload is None or active_count < min_workload:
            min_workload = active_count
            best_engineer = eng

    return best_engineer or engineers.first()


# -------------------------------------------------------------
# UC-IWD-001: Submit Maintenance Complaint (BW-IWD-01)
# -------------------------------------------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def submit_maintenance_complaint(request):
    """
    UC-IWD-001: Submit complaint with category, location, urgency, remarks.
    Automatically assigns engineer (BR-IWD-002).
    """
    category = request.data.get("issue_category", "Civil")
    location = request.data.get("location", "")
    urgency = request.data.get("urgency", "Low")
    remarks = request.data.get("remarks", "")

    if not location:
        return Response({"error": "Location is required."}, status=status.HTTP_400_BAD_REQUEST)

    complaint = MaintenanceComplaint.objects.create(
        requester=request.user,
        issue_category=category,
        location=location,
        urgency=urgency,
        remarks=remarks,
        status=IWDStates.SUBMITTED,
    )
    log_audit_trail(
        complaint, request.user, IWDRoles.INSTITUTE_EMPLOYEE,
        "submit_complaint", IWDStates.NO_COMPLAINT, IWDStates.SUBMITTED, remarks
    )

    # Automatic assignment (BR-IWD-002)
    assigned_eng = assign_engineer_automatically(category)
    if assigned_eng:
        complaint.assigned_engineer = assigned_eng
        complaint.status = IWDStates.ASSIGNED
        complaint.save()
        log_audit_trail(
            complaint, None, IWDRoles.SYSTEM,
            "auto_assign_engineer", IWDStates.SUBMITTED, IWDStates.ASSIGNED,
            f"Automatically assigned to {assigned_eng.username}"
        )

    return Response({
        "message": "Complaint submitted successfully.",
        "complaint_id": complaint.complaint_id,
        "status": complaint.status,
        "assigned_engineer": complaint.assigned_engineer.username if complaint.assigned_engineer else None,
    }, status=status.HTTP_201_CREATED)


# -------------------------------------------------------------
# UC-IWD-005: Track Complaint Status
# -------------------------------------------------------------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def track_complaint_status(request):
    """UC-IWD-005: Track complaints submitted by current user."""
    complaints = MaintenanceComplaint.objects.filter(requester=request.user).order_by("-created_at")
    results = []
    for c in complaints:
        history = [
            {
                "actor": a.actor.username if a.actor else a.actor_role,
                "action": a.action,
                "previous_state": a.previous_state,
                "new_state": a.new_state,
                "timestamp": a.timestamp,
                "remarks": a.remarks,
            }
            for a in c.audit_trails.all().order_by("timestamp")
        ]
        results.append({
            "complaint_id": c.complaint_id,
            "category": c.issue_category,
            "location": c.location,
            "urgency": c.urgency,
            "status": c.status,
            "is_resolved": c.is_resolved,
            "created_at": c.created_at,
            "history": history,
        })
    return Response({"complaints": results})


# -------------------------------------------------------------
# UC-IWD-015: Assess Assigned Complaint
# -------------------------------------------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def assess_assigned_complaint(request, complaint_id):
    """UC-IWD-015: Engineer records repair assessment."""
    try:
        complaint = MaintenanceComplaint.objects.get(complaint_id=complaint_id)
    except MaintenanceComplaint.DoesNotExist:
        return Response({"error": "Complaint not found."}, status=status.HTTP_404_NOT_FOUND)

    assessment_details = request.data.get("assessment_details", "")
    complaint.assessment_details = assessment_details
    complaint.assessment_date = timezone.now()
    prev_status = complaint.status
    complaint.status = IWDStates.ASSESSED
    complaint.save()

    log_audit_trail(
        complaint, request.user, IWDRoles.ENGINEER,
        "assess_complaint", prev_status, IWDStates.ASSESSED, assessment_details
    )

    return Response({
        "message": "Assessment recorded.",
        "complaint_id": complaint.complaint_id,
        "status": complaint.status,
    })


# -------------------------------------------------------------
# UC-IWD-021: Prepare and Submit Estimate (Cost-Band Routing)
# -------------------------------------------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def submit_estimate(request, complaint_id):
    """
    UC-IWD-021, BR-IWD-003: Cost-band routing
    - < 25k: Low-Cost Review Pending
    - 25k to 2.5L: Mid-Range Committee Review Pending
    - > 2.5L: Director Review Pending (High-Cost)
    """
    try:
        complaint = MaintenanceComplaint.objects.get(complaint_id=complaint_id)
    except MaintenanceComplaint.DoesNotExist:
        return Response({"error": "Complaint not found."}, status=status.HTTP_404_NOT_FOUND)

    try:
        total_cost = Decimal(str(request.data.get("total_cost", 0)))
    except Exception:
        return Response({"error": "Invalid total cost."}, status=status.HTTP_400_BAD_REQUEST)

    time_days = int(request.data.get("estimated_time_days", 1))
    materials = request.data.get("materials_details", "")
    cost_band = CostBands.classify(total_cost)

    estimate = RepairEstimate.objects.create(
        complaint=complaint,
        engineer=request.user,
        estimated_time_days=time_days,
        materials_details=materials,
        total_cost=total_cost,
        cost_band=cost_band,
    )

    prev_status = complaint.status
    if cost_band == CostBands.LOW:
        next_state = IWDStates.LOW_COST_REVIEW_PENDING
    elif cost_band == CostBands.MID:
        next_state = IWDStates.MID_RANGE_COMMITTEE_REVIEW_PENDING
    else:
        next_state = IWDStates.DIRECTOR_REVIEW_PENDING_HIGH

    complaint.status = next_state
    complaint.save()

    log_audit_trail(
        complaint, request.user, IWDRoles.ENGINEER,
        "submit_estimate", prev_status, next_state,
        f"Submitted estimate Rs.{total_cost} ({cost_band} band)"
    )

    return Response({
        "message": "Estimate submitted and routed.",
        "estimate_id": estimate.id,
        "cost_band": cost_band,
        "status": complaint.status,
    }, status=status.HTTP_201_CREATED)


# -------------------------------------------------------------
# UC-IWD-025 & UC-IWD-055: Urgent Fast-Track Review (BW-IWD-15)
# -------------------------------------------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def flag_urgent_repair(request, complaint_id):
    """UC-IWD-025: Engineer flags urgent repair for fast-track review."""
    try:
        complaint = MaintenanceComplaint.objects.get(complaint_id=complaint_id)
    except MaintenanceComplaint.DoesNotExist:
        return Response({"error": "Complaint not found."}, status=status.HTTP_404_NOT_FOUND)

    remarks = request.data.get("remarks", "")
    complaint.is_urgent_escalated = True
    complaint.urgent_remarks = remarks
    prev_status = complaint.status
    complaint.status = IWDStates.URGENT_REVIEW_PENDING
    complaint.save()

    log_audit_trail(
        complaint, request.user, IWDRoles.ENGINEER,
        "flag_urgent", prev_status, IWDStates.URGENT_REVIEW_PENDING, remarks
    )

    return Response({
        "message": "Urgent flag submitted for fast-track review.",
        "status": complaint.status,
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def review_urgent_escalation(request, complaint_id):
    """UC-IWD-055: Dept Head or Director reviews urgent escalation (BR-IWD-012)."""
    try:
        complaint = MaintenanceComplaint.objects.get(complaint_id=complaint_id)
    except MaintenanceComplaint.DoesNotExist:
        return Response({"error": "Complaint not found."}, status=status.HTTP_404_NOT_FOUND)

    decision = request.data.get("decision", "accept")  # accept or decline
    role = request.data.get("role", IWDRoles.DEPARTMENT_HEAD)

    if decision == "accept":
        next_state = IWDStates.URGENT_PRIORITY_ACTIVE
    else:
        next_state = IWDStates.ASSESSED

    prev_status = complaint.status
    complaint.status = next_state
    complaint.save()

    log_audit_trail(
        complaint, request.user, role,
        "review_urgent_escalation", prev_status, next_state,
        f"Urgent escalation decision: {decision}"
    )

    return Response({
        "message": f"Urgent review completed ({decision}).",
        "status": complaint.status,
    })


# -------------------------------------------------------------
# UC-IWD-031: Review Low-Cost Estimate (BW-IWD-02)
# -------------------------------------------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def review_low_cost_estimate(request, complaint_id):
    """UC-IWD-031, BR-IWD-004: IWD Admin approve/reject low cost (< Rs. 25,000)."""
    try:
        complaint = MaintenanceComplaint.objects.get(complaint_id=complaint_id)
        estimate = complaint.estimates.latest("created_at")
    except Exception:
        return Response({"error": "Complaint or estimate not found."}, status=status.HTTP_404_NOT_FOUND)

    decision = request.data.get("decision", "approve")  # approve or reject
    reason = request.data.get("rejection_reason", "")

    prev_status = complaint.status
    if decision == "approve":
        complaint.status = IWDStates.ESTIMATE_APPROVED
        estimate.status = "Approved"
    else:
        complaint.status = IWDStates.REJECTED_LOW_COST
        estimate.status = "Rejected"
        estimate.rejection_reason = reason

    estimate.save()
    complaint.save()

    log_audit_trail(
        complaint, request.user, IWDRoles.IWD_ADMIN,
        "review_low_cost", prev_status, complaint.status,
        f"Decision: {decision}. Reason: {reason}"
    )

    return Response({
        "message": f"Low-cost estimate {decision}d.",
        "status": complaint.status,
    })


# -------------------------------------------------------------
# UC-IWD-041: Conduct Mid-Range Review (BW-IWD-03, BW-IWD-04)
# -------------------------------------------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def conduct_mid_range_review(request, complaint_id):
    """
    UC-IWD-041, BR-IWD-005, BR-IWD-006:
    Committee review + Department Head decision (approve, reject, forward).
    Note: Dean is a distinct role and cannot act as Department Head (BR-IWD-018).
    """
    try:
        complaint = MaintenanceComplaint.objects.get(complaint_id=complaint_id)
        estimate = complaint.estimates.latest("created_at")
    except Exception:
        return Response({"error": "Complaint or estimate not found."}, status=status.HTTP_404_NOT_FOUND)

    step = request.data.get("step", "dept_head")  # "committee" or "dept_head"

    if step == "committee":
        committee_remarks = request.data.get("committee_outcome", "")
        estimate.committee_outcome = committee_remarks
        estimate.committee_approved = True
        estimate.save()
        prev_status = complaint.status
        complaint.status = IWDStates.DEPARTMENT_HEAD_REVIEW_PENDING
        complaint.save()
        log_audit_trail(
            complaint, request.user, IWDRoles.REVIEW_COMMITTEE,
            "record_committee_review", prev_status, complaint.status, committee_remarks
        )
        return Response({"message": "Committee review recorded.", "status": complaint.status})

    # Department Head decision
    decision = request.data.get("decision", "approve")  # approve, reject, forward
    reason = request.data.get("remarks", "")
    prev_status = complaint.status

    if decision == "approve":
        complaint.status = IWDStates.ESTIMATE_APPROVED
        estimate.dept_head_decision = "Approved"
    elif decision == "reject":
        complaint.status = IWDStates.REJECTED_MID_RANGE
        estimate.dept_head_decision = "Rejected"
        estimate.rejection_reason = reason
    elif decision == "forward":
        complaint.status = IWDStates.DIRECTOR_REVIEW_PENDING_MID
        estimate.dept_head_decision = "Forwarded to Director"
    else:
        return Response({"error": "Invalid decision."}, status=status.HTTP_400_BAD_REQUEST)

    estimate.dept_head_remarks = reason
    estimate.save()
    complaint.save()

    log_audit_trail(
        complaint, request.user, IWDRoles.DEPARTMENT_HEAD,
        "dept_head_decision", prev_status, complaint.status,
        f"Decision: {decision}. Remarks: {reason}"
    )

    return Response({"message": f"Department Head decision: {decision}.", "status": complaint.status})


# -------------------------------------------------------------
# UC-IWD-051: Director Review & High-Cost Bidding Authorization (BW-IWD-05)
# -------------------------------------------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def director_review_estimate(request, complaint_id):
    """
    UC-IWD-051, BR-IWD-007:
    Director review for high cost (> 2.5L) authorizes external bidding,
    or approves forwarded mid-range estimate.
    """
    try:
        complaint = MaintenanceComplaint.objects.get(complaint_id=complaint_id)
        estimate = complaint.estimates.latest("created_at")
    except Exception:
        return Response({"error": "Complaint or estimate not found."}, status=status.HTTP_404_NOT_FOUND)

    decision = request.data.get("decision", "approve")
    reason = request.data.get("remarks", "")
    prev_status = complaint.status

    if complaint.status == IWDStates.DIRECTOR_REVIEW_PENDING_HIGH:
        if decision == "approve":
            complaint.status = IWDStates.BIDDING_AUTHORIZED
        else:
            complaint.status = IWDStates.REJECTED_DIRECTOR_ROUTE
            estimate.rejection_reason = reason
    else:  # Forwarded mid-range
        if decision == "approve":
            complaint.status = IWDStates.ESTIMATE_APPROVED
        else:
            complaint.status = IWDStates.REJECTED_DIRECTOR_ROUTE
            estimate.rejection_reason = reason

    estimate.director_decision = decision
    estimate.director_remarks = reason
    estimate.save()
    complaint.save()

    log_audit_trail(
        complaint, request.user, IWDRoles.DIRECTOR,
        "director_review", prev_status, complaint.status,
        f"Director decision: {decision}. Remarks: {reason}"
    )

    return Response({"message": f"Director decision recorded: {decision}.", "status": complaint.status})


# -------------------------------------------------------------
# UC-IWD-061: Check Stock & Issue Material (BW-IWD-06, 07, 08; CW-IWD-02)
# -------------------------------------------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def check_stock_and_issue(request, complaint_id):
    """
    UC-IWD-061, BR-IWD-010, BR-IWD-011:
    Inventory check before procurement.
    """
    try:
        complaint = MaintenanceComplaint.objects.get(complaint_id=complaint_id)
    except MaintenanceComplaint.DoesNotExist:
        return Response({"error": "Complaint not found."}, status=status.HTTP_404_NOT_FOUND)

    item_id = request.data.get("item_id")
    quantity = int(request.data.get("quantity", 1))

    try:
        stock_item = InventoryStock.objects.get(id=item_id)
    except InventoryStock.DoesNotExist:
        return Response({"error": "Stock item not found."}, status=status.HTTP_404_NOT_FOUND)

    prev_status = complaint.status
    if stock_item.quantity_available >= quantity:
        # Issue stock
        stock_item.quantity_available -= quantity
        stock_item.save()
        MaterialIssueRecord.objects.create(
            complaint=complaint,
            material=stock_item,
            quantity_issued=quantity,
            issued_by=request.user,
            remarks=request.data.get("remarks", "Direct issue from inventory"),
        )
        complaint.status = IWDStates.MATERIALS_ISSUED
        complaint.save()
        log_audit_trail(
            complaint, request.user, IWDRoles.IWD_ADMIN,
            "issue_material", prev_status, IWDStates.MATERIALS_ISSUED,
            f"Issued {quantity} of {stock_item.item_name}"
        )
        return Response({"message": "Material issued successfully.", "status": complaint.status})
    else:
        # Shortage -> route to procurement
        estimate = complaint.estimates.last()
        cost_band = estimate.cost_band if estimate else CostBands.LOW
        if cost_band == CostBands.LOW:
            complaint.status = IWDStates.PROCUREMENT_NEEDED_LOW
        else:
            complaint.status = IWDStates.PROCUREMENT_NEEDED_MID
        complaint.save()
        log_audit_trail(
            complaint, request.user, IWDRoles.IWD_ADMIN,
            "stock_shortage", prev_status, complaint.status,
            f"Insufficient stock for {stock_item.item_name}. Routed to procurement."
        )
        return Response({
            "message": "Stock unavailable. Routed to procurement coordination.",
            "status": complaint.status,
        })


# -------------------------------------------------------------
# UC-IWD-091: Execute Repair Work (BW-IWD-09, BW-IWD-10)
# -------------------------------------------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def execute_repair_work(request, complaint_id):
    """UC-IWD-091: Engineer marks repair work complete."""
    try:
        complaint = MaintenanceComplaint.objects.get(complaint_id=complaint_id)
    except MaintenanceComplaint.DoesNotExist:
        return Response({"error": "Complaint not found."}, status=status.HTTP_404_NOT_FOUND)

    prev_status = complaint.status
    complaint.status = IWDStates.VERIFICATION_PENDING
    complaint.save()

    log_audit_trail(
        complaint, request.user, IWDRoles.ENGINEER,
        "complete_repair_work", prev_status, IWDStates.VERIFICATION_PENDING,
        request.data.get("remarks", "Repair work completed. Ready for physical verification.")
    )

    return Response({"message": "Work marked complete. Pending verification.", "status": complaint.status})


# -------------------------------------------------------------
# UC-IWD-101: Verify Completed Work (BW-IWD-09, BW-IWD-10; BR-IWD-014)
# -------------------------------------------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def verify_completed_work(request, complaint_id):
    """
    UC-IWD-101, BR-IWD-014:
    Department Head physical verification.
    Outcome:
    - Approved -> Resolved
    - Rework Required -> Max 1 rework traversal (BW-IWD-10)
    """
    try:
        complaint = MaintenanceComplaint.objects.get(complaint_id=complaint_id)
    except MaintenanceComplaint.DoesNotExist:
        return Response({"error": "Complaint not found."}, status=status.HTTP_404_NOT_FOUND)

    outcome = request.data.get("outcome", "Approved")  # Approved or Rework Required
    remarks = request.data.get("remarks", "")
    prev_status = complaint.status

    if outcome == "Approved":
        complaint.status = IWDStates.RESOLVED
        complaint.is_resolved = True
        complaint.resolved_at = timezone.now()
        complaint.save()
    else:
        # Check rework traversal count (BW-IWD-10: exactly one traversal)
        if complaint.rework_count >= 1:
            return Response({
                "error": "Maximum rework traversals (1) reached. Cannot request further rework.",
            }, status=status.HTTP_400_BAD_REQUEST)
        complaint.rework_count += 1
        complaint.status = IWDStates.REWORK_REQUIRED
        complaint.save()

    PhysicalVerification.objects.create(
        complaint=complaint,
        verified_by=request.user,
        outcome=outcome,
        remarks=remarks,
        traversal_number=complaint.rework_count,
    )

    log_audit_trail(
        complaint, request.user, IWDRoles.DEPARTMENT_HEAD,
        "physical_verification", prev_status, complaint.status,
        f"Verification outcome: {outcome}. Remarks: {remarks}"
    )

    return Response({
        "message": f"Verification recorded ({outcome}).",
        "status": complaint.status,
        "is_resolved": complaint.is_resolved,
    })


# -------------------------------------------------------------
# UC-IWD-111, 121, 131: Final Bill, Audit & Settlement (BW-IWD-11)
# -------------------------------------------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def submit_final_bill(request, complaint_id):
    """UC-IWD-111, BR-IWD-014: Engineer submits final bill (guarded by Resolved state)."""
    try:
        complaint = MaintenanceComplaint.objects.get(complaint_id=complaint_id)
    except MaintenanceComplaint.DoesNotExist:
        return Response({"error": "Complaint not found."}, status=status.HTTP_404_NOT_FOUND)

    if not complaint.is_resolved:
        return Response({
            "error": "BR-IWD-014: Complaint must be verified and resolved before final bill submission.",
        }, status=status.HTTP_400_BAD_REQUEST)

    amount = Decimal(str(request.data.get("total_amount", 0)))
    bill = FinalBillRecord.objects.create(
        complaint=complaint,
        engineer=request.user,
        total_amount=amount,
    )
    prev_status = complaint.status
    complaint.status = IWDStates.AUDIT_PENDING
    complaint.save()

    log_audit_trail(
        complaint, request.user, IWDRoles.ENGINEER,
        "submit_final_bill", prev_status, IWDStates.AUDIT_PENDING,
        f"Submitted final bill for Rs.{amount}"
    )

    return Response({
        "message": "Final bill submitted for audit.",
        "bill_id": bill.id,
        "status": complaint.status,
    }, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def audit_final_bill(request, complaint_id):
    """UC-IWD-121, BR-IWD-015: Auditor validates final bill."""
    try:
        complaint = MaintenanceComplaint.objects.get(complaint_id=complaint_id)
        bill = complaint.final_bills.latest("created_at")
    except Exception:
        return Response({"error": "Bill or complaint not found."}, status=status.HTTP_404_NOT_FOUND)

    outcome = request.data.get("outcome", "Validated")  # Validated or Query
    remarks = request.data.get("remarks", "")
    bill.auditor_status = outcome
    bill.auditor_remarks = remarks
    bill.audited_at = timezone.now()
    bill.save()

    prev_status = complaint.status
    if outcome == "Validated":
        complaint.status = IWDStates.DIRECTOR_PAYMENT_APPROVAL_PENDING
        complaint.save()

    log_audit_trail(
        complaint, request.user, IWDRoles.AUDITOR,
        "audit_final_bill", prev_status, complaint.status,
        f"Audit outcome: {outcome}. Remarks: {remarks}"
    )

    return Response({"message": f"Bill audit recorded ({outcome}).", "status": complaint.status})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def approve_payment_settlement(request, complaint_id):
    """
    UC-IWD-131, BR-IWD-016:
    Director final payment approval -> Accounts settlement.
    """
    try:
        complaint = MaintenanceComplaint.objects.get(complaint_id=complaint_id)
        bill = complaint.final_bills.latest("created_at")
    except Exception:
        return Response({"error": "Bill or complaint not found."}, status=status.HTTP_404_NOT_FOUND)

    action_type = request.data.get("action_type", "director_approval")

    prev_status = complaint.status
    if action_type == "director_approval":
        bill.director_payment_approval = True
        bill.director_approved_at = timezone.now()
        bill.save()
        complaint.status = IWDStates.ACCOUNTS_SETTLEMENT_PENDING
        complaint.save()
        log_audit_trail(
            complaint, request.user, IWDRoles.DIRECTOR,
            "director_payment_approval", prev_status, complaint.status,
            "Director approved payment for settlement"
        )
        return Response({"message": "Payment approved for accounts settlement.", "status": complaint.status})

    elif action_type == "accounts_settlement":
        bill.accounts_settled = True
        bill.settled_at = timezone.now()
        bill.settlement_reference = request.data.get("reference", "REF-IWD-SETTLED")
        bill.save()
        complaint.status = IWDStates.SETTLED
        complaint.save()
        log_audit_trail(
            complaint, request.user, IWDRoles.ACCOUNTS,
            "accounts_settle", prev_status, complaint.status,
            f"Settlement completed. Ref: {bill.settlement_reference}"
        )
        return Response({"message": "Payment settled successfully.", "status": complaint.status})

    return Response({"error": "Invalid action type."}, status=status.HTTP_400_BAD_REQUEST)


# -------------------------------------------------------------
# UC-IWD-141: Feedback & Post-Repair Issue (BR-IWD-017)
# -------------------------------------------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def submit_complaint_feedback(request, complaint_id):
    """UC-IWD-141, BR-IWD-017: Feedback and post-repair issue after resolution."""
    try:
        complaint = MaintenanceComplaint.objects.get(complaint_id=complaint_id)
    except MaintenanceComplaint.DoesNotExist:
        return Response({"error": "Complaint not found."}, status=status.HTTP_404_NOT_FOUND)

    if not complaint.is_resolved:
        return Response({"error": "Feedback can only be submitted after resolution."}, status=status.HTTP_400_BAD_REQUEST)

    rating = int(request.data.get("rating", 5))
    comments = request.data.get("comments", "")
    has_post_issue = bool(request.data.get("post_repair_issue", False))
    post_remarks = request.data.get("post_repair_remarks", "")

    feedback = ComplaintFeedback.objects.create(
        complaint=complaint,
        employee=request.user,
        rating=rating,
        comments=comments,
        post_repair_issue=has_post_issue,
        post_repair_remarks=post_remarks,
    )

    log_audit_trail(
        complaint, request.user, IWDRoles.INSTITUTE_EMPLOYEE,
        "submit_feedback", complaint.status, complaint.status,
        f"Submitted rating: {rating}, Post repair issue: {has_post_issue}"
    )

    return Response({"message": "Feedback submitted successfully.", "feedback_id": feedback.id})


# -------------------------------------------------------------
# UC-IWD-151: Modify and Resubmit Rejected Request (BW-IWD-12, 13, 14)
# -------------------------------------------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def modify_and_resubmit_rejected(request, complaint_id):
    """
    UC-IWD-151, BR-IWD-009:
    Modify rejected estimate and resubmit to appropriate cost-band route.
    """
    try:
        complaint = MaintenanceComplaint.objects.get(complaint_id=complaint_id)
        estimate = complaint.estimates.latest("created_at")
    except Exception:
        return Response({"error": "Complaint or estimate not found."}, status=status.HTTP_404_NOT_FOUND)

    new_cost = request.data.get("total_cost")
    if new_cost:
        estimate.total_cost = Decimal(str(new_cost))
        estimate.cost_band = CostBands.classify(estimate.total_cost)

    estimate.materials_details = request.data.get("materials_details", estimate.materials_details)
    estimate.estimated_time_days = int(request.data.get("estimated_time_days", estimate.estimated_time_days))
    estimate.resubmission_count += 1
    estimate.status = "Resubmitted"
    estimate.save()

    prev_status = complaint.status
    if estimate.cost_band == CostBands.LOW:
        complaint.status = IWDStates.LOW_COST_REVIEW_PENDING
    elif estimate.cost_band == CostBands.MID:
        complaint.status = IWDStates.MID_RANGE_COMMITTEE_REVIEW_PENDING
    else:
        complaint.status = IWDStates.DIRECTOR_REVIEW_PENDING_HIGH

    complaint.save()

    log_audit_trail(
        complaint, request.user, IWDRoles.ENGINEER,
        "modify_resubmit", prev_status, complaint.status,
        f"Resubmitted estimate (attempt #{estimate.resubmission_count})"
    )

    return Response({
        "message": "Rejected request modified and resubmitted.",
        "cost_band": estimate.cost_band,
        "status": complaint.status,
    })


# -------------------------------------------------------------
# UC-IWD-181: Switch Active IWD Role (BR-IWD-001, BR-IWD-018)
# -------------------------------------------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def switch_active_iwd_role(request):
    """
    UC-IWD-181, BR-IWD-001, BR-IWD-018:
    Switch active IWD role. Department Head and Dean are distinct roles.
    """
    role = request.data.get("role")
    if role not in IWDRoles.ALL_ROLES:
        return Response({
            "error": f"Invalid role '{role}'. Permitted roles: {IWDRoles.ALL_ROLES}"
        }, status=status.HTTP_400_BAD_REQUEST)

    # In a full session/JWT system, save to session:
    request.session["active_iwd_role"] = role

    return Response({
        "message": f"Active IWD role switched to '{role}'.",
        "active_role": role,
    })
