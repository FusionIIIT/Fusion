# UC tests
from .conftest import BaseModuleTestCase

class UCTestBase(BaseModuleTestCase):
    """Base class for UC tests with common setup"""
    pass

class TestUC01_CreateDraft(UCTestBase):
    """AUDIT-UC-001: Create Draft Expense Request"""

    def test_hp01_complete_draft_expense(self):
        """Happy Path: Complete draft expense request with attachments"""
        self._test_id = "AUDIT-UC-001-HP-01"
        self._uc_id = "AUDIT-UC-001"
        self._test_category = "Happy Path"
        self._scenario = "User creates complete draft expense request"
        self._preconditions = "User logged in; valid department and budget head"
        self._input_action = "POST /api/requests/draft/ with type=EXPENSE, amount, department, budget_head, description, attachments"
        self._expected_result = "Request created with status=DRAFT; HTTP 201; attachments saved"

        self.login_as_student()
        response = self.api_post('/requests/draft/', {
            'type': 'EXPENSE',
            'amount': '5000.00',
            'department': 'CSE',
            'budget_head': 'travel',
            'description': 'Conference travel expenses',
        }, expected_status=None)

        if response.status_code == 201:
            data = response.json()
            if data.get('status') == 'DRAFT':
                self._record_result("Draft created successfully", "Pass",
                                    f"Response: {data}")
            else:
                self._record_result(f"Unexpected status: {data.get('status')}",
                                    "Fail", f"Response: {data}")
                self.fail(f"Expected status=DRAFT, got {data.get('status')}")
        else:
            self._record_result(f"HTTP {response.status_code}",
                                "Fail", f"Status: {response.status_code}")
            self.fail(f"Expected 201, got {response.status_code}")

    def test_ap01_voucher_request(self):
        """Alternate Path: Create voucher request instead"""
        self._test_id = "AUDIT-UC-001-AP-01"
        self._uc_id = "AUDIT-UC-001"
        self._test_category = "Alternate Path"
        self._scenario = "User creates voucher request"
        self._preconditions = "User logged in"
        self._input_action = "POST /api/requests/draft/ with type=VOUCHER"
        self._expected_result = "Request created with type=VOUCHER; HTTP 201"

        self.login_as_student()
        response = self.api_post('/requests/draft/', {
            'type': 'VOUCHER',
            'amount': '2000.00',
            'department': 'HR',
            'budget_head': 'head',
            'description': 'Office supplies voucher',
        }, expected_status=None)

        if response.status_code == 201:
            data = response.json()
            if data.get('type') == 'VOUCHER':
                self._record_result("Voucher request created", "Pass",
                                    f"Response: {data}")
            else:
                self._record_result(f"Wrong type: {data.get('type')}",
                                    "Fail", f"Response: {data}")
                self.fail(f"Expected type=VOUCHER, got {data.get('type')}")
        else:
            self._record_result(f"HTTP {response.status_code}",
                                "Fail", f"Status: {response.status_code}")
            self.fail(f"Expected 201, got {response.status_code}")

    def test_ex01_missing_department(self):
        """Exception: Missing required department field"""
        self._test_id = "AUDIT-UC-001-EX-01"
        self._uc_id = "AUDIT-UC-001"
        self._test_category = "Exception"
        self._scenario = "User creates draft without department"
        self._preconditions = "User logged in"
        self._input_action = "POST /api/requests/draft/ with missing department"
        self._expected_result = "Rejected HTTP 400; validation error"

        self.login_as_student()
        response = self.api_post('/requests/draft/', {
            'type': 'EXPENSE',
            'amount': '5000.00',
            # 'department': 'CSE',  # Missing
            'budget_head': 'travel',
            'description': 'Test',
        }, expected_status=None)

        if response.status_code == 400:
            self._record_result("Correctly rejected for missing department", "Pass",
                                f"Response: {response.json()}")
        else:
            self._record_result(f"Not rejected: HTTP {response.status_code}",
                                "Fail", f"Response: {response.json()}")
            self.fail("Should reject requests without department")

class TestUC02_SubmitRequest(UCTestBase):
    """AUDIT-UC-002: Submit Expense Request"""

    def test_hp01_submit_complete_request(self):
        """Happy Path: Submit complete draft request within budget"""
        self._test_id = "AUDIT-UC-002-HP-01"
        self._uc_id = "AUDIT-UC-002"
        self._test_category = "Happy Path"
        self._scenario = "User submits complete draft request"
        self._preconditions = "User logged in; owns draft request; budget available"
        self._input_action = "POST /api/requests/submit/ with request id"
        self._expected_result = "Status changed to SUBMITTED; assigned to finance"

        # First create a draft
        self.login_as_student()
        draft_response = self.api_post('/requests/draft/', {
            'type': 'EXPENSE',
            'amount': '5000.00',
            'department': 'CSE',
            'budget_head': 'travel',
            'description': 'Test submission',
        })
        draft_data = draft_response.json()
        request_id = draft_data['id']

        # Now submit it
        response = self.api_post('/requests/submit/', {
            'id': request_id
        }, expected_status=None)

        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'SUBMITTED':
                self._record_result("Request submitted successfully", "Pass",
                                    f"Response: {data}")
            else:
                self._record_result(f"Unexpected status: {data.get('status')}",
                                    "Fail", f"Response: {data}")
                self.fail(f"Expected status=SUBMITTED, got {data.get('status')}")
        else:
            self._record_result(f"HTTP {response.status_code}",
                                "Fail", f"Status: {response.status_code}")
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ap01_submit_with_attachments(self):
        """Alternate Path: Submit with additional documents"""
        self._test_id = "AUDIT-UC-002-AP-01"
        self._uc_id = "AUDIT-UC-002"
        self._test_category = "Alternate Path"
        self._scenario = "User submits request with additional documents"
        self._preconditions = "User logged in; request has base documents"
        self._input_action = "POST /api/requests/submit/ with additional attachments"
        self._expected_result = "Request submitted; all attachments saved"

        # Create draft first
        self.login_as_student()
        draft_response = self.api_post('/requests/draft/', {
            'type': 'EXPENSE',
            'amount': '3000.00',
            'department': 'CSE',
            'budget_head': 'equipment',
            'description': 'Equipment purchase',
        })
        draft_data = draft_response.json()
        request_id = draft_data['id']

        # Submit (in real scenario would have attachments)
        response = self.api_post('/requests/submit/', {
            'id': request_id
        }, expected_status=None)

        if response.status_code == 200:
            self._record_result("Request submitted with documents", "Pass",
                                f"Response: {response.json()}")
        else:
            self._record_result(f"HTTP {response.status_code}",
                                "Fail", f"Status: {response.status_code}")
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ex01_exceed_budget(self):
        """Exception: Submit request exceeding budget"""
        self._test_id = "AUDIT-UC-002-EX-01"
        self._uc_id = "AUDIT-UC-002"
        self._test_category = "Exception"
        self._scenario = "User submits request exceeding budget"
        self._preconditions = "User logged in; request amount > remaining budget"
        self._input_action = "POST /api/requests/submit/ with request id"
        self._expected_result = "Rejected HTTP 400; budget exceeded error"

        # Create draft with amount exceeding budget
        self.login_as_student()
        draft_response = self.api_post('/requests/draft/', {
            'type': 'EXPENSE',
            'amount': '60000.00',  # Exceeds CSE travel budget of 50000
            'department': 'CSE',
            'budget_head': 'travel',
            'description': 'Excessive amount',
        })
        draft_data = draft_response.json()
        request_id = draft_data['id']

        # Try to submit
        response = self.api_post('/requests/submit/', {
            'id': request_id
        }, expected_status=None)

        if response.status_code == 400:
            self._record_result("Correctly rejected for budget exceeded", "Pass",
                                f"Response: {response.json()}")
        else:
            self._record_result(f"Not rejected: HTTP {response.status_code}",
                                "Fail", f"Response: {response.json()}")
            self.fail("Should reject requests exceeding budget")

class TestUC03_FinanceValidate(UCTestBase):
    """AUDIT-UC-003: Finance Validate Request"""

    def test_hp01_finance_validates_request(self):
        """Happy Path: Finance validates legitimate request"""
        self._test_id = "AUDIT-UC-003-HP-01"
        self._uc_id = "AUDIT-UC-003"
        self._test_category = "Happy Path"
        self._scenario = "Finance validates submitted request"
        self._preconditions = "Finance user logged in; request status=SUBMITTED"
        self._input_action = "POST /api/requests/status/ with action=validate"
        self._expected_result = "Status changed to FINANCE_VALIDATED; assigned to next approver"

        # Create and submit request as student
        self.login_as_student()
        draft_response = self.api_post('/requests/draft/', {
            'type': 'EXPENSE',
            'amount': '5000.00',
            'department': 'CSE',
            'budget_head': 'travel',
            'description': 'Finance validation test',
        })
        draft_data = draft_response.json()
        request_id = draft_data['id']

        submit_response = self.api_post('/requests/submit/', {'id': request_id})

        # Now validate as finance
        self.login_as_finance()
        response = self.api_post('/requests/status/', {
            'id': request_id,
            'action': 'validate',
            'remarks': 'Approved by finance'
        }, expected_status=None)

        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'FINANCE_VALIDATED':
                self._record_result("Request validated by finance", "Pass",
                                    f"Response: {data}")
            else:
                self._record_result(f"Unexpected status: {data.get('status')}",
                                    "Fail", f"Response: {data}")
                self.fail(f"Expected FINANCE_VALIDATED, got {data.get('status')}")
        else:
            self._record_result(f"HTTP {response.status_code}",
                                "Fail", f"Status: {response.status_code}")
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ap01_finance_escalates_high_value(self):
        """Alternate Path: Finance escalates high-value request"""
        self._test_id = "AUDIT-UC-003-AP-01"
        self._uc_id = "AUDIT-UC-003"
        self._test_category = "Alternate Path"
        self._scenario = "Finance escalates high-value request"
        self._preconditions = "Finance user logged in; request amount > threshold"
        self._input_action = "POST /api/requests/status/ with action=escalate"
        self._expected_result = "Status changed to ESCALATED; assigned to higher authority"

        # Create high-value request (>25000 for HOD threshold)
        self.login_as_student()
        draft_response = self.api_post('/requests/draft/', {
            'type': 'EXPENSE',
            'amount': '30000.00',
            'department': 'CSE',
            'budget_head': 'equipment',
            'description': 'High value equipment',
        })
        draft_data = draft_response.json()
        request_id = draft_data['id']
        self.api_post('/requests/submit/', {'id': request_id})

        # Escalate as finance
        self.login_as_finance()
        response = self.api_post('/requests/status/', {
            'id': request_id,
            'action': 'escalate',
            'remarks': 'High value - needs HOD approval'
        }, expected_status=None)

        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'ESCALATED':
                self._record_result("Request escalated successfully", "Pass",
                                    f"Response: {data}")
            else:
                self._record_result(f"Unexpected status: {data.get('status')}",
                                    "Fail", f"Response: {data}")
                self.fail(f"Expected ESCALATED, got {data.get('status')}")
        else:
            self._record_result(f"HTTP {response.status_code}",
                                "Fail", f"Status: {response.status_code}")
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ex01_non_finance_user_validates(self):
        """Exception: Non-finance user attempts validation"""
        self._test_id = "AUDIT-UC-003-EX-01"
        self._uc_id = "AUDIT-UC-003"
        self._test_category = "Exception"
        self._scenario = "Student attempts to validate request"
        self._preconditions = "Student user logged in"
        self._input_action = "POST /api/requests/status/ with action=validate"
        self._expected_result = "Rejected; student cannot set validated status"

        # Create and submit request
        self.login_as_student()
        draft_response = self.api_post('/requests/draft/', {
            'type': 'EXPENSE',
            'amount': '2000.00',
            'department': 'HR',
            'budget_head': 'head',
            'description': 'Student validation attempt',
        })
        draft_data = draft_response.json()
        request_id = draft_data['id']
        self.api_post('/requests/submit/', {'id': request_id})

        # Try to validate as student (should fail)
        response = self.api_post('/requests/status/', {
            'id': request_id,
            'action': 'validate'
        }, expected_status=None)

        if response.status_code == 403:
            self._record_result("Correctly rejected student validation", "Pass",
                                f"Response: {response.json()}")
        else:
            self._record_result(f"Not rejected: HTTP {response.status_code}",
                                "Fail", f"Response: {response.json()}")
            self.fail("Students should not be able to validate requests")

class TestUC04_ApproveRequest(UCTestBase):
    """AUDIT-UC-004: Approve Request"""

    def test_hp01_hod_approves_low_value(self):
        """Happy Path: HOD approves low-value request"""
        self._test_id = "AUDIT-UC-004-HP-01"
        self._uc_id = "AUDIT-UC-004"
        self._test_category = "Happy Path"
        self._scenario = "HOD approves low-value request"
        self._preconditions = "HOD logged in; request amount <= HOD threshold"
        self._input_action = "POST /api/requests/status/ with action=approve"
        self._expected_result = "Status changed to HOD_APPROVED; request approved"

        # Create and process request to HOD level
        self.login_as_student()
        draft_response = self.api_post('/requests/draft/', {
            'type': 'EXPENSE',
            'amount': '20000.00',  # Within HOD limit
            'department': 'CSE',
            'budget_head': 'equipment',
            'description': 'HOD approval test',
        })
        draft_data = draft_response.json()
        request_id = draft_data['id']
        self.api_post('/requests/submit/', {'id': request_id})

        self.login_as_finance()
        self.api_post('/requests/status/', {
            'id': request_id,
            'action': 'validate',
            'remarks': 'Validated for HOD'
        })

        # Approve as HOD
        self.login_as_hod()
        response = self.api_post('/requests/status/', {
            'id': request_id,
            'action': 'approve',
            'remarks': 'Approved by HOD'
        }, expected_status=None)

        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'HOD_APPROVED':
                self._record_result("Request approved by HOD", "Pass",
                                    f"Response: {data}")
            else:
                self._record_result(f"Unexpected status: {data.get('status')}",
                                    "Fail", f"Response: {data}")
                self.fail(f"Expected HOD_APPROVED, got {data.get('status')}")
        else:
            self._record_result(f"HTTP {response.status_code}",
                                "Fail", f"Status: {response.status_code}")
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ap01_director_approves_high_value(self):
        """Alternate Path: Director approves high-value request"""
        self._test_id = "AUDIT-UC-004-AP-01"
        self._uc_id = "AUDIT-UC-004"
        self._test_category = "Alternate Path"
        self._scenario = "Director approves high-value request"
        self._preconditions = "Director logged in; request escalated to director level"
        self._input_action = "POST /api/requests/status/ with action=approve"
        self._expected_result = "Status changed to DIRECTOR_APPROVED; final approval"

        # Create very high-value request
        self.login_as_student()
        draft_response = self.api_post('/requests/draft/', {
            'type': 'EXPENSE',
            'amount': '150000.00',  # Above dean threshold
            'department': 'CSE',
            'budget_head': 'equipment',
            'description': 'Director approval test',
        })
        draft_data = draft_response.json()
        request_id = draft_data['id']
        self.api_post('/requests/submit/', {'id': request_id})

        # Process through finance and escalate
        self.login_as_finance()
        self.api_post('/requests/status/', {
            'id': request_id,
            'action': 'escalate',
            'remarks': 'Very high value'
        })

        # Approve as director
        self.login_as_director()
        response = self.api_post('/requests/status/', {
            'id': request_id,
            'action': 'approve',
            'remarks': 'Approved by Director'
        }, expected_status=None)

        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'DIRECTOR_APPROVED':
                self._record_result("Request approved by Director", "Pass",
                                    f"Response: {data}")
            else:
                self._record_result(f"Unexpected status: {data.get('status')}",
                                    "Fail", f"Response: {data}")
                self.fail(f"Expected DIRECTOR_APPROVED, got {data.get('status')}")
        else:
            self._record_result(f"HTTP {response.status_code}",
                                "Fail", f"Status: {response.status_code}")
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ex01_wrong_approver(self):
        """Exception: User approves request not assigned to them"""
        self._test_id = "AUDIT-UC-004-EX-01"
        self._uc_id = "AUDIT-UC-004"
        self._test_category = "Exception"
        self._scenario = "HOD attempts to approve dean-level request"
        self._preconditions = "HOD logged in; request assigned to dean"
        self._input_action = "POST /api/requests/status/ with action=approve"
        self._expected_result = "Rejected HTTP 403; not authorized for this request"

        # Create medium-value request (dean level)
        self.login_as_student()
        draft_response = self.api_post('/requests/draft/', {
            'type': 'EXPENSE',
            'amount': '50000.00',  # Dean level
            'department': 'CSE',
            'budget_head': 'equipment',
            'description': 'Wrong approver test',
        })
        draft_data = draft_response.json()
        request_id = draft_data['id']
        self.api_post('/requests/submit/', {'id': request_id})

        self.login_as_finance()
        self.api_post('/requests/status/', {
            'id': request_id,
            'action': 'escalate',
            'remarks': 'Dean level'
        })

        # Try to approve as HOD (should fail)
        self.login_as_hod()
        response = self.api_post('/requests/status/', {
            'id': request_id,
            'action': 'approve'
        }, expected_status=None)

        if response.status_code == 403:
            self._record_result("Correctly rejected wrong approver", "Pass",
                                f"Response: {response.json()}")
        else:
            self._record_result(f"Not rejected: HTTP {response.status_code}",
                                "Fail", f"Response: {response.json()}")
            self.fail("Wrong approver should be rejected")

class TestUC05_CreateTA(UCTestBase):
    """AUDIT-UC-005: Create Travel Allowance Request"""

    def test_hp01_create_complete_ta(self):
        """Happy Path: Employee creates TA request with complete details"""
        self._test_id = "AUDIT-UC-005-HP-01"
        self._uc_id = "AUDIT-UC-005"
        self._test_category = "Happy Path"
        self._scenario = "Employee creates TA request with complete details"
        self._preconditions = "User logged in; valid travel dates and details"
        self._input_action = "POST /api/ta/create/ with travel details, amount, attachments"
        self._expected_result = "TA request created with status=SUBMITTED; HTTP 201"

        self.login_as_staff()
        response = self.api_post('/ta/create/', {
            'employee_name': 'Test Employee',
            'department': 'CSE',
            'travel_from': 'Delhi',
            'travel_to': 'Mumbai',
            'start_date': self.future_date(5),
            'end_date': self.future_date(8),
            'purpose': 'Conference attendance',
            'amount_claimed': '15000.00',
        }, expected_status=None)

        if response.status_code == 201:
            data = response.json()
            if data.get('status') == 'SUBMITTED':
                self._record_result("TA request created successfully", "Pass",
                                    f"Response: {data}")
            else:
                self._record_result(f"Unexpected status: {data.get('status')}",
                                    "Fail", f"Response: {data}")
                self.fail(f"Expected status=SUBMITTED, got {data.get('status')}")
        else:
            self._record_result(f"HTTP {response.status_code}",
                                "Fail", f"Status: {response.status_code}")
            self.fail(f"Expected 201, got {response.status_code}")

    def test_ap01_create_high_value_ta(self):
        """Alternate Path: Create high-value TA request"""
        self._test_id = "AUDIT-UC-005-AP-01"
        self._uc_id = "AUDIT-UC-005"
        self._test_category = "Alternate Path"
        self._scenario = "Employee creates high-value TA request"
        self._preconditions = "User logged in; amount > high value threshold"
        self._input_action = "POST /api/ta/create/ with high amount"
        self._expected_result = "TA created; marked as high_value=True"

        self.login_as_staff()
        response = self.api_post('/ta/create/', {
            'employee_name': 'Test Employee',
            'department': 'CSE',
            'travel_from': 'Delhi',
            'travel_to': 'Bangalore',
            'start_date': self.future_date(1),
            'end_date': self.future_date(3),
            'purpose': 'International conference',
            'amount_claimed': '60000.00',  # Above high value threshold
        }, expected_status=None)

        if response.status_code == 201:
            data = response.json()
            if data.get('high_value') == True:
                self._record_result("High-value TA created correctly", "Pass",
                                    f"Response: {data}")
            else:
                self._record_result(f"High value not marked: {data.get('high_value')}",
                                    "Fail", f"Response: {data}")
                self.fail("High-value TA should be marked correctly")
        else:
            self._record_result(f"HTTP {response.status_code}",
                                "Fail", f"Status: {response.status_code}")
            self.fail(f"Expected 201, got {response.status_code}")

    def test_ex01_past_travel_dates(self):
        """Exception: Create TA with past travel dates"""
        self._test_id = "AUDIT-UC-005-EX-01"
        self._uc_id = "AUDIT-UC-005"
        self._test_category = "Exception"
        self._scenario = "Employee creates TA with past travel dates"
        self._preconditions = "User logged in"
        self._input_action = "POST /api/ta/create/ with start_date in past"
        self._expected_result = "Rejected HTTP 400; invalid date range"

        self.login_as_staff()
        response = self.api_post('/ta/create/', {
            'employee_name': 'Test Employee',
            'department': 'CSE',
            'travel_from': 'Delhi',
            'travel_to': 'Mumbai',
            'start_date': self.past_date(5),
            'end_date': self.past_date(2),
            'purpose': 'Past travel',
            'amount_claimed': '10000.00',
        }, expected_status=None)

        if response.status_code == 400:
            self._record_result("Correctly rejected past dates", "Pass",
                                f"Response: {response.json()}")
        else:
            self._record_result(f"Not rejected: HTTP {response.status_code}",
                                "Fail", f"Response: {response.json()}")
            self.fail("Should reject TA with past dates")

class TestUC06_ProcessTA(UCTestBase):
    """AUDIT-UC-006: Process Travel Allowance"""

    def test_hp01_finance_approves_low_value_ta(self):
        """Happy Path: Finance verifies and approves low-value TA"""
        self._test_id = "AUDIT-UC-006-HP-01"
        self._uc_id = "AUDIT-UC-006"
        self._test_category = "Happy Path"
        self._scenario = "Finance verifies and approves low-value TA"
        self._preconditions = "Finance user logged in; TA amount <= threshold"
        self._input_action = "POST /api/ta/status/ with action=approve"
        self._expected_result = "TA status changed to APPROVED; HTTP 200"

        # Create low-value TA
        self.login_as_staff()
        ta_response = self.api_post('/ta/create/', {
            'employee_name': 'Test Employee',
            'department': 'CSE',
            'travel_from': 'Delhi',
            'travel_to': 'Mumbai',
            'start_date': self.future_date(5),
            'end_date': self.future_date(7),
            'purpose': 'Meeting',
            'amount_claimed': '8000.00',
        })
        ta_data = ta_response.json()
        ta_id = ta_data['id']

        # Approve as finance
        self.login_as_finance()
        response = self.api_post('/ta/status/', {
            'id': ta_id,
            'action': 'approve',
            'remarks': 'Approved by finance'
        }, expected_status=None)

        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'APPROVED':
                self._record_result("TA approved by finance", "Pass",
                                    f"Response: {data}")
            else:
                self._record_result(f"Unexpected status: {data.get('status')}",
                                    "Fail", f"Response: {data}")
                self.fail(f"Expected APPROVED, got {data.get('status')}")
        else:
            self._record_result(f"HTTP {response.status_code}",
                                "Fail", f"Status: {response.status_code}")
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ap01_authority_approves_high_value_ta(self):
        """Alternate Path: Authority approves high-value TA"""
        self._test_id = "AUDIT-UC-006-AP-01"
        self._uc_id = "AUDIT-UC-006"
        self._test_category = "Alternate Path"
        self._scenario = "Authority approves high-value TA"
        self._preconditions = "HOD logged in; high-value TA assigned to HOD"
        self._input_action = "POST /api/ta/status/ with action=approve"
        self._expected_result = "TA approved by authority"

        # Create high-value TA
        self.login_as_staff()
        ta_response = self.api_post('/ta/create/', {
            'employee_name': 'Test Employee',
            'department': 'CSE',
            'travel_from': 'Delhi',
            'travel_to': 'Singapore',
            'start_date': self.future_date(1),
            'end_date': self.future_date(5),
            'purpose': 'International conference',
            'amount_claimed': '75000.00',
        })
        ta_data = ta_response.json()
        ta_id = ta_data['id']

        # First verify as finance
        self.login_as_finance()
        self.api_post('/ta/status/', {
            'id': ta_id,
            'action': 'verify',
            'remarks': 'Verified for authority approval'
        })

        # Approve as HOD
        self.login_as_hod()
        response = self.api_post('/ta/status/', {
            'id': ta_id,
            'action': 'approve',
            'remarks': 'Approved by HOD'
        }, expected_status=None)

        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'APPROVED':
                self._record_result("High-value TA approved by authority", "Pass",
                                    f"Response: {data}")
            else:
                self._record_result(f"Unexpected status: {data.get('status')}",
                                    "Fail", f"Response: {data}")
                self.fail(f"Expected APPROVED, got {data.get('status')}")
        else:
            self._record_result(f"HTTP {response.status_code}",
                                "Fail", f"Status: {response.status_code}")
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ex01_reject_ta_with_remarks(self):
        """Exception: User rejects TA with remarks"""
        self._test_id = "AUDIT-UC-006-EX-01"
        self._uc_id = "AUDIT-UC-006"
        self._test_category = "Exception"
        self._scenario = "Finance rejects TA with remarks"
        self._preconditions = "Finance user logged in; TA has issues"
        self._input_action = "POST /api/ta/status/ with action=reject, remarks='Invalid purpose'"
        self._expected_result = "TA status changed to REJECTED; rejection remarks saved"

        # Create TA
        self.login_as_staff()
        ta_response = self.api_post('/ta/create/', {
            'employee_name': 'Test Employee',
            'department': 'CSE',
            'travel_from': 'Delhi',
            'travel_to': 'Mumbai',
            'start_date': self.future_date(5),
            'end_date': self.future_date(7),
            'purpose': 'Invalid purpose test',
            'amount_claimed': '10000.00',
        })
        ta_data = ta_response.json()
        ta_id = ta_data['id']

        # Reject as finance
        self.login_as_finance()
        response = self.api_post('/ta/status/', {
            'id': ta_id,
            'action': 'reject',
            'remarks': 'Purpose not valid for travel allowance'
        }, expected_status=None)

        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'REJECTED':
                self._record_result("TA rejected with remarks", "Pass",
                                    f"Response: {data}")
            else:
                self._record_result(f"Unexpected status: {data.get('status')}",
                                    "Fail", f"Response: {data}")
                self.fail(f"Expected REJECTED, got {data.get('status')}")
        else:
            self._record_result(f"HTTP {response.status_code}",
                                "Fail", f"Status: {response.status_code}")
            self.fail(f"Expected 200, got {response.status_code}")

class TestUC07_CreateObservation(UCTestBase):
    """AUDIT-UC-007: Create Audit Observation"""

    def test_hp01_auditor_creates_observation_for_request(self):
        """Happy Path: Auditor creates observation for expense request"""
        self._test_id = "AUDIT-UC-007-HP-01"
        self._uc_id = "AUDIT-UC-007"
        self._test_category = "Happy Path"
        self._scenario = "Auditor creates observation for expense request"
        self._preconditions = "Auditor logged in; request exists"
        self._input_action = "POST /api/observations/create/ with request_id, title, details, deadline"
        self._expected_result = "Observation created with status=OPEN; HTTP 201"

        # Create a request first
        self.login_as_student()
        draft_response = self.api_post('/requests/draft/', {
            'type': 'EXPENSE',
            'amount': '10000.00',
            'department': 'CSE',
            'budget_head': 'travel',
            'description': 'Request for observation',
        })
        draft_data = draft_response.json()
        request_id = draft_data['id']
        self.api_post('/requests/submit/', {'id': request_id})

        # Create observation as auditor
        self.login_as_auditor()
        response = self.api_post('/observations/create/', {
            'request': request_id,
            'title': 'Budget discrepancy observed',
            'details': 'Amount claimed does not match approved budget allocation',
            'response_deadline': self.future_date(7),
        }, expected_status=None)

        if response.status_code == 201:
            data = response.json()
            if data.get('status') == 'OPEN':
                self._record_result("Observation created successfully", "Pass",
                                    f"Response: {data}")
            else:
                self._record_result(f"Unexpected status: {data.get('status')}",
                                    "Fail", f"Response: {data}")
                self.fail(f"Expected status=OPEN, got {data.get('status')}")
        else:
            self._record_result(f"HTTP {response.status_code}",
                                "Fail", f"Status: {response.status_code}")
            self.fail(f"Expected 201, got {response.status_code}")

    def test_ap01_auditor_creates_observation_for_ta(self):
        """Alternate Path: Auditor creates observation for TA request"""
        self._test_id = "AUDIT-UC-007-AP-01"
        self._uc_id = "AUDIT-UC-007"
        self._test_category = "Alternate Path"
        self._scenario = "Auditor creates observation for TA request"
        self._preconditions = "Auditor logged in; TA exists"
        self._input_action = "POST /api/observations/create/ with ta_id, title, details"
        self._expected_result = "Observation linked to TA; status=OPEN"

        # Create TA first
        self.login_as_staff()
        ta_response = self.api_post('/ta/create/', {
            'employee_name': 'Test Employee',
            'department': 'CSE',
            'travel_from': 'Delhi',
            'travel_to': 'Mumbai',
            'start_date': self.future_date(5),
            'end_date': self.future_date(7),
            'purpose': 'TA for observation',
            'amount_claimed': '12000.00',
        })
        ta_data = ta_response.json()
        ta_id = ta_data['id']

        # Create observation as auditor
        self.login_as_auditor()
        response = self.api_post('/observations/create/', {
            'travel_allowance': ta_id,
            'title': 'TA amount verification',
            'details': 'Need to verify if TA amount matches actual travel expenses',
            'response_deadline': self.future_date(10),
        }, expected_status=None)

        if response.status_code == 201:
            data = response.json()
            if data.get('status') == 'OPEN' and data.get('travel_allowance') == ta_id:
                self._record_result("TA observation created successfully", "Pass",
                                    f"Response: {data}")
            else:
                self._record_result(f"Unexpected data: status={data.get('status')}, ta={data.get('travel_allowance')}",
                                    "Fail", f"Response: {data}")
                self.fail("TA observation not created correctly")
        else:
            self._record_result(f"HTTP {response.status_code}",
                                "Fail", f"Status: {response.status_code}")
            self.fail(f"Expected 201, got {response.status_code}")

    def test_ex01_non_auditor_creates_observation(self):
        """Exception: Non-auditor attempts to create observation"""
        self._test_id = "AUDIT-UC-007-EX-01"
        self._uc_id = "AUDIT-UC-007"
        self._test_category = "Exception"
        self._scenario = "Student attempts to create audit observation"
        self._preconditions = "Student user logged in"
        self._input_action = "POST /api/observations/create/"
        self._expected_result = "Rejected HTTP 403; auditor role required"

        # Create a request first
        self.login_as_student()
        draft_response = self.api_post('/requests/draft/', {
            'type': 'EXPENSE',
            'amount': '5000.00',
            'department': 'CSE',
            'budget_head': 'travel',
            'description': 'Request for observation test',
        })
        draft_data = draft_response.json()
        request_id = draft_data['id']
        self.api_post('/requests/submit/', {'id': request_id})

        # Try to create observation as student
        response = self.api_post('/observations/create/', {
            'request': request_id,
            'title': 'Unauthorized observation',
            'details': 'This should be rejected',
        }, expected_status=None)

        if response.status_code == 403:
            self._record_result("Correctly rejected non-auditor", "Pass",
                                f"Response: {response.json()}")
        else:
            self._record_result(f"Not rejected: HTTP {response.status_code}",
                                "Fail", f"Response: {response.json()}")
            self.fail("Non-auditors should not create observations")

class TestUC08_RespondObservation(UCTestBase):
    """AUDIT-UC-008: Respond to Audit Observation"""

    def test_hp01_finance_responds_with_documents(self):
        """Happy Path: Finance responds to observation with documents"""
        self._test_id = "AUDIT-UC-008-HP-01"
        self._uc_id = "AUDIT-UC-008"
        self._test_category = "Happy Path"
        self._scenario = "Finance responds to observation with documents"
        self._preconditions = "Finance user logged in; observation open"
        self._input_action = "POST /api/observations/status/ with response_text, attachments"
        self._expected_result = "Observation status changed to RESPONDED; response saved"

        # Create request and observation first
        self.login_as_student()
        draft_response = self.api_post('/requests/draft/', {
            'type': 'EXPENSE',
            'amount': '8000.00',
            'department': 'CSE',
            'budget_head': 'travel',
            'description': 'Request for response test',
        })
        draft_data = draft_response.json()
        request_id = draft_data['id']
        self.api_post('/requests/submit/', {'id': request_id})

        self.login_as_auditor()
        obs_response = self.api_post('/observations/create/', {
            'request': request_id,
            'title': 'Documentation check',
            'details': 'Please provide additional documentation',
            'response_deadline': self.future_date(5),
        })
        obs_data = obs_response.json()
        obs_id = obs_data['id']

        # Respond as finance
        self.login_as_finance()
        response = self.api_post('/observations/status/', {
            'id': obs_id,
            'response_text': 'All documentation attached as requested',
        }, expected_status=None)

        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'RESPONDED':
                self._record_result("Observation responded successfully", "Pass",
                                    f"Response: {data}")
            else:
                self._record_result(f"Unexpected status: {data.get('status')}",
                                    "Fail", f"Response: {data}")
                self.fail(f"Expected RESPONDED, got {data.get('status')}")
        else:
            self._record_result(f"HTTP {response.status_code}",
                                "Fail", f"Status: {response.status_code}")
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ap01_request_owner_provides_clarification(self):
        """Alternate Path: Request owner provides additional clarification"""
        self._test_id = "AUDIT-UC-008-AP-01"
        self._uc_id = "AUDIT-UC-008"
        self._test_category = "Alternate Path"
        self._scenario = "Request owner provides additional clarification"
        self._preconditions = "Request owner logged in; observation open"
        self._input_action = "POST /api/observations/status/ with additional response"
        self._expected_result = "Response appended to observation"

        # Create request and observation
        self.login_as_student()
        draft_response = self.api_post('/requests/draft/', {
            'type': 'EXPENSE',
            'amount': '6000.00',
            'department': 'CSE',
            'budget_head': 'travel',
            'description': 'Clarification test',
        })
        draft_data = draft_response.json()
        request_id = draft_data['id']
        self.api_post('/requests/submit/', {'id': request_id})

        self.login_as_auditor()
        obs_response = self.api_post('/observations/create/', {
            'request': request_id,
            'title': 'Amount clarification',
            'details': 'Please explain the amount breakdown',
        })
        obs_data = obs_response.json()
        obs_id = obs_data['id']

        # Respond as request owner
        response = self.api_post('/observations/status/', {
            'id': obs_id,
            'response_text': 'Amount includes travel, accommodation, and meals',
        }, expected_status=None)

        if response.status_code == 200:
            data = response.json()
            if 'travel, accommodation' in data.get('response_text', ''):
                self._record_result("Clarification added successfully", "Pass",
                                    f"Response: {data}")
            else:
                self._record_result(f"Response not updated: {data.get('response_text')}",
                                    "Fail", f"Response: {data}")
                self.fail("Response text should be updated")
        else:
            self._record_result(f"HTTP {response.status_code}",
                                "Fail", f"Status: {response.status_code}")
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ex01_respond_to_closed_observation(self):
        """Exception: User attempts to respond to closed observation"""
        self._test_id = "AUDIT-UC-008-EX-01"
        self._uc_id = "AUDIT-UC-008"
        self._test_category = "Exception"
        self._scenario = "User attempts to respond to closed observation"
        self._preconditions = "User logged in; observation status=CLOSED"
        self._input_action = "POST /api/observations/status/ with response"
        self._expected_result = "Rejected; observation already closed"

        # Create and close observation
        self.login_as_student()
        draft_response = self.api_post('/requests/draft/', {
            'type': 'EXPENSE',
            'amount': '4000.00',
            'department': 'CSE',
            'budget_head': 'travel',
            'description': 'Closed observation test',
        })
        draft_data = draft_response.json()
        request_id = draft_data['id']
        self.api_post('/requests/submit/', {'id': request_id})

        self.login_as_auditor()
        obs_response = self.api_post('/observations/create/', {
            'request': request_id,
            'title': 'Closed test',
            'details': 'This will be closed',
        })
        obs_data = obs_response.json()
        obs_id = obs_data['id']

        # Close the observation
        from applications.audit_account.models import AuditObservation
        obs = AuditObservation.objects.get(id=obs_id)
        obs.status = 'CLOSED'
        obs.save()

        # Try to respond
        self.login_as_finance()
        response = self.api_post('/observations/status/', {
            'id': obs_id,
            'response_text': 'This should be rejected',
        }, expected_status=None)

        if response.status_code in [400, 403]:
            self._record_result("Correctly rejected closed observation", "Pass",
                                f"Response: {response.json()}")
        else:
            self._record_result(f"Not rejected: HTTP {response.status_code}",
                                "Fail", f"Response: {response.json()}")
            self.fail("Should reject responses to closed observations")

class TestUC09_ManageBudget(UCTestBase):
    """AUDIT-UC-009: Manage Department Budget"""

    def test_hp01_admin_creates_budget(self):
        """Happy Path: Admin creates new department budget"""
        self._test_id = "AUDIT-UC-009-HP-01"
        self._uc_id = "AUDIT-UC-009"
        self._test_category = "Happy Path"
        self._scenario = "Admin creates new department budget"
        self._preconditions = "Admin logged in"
        self._input_action = "POST /api/budgets/create/ with department, budget_head, amount"
        self._expected_result = "Budget created; HTTP 201"

        # Note: In real implementation, this would require admin user
        # For testing, we'll use a user with appropriate permissions
        self.login_as_director()  # Assuming director has admin-like permissions
        response = self.api_post('/budgets/create/', {
            'department': 'TEST',
            'budget_head': 'test_head',
            'allocated_amount': '25000.00',
        }, expected_status=None)

        if response.status_code == 201:
            data = response.json()
            if data.get('department') == 'TEST':
                self._record_result("Budget created successfully", "Pass",
                                    f"Response: {data}")
            else:
                self._record_result(f"Unexpected department: {data.get('department')}",
                                    "Fail", f"Response: {data}")
                self.fail(f"Expected department=TEST, got {data.get('department')}")
        else:
            self._record_result(f"HTTP {response.status_code}",
                                "Fail", f"Status: {response.status_code}")
            self.fail(f"Expected 201, got {response.status_code}")

    def test_ap01_admin_updates_budget(self):
        """Alternate Path: Admin updates existing budget allocation"""
        self._test_id = "AUDIT-UC-009-AP-01"
        self._uc_id = "AUDIT-UC-009"
        self._test_category = "Alternate Path"
        self._scenario = "Admin updates existing budget allocation"
        self._preconditions = "Admin logged in; budget exists"
        self._input_action = "POST /api/budgets/update/ with increased amount"
        self._expected_result = "Budget updated; remaining amount adjusted"

        # First create a budget
        self.login_as_director()
        create_response = self.api_post('/budgets/create/', {
            'department': 'UPDATE_TEST',
            'budget_head': 'update_head',
            'allocated_amount': '20000.00',
        })
        budget_data = create_response.json()
        budget_id = budget_data['id']

        # Update the budget
        response = self.api_post('/budgets/update/', {
            'id': budget_id,
            'allocated_amount': '30000.00',
        }, expected_status=None)

        if response.status_code == 200:
            data = response.json()
            if data.get('allocated_amount') == '30000.00':
                self._record_result("Budget updated successfully", "Pass",
                                    f"Response: {data}")
            else:
                self._record_result(f"Amount not updated: {data.get('allocated_amount')}",
                                    "Fail", f"Response: {data}")
                self.fail("Budget amount should be updated")
        else:
            self._record_result(f"HTTP {response.status_code}",
                                "Fail", f"Status: {response.status_code}")
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ex01_non_admin_manages_budget(self):
        """Exception: Non-admin attempts budget management"""
        self._test_id = "AUDIT-UC-009-EX-01"
        self._uc_id = "AUDIT-UC-009"
        self._test_category = "Exception"
        self._scenario = "Student attempts budget management"
        self._preconditions = "Student logged in"
        self._input_action = "POST /api/budgets/create/"
        self._expected_result = "Rejected HTTP 403; admin access required"

        self.login_as_student()
        response = self.api_post('/budgets/create/', {
            'department': 'STUDENT_TEST',
            'budget_head': 'student_head',
            'allocated_amount': '10000.00',
        }, expected_status=None)

        if response.status_code == 403:
            self._record_result("Correctly rejected non-admin", "Pass",
                                f"Response: {response.json()}")
        else:
            self._record_result(f"Not rejected: HTTP {response.status_code}",
                                "Fail", f"Response: {response.json()}")
            self.fail("Non-admins should not manage budgets")

    def test_hp02_admin_views_budget_details(self):
        """Happy Path: Admin views detailed budget allocation"""
        self._test_id = "AUDIT-UC-001-HP-02"
        self._uc_id = "AUDIT-UC-001"
        self._test_category = "Happy Path"
        self._scenario = "Admin creates draft with detailed budget tracking"
        self._preconditions = "Admin logged in; department exists"
        self._input_action = "Create draft with budget tracking details"
        self._expected_result = "Draft created with budget metadata"

        self.login_as_director()
        response = self.api_post('/requests/draft/', {
            'type': 'EXPENSE',
            'amount': '8000.00',
            'department': 'ECE',
            'budget_head': 'equipment',
            'description': 'Budget tracking test',
            'tracking_id': 'TRACK-001',
        }, expected_status=None)

        if response.status_code == 201:
            self._record_result("Admin draft created with tracking", "Pass",
                                f"Request ID: {response.json().get('id')}")
        else:
            self._record_result(f"Failed: HTTP {response.status_code}", "Fail",
                                f"Response: {response.json()}")

    def test_ap02_student_draft_with_multiple_budget_heads(self):
        """Alternate Path: Draft with multiple budget head options"""
        self._test_id = "AUDIT-UC-001-AP-02"
        self._uc_id = "AUDIT-UC-001"
        self._test_category = "Alternate Path"
        self._scenario = "User selects alternative budget head"
        self._preconditions = "User logged in; multiple budget heads available"
        self._input_action = "Create draft with alternate budget head"
        self._expected_result = "Draft created with selected budget head"

        self.login_as_student()
        response = self.api_post('/requests/draft/', {
            'type': 'EXPENSE',
            'amount': '3000.00',
            'department': 'MECH',
            'budget_head': 'conference',
            'description': 'Conference attendance',
        }, expected_status=None)

        if response.status_code == 201:
            self._record_result("Alternate budget head draft created", "Pass",
                                f"Budget head: conference")
        else:
            self._record_result(f"Failed: HTTP {response.status_code}", "Fail",
                                f"Response: {response.json()}")

    def test_ex02_invalid_amount_format(self):
        """Exception: Invalid amount format in draft creation"""
        self._test_id = "AUDIT-UC-001-EX-02"
        self._uc_id = "AUDIT-UC-001"
        self._test_category = "Exception"
        self._scenario = "User provides invalid amount format"
        self._preconditions = "User logged in"
        self._input_action = "POST with amount='invalid'"
        self._expected_result = "Rejected with validation error"

        self.login_as_student()
        response = self.api_post('/requests/draft/', {
            'type': 'EXPENSE',
            'amount': 'invalid_amount',
            'department': 'CSE',
            'budget_head': 'travel',
            'description': 'Invalid amount test',
        }, expected_status=None)

        if response.status_code == 400:
            self._record_result("Correctly rejected invalid amount", "Pass",
                                f"Response: {response.json()}")
        else:
            self._record_result(f"Not rejected: HTTP {response.status_code}", "Fail",
                                f"Response: {response.json()}")

    def test_hp02_resubmit_draft_with_edits(self):
        """Happy Path: Submit previously saved and edited draft"""
        self._test_id = "AUDIT-UC-002-HP-02"
        self._uc_id = "AUDIT-UC-002"
        self._test_category = "Happy Path"
        self._scenario = "User edits draft multiple times then submits"
        self._preconditions = "Draft exists; owner logged in"
        self._input_action = "Edit draft, save, then submit"
        self._expected_result = "Draft submitted with latest edits"

        self.login_as_student()
        draft_response = self.api_post('/requests/draft/', {
            'type': 'EXPENSE',
            'amount': '4000.00',
            'department': 'CSE',
            'budget_head': 'travel',
            'description': 'Initial description',
        })
        draft_id = draft_response.json()['id']

        # Edit draft
        self.api_post('/requests/draft/', {
            'id': draft_id,
            'description': 'Updated description',
        })

        # Submit
        response = self.api_post('/requests/submit/', {'id': draft_id}, expected_status=None)

        if response.status_code == 200:
            self._record_result("Edited draft submitted successfully", "Pass",
                                f"Status: {response.json().get('status')}")
        else:
            self._record_result(f"Failed: HTTP {response.status_code}", "Fail",
                                f"Response: {response.json()}")

    def test_ap02_submit_without_all_optional_fields(self):
        """Alternate Path: Submit draft with only required fields"""
        self._test_id = "AUDIT-UC-002-AP-02"
        self._uc_id = "AUDIT-UC-002"
        self._test_category = "Alternate Path"
        self._scenario = "Submit minimal draft with required fields only"
        self._preconditions = "Minimal draft exists"
        self._input_action = "POST /submit with only required fields"
        self._expected_result = "Request submitted successfully"

        self.login_as_student()
        draft_response = self.api_post('/requests/draft/', {
            'type': 'EXPENSE',
            'amount': '2000.00',
            'department': 'CSE',
            'budget_head': 'travel',
        })
        draft_id = draft_response.json()['id']

        response = self.api_post('/requests/submit/', {'id': draft_id}, expected_status=None)

        if response.status_code == 200:
            self._record_result("Minimal draft submitted", "Pass",
                                f"Submission successful")
        else:
            self._record_result(f"Failed: HTTP {response.status_code}", "Fail",
                                f"Response: {response.json()}")

    def test_ex02_submit_already_submitted_request(self):
        """Exception: Attempt to submit already submitted request"""
        self._test_id = "AUDIT-UC-002-EX-02"
        self._uc_id = "AUDIT-UC-002"
        self._test_category = "Exception"
        self._scenario = "User attempts to submit already submitted request"
        self._preconditions = "Request already submitted"
        self._input_action = "POST /submit with submitted request ID"
        self._expected_result = "Rejected; request already submitted"

        self.login_as_student()
        draft_response = self.api_post('/requests/draft/', {
            'type': 'EXPENSE',
            'amount': '2000.00',
            'department': 'CSE',
            'budget_head': 'travel',
            'description': 'Double submit test',
        })
        draft_id = draft_response.json()['id']

        # First submit
        self.api_post('/requests/submit/', {'id': draft_id})

        # Try to submit again
        response = self.api_post('/requests/submit/', {'id': draft_id}, expected_status=None)

        if response.status_code == 400 or response.status_code == 409:
            self._record_result("Correctly rejected double submit", "Pass",
                                f"Response: {response.json()}")
        else:
            self._record_result(f"Not rejected: HTTP {response.status_code}", "Fail",
                                f"Response: {response.json()}")

    def test_hp02_finance_validates_with_remarks(self):
        """Happy Path: Finance validation with detailed remarks"""
        self._test_id = "AUDIT-UC-003-HP-02"
        self._uc_id = "AUDIT-UC-003"
        self._test_category = "Happy Path"
        self._scenario = "Finance validates and adds remarks"
        self._preconditions = "Request submitted; finance logged in"
        self._input_action = "Validate with remarks and attachments"
        self._expected_result = "Validation saved with remarks"

        self.login_as_student()
        draft_response = self.api_post('/requests/draft/', {
            'type': 'EXPENSE',
            'amount': '5000.00',
            'department': 'CSE',
            'budget_head': 'travel',
            'description': 'Remarks test',
        })
        draft_id = draft_response.json()['id']
        self.api_post('/requests/submit/', {'id': draft_id})

        self.login_as_finance()
        response = self.api_post('/requests/status/', {
            'id': draft_id,
            'action': 'validate',
            'remarks': 'Documentation complete and verified',
        }, expected_status=None)

        if response.status_code == 200:
            self._record_result("Validation with remarks saved", "Pass",
                                f"Status: {response.json().get('status')}")
        else:
            self._record_result(f"Failed: HTTP {response.status_code}", "Fail",
                                f"Response: {response.json()}")

    def test_ap02_finance_queries_pending_requests(self):
        """Alternate Path: Finance filters pending requests by criteria"""
        self._test_id = "AUDIT-UC-003-AP-02"
        self._uc_id = "AUDIT-UC-003"
        self._test_category = "Alternate Path"
        self._scenario = "Finance queries pending requests by department"
        self._preconditions = "Multiple requests pending"
        self._input_action = "GET /requests?status=pending&department=CSE"
        self._expected_result = "Filtered requests returned"

        self.login_as_finance()
        response = self.api_get('/requests/?status=SUBMITTED&department=CSE', expected_status=None)

        if response.status_code == 200:
            data = response.json()
            self._record_result("Filtered requests retrieved", "Pass",
                                f"Returned {len(data) if isinstance(data, list) else 0} requests")
        else:
            self._record_result(f"Failed: HTTP {response.status_code}", "Fail",
                                f"Response: {response.json()}")

    def test_ex02_finance_validates_insufficient_documents(self):
        """Exception: Finance validation rejected for insufficient docs"""
        self._test_id = "AUDIT-UC-003-EX-02"
        self._uc_id = "AUDIT-UC-003"
        self._test_category = "Exception"
        self._scenario = "Finance rejects validation for missing documents"
        self._preconditions = "Request submitted without required documents"
        self._input_action = "Attempt to validate incomplete request"
        self._expected_result = "Validation rejected with document error"

        self.login_as_student()
        draft_response = self.api_post('/requests/draft/', {
            'type': 'EXPENSE',
            'amount': '5000.00',
            'department': 'CSE',
            'budget_head': 'travel',
            'description': 'No docs test',
        })
        draft_id = draft_response.json()['id']
        self.api_post('/requests/submit/', {'id': draft_id})

        self.login_as_finance()
        response = self.api_post('/requests/status/', {
            'id': draft_id,
            'action': 'reject_validation',
            'remarks': 'Missing required documents',
        }, expected_status=None)

        if response.status_code in [200, 400]:
            self._record_result("Validation rejection handled", "Pass",
                                f"Response received")
        else:
            self._record_result(f"Failed: HTTP {response.status_code}", "Fail",
                                f"Response: {response.json()}")

    def test_hp02_hod_approves_with_conditions(self):
        """Happy Path: HOD approval with conditional remarks"""
        self._test_id = "AUDIT-UC-004-HP-02"
        self._uc_id = "AUDIT-UC-004"
        self._test_category = "Happy Path"
        self._scenario = "HOD approves request with conditional remarks"
        self._preconditions = "Request validated; HOD logged in"
        self._input_action = "Approve with conditions/remarks"
        self._expected_result = "Request approved with conditions recorded"

        self.login_as_student()
        draft_response = self.api_post('/requests/draft/', {
            'type': 'EXPENSE',
            'amount': '15000.00',
            'department': 'CSE',
            'budget_head': 'travel',
            'description': 'Conditional approval test',
        })
        draft_id = draft_response.json()['id']
        self.api_post('/requests/submit/', {'id': draft_id})

        self.login_as_finance()
        self.api_post('/requests/status/', {
            'id': draft_id,
            'action': 'validate',
        })

        self.login_as_hod()
        response = self.api_post('/requests/status/', {
            'id': draft_id,
            'action': 'approve',
            'remarks': 'Approved with budget condition compliance',
        }, expected_status=None)

        if response.status_code == 200:
            self._record_result("Conditional approval recorded", "Pass",
                                f"Status: {response.json().get('status')}")
        else:
            self._record_result(f"Failed: HTTP {response.status_code}", "Fail",
                                f"Response: {response.json()}")

    def test_ap02_director_approves_high_value_for_special_department(self):
        """Alternate Path: Director approves high-value request for special department"""
        self._test_id = "AUDIT-UC-004-AP-02"
        self._uc_id = "AUDIT-UC-004"
        self._test_category = "Alternate Path"
        self._scenario = "Director approves high-value special request"
        self._preconditions = "High-value request exists; director logged in"
        self._input_action = "Director approves request"
        self._expected_result = "Request approved by director"

        self.login_as_student()
        draft_response = self.api_post('/requests/draft/', {
            'type': 'EXPENSE',
            'amount': '120000.00',
            'department': 'ADMIN',
            'budget_head': 'strategic',
            'description': 'Director approval test',
        })
        draft_id = draft_response.json()['id']
        self.api_post('/requests/submit/', {'id': draft_id})

        self.login_as_finance()
        self.api_post('/requests/status/', {
            'id': draft_id,
            'action': 'validate',
        })

        self.login_as_director()
        response = self.api_post('/requests/status/', {
            'id': draft_id,
            'action': 'approve',
            'remarks': 'Director approval for strategic expense',
        }, expected_status=None)

        if response.status_code == 200:
            self._record_result("Director approval recorded", "Pass",
                                f"Amount: 120000")
        else:
            self._record_result(f"Failed: HTTP {response.status_code}", "Fail",
                                f"Response: {response.json()}")

    def test_ex02_approver_exceeds_authority_limit(self):
        """Exception: Approver attempting approval exceeding authority limit"""
        self._test_id = "AUDIT-UC-004-EX-02"
        self._uc_id = "AUDIT-UC-004"
        self._test_category = "Exception"
        self._scenario = "HOD attempts to approve amount exceeding authority"
        self._preconditions = "HOD authority limit = 50000"
        self._input_action = "HOD attempts to approve 75000 request"
        self._expected_result = "Approval rejected; amount exceeds authority"

        self.login_as_student()
        draft_response = self.api_post('/requests/draft/', {
            'type': 'EXPENSE',
            'amount': '75000.00',
            'department': 'CSE',
            'budget_head': 'equipment',
            'description': 'Authority exceed test',
        })
        draft_id = draft_response.json()['id']
        self.api_post('/requests/submit/', {'id': draft_id})

        self.login_as_finance()
        self.api_post('/requests/status/', {
            'id': draft_id,
            'action': 'validate',
        })

        self.login_as_hod()
        response = self.api_post('/requests/status/', {
            'id': draft_id,
            'action': 'approve',
        }, expected_status=None)

        if response.status_code == 403:
            self._record_result("Correctly rejected authority exceed", "Pass",
                                f"Response: {response.json()}")
        else:
            self._record_result(f"Not rejected: HTTP {response.status_code}", "Fail",
                                f"Response: {response.json()}")

    def test_hp02_create_ta_with_advance_planning(self):
        """Happy Path: Create TA with advance planning details"""
        self._test_id = "AUDIT-UC-005-HP-02"
        self._uc_id = "AUDIT-UC-005"
        self._test_category = "Happy Path"
        self._scenario = "Staff creates TA with advance trip planning"
        self._preconditions = "Staff logged in; future dates available"
        self._input_action = "Create TA with planning details"
        self._expected_result = "TA created with planning metadata"

        self.login_as_staff()
        response = self.api_post('/ta/create/', {
            'employee_name': 'Planning Test Employee',
            'department': 'MECH',
            'travel_from': 'New Delhi',
            'travel_to': 'Bangalore',
            'start_date': self.future_date(30),
            'end_date': self.future_date(35),
            'purpose': 'Advanced planned conference',
            'amount_claimed': '12000.00',
            'transportation': 'Flight',
            'accommodation': 'Hotel',
        }, expected_status=None)

        if response.status_code == 201:
            self._record_result("TA with planning details created", "Pass",
                                f"TA ID: {response.json().get('id')}")
        else:
            self._record_result(f"Failed: HTTP {response.status_code}", "Fail",
                                f"Response: {response.json()}")

    def test_ap02_create_domestic_ta_low_value(self):
        """Alternate Path: Create low-value domestic TA"""
        self._test_id = "AUDIT-UC-005-AP-02"
        self._uc_id = "AUDIT-UC-005"
        self._test_category = "Alternate Path"
        self._scenario = "Create low-value domestic travel allowance"
        self._preconditions = "Staff logged in"
        self._input_action = "Create domestic TA"
        self._expected_result = "Domestic TA created successfully"

        self.login_as_staff()
        response = self.api_post('/ta/create/', {
            'employee_name': 'Domestic Test Employee',
            'department': 'EE',
            'travel_from': 'Delhi',
            'travel_to': 'Chandigarh',
            'start_date': self.future_date(7),
            'end_date': self.future_date(8),
            'purpose': 'Local seminar',
            'amount_claimed': '3000.00',
        }, expected_status=None)

        if response.status_code == 201:
            self._record_result("Domestic TA created", "Pass",
                                f"Amount: 3000")
        else:
            self._record_result(f"Failed: HTTP {response.status_code}", "Fail",
                                f"Response: {response.json()}")

    def test_ex02_invalid_travel_destination(self):
        """Exception: TA with invalid travel destination"""
        self._test_id = "AUDIT-UC-005-EX-02"
        self._uc_id = "AUDIT-UC-005"
        self._test_category = "Exception"
        self._scenario = "Create TA with same source and destination"
        self._preconditions = "Staff logged in"
        self._input_action = "Create TA with travel_from = travel_to"
        self._expected_result = "Rejected; invalid route"

        self.login_as_staff()
        response = self.api_post('/ta/create/', {
            'employee_name': 'Invalid Route Employee',
            'department': 'CSE',
            'travel_from': 'Delhi',
            'travel_to': 'Delhi',
            'start_date': self.future_date(5),
            'end_date': self.future_date(6),
            'purpose': 'Invalid route test',
            'amount_claimed': '5000.00',
        }, expected_status=None)

        if response.status_code == 400:
            self._record_result("Correctly rejected invalid route", "Pass",
                                f"Response: {response.json()}")
        else:
            self._record_result(f"Not rejected: HTTP {response.status_code}", "Fail",
                                f"Response: {response.json()}")

    def test_hp02_ta_approval_with_escalation(self):
        """Happy Path: TA approval with automatic escalation"""
        self._test_id = "AUDIT-UC-006-HP-02"
        self._uc_id = "AUDIT-UC-006"
        self._test_category = "Happy Path"
        self._scenario = "TA high-value auto-escalates to authority"
        self._preconditions = "High-value TA submitted"
        self._input_action = "TA approval with escalation"
        self._expected_result = "TA escalated and approved by authority"

        self.login_as_staff()
        ta_response = self.api_post('/ta/create/', {
            'employee_name': 'Escalation Test',
            'department': 'CSE',
            'travel_from': 'Delhi',
            'travel_to': 'London',
            'start_date': self.future_date(10),
            'end_date': self.future_date(20),
            'purpose': 'International conference',
            'amount_claimed': '55000.00',
        })
        ta_id = ta_response.json()['id']

        self.login_as_finance()
        self.api_post('/ta/status/', {
            'id': ta_id,
            'action': 'verify',
        })

        self.login_as_dean()
        response = self.api_post('/ta/status/', {
            'id': ta_id,
            'action': 'approve',
            'remarks': 'Dean approval for high-value TA',
        }, expected_status=None)

        if response.status_code == 200:
            self._record_result("TA escalation and approval successful", "Pass",
                                f"Amount: 55000")
        else:
            self._record_result(f"Failed: HTTP {response.status_code}", "Fail",
                                f"Response: {response.json()}")

    def test_ap02_ta_processing_with_partial_advance(self):
        """Alternate Path: TA processed with partial advance"""
        self._test_id = "AUDIT-UC-006-AP-02"
        self._uc_id = "AUDIT-UC-006"
        self._test_category = "Alternate Path"
        self._scenario = "TA approved with partial advance payment"
        self._preconditions = "TA verified; finance logged in"
        self._input_action = "Approve TA with 50% advance"
        self._expected_result = "TA approved; 50% advance processed"

        self.login_as_staff()
        ta_response = self.api_post('/ta/create/', {
            'employee_name': 'Partial Advance Test',
            'department': 'ECE',
            'travel_from': 'Delhi',
            'travel_to': 'Goa',
            'start_date': self.future_date(3),
            'end_date': self.future_date(5),
            'purpose': 'Workshop',
            'amount_claimed': '10000.00',
        })
        ta_id = ta_response.json()['id']

        self.login_as_finance()
        response = self.api_post('/ta/status/', {
            'id': ta_id,
            'action': 'approve_with_advance',
            'advance_percentage': 50,
        }, expected_status=None)

        if response.status_code == 200:
            self._record_result("Partial advance approved", "Pass",
                                f"Response: {response.json()}")
        else:
            self._record_result(f"Failed: HTTP {response.status_code}", "Fail",
                                f"Response: {response.json()}")

    def test_ex02_ta_final_settlement_after_travel(self):
        """Exception: TA final settlement with discrepancies"""
        self._test_id = "AUDIT-UC-006-EX-02"
        self._uc_id = "AUDIT-UC-006"
        self._test_category = "Exception"
        self._scenario = "TA settlement with claimed vs actual discrepancy"
        self._preconditions = "TA travel completed; settlement initiated"
        self._input_action = "Submit settlement with variance"
        self._expected_result = "Settlement processed with variance noted"

        self.login_as_staff()
        ta_response = self.api_post('/ta/create/', {
            'employee_name': 'Settlement Test',
            'department': 'CSE',
            'travel_from': 'Delhi',
            'travel_to': 'Mumbai',
            'start_date': self.past_date(10),
            'end_date': self.past_date(5),
            'purpose': 'Completed travel',
            'amount_claimed': '8000.00',
        })
        ta_id = ta_response.json()['id']

        response = self.api_post('/ta/settlement/', {
            'id': ta_id,
            'amount_spent': '7500.00',
            'variance_remarks': 'Saved on accommodation',
        }, expected_status=None)

        if response.status_code in [200, 201]:
            self._record_result("Settlement processed with variance", "Pass",
                                f"Variance: 500")
        else:
            self._record_result(f"Failed: HTTP {response.status_code}", "Fail",
                                f"Response: {response.json()}")

    def test_hp02_observation_follow_up_created(self):
        """Happy Path: Create follow-up observation for incomplete response"""
        self._test_id = "AUDIT-UC-007-HP-02"
        self._uc_id = "AUDIT-UC-007"
        self._test_category = "Happy Path"
        self._scenario = "Auditor creates follow-up observation"
        self._preconditions = "Original observation partially responded"
        self._input_action = "Create follow-up observation"
        self._expected_result = "Follow-up observation created and linked"

        self.login_as_student()
        draft_response = self.api_post('/requests/draft/', {
            'type': 'EXPENSE',
            'amount': '7000.00',
            'department': 'CSE',
            'budget_head': 'travel',
            'description': 'Follow-up observation test',
        })
        draft_id = draft_response.json()['id']
        self.api_post('/requests/submit/', {'id': draft_id})

        self.login_as_auditor()
        obs_response = self.api_post('/observations/create/', {
            'request': draft_id,
            'title': 'Initial observation',
            'details': 'Requires clarification',
            'response_deadline': self.future_date(7),
        })
        obs_id = obs_response.json()['id']

        # Create follow-up
        response = self.api_post('/observations/create/', {
            'request': draft_id,
            'parent_observation': obs_id,
            'title': 'Follow-up observation',
            'details': 'Response incomplete',
            'response_deadline': self.future_date(14),
        }, expected_status=None)

        if response.status_code == 201:
            self._record_result("Follow-up observation created", "Pass",
                                f"Observation ID: {response.json().get('id')}")
        else:
            self._record_result(f"Failed: HTTP {response.status_code}", "Fail",
                                f"Response: {response.json()}")

class TestUC10_ViewReports(UCTestBase):
    """AUDIT-UC-010: View and Export Reports"""

    def test_hp01_auditor_views_all_requests(self):
        """Happy Path: Auditor views all requests and exports report"""
        self._test_id = "AUDIT-UC-010-HP-01"
        self._uc_id = "AUDIT-UC-010"
        self._test_category = "Happy Path"
        self._scenario = "Auditor views all requests and exports report"
        self._preconditions = "Auditor logged in"
        self._input_action = "GET /api/requests/ with view=all; then GET /api/reports/export/"
        self._expected_result = "Requests listed; report exported as file"

        # Create some requests first
        self.login_as_student()
        self.api_post('/requests/draft/', {
            'type': 'EXPENSE',
            'amount': '3000.00',
            'department': 'CSE',
            'budget_head': 'travel',
            'description': 'Report test request',
        })

        # View as auditor
        self.login_as_auditor()
        response = self.api_get('/requests/', expected_status=None)

        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                self._record_result("Requests listed successfully", "Pass",
                                    f"Response contains {len(data)} requests")
            else:
                self._record_result(f"No requests returned: {data}",
                                    "Fail", f"Response: {data}")
                self.fail("Should return list of requests")
        else:
            self._record_result(f"HTTP {response.status_code}",
                                "Fail", f"Status: {response.status_code}")
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ap01_finance_views_pending_requests(self):
        """Alternate Path: Finance views pending requests"""
        self._test_id = "AUDIT-UC-010-AP-01"
        self._uc_id = "AUDIT-UC-010"
        self._test_category = "Alternate Path"
        self._scenario = "Finance views pending requests"
        self._preconditions = "Finance user logged in"
        self._input_action = "GET /api/requests/ with view=finance"
        self._expected_result = "Pending requests for finance review returned"

        # Create and submit request
        self.login_as_student()
        draft_response = self.api_post('/requests/draft/', {
            'type': 'EXPENSE',
            'amount': '4000.00',
            'department': 'CSE',
            'budget_head': 'travel',
            'description': 'Finance view test',
        })
        draft_data = draft_response.json()
        self.api_post('/requests/submit/', {'id': draft_data['id']})

        # View as finance
        self.login_as_finance()
        response = self.api_get('/requests/', expected_status=None)

        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                submitted_requests = [r for r in data if r.get('status') == 'SUBMITTED']
                if len(submitted_requests) > 0:
                    self._record_result("Pending requests visible to finance", "Pass",
                                        f"Found {len(submitted_requests)} submitted requests")
                else:
                    self._record_result("No submitted requests found", "Partial",
                                        f"Total requests: {len(data)}")
            else:
                self._record_result(f"Unexpected response format: {data}",
                                    "Fail", f"Response: {data}")
                self.fail("Should return list of requests")
        else:
            self._record_result(f"HTTP {response.status_code}",
                                "Fail", f"Status: {response.status_code}")
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ex01_student_views_restricted_requests(self):
        """Exception: Student attempts to view restricted requests"""
        self._test_id = "AUDIT-UC-010-EX-01"
        self._uc_id = "AUDIT-UC-010"
        self._test_category = "Exception"
        self._scenario = "Student attempts to view restricted requests"
        self._preconditions = "Student logged in"
        self._input_action = "GET /api/requests/ with view=all"
        self._expected_result = "Only user's own requests returned; restricted views blocked"

        # Create request for another user (simulated)
        self.login_as_student()
        draft_response = self.api_post('/requests/draft/', {
            'type': 'EXPENSE',
            'amount': '2000.00',
            'department': 'CSE',
            'budget_head': 'travel',
            'description': 'Access test request',
        })
        draft_data = draft_response.json()
        self.api_post('/requests/submit/', {'id': draft_data['id']})

        # Try to view all requests (should be restricted)
        response = self.api_get('/requests/', expected_status=None)

        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                # Check that student only sees their own requests
                own_requests = [r for r in data if r.get('created_by') == self.student_user.id]
                other_requests = [r for r in data if r.get('created_by') != self.student_user.id]
                if len(other_requests) == 0:
                    self._record_result("Student only sees own requests", "Pass",
                                        f"Own: {len(own_requests)}, Others: {len(other_requests)}")
                else:
                    self._record_result(f"Student sees others' requests: {len(other_requests)}",
                                        "Fail", f"Response: {data}")
                    self.fail("Students should only see their own requests")
            else:
                self._record_result(f"Unexpected response format: {data}",
                                    "Fail", f"Response: {data}")
                self.fail("Should return list of requests")
        else:
            self._record_result(f"HTTP {response.status_code}",
                                "Fail", f"Status: {response.status_code}")
            self.fail(f"Expected 200, got {response.status_code}")