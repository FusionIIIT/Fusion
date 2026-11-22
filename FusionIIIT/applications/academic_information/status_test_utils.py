"""Shared fixtures for the student-status tests (not a test module itself)."""
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.authtoken.models import Token

from applications.academic_information.models import Student
from applications.globals.models import Designation, ExtraInfo, HoldsDesignation
from applications.programme_curriculum.models import Batch, Curriculum, Discipline, Programme


def make_batch(year=2021, acronym='CSE'):
    programme, _ = Programme.objects.get_or_create(
        category='UG', name='B.Tech', defaults={'programme_begin_year': year})
    curriculum, _ = Curriculum.objects.get_or_create(
        programme=programme, name='B.Tech %s' % year, defaults={'no_of_semester': 8})
    discipline, _ = Discipline.objects.get_or_create(
        acronym=acronym, defaults={'name': 'Discipline %s' % acronym})
    batch, _ = Batch.objects.get_or_create(
        name='B.Tech', year=year, discipline=discipline, curriculum=curriculum)
    return batch


def make_student(roll, status='PRESENT', batch=None, semester=8):
    batch = batch or make_batch()
    user = User.objects.create_user(username=roll, password='x')
    extra = ExtraInfo.objects.create(id=roll, user=user, user_type='student',
                                     user_status=status, sex='M')
    return Student.objects.create(id=extra, programme='B.Tech', batch=batch.year,
                                  batch_id=batch, category='GEN',
                                  curr_semester_no=semester)


def make_staff(username='status_admin', designation='acadadmin'):
    user = User.objects.create_user(username=username, password='x')
    ExtraInfo.objects.create(id=username, user=user, user_type='staff')
    HoldsDesignation.objects.create(
        user=user, working=user, held_at=timezone.now(),
        designation=Designation.objects.get_or_create(name=designation)[0])
    return user


def token_for(user):
    return Token.objects.get_or_create(user=user)[0].key


def set_status(student, status):
    """What sysadmin does: write ExtraInfo.user_status directly."""
    type(student.id).objects.filter(pk=student.id_id).update(user_status=status)
