import datetime
import json
from io import BytesIO
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
import xlsxwriter
from applications.academic_procedures.models import course_registration
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
from applications.programme_curriculum.models import Course as Courses, CourseSlot, Batch, Semester
from applications.academic_procedures.models import InitialRegistration
from . import serializers
from rest_framework.generics import ListCreateAPIView
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse

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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_xlsheet_api(request):
    try:
        # Extract parameters
        batch = request.data.get('batch', datetime.datetime.now().year)
        course_id = request.data.get('course')

        # Validate course ID
        if not course_id:
            return Response({"error": "Course ID is required"}, status=400)

        try:
            # Ensure the course exists
            course = get_object_or_404(Courses, id=course_id)
        except Courses.DoesNotExist:
            return Response({"error": "Invalid course ID"}, status=400)

        # Fetch registered students
        registered_courses = course_registration.objects.filter(
            working_year=int(batch),
            course_id=course,
            student_id__finalregistration__verified=True
        ).select_related("student_id__id__user")

        # Prepare student data
        ans = []
        student_ids = set()
        for reg in registered_courses:
            student = reg.student_id
            if student.id.id not in student_ids:
                student_ids.add(student.id.id)
                ans.append([
                    student.id.id,
                    student.id.user.first_name,
                    student.id.user.last_name,
                    student.id.department.name
                ])

        # Sort students
        ans.sort()

        # Create Excel file
        output = BytesIO()
        book = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = book.add_worksheet()

        # Add headers
        headers = ["Sl. No", "Roll No", "Name", "Discipline", "Signature"]
        for col, header in enumerate(headers):
            sheet.write(2, col, header)

        # Add student data
        for index, row in enumerate(ans, start=1):
            sheet.write(index + 2, 0, index)
            sheet.write(index + 2, 1, row[0])
            sheet.write(index + 2, 2, f"{row[1]} {row[2]}")
            sheet.write(index + 2, 3, row[3])

        book.close()
        output.seek(0)

        # Return as a downloadable file
        response = HttpResponse(output.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename={course.code}.xlsx'
        return response

    except Exception as e:
        return Response({"error": str(e)}, status=500)
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def generate_preregistration_report(request):
    """
    to generate preresgistration report after pre-registration

    @param:
        request - contains metadata about the requested page

    @variables:
        sem - get current semester from current time
        now - get current time
        year - getcurrent year
        batch - gets the batch from form
        sem - stores the next semester
        obj - All the registration details appended into one
        data - Formated data for context
        m - counter for Sl. No (in formated data)
        z - temporary array to add data to variable data
        k -temporary array to add data to formatted array/variable
        output - io Bytes object to write to xlsx file
        book - workbook of xlsx file
        title - formatting variable of title the workbook
        subtitle - formatting variable of subtitle the workbook
        normaltext - formatting variable for normal text
        sheet - xlsx sheet to be rendered
        titletext - formatting variable of title text
        dep - temporary variables
        z - temporary variables for final output
        b - temporary variables for final output
        c - temporary variables for final output
        st - temporary variables for final output

    """
        
    if request.method == "POST":
        sem = request.data.get('semester_no')
        batch_id=request.data.get('batch_branch')
        batch = Batch.objects.filter(id = batch_id).first()
        obj = InitialRegistration.objects.filter(student_id__batch_id=batch_id, semester_id__semester_no=sem)



        registered_students = set()
        unregistered_students = set()

        # registered students contains objects of type InitialRegistration
        for stu in obj:
            registered_students.add(stu.student_id)

        students = Student.objects.filter(batch_id = batch_id)

        for stu in students:
            if stu not in registered_students:
                unregistered_students.add(stu)
        

        # for stu in obj:
        #     registered_students.add(stu.student_id)
        # students = Student.objects.filter(batch_id = batch_id)
        # for stu in students:
        #     if stu not in registered_students:
        #         unregistered_students.add(stu)



        data = []
        m = 1
        for i in unregistered_students:
            # z is a row in excel
            z = []
            z.append(m)
            m += 1
            z.append(i.id.user.username)
            z.append(str(i.id.user.first_name)+" "+str(i.id.user.last_name))
            z.append(i.id.department.name)
            z.append('Not Registered')
            data.append(z)

        sem_id = Semester.objects.get(curriculum = batch.curriculum, semester_no = sem)
        course_slots = CourseSlot.objects.all().filter(semester = sem_id)
        max_width = 1
        for student in registered_students:
            #z = []
            # z.append(m)
            # m += 1
            # z.append(i.id.user.username)
            # z.append(str(i.id.user.first_name)+" "+str(i.id.user.last_name))
            # z.append(i.id.department.name)
            # z.append('Registered')
            # data.append(z)
            current_student_registered_courses = InitialRegistration.objects.filter(student_id=student, semester_id__semester_no=sem).all()
            timestamp = current_student_registered_courses.first().timestamp
            #print("current student is ",student.id.user.username)
            #print("timstamp value ",timestamp)
            for slot in course_slots:
                #print("current slot belongs to ",slot)
                z = []
                z.append(m)
                z.append(student.id.user.username)
                z.append(str(student.id.user.first_name)+" "+str(student.id.user.last_name))
                z.append(student.id.department.name)
                z.append('Registered')
                z.append(str(timestamp))
                z.append(str(slot.name))
                
                choices_of_current_student = InitialRegistration.objects.filter(student_id=student, semester_id__semester_no=sem,course_slot_id = slot).all()
                max_width = max(max_width,len(choices_of_current_student))

                for choice in range(1,len(choices_of_current_student)+1):
                    try:
                        current_choice = InitialRegistration.objects.get(student_id=student, semester_id__semester_no=sem, course_slot_id=slot, priority=choice)
                        z.append(str(current_choice.course_id.code) + "-" + str(current_choice.course_id.name))
                    except :
                        z.append("No registration found")
                    # current_choice = InitialRegistration.objects.get(student_id=student, semester_id__semester_no=sem,course_slot_id = slot,priority = choice)
                    # # #print("current choice is ",current_choice)
                    # z.append(str(current_choice.course_id.code)+"-"+str(current_choice.course_id.name))
                
                data.append(z)
                m+=1
        output = BytesIO()

        book = xlsxwriter.Workbook(output,{'in_memory':True})
        title = book.add_format({'bold': True,
                                    'font_size': 22,
                                    'align': 'center',
                                    'valign': 'vcenter'})
        subtitle = book.add_format({'bold': True,
                                    'font_size': 15,
                                    'align': 'center',
                                    'valign': 'vcenter'})
        normaltext = book.add_format({'bold': False,
                                    'font_size': 15,
                                    'align': 'center',
                                    'valign': 'vcenter'})
        sheet = book.add_worksheet()

        # add semester too in title text
        title_text = ("Pre-registeration : "+ batch.name + str(" ") + batch.discipline.acronym + str(" ") + str(batch.year) + " Semester : "+str(sem))
        # ??
        sheet.set_default_row(25)
        characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        # text, formatting
        sheet.merge_range('A2:E2', title_text, title)
        sheet.write_string('A3',"Sl. No",subtitle)
        sheet.write_string('B3',"Roll No",subtitle)
        sheet.write_string('C3',"Name",subtitle)
        sheet.write_string('D3',"Discipline",subtitle)
        sheet.write_string('E3','Status',subtitle)
        sheet.write_string('F3','TimeStamp',subtitle)
        sheet.write_string('G3','Course Slot ID',subtitle)
        for choice_num  in range(7,7+max_width):
            sheet.write_string(characters[choice_num]+'3','Choice '+str(choice_num-6),subtitle)

        
        # Width of column
        sheet.set_column('A:A',20)
        sheet.set_column('B:B',20)
        sheet.set_column('C:C',50)
        sheet.set_column('D:D',15)
        sheet.set_column('E:E',20)
        sheet.set_column('F:F',40)
        sheet.set_column('G:G',30)
        sheet.set_column('H:H',70)
        sheet.set_column('I:I',70)
        sheet.set_column('J:J',70)
        sheet.set_column('K:K',70)
        sheet.set_column('L:L',70)
        sheet.set_column('M:M',70)
        #rows numbers
        k = 4
        # SERIAL numbers S.no 1,2,3...
        num = 1
        for i in data:
            sheet.write_number('A'+str(k),num,normaltext)
            num+=1
            z,b,c = str(i[0]),i[1],i[2]
            if(len(i) > 5):
                a,b,c,d,e,f,g = str(i[0]),str(i[1]),str(i[2]),str(i[3]),str(i[4]),str(i[5]),str(i[6])
                temp = str(i[3]).split()
                sheet.write_string('B'+str(k),b,normaltext)
                sheet.write_string('C'+str(k),c,normaltext)
                sheet.write_string('D'+str(k),d,normaltext)
                sheet.write_string('E'+str(k),e,normaltext)
                sheet.write_string('F'+str(k),f,normaltext)
                sheet.write_string('G'+str(k),g,normaltext)
                characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                # for character in characters
                for temp_num in range(7,len(i)):
                    sheet.write_string(characters[temp_num]+str(k),str(i[temp_num]),normaltext)
            else:
                a,b,c,d,e= str(i[0]),str(i[1]),str(i[2]),str(i[3]),str(i[4])
                temp = str(i[3]).split()
                sheet.write_string('B'+str(k),b,normaltext)
                sheet.write_string('C'+str(k),c,normaltext)
                sheet.write_string('D'+str(k),d,normaltext)
                sheet.write_string('E'+str(k),e,normaltext)

            k+=1
        book.close()
        # ?? 
        output.seek(0)
        response = HttpResponse(output.read(),content_type = 'application/vnd.ms-excel')
        st = 'attachment; filename = ' + batch.name + batch.discipline.acronym + str(batch.year) + '-preresgistration.xlsx'
        response['Content-Disposition'] = st
        return response
