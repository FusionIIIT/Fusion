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
from applications.examination.models import(hidden_grades , authentication , grade)
from . import serializers

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





@api_view(['GET', 'POST'])
def fetch_student_details(request):
    if request.method == 'GET':
        # Retrieve the course_id from the request query parameters
        course_id = request.query_params.get('course_id')

        if course_id is None:
            return Response({'error': 'Course ID is required in the request parameters'}, status=status.HTTP_400_BAD_REQUEST)

        # Filter students by the provided course ID
        obj = course_registration.objects.filter(course_id=course_id)

        # Serialize the queryset
        obj_serialized = serializers.CourseRegistrationSerializer(obj, many=True).data

        # Prepare the response data
        resp = {
            'objt': obj_serialized
        }

        # Return the response
        return Response(data=resp, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        # Extract data from the request
        data = request.data
        student_id = data.get('student_id')
        course_id = data.get('course_id')
        semester_id = data.get('semester_id')
        grade = data.get('grade')

        if student_id is None or course_id is None or semester_id is None or grade is None:
            return Response({'error': 'Incomplete data provided'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the entry already exists
        try:
            hidden_grade_obj = hidden_grades.objects.get(student_id=student_id, course_id=course_id)
            # If exists, update the grade
            hidden_grade_obj.grade = grade
            hidden_grade_obj.save()
        except hidden_grades.DoesNotExist:
            # If doesn't exist, create a new entry
            hidden_grade_obj = hidden_grades.objects.create(
                student_id=student_id,
                course_id=course_id,
                semester_id=semester_id,
                grade=grade
            )

        return Response({'message': 'Hidden grade added successfully'}, status=status.HTTP_201_CREATED)



@api_view(['PATCH'])
def update_hidden_grade(request):
    course_id = request.query_params.get('course_id')
    student_id = request.query_params.get('student_id')

    if request.method == 'PATCH':
        # Check if the grade data is provided in the request
        if 'grade' in request.data:
            grade = request.data['grade']
            # Get the hidden grade object for the given course_id and student_id
            try:
                hidden_grade = hidden_grades.objects.get(course_id=course_id, student_id=student_id)
                hidden_grade.grade = grade
                hidden_grade.save()
                return JsonResponse({'message': 'Grade updated successfully'}, status=200)
            except hidden_grades.DoesNotExist:
                return JsonResponse({'error': 'No hidden grade found for the provided course_id and student_id'}, status=404)
        else:
            return JsonResponse({'error': 'Incomplete data provided'}, status=400)
    else:
        return JsonResponse({'error': 'Unsupported method'}, status=405)
    






from datetime import datetime
@api_view(['PATCH'])
def update_authenticator(request):
    if request.method == 'PATCH':
        # Extract year and authenticator number from the request
        year = request.data.get('year')
        authenticator_number = request.data.get('authenticator_number')
        
        # Validate year format
        try:
            datetime.strptime(year, '%Y')
        except ValueError:
            return Response({'error': 'Invalid year format. Please use YYYY format.'}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve all authentication objects for the given year
        auth_objects = authentication.objects.filter(year__year=year)
        
        if not auth_objects.exists():
            return Response({'error': 'No authentication entries found for the provided year.'}, status=status.HTTP_404_NOT_FOUND)

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

        return Response({'message': f'Authenticator {authenticator_number} toggled successfully for the year {year}'}, status=status.HTTP_200_OK)




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
    

