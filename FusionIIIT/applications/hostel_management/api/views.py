from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes,authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from applications.academic_information.models import Student
from . import serializers
from applications.hostel_management.models import (Hall, HallCaretaker, HallWarden, HallRoom, HostelManagementConstants,
                                                   HostelNoticeBoard, HostelStudentAttendence, GuestRoomBooking,
                                                    StaffSchedule, WorkerReport)
@api_view(["GET"])
def get_notice(request):
    notices = serializers.Notice_serializer(HostelNoticeBoard.objects.all()).data()
    resp = {
        'hostel_notices': notices
    }
    return Response(data=resp, status=status.HTTP_200_OK)

@api_view(["GET"])
def get_hall(request):
    halls = serializers.Hall_serializer(Hall.objects.all()).data()
    resp = {
        'halls': halls
    }
    return Response(data=resp, status=status.HTTP_200_OK)

@api_view(["GET"])
def get_student(request):
    students = serializers.Student_serializer(Student.objects.all()).data()
    resp = {
        'students': students
    }
    return Response(data=resp, status=status.HTTP_200_OK)

@api_view(["POST"])
def book_guest_room(request):
    pass

@api_view(["PUT"])
def update_guest_room_booking(request):
    pass
