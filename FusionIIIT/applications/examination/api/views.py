from datetime import datetime
from django.db.models.query_utils import Q
from django.http import request, HttpResponse
from django.shortcuts import get_object_or_404, render, HttpResponse, redirect
from django.http import HttpResponse, HttpResponseRedirect
import itertools
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse

# from applications.academic_information.models import Student
from applications.globals.models import (DepartmentInfo, Designation,
                                         ExtraInfo, Faculty, HoldsDesignation)

from applications.academic_procedures.models import (course_registration)
from applications.examination.models import (
    hidden_grades, authentication, grade)
from . import serializers

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response





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
        obj_serialized = serializers.CourseRegistrationSerializer(
            obj, many=True).data

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
            hidden_grade_obj = hidden_grades.objects.get(
                student_id=student_id, course_id=course_id)
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
    
@api_view(['POST'])
def enter_student_grades(request):
    if request.method == 'POST':
        # Extract data from the request
        data = request.data.get('grades', [])
        
        if not data:
            return Response({'error': 'No data provided'}, status=status.HTTP_400_BAD_REQUEST)

        for grade_data in data:
            student_id = grade_data.get('student_id')
            course_id = grade_data.get('course_id')
            semester_id = grade_data.get('semester_id')
            grade = grade_data.get('grade')

            if student_id is None or course_id is None or semester_id is None or grade is None:
                return Response({'error': 'Incomplete data provided'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                hidden_grade_obj = hidden_grades.objects.get(
                    student_id=student_id, 
                    course_id=course_id,
                    semester_id=semester_id
                )
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

        return Response({'message': 'Hidden grades added successfully'}, status=status.HTTP_201_CREATED)
    else:
        return Response({'error': 'Unsupported method'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
       

    
       


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
                hidden_grade = hidden_grades.objects.get(
                    course_id=course_id, student_id=student_id)
                hidden_grade.grade = grade
                hidden_grade.save()
                return JsonResponse({'message': 'Grade updated successfully'}, status=200)
            except hidden_grades.DoesNotExist:
                return JsonResponse({'error': 'No hidden grade found for the provided course_id and student_id'}, status=404)
        else:
            return JsonResponse({'error': 'Incomplete data provided'}, status=400)
    else:
        return JsonResponse({'error': 'Unsupported method'}, status=405)


@api_view(['PATCH'])
def update_hidden_grade_multiple(request):
    if request.method == 'PATCH':
        # Check if the data is provided in the request
        if 'grades' in request.data:
            grades_data = request.data['grades']
            for grade_data in grades_data:
                course_id = grade_data.get('course_id')
                student_id = grade_data.get('student_id')
                semester_id = grade_data.get('semester_id')
                grade = grade_data.get('grade')

                if course_id is None or student_id is None or semester_id is None or grade is None:
                    return Response({'error': 'Incomplete data provided for one of the grades'}, status=400)

                # Get the hidden grade object for the given course_id, student_id, and semester_id
                try:
                    hidden_grade = hidden_grades.objects.get(
                        course_id=course_id, student_id=student_id, semester_id=semester_id)
                    hidden_grade.grade = grade
                    hidden_grade.save()
                except hidden_grades.DoesNotExist:
                    # If the grade doesn't exist, create a new one
                    hidden_grade = hidden_grades.objects.create(
                        course_id=course_id, student_id=student_id, semester_id=semester_id, grade=grade)
                    hidden_grade.save()

            return Response({'message': 'Grades updated successfully'}, status=200)
        else:
            return Response({'error': 'No grade data provided'}, status=400)
    else:
        return Response({'error': 'Unsupported method'}, status=405)


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
            hidden_grades_list = hidden_grades.objects.filter(
                course_id=course_id)

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


