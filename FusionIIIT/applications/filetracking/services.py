from applications.filetracking import utils


def generate_file_number(prefix, department):
    return utils.generate_file_number(prefix, department)


def get_initial_handler_for_file_type(file_type, department=None):
    return utils.get_initial_handler_for_file_type(file_type, department=department)


def get_next_required_designation(file_id):
    return utils.get_next_required_designation(file_id)


def get_next_required_designations(file_id):
    return utils.get_next_required_designations(file_id)


def forward_file(file_id, sender_user, remarks='', receiver_username='', receiver_designation_name=''):
    return utils.forward_file(
        file_id,
        sender_user,
        remarks=remarks,
        receiver_username=receiver_username,
        receiver_designation_name=receiver_designation_name,
    )


def approve_file(file_id, approver_user, remarks=''):
    return utils.approve_file(file_id, approver_user, remarks)


def reject_file(file_id, rejector_user, remarks=''):
    return utils.reject_file(file_id, rejector_user, remarks)


def close_file(file_id, closer_user, remarks=''):
    return utils.close_file(file_id, closer_user, remarks)


def archive_file(file_id, actor_user, remarks='File archived'):
    return utils.archive_file(file_id, actor_user, remarks)


def unarchive_file(file_id, actor_user, remarks='File unarchived'):
    return utils.unarchive_file(file_id, actor_user, remarks)


def return_file(file_id, returner_user, remarks=''):
    return utils.return_file(file_id, returner_user, remarks)


def amend_file_with_action(
    file_id,
    amender_user,
    action='SAVE',
    comment='',
    receiver_username='',
    receiver_designation_name='',
    **kwargs,
):
    """Wrapper for utils.amend_file_with_action with consistent argument mapping."""
    # Capture any legacy kwargs and raise clear error
    if kwargs:
        unexpected = ', '.join(sorted(kwargs.keys()))
        raise TypeError(f'unexpected keyword argument(s): {unexpected}')

    # Call utils with correct keyword argument order and names
    return utils.amend_file_with_action(
        file_id=file_id,
        amender_user=amender_user,
        action=action,
        comment=comment,
        receiver_username=receiver_username,
        receiver_designation_name=receiver_designation_name,
    )


def delete_draft(draft_id, user):
    return utils.delete_draft(draft_id, user)


def get_file_history(file_id):
    return utils.get_file_history(file_id)
