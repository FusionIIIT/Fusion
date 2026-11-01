"""
IWD Workflow Engine & State-Transition System
DIRECT_FINAL_v2 Basis and Composite workflows; authoritative state-transition tables
Version: v1.4 | Date: 30 August 2026
Implements:
- BW-IWD-01 through BW-IWD-15
- CW-IWD-01 through CW-IWD-04
- Business Rules BR-IWD-001 through BR-IWD-018
"""

from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any


class IWDStates:
    # Initial / Intake
    NO_COMPLAINT = "No Complaint"
    SUBMITTED = "Submitted"
    ASSIGNED = "Assigned"
    ASSESSED = "Assessed"

    # Approvals - Low Cost (< Rs. 25,000)
    LOW_COST_REVIEW_PENDING = "Low-Cost Review Pending"
    REJECTED_LOW_COST = "Rejected - Low-Cost"

    # Approvals - Mid Range (Rs. 25,000 to Rs. 2.5 Lakh)
    MID_RANGE_COMMITTEE_REVIEW_PENDING = "Mid-Range Committee Review Pending"
    DEPARTMENT_HEAD_REVIEW_PENDING = "Department Head Review Pending"
    DIRECTOR_REVIEW_PENDING_MID = "Director Review Pending (Mid-Range)"
    REJECTED_MID_RANGE = "Rejected - Mid-Range"

    # Approvals - High Cost (> Rs. 2.5 Lakh)
    DIRECTOR_REVIEW_PENDING_HIGH = "Director Review Pending (High-Cost)"
    BIDDING_AUTHORIZED = "Bidding Authorized"
    VENDOR_SELECTED = "Vendor/Contractor Selected"
    REJECTED_DIRECTOR_ROUTE = "Rejected - Director Route"

    # General Approved State
    ESTIMATE_APPROVED = "Estimate Approved"
    DIRECTOR_APPROVED = "Director Approved"

    # Inventory & Procurement
    MATERIALS_ISSUED = "Materials Issued"
    PROCUREMENT_NEEDED_LOW = "Procurement Needed (Low)"
    PROCUREMENT_NEEDED_MID = "Procurement Needed (Mid)"
    MATERIALS_AVAILABLE = "Materials Available"

    # Work Execution & Verification
    READY_FOR_EXECUTION = "Ready for Execution"
    VERIFICATION_PENDING = "Verification Pending"
    REWORK_REQUIRED = "Rework Required"
    RESOLVED = "Resolved"

    # Billing, Audit & Settlement
    AUDIT_PENDING = "Audit Pending"
    DIRECTOR_PAYMENT_APPROVAL_PENDING = "Director Payment Approval Pending"
    ACCOUNTS_SETTLEMENT_PENDING = "Accounts Settlement Pending"
    SETTLED = "Settled"

    # Urgent Fast-Track
    URGENT_REVIEW_PENDING = "Urgent Review Pending"
    URGENT_PRIORITY_ACTIVE = "Urgent Priority Active"


class IWDRoles:
    INSTITUTE_EMPLOYEE = "Institute Employee"
    ENGINEER = "Engineer"
    IWD_ADMIN = "IWD Admin"
    DEPARTMENT_HEAD = "Department Head"
    DEAN = "Dean"
    DIRECTOR = "Director"
    AUDITOR = "Auditor"
    ACCOUNTS = "Accounts Department"
    REVIEW_COMMITTEE = "Review Committee"
    PROCUREMENT_TEAM = "Procurement Team"
    SYSTEM = "System"

    # BR-IWD-001 & BR-IWD-018: Distinct role validation
    ALL_ROLES = [
        INSTITUTE_EMPLOYEE, ENGINEER, IWD_ADMIN,
        DEPARTMENT_HEAD, DEAN, DIRECTOR, AUDITOR, ACCOUNTS
    ]


class CostBands:
    LOW = "LOW"        # < 25,000
    MID = "MID"        # 25,000 <= total <= 250,000
    HIGH = "HIGH"      # > 250,000

    LOW_THRESHOLD = Decimal("25000.00")
    MID_MAX_THRESHOLD = Decimal("250000.00")

    @classmethod
    def classify(cls, amount: Decimal) -> str:
        """BR-IWD-003: Cost-band routing classification."""
        amount = Decimal(str(amount))
        if amount < cls.LOW_THRESHOLD:
            return cls.LOW
        elif amount <= cls.MID_MAX_THRESHOLD:
            return cls.MID
        else:
            return cls.HIGH


class WorkflowEngine:
    """
    Authoritative state transition engine implementing the 15 Basis Workflows
    and 4 Composite Workflows of DIRECT_FINAL_v2.
    """

    TRANSITIONS: Dict[str, List[Dict[str, Any]]] = {
        # BW-IWD-01: Complaint Intake and Assessment
        IWDStates.NO_COMPLAINT: [
            {
                "action": "submit_complaint",
                "actor": IWDRoles.INSTITUTE_EMPLOYEE,
                "use_case": "UC-IWD-001",
                "guard": lambda ctx: ctx.get("is_valid_submission", False),
                "next_state": IWDStates.SUBMITTED,
                "rule": "BR-IWD-001"
            }
        ],
        IWDStates.SUBMITTED: [
            {
                "action": "auto_assign_engineer",
                "actor": IWDRoles.SYSTEM,
                "use_case": "UC-IWD-001",
                "guard": lambda ctx: bool(ctx.get("assigned_engineer")),
                "next_state": IWDStates.ASSIGNED,
                "rule": "BR-IWD-002"
            }
        ],
        IWDStates.ASSIGNED: [
            {
                "action": "assess_complaint",
                "actor": IWDRoles.ENGINEER,
                "use_case": "UC-IWD-015",
                "guard": lambda ctx: ctx.get("assessment_recorded", False),
                "next_state": IWDStates.ASSESSED,
                "rule": "BR-IWD-001"
            },
            {
                "action": "flag_urgent",
                "actor": IWDRoles.ENGINEER,
                "use_case": "UC-IWD-025",
                "guard": lambda ctx: True,
                "next_state": IWDStates.URGENT_REVIEW_PENDING,
                "rule": "BR-IWD-012"
            }
        ],
        IWDStates.ASSESSED: [
            # BW-IWD-02 / CW-IWD-01: Low cost
            {
                "action": "submit_estimate",
                "actor": IWDRoles.ENGINEER,
                "use_case": "UC-IWD-021",
                "guard": lambda ctx: CostBands.classify(ctx.get("estimate_cost", 0)) == CostBands.LOW,
                "next_state": IWDStates.LOW_COST_REVIEW_PENDING,
                "rule": "BR-IWD-003"
            },
            # BW-IWD-03 / CW-IWD-01: Mid range
            {
                "action": "submit_estimate",
                "actor": IWDRoles.ENGINEER,
                "use_case": "UC-IWD-021",
                "guard": lambda ctx: CostBands.classify(ctx.get("estimate_cost", 0)) == CostBands.MID,
                "next_state": IWDStates.MID_RANGE_COMMITTEE_REVIEW_PENDING,
                "rule": "BR-IWD-003, BR-IWD-005"
            },
            # BW-IWD-05 / CW-IWD-01: High cost
            {
                "action": "submit_estimate",
                "actor": IWDRoles.ENGINEER,
                "use_case": "UC-IWD-021",
                "guard": lambda ctx: CostBands.classify(ctx.get("estimate_cost", 0)) == CostBands.HIGH,
                "next_state": IWDStates.DIRECTOR_REVIEW_PENDING_HIGH,
                "rule": "BR-IWD-003, BR-IWD-007"
            },
            {
                "action": "flag_urgent",
                "actor": IWDRoles.ENGINEER,
                "use_case": "UC-IWD-025",
                "guard": lambda ctx: True,
                "next_state": IWDStates.URGENT_REVIEW_PENDING,
                "rule": "BR-IWD-012"
            }
        ],

        # Low-Cost Approvals (BW-IWD-02, BW-IWD-12)
        IWDStates.LOW_COST_REVIEW_PENDING: [
            {
                "action": "approve_low_cost",
                "actor": IWDRoles.IWD_ADMIN,
                "use_case": "UC-IWD-031",
                "guard": lambda ctx: ctx.get("decision") == "approve",
                "next_state": IWDStates.ESTIMATE_APPROVED,
                "rule": "BR-IWD-004, BR-IWD-013"
            },
            {
                "action": "reject_low_cost",
                "actor": IWDRoles.IWD_ADMIN,
                "use_case": "UC-IWD-031",
                "guard": lambda ctx: ctx.get("decision") == "reject" and bool(ctx.get("rejection_reason")),
                "next_state": IWDStates.REJECTED_LOW_COST,
                "rule": "BR-IWD-009, BR-IWD-013"
            }
        ],
        IWDStates.REJECTED_LOW_COST: [
            {
                "action": "modify_resubmit",
                "actor": IWDRoles.ENGINEER,
                "use_case": "UC-IWD-151",
                "guard": lambda ctx: CostBands.classify(ctx.get("estimate_cost", 0)) == CostBands.LOW,
                "next_state": IWDStates.LOW_COST_REVIEW_PENDING,
                "rule": "BR-IWD-009, BR-IWD-003"
            }
        ],

        # Mid-Range Approvals (BW-IWD-03, BW-IWD-04, BW-IWD-13)
        IWDStates.MID_RANGE_COMMITTEE_REVIEW_PENDING: [
            {
                "action": "record_committee_review",
                "actor": IWDRoles.REVIEW_COMMITTEE,
                "use_case": "UC-IWD-041",
                "guard": lambda ctx: ctx.get("committee_outcome_recorded", False),
                "next_state": IWDStates.DEPARTMENT_HEAD_REVIEW_PENDING,
                "rule": "BR-IWD-005"
            }
        ],
        IWDStates.DEPARTMENT_HEAD_REVIEW_PENDING: [
            {
                "action": "dept_head_approve",
                "actor": IWDRoles.DEPARTMENT_HEAD,
                "use_case": "UC-IWD-041",
                "guard": lambda ctx: ctx.get("decision") == "approve",
                "next_state": IWDStates.ESTIMATE_APPROVED,
                "rule": "BR-IWD-006, BR-IWD-013"
            },
            {
                "action": "dept_head_reject",
                "actor": IWDRoles.DEPARTMENT_HEAD,
                "use_case": "UC-IWD-041",
                "guard": lambda ctx: ctx.get("decision") == "reject" and bool(ctx.get("rejection_reason")),
                "next_state": IWDStates.REJECTED_MID_RANGE,
                "rule": "BR-IWD-006, BR-IWD-009"
            },
            {
                "action": "dept_head_forward_director",
                "actor": IWDRoles.DEPARTMENT_HEAD,
                "use_case": "UC-IWD-041",
                "guard": lambda ctx: ctx.get("decision") == "forward",
                "next_state": IWDStates.DIRECTOR_REVIEW_PENDING_MID,
                "rule": "BR-IWD-006"
            }
        ],
        IWDStates.DIRECTOR_REVIEW_PENDING_MID: [
            {
                "action": "director_approve_mid",
                "actor": IWDRoles.DIRECTOR,
                "use_case": "UC-IWD-051",
                "guard": lambda ctx: ctx.get("decision") == "approve",
                "next_state": IWDStates.ESTIMATE_APPROVED,
                "rule": "BR-IWD-006, BR-IWD-013"
            },
            {
                "action": "director_reject_mid",
                "actor": IWDRoles.DIRECTOR,
                "use_case": "UC-IWD-051",
                "guard": lambda ctx: ctx.get("decision") == "reject" and bool(ctx.get("rejection_reason")),
                "next_state": IWDStates.REJECTED_DIRECTOR_ROUTE,
                "rule": "BR-IWD-009"
            }
        ],
        IWDStates.REJECTED_MID_RANGE: [
            {
                "action": "modify_resubmit",
                "actor": IWDRoles.ENGINEER,
                "use_case": "UC-IWD-151",
                "guard": lambda ctx: CostBands.classify(ctx.get("estimate_cost", 0)) == CostBands.MID,
                "next_state": IWDStates.MID_RANGE_COMMITTEE_REVIEW_PENDING,
                "rule": "BR-IWD-009, BR-IWD-005"
            }
        ],

        # High-Cost Approvals & Bidding (BW-IWD-05, BW-IWD-14)
        IWDStates.DIRECTOR_REVIEW_PENDING_HIGH: [
            {
                "action": "director_approve_bidding",
                "actor": IWDRoles.DIRECTOR,
                "use_case": "UC-IWD-051",
                "guard": lambda ctx: ctx.get("decision") == "approve",
                "next_state": IWDStates.BIDDING_AUTHORIZED,
                "rule": "BR-IWD-007, BR-IWD-013"
            },
            {
                "action": "director_reject_high",
                "actor": IWDRoles.DIRECTOR,
                "use_case": "UC-IWD-051",
                "guard": lambda ctx: ctx.get("decision") == "reject" and bool(ctx.get("rejection_reason")),
                "next_state": IWDStates.REJECTED_DIRECTOR_ROUTE,
                "rule": "BR-IWD-007, BR-IWD-009"
            }
        ],
        IWDStates.BIDDING_AUTHORIZED: [
            {
                "action": "select_vendor",
                "actor": IWDRoles.IWD_ADMIN,
                "use_case": "UC-IWD-081",
                "guard": lambda ctx: ctx.get("vendor_selected", False),
                "next_state": IWDStates.VENDOR_SELECTED,
                "rule": "BR-IWD-007, BR-IWD-008"
            }
        ],
        IWDStates.VENDOR_SELECTED: [
            {
                "action": "finalize_high_cost_authorization",
                "actor": IWDRoles.DIRECTOR,
                "use_case": "UC-IWD-081",
                "guard": lambda ctx: True,
                "next_state": IWDStates.READY_FOR_EXECUTION,
                "rule": "BR-IWD-008"
            }
        ],
        IWDStates.REJECTED_DIRECTOR_ROUTE: [
            {
                "action": "modify_resubmit",
                "actor": IWDRoles.ENGINEER,
                "use_case": "UC-IWD-151",
                "guard": lambda ctx: True,
                "next_state": IWDStates.DIRECTOR_REVIEW_PENDING_HIGH,
                "rule": "BR-IWD-009, BR-IWD-007"
            }
        ],

        # Inventory & Procurement (BW-IWD-06, 07, 08; CW-IWD-02)
        IWDStates.ESTIMATE_APPROVED: [
            # Stock available
            {
                "action": "check_stock_available",
                "actor": IWDRoles.IWD_ADMIN,
                "use_case": "UC-IWD-061",
                "guard": lambda ctx: ctx.get("stock_available", False),
                "next_state": IWDStates.MATERIALS_ISSUED,
                "rule": "BR-IWD-010, BR-IWD-011"
            },
            # Stock unavailable - low cost
            {
                "action": "stock_shortage_low",
                "actor": IWDRoles.IWD_ADMIN,
                "use_case": "UC-IWD-061",
                "guard": lambda ctx: not ctx.get("stock_available", False) and CostBands.classify(ctx.get("estimate_cost", 0)) == CostBands.LOW,
                "next_state": IWDStates.PROCUREMENT_NEEDED_LOW,
                "rule": "BR-IWD-010"
            },
            # Stock unavailable - mid range
            {
                "action": "stock_shortage_mid",
                "actor": IWDRoles.IWD_ADMIN,
                "use_case": "UC-IWD-061",
                "guard": lambda ctx: not ctx.get("stock_available", False) and CostBands.classify(ctx.get("estimate_cost", 0)) == CostBands.MID,
                "next_state": IWDStates.PROCUREMENT_NEEDED_MID,
                "rule": "BR-IWD-010"
            }
        ],
        IWDStates.PROCUREMENT_NEEDED_LOW: [
            {
                "action": "complete_low_cost_procurement",
                "actor": IWDRoles.IWD_ADMIN,
                "use_case": "UC-IWD-071",
                "guard": lambda ctx: ctx.get("procurement_completed", False),
                "next_state": IWDStates.MATERIALS_AVAILABLE,
                "rule": "BR-IWD-004, BR-IWD-008"
            }
        ],
        IWDStates.PROCUREMENT_NEEDED_MID: [
            {
                "action": "complete_mid_range_procurement",
                "actor": IWDRoles.IWD_ADMIN,
                "use_case": "UC-IWD-071",
                "guard": lambda ctx: ctx.get("procurement_completed", False),
                "next_state": IWDStates.MATERIALS_AVAILABLE,
                "rule": "BR-IWD-008"
            }
        ],
        IWDStates.MATERIALS_AVAILABLE: [
            {
                "action": "issue_procured_materials",
                "actor": IWDRoles.IWD_ADMIN,
                "use_case": "UC-IWD-061",
                "guard": lambda ctx: True,
                "next_state": IWDStates.MATERIALS_ISSUED,
                "rule": "BR-IWD-010, BR-IWD-011"
            }
        ],
        IWDStates.MATERIALS_ISSUED: [
            {
                "action": "proceed_to_execution",
                "actor": IWDRoles.ENGINEER,
                "use_case": "UC-IWD-091",
                "guard": lambda ctx: True,
                "next_state": IWDStates.READY_FOR_EXECUTION,
                "rule": "BR-IWD-011"
            }
        ],

        # Execution & Verification (BW-IWD-09, BW-IWD-10; CW-IWD-03)
        IWDStates.READY_FOR_EXECUTION: [
            {
                "action": "complete_work",
                "actor": IWDRoles.ENGINEER,
                "use_case": "UC-IWD-091",
                "guard": lambda ctx: ctx.get("work_completed", False),
                "next_state": IWDStates.VERIFICATION_PENDING,
                "rule": "BR-IWD-011, BR-IWD-014"
            }
        ],
        IWDStates.VERIFICATION_PENDING: [
            # Successful verification -> Resolved
            {
                "action": "verify_approved",
                "actor": IWDRoles.DEPARTMENT_HEAD,
                "use_case": "UC-IWD-101",
                "guard": lambda ctx: ctx.get("verification_outcome") == "Approved",
                "next_state": IWDStates.RESOLVED,
                "rule": "BR-IWD-014, BR-IWD-013"
            },
            # Failed verification -> Rework Required (One traversal max: BW-IWD-10)
            {
                "action": "verify_rework_needed",
                "actor": IWDRoles.DEPARTMENT_HEAD,
                "use_case": "UC-IWD-101",
                "guard": lambda ctx: ctx.get("verification_outcome") == "Rework Required" and ctx.get("rework_traversals", 0) < 1,
                "next_state": IWDStates.REWORK_REQUIRED,
                "rule": "BR-IWD-014, BR-IWD-013"
            }
        ],
        IWDStates.REWORK_REQUIRED: [
            {
                "action": "execute_rework",
                "actor": IWDRoles.ENGINEER,
                "use_case": "UC-IWD-091",
                "guard": lambda ctx: ctx.get("rework_completed", False),
                "next_state": IWDStates.VERIFICATION_PENDING,
                "rule": "BR-IWD-011"
            }
        ],

        # Billing, Audit & Settlement (BW-IWD-11)
        IWDStates.RESOLVED: [
            {
                "action": "submit_final_bill",
                "actor": IWDRoles.ENGINEER,
                "use_case": "UC-IWD-111",
                "guard": lambda ctx: ctx.get("bill_submitted", False),
                "next_state": IWDStates.AUDIT_PENDING,
                "rule": "BR-IWD-014"
            }
        ],
        IWDStates.AUDIT_PENDING: [
            {
                "action": "audit_validate_bill",
                "actor": IWDRoles.AUDITOR,
                "use_case": "UC-IWD-121",
                "guard": lambda ctx: ctx.get("audit_outcome") == "Validated",
                "next_state": IWDStates.DIRECTOR_PAYMENT_APPROVAL_PENDING,
                "rule": "BR-IWD-015, BR-IWD-016"
            }
        ],
        IWDStates.DIRECTOR_PAYMENT_APPROVAL_PENDING: [
            {
                "action": "director_approve_payment",
                "actor": IWDRoles.DIRECTOR,
                "use_case": "UC-IWD-131",
                "guard": lambda ctx: ctx.get("decision") == "approve",
                "next_state": IWDStates.ACCOUNTS_SETTLEMENT_PENDING,
                "rule": "BR-IWD-016, BR-IWD-013"
            }
        ],
        IWDStates.ACCOUNTS_SETTLEMENT_PENDING: [
            {
                "action": "accounts_settle",
                "actor": IWDRoles.ACCOUNTS,
                "use_case": "UC-IWD-131",
                "guard": lambda ctx: ctx.get("settlement_recorded", False),
                "next_state": IWDStates.SETTLED,
                "rule": "BR-IWD-016"
            }
        ],

        # Urgent Fast-Track (BW-IWD-15)
        IWDStates.URGENT_REVIEW_PENDING: [
            {
                "action": "accept_fast_track",
                "actor": IWDRoles.DEPARTMENT_HEAD,
                "use_case": "UC-IWD-055",
                "guard": lambda ctx: ctx.get("fast_track_accepted", False),
                "next_state": IWDStates.URGENT_PRIORITY_ACTIVE,
                "rule": "BR-IWD-012, BR-IWD-013"
            },
            {
                "action": "accept_fast_track_director",
                "actor": IWDRoles.DIRECTOR,
                "use_case": "UC-IWD-055",
                "guard": lambda ctx: ctx.get("fast_track_accepted", False),
                "next_state": IWDStates.URGENT_PRIORITY_ACTIVE,
                "rule": "BR-IWD-012, BR-IWD-013"
            }
        ]
    }

    @classmethod
    def can_transition(cls, current_state: str, action: str, actor_role: str, context: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate whether a state transition is permitted.
        Returns: (is_permitted, next_state, rule_or_reason)
        """
        # BR-IWD-001 & BR-IWD-018: Strict Role separation check
        if actor_role == IWDRoles.DEAN and action in ["dept_head_approve", "verify_approved", "verify_rework_needed"]:
            return False, None, "BR-IWD-018: Dean and Department Head are distinct roles; Dean cannot perform Department Head transitions."

        transitions = cls.TRANSITIONS.get(current_state, [])
        for t in transitions:
            if t["action"] == action:
                if t["actor"] != actor_role and actor_role != IWDRoles.SYSTEM:
                    return False, None, f"BR-IWD-001: Actor {actor_role} is not authorized for {action} (requires {t['actor']})"
                if not t["guard"](context):
                    return False, None, f"Guard failed for transition {action} from {current_state}"
                return True, t["next_state"], t["rule"]

        return False, None, f"No valid transition from '{current_state}' with action '{action}'"
