from django_cron import CronJobBase, Schedule
from datetime import datetime

class EmailPrinterCron(CronJobBase):
    RUN_EVERY_MINS = 1000  # Runs every 2 minutes

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'academic_procedures.email_printer_cron'  # Unique code

    def do(self):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"Email sent at {now}")

# NOTE: the PhD thesis review-invitation lifecycle (send/expire/cascade/remind)
# used to live here as a django_cron job, but django_cron isn't an installed
# dependency in this project (only django-crontab/Celery are) so it never ran.
# It's now implemented as a real Celery beat task:
# applications/academic_procedures/tasks.py::process_review_invitations,
# registered in Fusion/settings/common.py CELERY_BEAT_SCHEDULE.