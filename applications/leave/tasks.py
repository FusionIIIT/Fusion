from __future__ import absolute_import, unicode_literals

import celery
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .models import LeaveMigration


@celery.task()
@transaction.atomic
def execute_leave_migrations():
    today = timezone.now().date()
    # today = timezone.now()
    migrations = LeaveMigration.objects.filter(Q(on_date__lte=today)).order_by('on_date')

    for migration in migrations:
        if migration.type_migration == 'transfer':
            to_update = migration.replacer
        else:
            to_update = migration.replacee
        rep_type = migration.replacement_type
        migration.replacee.holds_designations.filter(Q(designation__type=rep_type)) \
                                             .update(working=to_update)

    migrations.delete()


@celery.task()
def testing(a, b):
    return a+b
