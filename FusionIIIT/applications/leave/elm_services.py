"""Domain operations for the ELM workflow built on Fusion's legacy leave records."""
import datetime
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.db import models, transaction
from django.utils import timezone

from .models import (ELMAccountTransaction, ELMCalendar, ELMCalendarDate,
                     ELMChangeRequest, ELMPolicy, ELMRouteConfiguration,
                     ELMWorkflowTask, Leave, LeaveSegment, LeavesCount,
                     ReplacementSegment)


CATEGORY_NAMES = {'CL': 'Casual', 'RH': 'Restricted', 'SCL': 'Special Casual',
                  'EL': 'Earned', 'COL': 'Commuted', 'VL': 'Vacation'}
CONTINUOUS = ('EL', 'COL', 'VL')


def effective_policy(category, day=None):
    day = day or timezone.now().date()
    return ELMPolicy.objects.filter(category=category, published=True,
                                    effective_from__lte=day).filter(
        models.Q(effective_to__isnull=True) | models.Q(effective_to__gte=day)
    ).order_by('-effective_from', '-created_at').first()


def _route_configs(category, unit, **filters):
    routes = ELMRouteConfiguration.objects.filter(category=category, **filters)
    if unit and routes.filter(unit=unit).exists():
        return routes.filter(unit=unit)
    return routes.filter(unit__isnull=True)


def _dates(start, end):
    current = start
    while current <= end:
        yield current
        current += datetime.timedelta(days=1)


def _published_calendar_date(day, date_type):
    calendar = ELMCalendar.objects.filter(year=day.year, published=True,
        effective_from__lte=day).filter(
            models.Q(effective_to__isnull=True) | models.Q(effective_to__gte=day)
        ).order_by('-effective_from', '-created_at').first()
    return bool(calendar and ELMCalendarDate.objects.filter(calendar=calendar,
        date=day, date_type=date_type).exists())


def charged_days(category, start, end, start_half=False, end_half=False):
    if start > end:
        raise ValidationError('The start date must not be after the end date.')
    if category != 'CL' and (start_half or end_half):
        raise ValidationError('Half-day requests are supported for CL only.')
    if start == end and start_half and end_half:
        raise ValidationError('Select only one half for a same-day CL request.')
    calendar_dates = {day for day in _dates(start, end)
                      if _published_calendar_date(day, 'closed')}
    closed = calendar_dates
    if category in CONTINUOUS:
        return Decimal((end - start).days + 1)
    days = Decimal(sum(1 for d in _dates(start, end) if d.weekday() < 5 and d not in closed))
    if start == end:
        if start_half != end_half:
            days -= Decimal('0.5')
    else:
        if start_half and start.weekday() < 5 and start not in closed:
            days -= Decimal('0.5')
        if end_half and end.weekday() < 5 and end not in closed:
            days -= Decimal('0.5')
    return max(days, Decimal('0'))


def _leave_type(category):
    from .models import LeaveType
    return LeaveType.objects.filter(name__iexact=CATEGORY_NAMES[category]).first()


def _balance(user, category, year):
    leave_type = _leave_type(category)
    if not leave_type:
        raise ValidationError('The legacy leave type for {} is not configured.'.format(category))
    try:
        return LeavesCount.objects.select_for_update().get(user=user, leave_type=leave_type, year=year)
    except LeavesCount.DoesNotExist:
        raise ValidationError('A {} balance record is not configured for {}.'.format(category, year))


def _active_overlap(user, start, end, category, start_half=False, end_half=False,
                    exclude=None, allow_split_cl=False):
    qs = LeaveSegment.objects.filter(leave__applicant=user,
                                     leave__status__in=('pending', 'accepted'),
                                     start_date__lte=end, end_date__gte=start)
    if exclude:
        qs = qs.exclude(leave_id=exclude)
    for other in qs.select_related('leave', 'leave_type'):
        same_cl_day_halves = (allow_split_cl and category == 'CL' and other.leave_type and
                              other.leave_type.name.lower() == 'casual' and
                              start == end == other.start_date == other.end_date and
                              start_half != other.start_half and end_half != other.end_half)
        if not same_cl_day_halves:
            return True
    return False


def _close_task_peers(task):
    if task.status == 'pending':
        return
    pending = ELMWorkflowTask.objects.filter(leave=task.leave, status='pending')
    if task.change_request_id:
        pending = pending.filter(change_request_id=task.change_request_id)
    else:
        pending = pending.filter(change_request__isnull=True)
    pending.filter(task_type=task.task_type, route_step=task.route_step) \
        .exclude(pk=task.pk).update(status='superseded', completed_at=timezone.now())
    workflow_finished = (task.change_request_id and task.change_request.status != 'pending') or \
        (not task.change_request_id and task.leave.elm_state in ('approved', 'rejected', 'withdrawn', 'cancelled', 'closed'))
    if workflow_finished:
        pending.exclude(pk=task.pk).update(status='superseded', completed_at=timezone.now())


def _route_tasks(leave, category, unit, change_request=None):
    first = _route_configs(category, unit, published=True, is_unit_head=False,
        is_director_self_sanction=False, is_resumption_verifier=False).order_by('step').first()
    if not first:
        raise ValidationError('No published approval route is configured for {}.'.format(category))
    _create_route_step(leave, unit, first, change_request)


def _create_route_step(leave, unit, step, change_request=None):
    holders = step.designation.designees.filter(working__is_active=True)
    if unit:
        scoped = holders.filter(working__extrainfo__department=unit)
        if scoped.exists():
            holders = scoped
    if not holders.exists():
        raise ValidationError('No active user holds configured designation {}.'.format(step.designation))
    for holder in holders:
        ELMWorkflowTask.objects.create(leave=leave,
            task_type='establishment' if step.is_establishment else 'sanction',
            change_request=change_request,
            route_step=step.step, assignee=holder.working,
            reminder_after_hours=step.reminder_after_hours,
            escalate_after_hours=step.escalate_after_hours)


@transaction.atomic
def submit_leave(user, category, start, end, purpose, start_half=False, end_half=False,
                 substitute=None, station_leave=False, station_details='', medical_evidence=None):
    category = category.upper()
    if category not in CATEGORY_NAMES:
        raise ValidationError('Select a supported leave category.')
    user_type = getattr(getattr(user, 'extrainfo', None), 'user_type', None)
    if user_type not in ('faculty', 'staff'):
        raise ValidationError('ELM is available to faculty and staff employees.')
    policy = effective_policy(category, start)
    if not policy or not getattr(policy, 'eligible_' + user_type):
        raise ValidationError('No effective published policy makes this employee eligible for {}.'.format(category))
    if category == 'VL':
        vacation = sum(1 for day in _dates(start, end) if _published_calendar_date(day, 'vacation'))
        if vacation != (end - start).days + 1:
            raise ValidationError('Vacation Leave must fall entirely within a published vacation period.')
    if category == 'RH' and (start != end or not _published_calendar_date(start, 'restricted')):
        raise ValidationError('The requested RH date is not in the published RH calendar.')
    if _active_overlap(user, start, end, category, start_half, end_half, allow_split_cl=True):
        raise ValidationError('The requested period overlaps active leave.')
    amount = charged_days(category, start, end, start_half, end_half)
    balance = _balance(user, category, start.year)
    if Decimal(str(balance.remaining_leaves)) < amount:
        raise ValidationError('Insufficient {} balance.'.format(category))
    if policy.requires_medical_evidence and not medical_evidence:
        raise ValidationError('Supporting medical evidence is required by the effective policy.')
    if policy.requires_substitute or substitute:
        if not substitute or substitute == user or not substitute.is_active:
            raise ValidationError('Choose an eligible substitute other than yourself.')
        if getattr(getattr(substitute, 'extrainfo', None), 'user_type', None) not in ('faculty', 'staff'):
            raise ValidationError('The substitute must be an employee.')
        if _active_overlap(substitute, start, end, category):
            raise ValidationError('The selected substitute has overlapping active leave.')

    leave = Leave.objects.create(applicant=user, purpose=purpose, elm_state='awaiting_substitute' if (policy.requires_substitute or substitute) else 'awaiting_unit_head',
                                 station_leave=station_leave, station_details=station_details)
    leave_type = _leave_type(category)
    segment = LeaveSegment.objects.create(leave=leave, leave_type=leave_type,
        start_date=start, end_date=end, start_half=start_half, end_half=end_half,
        document=medical_evidence)
    if substitute:
        ReplacementSegment.objects.create(leave=leave, replacer=substitute,
            replacement_type='academic', start_date=start, end_date=end)
        ELMWorkflowTask.objects.create(leave=leave, task_type='substitute', assignee=substitute)
    else:
        _start_approval(leave, user)
    ELMAccountTransaction.objects.create(user=user, category=category, year=start.year,
        amount=-amount, reason='requested', leave=leave)
    balance.remaining_leaves = Decimal(str(balance.remaining_leaves)) - amount
    balance.save(update_fields=('remaining_leaves',))
    from notification.views import leave_module_notif
    recipients = list(ELMWorkflowTask.objects.filter(leave=leave, status='pending')
                      .values_list('assignee', flat=True))
    leave_module_notif(user, user, 'leave_applied')
    if recipients:
        leave_module_notif(user, list(User.objects.filter(pk__in=recipients)),
                           'leave_request', date=user.get_full_name() or user.username)
    return leave


def _make_unit_head_task(leave, user, change_request=None, task_type='unit_head'):
    """Resolve Unit Head through an explicit published route mapping."""
    unit = getattr(getattr(user, 'extrainfo', None), 'department', None)
    category = _category_for(leave)
    route = _route_configs(category, unit, published=True, is_unit_head=True).order_by('step').first()
    if not route:
        raise ValidationError('No published Unit Head mapping exists for this unit and category.')
    holders = route.designation.designees.filter(working__is_active=True)
    if unit:
        scoped = holders.filter(working__extrainfo__department=unit)
        if scoped.exists():
            holders = scoped
    if not holders.exists():
        raise ValidationError('No active user holds the configured Unit Head designation.')
    for holder in holders:
        ELMWorkflowTask.objects.create(leave=leave, task_type=task_type,
            change_request=change_request, assignee=holder.working,
            reminder_after_hours=route.reminder_after_hours,
            escalate_after_hours=route.escalate_after_hours)


def _start_approval(leave, user):
    category = _category_for(leave)
    unit = getattr(getattr(user, 'extrainfo', None), 'department', None)
    director_route = _route_configs(category, unit, published=True,
        is_director_self_sanction=True).order_by('step').first()
    if director_route and director_route.designation.designees.filter(working=user).exists():
        ELMWorkflowTask.objects.create(leave=leave, task_type='sanction',
            route_step=director_route.step, assignee=user,
            reminder_after_hours=director_route.reminder_after_hours,
            escalate_after_hours=director_route.escalate_after_hours)
        leave.elm_state = 'awaiting_director_self_sanction'
        leave.save(update_fields=('elm_state',))
    else:
        _make_unit_head_task(leave, user)


def _make_resumption_task(leave, user, change):
    category = _category_for(leave)
    unit = getattr(getattr(user, 'extrainfo', None), 'department', None)
    route = _route_configs(category, unit, published=True,
        is_resumption_verifier=True).order_by('step').first()
    if not route:
        raise ValidationError('No published resumption-verifier route exists for this unit and category.')
    holders = route.designation.designees.filter(working__is_active=True)
    if unit:
        scoped = holders.filter(working__extrainfo__department=unit)
        if scoped.exists():
            holders = scoped
    if not holders.exists():
        raise ValidationError('No active user holds the configured resumption-verifier designation.')
    for holder in holders:
        ELMWorkflowTask.objects.create(leave=leave, change_request=change,
            task_type='resumption', route_step=route.step, assignee=holder.working,
            reminder_after_hours=route.reminder_after_hours,
            escalate_after_hours=route.escalate_after_hours)


@transaction.atomic
def respond_to_task(task, actor, decision, remark=''):
    task = ELMWorkflowTask.objects.select_for_update().select_related('leave').get(pk=task.pk)
    if task.assignee_id != actor.id or task.status != 'pending':
        raise ValidationError('This workflow task is not actionable by this user.')
    leave = task.leave
    if task.change_request_id:
        return _respond_to_change(task, actor, decision, remark)
    if leave.elm_state in ('withdrawn', 'rejected', 'cancelled', 'closed'):
        raise ValidationError('This request is no longer actionable.')
    now = timezone.now()
    task.remark = remark
    task.completed_at = now
    if task.task_type == 'substitute':
        if decision not in ('accept', 'decline'):
            raise ValidationError('Substitute decision must be accept or decline.')
        task.status = 'accepted' if decision == 'accept' else 'declined'
        leave.elm_state = 'awaiting_unit_head' if decision == 'accept' else 'substitute_declined'
        if decision == 'accept':
            _start_approval(leave, leave.applicant)
    elif task.task_type == 'unit_head':
        if decision not in ('recommend', 'not_recommend', 'approve', 'reject'):
            raise ValidationError('Unsupported Unit Head decision.')
        higher = any(s.leave_type and s.leave_type.name.lower() not in ('casual', 'restricted') for s in leave.segments.all())
        if higher and decision in ('recommend', 'not_recommend'):
            task.status = 'recommended' if decision == 'recommend' else 'not_recommended'
            leave.elm_state = 'awaiting_final_sanction'
            unit = getattr(getattr(leave.applicant, 'extrainfo', None), 'department', None)
            category = next((code for code, name in CATEGORY_NAMES.items()
                             if any(s.leave_type and s.leave_type.name.lower() == name.lower() for s in leave.segments.all())), None)
            if category:
                _route_tasks(leave, category, unit)
        elif not higher and decision in ('approve', 'reject'):
            task.status = 'approved' if decision == 'approve' else 'rejected'
            leave.status = 'accepted' if decision == 'approve' else 'rejected'
            leave.elm_state = 'approved' if decision == 'approve' else 'rejected'
            if decision == 'reject':
                _restore_leave_balance(leave, 'rejection_restore')
        else:
            raise ValidationError('Unit Head approval/rejection is final only for CL and RH; higher categories require a recommendation.')
    elif task.task_type in ('establishment', 'sanction'):
        if decision not in ('forward', 'approve', 'reject'):
            raise ValidationError('Unsupported sanctioning decision.')
        task.status = 'approved' if decision in ('forward', 'approve') else 'rejected'
        if decision == 'forward':
            category = _category_for(leave)
            unit = getattr(getattr(leave.applicant, 'extrainfo', None), 'department', None)
            next_step = _route_configs(category, unit, published=True,
                is_unit_head=False, is_director_self_sanction=False,
                is_resumption_verifier=False, step__gt=task.route_step).order_by('step').first()
            if not next_step:
                raise ValidationError('No later approval step is configured for this route.')
            _create_route_step(leave, unit, next_step)
            leave.elm_state = 'awaiting_establishment' if next_step.is_establishment else 'awaiting_final_sanction'
        else:
            leave.status = 'accepted' if decision == 'approve' else 'rejected'
            leave.elm_state = 'approved' if decision == 'approve' else 'rejected'
            if decision == 'reject':
                _restore_leave_balance(leave, 'rejection_restore')
    else:
        raise ValidationError('Task type requires its dedicated lifecycle operation.')
    task.save()
    leave.save()
    _close_task_peers(task)
    if task.task_type == 'substitute':
        from notification.views import leave_module_notif
        leave_module_notif(actor, leave.applicant,
                           'request_accepted' if task.status == 'accepted' else 'request_declined')
    if leave.elm_state in ('approved', 'rejected'):
        from notification.views import leave_module_notif
        leave_module_notif(actor, leave.applicant,
                           'leave_accepted' if leave.elm_state == 'approved' else 'leave_rejected')
    return leave


@transaction.atomic
def withdraw_pending(leave, actor):
    leave = Leave.objects.select_for_update().get(pk=leave.pk, applicant=actor)
    if leave.elm_state not in ('awaiting_substitute', 'substitute_declined',
            'awaiting_unit_head', 'awaiting_establishment',
            'awaiting_final_sanction', 'awaiting_director_self_sanction'):
        raise ValidationError('Only a pending request can be withdrawn.')
    leave.elm_state = 'withdrawn'
    leave.status = 'rejected'
    leave.save()
    recipients = list(ELMWorkflowTask.objects.filter(leave=leave, status='pending')
                      .values_list('assignee', flat=True))
    ELMWorkflowTask.objects.filter(leave=leave, status='pending').update(status='superseded', completed_at=timezone.now())
    _restore_leave_balance(leave, 'withdrawal_restore')
    if recipients:
        from notification.views import leave_module_notif
        leave_module_notif(actor, list(User.objects.filter(pk__in=recipients)),
                           'leave_withdrawn', date=actor.get_full_name() or actor.username)
    return leave


@transaction.atomic
def nominate_new_substitute(leave, actor, substitute):
    leave = Leave.objects.select_for_update().get(pk=leave.pk, applicant=actor)
    if leave.elm_state != 'substitute_declined':
        raise ValidationError('A replacement may be nominated only after the current substitute declines.')
    if not substitute or substitute == actor or not substitute.is_active or getattr(getattr(substitute, 'extrainfo', None), 'user_type', None) not in ('faculty', 'staff'):
        raise ValidationError('Choose another active faculty or staff employee.')
    segment = leave.segments.order_by('start_date').first()
    if not segment or _active_overlap(substitute, segment.start_date, segment.end_date,
                                      _category_for(leave)):
        raise ValidationError('The selected employee has overlapping active leave.')
    ELMWorkflowTask.objects.filter(leave=leave, task_type='substitute', status='pending') \
        .update(status='superseded', completed_at=timezone.now())
    ReplacementSegment.objects.create(leave=leave, replacer=substitute,
        replacement_type='academic', start_date=segment.start_date, end_date=segment.end_date)
    ELMWorkflowTask.objects.create(leave=leave, task_type='substitute', assignee=substitute)
    leave.elm_state = 'awaiting_substitute'
    leave.save(update_fields=('elm_state',))
    return leave


@transaction.atomic
def modify_pending(leave, actor, category, start, end, purpose, start_half=False,
                   end_half=False, substitute=None, station_leave=False,
                   station_details='', medical_evidence=None):
    leave = Leave.objects.select_for_update().get(pk=leave.pk, applicant=actor)
    if leave.elm_state not in ('awaiting_substitute', 'substitute_declined',
                               'awaiting_unit_head', 'awaiting_establishment',
                               'awaiting_final_sanction', 'awaiting_director_self_sanction'):
        raise ValidationError('This request is not in a modifiable pending state.')
    old_segment = leave.segments.select_related('leave_type').first()
    if not old_segment:
        raise ValidationError('The existing leave period cannot be resolved.')
    category = category.upper()
    if category not in CATEGORY_NAMES:
        raise ValidationError('Select a supported leave category.')
    policy = effective_policy(category, start)
    user_type = actor.extrainfo.user_type
    if not policy or not getattr(policy, 'eligible_' + user_type):
        raise ValidationError('No effective published policy makes this employee eligible for {}.'.format(category))
    if _active_overlap(actor, start, end, category, start_half, end_half,
                       exclude=leave.pk, allow_split_cl=True):
        raise ValidationError('The revised period overlaps active leave.')
    if category == 'RH' and (start != end or not _published_calendar_date(start, 'restricted')):
        raise ValidationError('The revised RH date must match the published RH calendar.')
    if category == 'VL' and sum(1 for day in _dates(start, end) if _published_calendar_date(day, 'vacation')) != (end - start).days + 1:
        raise ValidationError('Vacation Leave must fall entirely within a published vacation period.')
    if policy.requires_medical_evidence and not medical_evidence and not old_segment.document:
        raise ValidationError('Supporting medical evidence is required by the effective policy.')
    if policy.requires_substitute or substitute:
        if not substitute or substitute == actor or not substitute.is_active:
            raise ValidationError('Choose an eligible substitute other than yourself.')
        if getattr(getattr(substitute, 'extrainfo', None), 'user_type', None) not in ('faculty', 'staff'):
            raise ValidationError('The substitute must be an employee.')
        if _active_overlap(substitute, start, end, category):
            raise ValidationError('The selected substitute has overlapping active leave.')
    old_category = _category_for(leave)
    old_amount = charged_days(old_category, old_segment.start_date, old_segment.end_date,
                              old_segment.start_half, old_segment.end_half)
    old_balance = _balance(actor, old_category, old_segment.start_date.year)
    old_balance.remaining_leaves = Decimal(str(old_balance.remaining_leaves)) + old_amount
    old_balance.save(update_fields=('remaining_leaves',))
    new_amount = charged_days(category, start, end, start_half, end_half)
    new_balance = _balance(actor, category, start.year)
    if Decimal(str(new_balance.remaining_leaves)) < new_amount:
        raise ValidationError('Insufficient balance for the revised request.')
    new_balance.remaining_leaves = Decimal(str(new_balance.remaining_leaves)) - new_amount
    new_balance.save(update_fields=('remaining_leaves',))
    ELMAccountTransaction.objects.create(user=actor, category=old_category,
        year=old_segment.start_date.year, amount=old_amount, reason='modification_restore', leave=leave)
    ELMAccountTransaction.objects.create(user=actor, category=category,
        year=start.year, amount=-new_amount, reason='modified_request', leave=leave)
    ELMWorkflowTask.objects.filter(leave=leave, status='pending').update(
        status='superseded', completed_at=timezone.now())
    leave.purpose = purpose
    leave.station_leave = station_leave
    leave.station_details = station_details
    leave.status = 'pending'
    leave.elm_state = 'awaiting_substitute' if (policy.requires_substitute or substitute) else 'awaiting_unit_head'
    leave.save()
    old_segment.leave_type = _leave_type(category)
    old_segment.start_date, old_segment.end_date = start, end
    old_segment.start_half, old_segment.end_half = start_half, end_half
    if medical_evidence:
        old_segment.document = medical_evidence
    old_segment.save()
    leave.replace_segments.all().delete()
    if substitute:
        ReplacementSegment.objects.create(leave=leave, replacer=substitute,
            replacement_type='academic', start_date=start, end_date=end)
        ELMWorkflowTask.objects.create(leave=leave, task_type='substitute', assignee=substitute)
    else:
        _start_approval(leave, actor)
    return leave


def _category_for(leave):
    segment = leave.segments.select_related('leave_type').first()
    if not segment or not segment.leave_type:
        raise ValidationError('The leave category cannot be resolved.')
    return next((code for code, name in CATEGORY_NAMES.items() if name.lower() == segment.leave_type.name.lower()), 'CL')


def _restore_leave_balance(leave, reason, amount=None):
    segment = leave.segments.select_related('leave_type').first()
    if not segment:
        raise ValidationError('The leave period cannot be resolved.')
    category = _category_for(leave)
    if amount is None:
        amount = charged_days(category, segment.start_date, segment.end_date,
                             segment.start_half, segment.end_half)
    balance = _balance(leave.applicant, category, segment.start_date.year)
    balance.remaining_leaves = Decimal(str(balance.remaining_leaves)) + amount
    balance.save(update_fields=('remaining_leaves',))
    ELMAccountTransaction.objects.create(user=leave.applicant, category=category,
        year=segment.start_date.year, amount=amount, reason=reason, leave=leave)


def submit_change(leave, actor, change_type, **values):
    if leave.applicant_id != actor.id:
        raise ValidationError('Only the applicant can change this leave.')
    now = timezone.now().date()
    category = _category_for(leave)
    substitute = values.pop('substitute', None)
    extension_policy = None
    extension_amount = Decimal('0')
    if change_type not in ('cancel', 'extension', 'resumption'):
        raise ValidationError('Select a supported lifecycle request.')
    if change_type == 'cancel':
        if leave.elm_state != 'approved' or any(s.start_date <= now for s in leave.segments.all()):
            raise ValidationError('Approved leave can only be cancelled before it starts.')
    elif change_type in ('extension', 'resumption') and category not in CONTINUOUS:
        raise ValidationError('Extension and resumption are supported for EL, COL and VL only.')
    elif change_type == 'extension':
        segment = leave.segments.order_by('-end_date').first()
        if not segment or not (segment.start_date <= now <= segment.end_date):
            raise ValidationError('An extension requires leave that is currently ongoing.')
        values.setdefault('start_date', segment.end_date + datetime.timedelta(days=1))
        if values.get('end_date') and values['end_date'] < values['start_date']:
            raise ValidationError('The extension end date must follow its start date.')
        extension_policy = effective_policy(category, values['start_date'])
        if not extension_policy or not getattr(extension_policy, 'eligible_' + actor.extrainfo.user_type):
            raise ValidationError('No effective published policy exists for this extension.')
        if extension_policy.requires_substitute:
            if not substitute or substitute == actor or not substitute.is_active or getattr(getattr(substitute, 'extrainfo', None), 'user_type', None) not in ('faculty', 'staff'):
                raise ValidationError('Choose an eligible substitute for this extension.')
            if _active_overlap(substitute, values['start_date'], values.get('end_date') or values['start_date'], category):
                raise ValidationError('The selected substitute has overlapping active leave.')
        if _active_overlap(actor, values['start_date'], values.get('end_date') or values['start_date'], category,
                           exclude=leave.pk):
            raise ValidationError('The extension overlaps another active leave request.')
        amount = charged_days(category, values['start_date'], values.get('end_date') or values['start_date'])
        extension_amount = amount
        balance = _balance(actor, category, values['start_date'].year)
        if Decimal(str(balance.remaining_leaves)) < amount:
            raise ValidationError('Insufficient balance for the extension.')
        extension_end = values.get('end_date') or values['start_date']
        if category == 'VL' and sum(1 for day in _dates(values['start_date'], extension_end)
                                    if _published_calendar_date(day, 'vacation')) != (extension_end - values['start_date']).days + 1:
            raise ValidationError('The Vacation Leave extension must fall within the published vacation calendar.')
        if extension_policy.requires_medical_evidence and not values.get('medical_evidence'):
            raise ValidationError('Supporting medical evidence is required for this extension.')
    elif change_type == 'resumption':
        segment = leave.segments.order_by('-end_date').first()
        actual_date = values.get('actual_return_date')
        if leave.elm_state != 'approved' or not segment or not actual_date or actual_date <= segment.start_date or actual_date > segment.end_date + datetime.timedelta(days=1):
            raise ValidationError('Resumption must be submitted for an approved ongoing leave and a date in its approved period.')
    change = ELMChangeRequest.objects.create(leave=leave, requested_by=actor,
        change_type=change_type, **values)
    unit = getattr(getattr(leave.applicant, 'extrainfo', None), 'department', None)
    if change_type == 'cancel':
        leave.elm_state = 'cancellation_pending'
        leave.save(update_fields=('elm_state',))
        _make_unit_head_task(leave, actor, change)
    elif change_type == 'extension':
        balance = _balance(actor, category, change.start_date.year)
        balance.remaining_leaves = Decimal(str(balance.remaining_leaves)) - extension_amount
        balance.save(update_fields=('remaining_leaves',))
        ELMAccountTransaction.objects.create(user=actor, category=category,
            year=change.start_date.year, amount=-extension_amount,
            reason='extension_reserved', leave=leave)
        leave.elm_state = 'extension_pending'
        leave.save(update_fields=('elm_state',))
        if extension_policy and extension_policy.requires_substitute:
            ReplacementSegment.objects.create(leave=leave, replacer=substitute,
                replacement_type='academic', start_date=change.start_date, end_date=change.end_date)
            ELMWorkflowTask.objects.create(leave=leave, change_request=change,
                task_type='substitute', assignee=substitute)
            leave.elm_state = 'extension_awaiting_substitute'
            leave.save(update_fields=('elm_state',))
        else:
            _make_unit_head_task(leave, actor, change)
    elif change_type == 'resumption':
        leave.elm_state = 'awaiting_resumption_verification'
        leave.save(update_fields=('elm_state',))
        _make_resumption_task(leave, actor, change)
    return change


@transaction.atomic
def record_offline_leave(applicant, actor, category, start, end, purpose, reference,
                         start_half=False, end_half=False, station_leave=False,
                         station_details='', medical_evidence=None):
    if not reference.strip():
        raise ValidationError('Enter the offline sanction reference.')
    if getattr(getattr(applicant, 'extrainfo', None), 'user_type', None) not in ('faculty', 'staff'):
        raise ValidationError('Offline ELM entries are limited to faculty and staff.')
    category = category.upper()
    policy = effective_policy(category, start)
    if not policy or not getattr(policy, 'eligible_' + applicant.extrainfo.user_type):
        raise ValidationError('No effective policy makes the employee eligible for this category.')
    if _active_overlap(applicant, start, end, category, start_half, end_half, allow_split_cl=True):
        raise ValidationError('The offline entry overlaps another active leave.')
    if policy.requires_medical_evidence and not medical_evidence:
        raise ValidationError('Supporting medical evidence is required by policy.')
    amount = charged_days(category, start, end, start_half, end_half)
    balance = _balance(applicant, category, start.year)
    if Decimal(str(balance.remaining_leaves)) < amount:
        raise ValidationError('Insufficient leave balance for the offline entry.')
    leave = Leave.objects.create(applicant=applicant, purpose=purpose,
        status='accepted', elm_state='approved', station_leave=station_leave,
        station_details=station_details, extra_info='Offline sanction: {}'.format(reference))
    LeaveSegment.objects.create(leave=leave, leave_type=_leave_type(category),
        start_date=start, end_date=end, start_half=start_half, end_half=end_half,
        document=medical_evidence)
    balance.remaining_leaves = Decimal(str(balance.remaining_leaves)) - amount
    balance.save(update_fields=('remaining_leaves',))
    ELMAccountTransaction.objects.create(user=applicant, category=category, year=start.year,
        amount=-amount, reason='offline_sanction_sync', leave=leave, reference=reference)
    return leave


@transaction.atomic
def _respond_to_change(task, actor, decision, remark=''):
    change = task.change_request
    leave = task.leave
    if change.status != 'pending':
        raise ValidationError('This lifecycle request has already been completed.')
    task.completed_at = timezone.now()
    task.remark = remark
    if task.task_type == 'substitute':
        if decision not in ('accept', 'decline'):
            raise ValidationError('Substitute decision must be accept or decline.')
        task.status = 'accepted' if decision == 'accept' else 'declined'
        if decision == 'accept':
            _make_unit_head_task(leave, change.requested_by, change)
            leave.elm_state = 'extension_pending'
        else:
            change.status = 'rejected'
            change.completed_at = timezone.now()
            leave.elm_state = 'approved'
        task.save()
        change.save()
        leave.save(update_fields=('elm_state',))
        _close_task_peers(task)
        return leave
    if change.change_type == 'resumption':
        if decision != 'verify':
            raise ValidationError('The configured verifier must verify the return.')
        segment = leave.segments.select_related('leave_type').first()
        if not segment or not change.actual_return_date:
            raise ValidationError('Resumption details are incomplete.')
        if change.actual_return_date <= segment.start_date or change.actual_return_date > segment.end_date + datetime.timedelta(days=1):
            raise ValidationError('Actual return date must follow the leave start and be no later than the day after its approved end.')
        unused = Decimal('0')
        if change.actual_return_date <= segment.end_date:
            unused = charged_days(_category_for(leave), change.actual_return_date,
                                  segment.end_date, False, segment.end_half)
        if unused > 0:
            _restore_leave_balance(leave, 'early_resumption_restore', unused)
        segment.end_date = change.actual_return_date - datetime.timedelta(days=1)
        segment.save(update_fields=('end_date',))
        leave.elm_state = 'closed'
        change.status = 'verified'
        task.status = 'approved'
    else:
        if task.task_type in ('unit_head', 'resumption'):
            if task.task_type == 'unit_head' and decision not in ('recommend', 'not_recommend', 'approve', 'reject'):
                raise ValidationError('Unsupported Unit Head decision.')
            higher = _category_for(leave) not in ('CL', 'RH')
            if task.task_type == 'unit_head' and change.change_type in ('extension', 'cancel') and higher and decision in ('recommend', 'not_recommend'):
                task.status = 'recommended' if decision == 'recommend' else 'not_recommended'
                task.save()
                _close_task_peers(task)
                _route_tasks(leave, _category_for(leave), getattr(getattr(actor, 'extrainfo', None), 'department', None), change)
                leave.elm_state = 'extension_awaiting_sanction' if change.change_type == 'extension' else 'cancellation_pending'
                leave.save(update_fields=('elm_state',))
                return leave
            if task.task_type == 'unit_head' and change.change_type in ('extension', 'cancel') and higher:
                raise ValidationError('The Unit Head may recommend or not recommend, but cannot finally decide this category.')
            if decision not in ('approve', 'reject'):
                raise ValidationError('Decision must approve or reject this lifecycle request.')
        elif task.task_type in ('establishment', 'sanction'):
            if decision == 'forward':
                category = _category_for(leave)
                unit = getattr(getattr(leave.applicant, 'extrainfo', None), 'department', None)
                next_step = _route_configs(category, unit, published=True,
                    is_unit_head=False, is_director_self_sanction=False,
                    is_resumption_verifier=False, step__gt=task.route_step).order_by('step').first()
                if not next_step:
                    raise ValidationError('No later approval step is configured for this route.')
                _create_route_step(leave, unit, next_step, change)
                task.status = 'approved'
                task.save()
                _close_task_peers(task)
                return leave
            if decision not in ('approve', 'reject'):
                raise ValidationError('Decision must forward, approve, or reject.')
        else:
            raise ValidationError('This task cannot decide the lifecycle request.')
        task.status = 'approved' if decision == 'approve' else 'rejected'
        if decision == 'approve':
            change.status = 'approved'
            if change.change_type == 'cancel':
                _restore_leave_balance(leave, 'cancellation_restore')
                leave.status = 'rejected'
                leave.elm_state = 'cancelled'
            else:
                amount = charged_days(_category_for(leave), change.start_date, change.end_date)
                balance = _balance(leave.applicant, _category_for(leave), change.start_date.year)
                balance.remaining_leaves = Decimal(str(balance.remaining_leaves)) - amount
                balance.save(update_fields=('remaining_leaves',))
                LeaveSegment.objects.create(leave=leave, leave_type=_leave_type(_category_for(leave)),
                    start_date=change.start_date, end_date=change.end_date)
                leave.elm_state = 'approved'
        else:
            change.status = 'rejected'
            leave.elm_state = 'approved'
            if change.change_type == 'extension':
                amount = charged_days(_category_for(leave), change.start_date, change.end_date)
                balance = _balance(leave.applicant, _category_for(leave), change.start_date.year)
                balance.remaining_leaves = Decimal(str(balance.remaining_leaves)) + amount
                balance.save(update_fields=('remaining_leaves',))
                ELMAccountTransaction.objects.create(user=leave.applicant, category=_category_for(leave),
                    year=change.start_date.year, amount=amount,
                    reason='extension_rejected_restore', leave=leave)
        change.completed_at = timezone.now()
    task.save()
    leave.save()
    change.save()
    _close_task_peers(task)
    return leave
