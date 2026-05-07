#!/usr/bin/env python3
"""Create an active quiz for testing"""
import requests
import json
from datetime import datetime, timedelta

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

print("="*70)
print("CREATING ACTIVE QUIZ FOR STUDENT VISIBILITY")
print("="*70)

# Login as teacher
teacher_token = login("testteacher", "testteacher123")
if not teacher_token:
    print("✗ Failed to login as teacher")
    exit(1)

print(f"\n✓ Teacher logged in")

# Create a quiz with active time window
now = datetime.utcnow()
start_time = now - timedelta(minutes=5)  # Started 5 minutes ago
end_time = now + timedelta(hours=2)      # Ends in 2 hours

print(f"\nCurrent UTC time: {now.isoformat()}")
print(f"Quiz start time: {start_time.isoformat()}")
print(f"Quiz end time:   {end_time.isoformat()}")

quiz_data = {
    "title": "Active Quiz for Testing",
    "description": "This quiz is currently active and visible to students",
    "start_time": start_time.isoformat() + "Z",
    "end_time": end_time.isoformat() + "Z",
    "duration": 30,
    "negative_marks": 0,
    "total_questions": 3
}

print(f"\n" + "-"*70)
print("Creating quiz...")
print("-"*70)

headers = {"Authorization": f"Token {teacher_token}"}
response = requests.post(
    f"{BASE_URL}/ocms/api/CS101/quizzes/create/",
    headers=headers,
    json=quiz_data
)

print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

if response.status_code in [200, 201]:
    print("\n✅ Quiz created successfully!")
    
    # Test if student can now see it
    print(f"\n" + "-"*70)
    print("Testing student visibility...")
    print("-"*70)
    
    student_token = login("student01", "Control d")
    headers = {"Authorization": f"Token {student_token}"}
    response = requests.get(
        f"{BASE_URL}/ocms/api/CS101/quizzes/",
        headers=headers
    )
    
    if response.status_code == 200:
        quizzes = response.json()
        print(f"Student can see {len(quizzes)} quiz(zes)")
        for q in quizzes:
            if "Active" in q['title']:
                print(f"\n✅ SUCCESS! Student can see the active quiz:")
                print(f"   Title: {q['title']}")
                print(f"   Start: {q['startTime']}")
                print(f"   End:   {q['endTime']}")
else:
    print(f"\n✗ Failed to create quiz: {response.text}")

print("\n" + "="*70)
