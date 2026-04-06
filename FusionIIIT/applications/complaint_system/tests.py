from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from applications.complaint_system.models import Caretaker, StudentComplain, Supervisor
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
			# Even if payload tries to spoof complainer, backend should ignore it.
			'complainer': self.other_student_extra.id,
		}
		response = self.client.post('/complaint/api/newcomplain', payload, format='json')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		created = StudentComplain.objects.get(id=response.data['id'])
		self.assertEqual(created.complainer_id, self.student_extra.id)

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

		update_response = self.client.put(
			f'/complaint/api/updatecomplain/{self.complaint_1.id}',
			{'status': 2},
			format='json',
		)
		self.assertEqual(update_response.status_code, status.HTTP_200_OK)
		self.complaint_1.refresh_from_db()
		self.assertEqual(self.complaint_1.status, 2)

	def test_owner_can_delete(self):
		self._auth(self.student_user)

		delete_response = self.client.delete(f'/complaint/api/removecomplain/{self.complaint_1.id}')
		self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
		self.assertFalse(StudentComplain.objects.filter(id=self.complaint_1.id).exists())
