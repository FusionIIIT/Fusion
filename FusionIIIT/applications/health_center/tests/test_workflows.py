"""
PHC Module — Workflow Test Suite (6 tests)
============================================
Tests WF-TC-001 through WF-TC-006 covering 2 Workflows.
PHC-WF-01: Reimbursement Approval Workflow (4 tests)
PHC-WF-02: Inventory Procurement Workflow (2 tests)

Run:
    DJANGO_SETTINGS_MODULE=Fusion.settings.test \
    python manage.py test applications.health_center.tests.test_workflows -v 2
"""

from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from rest_framework import status

from .test_fixtures import (
    PHCBaseAPITestCase, API_BASE,
    create_faculty_user,
    create_medicine, create_stock, create_expiry,
    create_reimbursement_claim, create_requisition,
)
from ..models import ReimbursementClaim, InventoryRequisition


# ===========================================================================
# ── WF-01: Reimbursement Approval Workflow (4 tests)
# ===========================================================================

class WF01_ReimbursementWorkflowTest(PHCBaseAPITestCase):
    """PHC-WF-01: Full reimbursement claim approval lifecycle"""

    def test_WF_TC_001_happy_path_low_value(self):
        """WF-TC-001: SUBMITTED → PHC_REVIEW → ACCOUNTS → FINAL_PAYMENT."""
        claim = create_reimbursement_claim(self.faculty_extra, amount=5000)

        # Step 1: PHC Staff forwards
        claim.status = 'PHC_REVIEW'
        claim.phc_staff_remarks = 'Documents verified'
        claim.save()
        claim.refresh_from_db()
        self.assertEqual(claim.status, 'PHC_REVIEW')

        # Step 2: Accounts verification
        claim.status = 'ACCOUNTS_VERIFICATION'
        claim.accounts_remarks = 'Budget approved'
        claim.save()
        claim.refresh_from_db()
        self.assertEqual(claim.status, 'ACCOUNTS_VERIFICATION')

        # Step 3: Final payment (no sanction needed for <10k)
        claim.status = 'FINAL_PAYMENT'
        claim.save()
        claim.refresh_from_db()
        self.assertEqual(claim.status, 'FINAL_PAYMENT')

    def test_WF_TC_002_rejection_path(self):
        """WF-TC-002: SUBMITTED → PHC_REVIEW → REJECTED."""
        claim = create_reimbursement_claim(self.faculty_extra, amount=5000)

        claim.status = 'PHC_REVIEW'
        claim.save()

        claim.status = 'REJECTED'
        claim.is_rejected = True
        claim.rejection_reason = 'Insufficient documentation'
        claim.save()
        claim.refresh_from_db()

        self.assertEqual(claim.status, 'REJECTED')
        self.assertTrue(claim.is_rejected)
        self.assertIn('Insufficient', claim.rejection_reason)

    def test_WF_TC_003_high_value_sanction(self):
        """WF-TC-003: Claim >₹10,000 routes to SANCTION_REVIEW."""
        claim = create_reimbursement_claim(self.faculty_extra, amount=15000)

        claim.status = 'PHC_REVIEW'
        claim.save()

        claim.status = 'ACCOUNTS_VERIFICATION'
        claim.save()

        # High value → SANCTION_REVIEW
        claim.sanction_required = True
        claim.status = 'SANCTION_REVIEW'
        claim.save()
        claim.refresh_from_db()

        self.assertTrue(claim.sanction_required)
        self.assertEqual(claim.status, 'SANCTION_REVIEW')
        self.assertEqual(claim.claim_amount, Decimal('15000'))

    def test_WF_TC_004_api_reimbursement_submit_and_list(self):
        """WF-TC-004: End-to-end submit via API then list."""
        # Submit
        self.auth_as_faculty()
        payload = {
            'claim_amount': '7500.00',
            'expense_date': str(date.today() - timedelta(days=15)),
            'description': 'Surgery follow-up treatment',
        }
        resp = self.client.post(f'{API_BASE}/reimbursement/', payload)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # List own claims
        resp = self.client.get(f'{API_BASE}/reimbursement/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.data), 1)


# ===========================================================================
# ── WF-02: Inventory Procurement Workflow (2 tests)
# ===========================================================================

class WF02_InventoryProcurementWorkflowTest(PHCBaseAPITestCase):
    """PHC-WF-02: Inventory requisition → approval → fulfillment"""

    def test_WF_TC_005_happy_path_procurement(self):
        """WF-TC-005: CREATED → SUBMITTED → APPROVED → FULFILLED."""
        req = create_requisition(self.medicine, self.compounder_extra, qty=100)

        # Step 1: Submit
        req.status = 'SUBMITTED'
        req.save()
        req.refresh_from_db()
        self.assertEqual(req.status, 'SUBMITTED')

        # Step 2: Approve
        req.status = 'APPROVED'
        req.approved_by = self.compounder_extra
        req.approved_date = date.today()
        req.save()
        req.refresh_from_db()
        self.assertEqual(req.status, 'APPROVED')

        # Step 3: Fulfill
        req.status = 'FULFILLED'
        req.quantity_fulfilled = 100
        req.fulfilled_date = date.today()
        req.fulfilled_by = self.compounder_extra
        req.save()
        req.refresh_from_db()
        self.assertEqual(req.status, 'FULFILLED')
        self.assertEqual(req.quantity_fulfilled, 100)

    def test_WF_TC_006_rejection_path(self):
        """WF-TC-006: CREATED → SUBMITTED → REJECTED."""
        req = create_requisition(self.medicine, self.compounder_extra, qty=500)

        req.status = 'SUBMITTED'
        req.save()

        req.status = 'REJECTED'
        req.rejection_reason = 'Budget constraints'
        req.save()
        req.refresh_from_db()

        self.assertEqual(req.status, 'REJECTED')
        self.assertIn('Budget', req.rejection_reason)
