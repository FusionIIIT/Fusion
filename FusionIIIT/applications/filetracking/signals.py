"""
Signals for File Tracking System - Send notifications on file events
"""
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from notifications.signals import notify

from .models import FileMovement


logger = logging.getLogger(__name__)


@receiver(post_save, sender=FileMovement)
def notify_file_action(sender, instance, created, **kwargs):
    """
    Send notification when file movement occurs
    - File created → notify initial handler
    - File forwarded → notify receiver
    - File approved/rejected/closed → notify creator
    """
    if not created:
        return

    movement = instance
    file = movement.file
    action = movement.action
    receiver_user = movement.receiver

    try:
        # Determine notification message and recipient
        if action == 'CREATE':
            # Notify initial handler that file is assigned
            message = f"New file assigned to you: {file.file_number} - {file.subject[:50]}"
            recipient = file.current_holder.user if file.current_holder else None

        elif action == 'FORWARD':
            # Notify receiver that file is forwarded to them
            message = f"File forwarded to you: {file.file_number} - {file.subject[:50]}"
            recipient = receiver_user.user if receiver_user else None

        elif action == 'APPROVE':
            # Notify creator that file is approved
            message = f"Your file approved: {file.file_number}"
            recipient = file.created_by.user

        elif action == 'REJECT':
            # Notify creator that file is rejected
            message = f"Your file rejected: {file.file_number}"
            recipient = file.created_by.user

        elif action == 'RETURN':
            # Notify creator that file is returned
            message = f"Your file returned: {file.file_number}"
            recipient = file.created_by.user

        elif action == 'CLOSE':
            # Notify creator that file is closed
            message = f"Your file closed: {file.file_number}"
            recipient = file.created_by.user

        elif action == 'ARCHIVE':
            # Notify creator that file is archived
            message = f"Your file archived: {file.file_number}"
            recipient = file.created_by.user

        elif action == 'REOPEN':
            # Notify creator that file is reopened from archive
            message = f"Your file reopened: {file.file_number}"
            recipient = file.created_by.user

        elif action == 'COMMENT':
            # Notify creator that comment is added
            message = f"New comment on file: {file.file_number}"
            recipient = file.created_by.user

        else:
            return

        # Create notification through the shared notification engine.
        if recipient:
            try:
                notify.send(
                    sender=movement.sender.user if movement.sender and movement.sender.user else recipient,
                    recipient=recipient,
                    url=f'filetracking/{file.id}',
                    module='File Tracking',
                    verb=message,
                    target=file,
                )
            except Exception as e:
                # Keep workflow resilient even if notification backend schema changes.
                logger.exception(
                    'Failed to dispatch filetracking notification for file_id=%s action=%s: %s',
                    file.id,
                    action,
                    str(e),
                )

            # Optional: Send email notification (can be enabled later)
            # send_email_notification(recipient.email, message)

    except Exception as e:
        # Log error but don't break the workflow
        logger.exception('Notification signal failed for file_id=%s: %s', file.id, str(e))


def send_email_notification(email, message):
    """
    Send email notification (optional enhancement)
    Can be enabled by uncommenting the email_backend in settings
    """
    try:
        send_mail(
            subject='File Tracking Update',
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=True,
        )
    except Exception as e:
        logger.exception('Email notification failed for recipient=%s: %s', email, str(e))
