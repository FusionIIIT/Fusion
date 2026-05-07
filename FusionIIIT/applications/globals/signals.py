from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_extrainfo(sender, instance, created, **kwargs):
    """
    Signal handler that creates an ExtraInfo record when a new User is created.
    This ensures every user has the required ExtraInfo profile.
    """
    if created:
        try:
            # Check if ExtraInfo already exists
            if not hasattr(instance, 'extrainfo'):
                ExtraInfo.objects.get_or_create(
                    id=instance.username,
                    defaults={
                        'user': instance,
                        'title': 'Mr.',
                        'sex': 'M',
                        'user_type': 'Student',  # Default type
                        'user_status': 'PRESENT',
                    }
                )
                logger.info(f"Created ExtraInfo for user: {instance.username}")
        except Exception as e:
            logger.error(f"Error creating ExtraInfo for user {instance.username}: {e}")


@receiver(post_save, sender=User)
def save_user_extrainfo(sender, instance, **kwargs):
    """
    Signal handler that ensures ExtraInfo exists for saved users.
    """
    if not kwargs.get('created'):  # Only for updates, not creation
        try:
            if not hasattr(instance, 'extrainfo'):
                ExtraInfo.objects.get_or_create(
                    id=instance.username,
                    defaults={
                        'user': instance,
                        'title': 'Mr.',
                        'sex': 'M',
                        'user_type': 'Student',
                        'user_status': 'PRESENT',
                    }
                )
        except Exception as e:
            logger.error(f"Error ensuring ExtraInfo for user {instance.username}: {e}")
