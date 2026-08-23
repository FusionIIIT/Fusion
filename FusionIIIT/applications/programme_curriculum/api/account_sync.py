"""Push an admission record's details onto the account it created.

Upcoming Batches is the source of truth for the batches it covers (2025
onwards). The account tables stay the read surface for the whole institute,
so students from earlier batches, who have no admission record, are
untouched by this.
"""
import re

from applications.academic_information.models import Student
from applications.globals.models import ExtraInfo

SEX_BY_GENDER = {"MALE": "M", "M": "M", "FEMALE": "F", "F": "F", "OTHER": "O"}

# the one vocabulary both the sync and the normalising command work from
RESERVATION_BY_RAW_CATEGORY = {
    "GEN": "GEN", "GENERAL": "GEN", "UR": "GEN", "OP": "GEN",
    "OPNO": "GEN", "OPPH": "GEN", "EWS": "GEN", "GEN-EWS": "GEN",
    "GEN- EWS": "GEN", "GEN EWS": "GEN", "EWNO": "GEN", "EWPH": "GEN",
    "GEN-PWD": "GEN", "GEN_PWD": "GEN",
    "OBC": "OBC", "OBC-NCL": "OBC", "BCNO": "OBC", "BCPH": "OBC",
    "SC": "SC", "SCNO": "SC", "SC 2 LAKH": "SC", "SCPH": "SC",
    "ST": "ST", "STNO": "ST", "ST 2 LAKH": "ST", "STPH": "ST",
    "OTHER BACKWARD CLASS": "OBC",
    "OTHER BACKWARD CLASS (NON-CREAMY LAYER)": "OBC",
    "SCHEDULED CASTE": "SC",
    "SCHEDULED TRIBE": "ST",
    "ECONOMICALLY WEAKER SECTION": "GEN",
    "GENERAL EWS": "GEN",
}

EWS_CATEGORIES = {
    "EWS", "GEN-EWS", "GEN- EWS", "GEN EWS", "EWNO", "EWPH",
    "GENERAL EWS", "ECONOMICALLY WEAKER SECTION",
}

PWD_CATEGORIES = {"OPPH", "EWPH", "BCPH", "GEN-PWD", "GEN_PWD"}


def reservation_category(raw):
    """Narrow any spelling of a category to the four the account field allows."""
    return RESERVATION_BY_RAW_CATEGORY.get(" ".join(str(raw or "").split()).upper())


def admission_category(raw):
    """Narrow any spelling to the codes the admission model declares, which
    unlike the account keep EWS as a category of its own."""
    cleaned = " ".join(str(raw or "").split()).upper()
    if cleaned in EWS_CATEGORIES:
        return "EWS"
    return RESERVATION_BY_RAW_CATEGORY.get(cleaned)

def _digits(value):
    digits = re.sub(r"\D", "", str(value or ""))
    return int(digits) if digits else None


def _clean(value):
    return " ".join(str(value or "").split())


def _sync_user(user, record):
    changed = []
    name = _clean(record.name)
    if name:
        parts = name.split()
        first, last = parts[0], " ".join(parts[1:])
        if user.first_name != first or user.last_name != last:
            user.first_name = first
            user.last_name = last
            changed.append("name")
    email = _clean(getattr(record, "institute_email", ""))
    if email and user.email != email:
        user.email = email
        changed.append("email")
    if changed:
        user.save(update_fields=["first_name", "last_name", "email"])
    return changed


def _sync_extra_info(extra, record):
    changed = []
    sex = SEX_BY_GENDER.get(_clean(record.gender).upper())
    if sex and extra.sex != sex:
        extra.sex = sex
        changed.append("sex")
    dob = getattr(record, "date_of_birth", None)
    if dob and extra.date_of_birth != dob:
        extra.date_of_birth = dob
        changed.append("date_of_birth")
    address = _clean(getattr(record, "address", ""))
    if address and extra.address != address:
        extra.address = address
        changed.append("address")
    phone = _digits(getattr(record, "phone_number", None))
    if phone and extra.phone_no != phone:
        extra.phone_no = phone
        changed.append("phone_no")
    if changed:
        extra.save(update_fields=changed)
    return changed


def _sync_student(student, record):
    changed = []
    # narrowed to the account's vocabulary; the record keeps the full detail
    raw_category = _clean(record.category)
    category = reservation_category(raw_category)
    if category and student.category != category:
        student.category = category
        changed.append("category")

    is_ews = raw_category.upper() in EWS_CATEGORIES
    if raw_category and student.is_ews != is_ews:
        student.is_ews = is_ews
        changed.append("is_ews")

    pwd = _clean(getattr(record, "pwd", "")).upper()
    if pwd in ("YES", "NO"):
        is_pwd = pwd == "YES"
        if student.is_pwd != is_pwd:
            student.is_pwd = is_pwd
            changed.append("is_pwd")
    for field in ("father_name", "mother_name"):
        value = _clean(getattr(record, field, ""))
        if value and getattr(student, field) != value:
            setattr(student, field, value)
            changed.append(field)
    if changed:
        student.save(update_fields=changed)
    return changed


def sync_account_from_admission(record):
    """Copy an admission record onto its User, ExtraInfo and Student rows."""
    user = getattr(record, "user", None)
    if user is None:
        return []

    changed = list(_sync_user(user, record))

    extra = ExtraInfo.objects.filter(user=user).first()
    if extra is None:
        return changed

    changed += _sync_extra_info(extra, record)

    student = Student.objects.filter(id=extra).first()
    if student is not None:
        changed += _sync_student(student, record)
    return changed
