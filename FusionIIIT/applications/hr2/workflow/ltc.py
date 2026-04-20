"""LTC workflow: submit to chosen approver (e.g. HR Admin) → approve/reject → forward to Accountant on approval."""

from django.utils import timezone

from applications.globals.models import HoldsDesignation

WF_SUBMITTED = "submitted"
WF_HR_APPROVED = "hr_approved"
WF_HR_REJECTED = "hr_rejected"
WF_FORWARDED_DIRECTOR = "forwarded_to_director"
WF_FORWARDED_REGISTRAR = "forwarded_to_registrar"
WF_DIRECTOR_APPROVED = "director_approved"
WF_DIRECTOR_REJECTED = "director_rejected"
WF_REGISTRAR_APPROVED = "registrar_approved"
WF_REGISTRAR_REJECTED = "registrar_rejected"
WF_WITH_ACCOUNTANT = "with_accountant"

TERMINAL_STATUSES = frozenset(
    {WF_HR_REJECTED, WF_DIRECTOR_REJECTED, WF_REGISTRAR_REJECTED}
)

LTC_FINANCIAL_THRESHOLD = 25000


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


def resolve_hr_admin():
    """Prefer ``hr_admin`` user when multiple hold HR Admin."""
    qs = HoldsDesignation.objects.filter(
        designation__name__iexact="HR Admin"
    ).select_related("working")
    hd = qs.filter(working__username__iexact="hr_admin").first()
    if not hd:
        hd = qs.order_by("working__username").first()
    if hd and hd.working_id:
        return hd.working.username, hd.designation.name
    return None, None


def resolve_director():
    """Prefer the canonical ``director`` account when multiple users hold Director."""
    qs = HoldsDesignation.objects.filter(
        designation__name__iexact="Director"
    ).select_related("working")
    hd = qs.filter(working__username__iexact="director").first()
    if not hd:
        hd = qs.order_by("working__username").first()
    if hd and hd.working_id:
        return hd.working.username, "Director"
    return None, None


def resolve_registrar():
    """Prefer the canonical ``registrar`` account when multiple users hold Registrar."""
    qs = HoldsDesignation.objects.filter(
        designation__name__iexact="Registrar"
    ).select_related("working")
    hd = qs.filter(working__username__iexact="registrar").first()
    if not hd:
        hd = qs.order_by("working__username").first()
    if hd and hd.working_id:
        return hd.working.username, "Registrar"
    return None, None


def resolve_accountant():
    from applications.hr2.workflow import cpda_advance as cpda_wf

    return cpda_wf.resolve_accountant()


def designation_is_hr_admin(name):
    return (name or "").strip().lower() == "hr admin"


def designation_is_director(name):
    return (name or "").strip().lower() == "director"


def designation_is_registrar(name):
    return (name or "").strip().lower() == "registrar"


def sync_file_extra_workflow(file_obj, workflow_status):
    from applications.hr2.constants.form_types import FormType

    extra = dict(file_obj.file_extra_JSON or {})
    extra["type"] = FormType.LTC
    extra["workflow_status"] = workflow_status
    file_obj.file_extra_JSON = extra
    file_obj.save(update_fields=["file_extra_JSON"])
