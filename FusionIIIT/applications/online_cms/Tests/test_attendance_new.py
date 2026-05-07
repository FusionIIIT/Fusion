#!/usr/bin/env python3
"""Test attendance API for new CourseInstructor system"""
import requests
import json
from datetime import datetime, date

BASE_URL = "http://localhost:8000"

# Test credentials
TEACHER_USER = "testteacher"
TEACHER_PASS = "testteacher123"
STUDENT_USER = "student01"
STUDENT_PASS = "Control d"

def login(username, password):
    """Get authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login/",
        data={"username": username, "password": password}
    )
    if response.status_code == 200:
        data = response.json()
        # Handle both token formats: "token" or "access"
        token = data.get("token") or data.get("access")
        if token:
            print(f"✓ Logged in as {username}: {token[:20]}...")
            return token
        else:
            print(f"✗ Login failed for {username}: No token in response - {data}")
            return None
    else:
        print(f"✗ Login failed for {username}: {response.status_code} - {response.text}")
        return None

def test_get_attendance(token, course_code="CS101"):
    """Test GET attendance endpoint"""
    headers = {"Authorization": f"Token {token}"}
    response = requests.get(
        f"{BASE_URL}/ocms/api/{course_code}/attendance/",
        headers=headers
    )
    print(f"\nGET /ocms/api/{course_code}/attendance/")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"✓ Response: {json.dumps(response.json(), indent=2)}")
        return True
    else:
        print(f"✗ Error: {response.text}")
        return False

def test_post_attendance(token, course_code="CS101"):
    """Test POST attendance endpoint"""
    headers = {"Authorization": f"Token {token}"}
    payload = {
        "date": str(date.today()),
        "attendance": [
            {"student_id": "student01", "present": True},
            {"student_id": "student02", "present": False}
        ]
    }
    response = requests.post(
        f"{BASE_URL}/ocms/api/{course_code}/attendance/",
        headers=headers,
        json=payload
    )
    print(f"\nPOST /ocms/api/{course_code}/attendance/")
    print(f"Status: {response.status_code}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    if response.status_code == 200:
        print(f"✓ Response: {json.dumps(response.json(), indent=2)}")
        return True
    else:
        print(f"✗ Error: {response.text}")
        return False

def main():
    print("=" * 60)
    print("Testing Attendance API for New CourseInstructor System")
    print("=" * 60)
    
    # Test teacher flow
    print("\n[TEACHER TESTS]")
    teacher_token = login(TEACHER_USER, TEACHER_PASS)
    if not teacher_token:
        return
    
    print("\n--- Test 1: GET existing attendance (should be empty initially) ---")
    test_get_attendance(teacher_token, "CS101")
    
    print("\n--- Test 2: POST attendance records ---")
    test_post_attendance(teacher_token, "CS101")
    
    print("\n--- Test 3: GET attendance again (should show saved records) ---")
    test_get_attendance(teacher_token, "CS101")
    
    # Test student flow
    print("\n\n[STUDENT TESTS]")
    student_token = login(STUDENT_USER, STUDENT_PASS)
    if not student_token:
        return
    
    print("\n--- Test 4: Student GET attendance (should show their own records) ---")
    test_get_attendance(student_token, "CS101")
    
    print("\n" + "=" * 60)
    print("Attendance API Tests Complete")
    print("=" * 60)

if __name__ == "__main__":
    main()
