from datetime import timedelta

from django.core.mail import EmailMultiAlternatives
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
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        accept_url = f"{frontend_url}/thesis-invitation/{inv.token}/accept"
        reject_url = f"{frontend_url}/thesis-invitation/{inv.token}/reject"
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
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        review_url = f"{frontend_url}/thesis-evaluation/{inv.token}"

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


def send_examiner_panel_invitation_email(candidate):
    """
    Send the initial invitation email to a ThesisExaminerPanel candidate.
    """
    try:
        batch_name = str(candidate.panel.batch)
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        accept_url = f"{frontend_url}/thesis-examiner-panel/{candidate.token}/accept"
        reject_url = f"{frontend_url}/thesis-examiner-panel/{candidate.token}/reject"
        expires_at = candidate.expires_at.strftime('%Y-%m-%d') if candidate.expires_at else 'N/A'

        context = {
            'prof_name': candidate.name,
            'batch_name': batch_name,
            'accept_url': accept_url,
            'reject_url': reject_url,
            'expires_at': expires_at,
        }

        subject = f"Examiner invitation: {batch_name}"
        html_content = render_to_string('email/examiner_panel_invitation.html', context)
        text_content = render_to_string('email/examiner_panel_invitation.txt', context)

        msg = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [candidate.email],
        )
        msg.attach_alternative(html_content, 'text/html')
        msg.send()
        logger.info(f"Examiner panel invitation sent to {candidate.email} for token {candidate.token}")
    except Exception as e:
        logger.exception(f"Failed to send examiner panel invitation for token {candidate.token}: {e}")
        raise


def send_examiner_panel_scoring_email(candidate):
    """
    Send the batch-scoring link after the candidate has accepted.
    """
    try:
        batch_name = str(candidate.panel.batch)
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        scoring_url = f"{frontend_url}/thesis-examiner-panel/{candidate.token}/score"

        context = {
            'prof_name': candidate.name,
            'batch_name': batch_name,
            'scoring_url': scoring_url,
        }

        subject = f"Scoring form: {batch_name}"
        html_content = render_to_string('email/examiner_panel_scoring.html', context)
        text_content = render_to_string('email/examiner_panel_scoring.txt', context)

        msg = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [candidate.email],
        )
        msg.attach_alternative(html_content, 'text/html')
        msg.send()
        logger.info(f"Examiner panel scoring link sent to {candidate.email} for token {candidate.token}")
    except Exception as e:
        logger.exception(f"Failed to send examiner panel scoring link for token {candidate.token}: {e}")
        raise


def advance_examiner_panel_invitation(panel):
    """
    Send the invitation to the next-ranked, not-yet-sent candidate for this
    panel. Used when a candidate declines, so decline always falls through
    to the next professor in the Dean's priority order. Returns the newly
    invited candidate, or None (and marks the panel 'all_declined') if no
    candidates remain.
    """
    from .models import ThesisExaminerCandidate

    next_candidate = (
        ThesisExaminerCandidate.objects
        .filter(panel=panel, last_sent__isnull=True)
        .order_by('priority')
        .first()
    )
    if next_candidate is None:
        panel.status = 'all_declined'
        panel.save(update_fields=['status'])
        logger.warning(f"No more examiner candidates left to invite for panel {panel.id} ({panel.batch})")
        return None

    next_candidate.status = 'invited'
    next_candidate.last_sent = timezone.now()
    next_candidate.expires_at = timezone.now() + timedelta(days=INVITATION_TIMEOUT_DAYS)
    next_candidate.save(update_fields=['status', 'last_sent', 'expires_at'])
    send_examiner_panel_invitation_email(next_candidate)
    return next_candidate


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
