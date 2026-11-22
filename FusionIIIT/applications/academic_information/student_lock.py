"""Refuse any save or delete of a locked student's academic records.

Every model with a ForeignKey/OneToOneField to ``Student`` is guarded (found
by introspection, so a new model is covered without a change here), plus
``Student`` itself and ``Student_grades``, which links by its ``roll_no``
text field. The lock is read from the database on every call, so a Restore
in the System Administrator takes effect at once.

Bulk writes that skip model save (``QuerySet.update``, ``bulk_create``,
``bulk_update``) are not seen here; their callers check with
``student_status.assert_unlocked`` themselves.
"""
from typing import List, Type

from django.apps import apps
from django.db.models import ForeignKey, Model, OneToOneField
from django.db.models.signals import pre_delete, pre_save

from applications.academic_information.student_status import assert_unlocked

# Certificates a locked student can still be issued (spec: alumni and
# withdrawn students keep Medium of Instruction and Pointer Conversion).
KEPT_CERTIFICATE_TYPES = frozenset({'medium_of_instruction', 'pointer_conv'})


def _student_model():
    return apps.get_model('academic_information', 'Student')


def _student_fields(model) -> List[str]:
    """attnames of the fields on ``model`` that point at ``Student``."""
    student = _student_model()
    return [
        f.attname for f in model._meta.concrete_fields
        if isinstance(f, (ForeignKey, OneToOneField)) and f.related_model is student
    ]


def guarded_models() -> List[Type[Model]]:
    student = _student_model()
    found = [student, apps.get_model('examination', 'Student_grades')]
    for model in apps.get_models():
        if model not in found and _student_fields(model):
            found.append(model)
    return found


def rolls_for(instance) -> List[str]:
    """The roll numbers whose records ``instance`` belongs to."""
    model = type(instance)
    if model is _student_model():
        return [instance.pk] if instance.pk else []
    if model._meta.label == 'examination.Student_grades':
        return [(instance.roll_no or '').strip()]
    return [getattr(instance, name) for name in _student_fields(model)
            if getattr(instance, name)]


def _exempt(instance) -> bool:
    return (type(instance)._meta.label == 'academic_procedures.BonafideCertificate'
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
