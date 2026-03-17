"""
Fix existing designation names from underscore to space format.
This script corrects mismatched designation names that prevent role checks from working.

Run with:
  python manage.py shell < fix_designation_names.py
"""

from applications.globals.models import Designation, HoldsDesignation

print("Fixing Designation names...")

# Fix placement_officer -> placement officer
old_desig = Designation.objects.filter(name='placement_officer').first()
if old_desig:
    # Check if new one already exists
    new_desig, _ = Designation.objects.get_or_create(
        name='placement officer',
        defaults={
            'full_name': 'Placement Officer',
            'type': 'administrative'
        }
    )

    # Migrate all HoldsDesignation references from old to new
    count = HoldsDesignation.objects.filter(designation=old_desig).count()
    HoldsDesignation.objects.filter(designation=old_desig).update(designation=new_desig)

    # Delete old designation
    old_desig.delete()
    print(f"  ✓ Migrated {count} HoldsDesignation records from 'placement_officer' to 'placement officer'")
    print(f"  ✓ Deleted old 'placement_officer' designation")
else:
    print("  ℹ No 'placement_officer' designation found (already fixed)")

# Verify new one exists
final_desig, created = Designation.objects.get_or_create(
    name='placement officer',
    defaults={
        'full_name': 'Placement Officer',
        'type': 'administrative'
    }
)
if created:
    print("  ✓ Created new 'placement officer' designation")
else:
    print("  ✓ 'placement officer' designation exists and is correct")

print("\nFix completed. Placement officers should now have access to create postings.")

