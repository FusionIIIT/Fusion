"""Run the VMS event-triggered services once (VMS-UC-037/038/039/040).

Schedule it every few minutes with cron if Celery beat is not running::

    */5 * * * * cd /path/to/FusionIIIT && python manage.py vms_run_scheduled_tasks
"""

from django.core.management.base import BaseCommand

from applications.visitor_management.services.lifecycle import run_scheduled_tasks


class Command(BaseCommand):
    help = "Expire timed-out requests, send reminders, auto-checkout and reconcile offline gate events."

    def handle(self, *args, **options):
        result = run_scheduled_tasks()
        self.stdout.write(self.style.SUCCESS(
            "expired={expired} reminders={reminders} auto_checked_out={auto_checked_out} "
            "offline_reconciled={offline_reconciled}".format(**result)))
