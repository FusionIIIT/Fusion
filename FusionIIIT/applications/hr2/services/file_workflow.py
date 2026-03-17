"""Service layer for file creation and forwarding workflows.

This module centralizes interactions with the filetracking SDK so that views remain thin
and can be unit tested more easily.
"""

from applications.filetracking.sdk.methods import (
    archive_file,
    create_file,
    forward_file,
    view_archived,
    view_history,
    view_inbox,
    view_outbox,
)


def create_form_file(*, uploader: str, uploader_designation: str, receiver: str, receiver_designation: str,
                     src_object_id: str, form_type: str, src_module: str = "HR", attached_file=None):
    """Create a file in filetracking for a form and return the created file id."""

    return create_file(
        uploader=uploader,
        uploader_designation=uploader_designation,
        receiver=receiver,
        receiver_designation=receiver_designation,
        src_module=src_module,
        src_object_id=src_object_id,
        file_extra_JSON={"type": form_type},
        attached_file=attached_file,
    )


def forward_form_file(*, file_id: str, receiver: str, receiver_designation: str, remarks: str, file_extra_JSON: dict):
    """Forward an existing file in the filetracking workflow."""

    return forward_file(
        file_id=file_id,
        receiver=receiver,
        receiver_designation=receiver_designation,
        remarks=remarks,
        file_extra_JSON=file_extra_JSON,
    )


def archive_form_file(*, file_id: str) -> bool:
    """Archive a file (soft delete) in the filetracking workflow."""
    return archive_file(file_id=file_id)


def get_inbox(*, username: str, designation: str, src_module: str = "HR"):
    return view_inbox(username=username, designation=designation, src_module=src_module)


def get_archived(*, username: str, designation: str, src_module: str = "HR"):
    return view_archived(username=username, designation=designation, src_module=src_module)


def get_outbox(*, username: str, designation: str, src_module: str = "HR"):
    return view_outbox(username=username, designation=designation, src_module=src_module)


def get_file_history(*, file_id: str):
    return view_history(file_id)
