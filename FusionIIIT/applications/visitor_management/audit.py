"""Audit trail (VMS-CFR-005, AFR-006, AFR-216)."""

from django.core.serializers.json import DjangoJSONEncoder
import json

from .models import AuditLog


def _clean(metadata):
    # Round-trip through the Django encoder so datetimes/decimals are JSON-safe.
    return json.loads(json.dumps(metadata or {}, cls=DjangoJSONEncoder))


def record(actor, actor_role, action, entity, message="", metadata=None, visitor=None):
    entity_type = entity.__class__.__name__ if entity is not None else ""
    entity_id = str(getattr(entity, "pk", "") or "") if entity is not None else ""
    return AuditLog.objects.create(
        actor=actor if (actor is not None and getattr(actor, "is_authenticated", False)) else None,
        actor_role=actor_role,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        visitor=visitor,
        message=message,
        metadata=_clean(metadata),
    )
