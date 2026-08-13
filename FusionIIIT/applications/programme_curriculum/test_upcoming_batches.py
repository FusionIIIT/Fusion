"""
Regression tests for the Admin "Upcoming Batches" student-image feature:
hindi_name / aadhar_number text fields and base64 photo/signature uploads
stored as DB blobs (so pg_dump captures them) and served via the image endpoint.

Run: python manage.py test applications.programme_curriculum.test_upcoming_batches
"""
import base64
import json

from django.test import TestCase, Client
from django.utils import timezone
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

from applications.globals.models import Designation, HoldsDesignation
from applications.programme_curriculum.models_student_management import (
    StudentBatchUpload,
    PhdStudentBatchUpload,
)
from applications.programme_curriculum.api.views_student_management import (
    _decode_base64_blob,
)

# 1x1 pixel PNG as a data URL.
PNG_1x1 = (
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0l"
    "EQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)
JPG_1x1 = "data:image/jpeg;base64," + PNG_1x1.split(",", 1)[1]
GIF_1x1 = (
    "data:image/gif;base64,R0lGODdhAQABAIAAAP///////ywAAAAAAQABAAACAkQBADs="
)


def _oversized_png(kb):
    raw = base64.b64encode(b"\x00" * (kb * 1024)).decode()
    return "data:image/png;base64," + raw


class DecodeBase64BlobTests(TestCase):
    def test_valid_png_returns_bytes_and_mime(self):
        raw, mime = _decode_base64_blob(PNG_1x1, max_kb=200)
        self.assertIsNotNone(raw)
        self.assertGreater(len(raw), 0)
        self.assertEqual(mime, "image/png")

    def test_jpeg_mime(self):
        raw, mime = _decode_base64_blob(JPG_1x1, max_kb=30)
        self.assertIsNotNone(raw)
        self.assertEqual(mime, "image/jpeg")

    def test_oversized_is_rejected(self):
        self.assertEqual(_decode_base64_blob(_oversized_png(210), max_kb=200), (None, None))

    def test_non_png_jpg_type_is_rejected(self):
        self.assertEqual(_decode_base64_blob(GIF_1x1, max_kb=200), (None, None))

    def test_existing_url_is_ignored(self):
        self.assertEqual(_decode_base64_blob("/programme_curriculum/api/student/image/ug/1/photo/"), (None, None))

    def test_empty_or_none_is_ignored(self):
        self.assertEqual(_decode_base64_blob(""), (None, None))
        self.assertEqual(_decode_base64_blob(None), (None, None))


class StudentImageModelTests(TestCase):
    def test_new_fields_and_image_persist(self):
        raw, mime = _decode_base64_blob(PNG_1x1, max_kb=200)
        student = StudentBatchUpload.objects.create(
            name="Test Student",
            father_name="Father",
            mother_name="Mother",
            gender="Male",
            category="GEN",
            address="Somewhere",
            branch="Computer Science and Engineering",
            programme_type="pg",
            hindi_name="टेस्ट नाम",
            aadhar_number="123456789012",
            photo_blob=raw,
            photo_mime=mime,
        )
        student.refresh_from_db()
        self.assertEqual(student.hindi_name, "टेस्ट नाम")
        self.assertEqual(student.aadhar_number, "123456789012")
        self.assertTrue(student.photo_blob)
        self.assertEqual(student.photo_mime, "image/png")

    def test_phd_model_has_the_new_fields(self):
        for field in (
            "hindi_name", "aadhar_number",
            "photo_blob", "photo_mime", "signature_blob", "signature_mime",
        ):
            # Raises FieldDoesNotExist if a field is missing.
            PhdStudentBatchUpload._meta.get_field(field)


class UpdateStudentImageEndpointTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="acad_test", password="pw")
        self.token = Token.objects.create(user=self.user)
        designation = Designation.objects.create(name="acadadmin")
        HoldsDesignation.objects.create(
            user=self.user,
            working=self.user,
            designation=designation,
            held_at=timezone.now(),
        )
        self.student = StudentBatchUpload.objects.create(
            name="Round Trip",
            father_name="Father",
            mother_name="Mother",
            gender="Male",
            category="GEN",
            address="Somewhere",
            branch="Computer Science and Engineering",
            programme_type="pg",
            roll_number="26MCSA99",
        )

    def _put(self, payload):
        return self.client.put(
            "/programme_curriculum/api/student/{}/update/".format(self.student.id),
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION="Token {}".format(self.token.key),
        )

    def test_requires_authorization(self):
        resp = self.client.put(
            "/programme_curriculum/api/student/{}/update/".format(self.student.id),
            data=json.dumps({"hindi_name": "x"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 403)

    def test_update_persists_text_and_images(self):
        resp = self._put(
            {
                "programmeType": "pg",
                "hindi_name": "हिंदी नाम",
                "aadhar_number": "111122223333",
                "photo": PNG_1x1,
                "signature": JPG_1x1,
            }
        )
        self.assertEqual(resp.status_code, 200)
        self.student.refresh_from_db()
        self.assertEqual(self.student.hindi_name, "हिंदी नाम")
        self.assertEqual(self.student.aadhar_number, "111122223333")
        self.assertTrue(self.student.photo_blob)
        self.assertEqual(self.student.photo_mime, "image/png")
        self.assertTrue(self.student.signature_blob)
        self.assertEqual(self.student.signature_mime, "image/jpeg")

    def test_oversized_image_is_not_saved(self):
        resp = self._put({"programmeType": "pg", "photo": _oversized_png(210)})
        self.assertEqual(resp.status_code, 200)
        self.student.refresh_from_db()
        self.assertFalse(self.student.photo_blob)

    def test_replacing_image_updates_blob(self):
        self._put({"programmeType": "pg", "photo": PNG_1x1})
        self.student.refresh_from_db()
        self.assertEqual(self.student.photo_mime, "image/png")
        self._put({"programmeType": "pg", "photo": JPG_1x1})
        self.student.refresh_from_db()
        self.assertEqual(self.student.photo_mime, "image/jpeg")

    def test_unchanged_image_is_preserved(self):
        self._put({"programmeType": "pg", "photo": PNG_1x1})
        self.student.refresh_from_db()
        saved = bytes(self.student.photo_blob)
        # Re-sending the stored URL (as the edit form does) must not wipe it.
        self._put({"programmeType": "pg", "photo": "/programme_curriculum/api/student/image/ug/%d/photo/" % self.student.id})
        self.student.refresh_from_db()
        self.assertEqual(bytes(self.student.photo_blob), saved)

    def test_served_image_returns_bytes(self):
        self._put({"programmeType": "pg", "photo": PNG_1x1})
        resp = self.client.get(
            "/programme_curriculum/api/student/image/ug/%d/photo/" % self.student.id
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "image/png")
        self.assertGreater(len(resp.content), 0)
