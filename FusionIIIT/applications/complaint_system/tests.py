from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
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

	def test_supervisor_list_includes_all_mapped_supervisor_types(self):
		Supervisor.objects.create(sup_id=self.faculty_extra, type='plumber')
		self._auth(self.faculty_user)
		response = self.client.get('/complaint/api/studentcomplain')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		complaints = response.data['student_complain']
		self.assertEqual(len(complaints), 2)
		types = sorted([item['complaint_type'] for item in complaints])
		self.assertEqual(types, ['internet', 'plumber'])

	def test_supervisor_area_scope_filters_complaints(self):
		Supervisor.objects.filter(sup_id=self.faculty_extra, type='internet').update(area='hall-3')
		self.complaint_2.complaint_type = 'internet'
		self.complaint_2.location = 'hall-1'
		self.complaint_2.save(update_fields=['complaint_type', 'location'])

		self._auth(self.faculty_user)
		response = self.client.get('/complaint/api/studentcomplain')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		complaints = response.data['student_complain']
		self.assertEqual(len(complaints), 1)
		self.assertEqual(complaints[0]['location'], 'hall-3')

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

	def test_create_rejects_invalid_attachment_type(self):
		self._auth(self.student_user)
		payload = {
			'complaint_type': 'internet',
			'location': 'hall-3',
			'specific_location': 'Room 110',
			'details': 'File type validation',
			'priority': 'Standard',
			'upload_complaint': SimpleUploadedFile(
				'bad.exe',
				b'bad-content',
				content_type='application/x-msdownload',
			),
		}
		response = self.client.post('/complaint/api/newcomplain', payload, format='multipart')
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn('upload_complaint', response.data)

	def test_create_rejects_oversized_attachment(self):
		self._auth(self.student_user)
		payload = {
			'complaint_type': 'internet',
			'location': 'hall-3',
			'specific_location': 'Room 110',
			'details': 'File size validation',
			'priority': 'Standard',
			'upload_complaint': SimpleUploadedFile(
				'large.pdf',
				b'a' * (5 * 1024 * 1024 + 1),
				content_type='application/pdf',
			),
		}
		response = self.client.post('/complaint/api/newcomplain', payload, format='multipart')
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn('upload_complaint', response.data)

	def test_create_draft_allows_partial_payload_and_skips_sla(self):
		self._auth(self.student_user)
		payload = {
			'location': 'hall-3',
			'details': '',
			'is_draft': True,
		}
		response = self.client.post('/complaint/api/newcomplain', payload, format='json')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		draft = StudentComplain.objects.get(id=response.data['id'])
		self.assertTrue(draft.is_draft)
		self.assertIsNone(draft.sla_deadline)
		self.assertTrue(str(draft.complaint_ref).startswith('DRF-'))
		self.assertTrue(ComplaintEvent.objects.filter(complaint=draft, action='draft_saved').exists())

	def test_drafts_are_hidden_from_caretaker_queue(self):
		StudentComplain.objects.create(
			complainer=self.student_extra,
			complaint_type='internet',
			location='hall-3',
			details='Draft complaint',
			is_draft=True,
		)
		self._auth(self.staff_user)
		response = self.client.get('/complaint/api/studentcomplain')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		for item in response.data['student_complain']:
			self.assertFalse(item.get('is_draft'))

	def test_submit_draft_starts_sla_and_assignment(self):
		draft = StudentComplain.objects.create(
			complainer=self.student_extra,
			complaint_type='internet',
			location='hall-3',
			details='Saved draft details',
			is_draft=True,
		)
		self._auth(self.student_user)
		response = self.client.post(f'/complaint/api/submitdraft/{draft.id}', {}, format='json')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		draft.refresh_from_db()
		self.assertFalse(draft.is_draft)
		self.assertIsNotNone(draft.submitted_at)
		self.assertIsNotNone(draft.sla_deadline)
		self.assertTrue(str(draft.complaint_ref).startswith('CMP-'))
		self.assertEqual(draft.assigned_to_id, self.internet_worker.id)
		self.assertTrue(ComplaintEvent.objects.filter(complaint=draft, action='draft_submitted').exists())

	def test_report_analytics_returns_kpis_and_status_logs(self):
		self.complaint_1.complaint_date = timezone.now() - timedelta(hours=10)
		self.complaint_1.sla_deadline = timezone.now() - timedelta(hours=1)
		self.complaint_1.resolved_at = timezone.now() - timedelta(hours=2)
		self.complaint_1.status = 2
		self.complaint_1.feedback = 'Resolved quickly'
		self.complaint_1.save(update_fields=['complaint_date', 'sla_deadline', 'resolved_at', 'status', 'feedback'])

		self.complaint_2.complaint_date = timezone.now() - timedelta(hours=100)
		self.complaint_2.sla_deadline = timezone.now() - timedelta(hours=90)
		self.complaint_2.closed_at = timezone.now() - timedelta(hours=10)
		self.complaint_2.status = 3
		self.complaint_2.reopen_requested = True
		self.complaint_2.save(update_fields=['complaint_date', 'sla_deadline', 'closed_at', 'status', 'reopen_requested'])

		ComplaintEvent.objects.create(complaint=self.complaint_1, actor=self.staff_extra, action='status_updated')
		ComplaintEvent.objects.create(complaint=self.complaint_1, actor=self.staff_extra, action='status_updated')
		ComplaintEvent.objects.create(complaint=self.complaint_2, actor=self.staff_extra, action='verified_and_closed')

		self._auth(self.superuser)
		response = self.client.get('/complaint/api/report-analytics')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['totals']['complaint_count'], 2)
		self.assertEqual(response.data['totals']['resolved_count'], 2)
		self.assertEqual(response.data['totals']['feedback_count'], 1)
		self.assertAlmostEqual(response.data['kpis']['avg_resolution_time_hours'], 49.0, delta=0.2)
		self.assertEqual(response.data['kpis']['sla_compliance_rate'], 50.0)
		self.assertEqual(response.data['kpis']['reopen_rate'], 50.0)
		self.assertEqual(response.data['kpis']['feedback_response_rate'], 50.0)
		actions = {entry['action']: entry['count'] for entry in response.data['status_logs']}
		self.assertEqual(actions.get('status_updated'), 2)
		self.assertIn('analytics', response.data)
		self.assertIn('category_hotspots', response.data['analytics'])
		self.assertIn('location_hotspots', response.data['analytics'])
		self.assertIn('recurring_issue_clusters', response.data['analytics'])
		self.assertIn('time_series', response.data['analytics'])

	def test_report_analytics_rejects_invalid_date_range(self):
		self._auth(self.superuser)
		response = self.client.get('/complaint/api/report-analytics?date_from=2026-04-20&date_to=2026-04-01')
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

	def test_report_analytics_denies_non_supervisor_user(self):
		self._auth(self.student_user)
		response = self.client.get('/complaint/api/report-analytics')
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_report_analytics_for_supervisor_is_scoped_to_supervisor_types(self):
		self._auth(self.faculty_user)
		response = self.client.get('/complaint/api/report-analytics')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['totals']['complaint_count'], 1)
		self.assertEqual(response.data['complaints'][0]['complaint_type'], 'internet')

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

	@patch('applications.complaint_system.notifications.complaint_system_notif')
	def test_sla_reminder_job_notifies_before_breach_and_logs_event(self, mocked_notif):
		self.complaint_1.sla_deadline = timezone.now() + timedelta(hours=2)
		self.complaint_1.assigned_to = self.internet_worker
		self.complaint_1.save(update_fields=['sla_deadline', 'assigned_to'])

		from applications.complaint_system.tasks import send_sla_deadline_reminders

		result = send_sla_deadline_reminders()
		self.assertEqual(result['reminder_count'], 1)
		self.assertIn(self.complaint_1.id, result['reminder_ids'])
		event = ComplaintEvent.objects.filter(complaint=self.complaint_1, action='sla_reminder_sent').first()
		self.assertIsNotNone(event)
		self.assertEqual(event.metadata.get('source'), 'automatic')
		self.assertTrue(mocked_notif.called)

	@patch('applications.complaint_system.notifications.complaint_system_notif')
	def test_sla_reminder_job_does_not_duplicate_for_same_deadline(self, mocked_notif):
		self.complaint_1.sla_deadline = timezone.now() + timedelta(hours=3)
		self.complaint_1.assigned_to = self.internet_worker
		self.complaint_1.save(update_fields=['sla_deadline', 'assigned_to'])

		from applications.complaint_system.tasks import send_sla_deadline_reminders

		first = send_sla_deadline_reminders()
		second = send_sla_deadline_reminders()

		self.assertEqual(first['reminder_count'], 1)
		self.assertEqual(second['reminder_count'], 0)
		self.assertEqual(
			ComplaintEvent.objects.filter(complaint=self.complaint_1, action='sla_reminder_sent').count(),
			1,
		)

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

	def test_feedback_submission_requires_closed_status_and_complainant(self):
		self._auth(self.student_user)
		not_closed = self.client.post(
			f'/complaint/api/feedback/{self.complaint_1.id}',
			{'feedback': 'good', 'rating': 4},
			format='json',
		)
		self.assertEqual(not_closed.status_code, status.HTTP_400_BAD_REQUEST)

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
		self.client.post(
			f'/complaint/api/verify/{self.complaint_1.id}',
			{'verification_source': 'complainant', 'verification_decision': 'approve'},
			format='json',
		)

		self._auth(self.other_student_user)
		forbidden = self.client.post(
			f'/complaint/api/feedback/{self.complaint_1.id}',
			{'feedback': 'not owner', 'rating': 3},
			format='json',
		)
		self.assertEqual(forbidden.status_code, status.HTTP_403_FORBIDDEN)

		self._auth(self.student_user)
		ok = self.client.post(
			f'/complaint/api/feedback/{self.complaint_1.id}',
			{'feedback': 'Issue fixed properly', 'rating': 5},
			format='json',
		)
		self.assertEqual(ok.status_code, status.HTTP_200_OK)
		self.complaint_1.refresh_from_db()
		self.assertEqual(self.complaint_1.feedback, 'Issue fixed properly')
		self.assertEqual(self.complaint_1.flag, 5)
		self.assertTrue(
			ComplaintEvent.objects.filter(complaint=self.complaint_1, action='feedback_submitted').exists()
		)

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

	def test_non_matching_supervisor_cannot_reopen(self):
		self._auth(self.staff_user)
		self.client.put(
			f'/complaint/api/updatecomplain/{self.complaint_2.id}',
			{'status': 1, 'remarks': 'in progress'},
			format='json',
		)
		self.client.put(
			f'/complaint/api/updatecomplain/{self.complaint_2.id}',
			{'status': 2, 'remarks': 'resolved'},
			format='json',
		)

		self._auth(self.faculty_user)
		response = self.client.post(
			f'/complaint/api/reopen/{self.complaint_2.id}',
			{'reopen_reason': 'Try reopen plumber complaint'},
			format='json',
		)
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

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

	@patch('applications.complaint_system.notifications.complaint_system_notif')
	def test_bulk_reassign_updates_assignment_and_notifies(self, mocked_notif):
		new_worker = Workers.objects.create(
			secincharge_id=self.secincharge,
			name='Replacement Worker',
			age='29',
			phone=8888888888,
			worker_type='internet',
		)

		self._auth(self.faculty_user)
		response = self.client.post(
			'/complaint/api/bulk-action',
			{
				'action': 'reassign',
				'complaint_ids': [self.complaint_1.id],
				'assigned_to': new_worker.id,
				'assigned_team': 'Night shift',
				'remarks': 'Reassigned for follow up',
			},
			format='json',
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.complaint_1.refresh_from_db()
		self.assertEqual(self.complaint_1.assigned_to_id, new_worker.id)
		self.assertEqual(self.complaint_1.assigned_team, 'Night shift')
		self.assertTrue(ComplaintEvent.objects.filter(complaint=self.complaint_1, action='bulk_reassigned').exists())
		self.assertTrue(mocked_notif.called)
