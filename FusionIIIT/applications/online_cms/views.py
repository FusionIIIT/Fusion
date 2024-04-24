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
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.utils import timezone

from applications.academic_information.models import (Course, Curriculum_Instructor,Curriculum,
                                                      Student,Student_attendance)
from applications.academic_procedures.models import Register
from applications.globals.models import ExtraInfo
from applications.globals.models import *

from .forms import *
# from .helpers import create_thumbnail, semester
from .models import *
from .helpers import create_thumbnail, semester


@login_required
def viewcourses(request):
    '''
    desc: Shows all the courses under the user
    '''
    user = request.user

    extrainfo = ExtraInfo.objects.select_related().get(user=user)  #get the type of user
    if extrainfo.user_type == 'student':         #if student is using
        student = Student.objects.select_related('id').get(id=extrainfo)
        roll = student.id.id[:4]                       #get the roll no. of the student
        register = Register.objects.select_related().filter(student_id=student, semester=semester(roll))  #info of registered student
        courses = collections.OrderedDict()   #courses in which student is registerd
        for reg in register:   #info of the courses
            instructor = Curriculum_Instructor.objects.select_related().get(course_id=reg.course_id)
            courses[reg] = instructor
        return render(request, 'coursemanagement/coursemanagement1.html',
                      {'courses': courses,

                       'extrainfo': extrainfo})
    else:   #if the user is lecturer
        instructor = Curriculum_Instructor.objects.select_related('curriculum_id').filter(instructor_id=extrainfo)   #get info of the instructor
        curriculum_list = []
        for x in instructor:
            c = Curriculum.objects.select_related().get(curriculum_id = x.curriculum_id.curriculum_id)
            curriculum_list.append(c)


        return render(request, 'coursemanagement/coursemanagement1.html',
                      {'instructor': instructor,
                       'extrainfo': extrainfo,
                       'curriculum_list': curriculum_list})



@login_required
def course(request, course_code):
    '''
    desc: Home page for each courses for Student/Faculty
    '''
    user = request.user
    extrainfo = ExtraInfo.objects.select_related().get(user=user)
    if extrainfo.user_type == 'student':   #if the user is student .. funtionality used by him/her
        student = Student.objects.select_related('id').get(id=extrainfo)
        roll = student.id.id[:4]

        #info about courses he is registered in
        curriculum = Curriculum.objects.select_related('course_id').get(course_code=course_code)
        course = curriculum.course_id
        #instructor of the course
        instructor = Curriculum_Instructor.objects.select_related().get(curriculum_id=curriculum)
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
            channel_url = "https://www.googleapis.com/youtube/v3/channels"
            playlist_url = "https://www.googleapis.com/youtube/v3/playlistItems"
            videos_url = "https://www.googleapis.com/youtube/v3/videos"

            videos_list = []
            channel_params = {
                'part': 'contentDetails',
                'id': 'channel_id',
                'key': settings.YOUTUBE_DATA_API_KEY,
            }
            r = requests.get(channel_url, params=channel_params)
            results = r.json()['items'][0]['contentDetails']['relatedPlaylists']['uploads']

            playlist_params = {
                'key': settings.YOUTUBE_DATA_API_KEY,
                'part': 'snippet',
                'playlistId': results,
                'maxResults': 5,
            }
            p = requests.get(playlist_url, params=playlist_params)
            results1 = p.json()['items']

            for result in results1:
                # print(results)
                videos_list.append(result['snippet']['resourceId']['videoId'])

            videos_params = {
                'key': settings.YOUTUBE_DATA_API_KEY,
                'part': 'snippet',
                'id': ','.join(videos_list)
            }

            v = requests.get(videos_url, params=videos_params)
            results2 = v.json()['items']
            videos = []
            for res in results2:
                video_data = {
                    'id': res['id'],
                    'title': res['snippet']['title'],
                }

                videos.append(video_data)
            # print(videos)
        slides = CourseDocuments.objects.select_related().filter(course_id=course)
        quiz = Quiz.objects.select_related().filter(course_id=course)
        assignment = Assignment.objects.select_related().filter(course_id=course)
        student_assignment = []
        for assi in assignment:
            sa = StudentAssignment.objects.select_related().filter(assignment_id=assi, student_id=student)
            student_assignment.append(sa)
        '''
        marks to store the marks of quizes of student
        marks_pk to store the quizs taken by student
        quizs=>quizs that are not over
        '''
        marks = []
        quizs = []
        marks_pk = []
        #quizzes details
        for q in quiz:
            qs = QuizResult.objects.select_related().filter(quiz_id=q, student_id=student)
            qs_pk = qs.values_list('quiz_id', flat=True)
            if q.end_time > timezone.now():
                quizs.append(q)
            if qs:
                marks.append(qs[0])
                marks_pk.append(qs_pk[0])
        lec = 0
        comments = Forum.objects.select_related().filter(course_id=course).order_by('comment_time')
        answers = collections.OrderedDict()
        for comment in comments:
            fr = ForumReply.objects.select_related().filter(forum_reply=comment)
            fr1 = ForumReply.objects.select_related().filter(forum_ques=comment)
            if not fr:
                answers[comment] = fr1
        return render(request, 'coursemanagement/viewcourse.html',
                      {'course': course,
                       'quizs': marks,
                       'quizs_pk': marks_pk,
                       'fut_quiz': quizs,
                       'videos': videos,
                       'instructor': instructor,
                       'slides': slides,
                       'extrainfo': extrainfo,
                       'answers': answers,
                       'assignment': assignment,
                       'student_assignment': student_assignment,
                       'Lecturer': lec,
                       'curriculum': curriculum})

    else:
        instructor = Curriculum_Instructor.objects.select_related('curriculum_id').filter(instructor_id=extrainfo)
        for ins in instructor:
            if ins.curriculum_id.course_code == course_code:
                registered_students = Register.objects.select_related('student_id').filter(curr_id = ins.curriculum_id.curriculum_id)
                students = {}
                test_marks = {}
                for x in registered_students:
                     students[x.student_id.id.id] = (x.student_id.id.user.first_name + " " + x.student_id.id.user.last_name, x.id)
                #     stored_marks = StoreMarks.objects.filter(mid = x.r_id)
                #     for x in stored_marks:
                #         test_marks[x.id] = (x.mid.r_id,x.exam_type,x.marks)
                    #marks_id.append(x.curr_id)
                    #print(stored_marks)
                    #for x in stored_marks:
                    #    print(x)

                curriculum = ins.curriculum_id
                course = ins.curriculum_id.course_id
                result_topics = Topics.objects.select_related().filter(course_id = course)
                if (len(list(result_topics))!=0):
                    topics = result_topics
                else:
                    topics = None
                present_attendance = {}
        total_attendance=None
        for x in registered_students:
            a = Student_attendance.objects.select_related().filter(student_id=x.student_id , instructor_id = ins)
            total_attendance = len(a)
            count =0
            for row in a:
                if(row.present):
                    count += 1
            present_attendance[x.student_id.id.id] = count

        lec = 1

        # videos = CourseVideo.objects.filter(course_id=course)
        channel_url = "https://www.googleapis.com/youtube/v3/channels"
        playlist_url = "https://www.googleapis.com/youtube/v3/playlistItems"
        videos_url = "https://www.googleapis.com/youtube/v3/videos"

        videos_list = []
        channel_params = {
            'part': 'contentDetails',
            # 'forUsername': 'TechGuyWeb',
            'id': 'UCdGQeihs84hyCssI2KuAPmA',
            'key': settings.YOUTUBE_DATA_API_KEY,
        }
        r = requests.get(channel_url, params=channel_params)
        results = r.json()['items'][0]['contentDetails']['relatedPlaylists']['uploads']

        playlist_params = {
            'key': settings.YOUTUBE_DATA_API_KEY,
            'part': 'snippet',
            'playlistId': results,
            'maxResults': 5,
        }
        p = requests.get(playlist_url, params=playlist_params)
        results1 = p.json()['items']

        for result in results1:
            videos_list.append(result['snippet']['resourceId']['videoId'])

        videos_params = {
            'key': settings.YOUTUBE_DATA_API_KEY,
            'part': 'snippet',
            'id': ','.join(videos_list)
        }

        v = requests.get(videos_url, params=videos_params)
        results2 = v.json()['items']
        videos = []
        for res in results2:
            video_data = {
                'id': res['id'],
                'title': res['snippet']['title'],
            }

            videos.append(video_data)
        slides = CourseDocuments.objects.select_related().filter(course_id=course)
        quiz = Quiz.objects.select_related().filter(course_id=course)
        marks = []
        quizs = []
        assignment = Assignment.objects.select_related().filter(course_id=course)
        student_assignment = []
        for assi in assignment:
            sa = StudentAssignment.objects.select_related().filter(assignment_id=assi)
            student_assignment.append(sa)
        for q in quiz:
            qs = QuizResult.objects.select_related().filter(quiz_id=q)
            if q.end_time > timezone.now():
                quizs.append(q)
            if len(qs) != 0:
                marks.append(qs)
        comments = Forum.objects.select_related().filter(course_id=course).order_by('comment_time')
        answers = collections.OrderedDict()
        for comment in comments:
            fr = ForumReply.objects.select_related().filter(forum_reply=comment)
            fr1 = ForumReply.objects.select_related().filter(forum_ques=comment)
            if not fr:
                answers[comment] = fr1
        qb = QuestionBank.objects.select_related().filter(instructor_id=extrainfo, course_id=course)
        return render(request, 'coursemanagement/viewcourse.html',
                      {'instructor': instructor,
                       'extrainfo': extrainfo,
                       'curriculum': curriculum,
                       'students' : students,
                       'registered_students': registered_students,
                       'fut_quiz': quizs,
                       'quizs': marks,
                       'videos': videos,
                       'slides': slides,
                       'topics':topics,
                       'course': course,
                       'answers': answers,
                       'assignment': assignment,
                       'student_assignment': student_assignment,
                       'Lecturer': lec,
                       'questionbank': qb,
                       'students': students,
                       'total_attendance' : total_attendance,
                       'present_attendance':present_attendance,
                       'test_marks': test_marks
                       })

#when student uploads the assignment's solution
@login_required
def upload_assignment(request, course_code):
    extrainfo = ExtraInfo.objects.select_related().get(user=request.user)
    if extrainfo.user_type == "student":
        student = Student.objects.select_related('id').get(id=extrainfo)
        try:
            #all details of the assignment
            doc = request.FILES.get('img')    #the images in the assignment
            assi_name = request.POST.get('assignment_topic')
            name = request.POST.get('name')
            assign = Assignment.objects.get(pk=assi_name)
            filename, file_extenstion = os.path.splitext(request.FILES.get('img').name)
        except:
            return HttpResponse("Please fill each and every field correctly!")
        filename = name
        full_path = settings.MEDIA_ROOT + "/online_cms/" + course_code + "/assi/"  #storing the media files
        full_path = full_path + assign.assignment_name + "/" + student.id.id + "/"
        url = settings.MEDIA_URL + filename
        if not os.path.isdir(full_path):
            cmd = "mkdir " + full_path
            subprocess.call(cmd, shell=True)
        fs = FileSystemStorage(full_path, url)
        fs.save(name + file_extenstion, doc)  #saving the media files
        uploaded_file_url = full_path+ "/" + name + file_extenstion
        # to save the solution of assignment the database
        sa = StudentAssignment(
         student_id=student,
         assignment_id=assign,
         upload_url=uploaded_file_url,
         assign_name=name+file_extenstion
        )
        sa.save()
        return HttpResponse("Upload successful.")
    else:
        return HttpResponse("not found")

# when faculty uploads the slides, ppt
@login_required
def add_document(request, course_code):
    extrainfo = ExtraInfo.objects.select_related().get(user=request.user)
    if extrainfo.user_type == "faculty":  #user should be faculty only
        instructor = Curriculum_Instructor.objects.select_related('curriculum_id').filter(instructor_id=extrainfo)  #get the course information

        for ins in instructor:
            if ins.curriculum_id.course_code == course_code:
                course = ins.curriculum_id.course_id

        try:
            description = request.POST.get('description')
            doc = request.FILES.get('img')
            name = request.POST.get('name')
            filename, file_extenstion = os.path.splitext(request.FILES.get('img').name)
        except:
            return HttpResponse("Please fill each and every field correctly!")
        #for storing the media files properly
        filename = name
        full_path = settings.MEDIA_ROOT + "/online_cms/" + course_code + "/doc/"
        url = settings.MEDIA_URL + filename + file_extenstion
        if not os.path.isdir(full_path):
            cmd = "mkdir " + full_path
            subprocess.call(cmd, shell=True)
        fs = FileSystemStorage(full_path, url)
        fs.save(filename + file_extenstion, doc)
        uploaded_file_url = full_path + filename + file_extenstion
        #save the info/details in the database
        CourseDocuments.objects.create(
            course_id=course,
            upload_time=datetime.datetime.now(),
            description=description,
            document_url=uploaded_file_url,
            document_name=name+file_extenstion
        )
        return HttpResponse("Upload successful.")
    else:
        return HttpResponse("not found")

#it is to delete things(assignment, slides, videos, ) from the dustin icon or delete buttons
@login_required
def delete(request, course_code):
    data_type = request.POST.get('type')
    user = request.user
    extrainfo = ExtraInfo.objects.select_related().get(user=user)
    #get the course and user information first

    if extrainfo.user_type == "faculty":
        instructor = Curriculum_Instructor.objects.select_related('curriculum_id').filter(instructor_id=extrainfo)
        for ins in instructor:
            if ins.curriculum_id.course_code == course_code:
                course = ins.curriculum_id.course_id

    if extrainfo.user_type == 'student':
        curriculum_details = Curriculum.objects.select_related('course_id').filter(course_code=course_code)
        course = curriculum_details
        course1 = curriculum_details[0].course_id
        curriculum1 = course[0]
    pk = request.POST.get('pk')
    #to delete videos
    if data_type == 'video':
        video = CourseVideo.objects.get(pk=pk, course_id=course)
        path = video.video_url
        video.delete()
    #to delete slides/documents
    elif data_type == 'slide':
        slide = CourseDocuments.objects.select_related().get(pk=pk, course_id=course)
        path = slide.document_url
        slide.delete()
    #to delete the submitted assignment
    elif data_type == 'stuassignment':
        stu_assi = StudentAssignment.objects.select_related().get(pk=pk)
        path = stu_assi.upload_url
        stu_assi.delete()
    #to delete the assignment uploaded by faculty
    elif data_type == 'lecassignment':
        lec_assi = Assignment.objects.select_related().get(pk=pk)
        path = lec_assi.assignment_url
        lec_assi.delete()
    cmd = "rm "+path
    subprocess.call(cmd, shell=True)
    data = { 'msg': 'Data Deleted successfully'}
    return HttpResponse(json.dumps(data), content_type='application/json')

# to upload videos related to the course
@login_required
def add_videos(request, course_code):
    extrainfo = ExtraInfo.objects.select_related().get(user=request.user)
    #only faculty can add the videos
    if extrainfo.user_type == "faculty":
        instructor = Curriculum_Instructor.objects.select_related('curriculum_id').filter(instructor_id=extrainfo)
        for ins in instructor:
            if ins.curriculum_id.course_code == course_code:
                course = ins.curriculum_id.course_id
        try:
            description = request.POST.get('description')   #the media files required
            vid = request.FILES.get('img')
            name = request.POST.get('name')
            filename, file_extenstion = os.path.splitext(request.FILES.get('img').name)
        except:
            return HttpResponse("Please fill each and every field correctly!")
        #saving the media files
        filename = name
        full_path = settings.MEDIA_ROOT + "/online_cms/" + course_code + "/vid/"
        url = settings.MEDIA_URL+filename + file_extenstion
        if not os.path.isdir(full_path):
            cmd = "mkdir "+full_path
            subprocess.call(cmd, shell=True)
        fs = FileSystemStorage(full_path, url)
        fs.save(filename+file_extenstion, vid)
        uploaded_file_url = full_path + filename + file_extenstion
        #saving in the
        video = CourseVideo.objects.create(
            course_id=course,
            upload_time=datetime.datetime.now(),
            description=description,
            video_url=uploaded_file_url,
            video_name=name
        )
        create_thumbnail(course_code,course, video, name, file_extenstion, 'Big', 1, '700:500')
        create_thumbnail(course_code,course, video, name, file_extenstion, 'Small', 1, '170:127')
        return HttpResponse("Upload successful.")
    else:
        return HttpResponse("not found")


@login_required
def forum(request, course_code):
    # take care of sem
    extrainfo = ExtraInfo.objects.select_related().get(user=request.user)
    if extrainfo.user_type == "student":
        student = Student.objects.select_related('id').get(id=extrainfo)
        roll = student.id.id[:4]
        course = Course.objects.select_related().get(course_id=course_code, sem=semester(roll))
    else:
        instructor = Curriculum_Instructor.objects.select_related().filter(instructor_id=extrainfo)
        for ins in instructor:
            if ins.course_id.course_id == course_code:
                course = ins.course_id
    comments = Forum.objects.select_related().filter(course_id=course).order_by('comment_time')
    instructor = Curriculum_Instructor.objects.get(course_id=course)
    if instructor.instructor_id.user.pk == request.user.pk:
        lec = 1
    else:
        lec = 0
    answers = collections.OrderedDict()
    for comment in comments:
        fr = ForumReply.objects.select_related().filter(forum_reply=comment)
        fr1 = ForumReply.objects.select_related().filter(forum_ques=comment)
        if not fr:
            answers[comment] = fr1
    context = {'course': course, 'answers': answers, 'Lecturer': lec}
    return render(request, 'online_cms/forum.html', context)


@login_required
def ajax_reply(request, course_code):
    extrainfo = ExtraInfo.objects.select_related().get(user=request.user)
    if extrainfo.user_type == "student":
        student = Student.objects.select_related('id').get(id=extrainfo)
        roll = student.id.id[:4]

        curriculum_details = Curriculum.objects.select_related('course_id').filter(course_code=course_code)  #curriculum id
        #print(curriculum_details[0].course_id)
        #print(Curriculum.objects.values_list('curriculum_id'))
        course =  curriculum_details[0].course_id
       # course = Course.objects.get(course_id=course_code, sem=semester(roll))
    else:
        instructor = Curriculum_Instructor.objects.select_related('curriculum_id').filter(instructor_id=extrainfo)
        for ins in instructor:
            if ins.curriculum_id.course_code == course_code:
                course = ins.curriculum_id.course_id
    ex = ExtraInfo.objects.select_related().get(user=request.user)
    f = Forum(
        course_id=course,
        commenter_id=ex,
        comment=request.POST.get('reply')
    )
    f.save()
    ques = Forum.objects.select_related().get(pk=request.POST.get('question'))
    fr = ForumReply(
        forum_ques=ques,
        forum_reply=f
    )
    fr.save()
    name = request.user.first_name + " " + request.user.last_name
    time = f.comment_time.strftime('%b. %d, %Y, %I:%M %p')
    data = {'pk': f.pk, 'reply': f.comment, 'replier': name, 'time': time}
    return HttpResponse(json.dumps(data), content_type='application/json')


@login_required
def ajax_new(request, course_code):
    extrainfo = ExtraInfo.objects.select_related().get(user=request.user)
    if extrainfo.user_type == "student":
        student = Student.objects.select_related('id').get(id=extrainfo)
        roll = student.id.id[:4]
        #course = Course.objects.get(course_id=course_code, sem=semester(roll))
        curriculum_details = Curriculum.objects.select_related('course_id').filter(course_code=course_code)  #curriculum id
        #print(curriculum_details[0].course_id)
        #print(Curriculum.objects.values_list('curriculum_id'))
        course =  curriculum_details[0].course_id
    else:

        instructor = Curriculum_Instructor.objects.select_related('curriculum_id').filter(instructor_id=extrainfo)
        for ins in instructor:
            if ins.curriculum_id.course_code == course_code:
                course = ins.curriculum_id.course_id
    ex = ExtraInfo.objects.select_related().get(user=request.user)
    f = Forum(
        course_id=course,
        commenter_id=ex,
        comment=request.POST.get('question')
    )
    f.save()
    name = request.user.first_name + " " + request.user.last_name
    time = f.comment_time.strftime('%b. %d, %Y, %I:%M %p')

    data = {'pk': f.pk, 'question': f.comment, 'replier': f.commenter_id.user.username,
            'time': time, 'name': name}
    return HttpResponse(json.dumps(data), content_type='application/json')


@login_required
def ajax_remove(request, course_code):
    f = Forum.objects.select_related().get(
        pk=request.POST.get('question')
    )
    fr = ForumReply.objects.select_related().filter(
        forum_reply=f
    )

    if not fr:
        fr1 = ForumReply.objects.select_related().filter(
            forum_ques=f
        )
        for x in fr1:
            x.forum_reply.delete()
            x.delete()
        f.delete()
    else:
        fr.delete()
        f.delete()
    data = {'message': 'deleted'}
    return HttpResponse(json.dumps(data), content_type='application/json')


@login_required
def add_assignment(request, course_code):                 #from faculty side
    extrainfo = ExtraInfo.objects.select_related().get(user=request.user)
    if extrainfo.user_type == "faculty":
        instructor = Curriculum_Instructor.objects.select_related('curriculum_id').filter(instructor_id=extrainfo)
        for ins in instructor:
            if ins.curriculum_id.course_code == course_code:
                course = ins.curriculum_id.course_id
        try:
            assi = request.FILES.get('img')
            name = request.POST.get('name')
            filename, file_extenstion = os.path.splitext(request.FILES.get('img').name)
        except:
            return HttpResponse("Please Enter The Form Properly")
        filename = name
        full_path = settings.MEDIA_ROOT + "/online_cms/" + course_code + "/assi/" + name + "/"
        url = settings.MEDIA_URL + filename
        if not os.path.isdir(full_path):
            cmd = "mkdir " + full_path
            subprocess.call(cmd, shell=True)
        fs = FileSystemStorage(full_path, url)
        fs.save(filename+file_extenstion, assi)
        uploaded_file_url = full_path + filename + file_extenstion
        assign = Assignment(
            course_id=course,
            submit_date=request.POST.get('myDate'),
            assignment_url=uploaded_file_url,
            assignment_name=name
        )
        assign.save()
        return HttpResponse("Upload successful.")
    else:
        return HttpResponse("not found")


@login_required
def edit_bank(request, course_code, qb_code):
    user = request.user
    extrainfo = ExtraInfo.objects.select_related().get(user=user)
    lec = 1
    if extrainfo.user_type == "faculty":
        instructor = Curriculum_Instructor.objects.select_related('curriculum_id').filter(instructor_id=extrainfo)
        for ins in instructor:
            if ins.curriculum_id.course_code == course_code:
                course = ins.curriculum_id.course_id
        qb = QuestionBank.objects.select_related().filter(id=qb_code)
        topics = Topics.objects.select_related().filter(course_id=course)
        Topic = {}
        if qb:
            questions = Question.objects.select_related().filter(question_bank=qb[0]).values_list('topic', flat=True)
            counter = dict(collections.Counter(questions))
            for topic in topics:
                if topic.pk in counter.keys():
                    Topic[topic] = counter[topic.pk]
                else:
                    Topic[topic] = 0
            context = {
                'Lecturer': lec,
                'questionbank': qb[0],
                'topics': Topic,
                'course': course
                }
            return render(request, 'coursemanagement/create_bank.html', context)
        else:
            return HttpResponse("Unauthorized")


@login_required
def create_bank(request, course_code):
    user = request.user
    extrainfo = ExtraInfo.objects.select_related().get(user=user)
    if extrainfo.user_type == "faculty":
        instructor = Curriculum_Instructor.objects.select_related('curriculum_id').filter(instructor_id=extrainfo)
        for ins in instructor:
            if ins.curriculum_id.course_code == course_code:
                course = ins.curriculum_id.course_id
        qb = QuestionBank.objects.create(instructor_id=extrainfo,
                                         course_id=course, name=request.POST.get('qbname'))
        return redirect('/ocms/' + course_code + '/edit_bank/'+str(qb.id))

@login_required
def create_topic(request, course_code):
    user = request.user
    extrainfo = ExtraInfo.objects.select_related().get(user=user)
    if extrainfo.user_type == "faculty":
        instructor = Curriculum_Instructor.objects.select_related('curriculum_id').filter(instructor_id=extrainfo)
        for ins in instructor:
            if ins.curriculum_id.course_code == course_code:
                course = ins.curriculum_id.course_id
        topic = Topics.objects.create(course_id=course, topic_name=request.POST.get('topic_name'))
        return redirect('/ocms/' + course_code)



@login_required
def remove_bank(request, course_code):
    user = request.user
    extrainfo = ExtraInfo.objects.select_related().get(user=user)
    if extrainfo.user_type == "faculty":
        instructor = Curriculum_Instructor.objects.select_related('curriculum_id').filter(instructor_id=extrainfo)
        for ins in instructor:
            if ins.curriculum_id.course_code == course_code:
                course = ins.curriculum_id.course_id
        qb = QuestionBank.objects.select_related().get(id=request.POST.get('pk'))
        qb.delete()
        qb = QuestionBank.objects.select_related().filter(instructor_id=extrainfo, course_id=course)
        data = {'message': "Removed", 'numberof_qbs': len(qb)}
        return HttpResponse(json.dumps(data), content_type='application/json')

@login_required
def remove_topic(request, course_code):
    user = request.user
    extrainfo = ExtraInfo.objects.select_related().get(user=user)
    if extrainfo.user_type == "faculty":
        instructor = Curriculum_Instructor.objects.select_related('curriculum_id').filter(instructor_id=extrainfo)
        for ins in instructor:
            if ins.curriculum_id.course_code == course_code:
                course = ins.curriculum_id.course_id
        topic = Topics.objects.select_related().get(id=request.POST.get('pk'))
        topic.delete()
        n_topics = Topics.objects.select_related().filter(course_id=course)
        data = {'message': "Removed", 'numberof_topics': len(n_topics)}
        return HttpResponse(json.dumps(data), content_type='application/json')


@login_required
def add_question(request, course_id, qb_code, topic_id):
    user = request.user
    course = Course.objects.select_related().get(pk=course_id)
    curriculum = Curriculum.objects.select_related().get(course_id=course)
    course_code = curriculum.course_code
    extrainfo = ExtraInfo.objects.select_related().get(user=user)
    if extrainfo.user_type == "faculty":
        qb = QuestionBank.objects.select_related().filter(pk=qb_code)
        topic = Topics.objects.select_related().get(id=request.POST.get('topic'))
        try:
            filename, file_extenstion = os.path.splitext(request.FILES['image'].name)
            image = request.FILES['image']
            topic_name = topic.topic_name.replace(" ", "_")[:-2]
            full_path = settings.MEDIA_ROOT + "/online_cms/" + course_code
            full_path = full_path + "/qb/" + qb_code + "/" + topic_name + "/"
            url = settings.MEDIA_URL + filename
            if not os.path.isdir(full_path):
                cmd = "mkdir " + full_path
                subprocess.call(cmd, shell=True)
            fs = FileSystemStorage(full_path, url)
            fs.save(image.name, image)
            uploaded_file_url = "/media/online_cms/" + course_code
            uploaded_file_url = uploaded_file_url + "/qb/" + qb_code + "/"
            uploaded_file_url = uploaded_file_url + topic_name + "/" + image.name
        except:
            uploaded_file_url = None

        Question.objects.create(
            question_bank=qb[0],
            topic=topic,
            image=uploaded_file_url,
            question=request.POST.get('problem-statement'),
            options1=request.POST.get('option1'),
            options2=request.POST.get('option2'),
            options3=request.POST.get('option3'),
            options4=request.POST.get('option4'),
            options5=request.POST.get('option5'),
            answer=request.POST.get('answer'),
            marks=request.POST.get('score')
        )
        return redirect('/ocms/' + course_code + '/edit_bank/'+str(qb[0].id))


@login_required
def remove_question(request, course_code, qb_code, topic_id):
    user = request.user
    extrainfo = ExtraInfo.objects.select_related().get(user=user)
    if extrainfo.user_type == "faculty":
        question = Question.objects.select_related().get(pk=request.POST.get('pk'))
        question.delete()
        data = {'message': 'question deleted'}
        return HttpResponse(json.dumps(data), content_type='application/json')


@login_required
def edit_qb_topics(request, course_code, qb_code, topic_id):
    user = request.user
    extrainfo = ExtraInfo.objects.select_related().get(user=user)
    lec = 1
    if extrainfo.user_type == "faculty":
        instructor = Curriculum_Instructor.objects.select_related().filter(instructor_id=extrainfo)
        for ins in instructor:
            if ins.course_id.course_id == course_code:
                course = ins.course_id
        qb = QuestionBank.objects.select_related().filter(pk=qb_code)
        topic = Topics.objects.select_related().get(id=topic_id)
        questions = Question.objects.select_related().filter(question_bank=qb[0], topic=topic)
        context = {
            'Lecturer': lec,
            'questionbank': qb[0],
            'topic': topic,
            'questions': questions,
            'course': course
        }
        return render(request, 'coursemanagement/topicwisequestion.html', context)


@login_required
def quiz(request, quiz_id):
    user = request.user
    extrainfo = ExtraInfo.objects.select_related().get(user=user)
    if extrainfo.user_type == 'student':
        # student = Student.objects.get(id=extrainfo)
        quiz = Quiz.objects.select_related().get(pk=quiz_id)
        length = quiz.number_of_question
        rules = quiz.rules
        rules = [z.encode('ascii', 'ignore') for z in rules.split('/')]
        ques_pk = QuizQuestion.objects.select_related().filter(quiz_id=quiz).values_list('pk', flat=True)
        try:
            random_ques_pk = random.sample(list(ques_pk), length)
        except:
            random_ques_pk = ques_pk
        shuffed_questions = []
        for x in random_ques_pk:
            shuffed_questions.append(QuizQuestion.objects.select_related().get(pk=x))
        end = quiz.end_time
        now = timezone.now() + datetime.timedelta(hours=5.5)
        diff = end-now
        days, seconds = diff.days, diff.seconds
        hours = days * 24 + seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return render(request, 'coursemanagement/quiz.html',
                      {'contest': quiz, 'ques': shuffed_questions,
                       'days': days, 'hours': hours, 'minutes': minutes,
                       'seconds': seconds, 'rules': rules})
    else:
        return HttpResponse("unautherized Access!!It will be reported!!")


@login_required
def ajax_q(request, quiz_code):
    user = request.user
    extrainfo = ExtraInfo.objects.select_related().get(user=user)
    student = Student.objects.select_related('id').get(id=extrainfo)
    q = request.POST.get('question')
    question = Question.objects.select_related().get(pk=q)
    quiz_id = Quiz.objects.select_related().get(pk=quiz_code)
    ques = QuizQuestion.objects.select_related().get(question=question, quiz_id=quiz_id)

    ans = int(request.POST.get('answer'))
    lead = StudentAnswer.objects.filter(quiz_id=quiz_id, question_id=ques, student_id=student)
    if lead:
        lead = lead[0]
        lead.choice = ans
        lead.save()
    else:
        lead = StudentAnswer(quiz_id=quiz_id, question_id=ques, student_id=student, choice=ans)
        lead.save()
    data = {'status': "1"}
    return HttpResponse(json.dumps(data), content_type='application/json')


@login_required
def submit(request, quiz_code):
    ei = ExtraInfo.objects.select_related().get(user=request.user)
    student = Student.objects.select_related().get(id=ei)
    quiz = Quiz.objects.select_related().get(pk=quiz_code)
    stu_ans = StudentAnswer.objects.select_related('question_id__quiz_id').filter(student_id=student, quiz_id=quiz)
    score = 0
    for s_ans in stu_ans:
        if s_ans.question_id.question.answer == s_ans.choice:
            score += s_ans.question_id.question.marks
        else:
            score += (s_ans.quiz_id.negative_marks * s_ans.question_id.question.marks)
    quiz_res = QuizResult(
        quiz_id=quiz,
        student_id=student,
        score=score,
        finished=True
    )
    quiz_res.save()
    data = {'message': 'you have submitted, cant enter again now', 'score': quiz_res.score}
    return HttpResponse(json.dumps(data), content_type="application/json")


@login_required
def create_quiz(request, course_code):
    extrainfo = ExtraInfo.objects.select_related().get(user=request.user)

    if extrainfo.user_type == 'faculty':
        instructor = Curriculum_Instructor.objects.select_related('curriculum_id').filter(instructor_id=extrainfo)
        for ins in instructor:
            if ins.curriculum_id.course_code == course_code:
                curriculum = ins.curriculum_id
                course = ins.curriculum_id.course_id

        for ins in instructor:
            if ins.curriculum_id.course_code == course_code:
                registered_students = Register.objects.filter(curr_id = ins.curriculum_id.curriculum_id)

                course = ins.curriculum_id.course_id

        form = QuizForm(request.POST or None)
        errors = None
        if form.is_valid():
            st_time = form.cleaned_data['starttime']
            k1 = st_time.hour
            k2 = st_time.minute
            k3 = st_time.second
            start_date_time = datetime.datetime.combine(form.cleaned_data['startdate'], datetime.time(k1, k2, k3))
            st_time = form.cleaned_data['endtime']
            k1 = st_time.hour
            k2 = st_time.minute
            k3 = st_time.second
            end_date_time = datetime.datetime.combine(form.cleaned_data['enddate'], datetime.time(k1, k2, k3))
            duration = end_date_time - start_date_time
            days, seconds = duration.days, duration.seconds
            hours, remainder = divmod(duration.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            # If you want to take into account fractions of a second
            seconds += duration.microseconds / 1e6

            description = form.cleaned_data['description'].replace('\r\n', '/')
            rules = form.cleaned_data['rules'].replace('\r\n', '/')
            obj = Quiz.objects.create(
                course_id=course,
                quiz_name=form.cleaned_data['name'],
                description=description,
                rules=rules,
                number_of_question=form.cleaned_data['number_of_questions'],
                negative_marks=form.cleaned_data['negative_marks'],
                start_time=start_date_time,
                end_time=end_date_time,
                d_day=days,
                d_hour=hours,
                d_minute=minutes,
                            )
            return redirect('/ocms/' + course_code + '/edit_quiz/' + str(obj.pk))
        if form.errors:
            errors = form.errors
        return render(request, 'coursemanagement/createcontest.html',
                      {'form': form, 'errors': errors})

    else:
        return HttpResponse("unauthorized Access!!It will be reported!!")


@login_required
def edit_quiz_details(request, course_code, quiz_code):
    extrainfo = ExtraInfo.objects.select_related().get(user=request.user)
    if extrainfo.user_type == 'faculty':
        x = request.POST.get('number')
        quiz = Quiz.objects.select_related().get(pk=quiz_code)
        if x == 'edit1':
            st_time = request.POST.get('starttime')
            st_date = request.POST.get('startdate_month') + " " + request.POST.get('startdate_day')
            st_date = st_date + " " + request.POST.get('startdate_year')
            string = str(st_date) + " " + str(st_time)
            datetime_object = datetime.datetime.strptime(string, '%m %d %Y %H:%M')
            quiz.start_time = datetime_object
            quiz.save()
        elif x == 'edit2':
            st_time = request.POST.get('endtime')
            st_date = request.POST.get('enddate_month') + " " + request.POST.get('enddate_day')
            st_date = st_date + " " + request.POST.get('enddate_year')
            string = str(st_date) + " " + str(st_time)
            datetime_object = datetime.datetime.strptime(string, '%m %d %Y %H:%M')
            quiz.end_time = datetime_object
            quiz.save()
        elif x == 'edit3':
            number = request.POST.get('number_of_questions')
            score = int(quiz.total_score / quiz.number_of_question)
            quiz.number_of_question = number
            quiz.total_score = int(number) * score
            quiz.save()
        elif x == 'edit4':
            score = request.POST.get('per_question_score')
            quiz.total_score = int(score) * quiz.number_of_question
            quiz.save()
        return HttpResponse("Done")

    else:
        return HttpResponse("unautherized Access!!It will be reported!!")


@login_required
def edit_quiz(request, course_code, quiz_code):
    extrainfo = ExtraInfo.objects.select_related().get(user=request.user)
    if extrainfo.user_type == 'faculty':
        lec = 1
        instructor = Curriculum_Instructor.objects.select_related('curriculum_id').filter(instructor_id=extrainfo)
        for ins in instructor:
            if ins.curriculum_id.course_code == course_code:
                curriculum = ins.curriculum_id
                course = ins.curriculum_id.course_id
        # errors = None
        quiz = Quiz.objects.select_related().get(pk=quiz_code)
        questions = QuizQuestion.objects.select_related('question').filter(quiz_id=quiz)
        topic_list = []
        for q in questions:
            topic_list.append(q.question.topic)
        counter = dict(collections.Counter(topic_list))
        form = QuizForm()
        questions_left = quiz.number_of_question - len(questions)
        description = quiz.description
        description = [z.encode('ascii', 'ignore') for z in description.split('/')]
        rules = quiz.rules
        rules = [z.encode('ascii', 'ignore') for z in rules.split('/')]
        questionbank = QuestionBank.objects.select_related().filter(instructor_id=extrainfo, course_id=course)
        topic = Topics.objects.select_related().filter(course_id=course)
        return render(request, 'coursemanagement/editcontest.html',
                      {'details': quiz, 'questionbank': questionbank, 'topics': topic,
                       'course': course, 'lecturer': lec, 'form': form,
                       'counter': counter, 'questions': questions, 'description': description,
                       'rules': rules, 'questions_left': questions_left, 'curriculum': curriculum})
    else:
        return HttpResponse("unauthorized Access!!It will be reported!!")


@login_required
def edit_quiz_topic(request, course_code, quiz_code, topic_id):
    user = request.user
    extrainfo = ExtraInfo.objects.select_related().get(user=user)
    lec = 1
    if extrainfo.user_type == "faculty":
        instructor = Curriculum_Instructor.objects.select_related().filter(instructor_id=extrainfo)
        for ins in instructor:
            if ins.course_id.course_id == course_code:
                course = ins.course_id
        quiz_question = QuizQuestion.objects.select_related('question').filter(quiz_id=quiz_code)
        quest = []
        quiz = Quiz.objects.select_related().get(pk=quiz_code)
        for q in quiz_question:
            if str(q.question.topic.pk) == topic_id:
                quest.append(q.question)

        topic = Topics.objects.select_related().get(id=topic_id)
        return render(request, 'coursemanagement/topicwisequiz.html',
                      {'Lecturer': lec, 'questions': quest,
                       'quiz': quiz, 'topic': topic, 'course': course})


@login_required
def remove_quiz_question(request, course_code, quiz_code, topic_id):
    user = request.user
    extrainfo = ExtraInfo.objects.select_related().get(user=user)
    if extrainfo.user_type == "faculty":
        question = Question.objects.select_related().get(pk=request.POST.get('pk'))
        question_remove = QuizQuestion.objects.select_related().get(question=question, quiz_id=quiz_code)
        question_remove.delete()
        data = {'message': 'question deleted'}
        return HttpResponse(json.dumps(data), content_type='application/json')


@login_required
def add_question_topicwise(request, course_code, quiz_id):
    extrainfo = ExtraInfo.objects.select_related().get(user=request.user)
    if extrainfo.user_type == 'faculty':
        instructor = Curriculum_Instructor.objects.select_related('curriculum_id').filter(instructor_id=extrainfo)
        for ins in instructor:
            if ins.curriculum_id.course_code == course_code:
                course = ins.curriculum_id.course_id
        ques_bank = request.POST.get('qbank')
        quiz = Quiz.objects.select_related().get(pk=quiz_id)
        topic = request.POST.get('topic')
        questions = Question.objects.select_related().filter(question_bank=ques_bank, topic=topic)
        questions_already_present = QuizQuestion.objects.select_related().filter(quiz_id=quiz_id)
        question_already_present = []
        for ques in questions_already_present:
            question_already_present.append(ques.question)
        temp = []
        if questions_already_present:
            for question in questions:
                if question not in question_already_present:
                    temp.append(question)
            questions = temp
        context = {
                    'questions': questions,
                    'course': course,
                    'details': quiz
                    }
        return render(request, 'coursemanagement/select_question.html', context)


@login_required
def add_questions_to_quiz(request, course_id, quiz_id):
    course = Course.objects.select_related().get(pk=course_id)
    curriculum = Curriculum.objects.select_related().get(course_id = course)
    course_code = curriculum.course_code
    extrainfo = ExtraInfo.objects.select_related().get(user=request.user)
    if extrainfo.user_type == 'faculty':
        questions_selected = request.POST.getlist('questions_selected')
        quiz = Quiz.objects.select_related().get(pk=quiz_id)
        for questions in questions_selected:
            question = Question.objects.select_related().get(pk=int(questions))
            QuizQuestion.objects.create(
                quiz_id=quiz,
                question=question
            )
        return redirect('/ocms/' + course_code + '/edit_quiz/' + quiz_id)


@login_required
def preview_quiz(request, course_code, quiz_code):
    extrainfo = ExtraInfo.objects.select_related().get(user=request.user)
    if extrainfo.user_type == 'faculty':
        instructor = Curriculum_Instructor.objects.select_related('curriculum_id').filter(instructor_id=extrainfo)
        for ins in instructor:
            if ins.curriculum_id.course_code == course_code:
                course = ins.curriculum_id.course_id
    quiz = Quiz.objects.select_related().get(pk=quiz_code)
    questions = QuizQuestion.objects.select_related().filter(quiz_id=quiz)

    total_marks = 0
    for q in questions:
        total_marks = total_marks + q.question.marks
    rules = quiz.rules
    rules = [z.encode('ascii', 'ignore') for z in rules.split('/')]

    context = {
        'contest': quiz,
        'course': course,
        'rules': rules,
        'questions': questions,
        'totalmarks': total_marks,
    }
    return render(request, 'coursemanagement/preview_quiz.html', context)


@login_required
def remove_quiz(request, course_code):
    quiz = Quiz.objects.select_related().get(pk=request.POST.get('pk'))
    quizQuestion = QuizQuestion.objects.select_related().filter(quiz_id=quiz)
    for q in quizQuestion:
        q.delete()
    quiz.delete()
    return HttpResponse("Done")


@login_required
def ajax_assess(request, course_code):
    sa = StudentAssignment.objects.select_related().get(pk=request.POST.get('pk'))
    sa.score = request.POST.get('marks')
    sa.save()
    return HttpResponse("Marks uploaded")


@login_required
def ajax_feedback(request, course_code):
    sa = StudentAssignment.objects.select_related().get(pk=request.POST.get('pk'))
    sa.feedback = request.POST.get('feedback')
    sa.save()
#    print(sa,"qwerty")
    return HttpResponse("Feedback uploaded")

#For adding objective assignments for practice
@login_required
def create_practice_contest(request, course_code):
    extrainfo = ExtraInfo.objects.select_related().get(user=request.user)

    if extrainfo.user_type == 'faculty':
        instructor = Instructor.objects.filter(instructor_id=extrainfo)
        for ins in instructor:
            if ins.course_id.course_id == course_code:
                course = ins.course_id
        form = PracticeForm(request.POST or None)
        errors = None
        if form.is_valid():
            description = form.cleaned_data['description'].replace('\r\n', '/')
            obj = Practice.objects.create(
                course_id=course,
                prac_quiz_name=form.cleaned_data['name'],
                negative_marks=form.cleaned_data['negative_marks'],
                number_of_question=form.cleaned_data['number_of_questions'],
                description=description,
                total_score =form.cleaned_data['total_score'],
                )
            # print "Done"
            return redirect('/ocms/' + course_code + '/edit_practice_contest/' + str(obj.pk))
            '''except:
                return HttpResponse('Unexpected Error')'''
        if form.errors:
            errors = form.errors
        return render(request, 'coursemanagement/create_practice_contest.html',
                      {'form': form, 'errors': errors})

@login_required
def edit_practice_contest(request, course_code, practice_contest_code):
    extrainfo = ExtraInfo.objects.select_related().get(user=request.user)
    if extrainfo.user_type == 'faculty':
        lec = 1
        instructor = Instructor.objects.filter(instructor_id=extrainfo)
        for ins in instructor:
            if ins.course_id.course_id == course_code:
                course = ins.course_id
        # errors = None
        practice_contest = Practice.objects.get(pk=practice_contest_code)
        questions = PracticeQuestion.objects.filter(prac_quiz_id=practice_contest)
        topic_list = []
        for q in questions:
            topic_list.append(q.question.topic)
        counter = dict(collections.Counter(topic_list))
        form = PracticeQuestionFormObjective()
        questions_left = practice_contest.number_of_question - len(questions)
        description = practice_contest.description
        description = [z.encode('ascii', 'ignore') for z in description.split('/')]

        #questionbank = QuestionBank.objects.filter(instructor_id=extrainfo, course_id=course)
        #topic = Topics.objects.filter(course_id=course)
        return render(request, 'coursemanagement/edit_practice_contest.html',
                      {'details': practice_contest, #'questionbank': questionbank, 'topics': topic,
                       'course': course, 'lecturer': lec, 'form': form,
                       'counter': counter, 'questions': questions, 'description': description,
                        'questions_left': questions_left})
    else:
        return HttpResponse("unautherized Access!!It will be reported!!")

@login_required
def edit_practice_details(request, course_code,practice_contest_code):
    extrainfo = ExtraInfo.objects.select_related().get(user=request.user)
    if extrainfo.user_type == 'faculty':
        x = request.POST.get('number')
        practice_contest = Practice.objects.select_related().get(pk=practice_contest_code)

        if x == 'edit1':
            number = request.POST.get('number_of_questions')
            score = int(practice_contest.total_score / practice_contest.number_of_question)
            practice_contest.number_of_question = number
           # practice_contest.total_score = int(number) * score
            practice_contest.save()
        elif x == 'edit2':
            score = request.POST.get('total_score')
            practice_contest.total_score = int(score) * practice_contest.number_of_question
            practice_contest.save()
        return HttpResponse("Done")

    else:
        return HttpResponse("unauthorized Access!!It will be reported!!")

@login_required
def add_questions_to_practice_contest(request, course_code, practice_contest_id):
    extrainfo = ExtraInfo.objects.select_related().get(user=request.user)
    if extrainfo.user_type == 'faculty':
        questions_selected = request.POST.getlist('questions_selected')
        quiz = Quiz.objects.select_related().get(pk=quiz_id)
        for questions in questions_selected:
            question = Question.objects.select_related().get(pk=int(questions))
            PracticeQuestion.objects.create(
                quiz_id=quiz,
                question=question
            )
        return redirect('/ocms/' + course_code + '/edit_quiz/' + quiz_id)

def add_practice_question(request, course_code, practice_contest_code):
    user = request.user
    extrainfo = ExtraInfo.objects.select_related().get(user=user)
    if extrainfo.user_type == "faculty":
        prac_question = PracticeQuestion.objects.select_related().filter(pk=practice_contest_code)
     #   topic = Topics.objects.get(id=request.POST.get('topic'))
        try:
            filename, file_extenstion = os.path.splitext(request.FILES['image'].name)
            image = request.FILES['image']
        #    topic_name = topic.topic_name.replace(" ", "_")[:-2]
            full_path = settings.MEDIA_ROOT + "/online_cms/" + course_code
            full_path = full_path + "/pq/" +practice_contest_code+ "/" + topic_name + "/"
            url = settings.MEDIA_URL + filename
            if not os.path.isdir(full_path):
                cmd = "mkdir " + full_path
                subprocess.call(cmd, shell=True)
            fs = FileSystemStorage(full_path, url)
            fs.save(image.name, image)
            uploaded_file_url = "/media/online_cms/" + course_code
            uploaded_file_url = uploaded_file_url + "/pq/" + practice_contest_code + "/"
            uploaded_file_url = uploaded_file_url + "/" + image.name
        except:
            uploaded_file_url = None

        Question.objects.create(
            prac_question=pq[0],
         #   topic=topic,
            image=uploaded_file_url,
            question=request.POST.get('problem-statement'),
            options1=request.POST.get('option1'),
            options2=request.POST.get('option2'),
            options3=request.POST.get('option3'),
            options4=request.POST.get('option4'),
            options5=request.POST.get('option5'),
            answer=request.POST.get('answer'),

        )
        return redirect('/ocms/' + course_code + '/edit_practice_contest/'+str(pq[0].id))

# @csrf_protect
# @login_required
# def edit_marks(request, course_code):
#     user = request.user
#     extrainfo = ExtraInfo.objects.get(user=user)

#     if extrainfo.user_type == 'faculty':
#         instructor = Curriculum_Instructor.objects.filter(instructor_id=extrainfo)

#         for ins in instructor:
#             if ins.curriculum_id.course_code == course_code:
#                 registered_students = Register.objects.filter(curr_id = ins.curriculum_id.curriculum_id)


#         exam = request.POST.get('examtype')
#         score = request.POST.getlist('enteredmarks')

#         List = list()

#         for i in range(len(registered_students)):
#             m_id = registered_students[i]            
#             s = score[i]

#             # rows = StoreMarks.objects.filter(mid=m_id, exam_type=exam)
#             num = StoreMarks.objects.filter(mid=m_id, exam_type=exam).count()
#             record = StoreMarks.objects.filter(mid=m_id, exam_type=exam).values_list('marks', flat=True)

#             List.append(list(record))

#             if num==0:
#                 StoreMarks.objects.create(
#                     mid=m_id,
#                     exam_type=exam,
#                     marks=s
#                     )
#             else:
#                 StoreMarks.objects.filter(mid=m_id, exam_type=exam).update(marks=s)

#         #print(registered_students)


#         return HttpResponse("Upload successful")  
#         context= {'m_id':m_id,'registered_students': registered_students, 'record':List}
#     return render(request, 'coursemanagement/assessment.html', context)

@csrf_protect
@login_required
def get_exam_data(request,course_code):   #it is store the type of exam helpful in storing the marks
    exam_name = request.POST['exam_name']
    data = serializers.serialize('json', StoreMarks.objects.filter(exam_type=exam_name))
    return HttpResponse(data, content_type='application/json')


#to store the attendance of the student by taking from templates (attendance.html)
@login_required
def submit_attendance(request, course_code):

    user = request.user
    extrainfo = ExtraInfo.objects.select_related().get(user=user)

    if extrainfo.user_type == 'faculty':   #only faculty can change the attendance of the students
        instructor_old = Curriculum_Instructor.objects.select_related().filter(instructor_id=extrainfo)
    for x in instructor_old:
        instructor = x

    if request.method == 'POST':
        form = AttendanceForm(request.POST)     #from the django forms using AttendanceForm

        if form.is_valid():
        #     for item in form.cleaned_data['Present_absent']:
        #         print(item)
            date =  request.POST['date']


            #mark the attendance according to the student roll no.
            all_students = request.POST.getlist('Roll')
            present_students = request.POST.getlist('Present_absent')


            for student in all_students:

                s_id = Student.objects.select_related().get(id = student)
                present = False
                if student in present_students:
                    present = True

                Student_attendance.objects.create(
                        student_id = s_id,
                        instructor_id = instructor,
                        date = date,
                        present = present
                    )


    return HttpResponse("Feedback uploaded")
