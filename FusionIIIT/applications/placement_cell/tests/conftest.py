import datetime
from decimal import Decimal
from pathlib import Path

import yaml
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from applications.academic_information.models import Student
from applications.globals.models import DepartmentInfo, Designation, ExtraInfo, HoldsDesignation
from applications.placement_cell.models import (
    Education,
    Has,
    NotifyStudent,
    PlacementProfileDocument,
    PlacementSchedule,
    Project,
    Skill,
)


class PlacementCellSpecBase(TestCase):
    specs_dir = Path(__file__).resolve().parent / "specs"

    @classmethod
    def load_spec(cls, filename, item_key, item_id):
        with (cls.specs_dir / filename).open("r", encoding="utf-8") as spec_file:
            payload = yaml.safe_load(spec_file) or {}
        for item in payload.get(item_key, []):
            if item.get("id") == item_id:
                return item
        raise AssertionError("Specification {}:{} not found".format(filename, item_id))

    def setUp(self):
        self.department_cse = DepartmentInfo.objects.create(name="CSE")
        self.department_ece = DepartmentInfo.objects.create(name="ECE")
        self.student_designation = Designation.objects.create(name="student", full_name="Student")
        self.officer = User.objects.create_user(
            username="officer",
            password="password",
            email="officer@example.com",
        )
        self.student_user = self._create_student_user(
            roll_no="2023001",
            username="student1",
            department=self.department_cse,
        )
        self.other_student_user = self._create_student_user(
            roll_no="2023002",
            username="student2",
            department=self.department_ece,
        )

    def api_get(self, path, *, user=None, data=None):
        client = APIClient()
        if user is not None:
            client.force_authenticate(user=user)
        return client.get(path, data=data or {}, format="json")

    def api_post(self, path, *, user=None, data=None, format="json"):
        client = APIClient()
        if user is not None:
            client.force_authenticate(user=user)
        return client.post(path, data=data or {}, format=format)

    def api_put(self, path, *, user=None, data=None, format="json"):
        client = APIClient()
        if user is not None:
            client.force_authenticate(user=user)
        return client.put(path, data=data or {}, format=format)

    def api_delete(self, path, *, user=None, data=None):
        client = APIClient()
        if user is not None:
            client.force_authenticate(user=user)
        return client.delete(path, data=data or {}, format="json")

    def _create_student_user(self, *, roll_no, username, department):
        user = User.objects.create_user(
            username=username,
            password="password",
            email="{}@example.com".format(username),
            first_name=username,
        )
        extra = ExtraInfo.objects.get(user=user)
        extra.user_type = "student"
        extra.department = department
        extra.save(update_fields=["user_type", "department"])
        Student.objects.create(
            id=extra,
            programme="B.Tech",
            batch=2026,
            cpi=8.5,
            category="GEN",
        )
        HoldsDesignation.objects.create(
            user=user,
            working=user,
            designation=self.student_designation,
        )
        return user

    def _create_officer_designation(self, name="placement officer"):
        designation, _ = Designation.objects.get_or_create(name=name, defaults={"full_name": name.title()})
        HoldsDesignation.objects.get_or_create(
            user=self.officer,
            working=self.officer,
            designation=designation,
        )
        return designation

    def _create_officer_designation_for_user(self, user, name="placement officer"):
        designation, _ = Designation.objects.get_or_create(name=name, defaults={"full_name": name.title()})
        extra, _ = ExtraInfo.objects.get_or_create(
            user=user,
            defaults={
                "id": user.username,
                "user_type": "staff",
                "department": self.department_cse,
            },
        )
        extra.user_type = "staff"
        extra.department = self.department_cse
        extra.save(update_fields=["user_type", "department"])
        HoldsDesignation.objects.get_or_create(
            user=user,
            working=user,
            designation=designation,
        )
        return designation

    def _get_student(self, user):
        return Student.objects.get(id__user=user)

    def _create_schedule(
        self,
        *,
        company_name,
        placement_type="PLACEMENT",
        placement_date=None,
        role=None,
        location="Campus",
        ctc="10.00",
    ):
        notify = NotifyStudent.objects.create(
            placement_type=placement_type,
            company_name=company_name,
            ctc=Decimal(ctc),
            description="Campus drive",
        )
        return PlacementSchedule.objects.create(
            notify_id=notify,
            title=company_name,
            placement_date=placement_date or (timezone.now().date() + datetime.timedelta(days=2)),
            location=location,
            description="Campus drive",
            time=datetime.time(10, 0),
            schedule_at=timezone.now(),
            role=role,
        )

    def _make_profile_complete(self, user):
        student = self._get_student(user)
        response = self.api_put(
            "/placement/api/profile/",
            user=user,
            data={
                "first_name": "Student",
                "last_name": "One",
                "email": "{}@example.com".format(user.username),
                "phone_no": "9876543210",
                "address": "Hostel A",
                "about_me": "Ready for placements",
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 200)
        Education.objects.get_or_create(
            unique_id=student,
            degree="B.Tech",
            grade="90",
            institute="IIITDMJ",
            sdate=datetime.date(2020, 1, 1),
            edate=datetime.date(2021, 1, 1),
        )
        skill, _ = Skill.objects.get_or_create(skill="Python")
        Has.objects.get_or_create(
            skill_id=skill,
            unique_id=student,
            defaults={"skill_rating": 80},
        )
        Project.objects.get_or_create(
            unique_id=student,
            project_name="Capstone",
            defaults={
                "project_status": "COMPLETED",
                "sdate": datetime.date(2020, 1, 1),
                "edate": datetime.date(2020, 2, 1),
            },
        )
        PlacementProfileDocument.objects.get_or_create(
            student=student,
            name="Resume",
            defaults={
                "document": SimpleUploadedFile(
                    "resume.pdf",
                    b"pdf-content",
                    content_type="application/pdf",
                )
            },
        )
        return student
