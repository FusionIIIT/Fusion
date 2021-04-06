import datetime

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect

from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes,authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from applications.globals.models import HoldsDesignation, Designation, ExtraInfo

from applications.academic_procedures.views import (get_user_semester, get_acad_year,
                                                    get_currently_registered_courses,
                                                    get_current_credits, get_branch_courses,
                                                    Constants, get_faculty_list,
                                                    get_registration_courses)

from . import serializers

User = get_user_model()

date_time = datetime.datetime.now()

@api_view(['GET'])
def academic_procedures_faculty(request):
    current_user = request.user
    user_details = current_user.extrainfo
    des = current_user.holds_designations.all().first()

    if str(des.designation) == 'student':
        return Response({'error':'Not a faculty'}, status=status.HTTP_400_BAD_REQUEST)
    elif str(current_user) == 'acadadmin':
        return Response({'error':'User is acadadmin'}, status=status.HTTP_400_BAD_REQUEST)

    elif str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor":
        faculty_object = user_details.faculty
        month = int(date_time.month)
        sem = []
        if month>=7 and month<=12:
            sem = [1,3,5,7]
        else:
            sem = [2,4,6,8]
        student_flag = False
        fac_flag = True

        thesis_supervision_request_list = faculty_object.thesistopicprocess_supervisor.all()
        thesis_supervision_request_list_data = serializers.ThesisTopicProcessSerializer(thesis_supervision_request_list, many=True).data
        approved_thesis_request_list = serializers.ThesisTopicProcessSerializer(thesis_supervision_request_list.filter(approval_supervisor = True), many=True).data
        pending_thesis_request_list = serializers.ThesisTopicProcessSerializer(thesis_supervision_request_list.filter(pending_supervisor = True), many=True).data
        courses_list = serializers.CurriculumInstructorSerializer(user_details.curriculum_instructor_set.all(), many=True).data
        fac_details = serializers.UserSerializer(current_user).data

        resp = {
            'student_flag' : student_flag,
            'fac_flag' : fac_flag,
            'thesis_supervision_request_list' : thesis_supervision_request_list_data,
            'pending_thesis_request_list' : pending_thesis_request_list,
            'approved_thesis_request_list' : approved_thesis_request_list,
            'courses_list': courses_list,
            'faculty': fac_details
        }
        return Response(data=resp, status=status.HTTP_200_OK)

@api_view(['GET'])
def academic_procedures_student(request):
    current_user = request.user
    current_user_data = serializers.UserSerializer(current_user).data
    user_details = current_user.extrainfo
    des = current_user.holds_designations.all().first()
    if str(des.designation) == 'student':
        obj = user_details.student

        if obj.programme.upper() == "PH.D":
            student_flag = True
            ug_flag = False
            masters_flag = False
            phd_flag = True
            fac_flag = False
            des_flag = False

        elif obj.programme.upper() == "M.DES":
            student_flag = True
            ug_flag = False
            masters_flag = True
            phd_flag = False
            fac_flag = False
            des_flag = True

        elif obj.programme.upper() == "B.DES":
            student_flag = True
            ug_flag = True
            masters_flag = False
            phd_flag = False
            fac_flag = False
            des_flag = True

        elif obj.programme.upper() == "M.TECH":
            student_flag = True
            ug_flag = False
            masters_flag = True
            phd_flag = False
            fac_flag = False
            des_flag = False

        elif obj.programme.upper() == "B.TECH":
            student_flag = True
            ug_flag = True
            masters_flag = False
            phd_flag = False
            fac_flag = False
            des_flag = False

        else:
            return Response({'message':'Student has no record'}, status=status.HTTP_400_BAD_REQUEST)

        current_date = date_time.date()
        current_year = date_time.year
        user_sem = get_user_semester(request.user, ug_flag, masters_flag, phd_flag)
        acad_year = get_acad_year(user_sem, current_year)
        user_branch = user_details.department.name
        cpi = obj.cpi

        details = {
            'current_user': current_user_data,
            'year': acad_year,
            'user_sem': user_sem,
            'user_branch' : str(user_branch),
            'cpi' : cpi
        }
        currently_registered_courses = get_currently_registered_courses(user_details.id, user_sem)
        currently_registered_courses_data = serializers.CurriculumSerializer(currently_registered_courses, many=True).data
        try:
            pre_registered_courses = obj.initialregistrations_set.all().filter(semester = user_sem)
            pre_registered_courses_show = obj.initialregistrations_set.all().filter(semester = user_sem+1)
        except:
            pre_registered_courses =  None
        try:
            final_registered_courses = obj.finalregistrations_set.all().filter(semester = user_sem)
        except:
            final_registered_courses = None

        pre_registered_courses_data = serializers.InitialRegistrationsSerializer(pre_registered_courses, many=True).data
        pre_registered_courses_show_data = serializers.InitialRegistrationsSerializer(pre_registered_courses_show, many=True).data
        final_registered_courses_data = serializers.FinalRegistrationsSerializer(final_registered_courses, many=True).data

        current_credits = get_current_credits(currently_registered_courses)

        next_sem_branch_courses = get_branch_courses(current_user, user_sem+1, user_branch)
        next_sem_branch_courses_data = serializers.CurriculumSerializer(next_sem_branch_courses, many=True).data

        fee_payment_mode_list = dict(Constants.PaymentMode)

        next_sem_branch_registration_courses = get_registration_courses(next_sem_branch_courses)
        # next_sem_branch_registration_courses_data = serializers.CurriculumSerializer(next_sem_branch_registration_courses, many=True).data

        final_registration_choices = get_registration_courses(get_branch_courses(request.user, user_sem, user_branch))
        # final_registration_choices_data = serializers.CurrxiculumSerializer(final_registration_choices, many=True).data

        performance_list = []
        result_announced = False
        for i in currently_registered_courses:
            try:
                performance_obj = obj.semestermarks_set.all().filter(curr_id = i).first()
            except:
                performance_obj = None
            performance_list.append(performance_obj)

        # faculty_list = serializers.HoldsDesignationSerializer(get_faculty_list(), many=True).data

        resp = {
            'details': details,
            'currently_registered': currently_registered_courses_data,
            'currently_registered': currently_registered_courses,
            'pre_registered_courses' : pre_registered_courses_data,
            'pre_registered_courses_show' : pre_registered_courses_show_data,
            'final_registered_courses' : final_registered_courses_data,
            'current_credits' : current_credits,
            'courses_list': next_sem_branch_courses_data,
            'fee_payment_mode_list' : fee_payment_mode_list,
            'next_sem_branch_registration_courses' : str(next_sem_branch_registration_courses),
            'final_registration_choices' : str(final_registration_choices),
            'performance_list' : performance_list
            # 'faculty_list' : faculty_list
        }
        return Response(data=resp, status=status.HTTP_200_OK)
