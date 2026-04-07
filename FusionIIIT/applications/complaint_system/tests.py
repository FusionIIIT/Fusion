from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch
from rest_framework import status
from rest_framework.test import APITestCase

from applications.complaint_system.models import (
	Caretaker,
	ComplaintEvent,
	SectionIncharge,
	StudentComplain,
	VerificationStatus,
	Supervisor,
	Workers,
)
from applications.globals.models import DepartmentInfo, ExtraInfo


class ComplaintApiTests(APITestCase):
	def setUp(self):
		self.department = DepartmentInfo.objects.create(name='CSE-Test')

		self.student_user = User.objects.create_user(username='student1', password='pass123')
		self.student_extra = ExtraInfo.objects.create(
			id='stu001',
			user=self.student_user,
			user_type='student',
			department=self.department,
		)

		self.other_student_user = User.objects.create_user(username='student2', password='pass123')
		self.other_student_extra = ExtraInfo.objects.create(
			id='stu002',
			user=self.other_student_user,
			user_type='student',
			department=self.department,
		)

		self.staff_user = User.objects.create_user(username='staff1', password='pass123')
		self.staff_extra = ExtraInfo.objects.create(
			id='stf001',
			user=self.staff_user,
			user_type='staff',
			department=self.department,
		)
		Caretaker.objects.create(staff_id=self.staff_extra, area='hall-3')
		self.secincharge = SectionIncharge.objects.create(
			staff_id=self.staff_extra,
			work_type='internet',
		)
		self.internet_worker = Workers.objects.create(
			secincharge_id=self.secincharge,
			name='Internet Worker',
			age='32',
			phone=9999999999,
			worker_type='internet',
		)

		self.faculty_user = User.objects.create_user(username='faculty1', password='pass123')
		self.faculty_extra = ExtraInfo.objects.create(
			id='fac001',
			user=self.faculty_user,
			user_type='faculty',
			department=self.department,
		)
		Supervisor.objects.create(sup_id=self.faculty_extra, type='internet')

		self.superuser = User.objects.create_superuser(
			username='admin1', email='admin@test.com', password='pass123'
		)
		self.super_extra = ExtraInfo.objects.create(
			id='adm001',
			user=self.superuser,
			user_type='staff',
			department=self.department,
		)

		self.complaint_1 = StudentComplain.objects.create(
			complainer=self.student_extra,
			complaint_type='internet',
			location='hall-3',
			details='Wifi not working',
			specific_location='Room 101',
		)
		self.complaint_2 = StudentComplain.objects.create(
			complainer=self.other_student_extra,
			complaint_type='plumber',
			location='hall-1',
			details='Leakage in washroom',
			specific_location='Ground floor',
		)

	def _auth(self, user):
		self.client.force_authenticate(user=user)

	def test_list_requires_authentication(self):
		response = self.client.get('/complaint/api/studentcomplain')
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_student_list_returns_only_own_complaints(self):
		self._auth(self.student_user)
		response = self.client.get('/complaint/api/studentcomplain')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		complaints = response.data['student_complain']
		self.assertEqual(len(complaints), 1)
		self.assertEqual(complaints[0]['id'], self.complaint_1.id)

	def test_caretaker_list_filters_by_area(self):
		self._auth(self.staff_user)
		response = self.client.get('/complaint/api/studentcomplain')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		complaints = response.data['student_complain']
		self.assertEqual(len(complaints), 1)
		self.assertEqual(complaints[0]['location'], 'hall-3')

	def test_supervisor_list_filters_by_type(self):
		self._auth(self.faculty_user)
		response = self.client.get('/complaint/api/studentcomplain')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		complaints = response.data['student_complain']
		self.assertEqual(len(complaints), 1)
		self.assertEqual(complaints[0]['complaint_type'], 'internet')

	def test_create_sets_logged_in_user_as_complainer(self):
		self._auth(self.student_user)
		payload = {
			'complaint_type': 'garbage',
			'location': 'hall-3',
			'specific_location': 'Near lift',
			'details': 'Garbage not cleared',
			'priority': 'Standard',
			# Even if payload tries to spoof complainer, backend should ignore it.
			'complainer': self.other_student_extra.id,
		}
		response = self.client.post('/complaint/api/newcomplain', payload, format='json')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		created = StudentComplain.objects.get(id=response.data['id'])
		self.assertEqual(created.complainer_id, self.student_extra.id)
		self.assertTrue(created.complaint_ref)
		self.assertGreaterEqual(len(created.complaint_ref), 10)
		self.assertTrue(created.sla_deadline)
		self.assertTrue(ComplaintEvent.objects.filter(complaint=created, action='created').exists())
		self.assertEqual(created.assigned_to_id, self.internet_worker.id)

	def test_sla_deadline_respects_priority(self):
		self._auth(self.student_user)
		payload = {
			'complaint_type': 'internet',
			'location': 'hall-3',
			'specific_location': 'Room 102',
			'details': 'No internet',
			'priority': 'Urgent',
		}
		response = self.client.post('/complaint/api/newcomplain', payload, format='json')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		created = StudentComplain.objects.get(id=response.data['id'])
		delta_hours = (created.sla_deadline - created.complaint_date).total_seconds() / 3600
		self.assertLessEqual(delta_hours, 25)
		self.assertGreaterEqual(delta_hours, 23)

	def test_assignment_falls_back_to_any_worker_when_no_category_match(self):
		self._auth(self.student_user)
		payload = {
			'complaint_type': 'garbage',
			'location': 'NR3',
			'specific_location': 'Main gate',
			'details': 'Garbage pileup',
			'priority': 'Low',
		}
		response = self.client.post('/complaint/api/newcomplain', payload, format='json')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		created = StudentComplain.objects.get(id=response.data['id'])
		self.assertEqual(created.assigned_to_id, self.internet_worker.id)
		event = ComplaintEvent.objects.filter(complaint=created, action='created').first()
		self.assertIsNotNone(event)
		self.assertEqual(event.metadata.get('assignment_strategy'), 'any_worker')

	def test_create_requires_category_location_and_description(self):
		self._auth(self.student_user)
		payload = {
			'complaint_type': '',
			'location': '',
			'details': '',
		}
		response = self.client.post('/complaint/api/newcomplain', payload, format='json')
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn('complaint_type', response.data)

	def test_escalation_rejects_empty_reason(self):
		self._auth(self.staff_user)
		response = self.client.post(
			f'/complaint/api/escalate/{self.complaint_1.id}',
			{'escalation_reason': ''},
			format='json',
		)
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.complaint_1.refresh_from_db()
		self.assertEqual(self.complaint_1.status, 0)

	@patch('applications.complaint_system.escalation.complaint_system_notif')
	def test_manual_escalation_logs_history_and_notifies_supervisor(self, mocked_notif):
		self._auth(self.staff_user)
		response = self.client.post(
			f'/complaint/api/escalate/{self.complaint_1.id}',
			{'escalation_reason': 'Needs supervisor review'},
			format='json',
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.complaint_1.refresh_from_db()
		self.assertEqual(self.complaint_1.status, 4)
		event = ComplaintEvent.objects.filter(complaint=self.complaint_1, action='escalated').first()
		self.assertIsNotNone(event)
		self.assertEqual(event.note, 'Needs supervisor review')
		self.assertTrue(mocked_notif.called)

	@patch('applications.complaint_system.escalation.complaint_system_notif')
	def test_auto_escalation_job_escalates_overdue_complaints(self, mocked_notif):
		self.complaint_1.sla_deadline = timezone.now() - timedelta(hours=1)
		self.complaint_1.save(update_fields=['sla_deadline'])

		from applications.complaint_system.tasks import escalate_overdue_complaints

		result = escalate_overdue_complaints()
		self.assertEqual(result['escalated_count'], 1)
		self.complaint_1.refresh_from_db()
		self.assertEqual(self.complaint_1.status, 4)
		event = ComplaintEvent.objects.filter(complaint=self.complaint_1, action='auto_escalated').first()
		self.assertIsNotNone(event)
		self.assertEqual(event.metadata.get('source'), 'automatic')
		self.assertTrue(mocked_notif.called)

	def test_detail_denies_unrelated_student(self):
		self._auth(self.other_student_user)
		response = self.client.get(f'/complaint/api/user/detail/{self.complaint_1.id}/')
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_owner_can_update_description_but_cannot_change_status(self):
		self._auth(self.student_user)

		update_response = self.client.put(
			f'/complaint/api/updatecomplain/{self.complaint_1.id}',
			{'details': 'Wifi down since morning'},
			format='json',
		)
		self.assertEqual(update_response.status_code, status.HTTP_200_OK)
		self.complaint_1.refresh_from_db()
		self.assertEqual(self.complaint_1.details, 'Wifi down since morning')

		status_update_response = self.client.put(
			f'/complaint/api/updatecomplain/{self.complaint_1.id}',
			{'status': 1},
			format='json',
		)
		self.assertEqual(status_update_response.status_code, status.HTTP_403_FORBIDDEN)
		self.complaint_1.refresh_from_db()
		self.assertEqual(self.complaint_1.status, 0)

	def test_caretaker_can_change_status(self):
		self._auth(self.staff_user)

		in_progress_response = self.client.put(
			f'/complaint/api/updatecomplain/{self.complaint_1.id}',
			{'status': 1, 'remarks': 'started'},
			format='json',
		)
		self.assertEqual(in_progress_response.status_code, status.HTTP_200_OK)

		update_response = self.client.put(
			f'/complaint/api/updatecomplain/{self.complaint_1.id}',
			{'status': 2},
			format='json',
		)
		self.assertEqual(update_response.status_code, status.HTTP_200_OK)
		self.complaint_1.refresh_from_db()
		self.assertEqual(self.complaint_1.status, 2)

	def test_invalid_status_transition_is_rejected(self):
		self._auth(self.staff_user)
		response = self.client.put(
			f'/complaint/api/updatecomplain/{self.complaint_1.id}',
			{'status': 2},
			format='json',
		)
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

	def test_resolution_requires_remarks(self):
		self._auth(self.staff_user)
		response = self.client.put(
			f'/complaint/api/updatecomplain/{self.complaint_1.id}',
			{'status': 1, 'remarks': '   '},
			format='json',
		)
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

	def test_closure_requires_verification_endpoint(self):
		self._auth(self.staff_user)
		response = self.client.put(
			f'/complaint/api/updatecomplain/{self.complaint_1.id}',
			{'status': 3, 'verification_source': 'complainant'},
			format='json',
		)
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

	def test_verify_closes_only_resolved_complaints(self):
		self._auth(self.staff_user)

		not_resolved = self.client.post(
			f'/complaint/api/verify/{self.complaint_1.id}',
			{'verification_source': 'complainant'},
			format='json',
		)
		self.assertEqual(not_resolved.status_code, status.HTTP_400_BAD_REQUEST)

		self.client.put(
			f'/complaint/api/updatecomplain/{self.complaint_1.id}',
			{'status': 1, 'remarks': 'in progress'},
			format='json',
		)
		self.client.put(
			f'/complaint/api/updatecomplain/{self.complaint_1.id}',
			{'status': 2, 'remarks': 'resolved'},
			format='json',
		)

		self._auth(self.student_user)
		verified = self.client.post(
			f'/complaint/api/verify/{self.complaint_1.id}',
			{'verification_source': 'complainant', 'verification_decision': 'approve'},
			format='json',
		)
		self.assertEqual(verified.status_code, status.HTTP_200_OK)
		self.complaint_1.refresh_from_db()
		self.assertEqual(self.complaint_1.status, 3)
		self.assertEqual(self.complaint_1.verification_status, VerificationStatus.APPROVED)

	def test_supervisor_can_reject_a_resolved_complaint(self):
		self._auth(self.staff_user)
		self.client.put(
			f'/complaint/api/updatecomplain/{self.complaint_1.id}',
			{'status': 1, 'remarks': 'in progress'},
			format='json',
		)
		self.client.put(
			f'/complaint/api/updatecomplain/{self.complaint_1.id}',
			{'status': 2, 'remarks': 'resolved'},
			format='json',
		)

		self._auth(self.faculty_user)
		response = self.client.post(
			f'/complaint/api/verify/{self.complaint_1.id}',
			{
				'verification_source': 'supervisor',
				'verification_decision': 'reject',
				'verification_notes': 'Issue still persists',
			},
			format='json',
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.complaint_1.refresh_from_db()
		self.assertEqual(self.complaint_1.status, 5)
		self.assertEqual(self.complaint_1.verification_status, VerificationStatus.REJECTED)
		self.assertTrue(self.complaint_1.reopen_requested)

	def test_reopen_requires_non_empty_reason(self):
		self._auth(self.staff_user)
		self.client.put(
			f'/complaint/api/updatecomplain/{self.complaint_1.id}',
			{'status': 1, 'remarks': 'in progress'},
			format='json',
		)
		self.client.put(
			f'/complaint/api/updatecomplain/{self.complaint_1.id}',
			{'status': 2, 'remarks': 'resolved'},
			format='json',
		)

		response = self.client.post(
			f'/complaint/api/reopen/{self.complaint_1.id}',
			{'reopen_reason': '   '},
			format='json',
		)
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

	def test_reopen_rejects_expired_window(self):
		self._auth(self.student_user)
		self.client.put(
			f'/complaint/api/updatecomplain/{self.complaint_1.id}',
			{'status': 1, 'remarks': 'in progress'},
			format='json',
		)
		self.client.put(
			f'/complaint/api/updatecomplain/{self.complaint_1.id}',
			{'status': 2, 'remarks': 'resolved'},
			format='json',
		)
		self.complaint_1.refresh_from_db()
		self.complaint_1.resolved_at = timezone.now() - timedelta(days=8)
		self.complaint_1.save(update_fields=['resolved_at'])

		response = self.client.post(
			f'/complaint/api/reopen/{self.complaint_1.id}',
			{'reopen_reason': 'Still broken'},
			format='json',
		)
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

	def test_assigned_caretaker_can_submit_progress_update(self):
		self._auth(self.staff_user)
		self.complaint_1.assigned_to = self.internet_worker
		self.complaint_1.save(update_fields=['assigned_to'])

		response = self.client.post(
			f'/complaint/api/caretaker-action/{self.complaint_1.id}',
			{
				'status': 1,
				'remarks': 'Started troubleshooting',
				'progress_notes': 'Checked router and local switch',
			},
			format='multipart',
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.complaint_1.refresh_from_db()
		self.assertEqual(self.complaint_1.status, 1)
		self.assertEqual(self.complaint_1.remarks, 'Started troubleshooting')

	def test_unassigned_caretaker_cannot_submit_progress_update(self):
		other_staff = User.objects.create_user(username='staff2', password='pass123')
		other_extra = ExtraInfo.objects.create(
			id='stf002',
			user=other_staff,
			user_type='staff',
			department=self.department,
		)
		Caretaker.objects.create(staff_id=other_extra, area='hall-1')

		self._auth(other_staff)
		self.complaint_1.assigned_to = self.internet_worker
		self.complaint_1.save(update_fields=['assigned_to'])

		response = self.client.post(
			f'/complaint/api/caretaker-action/{self.complaint_1.id}',
			{'status': 1, 'remarks': 'Attempted update'},
			format='multipart',
		)
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_caretaker_progress_update_rejects_invalid_transition(self):
		self._auth(self.staff_user)
		self.complaint_1.assigned_to = self.internet_worker
		self.complaint_1.save(update_fields=['assigned_to'])

		response = self.client.post(
			f'/complaint/api/caretaker-action/{self.complaint_1.id}',
			{'status': 2, 'remarks': 'Resolved directly'},
			format='multipart',
		)
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

	def test_owner_can_delete(self):
		self._auth(self.student_user)

		delete_response = self.client.delete(f'/complaint/api/removecomplain/{self.complaint_1.id}')
		self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
		self.assertFalse(StudentComplain.objects.filter(id=self.complaint_1.id).exists())

	@patch('applications.complaint_system.notifications.complaint_system_notif')
	def test_create_complaint_sends_notifications(self, mocked_notif):
		self._auth(self.student_user)
		payload = {
			'complaint_type': 'internet',
			'location': 'hall-3',
			'specific_location': 'Room 110',
			'details': 'Frequent disconnects',
			'priority': 'Standard',
		}
		response = self.client.post('/complaint/api/newcomplain', payload, format='json')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertTrue(mocked_notif.called)

	@patch('applications.complaint_system.notifications.complaint_system_notif')
	def test_status_update_sends_notifications(self, mocked_notif):
		self._auth(self.staff_user)
		response = self.client.post(
			f'/complaint/api/caretaker-action/{self.complaint_1.id}',
			{'status': 1, 'remarks': 'Work started'},
			format='multipart',
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertTrue(mocked_notif.called)

	@patch('applications.complaint_system.notifications.complaint_system_notif')
	def test_verification_and_reopen_notifications_are_sent(self, mocked_notif):
		self._auth(self.staff_user)
		self.client.put(
			f'/complaint/api/updatecomplain/{self.complaint_1.id}',
			{'status': 1, 'remarks': 'in progress'},
			format='json',
		)
		self.client.put(
			f'/complaint/api/updatecomplain/{self.complaint_1.id}',
			{'status': 2, 'remarks': 'resolved'},
			format='json',
		)

		self._auth(self.student_user)
		verify_resp = self.client.post(
			f'/complaint/api/verify/{self.complaint_1.id}',
			{'verification_source': 'complainant', 'verification_decision': 'approve'},
			format='json',
		)
		self.assertEqual(verify_resp.status_code, status.HTTP_200_OK)
		self.assertTrue(mocked_notif.called)

		mocked_notif.reset_mock()
		reopen_resp = self.client.post(
			f'/complaint/api/reopen/{self.complaint_1.id}',
			{'reopen_reason': 'Issue still present'},
			format='json',
		)
		self.assertEqual(reopen_resp.status_code, status.HTTP_200_OK)
		self.assertTrue(mocked_notif.called)
