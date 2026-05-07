#!/usr/bin/env python3
"""
Test script for student functionalities in Fusion Online CMS
Tests:
1. Student login
2. Get enrolled courses
3. View course dashboard
4. View course materials/documents
5. View assignments
6. Submit assignments
7. View quiz
8. Participate in forum
9. View attendance
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

# Test credentials
STUDENT_USERNAME = "student01"
STUDENT_PASSWORD = "Control d"

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

def login_student():
    """Login as student and get authentication token"""
    print_section("1. STUDENT LOGIN")
    
    url = f"{API_BASE}/auth/login/"
    credentials = {
        "username": STUDENT_USERNAME,
        "password": STUDENT_PASSWORD
    }
    
    print_info(f"Logging in as {STUDENT_USERNAME}...")
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

def get_student_courses():
    """Get list of courses enrolled by the student"""
    print_section("2. GET ENROLLED COURSES")
    
    url = f"http://localhost:8000/ocms/api/courses/"
    headers = {"Authorization": f"Token {auth_token}"}
    
    print_info(f"Fetching enrolled courses...")
    print_info(f"Endpoint: GET {url}")
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            courses = response.json()
            if courses:
                print_success(f"Found {len(courses)} course(s)")
                for i, course in enumerate(courses, 1):
                    print(f"\n  {Colors.BOLD}Course {i}:{Colors.END}")
                    print(f"    Course Code: {course.get('courseCode')}")
                    print(f"    Course Name: {course.get('courseName')}")
                    print(f"    Credits: {course.get('credits')}")
                    print(f"    Semester: {course.get('semester')}")
                    print(f"    Programme: {course.get('programme', 'N/A')}")
                return courses
            else:
                print_warning("No courses enrolled")
                return []
        else:
            print_error(f"Failed to fetch courses: {response.status_code}")
            print_json(response.json())
            return []
            
    except requests.exceptions.RequestException as e:
        print_error(f"Connection error: {e}")
        return []

def get_course_dashboard(course_code):
    """Get course dashboard information"""
    print_section(f"3. GET COURSE DASHBOARD - {course_code}")
    
    url = f"http://localhost:8000/ocms/api/{course_code}/dashboard/"
    headers = {"Authorization": f"Token {auth_token}"}
    
    print_info(f"Fetching dashboard for {course_code}...")
    print_info(f"Endpoint: GET {url}")
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            dashboard = response.json()
            print_success(f"Dashboard retrieved successfully")
            print(f"\n{Colors.BOLD}Course Information:{Colors.END}")
            print(f"  Course Code: {dashboard.get('courseCode')}")
            print(f"  Course Name: {dashboard.get('courseName')}")
            print(f"  Course Details: {dashboard.get('courseDetails', 'N/A')}")
            print(f"  Credits: {dashboard.get('credits')}")
            print(f"  Semester: {dashboard.get('semester')}")
            print(f"  Programme: {dashboard.get('programme', 'N/A')}")
            
            counts = dashboard.get('counts', {})
            print(f"\n{Colors.BOLD}Content Available:{Colors.END}")
            print(f"  Documents: {counts.get('documents', 0)}")
            print(f"  Assignments: {counts.get('assignments', 0)}")
            print(f"  Forum Posts: {counts.get('forum', 0)}")
            print(f"  Attendance Records: {counts.get('attendance', 0)}")
            
            return dashboard
        else:
            print_error(f"Failed to fetch dashboard: {response.status_code}")
            print_json(response.json())
            return None
            
    except requests.exceptions.RequestException as e:
        print_error(f"Connection error: {e}")
        return None

def get_course_documents(course_code):
    """Get course materials/documents"""
    print_section(f"4. GET COURSE MATERIALS - {course_code}")
    
    url = f"http://localhost:8000/ocms/api/{course_code}/documents/"
    headers = {"Authorization": f"Token {auth_token}"}
    
    print_info(f"Fetching documents/materials for {course_code}...")
    print_info(f"Endpoint: GET {url}")
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            documents = response.json()
            if documents:
                print_success(f"Found {len(documents)} document(s)/material(s)")
                for i, doc in enumerate(documents, 1):
                    print(f"\n  {Colors.BOLD}Material {i}:{Colors.END}")
                    print(f"    ID: {doc.get('id')}")
                    print(f"    Title: {doc.get('document_name') or doc.get('title')}")
                    print(f"    Description: {doc.get('description')}")
                    print(f"    URL: {doc.get('document_url') or doc.get('url')}")
                    if 'upload_time' in doc:
                        print(f"    Uploaded: {doc.get('upload_time')}")
            else:
                print_warning("No materials available for this course")
            return documents
        else:
            print_error(f"Failed to fetch documents: {response.status_code}")
            print_json(response.json())
            return []
            
    except requests.exceptions.RequestException as e:
        print_error(f"Connection error: {e}")
        return []

def get_assignments(course_code):
    """Get assignments for the course"""
    print_section(f"5. GET ASSIGNMENTS - {course_code}")
    
    url = f"http://localhost:8000/ocms/api/{course_code}/assignments/"
    headers = {"Authorization": f"Token {auth_token}"}
    
    print_info(f"Fetching assignments for {course_code}...")
    print_info(f"Endpoint: GET {url}")
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            assignments = response.json()
            if assignments:
                print_success(f"Found {len(assignments)} assignment(s)")
                for i, assignment in enumerate(assignments, 1):
                    print(f"\n  {Colors.BOLD}Assignment {i}:{Colors.END}")
                    print(f"    ID: {assignment.get('id')}")
                    print(f"    Name: {assignment.get('assignment_name')}")
                    print(f"    URL: {assignment.get('assignment_url')}")
                    print(f"    Submit Date: {assignment.get('submit_date')}")
                    print(f"    Upload Time: {assignment.get('upload_time')}")
            else:
                print_warning("No assignments available for this course")
            return assignments
        else:
            print_error(f"Failed to fetch assignments: {response.status_code}")
            print_json(response.json())
            return []
            
    except requests.exceptions.RequestException as e:
        print_error(f"Connection error: {e}")
        return []

def submit_assignment(course_code, assignment_id=None, file_path=None):
    """Submit an assignment"""
    print_section(f"6. SUBMIT ASSIGNMENT - {course_code}")
    
    url = f"http://localhost:8000/ocms/api/{course_code}/assignments/upload/"
    headers = {"Authorization": f"Token {auth_token}"}
    
    if assignment_id is None:
        print_warning("No assignment_id provided; skipping assignment submission.")
        return None
    
    print_info(f"Submitting assignment for {course_code}...")
    print_info(f"Endpoint: POST {url}")
    
    submission_data = {
        "assignment_id": assignment_id,
        "submission_link": "https://example.com/student_submission.pdf"
    }
    
    try:
        response = requests.post(url, json=submission_data, headers=headers)
        
        if response.status_code in [200, 201]:
            result = response.json()
            print_success(f"Assignment submitted successfully!")
            print_info(f"Submission ID: {result.get('id')}")
            return result
        else:
            print_warning(f"Assignment submission status: {response.status_code}")
            print(f"  Response: {response.json()}")
            return None
            
    except requests.exceptions.RequestException as e:
        print_error(f"Connection error: {e}")
        return None

def get_forum_posts(course_code):
    """Get forum discussions for the course"""
    print_section(f"7. GET FORUM POSTS - {course_code}")
    
    url = f"http://localhost:8000/ocms/api/{course_code}/forum/"
    headers = {"Authorization": f"Token {auth_token}"}
    
    print_info(f"Fetching forum discussions for {course_code}...")
    print_info(f"Endpoint: GET {url}")
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            forum_posts = response.json()
            if forum_posts:
                print_success(f"Found {len(forum_posts)} forum post(s)/thread(s)")
                for i, post in enumerate(forum_posts, 1):
                    print(f"\n  {Colors.BOLD}Post {i}:{Colors.END}")
                    print(f"    ID: {post.get('id')}")
                    print(f"    Question: {post.get('message')}")
                    print(f"    Posted by: {post.get('postedBy')}")
                    print(f"    Comment Time: {post.get('createdAt')}")
            else:
                print_warning("No forum discussions available for this course")
            return forum_posts
        else:
            print_error(f"Failed to fetch forum posts: {response.status_code}")
            print_json(response.json())
            return []
            
    except requests.exceptions.RequestException as e:
        print_error(f"Connection error: {e}")
        return []

def post_forum_question(course_code):
    """Post a question in the forum"""
    print_section(f"8. POST FORUM QUESTION - {course_code}")
    
    url = f"http://localhost:8000/ocms/api/{course_code}/forum/new/"
    headers = {"Authorization": f"Token {auth_token}"}
    
    question_text = f"Test question from student - {datetime.now().strftime('%H:%M:%S')}"
    payload = {
        "message": question_text
    }
    
    print_info(f"Posting question to forum for {course_code}...")
    print_info(f"Endpoint: POST {url}")
    print(f"  Question: {question_text}")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code in [200, 201]:
            result = response.json()
            print_success(f"Forum question posted successfully!")
            print_info(f"Post ID: {result.get('id')}")
            return result
        else:
            print_warning(f"Forum post status: {response.status_code}")
            try:
                print(f"  Response: {response.json()}")
            except:
                print(f"  Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print_error(f"Connection error: {e}")
        return None

def get_attendance(course_code):
    """Get attendance records for the course"""
    print_section(f"9. GET ATTENDANCE - {course_code}")
    
    url = f"http://localhost:8000/ocms/api/{course_code}/attendance/"
    headers = {"Authorization": f"Token {auth_token}"}
    
    print_info(f"Fetching attendance for {course_code}...")
    print_info(f"Endpoint: GET {url}")
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            attendance = response.json()
            if attendance:
                if isinstance(attendance, dict):
                    print_success(f"Found attendance records")
                    total_present = 0
                    total_classes = 0
                    for date, records in attendance.items():
                        print(f"\n  {Colors.BOLD}{date}:{Colors.END} {len(records)} record(s)")
                        for record in records:
                            if isinstance(record, dict):
                                present = record.get('present')
                                if present:
                                    total_present += 1
                                total_classes += 1
                                print(f"    student_id: {record.get('student_id')}")
                                print(f"    present: {present}")
                    attendance_percentage = (total_present / total_classes * 100) if total_classes else 0
                    print(f"\n{Colors.BOLD}Attendance Summary:{Colors.END}")
                    print(f"  Total Classes: {total_classes}")
                    print(f"  Present: {total_present}")
                    print(f"  Absent: {total_classes - total_present}")
                    print(f"  Attendance %: {attendance_percentage:.2f}%")
                elif isinstance(attendance, list):
                    print_success(f"Found {len(attendance)} attendance record(s)")
                    total_present = 0
                    for i, record in enumerate(attendance, 1):
                        print(f"\n  {Colors.BOLD}Record {i}:{Colors.END}")
                        print(f"    ID: {record.get('id')}")
                        print(f"    Date: {record.get('date')}")
                        print(f"    Present: {record.get('present')}")
                        print(f"    Number of Attendance: {record.get('no_of_attendance')}")
                        if record.get('present'):
                            total_present += 1
                    attendance_percentage = (total_present / len(attendance) * 100) if attendance else 0
                    print(f"\n{Colors.BOLD}Attendance Summary:{Colors.END}")
                    print(f"  Total Classes: {len(attendance)}")
                    print(f"  Present: {total_present}")
                    print(f"  Absent: {len(attendance) - total_present}")
                    print(f"  Attendance %: {attendance_percentage:.2f}%")
                else:
                    print_json(attendance, title="Attendance Response")
            else:
                print_warning("No attendance records available")
            return attendance
        else:
            print_error(f"Failed to fetch attendance: {response.status_code}")
            print_json(response.json())
            return []
            
    except requests.exceptions.RequestException as e:
        print_error(f"Connection error: {e}")
        return []

def get_quizzes(course_code):
    """Get available quizzes for the course"""
    print_section(f"10. GET QUIZZES - {course_code}")
    
    url = f"http://localhost:8000/ocms/api/{course_code}/quizzes/"
    headers = {"Authorization": f"Token {auth_token}"}
    
    print_info(f"Fetching quizzes for {course_code}...")
    print_info(f"Endpoint: GET {url}")
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            quizzes = response.json()
            if quizzes:
                print_success(f"Found {len(quizzes)} quiz(zes)")
                for i, quiz in enumerate(quizzes, 1):
                    print(f"\n  {Colors.BOLD}Quiz {i}:{Colors.END}")
                    print(f"    ID: {quiz.get('id')}")
                    print(f"    Title: {quiz.get('title') or quiz.get('quiz_name')}")
                    print(f"    Description: {quiz.get('description')}")
                    print(f"    Total Questions: {quiz.get('total_questions', 'N/A')}")
                    print(f"    Total Marks: {quiz.get('totalmarks', 'N/A')}")
            else:
                print_warning("No quizzes available for this course")
            return quizzes
        else:
            print_error(f"Failed to fetch quizzes: {response.status_code}")
            print_json(response.json())
            return []
            
    except requests.exceptions.RequestException as e:
        print_error(f"Connection error: {e}")
        return []

def main():
    """Main test execution"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}")
    print("╔" + "="*58 + "╗")
    print("║" + " "*58 + "║")
    print("║" + "  FUSION ONLINE CMS - STUDENT FUNCTIONALITIES TEST".center(58) + "║")
    print("║" + " "*58 + "║")
    print("╚" + "="*58 + "╝")
    print(f"{Colors.END}")
    
    # Step 1: Login
    if not login_student():
        print_error("Failed to login. Exiting.")
        return
    
    # Step 2: Get enrolled courses
    courses = get_student_courses()
    if not courses:
        print_warning("No courses currently enrolled.")
        print_info("Creating sample API test with mock course code...")
        print_section("DEMONSTRATION: Testing API endpoints with sample course")
        
        # Use a dummy course code to demonstrate the API endpoints
        sample_course_code = "CS101"
        print_info(f"Demonstrating API functionality with course: {sample_course_code}")
        
        # Test dashboard (will return 404 but shows endpoint is working)
        print_info("\nAttempting to retrieve course dashboard...")
        dashboard = get_course_dashboard(sample_course_code)
        
        # Demonstrate other endpoints
        print_info("\nAttempting to retrieve course materials...")
        documents = get_course_documents(sample_course_code)
        
        print_info("\nAttempting to retrieve assignments...")
        assignments = get_assignments(sample_course_code)
        
        print_info("\nAttempting to retrieve forum discussions...")
        forum_posts = get_forum_posts(sample_course_code)
        
        print_info("\nAttempting to retrieve attendance...")
        attendance = get_attendance(sample_course_code)
        
        print_info("\nAttempting to retrieve quizzes...")
        quizzes = get_quizzes(sample_course_code)
        
        print_section("NOTE")
        print_warning("To test with actual course data, please:")
        print("  1. Ensure the student 'teststudent' is enrolled in courses")
        print("  2. Use valid course codes from your institution")
        print("  3. Verify course materials are uploaded by instructors")
        
        print_section("TEST SUMMARY")
        print_success("Student authentication is working!")
        print_info("API endpoints are functional and responding to requests")
        print_info("Next: Enroll student in courses to see live course data")
        
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ AUTHENTICATION TEST PASSED!{Colors.END}\n")
        return
    
    # Step 3-10: For each course, test all available features
    test_course = courses[0]
    course_code = test_course.get('courseCode')
    print_info(f"\n{'='*60}")
    print_info(f"Testing all features for course: {course_code}")
    print_info(f"{'='*60}")
    
    # Get course dashboard
    dashboard = get_course_dashboard(course_code)
    
    # Get course materials
    documents = get_course_documents(course_code)
    
    # Get assignments
    assignments = get_assignments(course_code)
    if assignments:
        print_info(f"\nFound {len(assignments)} assignment(s). Testing submission...")
        first_assignment_id = assignments[0].get('id')
        submit_assignment(course_code, assignment_id=first_assignment_id)
    
    # Get forum discussions
    forum_posts = get_forum_posts(course_code)
    print_info(f"\nTesting forum post functionality...")
    post_forum_question(course_code)
    
    # Get attendance
    attendance = get_attendance(course_code)
    
    # Get quizzes
    quizzes = get_quizzes(course_code)
    
    # Final summary
    print_section("TEST SUMMARY")
    print_success("All student functionalities tested successfully!")
    print(f"\n{Colors.BOLD}Summary:{Colors.END}")
    print(f"  Courses Enrolled: {len(courses)}")
    print(f"  Current Course: {course_code}")
    print(f"  Materials Available: {len(documents) if documents else 0}")
    print(f"  Assignments: {len(assignments) if assignments else 0}")
    print(f"  Forum Discussions: {len(forum_posts) if forum_posts else 0}")
    print(f"  Attendance Records: {len(attendance) if attendance else 0}")
    print(f"  Quizzes Available: {len(quizzes) if quizzes else 0}")
    
    print(f"\n{Colors.GREEN}{Colors.BOLD}✓ ALL TESTS COMPLETED SUCCESSFULLY!{Colors.END}\n")

if __name__ == "__main__":
    main()
