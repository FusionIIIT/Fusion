"""HR2 signals: auto-provision leave balance when an Employee row is created."""

from django.db.models.signals import post_save
from django.dispatch import receiver

from applications.hr2.models import Employee, LeaveBalance, CPDABalance


@receiver(post_save, sender=Employee)
def create_leave_balance_on_employee_create(sender, instance, created, **kwargs):
    if not created:
        return
    LeaveBalance.objects.get_or_create(
        employeeId=instance.extra_info,
        defaults={},
    )
    CPDABalance.objects.get_or_create(
        employeeId=instance.extra_info,
        defaults={'cpda_allotted': 300000.00, 'cpda_used': 0.00},
    )
