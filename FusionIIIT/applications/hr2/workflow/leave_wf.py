"""Leave multi-step workflow: Employee → HOD → HR Admin.

This mirrors the legacy ``applications.leave`` pipeline (replacement →
sanctioning authority → officer) but is implemented on ``hr2.LeaveForm``
plus file tracking, aligned with other HR2 forms (CPDA, LTC).
"""

import re

from django.utils import timezone

from applications.globals.models import Designation, ExtraInfo, HoldsDesignation

WF_SUBMITTED = "submitted"
WF_HOD_APPROVED = "hod_approved"
WF_HOD_REJECTED = "hod_rejected"
WF_HR_APPROVED = "hr_approved"
WF_HR_REJECTED = "hr_rejected"

TERMINAL_STATUSES = frozenset(
    {WF_HOD_REJECTED, WF_HR_APPROVED, WF_HR_REJECTED}
)


def archive_tracked_file_if_workflow_closed(file_id, workflow_status: str) -> None:
    """Move the file to HR file-tracking archive when the workflow cannot progress further."""
    if workflow_status not in TERMINAL_STATUSES:
        return
    from applications.hr2.services import archive_form_file

    archive_form_file(file_id=str(file_id))


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
    
    dept_name = None
    if extra and extra.department:
        dept_name = (extra.department.name or "").strip()
        
    candidates = []
    if dept_name:
        candidates = [f"HOD ({dept_name})", f"{dept_name} HOD"]
        
    # If no department, or to ensure we always find an HOD, append a fallback
    candidates.append("HOD (CSE)")
    
    for desig_name in candidates:
        if not Designation.objects.filter(name=desig_name).exists():
            continue
        qs = HoldsDesignation.objects.filter(designation__name=desig_name).select_related(
            "working"
        )
        # Prefer seeded workflow HOD accounts (hod_cse, …) over other users
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


def resolve_hr_admin():
    """Prefer the canonical `hr_admin` account when multiple users hold HR Admin."""
    qs = HoldsDesignation.objects.filter(designation__name__iexact="HR Admin").select_related(
        "working"
    )
    hd = qs.filter(working__username__iexact="hr_admin").first()
    if not hd:
        hd = qs.filter(working__username__iexact="hradmin").first()
    if not hd:
        hd = qs.order_by("working__username").first()
    if hd and hd.working_id:
        return hd.working.username, "HR Admin"
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


def designation_is_hr_admin(name):
    return (name or "").strip().lower() == "hr admin"


def sync_file_extra_workflow(file_obj, workflow_status):
    extra = dict(file_obj.file_extra_JSON or {})
    extra["workflow_status"] = workflow_status
    file_obj.file_extra_JSON = extra
    file_obj.save(update_fields=["file_extra_JSON"])
