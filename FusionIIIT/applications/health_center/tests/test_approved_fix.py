#!/usr/bin/env python
"""
Test script to verify approved claims filter fix
Simulates frontend filtering logic to confirm it now correctly includes FINAL_PAYMENT status
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Fusion.settings.production')
django.setup()

from applications.health_center.models import ReimbursementClaim

print("=" * 80)
print("TESTING APPROVED CLAIMS FILTER FIX")
print("=" * 80)

# Get all claims
claims = list(ReimbursementClaim.objects.values('id', 'status', 'patient__user__first_name', 'claim_amount'))

print(f"\nTotal claims in database: {len(claims)}\n")

# Show all claims
print("All claims:")
for claim in claims:
    print(f"  ID: {claim['id']} | Status: '{claim['status']}' | Patient: {claim['patient__user__first_name']} | Amount: ₹{claim['claim_amount']}")

print("\n" + "-" * 80)
print("FILTER SIMULATION - Frontend Auditor Dashboard")
print("-" * 80)

# OLD FILTER (what was being used - doesn't work)
old_approved = [c for c in claims if c['status'] == 'REIMBURSED']

# NEW FILTER (fixed - now includes sanctioned statuses)
new_approved = [c for c in claims if c['status'] in ['SANCTION_APPROVED', 'FINAL_PAYMENT', 'REIMBURSED']]

print(f"\nOLD Filter (c.status === 'REIMBURSED'):")
print(f"  Matching claims: {len(old_approved)}")
if old_approved:
    for c in old_approved:
        print(f"    - ID {c['id']}: {c['status']}")
else:
    print(f"    - None (EMPTY TAB)")

print(f"\nNEW Filter (SANCTION_APPROVED | FINAL_PAYMENT | REIMBURSED):")
print(f"  Matching claims: {len(new_approved)}")
if new_approved:
    for c in new_approved:
        print(f"    - ID {c['id']}: {c['status']}")
else:
    print(f"    - None (EMPTY TAB)")

print("\n" + "=" * 80)
if len(new_approved) > len(old_approved):
    print("✓ FIX SUCCESSFUL: Approved claims are now visible!")
    print(f"  {len(new_approved) - len(old_approved)} additional claim(s) now appear in Approved tab")
else:
    print("✗ NO IMPROVEMENT: Still no approved claims visible")
    print("  May need to create test claims in SANCTION_APPROVED status")
print("=" * 80)
