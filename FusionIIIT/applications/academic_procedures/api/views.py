import datetime

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect

from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes,authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from applications.academic_information.models import Curriculum
from applications.academic_procedures.models import ThesisTopicProcess
from applications.globals.models import HoldsDesignation, Designation, ExtraInfo
from applications.programme_curriculum.models import (CourseSlot, Course as Courses, Batch, Semester)


from applications.academic_procedures.views import (get_user_semester, get_acad_year,
                                                    get_currently_registered_courses,
                                                    get_current_credits, get_branch_courses,
                                                    Constants, get_faculty_list,
                                                    get_registration_courses, get_add_course_options,
                                                    get_pre_registration_eligibility,
                                                    get_final_registration_eligibility,
                                                    get_add_or_drop_course_date_eligibility)

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
    current_user_data = {
        'first_name': current_user.first_name,
        'last_name': current_user.last_name,
        'username': current_user.username,
        'email': current_user.email
    }
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
        batch = obj.batch_id
        user_sem = get_user_semester(request.user, ug_flag, masters_flag, phd_flag)
        acad_year = get_acad_year(user_sem, current_year)
        user_branch = user_details.department.name
        cpi = obj.cpi
        cur_spi='Sem results not available' # To be fetched from db if result uploaded

        details = {
            'current_user': current_user_data,
            'year': acad_year,
            'user_sem': user_sem,
            'user_branch' : str(user_branch),
            'cpi' : cpi,
            'spi' : cur_spi
        }
        currently_registered_courses = get_currently_registered_courses(user_details.id, user_sem)
        currently_registered_courses_data = serializers.CurriculumSerializer(currently_registered_courses, many=True).data
        try:
            pre_registered_courses = obj.initialregistrations_set.all().filter(semester = user_sem)
            pre_registered_courses_show = obj.initialregistrations_set.all().filter(semester = user_sem+1)
        except:
            pre_registered_courses =  None
            pre_registered_courses_show=None
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
        next_sem_branch_registration_courses_data = []
        for choices in next_sem_branch_registration_courses:
            next_sem_branch_registration_courses_data.append(serializers.CurriculumSerializer(choices, many=True).data)
        # next_sem_branch_registration_courses_data = serializers.CurriculumSerializer(next_sem_branch_registration_courses, many=True).data

        final_registration_choices = get_registration_courses(get_branch_courses(request.user, user_sem, user_branch))
        final_registration_choices_data = []
        for choices in final_registration_choices:
            final_registration_choices_data.append(serializers.CurriculumSerializer(choices, many=True).data)

        performance_list = []
        result_announced = False
        for i in currently_registered_courses:
            try:
                performance_obj = obj.semestermarks_set.all().filter(curr_id = i).first()
            except:
                performance_obj = None
            performance_list.append(performance_obj)
        performance_list_data = serializers.SemesterMarksSerializer(performance_list, many=True).data

        thesis_request_list = serializers.ThesisTopicProcessSerializer(obj.thesistopicprocess_set.all(), many=True).data

        pre_existing_thesis_flag = True if obj.thesistopicprocess_set.all() else False

        current_sem_branch_courses = get_branch_courses(current_user, user_sem, user_branch)

        pre_registration_date_flag = get_pre_registration_eligibility(current_date)
        final_registration_date_flag = get_final_registration_eligibility(current_date)

        add_or_drop_course_date_flag = get_add_or_drop_course_date_eligibility(current_date)

        student_registration_check_pre = obj.studentregistrationcheck_set.all().filter(semester=user_sem+1)
        student_registration_check_final = obj.studentregistrationcheck_set.all().filter(semester=user_sem)
        pre_registration_flag = False
        final_registration_flag = False
        if(student_registration_check_pre):
            pre_registration_flag = student_registration_check_pre.pre_registration_flag
        if(student_registration_check_final):
            final_registration_flag = student_registration_check_final.final_registration_flag

        teaching_credit_registration_course = None
        if phd_flag:
            teaching_credit_registration_course = Curriculum.objects.all().filter(batch = 2016, sem =6)
        teaching_credit_registration_course_data = serializers.CurriculumSerializer(teaching_credit_registration_course, many=True).data

        if student_flag:
            try:
                due = obj.dues_set.get()
                lib_d = due.library_due
                pc_d = due.placement_cell_due
                hos_d = due.hostel_due
                mess_d = due.mess_due
                acad_d = due.academic_due
            except:
                lib_d, pc_d, hos_d, mess_d, acad_d = 0, 0, 0, 0, 0

        tot_d = lib_d + acad_d + pc_d + hos_d + mess_d

        registers = obj.register_set.all()
        course_list = []
        for i in registers:
            course_list.append(i.curr_id)
        attendence = []
        for i in course_list:
            instructors = i.curriculum_instructor_set.all()
            pr,ab=0,0
            for j in list(instructors):

                presents = obj.student_attendance_set.all().filter(instructor_id=j, present=True)
                absents = obj.student_attendance_set.all().filter(instructor_id=j, present=False)
                pr += len(presents)
                ab += len(absents)
            attendence.append((i,pr,pr+ab))
        attendance_data = {}
        for course in attendence:
            attendance_data[course[0].course_id.course_name] = {
                'present' : course[1],
                'total' : course[2]
            }

        branchchange_flag = False
        if user_sem == 2:
            branchchange_flag=True

        # faculty_list = serializers.HoldsDesignationSerializer(get_faculty_list(), many=True).data

        resp = {
            'details': details,
            'currently_registered': currently_registered_courses_data,
            'pre_registered_courses' : pre_registered_courses_data,
            'pre_registered_courses_show' : pre_registered_courses_show_data,
            'final_registered_courses' : final_registered_courses_data,
            'current_credits' : current_credits,
            'courses_list': next_sem_branch_courses_data,
            'fee_payment_mode_list' : fee_payment_mode_list,
            'next_sem_branch_registration_courses' : next_sem_branch_registration_courses_data,
            'final_registration_choices' : final_registration_choices_data,
            'performance_list' : performance_list_data,
            'thesis_request_list' : thesis_request_list,
            'student_flag' : student_flag,
            'ug_flag' : ug_flag,
            'masters_flag' : masters_flag,
            'phd_flag' : phd_flag,
            'fac_flag' : fac_flag,
            'des_flag' : des_flag,
            'thesis_flag' : pre_existing_thesis_flag,
            'drop_courses_options' : currently_registered_courses_data,
            'pre_registration_date_flag': pre_registration_date_flag,
            'final_registration_date_flag': final_registration_date_flag,
            'add_or_drop_course_date_flag': add_or_drop_course_date_flag,
            'pre_registration_flag' : pre_registration_flag,
            'final_registration_flag': final_registration_flag,
            'teaching_credit_registration_course' : teaching_credit_registration_course_data,
            'lib_d':lib_d,
            'acad_d':acad_d,
            'mess_d':mess_d,
            'pc_d':pc_d,
            'hos_d':hos_d,
            'tot_d':tot_d,
            'attendance': attendance_data,
            'Branch_Change_Flag':branchchange_flag
            # 'faculty_list' : faculty_list
        }
        return Response(data=resp, status=status.HTTP_200_OK)

@api_view(['POST'])
def add_thesis(request):
    current_user = request.user
    profile = current_user.extrainfo
    if profile.user_type == 'student':
        if not 'thesis_topic' in request.data:
            return Response({'error':'Thesis topic is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not 'research_area' in request.data:
            return Response({'error':'Research area is required'}, status=status.HTTP_400_BAD_REQUEST)
        if 'supervisor_id' in request.data:
            try:
                supervisor_faculty = User.objects.get(username=request.data['supervisor_id'])
                supervisor_faculty = supervisor_faculty.extrainfo
                request.data['supervisor_id'] = supervisor_faculty
            except:
                return Response({'error':'Wrong supervisor id. User does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error':'supervisor id is required'}, status=status.HTTP_400_BAD_REQUEST)
        if 'co_supervisor_id' in request.data:
            try:
                co_supervisor_faculty = User.objects.get(username=request.data['co_supervisor_id'])
                co_supervisor_faculty = co_supervisor_faculty.extrainfo
                request.data['co_supervisor_id'] = co_supervisor_faculty
            except:
                return Response({'error':'Wrong co_supervisor id. User does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            co_supervisor_faculty = None
        if 'curr_id' in request.data:
            curr_id = None
        student = profile.student
        request.data['student_id'] = profile
        request.data['submission_by_student'] = True
        serializer = serializers.ThesisTopicProcessSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({'error':'Cannot add thesis'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
def approve_thesis(request, id):
    current_user = request.user
    profile = current_user.extrainfo
    if profile.user_type == 'faculty':
        try:
            thesis = ThesisTopicProcess.objects.get(id=id)
        except:
            return Response({'error':'This thesis does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        if 'member1' in request.data:
            try:
                user1 = User.objects.get(username=request.data['member1'])
                member1 = user1.extrainfo
                request.data['member1'] = member1
            except:
                return Response({'error':'Wrong username of member 1. User does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error':'Member 1 is required'}, status=status.HTTP_400_BAD_REQUEST)
        if 'member2' in request.data:
            try:
                user2 = User.objects.get(username=request.data['member2'])
                member2 = user2.extrainfo
                request.data['member2'] = member2
            except:
                return Response({'error':'Wrong username of member 2. User does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error':'Member 2 is required'}, status=status.HTTP_400_BAD_REQUEST)
        if 'member3' in request.data:
            try:
                user3 = User.objects.get(username=request.data['member3'])
                member3 = user3.extrainfo
                request.data['member3'] = member3
            except:
                return Response({'error':'Wrong username of member 3. User does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            member3 = None
        if not 'approval' in request.data:
            return Response({'error':'Approval value is required.'}, status=status.HTTP_400_BAD_REQUEST)
        elif request.data['approval'] != 'yes' and request.data['approval'] != 'no':
            return Response({'error':'Wrong approval value provided. Approval value should be yes or no'}, status=status.HTTP_400_BAD_REQUEST)
        if request.data['approval'] == 'yes':
            request.data.pop('approval', None)
            request.data['pending_supervisor'] = False
            request.data['approval_supervisor'] = True
            request.data['forwarded_to_hod'] = True
            request.data['pending_hod'] = True
        else:
            request.data.pop('approval', None)
            request.data['pending_supervisor'] = False
            request.data['approval_supervisor'] = False
            request.data['forwarded_to_hod'] = False
            request.data['pending_hod'] = False
        serializer = serializers.ThesisTopicProcessSerializer(thesis, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({'error':'Cannot approve thesis'}, status=status.HTTP_400_BAD_REQUEST)
