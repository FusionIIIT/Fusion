"""Reporting, dashboards and audit review.

VMS-UC-004 audit trails, VMS-UC-007 reports/analytics (AFR-142..153),
VMS-UC-022 live dashboard (AFR-092/093, 161/162). All read-only.
"""

import csv
import datetime
import hashlib
import io
from collections import Counter, defaultdict

from django.db.models import Count, Q
from django.db.models.functions import ExtractHour, TruncDate

from ..constants import (
    AlertStatus,
    AlertType,
    EventStatus,
    GateAttemptStatus,
    LogType,
    OfflineEventStatus,
    VisitStatus,
)
from ..errors import ValidationFailed
from ..models import (
    AuditLog,
    GateAttempt,
    OfflineGateEvent,
    SecurityAlert,
    VisitLog,
    VisitorEvent,
    VisitRequest,
)
from ..selectors import now

REPORT_TYPES = (
    "visitor_volume", "peak_hours", "frequent_visitors", "denial_statistics", "sla_compliance",
    "daily_summary", "audit_trail", "zone_access", "blacklist_hits",
)


def _pseudonym(value):
    return "V-" + hashlib.sha256((value or "").encode("utf-8")).hexdigest()[:8].upper()


def _anon(row, fields, enabled):
    """AFR-153: anonymised view replaces personal identifiers with a stable pseudonym."""
    if not enabled:
        return row
    for field in fields:
        if field in row and row[field]:
            row[field] = _pseudonym(str(row[field]))
    return row


def _date_range(params):
    today = now().date()
    try:
        start = datetime.date.fromisoformat(params["date_from"]) if params.get("date_from") else today - datetime.timedelta(days=6)
        end = datetime.date.fromisoformat(params["date_to"]) if params.get("date_to") else today
    except ValueError:
        raise ValidationFailed("Dates must be YYYY-MM-DD.", details={"date_from": ["invalid"]})
    if end < start:
        raise ValidationFailed("date_to must not be before date_from.", details={"date_to": ["invalid"]})
    if (end - start).days > 366:
        raise ValidationFailed("Report range is limited to one year.", details={"date_to": ["too wide"]})
    lower = datetime.datetime.combine(start, datetime.time.min)
    upper = datetime.datetime.combine(end, datetime.time.max)
    return start, end, lower, upper


def generate_report(report_type, params):
    if report_type not in REPORT_TYPES:
        raise ValidationFailed("Unsupported report type.", details={"report_type": list(REPORT_TYPES)})
    anonymize = str(params.get("anonymize", "")).lower() in ("1", "true", "yes")
    start, end, lower, upper = _date_range(params)
    builder = globals()["_report_" + report_type]
    rows, summary = builder(lower, upper, params, anonymize)
    return {
        "report_type": report_type,
        "date_from": start.isoformat(),
        "date_to": end.isoformat(),
        "anonymized": anonymize,
        "generated_at": now().isoformat(),
        "summary": summary,
        "rows": rows,
    }


def _report_visitor_volume(lower, upper, params, anonymize):
    requests = VisitRequest.objects.filter(submitted_at__range=(lower, upper))
    by_day_req = dict(requests.annotate(d=TruncDate("submitted_at")).values_list("d").annotate(c=Count("id")))
    checkins = VisitLog.objects.filter(log_type=LogType.CHECK_IN, occurred_at__range=(lower, upper))
    by_day_in = dict(checkins.annotate(d=TruncDate("occurred_at")).values_list("d").annotate(c=Count("id")))
    rows, day = [], lower.date()
    while day <= upper.date():
        rows.append({"date": day.isoformat(), "requests": by_day_req.get(day, 0), "check_ins": by_day_in.get(day, 0)})
        day += datetime.timedelta(days=1)
    channels = dict(requests.values_list("channel").annotate(c=Count("id")))
    return rows, {"total_requests": requests.count(), "total_check_ins": checkins.count(), "by_channel": channels}


def _report_peak_hours(lower, upper, params, anonymize):
    counts = dict(VisitLog.objects.filter(log_type=LogType.CHECK_IN, occurred_at__range=(lower, upper))
                  .annotate(h=ExtractHour("occurred_at")).values_list("h").annotate(c=Count("id")))
    rows = [{"hour": "{:02d}:00".format(h), "check_ins": counts.get(h, 0)} for h in range(24)]
    peak = max(rows, key=lambda r: r["check_ins"]) if any(r["check_ins"] for r in rows) else None
    return rows, {"peak_hour": peak["hour"] if peak else None}


def _report_frequent_visitors(lower, upper, params, anonymize):
    limit = min(int(params.get("limit") or 20), 200)
    visits = VisitRequest.objects.filter(check_in_at__range=(lower, upper)).select_related("visitor")
    counter, names = Counter(), {}
    for visit in visits:
        key = visit.visitor.id_doc_key or visit.visitor.phone_key or str(visit.visitor_id)
        counter[key] += 1
        names[key] = (visit.visitor.full_name, visit.visitor.organization, visit.visitor.phone)
    rows = []
    for key, count in counter.most_common(limit):
        name, org, phone = names[key]
        rows.append(_anon({"visitor": name, "organization": org, "phone": phone, "visits": count},
                          ("visitor", "phone"), anonymize))
    return rows, {"distinct_visitors": len(counter)}


def _report_denial_statistics(lower, upper, params, anonymize):
    attempts = GateAttempt.objects.filter(attempted_at__range=(lower, upper))
    blocked = attempts.exclude(status=GateAttemptStatus.ALLOWED)
    reasons = Counter()
    for failures in blocked.values_list("failure_reasons", flat=True):
        reasons.update(failures or [])
    zone_denials = VisitLog.objects.filter(log_type=LogType.ACCESS_DENIED, zone__isnull=False,
                                           occurred_at__range=(lower, upper)).count()
    rows = [{"reason": reason, "count": count} for reason, count in reasons.most_common()]
    return rows, {
        "gate_attempts": attempts.count(),
        "gate_blocked": blocked.count(),
        "overrides_authorized": attempts.filter(status__in=[GateAttemptStatus.OVERRIDE_AUTHORIZED,
                                                            GateAttemptStatus.MANUAL_ENTRY_RECORDED]).count(),
        "zone_denials": zone_denials,
    }


def _report_sla_compliance(lower, upper, params, anonymize):
    """AFR-146: approval times against each visit's own approval window."""
    decided = VisitRequest.objects.filter(submitted_at__range=(lower, upper), decided_at__isnull=False,
                                          channel__in=["ONLINE", "WALK_IN"])
    rows, durations, within = [], [], 0
    for visit in decided.select_related("visitor"):
        minutes_taken = (visit.decided_at - visit.submitted_at).total_seconds() / 60
        window = visit.policy_snapshot.get(
            "contingency_sla_minutes" if visit.host_unavailable else "approval_timeout_minutes")
        ok = window is not None and minutes_taken <= window
        within += ok
        durations.append(minutes_taken)
        rows.append(_anon({"reference": visit.reference, "visitor": visit.visitor.full_name,
                           "channel": visit.channel, "minutes_to_decision": round(minutes_taken, 1),
                           "window_minutes": window, "within_sla": ok}, ("visitor",), anonymize))
    expired = VisitRequest.objects.filter(submitted_at__range=(lower, upper), status=VisitStatus.EXPIRED).count()
    durations.sort()
    median = durations[len(durations) // 2] if durations else None
    return rows, {
        "decided": len(durations),
        "within_sla": within,
        "compliance_percent": round(100.0 * within / len(durations), 1) if durations else None,
        "median_minutes": round(median, 1) if median is not None else None,
        "expired_without_decision": expired,
    }


def _report_daily_summary(lower, upper, params, anonymize):
    logs = VisitLog.objects.filter(occurred_at__range=(lower, upper))
    rows, day = [], lower.date()
    in_by = dict(logs.filter(log_type=LogType.CHECK_IN).annotate(d=TruncDate("occurred_at")).values_list("d").annotate(c=Count("id")))
    out_by = dict(logs.filter(log_type=LogType.CHECK_OUT).annotate(d=TruncDate("occurred_at")).values_list("d").annotate(c=Count("id")))
    req_by = dict(VisitRequest.objects.filter(submitted_at__range=(lower, upper)).annotate(
        d=TruncDate("submitted_at")).values_list("d").annotate(c=Count("id")))
    while day <= upper.date():
        rows.append({"date": day.isoformat(), "requests": req_by.get(day, 0), "check_ins": in_by.get(day, 0),
                     "check_outs": out_by.get(day, 0)})
        day += datetime.timedelta(days=1)
    return rows, {"on_site_now": VisitRequest.objects.filter(status__in=VisitStatus.ON_CAMPUS).count()}


def audit_queryset(params):
    query = AuditLog.objects.select_related("actor", "visitor")
    _, _, lower, upper = _date_range(params)
    query = query.filter(created_at__range=(lower, upper))
    if params.get("visitor"):
        term = params["visitor"]
        query = query.filter(Q(visitor__full_name__icontains=term) | Q(visitor__id_doc_key=term.upper())
                             | Q(metadata__visit=term))
    if params.get("action"):
        query = query.filter(action=params["action"])
    if params.get("actor"):
        query = query.filter(actor__username=params["actor"])
    if params.get("entity_type"):
        query = query.filter(entity_type=params["entity_type"])
    return query


def _report_audit_trail(lower, upper, params, anonymize):
    limit = min(int(params.get("limit") or 500), 5000)
    rows = []
    for log in audit_queryset(params)[:limit]:
        rows.append(_anon({
            "timestamp": log.created_at.isoformat(), "actor": log.actor.username if log.actor else "system",
            "role": log.actor_role, "action": log.action, "entity": "{}:{}".format(log.entity_type, log.entity_id),
            "visitor": log.visitor.full_name if log.visitor else "", "message": log.message,
        }, ("visitor",), anonymize))
    return rows, {"returned": len(rows)}


def _report_zone_access(lower, upper, params, anonymize):
    logs = VisitLog.objects.filter(zone__isnull=False, occurred_at__range=(lower, upper),
                                   log_type__in=[LogType.ZONE_ACCESS, LogType.ACCESS_DENIED, LogType.CHECK_IN])
    stats = defaultdict(lambda: {"allowed": 0, "denied": 0})
    for zone_code, zone_name, log_type in logs.values_list("zone__code", "zone__name", "log_type"):
        stats[(zone_code, zone_name)]["denied" if log_type == LogType.ACCESS_DENIED else "allowed"] += 1
    rows = [{"zone": code, "name": name, **counts} for (code, name), counts in sorted(stats.items())]
    return rows, {"zones": len(rows)}


def _report_blacklist_hits(lower, upper, params, anonymize):
    hits = SecurityAlert.objects.filter(alert_type__in=[AlertType.BLACKLIST_MATCH, AlertType.WATCHLIST_MATCH],
                                        created_at__range=(lower, upper)).select_related("registry_entry")
    rows = []
    for alert in hits:
        identity = alert.metadata.get("identity", {})
        rows.append(_anon({
            "timestamp": alert.created_at.isoformat(), "type": alert.alert_type, "checkpoint": alert.checkpoint,
            "severity": alert.metadata.get("severity"), "visitor": identity.get("full_name", ""),
            "phone": identity.get("phone", ""), "rejected": alert.metadata.get("rejected"),
            "registry_entry": alert.registry_entry_id,
        }, ("visitor", "phone"), anonymize))
    by_checkpoint = dict(hits.values_list("checkpoint").annotate(c=Count("id")))
    return rows, {"total_hits": len(rows), "by_checkpoint": by_checkpoint}


# --------------------------------------------------------------------------
# Exports (AFR-151 CSV, AFR-152 PDF)
# --------------------------------------------------------------------------

def export_csv(report):
    buffer = io.StringIO()
    rows = report["rows"]
    if rows:
        writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    else:
        buffer.write("No records for the selected range\n")
    return buffer.getvalue().encode("utf-8")


def export_pdf(report):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), title="VMS report")
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Visitor Management System: {}".format(report["report_type"].replace("_", " ").title()), styles["Title"]),
        Paragraph("{} to {}{}".format(report["date_from"], report["date_to"],
                                      " (anonymised)" if report["anonymized"] else ""), styles["Normal"]),
        Spacer(1, 12),
    ]
    rows = report["rows"]
    if rows:
        headers = list(rows[0].keys())
        data = [headers] + [[str(r.get(h, ""))[:60] for h in headers] for r in rows[:1000]]
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3a5f")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ]))
        story.append(table)
    else:
        story.append(Paragraph("No records for the selected range.", styles["Normal"]))
    doc.build(story)
    return buffer.getvalue()


# --------------------------------------------------------------------------
# VMS-UC-022 Monitor Live Visitor Dashboard
# --------------------------------------------------------------------------

def live_dashboard():
    current = now()
    on_site = VisitRequest.objects.filter(status__in=VisitStatus.ON_CAMPUS).select_related(
        "visitor", "host__user", "last_seen_zone", "entry_gate", "visit_pass")
    roster = []
    for visit in on_site:
        visit_pass = getattr(visit, "visit_pass", None)
        roster.append({
            "reference": visit.reference, "visitor": visit.visitor.full_name, "phone": visit.visitor.phone,
            "host": visit.host.user.get_full_name() or visit.host.user.username, "status": visit.status,
            "checked_in_at": visit.check_in_at, "entry_gate": visit.entry_gate.code if visit.entry_gate else None,
            "last_seen_zone": visit.last_seen_zone.code if visit.last_seen_zone else None,
            "last_seen_at": visit.last_seen_at, "valid_until": visit_pass.valid_until if visit_pass else None,
            "overstay": bool(visit_pass and visit_pass.valid_until < current),
            "pending_exit": visit.status == VisitStatus.ON_SITE_PENDING_EXIT,
            "watchlist_flag": visit.watchlist_flag,
        })
    movements = [{
        "time": log.occurred_at, "type": log.log_type, "visitor": log.visit.visitor.full_name if log.visit else None,
        "reference": log.visit.reference if log.visit else None, "gate": log.gate.code if log.gate else None,
        "zone": log.zone.code if log.zone else None, "detail": log.detail,
    } for log in VisitLog.objects.select_related("visit", "visit__visitor", "gate", "zone")[:50]]
    alerts = [{
        "id": a.pk, "type": a.alert_type, "status": a.status, "message": a.message, "created_at": a.created_at,
        "zone": a.zone.code if a.zone else None, "reference": a.visit.reference if a.visit else None,
    } for a in SecurityAlert.objects.filter(status__in=[AlertStatus.OPEN, AlertStatus.ESCALATED]).select_related(
        "zone", "visit")[:100]]
    contingency = [{
        "reference": v.reference, "visitor": v.visitor.full_name, "deadline": v.contingency_deadline,
        "minutes_left": int((v.contingency_deadline - current).total_seconds() // 60) if v.contingency_deadline else None,
    } for v in VisitRequest.objects.filter(status=VisitStatus.PENDING_ADMIN_CONTINGENCY).select_related("visitor")]
    events = []
    for event in VisitorEvent.objects.filter(status__in=[EventStatus.PASSES_ACTIVE, EventStatus.CONTROLS_ACTIVE]):
        events.append(event_attendance(event, current))
    return {
        "generated_at": current,
        "on_site_count": len(roster),
        "roster": roster,
        "recent_movements": movements,
        "open_alerts": alerts,
        "blocked_attempts_pending": GateAttempt.objects.filter(status=GateAttemptStatus.BLOCKED,
                                                               override_requested_at__isnull=False).count(),
        "pending_contingency": contingency,
        "offline_conflicts": OfflineGateEvent.objects.filter(status=OfflineEventStatus.CONFLICT).count(),
        "events": events,
    }


def event_attendance(event, current=None):
    """AFR-161 attendance and AFR-162 entry throughput (check-ins per 15 minutes, last 2 hours)."""
    current = current or now()
    visits = VisitRequest.objects.filter(event=event)
    checkins = VisitLog.objects.filter(visit__event=event, log_type=LogType.CHECK_IN)
    window_start = current - datetime.timedelta(hours=2)
    buckets = []
    for i in range(8):
        lo = window_start + datetime.timedelta(minutes=15 * i)
        hi = lo + datetime.timedelta(minutes=15)
        buckets.append({"from": lo, "to": hi, "check_ins": checkins.filter(occurred_at__gte=lo, occurred_at__lt=hi).count()})
    return {
        "event_id": event.pk, "name": event.name, "status": event.status,
        "passes": visits.filter(visit_pass__isnull=False).count(),
        "attended": visits.filter(check_in_at__isnull=False).count(),
        "on_site": visits.filter(status__in=VisitStatus.ON_CAMPUS).count(),
        "completed": visits.filter(status=VisitStatus.COMPLETED).count(),
        "throughput": buckets,
    }
