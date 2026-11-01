# Assignment 7 LMS Course Management implementation

This Codex-assisted LMS implementation targets the AI branch `FusionIIIT/Fusion:lms-v2` and follows the supplied Course Management v1.0 synchronized specification bundle. It is separate from the earlier ELM submissions in Fusion-Integrated.

## Implemented

- New `applications.coursemanagement` Django app, initial migration and `/lms/` routes.
- Existing `academic_procedures.course_registration` records govern student access. Existing `programme_curriculum.CourseInstructor` records govern faculty access. Year and semester type scope each workspace. Registration tables are read, never modified.
- Course home, syllabus/schedule editing, instructor and TA display.
- File, text and link materials, sections, immediate publication and future release.
- Timestamped announcements; TAs need a per-course explicit announcement permission.
- Draft assignments, publication, scheduled release, due date, instructions, submission type and points possible.
- One baseline on-time student submission, private file downloads and own history.
- Faculty/TA draft grading with grader attribution, Faculty-only release, hidden draft feedback, grade audit rows and stale-update checks.
- Explicit per-course TA/Observer bindings through the existing Django admin. Observer views exclude assignments, individual submissions, grades and all writes.
- Celery periodic release task and `python manage.py release_lms_content` fallback.
- Simple server-rendered forms using Fusion's existing base template and authentication.

## Unresolved source policies

The supplied specification intentionally leaves ISS-LMS-001 through ISS-LMS-006 open. Late submissions, resubmissions and edits to released grades return an explicit unresolved-policy error instead of assuming an institutional rule. Notification delivery is not implemented. CourseRole is an implementation binding, not an adjudication of Observer-to-student/section linkage policy. Populate TA/Observer bindings only from an authorized course association; they cannot self-enroll. TA permission configurability remains an implementation choice pending the specification's resolution.

GradeAudit records draft grading and release. Post-release changes remain blocked pending authority/effect clarification; a complete post-release correction lifecycle is not claimed. Missing/late status workflows, broad automated tests and polished frontend integration are not complete. The baseline history records submitted work; explicit missing-status displays are a remaining gap.

## Setup

Use the branch's documented Python 3.8.10, Django 3.1.5 and PostgreSQL 14 environment. Install its existing requirements and configure the supplied Fusion database. Then run:

```text
cd FusionIIIT
python manage.py migrate coursemanagement
python manage.py release_lms_content
```

Start Fusion normally, sign in with an existing account and open `/lms/`. Student registrations and instructor assignments must contain year and semester type; ambiguous legacy rows are not silently mapped to a different offering. Course-role links can be maintained by an authorized Django administrator. Private uploads default to `lms-private` beside `MEDIA_ROOT`; they must not be exposed by the web server. Maximum upload size in the forms is 10 MB (an implementation limit, not a requirement-derived course policy).

## Actual verification

Passed local Python-3.8 grammar parsing, isolated migration generation/application, Django system checks, migration drift and parsing of all three new templates. Isolated smoke checks passed for submission creation, unresolved resubmission refusal, draft grading, Faculty release, audit rows, unresolved post-release edit refusal, scheduled-release replay and invalid points.

These checks used the available Django 5.2.18 runtime with SQLite and patched course authorization. They do not verify the full repository's required Django 3.1.5/PostgreSQL environment, actual registration queries, live login, browser layout, Celery worker or complete requirements coverage. The full legacy dependency stack was not installed under the submission time limit. Run the checked-in isolated checker with an appropriate Django environment; it creates only an in-memory database.

The Assignment 7 guideline names Fusion-Integrated, but that repository has no LMS branch. The user explicitly selected `FusionIIIT/Fusion:lms-v2` after the repository README identified v2 as the AI implementation branch. The source fork branch and PR target should both be `lms-v2` in their respective repositories.
