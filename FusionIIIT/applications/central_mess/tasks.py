
from celery.decorators import periodic_task
from celery.task.schedules import crontab
from datetime import datetime, timedelta
from applications.central_mess.models import Rebate, Monthly_bill, Vacation_food, Messinfo
from applications.central_mess.handlers import generate_bill
from django.utils import timezone

@periodic_task(run_every=crontab(minute='0', hour='0'), name="escalate_rebates")
def escalate_rebates():
    yesterday = datetime.now().date() - timedelta(days=1)
    # escalate rules (pending for > 24 hours)
    pending_rebates = Rebate.objects.filter(status='1', app_date__lte=yesterday, escalated_at__isnull=True)
    for r in pending_rebates:
        r.escalation_remark = "Auto-escalated to Warden due to 24h SLA"
        r.escalated_at = timezone.now()
        r.save()

@periodic_task(run_every=crontab(0, 0, day_of_month='1'), name="auto_generate_bill")
def auto_generate_bill():
    generate_bill()

@periodic_task(run_every=crontab(minute='0', hour='0'), name="auto_generate_vacation_survey")
def auto_generate_vacation_survey():
    from applications.central_mess.models import MessAnnouncement
    today = datetime.now().date()
    # Assume vacations commonly start Dec 1 and May 1 for winter/summer breaks.
    # 7 days prior is Nov 24 and Apr 24.
    if (today.month == 11 and today.day == 24) or (today.month == 4 and today.day == 24):
        MessAnnouncement.objects.create(
            title="Vacation Survey Open",
            message="Please fill out the vacation food survey.",
            publish_date=today,
            expiry_date=today + timedelta(days=7),
            is_active=True
        )


@periodic_task(run_every=crontab(minute='0', hour='12'), name="route_refunds_to_finance")
def route_refunds_to_finance():
    # BR-MMS-018 & BR-MMS-022: refund routing workflow/finance clearance model
    from applications.central_mess.models import RefundCancellation
    from notification.views import central_mess_notif

    # Find refunds approved by warden but not yet processed by finance
    pending_refunds = RefundCancellation.objects.filter(warden_approved=True, finance_processed=False)
    for refund in pending_refunds:
        # Mocking finance clearance - auto approve for demonstration or send notification to finance
        refund.finance_processed = True
        refund.save()
        # notify student
        try:
            central_mess_notif(refund.student_id.id.user, refund.student_id.id.user, 'refund_cleared', 'Your refund of amount {} has been cleared by finance.'.format(refund.amount))
        except Exception:
            pass
