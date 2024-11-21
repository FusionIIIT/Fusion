from django.conf import settings
from django.shortcuts import render
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from .serializers import *
from applications.academic_information.models import Student
from applications.programme_curriculum.models import Course as Courses, CourseInstructor
from applications.academic_procedures.models import course_registration
from applications.globals.models import ExtraInfo


@api_view(['GET'])
def courseview(request):
    user = request.user
    extrainfo = ExtraInfo.objects.select_related().get(user=user)
    
    if extrainfo.user_type == 'student':
        student = Student.objects.select_related('id').get(id=extrainfo)
        register = course_registration.objects.select_related().filter(student_id=student)
        
        courses_info = [Courses.objects.select_related().get(pk=reg.course_id.id) for reg in register]
        course_serializer = CourseRegistrationSerializer(courses_info, many=True)
        
        data = {"courses": course_serializer.data}
        return Response(data, status=status.HTTP_200_OK)
        
    elif extrainfo.user_type == 'faculty':
        instructor = CourseInstructor.objects.select_related('course_id').filter(instructor_id=extrainfo)
        courses_info = [Courses.objects.select_related().get(pk=ins.course_id.id) for ins in instructor]
        
        course_serializer = CourseRegistrationSerializer(courses_info, many=True)
        data = {"courses": course_serializer.data}
        return Response(data, status=status.HTTP_200_OK)
    
    else:
        return Response({"error": "error occurred"})


@api_view(['GET'])
def course(request, course_code, version):
    user = request.user
    extrainfo = ExtraInfo.objects.select_related().get(user=user)
    
    if extrainfo.user_type == 'student':
        student = Student.objects.select_related('id').get(id=extrainfo)
        course = Courses.objects.select_related().get(code=course_code, version=version)
        instructor = CourseInstructor.objects.select_related().get(course_id=course, batch_id=student.batch_id)

        course_serializer = CoursesSerializer(course)
        instructor_serializer = CourseInstructorSerializer(instructor)

        modules = Modules.objects.select_related().filter(course_id=course)
        slides = CourseDocuments.objects.select_related().filter(course_id=course)
        
        modules_with_slides = {
            m: [slide for slide in slides if slide.module_id.id == m.id] or 0 
            for m in modules
        }
        
        attendance_records = Attendance.objects.select_related().filter(student_id=student, instructor_id=instructor)
        total_attendance = len(attendance_records)
        count = sum(1 for record in attendance_records if record.present)
        present_attendance = {record.date: int(record.present) for record in attendance_records}
        attendance_percent = round((count / total_attendance) * 100, 2) if total_attendance else 0
        
        attendance_file = AttendanceFiles.objects.select_related().filter(course_id=course)
        
        comments = Forum.objects.select_related().filter(course_id=course).order_by('comment_time')
        answers = {
            comment: ForumReply.objects.select_related().filter(forum_ques=comment)
            for comment in comments
        }
        
        data = {
            'course': course_serializer.data,
            'instructor': instructor_serializer.data,
            'modules': ModulesSerializer(modules, many=True).data,
            'slides': CourseDocumentsSerializer(slides, many=True).data,
            'attendance': AttendanceSerializer(attendance_records, many=True).data,
            'present_attendance': present_attendance,
            'attendance_percent': attendance_percent,
            'attendance_file': AttendanceFilesSerializer(attendance_file, many=True).data,
        }
        
        return Response(data, status=status.HTTP_200_OK)
    
    else:
        instructor = CourseInstructor.objects.select_related('course_id').filter(instructor_id=extrainfo)
        
        for ins in instructor:
            if ins.course_id.code == course_code and ins.course_id.version == Decimal(version):
                registered_students = course_registration.objects.select_related('student_id').filter(course_id=ins.course_id)
                students_info = [Student.objects.select_related().get(pk=stu.student_id.id) for stu in registered_students]
                
                topics = Topics.objects.select_related().filter(course_id=ins.course_id)
                attendance_records = {
                    x.student_id.id.id: {
                        'count': sum(1 for a in Attendance.objects.select_related().filter(student_id=x.student_id, instructor_id=ins) if a.present),
                        'attendance_percent': round(
                            (sum(1 for a in Attendance.objects.select_related().filter(student_id=x.student_id, instructor_id=ins) if a.present)
                             / len(Attendance.objects.select_related().filter(student_id=x.student_id, instructor_id=ins))) * 100,
                            2
                        ) if len(Attendance.objects.select_related().filter(student_id=x.student_id, instructor_id=ins)) else 0
                    }
                    for x in registered_students
                }

                modules = Modules.objects.select_related().filter(course_id=ins.course_id)
                slides = CourseDocuments.objects.select_related().filter(course_id=ins.course_id)

                gradingscheme = GradingScheme.objects.select_related().filter(course_id=ins.course_id)
                topics_serializer = TopicsSerializer(topics, many=True)
                
                data = {
                    "students": StudentSerializer(students_info, many=True).data,
                    "topics": topics_serializer.data,
                    "present_att": attendance_records,
                    "modules": ModulesSerializer(modules, many=True).data,
                    "slides": CourseDocumentsSerializer(slides, many=True).data,
                    "grading_scheme": GradingSchemeSerializer(gradingscheme, many=True).data,
                }
                
                return Response(data, status=status.HTTP_200_OK)
