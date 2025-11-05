import datetime
import random
from collections import defaultdict, deque, OrderedDict
from functools import wraps
from datetime import date
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect
from django.db import transaction
from django.db.models import Prefetch
from django.db.models.functions import Concat,ExtractYear,ExtractMonth,ExtractDay,Cast
from django.db.models import Max,Value,IntegerField,CharField,F,Sum, Case, When
from io import BytesIO
import json
import xlrd
from xlsxwriter.workbook import Workbook
from django.db.models import Prefetch
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes,authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
import pandas as pd
from rest_framework.decorators import (
    api_view, parser_classes, permission_classes
)
from rest_framework.parsers    import MultiPartParser, FormParser

from applications.globals.models import Faculty, HoldsDesignation, Designation, ExtraInfo
from applications.programme_curriculum.models import ( CourseInstructor, CourseSlot, Course as Courses, Batch, Semester)
# from applications.programme_curriculum.models import Course

from applications.academic_procedures.models import ( MTechGraduateSeminarReport, PhDProgressExamination, Student, Curriculum , ThesisTopicProcess, InitialRegistrations,
                                                     FinalRegistration, SemesterMarks,backlog_course,
                                                     BranchChange , StudentRegistrationChecks, Semester , FeePayments , course_registration, course_replacement, AssistantshipClaim, Assignment, StipendRequest, CourseReplacementRequest, BatchChangeHistory, FeedbackQuestion, FeedbackResponse, FeedbackFilled, FeedbackOption)

from applications.academic_information.models import (Curriculum_Instructor , Calendar)

from applications.academic_procedures.views import (get_user_semester, get_acad_year,
                                                    get_currently_registered_courses,
                                                    get_current_credits, get_branch_courses,
                                                    Constants, get_faculty_list,
                                                    get_registration_courses, get_add_course_options,
                                                    get_final_registration_eligibility,
                                                    get_add_or_drop_course_date_eligibility,
                                                    get_detailed_sem_courses,
                                                    InitialRegistration)

from applications.academic_procedures.views import get_sem_courses, get_student_registrtion_check, get_cpi, academics_module_notif, get_final_registration_choices, get_currently_registered_course, get_add_course_options, get_drop_course_options, get_replace_course_options
from applications.examination.api.views import parse_academic_year

from . import serializers

User = get_user_model()

date_time = datetime.datetime.now()

def make_label(no: int, sem_type: str) -> str:
    """
    - odd → "Semester <no>"
    - even & Even Semester → "Semester <no>"
    - even & Summer Semester → "Summer <no//2>"
    """
    if no % 2 == 1:
        return f"Semester {no}"
    if sem_type == "Summer Semester":
        return f"Summer {no // 2}"
    return f"Semester {no}"


def get_semester_type(semester):
    """
    Returns the semester type string.
    """
    if semester % 2 == 1:
        return "Odd Semester"
    elif semester % 2 == 0:
        return "Even Semester"
    else:
        return "Summer Semester"


def generate_current_session(current_year, semester) :
    """
    Returns a tuple of (session, semester_type).
    """
    semester_type = get_semester_type(semester)

    if semester_type == "Odd Semester":
        session = f"{current_year}-{str(current_year + 1)[-2:]}"
    else:  # Even or Summer
        session = f"{current_year - 1}-{str(current_year)[-2:]}"
    
    return session, semester_type


def generate_next_session(current_year, next_semester) :
    """
    Returns a tuple of (session, semester_type) for student's next semester.
    """
    semester_type = get_semester_type(next_semester)

    if semester_type == "Odd Semester" or semester_type == "Even Semester":
        session = f"{current_year}-{str(current_year + 1)[-2:]}"
    else:
        session = f"{current_year - 1}-{str(current_year)[-2:]}"
    
    return session, semester_type


def role_required(allowed_roles):
    """
    Decorator factory that accepts a list of allowed role names.
    Accepts multiple HoldsDesignation records per user.
    """
    allowed_lower = {role.lower() for role in allowed_roles}

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Fetch all designations for this user
            user_roles = (
                HoldsDesignation.objects
                .select_related('designation')
                .filter(user=request.user)
                .values_list('designation__name', flat=True)  # or whichever field holds the string
            )

            # Normalize to lowercase for comparison
            user_roles_lower = {r.lower() for r in user_roles}

            # Check intersection
            if not (user_roles_lower & allowed_lower):
                return Response(
                    {"error": "Permission denied: one of %s required" % allowed_roles},
                    status=status.HTTP_403_FORBIDDEN
                )

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator



#--------------------------------------- APIs of student----------------------------------------------------------

demo_date = timezone.now()

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@role_required(['acadadmin'])
def get_all_courses(request):
    try:
        obj = Courses.objects.all()
        serializer = serializers.CourseSerializer(obj, many=True).data
        
        return Response(serializer, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(data = str(e) , status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# @api_view(['POST'])
# @role_required(['acadadmin'])
# def gen_roll_list(request):
#     try:
#         batch = request.data['batch']
#         course_id = request.data['course']
#         course = Courses.objects.get(id = course_id)
#         #obj = course_registration.objects.all().filter(course_id = course)
#         obj=course_registration.objects.filter(course_id__id=course_id, student_id__batch=batch).select_related(
#         'student_id__id__user','student_id__id__department').only('student_id__batch', 
#         'student_id__id__user__first_name', 'student_id__id__user__last_name',
#         'student_id__id__department__name','student_id__id__user__username')
#     except Exception as e:
#         batch=""
#         course=""
#         obj=""
#     students = []
#     for i in obj:
#         students.append({"rollno":i.student_id.id.user.username, 
#         "name":i.student_id.id.user.first_name+" "+i.student_id.id.user.last_name, 
#         "department":i.student_id.id.department.name})
#     # {'students': students, 'batch':batch, 'course':course_id}
#     return JsonResponse({'students': students, 'batch':batch, 'course':course_id}, status=200)


# api for student for adding courses  
# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def add_course(request):
#     try:
#         current_user = request.user
#         current_user = ExtraInfo.objects.all().filter(user=current_user).first()
#         current_user = Student.objects.all().filter(id=current_user.id).first()

#         sem_id_instance = Semester.objects.get(id = request.data['semester'])
        
#         count = request.data['ct']
#         count = int(count)
#         reg_curr = []

#         for i in range(1, count+1):
#             choice = "choice["+str(i)+"]"
#             slot = "slot["+str(i)+"]"
#             try:
#                 course_id_instance = Courses.objects.get(id = request.data[choice])
#                 courseslot_id_instance = CourseSlot.objects.get(id = request.data[slot])
                
#                 print(courseslot_id_instance.max_registration_limit)
#                 if course_registration.objects.filter(working_year = current_user.batch_id.year, course_id = course_id_instance).count() < courseslot_id_instance.max_registration_limit and (course_registration.objects.filter(course_id=course_id_instance, student_id=current_user).count() == 0):
#                     print("space left = True")
#                     p = course_registration(
#                         course_id=course_id_instance,
#                         student_id=current_user,
#                         course_slot_id=courseslot_id_instance,
#                         semester_id=sem_id_instance
#                     )
#                     print(serializers.course_registration(p))
#                     if p not in reg_curr:
#                         reg_curr.append(p)
#                     else:
#                         print("already exist")
#             except Exception as e:
#                 error_message = str(e) 
#                 resp = {'message': 'Course addition failed', 'error': error_message}
#                 return Response(resp, status=status.HTTP_400_BAD_REQUEST)
#         print(reg_curr)
#         course_registration_data = course_registration.objects.bulk_create(reg_curr)
#         course_registration_data = serializers.CourseRegistrationSerializer(course_registration_data , many = True).data
#         res = {'message' : 'Courses successfully added' , "courses_added" : course_registration_data }
#         return Response(data = res , status = status.HTTP_200_OK)
#     except Exception as e:
#         print(e)
#         return Response(data = str(e) , status= status.HTTP_500_INTERNAL_SERVER_ERROR)

    
# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def drop_course(request):
#     if not request.user.is_authenticated:
#         return Response({'message': 'Login required '}, status=status.HTTP_400_BAD_REQUEST)
#     data = request.GET.get('id')
#     reg_id = int(data)
#     current_user = request.user
#     current_user = ExtraInfo.objects.all().filter(user=current_user).first()
#     current_user = Student.objects.all().filter(id = current_user.id).first()
#     try:
#         course_registration.objects.filter(id = reg_id, student_id = current_user).delete()
#     except Exception as e:
#         resp = {"message" : "Course drop failed", "error" : str(e)}
#         return Response(data = resp, status = status.HTTP_400_BAD_REQUEST)
    
#     resp = {"message" : "Course successfully dropped"}
#     return Response(data = resp , status = status.HTTP_200_OK)


# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def student_swayam_add_course(request):
#     if not request.user.is_authenticated:
#         return JsonResponse({'message': 'Login required '}, status=401)
#     try:
#         current_user = request.user
#         current_user = ExtraInfo.objects.all().filter(user=current_user).first()
#         current_user = Student.objects.all().filter(id = current_user.id).first()
#         course_id = request.POST["course_id"]
#         courseslot_id = request.POST["courseslot_id"]
#         registration_type = request.POST["registration_type"]
#         if (not course_id) or (not courseslot_id) or (not registration_type):
#             return JsonResponse({'message': 'Enter Complete Form Details '}, status=400)
#         course = Courses.objects.get(id=course_id)
#         courseslot = CourseSlot.objects.get(id=courseslot_id)
#         semester_no = current_user.curr_semester_no
#         curr_id = current_user.batch_id.curriculum
#         semester = Semester.objects.get(curriculum = curr_id, semester_no = semester_no)
#         try:
#             course_registration.objects.get(course_slot_id = courseslot, student_id = current_user)
#             return JsonResponse({'message': 'already registered a course in course slot'}, status=400)
#         except:
#             pass
#         try:
#             course_registration.objects.get(course_id = course, student_id = current_user)
#             return JsonResponse({'message': 'already registered a particular course'}, status=400)
#         except:
#             pass
#         cr = course_registration(
#             course_slot_id=courseslot, course_id=course, student_id=current_user, semester_id=semester , working_year = datetime.datetime.now().year, registration_type=registration_type)
#         cr.save()
#         return JsonResponse({'message': 'Successfully added swayam course' }, status=200)
#     except Exception as e:
#         print(str(e))
#         return JsonResponse({'message': 'Error adding course '}, status=500)
        

# simple api for getting to know the details of user who have logined in the system
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_info(request):
    current_user = request.user
    details1 = serializers.UserSerializer(current_user).data
    details2 = serializers.ExtraInfoSerializer(current_user.extrainfo).data
    details = {
        "user_serializer_Data" : details1,
        "ExtraInfoSerializer_Data" : details2
    }
    return Response(data = details  , status= status.HTTP_200_OK)


# with this api student can see the list of courses offered to him in upcoming semester
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@role_required(['student'])
def view_offered_courses(request):
    try : 
        obj = Curriculum.objects.filter(
            programme = request.data['programme'],
            branch = request.data['branch'],
            batch = request.data["batch"],
            sem = request.data["semester"]
        )
        serializer = serializers.CurriculumSerializer(obj, many=True).data
        return Response(serializer, status=status.HTTP_200_OK)
    except Exception as e:
            return Response(data = str(e) , status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    # try:
    #     ug_flag = True
    #     masters_flag = False
    #     phd_flag = False
    #     current_semester =  get_user_semester(request.user, ug_flag, masters_flag, phd_flag)
    #     current_year = date_time.date().year
        
    #     return Response(data= { } , status=status.HTTP_200_OK)
    # except Exception as e:
    #     return Response(data = {"error" : str(e)} , status= status.HTTP_500_INTERNAL_SERVER_ERROR)


#  with this student can know status of pre registration and final registration
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@role_required(['student'])
def student_view_registration(request):
    try:
        # getting the registration status of current user for the given semester
        current_user = request.user
        student_id = current_user.extrainfo.id
        
        sem_id = Semester.objects.get(id = request.data.get('semester'))
        sem_id = serializers.SemesterSerializer(sem_id).data["id"]

        # filter based on the semester id and student id
        obj = StudentRegistrationChecks.objects.filter(semester_id_id = sem_id,  student_id = student_id)

        # serialize the data for displaying
        serializer = serializers.StudentRegistrationChecksSerializer(obj, many=True).data

        return Response(serializer, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(data = str(e) , status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# with this student can do his pre registration for the upcoming semester
# @api_view(['POST'])
# @transaction.atomic
# def student_pre_registration(request):
#     try:
#         current_user = request.user
#         current_user_id = serializers.UserSerializer(current_user).data["id"]
#         s_id = current_user.extrainfo.id

#         current_user = ExtraInfo.objects.all().select_related('user','department').filter(user=current_user_id).first()
#         current_user = serializers.ExtraInfoSerializer(current_user).data

#         current_user_instance = Student.objects.all().filter(id=current_user["id"]).first()
#         current_user = serializers.StudentSerializers(current_user_instance).data

#         sem_id_instance = Semester.objects.get(id = request.data.get('semester'))
#         sem_id = serializers.SemesterSerializer(sem_id_instance).data["id"]

#         # filter based on the semester id and student id
#         obj = StudentRegistrationChecks.objects.filter(semester_id_id = sem_id,  student_id = s_id)
#         # serialize the data for displaying
#         student_registration_check = serializers.StudentRegistrationChecksSerializer(obj, many=True).data

#         try:
#             # check if user have already done pre registration
#             if(student_registration_check and student_registration_check[0]["pre_registration_flag"] ):
#                 return Response(data = {"message" : "You have already registered for this semester" }, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             return Response(data = str(e) , status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#         course_slots=request.data.get("course_slot")
#         reg_curr = []
        

#         for course_slot in course_slots :
#             course_priorities = request.data.get("course_priority-"+course_slot)
#             if(course_priorities[0] == 'NULL'):
#                 print("NULL FOUND")
#                 continue
#             course_slot_id_for_model = CourseSlot.objects.get(id = int(course_slot))

#             # return Response(data = course_slots , status=status.HTTP_200_OK)
#             for course_priority in course_priorities:
#                 priority_of_current_course,course_id = map(int,course_priority.split("-"))
#                 # get course id for the model
#                 course_id_for_model = Courses.objects.get(id = course_id)
#                 print("check")
#                 p = InitialRegistration(
#                     course_id = course_id_for_model,
#                     semester_id = sem_id_instance,
#                     student_id = current_user_instance,
#                     course_slot_id = course_slot_id_for_model,
#                     priority = priority_of_current_course
#                 )
#                 p.save()
#                 reg_curr.append(p)

        
#         try:
#             serialized_reg_curr = serializers.InitialRegistrationSerializer(reg_curr, many=True).data
            
#             registration_check = StudentRegistrationChecks(
#                         student_id = current_user_instance,
#                         pre_registration_flag = True,
#                         final_registration_flag = False,
#                         semester_id = sem_id_instance
#                     )
#             registration_check.save()
#             return Response(data={"message": "Successfully Registered for the courses.", "registrations": serialized_reg_curr}, status=status.HTTP_200_OK)
#         except Exception as e:
#             return Response(data = {"message" : "Error in Registration." , "error" : str(e)} , status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#     except Exception as e:
#         return Response(data = {"message" : "Error in Registration." , "error" : str(e)} , status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@role_required(['student'])
def final_registration(request):
    try:
        with transaction.atomic():
            print(request.data)
            current_user = request.user
            extra_info = current_user.extrainfo
            student = Student.objects.filter(id=extra_info).first()

            sem_id = Semester.objects.get(id=request.data.get('semester'))

            mode = str(request.data.get('mode'))
            transaction_id = str(request.data.get('transaction_id'))
            deposit_date = request.data.get('deposit_date')
            utr_number = str(request.data.get('utr_number'))
            fee_paid = request.data.get('fee_paid')
            actual_fee = request.data.get('actual_fee')
            reason = str(request.data.get('reason')) or None  # Handle empty string
            fee_receipt = request.FILES['fee_receipt']
            # Save FeePayments object
            obj = FeePayments(
                student_id=student,
                semester_id=sem_id,
                mode=mode,
                transaction_id=transaction_id,
                deposit_date=deposit_date,
                utr_number=utr_number,
                fee_paid=fee_paid,
                actual_fee=actual_fee,
                reason=reason,
                fee_receipt=fee_receipt
            )
            obj.save()

            # Update StudentRegistrationChecks
            StudentRegistrationChecks.objects.filter(
                student_id=student,
                semester_id=sem_id
            ).update(final_registration_flag=True)

            return JsonResponse({'message': 'Final Registration Successful'})
        
    except Exception as e:
        return JsonResponse({'message': f'Final Registration Failed: {str(e)}'}, status=500)
        
        
# with this student can do his final registration for the upcoming semester
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def student_final_registration(request):
    try:
        current_user = request.user
        current_user_id = serializers.UserSerializer(current_user).data["id"]
        s_id = current_user.extrainfo.id

        current_user = ExtraInfo.objects.all().select_related('user','department').filter(user=current_user).first()
        current_user = serializers.ExtraInfoSerializer(current_user).data

        current_user_instance = Student.objects.all().filter(id=current_user["id"]).first()
        current_user = serializers.StudentSerializers(current_user_instance).data

        # these details we need from the body of the request fot doing final registration
        sem_id_instance = Semester.objects.get(id = request.data.get('semester'))
        sem_id = serializers.SemesterSerializer(sem_id_instance).data["id"]
        registration_status = StudentRegistrationChecks.objects.filter(student_id = current_user["id"], semester_id = sem_id)
        registration_status = serializers.StudentRegistrationChecksSerializer(registration_status , many = True ).data
        
        if(len(registration_status)>0 and registration_status[0]["pre_registration_flag"] == False):
            return Response(data = {"message" : "Student haven't done pre registration yet."} , status= status.HTTP_400_BAD_REQUEST )
        mode = str(request.data.get('mode'))
        transaction_id = str(request.data.get('transaction_id'))
        deposit_date = request.data.get('deposit_date')
        utr_number = str(request.data.get('utr_number'))
        fee_paid = request.data.get('fee_paid')
        actual_fee = request.data.get('actual_fee')
        reason = str(request.data.get('reason'))
        if reason=="":
            reason=None
        # fee_receipt = request.FILES['fee_receipt']

        # print(fee_receipt)
        obj = FeePayments(
            student_id = current_user_instance,
            semester_id = sem_id_instance,
            mode = mode,
            transaction_id = transaction_id,
            # fee_receipt = fee_receipt,
            deposit_date = deposit_date,
            utr_number = utr_number,
            fee_paid = fee_paid,
            actual_fee = actual_fee,
            reason = reason
            )
        obj.save()
        try:
            registration_status = StudentRegistrationChecks.objects.filter(student_id = current_user_instance, semester_id = sem_id).update(final_registration_flag = True)
            return Response(data = {"message" : "Final Registration Successfull" } , status= status.HTTP_200_OK)
        except Exception as e:
            return Response(data = {"message" : "Final Registration Failed " , "error" : str(e)} , status = status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return Response(data = {"message" : "Final Registration Failed " , "error" : str(e)} , status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# with this api student can get his backlog courses list
# @api_view(['GET'])
# def student_backlog_courses(request):
#     try : 
#         stu_id = Student.objects.select_related('id','id__user','id__department').get(id=request.user.username)
#         backlogCourseList = []
#         backlogCourses = backlog_course.objects.select_related('course_id' , 'student_id' , 'semester_id' ).filter(student_id=stu_id)
#         for i in backlogCourses:
#             obj = {
#                 "course_id" : i.course_id.id,
#                 "course_name" : i.course_id.course_name,
#                 "faculty" : i.course_id.course_details,
#                 "semester" : i.semester_id.semester_no,
#                 "is_summer_course" : i.is_summer_course
#             }
#             backlogCourseList.append(obj)

#         return Response(backlogCourseList, status=status.HTTP_200_OK)
#     except Exception as e:
#             return Response(data = str(e) , status=status.HTTP_500_INTERNAL_SERVER_ERROR)



#--------------------------------------- APIs of acad person----------------------------------------------------------


# with this acad admin can fetch the list of courses for any batch , semester and brach
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@role_required(['acadadmin'])
def get_course_list(request):
    
    programme = request.data['programme']
    branch = request.data['branch']
    batch = request.data['batch']

    try : 
        print(programme , branch , batch)
        obj = Curriculum.objects.filter(
            programme = request.data['programme'],
            branch = request.data['branch'],
            batch = request.data["batch"]
        )
        serializer = serializers.CurriculumSerializer(obj, many=True).data
        return Response(serializer, status=status.HTTP_200_OK)
    except Exception as e:
            return Response(data = str(e) , status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    # obj = Curriculum.objects.filter(curriculum_id_=curriculum_id, course_type_ = course_type, programme_ = programme, batch_ = batch, branch_ = branch, sem_ = sem, optional_ = optional)


#  with this api acad person can see the list of students who have completed their pre and final registrations for any semester
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@role_required(['acadadmin'])
def acad_view_reigstrations(request):
    try:
        semester = request.data["semester"]
        sem_id_instance = Semester.objects.get(id = request.data.get('semester'))
        sem_id = serializers.SemesterSerializer(sem_id_instance).data["id"]
        obj = StudentRegistrationChecks.objects.filter(semester_id_id = sem_id,   final_registration_flag =True)
        student_registration_check = serializers.StudentRegistrationChecksSerializer(obj, many=True).data

        return Response(data= student_registration_check  , status=status.HTTP_200_OK)
    except Exception as e:
        return Response(data = {"error" : str(e)} , status= status.HTTP_500_INTERNAL_SERVER_ERROR)


# with this api acad person set the date of pre registration date for any semester
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@role_required(['acadadmin'])
def configure_pre_registration_date(request):
    try:
        try:
            from_date = request.data.get('from_date')
            to_date = request.data.get('to_date')
            semester = request.data.get('semester')
            current_year = date_time.date().year
            desc = "Pre Registration " + str(semester) +" " + str(current_year)
            print(from_date , to_date , desc)
            from_date = from_date.split('-')
            from_date = [int(i) for i in from_date]
            from_date = datetime.datetime(*from_date).date()
            to_date = to_date.split('-')
            to_date = [int(i) for i in to_date]
            to_date = datetime.datetime(*to_date).date()
        except Exception as e:
            from_date=""
            to_date=""
            desc=""
            pass
        c = Calendar(
            from_date=from_date,
            to_date=to_date,
            description=desc)
        c.save()
        return Response(data = {"message" : "Pre registration for semester " + str(semester) + " will be opened from " + str(from_date) + " to " + str(to_date) + ". "  ,  } , status= status.HTTP_200_OK)
    except Exception as e:
        return Response(data = {"error " : str(e)} , status= status.HTTP_500_INTERNAL_SERVER_ERROR)


# with this api request acad person can set the date of final registration
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@role_required(['acadadmin'])
def configure_final_registration_date(request):
    try:
        try:
            from_date = request.data.get('from_date')
            to_date = request.data.get('to_date')
            semester = request.data.get('semester')
            current_year = date_time.date().year
            desc = "Physical Reporting at the Institute"
            print(from_date , to_date , desc)
            from_date = from_date.split('-')
            from_date = [int(i) for i in from_date]
            from_date = datetime.datetime(*from_date).date()
            to_date = to_date.split('-')
            to_date = [int(i) for i in to_date]
            to_date = datetime.datetime(*to_date).date()
        except Exception as e:
            from_date=""
            to_date=""
            desc=""
            pass
        c = Calendar(
            from_date=from_date,
            to_date=to_date,
            description=desc)
        c.save()
        return Response(data = {"message" : "Physical Reporting at the Institute will be opened from " + str(from_date) + " to " + str(to_date) + ". "  ,  } , status= status.HTTP_200_OK)
    except Exception as e:
        return Response(data = {"error " : str(e)} , status= status.HTTP_500_INTERNAL_SERVER_ERROR)

# with this api request acad person can add any courses in a specific slot   
# @api_view(['POST'])
# def add_course_to_slot(request):
#     course_code = request.data.get('course_code')
#     course_slot_name = request.data.get('course_slot_name')
#     try:
#         course_slot = CourseSlot.objects.get(name=course_slot_name)
#         course = Courses.objects.get(code=course_code)
#         course_slot.courses.add(course)
        
#         return JsonResponse({'message': f'Course {course_code} added to slot {course_slot_name} successfully.'}, status=200)
#     except CourseSlot.DoesNotExist:
#         return JsonResponse({'error': 'Course slot does not exist.'}, status=400)
#     except Courses.DoesNotExist:
#         return JsonResponse({'error': 'Course does not exist.'}, status=400)

# # with this api request acad person can remove any course from a specific slot   
# @api_view(['POST'])
# def remove_course_from_slot(request):
#     course_code = request.data.get('course_code')
#     course_slot_name = request.data.get('course_slot_name')
#     try:
#         course_slot = CourseSlot.objects.get(name=course_slot_name)
#         course = Courses.objects.get(code=course_code)
#         course_slot.courses.remove(course)
#         return JsonResponse({'message': f'Course {course_code} removed from slot {course_slot_name} successfully.'}, status=200)
#     except CourseSlot.DoesNotExist:
#         return JsonResponse({'error': 'Course slot does not exist.'}, status=400)
#     except Course.DoesNotExist:
#         return JsonResponse({'error': 'Course does not exist.'}, status=400)
  


#--------------------------------------- APIs of faculty----------------------------------------------------------

# with this api faculty can know what are the courses assigned to him 
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def faculty_assigned_courses(request):
    
    
    try:
        current_user = request.user
        curriculum_ids = Curriculum_Instructor.objects.filter(instructor_id=current_user.id).values_list('curriculum_id', flat=True)
        course_infos = []
        print(current_user.id)
        for curriculum_id in curriculum_ids:
            course_info = Curriculum.objects.filter(curriculum_id=curriculum_id).values_list('course_code','course_type','programme','branch','sem','course_id_id').first()
            # course_infos.append(course_info)
            context = {
                "course_code": course_info[0],
                "course_type": course_info[1],
                "programme": course_info[2],
                "branch": course_info[3],
                "sem": course_info[4],
                "course_id": course_info[5]
            }
            course_infos.append(context)
    
        return Response(data= course_infos , status=status.HTTP_200_OK)
    except Exception as e:
        return Response(data = {"error" : str(e)} , status= status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_next_sem_courses(request):
    try:
        next_sem = request.data.get('next_sem')
        branch = request.data.get('branch')
        programme = request.data.get('programme')
        batch = request.data.get('batch')

        #  we go to student table and apply filters and get batch_id of the students with these filter
        batch_id = Student.objects.filter(programme = programme , batch = batch , specialization = branch)[0].batch_id

        curr_id = batch_id.curriculum
        next_sem_id = Semester.objects.get(curriculum = curr_id, semester_no = next_sem)
        
        if next_sem_id:
            next_sem_registration_courses = get_detailed_sem_courses(next_sem_id )
            return JsonResponse(next_sem_registration_courses, safe=False)
    except Exception as e:
        return Response(data = {"error" : str(e)} , status= status.HTTP_500_INTERNAL_SERVER_ERROR)

# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def add_one_course(request):
#     try:    
#         print(request.data)
#         current_user = get_object_or_404(User, username=request.data.get('user'))
#         current_user = ExtraInfo.objects.all().filter(user=current_user).first()
#         current_user = Student.objects.all().filter(id=current_user.id).first()

#         sem_id = Semester.objects.get(id=request.data.get('semester'))
#         choice = request.data.get('choice')
#         slot = request.data.get('slot')

#         try:
#             course_id = Courses.objects.get(id=choice)
#             courseslot_id = CourseSlot.objects.get(id=slot)
#             print(courseslot_id.id)
#             print(courseslot_id.type)
#             print(courseslot_id.max_registration_limit)
#             if course_registration.objects.filter(course_slot_id_id=courseslot_id, student_id=current_user).count() == 1 and courseslot_id.type != "Swayam":
#                 already_registered_course_id = course_registration.objects.filter(course_slot_id_id=courseslot_id, student_id=current_user)[0].course_id
#                 print(already_registered_course_id)
#                 msg = 'Already Registered in the course : ' +already_registered_course_id.code + '-'+ already_registered_course_id.name
#                 return JsonResponse({'message' : msg})
#             if((course_registration.objects.filter(course_id=course_id, student_id=current_user).count() >= 1)):
#                 return JsonResponse({'message': 'Already registered in this course!'}, status=200)
#             # Check if maximum course registration limit has not been reached
#             if course_registration.objects.filter(student_id__batch_id__year=current_user.batch_id.year, course_id=course_id).count() < courseslot_id.max_registration_limit and \
#                     (course_registration.objects.filter(course_id=course_id, student_id=current_user).count() == 0):
#                 p = course_registration(
                    
#                     course_id=course_id,
#                     student_id=current_user,
#                     course_slot_id=courseslot_id,
#                     semester_id=sem_id
#                 )
#                 p.save()
#                 return JsonResponse({'message': 'Course added successfully'}, status=200)
#             else:
#                 return JsonResponse({'message': 'Course not added because seats are full!'}, status=404)
#         except Exception as e:
#             print(e)
#             return JsonResponse({'message': 'Error adding course'}, status=500)
#     except Exception as e:
#         return JsonResponse({'message': 'Error adding course'}, status=500)
    

@transaction.atomic
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
@role_required(['acadadmin'])
def verify_registration(request):
    data = json.loads(request.body)
    print(data)
    if data.get('status_req') == "accept" :
        student_id = data.get('student_id')
        student = Student.objects.get(id = student_id)
        batch = student.batch_id
        curr_id = batch.curriculum
        
        if(student.curr_semester_no+1 >= 9):
            # print('----------------------------------------------------------------' , student.curr_semester_no)
            sem_no = 8
        else:
            # print('----------------------------------------------------------------' , student.curr_semester_no)
            sem_no = student.curr_semester_no+1
        sem_id = Semester.objects.get(curriculum = curr_id, semester_no = sem_no)
        # print('----------------------------------------------------------------' , student.curr_semester_no)
        
        final_register_list = FinalRegistration.objects.all().filter(student_id = student, verified = False, semester_id = sem_id)
        
        # final_register_list = FinalRegistration.objects.all().filter(student_id = student, verified = False)
        
        with transaction.atomic():
            ver_reg = []
            for obj in final_register_list:
                p = course_registration(
                    course_id=obj.course_id,
                    student_id=student,
                    semester_id=obj.semester_id,
                    course_slot_id = obj.course_slot_id,
                    working_year = datetime.datetime.now().year,
                    registration_type=obj.registration_type
                    )
                # ver_reg.append(p)
                p.save()
                if (obj.old_course_registration):
                    course_replacement.objects.create(new_course_registration=p, old_course_registration=obj.old_course_registration)
                o = FinalRegistration.objects.filter(id= obj.id).update(verified = True)
            # course_registration.objects.bulk_create(ver_reg)
            academics_module_notif(request.user, student.id.user, 'registration_approved')
            
            Student.objects.filter(id = student_id).update(curr_semester_no = sem_no)
            return JsonResponse({'status': 'success', 'message': 'Successfully Accepted'})
         
    elif data.get('status_req') == "reject" :
        reject_reason = data.get('reason', '')
        student_id = data.get('student_id')
        student_id = Student.objects.get(id = student_id)
        batch = student_id.batch_id
        curr_id = batch.curriculum
        if(student_id.curr_semester_no+1 >= 9):
            sem_no = 8
        else:
            sem_no = student_id.curr_semester_no+1
        sem_id = Semester.objects.get(curriculum = curr_id, semester_no = sem_no)
        with transaction.atomic():
            academicadmin = get_object_or_404(User, username = request.user.username)
            # print(sem_id)
            # FinalRegistration.objects.filter(student_id = student_id, verified = False, semester_id = sem_id).delete()
            # StudentRegistrationChecks.objects.filter(student_id = student_id, semester_id = sem_id).update(final_registration_flag = False)
            FeePayments.objects.filter(student_id = student_id, semester_id = sem_id).delete()
            academics_module_notif(academicadmin, student_id.id.user, 'Registration Declined - '+reject_reason)
            return JsonResponse({'status': 'success', 'message': 'Successfully Rejected'})
        
    return JsonResponse({'status': 'error', 'message': 'Error in processing'})

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@role_required(['acadadmin'])
def verify_course(request):
    roll_no = request.data.get("rollno")
    if not roll_no:
        return Response({"error": "rollno is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Convert to uppercase after null check
    roll_no = roll_no.strip().upper()

    # First check main academic tables
    student = Student.objects.filter(id_id=roll_no).first()
    if not student:
        # If not found in main tables, check StudentBatchUpload
        try:
            from applications.programme_curriculum.models_student_management import StudentBatchUpload
            batch_student = StudentBatchUpload.objects.filter(roll_number=roll_no).first()
            if batch_student:
                if batch_student.reported_status == 'REPORTED':
                    return Response({
                        "error": f"Student {roll_no} has reported but not yet transferred to main academic system. Please contact academic office."
                    }, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({
                        "error": f"Student {roll_no} found in upcoming batches but status is '{batch_student.reported_status}'. Student must report first."
                    }, status=status.HTTP_400_BAD_REQUEST)
        except ImportError:
            pass
        
        return Response({"error": "Student record not found"}, status=status.HTTP_400_BAD_REQUEST)


    extra = student.id
    user_obj = extra.user
    
    # name & roll for frontend
    dict2 = {
        "roll_no": roll_no,
        "firstname": user_obj.first_name or "",
        "lastname": user_obj.last_name or "",
    }

    # current curriculum & semester - handle None batch_id case
    if not student.batch_id:
        return Response({
            "error": f"Student {roll_no} does not have a valid batch assignment. Please contact academic office to complete student setup."
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not student.batch_id.curriculum:
        return Response({
            "error": f"Student {roll_no}'s batch does not have a curriculum assigned. Please contact academic office."
        }, status=status.HTTP_400_BAD_REQUEST)
    
    curr = student.batch_id.curriculum
    curr_sem = Semester.objects.filter(curriculum=curr, semester_no=student.curr_semester_no).first()
    if not curr_sem:
        return Response({"error": "Current semester not found"}, status=status.HTTP_404_NOT_FOUND)

    # gather registered courses for this semester
    regs = course_registration.objects.filter(student_id=student).order_by('-semester_id__semester_no')
    details = []
    for reg in regs:
        slot_course = Courses.objects.filter(id=reg.course_id.id).first()
        repl_qs = course_replacement.objects.filter(old_course_registration=reg)
        replaced_list = []
        for repl in repl_qs:
            nr = repl.new_course_registration
            replaced_list.append({
                "course_id": {
                    "code": nr.course_id.code,
                    "name": nr.course_id.name,
                },
                "semester_id": {
                    "semester_no": nr.semester_id.semester_no,
                },
            })

        details.append({
            "id": reg.id,
            "reg_id": reg.id,
            "rid": f"{roll_no} - {reg.course_id.code}",
            "course_id": reg.course_id.code,
            "course_name": reg.course_id.name,
            "sem": reg.semester_id.semester_no,
            "semester_type" : reg.semester_type,
            "credits": slot_course.credit if slot_course else 0,
            "registration_type": reg.registration_type,
            "replaced_by": replaced_list,
        })

    # lists for selects (no serializers)
    course_list = list(Courses.objects.values("id", "code", "name", "credit"))
    semester_list = list(
        Semester.objects.filter(curriculum=curr).values("id", "semester_no")
    )
    courseslot_list = list(
        CourseSlot.objects.filter(semester__in=[s["id"] for s in semester_list]).values("id", "name")
    )

    # academic year & semflag
    today = date.today()
    year = today.year
    semflag = 1 if today.month >= 7 else 2
    yearr = f"{year}-{year+1}"

    return Response({
        "details": details,
        "dict2": dict2,
        "course_list": course_list,
        "semester_list": semester_list,
        "courseslot_list": courseslot_list,
        "date": {"year": yearr, "semflag": semflag},
    })


#  These apis were implemented before but now don't use them they have some errors


# @api_view(['GET'])
# def academic_procedures_faculty(request):
#     current_user = request.user
#     user_details = current_user.extrainfo
#     des = current_user.holds_designations.all().first()

#     if str(des.designation) == 'student':
#         return Response({'error':'Not a faculty'}, status=status.HTTP_400_BAD_REQUEST)
#     elif str(current_user) == 'acadadmin':
#         return Response({'error':'User is acadadmin'}, status=status.HTTP_400_BAD_REQUEST)

#     elif str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor":
#         faculty_object = user_details.faculty
#         month = int(date_time.month)
#         sem = []
#         if month>=7 and month<=12:
#             sem = [1,3,5,7]
#         else:
#             sem = [2,4,6,8]
#         student_flag = False
#         fac_flag = True

#         thesis_supervision_request_list = faculty_object.thesistopicprocess_supervisor.all()
#         thesis_supervision_request_list_data = serializers.ThesisTopicProcessSerializer(thesis_supervision_request_list, many=True).data
#         approved_thesis_request_list = serializers.ThesisTopicProcessSerializer(thesis_supervision_request_list.filter(approval_supervisor = True), many=True).data
#         pending_thesis_request_list = serializers.ThesisTopicProcessSerializer(thesis_supervision_request_list.filter(pending_supervisor = True), many=True).data
#         courses_list = serializers.CurriculumInstructorSerializer(user_details.curriculum_instructor_set.all(), many=True).data
#         fac_details = serializers.UserSerializer(current_user).data

#         resp = {
#             'student_flag' : student_flag,
#             'fac_flag' : fac_flag,
#             'thesis_supervision_request_list' : thesis_supervision_request_list_data,
#             'pending_thesis_request_list' : pending_thesis_request_list,
#             'approved_thesis_request_list' : approved_thesis_request_list,
#             'courses_list': courses_list,
#             'faculty': fac_details
#         }
#         return Response(data=resp, status=status.HTTP_200_OK)






# @api_view(['GET'])
# def academic_procedures_student(request):
#     current_user = request.user
#     current_user_data = {
#         'first_name': current_user.first_name,
#         'last_name': current_user.last_name,
#         'username': current_user.username,
#         'email': current_user.email
#     }
#     user_details = current_user.extrainfo
#     des = current_user.holds_designations.all().first()
#     if str(des.designation) == 'student':
#         obj = user_details.student

#         if obj.programme.upper() == "PH.D":
#             student_flag = True
#             ug_flag = False
#             masters_flag = False
#             phd_flag = True
#             fac_flag = False
#             des_flag = False

#         elif obj.programme.upper() == "M.DES":
#             student_flag = True
#             ug_flag = False
#             masters_flag = True
#             phd_flag = False
#             fac_flag = False
#             des_flag = True

#         elif obj.programme.upper() == "B.DES":
#             student_flag = True
#             ug_flag = True
#             masters_flag = False
#             phd_flag = False
#             fac_flag = False
#             des_flag = True

#         elif obj.programme.upper() == "M.TECH":
#             student_flag = True
#             ug_flag = False
#             masters_flag = True
#             phd_flag = False
#             fac_flag = False
#             des_flag = False

#         elif obj.programme.upper() == "B.TECH":
#             student_flag = True
#             ug_flag = True
#             masters_flag = False
#             phd_flag = False
#             fac_flag = False
#             des_flag = False

#         else:
#             return Response({'message':'Student has no record'}, status=status.HTTP_400_BAD_REQUEST)

#         current_date = date_time.date()
#         current_year = date_time.year
#         batch = obj.batch_id
#         user_sem = get_user_semester(request.user, ug_flag, masters_flag, phd_flag)
#         acad_year = get_acad_year(user_sem, current_year)
#         user_branch = user_details.department.name
#         cpi = obj.cpi
#         cur_spi='Sem results not available' # To be fetched from db if result uploaded

#         details = {
#             'current_user': current_user_data,
#             'year': acad_year,
#             'user_sem': user_sem,
#             'user_branch' : str(user_branch),
#             'cpi' : cpi,
#             'spi' : cur_spi
#         }
        
#         currently_registered_courses = get_currently_registered_courses(user_details.id, user_sem)
#         currently_registered_courses_data = serializers.CurriculumSerializer(currently_registered_courses, many=True).data
#         try:
#             pre_registered_courses = obj.initialregistrations_set.all().filter(semester = user_sem)
#             pre_registered_courses_show = obj.initialregistrations_set.all().filter(semester = user_sem+1)
#         except:
#             pre_registered_courses =  None
#             pre_registered_courses_show=None
#         try:
#             final_registered_courses = obj.finalregistrations_set.all().filter(semester = user_sem)
#         except:
#             final_registered_courses = None

#         pre_registered_courses_data = serializers.InitialRegistrationsSerializer(pre_registered_courses, many=True).data
#         pre_registered_courses_show_data = serializers.InitialRegistrationsSerializer(pre_registered_courses_show, many=True).data
#         final_registered_courses_data = serializers.FinalRegistrationsSerializer(final_registered_courses, many=True).data

#         current_credits = get_current_credits(currently_registered_courses)
#         print(current_user, user_sem+1, user_branch)
#         try:
#             next_sem_branch_courses = get_branch_courses(current_user, user_sem+1, user_branch)
#         except Exception as e:
#             return Response(data = str(e))
#         next_sem_branch_courses_data = serializers.CurriculumSerializer(next_sem_branch_courses, many=True).data

#         fee_payment_mode_list = dict(Constants.PaymentMode)

#         next_sem_branch_registration_courses = get_registration_courses(next_sem_branch_courses)
#         next_sem_branch_registration_courses_data = []
#         for choices in next_sem_branch_registration_courses:
#             next_sem_branch_registration_courses_data.append(serializers.CurriculumSerializer(choices, many=True).data)
#         # next_sem_branch_registration_courses_data = serializers.CurriculumSerializer(next_sem_branch_registration_courses, many=True).data

#         final_registration_choices = get_registration_courses(get_branch_courses(request.user, user_sem, user_branch))
#         final_registration_choices_data = []
#         for choices in final_registration_choices:
#             final_registration_choices_data.append(serializers.CurriculumSerializer(choices, many=True).data)

#         performance_list = []
#         result_announced = False
#         for i in currently_registered_courses:
#             try:
#                 performance_obj = obj.semestermarks_set.all().filter(curr_id = i).first()
#             except:
#                 performance_obj = None
#             performance_list.append(performance_obj)
#         performance_list_data = serializers.SemesterMarksSerializer(performance_list, many=True).data

#         thesis_request_list = serializers.ThesisTopicProcessSerializer(obj.thesistopicprocess_set.all(), many=True).data

#         pre_existing_thesis_flag = True if obj.thesistopicprocess_set.all() else False

#         current_sem_branch_courses = get_branch_courses(current_user, user_sem, user_branch)

#     #     pre_registration_date_flag = get_pre_registration_eligibility(current_date)
#         final_registration_date_flag = get_final_registration_eligibility(current_date)

#         add_or_drop_course_date_flag = get_add_or_drop_course_date_eligibility(current_date)

#         student_registration_check_pre = obj.studentregistrationcheck_set.all().filter(semester=user_sem+1)
#         student_registration_check_final = obj.studentregistrationcheck_set.all().filter(semester=user_sem)
#         pre_registration_flag = False
#         final_registration_flag = False
#         if(student_registration_check_pre):
#             pre_registration_flag = student_registration_check_pre.pre_registration_flag
#         if(student_registration_check_final):
#             final_registration_flag = student_registration_check_final.final_registration_flag

#         teaching_credit_registration_course = None
#         if phd_flag:
#             teaching_credit_registration_course = Curriculum.objects.all().filter(batch = 2016, sem =6)
#         teaching_credit_registration_course_data = serializers.CurriculumSerializer(teaching_credit_registration_course, many=True).data

#         if student_flag:
#             try:
#                 due = obj.dues_set.get()
#                 lib_d = due.library_due
#                 pc_d = due.placement_cell_due
#                 hos_d = due.hostel_due
#                 mess_d = due.mess_due
#                 acad_d = due.academic_due
#             except:
#                 lib_d, pc_d, hos_d, mess_d, acad_d = 0, 0, 0, 0, 0

#         tot_d = lib_d + acad_d + pc_d + hos_d + mess_d

#         registers = obj.register_set.all()
#         course_list = []
#         for i in registers:
#             course_list.append(i.curr_id)
#         attendence = []
#         for i in course_list:
#             instructors = i.curriculum_instructor_set.all()
#             pr,ab=0,0
#             for j in list(instructors):

#                 presents = obj.student_attendance_set.all().filter(instructor_id=j, present=True)
#                 absents = obj.student_attendance_set.all().filter(instructor_id=j, present=False)
#                 pr += len(presents)
#                 ab += len(absents)
#             attendence.append((i,pr,pr+ab))
#         attendance_data = {}
#         for course in attendence:
#             attendance_data[course[0].course_id.course_name] = {
#                 'present' : course[1],
#                 'total' : course[2]
#             }

#         branchchange_flag = False
#         if user_sem == 2:
#             branchchange_flag=True

#         faculty_list = serializers.HoldsDesignationSerializer(get_faculty_list(), many=True).data

#         resp = {
#             'details': details,
#             'currently_registered': currently_registered_courses_data,
#             # 'pre_registered_courses' : pre_registered_courses_data,
#             # 'pre_registered_courses_show' : pre_registered_courses_show_data,
#             'final_registered_courses' : final_registered_courses_data,
#             'current_credits' : current_credits,
#             'courses_list': next_sem_branch_courses_data,
#             'fee_payment_mode_list' : fee_payment_mode_list,
#             'next_sem_branch_registration_courses' : next_sem_branch_registration_courses_data,
#             'final_registration_choices' : final_registration_choices_data,
#             'performance_list' : performance_list_data,
#             'thesis_request_list' : thesis_request_list,
#             'student_flag' : student_flag,
#             'ug_flag' : ug_flag,
#             'masters_flag' : masters_flag,
#             'phd_flag' : phd_flag,
#             'fac_flag' : fac_flag,
#             'des_flag' : des_flag,
#             'thesis_flag' : pre_existing_thesis_flag,
#             'drop_courses_options' : currently_registered_courses_data,
#             # 'pre_registration_date_flag': pre_registration_date_flag,
#             'final_registration_date_flag': final_registration_date_flag,
#             'add_or_drop_course_date_flag': add_or_drop_course_date_flag,
#             # 'pre_registration_flag' : pre_registration_flag,
#             'final_registration_flag': final_registration_flag,
#             'teaching_credit_registration_course' : teaching_credit_registration_course_data,
#             'lib_d':lib_d,
#             'acad_d':acad_d,
#             'mess_d':mess_d,
#             'pc_d':pc_d,
#             'hos_d':hos_d,
#             'tot_d':tot_d,
#             'attendance': attendance_data,
#             'Branch_Change_Flag':branchchange_flag
#             # 'faculty_list' : faculty_list
#         }
#     return Response(data=resp, status=status.HTTP_200_OK)






















#               These apis are not needed in this module



# @api_view(['POST'])
# def add_thesis(request):
#     current_user = request.user
#     profile = current_user.extrainfo
#     if profile.user_type == 'student':
#         if not 'thesis_topic' in request.data:
#             return Response({'error':'Thesis topic is required'}, status=status.HTTP_400_BAD_REQUEST)
#         if not 'research_area' in request.data:
#             return Response({'error':'Research area is required'}, status=status.HTTP_400_BAD_REQUEST)
#         if 'supervisor_id' in request.data:
#             try:
#                 supervisor_faculty = User.objects.get(username=request.data['supervisor_id'])
#                 supervisor_faculty = supervisor_faculty.extrainfo
#                 request.data['supervisor_id'] = supervisor_faculty
#             except:
#                 return Response({'error':'Wrong supervisor id. User does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
#         else:
#             return Response({'error':'supervisor id is required'}, status=status.HTTP_400_BAD_REQUEST)
#         if 'co_supervisor_id' in request.data:
#             try:
#                 co_supervisor_faculty = User.objects.get(username=request.data['co_supervisor_id'])
#                 co_supervisor_faculty = co_supervisor_faculty.extrainfo
#                 request.data['co_supervisor_id'] = co_supervisor_faculty
#             except:
#                 return Response({'error':'Wrong co_supervisor id. User does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
#         else:
#             co_supervisor_faculty = None
#         if 'curr_id' in request.data:
#             curr_id = None
#         student = profile.student
#         request.data['student_id'] = profile
#         request.data['submission_by_student'] = True
#         serializer = serializers.ThesisTopicProcessSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         else:
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#     else:
#         return Response({'error':'Cannot add thesis'}, status=status.HTTP_400_BAD_REQUEST)

















# @api_view(['PUT'])
# def approve_thesis(request, id):
#     current_user = request.user
#     profile = current_user.extrainfo
#     if profile.user_type == 'faculty':
#         try:
#             thesis = ThesisTopicProcess.objects.get(id=id)
#         except:
#             return Response({'error':'This thesis does not exist'}, status=status.HTTP_400_BAD_REQUEST)
#         if 'member1' in request.data:
#             try:
#                 user1 = User.objects.get(username=request.data['member1'])
#                 member1 = user1.extrainfo
#                 request.data['member1'] = member1
#             except:
#                 return Response({'error':'Wrong username of member 1. User does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
#         else:
#             return Response({'error':'Member 1 is required'}, status=status.HTTP_400_BAD_REQUEST)
#         if 'member2' in request.data:
#             try:
#                 user2 = User.objects.get(username=request.data['member2'])
#                 member2 = user2.extrainfo
#                 request.data['member2'] = member2
#             except:
#                 return Response({'error':'Wrong username of member 2. User does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
#         else:
#             return Response({'error':'Member 2 is required'}, status=status.HTTP_400_BAD_REQUEST)
#         if 'member3' in request.data:
#             try:
#                 user3 = User.objects.get(username=request.data['member3'])
#                 member3 = user3.extrainfo
#                 request.data['member3'] = member3
#             except:
#                 return Response({'error':'Wrong username of member 3. User does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
#         else:
#             member3 = None
#         if not 'approval' in request.data:
#             return Response({'error':'Approval value is required.'}, status=status.HTTP_400_BAD_REQUEST)
#         elif request.data['approval'] != 'yes' and request.data['approval'] != 'no':
#             return Response({'error':'Wrong approval value provided. Approval value should be yes or no'}, status=status.HTTP_400_BAD_REQUEST)
#         if request.data['approval'] == 'yes':
#             request.data.pop('approval', None)
#             request.data['pending_supervisor'] = False
#             request.data['approval_supervisor'] = True
#             request.data['forwarded_to_hod'] = True
#             request.data['pending_hod'] = True
#         else:
#             request.data.pop('approval', None)
#             request.data['pending_supervisor'] = False
#             request.data['approval_supervisor'] = False
#             request.data['forwarded_to_hod'] = False
#             request.data['pending_hod'] = False
#         serializer = serializers.ThesisTopicProcessSerializer(thesis, data=request.data, partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         else:
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#     else:
#         return Response({'error':'Cannot approve thesis'}, status=status.HTTP_400_BAD_REQUEST)

#--------------------------------------- New APIs Made for React ----------------------------------------------------------

# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# @authentication_classes([TokenAuthentication])
# def student_next_sem_courses(request):
#     """
#     REST API endpoint to return the courses_list as JSON.  Uses DRF authentication.
#     """

#     user_details = ExtraInfo.objects.select_related('user', 'department').get(user=request.user) # Changed to user=request.user
#     des = HoldsDesignation.objects.all().select_related().filter(user=request.user).first()

#     if str(des.designation) != "student":
#         return Response({"error": "User is not a student"}, status=status.HTTP_403_FORBIDDEN)  # 403 Forbidden - DRF style

#     obj = Student.objects.select_related('id', 'id__user', 'id__department').get(id=user_details.id)
#     batch = obj.batch_id
#     curr_id = batch.curriculum

#     try:
#         semester_no = obj.curr_semester_no
#         sem_no = semester_no + 1
#         next_sem_id = Semester.objects.get(curriculum=curr_id, semester_no=sem_no)
#     except Semester.DoesNotExist:  # Handle the case where next semester doesn't exist.
#         return Response({"error": "Next semester not found"}, status=status.HTTP_404_NOT_FOUND)


#     # Serialize the data (using DRF serializers is highly recommended)
#     course_slot = CourseSlot.objects.all().filter(semester_id = next_sem_id).prefetch_related(Prefetch('courses', queryset=Courses.objects.all()))
#     print(course_slot[0].courses)
#     serializer = serializers.CourseSlotSerializer(course_slot, many=True) # Assuming you have a CourseSerializer
#     courses_list_data = serializer.data

#     return Response({"courses_list": courses_list_data}, status=status.HTTP_200_OK)

# @api_view(['GET'])
# @authentication_classes([TokenAuthentication])
# @permission_classes([IsAuthenticated])
# def current_courseregistration(request):
#     try:
#         current_user = request.user
#         user_details = current_user.extrainfo

#         student = Student.objects.get(id=user_details)

#         current_semester = student.curr_semester_no

#         current_courses = course_registration.objects.filter(
#             student_id=student, semester_id__semester_no=current_semester
#         )
#         print(current_courses)

#         serializer = serializers.CourseRegistrationSerializer(current_courses, many=True)
#         print(serializer.data)
#         return Response(serializer.data, status=status.HTTP_200_OK)

#     except Student.DoesNotExist:
#         return Response({"error": "Student profile not found"}, status=status.HTTP_404_NOT_FOUND)
#     except Exception as e:
#         return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@role_required(['student'])
def final_registration_page(request):
    try:
        current_user = request.user
        user_details = current_user.extrainfo
        student = Student.objects.get(id=user_details)
        curr_id = student.batch_id.curriculum
        next_sem_id = Semester.objects.get(curriculum=curr_id, semester_no=student.curr_semester_no+1)
        current_date = date_time.date()
        final_registration_date_flag = get_final_registration_eligibility(current_date)
        student_registration_check = get_student_registrtion_check(student, next_sem_id)
        final_registration_flag = False
        if student_registration_check:
            final_registration_flag = student_registration_check.final_registration_flag

        final_registration = FinalRegistration.objects.filter(
            student_id=user_details.id, semester_id=next_sem_id
        )
        if final_registration.exists():
            final_registration = serializers.FinalRegistrationSerializer(final_registration, many=True).data
        else:
            final_registration = None
        resp = {
            'frd': final_registration_date_flag,
            'final_registration_flag': final_registration_flag,
            'final_registration': final_registration,
        }
        print(resp)
        return Response(data=resp, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@role_required(['acadadmin'])
def student_list(request):
    if request.method == 'POST':
        excel_export = request.GET.get("excel_export", "false")
        data = json.loads(request.body)
        batch = data.get('batch')
        print(batch)
        
        year = demo_date.year
        month = demo_date.month
        yearr = f'{year}-{year+1}'
        semflag = 1 if month >= 7 else 2
        queryflag = 1

        batch_id = Batch.objects.get(id=batch)
        student_obj = FeePayments.objects.all().select_related('student_id').filter(student_id__batch_id=batch_id)
        print(student_obj)

        if excel_export == "false":
            if student_obj:
                reg_table = list(student_obj.prefetch_related('student_id__studentregistrationchecks')
                    .filter(semester_id=student_obj[0].semester_id, student_id__studentregistrationchecks__final_registration_flag=True, 
                            student_id__finalregistration__verified=False, student_id__finalregistration__semester_id=student_obj[0].semester_id)
                    .select_related('student_id', 'student_id__id', 'student_id__id__user', 'student_id__id__department')
                    .values(
                        'student_id__id', 'student_id__id__user__first_name', 'student_id__id__user__last_name',
                        'student_id__batch', 'student_id__id__department__name', 'student_id__programme',
                        'student_id__curr_semester_no', 'student_id__id__sex', 'student_id__id__phone_no',
                        'student_id__category', 'student_id__specialization', 'mode', 'transaction_id', 'deposit_date',
                        'fee_paid', 'utr_number', 'reason', 'fee_receipt', 'actual_fee',
                        'student_id__id__user__username'
                    ).distinct())

            else:
                reg_table = []

            response_data = {
                'date': {'year': yearr, 'month': month, 'semflag': semflag, 'queryflag': queryflag},
                'students': reg_table
            }

            return JsonResponse(response_data, safe=False)

        elif excel_export == "true":
            if student_obj:
                table = [("Admission Year", "Semester", "Roll Number", "Full Name", "Program", "Discipline", "Specialization", "Gender", "Category", "Mobile Number", "Actual Fee", "Fee Paid By Student", "Reason", "Date", "Mode", "UTR Number", "Fee Receipt")]
                
                table += student_obj.prefetch_related('student_id__studentregistrationchecks').filter(semester_id=student_obj[0].semester_id, student_id__studentregistrationchecks__final_registration_flag=True).select_related('student_id', 'student_id__id', 'student_id__id__user', 'student_id__id__department').annotate(
                    admission_year = F('student_id__batch'),
                    semester=F('student_id__curr_semester_no') + 1,
                    roll_no=F('student_id__id__user__username'),
                    full_name=Concat('student_id__id__user__first_name', Value(' '), 'student_id__id__user__last_name'),
                    program=F('student_id__programme'),
                    discipline=F('student_id__id__department__name'),
                    specialization=F('student_id__specialization'),
                    gender=F('student_id__id__sex'),
                    category=F('student_id__category'),
                    phone_no=F('student_id__id__phone_no'),
                    date_deposited=Concat(Cast(ExtractDay('deposit_date'), CharField()), Value('/'),
                                      Cast(ExtractMonth('deposit_date'), CharField()), Value('/'),
                                      Cast(ExtractYear('deposit_date'), CharField()), output_field=CharField())
                    ).values_list('admission_year', 'semester', 'roll_no', 'full_name', 'program', 'discipline', 'specialization', 'gender', 'category', 'phone_no', 'actual_fee', 'fee_paid', 'reason', 'date_deposited', 'mode', 'utr_number', 'fee_receipt').distinct()

                excel_response = BytesIO()
                final_register_workbook = Workbook(excel_response)
                final_register_worksheet = final_register_workbook.add_worksheet()

                for i, row in enumerate(table):
                    for j, cell in enumerate(row):
                        final_register_worksheet.write(i, j, cell)

                final_register_workbook.close()
                excel_response.seek(0)

                response = HttpResponse(excel_response.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = f'attachment; filename="{batch_id.name}_{batch_id.discipline.acronym}_{batch_id.year}_final_registered.xlsx"'
                return response

            else:
                return JsonResponse({'error': 'No registered students found'}, status=404)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@role_required(['acadadmin'])
def course_list(request):
    request_body = json.loads(request.body)
    student_id = request_body['student_id']
    semester_no = request_body['semester_no']

    # final_registration_table = FinalRegistration.objects.all().filter(semester_id = semester_id, verified = False)
    # final = final_registration_table.filter(student_id = student_id, semester_id = semester_id)
    final = FinalRegistration.objects.all().filter(semester_id__semester_no = semester_no, student_id__id=student_id, verified = False)
    if final.exists():
        final_registration = serializers.FinalRegistrationSerializer(final, many=True).data
    else:
        final_registration = None
    resp = {
        'final_registration': final_registration,
    }
    return Response(data=resp, status=status.HTTP_200_OK)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@role_required(['acadadmin'])
def dropcourseadmin(request):
    try:
        reg_id = request.data.get('id')
        roll_no = request.data.get('roll_no')

        if not reg_id or not roll_no:
            return JsonResponse({'error': 'Missing registration ID or roll number'}, status=400)

        reg_id = int(reg_id)
        course_registration.objects.filter(id=reg_id).delete()

        return JsonResponse({'message': 'Success!'}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@role_required(['acadadmin'])
def acad_add_course(request):
    data = request.data
    for fld in ("roll_no", "semester_id", "courseslot_id", "course_id", "academic_year", "registration_type", "semester_type"):
        if not data.get(fld):
            return Response({ "error": f"{fld} is required" }, status=status.HTTP_400_BAD_REQUEST)
    student = get_object_or_404(Student, id=data["roll_no"].upper())
    semester = get_object_or_404(Semester,   id=data["semester_id"])
    slot     = get_object_or_404(CourseSlot, id=data["courseslot_id"])
    course   = get_object_or_404(Courses,     id=data["course_id"])
    session  = data["academic_year"]
    reg_type = data["registration_type"]
    old_id   = data.get("old_course")
    sem_type = data["semester_type"]
    with transaction.atomic():
        cr = course_registration.objects.create(
            student_id       = student,
            semester_id      = semester,
            course_slot_id   = slot,
            course_id        = course,
            session          = session,
            registration_type= reg_type,
            semester_type = sem_type,
            working_year = parse_academic_year(academic_year=session, semester_type=sem_type)[0]
        )
        if old_id:
            old = course_registration.objects.filter(id=old_id).first()
            if old:
                course_replacement.objects.create(
                    old_course_registration = old,
                    new_course_registration = cr,
                )

    return Response({ "message": "Course added successfully" }, status=status.HTTP_200_OK)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def academic_procedures_faculty_api(request):
    try:
        # Ensure the user is a faculty member
        if request.user.extrainfo.user_type != 'faculty':
            return Response({"error": "Unauthorized access. Faculty only."}, status=403)

        user_details = ExtraInfo.objects.select_related("department").get(user=request.user)

        # Get courses taught by the faculty
        courses = CourseInstructor.objects.filter(instructor_id=user_details.id).select_related("course_id")

        current_year = timezone.now().year
        response_data = []

        for course in courses:
            # Calculate academic year from calendar year + semester
            
            response_data.append({
                "course_id": course.course_id.id,
                "course_code": course.course_id.code,
                "course_name": course.course_id.name,
                "version": course.course_id.version,
                "semester_type": course.semester_type,
                "academic_year": course.academic_year,
            })

        return Response({"assigned_courses": response_data})

    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@role_required(['acadadmin'])
def search_preregistration(request):
    try:
        roll_no=request.data.get("roll_no")
        sem_no=request.data.get("sem_no")
        initial_registrations = InitialRegistration.objects.filter(
            student_id_id=roll_no, semester_id__semester_no=sem_no
        )
        student_registration_check = StudentRegistrationChecks.objects.filter(
            student_id_id=roll_no, semester_id__semester_no=sem_no
        ).first()
        initial = serializers.InitialRegistrationSerializer(initial_registrations, many=True)
        student_registration_check_data = serializers.StudentRegistrationChecksSerializer(student_registration_check)
        return Response({
            "initial_registration": initial.data,  # Send serialized initial registrations
            "student_registration_check": student_registration_check_data.data if student_registration_check else None
        })
    except Exception as e:
        return Response(
            {"error": f"An error occurred: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@role_required(['acadadmin'])
def delete_preregistration(request):
    try:
        # Extract roll_no and sem_no from the request
        roll_no = request.data.get("roll_no")
        sem_no = request.data.get("sem_no")

        # Validate input data
        if not roll_no or not sem_no:
            return Response(
                {"error": "Both roll_no and sem_no are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Delete initial registration entries
        initial_registrations = InitialRegistration.objects.filter(
            student_id_id=roll_no, semester_id__semester_no=sem_no
        )
        initial_count = initial_registrations.delete()

        # Delete student registration check entries
        student_registration_check = StudentRegistrationChecks.objects.filter(
            student_id_id=roll_no, semester_id__semester_no=sem_no
        )
        student_registration_check_count = student_registration_check.delete()

        # Return a success response with counts of deleted entries
        return Response({
            "message": "Successfully Deleted."
        })

    except Exception as e:
        return Response(
            {"error": f"An error occurred: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@role_required(['acadadmin'])
def allot_courses(request):
    if 'allotedCourses' not in request.FILES:
        return Response({'error': 'Excel file not provided.'},
                        status=status.HTTP_400_BAD_REQUEST)

    batch_id = request.data.get('batch')
    sem_no = request.data.get('semester')
    sem_type = request.data.get('semester_type')
    academic_year = request.data.get('academic_year')
    working_year, _ = parse_academic_year(academic_year=academic_year, semester_type=sem_type)

    if not all([batch_id, sem_no, sem_type, academic_year]):
        return Response({'error': 'Missing required fields.'},
                        status=status.HTTP_400_BAD_REQUEST)

    try:
        sem_no = int(sem_no)
    except ValueError:
        return Response({'error': 'Semester must be integer.'},
                        status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            batch = Batch.objects.get(id=batch_id)
            sem = Semester.objects.get(
                curriculum=batch.curriculum,
                semester_no=sem_no
            )
            book = xlrd.open_workbook(file_contents=request.FILES['allotedCourses'].read())
            sheet = book.sheet_by_index(0)

            checks, pre_regs, final_regs, course_regs = [], [], [], []
            seen = set()

            for i in range(1, sheet.nrows):

                try:
                    roll_no = str(sheet.cell_value(i,0)).split('.')[0].strip()
                    slot_name = sheet.cell_value(i,1).strip()
                    code = sheet.cell_value(i,2).strip()

                    # user = User.objects.get(username=roll_no)
                    student = Student.objects.get(id__user__username=roll_no)
                    slot = CourseSlot.objects.get(name=slot_name, semester=sem)
                    course = slot.courses.get(code=code)
                    if roll_no not in seen:
                        checks.append(StudentRegistrationChecks(
                            student_id=student,
                            semester_id=sem,
                            pre_registration_flag=True,
                            final_registration_flag=True
                        ))
                        seen.add(roll_no)

                    pre_regs.append(InitialRegistration(
                        student_id=student,
                        course_slot_id=slot,
                        course_id=course,
                        semester_id=sem,
                        priority=1
                    ))
                    final_regs.append(FinalRegistration(
                        student_id=student,
                        course_slot_id=slot,
                        course_id=course,
                        semester_id=sem,
                        verified=True
                    ))
                    course_regs.append(course_registration(
                        session=academic_year,
                        working_year = working_year,
                        course_id=course,
                        semester_id=sem,
                        student_id=student,
                        course_slot_id=slot,
                        semester_type = sem_type
                    ))
                except Exception as e:
                    print(e, "-----", roll_no, slot_name, code)

            StudentRegistrationChecks.objects.bulk_create(checks, ignore_conflicts=True)
            InitialRegistration.objects.bulk_create(pre_regs, ignore_conflicts=True)
            FinalRegistration.objects.bulk_create(final_regs, ignore_conflicts=True)
            course_registration.objects.bulk_create(course_regs, ignore_conflicts=True)

        return Response({'message': 'Successfully uploaded!'})
    except Batch.DoesNotExist:
        return Response({'error': 'Invalid batch id.'}, status=status.HTTP_400_BAD_REQUEST)
    except Semester.DoesNotExist:
        return Response({'error': 'Invalid semester or type.'}, status=status.HTTP_400_BAD_REQUEST)
    except xlrd.XLRDError:
        return Response({'error': 'Invalid Excel format.'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print(e)
        return Response({'error': f'Processing error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
@role_required(['student'])
def student_next_sem_courses(request):
    """
    REST API endpoint to return the courses_list as JSON.  Uses DRF authentication.
    """

    user_details = ExtraInfo.objects.select_related('user', 'department').get(user=request.user) # Changed to user=request.user
    des = HoldsDesignation.objects.all().select_related().filter(user=request.user).first()

    if str(des.designation) != "student":
        return Response({"error": "User is not a student"}, status=status.HTTP_403_FORBIDDEN)  # 403 Forbidden - DRF style

    obj = Student.objects.select_related('id', 'id__user', 'id__department').get(id=user_details.id)
    batch = obj.batch_id
    curr_id = batch.curriculum

    try:
        semester_no = obj.curr_semester_no
        sem_no = semester_no + 1
        next_sem_id = Semester.objects.get(curriculum=curr_id, semester_no=sem_no)
    except Semester.DoesNotExist:  # Handle the case where next semester doesn't exist.
        return Response({"error": "Next semester not found"}, status=status.HTTP_404_NOT_FOUND)


    # Serialize the data (using DRF serializers is highly recommended)
    course_slot = CourseSlot.objects.all().filter(semester_id = next_sem_id).prefetch_related(Prefetch('courses', queryset=Courses.objects.all()))
    print(course_slot[0].courses)
    serializer = serializers.CourseSlotSerializer(course_slot, many=True) # Assuming you have a CourseSerializer
    courses_list_data = serializer.data

    return Response({"courses_list": courses_list_data}, status=status.HTTP_200_OK)

# @api_view(['GET'])
# @authentication_classes([TokenAuthentication])
# @permission_classes([IsAuthenticated])
# def current_courseregistration(request):
#     try:
#         current_user = request.user
#         user_details = current_user.extrainfo

#         student = Student.objects.get(id=user_details)

#         current_semester = student.curr_semester_no
#         print(current_semester)

#         try:
#             semester = Semester.objects.get(curriculum=student.batch_id.curriculum, semester_no=current_semester)
#         except Semester.DoesNotExist:
#             return JsonResponse({"error": "semester not found."}, status=404)

#         print(student)
#         current_courses = course_registration.objects.filter(
#             student_id=student, semester_id=semester
#         )
#         print(current_courses)

#         serializer = serializers.CourseRegistrationSerializer(current_courses, many=True)
#         print(serializer.data)
#         return Response(serializer.data, status=status.HTTP_200_OK)

#     except Student.DoesNotExist:
#         return Response({"error": "Student profile not found"}, status=status.HTTP_404_NOT_FOUND)
#     except Exception as e:
#         return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@role_required(['student'])
def course_registration_view(request):
    try:
        current_user = request.user
        user_details = current_user.extrainfo
        student = Student.objects.get(id=user_details)

        semester_no = request.query_params.get('semester', student.curr_semester_no)
        semester_type = request.query_params.get('semester_type', 'Even Semester' if student.curr_semester_no%2==0 else 'Odd Semester')
        try:
            semester = Semester.objects.get(curriculum=student.batch_id.curriculum, semester_no=semester_no)
        except Semester.DoesNotExist:
            return JsonResponse({"error": "Semester not found."}, status=404)

        courses = course_registration.objects.filter(student_id=student, semester_id=semester, semester_type=semester_type)

        result = []
        for reg in courses:
            course_data = serializers.CourseRegistrationSerializer(reg).data

            replacements = course_replacement.objects.filter(old_course_registration=reg)
            replaced_by_list = []

            for replacement in replacements:
                new_reg = replacement.new_course_registration
                replaced_by_list.append({
                    "code": new_reg.course_id.code,
                    "name": new_reg.course_id.name,
                    "semester_no": new_reg.semester_id.semester_no,
                    "label" : make_label(new_reg.semester_id.semester_no, new_reg.semester_type)
                })

            course_data["replaced_by"] = replaced_by_list
            result.append(course_data)
        return Response({"reg_data": result, "sem_no": semester_no, "semester_type": semester_type}, status=status.HTTP_200_OK)

    except Student.DoesNotExist:
        return Response({"error": "Student profile not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def get_add_drop_replace_registration_eligibility(current_date, user_sem, year = datetime.datetime.now().year):
    try:
        add_drop_date = Calendar.objects.get(description=f"Add/Drop/Replace {user_sem} {year}")
        add_drop_start_date = add_drop_date.from_date
        add_drop_end_date = add_drop_date.to_date
        if current_date<add_drop_start_date:
            return JsonResponse({f"error": "Add/Drop/Replace will start from {add_drop_start_date} to {add_drop_end_date}"}, status=400)
        elif current_date > add_drop_end_date:
            return JsonResponse({f"error": "Add/Drop/Replace has ended"}, status=400)
    except Calendar.DoesNotExist:
        return JsonResponse({f"error": "Add/Drop/Replace Date is not yet Decided"}, status=400)
    except Exception as e:
        pass


def get_pre_registration_eligibility(current_date, user_sem, year = datetime.datetime.now().year):
    try:
        pre_registration_date = Calendar.objects.get(description=f"Pre Registration {user_sem} {year}")
        prd_start_date = pre_registration_date.from_date
        prd_end_date = pre_registration_date.to_date
        if current_date<prd_start_date:
            return JsonResponse({f"error": "Pre Registration will start from {prd_start_data} to {prd_end_date}"}, status=400)
        elif current_date > prd_end_date:
            return JsonResponse({f"error": "Pre Registration Registration has ended"}, status=400)
    except Calendar.DoesNotExist:
        return JsonResponse({f"error": "Pre Registration Date is not yet Decided"}, status=400)
    except Exception as e:
        pass

def get_swayam_registration_eligibility(current_date, user_sem, year = datetime.datetime.now().year):
    try:
        swayam_add_date = Calendar.objects.get(description=f"Swayam {user_sem} {year}")
        swayam_add_start_date = swayam_add_date.from_date
        swayam_add_end_date = swayam_add_date.to_date
        if current_date<swayam_add_start_date:
            return JsonResponse({f"error": "Swayam Registration will start from {swayam_add_start_date} to {swayam_add_end_date}"}, status=400)
        elif current_date > swayam_add_end_date:
            return JsonResponse({f"error": "Swayam Registration has ended"}, status=400)
    except Calendar.DoesNotExist:
        return JsonResponse({f"error": "Swayam Registration Date is not yet Decided"}, status=400)
    except Exception as e:
        pass

def get_student_registrtion_check(student, sem):
    return StudentRegistrationChecks.objects.filter(student_id=student, semester_id=sem).first()



def get_student_registrations(student, semester):
    """
    Returns a QuerySet of InitialRegistration entries for the given student and semester.
    
    Args:
        student (Student): The student instance.
        semester (Semester): The semester instance.
        
    Returns:
        QuerySet: Registrations for the student in the given semester.
    """
    return InitialRegistration.objects.filter(student_id=student, semester_id=semester)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@role_required(['student'])
def get_preregistration_data(request):
    """
    Returns the list of course slots available for the student's next semester,
    along with the list of courses available in each slot.
    If the student has already completed pre-registration, returns the registered
    courses with their priorities.
    """
    try:
        current_user = request.user
        user_details = current_user.extrainfo
        student = Student.objects.get(id=user_details)
        semester_no = student.curr_semester_no
        next_sem_no = semester_no+1
        try:
            next_semester = Semester.objects.get(curriculum=student.batch_id.curriculum, semester_no=next_sem_no)
        except Semester.DoesNotExist:
            return JsonResponse({"error": "Not Eligible for Pre Registration"}, status=400)

        # Check if the student has already completed pre-registration.
        registration_check = get_student_registrtion_check(student, next_semester)
        course_slots = CourseSlot.objects.filter(semester=next_semester)\
            .exclude(name__icontains='SW')
        data = []
        if registration_check and registration_check.pre_registration_flag:
            registrations = get_student_registrations(student, next_semester)
            regular_regs =  registrations.exclude(course_slot_id__name__icontains='BL')
            backlog_regs = registrations.filter(
                course_slot_id__name__startswith='BL'
            )
            # Build a lookup dictionary: {(slot_id, course_id): priority}
            reg_lookup = {
                (reg.course_slot_id.id if reg.course_slot_id else None, reg.course_id.id): reg.priority 
                for reg in regular_regs
            }
            for slot in course_slots:
                courses = slot.courses.all()
                # print(slot.id)
                course_choices = [
                    {
                        "id": course.id,
                        "code": course.code,
                        "name": course.name,
                        "credits": course.credit,
                        "priority": reg_lookup.get((slot.id, course.id), "")
                    }
                    for course in courses
                ]
                data.append({
                    "sno": slot.id,
                    "slot_name": slot.name,
                    "slot_type": slot.type,
                    "semester": next_sem_no,
                    "course_choices": course_choices,
                })

                backlog_data = []
                for reg in backlog_regs:
                    backlog_data.append({
                        "sno": reg.course_slot_id.id if reg.course_slot_id else None,
                        "slot_name": reg.course_slot_id.name if reg.course_slot_id else "Unknown",
                        "course_choices": [{
                            "id": reg.course_id.id,
                            "code": reg.course_id.code,
                            "name": reg.course_id.name
                        }],
                        "prev_registration": {
                            "id": reg.old_course_registration.id if reg.old_course_registration else "",
                            "code": reg.old_course_registration.course_id.code if reg.old_course_registration and reg.old_course_registration.course_id else "",
                            "name": reg.old_course_registration.course_id.name if reg.old_course_registration and reg.old_course_registration.course_id else "",
                            "semester_no": reg.old_course_registration.semester_id.semester_no if reg.old_course_registration and reg.old_course_registration.semester_id else "",
                        }
                    })
            return JsonResponse({"message": "Already registered", "data": data, "backlog_data":backlog_data}, safe=False)
        else:
            # If not already registered, return slots without pre-set priorities.
            eligibility_resp = get_pre_registration_eligibility(timezone.now().date(), next_sem_no)
            if isinstance(eligibility_resp, JsonResponse):
                return eligibility_resp
            prev_registrations = serializers.CourseRegistrationSerializer(course_registration.objects.filter(student_id=student), many=True).data
            for slot in course_slots:
                courses = slot.courses.all()
                course_choices = [
                    {
                        "id": course.id,
                        "code": course.code,
                        "name": course.name,
                        "credits": course.credit
                    }
                    for course in courses
                ]
                data.append({
                    "sno": slot.id,
                    "slot_name": slot.name,
                    "slot_type": slot.type,
                    "semester": next_sem_no,
                    "course_choices": course_choices,
                    "prev_registrations": prev_registrations
                })
            return JsonResponse(data, safe=False)
    except Student.DoesNotExist:
        return Response({"error": "Student profile not found"}, status=400)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@role_required(['student'])
def submit_preregistration(request):
    """
    Expects a POST request with JSON data containing an array "registrations".
    Each registration entry should include:
      - slot_id: the ID of the CourseSlot
      - course_id: the chosen Course ID for that slot
      - priority: the priority assigned by the student
    If the student has not pre-registered, the registrations will be created.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=400)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return Response({"Invalid JSON"})

    registrations = data.get("registrations", [])
    backlog_registrations = data.get("backlog_registrations", [])
    try:
        current_user = request.user
        user_details = current_user.extrainfo
        student = Student.objects.get(id=user_details)
        semester_no = student.curr_semester_no
        # Here you may want to use next_sem_no = semester_no + 1 if that is the logic.
        next_sem_no = semester_no+1
        try:
            next_semester = Semester.objects.get(curriculum=student.batch_id.curriculum, semester_no=next_sem_no)
        except Semester.DoesNotExist:
            return JsonResponse({"error": "Not Eligible for Pre Registration"}, status=400)
        eligibility_resp = get_pre_registration_eligibility(timezone.now().date(), next_sem_no)
        if isinstance(eligibility_resp, JsonResponse):
            return eligibility_resp
    except Student.DoesNotExist:
        return Response({"error": "Student profile not found"}, status=400)

    for reg in registrations:
        slot_id = reg.get("slot_id")
        course_id = reg.get("course_id")
        priority = reg.get("priority")

        InitialRegistration.objects.create(
            course_id_id=course_id,
            semester_id_id=next_semester.id,
            student_id=student,
            course_slot_id_id=slot_id,
            priority=priority,
            timestamp=timezone.now()
        )

    for reg in backlog_registrations:
        slot_id = reg.get("slot_id")
        course_id = reg.get("course_id")
        priority = reg.get("priority")
        prev_registration_id = reg.get("prev_registration_id")

        InitialRegistration.objects.create(
            course_id_id=course_id,
            semester_id_id=next_semester.id,
            student_id=student,
            course_slot_id_id=slot_id,
            priority=priority,
            registration_type='Backlog',
            old_course_registration_id = prev_registration_id,
            timestamp=timezone.now()
        )
    
    # Optionally, update the StudentRegistrationChecks record to mark pre-registration as complete.
    reg_check, created = StudentRegistrationChecks.objects.get_or_create(
        student_id=student, semester_id_id=next_semester.id,
        defaults={'pre_registration_flag': True}
    )
    if not created:
        reg_check.pre_registration_flag = True
        reg_check.save()
        
    return JsonResponse({"status": "success"}, status=201)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@role_required(['student'])
def get_swayam_registration_data(request):
    """
    Returns the list of course slots available for Swayam registration for the student's next semester,
    along with the list of courses available in each slot.
    (Only course slots whose name starts with "SW" are returned.
    No registration check is performed.)
    """
    try:
        current_user = request.user
        user_details = current_user.extrainfo  # assuming extrainfo holds the student id/reference
        student = Student.objects.get(id=user_details)
        semester_no = student.curr_semester_no
        next_sem_no = semester_no + 1  # adjust if needed (e.g. semester_no+1)
        try:
            next_semester = Semester.objects.get(
                curriculum=student.batch_id.curriculum, 
                semester_no=next_sem_no
            )
        except Semester.DoesNotExist:
            return JsonResponse({"error": "Not Eligible for Swayam Registration"}, status=400)

        eligibility_resp = get_swayam_registration_eligibility(timezone.now().date(), next_sem_no)
        if isinstance(eligibility_resp, JsonResponse):
            return eligibility_resp
        # For Swayam registration, fetch only those course slots whose name starts with "SW".
        course_slots = CourseSlot.objects.filter(semester=next_semester, name__startswith="SW")
        data = []
        for slot in course_slots:
            courses = slot.courses.all()
            course_choices = [
                {
                    "id": course.id,
                    "code": course.code,
                    "name": course.name,
                    "credits": course.credit
                }
                for course in courses
            ]
            data.append({
                "sno": slot.id,
                "slot_name": slot.name,
                "slot_type": slot.type,
                "semester": next_sem_no,
                "course_choices": course_choices,
            })
        return JsonResponse(data, safe=False)
    except Student.DoesNotExist:
        return Response({"error": "Student profile not found"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@role_required(['student'])
def submit_swayam_registration(request):
    """
    Accepts a POST request with JSON data for Swayam registration.
    
    Expected payload structure:
    {
         "registrations": [
              {
                 "slot_id": <slot id>,
                 "course_id": <course id>,
                 "selected_option": "<selected option string>",
                 "remark": "<remark>"
              },
              ...
         ]
    }
    
    For each registration entry, a record is created in InitialRegistrations.
    Since Swayam courses are not tied to a course slot in the same way as other courses,
    the fields course_slot_id and priority are set to None.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=400)
    try:
        payload = json.loads(request.body)
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    try:
        current_user = request.user
        user_details = current_user.extrainfo
        student = Student.objects.get(id=user_details)
        semester_no = student.curr_semester_no
        next_sem_no = semester_no + 1
        try:
            semester = Semester.objects.get(
                curriculum=student.batch_id.curriculum, 
                semester_no=next_sem_no
            )
        except Semester.DoesNotExist:
            return JsonResponse({"error": "Not Eligible for Swayam Registration"}, status=400)
    except Student.DoesNotExist:
        return Response({"error": "Student not found"}, status=404)
    
    eligibility_resp = get_swayam_registration_eligibility(timezone.now().date(), next_sem_no)
    if isinstance(eligibility_resp, JsonResponse):
        return eligibility_resp
    registrations = payload.get("registrations", [])
    for reg in registrations:
        slot_id = reg.get("slot_id")
        course_id = reg.get("course_id")
        selected_option = reg.get("selected_option")
        remark = reg.get("remark")
        print(selected_option, course_id, remark)
        try:
            course = Courses.objects.get(id=course_id)
        except Courses.DoesNotExist:
            continue
        
        course_registration.objects.create(
            course_id=course,
            semester_id_id=semester.id,
            student_id=student,
            course_slot_id_id=slot_id, 
        )
    return JsonResponse({"status": "success"}, status=201)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@role_required(['acadadmin'])
def get_add_course_slots(request):
    """
    GET /api/course-slots/?semester_id=<id>
    Returns JSON list of { id, name } for all slots in that semester.
    """
    sem_id = request.query_params.get("semester_id")
    if not sem_id:
        return Response(
            {"error": "semester_id query parameter is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # ensure the semester exists (404 if not)
    get_object_or_404(Semester, id=sem_id)

    # fetch slots and return only id & name
    slots = CourseSlot.objects.filter(semester_id=sem_id).values("id", "name")
    return Response(list(slots), status=status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@role_required(['acadadmin'])
def get_add_course_courses(request):
    """
    GET /api/courses/?courseslot_id=<id>
    Returns JSON list of { id, code, name, credit } for all courses in that slot.
    """
    slot_id = request.query_params.get("courseslot_id")
    if not slot_id:
        return Response(
            {"error": "courseslot_id query parameter is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # ensure the slot exists (404 if not)
    slot = get_object_or_404(CourseSlot, id=slot_id)

    # via the M2M relationship .courses
    courses = slot.courses.all().values("id", "code", "name", "credit")
    return Response(list(courses), status=status.HTTP_200_OK)


def roman_to_int(s):
    roman = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6,
             'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10}
    return roman.get(s.strip().upper())

@api_view(['POST'])
@parser_classes([MultiPartParser])
@role_required(['acadadmin'])
def upload_excel_replacement(request):
    file = request.FILES.get('file')
    if not file:
        return Response({'error': 'No file uploaded'}, status=400)

    try:
        df = pd.read_excel(file)
    except Exception as e:
        return Response({'error': f'Failed to read Excel: {e}'}, status=400)

    expected = {'student_id', 'old_course_code', 'new_course_code',
                'old_semester_roman', 'new_semester_number'}
    if not expected.issubset(df.columns):
        return Response(
            {'error': f'Missing columns: {expected - set(df.columns)}'},
            status=400
        )

    valid_entries = []
    failed_rows = []

    # Validate all rows first
    for idx, row in df.iterrows():
        sid = str(row['student_id']).strip()
        old_code = str(row['old_course_code']).strip()
        new_code = str(row['new_course_code']).strip()
        old_rom = str(row['old_semester_roman']).strip()
        new_sem = int(row['new_semester_number'])

        sem_old = roman_to_int(old_rom)
        if sem_old is None:
            msg = f'Row {idx+2} Invalid Roman numeral {old_rom}'
            print(msg)
            failed_rows.append(msg)
            continue

        try:
            student = Student.objects.get(id_id=sid)
        except Student.DoesNotExist:
            msg = f'Row {idx+2} Student {sid} not found'
            print(msg)
            failed_rows.append(msg)
            continue

        try:
            old_reg = course_registration.objects.get(
                student_id=student,
                course_id__code=old_code,
                semester_id__semester_no=sem_old
            )
        except course_registration.DoesNotExist:
            msg = f'Row {idx+2} Old registration not found: {sid}, {old_code}, {sem_old}'
            print(msg)
            failed_rows.append(msg)
            continue

        try:
            new_reg = course_registration.objects.get(
                student_id=student,
                course_id__code=new_code,
                semester_id__semester_no=new_sem
            )
        except course_registration.DoesNotExist:
            msg = f'Row {idx+2} New registration not found: {sid}, {new_code}, {new_sem}'
            print(msg)
            failed_rows.append(msg)
            continue

        valid_entries.append((old_reg, new_reg))

    # Abort if any error was found
    if failed_rows:
        return Response({
            'error': 'Some rows are invalid. No changes were made.',
            'failed_rows': failed_rows
        }, status=400)

    # All rows valid: Perform atomic save
    try:
        with transaction.atomic():
            for old_reg, new_reg in valid_entries:
                course_replacement.objects.create(
                    old_course_registration=old_reg,
                    new_course_registration=new_reg
                )
    except Exception as e:
        return Response({'error': str(e)}, status=400)

    return Response({
        'message': f'{len(valid_entries)} replacements added successfully',
        'failed_rows': []
    }, status=200)



# ─── Mapping HOD designation → allowed Student.specialization ─────────────
HOD_SPECIALIZATION_MAPPING = {
    # designation code without spaces/brackets → list of allowed specializations
    'ECE': ['PNC'],        # HOD(ECE) can only assign PNC students
    'CSE': ['AIML'],       # HOD(CSE) can only assign AIML students
    # add more as needed
}

def check_role(request, required_role):
    role = request.query_params.get('role') if request.method=='GET' else request.data.get('role')
    return role == required_role

def get_allowed_specs(user):
    """
    Find the HOD's designation name (e.g. "HOD (ECE)"), extract "ECE",
    and return the list of allowed student specializations.
    """
    des = HoldsDesignation.objects.filter(
        working=user, designation__name__startswith='HOD'
    ).first()
    if not des:
        return None
    # extract between parentheses
    raw = des.designation.name
    try:
        code = raw.split('(',1)[1].split(')',1)[0].strip()
    except:
        return None
    return HOD_SPECIALIZATION_MAPPING.get(code)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def tas_list(request):
    """GET /api/tas/ → return all TA usernames."""
    data = [{'username': s.id.user.username} for s in Student.objects.all()]
    return Response({'tas': data})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def faculties_list(request):
    """GET /api/faculties/ → return all Faculty usernames."""
    data = [{'username': f.id.user.username} for f in Faculty.objects.all()]
    return Response({'faculties': data})


# --- HOD endpoints ---

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def hod_students(request):
    if not check_role(request,'hod'):
        return Response({'error':'role=hod required'}, status=status.HTTP_403_FORBIDDEN)
    allowed = get_allowed_specs(request.user)
    if not allowed:
        return Response({'error':'Invalid HOD designation or no mapping'}, status=status.HTTP_403_FORBIDDEN)
    qs = Student.objects.filter(specialization__in=allowed)
    data = [{'username': s.id.user.username, 'batch': s.batch} for s in qs]
    return Response({'students': data})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def hod_assign_manual(request):
    if not check_role(request,'hod'):
        return Response({'error':'role=hod required'}, status=status.HTTP_403_FORBIDDEN)
    allowed = get_allowed_specs(request.user)
    if not allowed:
        return Response({'error':'Invalid HOD designation or no mapping'}, status=status.HTTP_403_FORBIDDEN)
    d = request.data
    try:
        stu = Student.objects.get(id__user__username=d['ta_username'])
    except Student.DoesNotExist:
        return Response({'error':'TA not found'}, status=status.HTTP_404_NOT_FOUND)
    if stu.specialization not in allowed:
        return Response({'error':'Specialization mismatch'}, status=status.HTTP_403_FORBIDDEN)
    try:
        fac = Faculty.objects.get(id__user__username=d['faculty_username'])
    except Faculty.DoesNotExist:
        return Response({'error':'Faculty not found'}, status=status.HTTP_404_NOT_FOUND)

    try:
        a = Assignment.objects.create(
            ta=stu, faculty=fac,
            start_year=int(d['start_year']),  start_month=int(d['start_month']),
            end_year=int(d['end_year']),      end_month=int(d['end_month'])
        )
        return Response({'assignment_id': a.id}, status=status.HTTP_201_CREATED)
    except KeyError:
        return Response({'error':'Missing field'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error':str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def hod_upload_excel(request):
    if not check_role(request,'hod'):
        return Response({'error':'role=hod required'}, status=status.HTTP_403_FORBIDDEN)
    allowed = get_allowed_specs(request.user)
    if not allowed:
        return Response({'error':'Invalid HOD designation or no mapping'}, status=status.HTTP_403_FORBIDDEN)
    f = request.FILES.get('file')
    if not f:
        return Response({'error':'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        df = pd.read_excel(f)
    except:
        return Response({'error':'Invalid Excel file'}, status=status.HTTP_400_BAD_REQUEST)

    created, errors = [], []
    for idx, row in df.iterrows():
        try:
            stu = Student.objects.get(id__user__username=row['ta_username'])
            if stu.specialization not in allowed:
                raise PermissionError('Specialization mismatch')
            fac = Faculty.objects.get(id__user__username=row['faculty_username'])
            a = Assignment.objects.create(
                ta=stu, faculty=fac,
                start_year=int(row['start_year']), start_month=int(row['start_month']),
                end_year=int(row['end_year']),     end_month=int(row['end_month'])
            )
            created.append(a.id)
        except Exception as e:
            errors.append({'row': int(idx), 'error': str(e)})

    return Response({'created': created, 'errors': errors})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def hod_pending(request):
    if not check_role(request,'hod'):
        return Response({'error':'role=hod required'}, status=status.HTTP_403_FORBIDDEN)
    qs = StipendRequest.objects.filter(status=StipendRequest.FAC_APPROVED)
    data = [{
        'id': s.id,
        'ta': s.assignment.ta.id.user.username,
        'faculty': s.assignment.faculty.id.user.username,
        'month': s.month, 'year': s.year,
        'faculty_remark': s.faculty_remark
    } for s in qs]
    return Response({'stipends': data})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def hod_approved(request):
    if not check_role(request,'hod'):
        return Response({'error':'role=hod required'}, status=status.HTTP_403_FORBIDDEN)
    qs = StipendRequest.objects.filter(status=StipendRequest.HOD_APPROVED)
    data = [{
        'id': s.id,
        'ta': s.assignment.ta.id.user.username,
        'faculty': s.assignment.faculty.id.user.username,
        'month': s.month, 'year': s.year,
    } for s in qs]
    return Response({'stipends': data})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def hod_approve(request, sid):
    if not check_role(request,'hod'):
        return Response({'error':'role=hod required'}, status=status.HTTP_403_FORBIDDEN)
    try:
        s = StipendRequest.objects.get(id=sid)
    except StipendRequest.DoesNotExist:
        return Response({'error':'Stipend not found'}, status=status.HTTP_404_NOT_FOUND)

    if s.status != StipendRequest.FAC_APPROVED:
        return Response({'error':'Faculty must approve first'}, status=status.HTTP_400_BAD_REQUEST)

    s.status = StipendRequest.HOD_APPROVED
    s.hod_remark = request.data.get('remark','')
    s.save()
    return Response({'success': True})




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def faculty_assignments(request):
    # if not check_role(request,'faculty'):
    #     return Response({'error':'role=faculty required'}, status=status.HTTP_403_FORBIDDEN)
    qs = Assignment.objects.filter(faculty__id__username='skjain')
    data = [{
        'id': a.id,
        'ta_username': a.ta.id.user.username,
        'start_month': a.start_month, 'start_year': a.start_year,
        'end_month': a.end_month,     'end_year': a.end_year
    } for a in qs]
    return Response({'assignments': data})

from django.db.models import Q

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def faculty_pending(request):
    if not check_role(request,'faculty'):
        return Response({'error':'role=faculty required'}, status=status.HTTP_403_FORBIDDEN)
    now = datetime.now()
    qs = StipendRequest.objects.filter(
        assignment__faculty=request.user.faculty,
        status=StipendRequest.PENDING
    ).filter(
        Q(year__lt=now.year) |
        Q(year=now.year, month__lte=now.month)
    )
    data = [{'id': s.id, 'ta': s.assignment.ta.id.user.username,
             'month': s.month, 'year': s.year} for s in qs]
    return Response({'stipends': data})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def faculty_approved(request):
    if not check_role(request,'faculty'):
        return Response({'error':'role=faculty required'}, status=status.HTTP_403_FORBIDDEN)
    qs = StipendRequest.objects.filter(
        assignment__faculty=request.user.faculty,
        status=StipendRequest.FAC_APPROVED
    )
    data = [{'id': s.id, 'ta': s.assignment.ta.id.user.username,
             'month': s.month, 'year': s.year} for s in qs]
    return Response({'stipends': data})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def faculty_approve(request, sid):
    if not check_role(request,'faculty'):
        return Response({'error':'role=faculty required'}, status=status.HTTP_403_FORBIDDEN)
    try:
        s = StipendRequest.objects.get(id=sid, assignment__faculty=request.user.faculty)
        now = datetime.now()
        if (s.year, s.month) > (now.year, now.month):
            return Response({'error':'Cannot approve future'}, status=status.HTTP_400_BAD_REQUEST)
        s.status = StipendRequest.FAC_APPROVED
        s.faculty_remark = request.data.get('remark','')
        s.save()
        return Response({'success': True})
    except StipendRequest.DoesNotExist:
        return Response({'error':'Stipend not found'}, status=status.HTTP_404_NOT_FOUND)

# --- TA endpoints ---

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ta_stipends(request):
    if not check_role(request,'ta'):
        return Response({'error':'role=ta required'}, status=status.HTTP_403_FORBIDDEN)
    qs = StipendRequest.objects.filter(assignment__ta=request.user.student)
    data = [{'month': s.month, 'year': s.year,
             'status': s.status, 'faculty_remark': s.faculty_remark}
            for s in qs]
    return Response({'stipends': data})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@role_required(['student'])
def registered_slots(request):
    try:
        current_user = request.user
        user_details = current_user.extrainfo
        student = Student.objects.get(id=user_details)
        session, semester_type = generate_current_session(datetime.datetime.now().year, student.curr_semester_no) 
        eligibility_resp = get_add_drop_replace_registration_eligibility(timezone.now().date(), student.curr_semester_no, datetime.datetime.now().year)
        if isinstance(eligibility_resp, JsonResponse):
            return eligibility_resp
        regs = course_registration.objects.filter(student_id=student, semester_id__semester_no = student.curr_semester_no).exclude(course_slot_id__name__startswith='SW').exclude(course_slot_id__name__startswith='BL')
        payload = []
        for reg in regs:
            slot = reg.course_slot_id
            others = slot.courses.all().exclude(id=reg.course_id.id)

            payload.append({
                "id": slot.id,
                "name": slot.name,
                "academic_year": reg.session,
                "semester_type": reg.semester_type,
                "old_course": {"id": reg.course_id.id, "code": reg.course_id.code, "name" : reg.course_id.name},
                "new_courses": [
                    {"id": c.id, "code": c.code, "name": c.name, "seats_available": max(c.max_seats - (course_registration.objects.filter(course_id=c, session = session, semester_type = semester_type).exclude(course_slot_id__name__startswith = 'BL').count()), 0)} for c in others
                ],
            })
        print(payload)
        return JsonResponse(payload, safe=False)   
    except Student.DoesNotExist:
        return Response({"error": "Student profile not found"}, status=400)
    except Exception as e:
        return Response({"error": str(e)}, status=500)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@role_required(['student'])
def batch_create_requests(request):
    try:
        current_user = request.user
        user_details = current_user.extrainfo
        student = Student.objects.get(id=user_details)
        eligibility_resp = get_add_drop_replace_registration_eligibility(timezone.now().date(), student.curr_semester_no, datetime.datetime.now().year)
        if isinstance(eligibility_resp, JsonResponse):
            return eligibility_resp
        data = json.loads(request.body).get('requests', [])

        created = []
        errors = []

        for idx, item in enumerate(data):
            try:
                slot_id = item.get('course_slot')
                old_id = item.get('old_course')
                new_id = item.get('new_course')
                ay = item.get('academic_year')
                sem = item.get('semester_type')

                if not all([slot_id, old_id, new_id, ay, sem]):
                    raise ValueError("Missing required fields.")

                slot = CourseSlot.objects.get(pk=slot_id)
                old = Courses.objects.get(pk=old_id)
                new = Courses.objects.get(pk=new_id)

                reg = course_registration.objects.get(
                    student_id=student,
                    course_slot_id=slot,
                    course_id=old,
                    session=ay,
                    semester_type=sem
                )

                if not slot.courses.filter(id=new.id).exists():
                    raise ValueError("New course not in selected slot.")

                with transaction.atomic():
                    req, created_flag = CourseReplacementRequest.objects.get_or_create(
                        student=student,
                        course_slot=slot,
                        academic_year=ay,
                        semester_type=sem,
                        defaults={
                            "old_course": old,
                            "new_course": new,
                        }
                    )

                    action = "created"
                    if not created_flag:
                        if req.old_course != old or req.new_course != new:
                            req.old_course = old
                            req.new_course = new
                            req.status = "Pending"
                            req.processed_at = None
                            req.save()
                            action = "updated"
                        else:
                            action = "unchanged"

                    created.append({
                        "id": req.id,
                        "slot": slot.name,
                        "old": old.code,
                        "new": new.code,
                        "status": req.status,
                        "action": action,
                    })

            except Exception as e:
                errors.append({"index": idx, "error": str(e)})

        return JsonResponse({"created": created, "errors": errors}, status=201)

    except Exception as e:
        return JsonResponse({"detail": "Something went wrong", "error": str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@role_required(['acadadmin'])
def admin_list_requests(request):
    qs = CourseReplacementRequest.objects.all().order_by('-created_at')
    year = request.GET.get('academic_year')
    sem  = request.GET.get('semester_type')
    if year:
        qs = qs.filter(academic_year=year)
    if sem:
        qs = qs.filter(semester_type=sem)

    out = []
    for r in qs:
        out.append({
            'id': r.id,
            'student': r.student_id,
            'slot': r.course_slot.name,
            'old_course': r.old_course.code,
            'new_course': r.new_course.code,
            'status': r.status,
            'academic_year': r.academic_year,
            'semester_type': r.semester_type,
            'created_at': r.created_at.isoformat(),
        })
    return JsonResponse(out, safe=False)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
@role_required(['student'])
def student_list_requests(request):
    current_user = request.user
    user_details = current_user.extrainfo
    student = Student.objects.get(id=user_details)
    academic_year, semester_type = generate_current_session(datetime.datetime.now().year, student.curr_semester_no)
    qs = CourseReplacementRequest.objects.filter(student=student, academic_year=academic_year, semester_type = semester_type).order_by('-created_at')
    out = []
    for r in qs:
        out.append({
            'id': r.id,
            'slot': r.course_slot.name,
            'old_course': r.old_course.code,
            'new_course': r.new_course.code,
            'status': r.status,
            'academic_year': r.academic_year,
            'semester_type': r.semester_type,
            'created_at': r.created_at.isoformat(),
        })
    return JsonResponse(out, safe=False)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
@role_required(['acadadmin'])
def allocate_all(request):
    import json
    try:
        body = json.loads(request.body)
        year = body.get('academic_year')
        sem  = body.get('semester_type')
    except:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    pending = CourseReplacementRequest.objects.select_for_update().filter(
        status="Pending", academic_year=year, semester_type=sem
    )
    by_course = defaultdict(list)
    for cr in pending:
        by_course[cr.new_course].append(cr)

    queue = deque()
    in_q  = set()
    for course, reqs in by_course.items():
        course = Courses.objects.select_for_update().get(pk=course.pk)
        used   = course_registration.objects.filter(course_id=course, session = year, semester_type = sem).exclude(course_slot_id__name__startswith = 'BL').count()
        free   = max(course.max_seats - used, 0)
        if free > 0:
            queue.append(course)
            in_q.add(course)

    results = []
    while queue:
        course = queue.popleft()
        in_q.discard(course)

        while True:
            used = course_registration.objects.filter(course_id=course, session=year, semester_type=sem).exclude(course_slot_id__name__startswith='BL').count()
            free = max(course.max_seats - used, 0)
            reqs = by_course[course]
            if free <= 0 or not reqs:
                break

            # Always pick one request at a time (FIFO)
            cr = reqs[0]
            cr.status = "Approved"
            cr.processed_at = timezone.now()
            cr.save(update_fields=['status', 'processed_at'])
            results.append({'id': cr.id, 'status': 'Approved'})
            # print(
            #     "Looking for old_reg with:",
            #     "student_id=", cr.student,
            #     "course_slot_id=", cr.course_slot,
            #     "session=", cr.academic_year,
            #     "semester_type=", cr.semester_type
            # )
            # swap registrations
            old_reg = course_registration.objects.select_for_update().get(
                student_id=cr.student,
                course_slot_id=cr.course_slot,
                session=cr.academic_year,
                semester_type=cr.semester_type
            )
            old_course = old_reg.course_id
            # print(old_course)
            semester_id = old_reg.semester_id
            old_reg.delete()

            working_year, _ = parse_academic_year(cr.academic_year, cr.semester_type)
            course_registration.objects.create(
                student_id=cr.student,
                course_slot_id=cr.course_slot,
                course_id=course,
                session=cr.academic_year,
                semester_type=cr.semester_type,
                semester_id=semester_id,
                working_year=working_year
            )
            by_course[course].remove(cr)

            # cascade enqueue old_course if it now has free seats and pending requests
            used_old = course_registration.objects.filter(course_id=old_course, session=year, semester_type=sem).exclude(course_slot_id__name__startswith='BL').count()
            free_old = max(old_course.max_seats - used_old, 0)
            if free_old > 0 and by_course.get(old_course) and by_course[old_course] and old_course not in in_q:
                queue.append(old_course)
                in_q.add(old_course)

    # reject leftovers
    for reqs in by_course.values():
        for cr in reqs:
            cr.status = "Rejected"
            cr.processed_at = timezone.now()
            cr.save(update_fields=['status', 'processed_at'])
            results.append({'id': cr.id, 'status': 'Rejected'})

    return JsonResponse(results, safe=False)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@role_required(['student'])
def student_registrations_for_drop(request):
    """
    GET /api/student/registrations/
    List all active registrations for the logged-in student.
    """
    current_user = request.user
    user_details = current_user.extrainfo
    student = Student.objects.get(id=user_details)
    eligibility_resp = get_add_drop_replace_registration_eligibility(timezone.now().date(), student.curr_semester_no, datetime.datetime.now().year)
    if isinstance(eligibility_resp, JsonResponse):
        return eligibility_resp
    regs = course_registration.objects.filter(student_id=student, semester_id__semester_no = student.curr_semester_no )
    out = []
    for reg in regs:
        out.append({
            'id': reg.id,
            'slot': reg.course_slot_id.name,
            'course': reg.course_id.code,
            'academic_year': reg.session,
            'semester_type': reg.semester_type,
        })
    return Response(out, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@role_required(['student'])
def drop_course(request):
    """
    POST /api/student/drop-course/
    Body: { "registration_id": <int> }
    Deletes that registration if it belongs to the student.
    """
    current_user = request.user
    user_details = current_user.extrainfo
    student = Student.objects.get(id=user_details)
    eligibility_resp = get_add_drop_replace_registration_eligibility(timezone.now().date(), student.curr_semester_no, datetime.datetime.now().year)
    if isinstance(eligibility_resp, JsonResponse):
        return eligibility_resp
    reg_id = request.data.get('registration_id')
    if not reg_id:
        return Response(
            {'error': 'registration_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        with transaction.atomic():
            reg = course_registration.objects.get(id=reg_id, student_id=student)
            reg.delete()
        return Response(
            {'status': 'dropped', 'registration_id': reg_id},
            status=status.HTTP_200_OK
        )
    except course_registration.DoesNotExist:
        return Response(
            {'error': 'Registration not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Internal error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@role_required(['student'])
def student_calendar_view(request):
    calendar_entries = Calendar.objects.all().order_by('from_date')

    result = [
        {
            "from_date": entry.from_date,
            "to_date": entry.to_date,
            "description": entry.description,
        }
        for entry in calendar_entries
    ]

    return Response({"calendar_events": result})

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@role_required(['acadadmin'])
def student_search(request):
    roll_no = request.data.get('rollno','').upper()
    if not roll_no:
        return JsonResponse({'error':'rollno is required'},status=400)
    student = Student.objects.filter(id_id=roll_no).first()
    if not student:
        return JsonResponse({'error':'Student record not found'},status=400)
    extra = student.id
    user = extra.user
    data = {
        'roll_no':roll_no,
        'full_name':f"{user.first_name} {user.last_name}".strip(),
        'date_of_birth':str(extra.date_of_birth),
        'user_status':extra.user_status,
        'address':extra.address,
        'phone_no':extra.phone_no,
        'department':extra.department.name if extra.department else None,
        'programme':student.programme,
        'batch':student.batch,
        'batch_name':student.batch_id.name if student.batch_id else None,
        'discipline':student.batch_id.discipline.name if student.batch_id and student.batch_id.discipline else None,
        'curriculum':student.batch_id.curriculum.name if student.batch_id and student.batch_id.curriculum else None,
        'cpi':student.cpi,
        'category':student.category,
        'father_name':student.father_name,
        'mother_name':student.mother_name,
        'hall_no':student.hall_no,
        'room_no':student.room_no,
        'specialization':student.specialization,
        'curr_semester_no':student.curr_semester_no,
    }
    return JsonResponse(data,status=200)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@role_required(['student'])
def student_registration_semesters_view(request):
    """
    Return a list of distinct semesters in which the student has registrations.
    For new students, also include their current semester even if no registrations exist.
    """
    try:
        roll_number = request.user.username
        student = Student.objects.get(id_id=roll_number)

        # Pull distinct (semester_no, semester_type) from the student's course registrations
        qs = (course_registration.objects
              .filter(student_id=student)
              .values_list('semester_id__semester_no', 'semester_type')
              .distinct()
              .order_by('semester_id__semester_no'))

        unique = OrderedDict()
        for sem_no, sem_type in qs:
            label = make_label(sem_no, sem_type or "")
            unique[(sem_no, sem_type)] = label

        # For new students who haven't registered for any courses yet,
        # include their current semester
        if not unique and student.curr_semester_no:
            # Determine semester type based on semester number (odd/even)
            current_sem_type = "Odd Semester" if student.curr_semester_no % 2 == 1 else "Even Semester"
            current_label = make_label(student.curr_semester_no, current_sem_type)
            unique[(student.curr_semester_no, current_sem_type)] = current_label

        semesters = [
            {"semester_no": no, "semester_type": typ, "label": lbl}
            for (no, typ), lbl in unique.items()
        ]

        return JsonResponse({"success": True, "semesters": semesters}, status=200)

    except Student.DoesNotExist:
        return JsonResponse({"success": False, "error": "Student not found."}, status=404)
    except Exception as e:
        print(e)
        return JsonResponse({"success": False, "error": str(e)}, status=500)
    

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@role_required(['student'])
def student_filled(request):
    roll_number = request.user.username
    student = Student.objects.get(id_id=roll_number)
    semester_no = student.curr_semester_no
    done = FeedbackFilled.objects.filter(student=student, semester_no = semester_no).exists()
    return Response({"filled": done})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@role_required(['student'])
def student_questions(request):
    try:
        roll_number = request.user.username
        student = Student.objects.get(id_id=roll_number)
    except Student.DoesNotExist:
        return Response({"detail": "Student profile not found."}, status=status.HTTP_404_NOT_FOUND)

    semester_no = student.curr_semester_no

    filled = FeedbackFilled.objects.filter(
        student=student,
        semester_no=semester_no
    ).exists()

    registrations = course_registration.objects.filter(
        student_id=student,
        semester_id__semester_no=semester_no,
    ).select_related("course_id")

    courses = []
    for reg in registrations:
        course = reg.course_id
        academic_year, _ = parse_academic_year(reg.session, reg.semester_type)
        instructor_entry = CourseInstructor.objects.filter(
            course_id=course,
            semester_type=reg.semester_type,
            year = academic_year
            
        ).first()

        instructor_id = instructor_entry.id if instructor_entry else None
        instructor_name = (
            f"{instructor_entry.instructor_id.id.user.first_name} {instructor_entry.instructor_id.id.user.last_name}"
            if instructor_entry else ""
        )

        courses.append({
            "course_id": course.id,
            "code": course.code,
            "name": course.name,
            "instructor_id": instructor_id,
            "instructor_name": instructor_name,
        })

    questions = [
        {
            "id": question.id,
            "section": question.section,
            "text": question.text,
            "options": [{"id": option.id, "text": option.text} for option in question.options.all()],
        }
        for question in FeedbackQuestion.objects.all()
    ]

    return Response({
        "filled": filled,
        "courses": courses,
        "questions": questions,
    })

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@role_required(['student'])
def student_submit(request):
    try:
        roll_number = request.user.username
        student = Student.objects.get(id_id=roll_number)
    except Student.DoesNotExist:
        return Response({"detail": "Student profile not found."}, status=status.HTTP_404_NOT_FOUND)

    semester_no = student.curr_semester_no
    data = request.data
    if FeedbackFilled.objects.filter(student=student, semester_no = semester_no).exists():
        return Response({"detail":"Already filled."}, status=status.HTTP_409_CONFLICT)

    with transaction.atomic():
        for r in data["responses"]:

            reg = course_registration.objects.get(student_id =student, course_id_id = r["course_id"], semester_id__semester_no = student.curr_semester_no)
            FeedbackResponse.objects.create(
                question_id   = r["question_id"],
                option_id     = r.get("option_id"),
                text_answer   = r.get("text_answer",""),
                course_id     = r["course_id"],
                section       = r["section"],
                session       = reg.session,
                semester_type = reg.semester_type,
            )
        FeedbackFilled.objects.create(student=student, semester_no = student.curr_semester_no)

    return Response({"detail":"Submitted"}, status=status.HTTP_201_CREATED)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def inst_courses(request):
    """
    GET /inst/courses/?session=<str>&semester_type=<str>
    Returns the list of courses the logged-in instructor is teaching.
    """
    fac = request.user.username
    sess = request.query_params.get("session")
    semt = request.query_params.get("semester_type")
    if not sess or not semt:
        return Response({"detail": "Provide 'session' and 'semester_type'."}, status=status.HTTP_400_BAD_REQUEST)

    academic_year, _ = parse_academic_year(sess, semt)
    regs = CourseInstructor.objects.filter(
        instructor_id_id=fac,
        year=academic_year,
        semester_type=semt,
    )

    return Response([{
        "course_id": cr.course_id.id,
        "code":      cr.course_id.code,
        "name":      cr.course_id.name,
    } for cr in regs])


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def inst_all_stats(request):
    """
    GET /inst/stats/all/?session=&semester_type=&course_id=
    Returns per-question counts + comments for the 'Course Instructor' section.
    If no responses yet, returns {"detail": "No responses found till now."}.
    """
    sess = request.query_params.get("session")
    semt = request.query_params.get("semester_type")
    cid = request.query_params.get("course_id")

    academic_year, _ = parse_academic_year(sess, semt)
    if not CourseInstructor.objects.filter(
        course_id_id=cid,
        instructor_id_id=request.user.username,
        year=academic_year,
        semester_type=semt,
    ).exists():
        return Response(
            {"error": "Access denied: you are not assigned as instructor for this course."},
            status=status.HTTP_403_FORBIDDEN
        )

    has_any = FeedbackResponse.objects.filter(
        course_id=cid,
        session=sess,
        semester_type=semt,
        question__section="instructor",
    ).exists()

    if not has_any:
        return Response(
            {"detail": "No responses found till now."},
            status=status.HTTP_200_OK
        )

    out = []
    questions = FeedbackQuestion.objects.filter(section="instructor").order_by("order")
    
    for q in questions:
        base = FeedbackResponse.objects.filter(
            question=q,
            course_id=cid,
            session=sess,
            semester_type=semt,
        )
        counts = {
            o.text: base.filter(option=o).count()
            for o in FeedbackOption.objects.filter(question=q)
        }
        comments = list(
            base.filter(option__isnull=True).values_list("text_answer", flat=True)
        )
        out.append({
            "question_id": q.id,
            "text": q.text,
            "counts": counts,
            "comments": comments,
        })

    return Response(out, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@role_required(['acadadmin'])
def admin_course_list(request):
    """
    GET /admin/courses/?session=<str>&semester_type=<str>
    """
    sess = request.query_params.get("session")
    semt = request.query_params.get("semester_type")
    if not sess or not semt:
        return Response(
            {"detail":"Provide 'session' & 'semester_type'."},
            status=status.HTTP_400_BAD_REQUEST
        )

    regs = FeedbackResponse.objects.filter(
        session=sess,
        semester_type=semt,
    ).select_related("course").distinct()

    seen = set()
    courses = []
    for reg in regs:
        c = reg.course
        if c.id in seen:
            continue
        seen.add(c.id)
        courses.append({
            "course_id": c.id,
            "code":      c.code,
            "name":      c.name,
        })

    return Response(courses)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@role_required(['acadadmin'])
def admin_all_stats(request):
    """
    GET /admin/stats/all/?session=<str>&semester_type=<str>&course_id=<int>
    Returns a JSON payload grouped by section:
      {
        sections: [
          {
            section: "<section_key>",
            questions: [
              {
                question_id, text,
                counts: { option_text: count, ... },
                comments: [ ... ]
              },
              ...
            ]
          },
          ...
        ]
      }
    """
    sess = request.query_params.get("session")
    semt = request.query_params.get("semester_type")
    cid  = request.query_params.get("course_id")
    if not sess or not semt or not cid:
        return Response(
            {"detail":"Provide 'session', 'semester_type', and 'course_id'."},
            status=status.HTTP_400_BAD_REQUEST
        )

    raw = []
    for q in FeedbackQuestion.objects.all().order_by("order"):
        base = FeedbackResponse.objects.filter(
            question=q,
            course_id=cid,
            session=sess,
            semester_type=semt,
        )
        counts = {
            o.text: base.filter(option=o).count()
            for o in FeedbackOption.objects.filter(question=q)
        }
        comments = list(
            base.filter(option__isnull=True)
                .values_list("text_answer", flat=True)
        )
        raw.append({
            "section":     q.section,
            "question_id": q.id,
            "text":        q.text,
            "counts":      counts,
            "comments":    comments,
        })

    grouped = {}
    for item in raw:
        sec = item["section"]
        grouped.setdefault(sec, []).append({
            "question_id": item["question_id"],
            "text":        item["text"],
            "counts":      item["counts"],
            "comments":    item["comments"],
        })

    response = {
        "sections": [
            {"section": sec, "questions": qs}
            for sec, qs in grouped.items()
        ]
    }

    if not raw or all(len(v["questions"]) == 0 for v in response["sections"]):
        return Response({"detail":"No responses found till now."})

    return Response(response)



@api_view(["GET"])
@permission_classes([IsAuthenticated])
@role_required(['acadadmin'])
def list_batches(request):
    batches = Batch.objects.filter(running_batch=True).select_related("discipline").order_by("year", "name")
    result = []
    for b in batches:
        label = f"{b.name} {b.discipline.acronym} {b.year}"
        result.append({"id": b.id, "label": label, "year": b.year})
    return Response(result)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@role_required(['acadadmin'])
def list_students_in_batch(request):
    batch_id = request.query_params.get("batch_id")
    if not batch_id:
        return Response({"detail": "batch_id required."}, status=status.HTTP_400_BAD_REQUEST)
    students = Student.objects.filter(batch_id__id=batch_id)
    result = []
    for st in students:
        cb = st.batch_id
        cb_label = f"{cb.name} {cb.discipline.acronym} {cb.year}"
        result.append({
            "id": st.id_id,
            "username": str(st.id_id),
            "current_batch": cb_label,
            "current_batch_id": cb.id,
            "current_batch_year": st.batch,
        })
    return Response(result)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@role_required(['acadadmin'])
def apply_batch_changes(request):
    data = request.data
    user = request.user
    errors = []

    with transaction.atomic():
        for idx, pair in enumerate(data):
            sid = pair.get("student_id")
            nid = pair.get("new_batch_id")
            nyear = pair.get("new_batch_year")
            if not sid or not nid or nyear is None:
                errors.append({"index": idx, "detail": "student_id, new_batch_id, new_batch_year required."})
                continue
            try:
                student = Student.objects.get(id=sid)
            except Student.DoesNotExist:
                errors.append({"index": idx, "detail": f"Student {sid} not found."})
                continue

            old_batch = student.batch_id
            if old_batch and old_batch.id == nid and student.batch == nyear:
                continue
            try:
                new_batch = Batch.objects.get(id=nid)
            except Batch.DoesNotExist:
                errors.append({"index": idx, "detail": f"Batch {nid} not found."})
                continue

            BatchChangeHistory.objects.create(
                student=student,
                old_batch=old_batch,
                new_batch=new_batch,
            )
            student.batch_id = new_batch
            student.batch = nyear
            student.save()
            
            # Sync branch, department, and specialization
            try:
                from applications.programme_curriculum.models_student_management import StudentBatchUpload
                from applications.globals.models import DepartmentInfo
                student_upload = StudentBatchUpload.objects.filter(roll_number=student.id_id).first()
                if student_upload:
                    student_upload.branch = new_batch.discipline.name
                    student_upload.save()
                dept_name = new_batch.discipline.acronym
                department = DepartmentInfo.objects.filter(name=dept_name).first()
                if department:
                    student.id.department = department
                    student.id.save()
                student.specialization = dept_name
                student.save()
            except:
                pass

    if errors:
        return Response({"errors": errors}, status=status.HTTP_207_MULTI_STATUS)
    return Response({"detail": "Batch changes applied."}, status=status.HTTP_200_OK)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@role_required(['acadadmin'])
def list_students_in_batch_semester_promotion(request):
    batch_id = request.query_params.get("batch_id")
    if not batch_id:
        return Response({"detail": "batch_id required."}, status=status.HTTP_400_BAD_REQUEST)
    students = Student.objects.filter(batch_id__id=batch_id).order_by('id_id')
    result = []
    for st in students:
        result.append({
            "id": st.id_id,
            "username": str(st.id_id),
            "current_semester_no": st.curr_semester_no,
        })
    return Response(result)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@role_required(['acadadmin'])
def apply_promotion(request):
    data = request.data  # list of student IDs
    user = request.user
    errors = []
    with transaction.atomic():
        for idx, sid in enumerate(data):
            try:
                student = Student.objects.get(id=sid)
            except Student.DoesNotExist:
                errors.append({"index": idx, "detail": f"Student {sid} not found."})
                continue
            old_sem = student.curr_semester_no
            new_sem = old_sem + 1
            try:
                semester_obj = Semester.objects.get(curriculum=student.batch_id.curriculum,semester_no=new_sem)
            except Semester.DoesNotExist:
                errors.append({"index": idx, "detail": f"Semester {new_sem} not defined."})
                continue
            student.curr_semester_no = new_sem
            student.save()
            frs = FinalRegistration.objects.filter(student_id=student, verified=False, semester_id = semester_obj)
            for fr in frs:
                course = fr.course_id
                exists = course_registration.objects.filter(
                    student_id=student,
                    course_id=course,
                    semester_id=semester_obj
                ).exists()
                session, semester_type = generate_next_session(date_time.year, new_sem)
                if not exists:
                    new_cr = course_registration.objects.create(
                        student_id=student,
                        working_year=None,
                        semester_id=semester_obj,
                        course_id=course,
                        course_slot_id=fr.course_slot_id,
                        registration_type=fr.registration_type,
                        session=session,
                        semester_type=semester_type
                    )
                    if fr.old_course_registration:
                        course_replacement.objects.create(
                            old_course_registration=fr.old_course_registration,
                            new_course_registration=new_cr
                        )
                fr.verified = True
                fr.save()
    if errors:
        return Response({"errors": errors}, status=status.HTTP_207_MULTI_STATUS)
    return Response({"detail": "Promotion applied."}, status=status.HTTP_200_OK)


# @api_view(["GET"])
# @permission_classes([IsAuthenticated])
# def download_user_template(request):
#     columns = [
#         "username", "first_name", "last_name", "email", "gender", "date_of_birth",
#         "user_status", "address", "phone_no", "user_type", "department",
#         "title", "about_me",
#         "programme", "batch", "batch_id", "category",
#         "father_name", "mother_name", "hall_no", "room_no", "specialization", "curr_semester_no"
#     ]
#     df = pd.DataFrame(columns=columns)
#     buffer = io.BytesIO()
#     df.to_excel(buffer, index=False)
#     buffer.seek(0)
#     resp = HttpResponse(buffer, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
#     resp["Content-Disposition"] = "attachment; filename=student_upload_template.xlsx"
#     return resp

# @api_view(["POST"])
# @permission_classes([IsAuthenticated])
# def upload_users(request):
#     f = request.FILES.get("file")
#     if not f:
#         return JsonResponse({"detail": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)
#     try:
#         df = pd.read_excel(f)
#     except Exception:
#         return JsonResponse({"detail": "Invalid Excel file."}, status=status.HTTP_400_BAD_REQUEST)
#     required = ["username", "first_name", "last_name", "email", "gender", "date_of_birth", "user_type", "programme", "batch", "category"]
#     errors = []
#     created = []
#     with transaction.atomic():
#         for idx, row in df.iterrows():
#             rownum = idx + 2
#             for field in required:
#                 if pd.isna(row.get(field)):
#                     errors.append({"row": rownum, "detail": f"{field} is required."})
#                     break
#             else:
#                 uname = str(row["username"]).strip()
#                 if User.objects.filter(username=uname).exists():
#                     errors.append({"row": rownum, "detail": "Username already exists."})
#                     continue
#                 email = str(row["email"]).strip()
#                 gender = str(row["gender"]).strip().upper()[0]
#                 dob = row["date_of_birth"]
#                 if isinstance(dob, datetime.date) is False:
#                     errors.append({"row": rownum, "detail": "Invalid date_of_birth."})
#                     continue
#                 user = User.objects.create_user(username=uname, email=email, password="user@123")
#                 user.first_name = str(row["first_name"]).strip()
#                 user.last_name = str(row["last_name"]).strip()
#                 user.save()
#                 eid = uname  # using username as ExtraInfo.id
#                 dept_name = str(row.get("department", "")).strip()
#                 dept = None
#                 if dept_name:
#                     dept, _ = DepartmentInfo.objects.get_or_create(name=dept_name)
#                 ei = ExtraInfo.objects.create(
#                     id=eid,
#                     user=user,
#                     title=str(row.get("title", "")).strip() or None,
#                     sex=gender,
#                     date_of_birth=dob,
#                     user_status=str(row.get("user_status", "")).strip() or None,
#                     address=str(row.get("address", "")).strip() or None,
#                     phone_no=int(row.get("phone_no")) if not pd.isna(row.get("phone_no")) else None,
#                     user_type=str(row["user_type"]).strip(),
#                     department=dept,
#                     about_me=str(row.get("about_me", "")).strip() or None,
#                 )
#                 batch_year = int(row["batch"])
#                 prog = str(row["programme"]).strip()
#                 cat = str(row["category"]).strip()
#                 batch_id_val = row.get("batch_id")
#                 batch_obj = None
#                 if not pd.isna(batch_id_val):
#                     try:
#                         batch_obj = Batch.objects.get(id=int(batch_id_val))
#                     except Batch.DoesNotExist:
#                         errors.append({"row": rownum, "detail": "Invalid batch_id."})
#                         continue
#                 student = Student.objects.create(
#                     id=ei,
#                     programme=prog,
#                     batch=batch_year,
#                     batch_id=batch_obj,
#                     cpi=float(row.get("cpi", 0)) if not pd.isna(row.get("cpi")) else 0,
#                     category=cat,
#                     father_name=str(row.get("father_name", "")).strip() or None,
#                     mother_name=str(row.get("mother_name", "")).strip() or None,
#                     hall_no=int(row.get("hall_no")) if not pd.isna(row.get("hall_no")) else 0,
#                     room_no=str(row.get("room_no", "")).strip() or None,
#                     specialization=str(row.get("specialization", "")).strip() or None,
#                     curr_semester_no=int(row.get("curr_semester_no")) if not pd.isna(row.get("curr_semester_no")) else 1
#                 )
#                 created.append(uname)
#     status_code = status.HTTP_207_MULTI_STATUS if errors else status.HTTP_201_CREATED
#     return JsonResponse({"created": created, "errors": errors}, status=status_code)