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

from applications.academic_procedures.models import(course_registration)
from applications.academic_information.models import Course
from applications.examination.models import(hidden_grades , authentication , grade)
from applications.department.models import(Announcements)
from applications.academic_information.models import(Student)
from applications.online_cms.models import(Student_grades)
from . import serializers
from datetime import date 
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response


#Login 
# @login_required(login_url='/accounts/login')
# def exam(request):
#     """
#     This function is used to Differenciate acadadmin and all other user.

#     @param:
#         request - contains metadata about the requested page

#     @variables:
#         user_details - Gets the information about the logged in user.
#         des - Gets the designation about the looged in user.
#     """
#     user_details = ExtraInfo.objects.get(user = request.user)
#     des = HoldsDesignation.objects.all().filter(user = request.user).first()
#     if str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
#         return HttpResponseRedirect('/examination/submit/')
#     elif str(request.user) == "acadadmin" :
#         return HttpResponseRedirect('/examination/submit/')
    
#     return HttpResponseRedirect('/dashboard/')

# @login_required(login_url='/accounts/login')




#Get all students
# @api_view(['GET'])
# def fetch_student_details(request):
#     if request.method == 'GET':
#         # obj=course_registration.objects.filter(course_id__id=course_id, student_id__batch=batch)
#         obj=course_registration.objects.all()
#         obj_serialized = serializers.CourseRegistrationSerializer(obj , many=True).data
#         resp = {
#             'objt' : obj_serialized
#         }

#         return Response(data=resp , status=status.HTTP_200_OK)
















# @api_view(['GET', 'POST'])
# def fetch_roll_of_courses(request):
#     if request.method == 'GET':
#         # Retrieve the course_id from the request query parameters
#         course_id = request.query_params.get('course_id')
#         batch = request.query_params.get('batch')

#         if course_id is None:
#             return Response({'error': 'Course ID is required in the request parameters'}, status=status.HTTP_400_BAD_REQUEST)

#         # Filter students by the provided course ID
#         obj = course_registration.objects.filter(course_id=course_id)

#         # Serialize the queryset
#         obj_serialized = serializers.CourseRegistrationSerializer(obj, many=True).data

#         # Prepare the response data
#         resp = {
#             'objt': obj_serialized
#         }

#         # Return the response
#         return Response(data=resp, status=status.HTTP_200_OK)
    
#     elif request.method == 'POST':
#     # Extract data from the request
#         data_list = request.data  # Assuming data is a list of objects

#         for data in data_list:
#             student_id = data.get('student_id')
#             course_id = data.get('course_id')
#             semester_id = data.get('semester_id')
#             grade = data.get('grade')

#             if student_id is None or course_id is None or semester_id is None or grade is None:
#                 return Response({'error': 'Incomplete data provided'}, status=status.HTTP_400_BAD_REQUEST)

#             # Check if the entry already exists
#             try:
#                 hidden_grade_obj = hidden_grades.objects.get(student_id=student_id, course_id=course_id)
#                 # If exists, update the grade
#                 hidden_grade_obj.grade = grade
#                 hidden_grade_obj.save()
#             except hidden_grades.DoesNotExist:
#                 # If doesn't exist, create a new entry
#                 hidden_grade_obj = hidden_grades.objects.create(
#                     student_id=student_id,
#                     course_id=course_id,
#                     semester_id=semester_id,
#                     grade=grade
#                 )

#     return Response({'message': 'Hidden grades added successfully'}, status=status.HTTP_201_CREATED)














@api_view(['GET', 'POST'])
def fetch_roll_of_courses(request):
    if request.method == 'POST':
        # Retrieve the course_id from the request query parameters
        course_id = request.data.get('course_id')
        working_year = request.data.get('working_year')

        if course_id is None:
            return Response({'error': 'Course ID is required in the request parameters'}, status=status.HTTP_400_BAD_REQUEST)

        # Filter students by the provided course ID
        print(course_id,working_year)
        obj = course_registration.objects.filter(course_id=course_id , working_year=working_year)
        print(course_registration.objects.all()[0].course_id)
        # Serialize the queryset
        obj_serialized = serializers.CourseRegistrationSerializer(obj, many=True).data

        # Prepare the response data
        resp = {
            'objt': obj_serialized
        }

        # Return the response
        return Response(data=resp, status=status.HTTP_200_OK)

    return Response({'message': 'Students'}, status=status.HTTP_201_CREATED)






@api_view(['GET', 'POST'])
def fetch_student_details(request):
    if request.method == 'GET':
        # Retrieve query parameters
        course_id = int(request.query_params.get('course'))
        semester_id = request.query_params.get('semester')
        batch = request.query_params.get('batch')
        print(course_id,semester_id,batch)
        if course_id is None or semester_id is None or batch is None:
            return JsonResponse({'error': 'Incomplete parameters provided'}, status=400)

        # Filter student grades based on provided parameters
        course_present = Student_grades.objects.filter(course_id=course_id, semester=semester_id, batch=batch)

        # Prepare data to return in JSON format
        data = {
            'registrations': list(course_present.values())  # Convert queryset to list of dictionaries
        }

        # Return JSON response
        return JsonResponse(data)





@api_view(['GET', 'POST'])
def update_hidden_grade(request):
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












# @api_view(['PATCH'])
# def update_hidden_grade(request):
#     course_id = request.query_params.get('course_id')
    
#     student_id = request.query_params.get('student_id')

#     if request.method == 'PATCH':
#         # Check if the grade data is provided in the request
#         if 'grade' in request.data:
#             grade = request.data['grade']
#             # Get the hidden grade object for the given course_id and student_id
#             try:
#                 hidden_grade = hidden_grades.objects.get(course_id=course_id, student_id=student_id)
#                 hidden_grade.grade = grade
#                 hidden_grade.save()
#                 return JsonResponse({'message': 'Grade updated successfully'}, status=200)
#             except hidden_grades.DoesNotExist:
#                 return JsonResponse({'error': 'No hidden grade found for the provided course_id and student_id'}, status=404)
#         else:
#             return JsonResponse({'error': 'Incomplete data provided'}, status=400)
#     else:
#         return JsonResponse({'error': 'Unsupported method'}, status=405)
    

@api_view(['GET'])
def check_all_authenticators(request):
    if request.method == 'GET':
        # Extract year from the request
        course_id = int(request.query_params.get('course_id'))
        year = request.query_params.get('year')
        
        # Validate year format
        try:
            datetime.strptime(year, '%Y')
        except ValueError:
            return Response({'error': 'Invalid year format. Please use YYYY format.'}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve all authentication objects for the given year
        auth_objects = authentication.objects.filter(year__year=year ,course_id = course_id)
        
        if not auth_objects.exists():
            return Response({'error': 'No authentication entries found for the provided year.'}, status=status.HTTP_404_NOT_FOUND)

        # Check if all three authenticators are verified for all authentication objects
        for auth_object in auth_objects:
            if not (auth_object.authenticator_1 and auth_object.authenticator_2 and auth_object.authenticator_3):
                return Response({'all_authenticated': False}, status=status.HTTP_200_OK)
        
        return Response({'all_authenticated': True}, status=status.HTTP_200_OK)




from datetime import datetime
@api_view(['PATCH'])
def update_authenticator(request):
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




@api_view(['GET'])
def publish_grade(request):
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




# def submit(request):
    
#     return render(request,'../templates/examination/submit.html' , {})

# @login_required(login_url='/accounts/login')
# def verify(request):
#     return render(request,'../templates/examination/verify.html' , {})

# @login_required(login_url='/accounts/login')      
# def publish(request):
#     return render(request,'../templates/examination/publish.html' ,{})


# @login_required(login_url='/accounts/login')
# def notReady_publish(request):
#     return render(request,'../templates/examination/notReady_publish.html',{})
    

# @api_view(['POST'])
# def publish_result(request):









# def add_student(request):
#     if request.method == 'POST':
#         # Assuming the POST request contains necessary data for a new student
#         student_id = request.POST.get('student_id')
#         course_id = request.POST.get('course_id')
#         semester_id = request.POST.get('semester_id')
#         grades = request.POST.get('grades')

#         # Create a new private_grade object
#         new_student = hidden_grades.objects.create(
#             student_id=student_id,
#             course_id=course_id,
#             semester_id=semester_id,
#             grades=grades
#         )

#         return JsonResponse({'message': 'Student added successfully'})
#     else:
#         return JsonResponse({'error': 'Invalid request method'}, status=400)
    






# def generate_transcript(request):

#     student_id = request.GET.get('student')

#     # Fetch the courses registered by the student
#     courses_registered = course_registration.objects.filter(
#         student_id=student_id)

#     # Initialize a dictionary to store course grades
#     course_grades = {}

#     # Fetch grades for the courses registered by the student
#     for course in courses_registered:
#         try:
#             # Attempt to fetch the grade for the course from hidden_grades
#             grade = hidden_grades.objects.get(
#                 student_id=student_id, course_id=course.course_id_id)
#             print(course.course_id.code)
#             course_grades[course] = grade.grade  # Store the grade
#         except hidden_grades.DoesNotExist:
#             # Grade not available
#             course_grades[course] = "Grading not done yet"

#     context = {
#         'courses_grades': course_grades
#     }

#     return render(request, 'examination/generate_transcript.html', context)

from django.core.serializers import serialize
from django.http import JsonResponse
import json

@api_view(['POST', 'GET'])
def generate_transcript_form(request):
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
#     student_id = request.data.get('student')

#     # Fetch the courses registered by the student
#     courses_registered = course_registration.objects.filter(student_id=student_id)
    
#     # Initialize a dictionary to store course grades
#     course_grades = {}

#     # Fetch grades for the courses registered by the student
#     # for course in courses_registered:
#     #     try:
#     #         # Attempt to fetch the grade for the course from hidden_grades
#     #         grade = HiddenGrades.objects.get(student_id=student_id, course_id=course.course_id_id)
#     #         course_grades[course.course_id.code] = grade.grade  # Store the grade
#     #     except HiddenGrades.DoesNotExist:
#     #         # Grade not available
#     #         course_grades[course.course_id.code] = "Grading not done yet"

#     return JsonResponse({'courses_grades': courses_registered})




@api_view(['POST', 'GET'])
def generate_transcript(request):
    if request.method == 'POST':
        student_id = request.data.get('student_id')
        semester = request.data.get('semester')
        
        print(student_id,semester)
        # Fetch the courses and grades for the student in the specified semester
        student_grades = Student_grades.objects.filter(roll_no=student_id, semester=semester)
        
        # Prepare data to be returned
        transcript_data = []
        for grade in student_grades:
            # Access fields of each object
            course_info = {
                'course_id': grade.course_id.course_name,
                'total_marks': grade.total_marks,
                'grade': grade.grade
            }
            transcript_data.append(course_info)
        print(transcript_data)
        return JsonResponse({'transcript': transcript_data})
    else:
        return JsonResponse({'error': 'Invalid request method'})


@api_view(['POST', 'GET'])
def get_grade_for_course(course_id, batch, year, semester_id, selected_student_id):
    # Filter Student_grades based on course_id, batch, programme, specialization, and selected_student_id

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
    if request.method == 'GET':
        # Retrieve all course names and IDs
        courses = Course.objects.all()
        course_data = [{'id': course.id, 'name': course.course_name} for course in courses]
        
        if not course_data:
            return JsonResponse({'error': 'No courses found.'}, status=status.HTTP_404_NOT_FOUND)
        
        return JsonResponse({'courses': course_data}, status=status.HTTP_200_OK)



@api_view(['POST'])
def add_courses(request):
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



@api_view(['POST', 'GET'])
def get_registered_students_roll_no(request):
    # Retrieve the course_id and year from the request query parameters
    course_id = request.data.get('course_id')
    year = request.data.get('year')
    print(course_id,year)
    if not course_id or not year:
        return JsonResponse({'error': 'Course ID and year are required'}, status=400)

    try:
        # Filter course registrations by course_id and year
        registrations = Student_grades.objects.filter(course_id=course_id, year=year)
        # Serialize the queryset
        data = [{'course_id': registration.course_id_id,
                 'semester': registration.semester,
                 'year': registration.year,
                 'roll_no': registration.roll_no,
                 'total_marks': registration.total_marks,
                 'grade': registration.grade,
                 'batch': registration.batch} for registration in registrations]
        # Return the serialized data in the response
        return JsonResponse({'registrations': data}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)




