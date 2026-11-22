"""Refuse any save or delete of a locked student's academic records.

Guarded: ``Student`` itself, ``Student_grades`` (linked by its ``roll_no``
text field), every model with a ForeignKey/OneToOneField to ``Student``, and
every model that reaches one of those through up to two more ForeignKeys (a
replacement through its registrations, a thesis grade through its thesis
registration). They are found by introspection, so a new model is covered
without a change here. The lock is read from the database on every call, so a Restore
in the System Administrator takes effect at once.

Bulk writes that skip model save (``QuerySet.update``, ``bulk_create``,
``bulk_update``) are not seen here; their callers check with
``student_status.assert_unlocked`` themselves.
"""
from typing import Dict, List, Tuple, Type

from django.apps import apps
from django.db.models import ForeignKey, Model, OneToOneField
from django.db.models.signals import pre_delete, pre_save

from applications.academic_information.student_status import assert_unlocked

# Certificates a locked student can still be issued (spec: alumni and
# withdrawn students keep Medium of Instruction and Pointer Conversion).
KEPT_CERTIFICATE_TYPES = frozenset({'medium_of_instruction', 'pointer_conv'})


def _student_model():
    return apps.get_model('academic_information', 'Student')


# Student -> registration -> replacement / evaluation -> score.
_LINKS = 3
_owners = None


def _owner_fields() -> Dict[Type[Model], List[Tuple[str, Type[Model]]]]:
    """For each guarded model, its (attname, target model) fields that lead
    to the student, built once after the apps are loaded."""
    global _owners
    if _owners is not None:
        return _owners
    student = _student_model()
    grades = apps.get_model('examination', 'Student_grades')
    owners = {student: [], grades: []}
    frontier = {student, grades}
    for _ in range(_LINKS):
        reached = set()
        for model in apps.get_models():
            for f in model._meta.concrete_fields:
                if (isinstance(f, (ForeignKey, OneToOneField))
                        and f.related_model in frontier and f.related_model is not model):
                    fields = owners.setdefault(model, [])
                    if (f.attname, f.related_model) not in fields:
                        fields.append((f.attname, f.related_model))
                        reached.add(model)
        frontier = reached - {student, grades}
    _owners = owners
    return owners


def guarded_models() -> List[Type[Model]]:
    return list(_owner_fields())


def rolls_for(instance) -> List[str]:
    """The roll numbers whose records ``instance`` belongs to."""
    model = type(instance)
    if model is _student_model():
        return [instance.pk] if instance.pk else []
    if model._meta.label == 'examination.Student_grades':
        return [(instance.roll_no or '').strip()]
    rolls = []
    for attname, target in _owner_fields().get(model, []):
        value = getattr(instance, attname)
        if value is None:
            continue
        if target is _student_model():
            rolls.append(value)
        else:
            parent = target._default_manager.filter(pk=value).first()
            if parent is not None:
                rolls.extend(rolls_for(parent))
    return rolls


def assert_record_unlocked(instance) -> None:
    """For a view about to bulk-update rows hanging off ``instance``: raise
    ``StudentLocked`` first if ``instance`` belongs to a locked student."""
    assert_unlocked(rolls_for(instance))


def _exempt(instance) -> bool:
    label = type(instance)._meta.label
    # The record of withdrawing and re-admitting is written for a student
    # who is (about to be) locked.
    if label == 'academic_information.StudentStatusHistory':
        return True
    return (label == 'academic_procedures.BonafideCertificate'
            and instance.certificate_type in KEPT_CERTIFICATE_TYPES)


def _stored_rolls(instance) -> List[str]:
    """For an update, the owners the row has in the database now, so a record
    cannot be moved off a locked student either."""
    model = type(instance)
    if instance._state.adding or instance.pk is None or model is _student_model():
        return []
    stored = model._default_manager.filter(pk=instance.pk).first()
    return rolls_for(stored) if stored is not None else []


def _refuse_save(sender, instance, raw=False, **kwargs):
    if raw or _exempt(instance):
        return
    assert_unlocked(rolls_for(instance) + _stored_rolls(instance))


def _refuse_delete(sender, instance, **kwargs):
    if _exempt(instance):
        return
    assert_unlocked(rolls_for(instance))


def connect_student_lock() -> None:
    for model in guarded_models():
        label = model._meta.label
        pre_save.connect(_refuse_save, sender=model,
                         dispatch_uid='student_lock_save:' + label)
        pre_delete.connect(_refuse_delete, sender=model,
                           dispatch_uid='student_lock_delete:' + label)
