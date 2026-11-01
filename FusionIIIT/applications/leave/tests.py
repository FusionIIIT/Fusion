import datetime
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase
from django.test.utils import override_settings
from django.urls import resolve
from rest_framework.test import APIRequestFactory, force_authenticate

from applications.globals.models import DepartmentInfo, Designation, ExtraInfo
from .elm_services import charged_days, respond_to_task, submit_leave, withdraw_pending
from .models import (ELMPolicy, ELMRouteConfiguration, ELMWorkflowTask,
                     Leave, LeaveSegment, LeaveType, LeavesCount)
from .views import elm_dashboard
from .api.elm_views import elm_applications_api


class ELMServiceTests(TestCase):
    def setUp(self):
        self.department = DepartmentInfo.objects.create(name='ELM test unit')
        self.user = User.objects.create_user(username='elm_employee', password='unused')
        ExtraInfo.objects.create(id='elm-employee', user=self.user, user_type='staff',
                                 department=self.department)
        self.designation = Designation.objects.create(name='ELM Unit Head')
        from applications.globals.models import HoldsDesignation
        HoldsDesignation.objects.create(user=self.user, working=self.user,
                                        designation=self.designation)
        self.leave_type = LeaveType.objects.create(name='Casual')
        ELMPolicy.objects.create(category='CL', annual_entitlement=8,
            eligible_faculty=True, eligible_staff=True, published=True,
            effective_from=datetime.date(2020, 1, 1))
        ELMRouteConfiguration.objects.create(unit=self.department, category='CL',
            step=0, designation=self.designation, is_unit_head=True, published=True)
        self.balance = LeavesCount.objects.create(user=self.user, year=2030,
            leave_type=self.leave_type, remaining_leaves=Decimal('8'))

    def test_cl_half_day_charges_half(self):
        self.assertEqual(charged_days('CL', datetime.date(2030, 1, 7),
                                     datetime.date(2030, 1, 7), True, False), Decimal('0.5'))

    def test_continuous_leave_counts_weekend_days(self):
        self.assertEqual(charged_days('EL', datetime.date(2030, 1, 4),
                                     datetime.date(2030, 1, 7)), Decimal('4'))

    def test_elm_dashboard_route_is_registered(self):
        self.assertEqual(resolve('/leave/elm/').view_name, 'leave:elm-dashboard')

    def test_elm_application_api_route_is_registered(self):
        self.assertEqual(resolve('/leave/api/elm/applications/').view_name,
                         'leave:elm-applications-api')

    @override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
    def test_elm_dashboard_renders_for_employee(self):
        leave = Leave.objects.create(applicant=self.user, purpose='Test application',
                                     elm_state='awaiting_unit_head')
        LeaveSegment.objects.create(leave=leave, leave_type=self.leave_type,
            start_date=datetime.date(2030, 1, 7), end_date=datetime.date(2030, 1, 7))
        request = RequestFactory().get('/leave/elm/')
        request.user = self.user
        SessionMiddleware(lambda req: None).process_request(request)
        request.session.save()
        MessageMiddleware(lambda req: None).process_request(request)
        response = elm_dashboard(request)
        self.assertEqual(response.status_code, 200)

    def test_elm_applications_api_scopes_employee_requests(self):
        request = APIRequestFactory().get('/leave/api/elm/applications/')
        force_authenticate(request, user=self.user)
        response = elm_applications_api(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    @patch('notification.views.leave_module_notif')
    def test_submission_reserves_balance_and_withdrawal_restores_it(self, _notification):
        leave = submit_leave(self.user, 'CL', datetime.date(2030, 1, 7),
            datetime.date(2030, 1, 7), 'Personal', start_half=True)
        self.balance.refresh_from_db()
        self.assertEqual(Decimal(str(self.balance.remaining_leaves)), Decimal('7.5'))
        self.assertTrue(ELMWorkflowTask.objects.filter(leave=leave, task_type='unit_head', status='pending').exists())
        withdraw_pending(leave, self.user)
        self.balance.refresh_from_db()
        self.assertEqual(Decimal(str(self.balance.remaining_leaves)), Decimal('8'))

    @patch('notification.views.leave_module_notif')
    def test_required_substitute_consent_precedes_unit_head_routing(self, _notification):
        ELMPolicy.objects.filter(category='CL').update(requires_substitute=True)
        substitute = User.objects.create_user(username='elm_substitute', password='unused')
        ExtraInfo.objects.create(id='elm-substitute', user=substitute, user_type='staff',
                                 department=self.department)
        leave = submit_leave(self.user, 'CL', datetime.date(2030, 1, 7),
            datetime.date(2030, 1, 7), 'Personal', substitute=substitute)
        self.assertEqual(leave.elm_state, 'awaiting_substitute')
        self.assertFalse(ELMWorkflowTask.objects.filter(leave=leave, task_type='unit_head').exists())
        task = ELMWorkflowTask.objects.get(leave=leave, task_type='substitute')
        respond_to_task(task, substitute, 'accept')
        self.assertTrue(ELMWorkflowTask.objects.filter(leave=leave, task_type='unit_head', status='pending').exists())
