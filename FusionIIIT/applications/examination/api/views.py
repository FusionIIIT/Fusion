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

from applications.academic_procedures.models import(course_registration , Register)
# from applications.academic_information.models import Course , Curriculum
from applications.programme_curriculum.models import Course , Curriculum
from applications.examination.models import(hidden_grades , authentication , grade)
from applications.department.models import(Announcements , SpecialRequest)
from applications.academic_information.models import(Student)
from applications.online_cms.models import(Student_grades)
from applications.globals.models import(ExtraInfo)
from . import serializers
from datetime import date 
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from django.core.serializers import serialize
from django.http import JsonResponse
import json
from datetime import datetime



@api_view(['GET', 'POST'])
def fetch_roll_of_courses(request):
    """
    This function is used to fetch roll numbers of students registered for a specific course.

    @variables:
        course_id - ID of the course for which roll numbers are being fetched
        working_year - Year for which roll numbers are being fetched
        obj - Queryset containing student registrations filtered by course ID and working year
        obj_serialized - Serialized data of student registrations
        resp - Dictionary containing the response data
    """
    if request.method == 'POST':
        # Retrieve the course_id and working_year from the request data
        course_id = request.data.get('course_id')
        working_year = request.data.get('working_year')

        if course_id is None:
            return Response({'error': 'Course ID is required in the request parameters'}, status=status.HTTP_400_BAD_REQUEST)

        # Filter students by the provided course ID and working year
        obj = course_registration.objects.filter(course_id=course_id , working_year=working_year)

        # Serialize the queryset
        obj_serialized = serializers.CourseRegistrationSerializer(obj, many=True).data

        # Prepare the response data
        resp = {
            'objt': obj_serialized
        }

        # Return the response
        return Response(data=resp, status=status.HTTP_200_OK)

    # Return a default response for GET requests
    return Response({'message': 'Students'}, status=status.HTTP_201_CREATED)





# @api_view(['GET', 'POST'])
# def fetch_student_details(request):
#     """
#     This function is used to fetch student details based on course, semester, and batch.

#     @variables:
#         course_id - ID of the course for which student details are being fetched
#         semester_id - ID of the semester for which student details are being fetched
#         batch - Batch for which student details are being fetched
#         course_present - Queryset containing student grades filtered by course, semester, and batch
#         data - Dictionary containing the data to be returned in JSON format
#     """
#     if request.method == 'GET':
#         # Retrieve query parameters
#         course_id = int(request.query_params.get('course'))
#         semester_id = int(request.query_params.get('semester'))
#         year = int(request.query_params.get('batch'))
#         print(course_id,semester_id,year)
#         if course_id is None or semester_id is None or year is None:
#             return JsonResponse({'error': 'Incomplete parameters provided'}, status=400)

#         # Filter student grades based on provided parameters
#         course_present = Student_grades.objects.filter(course_id=course_id, semester=semester_id, year=year)

#         # Prepare data to return in JSON format
#         data = {
#             'registrations': list(course_present.values())  # Convert queryset to list of dictionaries
#         }

#         # Return JSON response
#         return JsonResponse(data)



@api_view(['GET'])
def fetch_student_details(request):
    """
    This function is used to fetch student details based on course, semester, and batch.
    """
    if request.method == 'GET':
        # Retrieve query parameters
        course_id = request.query_params.get('course')
        semester_id = request.query_params.get('semester')
        year = request.query_params.get('year')
        
        if course_id is None or semester_id is None or year is None:
            return JsonResponse({'error': 'Incomplete parameters provided'}, status=400)

        # Convert parameters to appropriate types
        try:
            course_id = int(course_id)
            semester_id = (semester_id)
            year = year
        except ValueError:
            return JsonResponse({'error': 'Invalid parameter types'}, status=400)

        # Filter student grades based on provided parameters
        course_present = Student_grades.objects.filter(course_id=course_id, semester=semester_id, year=year)
        # Prepare data to return in JSON format
        data = {
            'registrations': list(course_present.values())  # Convert queryset to list of dictionaries
        }

        # Return JSON response
        return JsonResponse(data)
    else:
        return JsonResponse({'error': 'Only GET requests are allowed'}, status=405)





@api_view(['GET', 'POST'])
def add_student_details(request):
    """
    This function is used to add student details to the database.

    @variables:
        course_id - ID of the course for which student details are being added
        semester - Semester for which student details are being added
        year - Year for which student details are being added
        roll_no - Roll number of the student
        total_marks - Total marks obtained by the student
        grade - Grade obtained by the student
        batch - Batch for which student details are being added
        student_data_list - List of dictionaries containing student details
        success_count - Counter to keep track of successfully added students
    """
    if request.method == 'POST':
        # Extract list of student details from the request
        student_data_list = request.data.get('students', [])

        # Validate data
        if not student_data_list:
            return Response({'error': 'No student data provided'}, status=400)

        # Counter for successfully added students
        success_count = 0

        # Loop through each student data and add to database
        for student_data in student_data_list:
            # Extract data for each student
            course_id = student_data.get('course_id')
            semester = student_data.get('semester')
            year = student_data.get('year')
            roll_no = student_data.get('roll_no')
            total_marks = student_data.get('total_marks')
            grade = student_data.get('grade')
            batch = student_data.get('batch')

            # Validate data for each student
            if not all([course_id, semester, year, roll_no, total_marks, grade, batch]):
                continue  # Skip this student if data is incomplete

            try:
                # Get the Course instance
                course_instance = Course.objects.get(pk=course_id)

                # Create new Student_grades instance
                Student_grades.objects.create(
                    course_id=course_instance,
                    semester=semester,
                    year=year,
                    roll_no=roll_no,
                    total_marks=total_marks,
                    grade=grade,
                    batch=batch
                )

                success_count += 1  # Increment success count
            except Course.DoesNotExist:
                continue  # Skip this student if course does not exist

        # Return response with success count
        return Response({'success': f'{success_count} student(s) added successfully'}, status=201)





@api_view(['GET', 'POST'])
def update_hidden_grade(request):
    """
    This function is used to retrieve or update hidden grades for a course.

    @variables:
        course_id - ID of the course for which hidden grades are being retrieved or updated
        students - Queryset containing students registered for the course
        students_serialized - Serialized data of students registered for the course
        resp - Dictionary containing the response data
        data_list - List of data for multiple students provided in the request body
        student_id - ID of the student for which hidden grade is being updated
        grade - Grade for the hidden grade being updated
        hidden_grade_obj - Hidden grade object corresponding to the course and student
    """
    if request.method == 'GET':
        # Retrieve the course_id from the request query parameters
        course_id = request.query_params.get('course_id')

        if course_id is None:
            return JsonResponse({'error': 'Course ID is required in the request parameters'}, status=status.HTTP_400_BAD_REQUEST)

        # Filter students by the provided course ID
        students = course_registration.objects.filter(course_id=course_id)

        # Serialize the queryset
        students_serialized = serializers.CourseRegistrationSerializer(students, many=True).data

        # Prepare the response data
        resp = {
            'students': students_serialized
        }

        # Return the response
        return JsonResponse(data=resp, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        # Extract course_id from query parameters
        course_id = request.query_params.get('course_id')

        # Extract data for multiple students
        data_list = request.data

        # Check if course_id is provided
        if not course_id:
            return JsonResponse({'error': 'Course ID is required in the request parameters'}, status=status.HTTP_400_BAD_REQUEST)

        # Process each student in the list
        for data in data_list:
            student_id = data.get('student_id')
            grade = data.get('grade')

            # Check if student_id and grade are provided
            if not all([student_id, grade]):
                return JsonResponse({'error': 'Incomplete data provided for one of the students'}, status=status.HTTP_400_BAD_REQUEST)

            # Check if the entry already exists
            try:
                hidden_grade_obj = hidden_grades.objects.get(course_id=course_id, student_id=student_id)
                # If exists, update the grade
                hidden_grade_obj.grade = grade
                hidden_grade_obj.save()
            except hidden_grades.DoesNotExist:
                # If doesn't exist, create a new entry
                hidden_grade_obj = hidden_grades.objects.create(
                    course_id=course_id,
                    student_id=student_id,
                    grade=grade
                )

        return JsonResponse({'message': 'Hidden grades updated successfully'}, status=status.HTTP_201_CREATED)

    else:
        return JsonResponse({'error': 'Unsupported method'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)





@api_view(['GET'])
def check_all_authenticators(request):
    """
    This function is used to check if all authenticators are verified for a specific course and year.

    @variables:
        course_id - ID of the course for which all authenticators are being checked
        year - Year for which all authenticators are being checked
        auth_objects - Queryset containing authentication objects filtered by year
    """
    if request.method == 'GET':
        # Extract year and course ID from the request
        course_id = int(request.query_params.get('course_id'))
        year = request.query_params.get('year')
        
        # Validate year format
        try:
            datetime.strptime(year, '%Y')
        except ValueError:
            return Response({'error': 'Invalid year format. Please use YYYY format.'}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve all authentication objects for the given year and course ID
        auth_objects = authentication.objects.filter(year__year=year ,course_id = course_id)
        
        if not auth_objects.exists():
            return Response({'error': 'No authentication entries found for the provided year.'}, status=status.HTTP_404_NOT_FOUND)

        # Check if all three authenticators are verified for all authentication objects
        for auth_object in auth_objects:
            if not (auth_object.authenticator_1 and auth_object.authenticator_2 and auth_object.authenticator_3):
                return Response({'all_authenticated': False}, status=status.HTTP_200_OK)
        
        return Response({'all_authenticated': True}, status=status.HTTP_200_OK)






@api_view(['PATCH'])
def update_authenticator(request):
    """
    This function is used to update the status of an authenticator for a specific course and year.

    @variables:
        course_id - ID of the course for which authenticator status is being updated
        year - Year for which authenticator status is being updated
        authenticator_number - Number representing the authenticator whose status is being updated
        auth_objects - Queryset containing authentication objects filtered by year and course_id
        auth_object - Authentication object for the given year and course_id
    """
    if request.method == 'PATCH':
        # Extract course id, year, and authenticator number from the request
        course_id = int(request.data.get('course_id'))
        year = request.data.get('year')[:4]
        authenticator_number = int(request.data.get('authenticator_number'))
        
        # Validate year format
        print(course_id,year,authenticator_number)
        try:
            datetime.strptime(year, '%Y')
        except ValueError:
            return Response({'error': 'Invalid year format. Please use YYYY format.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Retrieve all authentication objects for the given year and course id
        auth_objects = authentication.objects.filter(year__year=year ,course_id=course_id)
        print(authentication.objects.all()[0])
        if not auth_objects.exists():
            return Response({'error': 'No authentication entries found for the provided year and course id.'}, status=status.HTTP_404_NOT_FOUND)

        # Toggle the specified authenticator for each authentication object
        for auth_object in auth_objects:
            if authenticator_number == 1:
                auth_object.authenticator_1 = not auth_object.authenticator_1
            elif authenticator_number == 2:
                auth_object.authenticator_2 = not auth_object.authenticator_2
            elif authenticator_number == 3:
                auth_object.authenticator_3 = not auth_object.authenticator_3
            else:
                return Response({'error': 'Invalid authenticator number'}, status=status.HTTP_400_BAD_REQUEST)
            
            auth_object.save()

        return Response({'message': f'Authenticator {authenticator_number} toggled successfully for the year {year} and course id {course_id}'}, status=status.HTTP_200_OK)





@api_view(['GET','POST'])
def get_auth_status(request):
    """
    This function is used to get the authentication status for a specific course and year.

    @variables:
        course_id - ID of the course for which authentication status is being retrieved
        year - Year for which authentication status is being retrieved
        auth_objects - Queryset containing authentication objects filtered by year and course_id
        auth_object - Authentication object for the given year and course_id
        auth_status - Dictionary containing the authentication status for authenticators 1, 2, and 3
    """
    try:
        course_id = int(request.data.get('course_id'))
        year = request.data.get('year')[:4]
        print(course_id, year)

        # Use filter instead of get to handle multiple objects
        auth_objects = authentication.objects.filter(year__year=year, course_id=course_id)
        
        if auth_objects.exists():
            auth_object = auth_objects.first()  # Use first() to get the first object
            auth_status = {
                'authenticator1': auth_object.authenticator_1,
                'authenticator2': auth_object.authenticator_2,
                'authenticator3': auth_object.authenticator_3
            }
            print(auth_status)
            return JsonResponse(auth_status, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'No authentication entries found for the provided year and course id.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






@api_view(['GET'])
def publish_grade(request):
    """
    This function is used to publish grades for a course.

    @variables:
        course_id - ID of the course for which grades are being published
        auth_obj - Authentication object corresponding to the course_id
        hidden_grades_list - List of hidden grades for the given course
        hidden_grade - Hidden grade object in the hidden_grades_list
        existing_final_grade - Existing final grade object for the student and course
    """
    course_id = request.GET.get('course_id')
    auth_obj = authentication.objects.filter(course=course_id).first()

    if auth_obj:
        if auth_obj.authenticator_1 and auth_obj.authenticator_2 and auth_obj.authenticator_3:
            # Get hidden grades for the given course
            hidden_grades_list = hidden_grades.objects.filter(course_id=course_id)

            # Update final grades table
            for hidden_grade in hidden_grades_list:
                # Check if final grade already exists
                existing_final_grade = grade.objects.filter(
                    student_id=hidden_grade.student_id,
                    course_id=hidden_grade.course_id,
                    semester_id=hidden_grade.semester_id
                ).first()

                if not existing_final_grade:
                    # Create final grade only if it doesn't already exist
                    grade.objects.create(
                        student_id=hidden_grade.student_id,
                        course_id=hidden_grade.course_id,
                        semester_id=hidden_grade.semester_id,
                        grade=hidden_grade.grade
                    )

            return JsonResponse({'message': 'Grades are ready to publish'}, status=200)
        else:
            return JsonResponse({'error': 'Not all authenticators are True'}, status=400)
    else:
        return JsonResponse({'error': 'Authentication object not present'}, status=404)





@api_view(['POST', 'GET'])
def generate_transcript_form(request):
    """
    This function is used to generate a transcript form for students.

    @variables:
        programme - Programme selected for filtering students
        batch - Batch selected for filtering students
        specialization - Specialization selected for filtering students
        students - Queryset containing filtered students based on programme, batch, and specialization
        serialized_students - Serialized JSON string representing the filtered students
        students_data - Python object obtained by deserializing the JSON string
        programmes - List of distinct programme values from Student objects
        specializations - List of distinct specialization values from Student objects
        batches - List of distinct batch values from Student objects
        context - Dictionary containing programmes, batches, and specializations for rendering the form
    """
    if request.method == 'POST':
        programme = request.data.get('programme')
        batch = request.data.get('batch')
        specialization = request.data.get('specialization')
        print(programme, batch, specialization)

        if specialization is None:
            students = Student.objects.filter(programme=programme, batch=batch)
        else:
            students = Student.objects.filter(programme=programme, batch=batch, specialization=specialization)

        # Serialize QuerySet to JSON string
        serialized_students = serialize('json', students)
        print(serialized_students)
        # Deserialize JSON string to Python object
        students_data = json.loads(serialized_students)

        # Pass the deserialized data to JsonResponse
        return JsonResponse({'students': students_data})
    else:
        programmes = Student.objects.values_list('programme', flat=True).distinct()
        specializations = Student.objects.exclude(specialization__isnull=True).values_list('specialization', flat=True).distinct()
        batches = Student.objects.values_list('batch', flat=True).distinct()
        context = {
            'programmes': list(programmes),  
            'batches': list(batches),  
            'specializations': list(specializations),  
        }

        return JsonResponse(context)







# @api_view(['POST', 'GET'])
# def generate_transcript(request):
#     """
#     This function is used to generate a transcript for a student.

#     @variables:
#         student_id - ID of the student for whom the transcript is being generated
#         semester - Semester for which the transcript is being generated
#         student_grades - Queryset containing grades for the student in the specified semester
#         transcript_data - List to hold transcript data for each course
#         grade - Grade object for each course in the specified semester
#         course_info - Dictionary containing course information to be included in the transcript
#         student_info - Information about the student, such as CPI (Cumulative Performance Index)
#         cpi - Cumulative Performance Index of the student
#         course_detail - Details of the course obtained from Curriculum
#     """
#     if request.method == 'POST':
#         student_id = request.data.get('student_id')
#         semester = request.data.get('semester')
        
#         # Fetch the courses and grades for the student in the specified semester
#         student_grades = Student_grades.objects.filter(roll_no=student_id, semester=semester)
#         print(student_id,semester)

#         total_course_registered = Student_grades.objects.filter(
#         roll_no=student_id, semester__lte=semester)
        
#         # Prepare data to be returned
#         transcript_data = []
#         for grade in student_grades:
#             # Access fields of each object
#             course_info = {
#                 'course_id': grade.course_id.name,
#                 'total_marks': grade.total_marks,
#                 'grade': grade.grade,
#                 'batch': grade.batch,
#             }
            
#             student_info = Student.objects.filter(id=student_id).first()

#             ##### Student  Grades fetch all courses before semester find spi and update cpi in student table
#             print(student_info.cpi)
#             if student_info:
#                 cpi = student_info.cpi
#                 course_info['cpi'] = cpi
#             else:
#                 # Handle case where student info is not found
#                 print("cpi is not there")
#                 pass
#             # Fetch course details from Curriculum
#             course_detail = Course.objects.filter(id=grade.course_id.id).first()
#             if course_detail:
#                 # Include additional attributes
#                 course_info['course_code'] = course_detail.code
#                 course_info['credits'] = course_detail.credit
#             else:
#                 # If course details not found, assign default values
#                 course_info['course_code'] = "Unknown"
#                 course_info['credits'] = 0
            
#             transcript_data.append(course_info)
        
#         return JsonResponse({'transcript': transcript_data})
#     else:
#         return JsonResponse({'error': 'Invalid request method'})




@api_view(['POST', 'GET'])
def generate_transcript(request):
    """
    This function is used to generate a transcript for a student.

    @variables:
        student_id - ID of the student for whom the transcript is being generated
        semester - Semester for which the transcript is being generated
        student_grades - Queryset containing grades for the student in the specified semester
        transcript_data - List to hold transcript data for each course
        grade - Grade object for each course in the specified semester
        course_info - Dictionary containing course information to be included in the transcript
        student_info - Information about the student, such as CPI (Cumulative Performance Index)
        cpi - Cumulative Performance Index of the student
        course_detail - Details of the course obtained from Curriculum
    """
    if request.method == 'POST':
        student_id = request.data.get('student_id')
        semester = request.data.get('semester')
        
        # Fetch the courses and grades for the student in the specified semester
        student_grades = Student_grades.objects.filter(roll_no=student_id, semester=semester)
        print(student_id, semester)

        # Fetch all courses registered by the student up to the specified semester
        total_courses_registered = Student_grades.objects.filter(
            roll_no=student_id, semester__lte=semester
        ).values_list('course_id', flat=True).distinct().count()

        # Prepare data to be returned
        transcript_data = []
        for grade in student_grades:
            # Access fields of each object
            course_info = {
                'course_id': grade.course_id.name,
                'total_marks': grade.total_marks,
                'grade': grade.grade,
                'batch': grade.batch,
            }
            
            student_info = Student.objects.filter(id=student_id).first()

            ##### Student  Grades fetch all courses before semester find spi and update cpi in student table
            print(student_info.cpi)
            if student_info:
                cpi = student_info.cpi
                course_info['cpi'] = cpi
            else:
                # Handle case where student info is not found
                print("cpi is not there")
                pass
            # Fetch course details from Curriculum
            course_detail = Course.objects.filter(id=grade.course_id.id).first()
            if course_detail:
                # Include additional attributes
                course_info['course_code'] = course_detail.code
                course_info['credits'] = course_detail.credit
            else:
                # If course details not found, assign default values
                course_info['course_code'] = "Unknown"
                course_info['credits'] = 0
            
            transcript_data.append(course_info)
        
        return JsonResponse({'transcript': transcript_data, 'total_courses_registered': total_courses_registered})
    else:
        return JsonResponse({'error': 'Invalid request method'})








# @api_view(['POST', 'GET'])
# def get_curriculum_values(request):
#     """
#     This function is used to retrieve curriculum values for a given course.

#     @variables:
#         course_id - ID of the course for which curriculum values are being retrieved
#         curriculum_values - Curriculum object corresponding to the course_id
#     """
#     try:
#         course_id = request.data.get('course_id')
        
#         curriculum_values = Course.objects.get(id=course_id)
#         print(Curriculum.objects.all())
#         return JsonResponse({
#             'course_code': curriculum_values.course_code,
#             'credits': curriculum_values.credits,
#             'course_type': curriculum_values.course_type,
#             'programme': curriculum_values.programme,
#             'branch': curriculum_values.branch,
#             'sem': curriculum_values.sem,
#             'optional': curriculum_values.optional,
#             'floated': curriculum_values.floated
#         })
#     except Curriculum.DoesNotExist:
#         print(Curriculum.objects.all())
#         return JsonResponse({
#             'course_code': 'Unknown',
#             'credits': 0,
#             'course_type': 'Unknown',
#             'programme': 'Unknown',
#             'branch': 'Unknown',
#             'sem': 0,
#             'optional': False,
#             'floated': False
#         })




@api_view(['POST', 'GET'])
def get_curriculum_values(request):
    """
    This function is used to retrieve curriculum values for a given course.
    
    @variables:
        course_id - ID of the course for which curriculum values are being retrieved
        curriculum_values - Course object corresponding to the course_id
    """
    try:
        course_id = request.data.get('course_id')
        
        course_values = Course.objects.get(id=course_id)
        
        return JsonResponse({
            'code': course_values.code,
            'name': course_values.name,
            'credit': course_values.credit,
            'lecture_hours': course_values.lecture_hours,
            'tutorial_hours': course_values.tutorial_hours,
            'pratical_hours': course_values.pratical_hours,
            'discussion_hours': course_values.discussion_hours,
            'project_hours': course_values.project_hours,
            'pre_requisits': course_values.pre_requisits,
            # Add other fields as needed
        })
    except Course.DoesNotExist:
        return JsonResponse({
            'error': 'Course not found for the given ID',
        })




@api_view(['POST', 'GET'])
def get_grade_for_course(course_id, batch, year, semester_id, selected_student_id):
    """
    This function is used to retrieve the grade for a specific course, batch, year, semester, and student.

    @parameters:
        course_id - ID of the course for which grade is being retrieved
        batch - Batch for which grade is being retrieved
        year - Year for which grade is being retrieved
        semester_id - ID of the semester for which grade is being retrieved
        selected_student_id - ID of the student for whom grade is being retrieved
    
    @variables:
        grades - Queryset containing grades filtered by course_id, batch, year, semester_id, and selected_student_id
    """
    # Filter Student_grades based on course_id, batch, year, semester_id, and selected_student_id
    grades = Student_grades.objects.filter(
        course_id=course_id,
        batch=batch,
        roll_no=selected_student_id,
        year=year,
        semester=semester_id,
    )

    # Assuming only one grade is expected for a given combination of parameters
    if grades.exists():
        return grades.first().grade
    else:
        return None  # Return None if no grade is found





@api_view(['POST', 'GET'])
def get_course_names(request):
    """
    This function is used to retrieve course names and IDs.

    @variables:
        courses - Queryset containing all Course objects
        course_data - List of dictionaries containing course IDs and names
    """
    if request.method == 'GET':
        # Retrieve all course names and IDs
        courses = Course.objects.all()
        course_data = [{'id': course.id, 'name': course.name} for course in courses]
        
        if not course_data:
            return JsonResponse({'error': 'No courses found.'}, status=status.HTTP_404_NOT_FOUND)
        
        return JsonResponse({'courses': course_data}, status=status.HTTP_200_OK)





@api_view(['POST'])
def add_courses(request):
    """
    This function is used to add courses along with authentication objects.

    @variables:
        courses - List of courses received from the request body
        created_authentications - List to hold the created authentication objects
        course_instance - Instance of the Course model corresponding to the course ID
        authentication_object - Authentication object created for the course
        serialized_data - Serialized data of the created authentication objects
    """
    if request.method == 'POST':
        # Get the list of courses from the request body
        courses = request.data.get('courses', [])

        # Create a list to hold the created authentication objects
        created_authentications = []

        # Iterate over the list of courses and create an authentication object for each
        for course in courses:
            try:
                # Get the Course instance corresponding to the course ID
                course_instance = Course.objects.get(id=course['id']) 
                
                # Create a new authentication object with the Course instance
                authentication_object = authentication.objects.create(course_id=course_instance)
                
                # Append the created authentication object to the list
                created_authentications.append(authentication_object)
            except Exception as e:
                # Handle any errors that occur during object creation
                # You can choose to log the error or handle it based on your requirements
                print(f"Error creating authentication object for course ID {course['id']}: {e}")
        
        # Convert the created authentication objects to dictionaries
        serialized_data = [{'id': obj.id, 'authenticator_1': obj.authenticator_1, 'authenticator_2': obj.authenticator_2, 'authenticator_3': obj.authenticator_3, 'year': obj.year.year, 'course_id': obj.course_id_id} for obj in created_authentications]
        
        # Return a JSON response with the serialized data
        return JsonResponse(serialized_data, status=201, safe=False)





@api_view(['PATCH'])
def update_grades(request):
    """
    This function is used to update grades for students.

    @variables:
        updated_students_data - JSON data containing updated grades for students
        roll_no - Roll number of the student
        course_id - ID of the course for which grades are being updated
        semester_id - ID of the semester for which grades are being updated
        year - Year for which grades are being updated
        grade - Updated grade received by the student
        total_marks - Updated total marks obtained by the student
        student_grade_obj - Student grades object to be updated or created
        created - Flag indicating whether a new student grade object was created
    """
    if request.method == 'PATCH':
        try:
            # Extract the updated student data from the request body
            updated_students_data = json.loads(request.body)
            print(updated_students_data)
            # Iterate over each updated student data
            for student_data in updated_students_data:
                roll_no = student_data.get('roll_no')
                course_id = int(student_data.get('course_id'))
                semester_id = student_data.get('semester_id')
                year = int(student_data.get('year'))
                grade = student_data.get('grade')
                total_marks = student_data.get('total_marks')

                # Check if all necessary data is provided
                if not (roll_no and course_id and semester_id and year and grade and total_marks):
                    return JsonResponse({'error': 'Incomplete data provided'}, status=400)

                # Update the student grade
                student_grade_obj, created = Student_grades.objects.update_or_create(
                    roll_no=roll_no,
                    course_id=course_id,
                    semester=semester_id,
                    year=year,
                    defaults={'grade': grade, 'total_marks': total_marks}
                )

            return JsonResponse({'message': 'Student grades updated successfully'}, status=200)
        
        except json.JSONDecodeError as e:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        
        except KeyError as e:
            return JsonResponse({'error': 'Missing required field: ' + str(e)}, status=400)
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)





@api_view(['PATCH'])
def submit_grades(request):
    """
    This function is used to submit grades for students.

    @variables:
        updated_students_data - JSON data containing updated grades for students
        roll_no - Roll number of the student
        course_id - ID of the course for which grades are being submitted
        semester_id - ID of the semester for which grades are being submitted
        year - Year for which grades are being submitted
        grade - Grade received by the student (defaulted to 'NA')
        total_marks - Total marks obtained by the student (defaulted to 0)
        course - Course object corresponding to course_id
        student_grade_obj - Student grades object to be updated or created
        created - Flag indicating whether a new student grade object was created
    """
    if request.method == 'PATCH':
        try:
            updated_students_data = json.loads(request.body)
            print(updated_students_data)

            for student_data in updated_students_data:
                roll_no = student_data.get('roll_no')
                course_id = int(student_data.get('course_id'))
                semester_id = student_data.get('semester_id')
                year = int(student_data.get('year'))
                grade = student_data.get('grade','NA')
                total_marks = student_data.get('total_marks','0')

                if not (roll_no and course_id and semester_id and year and grade and total_marks):
                    return JsonResponse({'error': 'Incomplete data provided'}, status=400)

                # Retrieve the Course object based on course_id
                course = Course.objects.get(id=course_id)

                # Update or create the student grade object
                student_grade_obj, created = Student_grades.objects.update_or_create(
                    roll_no=roll_no,
                    course_id=course,  # Use the Course object instead of course_id
                    semester=semester_id,
                    year=year,
                    defaults={'grade': grade, 'total_marks': total_marks}
                )

            return JsonResponse({'message': 'Student grades updated successfully'}, status=200)
        
        except json.JSONDecodeError as e:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        
        except KeyError as e:
            return JsonResponse({'error': 'Missing required field: ' + str(e)}, status=400)
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)




@api_view(['POST', 'GET'])
def get_registered_students_roll_no(request):
    """
    This function is used to retrieve registered students' information for a particular course and year.

    @variables:
        course_id - ID of the course for which registrations are being retrieved
        year - Year for which registrations are being retrieved
        registrations - Queryset containing course registrations filtered by course_id and year
        data - List to store serialized student data
        student_data - Dictionary to store individual student information
        student_grade - Grade and total marks of the student for the specified course
    """
    # Retrieve the course_id and year from the request query parameters
    course_id = request.data.get('course_id')
    year = request.data.get('year')
    
    if not course_id or not year:
        return JsonResponse({'error': 'Course ID and year are required'}, status=400)

    try:
        # Filter course registrations by course_id and year
        registrations = course_registration.objects.filter(course_id=course_id, working_year=year)
        # registrations = Register.objects.filter(curr_id=course_id)
        print(registrations)
        # Serialize the queryset
        data = []
        for registration in registrations:
            # Access fields of the related Student instance
            print(registration)
            student_data = {
                'roll_no': registration.student_id.id.user.username,
                'name': registration.student_id.id.user.first_name,  # Assuming first_name is a field of the User model
                'email': registration.student_id.id.user.email,  # Assuming email is a field of the User model
                # Include other relevant fields from the Student model
                'grade': None,
                'marks': None
            }
            
            # Retrieve grades and total marks for the student
            try:
                print(registration.student_id.id , course_id)
                student_grade = Student_grades.objects.get(roll_no=student_data['roll_no'],course_id=course_id)
                student_data['grade'] = student_grade.grade
                student_data['marks'] = student_grade.total_marks
                
                # print(student_grade)
            except Student_grades.DoesNotExist:
                print("Didn't find grades for roll_no:", registration.student_id.id, "and course_id:", course_id)
                pass
            # print(student_data)
            data.append(student_data)
        # Return the serialized data in the response
        return JsonResponse({'registrations': data}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)





@api_view(['POST', 'GET'])
def get_to_request(username):
    """
    This function is used to get requests for the receiver

    @variables:
        req - Contains request queryset

    """
    req = SpecialRequest.objects.filter(request_receiver=username)
    return req




@api_view(['POST', 'GET'])
def browse_announcements():
    """
    This function is used to browse Announcements Department-Wise
    made by different faculties and admin.

    @variables:
        cse_ann - Stores CSE Department Announcements
        ece_ann - Stores ECE Department Announcements
        me_ann - Stores ME Department Announcements
        sm_ann - Stores SM Department Announcements
        all_ann - Stores Announcements intended for all Departments
        context - Dictionary for storing all above data

    """
    cse_ann = Announcements.objects.filter(department="CSE")
    ece_ann = Announcements.objects.filter(department="ECE")
    me_ann = Announcements.objects.filter(department="ME")
    sm_ann = Announcements.objects.filter(department="SM")
    all_ann = Announcements.objects.filter(department="ALL")

    context = {
        "cse" : cse_ann,
        "ece" : ece_ann,
        "me" : me_ann,
        "sm" : sm_ann,
        "all" : all_ann
    }

    return context




@api_view(['POST', 'GET'])
def announce(request):
    """
    This function is used to make announcements by faculty or admin.

    @variables:
        usrnm - Current user's username
        user_info - Extra information of the current user
        ann_maker_id - ID of the user making the announcement
        batch - Batch for which the announcement is intended
        programme - Programme for which the announcement is intended
        message - Content of the announcement
        upload_announcement - File uploaded with the announcement
        department - Department for which the announcement is intended
        ann_date - Date of the announcement
        getstudents - All users with extra information
        
    """
    usrnm = get_object_or_404(User, username=request.user.username)
    user_info = ExtraInfo.objects.all().select_related('user', 'department').filter(user=usrnm).first()
    ann_maker_id = user_info.id
    
    if request.method == 'POST':
        batch = request.data.get('batch', '')
        programme = request.data.get('programme', '')
        message = request.data.get('announcement', '')
        upload_announcement = request.FILES.get('upload_announcement')
        department = request.data.get('department', 'ALL')
        ann_date = datetime.today()
        user_info = ExtraInfo.objects.all().select_related('user', 'department').get(id=ann_maker_id)
        getstudents = ExtraInfo.objects.select_related('user')
        
        obj1, created = Announcements.objects.get_or_create(maker_id=user_info,
                                                            batch=batch,
                                                            programme=programme,
                                                            message=message,
                                                            upload_announcement=upload_announcement,
                                                            department=department,
                                                            ann_date=ann_date)

        response_data = {
            'status': 'success',
            'message': 'Announcement successfully created'
        }
        return JsonResponse(response_data)
    else:
        response_data = {
            'error': 'Invalid request method'
        }
        return JsonResponse(response_data, status=405)
