"""Bootstrap the VMS: campus zones/gates and one idempotent login per role.

The password is never stored in the repository::

    python manage.py setup_vms_roles --password '<password>'

or set VMS_ROLE_PASSWORD. Re-running refreshes the accounts and extends the
time-bound role assignments (VMS-BR-181) by another --days days.
"""

import datetime
import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from applications.globals.models import DepartmentInfo, Designation, ExtraInfo, HoldsDesignation
from applications.visitor_management.constants import RoleScope, VmsRole, ZoneAccessLevel
from applications.visitor_management.models import Gate, VmsRoleAssignment, Zone

ZONES = [
    ("COMMON", "Common areas", ZoneAccessLevel.PUBLIC, False),
    ("ACAD", "Academic block", ZoneAccessLevel.CONTROLLED, False),
    ("ADMIN", "Administration block", ZoneAccessLevel.CONTROLLED, False),
    ("LABS", "Research laboratories", ZoneAccessLevel.CONTROLLED, False),
    ("HOSTEL", "Hostel area", ZoneAccessLevel.CONTROLLED, True),
]
GATES = [("MAIN", "Main gate", None), ("HOSTEL_GATE", "Hostel gate", "HOSTEL")]

# username, user_type, VMS role, scope
ACCOUNTS = [
    ("vms_superadmin", "staff", VmsRole.SUPER_ADMIN, None),
    ("vms_admin", "staff", VmsRole.ADMIN, (RoleScope.CAMPUS, None, None)),
    ("vms_security", "staff", VmsRole.SECURITY, (RoleScope.GATE, None, "MAIN")),
    ("vms_host", "faculty", VmsRole.HOST, None),
]


class Command(BaseCommand):
    help = "Create VMS zones, gates and role accounts (super admin, admin, security, host)."

    def add_arguments(self, parser):
        parser.add_argument("--password", default=os.environ.get("VMS_ROLE_PASSWORD"))
        parser.add_argument("--department", default="CSE")
        parser.add_argument("--days", type=int, default=365, help="Validity of the seeded role assignments.")
        parser.add_argument("--topology-only", action="store_true", help="Only create zones and gates.")

    @transaction.atomic
    def handle(self, *args, **options):
        for code, name, level, hostel in ZONES:
            Zone.objects.get_or_create(code=code, defaults={"name": name, "access_level": level,
                                                            "is_hostel_area": hostel})
        for code, name, zone_code in GATES:
            Gate.objects.get_or_create(code=code, defaults={"name": name,
                                                            "zone": Zone.objects.filter(code=zone_code).first()})
        self.stdout.write("Zones and gates ready.")
        if options["topology_only"]:
            return

        password = options["password"]
        if not password:
            raise CommandError("Provide --password '<password>' or set VMS_ROLE_PASSWORD.")
        department, _ = DepartmentInfo.objects.get_or_create(name=options["department"])
        super_designation, _ = Designation.objects.get_or_create(
            name="vms_super_admin", defaults={"full_name": "VMS Super Admin", "type": "administrative"})
        now = timezone.now()
        until = now + datetime.timedelta(days=options["days"])

        for username, user_type, role, scope in ACCOUNTS:
            user, _ = User.objects.get_or_create(username=username,
                                                 defaults={"email": "{}@iiitdmj.ac.in".format(username),
                                                           "first_name": username.replace("_", " ").title()})
            user.set_password(password)
            user.save()
            extra, _ = ExtraInfo.objects.get_or_create(
                user=user, defaults={"id": username, "user_type": user_type, "department": department})
            if extra.user_type != user_type:
                extra.user_type = user_type
                extra.save(update_fields=["user_type"])
            if role == VmsRole.SUPER_ADMIN:
                HoldsDesignation.objects.get_or_create(user=user, working=user, designation=super_designation)
            elif scope is not None:
                scope_type, zone_code, gate_code = scope
                assignment = VmsRoleAssignment.objects.filter(
                    user=user, role=role, scope_type=scope_type, is_active=True).first()
                if assignment is None:
                    VmsRoleAssignment.objects.create(
                        user=user, role=role, scope_type=scope_type,
                        zone=Zone.objects.filter(code=zone_code).first() if zone_code else None,
                        gate=Gate.objects.filter(code=gate_code).first() if gate_code else None,
                        valid_from=now, valid_until=until)
                else:
                    assignment.valid_until = until
                    assignment.save(update_fields=["valid_until"])
            self.stdout.write("  {:<16} {}".format(username, role))
        self.stdout.write(self.style.SUCCESS("VMS role accounts ready."))
