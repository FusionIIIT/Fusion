from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework import serializers
from notifications.models import Notification
from applications.academic_information.models import Student, Course, Curriculum, Curriculum_Instructor, Student_attendance, Meeting, Calendar, Holiday, Grades, Spi, Timetable, Exam_timetable
from applications.globals.models import ExtraInfo,User

class StudentSerializers(serializers.ModelSerializer):
    class Meta:
        model=Student
        fields=('__all__')

class CourseSerializers(serializers.ModelSerializer):
    class Meta:
        model=Course
        fields=('__all__')

class CurriculumSerializers(serializers.ModelSerializer):
    class Meta:
        model=Curriculum
        fields=('__all__')

class Curriculum_InstructorSerializers(serializers.ModelSerializer):
    class Meta:
        model=Curriculum_Instructor
        fields=('__all__')

class Student_attendanceSerializers(serializers.ModelSerializer):
    class Meta:
        model=Student_attendance
        fields=('__all__')

class MeetingSerializers(serializers.ModelSerializer):
    class Meta:
        model=Meeting
        fields=('__all__')

class CalendarSerializers(serializers.ModelSerializer):
    class Meta:
        model=Calendar
        fields=('__all__')

class HolidaySerializers(serializers.ModelSerializer):
    class Meta:
        model=Holiday
        fields=('__all__')

class GradesSerializers(serializers.ModelSerializer):
    class Meta:
        model=Grades
        fields=('__all__')

class SpiSerializers(serializers.ModelSerializer):
    class Meta:
        model=Spi
        fields=('__all__')

class TimetableSerializers(serializers.ModelSerializer):
    class Meta:
        model=Timetable
        fields=('__all__')

class Exam_timetableSerializers(serializers.ModelSerializer):
    class Meta:
        model=Exam_timetable
        fields=('__all__')

