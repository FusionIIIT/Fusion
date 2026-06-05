from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from applications.audit_account.models import (
    ActionDecision,
    ActionLog,
    AuditObservation,
    AuditObservationStatus,
    DepartmentBudget,
    ObservationAttachment,
    ObservationAttachmentKind,
    Request,
    RequestAttachment,
    RequestStatus,
    RequestType,
    TARequestStatus,
    TravelAllowance,
    TravelAllowanceAttachment,
    WorkflowType,
)
from applications.globals.models import ExtraInfo, HoldsDesignation
from notification.views import audit_account_notif

from .serializers import (
    ActionLogSerializer,
    AuditObservationSerializer,
    RequestSerializer,
    TravelAllowanceSerializer,
)

FINANCE_ROLES = {
    "finance",
    "finance staff",
    "accounts",
    "accounts staff",
    "accountant",
    "accounts admin",
    "administrator",
    "adminstrator",
    "admin",
}
DEAN_ROLES = {"dean academic", "dean_s", "dean_rspc", "dean (p&d)", "dean (r&d)", "dean"}
DIRECTOR_ROLES = {"director"}
HOD_ROLES = {"hod", "head of department", "dept_admin", "department admin"}
AUDITOR_ROLES = {"auditor", "audit", "internal auditor"}

REQUEST_THRESHOLD_HOD = Decimal(str(getattr(settings, "AUDIT_ACCOUNT_REQUEST_THRESHOLD_HOD", "25000")))
REQUEST_THRESHOLD_DEAN = Decimal(str(getattr(settings, "AUDIT_ACCOUNT_REQUEST_THRESHOLD_DEAN", "100000")))
TA_HIGH_VALUE_THRESHOLD = Decimal(str(getattr(settings, "AUDIT_ACCOUNT_TA_HIGH_VALUE_THRESHOLD", "50000")))

DEFAULT_DEPARTMENTS = [
    "CSE",
    "HR",
    "MECH",
    "SM",
    "ECE",
    "PG",
    "ACAD",
    "ADMIN",
    "DEV",
    "CULTURAL",
]
DEFAULT_BUDGET_HEADS = ["head", "travel", "equipment"]
DEFAULT_INITIAL_BUDGET = Decimal("10000.00")


def _normalize_budget_key(value):
    return value.strip().lower() if isinstance(value, str) else ""


def _ensure_default_department_budgets():
    budgets_to_create = []
    for department in DEFAULT_DEPARTMENTS:
        for budget_head in DEFAULT_BUDGET_HEADS:
            if not DepartmentBudget.objects.filter(
                department__iexact=department,
                budget_head__iexact=budget_head,
                is_active=True,
            ).exists():
                budgets_to_create.append(
                    DepartmentBudget(
                        department=department,
                        budget_head=budget_head,
                        allocated_amount=DEFAULT_INITIAL_BUDGET,
                        remaining_amount=DEFAULT_INITIAL_BUDGET,
                        is_active=True,
                    )
                )
    if budgets_to_create:
        DepartmentBudget.objects.bulk_create(budgets_to_create)


def _get_department_budget(department, budget_head):
    if not department or not budget_head:
        return None
    _ensure_default_department_budgets()
    return DepartmentBudget.objects.filter(
        department__iexact=department,
        budget_head__iexact=budget_head,
        is_active=True,
    ).first()


def _normalize_role(role):
    return role.strip().lower() if isinstance(role, str) else ""


def _get_designation_names(user):
    roles = list(user.current_designation.all().values_list("designation__name", flat=True))
    user_type = getattr(getattr(user, "extrainfo", None), "user_type", None)
    if user_type:
        roles.append(user_type)
    if user.is_staff:
        roles.append("administrator")
    return [_normalize_role(role) for role in roles if role]


def _primary_role(user):
    roles = _get_designation_names(user)
    return roles[0] if roles else "user"


def _has_any(user, allowed):
    return bool(set(_get_designation_names(user)) & set(allowed))


def _as_decimal(value, default="0"):
    try:
        candidate = value if value not in [None, ""] else default
        return Decimal(str(candidate))
    except (InvalidOperation, ValueError):
        raise ValueError("Amount and budget values must be valid numbers.")


def _get_file_list(request, *keys):
    files = []
    for key in keys:
        files.extend(request.FILES.getlist(key))
    return files


def _save_request_attachments(obj, files, user, replace=False):
    if replace:
        obj.attachments.all().delete()
    for file_obj in files:
        RequestAttachment.objects.create(
            request=obj,
            file=file_obj,
            original_name=file_obj.name,
            uploaded_by=user,
        )
    obj.document_names = list(obj.attachments.values_list("original_name", flat=True))
    obj.save(update_fields=["document_names", "updated_at"])


def _save_ta_attachments(obj, files, user, replace=False):
    if replace:
        obj.attachments.all().delete()
    for file_obj in files:
        TravelAllowanceAttachment.objects.create(
            travel_allowance=obj,
            file=file_obj,
            original_name=file_obj.name,
            uploaded_by=user,
        )
    obj.document_names = list(obj.attachments.values_list("original_name", flat=True))
    obj.save(update_fields=["document_names", "updated_at"])


def _save_observation_attachments(obj, files, user, kind, replace=False):
    if replace:
        obj.attachments.filter(attachment_kind=kind).delete()
    for file_obj in files:
        ObservationAttachment.objects.create(
            observation=obj,
            file=file_obj,
            original_name=file_obj.name,
            attachment_kind=kind,
            uploaded_by=user,
        )
    obj.response_document_names = list(
        obj.attachments.filter(
            attachment_kind=ObservationAttachmentKind.RESPONSE
        ).values_list("original_name", flat=True)
    )
    obj.save(update_fields=["response_document_names", "updated_at"])


def _log(workflow, actor, decision, from_status="", to_status="", remarks="", **links):
    return ActionLog.objects.create(
        workflow=workflow,
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        actor_role=_primary_role(actor) if getattr(actor, "is_authenticated", False) else "",
        decision=decision,
        from_status=from_status or "",
        to_status=to_status or "",
        remarks=remarks or "",
        **links,
    )


def _next_request_role(amount):
    if amount <= REQUEST_THRESHOLD_HOD:
        return "hod"
    if amount <= REQUEST_THRESHOLD_DEAN:
        return "dean"
    return "director"


def _next_escalation_role(role):
    if role == "hod":
        return "dean"
    if role == "dean":
        return "director"
    return "director"


def _role_status(role):
    return {
        "hod": RequestStatus.HOD_APPROVED,
        "dean": RequestStatus.DEAN_APPROVED,
        "director": RequestStatus.DIRECTOR_APPROVED,
    }.get(role, RequestStatus.APPROVED)


def _request_role_allowed(user, role):
    if role == "finance":
        return _has_any(user, FINANCE_ROLES)
    if role == "hod":
        return _has_any(user, HOD_ROLES | DEAN_ROLES | DIRECTOR_ROLES)
    if role == "dean":
        return _has_any(user, DEAN_ROLES | DIRECTOR_ROLES)
    if role == "director":
        return _has_any(user, DIRECTOR_ROLES)
    return False


def _users_for_roles(role_names):
    normalized = {_normalize_role(role) for role in role_names if role}
    if not normalized:
        return User.objects.none()
    designation_ids = HoldsDesignation.objects.filter(
        designation__name__in=normalized
    ).values_list("working_id", flat=True)
    extra_ids = ExtraInfo.objects.filter(user_type__in=normalized).values_list("user_id", flat=True)
    return User.objects.filter(Q(id__in=designation_ids) | Q(id__in=extra_ids)).distinct()


def _notify_users(sender, recipients, notif_type, message):
    seen = set()
    for recipient in recipients:
        if not recipient or recipient.id in seen:
            continue
        seen.add(recipient.id)
        audit_account_notif(sender, recipient, notif_type, message)


def _create_observation_for_anomaly(actor, request_obj=None, ta_obj=None, title="", details=""):
    workflow = WorkflowType.EXPENSE if request_obj else WorkflowType.TA
    observation = AuditObservation.objects.create(
        target_workflow=workflow,
        request=request_obj,
        travel_allowance=ta_obj,
        title=title,
        details=details,
        raised_by=actor,
    )
    _log(
        WorkflowType.AUDIT_OBSERVATION,
        actor,
        ActionDecision.CREATED,
        to_status=observation.status,
        remarks=details,
        observation=observation,
    )
    return observation


def _requests_for_role(user, view):
    qs = Request.objects.select_related("created_by_user").prefetch_related("action_logs", "attachments")
    if view == "mine":
        return qs.filter(created_by=user.id)
    if view == "finance" and _has_any(user, FINANCE_ROLES):
        return qs.filter(status=RequestStatus.SUBMITTED)
    if view == "hod" and _has_any(user, HOD_ROLES | DEAN_ROLES | DIRECTOR_ROLES):
        return qs.filter(status__in=[RequestStatus.FINANCE_VALIDATED, RequestStatus.ESCALATED], current_approver_role="hod")
    if view == "dean" and _has_any(user, DEAN_ROLES | DIRECTOR_ROLES):
        return qs.filter(status__in=[RequestStatus.FINANCE_VALIDATED, RequestStatus.ESCALATED], current_approver_role="dean")
    if view == "director" and _has_any(user, DIRECTOR_ROLES):
        return qs.filter(status__in=[RequestStatus.FINANCE_VALIDATED, RequestStatus.ESCALATED], current_approver_role="director")
    if view == "auditor" and _has_any(user, AUDITOR_ROLES):
        return qs.exclude(status=RequestStatus.DRAFT)
    if view == "all" and (_has_any(user, FINANCE_ROLES | AUDITOR_ROLES) or user.is_superuser):
        return qs
    raise PermissionError("You do not have access to this request view.")


def _ta_for_role(user, view):
    qs = TravelAllowance.objects.select_related("employee").prefetch_related("action_logs", "attachments")
    if view == "mine":
        return qs.filter(employee=user)
    if view == "finance" and _has_any(user, FINANCE_ROLES):
        return qs.filter(status__in=[TARequestStatus.SUBMITTED, TARequestStatus.APPROVED])
    if view == "authority" and _has_any(user, HOD_ROLES | DEAN_ROLES | DIRECTOR_ROLES):
        allowed_roles = []
        if _has_any(user, HOD_ROLES):
            allowed_roles.append("hod")
        if _has_any(user, DEAN_ROLES):
            allowed_roles.append("dean")
        if _has_any(user, DIRECTOR_ROLES):
            allowed_roles.append("director")
        return qs.filter(status=TARequestStatus.VERIFIED, high_value=True, current_approver_role__in=allowed_roles)
    if view == "auditor" and _has_any(user, AUDITOR_ROLES):
        return qs
    if view == "all" and (_has_any(user, FINANCE_ROLES | AUDITOR_ROLES) or user.is_superuser):
        return qs
    raise PermissionError("You do not have access to this TA view.")


def _observations_for_role(user, view):
    qs = AuditObservation.objects.select_related("request", "travel_allowance", "raised_by").prefetch_related("action_logs", "attachments")
    if view == "auditor" and _has_any(user, AUDITOR_ROLES):
        return qs
    if view == "all" and (_has_any(user, FINANCE_ROLES | AUDITOR_ROLES) or user.is_superuser):
        return qs
    filters = (
        Q(request__created_by=user.id)
        | Q(travel_allowance__employee=user)
        | Q(responded_by=user)
        | Q(raised_by=user)
    )
    if _has_any(user, FINANCE_ROLES):
        filters |= Q(request__current_approver_role="finance", request__status=RequestStatus.SUBMITTED)
        filters |= Q(travel_allowance__current_approver_role="finance", travel_allowance__status=TARequestStatus.SUBMITTED)
    if _has_any(user, HOD_ROLES):
        filters |= Q(
            request__current_approver_role="hod",
            request__status__in=[RequestStatus.FINANCE_VALIDATED, RequestStatus.ESCALATED],
        )
        filters |= Q(
            travel_allowance__current_approver_role="hod",
            travel_allowance__status=TARequestStatus.VERIFIED,
        )
    if _has_any(user, DEAN_ROLES):
        filters |= Q(
            request__current_approver_role="dean",
            request__status__in=[RequestStatus.FINANCE_VALIDATED, RequestStatus.ESCALATED],
        )
        filters |= Q(
            travel_allowance__current_approver_role="dean",
            travel_allowance__status=TARequestStatus.VERIFIED,
        )
    if _has_any(user, DIRECTOR_ROLES):
        filters |= Q(
            request__current_approver_role="director",
            request__status__in=[RequestStatus.FINANCE_VALIDATED, RequestStatus.ESCALATED],
        )
        filters |= Q(
            travel_allowance__current_approver_role="director",
            travel_allowance__status=TARequestStatus.VERIFIED,
        )
    return qs.filter(filters).distinct()


def _can_access_request_action(user, obj):
    if obj.status == RequestStatus.SUBMITTED and _has_any(user, FINANCE_ROLES):
        return True
    if obj.status in [RequestStatus.FINANCE_VALIDATED, RequestStatus.ESCALATED]:
        return _request_role_allowed(user, obj.current_approver_role or "director")
    if obj.status in [
        RequestStatus.HOD_APPROVED,
        RequestStatus.DEAN_APPROVED,
        RequestStatus.DIRECTOR_APPROVED,
        RequestStatus.APPROVED,
    ] and _has_any(user, FINANCE_ROLES):
        return True
    return False


def _can_access_ta_action(user, obj):
    if obj.status == TARequestStatus.SUBMITTED and _has_any(user, FINANCE_ROLES):
        return True
    if obj.status == TARequestStatus.VERIFIED and obj.high_value:
        return _request_role_allowed(user, obj.current_approver_role or "director")
    if obj.status in [TARequestStatus.VERIFIED, TARequestStatus.APPROVED] and _has_any(user, FINANCE_ROLES):
        return True
    return False


def _can_respond_to_observation(user, obj):
    if obj.request:
        if obj.request.created_by == user.id:
            return True
        return _request_role_allowed(user, obj.request.current_approver_role or "finance")
    if obj.travel_allowance:
        if obj.travel_allowance.employee_id == user.id:
            return True
        return _request_role_allowed(user, obj.travel_allowance.current_approver_role or "finance")
    return False


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def create_draft(request):
    try:
        request_type = str(request.data.get("type", "")).upper()
        if request_type not in RequestType.values:
            raise ValueError("Invalid request type. Use EXPENSE or VOUCHER.")
        if not request.data.get("department"):
            raise ValueError("Department is required.")

        draft_id = request.data.get("id")
        files = _get_file_list(request, "attachments", "documents", "files")
        if draft_id:
            obj = Request.objects.get(id=draft_id, created_by=request.user.id)
            if obj.status != RequestStatus.DRAFT:
                raise ValueError("Only draft requests can be edited.")
            obj.type = request_type
            obj.amount = _as_decimal(request.data.get("amount"))
            obj.department = request.data.get("department", "")
            obj.description = request.data.get("description", "")
            obj.budget_head = request.data.get("budget_head", "")
            obj.save()
            if files:
                _save_request_attachments(obj, files, request.user, replace=True)
        else:
            obj = Request.objects.create(
                type=request_type,
                amount=_as_decimal(request.data.get("amount")),
                department=request.data.get("department", ""),
                description=request.data.get("description", ""),
                budget_head=request.data.get("budget_head", ""),
                created_by=request.user.id,
                created_by_user=request.user,
            )
            if files:
                _save_request_attachments(obj, files, request.user)
            _log(WorkflowType.EXPENSE, request.user, ActionDecision.CREATED, to_status=obj.status, request=obj)
        return Response(RequestSerializer(obj).data, status=status.HTTP_201_CREATED)
    except Request.DoesNotExist:
        return Response({"error": "Draft not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def submit_request_view(request):
    try:
        obj = Request.objects.get(id=request.data.get("id"))
        if obj.created_by != request.user.id:
            return Response({"error": "Only the request owner can submit this request."}, status=403)
        if obj.status != RequestStatus.DRAFT:
            raise ValueError("Only draft requests can be submitted.")

        files = _get_file_list(request, "attachments", "documents", "files")
        if files:
            _save_request_attachments(obj, files, request.user, replace=bool(obj.attachments.exists()))

        if not obj.amount or not obj.department or not obj.type or not obj.budget_head:
            raise ValueError("Mandatory fields are missing.")
        if not obj.document_names:
            raise ValueError("Supporting documents must be uploaded.")

        # Check budget availability
        budget = _get_department_budget(obj.department, obj.budget_head)
        if not budget:
            raise ValueError(
                f"No budget allocated for {obj.department} - {obj.budget_head}. Please contact the director or finance team."
            )
        if obj.amount > budget.remaining_amount:
            raise ValueError(
                f"Requested amount (₹{obj.amount}) exceeds available departmental budget (₹{budget.remaining_amount}). Please contact your department head or director to allocate more budget."
            )

        old = obj.status
        obj.status = RequestStatus.SUBMITTED
        obj.current_approver_role = "finance"
        obj.assigned_at = timezone.now()
        obj.save(update_fields=["status", "current_approver_role", "assigned_at", "updated_at"])
        _log(WorkflowType.EXPENSE, request.user, ActionDecision.SUBMITTED, old, obj.status, request=obj)
        _notify_users(
            request.user,
            _users_for_roles(FINANCE_ROLES),
            "request_submitted",
            f"Request #{obj.id} was submitted and is waiting for finance validation.",
        )
        return Response(RequestSerializer(obj).data)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def list_requests(request):
    try:
        data = _requests_for_role(request.user, request.query_params.get("view", "mine"))
        return Response(RequestSerializer(data.order_by("-updated_at"), many=True).data)
    except PermissionError as exc:
        return Response({"error": str(exc)}, status=403)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def update_request_status_view(request):
    try:
        obj = Request.objects.get(id=request.data.get("id"))
        action = str(request.data.get("action", request.data.get("status", ""))).upper()
        remarks = request.data.get("remarks", "")
        old = obj.status

        if action in {"FINANCE_VALIDATED", "VALIDATE"} and _has_any(request.user, FINANCE_ROLES) and obj.status == RequestStatus.SUBMITTED:
            obj.validation_remarks = remarks
            # Check budget from DepartmentBudget table
            budget = _get_department_budget(obj.department, obj.budget_head)
            authority_role = _next_request_role(obj.amount)
            if obj.created_by == request.user.id:
                authority_role = _next_escalation_role(authority_role)
            
            if not budget:
                obj.status = RequestStatus.ESCALATED
                obj.current_approver_role = "director"
                obj.anomaly_reason = f"No budget allocated for {obj.department} - {obj.budget_head}. Director approval required."
                decision = ActionDecision.ESCALATED
                _create_observation_for_anomaly(
                    request.user,
                    request_obj=obj,
                    title="Missing budget allocation",
                    details=obj.anomaly_reason,
                )
            elif obj.amount > budget.remaining_amount:
                obj.status = RequestStatus.ESCALATED
                obj.current_approver_role = _next_escalation_role(authority_role)
                obj.anomaly_reason = "Requested amount exceeds available departmental budget."
                decision = ActionDecision.ESCALATED
                _create_observation_for_anomaly(
                    request.user,
                    request_obj=obj,
                    title="Budget anomaly",
                    details=obj.anomaly_reason,
                )
            else:
                obj.status = RequestStatus.FINANCE_VALIDATED
                obj.current_approver_role = authority_role
                decision = ActionDecision.VALIDATED
            obj.assigned_at = timezone.now()
            obj.escalated_at = timezone.now() if obj.status == RequestStatus.ESCALATED else None
            obj.save()
            _notify_users(
                request.user,
                _users_for_roles({obj.current_approver_role}),
                "authority_queue",
                f"Request #{obj.id} is waiting for {obj.current_approver_role.upper()} approval.",
            )
        elif action in {"REJECTED", "REJECT"}:
            if not remarks:
                return Response({"error": "Rejection requires remarks."}, status=400)
            if obj.status not in [RequestStatus.SUBMITTED, RequestStatus.FINANCE_VALIDATED, RequestStatus.ESCALATED]:
                return Response({"error": "You cannot reject this request at this stage."}, status=403)
            if not _can_access_request_action(request.user, obj):
                return Response({"error": "You cannot reject this request at this stage."}, status=403)
            obj.status = RequestStatus.REJECTED
            obj.rejection_remarks = remarks
            obj.current_approver_role = ""
            obj.assigned_at = None
            decision = ActionDecision.REJECTED
            obj.save()
            if obj.created_by_user:
                _notify_users(
                    request.user,
                    [obj.created_by_user],
                    "request_rejected",
                    f"Request #{obj.id} was rejected. Remarks: {remarks}",
                )
        elif action in {"APPROVED", "APPROVE"} and obj.status in [RequestStatus.FINANCE_VALIDATED, RequestStatus.ESCALATED]:
            assigned_role = obj.current_approver_role or "director"
            if obj.created_by == request.user.id and assigned_role != "director":
                next_role = _next_escalation_role(assigned_role)
                obj.status = RequestStatus.ESCALATED
                obj.current_approver_role = next_role
                obj.escalated_at = timezone.now()
                obj.assigned_at = timezone.now()
                obj.anomaly_reason = "Approval rerouted due to segregation-of-duties."
                obj.save()
                _create_observation_for_anomaly(
                    request.user,
                    request_obj=obj,
                    title="Segregation of duties escalation",
                    details=obj.anomaly_reason,
                )
                _log(WorkflowType.EXPENSE, request.user, ActionDecision.ESCALATED, old, obj.status, obj.anomaly_reason, request=obj)
                _notify_users(
                    request.user,
                    _users_for_roles({next_role}),
                    "request_escalated",
                    f"Request #{obj.id} was escalated to {next_role.upper()} due to segregation-of-duties.",
                )
                return Response(RequestSerializer(obj).data)
            if not _request_role_allowed(request.user, assigned_role):
                return Response({"error": "You are not the assigned approving authority."}, status=403)
            obj.approval_remarks = remarks
            if assigned_role in ["hod", "dean"]:
                obj.status = RequestStatus.ESCALATED
                obj.current_approver_role = "director"
                obj.assigned_at = timezone.now()
                obj.escalated_at = timezone.now()
                decision = ActionDecision.ESCALATED
                _log(WorkflowType.EXPENSE, request.user, decision, old, obj.status, remarks, request=obj)
                _notify_users(
                    request.user,
                    _users_for_roles({"director"}),
                    "request_escalated",
                    f"Request #{obj.id} was escalated to DIRECTOR for final approval.",
                )
            else:
                obj.status = RequestStatus.APPROVED
                obj.current_approver_role = ""
                obj.assigned_at = None
                decision = ActionDecision.APPROVED
                obj.save()
                if obj.created_by_user:
                    _notify_users(
                        request.user,
                        [obj.created_by_user],
                        "request_approved",
                        f"Request #{obj.id} was approved.",
                    )
            obj.save()
        elif action in {"CLOSED", "CLOSE", "PROCESSED"} and _has_any(request.user, FINANCE_ROLES) and obj.status in [
            RequestStatus.HOD_APPROVED,
            RequestStatus.DEAN_APPROVED,
            RequestStatus.DIRECTOR_APPROVED,
            RequestStatus.APPROVED,
        ]:
            # Deduct from budget when processing the request
            budget = DepartmentBudget.objects.filter(
                department=obj.department,
                budget_head=obj.budget_head,
                is_active=True,
            ).first()
            if budget and budget.remaining_amount >= obj.amount:
                budget.remaining_amount -= obj.amount
                budget.save()
            obj.status = RequestStatus.CLOSED
            obj.processed_at = timezone.now()
            obj.closed_at = timezone.now()
            decision = ActionDecision.CLOSED
            obj.save()
        else:
            return Response({"error": "Invalid action for the current role or request status."}, status=400)

        _log(WorkflowType.EXPENSE, request.user, decision, old, obj.status, remarks, request=obj)
        return Response(RequestSerializer(obj).data)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def create_ta(request):
    try:
        required = ["department", "travel_from", "travel_to", "purpose", "amount_claimed"]
        missing = [field for field in required if not request.data.get(field)]
        if missing:
            raise ValueError(f"Missing mandatory fields: {', '.join(missing)}")

        files = _get_file_list(request, "attachments", "documents", "files")
        if not files:
            raise ValueError("Supporting documents must be uploaded.")

        start_date = request.data.get("start_date")
        end_date = request.data.get("end_date")
        if start_date and end_date:
            from datetime import datetime
            start = datetime.fromisoformat(start_date).date()
            end = datetime.fromisoformat(end_date).date()
            if start >= end:
                raise ValueError("Start date must be before end date.")

        amount = _as_decimal(request.data.get("amount_claimed"))
        obj = TravelAllowance.objects.create(
            employee=request.user,
            employee_name=request.user.get_full_name() or request.user.username,
            department=request.data.get("department"),
            travel_from=request.data.get("travel_from"),
            travel_to=request.data.get("travel_to"),
            start_date=start_date or None,
            end_date=end_date or None,
            purpose=request.data.get("purpose"),
            amount_claimed=amount,
            high_value=amount > TA_HIGH_VALUE_THRESHOLD,
            current_approver_role="finance",
            assigned_at=timezone.now(),
        )
        _save_ta_attachments(obj, files, request.user)
        _log(WorkflowType.TA, request.user, ActionDecision.SUBMITTED, to_status=obj.status, travel_allowance=obj)
        _notify_users(
            request.user,
            _users_for_roles(FINANCE_ROLES),
            "ta_submitted",
            f"TA #{obj.id} was submitted and is waiting for finance verification.",
        )
        return Response(TravelAllowanceSerializer(obj).data, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def list_ta(request):
    try:
        data = _ta_for_role(request.user, request.query_params.get("view", "mine"))
        return Response(TravelAllowanceSerializer(data.order_by("-updated_at"), many=True).data)
    except PermissionError as exc:
        return Response({"error": str(exc)}, status=403)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def update_ta(request):
    try:
        obj = TravelAllowance.objects.get(id=request.data.get("id"))
        action = str(request.data.get("action", "")).upper()
        remarks = request.data.get("remarks", "")
        old = obj.status
        if action in {"VERIFY", "VERIFIED"} and _has_any(request.user, FINANCE_ROLES) and obj.status == TARequestStatus.SUBMITTED:
            obj.finance_remarks = remarks
            if obj.high_value:
                authority_role = _next_request_role(obj.amount_claimed)
                if obj.employee_id == request.user.id:
                    authority_role = _next_escalation_role(authority_role)
                obj.status = TARequestStatus.VERIFIED
                obj.current_approver_role = authority_role
                obj.assigned_at = timezone.now()
                decision = ActionDecision.VALIDATED
                obj.save()
                _notify_users(
                    request.user,
                    _users_for_roles({authority_role}),
                    "ta_authority_queue",
                    f"High-value TA #{obj.id} is waiting for {authority_role.upper()} approval.",
                )
            else:
                obj.status = TARequestStatus.CLOSED
                obj.current_approver_role = ""
                obj.closed_at = timezone.now()
                obj.assigned_at = None
                decision = ActionDecision.CLOSED
                obj.save()
                if obj.employee:
                    _notify_users(request.user, [obj.employee], "ta_closed", f"TA #{obj.id} was verified and closed.")
        elif action in {"APPROVE", "APPROVED"} and obj.status == TARequestStatus.VERIFIED and obj.high_value:
            assigned_role = obj.current_approver_role or "director"
            if obj.employee_id == request.user.id:
                next_role = _next_escalation_role(assigned_role)
                if next_role == assigned_role == "director":
                    return Response({"error": "Cannot approve own TA claim at director level."}, status=403)
                obj.current_approver_role = next_role
                obj.escalated_at = timezone.now()
                obj.assigned_at = timezone.now()
                obj.save(update_fields=["current_approver_role", "escalated_at", "assigned_at", "updated_at"])
                _create_observation_for_anomaly(
                    request.user,
                    ta_obj=obj,
                    title="TA segregation-of-duties escalation",
                    details="High-value TA approval was rerouted due to segregation-of-duties.",
                )
                _log(WorkflowType.TA, request.user, ActionDecision.ESCALATED, old, obj.status, "TA rerouted due to segregation-of-duties.", travel_allowance=obj)
                _notify_users(
                    request.user,
                    _users_for_roles({next_role}),
                    "ta_escalated",
                    f"TA #{obj.id} was escalated to {next_role.upper()} due to segregation-of-duties.",
                )
                return Response(TravelAllowanceSerializer(obj).data)
            if not _request_role_allowed(request.user, assigned_role):
                return Response({"error": "You are not the assigned approving authority."}, status=403)
            obj.status = TARequestStatus.APPROVED
            obj.approval_remarks = remarks
            obj.current_approver_role = ""
            obj.assigned_at = timezone.now()
            decision = ActionDecision.APPROVED
            obj.save()
            _notify_users(request.user, _users_for_roles(FINANCE_ROLES), "ta_finance_close", f"TA #{obj.id} was approved and is waiting for finance closure.")
            if obj.employee:
                _notify_users(request.user, [obj.employee], "ta_approved", f"TA #{obj.id} was approved.")
        elif action in {"CLOSE", "CLOSED"} and _has_any(request.user, FINANCE_ROLES) and obj.status in [TARequestStatus.VERIFIED, TARequestStatus.APPROVED]:
            if obj.high_value and obj.status != TARequestStatus.APPROVED:
                raise ValueError("High-value TA must be approved before closure.")
            obj.status = TARequestStatus.CLOSED
            obj.current_approver_role = ""
            obj.closed_at = timezone.now()
            obj.assigned_at = None
            decision = ActionDecision.CLOSED
            obj.save()
        elif action in {"REJECT", "REJECTED"}:
            if not remarks:
                return Response({"error": "Rejection requires remarks."}, status=400)
            if not _can_access_ta_action(request.user, obj):
                return Response({"error": "You cannot reject this TA form at this stage."}, status=403)
            obj.status = TARequestStatus.REJECTED
            obj.current_approver_role = ""
            obj.rejection_remarks = remarks
            decision = ActionDecision.REJECTED
            obj.save()
            if obj.employee:
                _notify_users(request.user, [obj.employee], "ta_rejected", f"TA #{obj.id} was rejected. Remarks: {remarks}")
        else:
            return Response({"error": "Invalid TA action for the current role/status."}, status=400)
        _log(WorkflowType.TA, request.user, decision, old, obj.status, remarks, travel_allowance=obj)
        return Response(TravelAllowanceSerializer(obj).data)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def create_observation(request):
    try:
        if not _has_any(request.user, AUDITOR_ROLES | FINANCE_ROLES):
            return Response({"error": "Only auditors or finance administrators can raise observations."}, status=403)
        target = request.data.get("target_workflow", WorkflowType.EXPENSE)
        obj = AuditObservation.objects.create(
            target_workflow=target,
            request_id=request.data.get("request") or None,
            travel_allowance_id=request.data.get("travel_allowance") or None,
            title=request.data.get("title", ""),
            details=request.data.get("details", ""),
            response_deadline=request.data.get("response_deadline") or None,
            raised_by=request.user,
        )
        if not obj.title or not obj.details:
            obj.delete()
            raise ValueError("Observation title and details are required.")
        files = _get_file_list(request, "attachments", "documents", "files")
        if files:
            _save_observation_attachments(obj, files, request.user, ObservationAttachmentKind.OBSERVATION)
        _log(WorkflowType.AUDIT_OBSERVATION, request.user, ActionDecision.CREATED, to_status=obj.status, observation=obj)
        recipients = []
        if obj.request and obj.request.created_by_user:
            recipients.append(obj.request.created_by_user)
        if obj.travel_allowance and obj.travel_allowance.employee:
            recipients.append(obj.travel_allowance.employee)
        _notify_users(request.user, recipients, "observation_created", f"Audit observation #{obj.id} was raised.")
        return Response(
            AuditObservationSerializer(obj, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def list_observations(request):
    try:
        data = _observations_for_role(request.user, request.query_params.get("view", "mine"))
        return Response(
            AuditObservationSerializer(
                data.order_by("-updated_at"), many=True, context={"request": request}
            ).data
        )
    except PermissionError as exc:
        return Response({"error": str(exc)}, status=403)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def update_observation(request):
    try:
        obj = AuditObservation.objects.get(id=request.data.get("id"))
        action = str(request.data.get("action", "")).upper()
        remarks = request.data.get("remarks", "")
        old = obj.status
        if action == "RESPOND" and obj.status == AuditObservationStatus.OPEN:
            if not _can_respond_to_observation(request.user, obj):
                return Response({"error": "You are not allowed to respond to this observation."}, status=403)
            response_text = request.data.get("response_text", remarks)
            files = _get_file_list(request, "response_attachments", "attachments", "documents", "files")
            if not response_text:
                raise ValueError("Response is required.")
            if not files:
                raise ValueError("Supporting evidence documents are required.")
            obj.response_text = response_text
            obj.responded_by = request.user
            obj.status = AuditObservationStatus.RESPONDED
            obj.save()
            _save_observation_attachments(obj, files, request.user, ObservationAttachmentKind.RESPONSE, replace=True)
            decision = ActionDecision.RESPONDED
            if obj.raised_by:
                _notify_users(request.user, [obj.raised_by], "observation_responded", f"Audit observation #{obj.id} received a response.")
        elif action == "CLOSE" and _has_any(request.user, AUDITOR_ROLES | FINANCE_ROLES) and obj.status == AuditObservationStatus.RESPONDED:
            obj.closure_remarks = remarks
            obj.closed_by = request.user
            obj.closed_at = timezone.now()
            obj.status = AuditObservationStatus.CLOSED
            decision = ActionDecision.CLOSED
            obj.save()
            if obj.responded_by:
                _notify_users(request.user, [obj.responded_by], "observation_closed", f"Audit observation #{obj.id} was closed.")
        elif action == "REOPEN" and _has_any(request.user, AUDITOR_ROLES | FINANCE_ROLES) and obj.status in [AuditObservationStatus.RESPONDED, AuditObservationStatus.CLOSED]:
            obj.closure_remarks = remarks
            obj.closed_by = None
            obj.closed_at = None
            obj.status = AuditObservationStatus.OPEN
            decision = ActionDecision.UPDATED
            obj.save()
        else:
            return Response({"error": "Invalid observation action for current status/role."}, status=400)
        _log(WorkflowType.AUDIT_OBSERVATION, request.user, decision, old, obj.status, remarks, observation=obj)
        return Response(AuditObservationSerializer(obj, context={"request": request}).data)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def reports(request):
    if not (_has_any(request.user, FINANCE_ROLES | DEAN_ROLES | DIRECTOR_ROLES | AUDITOR_ROLES) or request.user.is_superuser):
        return Response({"error": "You do not have report access."}, status=403)
    requests = Request.objects.all()
    tas = TravelAllowance.objects.all()
    observations = AuditObservation.objects.all()
    payload = {
        "counts": {
            "requests": requests.count(),
            "ta_forms": tas.count(),
            "observations": observations.count(),
            "open_observations": observations.filter(status=AuditObservationStatus.OPEN).count(),
        },
        "requests_by_status": _status_counts(requests),
        "ta_by_status": _status_counts(tas),
        "observations_by_status": _status_counts(observations),
        "transactions": ActionLogSerializer(ActionLog.objects.all()[:100], many=True).data,
    }
    return Response(payload)


def _status_counts(qs):
    data = {}
    for row in qs.values("status"):
        data[row["status"]] = data.get(row["status"], 0) + 1
    return data


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def export_report(request):
    if not (_has_any(request.user, FINANCE_ROLES | DEAN_ROLES | DIRECTOR_ROLES | AUDITOR_ROLES) or request.user.is_superuser):
        return Response({"error": "You do not have report access."}, status=403)
    rows = ["workflow,id,decision,from_status,to_status,actor,remarks,created_at"]
    for log in ActionLog.objects.select_related("actor").all().order_by("-created_at"):
        actor = log.actor.username if log.actor else "System"
        remarks = (log.remarks or "").replace('"', '""').replace("\n", " ")
        rows.append(f'{log.workflow},{log.id},{log.decision},{log.from_status},{log.to_status},{actor},"{remarks}",{log.created_at.isoformat()}')
    response = HttpResponse("\n".join(rows), content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="audit_account_report.csv"'
    return response


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def list_department_budgets(request):
    if not _has_any(request.user, DIRECTOR_ROLES | FINANCE_ROLES | AUDITOR_ROLES):
        return Response({"error": "Only director, finance, or auditor roles can view budgets."}, status=403)
    _ensure_default_department_budgets()
    budgets = DepartmentBudget.objects.filter(is_active=True).order_by("department", "budget_head")
    data = []
    for budget in budgets:
        data.append({
            "id": budget.id,
            "department": budget.department,
            "budget_head": budget.budget_head,
            "allocated_amount": budget.allocated_amount,
            "remaining_amount": budget.remaining_amount,
            "updated_at": budget.updated_at,
        })
    return Response(data)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def update_department_budget(request):
    if not _has_any(request.user, DIRECTOR_ROLES):
        return Response({"error": "Only director can update department budgets."}, status=403)
    try:
        budget_id = request.data.get("id")
        additional_amount = _as_decimal(request.data.get("additional_amount", "0"))
        if additional_amount <= 0:
            raise ValueError("Additional amount must be positive.")

        budget = DepartmentBudget.objects.get(id=budget_id, is_active=True)
        budget.allocated_amount += additional_amount
        budget.remaining_amount += additional_amount
        budget.save()

        # Log the budget update
        _log(
            WorkflowType.EXPENSE,
            request.user,
            ActionDecision.UPDATED,
            remarks=f"Added ₹{additional_amount} to {budget.department} - {budget.budget_head} budget",
        )

        return Response({
            "id": budget.id,
            "department": budget.department,
            "budget_head": budget.budget_head,
            "allocated_amount": budget.allocated_amount,
            "remaining_amount": budget.remaining_amount,
            "updated_at": budget.updated_at,
        })
    except DepartmentBudget.DoesNotExist:
        return Response({"error": "Budget not found."}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=400)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def create_department_budget(request):
    if not _has_any(request.user, DIRECTOR_ROLES):
        return Response({"error": "Only director can create department budgets."}, status=403)
    try:
        department = str(request.data.get("department", "")).strip()
        budget_head = str(request.data.get("budget_head", "")).strip()
        amount = _as_decimal(request.data.get("amount", "0"))
        if not department:
            raise ValueError("Department is required.")
        if not budget_head:
            raise ValueError("Budget head is required.")
        if amount <= 0:
            raise ValueError("Allocation amount must be positive.")

        existing = DepartmentBudget.objects.filter(
            department__iexact=department,
            budget_head__iexact=budget_head,
            is_active=True,
        ).first()
        if existing:
            existing.allocated_amount += amount
            existing.remaining_amount += amount
            existing.save()
            budget = existing
            action = "Updated"
        else:
            budget = DepartmentBudget.objects.create(
                department=department,
                budget_head=budget_head,
                allocated_amount=amount,
                remaining_amount=amount,
                is_active=True,
            )
            action = "Created"

        _log(
            WorkflowType.EXPENSE,
            request.user,
            ActionDecision.UPDATED if action == "Updated" else ActionDecision.CREATED,
            remarks=f"{action} budget for {budget.department} - {budget.budget_head}: ₹{amount}",
        )

        return Response({
            "id": budget.id,
            "department": budget.department,
            "budget_head": budget.budget_head,
            "allocated_amount": budget.allocated_amount,
            "remaining_amount": budget.remaining_amount,
            "updated_at": budget.updated_at,
        })
    except Exception as e:
        return Response({"error": str(e)}, status=400)


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def director_auditor_dashboard(request):
    if not _has_any(request.user, DIRECTOR_ROLES | AUDITOR_ROLES):
        return Response({"error": "Only director or auditor roles can access this dashboard."}, status=403)

    # Get all requests and TAs that are not draft
    requests = Request.objects.exclude(status=RequestStatus.DRAFT).select_related("created_by_user").prefetch_related("action_logs", "attachments")
    tas = TravelAllowance.objects.all().select_related("employee").prefetch_related("action_logs", "attachments")
    observations = AuditObservation.objects.all().select_related("request", "travel_allowance", "raised_by").prefetch_related("action_logs", "attachments")

    # For director: show escalated requests, approved requests waiting for closure, and all observations
    # For auditor: show all requests, TAs, and observations
    if _has_any(request.user, DIRECTOR_ROLES):
        requests = requests.filter(
            Q(status__in=[RequestStatus.ESCALATED, RequestStatus.HOD_APPROVED, RequestStatus.DEAN_APPROVED, RequestStatus.DIRECTOR_APPROVED, RequestStatus.APPROVED, RequestStatus.PROCESSED]) |
            Q(status=RequestStatus.CLOSED, closed_at__gte=timezone.now() - timezone.timedelta(days=30))
        )
        tas = tas.filter(
            Q(status__in=[TARequestStatus.APPROVED, TARequestStatus.CLOSED]) |
            Q(status=TARequestStatus.CLOSED, closed_at__gte=timezone.now() - timezone.timedelta(days=30))
        )
    # Auditors see everything

    budgets = DepartmentBudget.objects.filter(is_active=True).order_by("department", "budget_head")
    data = {
        "requests": RequestSerializer(requests.order_by("-updated_at")[:50], many=True).data,
        "ta_forms": TravelAllowanceSerializer(tas.order_by("-updated_at")[:50], many=True).data,
        "observations": AuditObservationSerializer(observations.order_by("-updated_at")[:50], many=True, context={"request": request}).data,
        "budgets": [
            {
                "id": budget.id,
                "department": budget.department,
                "budget_head": budget.budget_head,
                "allocated_amount": budget.allocated_amount,
                "remaining_amount": budget.remaining_amount,
                "updated_at": budget.updated_at,
            }
            for budget in budgets
        ],
    }

    return Response(data)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def flag_anomaly(request):
    if not _has_any(request.user, DIRECTOR_ROLES | AUDITOR_ROLES):
        return Response({"error": "Only director or auditor can flag anomalies."}, status=403)
    try:
        workflow_type = request.data.get("workflow_type")
        target_id = request.data.get("target_id")
        title = request.data.get("title", "").strip()
        details = request.data.get("details", "").strip()

        if not title or not details:
            raise ValueError("Title and details are required for anomaly.")

        if workflow_type == "EXPENSE":
            target_obj = Request.objects.get(id=target_id)
            observation = _create_observation_for_anomaly(
                request.user,
                request_obj=target_obj,
                title=title,
                details=details,
            )
        elif workflow_type == "TA":
            target_obj = TravelAllowance.objects.get(id=target_id)
            observation = _create_observation_for_anomaly(
                request.user,
                ta_obj=target_obj,
                title=title,
                details=details,
            )
        else:
            raise ValueError("Invalid workflow type.")

        return Response(AuditObservationSerializer(observation, context={"request": request}).data, status=201)
    except (Request.DoesNotExist, TravelAllowance.DoesNotExist):
        return Response({"error": "Target not found."}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=400)


@api_view(["GET"])
def health_check(request):
    return Response({"status": "Audit Account API working"})
