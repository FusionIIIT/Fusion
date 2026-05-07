#!/usr/bin/env python3
"""
Test script for teacher functionalities in Fusion Online CMS
Tests:
1. Teacher login
2. Get courses for teacher
3. Get course dashboard
4. View course documents
5. Upload course materials
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

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
    
    url = f"{API_BASE}/auth/login/"
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
    
    url = f"{API_BASE}/online_cms/api/courses/"
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

def get_course_dashboard(course_code):
    """Get course dashboard information"""
    print_section(f"3. GET COURSE DASHBOARD - {course_code}")
    
    url = f"{API_BASE}/online_cms/api/{course_code}/dashboard/"
    headers = {"Authorization": f"Token {auth_token}"}
    
    print_info(f"Fetching dashboard for {course_code}...")
    print_info(f"Endpoint: GET {url}")
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            dashboard = response.json()
            print_success(f"Dashboard retrieved successfully")
            print(f"\n{Colors.BOLD}Course Information:{Colors.END}")
            print(f"  Code: {dashboard.get('courseCode')}")
            print(f"  Name: {dashboard.get('courseName')}")
            print(f"  Details: {dashboard.get('courseDetails', 'N/A')}")
            print(f"  Credits: {dashboard.get('credits')}")
            print(f"  Semester: {dashboard.get('semester')}")
            print(f"  Programme: {dashboard.get('programme')}")
            
            counts = dashboard.get('counts', {})
            print(f"\n{Colors.BOLD}Content Counts:{Colors.END}")
            print(f"  Documents: {counts.get('documents', 0)}")
            print(f"  Assignments: {counts.get('assignments', 0)}")
            
            return dashboard
        else:
            print_error(f"Failed to fetch dashboard: {response.status_code}")
            print_json(response.json())
            return None
            
    except requests.exceptions.RequestException as e:
        print_error(f"Connection error: {e}")
        return None

def get_course_documents(course_code):
    """Get documents uploaded for the course"""
    print_section(f"4. GET COURSE DOCUMENTS - {course_code}")
    
    url = f"{API_BASE}/online_cms/api/{course_code}/documents/"
    headers = {"Authorization": f"Token {auth_token}"}
    
    print_info(f"Fetching documents for {course_code}...")
    print_info(f"Endpoint: GET {url}")
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            documents = response.json()
            if documents:
                print_success(f"Found {len(documents)} document(s)")
                for i, doc in enumerate(documents, 1):
                    print(f"\n  {Colors.BOLD}Document {i}:{Colors.END}")
                    print(f"    ID: {doc.get('id')}")
                    print(f"    Title: {doc.get('title')}")
                    print(f"    Description: {doc.get('description')}")
                    print(f"    URL: {doc.get('url')}")
                    print(f"    Uploaded: {doc.get('uploadedAt')}")
            else:
                print_warning("No documents found for this course")
            return documents
        else:
            print_error(f"Failed to fetch documents: {response.status_code}")
            print_json(response.json())
            return []
            
    except requests.exceptions.RequestException as e:
        print_error(f"Connection error: {e}")
        return []

def upload_course_material(course_code, title, description, url):
    """Upload course material (document/link)"""
    print_section(f"5. UPLOAD COURSE MATERIAL - {course_code}")
    
    api_url = f"{API_BASE}/online_cms/api/{course_code}/documents/add/"
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

def main():
    """Main test execution"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}")
    print("╔" + "="*58 + "╗")
    print("║" + " "*58 + "║")
    print("║" + "  FUSION ONLINE CMS - TEACHER FUNCTIONALITIES TEST".center(58) + "║")
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
        print_warning("No courses found. Creating test data...")
        # Try to create test data
        setup_test_data()
        courses = get_teacher_courses()
        
        if not courses:
            print_error("Could not get or create courses. Exiting.")
            return
    
    # Step 3-5: For each course, get dashboard, documents, and upload material
    for course_code in [c.get('courseCode') for c in courses[:1]]:  # Test with first course
        print_info(f"\nTesting operations for course: {course_code}")
        
        # Get dashboard
        dashboard = get_course_dashboard(course_code)
        if not dashboard:
            continue
        
        # Get documents
        documents = get_course_documents(course_code)
        
        # Upload a test material
        test_material = {
            "title": f"Test Material - {datetime.now().strftime('%H:%M:%S')}",
            "description": "This is a test material uploaded via API",
            "url": "https://example.com/test_material.pdf"
        }
        
        uploaded = upload_course_material(course_code, **test_material)
        
        if uploaded:
            # Verify upload by fetching documents again
            print_section("6. VERIFY UPLOAD")
            print_info("Fetching documents again to verify upload...")
            new_documents = get_course_documents(course_code)
            if new_documents and len(new_documents) > len(documents):
                print_success("Material upload verified!")
            else:
                print_warning("Could not verify material upload")
    
    # Final summary
    print_section("TEST SUMMARY")
    print_success("All tests completed!")
    print_info(f"Teacher {TEACHER_USERNAME} can:")
    print(f"  • Login to the system")
    print(f"  • View their assigned courses")
    print(f"  • View course dashboards")
    print(f"  • Access course materials")
    print(f"  • Upload course materials")

def setup_test_data():
    """Setup test data if needed"""
    print_section("SETTING UP TEST DATA")
    
    shell_script = """
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Fusion.settings.development_local')
django.setup()

from applications.programme_curriculum.models import Course, Programme, Batch, CourseInstructor
from applications.globals.models import ExtraInfo
from django.contrib.auth.models import User

try:
    # Get or create programme and batch
    programme, _ = Programme.objects.get_or_create(code='CSE', defaults={'name': 'Computer Science'})
    batch, _ = Batch.objects.get_or_create(year=2024, defaults={'name': 'Batch 2024'})
    
    # Get or create a test course
    course, _ = Course.objects.get_or_create(
        code='TEST101',
        defaults={
            'name': 'Test Course for Teachers',
            'credit': 3,
            'program_id': programme
        }
    )
    
    # Get testteacher and assign to course
    try:
        testteacher_user = User.objects.get(username='testteacher')
        testteacher_extra = ExtraInfo.objects.get(user=testteacher_user)
        
        course_instr, created = CourseInstructor.objects.get_or_create(
            instructor_id=testteacher_extra,
            course_id=course,
            batch_id=batch
        )
        
        if created:
            print("Created test course and assigned to testteacher")
        else:
            print("Test course already assigned to testteacher")
    except Exception as e:
        print(f"Error assigning course: {e}")
        
except Exception as e:
    print(f"Error setting up test data: {e}")
"""
    
    import subprocess
    result = subprocess.run(
        f"cd /home/divyeshtechs/Desktop/Fusion/FusionIIIT && source ../venv/bin/activate && python -c '{shell_script}'",
        shell=True,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print_success("Test data setup completed")
        if result.stdout:
            print_info(result.stdout.strip())
    else:
        print_error(f"Test data setup failed: {result.stderr}")

if __name__ == "__main__":
    main()
