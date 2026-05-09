"""
Script to assign HoldsDesignation entries to all Supervisors in the complaint system
so that the role-switcher dropdown recognizes them.
"""
from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo, Designation, HoldsDesignation
from applications.complaint_system.models import Supervisor

supervisors = Supervisor.objects.all()
created_count = 0
skipped_count = 0
error_count = 0

for sup in supervisors:
    staff_id = sup.sup_id_id
    comp_type = sup.type

    # Find the ExtraInfo and its User
    try:
        extra = ExtraInfo.objects.get(id=staff_id)
        user = extra.user
    except ExtraInfo.DoesNotExist:
        print(f"  SKIP: ExtraInfo '{staff_id}' not found")
        error_count += 1
        continue

    # Format designation name based on type
    if comp_type.lower() == 'electricity':
        desig_name = 'Electricitysupervisor'
    else:
        desig_name = f"{comp_type.lower()}supervisor"

    desig, _ = Designation.objects.get_or_create(
        name=desig_name,
        defaults={'full_name': f'{comp_type.capitalize()} Supervisor', 'type': 'staff'}
    )

    # Create HoldsDesignation if not already present
    obj, created = HoldsDesignation.objects.get_or_create(
        user=user,
        working=user,
        designation=desig,
    )

    if created:
        print(f"  CREATED: {user.username} -> {desig_name}")
        created_count += 1
    else:
        print(f"  EXISTS:  {user.username} -> {desig_name}")
        skipped_count += 1

print(f"\nDone! Created: {created_count}, Already existed: {skipped_count}, Errors: {error_count}")
