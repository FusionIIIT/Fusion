from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from applications.globals.models import Designation, DepartmentInfo, ExtraInfo, HoldsDesignation
from applications.patent_system.models import Applicant, Application, Attorney


class Command(BaseCommand):
	help = "Seed patent test data for 23BCS226 and four attorneys."

	def add_arguments(self, parser):
		parser.add_argument(
			"--reset",
			action="store_true",
			help="Delete existing seeded patent test data before creating new records.",
		)

	def handle(self, *args, **options):
		reset = options["reset"]
		student_user = self._ensure_student_user()
		attorneys = self._ensure_attorneys()

		if reset:
			self._delete_existing_seed_data(student_user, attorneys)

		applicant = self._ensure_applicant(student_user)
		scenarios = self._seed_student_scenarios(applicant, attorneys)

		self.stdout.write(self.style.SUCCESS("Seeded 10 patent scenarios for 23BCS226."))
		self.stdout.write(self.style.SUCCESS(f"Seeded {len(attorneys)} attorneys."))
		for application in scenarios:
			self.stdout.write(
				f"- {application.id}: {application.title} | {application.status} | {application.attorney.name if application.attorney else 'No attorney'}"
			)

	def _ensure_student_user(self):
		user, _ = User.objects.get_or_create(
			username="23BCS226",
			defaults={
				"email": "23bcs226@example.com",
				"first_name": "Saumitra",
				"last_name": "Sharma",
			},
		)
		user.email = "23bcs226@example.com"
		user.first_name = "Saumitra"
		user.last_name = "Sharma"
		user.set_password("Pass1234!")
		user.save()

		dept, _ = DepartmentInfo.objects.get_or_create(name="CSE")
		extra, _ = ExtraInfo.objects.get_or_create(
			user=user,
			defaults={
				"id": f"EX{user.id}",
				"title": "Mr.",
				"sex": "M",
				"user_status": "PRESENT",
				"address": "Campus",
				"phone_no": 9999999999,
				"user_type": "student",
				"department": dept,
			},
		)
		extra.user_type = "student"
		extra.department = dept
		extra.last_selected_role = "student"
		extra.save()

		designation, _ = Designation.objects.get_or_create(
			name="student",
			defaults={"full_name": "student", "type": "academic"},
		)
		HoldsDesignation.objects.get_or_create(user=user, working=user, designation=designation)
		return user

	def _ensure_applicant(self, user):
		applicant, _ = Applicant.objects.get_or_create(
			user=user,
			defaults={
				"name": "23BCS226",
				"email": "23bcs226@example.com",
				"mobile": "9999999999",
				"address": "Campus",
			},
		)
		applicant.name = "23BCS226"
		applicant.email = "23bcs226@example.com"
		applicant.mobile = "9999999999"
		applicant.address = "Campus"
		applicant.save()
		return applicant

	def _ensure_attorneys(self):
		attorney_specs = [
			("Attorney One", "attorney1@example.com", "9000000001", "LexBridge LLP", "Patent Search"),
			("Attorney Two", "attorney2@example.com", "9000000002", "Nova Legal", "Drafting"),
			("Attorney Three", "attorney3@example.com", "9000000003", "IP Shield", "Office Actions"),
			("Attorney Four", "attorney4@example.com", "9000000004", "Crown IP", "Appeals"),
		]
		attorneys = []
		for name, email, phone, firm, expertise in attorney_specs:
			attorney, _ = Attorney.objects.get_or_create(
				email=email,
				defaults={
					"name": name,
					"phone": phone,
					"firm_name": firm,
					"expertise_domain": expertise,
					"is_panel_approved": True,
					"current_workload": 0,
				},
			)
			attorney.name = name
			attorney.phone = phone
			attorney.firm_name = firm
			attorney.expertise_domain = expertise
			attorney.is_panel_approved = True
			attorney.save()
			attorneys.append(attorney)
		return attorneys

	def _delete_existing_seed_data(self, user, attorneys):
		Application.objects.filter(primary_applicant__user=user).delete()
		Attorney.objects.filter(email__in=[attorney.email for attorney in attorneys]).delete()

	def _seed_student_scenarios(self, applicant, attorneys):
		scenarios = [
			{
				"title": "Scenario 01 - Submitted",
				"status": "Submitted",
				"decision_status": "Pending",
				"attorney": None,
				"comments": "Fresh submission awaiting PCC review.",
			},
			{
				"title": "Scenario 02 - PCC Reviewed",
				"status": "Reviewed by PCC Admin",
				"decision_status": "Pending",
				"attorney": None,
				"comments": "Reviewed by PCC Admin and ready to forward.",
			},
			{
				"title": "Scenario 03 - Forwarded",
				"status": "Forwarded for Director's Review",
				"decision_status": "Pending",
				"attorney": attorneys[0],
				"comments": "Forwarded to Director with attorney assignment.",
			},
			{
				"title": "Scenario 04 - Director Approved",
				"status": "Attorney Assigned",
				"decision_status": "Pending",
				"attorney": attorneys[1],
				"comments": "Director approved and attorney review pending.",
			},
			{
				"title": "Scenario 05 - Attorney Returned",
				"status": "Returned to Director",
				"decision_status": "Reviewed by Attorney",
				"attorney": attorneys[2],
				"comments": "Attorney completed patentability check and returned to Director.",
				"attorney_review_notes": "Prior-art analysis complete.",
			},
			{
				"title": "Scenario 06 - Needs Revision",
				"status": "Needs Revision",
				"decision_status": "Needs Revision",
				"attorney": attorneys[3],
				"comments": "PCC requested mandatory revision comments.",
				"revision_requested_at": date.today() - timedelta(days=2),
				"revision_due_date": date.today() + timedelta(days=28),
				"is_revision_locked": True,
			},
			{
				"title": "Scenario 07 - Revision Expired",
				"status": "Revision Expired",
				"decision_status": "Pending",
				"attorney": None,
				"comments": "Revision deadline has already expired.",
				"revision_requested_at": date.today() - timedelta(days=90),
				"revision_due_date": date.today() - timedelta(days=30),
				"is_revision_locked": True,
			},
			{
				"title": "Scenario 08 - Withdrawn",
				"status": "Withdrawn",
				"decision_status": "Rejected",
				"attorney": None,
				"comments": "Applicant withdrew the application.",
			},
			{
				"title": "Scenario 09 - Patent Filed",
				"status": "Patent Filed",
				"decision_status": "Pending",
				"attorney": attorneys[0],
				"comments": "Filed after attorney review.",
				"token_no": "IIITDMJ/CSE/2026-04-19/000009/PAT/109",
				"patent_filed_date": date.today() - timedelta(days=3),
			},
			{
				"title": "Scenario 10 - Patent Refused",
				"status": "Patent Refused",
				"decision_status": "Rejected",
				"attorney": attorneys[1],
				"comments": "Final refusal after director review.",
				"token_no": "IIITDMJ/CSE/2026-04-19/000010/PAT/110",
			},
		]

		created = []
		for index, scenario in enumerate(scenarios, start=1):
			defaults = {
				"title": scenario["title"],
				"status": scenario["status"],
				"decision_status": scenario["decision_status"],
				"submitted_date": date.today() - timedelta(days=30 - index),
				"comments": scenario.get("comments", ""),
				"attorney": scenario.get("attorney"),
				"is_revision_locked": scenario.get("is_revision_locked", False),
				"revision_requested_at": scenario.get("revision_requested_at"),
				"revision_due_date": scenario.get("revision_due_date"),
				"revised_submitted_at": scenario.get("revised_submitted_at"),
				"attorney_review_notes": scenario.get("attorney_review_notes"),
				"patent_filed_date": scenario.get("patent_filed_date"),
			}

			application, _ = Application.objects.get_or_create(
				primary_applicant=applicant,
				title=scenario["title"],
				defaults=defaults,
			)

			for field_name, field_value in defaults.items():
				setattr(application, field_name, field_value)

			application.token_no = scenario.get("token_no")
			application.forwarded_to_director_date = application.submitted_date + timedelta(days=2)
			application.reviewed_by_pcc_date = application.submitted_date + timedelta(days=1)
			application.director_approval_date = (
				application.submitted_date + timedelta(days=3)
				if scenario["status"] in ["Attorney Assigned", "Returned to Director", "Patent Filed", "Patent Refused"]
				else None
			)
			application.decision_date = application.submitted_date + timedelta(days=4) if scenario["status"] == "Patent Refused" else None
			if scenario["status"] == "Attorney Assigned" and not application.attorney:
				application.attorney = attorneys[0]
			application.save()
			created.append(application)

		return created
