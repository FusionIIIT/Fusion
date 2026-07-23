"""Create/refresh the placement-cell role accounts.

Idempotent: re-running updates the password and keeps a single account per role.

The password is NOT stored in the repository -- pass it explicitly::

    python manage.py setup_placement_roles --password '<password>'

or via the PLACEMENT_ROLE_PASSWORD environment variable.
"""

import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from applications.academic_information.models import Student
from applications.globals.models import (
    Designation,
    DepartmentInfo,
    ExtraInfo,
    HoldsDesignation,
    ModuleAccess,
)

# (username, designation name, full name, ExtraInfo.user_type, needs Student record)
ROLES = [
    ("placement_officer", "placement officer", "Placement Officer", "staff", False),
    ("placement_chairman", "placement chairman", "Placement Chairman", "staff", False),
    ("placement_student", "student", "Student", "student", True),
    ("placement_alumni", "alumni", "Alumni", "student", False),
]


class Command(BaseCommand):
    help = "Create the placement-cell role accounts (officer, chairman, student, alumni)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            default=os.environ.get("PLACEMENT_ROLE_PASSWORD"),
            help="Password for the role accounts (or set PLACEMENT_ROLE_PASSWORD).",
        )
        parser.add_argument(
            "--department",
            default="CSE",
            help="Department to attach the accounts to (default: CSE).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        password = options["password"]
        if not password:
            raise CommandError(
                "Provide --password '<password>' or set PLACEMENT_ROLE_PASSWORD."
            )

        department, _ = DepartmentInfo.objects.get_or_create(
            name=options["department"]
        )

        for username, role_name, full_name, user_type, needs_student in ROLES:
            designation, _ = Designation.objects.get_or_create(
                name=role_name, defaults={"full_name": full_name}
            )

            # Make the placement module visible in the sidebar for this role.
            access, _ = ModuleAccess.objects.get_or_create(designation=role_name)
            if not access.placement_cell:
                access.placement_cell = True
                access.save(update_fields=["placement_cell"])

            user, _ = User.objects.get_or_create(
                username=username,
                defaults={"email": "{}@iiitdmj.ac.in".format(username)},
            )
            user.set_password(password)
            user.save()

            extra, _ = ExtraInfo.objects.get_or_create(
                user=user,
                defaults={"id": username, "user_type": user_type, "department": department},
            )
            extra.user_type = user_type
            extra.department = department
            extra.last_selected_role = role_name
            extra.save(update_fields=["user_type", "department", "last_selected_role"])

            if needs_student:
                Student.objects.get_or_create(
                    id=extra,
                    defaults={
                        "programme": "B.Tech",
                        "batch": 2026,
                        "cpi": 8.5,
                        "category": "GEN",
                    },
                )

            HoldsDesignation.objects.get_or_create(
                user=user, working=user, designation=designation
            )

            self.stdout.write(
                self.style.SUCCESS(
                    "{:<18} -> role '{}'".format(username, role_name)
                )
            )

        self.stdout.write(self.style.SUCCESS("Placement role accounts ready."))
