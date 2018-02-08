from __future__ import unicode_literals

import collections
import json
import os
import random
import subprocess
from datetime import datetime, time, timedelta

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from applications.academic_information.models import (Course, Instructor,
                                                      Student)
from applications.academic_procedures.models import Register
from applications.globals.models import ExtraInfo

from .forms import QuestionFormObjective, QuizForm
from .helpers import semester
from .models import (Assignment, CourseDocuments, CourseVideo, Forum,
                     ForumReply, Quiz, QuizQuestion, QuizResult, StudentAnswer,
                     StudentAssignment)


def create_thumbnail(course, row, name, ext, attach_str, thumb_time, thumb_size):
    filepath = settings.MEDIA_ROOT + '/online_cms/' + course.course_id + '/vid/' + name + ext
#    video_name = row.video_name[:-4]
    filename = settings.MEDIA_ROOT + '/online_cms/' + course.course_id + '/vid/'
    filename = filename + name.replace(' ', '-') + '-' + attach_str + '.png'
    process = 'ffmpeg -y -i ' + filepath + ' -vframes ' + str(1) + ' -an -s '
    process = process + thumb_size + ' -ss ' + str(thumb_time) + ' ' + filename
    subprocess.call(process, shell=True)


@login_required
def viewcourses(request):
    user = request.user
    extrainfo = ExtraInfo.objects.get(user=user)
    if extrainfo.user_type == 'student':
        student = Student.objects.get(id=extrainfo)
        roll = student.id.id[:4]
        register = Register.objects.filter(student_id=student, semester=semester(roll))
        courses = collections.OrderedDict()
        for reg in register:
            instructor = Instructor.objects.get(course_id=reg.course_id)
            courses[reg] = instructor
        return render(request, 'coursemanagement/coursemanagement1.html',
                      {'courses': courses,
                       'extrainfo': extrainfo})
    else:
        instructor = Instructor.objects.filter(instructor_id=extrainfo)
        return render(request, 'coursemanagement/coursemanagement1.html',
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
        print (course)
        print ("ERROR.................................")
        instructor = Instructor.objects.get(course_id=course[0])
        videos = CourseVideo.objects.filter(course_id=course[0])
        slides = CourseDocuments.objects.filter(course_id=course[0])
        quiz = Quiz.objects.filter(course_id=course)
        marks = []
        quizs = []
        marks_pk = []
        assignment = Assignment.objects.filter(course_id=course[0])
        for q in quiz:
            qs = QuizResult.objects.filter(quiz_id=q, student_id=student)
            qs_pk = QuizResult.objects.filter(
                quiz_id=q, student_id=student).values_list('quiz_id', flat=True)
            if q.end_time > timezone.now():
                quizs.append(q)
            if len(qs) is not 0:
                marks.append(qs[0])
                marks_pk.append(qs_pk[0])
        lec = 0
        comments = Forum.objects.filter(course_id=course).order_by('comment_time')
        answers = collections.OrderedDict()
        for comment in comments:
            fr = ForumReply.objects.filter(forum_reply=comment)
            fr1 = ForumReply.objects.filter(forum_ques=comment)
            if not fr:
                answers[comment] = fr1
        return render(request, 'coursemanagement/viewcourse.html',
                      {'course': course[0],
                       'quizs': marks,
                       'quizs_pk': marks_pk,
                       'fut_quiz': quizs,
                       'videos': videos,
                       'instructor': instructor,
                       'slides': slides,
                       'extrainfo': extrainfo,
                       'answers': answers,
                       'assignment': assignment,
                       'Lecturer': lec})

    else:
        print(extrainfo)
        instructor = Instructor.objects.filter(instructor_id=extrainfo)
        print(instructor)
        for ins in instructor:
            if ins.course_id.course_id == course_code:
                course = ins.course_id
        lec = 1
        print("EOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOo")
        print(course)
        videos = CourseVideo.objects.filter(course_id=course)
        slides = CourseDocuments.objects.filter(course_id=course)
        quiz = Quiz.objects.filter(course_id=course)
        marks = []
        quizs = []
        assignment = Assignment.objects.filter(course_id=course)
        student_assignment = []
        for assi in assignment:
            sa = StudentAssignment.objects.filter(assignment_id=assi)
            student_assignment.append(sa)
        for q in quiz:
            qs = QuizResult.objects.filter(quiz_id=q)
            if q.end_time > timezone.now():
                quizs.append(q)
            if len(qs) is not 0:
                marks.append(qs)
        comments = Forum.objects.filter(course_id=course).order_by('comment_time')
        answers = collections.OrderedDict()
        for comment in comments:
            fr = ForumReply.objects.filter(forum_reply=comment)
            fr1 = ForumReply.objects.filter(forum_ques=comment)
            if not fr:
                answers[comment] = fr1
        return render(request, 'coursemanagement/viewcourse.html',
                      {'instructor': instructor,
                       'extrainfo': extrainfo,
                       'fut_quiz': quizs,
                       'quizs': marks,
                       'videos': videos,
                       'slides': slides,
                       'course': course,
                       'answers': answers,
                       'assignment': assignment,
                       'student_assignment': student_assignment,
                       'Lecturer': lec
                       })


@login_required
def upload_assignment(request, course_code):
    extrainfo = ExtraInfo.objects.get(user=request.user)
    if extrainfo.user_type == "student":
        student = Student.objects.get(id=extrainfo)
#        roll = student.id.id[:4]
#        course = Course.objects.filter(course_id=course_code, sem=semester(roll))
        try:
            doc = request.FILES.get('img')
            assi_name = request.POST.get('assignment_topic')
            name = request.POST.get('name')
            assign = Assignment.objects.get(pk=assi_name)
            filename, file_extenstion = os.path.splitext(request.FILES.get('img').name)
        except:
            return HttpResponse("Please fill each and every field correctly!")
        filename = name
        full_path = settings.MEDIA_ROOT + "/online_cms/" + course_code + "/assi/"
        full_path = full_path + assign.assignment_name + "/" + student.id.id + "/"
        url = settings.MEDIA_URL + filename
        if not os.path.isdir(full_path):
            cmd = "mkdir " + full_path
            subprocess.call(cmd, shell=True)
        fs = FileSystemStorage(full_path, url)
        fs.save(name + file_extenstion, doc)
        uploaded_file_url = "/media/online_cms/" + course_code + "/assi/" + assign.assignment_name
        uploaded_file_url = uploaded_file_url + "/" + student.id.id + "/" + name + file_extenstion
#        index = uploaded_file_url.rfind('/')
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


@login_required
def add_document(request, course_code):
    #    CHECK FOR ERRORS IN UPLOADING
    extrainfo = ExtraInfo.objects.get(user=request.user)
    if extrainfo.user_type == "faculty":
        instructor = Instructor.objects.filter(instructor_id=extrainfo)
        for ins in instructor:
            if ins.course_id.course_id == course_code:
                course = ins.course_id
        try:
            description = request.POST.get('description')
            doc = request.FILES.get('img')
            name = request.POST.get('name')
            filename, file_extenstion = os.path.splitext(request.FILES.get('img').name)
        except:
            return HttpResponse("Please fill each and every field correctly!")
        filename = name
        full_path = settings.MEDIA_ROOT + "/online_cms/" + course_code + "/doc/"
        url = settings.MEDIA_URL + filename + file_extenstion
        if not os.path.isdir(full_path):
            cmd = "mkdir " + full_path
            subprocess.call(cmd, shell=True)
        fs = FileSystemStorage(full_path, url)
        fs.save(filename + file_extenstion, doc)
        uploaded_file_url = "/media/online_cms/" + course_code + "/doc/" + filename
        uploaded_file_url = uploaded_file_url + file_extenstion
#        index = uploaded_file_url.rfind('/')

        CourseDocuments.objects.create(
            course_id=course,
            upload_time=datetime.now(),
            description=description,
            document_url=uploaded_file_url,
            document_name=name+file_extenstion
        )
        return HttpResponse("Upload successful.")
    else:
        return HttpResponse("not found")


@login_required
def add_videos(request, course_code):

    # CHECK FOR ERRORS IN UPLOADING
    extrainfo = ExtraInfo.objects.get(user=request.user)
    if extrainfo.user_type == "faculty":
        instructor = Instructor.objects.filter(instructor_id=extrainfo)
        for ins in instructor:
            if ins.course_id.course_id == course_code:
                course = ins.course_id
        try:
            description = request.POST.get('description')
            vid = request.FILES.get('img')
            name = request.POST.get('name')
            filename, file_extenstion = os.path.splitext(request.FILES.get('img').name)
        except:
            return HttpResponse("Please fill each and every field correctly!")
        filename = name
        full_path = settings.MEDIA_ROOT + "/online_cms/" + course_code + "/vid/"
        url = settings.MEDIA_URL+filename + file_extenstion
        if not os.path.isdir(full_path):
            cmd = "mkdir "+full_path
            subprocess.call(cmd, shell=True)
        fs = FileSystemStorage(full_path, url)
        fs.save(filename+file_extenstion, vid)
        uploaded_file_url = "/media/online_cms/" + course_code + "/vid/" + filename
        uploaded_file_url = uploaded_file_url + file_extenstion
#        index = uploaded_file_url.rfind('/')

        video = CourseVideo.objects.create(
            course_id=course,
            upload_time=datetime.now(),
            description=description,
            video_url=uploaded_file_url[:-4],
            video_name=name
        )
        create_thumbnail(course, video, name, file_extenstion, 'Big', 1, '700:500')
        create_thumbnail(course, video, name, file_extenstion, 'Small', 1, '170:127')
        return HttpResponse("Upload successful.")
    else:
        return HttpResponse("not found")


@login_required
def forum(request, course_code):
    # take care of sem
    extrainfo = ExtraInfo.objects.get(user=request.user)
    if extrainfo.user_type == "student":
        student = Student.objects.get(id=extrainfo)
        roll = student.id.id[:4]
        course = Course.objects.get(course_id=course_code, sem=semester(roll))
    else:
        instructor = Instructor.objects.filter(instructor_id=extrainfo)
        for ins in instructor:
            if ins.course_id.course_id == course_code:
                course = ins.course_id
    comments = Forum.objects.filter(course_id=course).order_by('comment_time')
    instructor = Instructor.objects.get(course_id=course)
    if instructor.instructor_id.user.pk == request.user.pk:
        lec = 1
    else:
        lec = 0
#    question = {}
    answers = collections.OrderedDict()
    for comment in comments:
        fr = ForumReply.objects.filter(forum_reply=comment)
        fr1 = ForumReply.objects.filter(forum_ques=comment)
        if not fr:
            answers[comment] = fr1
    context = {'course': course, 'answers': answers, 'Lecturer': lec}
    return render(request, 'online_cms/forum.html', context)


@login_required
def ajax_reply(request, course_code):
    extrainfo = ExtraInfo.objects.get(user=request.user)
    if extrainfo.user_type == "student":
        student = Student.objects.get(id=extrainfo)
        roll = student.id.id[:4]
        course = Course.objects.get(course_id=course_code, sem=semester(roll))
    else:
        instructor = Instructor.objects.filter(instructor_id=extrainfo)
        for ins in instructor:
            if ins.course_id.course_id == course_code:
                course = ins.course_id
    ex = ExtraInfo.objects.get(user=request.user)
    f = Forum(
        course_id=course,
        commenter_id=ex,
        comment=request.POST.get('reply')
    )
    f.save()
    ques = Forum.objects.get(pk=request.POST.get('question'))
    fr = ForumReply(
        forum_ques=ques,
        forum_reply=f
    )
    fr.save()
    name = request.user.first_name + " " + request.user.last_name
    time = f.comment_time.strftime('%b. %d, %Y, %I:%M %P')
    data = {'pk': f.pk, 'reply': f.comment, 'replier': name, 'time': time}
    return HttpResponse(json.dumps(data), content_type='application/json')


@login_required
def ajax_new(request, course_code):
    extrainfo = ExtraInfo.objects.get(user=request.user)
    if extrainfo.user_type == "student":
        student = Student.objects.get(id=extrainfo)
        roll = student.id.id[:4]
        course = Course.objects.get(course_id=course_code, sem=semester(roll))
    else:
        instructor = Instructor.objects.filter(instructor_id=extrainfo)
        for ins in instructor:
            if ins.course_id.course_id == course_code:
                course = ins.course_id
    ex = ExtraInfo.objects.get(user=request.user)
    f = Forum(
        course_id=course,
        commenter_id=ex,
        comment=request.POST.get('question')
    )
    f.save()
    name = request.user.first_name + " " + request.user.last_name
    time = f.comment_time.strftime('%b. %d, %Y, %I:%M %P')

    data = {'pk': f.pk, 'question': f.comment, 'replier': f.commenter_id.user.username,
            'time': time, 'name': name}
    print(f.pk)
    return HttpResponse(json.dumps(data), content_type='application/json')


@login_required
def ajax_remove(request, course_code):
    f = Forum.objects.get(
        pk=request.POST.get('question')
    )
    fr = ForumReply.objects.filter(
        forum_reply=f
    )

    if not fr:
        fr1 = ForumReply.objects.filter(
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
def add_assignment(request, course_code):
    #    CHECK FOR ERRORS IN UPLOADING
    extrainfo = ExtraInfo.objects.get(user=request.user)
    if extrainfo.user_type == "faculty":
        instructor = Instructor.objects.filter(instructor_id=extrainfo)
        for ins in instructor:
            if ins.course_id.course_id == course_code:
                course = ins.course_id
#        description = request.POST.get('description')
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
        uploaded_file_url = "/media/online_cms/" + course_code + "/assi/"
        uploaded_file_url = uploaded_file_url + name + "/" + name + file_extenstion
        name = request.POST.get('name')
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
def quiz(request, quiz_id):
    user = request.user
    extrainfo = ExtraInfo.objects.get(user=user)
    if extrainfo.user_type == 'student':
        # student = Student.objects.get(id=extrainfo)
        quiz = Quiz.objects.get(pk=quiz_id)
        length = quiz.number_of_question
        ques_pk = QuizQuestion.objects.filter(quiz_id=quiz).values_list('pk', flat=True)
        random_ques_pk = random.sample(list(ques_pk), length)
        shuffed_questions = []
        for x in random_ques_pk:
            shuffed_questions.append(QuizQuestion.objects.get(pk=x))
        end = quiz.end_time
        now = timezone.now() + timedelta(hours=5.5)
        diff = end-now
        days, seconds = diff.days, diff.seconds
        hours = days * 24 + seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return render(request, 'coursemanagement/quiz.html',
                      {'contest': quiz, 'ques': shuffed_questions,
                       'days': days, 'hours': hours, 'minutes': minutes, 'seconds': seconds})
    else:
        return HttpResponse("unautherized Access!!It will be reported!!")


@login_required
def ajax_q(request, quiz_code):
    user = request.user
    extrainfo = ExtraInfo.objects.get(user=user)
    student = Student.objects.get(id=extrainfo)
    q = request.POST.get('question')
    ques = QuizQuestion.objects.get(pk=q)
    quiz_id = Quiz.objects.get(pk=ques.quiz_id.pk)
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
    ei = ExtraInfo.objects.get(user=request.user)
    student = Student.objects.get(id=ei)
    quiz = Quiz.objects.get(pk=quiz_code)
    stu_ans = StudentAnswer.objects.filter(student_id=student, quiz_id=quiz)
    score = 0
    for s_ans in stu_ans:
        if s_ans.question_id.answer == s_ans.choice:
            score += s_ans.question_id.marks
        else:
            score -= (s_ans.quiz_id.negative_marks * s_ans.question_id.marks)
    # quiz_res=QuizResult.objects.filter(quiz_id=quiz,student_id=request.user)
    quiz_res = QuizResult(
        quiz_id=quiz,
        student_id=student,
        score=score,
        finished=True
    )
    quiz_res.save()
    data = {'message': 'you have submitted, cant enter again now', 'score': quiz_res.score}
    return HttpResponse(json.dumps(data), content_type="application/json")

#@login_required
#def create_prac_quiz(request, course_code):
#    extrainfo = ExtraInfo.objects.get(user=request.user)
#    print("tatti")
#    if extrainfo.user_type == 'faculty':
#        instructor = Instructor.objects.filter(instructor_id=extrainfo)
#        for ins in instructor:
#            if ins.course_id.course_id == course_code:
#                course = ins.course_id
#        form = PracticeQuizForm(request.POST or None)
#        errors = None
#        if form.is_valid():
#            total_score = form.cleaned_data[
#                'number_of_questions'] * form.cleaned_data[
#                'per_question_score']
#            description = form.cleaned_data['description']
#            obj = Practice.objects.create(
#                course_id=course,
#                prac_quiz_name=form.cleaned_data['name'],
#                description=description,
#                number_of_question=form.cleaned_data['number_of_questions'],
#                negative_marks=form.cleaned_data['negative_marks'],
#                total_score=total_score
#                            )
#            # print "Done"
#            return redirect('/ocms/' + course_code + '/edit_prac_quiz/' + str(obj.pk))
#            '''except:
#                return HttpResponse('Unexpected Error')'''
#        if form.errors:
#            errors = form.errors
#        print("ASDAS")
#        return render(request, 'coursemanagement/create_practice_contest.html',
#                      {'form': form, 'errors': errors})
#
#    else:
#        return HttpResponse("unautherized Access!!It will be reported!!")

@login_required
def create_quiz(request, course_code):
    extrainfo = ExtraInfo.objects.get(user=request.user)

    if extrainfo.user_type == 'faculty':
        instructor = Instructor.objects.filter(instructor_id=extrainfo)
        for ins in instructor:
            if ins.course_id.course_id == course_code:
                course = ins.course_id
        form = QuizForm(request.POST or None)
        errors = None
        if form.is_valid():
            st_time = form.cleaned_data['starttime']
            k1 = st_time.hour
            k2 = st_time.minute
            k3 = st_time.second
            start_date_time = datetime.combine(form.cleaned_data['startdate'], time(k1, k2, k3))
            st_time = form.cleaned_data['endtime']
            k1 = st_time.hour
            k2 = st_time.minute
            k3 = st_time.second
            end_date_time = datetime.combine(form.cleaned_data['enddate'], time(k1, k2, k3))
            duration = end_date_time - start_date_time
            days, seconds = duration.days, duration.seconds
            hours = days * 24 + seconds // 3600
            minutes = (seconds % 3600) // 60
            total_score = form.cleaned_data[
                'number_of_questions'] * form.cleaned_data[
                'per_question_score']
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
                total_score=total_score
                            )
            # print "Done"
            return redirect('/ocms/' + course_code + '/edit_quiz/' + str(obj.pk))
            '''except:
                return HttpResponse('Unexpected Error')'''
        if form.errors:
            errors = form.errors
        return render(request, 'coursemanagement/createcontest.html',
                      {'form': form, 'errors': errors})

    else:
        return HttpResponse("unautherized Access!!It will be reported!!")


@login_required
def edit_quiz_details(request, course_code, quiz_code):
    extrainfo = ExtraInfo.objects.get(user=request.user)
    if extrainfo.user_type == 'faculty':
        x = request.POST.get('number')
        quiz = Quiz.objects.get(pk=quiz_code)
        if x == 'edit1':
            st_time = request.POST.get('starttime')
            st_date = request.POST.get('startdate_month') + " " + request.POST.get('startdate_day')
            st_date = st_date + " " + request.POST.get('startdate_year')
            string = str(st_date) + " " + str(st_time)
            datetime_object = datetime.strptime(string, '%m %d %Y %H:%M')
            quiz.start_time = datetime_object
            quiz.save()
        elif x == 'edit2':
            st_time = request.POST.get('endtime')
            st_date = request.POST.get('enddate_month') + " " + request.POST.get('enddate_day')
            st_date = st_date + " " + request.POST.get('enddate_year')
            string = str(st_date) + " " + str(st_time)
            datetime_object = datetime.strptime(string, '%m %d %Y %H:%M')
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

#@login_required
#def edit_prac_quiz(request, course_code, quiz_code):
#    extrainfo = ExtraInfo.objects.get(user=request.user)
#    if extrainfo.user_type == 'faculty':
#        instructor = Instructor.objects.filter(instructor_id=extrainfo)
#        for ins in instructor:
#            if ins.course_id.course_id == course_code:
#                course = ins.course_id
#        # errors = None
#        practice = Practice.objects.get(pk=quiz_code)
#        if request.method == 'POST':
#            print (practice)
#            form = QuestionFormObjective(request.POST, request.FILES)
#            if(form.is_valid()):
#
#
#                options1 = form.cleaned_data['option1']
#                options2 = form.cleaned_data['option2']
#                options3 = form.cleaned_data['option3']
#                options4 = form.cleaned_data['option4']
#                options5 = form.cleaned_data['option5']
#                question = form.cleaned_data['problem_statement']
#                marks = form.cleaned_data['score']
#                answer = form.cleaned_data['answer']
#                try:
#                    filename, file_extenstion = os.path.splitext(request.FILES['image'].name)
#                    image = request.FILES['image']
#                    full_path = settings.MEDIA_ROOT + "/online_cms/" + course_code
#                    full_path = full_path + "/practice_quiz/" + quiz_code + "/"
#                    url = settings.MEDIA_URL + filename
#                    if not os.path.isdir(full_path):
#                        cmd = "mkdir " + full_path
#                        subprocess.call(cmd, shell=True)
#                    fs = FileSystemStorage(full_path, url)
#                    fs.save(image.name, image)
#                    uploaded_file_url = "/media/online_cms/" + course_code
#                    uploaded_file_url = uploaded_file_url + "/practice_quiz/" + quiz_code + "/" + image.name
#                    PracticeQuestion.objects.create(prac_quiz_id=practice, image=uploaded_file_url,
#                                            question=question,
#                                            answer=answer,
#                                            options1=options1, options2=options2,
#                                            options3=options3, options4=options4,
#                                            options5=options5)
#                except:
#                    PracticeQuestion.objects.create(prac_quiz_id=quiz,
#                                            question=question,
#                                            answer=answer,
#                                            options1=options1, options2=options2,
#                                            options3=options3, options4=options4,
#                                            options5=options5)
#
#                practice.total_score += form.cleaned_data['score']
#                practice.save()
#                PracticeQuestion.objects.filter(prac_quiz_id=quiz)
#                # print obj3
#                # return render(request,'/quiz/'+'edit_contest/'+str(obj.pk),
##                {'form1': form1 ,'form2':form2,'obj':obj3})
#                return redirect('/ocms/' + course_code + '/edit_prac_quiz/' + str(quiz.pk))
#            elif(form.errors):
#                form.errors
#        else:
#            form1 = QuizForm()
#            form = QuestionFormObjective()
#            questions = PracticeQuestion.objects.filter(prac_quiz_id=practice)
#            description = Practice.description
#            print(description,'asdasd')
#            return render(request, 'coursemanagement/edit_practice_contest.html',
#                          {'form1': form1, 'form': form, 'details': practice,
#                           'course': course, 'questions': questions,
#                           'description': description})
#    else:
#        return HttpResponse("unautherized Access!!It will be reported!!")

@login_required
def edit_quiz(request, course_code, quiz_code):
    extrainfo = ExtraInfo.objects.get(user=request.user)
    if extrainfo.user_type == 'faculty':
        instructor = Instructor.objects.filter(instructor_id=extrainfo)
        for ins in instructor:
            if ins.course_id.course_id == course_code:
                course = ins.course_id
        # errors = None
        quiz = Quiz.objects.get(pk=quiz_code)
        if request.method == 'POST':
            form = QuestionFormObjective(request.POST, request.FILES)
            if(form.is_valid()):


                options1 = form.cleaned_data['option1']
                options2 = form.cleaned_data['option2']
                options3 = form.cleaned_data['option3']
                options4 = form.cleaned_data['option4']
                options5 = form.cleaned_data['option5']
                question = form.cleaned_data['problem_statement']
                marks = form.cleaned_data['score']
                answer = form.cleaned_data['answer']
                try:
                    filename, file_extenstion = os.path.splitext(request.FILES['image'].name)
                    image = request.FILES['image']
                    full_path = settings.MEDIA_ROOT + "/online_cms/" + course_code
                    full_path = full_path + "/quiz/" + quiz_code + "/"
                    url = settings.MEDIA_URL + filename
                    if not os.path.isdir(full_path):
                        cmd = "mkdir " + full_path
                        subprocess.call(cmd, shell=True)
                    fs = FileSystemStorage(full_path, url)
                    fs.save(image.name, image)
                    uploaded_file_url = "/media/online_cms/" + course_code
                    uploaded_file_url = uploaded_file_url + "/quiz/" + quiz_code + "/" + image.name
                    QuizQuestion.objects.create(quiz_id=quiz, image=uploaded_file_url,
                                            question=question,
                                            answer=answer,
                                            options1=options1, options2=options2,
                                            options3=options3, options4=options4,
                                            options5=options5)
                except:
                    QuizQuestion.objects.create(quiz_id=quiz,
                                            question=question,
                                            answer=answer,
                                            options1=options1, options2=options2,
                                            options3=options3, options4=options4,
                                            options5=options5)

                # print uploaded_file_url


                # print "HOGAYA"
                quiz.total_score += form.cleaned_data['score']
                quiz.save()
                QuizQuestion.objects.filter(quiz_id=quiz)
                # print obj3
                # return render(request,'/quiz/'+'edit_contest/'+str(obj.pk),
#                {'form1': form1 ,'form2':form2,'obj':obj3})
                return redirect('/ocms/' + course_code + '/edit_quiz/' + str(quiz.pk))
            elif(form.errors):
                form.errors
        else:
            form1 = QuizForm()
            form = QuestionFormObjective()
            questions = QuizQuestion.objects.filter(quiz_id=quiz)
            description = quiz.description
            description = [z.encode('ascii', 'ignore') for z in description.split('/')]
            rules = quiz.rules
            rules = [z.encode('ascii', 'ignore') for z in rules.split('/')]
            return render(request, 'coursemanagement/editcontest.html',
                          {'form1': form1, 'form': form, 'details': quiz,
                           'course': course, 'questions': questions,
                           'description': description, 'rules': rules})
    else:
        return HttpResponse("unautherized Access!!It will be reported!!")


@login_required
def remove_quiz(request, course_code):
    quiz = Quiz.objects.get(pk=request.POST.get('pk'))
    quizQuestion = QuizQuestion.objects.filter(quiz_id=quiz)
    for q in quizQuestion:
        q.delete()
    quiz.delete()
    return HttpResponse("Done")


@login_required
def ajax_assess(request, course_code):
    sa = StudentAssignment.objects.get(pk=request.POST.get('pk'))
#    print(sa,"qwerty")
    sa.score = request.POST.get('marks')
    sa.save()
#    print(sa,"qwerty")
    return HttpResponse("Marks uploaded")


@login_required
def ajax_feedback(request, course_code):
    sa = StudentAssignment.objects.get(pk=request.POST.get('pk'))
#    print(sa,"qwerty")
    sa.feedback = request.POST.get('feedback')
    sa.save()
#    print(sa,"qwerty")
    return HttpResponse("Feedback uploaded")
