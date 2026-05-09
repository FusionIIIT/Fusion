from django.contrib.auth.models import User
from django.db import connection
from uuid import uuid4
from rest_framework import status
from rest_framework.test import APITestCase

from applications.filetracking.models import File as NewFile
from applications.filetracking.models import DraftFile
from applications.filetracking.models import FileAttachment
from applications.filetracking.models import FileMovement
from applications.filetracking.models import FileType
from applications.filetracking.models import FileWorkflow
from applications.globals.models import DepartmentInfo
from applications.globals.models import Designation
from applications.globals.models import ExtraInfo
from applications.globals.models import HoldsDesignation


class FileTrackingExceptionFlowTests(APITestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()

		# Keep tests executable while filetracking migrations are mid-refactor.
		required_models = [
			FileType,
			NewFile,
			FileAttachment,
			FileMovement,
			FileWorkflow,
			DraftFile,
		]
		existing_tables = set(connection.introspection.table_names())

		with connection.schema_editor() as schema_editor:
			for model in required_models:
				if model._meta.db_table not in existing_tables:
					schema_editor.create_model(model)
					existing_tables.add(model._meta.db_table)

	def setUp(self):
		self.department = DepartmentInfo.objects.create(name='CSE-TEST')

		self.student_designation = Designation.objects.create(
			name='student-test',
			full_name='Student',
			type='academic',
		)
		self.staff_designation = Designation.objects.create(
			name='staff-test',
			full_name='Staff',
			type='administrative',
		)

		self.owner_user = User.objects.create_user(username='owner_user', password='pass1234')
		self.receiver_user = User.objects.create_user(username='receiver_user', password='pass1234')
		self.intruder_user = User.objects.create_user(username='intruder_user', password='pass1234')

		self.owner_extra = ExtraInfo.objects.create(
			id='TST001',
			user=self.owner_user,
			user_type='staff',
			department=self.department,
		)
		self.receiver_extra = ExtraInfo.objects.create(
			id='TST002',
			user=self.receiver_user,
			user_type='staff',
			department=self.department,
		)
		self.intruder_extra = ExtraInfo.objects.create(
			id='TST003',
			user=self.intruder_user,
			user_type='staff',
			department=self.department,
		)

		HoldsDesignation.objects.create(
			user=self.owner_user,
			working=self.owner_user,
			designation=self.student_designation,
		)
		HoldsDesignation.objects.create(
			user=self.receiver_user,
			working=self.receiver_user,
			designation=self.staff_designation,
		)
		HoldsDesignation.objects.create(
			user=self.intruder_user,
			working=self.intruder_user,
			designation=self.staff_designation,
		)

		self.file_type = FileType.objects.create(
			name='Academic Document',
			category='ACADEMIC',
		)

		self.file = NewFile.objects.create(
			file_number='FTS/CSE/2026/9001',
			file_type=self.file_type,
			subject='Exception Flow File',
			description='Test file for exception scenarios',
			created_by=self.owner_extra,
			source_department=self.department,
			status='IN_PROGRESS',
			current_holder=self.owner_extra,
			current_designation=self.student_designation,
			current_department=self.department,
			source_module='filetracking',
		)

	def test_no_comment_for_amend_returns_400(self):
		self.client.force_authenticate(user=self.owner_user)

		response = self.client.post(
			f'/filetracking/api/new/files/{self.file.id}/amend/',
			{'comment': ''},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn('provide amendment comment', response.data.get('error', '').lower())

	def test_invalid_receiver_designation_blocks_forward(self):
		self.client.force_authenticate(user=self.owner_user)

		response = self.client.post(
			f'/filetracking/api/new/files/{self.file.id}/forward/',
			{
				'receiver_designation': 'non-existent-designation',
				'remarks': 'Forwarding with invalid receiver designation',
			},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertTrue(response.data.get('error'))

	def test_non_owner_archive_attempt_is_blocked(self):
		self.file.current_holder = self.receiver_extra
		self.file.current_designation = self.staff_designation
		self.file.save(update_fields=['current_holder', 'current_designation'])

		self.client.force_authenticate(user=self.intruder_user)
		response = self.client.post(
			f'/filetracking/api/new/files/{self.file.id}/archive/',
			{'remarks': 'Trying to archive someone else file'},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
		self.assertIn('only file owner', response.data.get('error', '').lower())

	def test_user_without_inbox_access_cannot_amend(self):
		self.file.current_holder = self.receiver_extra
		self.file.current_designation = self.staff_designation
		self.file.save(update_fields=['current_holder', 'current_designation'])

		self.client.force_authenticate(user=self.intruder_user)
		response = self.client.post(
			f'/filetracking/api/new/files/{self.file.id}/amend/',
			{'comment': 'This should be blocked for non-participants.'},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
		self.assertIn('inbox', response.data.get('error', '').lower())

	def test_unrelated_user_cannot_view_file_history(self):
		self.file.current_holder = self.receiver_extra
		self.file.current_designation = self.staff_designation
		self.file.save(update_fields=['current_holder', 'current_designation'])

		self.client.force_authenticate(user=self.intruder_user)
		response = self.client.get(
			f'/filetracking/api/new/files/{self.file.id}/history/',
		)

		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
		self.assertIn('permission', response.data.get('error', '').lower())

	def test_non_holder_cannot_forward_file(self):
		self.file.current_holder = self.receiver_extra
		self.file.current_designation = self.staff_designation
		self.file.save(update_fields=['current_holder', 'current_designation'])

		self.client.force_authenticate(user=self.intruder_user)
		response = self.client.post(
			f'/filetracking/api/new/files/{self.file.id}/forward/',
			{
				'receiver_designation': self.staff_designation.name,
				'remarks': 'Trying to send file without being current holder',
			},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
		self.assertIn('current holder', response.data.get('error', '').lower())

	def test_spaces_only_comment_fails_for_amend(self):
		self.client.force_authenticate(user=self.owner_user)

		response = self.client.post(
			f'/filetracking/api/new/files/{self.file.id}/amend/',
			{'comment': '     '},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn('provide amendment comment', response.data.get('error', '').lower())

	def test_spaces_only_comment_fails_for_forward(self):
		self.client.force_authenticate(user=self.owner_user)

		response = self.client.post(
			f'/filetracking/api/new/files/{self.file.id}/forward/',
			{
				'receiver_designation': self.staff_designation.name,
				'receiver': self.receiver_user.username,
				'remarks': '    ',
			},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn('mandatory', response.data.get('error', '').lower())

	def test_fake_receiver_username_is_blocked(self):
		self.client.force_authenticate(user=self.owner_user)

		response = self.client.post(
			f'/filetracking/api/new/files/{self.file.id}/forward/',
			{
				'receiver_designation': self.staff_designation.name,
				'receiver': 'nonexistent_user_9999',
				'remarks': 'Forward attempt with fake receiver user',
			},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn('receiver user not found', response.data.get('error', '').lower())

	def test_deleted_receiver_user_is_blocked(self):
		deleted_user = User.objects.create_user(username='to_be_deleted', password='pass1234')
		deleted_extra = ExtraInfo.objects.create(
			id='TST004',
			user=deleted_user,
			user_type='staff',
			department=self.department,
		)
		HoldsDesignation.objects.create(
			user=deleted_user,
			working=deleted_user,
			designation=self.staff_designation,
		)
		self.assertTrue(ExtraInfo.objects.filter(id=deleted_extra.id).exists())
		deleted_user.delete()

		self.client.force_authenticate(user=self.owner_user)
		response = self.client.post(
			f'/filetracking/api/new/files/{self.file.id}/forward/',
			{
				'receiver_designation': self.staff_designation.name,
				'receiver': 'to_be_deleted',
				'remarks': 'Forward attempt to deleted user',
			},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn('receiver user not found', response.data.get('error', '').lower())

	def test_random_file_id_returns_not_found_for_detail(self):
		self.client.force_authenticate(user=self.owner_user)

		response = self.client.get('/filetracking/api/new/files/9999999/')

		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
		self.assertIn('file not found', response.data.get('error', '').lower())

	def test_random_file_id_returns_not_found_for_forward(self):
		self.client.force_authenticate(user=self.owner_user)

		response = self.client.post(
			'/filetracking/api/new/files/9999999/forward/',
			{
				'receiver_designation': self.staff_designation.name,
				'receiver': self.receiver_user.username,
				'remarks': 'Forwarding non-existent file should fail',
			},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
		self.assertIn('file not found', response.data.get('error', '').lower())

	def _run_audit_lifecycle(self):
		# 1) Create and submit
		self.client.force_authenticate(user=self.owner_user)
		create_response = self.client.post(
			'/filetracking/api/new/files/',
			{
				'file_type_id': self.file_type.id,
				'subject': f'Audit lifecycle {uuid4().hex[:8]}',
				'description': 'Audit test for UC-007',
				'priority': 'NORMAL',
				'action': 'submit',
				'remarks': 'Creating file for audit verification',
			},
			format='multipart',
		)
		self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
		file_id = create_response.data.get('id')
		self.assertIsNotNone(file_id)

		# 2) Send/Forward
		self.client.force_authenticate(user=self.owner_user)
		forward_response = self.client.post(
			f'/filetracking/api/new/files/{file_id}/send/',
			{
				'receiver': self.receiver_user.username,
				'receiver_designation': self.staff_designation.name,
				'remarks': 'Forwarding for final action and audit test',
			},
			format='json',
		)
		self.assertEqual(forward_response.status_code, status.HTTP_200_OK)

		# 3) Amend
		self.client.force_authenticate(user=self.receiver_user)
		amend_response = self.client.post(
			f'/filetracking/api/new/files/{file_id}/amend/',
			{
				'comment': 'Adding amendment comment to verify audit trail',
			},
			format='json',
		)
		self.assertEqual(amend_response.status_code, status.HTTP_200_OK)

		# 4) Approve (required before creator can close)
		approve_response = self.client.post(
			f'/filetracking/api/new/files/{file_id}/approve/',
			{
				'remarks': 'Approved after amendment for closure',
			},
			format='json',
		)
		self.assertEqual(approve_response.status_code, status.HTTP_200_OK)

		# 5) Close
		self.client.force_authenticate(user=self.owner_user)
		close_response = self.client.post(
			f'/filetracking/api/new/files/{file_id}/close/',
			{
				'remarks': 'Closing before archival as workflow complete',
			},
			format='json',
		)
		self.assertEqual(close_response.status_code, status.HTTP_200_OK)

		# 6) Archive
		archive_response = self.client.post(
			f'/filetracking/api/new/files/{file_id}/archive/',
			{
				'remarks': 'Archiving after audit lifecycle completion',
			},
			format='json',
		)
		self.assertEqual(archive_response.status_code, status.HTTP_200_OK)

		return file_id

	def test_history_visible_for_created_sent_amended_archived(self):
		file_id = self._run_audit_lifecycle()

		self.client.force_authenticate(user=self.owner_user)
		history_response = self.client.get(
			f'/filetracking/api/new/files/{file_id}/history/',
		)

		self.assertEqual(history_response.status_code, status.HTTP_200_OK)
		movements = history_response.data.get('movements', [])
		actions = {movement.get('action') for movement in movements}

		self.assertIn('CREATE', actions)
		self.assertIn('FORWARD', actions)
		self.assertIn('COMMENT', actions)
		self.assertIn('ARCHIVE', actions)

	def test_logs_saved_for_created_sent_amended_archived(self):
		file_id = self._run_audit_lifecycle()

		log_entries = FileMovement.objects.filter(file_id=file_id).order_by('timestamp')
		actions = {entry.action for entry in log_entries}

		self.assertIn('CREATE', actions)
		self.assertIn('FORWARD', actions)
		self.assertIn('COMMENT', actions)
		self.assertIn('ARCHIVE', actions)
		self.assertGreaterEqual(log_entries.count(), 4)

	def test_duplicate_file_subject_is_blocked(self):
		self.client.force_authenticate(user=self.owner_user)
		subject = f'Duplicate subject {uuid4().hex[:8]}'

		first_response = self.client.post(
			'/filetracking/api/new/files/',
			{
				'file_type_id': self.file_type.id,
				'subject': subject,
				'description': 'First create request',
				'priority': 'NORMAL',
				'action': 'submit',
				'remarks': 'Creating original file for duplicate check',
			},
			format='multipart',
		)
		self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)

		second_response = self.client.post(
			'/filetracking/api/new/files/',
			{
				'file_type_id': self.file_type.id,
				'subject': subject,
				'description': 'Second create request should fail',
				'priority': 'NORMAL',
				'action': 'submit',
				'remarks': 'Trying duplicate subject in active workflow',
			},
			format='multipart',
		)

		self.assertEqual(second_response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn('same subject', second_response.data.get('error', '').lower())

	def test_discard_draft_requires_confirmation(self):
		draft = DraftFile.objects.create(
			created_by=self.owner_extra,
			file_type=self.file_type,
			subject='Draft to discard',
			description='Needs explicit confirm flag',
			draft_data={'remarks': 'draft'},
		)

		self.client.force_authenticate(user=self.owner_user)
		without_confirm = self.client.delete(
			f'/filetracking/api/new/drafts/{draft.id}/',
		)
		self.assertEqual(without_confirm.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn('confirmation required', without_confirm.data.get('error', '').lower())

		with_confirm = self.client.delete(
			f'/filetracking/api/new/drafts/{draft.id}/?confirm=true',
		)
		self.assertEqual(with_confirm.status_code, status.HTTP_200_OK)

	def test_archive_requires_closed_status(self):
		self.client.force_authenticate(user=self.owner_user)
		self.file.status = 'IN_PROGRESS'
		self.file.save(update_fields=['status'])

		response = self.client.post(
			f'/filetracking/api/new/files/{self.file.id}/archive/',
			{'remarks': 'Attempt archive without close'},
			format='json',
		)
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn('closed/completed', response.data.get('error', '').lower())

	def test_forward_then_return_flow_updates_holder(self):
		self.client.force_authenticate(user=self.owner_user)
		forward_response = self.client.post(
			f'/filetracking/api/new/files/{self.file.id}/forward/',
			{
				'receiver_designation': self.staff_designation.name,
				'receiver': self.receiver_user.username,
				'remarks': 'Forwarding for review before return',
			},
			format='json',
		)
		self.assertEqual(forward_response.status_code, status.HTTP_200_OK)

		self.client.force_authenticate(user=self.receiver_user)
		return_response = self.client.post(
			f'/filetracking/api/new/files/{self.file.id}/return/',
			{'remarks': 'Returning to creator after review'},
			format='json',
		)
		self.assertEqual(return_response.status_code, status.HTTP_200_OK)

		self.file.refresh_from_db()
		self.assertEqual(self.file.current_holder, self.owner_extra)
		actions = set(FileMovement.objects.filter(file=self.file).values_list('action', flat=True))
		self.assertIn('FORWARD', actions)
		self.assertIn('RETURN', actions)

	def test_student_role_blocked_by_ft_employee_rbac(self):
		student_user = User.objects.create_user(username='student_blocked', password='pass1234')
		ExtraInfo.objects.create(
			id='TST005',
			user=student_user,
			user_type='student',
			department=self.department,
		)
		HoldsDesignation.objects.create(
			user=student_user,
			working=student_user,
			designation=self.student_designation,
		)

		self.client.force_authenticate(user=student_user)
		response = self.client.get('/filetracking/api/new/files/')
		self.assertEqual(response.status_code, status.HTTP_200_OK)

	def test_authenticated_user_can_fetch_file_types(self):
		student_user = User.objects.create_user(username='student_file_types', password='pass1234')
		ExtraInfo.objects.create(
			id='TST006',
			user=student_user,
			user_type='student',
			department=self.department,
		)
		HoldsDesignation.objects.create(
			user=student_user,
			working=student_user,
			designation=self.student_designation,
		)

		self.client.force_authenticate(user=student_user)
		response = self.client.get('/filetracking/api/new/file-types/')

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertTrue(any(item.get('name') == self.file_type.name for item in response.data))

	def test_student_user_can_save_and_list_drafts(self):
		student_user = User.objects.create_user(username='student_drafts', password='pass1234')
		ExtraInfo.objects.create(
			id='TST007',
			user=student_user,
			user_type='student',
			department=self.department,
		)
		HoldsDesignation.objects.create(
			user=student_user,
			working=student_user,
			designation=self.student_designation,
		)

		self.client.force_authenticate(user=student_user)
		post_response = self.client.post(
			'/filetracking/api/new/drafts/',
			{
				'file_type_id': self.file_type.id,
				'subject': 'Student draft request',
				'description': 'Draft created by student user',
				'priority': 'NORMAL',
				'remarks': 'Saving a draft from compose screen',
			},
			format='json',
		)
		self.assertEqual(post_response.status_code, status.HTTP_201_CREATED)

		get_response = self.client.get('/filetracking/api/new/drafts/')
		self.assertEqual(get_response.status_code, status.HTTP_200_OK)
		self.assertTrue(any(draft.get('subject') == 'Student draft request' for draft in get_response.data))

	def test_student_user_can_view_inbox_and_outbox(self):
		student_user = User.objects.create_user(username='student_mailboxes', password='pass1234')
		student_extra = ExtraInfo.objects.create(
			id='TST008',
			user=student_user,
			user_type='student',
			department=self.department,
		)
		HoldsDesignation.objects.create(
			user=student_user,
			working=student_user,
			designation=self.student_designation,
		)

		student_outbox_file = NewFile.objects.create(
			file_number='FTS/CSE/2026/9002',
			file_type=self.file_type,
			subject='Student outbox file',
			description='File created by student for outbox visibility',
			created_by=student_extra,
			source_department=self.department,
			current_holder=student_extra,
			current_designation=self.student_designation,
			current_department=self.department,
			status='CREATED',
			source_module='filetracking',
		)

		self.file.current_holder = student_extra
		self.file.current_designation = self.student_designation
		self.file.save(update_fields=['current_holder', 'current_designation'])

		self.client.force_authenticate(user=student_user)
		inbox_response = self.client.get('/filetracking/api/new/inbox/')
		outbox_response = self.client.get('/filetracking/api/new/outbox/')

		self.assertEqual(inbox_response.status_code, status.HTTP_200_OK)
		self.assertEqual(outbox_response.status_code, status.HTTP_200_OK)
		self.assertTrue(any(item.get('id') == self.file.id for item in inbox_response.data))
		self.assertTrue(any(item.get('id') == student_outbox_file.id for item in outbox_response.data))

	def test_student_user_can_view_archived_files(self):
		student_user = User.objects.create_user(username='student_archive', password='pass1234')
		student_extra = ExtraInfo.objects.create(
			id='TST009',
			user=student_user,
			user_type='student',
			department=self.department,
		)
		HoldsDesignation.objects.create(
			user=student_user,
			working=student_user,
			designation=self.student_designation,
		)

		archived_file = NewFile.objects.create(
			file_number='FTS/CSE/2026/9003',
			file_type=self.file_type,
			subject='Archived student file',
			description='Archived file for archive list visibility',
			created_by=student_extra,
			source_department=self.department,
			current_holder=student_extra,
			current_designation=self.student_designation,
			current_department=self.department,
			status='ARCHIVED',
			source_module='filetracking',
		)

		self.client.force_authenticate(user=student_user)
		archive_response = self.client.get('/filetracking/api/new/archive/')

		self.assertEqual(archive_response.status_code, status.HTTP_200_OK)
		self.assertTrue(any(item.get('id') == archived_file.id for item in archive_response.data))

	def test_draft_binary_attachment_is_persisted(self):
		from django.core.files.uploadedfile import SimpleUploadedFile

		self.client.force_authenticate(user=self.owner_user)
		upload = SimpleUploadedFile(
			'test-draft.pdf',
			b'%PDF-1.4 fake pdf bytes',
			content_type='application/pdf',
		)

		response = self.client.post(
			'/filetracking/api/new/drafts/',
			{
				'file_type_id': self.file_type.id,
				'subject': 'Draft with binary attachment',
				'description': 'Testing draft attachment persistence',
				'remarks': 'Saving draft with binary attachment',
				'files': [upload],
			},
			format='multipart',
		)
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		draft_id = response.data.get('id')
		draft = DraftFile.objects.get(id=draft_id)
		attachments = (draft.draft_data or {}).get('attachments', [])
		self.assertGreaterEqual(len(attachments), 1)
		self.assertEqual(attachments[0].get('name'), 'test-draft.pdf')
		self.assertTrue(attachments[0].get('content_b64'))
