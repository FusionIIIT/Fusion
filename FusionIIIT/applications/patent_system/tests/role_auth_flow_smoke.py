from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

from django.contrib.auth.models import User
from rest_framework.test import APIClient

from applications.globals.models import Designation, DepartmentInfo, ExtraInfo, HoldsDesignation
from applications.patent_system.models import Applicant


PASSWORD = "Pass1234!"


def _ensure_account(username, first_name, last_name, user_type, role_name, designation_type):
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
    user.set_password(PASSWORD)
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

    if user_type == "student":
        Applicant.objects.get_or_create(
            user=user,
            defaults={
                "name": f"{first_name} {last_name}".strip(),
                "email": user.email,
                "mobile": "9999999999",
                "address": "Campus",
            },
        )


def _assert(condition, message):
    if not condition:
        raise AssertionError(message)


def _check_frontend_url(url):
    request = Request(url, method="GET")
    with urlopen(request, timeout=5) as response:
        body = response.read().decode("utf-8", errors="ignore")
        _assert(response.status == 200, f"frontend check failed for {url}: HTTP {response.status}")
        _assert("Fusion" in body or "fusion" in body, f"frontend response did not contain expected app marker for {url}")


def _run_role_flow(client, username, expected_role, expected_endpoint):
    login_response = client.post(
        "/api/auth/login/",
        {"username": username, "password": PASSWORD},
        format="json",
    )
    _assert(login_response.status_code == 200, f"login failed for {username}: {login_response.status_code}")

    token = login_response.data.get("token")
    _assert(token, f"login token missing for {username}")

    client.credentials(HTTP_AUTHORIZATION=f"Token {token}")

    me_response = client.get("/api/auth/me")
    _assert(me_response.status_code == 200, f"auth/me failed for {username}: {me_response.status_code}")

    designation_info = me_response.data.get("designation_info", [])
    _assert(expected_role in designation_info, f"expected role '{expected_role}' missing in designation_info for {username}: {designation_info}")

    update_role_response = client.patch(
        "/api/update-role/",
        {"last_selected_role": expected_role},
        format="json",
    )
    _assert(update_role_response.status_code == 200, f"update-role failed for {username}: {update_role_response.status_code}")

    me_after_update = client.get("/api/auth/me")
    _assert(me_after_update.status_code == 200, f"auth/me (after update-role) failed for {username}: {me_after_update.status_code}")
    _assert(
        me_after_update.data.get("last_selected_role") == expected_role,
        f"last_selected_role mismatch for {username}: {me_after_update.data.get('last_selected_role')} != {expected_role}",
    )

    endpoint_response = client.get(expected_endpoint)
    _assert(endpoint_response.status_code == 200, f"role endpoint failed for {username} on {expected_endpoint}: {endpoint_response.status_code}")


def run():
    _ensure_account("patent_student", "Patent", "Student", "student", "student", "academic")
    _ensure_account("patent_pcc", "Patent", "PCC", "staff", "PCC Admin", "administrative")
    _ensure_account("patent_director", "Patent", "Director", "staff", "Director", "administrative")

    # Frontend availability checks for login page and SPA route.
    _check_frontend_url("http://127.0.0.1:5173/accounts/login")
    _check_frontend_url("http://127.0.0.1:5173/patentsystem")

    client = APIClient()
    client.raise_request_exception = False

    _run_role_flow(
        client,
        username="patent_student",
        expected_role="student",
        expected_endpoint="/patentsystem/applicant/insights/",
    )
    _run_role_flow(
        client,
        username="patent_pcc",
        expected_role="PCC Admin",
        expected_endpoint="/patentsystem/pccAdmin/insights/",
    )
    _run_role_flow(
        client,
        username="patent_director",
        expected_role="Director",
        expected_endpoint="/patentsystem/director/insights/",
    )

    # Authorization boundary check: Director must not access PCC-only insights endpoint.
    login_director = client.post(
        "/api/auth/login/",
        {"username": "patent_director", "password": PASSWORD},
        format="json",
    )
    director_token = login_director.data.get("token")
    client.credentials(HTTP_AUTHORIZATION=f"Token {director_token}")
    forbidden_response = client.get("/patentsystem/pccAdmin/insights/")
    _assert(forbidden_response.status_code == 403, f"expected 403 for director on pcc insights, got {forbidden_response.status_code}")

    print("PATENT_ROLE_AUTH_FLOW_SMOKE: PASS")


try:
    run()
except (HTTPError, URLError) as exc:
    raise AssertionError(f"frontend availability check failed: {exc}")
