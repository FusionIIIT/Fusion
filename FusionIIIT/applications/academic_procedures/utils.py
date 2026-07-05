from datetime import timedelta

from django.core.mail import EmailMultiAlternatives
from django.urls import reverse
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)

INVITATION_TIMEOUT_DAYS = 15

def send_invitation_email(inv):
    """
    Send the initial invitation email to the professor with template rendering.
    """
    try:
        thesis_title = inv.submission.thesis.research_theme
        base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        accept_url = base_url + reverse('invitation_action', args=[inv.token, 'accept'])
        reject_url = base_url + reverse('invitation_action', args=[inv.token, 'reject'])
        expires_at = inv.expires_at.strftime('%Y-%m-%d') if inv.expires_at else 'N/A'


        context = {
            'prof_name': inv.prof_name,
            'thesis_title': thesis_title,
            'accept_url': accept_url,
            'reject_url': reject_url,
            'expires_at': expires_at,
        }
        
        subject = f"Invitation to review: {thesis_title}"
        html_content = render_to_string('email/invitation.html', context)
        text_content = render_to_string('email/invitation.txt', context)

        msg = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [inv.prof_email],
        )
        msg.attach_alternative(html_content, 'text/html')
        msg.send()
        logger.info(f"Invitation email sent to {inv.prof_email} for token {inv.token}")
    except Exception as e:
        logger.exception(f"Failed to send invitation email for token {inv.token}: {e}")
        raise


def send_review_form_email(inv):
    """
    Send the review form link after the professor has accepted the invitation.
    """
    try:
        thesis_title = inv.submission.thesis.research_theme
        base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        review_url = base_url + reverse('review_detail', args=[inv.token])

        context = {
            'prof_name': inv.prof_name,
            'thesis_title': thesis_title,
            'review_url': review_url,
        }

        subject = f"Review form: {thesis_title}"
        html_content = render_to_string('email/review_form.html', context)
        text_content = render_to_string('email/review_form.txt', context)

        msg = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [inv.prof_email],
        )
        msg.attach_alternative(html_content, 'text/html')
        msg.send()
        logger.info(f"Review form email sent to {inv.prof_email} for token {inv.token}")
    except Exception as e:
        logger.exception(f"Failed to send review form email for token {inv.token}: {e}")
        raise


def send_thank_you_email(inv):
    """
    Send a thank-you note once the professor submits their review.
    """
    try:
        thesis_title = inv.submission.thesis.research_theme

        context = {
            'prof_name': inv.prof_name,
            'thesis_title': thesis_title,
        }

        subject = f"Thank you for reviewing: {thesis_title}"
        html_content = render_to_string('email/thank_you.html', context)
        text_content = render_to_string('email/thank_you.txt', context)

        msg = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [inv.prof_email],
        )
        msg.attach_alternative(html_content, 'text/html')
        msg.send()
        logger.info(f"Thank you email sent to {inv.prof_email} for token {inv.token}")
    except Exception as e:
        logger.exception(f"Failed to send thank you email for token {inv.token}: {e}")
        raise


def advance_invitation(submission, examiner_type):
    """
    Send the invitation to the next-ranked, not-yet-sent examiner of the
    given type (indian/foreign) for this submission. Used both when an
    examiner declines and by the daily timeout job, so a decline/timeout
    always falls through to the next professor in the Director's priority
    order for that category.
    """
    from .models import ReviewInvitation

    next_inv = (
        ReviewInvitation.objects
        .filter(submission=submission, examiner_type=examiner_type, last_sent__isnull=True)
        .order_by('priority')
        .first()
    )
    if next_inv is None:
        logger.warning(
            f"No more {examiner_type} examiners left to invite for submission {submission.id}"
        )
        return None

    next_inv.last_sent = timezone.now()
    next_inv.expires_at = timezone.now() + timedelta(days=INVITATION_TIMEOUT_DAYS)
    next_inv.save(update_fields=['last_sent', 'expires_at'])
    send_invitation_email(next_inv)
    return next_inv
