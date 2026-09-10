from rest_framework import serializers


class CourseStudentCountSerializer(serializers.Serializer):
    """Serializer for course student count data"""
    academic_year = serializers.CharField()
    semester_type = serializers.CharField()
    code = serializers.CharField()
    name = serializers.CharField()
    credit = serializers.IntegerField()
    student_count = serializers.IntegerField()


class StudentCourseDetailSerializer(serializers.Serializer):
    """Serializer for student course detail data"""
    roll_no = serializers.CharField()
    course_code = serializers.CharField()
    course_name = serializers.CharField()
    credit = serializers.IntegerField()
    registration_type = serializers.CharField()
