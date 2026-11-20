"""Which discipline an HOD role belongs to.

An HOD role is a designation named "HOD (<discipline>)", and the discipline may
be written by its short name or its full name: "HOD (Des.)" and "HOD (Design)"
are both the HOD of Design, "HOD (LA)" and "HOD (Liberal Arts)" both of Liberal
Arts. Every check that ties an HOD to a discipline goes through here, so both
spellings work everywhere.
"""
import re

from applications.globals.models import Designation, HoldsDesignation

from .models import Discipline

_HOD_ROLE = re.compile(r'^\s*hod\s*\((?P<label>[^()]*)\)\s*$', re.IGNORECASE)


def discipline_key(text):
    """'Des.', 'des' and 'DES' all name the same discipline."""
    return re.sub(r'[^a-z0-9]', '', (text or '').lower())


def hod_role_label(designation_name):
    """'HOD (Design)' -> 'Design'; None for a designation that is not an HOD role."""
    match = _HOD_ROLE.match(designation_name or '')
    return match.group('label').strip() if match else None


def _acronyms_by_key():
    """Each discipline's short name, keyed by its short name and by its full name."""
    by_key = {}
    for name, acronym in Discipline.objects.values_list('name', 'acronym'):
        for text in (acronym, name):
            key = discipline_key(text)
            if key:
                by_key.setdefault(key, acronym)
    return by_key


def _discipline_acronym(label, by_key):
    """The short name of the discipline `label` names, or `label` itself if none matches."""
    return by_key.get(discipline_key(label), label)


def hod_disciplines_of(user):
    """Short names of the disciplines `user` is acting HOD of, each listed once."""
    by_key = _acronyms_by_key()
    acronyms = []
    names = HoldsDesignation.objects.filter(
        working=user, designation__name__istartswith='hod',
    ).values_list('designation__name', flat=True)
    for name in names:
        label = hod_role_label(name)
        if label is None:
            continue
        acronym = _discipline_acronym(label, by_key)
        if acronym not in acronyms:
            acronyms.append(acronym)
    return acronyms


def hod_designation_names(discipline):
    """Every existing designation name meaning "HOD of `discipline`".

    `discipline` may be a short name ("Des."), a full name ("Design") or a
    department name that matches one of them.
    """
    if not discipline:
        return []
    by_key = _acronyms_by_key()
    target = discipline_key(_discipline_acronym(discipline, by_key))
    names = []
    for name in Designation.objects.filter(name__istartswith='hod').values_list('name', flat=True):
        label = hod_role_label(name)
        if label is not None and discipline_key(_discipline_acronym(label, by_key)) == target:
            names.append(name)
    return names
