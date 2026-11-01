# Employee Leave Management in Fusion

ELM is implemented inside Fusion's existing `applications.leave` Django app and reuses `Leave`, `LeaveSegment`, `LeavesCount`, `User`, `ExtraInfo`, `Designation`, and `HoldsDesignation`. The legacy leave screens, APIs, and data remain available. The ELM entry point is `/leave/elm/`.

## Initial configuration

An authorized Django administrator must create leave types using the existing names `Casual`, `Restricted`, `Special Casual`, `Earned`, `Commuted`, and `Vacation`; seed the employee `LeavesCount` records; and publish `ELMPolicy` records with effective dates. The requirements' baseline entitlements are CL 8, RH 2, SCL 15, non-faculty EL 30, faculty VL 60, and eligible COL 20. Eligibility, carry-forward, medical-evidence, and substitute requirements are explicit policy fields. No policy is implicitly effective until published.

Publish each year's `ELMCalendar` with its RH, vacation, and closed dates. `effective_from` and `effective_to` define which published calendar applies. Configure `ELMRouteConfiguration` records per category and unit, including an `is_unit_head` mapping, ordered sanction/Establishment steps, optional reminder/escalation hours, a Director self-sanction mapping, and a resumption-verifier mapping where applicable. ELM fails closed when an effective policy or route is missing; unit-specific hierarchy and SLA durations are not hard-coded.

## Workflow and operations

Employee applications reserve leave balance and write an `ELMAccountTransaction`. Workflow decisions are restricted to the assigned `ELMWorkflowTask` user. Pending requests can be modified and revalidated or withdrawn; substitute decline permits a replacement nomination. Approved-leave cancellation, extension, and resumption are separate `ELMChangeRequest` records. Authorized leave administrators can record an existing paper-sanctioned leave at `/leave/elm/offline/`; this synchronizes the account and does not create an approval task. The dashboard shows balance transactions, printable applications, and CSV export.

Authenticated DRF endpoints are available under `/leave/api/elm/`: `GET`/`POST applications/`, `POST tasks/<id>/respond/`, and `GET account/?year=<year>`. They use the current session or Fusion's token authentication and scope employee inquiry to the signed-in user; task responses require the signed-in user to be the assignee.

Celery Beat runs configured SLA processing hourly and year-end account processing on December 31. `ELMYearEndRun` stores completion and exceptions; `ELMActionLog` stores reminders, escalations, and exceptions. The year-end task is idempotent by leave year.

## Validation

Run from `FusionIIIT/` in the repository's documented Python/Django environment:

```text
python manage.py makemigrations leave
python manage.py migrate
python manage.py check
python manage.py test applications.leave
```

ELM service tests cover half-day CL charging, continuous-day weekend counting, application balance reservation, task creation, and withdrawal restoration. Integration with attendance synchronization and any institute-specific approval hierarchy still depends on published Fusion configuration; this module records verified resumption but does not write to a separate attendance system because this repository does not expose an ELM attendance contract.
