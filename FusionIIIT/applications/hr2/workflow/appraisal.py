"""Appraisal workflow: submit to chosen approver (e.g. HR Admin) → approve or reject (no further routing)."""

from django.utils import timezone

from applications.hr2.constants.form_types import FormType

WF_SUBMITTED = "submitted"
WF_FORWARDED_REVIEWER = "forwarded_to_reviewer"
WF_REVIEWER_APPROVED = "reviewer_approved"
WF_REVIEWER_REJECTED = "reviewer_rejected"
WF_HR_APPROVED = "hr_approved"  # Legacy/Direct if needed
WF_HR_REJECTED = "hr_rejected"

TERMINAL_STATUSES = frozenset(
    {WF_REVIEWER_APPROVED, WF_REVIEWER_REJECTED, WF_HR_APPROVED, WF_HR_REJECTED}
)


def append_workflow_event(form, new_status, username, remarks="", **extra_fields):
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


def sync_file_extra_workflow(file_obj, workflow_status):
    extra = dict(file_obj.file_extra_JSON or {})
    extra["type"] = FormType.APPRAISAL
    extra["workflow_status"] = workflow_status
    file_obj.file_extra_JSON = extra
    file_obj.save(update_fields=["file_extra_JSON"])
