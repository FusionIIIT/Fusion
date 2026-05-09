"""VMS RBAC inspection tool.

Usage (run from the FusionIIIT directory):

    python vms_rbac.py list
        List every HostAuthority row: user, level, department, VIP-bypass flag.

    python vms_rbac.py check <username>
        Show which VMS permission classes pass/fail for <username>, and
        therefore which endpoints they can reach.

    python vms_rbac.py endpoints
        Print every VMS endpoint grouped by its permission requirement.

    python vms_rbac.py matrix
        Print the full role x endpoint access matrix.

    python vms_rbac.py users
        List all Django users alongside their VMS authority (if any).

This script only *reads* state; it does not create, modify, or remove
HostAuthority rows.
"""

from __future__ import annotations

import os
import sys
from typing import Iterable

# --- Django bootstrap -------------------------------------------------------
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Fusion.settings.development")
import django  # noqa: E402
django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from applications.vms.models import HostAuthority  # noqa: E402
from applications.vms.permissions import (  # noqa: E402
    CanBypassVIPApproval,
    CanRemoveBlacklist,
    HasHostApprovalAuthority,
    IsSuperAdmin,
    IsVmsAdmin,
)

User = get_user_model()

# ---------------------------------------------------------------------------
# Endpoint inventory. Mirrors applications/vms/api/views.py permission_classes.
# Each entry: (http_method, url_path, view_name, [permission_class_names...])
# ---------------------------------------------------------------------------
ENDPOINTS: list[tuple[str, str, str, list[str]]] = [
    # Staff tier (any authenticated user)
    ("POST", "/vms/register/",          "RegisterVisitorView",       ["Authenticated"]),
    ("POST", "/vms/verify/",            "VerifyVisitorView",         ["Authenticated"]),
    ("POST", "/vms/pass/",              "IssuePassView",             ["Authenticated"]),
    ("POST", "/vms/entry/",             "RecordEntryView",           ["Authenticated"]),
    ("POST", "/vms/exit/",              "RecordExitView",            ["Authenticated"]),
    ("POST", "/vms/deny/",              "DenyEntryView",             ["Authenticated"]),
    ("GET",  "/vms/active/",            "ActiveVisitorsView",        ["Authenticated"]),
    ("GET",  "/vms/recent/",            "RecentVisitsView",          ["Authenticated"]),
    ("GET",  "/vms/incidents/",         "SecurityIncidentView",      ["Authenticated"]),
    ("POST", "/vms/incidents/",         "SecurityIncidentView",      ["Authenticated"]),
    ("POST", "/vms/scan/",              "ScanPassView",              ["Authenticated"]),
    ("POST", "/vms/manual-check/",      "ManualVerificationView",    ["Authenticated"]),
    ("GET",  "/vms/overstay/",          "OverstayView",              ["Authenticated"]),
    ("GET",  "/vms/location/<id>/",     "VisitorLocationView",       ["Authenticated"]),
    ("GET",  "/vms/me/",                "WhoAmIView",                ["Authenticated"]),
    ("GET",  "/vms/blacklist/",         "BlacklistView (GET)",       ["Authenticated"]),
    ("POST", "/vms/escorts/",           "EscortAssignView",          ["Authenticated"]),
    ("GET",  "/vms/escorts/",           "EscortAssignView",          ["Authenticated"]),
    ("GET",  "/vms/escorts/available/", "AvailableEscortsView",      ["Authenticated"]),
    ("POST", "/vms/escorts/<id>/release/", "EscortReleaseView",      ["Authenticated"]),

    # Admin tier
    ("POST", "/vms/blacklist/",                   "BlacklistView (POST)",         ["Authenticated", "IsVmsAdmin"]),
    ("GET",  "/vms/blacklist/audit/<id>/",        "BlacklistAuditView",           ["Authenticated", "IsVmsAdmin"]),
    ("GET",  "/vms/history/<id>/",                "VisitorHistoryView",           ["Authenticated", "IsVmsAdmin"]),
    ("GET",  "/vms/history/<id>/incidents/",      "IncidentHistoryView",          ["Authenticated", "IsVmsAdmin"]),
    ("GET",  "/vms/visit-history/<id>/",          "VisitorHistoryByVisitView",    ["Authenticated", "IsVmsAdmin"]),
    ("POST", "/vms/vip/process/",                 "VIPProcessView",               ["Authenticated", "IsVmsAdmin"]),
    ("GET",  "/vms/vip/",                         "VIPVisitorsView",              ["Authenticated", "IsVmsAdmin"]),
    ("GET",  "/vms/vip/<id>/activity/",           "VIPActivityView",              ["Authenticated", "IsVmsAdmin"]),
    ("POST", "/vms/reports/",                     "ReportGenerationView",         ["Authenticated", "IsVmsAdmin"]),
    ("POST", "/vms/export/",                      "DataExportView",               ["Authenticated", "IsVmsAdmin"]),
    ("POST", "/vms/import/",                      "DataImportView",               ["Authenticated", "IsVmsAdmin"]),
    ("GET",  "/vms/data-operations/",             "DataOperationsView",           ["Authenticated", "IsVmsAdmin"]),
    ("POST", "/vms/visiting-hours/",              "VisitingHoursView (POST)",     ["Authenticated", "IsVmsAdmin"]),
    ("POST", "/vms/zones/",                       "AccessZoneView (POST)",        ["Authenticated", "IsVmsAdmin"]),

    # Blacklist removal
    ("POST", "/vms/blacklist/<id>/remove/",       "BlacklistRemoveView",          ["Authenticated", "CanRemoveBlacklist"]),

    # Super-admin tier
    ("GET",  "/vms/config/",                      "SystemConfigView (GET)",       ["Authenticated", "IsSuperAdmin"]),
    ("POST", "/vms/config/",                      "SystemConfigView (POST)",      ["Authenticated", "IsSuperAdmin"]),
    ("GET",  "/vms/config/history/",              "ConfigChangeHistoryView",      ["Authenticated", "IsSuperAdmin"]),
]

PERMISSION_MAP = {
    "IsVmsAdmin": IsVmsAdmin,
    "IsSuperAdmin": IsSuperAdmin,
    "CanRemoveBlacklist": CanRemoveBlacklist,
    "CanBypassVIPApproval": CanBypassVIPApproval,
    "HasHostApprovalAuthority": HasHostApprovalAuthority,
}


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------
CHECK = "[ok]"
CROSS = "[no]"

def _tick(ok: bool) -> str:
    return CHECK if ok else CROSS

def _box(title: str) -> None:
    line = "=" * max(60, len(title) + 4)
    print(f"\n{line}\n  {title}\n{line}")

def _rows(rows: Iterable[Iterable[str]]) -> None:
    rows = [list(map(str, r)) for r in rows]
    if not rows:
        return
    widths = [max(len(r[i]) for r in rows) for i in range(len(rows[0]))]
    for r in rows:
        print("  " + "  ".join(cell.ljust(widths[i]) for i, cell in enumerate(r)))


# ---------------------------------------------------------------------------
# A tiny stub that quacks like an authenticated DRF request for a given user.
# The permission classes only inspect `request.user`, so this is sufficient.
# ---------------------------------------------------------------------------
class _FakeRequest:
    def __init__(self, user):
        self.user = user
        self.method = "GET"


def _evaluate(user, perm_names: list[str]) -> dict[str, bool]:
    result: dict[str, bool] = {}
    if "Authenticated" in perm_names:
        result["Authenticated"] = bool(user and user.is_authenticated)
    for name in perm_names:
        if name == "Authenticated":
            continue
        cls = PERMISSION_MAP.get(name)
        if cls is None:
            result[name] = False
            continue
        try:
            result[name] = bool(cls().has_permission(_FakeRequest(user), None))
        except Exception as exc:  # pragma: no cover - diagnostic path
            result[name] = False
            print(f"    ! error evaluating {name}: {exc}")
    return result


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------
def cmd_list() -> None:
    _box("HostAuthority rows")
    rows = [("USERNAME", "LEVEL", "DEPARTMENT", "CAN_APPROVE_VIP", "MAX_DAILY")]
    qs = HostAuthority.objects.select_related("user").order_by("user__username")
    for ha in qs:
        rows.append((
            ha.user.username,
            ha.authority_level,
            ha.department or "-",
            "yes" if ha.can_approve_vip else "no",
            ha.max_daily_approvals,
        ))
    if len(rows) == 1:
        print("  (no HostAuthority rows — every user is plain Staff tier)")
        return
    _rows(rows)


def cmd_users() -> None:
    _box("All users and their VMS authority")
    rows = [("USERNAME", "ACTIVE", "STAFF", "SUPERUSER", "VMS_LEVEL", "VIP_BYPASS")]
    ha_by_user = {ha.user_id: ha for ha in HostAuthority.objects.all()}
    for u in User.objects.order_by("username"):
        ha = ha_by_user.get(u.id)
        rows.append((
            u.username,
            "yes" if u.is_active else "no",
            "yes" if u.is_staff else "no",
            "yes" if u.is_superuser else "no",
            ha.authority_level if ha else "-",
            "yes" if (ha and ha.can_approve_vip) else "no",
        ))
    _rows(rows)


def cmd_endpoints() -> None:
    _box("VMS endpoints and their permission requirements")
    groups: dict[tuple[str, ...], list[tuple[str, str, str]]] = {}
    for method, path, view, perms in ENDPOINTS:
        groups.setdefault(tuple(perms), []).append((method, path, view))
    for perms, eps in groups.items():
        print(f"\n  -- requires: {' + '.join(perms)} --")
        _rows([("METHOD", "PATH", "VIEW"), *eps])


def cmd_check(username: str) -> None:
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        print(f"  ! user '{username}' does not exist")
        sys.exit(1)

    ha = HostAuthority.objects.filter(user=user).first()

    _box(f"RBAC check for '{username}'")
    print(f"  user.is_active       : {user.is_active}")
    print(f"  user.is_staff        : {user.is_staff}")
    print(f"  user.is_superuser    : {user.is_superuser}")
    if ha:
        print(f"  vms authority_level  : {ha.authority_level}")
        print(f"  vms department       : {ha.department or '-'}")
        print(f"  vms can_approve_vip  : {ha.can_approve_vip}")
    else:
        print("  vms authority_level  : (no HostAuthority row — Staff tier only)")

    print("\n  Permission class evaluation:")
    for name, cls in PERMISSION_MAP.items():
        ok = bool(cls().has_permission(_FakeRequest(user), None))
        print(f"    {_tick(ok)}  {name}")

    _box(f"Endpoint access for '{username}'")
    rows = [("RESULT", "METHOD", "PATH", "GATE")]
    allow = deny = 0
    for method, path, _view, perms in ENDPOINTS:
        evals = _evaluate(user, perms)
        ok = all(evals.values())
        rows.append((_tick(ok), method, path, " + ".join(perms)))
        allow += int(ok)
        deny += int(not ok)
    _rows(rows)
    print(f"\n  summary: {allow} allowed  /  {deny} denied  /  {allow + deny} total")


def cmd_matrix() -> None:
    _box("Role x Endpoint access matrix")

    # Craft one representative user per role, purely in memory — we never save.
    class _P:
        def __init__(self, level: str | None = None, vip_bypass: bool = False,
                     authed: bool = True):
            self.level = level
            self.vip_bypass = vip_bypass
            self.authed = authed

    personas = [
        ("Anon",        _P(level=None, authed=False)),
        ("Staff",       _P(level=None)),
        ("Department",  _P(level=HostAuthority.LEVEL_DEPARTMENT, vip_bypass=True)),
        ("Admin",       _P(level=HostAuthority.LEVEL_ADMIN)),
        ("SuperAdmin",  _P(level=HostAuthority.LEVEL_SUPER)),
    ]

    # Build stand-in user + HostAuthority shims.
    class _U:
        def __init__(self, persona: _P):
            self._persona = persona
            self.is_authenticated = persona.authed

    def _evaluate_persona(persona: _P, perms: list[str]) -> bool:
        if "Authenticated" in perms and not persona.authed:
            return False
        # Emulate permissions.py logic against the persona directly.
        for name in perms:
            if name == "Authenticated":
                continue
            if not persona.authed:
                return False
            if name == "IsVmsAdmin":
                if persona.level not in (HostAuthority.LEVEL_ADMIN, HostAuthority.LEVEL_SUPER):
                    return False
            elif name == "IsSuperAdmin":
                if persona.level != HostAuthority.LEVEL_SUPER:
                    return False
            elif name == "CanRemoveBlacklist":
                if persona.level not in (HostAuthority.LEVEL_ADMIN, HostAuthority.LEVEL_SUPER):
                    return False
            elif name == "CanBypassVIPApproval":
                if not persona.vip_bypass:
                    return False
            elif name == "HasHostApprovalAuthority":
                if persona.level not in (
                    HostAuthority.LEVEL_DEPARTMENT,
                    HostAuthority.LEVEL_ADMIN,
                    HostAuthority.LEVEL_SUPER,
                ):
                    return False
        return True

    header = ["METHOD", "PATH"] + [name for name, _ in personas]
    rows = [header]
    for method, path, _view, perms in ENDPOINTS:
        row = [method, path]
        for _, persona in personas:
            row.append(_tick(_evaluate_persona(persona, perms)))
        rows.append(row)
    _rows(rows)
    print("\n  legend: [ok] = permitted   [no] = blocked")
    print("  note: 'Department' persona also has can_approve_vip=True")


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------
def main(argv: list[str]) -> None:
    if len(argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd, *rest = argv[1:]
    if cmd == "list":
        cmd_list()
    elif cmd == "users":
        cmd_users()
    elif cmd == "endpoints":
        cmd_endpoints()
    elif cmd == "matrix":
        cmd_matrix()
    elif cmd == "check":
        if not rest:
            print("  ! usage: python vms_rbac.py check <username>")
            sys.exit(1)
        cmd_check(rest[0])
    else:
        print(f"  ! unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv)
