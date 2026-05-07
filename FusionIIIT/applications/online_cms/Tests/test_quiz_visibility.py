#!/usr/bin/env python3
"""Check quiz visibility"""
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
print("QUIZ VISIBILITY TEST")
print("="*70)

# Login as teacher
teacher_token = login("testteacher", "testteacher123")
if not teacher_token:
    print("✗ Failed to login as teacher")
    exit(1)

# Login as student
student_token = login("student01", "Control d")
if not student_token:
    print("✗ Failed to login as student")
    exit(1)

print(f"\n✓ Teacher logged in")
print(f"✓ Student logged in")

# Teacher checks all quizzes (both active and inactive)
print("\n" + "-"*70)
print("TEACHER VIEW: All quizzes (no time filtering)")
print("-"*70)

headers = {"Authorization": f"Token {teacher_token}"}
response = requests.get(
    f"{BASE_URL}/ocms/api/CS101/quizzes/",
    headers=headers
)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    quizzes = response.json()
    print(f"Total quizzes: {len(quizzes)}")
    now = datetime.now().replace(tzinfo=None)
    print(f"Current time (local): {now.isoformat()}")
    for q in quizzes:
        start_str = q['startTime'].replace('Z', '+00:00').replace('+00:00', '')
        end_str = q['endTime'].replace('Z', '+00:00').replace('+00:00', '')
        start = datetime.fromisoformat(start_str)
        end = datetime.fromisoformat(end_str)
        
        print(f"\n  Quiz: {q['title']}")
        print(f"    Start: {q['startTime']}")
        print(f"    End:   {q['endTime']}")
        print(f"    Status: ", end="")
        
        if start > now:
            print(f"NOT STARTED (in {(start - now).total_seconds() / 3600:.1f} hours)")
        elif end < now:
            print(f"FINISHED (ended {(now - end).total_seconds() / 3600:.1f} hours ago)")
        else:
            print("ACTIVE (between start and end)")

# Student checks quizzes (with time filtering)
print("\n" + "-"*70)
print("STUDENT VIEW: Only active quizzes (with time filtering)")
print("-"*70)

headers = {"Authorization": f"Token {student_token}"}
response = requests.get(
    f"{BASE_URL}/ocms/api/CS101/quizzes/",
    headers=headers
)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    quizzes = response.json()
    print(f"Visible quizzes: {len(quizzes)}")
    if quizzes:
        for q in quizzes:
            print(f"\n  ✓ {q['title']}")
            print(f"    Start: {q['startTime']}")
            print(f"    End:   {q['endTime']}")
    else:
        print("\n⚠️  No quizzes visible to student!")
        print("\nPossible reasons:")
        print("1. All quizzes have start_time in the future")
        print("2. All quizzes have end_time in the past")
        print("3. Student has already completed all active quizzes")

print("\n" + "="*70)
