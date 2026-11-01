from celery import shared_task
from .services import release_due


@shared_task
def release_scheduled_content():
    return release_due()
