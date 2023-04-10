from rest_framework import serializers
from applications.hostel_management.models import Hall, HallCaretaker, HallWarden, HallRoom, HostelManagementConstants, HostelNoticeBoard, HostelStudentAttendence, GuestRoomBooking, StaffSchedule, WorkerReport
from applications.globals.models import ExtraInfo, Staff, Faculty
from applications.academic_information.models import Student

class Staff_editScheduleSerializer(serializers.Serializer):
    class Meta:
        model = StaffSchedule
        fields = "__all__"

class Notice_serializer(serializers.Serializer):
    class Meta:
        model = HostelNoticeBoard
        fields = "__all__"
        
class Hall_serializer(serializers.Serializer):
    class Meta:
        model = Hall
        fields = "__all__"

class Student_serializer(serializers.Serializer):
    class Meta:
        model = Student
        fields = "__all__" 