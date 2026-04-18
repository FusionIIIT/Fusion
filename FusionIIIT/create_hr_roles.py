"""
create_hr_roles.py
==================
Run with:  python manage.py shell < create_hr_roles.py

Creates role-based users required by the HR module (incl. CPDA Advance workflow):
  1. hr_admin      – HR Admin (can manage leave balances, offline leave, admin views)
  2. accountant    – Accountant (receives CPDA Advance after Director approval)
  3. hod_cse       – Head of Department - CSE (verifies/forwards CPDA for CSE faculty)
  4. director      – Director (sanctioning authority for CPDA Advance)

For each user the script creates:
  - django.contrib.auth.User
  - globals.ExtraInfo (links user to department)
  - globals.Designation (if it doesn't already exist)
  - globals.HoldsDesignation (assigns the designation to the user)
  - hr2.EmpConfidentialDetails (needed for LTC profile-complete check)
"""

import django, os, sys

# ── Bootstrap Django ────────────────────────────────────────────────────────
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Fusion.settings")

# If running via `python manage.py shell < create_hr_roles.py` this is a no-op;
# if running standalone it initialises Django.
django.setup()

from django.contrib.auth.models import User
from applications.globals.models import (
    Designation,
    DepartmentInfo,
    ExtraInfo,
    HoldsDesignation,
)
from applications.hr2.models import EmpConfidentialDetails

# ── Configuration ───────────────────────────────────────────────────────────
PASSWORD = "fusion123"  # Change as needed

USERS_TO_CREATE = [
    {
        "username": "hr_admin",
        "first_name": "HR",
        "last_name": "Admin",
        "email": "hradmin@iiitdmj.ac.in",
        "extra_info_id": "HR001",
        "user_type": "staff",
        "department_name": "HR Department",
        "designation_name": "HR Admin",
        "designation_full_name": "Human Resources Administrator",
        "designation_type": "administrative",
    },
    {
        "username": "accountant",
        "first_name": "Accounts",
        "last_name": "Officer",
        "email": "accountant@iiitdmj.ac.in",
        "extra_info_id": "ACC001",
        "user_type": "staff",
        "department_name": "Finance",
        "designation_name": "Accountant",
        "designation_full_name": "Accounts Officer",
        "designation_type": "administrative",
    },
    {
        "username": "hod_cse",
        "first_name": "HOD",
        "last_name": "CSE",
        "email": "hodcse@iiitdmj.ac.in",
        "extra_info_id": "HOD001",
        "user_type": "faculty",
        "department_name": "CSE",
        "designation_name": "HOD (CSE)",
        "designation_full_name": "Head of Department (Computer Science and Engineering)",
        "designation_type": "academic",
    },
    {
        "username": "director",
        "first_name": "Institute",
        "last_name": "Director",
        "email": "director@iiitdmj.ac.in",
        "extra_info_id": "DIR001",
        "user_type": "faculty",
        "department_name": "Administration",
        "designation_name": "Director",
        "designation_full_name": "Director of the Institute",
        "designation_type": "administrative",
    },
]

# ── Helper ──────────────────────────────────────────────────────────────────

def get_or_create_department(name):
    dept, created = DepartmentInfo.objects.get_or_create(name=name)
    if created:
        print(f"  ✅  Created department: {name}")
    else:
        print(f"  ℹ️  Department already exists: {name}")
    return dept


def get_or_create_designation(name, full_name, desig_type):
    desig, created = Designation.objects.get_or_create(
        name=name,
        defaults={"full_name": full_name, "type": desig_type},
    )
    if created:
        print(f"  ✅  Created designation: {name}")
    else:
        print(f"  ℹ️  Designation already exists: {name}")
    return desig


def create_role_user(cfg):
    username = cfg["username"]
    print(f"\n{'='*60}")
    print(f"  Processing: {username}")
    print(f"{'='*60}")

    # 1. User
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "first_name": cfg["first_name"],
            "last_name": cfg["last_name"],
            "email": cfg["email"],
            "is_active": True,
        },
    )
    if created:
        print(f"  ✅  Created User: {username}")
    else:
        print(f"  ℹ️  User already exists: {username}")
    # Always (re)set password so rerunning this script fixes "invalid credentials".
    user.set_password(PASSWORD)
    user.is_active = True
    user.save()
    print(f"  ✅  Password set: {PASSWORD}")

    # 2. Department
    dept = get_or_create_department(cfg["department_name"])

    # 3. ExtraInfo
    extra, created = ExtraInfo.objects.get_or_create(
        id=cfg["extra_info_id"],
        defaults={
            "user": user,
            "user_type": cfg["user_type"],
            "department": dept,
            "title": "Mr.",
            "sex": "M",
            "phone_no": 9999999999,
            "address": "IIITDM Jabalpur",
        },
    )
    if created:
        print(f"  ✅  Created ExtraInfo: {cfg['extra_info_id']}")
    else:
        # Make sure the ExtraInfo points to the right user
        if extra.user != user:
            extra.user = user
            extra.save()
            print(f"  ⚠️  ExtraInfo {cfg['extra_info_id']} existed but was re-linked to {username}")
        else:
            print(f"  ℹ️  ExtraInfo already exists: {cfg['extra_info_id']}")

    # 4. Designation
    desig = get_or_create_designation(
        cfg["designation_name"],
        cfg["designation_full_name"],
        cfg["designation_type"],
    )

    # 5. HoldsDesignation
    hd, created = HoldsDesignation.objects.get_or_create(
        user=user,
        designation=desig,
        defaults={"working": user},
    )
    if created:
        print(f"  ✅  Assigned designation '{desig.name}' to {username}")
    else:
        print(f"  ℹ️  HoldsDesignation already exists for {username} → {desig.name}")

    # 6. EmpConfidentialDetails (needed for LTC profile-complete check)
    emp_conf, created = EmpConfidentialDetails.objects.get_or_create(
        extra_info=extra,
        defaults={
            "aadhar_no": 123456789012,
            "maritial_status": "Single",
            "bank_account_no": 1234567890,
            "salary": 50000,
        },
    )
    if created:
        print(f"  ✅  Created EmpConfidentialDetails for {username}")
    else:
        print(f"  ℹ️  EmpConfidentialDetails already exists for {username}")


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "=" * 60)
    print("  HR Role User Creation Script")
    print("=" * 60)

    for cfg in USERS_TO_CREATE:
        create_role_user(cfg)

    print("\n" + "=" * 60)
    print("  DONE — Summary of created users:")
    print("=" * 60)
    print(f"  {'Username':<15} {'Designation':<20} {'Password'}")
    print(f"  {'-'*15} {'-'*20} {'-'*10}")
    for cfg in USERS_TO_CREATE:
        print(f"  {cfg['username']:<15} {cfg['designation_name']:<20} {PASSWORD}")
    print()


if __name__ == "__main__":
    main()
else:
    # When run via `python manage.py shell < script.py`
    main()
