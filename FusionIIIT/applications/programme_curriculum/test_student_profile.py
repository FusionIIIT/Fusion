"""
Regression tests for the first-login student profile-completion endpoints
(GET record + POST submit) on StudentBatchUpload.

Run: python manage.py test applications.programme_curriculum.test_student_profile \
  --settings=Fusion.settings.test_settings --noinput
"""
import json
import tempfile

from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

from applications.programme_curriculum.models_student_management import (
    StudentBatchUpload,
)

PNG_1x1 = (
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0l"
    "EQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)
GET_URL = "/programme_curriculum/api/student/profile_completion/"
SUBMIT_URL = "/programme_curriculum/api/student/profile_completion/submit/"


def _valid_payload(**overrides):
    payload = {
        "aadhar_number": "123456789012",
        "hindi_name": "छात्र",
        "photo": PNG_1x1,
        "signature": PNG_1x1,
        "phone_number": "9000000001",
        "father_mobile": "9000000002",
        "mother_mobile": "",
        "parent_email": "parent@example.com",
        "father_occupation": "Teacher",
        "mother_occupation": "",
        "minority": "",
        "blood_group": "B+",
        "blood_group_remarks": "",
        "country": "India",
        "nationality": "Indian",
        "income_group": "Between 0 to 2 Lakh",
        "income": "200000",
        "state": "Bihar",
        "address": "Some address",
    }
    payload.update(overrides)
    return payload


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="fusion_test_media_"))
class StudentProfileCompletionTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="26MCSA50", password="pw")
        self.token = Token.objects.create(user=self.user)
        self.student = StudentBatchUpload.objects.create(
            name="Test Student",
            father_name="Father",
            mother_name="Mother",
            gender="Male",
            category="GEN",
            address="",
            branch="Computer Science and Engineering",
            programme_type="pg",
            specialization="Data Science",
            roll_number="26MCSA50",
            user=self.user,
            profile_completed=False,
        )

    def _auth(self):
        return {"HTTP_AUTHORIZATION": "Token {}".format(self.token.key)}

    def _submit(self, payload):
        return self.client.post(
            SUBMIT_URL,
            data=json.dumps(payload),
            content_type="application/json",
            **self._auth(),
        )

    # --- auth ---
    def test_get_requires_auth(self):
        self.assertEqual(self.client.get(GET_URL).status_code, 401)

    def test_submit_requires_auth(self):
        resp = self.client.post(
            SUBMIT_URL, data=json.dumps(_valid_payload()), content_type="application/json"
        )
        self.assertEqual(resp.status_code, 401)

    # --- GET ---
    def test_get_returns_frozen_and_editable(self):
        resp = self.client.get(GET_URL, **self._auth())
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertEqual(data["roll_number"], "26MCSA50")
        self.assertEqual(data["specialization"], "Data Science")
        self.assertFalse(data["profile_completed"])

    # --- submit happy path ---
    def test_valid_submit_completes_profile(self):
        resp = self._submit(_valid_payload())
        self.assertEqual(resp.status_code, 200, resp.content)
        self.student.refresh_from_db()
        self.assertTrue(self.student.profile_completed)
        self.assertEqual(self.student.aadhar_number, "123456789012")
        self.assertEqual(self.student.blood_group, "B+")
        self.assertTrue(self.student.photo.name.endswith("_photo.png"))
        self.assertTrue(self.student.signature.name.endswith("_sign.png"))

    # --- validation rules ---
    def test_missing_required_is_rejected(self):
        resp = self._submit(_valid_payload(address=""))
        self.assertEqual(resp.status_code, 400)
        self.assertIn("address", resp.json()["errors"])
        self.student.refresh_from_db()
        self.assertFalse(self.student.profile_completed)

    def test_aadhaar_must_be_12_digits(self):
        resp = self._submit(_valid_payload(aadhar_number="123"))
        self.assertEqual(resp.status_code, 400)
        self.assertIn("aadhar_number", resp.json()["errors"])

    def test_at_least_one_parent_mobile(self):
        resp = self._submit(_valid_payload(father_mobile="", mother_mobile=""))
        self.assertEqual(resp.status_code, 400)
        self.assertIn("father_mobile", resp.json()["errors"])

    def test_student_mobile_not_equal_parent(self):
        resp = self._submit(
            _valid_payload(phone_number="9000000002", father_mobile="9000000002")
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("phone_number", resp.json()["errors"])

    def test_blood_group_other_requires_remarks(self):
        resp = self._submit(
            _valid_payload(blood_group="Other", blood_group_remarks="")
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("blood_group_remarks", resp.json()["errors"])

    def test_photo_required_when_none_saved(self):
        resp = self._submit(_valid_payload(photo=""))
        self.assertEqual(resp.status_code, 400)
        self.assertIn("photo", resp.json()["errors"])
