# Placement Cell test suite

Reliable, self-contained tests for the `placement_cell` API module.

## Roles

The placement module recognises four roles (the user's selected designation,
exposed to the frontend as `state.user.role`):

| Role (designation)  | What the role can do |
|---------------------|----------------------|
| `placement officer` | TPO: manage placement schedules, applications, interview rounds, debarments, restrictions, statistics, CV downloads and notifications |
| `placement chairman`| Admin: manage placement policies plus the officer capabilities |
| `student`           | Apply for placements, manage placement profile, view schedule/offers, download CV |
| `alumni`            | Alumni hub: alumni profile, referrals and mentorship sessions |

How roles are resolved:

- **Backend** authorizes via `HoldsDesignation(working=user, designation__name=…)`;
  `selectors.is_tpo` is true for `placement officer`/`placement chairman`.
- **Sidebar visibility** comes from `ModuleAccess.placement_cell` for the
  designation (surfaced by `/api/auth/me`).
- **Frontend** picks the tab set in `PlacementCellPage` from `state.user.role`.

### Role accounts

`manage.py setup_placement_roles` creates one idempotent login per role and
enables `ModuleAccess.placement_cell` for each:

| Username             | Role                |
|----------------------|---------------------|
| `placement_officer`  | placement officer   |
| `placement_chairman` | placement chairman  |
| `placement_student`  | student             |
| `placement_alumni`   | alumni              |

Create / refresh them (the password is supplied at runtime and is **not** stored
in this repo — pass `--password` or set `PLACEMENT_ROLE_PASSWORD`):

```bash
cd FusionIIIT
python manage.py setup_placement_roles --password '<password>'
```

## Running

Tests use a dedicated settings module (`FusionIIIT/test_settings.py`) that
disables migrations so the test database is built directly from the current
models. This is required because the project's historical migration chain does
not apply on a fresh database (e.g. `programme_curriculum.0026`), which would
otherwise break test-DB creation for reasons unrelated to placement.

List the modules explicitly — `applications/` has no `__init__.py`, so unittest
package/app-level discovery (`manage.py test applications.placement_cell`) fails
project-wide:

```bash
cd FusionIIIT
python manage.py test \
    applications.placement_cell.tests.test_placement_api \
    applications.placement_cell.tests.test_use_cases \
    applications.placement_cell.tests.test_business_rules \
    applications.placement_cell.tests.test_workflows \
    applications.placement_cell.tests.test_module \
    --settings=test_settings
```

Requires `PyYAML` (declared in `requirements.txt`) for the spec-driven modules.

## Layout

| File | What it covers |
|------|----------------|
| `test_placement_api.py` | Schema regressions (e.g. `Education.grade` width), URL wiring is API-only, authentication + role authorization. Has no external deps. |
| `test_use_cases.py` | Use-case scenarios from `specs/use_cases.yaml`. |
| `test_business_rules.py` | Business rules from `specs/business_rules.yaml`. |
| `test_workflows.py` | End-to-end workflows from `specs/workflows.yaml`. |
| `test_module.py` | Selector/service unit tests (active). The `PlacementCellApiTests` class is **skipped**: it exercises the `globals` dashboard-notification API (`NotificationList`, `Notification.module`) that is not present on this branch. Re-enable once that lands. |

## Expected result

`OK (skipped=36)` — all executed tests pass; the only skips are the documented
cross-module integration tests in `test_module.PlacementCellApiTests`.
