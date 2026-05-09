from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from applications.globals.utils import ensure_extrainfo


User = get_user_model()


@receiver(post_save, sender=User)
def create_extrainfo_for_new_user(sender, instance, created, **kwargs):
    if created:
        ensure_extrainfo(instance)
