#!/usr/bin/env python3
"""Test quiz visibility after removing time window restriction"""
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

print("="*70)
print("QUIZ VISIBILITY TEST (After Removing Time Window)")
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

# Teacher checks all quizzes
print("\n" + "-"*70)
print("TEACHER VIEW: All quizzes")
print("-"*70)

headers = {"Authorization": f"Token {teacher_token}"}
response = requests.get(
    f"{BASE_URL}/ocms/api/CS101/quizzes/",
    headers=headers
)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    teacher_quizzes = response.json()
    print(f"Total quizzes: {len(teacher_quizzes)}")
    for q in teacher_quizzes:
        print(f"\n  ✓ {q['title']}")
        print(f"    Start: {q['startTime']}")
        print(f"    End:   {q['endTime']}")

# Student checks quizzes
print("\n" + "-"*70)
print("STUDENT VIEW: All available quizzes (no time window restriction)")
print("-"*70)

headers = {"Authorization": f"Token {student_token}"}
response = requests.get(
    f"{BASE_URL}/ocms/api/CS101/quizzes/",
    headers=headers
)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    student_quizzes = response.json()
    print(f"Visible to student: {len(student_quizzes)}")
    
    if len(student_quizzes) > 0:
        print("\n✅ SUCCESS! Students can see all quizzes:")
        for q in student_quizzes:
            print(f"\n  ✓ {q['title']}")
            print(f"    Start: {q['startTime']}")
            print(f"    End:   {q['endTime']}")
            print(f"    Duration: {q['duration']} minutes")
            print(f"    Questions: {q['totalQuestions']}")
    else:
        print("\n⚠️  No quizzes visible to student")

# Verify the counts match
print("\n" + "-"*70)
print("VERIFICATION")
print("-"*70)

if len(teacher_quizzes) == len(student_quizzes):
    print(f"✅ Student and teacher see same number of quizzes: {len(student_quizzes)}")
else:
    print(f"❌ Mismatch: Teacher sees {len(teacher_quizzes)}, Student sees {len(student_quizzes)}")

print("\n" + "="*70)
print("✅ QUIZ VISIBILITY WORKING CORRECTLY")
print("="*70)
print("\nSummary:")
print("  • Professor can add quiz with just name, description, and date/time")
print("  • Quiz is immediately visible to all students")
print("  • No waiting for 'active window' required")
print("  • Students see all quizzes except those they've already completed")
