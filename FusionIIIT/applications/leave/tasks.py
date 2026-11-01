from __future__ import absolute_import, unicode_literals

import celery
from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone

from decimal import Decimal

from django.contrib.auth.models import User

from .models import (ELMAccountTransaction, ELMActionLog, ELMPolicy,
                     ELMYearEndRun, ELMWorkflowTask, LeaveMigration,
                     LeaveType, LeavesCount)


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


@celery.task()
@transaction.atomic
def execute_elm_year_end(year=None):
    """Run once per leave year; retain an exception log for incomplete accounts."""
    from datetime import date
    from django.utils import timezone
    from .elm_services import CATEGORY_NAMES

    year = year or timezone.now().date().year
    run, created = ELMYearEndRun.objects.get_or_create(year=year)
    if not created and run.completed_at:
        return 'already-completed'
    exceptions = []
    users = User.objects.filter(extrainfo__user_type__in=('faculty', 'staff'), is_active=True)
    policies = list(ELMPolicy.objects.filter(published=True, effective_from__lte=date(year, 12, 31))
                    .filter(models.Q(effective_to__isnull=True) | models.Q(effective_to__gte=date(year, 12, 31))))
    policy_by_category = {p.category: p for p in policies}
    for user in users.iterator():
        for category, leave_name in CATEGORY_NAMES.items():
            policy = policy_by_category.get(category)
            if not policy or not getattr(policy, 'eligible_' + user.extrainfo.user_type):
                continue
            leave_type = LeaveType.objects.filter(name__iexact=leave_name).first()
            if not leave_type:
                exceptions.append('{}: no legacy LeaveType {}'.format(user.username, leave_name))
                continue
            current, _ = LeavesCount.objects.get_or_create(user=user, year=year,
                leave_type=leave_type, defaults={'remaining_leaves': policy.annual_entitlement})
            amount = Decimal(str(current.remaining_leaves))
            next_amount = amount
            reason = 'carry_forward'
            if category in ('CL', 'RH', 'SCL'):
                next_amount = Decimal(str(policy.annual_entitlement))
                reason = 'year_end_lapse'
            elif category == 'VL':
                next_amount = Decimal('0')
                reason = 'vl_year_end_conversion'
                if user.extrainfo.user_type == 'faculty' and amount:
                    earned_type = LeaveType.objects.filter(name__iexact='Earned').first()
                    if not earned_type:
                        exceptions.append('{}: no Earned leave type for VL conversion'.format(user.username))
                    else:
                        earned_policy = policy_by_category.get('EL')
                        earned, _ = LeavesCount.objects.get_or_create(user=user, year=year,
                            leave_type=earned_type, defaults={'remaining_leaves': earned_policy.annual_entitlement if earned_policy else 0})
                        converted = amount / Decimal('2')
                        earned.remaining_leaves = Decimal(str(earned.remaining_leaves)) + converted
                        earned.save(update_fields=('remaining_leaves',))
                        ELMAccountTransaction.objects.create(user=user, category='EL', year=year,
                            amount=converted, reason='vl_conversion', reference='2 VL to 1 EL')
            else:
                retained = amount if policy.carry_forward else Decimal('0')
                next_amount = retained + Decimal(str(policy.annual_entitlement))
            current.remaining_leaves = Decimal('0') if category in ('CL', 'RH', 'SCL', 'VL') else amount
            current.save(update_fields=('remaining_leaves',))
            if amount and category in ('CL', 'RH', 'SCL', 'VL'):
                ELMAccountTransaction.objects.create(user=user, category=category, year=year,
                    amount=-amount, reason=reason)
            next_year, _ = LeavesCount.objects.get_or_create(user=user, year=year + 1,
                leave_type=leave_type, defaults={'remaining_leaves': next_amount})
            if category in ('CL', 'RH', 'SCL', 'VL'):
                next_year.remaining_leaves = policy.annual_entitlement if category != 'VL' else policy.annual_entitlement
                next_year.save(update_fields=('remaining_leaves',))
            if category in ('EL', 'COL'):
                ELMAccountTransaction.objects.create(user=user, category=category, year=year + 1,
                    amount=policy.annual_entitlement, reason='annual_credit_and_carry_forward')
            elif category in ('CL', 'RH', 'SCL', 'VL'):
                ELMAccountTransaction.objects.create(user=user, category=category, year=year + 1,
                    amount=policy.annual_entitlement, reason='annual_entitlement_credit')
    run.exceptions = '\n'.join(exceptions)
    run.completed_at = timezone.now()
    run.save(update_fields=('exceptions', 'completed_at'))
    for message in exceptions:
        ELMActionLog.objects.create(action='year_end_exception', message=message)
    return 'completed-with-{}-exceptions'.format(len(exceptions))


@celery.task()
@transaction.atomic
def process_elm_slas():
    """Log and notify only for tasks that remain pending at configured thresholds."""
    from datetime import timedelta
    from django.utils import timezone
    from notifications.signals import notify
    from django.urls import reverse

    now = timezone.now()
    processed = 0
    pending = ELMWorkflowTask.objects.select_for_update().filter(status='pending').select_related('assignee', 'leave')
    for task in pending.iterator():
        age = now - task.created_at
        if task.reminder_after_hours and age >= timedelta(hours=task.reminder_after_hours) and not task.last_reminder_at:
            message = 'ELM task {} for leave {} remains pending.'.format(task.get_task_type_display(), task.leave_id)
            notify.send(sender=task.leave.applicant, recipient=task.assignee, verb=message,
                        url=reverse('leave:elm-dashboard'), module='Employee Leave Management')
            ELMActionLog.objects.create(task=task, action='reminder', message=message)
            task.last_reminder_at = now
            processed += 1
        if task.escalate_after_hours and age >= timedelta(hours=task.escalate_after_hours) and not task.last_escalation_at:
            message = 'ELM task {} for leave {} has exceeded its configured response threshold.'.format(task.get_task_type_display(), task.leave_id)
            category = task.leave.segments.select_related('leave_type').first()
            route = None
            if category and category.leave_type:
                from .elm_services import CATEGORY_NAMES, _route_configs
                code = next((c for c, n in CATEGORY_NAMES.items() if n.lower() == category.leave_type.name.lower()), None)
                if code:
                    unit = getattr(getattr(task.leave.applicant, 'extrainfo', None), 'department', None)
                    routes = _route_configs(code, unit, published=True,
                        is_unit_head=False, is_director_self_sanction=False,
                        is_resumption_verifier=False)
                    next_route = routes.filter(step__gt=task.route_step).order_by('step').first() if task.route_step else routes.order_by('step').first()
                    if next_route:
                        route = next_route.designation.designees.filter(working__is_active=True).first()
            recipient = route.working if route else task.assignee
            notify.send(sender=task.leave.applicant, recipient=recipient, verb=message,
                        url=reverse('leave:elm-dashboard'), module='Employee Leave Management')
            ELMActionLog.objects.create(task=task, action='escalation', message=message)
            task.last_escalation_at = now
            processed += 1
        task.save(update_fields=('last_reminder_at', 'last_escalation_at'))
    return processed
