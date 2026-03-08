from __future__ import unicode_literals
from django.views.decorators.csrf import csrf_protect
from django.core import serializers
import collections
import json
import os
import random
import subprocess
import datetime
import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.utils import timezone
from django.core.serializers import serialize
from django.http import JsonResponse
from decimal import Decimal
from applications.academic_information.models import (Student,Student_attendance,Calendar, Timetable)
from applications.programme_curriculum.models import Course as Courses
from applications.programme_curriculum.models import CourseInstructor
from applications.academic_procedures.models import course_registration
from applications.globals.models import ExtraInfo
from django.contrib.auth.models import User
from notifications.signals import notify
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from django.db import connection
from rest_framework.permissions import IsAuthenticated
from applications.online_cms.models import Attendance
import pandas as pd
from datetime import datetime

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status  # Import for custom status codes
from .serializers import *

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_attendance(request):
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file uploaded'}, status=400)

    try:
        excel_file = request.FILES['file']
        df = pd.read_excel(excel_file, keep_default_na=False)

        # Normalize columns
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

        required_columns = ['student_id', 'instructor_id', 'date', 'present', 'no_of_attendance']
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            return JsonResponse({
                'error': 'Missing required columns',
                'missing': missing_cols,
                'found': df.columns.tolist()
            }, status=400)

        successes = 0
        errors = []

        for index, row in df.iterrows():
            try:
                # Get the actual values from the Excel columns
                student_id = str(row['student_id'])  # Changed from student_id_id
                instructor_id = str(row['instructor_id'])  # Changed from instructor_id_id

                if pd.isna(row['date']):
                    raise ValueError("Date cannot be empty")

                if isinstance(row['date'], str):
                    date_str = row['date'].split()[0]
                    try:
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                    except ValueError:
                        date_obj = datetime.strptime(date_str, '%d/%m/%Y').date()
                else:
                    date_obj = row['date'].date()

                present = int(row['present'])
                no_of_attendance = int(row['no_of_attendance'])

                with connection.cursor() as cursor:
                    # Check if record exists
                    cursor.execute(
                        "SELECT 1 FROM online_cms_attendance WHERE student_id_id = %s AND instructor_id_id = %s AND date = %s",
                        [student_id, instructor_id, date_obj]
                    )
                    exists = cursor.fetchone()

                    if exists:
                        # Update existing record
                        cursor.execute(
                            "UPDATE online_cms_attendance SET present = %s, no_of_attendance = %s "
                            "WHERE student_id_id = %s AND instructor_id_id = %s AND date = %s",
                            [present, no_of_attendance, student_id, instructor_id, date_obj]
                        )
                        action = 'updated'
                    else:
                        # Insert new record
                        cursor.execute(
                            "INSERT INTO online_cms_attendance (student_id_id, instructor_id_id, date, present, no_of_attendance) "
                            "VALUES (%s, %s, %s, %s, %s)",
                            [student_id, instructor_id, date_obj, present, no_of_attendance]
                        )
                        action = 'created'

                successes += 1
                print(f"Row {index + 2}: {action} successfully")

            except Exception as e:
                error_msg = f"Row {index + 2}: {str(e)}"
                errors.append(error_msg)
                print(f"Error in row {index + 2}:", e)

        return JsonResponse({
            'message': f'Processed {successes} rows successfully',
            'success_count': successes,
            'error_count': len(errors),
            'errors': errors if errors else None
        })

    except Exception as e:
        print("Upload failed:", str(e))
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_attendance(request):
    try:
        # Get query parameters for filtering
        student_id = request.GET.get('student_id')
        instructor_id = request.GET.get('instructor_id')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        
        # Start with all records
        queryset = Attendance.objects.all()
        
        # Apply filters if provided
        if student_id:
            queryset = queryset.filter(student_id_id=student_id)
        if instructor_id:
            queryset = queryset.filter(instructor_id_id=instructor_id)
        if date_from and date_to:
            queryset = queryset.filter(date__range=[date_from, date_to])
        elif date_from:
            queryset = queryset.filter(date__gte=date_from)
        elif date_to:
            queryset = queryset.filter(date__lte=date_to)
        
        # Prepare the response data
        data = []
        for attendance in queryset:
            data.append({
                'id': attendance.id,
                'student_id': attendance.student_id_id,  # Directly access the ID
                'instructor_id': attendance.instructor_id_id,  # Directly access the ID
                'date': attendance.date.strftime('%Y-%m-%d'),
                'present': attendance.present,
                'no_of_attendance': attendance.no_of_attendance
            })
        
        return JsonResponse({
            'success': True,
            'count': len(data),
            'data': data
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['GET'])
def get_modules(request):
    if request.method == "GET":
        modules = Modules.objects.all().values("id", "module_name")  # Use correct field name
        return JsonResponse(list(modules), safe=False)
    return JsonResponse({"error": "Method not allowed"}, status=405)
    
# add a module
@api_view(['POST'])
def add_module(request):
    # Extract data from the request
    course_id = request.data.get('course_id')
    module_name = request.data.get('module_name')


    # Ensure the course exists
    try:
        course = Courses.objects.get(id=course_id)
    except Courses.DoesNotExist:
        return Response({"error": "Course not found"}, status=status.HTTP_404_NOT_FOUND)

    # Create the module
    module = Modules.objects.create(module_name=module_name, course_id=course)

    # Serialize the module data and return
    serializer = ModulesSerializer(module)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


# delete a module
@api_view(['DELETE'])
def delete_module(request, module_id):
    try:
        # Get the module by primary key
        module = Modules.objects.get(pk=module_id)
        module.delete()  # Delete the module
        return Response(status=status.HTTP_204_NO_CONTENT)  # No content after deletion
    except Modules.DoesNotExist:
        return Response({"error": "Module not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_slides(request):
    documents = CourseDocuments.objects.all()  # Fetch all documents
    serializer = CourseDocumentsSerializer(documents, many=True)
    return Response(serializer.data)
    
# Add a slide
@api_view(['POST'])
def add_slide(request, module_id):
    try:
        # Get the module using module_id from the URL
        module = Modules.objects.get(id=module_id)
    except Modules.DoesNotExist:
        return Response({"error": "Module not found"}, status=status.HTTP_404_NOT_FOUND)

    # Extract data from the request body
    document_name = request.data.get('document_name')
    document_url = request.data.get('document_url')
    description = request.data.get('description', '')  # Default to empty string if not provided

    # Create a new CourseDocument for the slide
    course_document = CourseDocuments.objects.create(
        course_id=module.course_id,
        module_id=module,
        document_name=document_name,
        document_url=document_url,
        description=description
    )

    # Serialize the document data and return the response
    serializer = CourseDocumentsSerializer(course_document)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


# Delete a slide
@api_view(['DELETE'])
def delete_slide(request, slide_id):
    try:
        # Get the slide by primary key
        slide = CourseDocuments.objects.get(pk=slide_id)
        slide.delete()  # Delete the slide
        return Response(status=status.HTTP_204_NO_CONTENT)  # No content after deletion
    except CourseDocuments.DoesNotExist:
        return Response({"error": "Slide not found"}, status=status.HTTP_404_NOT_FOUND)
 
@api_view(['GET'])
def get_assignments_by_course(request, course_id):
     try:
         course = Courses.objects.get(pk=course_id)
     except Courses.DoesNotExist:
         return Response({"error": "Course not found"}, status=status.HTTP_404_NOT_FOUND)
 
     assignments = Assignment.objects.filter(course_id=course)
     serializer = AssignmentSerializer(assignments, many=True)
     return Response(serializer.data)

@api_view(['POST'])
def submit_assignment(request):
    student_id = request.data.get('student_id')
    assignment_id = request.data.get('assignment_id')
    upload_url = request.data.get('upload_url')
    assign_name = request.data.get('assign_name')

    if not all([student_id, assignment_id, upload_url, assign_name]):
        return Response(
            {"error": "Missing one or more required fields: student_id, assignment_id, upload_url, assign_name"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validate foreign keys manually
    try:
        student = Student.objects.get(pk=student_id)
    except Student.DoesNotExist:
        return Response({"error": f"Student with ID {student_id} not found."}, status=404)

    try:
        assignment = Assignment.objects.get(pk=assignment_id)
    except Assignment.DoesNotExist:
        return Response({"error": f"Assignment with ID {assignment_id} not found."}, status=404)

    # Prevent duplicate
    if StudentAssignment.objects.filter(student_id=student, assignment_id=assignment).exists():
        return Response(
            {"error": "You have already submitted this assignment."},
            status=400
        )

    student_assignment = StudentAssignment.objects.create(
        student_id=student,
        assignment_id=assignment,
        upload_url=upload_url,
        assign_name=assign_name
    )

    serializer = StudentAssignmentSerializer(student_assignment)
    return Response(serializer.data, status=201)


@api_view(['GET'])
def courseview(request):
    user = request.user
    extrainfo = ExtraInfo.objects.select_related().get(user=user)
    if extrainfo.user_type == 'student':
        student = Student.objects.select_related('id').get(id=extrainfo)
        # register = course_registration.objects.select_related().filter(student_id=student)
        # courses_info = Courses.objects.select_related().filter(id=register)
        
        # course_serializer = CourseRegistrationSerializer(course_infos, many=True)
        register = course_registration.objects.select_related().filter(student_id=student)

        courses_info = []
        for reg in register:
            course = Courses.objects.select_related().get(pk=reg.course_id.id)  # Optimized retrieval using primary key
            courses_info.append(course)

        course_serializer = CourseRegistrationSerializer(courses_info, many=True)
        print(course_serializer)
        data ={
            "courses":course_serializer.data
        }
        return Response(data,status=status.HTTP_200_OK)
        
    elif extrainfo.user_type == 'faculty':
        instructor = CourseInstructor.objects.select_related('course_id').filter(instructor_id=extrainfo)
        courses_info=[]
        for ins in instructor:
            course = Courses.objects.select_related().get(pk=ins.course_id.id)
            courses_info.append(course)
        
        course_serializer = CourseRegistrationSerializer(courses_info, many=True)
        data = {
            "courses":course_serializer.data
        }
        return Response(data, status=status.HTTP_200_OK)
    else:
        return Response({"error":"error occured"})

@api_view(['GET'])
def course(request, course_code, version):
    '''
    desc: Home page for each courses for Student/Faculty
    '''
    user = request.user
    extrainfo = ExtraInfo.objects.select_related().get(user=user)
    notifs = request.user.notifications.all()
    if extrainfo.user_type == 'student':   #if the user is student .. funtionality used by him/her
        # if request.session.get('currentDesignationSelected') != 'student':
        #     return HttpResponseRedirect('/dashboard/')
        student = Student.objects.select_related('id').get(id=extrainfo)
        #info about courses he is registered in
        course = Courses.objects.select_related().get(code=course_code, version = version)
        #instructor of the course
        instructor = CourseInstructor.objects.select_related().get(course_id = course, batch_id = student.batch_id)
        
        # Serialize course and instructor
        course_serializer = CoursesSerializer(course)
        instructor_serializer = CourseInstructorSerializer(instructor)
        #course material uploaded by the instructor
        # videos = CourseVideo.objects.filter(course_id=course)
        videos = []
        if request.method == 'POST':
            search_url = "https://www.googleapis.com/youtube/v3/search"
            video_url = "https://www.googleapis.com/youtube/v3/videos"
            search_params = {
                'part': 'snippet',
                'q': request.POST['search'],
                'key': settings.YOUTUBE_DATA_API_KEY,
                'type': 'video',
                'channelId': 'channel_id'
            }
            videos_ids = []
            r = requests.get(search_url, params=search_params)
            # print(r)
            results = r.json()['items']
            for result in results:
                videos_ids.append(result['id']['videoId'])

            video_params = {
                'key': settings.YOUTUBE_DATA_API_KEY,
                'part': 'snippet,contentDetails',
                'id': ','.join(videos_ids),
                'maxResults': 9
            }

            p = requests.get(video_url, params=video_params)
            results1 = p.json()['items']

            for result in results1:
                video_data = {
                    'id': result['id'],
                    # 'url': f'https://www.youtube.com/watch?v={result["id"]}',
                    'title': result['snippet']['title'],
                    # 'duration': int(parse_duration(result['contentDetails']['duration']).total_seconds() // 60),
                    # 'thumbnails': result['snippet']['thumbnails']['high']['url']
                }

                videos.append(video_data)
        else:
            x = 0
            # channel_url = "https://www.googleapis.com/youtube/v3/channels"
            # playlist_url = "https://www.googleapis.com/youtube/v3/playlistItems"
            # videos_url = "https://www.googleapis.com/youtube/v3/videos"

            # videos_list = []
            # channel_params = {
            #     'part': 'contentDetails',
            #     'id': 'channel_id',
            #     'key': settings.YOUTUBE_DATA_API_KEY,
            # }
            # r = requests.get(channel_url, params=channel_params)
            # results = r.json()['items'][0]['contentDetails']['relatedPlaylists']['uploads']

            # playlist_params = {
            #     'key': settings.YOUTUBE_DATA_API_KEY,
            #     'part': 'snippet',
            #     'playlistId': results,
            #     'maxResults': 5,
            # }
            # p = requests.get(playlist_url, params=playlist_params)
            # results1 = p.json()['items']

            # for result in results1:
            #     # print(results)
            #     videos_list.append(result['snippet']['resourceId']['videoId'])

            # videos_params = {
            #     'key': settings.YOUTUBE_DATA_API_KEY,
            #     'part': 'snippet',
            #     'id': ','.join(videos_list)
            # }

            # v = requests.get(videos_url, params=videos_params)
            # results2 = v.json()['items']
            # videos = []
            # for res in results2:
            #     video_data = {
            #         'id': res['id'],
            #         'title': res['snippet']['title'],
            #     }

            #     videos.append(video_data)
            # print(videos)

        modules = Modules.objects.select_related().filter(course_id=course)
        slides = CourseDocuments.objects.select_related().filter(course_id=course)

        modules_with_slides = collections.OrderedDict()
        for m in modules:
            sl = []
            for slide in slides:
                if slide.module_id.id == m.id:
                    sl.append(slide)
            if len(sl) == 0:
                modules_with_slides[m] = 0
            else:
                modules_with_slides[m] = sl
        # Serialize modules
        modules_serializer = ModulesSerializer(modules, many=True)
        slides_serializer =  CourseDocumentsSerializer(slides, many=True)

        quiz = Quiz.objects.select_related().filter(course_id=course)
        assignment = Assignment.objects.select_related().filter(course_id=course)
        submitable_assignments = []
        for assi in assignment:
            if assi.submit_date.date() >= datetime.date.today():
                submitable_assignments.append(assi)
                
        student_assignment = []
        for assi in assignment:
            sa = StudentAssignment.objects.select_related().filter(assignment_id=assi, student_id=student)
            student_assignment.append(sa)
            
        assignment_serializer = AssignmentSerializer(assignment, many=True)
            
        '''
        marks to store the marks of quizes of student
        marks_pk to store the quizs taken by student
        quizs=>quizs that are not over
        '''
        # marks = []
        # quizs = []
        # marks_pk = []
        # #quizzes details
        # for q in quiz:
        #     qs = QuizResult.objects.select_related().filter(quiz_id=q, student_id=student)
        #     qs_pk = qs.values_list('quiz_id', flat=True)
        #     if q.end_time > timezone.now():
        #         quizs.append(q)
        #     if qs:
        #         marks.append(qs[0])
        #         marks_pk.append(qs_pk[0])
        
        present_attendance = {}
        total_attendance=None
        a = Attendance.objects.select_related().filter(student_id=student , instructor_id = instructor)
        total_attendance = len(a)
        count = 0
        for row in a:
                if(row.present):
                    count+=1
                    present_attendance[row.date] = 1
                else:
                    present_attendance[row.date] = 0
        attendance_percent = 0
        if(total_attendance):
            attendance_percent = count/total_attendance*100
            attendance_percent = round(attendance_percent,2)

        attendance_file = {}
        try:
            attendance_file = AttendanceFiles.objects.select_related().filter(course_id=course)
        except AttendanceFiles.DoesNotExist:
            attendance_file = {}

        attendance_serializer = AttendanceSerializer(a, many=True)
        
        lec = 0
        comments = Forum.objects.select_related().filter(course_id=course).order_by('comment_time')
        answers = collections.OrderedDict()
        for comment in comments:
            fr = ForumReply.objects.select_related().filter(forum_reply=comment)
            fr1 = ForumReply.objects.select_related().filter(forum_ques=comment)
            if not fr:
                answers[comment] = fr1
        # serialise forum and reply
        forum_serializer = ForumSerializer(comments,many=True)
        # forum_reply_serializer = ForumReplySerializer(fr,many=True)
        
        data = {
            'course': course_serializer.data,
            'instructor': instructor_serializer.data,
            'modules': modules_serializer.data,
            'slides': slides_serializer.data,
            'assignments': assignment_serializer.data,
            'student_assignment': student_assignment,  # Include if needed
            'attendance': attendance_serializer.data, #try sending "total attendance"
            'present_attendance': present_attendance,
            'attendance_percent': attendance_percent,
            'attendance_file': attendance_file,
            # 'comments': nested_comments,  # Use nested comments for better structure
            # 'forum_reply': forum_reply_serializer.data,  # Include if not nested  # Include if needed
            # 'notifications': notifs.values('id', 'title', 'message', 'is_seen'),
        }
        print(course_serializer.data)
        return Response(data,status=status.HTTP_200_OK)

    else:
        # if request.session.get('currentDesignationSelected') != "faculty" and request.session.get('currentDesignationSelected') != "Associate Professor" and request.session.get('currentDesignationSelected') != "Professor" and request.session.get('currentDesignationSelected') != "Assistant Professor":
        #     return HttpResponseRedirect('/dashboard/')
        instructor = CourseInstructor.objects.select_related('course_id').filter(instructor_id=extrainfo)
        for ins in instructor:
            if ins.course_id.code == course_code and ins.course_id.version == Decimal(version):
                registered_students = course_registration.objects.select_related('student_id').filter(course_id = ins.course_id)
                students = {}
                test_marks = {}
                for x in registered_students:
                     students[x.student_id.id.id] = (x.student_id.id.user.first_name + " " + x.student_id.id.user.last_name)
                #     stored_marks = StoreMarks.objects.filter(mid = x.r_id)
                #     for x in stored_marks:
                #         test_marks[x.id] = (x.mid.r_id,x.exam_type,x.marks)
                    #marks_id.append(x.curr_id)
                    #print(stored_marks)
                    #for x in stored_marks:
                    #    print(x)
                students_info = []
                for stu in registered_students:
                    s = Student.objects.select_related().get(pk=stu.student_id.id)
                    students_info.append(s)
                    
                    
                # registered student serializer 
                registered_students_serialiser = StudentSerializer(students_info,many=True)
                course = ins.course_id
                result_topics = Topics.objects.select_related().filter(course_id = course)
                
                if (len(list(result_topics))!=0):
                    topics = result_topics
                else:
                    topics = None
                # serializer 
                topics_serialiser = TopicsSerializer(topics,many=True)
                present_attendance = {}
                total_attendance=None
                for x in registered_students:
                    a = Attendance.objects.select_related().filter(student_id=x.student_id , instructor_id = ins)
                    total_attendance = len(a)
                    count =0
                    for row in a:
                        if(row.present):
                            count += 1
                    
                    attendance_percent = 0
                    if(total_attendance):
                        attendance_percent = count/total_attendance*100
                        attendance_percent = round(attendance_percent,2)
                    present_attendance[x.student_id.id.id] = {
                        'count': count,
                        'attendance_percent': attendance_percent
                    }

        lec = 1
        videos = []
        
        # videos = CourseVideo.objects.filter(course_id=course)
        # channel_url = "https://www.googleapis.com/youtube/v3/channels"
        # playlist_url = "https://www.googleapis.com/youtube/v3/playlistItems"
        # videos_url = "https://www.googleapis.com/youtube/v3/videos"

        # videos_list = []
        # channel_params = {
        #     'part': 'contentDetails',
        #     # 'forUsername': 'TechGuyWeb',
        #     'id': 'UCdGQeihs84hyCssI2KuAPmA',
        #     'key': settings.YOUTUBE_DATA_API_KEY,
        # }
        # r = requests.get(channel_url, params=channel_params)
        # results = r.json()['items'][0]['contentDetails']['relatedPlaylists']['uploads']

        # playlist_params = {
        #     'key': settings.YOUTUBE_DATA_API_KEY,
        #     'part': 'snippet',
        #     'playlistId': results,
        #     'maxResults': 5,
        # }
        # p = requests.get(playlist_url, params=playlist_params)
        # results1 = p.json()['items']

        # for result in results1:
        #     videos_list.append(result['snippet']['resourceId']['videoId'])

        # videos_params = {
        #     'key': settings.YOUTUBE_DATA_API_KEY,
        #     'part': 'snippet',
        #     'id': ','.join(videos_list)
        # }

        # v = requests.get(videos_url, params=videos_params)
        # results2 = v.json()['items']
        # videos = []
        # for res in results2:
        #     video_data = {
        #         'id': res['id'],
        #         'title': res['snippet']['title'],
        #     }

        #     videos.append(video_data)
        modules = Modules.objects.select_related().filter(course_id=course)
        slides = CourseDocuments.objects.select_related().filter(course_id=course)
        modules_with_slides = collections.OrderedDict()
        for m in modules:
            sl = []
            for slide in slides:
                if slide.module_id.id == m.id:
                    sl.append(slide)
            if len(sl) == 0:
                modules_with_slides[m] = 0
            else:
                modules_with_slides[m] = sl
        # quiz = Quiz.objects.select_related().filter(course_id=course)
        # marks = []
        # quizs = []
        modules_serializer = ModulesSerializer(modules, many=True)
        slides_serializer =  CourseDocumentsSerializer(slides, many=True)
        
        assignment = Assignment.objects.select_related().filter(course_id=course)
        student_assignment = []
        for assi in assignment:
            sa = StudentAssignment.objects.select_related().filter(assignment_id=assi)
            student_assignment.append(sa)
        # for q in quiz:
        #     qs = QuizResult.objects.select_related().filter(quiz_id=q)
        #     if q.end_time > timezone.now():
        #         quizs.append(q)
        #     if len(qs) != 0:
        #         marks.append(qs)
        
        assignment_serializer = AssignmentSerializer(assignment, many=True)
        
        comments = Forum.objects.select_related().filter(course_id=course).order_by('comment_time')
        answers = collections.OrderedDict()
        for comment in comments:
            fr = ForumReply.objects.select_related().filter(forum_reply=comment)
            fr1 = ForumReply.objects.select_related().filter(forum_ques=comment)
            if not fr:
                answers[comment] = fr1
        # qb = QuestionBank.objects.select_related().filter(instructor_id=extrainfo, course_id=course)
        forum_serializer = ForumSerializer(comments,many=True)
        
        gradingscheme = GradingScheme.objects.select_related().filter(course_id=course)
        try:
            gradingscheme_grades = GradingScheme_grades.objects.select_related().get(course_id=course)
        except GradingScheme_grades.DoesNotExist:
            gradingscheme_grades = {}

        try:
            student_grades = Student_grades.objects.select_related().filter(course_id=course)
        except Student_grades.DoesNotExist:
            student_grades = {}
            
        gradingscheme_serialiser = GradingSchemeSerializer(gradingscheme,many=True)
        data = {
            "students":registered_students_serialiser.data,
            "topics":topics_serialiser.data,
            "present_att":present_attendance,
            "total_att":total_attendance,
            "modules":modules_serializer.data,
            "slides":slides_serializer.data,
            "assignment":assignment_serializer.data,
            "forum":forum_serializer.data,
            "grading_scheme":gradingscheme_serialiser.data,
        }
        return Response(data,status=status.HTTP_200_OK)
       

#Grading Scheme

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_grading_scheme(request):
    """
    API to create/update grading scheme.
    - Only faculty users can access this API.
    - Accepts all required data in the request body.
    """

    user = request.user

    # Check if user is faculty
    extrainfo = get_object_or_404(ExtraInfo, user=user)
    if extrainfo.user_type != 'faculty':
        return Response({"error": "Only faculty can create grading schemes"}, status=status.HTTP_403_FORBIDDEN)

    # Extract request data
    course_code = request.data.get("course_code")
    version = request.data.get("version")
    evaluations = request.data.get("evaluations", {})
    grading_boundaries = request.data.get("grading_boundaries", {})

    # Validate course existence
    course = get_object_or_404(Courses, code=course_code, version=version)

    # ✅ Save Grading Scheme (Evaluations)
    for eval_type, weightage in evaluations.items():
        GradingScheme.objects.update_or_create(
            course_id=course,
            type_of_evaluation=eval_type,
            defaults={"weightage": weightage}
        )

    # ✅ Save Grading Boundaries
    GradingScheme_grades.objects.update_or_create(
        course_id=course,
        defaults=grading_boundaries
    )

    return Response({"message": "Grading scheme created successfully"}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def view_attendance(request, course_code, version):
    user = request.user

    if not course_code or not version:
        return Response({"error": "course_code and version are required parameters"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        extrainfo = ExtraInfo.objects.select_related().get(user=user)
    except ExtraInfo.DoesNotExist:
        return Response({"error": "User information not found"}, status=status.HTTP_404_NOT_FOUND)

    if extrainfo.user_type == 'student':
        try:
            student = Student.objects.select_related('id').get(id=extrainfo)
            course = Courses.objects.select_related().get(code=course_code, version=version)
            instructor = CourseInstructor.objects.select_related().get(course_id=course, batch_id=student.batch_id)
            print(instructor)
            print(student)
            print(course)
        except (Student.DoesNotExist, Courses.DoesNotExist, CourseInstructor.DoesNotExist):
            return Response({"error": "Course or instructor not found"}, status=status.HTTP_404_NOT_FOUND)

        attendance_records = Attendance.objects.select_related().filter(student_id=student, instructor_id=instructor)
        attendance_serializer = AttendanceSerializer(attendance_records, many=True)

        return Response(attendance_serializer.data, status=status.HTTP_200_OK)

    elif extrainfo.user_type == 'instructor':
        try:
            instructor = CourseInstructor.objects.select_related('course_id').get(instructor_id=extrainfo, course_id__code=course_code, course_id__version=version)
        except CourseInstructor.DoesNotExist:
            return Response({"error": "Instructor or course not found"}, status=status.HTTP_404_NOT_FOUND)

        registered_students = course_registration.objects.select_related('student_id').filter(course_id=instructor.course_id)
        attendance_records = Attendance.objects.select_related().filter(instructor_id=instructor, student_id__in=[stu.student_id for stu in registered_students])
        attendance_serializer = AttendanceSerializer(attendance_records, many=True)

        return Response(attendance_serializer.data, status=status.HTTP_200_OK)

    return Response({"error": "Invalid user type"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_marks(request):
    """
    API to submit/update student marks for evaluations.
    - Only faculty users can access this API.
    - Accepts student marks data in batch or individual format.
    """
    user = request.user

    # Check if user is faculty
    extrainfo = get_object_or_404(ExtraInfo, user=user)
    if extrainfo.user_type != 'faculty':
        return Response({"error": "Only faculty can submit marks"}, status=status.HTTP_403_FORBIDDEN)

    # Extract request data
    course_code = request.data.get("course_code")
    version = request.data.get("version")
    evaluation_type = request.data.get("evaluation_type")  # e.g., "midsem", "endsem", "assignment1"
    marks_data = request.data.get("marks_data", [])  # List of student marks

    if not course_code or not version or not evaluation_type or not marks_data:
        return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

    # Validate course existence
    try:
        course = Courses.objects.get(code=course_code, version=version)
    except Courses.DoesNotExist:
        return Response({"error": f"Course {course_code} (version {version}) not found"}, 
                       status=status.HTTP_404_NOT_FOUND)

    # Check if faculty teaches this course
    instructor = CourseInstructor.objects.filter(instructor_id=extrainfo, course_id=course).first()
    if not instructor:
        return Response({"error": "You are not an instructor for this course"}, 
                       status=status.HTTP_403_FORBIDDEN)

    # Process marks data
    successful_updates = 0
    errors = []

    for entry in marks_data:
        try:
            # Get required fields
            student_id = entry.get("student_id")
            marks = entry.get("marks")
            
            if not student_id or marks is None:
                errors.append(f"Missing student_id or marks in entry: {entry}")
                continue

            # Validate student exists and is registered for the course
            try:
                student_extrainfo = ExtraInfo.objects.get(id=student_id)
                student = Student.objects.get(id=student_extrainfo)
                
                # Check if student is registered for this course
                registration = course_registration.objects.filter(
                    student_id=student, 
                    course_id=course
                ).exists()
                
                if not registration:
                    errors.append(f"Student {student_id} is not registered for this course")
                    continue
                    
            except (ExtraInfo.DoesNotExist, Student.DoesNotExist):
                errors.append(f"Student with ID {student_id} not found")
                continue

            # Create or update marks in Student_grades model
            defaults = {
                "marks": marks,
                "instructor_id": extrainfo
            }
            
            # Optional comment field
            if "comment" in entry:
                defaults["comment"] = entry.get("comment")

            # Update or create the marks entry
            Student_grades.objects.update_or_create(
                student_id=student,
                course_id=course,
                exam_type=evaluation_type,
                defaults=defaults
            )
            
            successful_updates += 1
            
        except Exception as e:
            errors.append(f"Error processing entry for student {entry.get('student_id')}: {str(e)}")

    # Return response with results
    response_data = {
        "message": f"Processed {successful_updates} mark entries successfully",
        "successful_updates": successful_updates,
        "error_count": len(errors)
    }
    
    if errors:
        response_data["errors"] = errors

    return Response(response_data, status=status.HTTP_200_OK if successful_updates > 0 else status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_course_notification(request):
    """
    API to send course management notifications.
    
    POST parameters:
    - recipient_id: User ID of the recipient
    - type: Type of notification (e.g., 'new_slide', 'new_assignment', etc.)
    - course_code: (Optional) Code of the course
    - message: (Optional) Custom message for custom notifications
    """
    try:
        # Extract data from request
        recipient_id = request.data.get('recipient_id')
        notification_type = request.data.get('type')
        course_code = request.data.get('course_code')
        message = request.data.get('message')
        
        # Validate required fields
        if not recipient_id or not notification_type:
            return Response(
                {"error": "recipient_id and type are required fields"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Get the recipient user
        try:
            recipient = User.objects.get(id=recipient_id)
        except User.DoesNotExist:
            return Response(
                {"error": f"Recipient with ID {recipient_id} not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Send notification
        sender = request.user  # Current logged-in user is the sender
        course_management_notif(
            sender=sender,
            recipient=recipient,
            type=notification_type,
            course_code=course_code,
            message=message
        )
        
        return Response(
            {"message": "Notification sent successfully"}, 
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        return Response(
            {"error": f"Failed to send notification: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

def course_management_notif(sender, recipient, type, course_code=None, message=None):
    """
    Function to handle course management notifications.
    
    @param:
        sender - User sending the notification
        recipient - User receiving the notification
        type - Type of notification (e.g., 'new_slide', 'new_assignment', etc.)
        course_code - Code of the course (optional)
        message - Custom message (optional)
    """
    url = 'online_cms:course'  # URL to redirect to when notification is clicked
    module = 'Course Management'
    sender = sender
    recipient = recipient
    verb = ''
    
    # Define different notification messages based on type
    if type == 'new_slide':
        verb = f"New slide has been uploaded for course {course_code}" if course_code else "New slide has been uploaded"
    elif type == 'new_assignment':
        verb = f"New assignment has been posted for course {course_code}" if course_code else "New assignment has been posted"
    elif type == 'grade_updated':
        verb = f"Your grades have been updated for course {course_code}" if course_code else "Your grades have been updated"
    elif type == 'assignment_feedback':
        verb = f"Feedback added to your assignment for course {course_code}" if course_code else "Feedback added to your assignment"
    elif type == 'attendance_updated':
        verb = f"Your attendance has been updated for course {course_code}" if course_code else "Your attendance has been updated"
    elif type == 'custom':
        # For custom notifications
        verb = message if message else "You have a new notification"
    
    # Send the notification
    notify.send(sender=sender, recipient=recipient, url=url, module=module, verb=verb)