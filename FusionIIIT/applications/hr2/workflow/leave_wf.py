"""Leave multi-step workflow: Employee → HOD → HR Admin.

This mirrors the legacy ``applications.leave`` pipeline (replacement →
sanctioning authority → officer) but is implemented on ``hr2.LeaveForm``
plus file tracking, aligned with other HR2 forms (CPDA, LTC).
"""

import re

from django.utils import timezone

from applications.globals.models import Designation, ExtraInfo, HoldsDesignation

WF_AWAITING_SUBSTITUTES = "awaiting_substitutes"
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


def check_and_advance_substitute_consent(leave_form):
    """Check if all substitute nominations for a leave form are accepted.

    If all are accepted (BR-HR-019 consent gate), advance the workflow from
    ``awaiting_substitutes`` to ``submitted`` and forward the file to HOD.

    Returns:
        (advanced: bool, message: str)
    """
    from applications.hr2.models import SubstituteNomination

    nominations = SubstituteNomination.objects.filter(leave_form=leave_form)
    if not nominations.exists():
        return False, "No substitute nominations found."

    pending = nominations.filter(consent_status='pending').count()
    declined = nominations.filter(consent_status='declined').count()

    if declined > 0:
        return False, "One or more substitutes declined the request."

    if pending > 0:
        return False, f"{pending} substitute(s) have not yet responded."

    # All accepted — advance workflow if still awaiting
    if leave_form.workflow_status != WF_AWAITING_SUBSTITUTES:
        return False, "Leave is not in awaiting_substitutes state."

    from applications.filetracking.models import File
    from applications.hr2.services import forward_form_file, create_form_file
    from applications.hr2.constants.form_types import FormType

    # Resolve HOD and forward
    hod_username, hod_designation = resolve_hod_for_applicant(leave_form.created_by)

    # BR-HR-028: Director self-sanction
    is_director = HoldsDesignation.objects.filter(
        working=leave_form.created_by, designation__name__iexact="Director"
    ).exists()
    if is_director:
        hod_username = leave_form.created_by.username
        hod_designation = "Director"

    if not hod_username:
        return False, "No HOD configured for applicant's department."

    append_workflow_event(
        leave_form,
        WF_SUBMITTED,
        leave_form.created_by.username,
        "All substitutes accepted — forwarded to HOD",
    )

    # Find the file tracking entry for this leave and forward it
    try:
        file_obj = File.objects.filter(
            src_object_id=str(leave_form.id),
        ).order_by('-id').first()

        if file_obj:
            forward_form_file(
                file_id=str(file_obj.id),
                receiver=hod_username,
                receiver_designation=hod_designation,
                remarks="All substitutes consented — forwarded for approval",
                file_extra_JSON={
                    "type": FormType.LEAVE,
                    "workflow_status": WF_SUBMITTED,
                },
            )
            sync_file_extra_workflow(file_obj, WF_SUBMITTED)
    except Exception:
        pass

    return True, "All substitutes accepted. Leave forwarded to HOD."
