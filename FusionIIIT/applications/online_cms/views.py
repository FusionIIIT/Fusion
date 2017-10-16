from __future__ import unicode_literals

import os
import subprocess
from datetime import datetime

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from django.shortcuts import render

from applications.academic_information.models import (Course, Instructor,
                                                      Student)
from applications.academic_procedures.models import Register
from applications.globals.models import ExtraInfo

from .forms import AddDocuments, AddVideos
from .helpers import semester
from .models import CourseDocuments, CourseVideo


@login_required
def viewcourses(request):
    user = request.user
    extrainfo = ExtraInfo.objects.get(user=user)
    if extrainfo.user_type == 'student':
        student = Student.objects.get(id=extrainfo)

        roll = student.id.id[:4]
        register = Register.objects.filter(student_id=student, semester=semester(roll))
        return render(request, 'online_cms/viewcourses.html',
                      {'register': register,
                       'extrainfo': extrainfo})
    else:
        instructor = Instructor.objects.filter(instructor_id=extrainfo)
        return render(request, 'online_cms/viewcourses.html',
                      {'instructor': instructor,
                       'extrainfo': extrainfo})


@login_required
def course(request, course_code):
    user = request.user
    extrainfo = ExtraInfo.objects.get(user=user)

    if extrainfo.user_type == 'student':
        student = Student.objects.get(id=extrainfo)
        roll = student.id.id[:4]
        course = Course.objects.filter(course_id=course_code, sem=semester(roll))
        instructor = Instructor.objects.get(course_id=course[0])
        return render(request, 'online_cms/course.html',
                      {'course': course[0],
                       'instructor': instructor,
                       'extrainfo': extrainfo})

    else:
        instructor = Instructor.objects.filter(instructor_id=extrainfo)
        for ins in instructor:
            if ins.course_id.course_id is course_code:
                course = ins.course_id
        return render(request, 'online_cms/course.html',
                      {'instructor': instructor,
                       'extrainfo': extrainfo})


@login_required
def add_document(request, course_code):
    #    CHECK FOR ERRORS IN UPLOADING
    extrainfo = ExtraInfo.objects.get(user=request.user)
    instructor = Instructor.objects.filter(instructor_id=extrainfo)
    for ins in instructor:
        if ins.course_id.course_id == course_code:
            course = ins.course_id

    if request.method == 'POST':
        form = AddDocuments(request.POST, request.FILES)
        if form.is_valid():
            description = request.POST.get('description')
            doc = request.FILES['doc']
            filename, file_extenstion = os.path.splitext(request.FILES['doc'].name)
            full_path = settings.MEDIA_ROOT+"/online_cms/"+course_code+"/doc/"
            url = settings.MEDIA_URL+filename
            if not os.path.isdir(full_path):
                cmd = "mkdir "+full_path
                subprocess.call(cmd, shell=True)
            fs = FileSystemStorage(full_path, url)
            fs.save(doc.name, doc)
            uploaded_file_url = "/media/online_cms/"+course_code+"/doc/"+doc.name
            index = uploaded_file_url.rfind('/')
            name = uploaded_file_url[index+1:]
            CourseDocuments.objects.create(
                course_id=course,
                upload_time=datetime.now(),
                description=description,
                document_url=uploaded_file_url,
                document_name=name
            )
            return HttpResponse("Upload successful.")
        elif form.errors:
            form.errors
    else:
        form = AddDocuments()
        document = CourseDocuments.objects.filter(course_id=course)
        return render(request, 'online_cms/add_doc.html',
                      {'form': form,
                       'document': document,
                       'extrainfo': extrainfo})


@login_required
def add_videos(request, course_code):

    # CHECK FOR ERRORS IN UPLOADING
    extrainfo = ExtraInfo.objects.get(user=request.user)
    instructor = Instructor.objects.filter(instructor_id=extrainfo)
    for ins in instructor:
        if ins.course_id.course_id == course_code:
            course = ins.course_id

    if request.method == 'POST':
        form = AddVideos(request.POST, request.FILES)
        if form.is_valid():
            description = request.POST.get('description')
            vid = request.FILES['vid']
            filename, file_extenstion = os.path.splitext(request.FILES['vid'].name)
            full_path = settings.MEDIA_ROOT+"/online_cms/"+course_code+"/vid/"
            url = settings.MEDIA_URL+filename
            if not os.path.isdir(full_path):
                cmd = "mkdir "+full_path
                subprocess.call(cmd, shell=True)
            fs = FileSystemStorage(full_path, url)
            fs.save(vid.name, vid)
            uploaded_file_url = "/media/online_cms/"+course_code+"/vid/"+vid.name
            index = uploaded_file_url.rfind('/')
            name = uploaded_file_url[index+1:]
            CourseVideo.objects.create(
                course_id=course,
                upload_time=datetime.now(),
                description=description,
                video_url=uploaded_file_url,
                video_name=name
            )
            return HttpResponse("Upload successful.")
        elif form.errors:
            form.errors
    else:
        form = AddVideos()
        video = CourseVideo.objects.filter(course_id=course)
        return render(request, 'online_cms/add_vid.html',
                      {'form': form,
                       'video': video,
                       'extrainfo': extrainfo})
