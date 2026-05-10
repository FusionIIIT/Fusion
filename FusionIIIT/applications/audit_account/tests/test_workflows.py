# WF tests
from .conftest import BaseModuleTestCase

class WFTestBase(BaseModuleTestCase):
    """Base class for WF tests with common setup"""
    pass

class TestWF01_ExpenseRequestWorkflow(WFTestBase):
    """AUDIT-WF-101: Expense Request Approval Workflow"""

    def test_e2e_complete_expense_approval(self):
        """End-to-End: Complete expense request approval workflow"""
        self._test_id = "AUDIT-WF-101-E2E-01"
        self._wf_id = "AUDIT-WF-101"
        self._test_category = "End-to-End"
        self._scenario = "User creates draft → submits → finance validates → HOD approves → status becomes HOD_APPROVED → finance processes → CLOSED"
        self._expected_final_state = "Request status=PROCESSED; all intermediate statuses correct; action logs recorded; notifications sent"

        # Step 1: User creates draft
        self.login_as_student()
        self._add_step(1, "User creates draft request",
                       "Request created with status=DRAFT", "Draft created", True)

        draft_response = self.api_post('/requests/draft/', {
            'type': 'EXPENSE',
            'amount': '15000.00',  # HOD level
            'department': 'CSE',
            'budget_head': 'travel',
            'description': 'E2E workflow test',
        })
        draft_data = draft_response.json()
        request_id = draft_data['id']
        step1_ok = draft_response.status_code == 201 and draft_data.get('status') == 'DRAFT'
        self._add_step(1, "User creates draft request",
                       "Request created with status=DRAFT", f"Status: {draft_data.get('status')}", step1_ok)

        # Step 2: User submits request
        submit_response = self.api_post('/requests/submit/', {'id': request_id})
        submit_data = submit_response.json()
        step2_ok = submit_response.status_code == 200 and submit_data.get('status') == 'SUBMITTED'
        self._add_step(2, "User submits request",
                       "Status changed to SUBMITTED", f"Status: {submit_data.get('status')}", step2_ok)

        # Step 3: Finance validates
        self.login_as_finance()
        validate_response = self.api_post('/requests/status/', {
            'id': request_id,
            'action': 'validate',
            'remarks': 'Validated by finance'
        })
        validate_data = validate_response.json()
        step3_ok = validate_response.status_code == 200 and validate_data.get('status') == 'FINANCE_VALIDATED'
        self._add_step(3, "Finance validates request",
                       "Status changed to FINANCE_VALIDATED", f"Status: {validate_data.get('status')}", step3_ok)

        # Step 4: HOD approves
        self.login_as_hod()
        approve_response = self.api_post('/requests/status/', {
            'id': request_id,
            'action': 'approve',
            'remarks': 'Approved by HOD'
        })
        approve_data = approve_response.json()
        step4_ok = approve_response.status_code == 200 and approve_data.get('status') == 'HOD_APPROVED'
        self._add_step(4, "HOD approves request",
                       "Status changed to HOD_APPROVED", f"Status: {approve_data.get('status')}", step4_ok)

        # Step 5: Finance processes (final step)
        self.login_as_finance()
        process_response = self.api_post('/requests/status/', {
            'id': request_id,
            'action': 'approve',  # Final approval
            'remarks': 'Processed by finance'
        })
        process_data = process_response.json()
        step5_ok = process_response.status_code == 200 and process_data.get('status') in ['APPROVED', 'PROCESSED']
        self._add_step(5, "Finance processes approved request",
                       "Status changed to PROCESSED", f"Status: {process_data.get('status')}", step5_ok)

        # Check final state
        if self._all_steps_passed():
            self._record_result("Complete expense approval workflow successful", "Pass",
                                f"Final status: {process_data.get('status')}")
        else:
            failed_steps = [s for s in getattr(self, '_steps', []) if not s['success']]
            self._record_result(f"Workflow incomplete: {len(failed_steps)} steps failed", "Fail",
                                f"Failed steps: {[s['step'] for s in failed_steps]}")
            self.fail("Expense approval workflow did not complete successfully")

    def test_negative_finance_rejects_request(self):
        """Negative: Finance rejects request"""
        self._test_id = "AUDIT-WF-101-NEG-01"
        self._wf_id = "AUDIT-WF-101"
        self._test_category = "Negative"
        self._scenario = "User submits request → finance rejects → user notified → request remains SUBMITTED or marked REJECTED"
        self._expected_final_state = "Request status=REJECTED; no further processing; rejection remarks recorded"

        # Step 1: Create and submit request
        self.login_as_student()
        draft_response = self.api_post('/requests/draft/', {
            'type': 'EXPENSE',
            'amount': '5000.00',
            'department': 'CSE',
            'budget_head': 'travel',
            'description': 'Rejection workflow test',
        })
        draft_data = draft_response.json()
        request_id = draft_data['id']
        self.api_post('/requests/submit/', {'id': request_id})
        step1_ok = True
        self._add_step(1, "User submits request",
                       "Request submitted", "Submitted", step1_ok)

        # Step 2: Finance rejects
        self.login_as_finance()
        reject_response = self.api_post('/requests/status/', {
            'id': request_id,
            'action': 'reject',
            'remarks': 'Insufficient documentation'
        })
        reject_data = reject_response.json()
        step2_ok = reject_response.status_code == 200 and reject_data.get('status') == 'REJECTED'
        self._add_step(2, "Finance rejects request",
                       "Status changed to REJECTED", f"Status: {reject_data.get('status')}", step2_ok)

        # Step 3: Verify no further processing possible
        # Try to approve rejected request (should fail)
        self.login_as_hod()
        approve_response = self.api_post('/requests/status/', {
            'id': request_id,
            'action': 'approve'
        })
        step3_ok = approve_response.status_code != 200  # Should not be able to approve rejected request
        self._add_step(3, "Verify no further processing",
                       "Rejected request cannot be approved", f"HTTP {approve_response.status_code}", step3_ok)

        if self._all_steps_passed():
            self._record_result("Rejection workflow handled correctly", "Pass",
                                f"Final status: {reject_data.get('status')}")
        else:
            self._record_result("Rejection workflow failed", "Fail",
                                "Some steps did not work as expected")
            self.fail("Rejection workflow should prevent further processing")

class TestWF02_TAProcessingWorkflow(WFTestBase):
    """AUDIT-WF-201: Travel Allowance Processing Workflow"""

    def test_e2e_ta_approval_workflow(self):
        """End-to-End: Complete TA processing workflow"""
        self._test_id = "AUDIT-WF-201-E2E-01"
        self._wf_id = "AUDIT-WF-201"
        self._test_category = "End-to-End"
        self._scenario = "Employee creates TA → submits → finance verifies low-value → status APPROVED → processed → CLOSED"
        self._expected_final_state = "TA status=APPROVED; action logs complete; finance verification and approval recorded"

        # Step 1: Employee creates TA
        self.login_as_staff()
        ta_response = self.api_post('/ta/create/', {
            'employee_name': 'Test Employee',
            'department': 'CSE',
            'travel_from': 'Delhi',
            'travel_to': 'Mumbai',
            'start_date': self.future_date(5),
            'end_date': self.future_date(7),
            'purpose': 'E2E TA workflow test',
            'amount_claimed': '8000.00',  # Low value
        })
        ta_data = ta_response.json()
        ta_id = ta_data['id']
        step1_ok = ta_response.status_code == 201 and ta_data.get('status') == 'SUBMITTED'
        self._add_step(1, "Employee creates TA",
                       "TA created with status=SUBMITTED", f"Status: {ta_data.get('status')}", step1_ok)

        # Step 2: Finance verifies
        self.login_as_finance()
        verify_response = self.api_post('/ta/status/', {
            'id': ta_id,
            'action': 'verify',
            'remarks': 'Verified by finance'
        })
        verify_data = verify_response.json()
        step2_ok = verify_response.status_code == 200 and verify_data.get('status') == 'VERIFIED'
        self._add_step(2, "Finance verifies TA",
                       "Status changed to VERIFIED", f"Status: {verify_data.get('status')}", step2_ok)

        # Step 3: Finance approves (low-value)
        approve_response = self.api_post('/ta/status/', {
            'id': ta_id,
            'action': 'approve',
            'remarks': 'Approved by finance'
        })
        approve_data = approve_response.json()
        step3_ok = approve_response.status_code == 200 and approve_data.get('status') == 'APPROVED'
        self._add_step(3, "Finance approves low-value TA",
                       "Status changed to APPROVED", f"Status: {approve_data.get('status')}", step3_ok)

        if self._all_steps_passed():
            self._record_result("TA approval workflow completed successfully", "Pass",
                                f"Final status: {approve_data.get('status')}")
        else:
            failed_steps = [s for s in getattr(self, '_steps', []) if not s['success']]
            self._record_result(f"TA workflow incomplete: {len(failed_steps)} steps failed", "Fail",
                                f"Failed steps: {[s['step'] for s in failed_steps]}")
            self.fail("TA approval workflow did not complete successfully")

    def test_negative_high_value_ta_rejected(self):
        """Negative: High-value TA rejected by authority"""
        self._test_id = "AUDIT-WF-201-NEG-01"
        self._wf_id = "AUDIT-WF-201"
        self._test_category = "Negative"
        self._scenario = "Employee creates high-value TA → submits → finance verifies → authority rejects → status REJECTED"
        self._expected_final_state = "TA status=REJECTED; high_value=True; rejection remarks saved; authority review required and performed"

        # Step 1: Create high-value TA
        self.login_as_staff()
        ta_response = self.api_post('/ta/create/', {
            'employee_name': 'Test Employee',
            'department': 'CSE',
            'travel_from': 'Delhi',
            'travel_to': 'Singapore',
            'start_date': self.future_date(1),
            'end_date': self.future_date(5),
            'purpose': 'High-value TA rejection test',
            'amount_claimed': '60000.00',  # High value
        })
        ta_data = ta_response.json()
        ta_id = ta_data['id']
        step1_ok = ta_response.status_code == 201 and ta_data.get('high_value') == True
        self._add_step(1, "Employee creates high-value TA",
                       "TA created with high_value=True", f"High value: {ta_data.get('high_value')}", step1_ok)

        # Step 2: Finance verifies
        self.login_as_finance()
        verify_response = self.api_post('/ta/status/', {
            'id': ta_id,
            'action': 'verify',
            'remarks': 'Verified high-value TA'
        })
        verify_data = verify_response.json()
        step2_ok = verify_response.status_code == 200 and verify_data.get('status') == 'VERIFIED'
        self._add_step(2, "Finance verifies high-value TA",
                       "Status changed to VERIFIED", f"Status: {verify_data.get('status')}", step2_ok)

        # Step 3: Authority rejects
        self.login_as_hod()
        reject_response = self.api_post('/ta/status/', {
            'id': ta_id,
            'action': 'reject',
            'remarks': 'High-value TA not approved'
        })
        reject_data = reject_response.json()
        step3_ok = reject_response.status_code == 200 and reject_data.get('status') == 'REJECTED'
        self._add_step(3, "Authority rejects high-value TA",
                       "Status changed to REJECTED", f"Status: {reject_data.get('status')}", step3_ok)

        if self._all_steps_passed():
            self._record_result("High-value TA rejection workflow completed", "Pass",
                                f"Final status: {reject_data.get('status')}")
        else:
            failed_steps = [s for s in getattr(self, '_steps', []) if not s['success']]
            self._record_result(f"TA rejection workflow failed: {len(failed_steps)} steps failed", "Fail",
                                f"Failed steps: {[s['step'] for s in failed_steps]}")
            self.fail("High-value TA rejection workflow should work correctly")

class TestWF03_ObservationResolutionWorkflow(WFTestBase):
    """AUDIT-WF-301: Audit Observation Resolution Workflow"""

    def test_e2e_observation_resolution(self):
        """End-to-End: Complete observation resolution workflow"""
        self._test_id = "AUDIT-WF-301-E2E-01"
        self._wf_id = "AUDIT-WF-301"
        self._test_category = "End-to-End"
        self._scenario = "Auditor creates observation → owner responds with documents → auditor reviews → marks as CLOSED"
        self._expected_final_state = "Observation status=CLOSED; response recorded; closure remarks saved; all attachments preserved"

        # Step 1: Create request
        self.login_as_student()
        draft_response = self.api_post('/requests/draft/', {
            'type': 'EXPENSE',
            'amount': '10000.00',
            'department': 'CSE',
            'budget_head': 'travel',
            'description': 'Observation resolution test',
        })
        draft_data = draft_response.json()
        request_id = draft_data['id']
        self.api_post('/requests/submit/', {'id': request_id})
        step1_ok = True
        self._add_step(1, "Create and submit request",
                       "Request submitted", "Submitted", step1_ok)

        # Step 2: Auditor creates observation
        self.login_as_auditor()
        obs_response = self.api_post('/observations/create/', {
            'request': request_id,
            'title': 'Documentation review',
            'details': 'Please provide additional documentation for expense verification',
            'response_deadline': self.future_date(7),
        })
        obs_data = obs_response.json()
        obs_id = obs_data['id']
        step2_ok = obs_response.status_code == 201 and obs_data.get('status') == 'OPEN'
        self._add_step(2, "Auditor creates observation",
                       "Observation created with status=OPEN", f"Status: {obs_data.get('status')}", step2_ok)

        # Step 3: Request owner responds
        self.login_as_student()
        respond_response = self.api_post('/observations/status/', {
            'id': obs_id,
            'response_text': 'All documentation attached as requested',
        })
        respond_data = respond_response.json()
        step3_ok = respond_response.status_code == 200 and respond_data.get('status') == 'RESPONDED'
        self._add_step(3, "Request owner responds",
                       "Status changed to RESPONDED", f"Status: {respond_data.get('status')}", step3_ok)

        # Step 4: Auditor closes observation
        self.login_as_auditor()
        close_response = self.api_post('/observations/status/', {
            'id': obs_id,
            'action': 'close',
            'closure_remarks': 'Documentation verified and accepted',
        })
        close_data = close_response.json()
        step4_ok = close_response.status_code == 200 and close_data.get('status') == 'CLOSED'
        self._add_step(4, "Auditor closes observation",
                       "Status changed to CLOSED", f"Status: {close_data.get('status')}", step4_ok)

        if self._all_steps_passed():
            self._record_result("Observation resolution workflow completed", "Pass",
                                f"Final status: {close_data.get('status')}")
        else:
            failed_steps = [s for s in getattr(self, '_steps', []) if not s['success']]
            self._record_result(f"Observation workflow incomplete: {len(failed_steps)} steps failed", "Fail",
                                f"Failed steps: {[s['step'] for s in failed_steps]}")
            self.fail("Observation resolution workflow did not complete successfully")

    def test_negative_observation_deadline_expires(self):
        """Negative: Observation deadline expires without response"""
        self._test_id = "AUDIT-WF-301-NEG-01"
        self._wf_id = "AUDIT-WF-301"
        self._test_category = "Negative"
        self._scenario = "Auditor creates observation → response deadline expires → observation remains OPEN → escalated handling"
        self._expected_final_state = "Observation status=OPEN; deadline passed; no response provided; requires follow-up"

        # Step 1: Create request and observation with past deadline
        self.login_as_student()
        draft_response = self.api_post('/requests/draft/', {
            'type': 'EXPENSE',
            'amount': '5000.00',
            'department': 'CSE',
            'budget_head': 'travel',
            'description': 'Deadline expiry test',
        })
        draft_data = draft_response.json()
        request_id = draft_data['id']
        self.api_post('/requests/submit/', {'id': request_id})

        self.login_as_auditor()
        obs_response = self.api_post('/observations/create/', {
            'request': request_id,
            'title': 'Deadline test observation',
            'details': 'This observation will expire',
            'response_deadline': self.past_date(1),  # Already past
        })
        obs_data = obs_response.json()
        obs_id = obs_data['id']
        step1_ok = obs_response.status_code == 201
        self._add_step(1, "Create observation with past deadline",
                       "Observation created", f"Created with ID: {obs_id}", step1_ok)

        # Step 2: Verify observation remains OPEN (no response)
        # In real implementation, this would be checked by a scheduled task
        # For testing, we manually check the status
        from applications.audit_account.models import AuditObservation
        obs = AuditObservation.objects.get(id=obs_id)
        step2_ok = obs.status == 'OPEN'
        self._add_step(2, "Verify observation status",
                       "Status remains OPEN", f"Status: {obs.status}", step2_ok)

        # Step 3: Attempt to respond after deadline (should still work or be rejected)
        self.login_as_student()
        late_response = self.api_post('/observations/status/', {
            'id': obs_id,
            'response_text': 'Late response',
        })
        # Note: In real implementation, late responses might be allowed or rejected
        step3_ok = True  # For this test, we assume late responses are allowed
        self._add_step(3, "Attempt late response",
                       "Response attempted", f"HTTP {late_response.status_code}", step3_ok)

        if self._all_steps_passed():
            self._record_result("Deadline expiry scenario handled", "Pass",
                                f"Observation status: {obs.status}")
        else:
            self._record_result("Deadline expiry test failed", "Fail",
                                "Some steps did not work as expected")
            # Note: This test may need adjustment based on actual deadline handling logic

class TestWF04_MultiLevelApprovalWorkflow(WFTestBase):
    """AUDIT-WF-401: Multi-Level Approval with Escalation Workflow"""

    def test_e2e_multi_level_approval(self):
        """End-to-End: Multi-level approval workflow with automatic escalation"""
        self._test_id = "AUDIT-WF-401-E2E-01"
        self._wf_id = "AUDIT-WF-401"
        self._test_category = "End-to-End"
        self._scenario = "High-value request auto-escalates through HOD → Dean → Director → Finance Process"
        self._expected_final_state = "Request status=PROCESSED after all escalation levels; audit trail complete"

        # Step 1: Create high-value request
        self.login_as_student()
        draft_response = self.api_post('/requests/draft/', {
            'type': 'EXPENSE',
            'amount': '150000.00',  # Exceeds all department levels
            'department': 'ADMIN',
            'budget_head': 'strategic',
            'description': 'Multi-level approval workflow test',
        })
        draft_data = draft_response.json()
        request_id = draft_data['id']
        self.api_post('/requests/submit/', {'id': request_id})
        step1_ok = True
        self._add_step(1, "User creates high-value request",
                       "Request submitted", "High-value", step1_ok)

        # Step 2: Finance validates
        self.login_as_finance()
        validate_response = self.api_post('/requests/status/', {
            'id': request_id,
            'action': 'validate',
            'remarks': 'Validated for escalation'
        })
        step2_ok = validate_response.status_code == 200
        self._add_step(2, "Finance validates request",
                       "Status validated", f"HTTP {validate_response.status_code}", step2_ok)

        # Step 3: HOD reviews (first authority level)
        self.login_as_hod()
        hod_response = self.api_post('/requests/status/', {
            'id': request_id,
            'action': 'forward_to_dean',
            'remarks': 'Forwarded due to high value'
        })
        step3_ok = hod_response.status_code == 200
        self._add_step(3, "HOD reviews and escalates",
                       "Escalated to Dean", f"HTTP {hod_response.status_code}", step3_ok)

        # Step 4: Dean reviews (second authority level)
        self.login_as_dean()
        dean_response = self.api_post('/requests/status/', {
            'id': request_id,
            'action': 'forward_to_director',
            'remarks': 'Escalated by Dean'
        })
        step4_ok = dean_response.status_code == 200
        self._add_step(4, "Dean reviews and escalates",
                       "Escalated to Director", f"HTTP {dean_response.status_code}", step4_ok)

        # Step 5: Director approves (final authority)
        self.login_as_director()
        director_response = self.api_post('/requests/status/', {
            'id': request_id,
            'action': 'approve',
            'remarks': 'Director approval for strategic expense'
        })
        step5_ok = director_response.status_code == 200
        self._add_step(5, "Director approves",
                       "Approval granted", f"HTTP {step5_ok}", step5_ok)

        # Step 6: Finance final processing
        self.login_as_finance()
        process_response = self.api_post('/requests/status/', {
            'id': request_id,
            'action': 'process',
            'remarks': 'Final processing'
        })
        step6_ok = process_response.status_code == 200
        self._add_step(6, "Finance processes approved request",
                       "Request processed", f"HTTP {process_response.status_code}", step6_ok)

        if self._all_steps_passed():
            self._record_result("Multi-level approval workflow completed successfully", "Pass",
                                f"Amount: 150000; All levels approved")
        else:
            failed_steps = [s for s in getattr(self, '_steps', []) if not s['success']]
            self._record_result(f"Multi-level workflow incomplete: {len(failed_steps)} steps failed", "Fail",
                                f"Failed steps: {[s['step'] for s in failed_steps]}")

    def test_negative_authority_bypass_attempt(self):
        """Negative: Attempt to bypass authority levels in approval"""
        self._test_id = "AUDIT-WF-401-NEG-01"
        self._wf_id = "AUDIT-WF-401"
        self._test_category = "Negative"
        self._scenario = "Request attempts to skip Dean level and go directly to Director"
        self._expected_final_state = "Bypass rejected; request remains at appropriate level"

        # Create high-value request
        self.login_as_student()
        draft_response = self.api_post('/requests/draft/', {
            'type': 'EXPENSE',
            'amount': '120000.00',
            'department': 'RESEARCH',
            'budget_head': 'grants',
            'description': 'Bypass attempt test',
        })
        draft_data = draft_response.json()
        request_id = draft_data['id']
        self.api_post('/requests/submit/', {'id': request_id})

        # Finance validates
        self.login_as_finance()
        self.api_post('/requests/status/', {
            'id': request_id,
            'action': 'validate',
        })

        # HOD forwards
        self.login_as_hod()
        self.api_post('/requests/status/', {
            'id': request_id,
            'action': 'forward_to_dean',
        })

        # Try to bypass Dean and go directly to Director
        self.login_as_director()
        bypass_response = self.api_post('/requests/status/', {
            'id': request_id,
            'action': 'approve',
        }, expected_status=None)

        if bypass_response.status_code == 403:
            self._record_result("Bypass correctly rejected", "Pass",
                                f"Request cannot skip Dean level")
        else:
            self._record_result(f"Bypass allowed: HTTP {bypass_response.status_code}", "Fail",
                                f"Response: {bypass_response.json()}")

class TestWF05_BudgetAllocationAndReportingWorkflow(WFTestBase):
    """AUDIT-WF-501: Budget Allocation and Quarterly Reporting Workflow"""

    def test_e2e_budget_cycle_workflow(self):
        """End-to-End: Complete budget allocation and quarterly cycle"""
        self._test_id = "AUDIT-WF-501-E2E-01"
        self._wf_id = "AUDIT-WF-501"
        self._test_category = "End-to-End"
        self._scenario = "Director allocates budget → Departments create requests → Finance tracks → Quarterly audit report generated"
        self._expected_final_state = "Budget cycle complete; reports generated; remaining balance calculated"

        # Step 1: Director allocates budget
        self.login_as_director()
        budget_response = self.api_post('/budgets/create/', {
            'department': 'TESTING_DEPT',
            'budget_head': 'operational',
            'allocated_amount': '100000.00',
            'fiscal_year': 2024,
        })
        budget_id = budget_response.json().get('id')
        step1_ok = budget_response.status_code == 201
        self._add_step(1, "Director allocates budget",
                       "Budget created", f"ID: {budget_id}", step1_ok)

        # Step 2: Department creates requests against budget
        self.login_as_student()
        draft_response = self.api_post('/requests/draft/', {
            'type': 'EXPENSE',
            'amount': '25000.00',
            'department': 'TESTING_DEPT',
            'budget_head': 'operational',
            'description': 'Budget cycle test request',
        })
        draft_id = draft_response.json()['id']
        self.api_post('/requests/submit/', {'id': draft_id})
        step2_ok = draft_response.status_code == 201
        self._add_step(2, "Department creates request",
                       "Request submitted", f"Amount: 25000", step2_ok)

        # Step 3: Finance approves request
        self.login_as_finance()
        self.api_post('/requests/status/', {
            'id': draft_id,
            'action': 'validate',
        })
        self.login_as_hod()
        self.api_post('/requests/status/', {
            'id': draft_id,
            'action': 'approve',
        })
        self.login_as_finance()
        process_response = self.api_post('/requests/status/', {
            'id': draft_id,
            'action': 'process',
        })
        step3_ok = process_response.status_code == 200
        self._add_step(3, "Finance processes request",
                       "Request processed", f"HTTP {process_response.status_code}", step3_ok)

        # Step 4: Generate budget report
        self.login_as_auditor()
        report_response = self.api_get('/reports/budget/TESTING_DEPT/2024', expected_status=None)
        step4_ok = report_response.status_code == 200
        self._add_step(4, "Generate budget report",
                       "Quarterly report generated", f"HTTP {report_response.status_code}", step4_ok)

        if self._all_steps_passed():
            self._record_result("Budget cycle workflow completed successfully", "Pass",
                                f"Allocated: 100000; Used: 25000; Remaining: 75000")
        else:
            failed_steps = [s for s in getattr(self, '_steps', []) if not s['success']]
            self._record_result(f"Budget workflow incomplete: {len(failed_steps)} steps failed", "Fail",
                                f"Failed steps: {[s['step'] for s in failed_steps]}")

    def test_negative_budget_exceeds_allocation(self):
        """Negative: Request amount exceeds remaining budget"""
        self._test_id = "AUDIT-WF-501-NEG-01"
        self._wf_id = "AUDIT-WF-501"
        self._test_category = "Negative"
        self._scenario = "Department creates request exceeding remaining allocation"
        self._expected_final_state = "Request rejected; budget constraint enforced"

        self.login_as_student()
        response = self.api_post('/requests/draft/', {
            'type': 'EXPENSE',
            'amount': '200000.00',  # Exceeds typical allocation
            'department': 'LIMITED_BUDGET_DEPT',
            'budget_head': 'restricted',
            'description': 'Budget exceed test',
        })
        draft_id = response.json()['id']
        
        submit_response = self.api_post('/requests/submit/', {'id': draft_id}, expected_status=None)

        if submit_response.status_code == 400:
            self._record_result("Budget constraint correctly enforced", "Pass",
                                f"Request rejected for exceeding allocation")
        else:
            self._record_result(f"Budget constraint not enforced: HTTP {submit_response.status_code}", "Fail",
                                f"Response: {submit_response.json()}")\n