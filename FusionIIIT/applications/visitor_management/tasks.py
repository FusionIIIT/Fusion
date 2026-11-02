"""Celery entry point for the event-triggered use cases VMS-UC-037/038/039/040."""

from celery import shared_task


@shared_task
def run_vms_lifecycle():
    from .services.lifecycle import run_scheduled_tasks
    return run_scheduled_tasks()
