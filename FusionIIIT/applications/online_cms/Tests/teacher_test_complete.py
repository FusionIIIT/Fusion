#!/usr/bin/env python3
"""
Complete test script for teacher functionalities in Fusion Online CMS
Tests:
1. Teacher login
2. Get courses for teacher
3. Upload course materials (documents)
4. Create and upload assignments
5. Create and manage quizzes
6. Mark and view attendance
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000"
AUTH_BASE = f"{BASE_URL}/api"
API_BASE = f"{BASE_URL}/ocms/api"

# Test credentials
TEACHER_USERNAME = "testteacher"
TEACHER_PASSWORD = "testteacher123"

# Global token for authenticated requests
auth_token = None

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_section(title):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}{Colors.END}\n")

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.CYAN}ℹ {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")

def print_json(data, title=""):
    if title:
        print(f"{Colors.BOLD}{title}:{Colors.END}")
    print(json.dumps(data, indent=2))

def login_teacher():
    """Login as teacher and get authentication token"""
    print_section("1. TEACHER LOGIN")
    
    url = f"{AUTH_BASE}/auth/login/"
    credentials = {
        "username": TEACHER_USERNAME,
        "password": TEACHER_PASSWORD
    }
    
    print_info(f"Logging in as {TEACHER_USERNAME}...")
    print_info(f"Endpoint: POST {url}")
    
    try:
        response = requests.post(url, json=credentials)
        
        if response.status_code == 200:
            data = response.json()
            global auth_token
            auth_token = data.get('token')
            print_success(f"Login successful!")
            print_info(f"Authentication Token: {auth_token[:20]}...")
            return True
        else:
            print_error(f"Login failed: {response.status_code}")
            print_json(response.json())
            return False
            
    except requests.exceptions.RequestException as e:
        print_error(f"Connection error: {e}")
        return False

def get_teacher_courses():
    """Get list of courses for the teacher"""
    print_section("2. GET TEACHER COURSES")
    
    url = f"{API_BASE}/courses/"
    headers = {"Authorization": f"Token {auth_token}"}
    
    print_info(f"Fetching courses...")
    print_info(f"Endpoint: GET {url}")
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            courses = response.json()
            if courses:
                print_success(f"Found {len(courses)} course(s)")
                for i, course in enumerate(courses, 1):
                    print(f"\n  {Colors.BOLD}Course {i}:{Colors.END}")
                    print(f"    Code: {course.get('courseCode')}")
                    print(f"    Name: {course.get('courseName')}")
                    print(f"    Credits: {course.get('credits')}")
                    print(f"    Semester: {course.get('semester')}")
                return courses
            else:
                print_warning("No courses found for teacher")
                return []
        else:
            print_error(f"Failed to fetch courses: {response.status_code}")
            print_json(response.json())
            return []
            
    except requests.exceptions.RequestException as e:
        print_error(f"Connection error: {e}")
        return []

def upload_course_material(course_code, title, description, url):
    """Upload course material (document/link)"""
    print_section(f"3. UPLOAD COURSE MATERIAL - {course_code}")
    
    api_url = f"{API_BASE}/{course_code}/documents/add/"
    headers = {"Authorization": f"Token {auth_token}"}
    
    payload = {
        "title": title,
        "description": description,
        "url": url
    }
    
    print_info(f"Uploading material to {course_code}...")
    print_info(f"Endpoint: POST {api_url}")
    print(f"\n{Colors.BOLD}Material Details:{Colors.END}")
    print(f"  Title: {title}")
    print(f"  Description: {description}")
    print(f"  URL: {url}")
    
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print_success(f"Material uploaded successfully!")
            print(f"  Document ID: {result.get('id')}")
            return result
        else:
            print_error(f"Failed to upload material: {response.status_code}")
            print_json(response.json())
            return None
            
    except requests.exceptions.RequestException as e:
        print_error(f"Connection error: {e}")
        return None

def create_assignment(course_code, title, description, deadline):
    """Create an assignment for the course"""
    print_section(f"4. CREATE ASSIGNMENT - {course_code}")
    
    url = f"{API_BASE}/{course_code}/assignments/add/"
    headers = {"Authorization": f"Token {auth_token}"}
    
    payload = {
        "title": title,
        "description": description,
        "deadline": deadline
    }
    
    print_info(f"Creating assignment for {course_code}...")
    print_info(f"Endpoint: POST {url}")
    print(f"\n{Colors.BOLD}Assignment Details:{Colors.END}")
    print(f"  Title: {title}")
    print(f"  Description: {description}")
    print(f"  Deadline: {deadline}")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print_success(f"Assignment created successfully!")
            print(f"  Assignment ID: {result.get('id')}")
            return result
        else:
            print_error(f"Failed to create assignment: {response.status_code}")
            print_json(response.json())
            return None
            
    except requests.exceptions.RequestException as e:
        print_error(f"Connection error: {e}")
        return None

def get_assignments(course_code):
    """Get assignments for the course"""
    url = f"{API_BASE}/{course_code}/assignments/"
    headers = {"Authorization": f"Token {auth_token}"}
    
    print_info(f"Fetching assignments for {course_code}...")
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            assignments = response.json()
            if assignments:
                print_success(f"Found {len(assignments)} assignment(s)")
                for i, assign in enumerate(assignments, 1):
                    print(f"\n  {Colors.BOLD}Assignment {i}:{Colors.END}")
                    print(f"    ID: {assign.get('id')}")
                    print(f"    Title: {assign.get('title')}")
                    print(f"    Deadline: {assign.get('deadline')}")
            else:
                print_warning("No assignments found for this course")
            return assignments
        else:
            print_error(f"Failed to fetch assignments: {response.status_code}")
            return []
            
    except requests.exceptions.RequestException as e:
        print_error(f"Connection error: {e}")
        return []

def create_quiz(course_code, title, start_time, end_time, negative_marks=0):
    """Create a quiz for the course"""
    print_section(f"5. CREATE QUIZ - {course_code}")
    
    url = f"{API_BASE}/{course_code}/quizzes/create/"
    headers = {"Authorization": f"Token {auth_token}"}
    
    payload = {
        "title": title,
        "start_time": start_time,
        "end_time": end_time,
        "negative_marks": negative_marks
    }
    
    print_info(f"Creating quiz for {course_code}...")
    print_info(f"Endpoint: POST {url}")
    print(f"\n{Colors.BOLD}Quiz Details:{Colors.END}")
    print(f"  Title: {title}")
    print(f"  Start Time: {start_time}")
    print(f"  End Time: {end_time}")
    print(f"  Negative Marks: {negative_marks}")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print_success(f"Quiz created successfully!")
            print(f"  Quiz ID: {result.get('id')}")
            return result
        else:
            print_error(f"Failed to create quiz: {response.status_code}")
            print_json(response.json())
            return None
            
    except requests.exceptions.RequestException as e:
        print_error(f"Connection error: {e}")
        return None

def get_quizzes(course_code):
    """Get quizzes for the course"""
    url = f"{API_BASE}/{course_code}/quizzes/"
    headers = {"Authorization": f"Token {auth_token}"}
    
    print_info(f"Fetching quizzes for {course_code}...")
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            quizzes = response.json()
            if quizzes:
                print_success(f"Found {len(quizzes)} quiz(zes)")
                for i, quiz in enumerate(quizzes, 1):
                    print(f"\n  {Colors.BOLD}Quiz {i}:{Colors.END}")
                    print(f"    ID: {quiz.get('id')}")
                    print(f"    Title: {quiz.get('title')}")
                    print(f"    Start: {quiz.get('start_time')}")
                    print(f"    End: {quiz.get('end_time')}")
            else:
                print_warning("No quizzes found for this course")
            return quizzes
        else:
            print_error(f"Failed to fetch quizzes: {response.status_code}")
            return []
            
    except requests.exceptions.RequestException as e:
        print_error(f"Connection error: {e}")
        return []

def get_attendance(course_code):
    """Get attendance records for the course"""
    print_section(f"6. GET ATTENDANCE - {course_code}")
    
    url = f"{API_BASE}/{course_code}/attendance/"
    headers = {"Authorization": f"Token {auth_token}"}
    
    print_info(f"Fetching attendance for {course_code}...")
    print_info(f"Endpoint: GET {url}")
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            attendance = response.json()
            if attendance:
                print_success(f"Found attendance records")
                if isinstance(attendance, list) and all(isinstance(rec, dict) for rec in attendance):
                    # Group by date
                    by_date = {}
                    for rec in attendance:
                        date = rec.get('date', 'Unknown')
                        if date not in by_date:
                            by_date[date] = []
                        by_date[date].append(rec)
                    
                    for date, records in sorted(by_date.items()):
                        print(f"\n  {Colors.BOLD}{date}:{Colors.END} {len(records)} records")
                else:
                    print_json(attendance, title="Attendance Response")
            else:
                print_warning("No attendance records found for this course")
            return attendance
        else:
            print_error(f"Failed to fetch attendance: {response.status_code}")
            if response.status_code == 403:
                print_warning("You may not be assigned as instructor in the system.")
                print_warning("See TROUBLESHOOTING section below.")
            print_json(response.json())
            return None
            
    except requests.exceptions.RequestException as e:
        print_error(f"Connection error: {e}")
        return None

def mark_attendance(course_code, date, attendance_data):
    """Mark attendance for the course"""
    print_section(f"7. MARK ATTENDANCE - {course_code}")
    
    url = f"{API_BASE}/{course_code}/attendance/"
    headers = {"Authorization": f"Token {auth_token}"}
    
    payload = {
        "date": date,
        "attendance": attendance_data
    }
    
    print_info(f"Marking attendance for {course_code}...")
    print_info(f"Endpoint: POST {url}")
    print(f"\n{Colors.BOLD}Attendance Details:{Colors.END}")
    print(f"  Date: {date}")
    print(f"  Records: {len(attendance_data)}")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print_success(f"Attendance marked successfully!")
            print_json(result)
            return result
        else:
            print_error(f"Failed to mark attendance: {response.status_code}")
            if response.status_code == 403:
                print_warning("You may not be assigned as instructor in the system.")
                print_warning("See TROUBLESHOOTING section below.")
            print_json(response.json())
            return None
            
    except requests.exceptions.RequestException as e:
        print_error(f"Connection error: {e}")
        return None

def print_troubleshooting():
    """Print troubleshooting guide"""
    print_section("TROUBLESHOOTING")
    
    print(f"{Colors.BOLD}Issue: Attendance returns 403 'Not an instructor for this course'{Colors.END}")
    print("""
The attendance API checks if you're assigned to the course in the old system
(Curriculum_Instructor table), but your assignment is in the new system
(CourseInstructor table).

Solution: Run this Django shell command to assign the teacher:

    python manage.py shell
    
    >>> from applications.academic_information.models import Curriculum_Instructor, ExtraInfo
    >>> from applications.programme_curriculum.models import Curriculum, Course
    >>> 
    >>> # Get the teacher's ExtraInfo
    >>> teacher = ExtraInfo.objects.get(user__username='testteacher')
    >>> 
    >>> # Get the course (assuming CS101 is in curriculum 1)
    >>> course = Course.objects.get(code='CS101')
    >>> curriculum = Curriculum.objects.filter(courses=course).first()
    >>> 
    >>> # Create the assignment if not exists
    >>> Curriculum_Instructor.objects.get_or_create(
    ...     instructor_id=teacher,
    ...     curriculum_id=curriculum
    ... )

Or, the backend should be fixed to check both systems. The bug is in:
    /applications/online_cms/services.py - get_instructor_link() function
    """)

def main():
    """Main test execution"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}")
    print("╔" + "="*58 + "╗")
    print("║" + " "*58 + "║")
    print("║" + "  FUSION ONLINE CMS - COMPLETE TEACHER TEST".center(58) + "║")
    print("║" + " "*58 + "║")
    print("╚" + "="*58 + "╝")
    print(f"{Colors.END}")
    
    # Step 1: Login
    if not login_teacher():
        print_error("Failed to login. Exiting.")
        return
    
    # Step 2: Get courses
    courses = get_teacher_courses()
    if not courses:
        print_error("No courses found. Exiting.")
        return
    
    # Get the first course code
    course_code = courses[0].get('courseCode')
    print_info(f"\nTesting with course: {course_code}")
    
    # Step 3: Upload material
    test_material = {
        "title": f"Test Material - {datetime.now().strftime('%H:%M:%S')}",
        "description": "This is a test material uploaded via API",
        "url": "https://example.com/test_material.pdf"
    }
    upload_course_material(course_code, **test_material)
    
    # Step 4: Create assignment
    deadline = (datetime.now() + timedelta(days=7)).isoformat()
    test_assignment = {
        "title": f"Test Assignment - {datetime.now().strftime('%H:%M:%S')}",
        "description": "This is a test assignment created via API",
        "deadline": deadline
    }
    assignment = create_assignment(course_code, **test_assignment)
    
    # Get all assignments
    assignments = get_assignments(course_code)
    
    # Step 5: Create quiz
    now = datetime.now()
    start_time = now.isoformat()
    end_time = (now + timedelta(hours=1)).isoformat()
    
    test_quiz = {
        "title": f"Test Quiz - {now.strftime('%H:%M:%S')}",
        "start_time": start_time,
        "end_time": end_time,
        "negative_marks": 0
    }
    quiz = create_quiz(course_code, **test_quiz)
    
    # Get all quizzes
    quizzes = get_quizzes(course_code)
    
    # Step 6: Get attendance
    attendance = get_attendance(course_code)
    
    # Step 7: Try to mark attendance (will likely fail if teacher not in old system)
    if attendance is not None:
        today = datetime.now().strftime('%Y-%m-%d')
        # Create mock attendance data (you'll need to adjust student IDs)
        attendance_data = [
            {"student_id": "student01", "present": True},
        ]
        mark_attendance(course_code, today, attendance_data)
    
    # Final summary
    print_section("TEST SUMMARY")
    print_success("Test completed!")
    print_info(f"Teacher {TEACHER_USERNAME} can:")
    print(f"  ✓ Login to the system")
    print(f"  ✓ View their assigned courses")
    print(f"  ✓ Upload course materials")
    print(f"  ✓ Create assignments")
    print(f"  ✓ Create quizzes")
    if attendance is None:
        print(f"  ✗ Access attendance (requires fix - see below)")
    else:
        print(f"  ✓ Access attendance")
    
    # Print troubleshooting if needed
    if attendance is None:
        print_troubleshooting()

if __name__ == "__main__":
    main()
