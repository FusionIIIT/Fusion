"""Programme-scoped academic administration.

`acadadmin` administers the whole institute. The Acad UG / Acad PG / Acad Ph.D.
roles do the same work for one programme category only, so every view they can
reach must narrow its data to that category. A view that is not scoped yet stays
closed to them, which costs them the feature but never leaks another
programme's students.
"""
from django.db.models import Q

from applications.globals.models import HoldsDesignation

SCOPE_BY_ROLE = {
    "Acad UG": "UG",
    "Acad PG": "PG",
    "Acad Ph.D.": "PHD",
}

UNSCOPED_ACAD_ROLES = ("acadadmin", "studentacadadmin")

SCOPED_ACAD_ROLES = tuple(SCOPE_BY_ROLE)

ALL_ACAD_ROLES = UNSCOPED_ACAD_ROLES + SCOPED_ACAD_ROLES

STUDENT_CATEGORY_PATH = "batch_id__curriculum__programme__category"

# Programme names as they are stored on Student.programme and on
# BatchConfiguration.programme. The PhD promotion flow writes 'Ph.D' while
# academic_information.Constants declares 'PhD', so both spellings count.
PROGRAMME_NAMES_BY_SCOPE = {
    "UG": ("B.Tech", "B.Des"),
    "PG": ("M.Tech", "M.Des"),
    "PHD": ("PhD", "Ph.D"),
}

# 'ug' / 'pg' / 'phd' as the admission-record models spell it
ADMISSION_TYPE_BY_SCOPE = {"UG": "ug", "PG": "pg", "PHD": "phd"}


def _role_names(user):
    if user is None or not getattr(user, "is_authenticated", False):
        return set()
    return set(
        HoldsDesignation.objects
        .filter(user=user)
        .values_list("designation__name", flat=True)
    )


def active_role(user):
    return getattr(getattr(user, "extrainfo", None), "last_selected_role", None)


def scopes_for(user):
    """Programme categories this user may see, or None for all of them.

    Someone holding both acadadmin and a programme role sees the whole
    institute until they switch to that role, so the switcher in the sidebar
    actually changes what the screen shows. Selecting a role you do not hold
    grants nothing, so this cannot be used to widen access.
    """
    names = _role_names(user)
    selected = active_role(user)
    if selected in SCOPE_BY_ROLE and selected in names:
        return frozenset({SCOPE_BY_ROLE[selected]})
    if names & set(UNSCOPED_ACAD_ROLES):
        return None
    scopes = {SCOPE_BY_ROLE[name] for name in names if name in SCOPE_BY_ROLE}
    return frozenset(scopes) if scopes else None


def is_scoped(user):
    return scopes_for(user) is not None


def scope_students(queryset, scopes):
    if scopes is None:
        return queryset
    return queryset.filter(**{"%s__in" % STUDENT_CATEGORY_PATH: scopes})


def scope_via_student(queryset, scopes, student_path):
    """Narrow any queryset that reaches a Student through ``student_path``."""
    if scopes is None:
        return queryset
    key = "%s__%s__in" % (student_path, STUDENT_CATEGORY_PATH)
    return queryset.filter(**{key: scopes})


def scope_allows(scopes, category):
    return scopes is None or (category or "").upper() in scopes


def student_in_scope(student, scopes):
    if scopes is None:
        return True
    try:
        category = student.batch_id.curriculum.programme.category
    except AttributeError:
        return False
    return scope_allows(scopes, category)


def batch_in_scope(batch, scopes):
    if scopes is None:
        return True
    try:
        return scope_allows(scopes, batch.curriculum.programme.category)
    except AttributeError:
        return False


def scope_batches(queryset, scopes):
    if scopes is None:
        return queryset
    return queryset.filter(curriculum__programme__category__in=scopes)


def scoped_ids(model, ids, scopes, student_path="student"):
    """Keep only the ids whose student falls inside ``scopes``."""
    if scopes is None:
        return list(ids)
    numeric = []
    for value in ids:
        try:
            numeric.append(int(value))
        except (TypeError, ValueError):
            continue
    allowed = scope_via_student(
        model.objects.filter(id__in=numeric), scopes, student_path)
    return list(allowed.values_list("id", flat=True))


def programme_names_for(scopes):
    """Programme names inside ``scopes``, or None when nothing is excluded."""
    if scopes is None:
        return None
    names = []
    for scope in scopes:
        names.extend(PROGRAMME_NAMES_BY_SCOPE.get(scope, ()))
    return tuple(names)


def programme_name_in_scope(name, scopes):
    if scopes is None:
        return True
    return (name or "") in programme_names_for(scopes)


def scope_by_programme_name(queryset, scopes, field="programme"):
    """Narrow rows that name their programme, such as BatchConfiguration."""
    if scopes is None:
        return queryset
    names = programme_names_for(scopes)
    if not names:
        return queryset.none()
    return queryset.filter(**{"%s__in" % field: names})


def admission_type_in_scope(programme_type, scopes):
    """For the 'ug'/'pg'/'phd' programme_type the admission models carry."""
    if scopes is None:
        return True
    wanted = (programme_type or "").strip().lower()
    return wanted in {ADMISSION_TYPE_BY_SCOPE[s] for s in scopes
                      if s in ADMISSION_TYPE_BY_SCOPE}


def scope_admission_records(queryset, scopes):
    """Narrow admission records. StudentBatchUpload names its own programme_type
    ('ug'/'pg'); PhdStudentBatchUpload has no such field and is PhD by model."""
    if scopes is None:
        return queryset
    field_names = {f.name for f in queryset.model._meta.fields}
    if "programme_type" not in field_names:
        return queryset if "PHD" in scopes else queryset.none()
    values = []
    for scope in scopes:
        spelling = ADMISSION_TYPE_BY_SCOPE.get(scope)
        if spelling:
            values.extend([spelling, spelling.upper()])
    if not values:
        return queryset.none()
    return queryset.filter(programme_type__in=values)


def scope_recipients(users, scopes):
    """Drop students outside the scope. Faculty and staff are not bound to a
    programme, so they stay: a role-targeted announcement still reaches them."""
    if scopes is None:
        return users
    return users.filter(
        Q(**{"extrainfo__student__" + STUDENT_CATEGORY_PATH + "__in": scopes})
        | Q(extrainfo__student__isnull=True)
    )


def allows_phd(scopes):
    return scopes is None or "PHD" in scopes


def admission_record_in_scope(record, scopes):
    if scopes is None:
        return True
    programme_type = (getattr(record, "programme_type", "") or "").upper()
    if not programme_type:
        return "PHD" in scopes
    return programme_type in scopes


ROLL_IN_SCOPE_SQL = """
    roll_no IN (
        SELECT s.id_id
        FROM academic_information_student s
        JOIN programme_curriculum_batch b ON s.batch_id_id = b.id
        JOIN programme_curriculum_curriculum c ON b.curriculum_id = c.id
        JOIN programme_curriculum_programme p ON c.programme_id = p.id
        WHERE p.category IN %s
    )
"""


def roll_scope_sql(scopes, alias="sg"):
    """SQL fragment and params confining a grade row's roll_no to ``scopes``."""
    if scopes is None:
        return "", []
    clause = ROLL_IN_SCOPE_SQL.replace("roll_no IN", "%s.roll_no IN" % alias, 1)
    return "AND " + clause, [tuple(sorted(scopes))]


def scope_grade_rows(queryset, scopes, roll_field="roll_no"):
    """Narrow rows keyed by a student's roll number, via a subquery rather
    than a materialised id list."""
    if scopes is None:
        return queryset
    from applications.academic_information.models import Student

    rolls = scope_students(Student.objects.all(), scopes).values("id_id")
    return queryset.filter(**{"%s__in" % roll_field: rolls})


def scope_programmes(queryset, scopes):
    if scopes is None:
        return queryset
    return queryset.filter(category__in=scopes)


def scope_curriculums(queryset, scopes):
    if scopes is None:
        return queryset
    return queryset.filter(programme__category__in=scopes)
