from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from applications.vms.models import Visit, Visitor
from applications.vms.services import RegistrationError, register_visitor


class RegisterVisitorServiceTest(TestCase):
    def test_register_creates_visitor_and_visit(self):
        data = {
            "full_name": "Test Visitor",
            "id_number": "TEST001",
            "id_type": "aadhaar",
            "contact_phone": "9999999999",
            "purpose": "Meeting",
            "host_name": "Dr. Host",
            "host_department": "CSE",
        }
        visitor, visit = register_visitor(data)
        self.assertEqual(visitor.full_name, "Test Visitor")
        self.assertEqual(visit.status, Visit.STATUS_REGISTERED)
        self.assertEqual(visit.visitor, visitor)

    def test_blacklisted_visitor_blocked(self):
        from applications.vms.models import BlacklistEntry
        BlacklistEntry.objects.create(id_number="BL001", reason="test", active=True)
        data = {
            "full_name": "Blocked Person",
            "id_number": "BL001",
            "id_type": "aadhaar",
            "contact_phone": "0000000000",
            "purpose": "Visit",
            "host_name": "Host",
            "host_department": "Dept",
        }
        with self.assertRaises(RegistrationError):
            register_visitor(data)


class RegisterVisitorAPITest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="teststaff", password="pass1234")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_register_endpoint_returns_201(self):
        payload = {
            "full_name": "API Visitor",
            "id_number": "API001",
            "id_type": "passport",
            "contact_phone": "1234567890",
            "purpose": "Conference",
            "host_name": "Prof. X",
            "host_department": "ECE",
        }
        response = self.client.post("/vms/register/", payload, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertIn("visit_id", response.data)

    def test_active_endpoint_returns_200(self):
        response = self.client.get("/vms/active/")
        self.assertEqual(response.status_code, 200)
