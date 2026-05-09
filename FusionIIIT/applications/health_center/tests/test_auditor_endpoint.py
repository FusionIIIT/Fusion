"""
Quick test script to verify auditor endpoint works
Run with: python manage.py shell < applications/health_center/test_auditor_endpoint.py
"""

from django.test import Client
from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo
from applications.health_center.models import ReimbursementClaim
import json

# Create test client
client = Client()

print("\n" + "="*60)
print("Testing Auditor Reimbursement Claims Endpoint")
print("="*60)

# Try to test the endpoint
try:
    # Get or create auditor user
    auditor_user, created = User.objects.get_or_create(
        username='test_auditor',
        defaults={
            'email': 'auditor@test.com',
            'first_name': 'Test',
            'last_name': ' Auditor'
        }
    )
    
    if created:
        print(f"\n✓ Created test auditor user: {auditor_user.username}")
    else:
        print(f"\n✓ Using existing test auditor user: {auditor_user.username}")
    
    # Get or create ExtraInfo for auditor
    extra_info, created = ExtraInfo.objects.get_or_create(
        user=auditor_user,
        defaults={
            'designation': 'auditor',
            'user_type': 'AUDITOR',
            'profile_image': ''
        }
    )
    
    if created:
        print(f"✓ Created ExtraInfo for auditor")
    else:
        print(f"✓ Using existing ExtraInfo for auditor")
    
    # Test endpoint without auth (should fail with 403)
    print("\n--- Test 1: GET without authentication ---")
    response = client.get('/healthcenter/api/phc/auditor/reimbursement-claims/')
    print(f"Status: {response.status_code} (Expected: 401 or 403)")
    if response.content:
        try:
            data = json.loads(response.content)
            print(f"Response: {data}")
        except:
            print(f"Response: {response.content[:100]}")
    
    # Check for claims with PHC_REVIEW status
    phc_review_claims = ReimbursementClaim.objects.filter(status='PHC_REVIEW')
    print(f"\n--- Claims in PHC_REVIEW status: {phc_review_claims.count()} ---")
    for claim in phc_review_claims[:3]:
        print(f"  - Claim #{claim.id}: {claim.status} (Patient: {claim.patient_id})")
        if claim.patient and claim.patient.user:
            print(f"    Patient Name: {claim.patient.user.get_full_name()}")
    
    print("\n✓ Test script completed successfully")
    
except Exception as e:
    print(f"\n✗ Error during testing: {str(e)}")
    import traceback
    traceback.print_exc()

print("="*60 + "\n")
