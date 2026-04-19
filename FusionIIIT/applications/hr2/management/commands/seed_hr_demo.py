import json
import datetime

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from applications.globals.models import DepartmentInfo, Designation, ExtraInfo, HoldsDesignation
from applications.hr2.models import (
    AppraisalFormNew,
    CPDAAdvanceNew,
    EmployeeCategory,
    EmployeeDetailsExtended,
    EmployeeLeaveBalance,
    LeaveApplicationNew,
    LeaveType,
    LTCApplicationNew,
)


class Command(BaseCommand):
    help = "Seed HR demo data for form testing."

    @staticmethod
    def _parse_date(value):
        if not value:
            return None
        return datetime.date.fromisoformat(value)

    @staticmethod
    def _parse_gender(value):
        if not value:
            return "M"
        value = value.strip().lower()
        if value.startswith("f"):
            return "F"
        if value.startswith("m"):
            return "M"
        return "O"

    @staticmethod
    def _split_name(full_name):
        if not full_name:
            return "", ""
        parts = full_name.strip().split()
        if len(parts) == 1:
            return parts[0], ""
        return parts[0], " ".join(parts[1:])

    def handle(self, *args, **options):
        departments = [
            "Computer Science and Engineering",
            "Administration",
            "Finance",
            "Director Office",
        ]

        employees = [
            {
                "employee_id": "EMP1001",
                "name": "Rahul Sharma",
                "email": "rahul.sharma@iiitdmj.ac.in",
                "phone": "9876543210",
                "gender": "Male",
                "dob": "1990-05-12",
                "department": "Computer Science and Engineering",
                "designation": "Assistant Professor",
                "role": "Employee",
                "employment_type": "Permanent",
                "date_of_joining": "2021-08-01",
                "reporting_to": "EMP1002",
                "status": "Active",
            },
            {
                "employee_id": "EMP1007",
                "name": "Dr. Anjali Mehta",
                "email": "anjali.mehta@iiitdmj.ac.in",
                "phone": "9876543216",
                "gender": "Female",
                "dob": "1985-11-08",
                "department": "Computer Science and Engineering",
                "designation": "Professor",
                "role": "Employee",
                "employment_type": "Permanent",
                "date_of_joining": "2016-07-20",
                "reporting_to": "EMP1002",
                "status": "Active",
            },
            {
                "employee_id": "EMP1002",
                "name": "Dr. Anil Kumar",
                "email": "anil.kumar@iiitdmj.ac.in",
                "phone": "9876543211",
                "gender": "Male",
                "dob": "1980-07-20",
                "department": "Computer Science and Engineering",
                "designation": "Professor and HOD",
                "role": "HOD",
                "employment_type": "Permanent",
                "date_of_joining": "2015-06-15",
                "reporting_to": "EMP1003",
                "status": "Active",
            },
            {
                "employee_id": "EMP1003",
                "name": "Dr. Meena Verma",
                "email": "director@iiitdmj.ac.in",
                "phone": "9876543212",
                "gender": "Female",
                "dob": "1975-02-11",
                "department": "Director Office",
                "designation": "Director",
                "role": "Director",
                "employment_type": "Permanent",
                "date_of_joining": "2019-01-10",
                "reporting_to": None,
                "status": "Active",
            },
            {
                "employee_id": "EMP1004",
                "name": "Suresh Verma",
                "email": "registrar@iiitdmj.ac.in",
                "phone": "9876543213",
                "gender": "Male",
                "dob": "1982-03-10",
                "department": "Administration",
                "designation": "Registrar",
                "role": "Registrar",
                "employment_type": "Permanent",
                "date_of_joining": "2018-01-15",
                "reporting_to": "EMP1003",
                "status": "Active",
            },
            {
                "employee_id": "EMP1005",
                "name": "Priya Nair",
                "email": "hr.admin@iiitdmj.ac.in",
                "phone": "9876543214",
                "gender": "Female",
                "dob": "1987-09-25",
                "department": "Administration",
                "designation": "HR Administrator",
                "role": "HR Admin",
                "employment_type": "Permanent",
                "date_of_joining": "2020-11-05",
                "reporting_to": "EMP1004",
                "status": "Active",
            },
            {
                "employee_id": "EMP1006",
                "name": "Arun Joshi",
                "email": "accountant@iiitdmj.ac.in",
                "phone": "9876543215",
                "gender": "Male",
                "dob": "1985-12-18",
                "department": "Finance",
                "designation": "Accountant",
                "role": "Accountant",
                "employment_type": "Permanent",
                "date_of_joining": "2019-08-12",
                "reporting_to": "EMP1004",
                "status": "Active",
            },
        ]

        users = [
            {
                "linked_employee_id": "EMP1001",
                "username": "rahul1001",
                "password": "rahul123",
            },
            {
                "linked_employee_id": "EMP1007",
                "username": "anjali1007",
                "password": "anjali123",
            },
            {
                "linked_employee_id": "EMP1002",
                "username": "hod1002",
                "password": "hod123",
            },
            {
                "linked_employee_id": "EMP1003",
                "username": "director1003",
                "password": "director123",
            },
            {
                "linked_employee_id": "EMP1004",
                "username": "registrar1004",
                "password": "registrar123",
            },
            {
                "linked_employee_id": "EMP1005",
                "username": "hradmin1005",
                "password": "hradmin123",
            },
            {
                "linked_employee_id": "EMP1006",
                "username": "accountant1006",
                "password": "accountant123",
            },
        ]

        leave_balance = {
            "employee_id": "EMP1001",
            "casual_leave": 10,
            "restricted_leave": 5,
            "medical_leave": 12,
            "earned_leave": 18,
            "vacation_leave": 20,
            "sabbatical_leave": 0,
        }

        leave_request = {
            "employee_id": "EMP1001",
            "employee_name": "Rahul Sharma",
            "department": "Computer Science and Engineering",
            "designation": "Assistant Professor",
            "leave_type": "Casual",
            "start_date": "2026-04-10",
            "end_date": "2026-04-12",
            "total_days": 3,
            "reason": "Personal work",
            "contact_during_leave": "9876543210",
            "address_during_leave": "Jabalpur, MP",
            "handover_notes": "Classes handed over to Dr. X",
            "attachment_file": "",
            "leave_balance_before": 10,
            "leave_balance_after": 7,
            "approval_status": "PENDING",
            "current_approver_role": "HOD",
            "remarks": "",
        }

        appraisal_request = {
            "employee_id": "EMP1001",
            "employee_name": "Rahul Sharma",
            "department": "Computer Science and Engineering",
            "designation": "Assistant Professor",
            "appraisal_year": "2025-2026",
            "self_summary": "Completed teaching and research responsibilities effectively.",
            "teaching_performance": "Good",
            "research_work": "Worked on 2 projects",
            "publications": "1 journal paper",
            "trainings_attended": "AI workshop",
            "administrative_contributions": "Exam coordination",
            "goals_achieved": "Completed syllabus and guided students",
            "future_goals": "Publish more papers",
            "reviewer_id": "EMP1002",
            "status": "PENDING",
            "remarks": "",
        }

        ltc_request = {
            "employee_id": "EMP1001",
            "employee_name": "Rahul Sharma",
            "department": "Computer Science and Engineering",
            "designation": "Assistant Professor",
            "ltc_block_year": "2024-2027",
            "travel_start_date": "2026-05-05",
            "travel_end_date": "2026-05-12",
            "destination": "Delhi",
            "purpose_of_travel": "Family travel",
            "family_members": [
                {"name": "Priya Sharma", "relationship": "Spouse"}
            ],
            "travel_mode": "Train",
            "ticket_number": "IRCTC12345",
            "ticket_cost": 12000,
            "accommodation_cost": 8000,
            "other_expenses": 2000,
            "total_amount_claimed": 22000,
            "tickets_upload": "",
            "bills_upload": "",
            "previous_ltc_used": True,
            "last_ltc_date": "2023-06-15",
            "verified_by_hr": False,
            "approval_status": "PENDING",
            "accountant_status": "Not Started",
            "remarks": "",
        }

        cpda_request = {
            "employee_id": "EMP1001",
            "employee_name": "Rahul Sharma",
            "department": "Computer Science and Engineering",
            "designation": "Assistant Professor",
            "event_name": "National Conference on AI",
            "event_type": "Conference",
            "organized_by": "IIT Delhi",
            "venue": "New Delhi",
            "start_date": "2026-06-20",
            "end_date": "2026-06-22",
            "registration_fee": 5000,
            "travel_expense": 8000,
            "accommodation_expense": 6000,
            "other_expenses": 1000,
            "total_amount": 20000,
            "purpose_of_attending": "Present paper and improve research skills",
            "benefits_to_institution": "Research development and academic exposure",
            "invitation_letter": "",
            "receipts": "",
            "certificates": "",
            "verified_by_hr": False,
            "approval_status": "PENDING",
            "accountant_processing_status": "Not Started",
            "remarks": "",
        }

        with transaction.atomic():
            for name in departments:
                DepartmentInfo.objects.get_or_create(name=name)

            teaching_category, _ = EmployeeCategory.objects.get_or_create(
                name="Teaching", defaults={"category_type": "TEACHING"}
            )
            non_teaching_category, _ = EmployeeCategory.objects.get_or_create(
                name="Non-Teaching", defaults={"category_type": "NON_TEACHING"}
            )

            user_lookup = {item["linked_employee_id"]: item for item in users}

            for employee in employees:
                user_info = user_lookup.get(employee["employee_id"], {})
                username = user_info.get("username") or employee["employee_id"].lower()
                first_name, last_name = self._split_name(employee["name"])

                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        "email": employee["email"],
                        "first_name": first_name,
                        "last_name": last_name,
                    },
                )
                if created and user_info.get("password"):
                    user.set_password(user_info["password"])
                    user.save()

                department_obj = DepartmentInfo.objects.get(name=employee["department"])

                extra_info, _ = ExtraInfo.objects.get_or_create(
                    id=employee["employee_id"],
                    defaults={
                        "user": user,
                        "sex": self._parse_gender(employee["gender"]),
                        "date_of_birth": self._parse_date(employee["dob"]),
                        "user_type": "faculty"
                        if employee["department"] == "Computer Science and Engineering"
                        else "staff",
                        "department": department_obj,
                        "phone_no": int(employee["phone"]),
                        "address": "",
                    },
                )

                category = teaching_category if extra_info.user_type == "faculty" else non_teaching_category
                EmployeeDetailsExtended.objects.get_or_create(
                    extra_info=extra_info,
                    defaults={
                        "category": category,
                        "date_of_joining": self._parse_date(employee["date_of_joining"]),
                        "appointment_type": employee["employment_type"],
                    },
                )

                designation_type = "academic" if extra_info.user_type == "faculty" else "administrative"
                designation, _ = Designation.objects.get_or_create(
                    name=employee["designation"],
                    defaults={
                        "full_name": employee["designation"],
                        "type": designation_type,
                    },
                )

                HoldsDesignation.objects.get_or_create(
                    user=user,
                    working=user,
                    designation=designation,
                )

            leave_types = [
                ("Casual", "CL", leave_balance["casual_leave"]),
                ("Restricted", "RL", leave_balance["restricted_leave"]),
                ("Medical", "ML", leave_balance["medical_leave"]),
                ("Earned", "EL", leave_balance["earned_leave"]),
                ("Vacation", "VL", leave_balance["vacation_leave"]),
                ("Sabbatical", "SL", leave_balance["sabbatical_leave"]),
            ]

            for name, code, _value in leave_types:
                LeaveType.objects.get_or_create(
                    name=name,
                    code=code,
                    defaults={"is_active": True},
                )

            employee_user = ExtraInfo.objects.get(id=leave_balance["employee_id"])
            year = datetime.date.today().year

            for name, code, value in leave_types:
                leave_type = LeaveType.objects.get(code=code)
                EmployeeLeaveBalance.objects.update_or_create(
                    employee=employee_user,
                    leave_type=leave_type,
                    year=year,
                    defaults={
                        "opening_balance": value,
                        "accrued": 0,
                        "availed": 0,
                        "current_balance": value,
                    },
                )

            LeaveApplicationNew.objects.get_or_create(
                employee=employee_user,
                start_date=self._parse_date(leave_request["start_date"]),
                end_date=self._parse_date(leave_request["end_date"]),
                defaults={
                    "employee_name": leave_request["employee_name"],
                    "department": leave_request["department"],
                    "designation": leave_request["designation"],
                    "leave_type": leave_request["leave_type"],
                    "total_days": leave_request["total_days"],
                    "reason": leave_request["reason"],
                    "contact_during_leave": leave_request["contact_during_leave"],
                    "address_during_leave": leave_request["address_during_leave"],
                    "handover_to": "Dr. X",
                    "handover_notes": leave_request["handover_notes"],
                    "medical_certificate": "",
                    "attachment_file": leave_request["attachment_file"],
                    "leave_balance_before": leave_request["leave_balance_before"],
                    "leave_balance_after": leave_request["leave_balance_after"],
                    "approval_status": leave_request["approval_status"],
                    "current_approver_role": leave_request["current_approver_role"],
                    "remarks": leave_request["remarks"],
                },
            )

            AppraisalFormNew.objects.get_or_create(
                employee=employee_user,
                appraisal_year=appraisal_request["appraisal_year"],
                defaults={
                    "employee_name": appraisal_request["employee_name"],
                    "department": appraisal_request["department"],
                    "designation": appraisal_request["designation"],
                    "self_summary": appraisal_request["self_summary"],
                    "key_responsibilities": "Teaching, research, and academic mentoring.",
                    "achievements": appraisal_request["goals_achieved"],
                    "challenges_faced": "",
                    "teaching_performance": appraisal_request["teaching_performance"],
                    "research_work": appraisal_request["research_work"],
                    "publications": appraisal_request["publications"],
                    "projects_handled": "",
                    "administrative_contributions": appraisal_request["administrative_contributions"],
                    "trainings_attended": appraisal_request["trainings_attended"],
                    "certifications": "",
                    "workshops": "",
                    "goals_achieved": appraisal_request["goals_achieved"],
                    "future_goals": appraisal_request["future_goals"],
                    "supporting_documents": "",
                    "reviewer_id": appraisal_request["reviewer_id"],
                    "reviewer_comments": "",
                    "rating": "",
                    "status": appraisal_request["status"],
                    "remarks": appraisal_request["remarks"],
                },
            )

            block_year = int(ltc_request["ltc_block_year"].split("-")[0])
            LTCApplicationNew.objects.get_or_create(
                employee=employee_user,
                travel_start_date=self._parse_date(ltc_request["travel_start_date"]),
                travel_end_date=self._parse_date(ltc_request["travel_end_date"]),
                defaults={
                    "employee_name": ltc_request["employee_name"],
                    "department": ltc_request["department"],
                    "designation": ltc_request["designation"],
                    "ltc_block_year": block_year,
                    "destination": ltc_request["destination"],
                    "purpose_of_travel": ltc_request["purpose_of_travel"],
                    "family_members": json.dumps(ltc_request["family_members"]),
                    "relationship_details": "Spouse",
                    "travel_mode": ltc_request["travel_mode"],
                    "ticket_number": ltc_request["ticket_number"],
                    "ticket_cost": ltc_request["ticket_cost"],
                    "accommodation_cost": ltc_request["accommodation_cost"],
                    "other_expenses": ltc_request["other_expenses"],
                    "total_amount_claimed": ltc_request["total_amount_claimed"],
                    "tickets_upload": ltc_request["tickets_upload"],
                    "bills_upload": ltc_request["bills_upload"],
                    "previous_ltc_used": ltc_request["previous_ltc_used"],
                    "last_ltc_date": self._parse_date(ltc_request["last_ltc_date"]),
                    "verified_by_hr": ltc_request["verified_by_hr"],
                    "approval_status": ltc_request["approval_status"],
                    "accountant_status": ltc_request["accountant_status"],
                    "remarks": ltc_request["remarks"],
                },
            )

            CPDAAdvanceNew.objects.get_or_create(
                employee=employee_user,
                start_date=self._parse_date(cpda_request["start_date"]),
                end_date=self._parse_date(cpda_request["end_date"]),
                defaults={
                    "employee_name": cpda_request["employee_name"],
                    "department": cpda_request["department"],
                    "designation": cpda_request["designation"],
                    "event_name": cpda_request["event_name"],
                    "event_type": cpda_request["event_type"],
                    "organized_by": cpda_request["organized_by"],
                    "venue": cpda_request["venue"],
                    "registration_fee": cpda_request["registration_fee"],
                    "travel_expense": cpda_request["travel_expense"],
                    "accommodation_expense": cpda_request["accommodation_expense"],
                    "other_expenses": cpda_request["other_expenses"],
                    "total_amount": cpda_request["total_amount"],
                    "purpose_of_attending": cpda_request["purpose_of_attending"],
                    "benefits_to_institution": cpda_request["benefits_to_institution"],
                    "invitation_letter": cpda_request["invitation_letter"],
                    "receipts": cpda_request["receipts"],
                    "certificates": cpda_request["certificates"],
                    "verified_by_hr": cpda_request["verified_by_hr"],
                    "approval_status": cpda_request["approval_status"],
                    "accountant_processing_status": cpda_request["accountant_processing_status"],
                    "remarks": cpda_request["remarks"],
                },
            )

        self.stdout.write(self.style.SUCCESS("HR demo data seeded."))
