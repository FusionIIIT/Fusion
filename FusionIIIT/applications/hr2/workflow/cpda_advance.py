"""CPDA Advance multi-step workflow: Faculty → HOD → Director → Accountant."""

import re

from django.utils import timezone

from applications.globals.models import Designation, ExtraInfo, HoldsDesignation

WF_SUBMITTED = "submitted"
WF_HOD_VERIFIED = "hod_verified"
WF_HOD_NOT_VERIFIED = "hod_not_verified"
WF_FORWARDED_DIRECTOR = "forwarded_to_director"
WF_DIRECTOR_APPROVED = "director_approved"
WF_DIRECTOR_REJECTED = "director_rejected"
WF_ACCOUNTANT_PROCESSED = "accountant_processed"

TERMINAL_STATUSES = frozenset(
    {WF_HOD_NOT_VERIFIED, WF_DIRECTOR_REJECTED, WF_ACCOUNTANT_PROCESSED}
)


def append_workflow_event(form, new_status, username, remarks="", **extra_fields):
    """Set workflow_status, append workflow_history, and apply optional field updates."""
    hist = list(form.workflow_history or [])
    hist.append(
        {
            "status": new_status,
            "by": username,
            "remarks": (remarks or "").strip(),
            "at": timezone.now().isoformat(),
        }
    )
    form.workflow_status = new_status
    form.workflow_history = hist
    for key, val in extra_fields.items():
        setattr(form, key, val)
    update_fields = ["workflow_status", "workflow_history"] + list(extra_fields.keys())
    form.save(update_fields=list(dict.fromkeys(update_fields)))


def resolve_hod_for_applicant(applicant_user):
    """Return (hod_username, hod_designation_name) or (None, None)."""
    extra = (
        ExtraInfo.objects.filter(user=applicant_user)
        .select_related("department")
        .first()
    )
    if not extra or not extra.department:
        return None, None
    dept_name = (extra.department.name or "").strip()
    if not dept_name:
        return None, None
    candidates = [f"HOD ({dept_name})", f"{dept_name} HOD"]
    for desig_name in candidates:
        if not Designation.objects.filter(name=desig_name).exists():
            continue
        qs = HoldsDesignation.objects.filter(designation__name=desig_name).select_related(
            "working"
        )
        # Prefer seeded workflow HOD accounts (hod_cse, …) over other users who may
        # also hold the same designation (e.g. legacy data where .first() was vkjain).
        hd = (
            qs.filter(working__username__startswith="hod_")
            .order_by("working__username")
            .first()
        )
        if not hd:
            hd = qs.first()
        if hd and hd.working_id:
            return hd.working.username, desig_name
    return None, None


def resolve_director():
    """Prefer the canonical ``director`` account when multiple users hold Director."""
    qs = HoldsDesignation.objects.filter(designation__name__iexact="Director").select_related(
        "working"
    )
    hd = qs.filter(working__username__iexact="director").first()
    if not hd:
        hd = qs.order_by("working__username").first()
    if hd and hd.working_id:
        return hd.working.username, "Director"
    return None, None


def resolve_accountant():
    """Prefer the canonical ``accountant`` account when multiple users hold Accountant."""
    qs = HoldsDesignation.objects.filter(designation__name__iexact="Accountant").select_related(
        "working"
    )
    hd = qs.filter(working__username__iexact="accountant").first()
    if not hd:
        hd = qs.order_by("working__username").first()
    if hd and hd.working_id:
        return hd.working.username, "Accountant"
    return None, None


def designation_is_hod(name):
    if not name:
        return False
    return bool(re.match(r"^HOD \(.+\)\s*$", name.strip()))


def hod_covers_applicant(hod_designation_name, applicant_user):
    m = re.match(r"HOD \((.+)\)", (hod_designation_name or "").strip())
    if not m:
        return False
    dept = m.group(1).strip()
    extra = (
        ExtraInfo.objects.filter(user=applicant_user)
        .select_related("department")
        .first()
    )
    return bool(
        extra and extra.department and (extra.department.name or "").strip() == dept
    )


def designation_is_director(name):
    return (name or "").strip().lower() == "director"


def designation_is_accountant(name):
    return (name or "").strip().lower() == "accountant"


def sync_file_extra_workflow(file_obj, workflow_status):
    extra = dict(file_obj.file_extra_JSON or {})
    extra["workflow_status"] = workflow_status
    file_obj.file_extra_JSON = extra
    file_obj.save(update_fields=["file_extra_JSON"])
