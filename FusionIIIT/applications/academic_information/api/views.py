import json
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from applications.academic_information.utils import allocate, check_for_registration_complete
from applications.globals.models import (HoldsDesignation,Designation)
from django.shortcuts import get_object_or_404
from django.forms.models import model_to_dict
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes,authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from applications.globals.models import User,ExtraInfo
from applications.academic_information.models import Student, Course, Curriculum, Curriculum_Instructor, Student_attendance, Meeting, Calendar, Holiday, Grades, Spi, Timetable, Exam_timetable
from . import serializers
from rest_framework.generics import ListCreateAPIView
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def student_api(request):

    if request.method == 'GET':
        student = Student.objects.all()
        student_serialized = serializers.StudentSerializers(student,many=True).data
        resp = {
            'students' : student_serialized,
        }
        return Response(data=resp,status=status.HTTP_200_OK)


@api_view(['GET'])
# @permission_classes([IsAuthenticated])
# @authentication_classes([TokenAuthentication])
def course_api(request):

    if request.method == 'GET':
        course = Course.objects.all()
        course_serialized = serializers.CourseSerializer(course,many=True).data
        resp = {
            'courses' : course_serialized,
        }
        return Response(data=resp,status=status.HTTP_200_OK)
 


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def curriculum_api(request):

    if request.method == 'GET':
        curriculum = Curriculum.objects.all()
        curriculum_serialized = serializers.CurriculumSerializer(curriculum,many=True).data
        resp = {
            'curriculum' : curriculum_serialized,
        }
        return Response(data=resp,status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def meeting_api(request):

    if request.method == 'GET':
        meeting = Meeting.objects.all()
        meeting_serialized = serializers.MeetingSerializers(meeting,many=True).data
        resp = {
            'meeting' : meeting_serialized,
        }
        return Response(data=resp,status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def calendar_api(request):

    if request.method == 'GET':
        calendar = Calendar.objects.all()
        calendar_serialized = serializers.CalendarSerializers(calendar,many=True).data
        resp = {
            'calendar' :calendar_serialized,
        }
        return Response(data=resp,status=status.HTTP_200_OK)
    
class ListCalendarView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes=[TokenAuthentication]
    serializer_class = serializers.CalendarSerializers
    queryset = Calendar.objects.all()

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def update_calendar(request):
    if request.method == "PUT":
        id = request.data.get("id")
        instance = Calendar.objects.get(pk = id)
        instance.from_date = request.data.get("from_date")
        instance.to_date = request.data.get("to_date")
        instance.description = request.data.get("description")
        instance.save()
        
        return Response({"message": "Updated successfully!"})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def add_calendar(request):
    if request.method == "POST":
        from_date = request.data.get("from_date")
        to_date = request.data.get("to_date")
        description = request.data.get("description")
        Calendar.objects.create(from_date=from_date, to_date=to_date, description=description)
        
        return Response({"message": "Created successfully!"})
    
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def delete_calendar(request):
    id = request.data.get("id")  # Get the ID from request body

    try:
        instance = Calendar.objects.get(pk=id)
        instance.delete()
        return Response({"message": "Deleted successfully!"}, status=200)
    except Calendar.DoesNotExist:
        return Response({"error": "Calendar entry not found"}, status=404)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def holiday_api(request):

    if request.method == 'GET':
        holiday = Holiday.objects.all()
        holiday_serialized = serializers.HolidaySerializers(holiday,many=True).data
        resp = {
            'holiday' : holiday_serialized,
        }
        return Response(data=resp,status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def timetable_api(request):

    if request.method == 'GET':
        timetable = Timetable.objects.all()
        timetable_serialized = serializers.TimetableSerializers(timetable,many=True).data
        resp = {
            'timetable' : timetable_serialized,
        }
        return Response(data=resp,status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def exam_timetable_api(request):

    if request.method == 'GET':
        exam_timetable = Exam_timetable.objects.all()
        exam_timetable_serialized = serializers.Exam_timetableSerializers(exam_timetable,many=True).data
        resp = {
            'exam_timetable' : exam_timetable_serialized,
        }
        return Response(data=resp,status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def curriculum_instructor_api(request):

    if request.method == 'GET':
        curriculum_instructor = Curriculum_Instructor.objects.all()
        curriculum_instructor_serialized = serializers.CurriculumInstructorSerializer(curriculum_instructor,many=True).data
        resp = {
            'curriculum_instructor' : curriculum_instructor_serialized,
        }
        return Response(data=resp,status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def student_attendance_api(request):

    if request.method == 'GET':
        student_attendance = Student_attendance.objects.all()
        student_attendance_serialized = serializers.Student_attendanceSerializers(student_attendance,many=True).data
        resp = {
            'student_attendance' : student_attendance_serialized,
        }
        return Response(data=resp,status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def grades_api(request):

    if request.method == 'GET':
        grades = Grades.objects.all()
        grades_serialized = serializers.GradesSerializers(grades,many=True).data
        resp = {
            'grades' : grades_serialized,
        }
        return Response(data=resp,status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def spi_api(request):

    if request.method == 'GET':
        spi = Spi.objects.all()
        spi_serialized = serializers.SpiSerializers(spi,many=True).data
        resp = {
            'spi' : spi_serialized,
        }
        return Response(data=resp,status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def check_allocation_api(request):
    """
    API to check the allocation status for a given batch, semester, and year.
    Uses the utility function to avoid code repetition.
    """
    try:
        batch = request.data.get('batch')
        sem = request.data.get('sem')
        year = request.data.get('year')

        if not batch or not sem or not year:
            return Response(
                {"status": -3, "message": "Batch, semester, and year are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            batch = int(batch)
            sem = int(sem)
        except ValueError:
            return Response(
                {"status": -3, "message": "Invalid batch or semester value"},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = check_for_registration_complete(batch, sem, year)

        # Map status values to appropriate HTTP codes
        status_code_map = {
            -3: status.HTTP_404_NOT_FOUND,
            -2: status.HTTP_403_FORBIDDEN,
            -1: status.HTTP_200_OK,
             1: status.HTTP_200_OK,
             2: status.HTTP_200_OK,
        }

        return Response(result, status=status_code_map.get(result["status"], status.HTTP_500_INTERNAL_SERVER_ERROR))

    except Exception as e:
        return Response(
            {"status": -3, "message": f"Internal Server Error: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@csrf_exempt
def start_allocation_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)

    try:
        data = json.loads(request.body.decode('utf-8'))
        batch = data.get("batch")
        semester = data.get("semester")
        year = data.get("year")

        if not batch or not semester or not year:
            return JsonResponse({"error": "Missing required fields"}, status=400)

        batch = int(batch)
        semester = int(semester)

        mock_request = type('MockRequest', (), {})()
        mock_request.POST = {'batch': batch, 'sem': semester, 'year': year}

        return allocate(mock_request)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)