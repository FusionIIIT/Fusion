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
# from applications.globals.models import *

# from .forms import *
# from .helpers import create_thumbnail, semester
# from .models import *
# from .helpers import create_thumbnail, semester
# from notification.views import course_management_notif
# def viewcourses_serialized(request):
#     user = request.user
#     extrainfo = ExtraInfo.objects.select_related().get(user=user)
    
#     # If the user is a student
#     if extrainfo.user_type == 'student':
#         student = Student.objects.select_related('id').get(id=extrainfo)
#         register = course_registration.objects.select_related().filter(student_id=student)

#         # Serialize registered courses
#         registered_courses_data = serializers.serialize('json', register)

#         return JsonResponse({
#             'user_type': 'student',
#             'registered_courses': registered_courses_data,
#         })

#     # If the user is faculty
#     elif extrainfo.user_type == 'faculty':
#         instructor = CourseInstructor.objects.select_related('curriculum_id').filter(instructor_id=extrainfo)
#         curriculum_list = [Courses.objects.select_related().get(pk=x.course_id) for x in instructor]

#         # Serialize curriculum list
#         curriculum_data = serializers.serialize('json', curriculum_list)

#         return JsonResponse({
#             'user_type': 'faculty',
#             'curriculum_list': curriculum_data,
#         })

#     # If the user is an admin
#     elif extrainfo.id == 'id_admin':
#         # if request.session.get('currentDesignationSelected') != 'acadadmin':
#         #     return HttpResponseRedirect('/dashboard/')
        
#         calendar = Calendar.objects.all()
#         timetable = Timetable.objects.all()

#         # Serialize calendar and timetable data
#         calendar_data = serializers.serialize('json', calendar)
#         timetable_data = serializers.serialize('json', timetable)

#         return JsonResponse({
#             'user_type': 'admin',
#             'academic_calendar': calendar_data,
#             'timetable': timetable_data,
#         })

#     return JsonResponse({
#         'error': 'Unknown user type'
#     })

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status  # Import for custom status codes
from .serializers import *
# class CourseListView(APIView):
#     def get(self, request):
#         user = request.user

#         try:
#             extrainfo = ExtraInfo.objects.select_related().get(user=user)
#         except ExtraInfo.DoesNotExist:
#             return Response({'message': 'ExtraInfo object not found for this user'}, status=status.HTTP_404_NOT_FOUND)

#         if extrainfo.user_type == 'student':
#             try:
#                 student = Student.objects.select_related('id').get(id=extrainfo)
#                 register = course_registration.objects.select_related().filter(student_id=student)
#             except (Student.DoesNotExist, course_registration.DoesNotExist):
#                 return Response({'message': 'No courses found for this student'}, status=status.HTTP_404_NOT_FOUND)

#             courses = collections.OrderedDict()
#             for reg in register:
#                 # instructor = CourseInstructor.objects.select_related().get(course_id=reg.course_id).first()
#                 instructors = CourseInstructor.objects.select_related().filter(course_id=reg.course_id)
#                 instructor = instructors.first()  # Get the first instructor

#                 courses[reg] = instructor

#             courses_serializer = CoursesSerializer(courses, many=True)  # Assuming CourseRegistrationSerializer exists
#             return Response(courses_serializer.data)
#         elif extrainfo.user_type == 'faculty':
#             # ... similar logic for faculty courses ...

#             return Response(faculty_courses_serializer.data)  # Assuming faculty_courses_serializer exists
#         elif extrainfo.user_type == 'id_admin':
#             # ... similar logic for admin courses ...

#             return Response(admin_courses_serializer.data)  # Assuming admin_courses_serializer exists
#         else:
#             return Response({'message': 'Invalid user type'}, status=status.HTTP_400_BAD_REQUEST)

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
       