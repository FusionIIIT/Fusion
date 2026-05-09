"""Seed the VMS module with demo-ready data.

Idempotent — safe to run multiple times. Populates:
  * Visitors (Aadhaar / passport / driver license, VIP + regular)
  * Visits in every workflow status (registered -> exited / denied)
  * Security incidents across all severities
  * A couple of blacklist entries
  * An active escort assignment for a VIP visit
  * A few active VisitorPasses so the "Issue QR" flow has history

Usage (from the FusionIIIT directory):
    python vms_seed.py            # add / refresh demo data
    python vms_seed.py --clean    # also remove any prior seeded rows
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import timedelta

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Fusion.settings.development")
import django  # noqa: E402
django.setup()

from django.utils import timezone  # noqa: E402

from applications.vms.models import (  # noqa: E402
    AccessZone,
    BlacklistEntry,
    EntryExitLog,
    EscortAssignment,
    SecurityIncident,
    SystemConfig,
    Visit,
    VisitingHours,
    Visitor,
    VisitorPass,
    calculate_valid_until,
)

# All seeded rows carry this marker in a free-text field so --clean can
# reliably remove them without touching real data.
SEED_TAG = "[vms-seed]"


# ---------------------------------------------------------------------------
# Visitors — the pool we spin demo visits from
# ---------------------------------------------------------------------------
VISITORS = [
    # (id_number, full_name, id_type, phone, email)
    ("100000000001", "Ananya Rao",     "aadhaar",        "9811100001", "ananya@example.com"),
    ("100000000002", "Bharath Menon",  "aadhaar",        "9811100002", "bharath@example.com"),
    ("100000000003", "Chitra Balan",   "aadhaar",        "9811100003", "chitra@example.com"),
    ("100000000004", "Devansh Kapoor", "aadhaar",        "9811100004", "devansh@example.com"),
    ("P9900011",     "Elena Ruiz",     "passport",       "9811100005", "elena@example.com"),
    ("P9900012",     "Farhan Ahmed",   "passport",       "9811100006", "farhan@example.com"),
    ("DL-07-90011",  "Gita Sahu",      "driver_license", "9811100007", "gita@example.com"),
    ("100000000008", "Harini Subbu",   "aadhaar",        "9811100008", "harini@example.com"),
    ("100000000009", "Ishaan Verma",   "aadhaar",        "9811100009", "ishaan@example.com"),
    ("100000000010", "Jaya Krishnan",  "aadhaar",        "9811100010", "jaya@example.com"),
    ("P9900013",     "Kenji Tanaka",   "passport",       "9811100011", "kenji@example.com"),
    ("DL-09-90012",  "Leela Pillai",   "driver_license", "9811100012", "leela@example.com"),
    ("100000000013", "Mohan Das",      "aadhaar",        "9811100013", "mohan@example.com"),
    ("100000000014", "Neha Arora",     "aadhaar",        "9811100014", "neha@example.com"),
    ("P9900015",     "Omar Siddiqui",  "passport",       "9811100015", "omar@example.com"),
    ("100000000016", "Priya Nair",     "aadhaar",        "9811100016", "priya@example.com"),
]


def _tick(label: str, created: bool) -> None:
    marker = "created" if created else "exists"
    print(f"  [{marker:>7}] {label}")


def seed_visitors() -> list[Visitor]:
    out: list[Visitor] = []
    for id_number, name, id_type, phone, email in VISITORS:
        v, created = Visitor.objects.update_or_create(
            id_number=id_number,
            defaults={
                "full_name": name,
                "id_type": id_type,
                "contact_phone": phone,
                "contact_email": email,
                "photo_reference": f"{SEED_TAG} {name}",
            },
        )
        out.append(v)
        _tick(f"visitor {name} ({id_type})", created)
    return out


# ---------------------------------------------------------------------------
# Visits — one per visitor, in different workflow statuses
# ---------------------------------------------------------------------------
VISIT_PLANS = [
    # (visitor_index, status, is_vip, vip_level, purpose, host, department, entry_delta_min, exit_delta_min)
    (0, Visit.STATUS_REGISTERED,  False, 0, "Guest lecture prep",         "Prof. V. Rao",   "CSE",  None, None),
    (1, Visit.STATUS_VERIFIED,    False, 0, "Vendor meeting",             "Mr. S. Sinha",   "Admin",None, None),
    (2, Visit.STATUS_PASS_ISSUED, False, 0, "Project review",             "Prof. N. Gupta", "ECE",  None, None),
    (3, Visit.STATUS_INSIDE,      True,  3, "Industry delegation",        "Director",      "Admin",-20,  None),
    (4, Visit.STATUS_INSIDE,      False, 0, "Library visit",              "Prof. A. Jain",  "Library",-45, None),
    (5, Visit.STATUS_EXITED,      False, 0, "Interview panel",            "Prof. M. Iyer",  "MBA",  -180, -30),
    (6, Visit.STATUS_DENIED,      False, 0, "Unscheduled drop-in",        "Prof. K. Bose",  "Physics",None, None),
    (7, Visit.STATUS_INSIDE,      True,  5, "Chief Guest - Annual Day",   "Dean",           "Admin",-60, None),
    (8, Visit.STATUS_REGISTERED,  False, 0, "Alumni campus tour",         "Prof. S. Das",   "Alumni", None, None),
    (9, Visit.STATUS_VERIFIED,    False, 0, "Research collaboration",     "Prof. R. Nair",  "CSE",  None, None),
    (10, Visit.STATUS_INSIDE,     True,  4, "External examiner",          "Dean Academics", "Academic",-30, None),
    (11, Visit.STATUS_PASS_ISSUED,False, 0, "Workshop participant",       "Prof. B. Rao",   "ME",   None, None),
    (12, Visit.STATUS_EXITED,     False, 0, "Equipment delivery",         "Mr. T. Kumar",   "Stores",-240,-120),
    (13, Visit.STATUS_INSIDE,     False, 0, "Placement interview",        "Placement Cell", "Admin",-90, None),
    (14, Visit.STATUS_DENIED,     False, 0, "Missing appointment",        "Reception",      "Admin", None, None),
    (15, Visit.STATUS_EXITED,     True,  3, "Board member visit",         "Registrar",     "Admin",-300,-180),
]


def seed_visits(visitors: list[Visitor]) -> list[Visit]:
    now = timezone.now()
    out: list[Visit] = []
    for i, status, is_vip, vip_level, purpose, host, dept, entry_off, exit_off in VISIT_PLANS:
        visitor = visitors[i]
        # Match an existing seeded visit by (visitor, purpose). Purpose is
        # distinctive enough in this pool to make each plan-row unique.
        visit, created = Visit.objects.get_or_create(
            visitor=visitor,
            purpose=purpose,
            defaults={
                "host_name": host,
                "host_department": dept,
                "host_contact": "9876543200",
                "expected_duration_minutes": 120,
                "is_vip": is_vip,
                "vip_level": vip_level,
                "status": status,
            },
        )
        visit.host_name = host
        visit.host_department = dept
        visit.is_vip = is_vip
        visit.vip_level = vip_level
        visit.status = status
        if entry_off is not None:
            visit.entry_at = now + timedelta(minutes=entry_off)
        if exit_off is not None:
            visit.exit_at = now + timedelta(minutes=exit_off)
        if status == Visit.STATUS_DENIED:
            visit.denial_reason = "host_unavailable"
            visit.denial_remarks = "Host not reachable; rescheduled"
        elif status in {Visit.STATUS_VERIFIED, Visit.STATUS_PASS_ISSUED, Visit.STATUS_INSIDE, Visit.STATUS_EXITED}:
            visit.verified_at = visit.verified_at or now - timedelta(minutes=60)
        visit.save()
        out.append(visit)
        _tick(f"visit #{visit.id} {visitor.full_name} [{status}]", created)

        # For inside/exited visits, drop an entry log so checkpoint history shows up.
        if entry_off is not None:
            EntryExitLog.objects.get_or_create(
                visit=visit,
                action=EntryExitLog.ACTION_ENTRY,
                defaults={"gate_name": "Main Gate", "items_declared": "Laptop"},
            )
        if exit_off is not None:
            EntryExitLog.objects.get_or_create(
                visit=visit,
                action=EntryExitLog.ACTION_EXIT,
                defaults={"gate_name": "Main Gate", "items_declared": ""},
            )

        # Issue a pass for visits past verification.
        if status in {Visit.STATUS_PASS_ISSUED, Visit.STATUS_INSIDE, Visit.STATUS_EXITED}:
            vp, _ = VisitorPass.objects.get_or_create(
                visit=visit,
                defaults={
                    "valid_from": now - timedelta(minutes=90),
                    "valid_until": calculate_valid_until(
                        now - timedelta(minutes=90), 180, is_vip
                    ),
                    "authorized_zones": "lobby,admin_block",
                    "status": (
                        VisitorPass.PASS_RETURNED
                        if status == Visit.STATUS_EXITED
                        else VisitorPass.PASS_ISSUED
                    ),
                    "is_vip_pass": is_vip,
                    "barcode_data": f"{SEED_TAG} demo-pass",
                },
            )
    return out


# ---------------------------------------------------------------------------
# Security incidents — mix of severities / types
# ---------------------------------------------------------------------------
INCIDENTS = [
    # (visit_index, severity, issue_type, description)
    (4, SecurityIncident.SEVERITY_HIGH,    "unauthorized_access",  "Attempted entry into restricted server room"),
    (3, SecurityIncident.SEVERITY_MEDIUM,  "policy_violation",     "VIP guest used unapproved side corridor"),
    (2, SecurityIncident.SEVERITY_LOW,     "equipment_failure",    "Checkpoint barcode scanner offline for 4 minutes"),
    (5, SecurityIncident.SEVERITY_HIGH,    "suspicious_behavior",  "Loitering near faculty parking after hours"),
    (6, SecurityIncident.SEVERITY_CRITICAL,"unauthorized_access",  "Visitor refused ID re-verification at exit"),
    (10, SecurityIncident.SEVERITY_MEDIUM, "policy_violation",     "External examiner used mobile camera in exam block"),
    (11, SecurityIncident.SEVERITY_LOW,    "other",                "Workshop attendee forgot to return lanyard"),
    (13, SecurityIncident.SEVERITY_HIGH,   "suspicious_behavior",  "Placement candidate tailgated through gate 2"),
    (14, SecurityIncident.SEVERITY_MEDIUM, "unauthorized_access",  "Turned back at main gate — missing approval"),
    (12, SecurityIncident.SEVERITY_LOW,    "equipment_failure",    "Stores gate barrier stuck open for 8 minutes"),
]


def seed_incidents(visits: list[Visit]) -> None:
    for visit_idx, severity, issue_type, description in INCIDENTS:
        visit = visits[visit_idx]
        inc, created = SecurityIncident.objects.get_or_create(
            visit=visit,
            issue_type=issue_type,
            description=description,
            defaults={
                "visitor": visit.visitor,
                "severity": severity,
            },
        )
        _tick(f"incident [{severity}] {issue_type}", created)


# ---------------------------------------------------------------------------
# Blacklist entries
# ---------------------------------------------------------------------------
BLACKLIST = [
    ("BL-999-0001", "Impersonation attempt flagged by gate officer",
     "Incident report 2026-04-15"),
    ("BL-999-0002", "Recurring policy violations across three visits",
     "Audit trail VMS-AUDIT-07"),
    ("BL-999-0003", "Tailgated through employee gate, refused ID check",
     "CCTV clip gate-2 2026-03-28"),
    ("BL-999-0004", "Confrontational behaviour with security staff",
     "Incident report VMS-IR-2026-19"),
]


def seed_blacklist() -> None:
    for id_number, reason, evidence in BLACKLIST:
        entry, created = BlacklistEntry.objects.get_or_create(
            id_number=id_number,
            defaults={"reason": reason, "evidence": evidence, "active": True},
        )
        _tick(f"blacklist {id_number}", created)


# ---------------------------------------------------------------------------
# Escort assignment for a VIP visit (Chief Guest)
# ---------------------------------------------------------------------------
def seed_escort(visits: list[Visit]) -> None:
    from applications.globals.models import ExtraInfo

    vip_visits = [v for v in visits if v.is_vip and v.status == Visit.STATUS_INSIDE]
    if not vip_visits:
        print("  [skip] no active VIP visit to escort")
        return
    escorts = list(ExtraInfo.objects.all()[:3])
    if not escorts:
        print("  [skip] no ExtraInfo available to assign as escort")
        return
    for idx, vip_visit in enumerate(vip_visits):
        existing = EscortAssignment.objects.filter(
            visit=vip_visit, released_at__isnull=True
        ).first()
        if existing:
            _tick(f"escort on visit #{vip_visit.id} (escort {existing.escort_id})", False)
            continue
        escort = escorts[idx % len(escorts)]
        EscortAssignment.objects.create(
            visit=vip_visit,
            escort=escort,
            notes=f"{SEED_TAG} VIP protocol — vip_level={vip_visit.vip_level}",
        )
        _tick(f"escort on visit #{vip_visit.id} (escort {escort})", True)


# ---------------------------------------------------------------------------
# Cleanup — removes only seeded rows, identified by the marker above
# ---------------------------------------------------------------------------
def clean() -> None:
    seed_id_numbers = [row[0] for row in VISITORS] + [row[0] for row in BLACKLIST]
    removed_bl = BlacklistEntry.objects.filter(id_number__in=[row[0] for row in BLACKLIST]).delete()
    removed_visits = Visit.objects.filter(visitor__id_number__in=[row[0] for row in VISITORS]).delete()
    removed_visitors = Visitor.objects.filter(id_number__in=[row[0] for row in VISITORS]).delete()
    print(f"  removed: blacklist={removed_bl}  visits={removed_visits}  visitors={removed_visitors}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed VMS demo data")
    parser.add_argument("--clean", action="store_true", help="delete seeded rows")
    args = parser.parse_args()

    if args.clean:
        print("== Cleaning seeded rows ==")
        clean()
        return

    print("== Seeding visitors ==")
    visitors = seed_visitors()
    print("== Seeding visits ==")
    visits = seed_visits(visitors)
    print("== Seeding incidents ==")
    seed_incidents(visits)
    print("== Seeding blacklist ==")
    seed_blacklist()
    print("== Seeding escort assignment ==")
    seed_escort(visits)
    print("== Seeding system config, visiting hours, access zones ==")
    seed_system_data()
    print("\nDone. Refresh the VMS pages to see the data.")


# ---------------------------------------------------------------------------
# System config + visiting hours + access zones — so WF-009 panels show data
# ---------------------------------------------------------------------------
def seed_system_data() -> None:
    cfg, created = SystemConfig.objects.update_or_create(
        key="escort_threshold",
        defaults={"value": "3", "description": "VIP level that mandates an escort"},
    )
    _tick(f"config {cfg.key}={cfg.value}", created)

    cfg2, created = SystemConfig.objects.update_or_create(
        key="max_daily_registrations",
        defaults={"value": "200", "description": "Daily cap per host (BR-007)"},
    )
    _tick(f"config {cfg2.key}={cfg2.value}", created)

    for day, start, end, holiday, name in [
        (0, "09:00", "17:00", False, ""),
        (1, "09:00", "17:00", False, ""),
        (2, "09:00", "17:00", False, ""),
        (3, "09:00", "17:00", False, ""),
        (4, "09:00", "17:00", False, ""),
        (5, "10:00", "14:00", False, ""),
        (6, "00:00", "00:00", True,  "Sunday closed"),
    ]:
        vh, created = VisitingHours.objects.update_or_create(
            day_of_week=day,
            defaults={
                "start_time": start,
                "end_time": end,
                "is_holiday": holiday,
                "holiday_name": name,
                "active": True,
            },
        )
        _tick(f"visiting hours day={day}", created)

    for name, desc, vip, escort, restricted in [
        ("lobby",         "Main reception lobby",        False, False, False),
        ("admin_block",   "Administrative building",     False, False, False),
        ("library",       "Central library",             False, False, False),
        ("server_room",   "Data centre — VIP escort only", True,  True,  True),
        ("labs",          "Research lab corridor",       False, True,  True),
    ]:
        z, created = AccessZone.objects.update_or_create(
            name=name,
            defaults={
                "description": desc,
                "requires_vip": vip,
                "requires_escort": escort,
                "is_restricted": restricted,
                "active": True,
            },
        )
        _tick(f"zone {z.name}", created)


if __name__ == "__main__":
    main()
