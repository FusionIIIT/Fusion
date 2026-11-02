"""Notification triggers (VMS-CFR-028) and channel routing (VMS-BR-174).

VMS owns the notification *event*; delivery infrastructure is external
(Problem Statement B-02). Every event is stored first, then each configured
channel is attempted. A delivery failure is recorded on the event and never
changes the visit state.
"""

import logging

from django.core.mail import send_mail
from django.utils.module_loading import import_string

from . import conf
from .constants import DeliveryStatus, IntegrationKey
from .models import VmsNotification
from .selectors import integration_usable

logger = logging.getLogger(__name__)

MODULE_NAME = "Visitor Management"
NOTIFICATION_URL = "vms:vms"


def _deliver_in_app(user, message, sender=None):
    if not integration_usable(IntegrationKey.IN_APP, default=True):
        return DeliveryStatus.NOT_CONFIGURED
    try:
        from notifications.signals import notify
        notify.send(sender=sender or user, recipient=user, url=NOTIFICATION_URL, module=MODULE_NAME, verb=message)
        return DeliveryStatus.SENT
    except Exception:  # delivery must never break the business action
        logger.exception("VMS in-app notification failed")
        return DeliveryStatus.FAILED


def _deliver_email(address, subject, message):
    if not address:
        return DeliveryStatus.SKIPPED
    if not integration_usable(IntegrationKey.EMAIL, default=True):
        return DeliveryStatus.NOT_CONFIGURED
    try:
        send_mail("Fusion VMS: " + subject, message, None, [address], fail_silently=False)
        return DeliveryStatus.SENT
    except Exception:
        logger.exception("VMS e-mail notification failed")
        return DeliveryStatus.FAILED


def _deliver_sms(phone, message):
    if not phone:
        return DeliveryStatus.SKIPPED
    backend_path = conf.sms_backend_path()
    if not backend_path or not integration_usable(IntegrationKey.SMS, default=False):
        return DeliveryStatus.NOT_CONFIGURED
    try:
        backend = import_string(backend_path)
        return DeliveryStatus.SENT if backend(phone, message) else DeliveryStatus.FAILED
    except Exception:
        logger.exception("VMS SMS notification failed")
        return DeliveryStatus.FAILED


def notify_user(user, event, title, message, visit=None, sender=None, email=True):
    """Host / Admin / Security recipient (Fusion account)."""
    if user is None:
        return None
    delivery = {"in_app": _deliver_in_app(user, message, sender=sender)}
    if email:
        delivery["email"] = _deliver_email(getattr(user, "email", ""), title, message)
    return VmsNotification.objects.create(
        event_type=event, recipient_user=user, visit=visit, title=title, message=message, delivery=delivery,
    )


def notify_users(users, event, title, message, visit=None, sender=None, email=True):
    return [notify_user(u, event, title, message, visit=visit, sender=sender, email=email) for u in users]


def notify_visitor(visitor, event, title, message, visit=None, sms=False):
    """Visitor recipient. The stored record is what the portal shows (VMS-UC-030).

    SMS is attempted for the critical events named by AFR-221 (pass delivery,
    emergency alerts) when an SMS backend is configured.
    """
    if visitor is None:
        return None
    delivery = {"portal": DeliveryStatus.SENT, "email": _deliver_email(visitor.email, title, message)}
    if sms:
        delivery["sms"] = _deliver_sms(visitor.phone, message)
    return VmsNotification.objects.create(
        event_type=event, recipient_visitor=visitor, visit=visit, title=title, message=message, delivery=delivery,
    )


def notify_role(role, event, title, message, visit=None):
    """Role-wide feed entry (e.g. expected arrivals for Security Personnel)."""
    return VmsNotification.objects.create(
        event_type=event, recipient_role=role, visit=visit, title=title, message=message,
        delivery={"feed": DeliveryStatus.SENT},
    )
