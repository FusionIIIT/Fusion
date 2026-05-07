#!/usr/bin/env python3
import requests

BASE_URL = "http://localhost:8000"

# student creds
token_url = f"{BASE_URL}/api/auth/login/"
student = "student01"
password = "Control d"

resp = requests.post(token_url, data={"username": student, "password": password})
print("login status", resp.status_code, resp.text)

if resp.status_code != 200:
    raise SystemExit("login failed")

json_data = resp.json()
token = json_data.get("token") or json_data.get("access")
print("token", token)

headers = {"Authorization": f"Token {token}"}

for course in ["CS101", "CS102", "CS201"]:
    r = requests.get(f"{BASE_URL}/ocms/api/{course}/attendance/", headers=headers)
    print("course", course, "status", r.status_code)
    print(r.json())
