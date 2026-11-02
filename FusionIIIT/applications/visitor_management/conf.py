"""Module settings with spec-backed defaults. Override any of them in Django settings."""

from django.conf import settings

from .constants import GateFailure


def _get(name, default):
    return getattr(settings, name, default)


def super_admin_designations():
    """Fusion designations that hold the VMS Super Admin role."""
    return tuple(_get("VMS_SUPER_ADMIN_DESIGNATIONS", ("vms_super_admin",)))


def override_eligible_failures():
    """Gate failures an Admin may override (VMS-BR-085).

    ISS-VMS-023 leaves blacklist overrides unresolved, so BLACKLIST_MATCH is
    excluded by default, as are failures where there is no valid pass to admit
    against (unknown credential, deactivated pass, visit not enterable).
    """
    return set(_get("VMS_OVERRIDE_ELIGIBLE_FAILURES", {
        GateFailure.OUTSIDE_VALIDITY_WINDOW,
        GateFailure.GATE_ZONE_NOT_PERMITTED,
        GateFailure.OTP_ALREADY_USED,
    }))


def watchlist_rejects():
    """Whether a WATCHLIST hit rejects like a BLACKLIST hit.

    Default False: a watchlist hit flags the visit and alerts security, a
    blacklist hit is disqualifying (VMS-BR-051/116 speak of the disqualifying
    blacklist match).
    """
    return bool(_get("VMS_WATCHLIST_REJECTS", False))


def self_checkout_enabled():
    """VMS-UC-031 precondition: a kiosk/app self-checkout interface is deployed."""
    return bool(_get("VMS_SELF_CHECKOUT_ENABLED", True))


def sms_backend_path():
    """Dotted path to ``callable(phone, message) -> bool``. None means SMS is not configured."""
    return _get("VMS_SMS_BACKEND", None)


def id_document_max_bytes():
    return int(_get("VMS_ID_DOCUMENT_MAX_BYTES", 5 * 1024 * 1024))
