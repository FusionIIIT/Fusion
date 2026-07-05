from __future__ import absolute_import, unicode_literals

import logging
from datetime import timedelta

import celery
from django.utils import timezone

from .models import ThesisSubmission, ReviewInvitation
from .utils import send_invitation_email, send_review_form_email, advance_invitation, INVITATION_TIMEOUT_DAYS

logger = logging.getLogger(__name__)

REMINDER_INTERVAL_DAYS = 3


@celery.task()
def process_review_invitations():
    """
    Runs daily. For each in-review submission, and each examiner category
    (Indian / Foreign) independently:
      1) If the lowest-priority invite in that category was never sent -> send it.
      2) If it has been pending past the timeout -> expire it and advance to
         the next-ranked examiner in that category.
      3) If still pending -> resend a reminder every few days.
      4) If accepted -> send the daily review-form link.
    """
    now = timezone.now()
    submissions = ThesisSubmission.objects.filter(status='in_review')
    logger.info(f"process_review_invitations starting for {submissions.count()} submissions")

    for sub in submissions:
        if ReviewInvitation.objects.filter(submission=sub, status='completed').exists():
            continue

        for examiner_type in ('indian', 'foreign'):
            invites = (
                ReviewInvitation.objects
                .filter(submission=sub, examiner_type=examiner_type)
                .order_by('priority')
            )
            for inv in invites:
                if inv.is_finalized():
                    continue

                try:
                    if inv.last_sent is None:
                        inv.last_sent = now
                        inv.expires_at = now + timedelta(days=INVITATION_TIMEOUT_DAYS)
                        inv.save(update_fields=['last_sent', 'expires_at'])
                        send_invitation_email(inv)
                        logger.info(f"Sent initial invitation for token {inv.token}")
                        break

                    if inv.is_expired():
                        inv.status = 'expired'
                        inv.save(update_fields=['status'])
                        logger.info(f"Expired invitation {inv.token} ({INVITATION_TIMEOUT_DAYS}-day timeout)")
                        advance_invitation(sub, examiner_type)
                        break

                    if inv.status == 'pending' and now >= inv.last_sent + timedelta(days=REMINDER_INTERVAL_DAYS):
                        send_invitation_email(inv)
                        inv.last_sent = now
                        inv.save(update_fields=['last_sent'])
                        logger.info(f"Sent reminder for token {inv.token}")
                        break

                    if inv.status == 'accepted' and (
                        inv.review_form_sent is None or now >= inv.review_form_sent + timedelta(days=1)
                    ):
                        send_review_form_email(inv)
                        inv.review_form_sent = now
                        inv.save(update_fields=['review_form_sent'])
                        logger.info(f"Sent review-form link for token {inv.token}")
                        break
                except Exception as e:
                    logger.exception(f"Error processing invitation {inv.token} for submission {sub.id}: {e}")
                    continue

    logger.info("process_review_invitations completed")
