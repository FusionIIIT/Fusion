# Fusion-Integrated

The non-academic platform. **Placement Cell** first; more modules later.
**Independent modules, one login.**

This service holds **no user table**. Identity, RBAC and common directory data
(student info, faculty info, staff info) all come from
**Fusion_System_Administrator**, which is the IAM.

```
        Fusion_System_Administrator   ( = the IAM )
        owns fusion_system_db
        · identity  — authenticates ALL users
        · RBAC      — roles, permissions, module grants
        · directory — student / faculty / staff info
        · its OWN console at /sysadmin/, its own operator login
                 │
                 │  HTTP   /api/iam/v1/*
                 ▼
        Fusion-Integrated                ← this repo
        owns fusion_integrated
        backend  →  placement  (more modules later)
        client   →  the shell: one login, one sidebar
        holds only user_id references — no user table
```

## Two logins, on purpose

|  | Who | Where | Against |
|---|---|---|---|
| **User login** | students, faculty, staff | this app's shell | the ERP user pool, via IAM |
| **Operator login** | sysadmin operators | `/sysadmin/`, its own URL | the console's own account pool |

Users get **one** login for every module they are granted. Operators keep a
separate door to the admin console — different audience, different account set.
Both are backed by the same identity service; they are not the same login page.

---

## Quick start

```bash
make install          # uv venv + dependencies
make up               # postgres + 2× redis (cache and broker, separately)
cp .env.example .env
make migrate seed     # schema, module registry, demo data
make dev              # http://127.0.0.1:8002
make check            # everything CI runs
```

Requires Python 3.12, [uv](https://docs.astral.sh/uv/) and Docker.

---

## What "independent module" actually means here

Not a naming convention — four rules, each enforced by a CI job that has been
tested against a deliberate violation:

| Rule | Enforced by |
|---|---|
| A module may reach another **only** through its `contracts.py` | `lint-imports` |
| **No foreign key crosses a module boundary** | `ops/checks/no_cross_module_fk.py` |
| `domain/` may not import Django, DRF or Celery | `lint-imports` |
| Cross-module getters are **plural** — they take a sequence of ids | `ops/checks/contracts_are_plural.py` |

The payoff is concrete: every module owns its own tables and its own migration
file, so lifting one out into its own service later means changing one file's
implementation, not doing schema surgery.

The plural rule is the sneaky-useful one. There is no `get_employment(user_id)`
anywhere, only `get_employments(user_ids)` — which makes the N+1 not merely
discouraged but *unwritable*.

### Anatomy of a module

```
modules/placement/
├── apps.py          Django app config
├── registry.py      its sidebar entry — seeded by `manage.py seed_modules`
├── contracts.py     THE ONLY thing other modules may import
├── models.py        its own tables, its own migrations
├── domain/          pure Python. rules, state machine. no Django.
├── selectors/       all reads.  ownership filtering lives here
├── services/        all writes. transactions, audit rows, domain→HTTP translation
├── api/             thin: serializers, views, urls
└── tests/
```

Adding a module: create the directory, add one line to `DOMAIN_MODULES` in
`config/settings/base.py`, write `registry.py`, run `make seed`. Nothing central
to edit — no menu array, no boolean column, no shadow model.

---

## How a request is authorized

Two gates, both server-side, on **every** request:

```python
permission_classes = [
    HasModuleGrant("placement_cell"),               # is this module yours at all?
    HasPermission("placement_cell.application.view"),  # may you do this?
]
```

Both must pass; the default is deny. `fusion_auth` resolves the caller's session
against IAM (cookie or `Authorization: Token`), builds a `Principal`, and every
check reads that.

**The sidebar is server-driven.** `GET /api/v1/me` returns `navigation` already
filtered and already in render shape — the client does zero filtering, so it
cannot draw a module the server did not send. This replaces the legacy pattern
of a hardcoded client array whose ids had to exactly match database *column*
names.

Ownership is enforced by filtering the queryset in the selector, never by
fetching-then-checking, which is why a foreign id naturally yields **404** and
not 403 (403 would leak existence and turn any id column into an enumeration
oracle).

---

## Layout

```
config/          settings (base/dev/test/prod), urls, celery
core/            shared kernel — error envelope, pagination, request-id, mixins
fusion_auth/     the IAM client, Principal, authentication, the two permission gates
modules/
  directory/     local projection of IAM's user data (a cache with a table)
  accesscontrol/ module registry + the server-driven sidebar
  placement/     companies, postings, applications, eligibility, state machine
ops/checks/      the boundary enforcement scripts
client/          the shell — Vite + React 18 + TS + Mantine 7.13
```

`core/` may not import `modules` — it is a leaf, and CI checks that too.

---

## Testing

```bash
make test          # 40 tests, ~0.6s
```

Domain tests are pure Python with no database, which is why they run in
milliseconds — that is the whole point of the no-Django-in-`domain/` rule. The
IAM is never contacted: `conftest.py` swaps in an in-memory fake, so the suite
needs no network and no running Fusion_System_Administrator.

---

## The client

```bash
cd client && npm install && npm run dev      # :5173, proxies /api to :8002
```

Vite + React 18 + TypeScript (strict) + Mantine **7.13.4, pinned to match the
sysadmin client** so the two apps look like one product. `theme.ts` and
`AppShellLayout.module.css` are ports of that client's files, not a redesign.

Routes are built **only** for modules the server granted, so an ungranted module
has no route — deep-linking it hits NotFound rather than an empty shell. Module
pages are lazy chunks (`PostingsPage`, `ApplicationsPage` build separately).

## Extracting a module into its own repo

This is what "independent" is for. Removing `hr` and `leave` from this codebase
touched **five files**, none of them in `placement`:

```
config/settings/base.py     one line in DOMAIN_MODULES
config/urls.py              one include()
devtools/…/seed_demo.py     fixtures
.importlinter               contract membership
modules/<name>/             the directory itself
```

Nothing in `placement`, `directory`, `accesscontrol`, `core` or `fusion_auth`
referenced them, because the boundary rules make that impossible. The same holds
in reverse: lifting a module into a separate repo means taking its directory and
its migrations, then replacing its `contracts.py` callers with HTTP.

## Status

Working today: the module system, both authorization gates, the server-driven
sidebar, the directory projection, the placement application state machine with
an append-only audit trail, and the client shell with login.

**Blocking next step — the IAM side.** `Fusion_System_Administrator` currently
authenticates operators only; its own router says so: *"this is what makes admin
operators a separate account set from the 3277 managed ERP users."* It needs
ERP-user authentication plus `/api/iam/v1/{auth/login, auth/logout, me,
directory/users}`. The client for those is written and tested against a fake —
the expected contract is in `fusion_auth/client.py`.

Then: offers and selection rounds, the declared-CPI integration.

Design documents — architecture, ADRs, the RBAC model, the placement domain and
the academic-snapshot contract — are in [`docs/`](docs/).
