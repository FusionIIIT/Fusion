from django.db.models.query_utils import Q
from django.http import request,HttpResponse
from django.shortcuts import get_object_or_404, render, HttpResponse,redirect
from django.http import HttpResponse, HttpResponseRedirect
import itertools
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse

# from applications.academic_information.models import Student
from applications.globals.models import (DepartmentInfo, Designation,
                                         ExtraInfo, Faculty, HoldsDesignation)

from applications.academic_procedures.models import(course_registration , Register, Semester)
# from applications.academic_information.models import Course , Curriculum
from applications.programme_curriculum.models import Course as Courses , Curriculum, Discipline, Batch, CourseSlot, CourseInstructor
from applications.examination.models import(hidden_grades , authentication , grade)
from applications.department.models import(Announcements , SpecialRequest)
from applications.academic_information.models import(Student)
from applications.online_cms.models import(Student_grades)
from applications.globals.models import(ExtraInfo)
from . import serializers
from datetime import date 
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response

from django.core.serializers import serialize
from django.http import JsonResponse
import json
from datetime import datetime
import csv
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from django.db.models import IntegerField
from django.db.models.functions import Cast
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import reverse
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment, Font
import traceback
from applications.academic_information.models import Course
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas
from django.core.exceptions import ObjectDoesNotExist


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def exam_view(request):
    """
    API to differentiate roles and provide appropriate redirection links.
    """
    role = request.data.get('Role')

    if not role:
        return Response({"error": "Role parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

    if role in ["Associate Professor", "Professor", "Assistant Professor"]:
        return Response({"redirect_url": "/examination/submitGradesProf/"})
    elif role == "acadadmin":
        return Response({"redirect_url": "/examination/updateGrades/"})
    elif role == "Dean Academic":
        return Response({"redirect_url": "/examination/verifyGradesDean/"})
    else:
        return Response({"redirect_url": "/dashboard/"})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def download_template(request):
    """
    API to download a CSV template for a course based on the provided role, course, and year.
    """
    role = request.data.get('Role')
    course = request.data.get('course')
    year = request.data.get('year')

    if not role:
        return Response({"error": "Role parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
    if not course or not year:
        return Response({"error": "Course and year are required."}, status=status.HTTP_400_BAD_REQUEST)

    if role not in ["acadadmin", "Associate Professor", "Professor", "Assistant Professor", "Dean Academic"]:
        return Response({"error": "Access denied."}, status=status.HTTP_403_FORBIDDEN)

    try:
        User = get_user_model()
        
        course_info = course_registration.objects.filter(
            course_id_id=course,
            working_year=year
        )

        if not course_info.exists():
            return Response({"error": "No registration data found for the provided course and year"}, status=status.HTTP_404_NOT_FOUND)

        course_obj = course_info.first().course_id
        response = HttpResponse(content_type="text/csv")
        filename = f"{course_obj.code}_template_{year}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)

        writer.writerow(["roll_no", "name", "grade", "remarks"])

        for entry in course_info:
            student_entry = entry.student_id
            student_user = User.objects.get(username=student_entry.id_id)
            writer.writerow([student_entry.id_id, f"{student_user.first_name} {student_user.last_name}", "", ""])

        return response

    except Exception as e:
        print(f"Error in download_template: {str(e)}")
        return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

class SubmitGradesView(APIView):
    """
    API to retrieve course information for a specific academic year
    or available working years for the dropdown.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        designation = request.data.get("Role")
        academic_year = request.data.get("academic_year")

        
        if designation != "acadadmin":
            return Response(
                {"success": False, "error": "Access denied."},
                status=status.HTTP_403_FORBIDDEN
            )

       
        if academic_year:
            if not str(academic_year).isdigit():
                return Response(
                    {"error": "Invalid academic year. It must be numeric."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Fetch unique course IDs for the given academic year
            unique_course_ids = course_registration.objects.filter(
                working_year=academic_year
            ).values("course_id").distinct()

            unique_course_ids = unique_course_ids.annotate(
                course_id_int=Cast("course_id", IntegerField())
            )

            # Retrieve course information
            courses_info = Courses.objects.filter(
                id__in=unique_course_ids.values_list("course_id_int", flat=True)
            ).order_by('code')

            
            return Response(
                {"courses": list(courses_info.values())},
                status=status.HTTP_200_OK
            )

        # If no academic year is provided, return available working years
        working_years = course_registration.objects.values("working_year").distinct()

        return Response(
            {"working_years": list(working_years)},
            status=status.HTTP_200_OK
        )
    


"""
API to upload student grades via a CSV file.

- Only users with the role of 'acadadmin' can access this endpoint.
- Requires 'course_id' and 'academic_year' as form data.
- Accepts a CSV file with columns: roll_no, grade, remarks, (optional) semester.
- Validates course existence and prevents duplicate grade submissions.
- Saves grades into the 'Student_grades' model.
- Redirects based on user role after successful upload.

Expected Request:
Headers:
    Authorization: Token <your_auth_token>

Form Data:
    Role: acadadmin
    course_id: <Course_ID>
    academic_year: <Academic_Year>
    csv_file: <CSV_File>

Response:
    200 OK - {"message": "Grades uploaded successfully.", "redirect_url": "/examination/submitGrades"}
    403 Forbidden - {"error": "Access denied."}
    400 Bad Request - {"error": "Invalid file format."} or other validation errors.
    500 Internal Server Error - {"error": "An error occurred: <error_message>"}
"""

class UploadGradesAPI(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        
        des = request.data.get("Role")
        if des != "acadadmin":
            return Response(
                {"success": False, "error": "Access denied."},
                status=status.HTTP_403_FORBIDDEN,
            )

        csv_file = request.FILES.get("csv_file")
        if not csv_file:
            return Response(
                {"error": "No file provided. Please upload a CSV file."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not csv_file.name.endswith(".csv"):
            return Response(
                {"error": "Invalid file format. Please upload a CSV file."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Extract course_id and academic_year from the request data
        course_id = request.data.get("course_id")
        academic_year = request.data.get("academic_year")

        if not course_id or not academic_year or not academic_year.isdigit():
            return Response(
                {"error": "Course ID and a valid Academic Year are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Fetch course and check existing grades
            courses_info = Courses.objects.get(id=course_id)
            courses = Student_grades.objects.filter(
                course_id=courses_info.id, year=academic_year
            )
            students = course_registration.objects.filter(
                course_id_id=course_id, working_year=academic_year
            )

            if not students.exists():
                message = "NO STUDENTS REGISTERED IN THIS COURSE THIS SEMESTER"
                redirect_url = reverse("examination:message") + f"?message={message}"
                return Response(
                    {"error": message, "redirect_url": redirect_url},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if courses.exists() and not courses.first().reSubmit:
                message = "THIS Course was Already Submitted"
                redirect_url = reverse("examination:message") + f"?message={message}"
                return Response(
                    {"error": message, "redirect_url": redirect_url},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Parse CSV file
            decoded_file = csv_file.read().decode("utf-8").splitlines()
            reader = csv.DictReader(decoded_file)

            required_columns = ["roll_no", "grade", "remarks"]
            if not all(column in reader.fieldnames for column in required_columns):
                return Response(
                    {
                        "error": "CSV file must contain the following columns: roll_no, grade, remarks."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            for row in reader:
                roll_no = row["roll_no"]
                grade = row["grade"]
                remarks = row.get("remarks", "")
                semester = row.get("semester", None)

                try:
                    # Fetch student details
                    stud = Student.objects.get(id_id=roll_no)
                    semester = semester or stud.curr_semester_no
                    batch = stud.batch
                    reSubmit = False
                    # Create grade entry
                    Student_grades.objects.update_or_create(
                    roll_no=roll_no,
                    course_id_id=course_id,
                    year=academic_year,
                    semester=semester,
                    batch=batch,
            # Fields that will be updated if a match is found
                    defaults={
                        'grade': grade,
                        'remarks': remarks,
                        'reSubmit': reSubmit,
                    }
                    )
                except Student.DoesNotExist:
                    return Response(
                        {"error": f"Student with roll_no {roll_no} does not exist."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # Determine redirect URL based on user designation
            redirect_url = (
                "/examination/submitGradesProf"
                if des in ["Associate Professor", "Professor", "Assistant Professor"]
                else "/examination/submitGrades"
            )

            return Response(
                {
                    "message": "Grades uploaded successfully.",
                    "redirect_url": redirect_url,
                },
                status=status.HTTP_200_OK,
            )

        except Courses.DoesNotExist:
            return Response(
                {"error": "Invalid course ID."}, status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        

"""
API to fetch courses with unverified grades along with unique academic years.

- Only users with the role of 'acadadmin' can access this endpoint.
- Retrieves courses where at least one student's grades are unverified.
- Fetches the academic years associated with unverified grades.

Expected Request:
Headers:
    Authorization: Token <your_auth_token>

Body (JSON):
    {
        "Role": "acadadmin"
    }

Response:
    200 OK - {
        "courses_info": [{"id": 1, "course_name": "Data Structures", ...}],
        "unique_year_ids": [{"year": "2024"}, {"year": "2025"}]
    }
    403 Forbidden - {"success": false, "error": "Access denied."}
"""

class UpdateGradesAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        
        des = request.data.get("Role")
        
        
        if des != "acadadmin":
            return Response(
                {"success": False, "error": "Access denied."},
                status=403,
            )

        # Get unique course IDs for unverified grades
        unique_course_ids = (
            Student_grades.objects.filter(verified=False)
            .values("course_id")
            .distinct()
            .annotate(course_id_int=Cast("course_id", IntegerField()))
        )

        # Retrieve courses
        courses_info = Courses.objects.filter(
            id__in=unique_course_ids.values_list("course_id_int", flat=True)
        )

        # Get unique academic years
        unique_year_ids = Student_grades.objects.values("year").distinct()

        return Response(
            {
                "courses_info": list(courses_info.values()),
                "unique_year_ids": list(unique_year_ids),
            },
            status=200,
        )
    


"""
API to check if grades have been submitted and are verified for a given course and academic year.

- Only users with the role of 'acadadmin' can access this endpoint.
- Verifies if grades exist for the requested course and year.
- Returns student grades if unverified, else indicates if already verified.

Expected Request:
Headers:
    Authorization: Token <your_auth_token>

Body (JSON):
    {
        "Role": "acadadmin",
        "course": <course_id>,
        "year": <academic_year>
    }

Response:
    200 OK - If grades exist but are unverified:
        {
            "registrations": [
                {"id": 1, "roll_no": "CS101001", "grade": "A", ...}
            ]
        }
    200 OK - If already verified:
        {"message": "This course is already verified."}
    400 Bad Request - If required fields are missing:
        {"error": "Both 'course' and 'year' are required."}
    404 Not Found - If no grades exist:
        {"message": "This course is not submitted by the instructor."}
    403 Forbidden - If access is denied:
        {"success": false, "error": "Access denied."}
"""

class UpdateEnterGradesAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        des = request.data.get("Role")

        
        if des != "acadadmin":
            return Response(
                {"success": False, "error": "Access denied."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get course_id and year from request body
        course_id = request.data.get("course")
        year = request.data.get("year")

        # Validate course_id and year
        if not course_id or not year:
            return Response(
                {"error": "Both 'course' and 'year' are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if the course exists with grades for the given year
        course_present = Student_grades.objects.filter(course_id=course_id, year=year)

        if not course_present.exists():
            return Response(
                {"message": "This course is not submitted by the instructor."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if the course is already verified
        verification = course_present.first().verified
        if verification:
            return Response(
                {"message": "This course is already verified."},
                status=status.HTTP_200_OK,
            )

        
        registrations = course_present.values()

        return Response(
            {"registrations": list(registrations)},
            status=status.HTTP_200_OK,
        )
    


"""
API for moderating student grades (updating, verifying, or creating hidden grades).

- Only users with the roles 'acadadmin' or 'Dean Academic' can access this endpoint.
- Updates grades for students based on course and semester.
- Marks grades as verified and supports resubmission if enabled.
- If a student grade doesn't exist, it creates a hidden grade record.
- Returns the updated grades in a downloadable CSV file.

Expected Request:
Headers:
    Authorization: Token <your_auth_token>

Body (JSON):
    {
        "Role": "acadadmin",
        "student_ids": ["20231001", "20231002"],
        "semester_ids": [5, 5],
        "course_ids": [101, 101],
        "grades": ["A", "B"],
        "allow_resubmission": "YES"
    }

Response:
    200 OK - CSV file with updated grades
    403 Forbidden - If access is denied:
        {"success": false, "error": "Access denied."}
    400 Bad Request - If required fields are missing or mismatched:
        {"error": "Invalid or incomplete grade data provided."}
    500 Internal Server Error - If any unexpected error occurs:
        {"error": "An error occurred: <error_message>"}
"""

class ModerateStudentGradesAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        
        des = request.data.get("Role")
        if des not in ["acadadmin", "Dean Academic"]:
            return Response(
                {"success": False, "error": "Access denied."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Extract data from the request
        student_ids = request.data.get("student_ids", [])
        semester_ids = request.data.get("semester_ids", [])
        course_ids = request.data.get("course_ids", [])
        grades = request.data.get("grades", [])
        allow_resubmission = request.data.get("allow_resubmission", "NO")

       
        if (
            not student_ids
            or not semester_ids
            or not course_ids
            or not grades
            or len(student_ids) != len(semester_ids)
            or len(semester_ids) != len(course_ids)
            or len(course_ids) != len(grades)
        ):
            return Response(
                {"error": "Invalid or incomplete grade data provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update or create grades
        for student_id, semester_id, course_id, grade in zip(
            student_ids, semester_ids, course_ids, grades
        ):
            try:
                grade_of_student = Student_grades.objects.get(
                    course_id=course_id, roll_no=student_id, semester=semester_id
                )
                grade_of_student.grade = grade
                grade_of_student.verified = True
                if allow_resubmission.upper() == "YES":
                    grade_of_student.reSubmit = True
                grade_of_student.save()
            except Student_grades.DoesNotExist:
                # Create a new hidden grade if the student grade doesn't exist
                hidden_grades.objects.create(
                    course_id=course_id,
                    student_id=student_id,
                    semester_id=semester_id,
                    grade=grade,
                )

        # Generate CSV file as the response
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="grades.csv"'

        writer = csv.writer(response)
        writer.writerow(["Student ID", "Semester ID", "Course ID", "Grade"])
        for student_id, semester_id, course_id, grade in zip(
            student_ids, semester_ids, course_ids, grades
        ):
            writer.writerow([student_id, semester_id, course_id, grade])

        # Return the CSV response
        return response
    


"""
API to generate a student's academic transcript for a specific semester.

- Only users with the role 'acadadmin' can access this endpoint.
- Fetches the courses and grades of the student for the requested semester.
- Also retrieves all courses registered by the student up to that semester.
- If a grade is unavailable for a course, it returns "Grading not done yet".

Expected Request:
Headers:
    Authorization: Token <your_auth_token>

Body (JSON):
    {
        "Role": "acadadmin",
        "student": "20231001",
        "semester": 3
    }

Response:
    200 OK - Transcript data
    403 Forbidden - If access is denied:
        {"error": "Access denied."}
    400 Bad Request - If required fields are missing:
        {"error": "Student ID and Semester are required."}
    500 Internal Server Error - If any unexpected error occurs:
        {"error": "An error occurred: <error_message>"}
"""

class GenerateTranscript(APIView):
    permission_classes = [IsAuthenticated] 

    def post(self, request):
       
        des = request.data.get("Role")
        student_id = request.data.get("student")
        semester = request.data.get("semester")
        if des != "acadadmin":
            return Response({"error": "Access denied."}, status=status.HTTP_403_FORBIDDEN)

       

        if not student_id or not semester:
            return Response({"error": "Student ID and Semester are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch courses registered for the given student and semester
        courses_registered = Student_grades.objects.filter(
            roll_no=student_id, semester=semester
        )

        
        course_grades = {}

        # Fetch all courses registered up to the given semester
        total_course_registered = Student_grades.objects.filter(
            roll_no=student_id, semester__lte=semester
        )

        for course in courses_registered:
            try:
                # Fetch the grade for the course
                grade = Student_grades.objects.get(
                    roll_no=student_id, course_id=course.course_id
                )

                course_instance = get_object_or_404(Courses, id=course.course_id_id)

                course_grades[course_instance.id] = {
                    "course_name": course_instance.name,
                    "course_code": course_instance.code,
                    "grade": grade.grade,
                }
            except Student_grades.DoesNotExist:
                course_grades[course.course_id.id] = {"message": "Grading not done yet"}

        total_courses_registered_serialized = [
            {
                "course_id": course.course_id.id,
                "semester": course.semester,
                "grade": course.grade,
            }
            for course in total_course_registered
        ]
        response_data = {
            "courses_grades": course_grades,
            "total_courses_registered": total_courses_registered_serialized,
        }

        return Response(response_data, status=status.HTTP_200_OK)
    


"""
API to fetch available academic details and retrieve students for generating transcripts.

- Only users with the role 'acadadmin' can access this endpoint.
- GET: Retrieves the list of available programmes, batches, and specializations.
- POST: Fetches students based on programme, batch, specialization (optional), and semester.

Expected Requests:
1. GET /api/generate-transcript-form/
   Headers:
       Authorization: Token <your_auth_token>
       X-User-Role: acadadmin
   Response:
       200 OK - List of programmes, batches, and specializations
       403 Forbidden - If access is denied:
           {"error": "Access denied. Invalid or missing role."}

2. POST /api/generate-transcript-form/
   Headers:
       Authorization: Token <your_auth_token>
       X-User-Role: acadadmin
   Body (JSON):
       {
           "programme": "B.Tech",
           "batch": 2021,
           "specialization": "AI & ML",
           "semester": 5
       }
   Response:
       200 OK - List of students in the given filters
       403 Forbidden - If access is denied:
           {"error": "Access denied. Invalid or missing role."}
       400 Bad Request - If required fields are missing:
           {"error": "Programme, batch, and semester are required fields."}
"""

class GenerateTranscriptForm(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        role = request.GET.get("role") 
        print(role,"abcd")
        if not role or role != "acadadmin":
            return Response({"error": "Access denied. Invalid or missing role."}, status=status.HTTP_403_FORBIDDEN)

        programmes = Student.objects.values_list('programme', flat=True).distinct()
        specializations = Student.objects.exclude(
            specialization__isnull=True
        ).values_list('specialization', flat=True).distinct()
        batches = Student.objects.values_list('batch', flat=True).distinct()

        return Response({
            "programmes": list(programmes),
            "batches": list(batches),
            "specializations": list(specializations),
        }, status=status.HTTP_200_OK)

    def post(self, request):
        
        role = request.data.get("Role")
        if not role or role != "acadadmin":
            return Response({"error": "Access denied. Invalid or missing role."}, status=status.HTTP_403_FORBIDDEN)

        programme = request.data.get('programme')
        batch = request.data.get('batch')
        specialization = request.data.get('specialization')
        semester = request.data.get('semester')

        if not programme or not batch or not semester:
            return Response(
                {"error": "Programme, batch, and semester are required fields."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if specialization:
            students = Student.objects.filter(
                programme=programme, batch=batch, specialization=specialization
            ).order_by('id')
        else:
            students = Student.objects.filter(
                programme=programme, batch=batch
            ).order_by('id')

        return Response({
            "students": list(students.values()),
            "semester": semester
        }, status=status.HTTP_200_OK)
    


class GenerateResultAPI(APIView):

    """
    API endpoint to generate an Excel file containing student grades, SPI, and CPI.
    Accessible only by users with the 'acadadmin' role.

    ### Headers:
    - **Authorization**: `Token <your_token>` (Required, for authentication)
    
    ### Request Body (JSON):
    - **Role** (string, required) → User role (must be `"acadadmin"`)
    - **semester** (integer, required) → Semester number for which result is generated
    - **specialization** (string, required) → Branch/discipline acronym (e.g., `"CSE"`)
    - **batch** (integer, required) → Batch year (e.g., `2021`)

    ### Response:
    - **Success (200 OK)**: Returns an Excel file (`student_grades.xlsx`) with student grades, SPI, and CPI.
    - **Errors**:
      - `403 Forbidden`: If the user does not have `"acadadmin"` role.
      - `400 Bad Request`: If required fields are missing.
      - `404 Not Found`: If branch, curriculum, or semester is not found.
      - `500 Internal Server Error`: For any unexpected errors.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            role = request.data.get("Role")
            if role != "acadadmin":
                return Response({"error": "Access denied."}, status=403)

            semester = request.data.get("semester")
            branch = request.data.get("specialization")
            batch = request.data.get("batch")

            if not semester or not branch or not batch:
                return Response({"error": "Semester, Specialization, and Batch are required."}, status=400)

            branch_info = Discipline.objects.filter(acronym=branch).first()
            if not branch_info:
                return Response({'error': 'Branch not found'}, status=404)

            # Fetch curriculum details
            curriculum_id = Batch.objects.filter(
                year=batch, discipline_id=branch_info.id
            ).values_list('curriculum_id', flat=True).first()
            if not curriculum_id:
                return Response({'error': 'Curriculum not found'}, status=404)

            # Validate semester
            semester_info = Semester.objects.filter(
                curriculum_id=curriculum_id, semester_no=semester
            ).first()
            if not semester_info:
                return Response({'error': 'Semester not found'}, status=404)

            # Fetch courses for the semester
            course_slots = CourseSlot.objects.filter(semester_id=semester_info)
            course_ids_from_slots = course_slots.values_list('courses', flat=True)
            course_ids_from_grades = Student_grades.objects.filter(
                batch=batch, semester=semester
            ).values_list('course_id_id', flat=True)
            course_ids = set(course_ids_from_slots).union(set(course_ids_from_grades))

            # Retrieve course details
            courses = Courses.objects.filter(id__in=course_ids)
            courses_map = {course.id: course.credit for course in courses}

            # Fetch students
            students = Student.objects.filter(batch=batch, specialization=branch).order_by('id')

            # Create Excel Workbook
            wb = Workbook()
            ws = wb.active
            ws.title = "Student Grades"

            # Set Header Row
            ws["A1"] = "S. No"
            ws["B1"] = "Roll No"
            ws["A1"].alignment = ws["B1"].alignment = Alignment(horizontal="center", vertical="center")
            ws["A1"].font = ws["B1"].font = Font(bold=True)

            # Adjust column width
            ws.column_dimensions[get_column_letter(1)].width = 12
            ws.column_dimensions[get_column_letter(2)].width = 18

            # Add Course Headers
            col_idx = 3
            for course in courses:
                ws.merge_cells(start_row=1, start_column=col_idx, end_row=1, end_column=col_idx + 1)
                ws.cell(row=1, column=col_idx).value = course.code
                ws.cell(row=1, column=col_idx).alignment = Alignment(horizontal="center", vertical="center")
                ws.cell(row=1, column=col_idx).font = Font(bold=True)

                ws.cell(row=2, column=col_idx).value = course.name
                ws.cell(row=2, column=col_idx).alignment = Alignment(horizontal="center", vertical="center")
                ws.cell(row=2, column=col_idx).font = Font(bold=True)

                ws.cell(row=3, column=col_idx).value = course.credit
                ws.cell(row=3, column=col_idx).alignment = Alignment(horizontal="center", vertical="center")
                ws.cell(row=3, column=col_idx).font = Font(bold=True)

                ws.cell(row=4, column=col_idx).value = "Grade"
                ws.cell(row=4, column=col_idx + 1).value = "Remarks"
                ws.cell(row=4, column=col_idx).alignment = ws.cell(row=4, column=col_idx + 1).alignment = Alignment(horizontal="center", vertical="center")

                ws.column_dimensions[get_column_letter(col_idx)].width = 25
                ws.column_dimensions[get_column_letter(col_idx + 1)].width = 25

                col_idx += 2

            # Add SPI and CPI headers
            ws.cell(row=1, column=col_idx).value = "SPI"
            ws.cell(row=1, column=col_idx).alignment = Alignment(horizontal="center", vertical="center")
            ws.cell(row=1, column=col_idx).font = Font(bold=True)

            ws.cell(row=1, column=col_idx + 1).value = "CPI"
            ws.cell(row=1, column=col_idx + 1).alignment = Alignment(horizontal="center", vertical="center")
            ws.cell(row=1, column=col_idx + 1).font = Font(bold=True)

            # Add Student Grades
            row_idx = 5
            for idx, student in enumerate(students, start=1):
                ws.cell(row=row_idx, column=1).value = idx
                ws.cell(row=row_idx, column=2).value = student.id_id

                ws.cell(row=row_idx, column=1).alignment = ws.cell(row=row_idx, column=2).alignment = Alignment(horizontal="center", vertical="center")

                student_grades = Student_grades.objects.filter(
                    roll_no=student.id_id, course_id_id__in=course_ids, semester=semester
                )

                grades_map = {grade.course_id_id: (grade.grade, grade.remarks, courses_map.get(grade.course_id_id, 0)) for grade in student_grades}

                col_idx = 3
                gained_credit = 0
                total_credit = 0
                grade_conversion = {
                    "O": 1, "A+": 1, "A": 0.9, "B+": 0.8, "B": 0.7,
                    "C+": 0.6, "C": 0.5, "D+": 0.4, "D": 0.3, "F": 0.2
                }

                for course in courses:
                    grade, remark, credits = grades_map.get(course.id, ("N/A", "N/A", 0))
                    ws.cell(row=row_idx, column=col_idx).value = grade
                    ws.cell(row=row_idx, column=col_idx + 1).value = remark
                    ws.cell(row=row_idx, column=col_idx).alignment = ws.cell(row=row_idx, column=col_idx + 1).alignment = Alignment(horizontal="center", vertical="center")

                    gained_credit += grade_conversion.get(grade, 0) * credits
                    total_credit += credits

                    col_idx += 2

                # Calculate SPI
                spi = (10 * gained_credit / total_credit) if total_credit else 0
                ws.cell(row=row_idx, column=col_idx).value = round(spi, 2)
                ws.cell(row=row_idx, column=col_idx + 1).value = 0  # CPI Placeholder
                ws.cell(row=row_idx, column=col_idx).alignment = ws.cell(row=row_idx, column=col_idx + 1).alignment = Alignment(horizontal="center", vertical="center")

                row_idx += 1

            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="student_grades.xlsx"'
            wb.save(response)
            return response

        except Exception as e:
            traceback.print_exc()
            return Response({'error': str(e)}, status=500)
        

class SubmitAPI(APIView):

    """
    API endpoint to fetch the list of unique courses available for submission.
    Accessible only by users with the 'acadadmin' or 'Dean Academic' role.

    ### Headers:
    - **Authorization**: `Token <your_token>` (Required, for authentication)
    
    ### Request Body (JSON):
    - **Role** (string, required) → User role (must be `"acadadmin"` or `"Dean Academic"`)

    ### Response:
    - **Success (200 OK)**: Returns a JSON object with `courses_info`, which contains course details.
    - **Errors**:
      - `403 Forbidden`: If the user does not have `"acadadmin"` or `"Dean Academic"` role.
      - `500 Internal Server Error`: For any unexpected errors.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        role = request.data.get("Role")

        if role not in ["acadadmin", "Dean Academic"]:
            return Response(
                {"error": "Access denied."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get unique course IDs
        unique_course_ids = (
            course_registration.objects.values("course_id")
            .distinct()
            .annotate(course_id_int=Cast("course_id", IntegerField()))
        )

        courses_info = Course.objects.filter(
            id__in=unique_course_ids.values_list("course_id_int", flat=True)
        )

        return Response(
            {"courses_info": list(courses_info.values())},
            status=status.HTTP_200_OK,
        )


class DownloadExcelAPI(APIView):

    """
    API endpoint to generate and download a CSV file containing student grades.

    ### Headers:
    - **Authorization**: `Token <your_token>` (Required, for authentication)

    ### Request Body (JSON):
    - **student_ids** (list, required) → List of student IDs.
    - **semester_ids** (list, required) → Corresponding semester IDs.
    - **course_ids** (list, required) → Corresponding course IDs.
    - **grades** (list, required) → Corresponding grades for the students.

    ### Response:
    - **Success (200 OK)**: Returns a downloadable CSV file with student grades.
    - **Errors**:
      - `400 Bad Request`: If input data is missing or inconsistent in length.
      - `500 Internal Server Error`: For any unexpected errors.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        student_ids = request.data.get("student_ids", [])
        semester_ids = request.data.get("semester_ids", [])
        course_ids = request.data.get("course_ids", [])
        grades = request.data.get("grades", [])

        if (
            not student_ids
            or not semester_ids
            or not course_ids
            or not grades
            or len(student_ids) != len(semester_ids)
            or len(semester_ids) != len(course_ids)
            or len(course_ids) != len(grades)
        ):
            return Response(
                {"error": "Invalid or incomplete grade data provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="grades.csv"'

        writer = csv.writer(response)
        writer.writerow(["Student ID", "Semester ID", "Course ID", "Grade"])
        for student_id, semester_id, course_id, grade in zip(
            student_ids, semester_ids, course_ids, grades
        ):
            writer.writerow([student_id, semester_id, course_id, grade])

        return response


class SubmitGradesProfAPI(APIView):

    """
    API endpoint to fetch courses assigned to a professor and available academic years.

    ### Headers:
    - **Authorization**: `Token <your_token>` (Required for authentication)

    ### Request Body (JSON):
    - **Role** (string, required) → User's role (Must be one of `Associate Professor`, `Professor`, or `Assistant Professor`).

   
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        
        role = request.data.get("Role")

        
        if role not in ["Associate Professor", "Professor", "Assistant Professor"]:
            return Response(
                {"success": False, "error": "Access denied."},
                status=status.HTTP_403_FORBIDDEN,
            )

        
        instructor_id = request.user.username

        # Fetch unique course IDs for the instructor
        unique_course_ids = (
            CourseInstructor.objects.filter(instructor_id_id=instructor_id)
            .values("course_id_id")
            .distinct()
            .annotate(course_id_int=Cast("course_id_id", IntegerField()))
        )

        # Retrieve course details
        courses_info = Courses.objects.filter(
            id__in=unique_course_ids.values_list("course_id_int", flat=True)
        )

        # Get unique academic years
        working_years = course_registration.objects.values("working_year").distinct()

        return Response(
            {
                "courses_info": list(courses_info.values()),
                "working_years": list(working_years),
            },
            status=status.HTTP_200_OK,
        )


class UploadGradesProfAPI(APIView):
    """
    API to upload grades for a course by a professor.
    
    This API allows professors (Associate Professor, Professor, Assistant Professor) 
    to upload student grades via a CSV file. The API performs necessary validations 
    before saving the grades in the database.

    Request:
        - Method: POST
        - Headers:
            - Authorization: Token <token>
        - Body (Form Data / Multipart Request):
            - Role: User role (Associate Professor, Professor, Assistant Professor)
            - csv_file: (file) CSV file containing student grades.
            - course_id:  ID of the course.
            - academic_year:  Academic year (should be a valid number).
    
    CSV File Format:
        - The uploaded file must be in CSV format.
        - Required columns:
            - roll_no (str): Student Roll Number
            - grade (str): Grade awarded
            - remarks (str): Additional comments (if any)
            - semester (optional): Semester number (if not provided, the student's current semester is used)

    Responses:
        - 200 OK: Grades uploaded successfully.
        - 400 Bad Request: Invalid input, incorrect file format, or missing data.
        - 403 Forbidden: User is not authorized.
        - 500 Internal Server Error: Unexpected errors.

    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        role = request.data.get("Role")
        if role not in ["Associate Professor", "Professor", "Assistant Professor"]:
            return Response({"error": "Access denied."}, status=403)

        csv_file = request.FILES.get("csv_file")
        if not csv_file:
            return Response({"error": "No file provided. Please upload a CSV file."}, status=400)

        if not csv_file.name.endswith(".csv"):
            return Response({"error": "Invalid file format. Please upload a CSV file."}, status=400)

        course_id = request.data.get("course_id")
        academic_year = request.data.get("academic_year")

        if not course_id or not academic_year or not academic_year.isdigit():
            return Response({"error": "Course ID and a valid Academic Year are required."}, status=400)

        try:
            # Fetch course information
            course_info = Courses.objects.get(id=course_id)

            # Check if students are registered for this course
            students = course_registration.objects.filter(course_id_id=course_id, working_year=academic_year)
            if not students.exists():
                message = "NO STUDENTS REGISTERED IN THIS COURSE THIS SEMESTER"
                redirect_url = reverse("examination:message") + f"?message={message}"
                return Response({"error": message, "redirect_url": redirect_url}, status=400)

            # Check if the course was already submitted and resubmission is not allowed
            course_grades = Student_grades.objects.filter(course_id=course_id, year=academic_year)
            if course_grades.exists() and not course_grades.first().reSubmit:
                message = "THIS Course was Already Submitted"
                redirect_url = reverse("examination:message") + f"?message={message}"
                return Response({"error": message, "redirect_url": redirect_url}, status=400)

            # Read and process CSV file
            decoded_file = csv_file.read().decode("utf-8").splitlines()
            reader = csv.DictReader(decoded_file)

            required_columns = ["roll_no", "grade", "remarks"]
            if not all(column in reader.fieldnames for column in required_columns):
                return Response({"error": "CSV file must contain: roll_no, grade, remarks."}, status=400)

            for row in reader:
                roll_no = row["roll_no"]
                grade = row["grade"]
                remarks = row.get("remarks", "")

                semester = row["semester"] if "semester" in row and row["semester"] else None
                student = Student.objects.get(id_id=roll_no)
                semester = semester or student.curr_semester_no

                Student_grades.objects.update_or_create(
                    roll_no=roll_no,
                    course_id_id=course_id,
                    year=academic_year,
                    semester=semester,
                    batch=student.batch,
                    defaults={"grade": grade, "remarks": remarks, "reSubmit": False},
                )

            redirect_url = "/examination/submitGradesProf"

            return Response({"message": "Grades uploaded successfully.", "redirect_url": redirect_url}, status=200)

        except Courses.DoesNotExist:
            return Response({"error": "Invalid course ID."}, status=400)
        except Student.DoesNotExist:
            return Response({"error": f"Student with roll_no {roll_no} does not exist."}, status=400)
        except Exception as e:
            return Response({"error": f"An error occurred: {str(e)}"}, status=500)
        

class DownloadGradesAPI(APIView):
    """
    API to retrieve downloadable student grades for professors.

    Request:
        - Method: POST
        - Headers:
            - Authorization: Token <token>
        - Body (JSON):
            {
                "Role": "Associate Professor",
                "academic_year": "2023"
            }

    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Handles POST request to retrieve student grades for download.
        """

        role = request.data.get("Role")
        if role not in ["Associate Professor", "Professor", "Assistant Professor"]:
            return Response(
                {"error": "Access denied."},
                status=status.HTTP_403_FORBIDDEN,
            )

        academic_year = request.data.get("academic_year")

        if academic_year:
            if not academic_year.isdigit():
                return Response({}, status=status.HTTP_400_BAD_REQUEST)

            unique_course_ids = (
                CourseInstructor.objects.filter(instructor_id_id=request.user.username)
                .values("course_id_id")
                .distinct()
                .annotate(course_id_int=Cast("course_id_id", IntegerField()))
            )

            courses_info = Student_grades.objects.filter(
                year=academic_year,
                course_id_id__in=unique_course_ids.values_list("course_id_int", flat=True)
            )

            courses_details = Courses.objects.filter(
                id__in=courses_info.values_list("course_id_id", flat=True)
            )

            return Response({"courses": list(courses_details.values())}, status=status.HTTP_200_OK)

        # If academic_year is not provided, return working years
        working_years = course_registration.objects.values("working_year").distinct()
        return Response({"working_years": list(working_years)}, status=status.HTTP_200_OK)
        

class GeneratePDFAPI(APIView):
    """
    API for generating a PDF containing grade details for a course.
    Only accessible to authenticated users with professor-level roles.
    
    Request:
        - Method: POST
        - Headers:
            - Authorization: Token <token>
        - Body (JSON):
            {
                "Role": "Associate Professor",
                "academic_year": 2023,
                "course_id": 101
            }

    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            role = request.data.get("Role")
            if role not in ["Associate Professor", "Professor", "Assistant Professor"]:
                return Response(
                    {"error": "Access denied."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            course_id = request.data.get("course_id")
            academic_year = request.data.get("academic_year")

            course_info = get_object_or_404(Courses, id=course_id)

            grades = Student_grades.objects.filter(course_id_id=course_id, year=academic_year).order_by("roll_no")

            # Verify if the requesting user is the assigned instructor
            course = CourseInstructor.objects.filter(
                course_id_id=course_id,
                year=academic_year,
                instructor_id_id=request.user.username
            )
            if not course.exists():
                return Response({"success": False, "error": "Course not found."}, status=404)

            # Extract semester from the first entry (assumption: all entries have the same semester)
            semester = course.first().semester_no

            all_grades = ["O", "A+", "A", "B+", "B", "C+", "C", "D+", "D", "F", "I", "S", "X"]
            grade_counts = {grade: grades.filter(grade=grade).count() for grade in all_grades}

            # Create HTTP response for PDF
            response = HttpResponse(content_type="application/pdf")
            response["Content-Disposition"] = f'attachment; filename="{course_info.code}_grades.pdf"'

            doc = SimpleDocTemplate(response, pagesize=letter)
            elements = []
            styles = getSampleStyleSheet()

            # Custom Header Style
            header_style = ParagraphStyle(
            "HeaderStyle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            textColor=HexColor("#333333"),
            spaceAfter=20,
            alignment=1,  
            )
            subheader_style = ParagraphStyle(
                "SubheaderStyle",
                parent=styles["Normal"],
                fontSize=12,
                textColor=HexColor("#666666"),
                spaceAfter=10,
            )
            instructor = request.user.first_name + " " + request.user.last_name

            # Add Header
            elements.append(Paragraph(f"Grade Sheet", header_style))
            field_label_style = ParagraphStyle(
            "FieldLabelStyle",
            parent=styles["Normal"],
            fontSize=12,
            textColor=colors.black, 
            spaceAfter=5,
        )
            field_value_style = ParagraphStyle(
            "FieldValueStyle",
            parent=styles["Normal"],
            fontSize=12,
            textColor=HexColor("#666666"), 
            spaceAfter=10,
        )

            elements.append(Paragraph(f"<b>Session:</b> {academic_year}", field_label_style))
            elements.append(Paragraph(f"<b>Semester:</b> {semester}", field_label_style))
            elements.append(Paragraph(f"<b>Course Code:</b> {course_info.code}", field_label_style))
            elements.append(Paragraph(f"<b>Course Name:</b> {course_info.name}", field_label_style))
            elements.append(Paragraph(f"<b>Instructor:</b> {instructor}", field_label_style))

            data = [["S.No.", "Roll Number", "Grade"]]
            for i, grade in enumerate(grades, 1):
                data.append([i, grade.roll_no, grade.grade])
            table = Table(data, colWidths=[80, 300, 100])

            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#E0E0E0")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 14),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                        ("BACKGROUND", (0, 1), (-1, -1), HexColor("#F9F9F9")),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#F9F9F9"), colors.white]),
                        ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
                        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 1), (-1, -1), 12),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ]
                )
            )
            elements.append(table)
            elements.append(Spacer(1, 20))

            elements.append(Paragraph(f"Grade Distribution:", header_style))

            grade_data1 = [["O", "A+", "A", "B+", "B", "C+", "C", "D+"]]
            grade_data1.append([grade_counts[grade] for grade in grade_data1[0]])
            grade_table1 = Table(grade_data1, colWidths=[60] * 8)
            grade_table1.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#E0E0E0")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 12),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                        ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
                    ]
                )
            )
            elements.append(grade_table1)
            elements.append(Spacer(1, 10))

            grade_data2 = [["D", "F", "I", "S", "X"]]
            grade_data2.append([grade_counts[grade] for grade in grade_data2[0]])
            grade_table2 = Table(grade_data2, colWidths=[60] * 5)
            grade_table2.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#E0E0E0")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 12),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                        ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
                    ]
                )
            )
            elements.append(grade_table2)
            elements.append(Spacer(1, 40))

            verified_style = ParagraphStyle(
            "VerifiedStyle",
            parent=styles["Normal"],
            fontSize=13,
            textColor=HexColor("#333333"),
            alignment=0, 
            spaceAfter=20,
            )
            elements.append(Paragraph("I have carefully checked and verified the submitted grade. The grade distribution and submitted grades are correct. [Please mention any exception below.]", verified_style))

            def draw_signatures(canvas, doc):
                canvas.saveState()
                width, height = letter
                canvas.drawString(inch, 0.75 * inch, "")
                canvas.drawString(inch, 0.5 * inch, "Date")
                canvas.drawString(width - 4 * inch, 0.75 * inch, "")
                canvas.drawString(width - 4 * inch, 0.5 * inch, "Course Instructor's Signature")
                canvas.restoreState()

            doc.build(elements, onLaterPages=draw_signatures, onFirstPage=draw_signatures)
            return response

        except Exception as e:
            traceback.print_exc()
            return Response({'error': str(e)}, status=500)


"""
API for the Dean Academic to verify if a course has been submitted by the instructor.

Only users with the role 'Dean Academic' can access this endpoint.

POST: Retrieves courses that have been verified by the Dean Academic.
Expected Requests:
1. POST /api/verify-grades-dean/
    Headers:
        Authorization: Token <your_auth_token>  
        X-User-Role: Dean Academic  
        Body (JSON):
        {
        "Role": "Dean Academic"
        }
    Response:
        200 OK - List of verified courses and unique years
            {
            "courses_info": [
                {
                "id": 1,
                "name": "Mathematics",
                "code": "MATH101"
                }
            ],
            "unique_year_ids": [
                {"year": 2024},
                {"year": 2023}
            ]
            }
        403 Forbidden - Access Denied
            {"error": "Access denied. Invalid or missing role."}
        400 Bad Request - Missing Required Fields
            {"error": "Role is required."}
        500 Internal Server Error - Unexpected Error
            {"error": "An error occurred: <error_message>"}
"""
class VerifyGradesDeanView(APIView):
    """
    API for Dean Academic to verify student grades.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        designation = request.data.get("Role")

        if designation != "Dean Academic":
            return Response(
                {"success": False, "error": "Access denied."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Fetch unique course IDs with verified grades
        unique_course_ids = Student_grades.objects.filter(
            verified=True
        ).values("course_id").distinct()

        unique_course_ids = unique_course_ids.annotate(
            course_id_int=Cast("course_id", IntegerField())
        )

        # Retrieve course information
        courses_info = Courses.objects.filter(
            id__in=unique_course_ids.values_list("course_id_int", flat=True)
        ).order_by("code")

        unique_year_ids = Student_grades.objects.values("year").distinct()

        return Response(
            {
                "courses_info": list(courses_info.values()),
                "unique_year_ids": list(unique_year_ids),
            },
            status=status.HTTP_200_OK
        )


"""
API for the Dean Academic to verify if a course has been submitted by the instructor.

Only users with the role 'Dean Academic' can access this endpoint.

POST: Checks if a course has been submitted by the instructor.
    If found, returns student registrations for that course.
    If not found, returns a message that the grading is not submitted.
Expected Requests:
1. POST /api/update-enter-grades-dean/
    Headers:
        Authorization: Token <your_auth_token>  
        X-User-Role: Dean Academic  
        Body (JSON):
        {
        "Role": "Dean Academic",
        "course": "CS101",
        "year": 2024
        }
    Response:
        200 OK - Course Found & Student Registrations
        {
        "registrations": [
            {
            "id": 1,
            "course_id": "CS101",
            "year": 2024,
            "grade": "A"
            }
        ]
        }
        404 Not Found - Course Not Submitted
            {"message": "THIS COURSE IS NOT SUBMITTED BY THE INSTRUCTOR"}
        403 Forbidden - Access Denied
            {"error": "Access denied. Invalid or missing role."}
        400 Bad Request - Missing Required Fields
            {"error": "Role, course, and year are required fields."}
        500 Internal Server Error - Unexpected Error
            {"error": "An error occurred: <error_message>"}
"""
class UpdateEnterGradesDeanView(APIView):
    """
    API for Dean Academic to verify if a course has been submitted by the instructor.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        designation = request.data.get("Role")
        course_id = request.data.get("course")
        year = request.data.get("year")

        if designation != "Dean Academic":
            return Response(
                {"success": False, "error": "Access denied."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if the course is present in Student_grades
        course_present = Student_grades.objects.filter(
            course_id=course_id, year=year
        )

        if not course_present.exists():
            return Response(
                {"message": "THIS COURSE IS NOT SUBMITTED BY THE INSTRUCTOR"},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            {"registrations": list(course_present.values())},
            status=status.HTTP_200_OK
        )


"""
Only users with the role 'Dean Academic' can access this endpoint.

POST: Returns a list of verified courses and available working years.
Expected Request:
1. POST /api/validate-dean/
    Headers:
        Authorization: Token <your_auth_token>  
        X-User-Role: Dean Academic  
        Body (JSON):
            {
            "Role": "Dean Academic"
            }
    Response:
        200 OK - List of Verified Courses & Working Years
            {
            "courses_info": [
                {
                "id": 1,
                "name": "Computer Networks",
                "code": "CN101"
                }
            ],
            "working_years": [
                {"working_year": 2024},
                {"working_year": 2023}
            ]
            }
        403 Forbidden - Access Denied
            {"error": "Access denied."}
        400 Bad Request - Missing Required Fields
            {"error": "Role is required."}
        500 Internal Server Error - Unexpected Error
            {"error": "An error occurred: <error_message>"}

"""
class ValidateDeanView(APIView):
    """
    API for Dean Academic to validate courses and fetch working years & batches.
    
    - Only users with the role 'Dean Academic' can access this endpoint.
    - Returns a list of verified courses, available working years, and batch details.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        role = request.data.get("Role")

        if role != "Dean Academic":
            return Response(
                {"error": "Access denied."}, 
                status=status.HTTP_403_FORBIDDEN
            )

        # Fetch unique verified course IDs
        unique_course_ids = Student_grades.objects.filter(verified=True).values("course_id").distinct()
        unique_course_ids = unique_course_ids.annotate(course_id_int=Cast("course_id", IntegerField()))

        # Retrieve course names and codes
        courses_info = Courses.objects.filter(
            id__in=unique_course_ids.values_list("course_id_int", flat=True)
        )

        # Fetch available working years and batch IDs
        working_years = course_registration.objects.values("working_year").distinct()
        unique_batch_ids = Student_grades.objects.values("batch").distinct()

        return Response(
            {
                "courses_info": list(courses_info.values()),
                "working_years": list(working_years),
                # "unique_batch_ids": list(unique_batch_ids),
            },
            status=status.HTTP_200_OK
        )


class ValidateDeanSubmitView(APIView):
    """
    API for Dean Academic to submit and validate student grades from a CSV file.
    
    - Only users with the role 'Dean Academic' can access this endpoint.
    - Accepts a CSV file containing roll numbers, grades, and remarks.
    - Validates grades against the existing database records and finds mismatches.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        role = request.data.get("Role")

        if role != "Dean Academic":
            return Response(
                {"error": "Access denied."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Validate file existence
        if "csv_file" not in request.FILES:
            return Response(
                {"error": "CSV file is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        csv_file = request.FILES["csv_file"]

        # Validate file type
        if not csv_file.name.endswith(".csv"):
            return Response(
                {"error": "Please submit a valid CSV file."},
                status=status.HTTP_400_BAD_REQUEST
            )

        course_id = request.data.get("course")
        academic_year = request.data.get("year")

        # Validate required fields
        if not course_id or not academic_year:
            return Response(
                {"error": "Course and Academic Year are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not academic_year.isdigit():
            return Response(
                {"error": "Academic Year must be a number."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Fetch students registered for the course
        students = course_registration.objects.filter(
            course_id_id=course_id, working_year=academic_year
        )

        try:
            # Parse the CSV file
            decoded_file = csv_file.read().decode("utf-8").splitlines()
            reader = csv.DictReader(decoded_file)

            required_columns = ["roll_no", "grade", "remarks"]
            if not all(column in reader.fieldnames for column in required_columns):
                return Response(
                    {"error": "CSV file must contain the following columns: roll_no, grade, remarks."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            mismatches = []

            for row in reader:
                roll_no = row["roll_no"]
                grade = row["grade"]
                remarks = row["remarks"]

                try:
                    student = Student.objects.get(id_id=roll_no)
                    semester = student.curr_semester_no
                    batch = student.batch

                    student_grade = Student_grades.objects.get(
                        roll_no=roll_no,
                        course_id_id=course_id,
                        year=academic_year,
                        batch=batch
                    )

                    if student_grade.grade != grade:
                        mismatches.append({
                            "roll_no": roll_no,
                            "csv_grade": grade,
                            "db_grade": student_grade.grade,
                            "remarks": remarks,
                            "batch": batch,
                            "semester": semester,
                            "course_id": course_id
                        })
                except ObjectDoesNotExist:
                    return Response(
                        {"error": f"Student or grade record not found for roll number: {roll_no}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            if not mismatches:
                return Response(
                    {"message": "There are no mismatches."},
                    status=status.HTTP_200_OK
                )

            return Response(
                {"mismatches": mismatches},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": f"An error occurred while processing the file: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CheckResultView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        roll_number = request.user.username
        semester = request.data.get('semester')
        # print(roll_number,semester)
        grades_info = Student_grades.objects.filter(roll_no=roll_number, semester=semester).select_related('course_id')

        gained_credit = 0
        total_credit = 0
        all_credits = 0

        for grades in grades_info:
            credits = grades.course_id.credit
            grade = grades.grade

            if grade == "O" or grade == "A+":
                gained_credit += 1 * credits
            elif grade == "A":
                gained_credit += 0.9 * credits
            elif grade == "B+":
                gained_credit += 0.8 * credits
            elif grade == "B":
                gained_credit += 0.7 * credits
            elif grade == "C+":
                gained_credit += 0.6 * credits
            elif grade == "C":
                gained_credit += 0.5 * credits
            elif grade == "D+":
                gained_credit += 0.4 * credits
            elif grade == "D":
                gained_credit += 0.3 * credits
            elif grade == "F":
                gained_credit += 0.2 * credits

            total_credit += credits
            all_credits += credits

        spi = 10 * (gained_credit / total_credit) if total_credit > 0 else 0

        all_grades = Student_grades.objects.filter(roll_no=roll_number)
        total_units = sum(grade.course_id.credit for grade in all_grades)
        # print(grades_info)
        response_data = {
            "success": True,
            "courses": [
                {
                    "courseid": grade.course_id.id,
                    "coursename": grade.course_id.name,
                    "credits": grade.course_id.credit,
                    "grade": grade.grade,
                }
                for grade in grades_info
            ],
            "spi": round(spi, 2),
            "su": all_credits, 
            "tu": total_units,  
        }

        return JsonResponse(response_data)