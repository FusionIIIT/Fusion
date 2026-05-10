from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

from applications.globals.models import Designation, DepartmentInfo, ExtraInfo, HoldsDesignation


def ensure_account(username, password, first_name, last_name, user_type, role_name, designation_type="administrative"):
    user, _ = User.objects.get_or_create(
        username=username,
        defaults={
            "email": f"{username}@example.com",
            "first_name": first_name,
            "last_name": last_name,
        },
    )
    user.first_name = first_name
    user.last_name = last_name
    user.email = f"{username}@example.com"
    user.set_password(password)
    user.save()

    dept, _ = DepartmentInfo.objects.get_or_create(name="CSE")

    extra, _ = ExtraInfo.objects.get_or_create(
        user=user,
        defaults={
            "id": f"EX{user.id}",
            "title": "Dr.",
            "sex": "M",
            "user_status": "PRESENT",
            "address": "Campus",
            "phone_no": 9999999999,
            "user_type": user_type,
            "department": dept,
        },
    )
    extra.user_type = user_type
    extra.department = dept
    extra.last_selected_role = role_name
    extra.save()

    designation, _ = Designation.objects.get_or_create(
        name=role_name,
        defaults={"full_name": role_name, "type": designation_type},
    )
    HoldsDesignation.objects.get_or_create(user=user, working=user, designation=designation)

    Token.objects.filter(user=user).delete()
    token = Token.objects.create(user=user)
    return user.username, token.key


def run():
    accounts = [
        ("patent_student", "Pass1234!", "Patent", "Student", "student", "student", "academic"),
        ("patent_pcc", "Pass1234!", "Patent", "PCC", "staff", "PCC Admin", "administrative"),
        ("patent_director", "Pass1234!", "Patent", "Director", "staff", "Director", "administrative"),
    ]

    for account in accounts:
        username, token = ensure_account(*account)
        print(f"{username} {token}")


run()
