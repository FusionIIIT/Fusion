#!/usr/bin/env python3
"""Check course setup"""
import requests
import json

BASE_URL = "http://localhost:8000"

def login(username, password):
    response = requests.post(
        f"{BASE_URL}/api/auth/login/",
        data={"username": username, "password": password}
    )
    if response.status_code == 200:
        data = response.json()
        return data.get("token") or data.get("access")
    return None

print("Getting available courses for teacher...")
teacher_token = login("testteacher", "testteacher123")
if teacher_token:
    headers = {"Authorization": f"Token {teacher_token}"}
    response = requests.get(
        f"{BASE_URL}/ocms/api/courses/",
        headers=headers
    )
    print(f"Status: {response.status_code}")
    print(f"Courses: {json.dumps(response.json(), indent=2)}")
