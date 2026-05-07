#!/usr/bin/env python3
"""Test student attendance visibility"""
import requests
import json
from datetime import date

BASE_URL = "http://localhost:8000"

def login(username, password):
    """Get authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login/",
        data={"username": username, "password": password}
    )
    if response.status_code == 200:
        data = response.json()
        token = data.get("token") or data.get("access")
        if token:
            print(f"✓ Logged in as {username}: {token[:20]}...")
            return token
        else:
            print(f"✗ No token in response: {data}")
            return None
    else:
        print(f"✗ Login failed: {response.status_code}")
        return None

def test_student_attendance():
    """Test student can see their attendance"""
    print("\n" + "="*60)
    print("Testing Student Attendance Visibility")
    print("="*60)
    
    # Get teacher token to create attendance records
    print("\n[Step 1] Teacher marks attendance for student01")
    teacher_token = login("testteacher", "testteacher123")
    if not teacher_token:
        return
    
    # Teacher posts attendance
    headers = {"Authorization": f"Token {teacher_token}"}
    payload = {
        "date": str(date.today()),
        "attendance": [
            {"student_id": "student01", "present": True},
        ]
    }
    response = requests.post(
        f"{BASE_URL}/ocms/api/CS101/attendance/",
        headers=headers,
        json=payload
    )
    print(f"POST attendance status: {response.status_code}")
    if response.status_code == 200:
        print(f"✓ Response: {response.json()}")
    else:
        print(f"✗ Error: {response.text}")
    
    # Get student token
    print("\n[Step 2] Student logs in")
    student_token = login("student01", "Control d")
    if not student_token:
        return
    
    # Student queries attendance
    print("\n[Step 3] Student queries their attendance for CS101")
    headers = {"Authorization": f"Token {student_token}"}
    response = requests.get(
        f"{BASE_URL}/ocms/api/CS101/attendance/",
        headers=headers
    )
    print(f"GET attendance status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        data = response.json()
        if data:
            print(f"\n✅ SUCCESS! Student can see their attendance records")
            today = str(date.today())
            if today in data:
                print(f"   Attendance for {today}: {data[today]}")
        else:
            print(f"\n⚠️  No attendance records found for student")
    else:
        print(f"\n✗ Error retrieving attendance: {response.text}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    test_student_attendance()
