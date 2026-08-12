"""
Regression tests for the Admin "Upcoming Batches" student-image feature:
hindi_name / aadhar_number text fields and base64 photo/signature uploads
persisted through the model and the update_student endpoint.

Run: python manage.py test applications.programme_curriculum.test_upcoming_batches
"""
import base64
import json
import shutil
import tempfile

from django.test import TestCase, Client, override_settings
from django.utils import timezone
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

from applications.globals.models import Designation, HoldsDesignation
from applications.programme_curriculum.models_student_management import (
    StudentBatchUpload,
    PhdStudentBatchUpload,
)
from applications.programme_curriculum.api.views_student_management import (
    _decode_base64_image,
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


class DecodeBase64ImageTests(TestCase):
    def test_valid_png_returns_named_contentfile(self):
        cf = _decode_base64_image(PNG_1x1, "26MCSA01_photo", max_kb=200)
        self.assertIsNotNone(cf)
        self.assertEqual(cf.name, "26MCSA01_photo.png")
        self.assertGreater(cf.size, 0)

    def test_jpeg_is_named_jpg(self):
        cf = _decode_base64_image(JPG_1x1, "x_sign", max_kb=30)
        self.assertIsNotNone(cf)
        self.assertEqual(cf.name, "x_sign.jpg")

    def test_oversized_is_rejected(self):
        self.assertIsNone(_decode_base64_image(_oversized_png(210), "x", max_kb=200))

    def test_non_png_jpg_type_is_rejected(self):
        self.assertIsNone(_decode_base64_image(GIF_1x1, "x", max_kb=200))

    def test_existing_media_path_is_ignored(self):
        self.assertIsNone(_decode_base64_image("/media/x/y_photo.png", "x"))

    def test_empty_or_none_is_ignored(self):
        self.assertIsNone(_decode_base64_image("", "x"))
        self.assertIsNone(_decode_base64_image(None, "x"))


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="fusion_test_media_"))
class StudentImageModelTests(TestCase):
    def test_new_fields_and_image_persist(self):
        cf = _decode_base64_image(PNG_1x1, "R1_photo", max_kb=200)
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
            photo=cf,
        )
        student.refresh_from_db()
        self.assertEqual(student.hindi_name, "टेस्ट नाम")
        self.assertEqual(student.aadhar_number, "123456789012")
        self.assertTrue(student.photo)
        self.assertIn("R1_photo", student.photo.name)

    def test_phd_model_has_the_new_fields(self):
        for field in ("hindi_name", "photo", "signature", "aadhar_number"):
            # Raises FieldDoesNotExist if a field is missing.
            PhdStudentBatchUpload._meta.get_field(field)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="fusion_test_media_"))
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

    def tearDown(self):
        # Isolate tests: clear uploaded files so filenames don't collide/dedup.
        import os
        from django.conf import settings

        for root, _dirs, files in os.walk(settings.MEDIA_ROOT):
            for name in files:
                os.remove(os.path.join(root, name))

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
        import os

        photo_name = os.path.basename(self.student.photo.name)
        sign_name = os.path.basename(self.student.signature.name)
        self.assertTrue(photo_name.startswith("26MCSA99_photo"))
        self.assertTrue(photo_name.endswith(".png"))
        self.assertTrue(sign_name.startswith("26MCSA99_sign"))
        self.assertTrue(sign_name.endswith(".jpg"))

    def test_oversized_image_is_not_saved(self):
        resp = self._put({"programmeType": "pg", "photo": _oversized_png(210)})
        self.assertEqual(resp.status_code, 200)
        self.student.refresh_from_db()
        self.assertFalse(self.student.photo)

    def test_replacing_image_deletes_old_file(self):
        self._put({"programmeType": "pg", "photo": PNG_1x1})
        self.student.refresh_from_db()
        old_path = self.student.photo.path
        import os

        self.assertTrue(os.path.exists(old_path))
        self._put({"programmeType": "pg", "photo": JPG_1x1})
        self.student.refresh_from_db()
        self.assertFalse(os.path.exists(old_path))

    def test_unchanged_image_path_is_preserved(self):
        self._put({"programmeType": "pg", "photo": PNG_1x1})
        self.student.refresh_from_db()
        saved_name = self.student.photo.name
        # Re-sending the stored path (as the edit form does) must not wipe it.
        self._put({"programmeType": "pg", "photo": "/media/" + saved_name})
        self.student.refresh_from_db()
        self.assertEqual(self.student.photo.name, saved_name)
