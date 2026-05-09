from .models import LegacyFile as File, LegacyTracking as Tracking, FileType, File as NewFile, FileMovement, FileWorkflow, DraftFile, FileVersion, FTAccessPolicy
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation, DepartmentInfo
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import IntegrityError, transaction
from django.db.models import Q, Count
from django.conf import settings
import datetime
import logging


logger = logging.getLogger(__name__)


# Centralized status state machine for File lifecycle.
ALLOWED_STATUS_TRANSITIONS = {
    'CREATED': {'PENDING', 'SUBMITTED'},
    'PENDING': {'FORWARDED', 'APPROVED', 'REJECTED', 'IN_PROGRESS'},
    'SUBMITTED': {'FORWARDED', 'APPROVED', 'REJECTED', 'IN_PROGRESS'},
    'IN_PROGRESS': {'FORWARDED', 'APPROVED', 'REJECTED'},
    'FORWARDED': {'FORWARDED', 'APPROVED', 'REJECTED', 'IN_PROGRESS'},
    'APPROVED': {'CLOSED'},
    'REJECTED': {'FORWARDED', 'IN_PROGRESS', 'CLOSED', 'ARCHIVED'},
    'CLOSED': {'ARCHIVED'},
    'ARCHIVED': {'CLOSED'},
}


def _assert_allowed_status_transition(current_status, target_status, operation_label='state transition'):
    """Validate status transitions against centralized state machine."""
    if current_status == target_status:
        return

    allowed_targets = ALLOWED_STATUS_TRANSITIONS.get(current_status, set())
    if target_status not in allowed_targets:
        raise ValueError(
            f'Invalid status transition for {operation_label}: '
            f'{current_status} -> {target_status}'
        )


def _transition_file_status(file_obj, target_status, operation_label='state transition'):
    """Apply status transition after validation."""
    _assert_allowed_status_transition(file_obj.status, target_status, operation_label=operation_label)
    file_obj.status = target_status


def _get_locked_file(file_id):
    """Lock file row for state transitions to prevent race conditions."""
    return NewFile.objects.select_for_update().get(id=file_id)


def _get_actor_extra(actor_user, action_label='perform this action'):
    """Resolve the active profile for an authenticated user."""
    actor_extra = ExtraInfo.objects.filter(user=actor_user).select_related('user', 'department').first()
    if not actor_extra:
        raise ValueError(f'No profile found for user while trying to {action_label}')
    return actor_extra


def _assert_actor_is_current_holder(file_obj, actor_extra, action_label='perform this action'):
    """Ensure only the current holder can execute holder-owned transitions."""
    if file_obj.current_holder_id != actor_extra.id:
        raise PermissionError(f'Only current holder can {action_label}')


def _get_file_department_context(file_obj, prefer_source=False):
    """Resolve the department context used for workflow routing and permission checks."""
    if prefer_source:
        return file_obj.source_department or file_obj.current_department
    return file_obj.current_department or file_obj.source_department


def _resolve_step_department(file_obj, step):
    """Resolve the effective department for a workflow step."""
    return step.department or _get_file_department_context(file_obj)


def _assert_actor_matches_file_context(file_obj, actor_extra, action_label='perform this action', prefer_source=False):
    """No-op context validator: role/department restrictions are intentionally disabled."""
    return


def _validate_holder_triplet(holder_extra, designation, department, context_label='holder state'):
    """Validate holder/designation/department tuple integrity."""
    if not holder_extra or not designation or not department:
        raise ValueError(f'Invalid {context_label}: holder, designation, and department are required')

    if holder_extra.department_id != department.id:
        raise ValueError(
            f'Invalid {context_label}: holder department ({holder_extra.department_id}) '
            f'does not match current department ({department.id})'
        )

    holds_designation = HoldsDesignation.objects.filter(
        working=holder_extra.user,
        designation=designation,
    ).exists()
    if not holds_designation:
        raise ValueError(
            f'Invalid {context_label}: user {holder_extra.user.username} '
            f'does not hold designation {designation.name}'
        )


def _validate_file_holder_consistency(file_obj):
    """Validate current holder tuple consistency on File model."""
    _validate_holder_triplet(
        file_obj.current_holder,
        file_obj.current_designation,
        file_obj.current_department,
        context_label=f'file {file_obj.file_number} current holder',
    )


def _get_workflow_steps_for_file(file_obj):
    """Return workflow steps for a file type in deterministic order."""
    steps = list(
        FileWorkflow.objects.filter(file_type=file_obj.file_type)
        .select_related('designation', 'department')
        .order_by('step_order', 'id')
    )
    if not steps:
        raise ValueError(f'No workflow configured for file type: {file_obj.file_type.name}')
    return steps


def _group_steps_by_order(steps):
    grouped = {}
    for step in steps:
        grouped.setdefault(step.step_order, []).append(step)
    return grouped


def _step_matches_holder(step, designation_id, department_id):
    if step.designation_id != designation_id:
        return False
    if step.department_id and step.department_id != department_id:
        return False
    return True


def _resolve_next_workflow_steps(file_obj):
    """Resolve candidate workflow rows for the next stage based on holder context and status."""
    steps = _get_workflow_steps_for_file(file_obj)
    grouped = _group_steps_by_order(steps)
    ordered_stage_ids = sorted(grouped.keys())

    # Initial send from draft/created file always goes to step 1.
    if file_obj.status == 'CREATED':
        return grouped.get(ordered_stage_ids[0], [])

    current_step = _resolve_current_workflow_step(file_obj)
    if not current_step:
        raise ValueError(
            f'Current holder designation/department is not aligned with workflow for file {file_obj.file_number}'
        )

    next_stage_id = next((stage_id for stage_id in ordered_stage_ids if stage_id > current_step.step_order), None)
    if next_stage_id is None:
        return []

    return grouped.get(next_stage_id, [])


def _resolve_next_workflow_step(file_obj):
    """Compatibility helper: return the first candidate row of the next workflow stage."""
    next_steps = _resolve_next_workflow_steps(file_obj)
    return next_steps[0] if next_steps else None


def _resolve_current_workflow_step(file_obj):
    """Resolve current workflow step from file's assigned designation/department."""
    steps = _get_workflow_steps_for_file(file_obj)
    file_department = _get_file_department_context(file_obj)
    for step in steps:
        effective_department = _resolve_step_department(file_obj, step)
        if _step_matches_holder(
            step,
            file_obj.current_designation_id,
            effective_department.id if effective_department else file_department.id if file_department else None,
        ):
            return step
    raise ValueError(
        f'Current holder designation/department is not aligned with workflow for file {file_obj.file_number}'
    )


def _assert_workflow_action_allowed(file_obj, operation):
    """Enforce workflow action_required for step-owned actions."""
    # Initial submit (CREATED -> first step) is allowed for creator.
    if file_obj.status == 'CREATED' and operation == 'FORWARD':
        return

    step = _resolve_current_workflow_step(file_obj)
    required = (step.action_required or '').strip().lower()
    if not required:
        return

    allowed = {
        'FORWARD': {'forward', 'review', 'route', 'process', 'recommend', 'comment'},
        'APPROVE': {'approve', 'sign', 'sanction', 'final_approve'},
        'REJECT': {'approve', 'review', 'sign', 'sanction', 'process'},
    }

    required_key = required.replace(' ', '_')
    if required_key not in allowed.get(operation, set()):
        raise PermissionError(
            f'Workflow step {step.step_order} requires action "{step.action_required}"; '
            f'operation "{operation.lower()}" is not allowed.'
        )


def _candidate_extras_for_step(file_obj, step):
    """Get all active employee profiles that hold step designation and optional department."""
    resolved_department = _resolve_step_department(file_obj, step)
    if not resolved_department:
        raise ValueError(
            f'Cannot resolve department for designation={step.designation.name} on file {file_obj.file_number}'
        )

    holders = HoldsDesignation.objects.filter(
        designation=step.designation,
        working__is_active=True,
    ).select_related('working')

    candidates = {}
    for holder in holders:
        working_user = holder.working
        if not working_user or not working_user.is_active:
            continue

        extra = ExtraInfo.objects.filter(user=working_user).first()
        if not extra:
            continue

        if extra.department_id != resolved_department.id:
            continue

        candidates[extra.id] = extra

    return [candidates[k] for k in sorted(candidates.keys())]


def _candidate_assignments_for_steps(file_obj, steps):
    """Return (holder, designation, department) assignments across all designation options in a stage."""
    assignments = []
    seen = set()
    for step in steps:
        step_department = _resolve_step_department(file_obj, step)
        for extra in _candidate_extras_for_step(file_obj, step):
            assignment_key = (extra.id, step.designation_id, step_department.id if step_department else None)
            if assignment_key in seen:
                continue
            seen.add(assignment_key)
            assignments.append({
                'extra': extra,
                'designation': step.designation,
                'department': step_department,
            })
    return assignments


def _choose_handler_for_step(file_obj, step):
    """Deterministically choose one handler for a workflow step."""
    candidates = _candidate_extras_for_step(file_obj, step)
    if not candidates:
        resolved_department = _resolve_step_department(file_obj, step)
        dept_name = resolved_department.name if resolved_department else 'any'
        raise ValueError(
            f'No active holder found for designation={step.designation.name}, department={dept_name}'
        )

    strategy = (getattr(settings, 'FILETRACKING_HANDLER_SELECTION_STRATEGY', 'least_workload') or 'least_workload').lower()
    active_statuses = ['CREATED', 'SUBMITTED', 'IN_PROGRESS', 'FORWARDED', 'REJECTED']

    if strategy == 'round_robin':
        policy_key = f'filetracking.routing.round_robin.file_type.{file_obj.file_type_id}.step.{step.step_order}'
        policy, _ = FTAccessPolicy.objects.select_for_update().get_or_create(
            key=policy_key,
            defaults={'value': {'last_index': -1}},
        )
        last_index = int((policy.value or {}).get('last_index', -1))
        next_index = (last_index + 1) % len(candidates)
        policy.value = {'last_index': next_index}
        policy.save(update_fields=['value', 'updated_at'])
        return candidates[next_index]

    # Default strategy: least workload, tie-break by profile id for deterministic selection.
    workloads = {
        row['current_holder']: row['count']
        for row in NewFile.objects.filter(
            current_holder_id__in=[candidate.id for candidate in candidates],
            status__in=active_statuses,
        ).values('current_holder').annotate(count=Count('id'))
    }

    return min(candidates, key=lambda extra: (workloads.get(extra.id, 0), extra.id))


def _choose_handler_for_steps(file_obj, steps):
    """Deterministically choose one assignment from a multi-designation workflow stage."""
    assignments = _candidate_assignments_for_steps(file_obj, steps)
    if not assignments:
        designation_names = ', '.join(sorted({step.designation.name for step in steps}))
        raise ValueError(f'No active holder found for designations: {designation_names}')

    strategy = (getattr(settings, 'FILETRACKING_HANDLER_SELECTION_STRATEGY', 'least_workload') or 'least_workload').lower()
    active_statuses = ['CREATED', 'SUBMITTED', 'IN_PROGRESS', 'FORWARDED', 'REJECTED']

    if strategy == 'round_robin':
        stage_order = steps[0].step_order if steps else 'unknown'
        policy_key = f'filetracking.routing.round_robin.file_type.{file_obj.file_type_id}.stage.{stage_order}'
        policy, _ = FTAccessPolicy.objects.select_for_update().get_or_create(
            key=policy_key,
            defaults={'value': {'last_index': -1}},
        )
        last_index = int((policy.value or {}).get('last_index', -1))
        next_index = (last_index + 1) % len(assignments)
        policy.value = {'last_index': next_index}
        policy.save(update_fields=['value', 'updated_at'])
        return assignments[next_index]

    workloads = {
        row['current_holder']: row['count']
        for row in NewFile.objects.filter(
            current_holder_id__in=[assignment['extra'].id for assignment in assignments],
            status__in=active_statuses,
        ).values('current_holder').annotate(count=Count('id'))
    }

    return min(
        assignments,
        key=lambda assignment: (
            workloads.get(assignment['extra'].id, 0),
            assignment['extra'].id,
            assignment['designation'].id,
        ),
    )


def _resolve_explicit_receiver_for_steps(file_obj, steps, receiver_username, receiver_designation_name=''):
    """Resolve a user-selected receiver - no workflow restrictions."""
    normalized_username = (receiver_username or '').strip()
    if not normalized_username:
        raise ValueError('Receiver username is required')

    receiver_user = User.objects.filter(username=normalized_username, is_active=True).first()
    if not receiver_user:
        raise ValueError(f'Receiver user not found or inactive: {normalized_username}')

    receiver_extra = ExtraInfo.objects.filter(user=receiver_user).select_related('user', 'department').first()
    if not receiver_extra:
        raise ValueError(f'Receiver profile missing for user {normalized_username}')

    # Get user's designations
    user_designations = HoldsDesignation.objects.filter(working=receiver_user).select_related('designation')
    if not user_designations.exists():
        raise ValueError(f'Receiver {normalized_username} has no designations')

    # If designation specified, use it; otherwise use first
    if receiver_designation_name:
        selected = user_designations.filter(
            designation__name__iexact=receiver_designation_name
        ).first()
        if not selected:
            raise ValueError(
                f'Receiver {normalized_username} does not hold designation {receiver_designation_name}'
            )
        receiver_designation = selected.designation
    else:
        receiver_designation = user_designations.first().designation

    # Use receiver's own department
    receiver_department = receiver_extra.department
    if not receiver_department:
        raise ValueError('Receiver department could not be resolved')

    return receiver_extra, receiver_designation, receiver_department


def get_designation(userid):
    """Get all designations held by a user"""
    user_designation = HoldsDesignation.objects.select_related('user', 'working', 'designation').filter(working=userid)
    return user_designation


def get_user_designations(user):
    """Get all designations held by a user"""
    return HoldsDesignation.objects.filter(
        working=user
    ).select_related('designation', 'designation__type')


def get_users_with_designation(designation_name):
    """Get all users holding a specific designation"""
    designation = Designation.objects.filter(name__icontains=designation_name).first()
    if not designation:
        return []

    return HoldsDesignation.objects.filter(
        designation=designation
    ).select_related('working', 'user')


def generate_file_number(prefix, department):
    """Generate unique file number"""
    year = datetime.datetime.now().year

    # Get department code
    dept_code = department.name[:3].upper() if department else 'GEN'

    # Get next sequence
    last_file = NewFile.objects.filter(
        file_number__startswith=f"{prefix}/{dept_code}/{year}"
    ).order_by('-file_number').first()

    if last_file:
        try:
            last_seq = int(last_file.file_number.split('/')[-1])
            next_seq = last_seq + 1
        except:
            next_seq = 1
    else:
        next_seq = 1

    return f"{prefix}/{dept_code}/{year}/{next_seq:04d}"


def get_initial_handler_for_file_type(file_type, department=None):
    """Get initial handler for a file type based on workflow"""
    first_step = FileWorkflow.objects.filter(
        file_type=file_type
    ).select_related('designation', 'department').order_by('step_order', 'id').first()

    if not first_step:
        return None

    first_stage_steps = list(
        FileWorkflow.objects.filter(file_type=file_type, step_order=first_step.step_order)
        .select_related('designation', 'department')
        .order_by('id')
    )

    stub_file = NewFile(
        file_type=file_type,
        current_designation=first_step.designation,
        current_department=first_step.department or department,
        source_department=department,
    )
    selected_assignment = _choose_handler_for_steps(stub_file, first_stage_steps)
    selected = selected_assignment['extra']
    selected_department = selected_assignment['department'] or selected.department
    return {
        'user': selected,
        'designation': selected_assignment['designation'],
        'department': selected_department,
    }


def get_next_required_designations(file_id):
    """Return designation names allowed in the next routing stage of a file."""
    file_obj = NewFile.objects.select_related(
        'file_type',
        'current_designation',
        'current_department',
        'source_department',
    ).get(id=file_id)

    next_steps = _resolve_next_workflow_steps(file_obj)
    names = sorted({step.designation.name for step in next_steps if step and step.designation})
    if not names:
        raise ValueError('No next workflow designation is configured for this file')

    return names


def get_next_required_designation(file_id):
    """Backward-compatible helper: return one designation from next-stage designation options."""
    return get_next_required_designations(file_id)[0]


def forward_file(file_id, sender_user, remarks='', receiver_username='', receiver_designation_name=''):
    """Forward file to next handler"""
    with transaction.atomic():
        file = _get_locked_file(file_id)
        sender_extra = _get_actor_extra(sender_user, 'forward this file')
        _assert_actor_is_current_holder(file, sender_extra, action_label='forward this file')
        _assert_actor_matches_file_context(file, sender_extra, action_label='forward this file')
        _validate_file_holder_consistency(file)

        if (receiver_username or '').strip():
            receiver_extra, receiver_designation, receiver_dept = _resolve_explicit_receiver_for_steps(
                file,
                [],
                receiver_username,
                receiver_designation_name=receiver_designation_name,
            )
        else:
            _assert_workflow_action_allowed(file, 'FORWARD')
            next_steps = _resolve_next_workflow_steps(file)
            if not next_steps:
                raise ValueError('No next workflow step available. File is already at final routing step.')
            selected_assignment = _choose_handler_for_steps(file, next_steps)
            receiver_extra = selected_assignment['extra']
            receiver_designation = selected_assignment['designation']
            receiver_dept = selected_assignment['department'] or receiver_extra.department

        # Get sender's current designation
        sender_hd = HoldsDesignation.objects.filter(working=sender_user).first()

        # Create movement record
        FileMovement.objects.create(
            file=file,
            action='FORWARD',
            sender=sender_extra,
            sender_designation=sender_hd.designation if sender_hd else file.current_designation,
            sender_department=sender_extra.department,
            receiver=receiver_extra,
            receiver_designation=receiver_designation,
            receiver_department=receiver_dept,
            remarks=remarks
        )

        # Update file current holder
        file.current_holder = receiver_extra
        file.current_designation = receiver_designation
        file.current_department = receiver_dept
        next_status = 'PENDING' if file.status == 'CREATED' else 'FORWARDED'
        _transition_file_status(file, next_status, operation_label='forward')
        _validate_file_holder_consistency(file)
        file.save(update_fields=['current_holder', 'current_designation', 'current_department', 'status', 'received_at'])

        return file


def get_file_history(file_id):
    """Get complete movement history of a file"""
    file = NewFile.objects.get(id=file_id)

    movements = FileMovement.objects.filter(file=file).select_related(
        'sender', 'receiver',
        'sender_designation', 'receiver_designation',
        'sender_department', 'receiver_department'
    ).order_by('timestamp')

    return {
        'file': file,
        'movements': list(movements),
        'total_movements': movements.count(),
        'days_open': (timezone.now() - file.created_at).days if file.status != 'CLOSED' else None
    }


def approve_file(file_id, approver_user, remarks=''):
    """Approve a file"""
    with transaction.atomic():
        file = _get_locked_file(file_id)
        approver_extra = _get_actor_extra(approver_user, 'approve this file')
        _assert_actor_is_current_holder(file, approver_extra, action_label='approve this file')
        _assert_actor_matches_file_context(file, approver_extra, action_label='approve this file')
        _validate_file_holder_consistency(file)
        try:
            _assert_workflow_action_allowed(file, 'APPROVE')
        except ValueError as exc:
            # Workflow-alignment enforcement is intentionally relaxed in current FT mode.
            if 'not aligned with workflow' not in str(exc):
                raise

        # Get approver's designation
        approver_hd = HoldsDesignation.objects.filter(working=approver_user).first()

        # Create approval movement
        FileMovement.objects.create(
            file=file,
            action='APPROVE',
            sender=approver_extra,
            sender_designation=approver_hd.designation if approver_hd else file.current_designation,
            sender_department=approver_extra.department,
            remarks=remarks
        )

        # Update file status
        _transition_file_status(file, 'APPROVED', operation_label='approve')
        file.save(update_fields=['status'])

        return file


def reject_file(file_id, rejector_user, remarks=''):
    """Reject a file"""
    with transaction.atomic():
        file = _get_locked_file(file_id)
        rejector_extra = _get_actor_extra(rejector_user, 'reject this file')
        _assert_actor_is_current_holder(file, rejector_extra, action_label='reject this file')
        _assert_actor_matches_file_context(file, rejector_extra, action_label='reject this file')
        _validate_file_holder_consistency(file)
        _assert_workflow_action_allowed(file, 'REJECT')

        # Get rejector's designation
        rejector_hd = HoldsDesignation.objects.filter(working=rejector_user).first()

        # Create rejection movement
        FileMovement.objects.create(
            file=file,
            action='REJECT',
            sender=rejector_extra,
            sender_designation=rejector_hd.designation if rejector_hd else file.current_designation,
            sender_department=rejector_extra.department,
            remarks=remarks
        )

        # Update file status
        _transition_file_status(file, 'REJECTED', operation_label='reject')
        file.save(update_fields=['status'])

        return file


def close_file(file_id, closer_user, remarks=''):
    """Close a file - only creator can close"""
    with transaction.atomic():
        file = _get_locked_file(file_id)
        closer_extra = _get_actor_extra(closer_user, 'close this file')
        _validate_file_holder_consistency(file)
        _assert_actor_matches_file_context(file, closer_extra, action_label='close this file', prefer_source=True)

        # ✅ SECURITY CHECK: Only file creator can close/archive (by Django user identity)
        if not file.created_by or file.created_by.user_id != closer_user.id:
            raise PermissionError(f"Only file creator can close this file. Creator: {file.created_by.user.username}")

        # Get closer's designation
        closer_hd = HoldsDesignation.objects.filter(working=closer_user).first()

        # Create closure movement
        FileMovement.objects.create(
            file=file,
            action='CLOSE',
            sender=closer_extra,
            sender_designation=closer_hd.designation if closer_hd else file.current_designation,
            sender_department=closer_extra.department,
            remarks=remarks
        )

        # Update file status (only APPROVED/REJECTED -> CLOSED)
        _transition_file_status(file, 'CLOSED', operation_label='close')
        file.closed_at = timezone.now()
        file.closure_remarks = remarks
        file.save(update_fields=['status', 'closed_at', 'closure_remarks'])

        return file


def return_file(file_id, returner_user, remarks=''):
    """Return a file to sender - allows rejection/return to previous holder"""
    with transaction.atomic():
        file = _get_locked_file(file_id)
        returner_extra = _get_actor_extra(returner_user, 'return this file')
        _assert_actor_is_current_holder(file, returner_extra, action_label='return this file')
        _assert_actor_matches_file_context(file, returner_extra, action_label='return this file')
        _validate_file_holder_consistency(file)

        # Get returner's designation
        returner_hd = HoldsDesignation.objects.filter(working=returner_user).first()

        # Get the file creator/original sender
        original_sender = file.created_by
        original_sender_hd = HoldsDesignation.objects.filter(working=original_sender.user).first()
        receiver_designation = original_sender_hd.designation if original_sender_hd and original_sender_hd.designation else file.current_designation
        _validate_holder_triplet(
            original_sender,
            receiver_designation,
            original_sender.department,
            context_label='return target assignment',
        )

        # Create return movement
        FileMovement.objects.create(
            file=file,
            action='RETURN',
            sender=returner_extra,
            sender_designation=returner_hd.designation if returner_hd else file.current_designation,
            sender_department=returner_extra.department,
            receiver=original_sender,
            receiver_designation=receiver_designation,
            receiver_department=original_sender.department,
            remarks=remarks
        )

        # Update file current holder back to creator.
        # Return indicates processing rejection/escalation back to originator,
        # so status should reflect REJECTED instead of IN_PROGRESS.
        file.current_holder = original_sender
        file.current_designation = receiver_designation
        file.current_department = original_sender.department
        _transition_file_status(file, 'REJECTED', operation_label='return')
        _validate_file_holder_consistency(file)
        file.save(update_fields=['current_holder', 'current_designation', 'current_department', 'status', 'received_at'])

        return file


def amend_file(file_id, amender_user, comment):
    """Add amendment and optionally forward the file."""
    with transaction.atomic():
        file = _get_locked_file(file_id)
        amender_extra = _get_actor_extra(amender_user, 'amend this file')
        _assert_actor_is_current_holder(file, amender_extra, action_label='amend this file')
        _assert_actor_matches_file_context(file, amender_extra, action_label='amend this file')
        _validate_file_holder_consistency(file)

        # Get amender's designation
        amender_hd = HoldsDesignation.objects.filter(working=amender_user).first()

        # Version snapshot captures file state before amendment workflow transitions.
        snapshot = {
            'file_number': file.file_number,
            'subject': file.subject,
            'description': file.description,
            'status': file.status,
            'current_holder': file.current_holder.user.username if file.current_holder and file.current_holder.user else '',
            'current_designation': file.current_designation.name if file.current_designation else '',
            'current_department': file.current_department.name if file.current_department else '',
            'attachments': [
                {
                    'id': att.id,
                    'name': att.name,
                    'uploaded_by': att.uploaded_by.user.username if att.uploaded_by and att.uploaded_by.user else '',
                    'uploaded_at': att.uploaded_at.isoformat() if att.uploaded_at else None,
                }
                for att in file.attachments.all().order_by('-uploaded_at')
            ],
        }

        latest_version = FileVersion.objects.filter(file=file).order_by('-version_number').first()
        next_version = (latest_version.version_number + 1) if latest_version else 1
        version = None
        try:
            version = FileVersion.objects.create(
                file=file,
                version_number=next_version,
                changed_by=amender_extra,
                action='SAVE',
                comment=comment,
                snapshot=snapshot,
            )
        except IntegrityError as err:
            logger.warning(
                'FileVersion creation skipped for file_id=%s due to DB integrity mismatch: %s',
                file_id,
                str(err),
            )

        # Create comment movement (amendment)
        FileMovement.objects.create(
            file=file,
            action='COMMENT',
            sender=amender_extra,
            sender_designation=amender_hd.designation if amender_hd else file.current_designation,
            sender_department=amender_extra.department,
            remarks=comment
        )

        return file, version


def amend_file_with_action(
    file_id,
    amender_user,
    action='SAVE',
    comment='',
    receiver_username='',
    receiver_designation_name='',
):
    """Amend a file and either save in inbox or forward to next handler."""
    with transaction.atomic():
        file = _get_locked_file(file_id)
        amender_extra = _get_actor_extra(amender_user, 'amend this file')

        if file.current_holder != amender_extra:
            raise PermissionError('Only current holder can amend this file')

        _assert_actor_matches_file_context(file, amender_extra, action_label='amend this file')

        _validate_file_holder_consistency(file)

        if file.status == 'CREATED':
            raise PermissionError('Created files cannot be amended before sending')

        if file.status in ['CLOSED', 'ARCHIVED']:
            raise ValueError('Closed or archived files cannot be amended')

        normalized_action = (action or 'SAVE').upper()
        if normalized_action not in ['SAVE', 'FORWARD']:
            raise ValueError('Invalid amendment action. Allowed values: SAVE, FORWARD')

        amended_file, version = amend_file(file_id, amender_user, comment)

        if normalized_action == 'FORWARD':
            forwarded_file = forward_file(
                file_id,
                amender_user,
                remarks=comment,
                receiver_username=receiver_username,
                receiver_designation_name=receiver_designation_name,
            )
            if version is not None:
                version.action = 'FORWARD'
                version.save(update_fields=['action'])
            return forwarded_file, version

        if amended_file.status in ['PENDING', 'SUBMITTED', 'FORWARDED', 'REJECTED']:
            _transition_file_status(amended_file, 'IN_PROGRESS', operation_label='amend-save')
            amended_file.save(update_fields=['status'])

        return amended_file, version


def archive_file(file_id, actor_user, remarks='File archived'):
    """Archive a file - only creator can archive and only from CLOSED state."""
    with transaction.atomic():
        file = _get_locked_file(file_id)
        actor_extra = _get_actor_extra(actor_user, 'archive this file')
        _validate_file_holder_consistency(file)
        _assert_actor_matches_file_context(file, actor_extra, action_label='archive this file', prefer_source=True)

        if not file.created_by or file.created_by.user_id != actor_user.id:
            raise PermissionError('Only file owner can archive this file')

        sender_hd = HoldsDesignation.objects.filter(working=actor_user).first()

        _transition_file_status(file, 'ARCHIVED', operation_label='archive')
        file.save(update_fields=['status'])

        FileMovement.objects.create(
            file=file,
            action='ARCHIVE',
            sender=actor_extra,
            sender_designation=sender_hd.designation if sender_hd else file.current_designation,
            sender_department=actor_extra.department,
            remarks=remarks,
        )

        return file


def unarchive_file(file_id, actor_user, remarks='File unarchived'):
    """Unarchive a file - only creator can unarchive and only from ARCHIVED state."""
    with transaction.atomic():
        file = _get_locked_file(file_id)
        actor_extra = _get_actor_extra(actor_user, 'unarchive this file')
        _validate_file_holder_consistency(file)
        _assert_actor_matches_file_context(file, actor_extra, action_label='unarchive this file', prefer_source=True)

        if not file.created_by or file.created_by.user_id != actor_user.id:
            raise PermissionError('Only file owner can unarchive this file')

        sender_hd = HoldsDesignation.objects.filter(working=actor_user).first()

        _transition_file_status(file, 'CLOSED', operation_label='unarchive')
        file.save(update_fields=['status'])

        FileMovement.objects.create(
            file=file,
            action='REOPEN',
            sender=actor_extra,
            sender_designation=sender_hd.designation if sender_hd else file.current_designation,
            sender_department=actor_extra.department,
            remarks=remarks,
        )

        return file


def delete_draft(draft_id, user):
    """Delete a draft file - only creator can delete"""
    draft = DraftFile.objects.get(id=draft_id)
    draft_creator = draft.created_by

    user_extra = _get_actor_extra(user, 'delete this draft')

    # ✅ SECURITY: Only creator can delete draft
    if draft_creator != user_extra:
        raise PermissionError(f"Only draft creator can delete this draft")

    draft.delete()
    return True