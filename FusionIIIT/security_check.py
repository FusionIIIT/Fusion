#!/usr/bin/env python3
"""Endpoint-auth regression guard for the in-production Fusion apps.

Static analysis (no Django runtime needed). Run from the FusionIIIT dir:

    python3 security_check.py

Exit code 0 = clean, 1 = a hard regression was found (suitable for CI / pre-commit).

Invariants (each previously broke in this codebase):

  GUARD A  (hard)  A view-auth decorator (@login_required / @require_designation /
                   @role_required) must only sit on a *view* whose first parameter
                   is `request`. On a helper it does `firstarg.user` and 500s.
  GUARD B  (hard)  A helper (first param != request) must NOT be routed as a URL
                   view -- helpers are internal and must stay unreachable over HTTP.
  GUARD C  (review) Every routed view should be gated: not AllowAny, and a plain
                   Django function view must carry an auth decorator. Printed for
                   review (a few cases are intentional public/read endpoints).
"""
import os
import re
import sys
import glob

APPS = [
    "academic_information", "academic_procedures",
    "examination", "online_cms", "programme_curriculum",
]
APP_DIR = "applications"
AUTH_DECORATORS = ("login_required", "require_designation", "role_required")
# In-body auth (the view authorizes inside its function body, not via a decorator).
INBODY_AUTH = ("_user_from_request", "user_holds_role", "user_holds_any_role",
               "require_designation(", "role_required(")
# Endpoints that are public catalog reads BY DESIGN (unauthenticated twins exist).
PUBLIC_ALLOWLIST = {
    "view_all_programmes", "view_all_working_curriculums", "view_all_courses",
    "view_all_discplines", "view_all_batches", "view_a_course", "view_a_courseslot",
    "view_a_semester_of_a_curriculum", "view_curriculums_of_a_programme",
    "view_semesters_of_a_curriculum", "faculty_view_a_course",
}

# A decorator header may be separated from its def/class by comment or blank
# lines (valid Python). Capture that whole header; comment lines are stripped
# later so a *commented-out* decorator is NOT mistaken for an active one.
HEADER = r'((?:^[ \t]*(?:@[^\n]*|#[^\n]*|)\n)*)'
DEF_RE = re.compile(HEADER + r'^def[ \t]+(\w+)[ \t]*\(([^)]*)', re.M)
CLASS_RE = re.compile(HEADER + r'^class[ \t]+(\w+)[ \t]*\(', re.M)


def active_decorators(header):
    """Drop comment/blank lines so commented-out decorators don't count."""
    return "\n".join(l for l in header.splitlines() if l.lstrip().startswith("@"))
# capture the dotted view reference after the route pattern, e.g. views.foo or Bar.as_view
ROUTE_RE = re.compile(r"(?:path|url)\(\s*r?['\"][^'\"]*['\"]\s*,\s*([\w.]+)", re.M)


def view_files(app):
    out = []
    for d in (f"{APP_DIR}/{app}", f"{APP_DIR}/{app}/api"):
        if os.path.isdir(d):
            out += sorted(glob.glob(f"{d}/views*.py"))
    return out


def parse_defs(src):
    """{name: (decorator_block, first_param)} for module-level defs."""
    out = {}
    bounds = sorted(x.start() for x in re.finditer(r'^(?:def|class)[ \t]', src, re.M))
    for m in DEF_RE.finditer(src):
        decs, name, params = active_decorators(m.group(1)), m.group(2), m.group(3)
        first = params.split(",")[0].strip().split(":")[0].strip() if params.strip() else ""
        defkw = m.start() + len(m.group(1))
        nxt = next((b for b in bounds if b > defkw), len(src))
        out.setdefault(name, (decs, first, src[defkw:nxt]))   # (decs, first_param, body)
    return out


def parse_classes(src):
    """{name: (decorator_block, body)} for top-level classes."""
    out = {}
    M = list(CLASS_RE.finditer(src))
    # boundaries = all top-level class/def starts
    bounds = sorted([m.start() for m in CLASS_RE.finditer(src)] +
                    [m.start() for m in re.finditer(r'^(?:def|class)[ \t]', src, re.M)])
    for m in M:
        decs, name = active_decorators(m.group(1)), m.group(2)
        nxt = next((b for b in bounds if b > m.start()), len(src))
        out.setdefault(name, (decs, src[m.start():nxt]))
    return out


def routed_refs(app):
    """{view_name: file_or_None} for every route in this app's urls files."""
    routed = {}
    for urls in (f"{APP_DIR}/{app}/urls.py", f"{APP_DIR}/{app}/api/urls.py"):
        if not os.path.exists(urls):
            continue
        d = os.path.dirname(urls)
        src = open(urls, encoding="utf-8", errors="ignore").read()
        for ref in ROUTE_RE.findall(src):
            ref = ref[:-len(".as_view")] if ref.endswith(".as_view") else ref
            parts = ref.split(".")
            if len(parts) >= 2:           # module.View  (e.g. views.foo)
                module, name = parts[0], parts[1]
            else:                          # directly-imported View
                module, name = "views", parts[0]
            if name in ("as_view", "site"):
                continue
            cand = f"{d}/{module}.py"
            routed[name] = cand if os.path.exists(cand) else None
    return routed


def fn_gated(decs):
    if "AllowAny" in decs:
        return False
    if any(("@" + k) in decs for k in AUTH_DECORATORS):
        return True
    if "@api_view" in decs:               # DRF default permission = IsAuthenticated
        return True
    return "IsAuthenticated" in decs or "permission_classes" in decs


def class_gated(decs, body):
    head = decs + body[:600]
    if "AllowAny" in head:
        return False
    # APIView with no explicit permission still gets DRF default IsAuthenticated
    return True


def main():
    guard_a, guard_b, guard_c = [], [], []
    for app in APPS:
        # Per-file maps so a route resolves to its ACTUAL file (names like
        # verify_registration exist in both views.py and api/views.py).
        per_defs, per_classes = {}, {}
        all_defs = {}
        for f in view_files(app):
            src = open(f, encoding="utf-8", errors="ignore").read()
            per_defs[f] = parse_defs(src)
            per_classes[f] = parse_classes(src)
            for n, info in per_defs[f].items():
                all_defs.setdefault(n, (f, *info))      # (file, decs, first) for A/B
        routed = routed_refs(app)

        # GUARD A/B: any mis-decorated / routed helper in any file of the app
        for name, (f, decs, first, _body) in all_defs.items():
            is_helper = first not in ("request", "self", "cls")
            if is_helper and any(("@" + k) in decs for k in AUTH_DECORATORS):
                guard_a.append(f"{app}: {name}( first='{first or '<none>'}' ) [{f}]")
            if is_helper and name in routed:
                guard_b.append(f"{app}: helper {name} is routed as a view")

        # GUARD C: check the def/class in the file the route actually resolves to
        for name, fpath in routed.items():
            d = per_defs.get(fpath, {})
            c = per_classes.get(fpath, {})
            if name in d:
                decs, _first, body = d[name]
                gated = (name in PUBLIC_ALLOWLIST or fn_gated(decs)
                         or any(tok in body for tok in INBODY_AUTH))
                if not gated:
                    guard_c.append(f"{app}: {name}() [{fpath}]")
            elif name in c:
                decs, body = c[name]
                if not class_gated(decs, body):
                    guard_c.append(f"{app}: {name} (class, AllowAny) [{fpath}]")
            # unresolved file / imported elsewhere -> skip

    def section(title, items):
        print(f"\n{title}: {'PASS' if not items else f'{len(items)} FOUND'}")
        for it in sorted(set(items)):
            print(f"  - {it}")

    print("=" * 70)
    print("Fusion endpoint-auth regression guard")
    print("=" * 70)
    section("GUARD A (hard) view-auth decorator on a helper", guard_a)
    section("GUARD B (hard) helper routed as a view", guard_b)
    section("GUARD C (review) routed view without a detectable auth gate", guard_c)

    hard = len(guard_a) + len(guard_b)
    print("\n" + "-" * 70)
    print(f"hard failures: {hard}   review items: {len(guard_c)}")
    if hard:
        print("RESULT: FAIL (hard regression). Fix GUARD A / GUARD B above.")
        return 1
    print("RESULT: PASS (no hard regressions).")
    if guard_c:
        print("Note: review GUARD C; some are intentional public/read endpoints.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
