#!/usr/bin/env python3
"""
Test script to verify API endpoint fixes for attendance, course roster, and quiz creation.
This script tests the key functionality that was failing.

Note: This script requires authentication. You need to provide a valid token
or run it in an authenticated session.
"""

import requests
import json
import sys
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000"  # Adjust as needed
API_BASE = "/ocms/api"

# Authentication - Replace with your actual token
# You can get this token from browser localStorage under key "authToken"
AUTH_TOKEN = ""  # Add your token here or pass as command line argument

def get_auth_headers():
    """Get authentication headers for API requests"""
    if AUTH_TOKEN:
        return {"Authorization": f"Token {AUTH_TOKEN}"}
    return {}

def test_course_list():
    """Test getting course list"""
    print("Testing course list...")
    try:
        headers = get_auth_headers()
        response = requests.get(f"{BASE_URL}{API_BASE}/courses/", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            courses = response.json()
            print(f"Found {len(courses)} courses")
            if courses:
                print(f"Sample course: {courses[0]}")
            return courses
        else:
            print(f"Error: {response.text}")
            return []
    except Exception as e:
        print(f"Exception: {e}")
        return []

def test_attendance_roster(course_code):
    """Test getting attendance roster"""
    print(f"\nTesting attendance roster for {course_code}...")
    try:
        headers = get_auth_headers()
        response = requests.get(f"{BASE_URL}{API_BASE}/{course_code}/attendance/roster/", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            roster = response.json()
            print(f"Roster size: {len(roster)}")
            if roster:
                print(f"Sample student: {roster[0]}")
            return roster
        else:
            print(f"Error: {response.text}")
            return []
    except Exception as e:
        print(f"Exception: {e}")
        return []

def test_quiz_creation(course_code):
    """Test creating a quiz"""
    print(f"\nTesting quiz creation for {course_code}...")
    try:
        headers = get_auth_headers()
        # Calculate future dates for the quiz
        now = datetime.now()
        start_time = now + timedelta(minutes=5)
        end_time = now + timedelta(minutes=35)
        
        data = {
            "title": "Test Quiz",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "negative_marks": 0.25,
            "description": "Test quiz for API verification",
            "rules": "No cheating"
        }
        
        response = requests.post(f"{BASE_URL}{API_BASE}/{course_code}/quizzes/create/", 
                               json=data, headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Quiz created: {result}")
            return result
        else:
            print(f"Error: {response.text}")
            return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

def test_attendance_submission(course_code):
    """Test submitting attendance"""
    print(f"\nTesting attendance submission for {course_code}...")
    try:
        headers = get_auth_headers()
        # Get current date
        today = datetime.now().strftime("%Y-%m-%d")
        
        data = {
            "date": today,
            "attendance": [
                {"student_id": "test_student_1", "present": True},
                {"student_id": "test_student_2", "present": False}
            ],
            "notes": "Test attendance"
        }
        
        response = requests.post(f"{BASE_URL}{API_BASE}/{course_code}/attendance/", 
                               json=data, headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Attendance submitted: {result}")
            return result
        else:
            print(f"Error: {response.text}")
            return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

def main():
    print("API Endpoint Fix Verification Test")
    print("=" * 50)
    
    # Test 1: Course list
    courses = test_course_list()
    
    if not courses:
        print("\n❌ No courses found. Please ensure you're authenticated and have courses.")
        return
    
    # Use the first course for testing
    course_code = courses[0].get('courseCode', '')
    if not course_code:
        print("\n❌ No course code found in course list")
        return
    
    print(f"\nUsing course: {course_code}")
    
    # Test 2: Attendance roster
    roster = test_attendance_roster(course_code)
    
    if not roster:
        print("⚠️  Empty roster - this might be expected if no students are enrolled")
    else:
        print(f"✅ Roster test passed - found {len(roster)} students")
    
    # Test 3: Quiz creation
    quiz = test_quiz_creation(course_code)
    
    if quiz:
        print("✅ Quiz creation test passed")
    else:
        print("❌ Quiz creation test failed")
    
    # Test 4: Attendance submission
    attendance = test_attendance_submission(course_code)
    
    if attendance:
        print("✅ Attendance submission test passed")
    else:
        print("❌ Attendance submission test failed")
    
    print("\n" + "=" * 50)
    print("Test completed. Check the results above.")
    print("Note: Some tests may fail if you're not authenticated or don't have proper permissions.")

if __name__ == "__main__":
    main()