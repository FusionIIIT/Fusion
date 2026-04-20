"""
Script to assign HoldsDesignation entries to all Caretakers in the complaint system
so that the role-switcher dropdown recognizes them.
"""
from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo, Designation, HoldsDesignation
from applications.complaint_system.models import Caretaker

# Area -> Designation name mapping
AREA_DESIGNATION_MAP = {
    'hall-1': 'hall1caretaker',
    'hall-3': 'hall3caretaker',
    'hall-4': 'hall4caretaker',
    'core_lab': 'corelabcaretaker',
    'LHTC': 'lhtccaretaker',
    'NR2': 'nr2caretaker',
    'Rewa_Residency': 'rewacaretaker',
    'Maa Saraswati Hostel': 'mshcaretaker',
    'Nagarjun Hostel': 'nhcaretaker',
    'Panini Hostel': 'phcaretaker',
}

caretakers = Caretaker.objects.all()
created_count = 0
skipped_count = 0
error_count = 0

for ct in caretakers:
    staff_id = ct.staff_id_id
    area = ct.area

    # Find the ExtraInfo and its User
    try:
        extra = ExtraInfo.objects.get(id=staff_id)
        user = extra.user
    except ExtraInfo.DoesNotExist:
        print(f"  SKIP: ExtraInfo '{staff_id}' not found")
        error_count += 1
        continue

    # Find the matching designation
    desig_name = AREA_DESIGNATION_MAP.get(area)
    if not desig_name:
        # Fallback: create a generic caretaker designation for this area
        safe_area = area.lower().replace(' ', '').replace('_', '')
        desig_name = f"{safe_area}caretaker"

    desig, _ = Designation.objects.get_or_create(
        name=desig_name,
        defaults={'full_name': f'Caretaker ({area})', 'type': 'staff'}
    )

    # Create HoldsDesignation if not already present
    obj, created = HoldsDesignation.objects.get_or_create(
        user=user,
        working=user,
        designation=desig,
    )

    if created:
        print(f"  CREATED: {user.username} -> {desig_name} ({area})")
        created_count += 1
    else:
        print(f"  EXISTS:  {user.username} -> {desig_name} ({area})")
        skipped_count += 1

print(f"\nDone! Created: {created_count}, Already existed: {skipped_count}, Errors: {error_count}")
