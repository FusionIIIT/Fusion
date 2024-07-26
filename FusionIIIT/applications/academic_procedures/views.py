from asyncio.log import logger
import traceback
from ctypes import Union
import json
from itertools import chain
from io import BytesIO
from django.template.loader import get_template
from xlsxwriter.workbook import Workbook
from xhtml2pdf import pisa
import xlrd
import logging
from django.db import transaction
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Max,Value,IntegerField,CharField,F,Sum
from django.http import HttpResponse, HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.template.loader import render_to_string
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from notification.views import AssistantshipClaim_notify,AssistantshipClaim_acad_notify,AssistantshipClaim_account_notify,AssistantshipClaim_faculty_notify
from applications.academic_information.models import (Calendar, Course, Student,Curriculum_Instructor, Curriculum,
                                                      Student_attendance)
                                                      
from applications.central_mess.models import(Monthly_bill, Payments)
from applications.online_cms.models import (Student_grades)
from applications.programme_curriculum.models import (CourseSlot, Course as Courses, Batch, Semester , CourseInstructor)
from applications.globals.models import (DepartmentInfo, Designation,
                                         ExtraInfo, Faculty, HoldsDesignation)
from applications.programme_curriculum.models import Course as Courses
from .models import (BranchChange, CoursesMtech, InitialRegistration, StudentRegistrationChecks,
                     Register, Thesis, FinalRegistration, ThesisTopicProcess,
                     Constants, FeePayments, TeachingCreditRegistration, SemesterMarks, 
                     MarkSubmissionCheck, Dues,AssistantshipClaim, MTechGraduateSeminarReport,
                     PhDProgressExamination,CourseRequested, course_registration, MessDue, Assistantship_status , backlog_course)
from notification.views import academics_module_notif
from .forms import BranchChangeForm
from django.db.models.functions import Concat,ExtractYear,ExtractMonth,ExtractDay,Cast
from .api import serializers
from django.core.serializers import serialize
import datetime

"""every newfuncitons that have been created with name auto_ in start of their original name is to implement new logic of registraion .. 
unlike the previous registration logic that was done with priority """


demo_date = timezone.now()
# demo_date = demo_date - datetime.timedelta(days = 180)
# demo_date = demo_date + datetime.timedelta(days = 180)
# demo_date = demo_date + datetime.timedelta(days = 3)
# demo_date = demo_date - datetime.timedelta(days = 5)
student_status = None
hod_status = None
account_status = None
available_cse_seats = 100
available_ece_seats = 100
available_me_seats = 100




@login_required(login_url='/accounts/login')
def academic_procedures_redirect(request):
    return HttpResponseRedirect('/academic-procedures/main/')


@login_required(login_url='/accounts/login')
def main(request):
    return HttpResponseRedirect('/academic-procedures/main/')


@login_required(login_url='/accounts/login')
def academic_procedures(request):

    current_user = get_object_or_404(User, username=request.user.username)

    #extra info details , user id used as main id
    user_details = ExtraInfo.objects.select_related('user','department').get(user = request.user)
    
    # des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()
    
    if request.session.get('currentDesignationSelected') == "student":
        obj = Student.objects.select_related('id','id__user','id__department').get(id = user_details.id)
        return HttpResponseRedirect('/academic-procedures/stu/')
        # return HttpResponseRedirect('/logout/')
    elif request.session.get('currentDesignationSelected') == "faculty" or request.session.get('currentDesignationSelected') == "Associate Professor" or request.session.get('currentDesignationSelected') == "Professor" or request.session.get('currentDesignationSelected') == "Assistant Professor" :
        return HttpResponseRedirect('/academic-procedures/fac/')
        # return HttpResponseRedirect('/logout/')

    elif request.session.get('currentDesignationSelected') == "acadadmin" :
        return HttpResponseRedirect('/aims/')

    elif str(request.user) == "rizwan":
        return HttpResponseRedirect('/academic-procedures/account/')
    
    elif str(request.user) == "talib":
        Messdue = MessDue.objects.all()
        dues = Dues.objects.all()
        return render(request,
        '../templates/academic_procedures/messdueassistant.html' ,
        {
            'Mess_due' : Messdue,
            'dues' : dues,

        })
    else:
        return HttpResponseRedirect('/dashboard/')
#
#
#
#
#
#
@login_required(login_url='/accounts/login')
def academic_procedures_faculty(request):

    current_user = get_object_or_404(User, username=request.user.username)
    if request.user.extrainfo.user_type != 'faculty':
        return HttpResponseRedirect('/dashboard/')
    #extra info details , user id used as main id
    user_details = ExtraInfo.objects.select_related('user','department').get(user = request.user)
    des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()
    fac_id = user_details
    fac_name = user_details.user.first_name + " " + user_details.user.last_name
    # if str(des.designation) == "student":
    #     return HttpResponseRedirect('/academic-procedures/main/')

    # elif str(request.user) == "acadadmin":
    #     return HttpResponseRedirect('/academic-procedures/main/')
    notifs = request.user.notifications.all()
    if request.session.get('currentDesignationSelected') == "faculty" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor":
       
        object_faculty = Faculty.objects.select_related('id','id__user','id__department').get(id = user_details.pk)
       
        month = int(demo_date.month)
        sem = []
        if month>=7 and month<=12:
            sem = [1,3,5,7]
        else:
            sem = [2,4,6,8]
        student_flag = False
        fac_flag = True
        Faculty_department =user_details.department
        # temp = Curriculum.objects.all().filter(course_code = "CS315L").first()
        # Curriculum_Instructor.objects.create(curriculum_id = temp, instructor_id = user_details)
        #thesis_supervision_request_list = ThesisTopicProcess.objects.all()
        thesis_supervision_request_list = ThesisTopicProcess.objects.all().select_related().filter(supervisor_id = object_faculty)
        approved_thesis_request_list = thesis_supervision_request_list.filter(approval_supervisor = True)
        pending_thesis_request_list = thesis_supervision_request_list.filter(pending_supervisor = True)
        faculty_list = get_faculty_list()
        assistantship_request_list = AssistantshipClaim.objects.all()
        hod_assistantship_request_list = assistantship_request_list.filter(ta_supervisor_remark = True).filter(thesis_supervisor_remark = True).filter(hod_approval = False)
        hod_approved_assistantship = assistantship_request_list.filter(ta_supervisor_remark = True).filter(thesis_supervisor_remark = True).filter(acad_approval = False)
        ta_approved_assistantship_request_list = AssistantshipClaim.objects.all().filter(ta_supervisor_remark=True)
        thesis_approved_assistantship_request_list = AssistantshipClaim.objects.all().filter(thesis_supervisor_remark=True)
        approved_assistantship_request_list = ta_approved_assistantship_request_list | thesis_approved_assistantship_request_list
        mtechseminar_request_list = MTechGraduateSeminarReport.objects.all().filter(Overall_grade = '')
        phdprogress_request_list = PhDProgressExamination.objects.all().filter(Overall_grade = '')
        courses_list = list(CourseInstructor.objects.select_related('course_id', 'batch_id', 'batch_id__discipline').filter(instructor_id__id=fac_id.id).only('course_id__code', 'course_id__name', 'batch_id'))

        assigned_courses = CourseInstructor.objects.select_related('course_id', 'batch_id', 'batch_id__discipline').filter(
                            instructor_id__id=fac_id.id,  # Filter by faculty ID
                            batch_id__running_batch=True,  # Filter by currently running batches
                            course_id__working_course=True  # Filter by currently active courses
                            ).only('course_id__code', 'course_id__name', 'batch_id')
        assigned_courses = list(assigned_courses)
        
        # print('------------------------------------------------------------------------------------------------------------------' , list(assigned_courses))
        r = range(4)
        return render(
                        request,
                         '../templates/academic_procedures/academicfac.html' ,
                         {
                            'student_flag' : student_flag,
                            'fac_flag' : fac_flag,
                            'hod_flag' : hod_status,
                            'thesis_supervision_request_list' : thesis_supervision_request_list,
                            'pending_thesis_request_list' : pending_thesis_request_list,
                            'approved_thesis_request_list' : approved_thesis_request_list,
                            'faculty_list' : faculty_list,
                            'courses_list' : courses_list,
                            'fac_id': fac_id,
                            'fac_name' : fac_name,
                            'department' : Faculty_department,
                            'assistantship_request_list' : assistantship_request_list,
                            'approved_assistantship_request_list' : approved_assistantship_request_list,
                            'hod_assistantship_request_list' : hod_assistantship_request_list,
                            'hod_approved_assistantship' : hod_approved_assistantship,
                            'mtechseminar_request_list' : mtechseminar_request_list,
                            'phdprogress_request_list' : phdprogress_request_list,
                            'r' : r,
                            'assigned_courses' : assigned_courses,
                            'notifications': notifs,
                        })
    else:
        HttpResponse("user not found")


@login_required(login_url='/accounts/login')
def account(request):
    assistant_account_list = AssistantshipClaim.objects.filter(ta_supervisor_remark = True).filter(thesis_supervisor_remark = True)
    assistant_pen_list = AssistantshipClaim.objects.filter(ta_supervisor_remark = True).filter(thesis_supervisor_remark = True).filter(acad_approval = True).filter(account_approval = False)
    assistant_account_length = len(assistant_account_list.filter(acad_approval = True).filter(account_approval = False))
    return render(request,
                        '../templates/ais/account.html' ,
                        {
                            'assistant_account_length' : assistant_account_length,
                            'assistant_account_list' : assistant_account_list ,
                            'assistant_pen_list' : assistant_pen_list,
                            'account_flag' : account_status,
                        })


@login_required(login_url='/accounts/login')
def academic_procedures_student(request):

    current_user = get_object_or_404(User, username=request.user.username)
    # if global_var != "student":
    #     return HttpResponse("Student has no record") 
    user_details = ExtraInfo.objects.select_related('user','department').get(id = request.user)
    des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()

    if str(des.designation) == "student":
        notifs = request.user.notifications.all()
        obj = Student.objects.select_related('id','id__user','id__department').get(id = user_details.id)

        if obj.programme.upper() == "PHD" :
            student_flag = True
            ug_flag = False
            masters_flag = False
            phd_flag = True
            fac_flag = False
            des_flag = False

        elif obj.programme.upper() == "M.DES" :
            student_flag = True
            ug_flag = False
            masters_flag = True
            phd_flag = False
            fac_flag = False
            des_flag = True

        elif obj.programme.upper() == "B.DES" :
            student_flag = True
            ug_flag = True
            masters_flag = False
            phd_flag = False
            fac_flag = False
            des_flag = True

        elif obj.programme.upper() == "M.TECH" :
            student_flag = True
            ug_flag = False
            masters_flag = True
            phd_flag = False
            fac_flag = False
            des_flag = False

        elif obj.programme.upper() == "B.TECH" :
            student_flag = True
            ug_flag = True
            masters_flag = False
            phd_flag = False
            fac_flag = False
            des_flag = False




        else :
            return HttpResponse("Student has no record")
        
        
        # masters_flag=True
        current_date = demo_date.date()
        year = demo_date.year
        
        registers = get_student_register(user_details.id)
        # user_sem = get_user_semester(request.user, ug_flag, masters_flag, phd_flag)
        user_branch = get_user_branch(user_details)

        batch = obj.batch_id

        #Actual Fee values in final registration form autofill purpose
        actual_fee_values=0
        if phd_flag==True:
            if batch.year==2015 or batch.year==2016:
                actual_fee_values=25000
            elif batch.year==2017:
                actual_fee_values=27000
            elif batch.year==2018:
                actual_fee_values=28700
            elif batch.year==2019 or batch.year==2020:
                actual_fee_values=32450
            elif batch.year==2021:
                actual_fee_values=39100
        elif masters_flag==True:
            if batch.year==2019 or batch.year==2020:
                actual_fee_values=73750
            elif batch.year==2021:
                actual_fee_values=79000
        elif ug_flag==True:
            if batch.year==2019 or batch.year==2020:
                actual_fee_values = 73040
            elif batch.year==2021:
                actual_fee_values = 83720
        
        curr_id = batch.curriculum
        curr_sem_id = Semester.objects.get(curriculum = curr_id, semester_no = obj.curr_semester_no)

        try:
            semester_no = obj.curr_semester_no+1
            next_sem_id = Semester.objects.get(curriculum = curr_id, semester_no = semester_no)
            user_sem = semester_no
            
        except Exception as e:
            user_sem = get_user_semester(request.user, ug_flag, masters_flag, phd_flag)
            next_sem_id = curr_sem_id

        student_registration_check_pre = get_student_registrtion_check(obj,next_sem_id)
        student_registration_check_final = get_student_registrtion_check(obj,next_sem_id)

        cpi = get_cpi(user_details.id)

        # branch change flag
        # Only First Year B.Tech student should have this option
        branchchange_flag=False
        if user_sem==2 and des_flag==False and ug_flag==True:
            branchchange_flag=True

        pre_registration_date_flag, prd_start_date= get_pre_registration_eligibility(current_date, user_sem, year)
        final_registration_date_flag = get_final_registration_eligibility(current_date)
        add_or_drop_course_date_flag = get_add_or_drop_course_date_eligibility(current_date)
        pre_registration_flag = False
        final_registration_flag = False

       # print("student registration check ----------> ",student_registration_check_pre.pre_registration_flag)

        if(student_registration_check_pre):
            pre_registration_flag = student_registration_check_pre.pre_registration_flag
        if(student_registration_check_final):
            final_registration_flag = student_registration_check_final.final_registration_flag

        # print(">>>>>>>>>>>>>>>>>>>>>>",student_registration_check_pre.pre_registration_flag)
        
        acad_year = get_acad_year(user_sem, year)
        currently_registered_courses = get_currently_registered_courses(user_details.id, user_sem)

        next_sem_branch_course = get_sem_courses(next_sem_id, batch)
        current_sem_branch_course = get_sem_courses(curr_sem_id, batch)
        next_sem_registration_courses = get_sem_courses(next_sem_id, batch)
        final_registration_choice, unavailable_courses_nextsem = get_final_registration_choices(next_sem_registration_courses,batch.year)
        currently_registered_course = get_currently_registered_course(obj,obj.curr_semester_no)

        current_credits = get_current_credits(currently_registered_course)
 
        cur_cpi=0.0
        details = {
                'current_user': current_user,
                'year': acad_year,
                'user_sem': user_sem - 1,
                'user_branch' : str(user_branch),
                'cpi' : cpi,
                }
        cur_cpi=details['cpi']

        swayam_courses_count = 0
        next_sem_student = user_sem + 1
        if(next_sem_student > 2):
            swayam_courses_count = 2
        if(next_sem_student == 6 or next_sem_student == 7 or next_sem_student == 8):
            swayam_courses_count = 3

        try:
            pre_registered_courses = InitialRegistration.objects.all().filter(student_id = user_details.id,semester_id = next_sem_id)
            pre_registered_course_show = {}
            pre_registration_timestamp=None
            for pre_registered_course in pre_registered_courses:
                pre_registration_timestamp=pre_registered_course.timestamp
                if(pre_registered_course.course_slot_id.name not in pre_registered_course_show):
                    pre_registered_course_show[pre_registered_course.course_slot_id.name] = [{"course_code":pre_registered_course.course_id.code,"course_name":pre_registered_course.course_id.name,"course_credit":pre_registered_course.course_id.credit,"priority":pre_registered_course.priority}]
                else:
                    pre_registered_course_show[pre_registered_course.course_slot_id.name].append({"course_code":pre_registered_course.course_id.code,"course_name":pre_registered_course.course_id.name,"course_credit":pre_registered_course.course_id.credit,"priority":pre_registered_course.priority})
            pre_registration_timestamp=str(pre_registration_timestamp)
        except Exception as e:
            pre_registered_courses =  None
            pre_registered_course_show = None

        try:
            final_registered_courses = FinalRegistration.objects.all().filter(student_id = user_details.id,semester_id = next_sem_id)
            final_registered_course_show=[]
            for final_registered_course in final_registered_courses:
                final_registered_course_show.append({"course_code":final_registered_course.course_id.code,"course_name":final_registered_course.course_id.name,"course_credit":final_registered_course.course_id.credit})
            add_courses_options = get_add_course_options(current_sem_branch_course, currently_registered_course, batch.year)
            drop_courses_options = get_drop_course_options(currently_registered_course)
            replace_courses_options = get_replace_course_options(currently_registered_course, batch.year)
        except Exception as e:
            final_registered_courses = None
            final_registered_course_show = None
            drop_courses_options = None
            add_courses_options = None
            replace_courses_options = None

        fee_payment_mode_list = dict(Constants.PaymentMode)


        performance_list = []
        result_announced = False
        for i in currently_registered_courses:
            try:
                performance_obj = SemesterMarks.objects.all().select_related('curr_id','student_id','curr_id__course_id','student_id__id','student_id__id__user','student_id__id__department').filter(student_id = obj, curr_id = i).first()
            except Exception as e:
                performance_obj = None
            performance_list.append(performance_obj)
        for i in currently_registered_courses:
            try:
                result_announced_obj = MarkSubmissionCheck.objects.select_related().get(curr_id = i)
                if result_announced_obj:
                    if result_announced_obj.announced == True:
                        result_announced = result_announced_obj.announced
                else:
                    continue
            except Exception as e:
                continue


        faculty_list = None
        thesis_request_list = None
        assistantship_list = None
        pre_existing_thesis_flag = False
        teaching_credit_registration_course = None
        if masters_flag:
            faculty_list = get_faculty_list()    
            thesis_request_list = ThesisTopicProcess.objects.all().filter(student_id = obj)
            assistantship_list = AssistantshipClaim.objects.all().filter(student = obj)
            pre_existing_thesis_flag = get_thesis_flag(obj)
        if phd_flag:
            pre_existing_thesis_flag = get_thesis_flag(obj)
            teaching_credit_registration_course = Curriculum.objects.all().select_related().filter(batch = 2016, sem =6)

        # Dues Check
        #Initializing all due with -1 value , since generating no due certificate requires total due=0 
        lib_d, pc_d, hos_d, mess_d, acad_d = -1, -1, -1, -1, -1
        if student_flag:
            try:

                obj = Dues.objects.select_related().get(student_id=Student.objects.select_related('id','id__user','id__department').get(id=request.user.username))

                lib_d = obj.library_due
                pc_d = obj.placement_cell_due
                hos_d = obj.hostel_due
                mess_d = obj.mess_due
                acad_d = obj.academic_due
            except ObjectDoesNotExist:
                logging.warning("entry in DB not found for student")

        tot_d = lib_d + acad_d + pc_d + hos_d + mess_d
        obj = Student.objects.select_related('id','id__user','id__department').get(id=request.user.username)
        course_list = []
        for i in registers:
            course_list.append(i.curr_id)
        attendence = []
        for i in course_list:

            instructors = Curriculum_Instructor.objects.select_related('curriculum_id','instructor_id','curriculum_id__course_id','instructor_id__department','instructor_id__user').filter(curriculum_id=i)
            pr,ab=0,0
            for j in list(instructors):

                presents = Student_attendance.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department','instructor_id','instructor_id__curriculum_id','instructor_id__curriculum_id__course_id','instructor_id__instructor_id','instructor_id__instructor_id__user','instructor_id__instructor_id__department').filter(student_id=obj,instructor_id=j, present=True)

                absents = Student_attendance.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department','instructor_id','instructor_id__curriculum_id','instructor_id__curriculum_id__course_id','instructor_id__instructor_id','instructor_id__instructor_id__user','instructor_id__instructor_id__department').filter(student_id=obj,instructor_id=j, present=False)
                pr += len(presents)
                ab += len(absents)
            attendence.append((i,pr,pr+ab))
        cur_spi='Sem results not available' # To be fetched from db if result uploaded

        backlogCourseList = []
        auto_backlog_courses = list(Student_grades.objects.filter(roll_no = obj , grade = 'F'))
        auto_backlog_courses_list = []
        for i in auto_backlog_courses:
            if not i.course_id.courseslots.filter(type__contains="Optional").exists():
                auto_backlog_courses_list.append([i.course_id.name, i.course_id.code, i.course_id.version, i.course_id.credit , i.grade])

        backlogCourses = backlog_course.objects.select_related('course_id' , 'student_id' , 'semester_id' ).filter(student_id=obj)
        for i in backlogCourses:
            summer_course = "Yes" if i.is_summer_course else "No"
            course_details = i.course_id.course_details if i.course_id.course_details else "N/A"

            backlogCourseList.append([i.course_id.course_name, course_details , i.semester_id.semester_no , summer_course])
        
        # Mess_bill = Monthly_bill.objects.filter(student_id = obj)
        # Mess_pay = Payments.objects.filter(student_id = obj)
        Mess_bill = []
        Mess_pay = []
        # Branch Change Form save
        if request.method=='POST':
            if True:
                # Processing Branch Change form
                objb = BranchChange()
                objb.branches=request.POST['branches']
                objb.save()

        return render(
                          request, '../templates/academic_procedures/academic.html',
                          {'details': details,
                        #    'calendar': calendar,
                            'currently_registered': currently_registered_course,
                            'pre_registered_course' : pre_registered_courses,
                            'pre_registered_course_show' : pre_registered_course_show,
                            'final_registered_course' : final_registered_courses,
                            'final_registered_course_show' : final_registered_course_show,
                            'actual_fee_values' : actual_fee_values,
                            'current_credits' : current_credits,
                            'courses_list': next_sem_branch_course,
                            'fee_payment_mode_list' : fee_payment_mode_list,
                            'next_sem_registration_courses': next_sem_registration_courses,
                            'final_registration_choice' : final_registration_choice,
                            'unavailable_courses_nextsem' : unavailable_courses_nextsem,
                            'performance_list' : performance_list,
                            'faculty_list' : faculty_list,
                            'thesis_request_list' : thesis_request_list,
                            'assistantship_list' : assistantship_list,
                            'next_sem': next_sem_id,
                            'curr_sem': curr_sem_id,

                           # 'final_register': final_register,
                           'student_flag' : student_flag,
                            'ug_flag' : ug_flag, 
                           'masters_flag' : masters_flag,
                           'phd_flag' : phd_flag,
                           'fac_flag' : fac_flag,
                           'des_flag' : des_flag,
                           'result_announced' : result_announced,
                           'thesis_flag' : pre_existing_thesis_flag,
                            
                           # 'change_branch': change_branch,
                           # 'add_course': add_course,
                            'add_courses_options': add_courses_options,
                            'drop_courses_options' : drop_courses_options,
                            'replace_courses_options' : replace_courses_options,
                           # 'pre_register': pre_register,
                            'pre_registration_timestamp': pre_registration_timestamp,
                            'prd': pre_registration_date_flag,
                            'prd_start_date': prd_start_date,
                            'frd': final_registration_date_flag,
                            'adc_date_flag': add_or_drop_course_date_flag,
                            'pre_registration_flag' : pre_registration_flag,
                            'final_registration_flag': final_registration_flag,
                            'swayam_courses_count':swayam_courses_count,
                           # 'final_r': final_register_1,
                            
                            'teaching_credit_registration_course' : teaching_credit_registration_course,
                            'cur_cpi': cur_cpi,
                           'cur_spi': cur_spi,
                           # 'mincr': minimum_credit,
                           'Mess_bill' : Mess_bill,
                           'Mess_pay' : Mess_pay,
                           'lib_d':lib_d,
                           'acad_d':acad_d,
                           'mess_d':mess_d,
                           'pc_d':pc_d,
                           'hos_d':hos_d,
                            'tot_d':tot_d,
                           'attendence':attendence,
                           'backlogCourseList' : backlogCourseList,
                           'auto_backlog_courses_list' : auto_backlog_courses_list,
                           'BranchChangeForm': BranchChangeForm(),
                           'BranchFlag':branchchange_flag,
                           'assistantship_flag' : student_status,
                           'notifications': notifs,
                           }
                )

    elif request.session.get('currentDesignationSelected') == "Associate Professor" :
        return HttpResponseRedirect('/academic-procedures/main/')

    elif request.session.get('currentDesignationSelected') == "acadadmin" :
        return HttpResponseRedirect('/academic-procedures/main/')

    else:
        return HttpResponse('user not found')


def dues_pdf(request):
    template = get_template('academic_procedures/dues_pdf.html')
    current_user = get_object_or_404(User, username=request.user.username)

    user_details = ExtraInfo.objects.get(id = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()

    name = ExtraInfo.objects.all().filter(id=request.user.username)[0].user
   
    if str(des.designation) == "student":
        obj = Student.objects.get(id = user_details.id)
    
        context = {
            'student_id' : request.user.username,
            'degree' : obj.programme.upper(),
            'name' : name.first_name +" "+ name.last_name,
            'branch' : get_user_branch(user_details),
            
        }
        pdf = render_to_pdf('academic_procedures/dues_pdf.html',context)
        if pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename=Bonafide.pdf' 
            return response
        return HttpResponse("PDF could not be generated")


def facultyData(request):
	current_value = request.POST['current_value']
	try:
		# students =ExtraInfo.objects.all().filter(user_type = "student")
		faculty = ExtraInfo.objects.all().filter(user_type = "faculty")
		facultyNames = []
		for i in faculty:
			name = i.user.first_name + " " + i.user.last_name
			if current_value != "":
				Lowname = name.lower()
				Lowcurrent_value = current_value.lower()
				if Lowcurrent_value in Lowname:
					facultyNames.append(name)
			else:
				facultyNames.append(name)
        
		faculty = json.dumps(facultyNames)
		return HttpResponse(faculty)
	except Exception as e:
		return HttpResponse("error")







def get_course_to_show_pg(initial_courses, final_register):
    '''
        This function fetches the PG courses from the database and store them into list x.
        @param:
                initial_courses - The courses that the registered PG student has already selected.
                final_register - Finally registered courses of the user.

        @variables:
                x - The courses that are not being finally registered.
    '''
    x = []
    for i in initial_courses:
        flag = 0
        for j in final_register:
            if(str(i.course_name) == str(j.course_id)):
                flag = 1
        if(flag == 0):
            x.append(i)
    return x




def get_pg_course(usersem, specialization):
    '''
        This function fetches the PG Spcialization courses from the database and store them into list result.
        @param:
                usersem - Current semester of the user.
                specialization - has the specialization of the logged in PG student.

        @variables:
                result - The selected Specialization courses.
    '''
    usersem = 2
    obj = CoursesMtech.objects.select_related().filter(specialization=specialization)
    obj3 = CoursesMtech.objects.select_related().filter(specialization="all")
    obj2 = Course.objects.filter(sem=usersem)
    result = []
    for i in obj:
        p = i.c_id
        for j in obj2:
            if(str(j.course_name) == str(p)):
                result.append(j)
    for i in obj3:
        p = i.c_id
        for j in obj2:
            if(str(j.course_name) == str(p)):
                result.append(j)
    return result





def get_add_course(branch, final):
    '''
        This function shows the courses that were added after pre-registration.
        @param:
                branch - Branch of the Logged in student.
                final - all the added courses after pre-registration.

        @variables:
                x - all the added courses after pre-registration.
                total_course - al the remaining courses that were not added.
    '''
    x = []
    for i in final:
        x.append(i.course_id)
    total_course = []
    for i in branch:
        if i not in x:
            total_course.append(i)
    return total_course





@login_required(login_url='/accounts/login')
def apply_branch_change(request):
    '''
        This function is used to verify the details to apply for the branch change. It checks the requirement and tells the user if he/she can change the branch or not.
        @param:
                request - trivial

        @variables:
                branches - selected branches by the user.
                student - details of the logged in user.
                extraInfo_user - gets the user details from the extrainfo model.
                cpi_data - cpi of the logged in user.
                semester - user's semester.
                label_for_change - boolean variable to check the eligibility.

    '''
    # Get all the departments
    # branch_list = DepartmentInfo.objects.all()
    branches = ['CSE', 'ME', 'ECE']

    # Get the current logged in user
    student = User.objects.all().filter(username=request.user).first()

    # Get the current logged in user's cpi
    extraInfo_user = ExtraInfo.objects.all().select_related('user','department').filter(user=student).first()
    cpi_data = Student.objects.all().select_related('id','id__user','id__department').filter(id=extraInfo_user.id).first()
    # for i in range(len(branch_list)):
    #     branch_cut = branch_list[i].name
    #     branches.append(branch_cut)

    label_for_change = False

    semester = get_user_semester(extraInfo_user.id, ug_flag, masters_flag, phd_flag)
    # semester = 2

    if cpi_data.cpi >= 8 and semester >= 1 and semester <= 2:
        label_for_change = True

    context = {
            'branches': branches,
            'student': student,
            'cpi_data': cpi_data,
            'label_for_change': label_for_change,
        }
    return context


def branch_change_request(request):
    '''
        This function is used to apply the branch change request.
        @param:
                request - trivial

        @variables:
                current_user - details of the current user.
                student - details of the logged in student.
                extraInfo_user - gets the user details from the extrainfo model.
                department - user's applied brach.
    '''

    if request.method == 'POST':
        current_user = get_object_or_404(User, username=request.user.username)
        extraInfo_user = ExtraInfo.objects.all().select_related('user','department').filter(user=current_user).first()
        student = Student.objects.all().select_related('id','id__user','id__department').filter(id=extraInfo_user.id).first()
        department = DepartmentInfo.objects.all().filter(id=int(request.POST['branches'])).first()
        change_save = BranchChange(
            branches=department,
            user=student
            )
        change_save.save()
        return HttpResponseRedirect('/academic-procedures/main')
    else:
        return HttpResponseRedirect('/academic-procedures/main')





@login_required(login_url='/acounts/login')
def approve_branch_change(request):
    '''
        This function is used to approve the branch change requests from acad admin's frame.
        @param:
                request - trivial

        @variables:
                choices - list of students who applied for the branch change.
                branches - selected brances by the student.
                get_student - updating the student's branch after approval.
                branch - branch of the current user.
    '''
    if request.method == 'POST':
        values_length = len(request.POST.getlist('choice'))
        choices = []
        branches = []
        for i in range(values_length):
            for key, values in request.POST.lists():
                if key == 'branch':
                    branches.append(values[i])
                if key == 'choice':
                    choices.append(values[i])
                else:
                    continue
        changed_branch = []
        for i in range(len(branches)):
            get_student = ExtraInfo.objects.all().select_related('user','department').filter(id=choices[i][:7])
            get_student = get_student[0]
            branch = DepartmentInfo.objects.all().filter(name=branches[i])
            get_student.department = branch[0]
            changed_branch.append(get_student)
            student = Student.objects.all().select_related('id','id__user','id__department').filter(id=choices[i][:7]).first()
            change = BranchChange.objects.select_related('branches','user','user__id','user__id__user','user__id__department').all().filter(user=student)
            change = change[0]
            change.delete()
        try:
            ExtraInfo.objects.bulk_update(changed_branch,['department'])
            messages.info(request, 'Apply for branch change successfull')
        except:
            messages.info(request, 'Unable to proceed, we will get back to you very soon')
        return HttpResponseRedirect('/academic-procedures/main')

    else:
        messages.info(request, 'Unable to proceed')
        return HttpResponseRedirect('/academic-procedures/main')

# Function returning Branch , Banch data which was required many times
def get_batch_query_detail(month, year):
    '''
        This function is used to get the batch's detail simply return branch which is required often.
        @param:
                month - current month
                year - current year.

        @variables:
                stream1 - string BTech.
                stream2 - string MTech.
                query_option1 - year to be shown on students course sho page acad admin
    '''
    stream1 = "B.Tech "
    stream2 = "M.Tech "
    query_option1 = {}
    if(month >= 7):
        query_option1 = {
                            stream1+str(year): stream1+str(year),
                            stream1+str(year-1): stream1+str(year-1),
                            stream1+str(year-2): stream1+str(year-2),
                            stream1+str(year-3): stream1+str(year-3),
                            stream1+str(year-4): stream1+str(year-4),
                            stream2+str(year): stream2+str(year),
                            stream2+str(year-1): stream2+str(year)}
    else:
        query_option1 = {
                            stream1+str(year-1): stream1+str(year-1),
                            stream1+str(year-2): stream1+str(year-2),
                            stream1+str(year-3): stream1+str(year-3),
                            stream1+str(year-4): stream1+str(year-4),
                            stream1+str(year-5): stream1+str(year-5),
                            stream2+str(year-1): stream2+str(year-1),
                            stream2+str(year-2): stream2+str(year-2), }
    return query_option1


# view when Admin drops a user course
@login_required(login_url='/accounts/login')
def dropcourseadmin(request):
    '''
        This function is used to get the view when Acad Admin drops any course of any student.
        @param:
                request - trivial

        @variables:
                data - user's id.
                rid - Registration ID of Registers table
                response_data - data to be responded.
    '''
    data = request.GET.get('id')
    data = data.split(" - ")
    student_id = data[0]
    course_code = data[1]
    course = Courses.objects.get(code=course_code , version = 1.0)
    # need to add batch and programme
    # curriculum_object = Curriculum.objects.all().filter(course_code = course_code)
    try:
        # Register.objects.filter(curr_id = curriculum_object.first(),student_id=int(data[0])).delete()
        course_registration.objects.filter(student_id = student_id , course_id = course.id).delete()
    except Exception as e:
        print(str(e))
        pass
        # print("hello ")
    response_data = {}
    return HttpResponse(json.dumps(response_data), content_type="application/json")

@login_required(login_url='/accounts/login')
def gen_course_list(request):
    if(request.POST):
        try:
            batch = request.POST['batch']
            course_id = request.POST['course']
            course = Courses.objects.get(id = course_id)
            #obj = course_registration.objects.all().filter(course_id = course)
            obj=course_registration.objects.filter(course_id__id=course_id, working_year=batch).select_related(
            'student_id__id__user','student_id__id__department').only('student_id__batch', 
            'student_id__id__user__first_name', 'student_id__id__user__last_name',
            'student_id__id__department__name','student_id__id__user__username')
        except Exception as e:
            batch=""
            course=""
            obj=""
        verified_students = []
        for registration in obj:
            final_registration = FinalRegistration.objects.filter(
                course_id=course,
                semester_id=registration.semester_id,
                student_id=registration.student_id,
                verified=True
            ).exists()
            if final_registration:
                verified_students.append({
                    "rollno": registration.student_id.id.user.username,
                    "name": registration.student_id.id.user.first_name + " " + registration.student_id.id.user.last_name,
                    "department": registration.student_id.id.department.name
                })
        html = render_to_string('academic_procedures/gen_course_list.html',
                                {'students': verified_students, 'batch':batch, 'course':course_id}, request)
        maindict = {'html': html}
        obj = json.dumps(maindict)
        return HttpResponse(obj, content_type='application/json')    

# view where Admin verifies the registered courses of every student


@login_required(login_url='/accounts/login')
def verify_course(request):
    '''
        This function is used to get the view when Acad Admin verifies the registered courses of every student.
        @param:
                request - trivial

        @variables:
                current_user - details of current user.
                desig_id - Finds the Acad admin whose designation is "Upper Division Clerk".
                acadadmin - details of the acad person(logged in).
                roll_no - roll number of all the students.
                firstname - firstname of the students.
                year - current year.
                month - current month.
                date - current date.
    '''
    if(request.POST):
        current_user = get_object_or_404(User, username=request.user.username)
        user_details = ExtraInfo.objects.all().select_related(
            'user', 'department').filter(user=current_user).first()
        desig_id = Designation.objects.all().filter(name='acadadmin').first()
        temp = HoldsDesignation.objects.all().select_related().filter(
            designation=desig_id).first()
        acadadmin = temp.working
        k = str(user_details).split()
        final_user = k[2]
        if ('acadadmin' != request.session.get('currentDesignationSelected')):
            return HttpResponseRedirect('/academic-procedures/')
        roll_no = request.POST["rollNo"]
        obj = ExtraInfo.objects.all().select_related(
            'user', 'department').filter(id=roll_no).first()
        firstname = obj.user.first_name
        lastname = obj.user.last_name
        dict2 = {'roll_no': roll_no,
                 'firstname': firstname, 'lastname': lastname}
        obj2 = Student.objects.all().select_related(
            'id', 'id__user', 'id__department').filter(id=roll_no).first()
        # obj = Register.objects.all().select_related('curr_id', 'student_id', 'curr_id__course_id',
        #                                             'student_id__id', 'student_id__id__user', 'student_id__id__department').filter(student_id=obj2)
        batch = obj2.batch_id
        curr_id = batch.curriculum
        curr_sem_id = Semester.objects.get(curriculum = curr_id, semester_no = obj2.curr_semester_no)
        # curr_sem_id = obj2.curr_semester_no
        details = []

        current_sem_courses = get_currently_registered_course(
            roll_no, curr_sem_id)

        idd = obj2
        for z in current_sem_courses:
            z = z[1]
            print(z)
            course_code = z.code
            course_name = z.name
            # course_code, course_name = str(z).split(" - ")
            k = {}
            # reg_ig has course registration id appended with the the roll number
            # so that when we have removed the registration we can be redirected to this view
            k['reg_id'] = roll_no+" - "+course_code
            k['rid'] = roll_no+" - "+course_code
            # Name ID Confusion here , be carefull
            courseobj2 = Courses.objects.all().filter(code=course_code)
            # if(str(z.student_id) == str(idd)):
            for p in courseobj2:
                k['course_id'] = course_code
                k['course_name'] = course_name
                k['sem'] = curr_sem_id.semester_no
                k['credits'] = p.credit
            details.append(k)

        year = demo_date.year
        month = demo_date.month
        yearr = str(year) + "-" + str(year+1)
        semflag = 0
        if(month >= 7):
            semflag = 1
        else:
            semflag = 2
        # TO DO Bdes
        date = {'year': yearr, 'semflag': semflag}
        course_list = Courses.objects.all()
        semester_list = Semester.objects.all()
        semester_no_list=[]
        for i in semester_list:
            semester_no_list.append(int(i.semester_no))
        html = render_to_string('academic_procedures/studentCourses.html',
                                {'details': details,
                                 'dict2': dict2,
                                 'course_list': course_list,
                                 'semester_list': semester_list,
                                 'date': date}, request)

        maindict = {'html': html}
        obj = json.dumps(maindict)
        return HttpResponse(obj, content_type='application/json')

# view to generate all list of students


# view to add Course for a student
def acad_add_course(request):
    if(request.method == "POST"):
        course_id = request.POST["course_id"]
        course = Courses.objects.get(id=course_id)
        roll_no = request.POST['roll_no']
        student = Student.objects.all().select_related(
            'id', 'id__user', 'id__department').filter(id=roll_no).first()
        sem_id = request.POST['semester_id']
        semester = Semester.objects.get(id=sem_id)
        cr = course_registration(
            course_id=course, student_id=student, semester_id=semester , working_year = datetime.datetime.now().year,)
        cr.save()

    return HttpResponseRedirect('/academic-procedures/')
   



def acad_branch_change(request):
    '''
        This function is used to approve the branch changes requested by the students.
        @param:
                request - trivial

        @variables:
                current_user - logged in user
                desig_id - Finds the Acad admin whose designation is "Upper Division Clerk".
                acadadmin - details of the logged in acad admin.
                user_details - details of the logged in user.
                change_queries - gets all the details of branch changes from the database.
                year - current year.
                month - current month
                date - current date.
                total_cse_seats - total availbale CSE seats.
                total_ece_seats - total availbale ECE seats.
                total_me_seats - total availbale ME seats.
                available_cse_seats - availbale CSE seats.
                available_ece_seats - available ECE seats.
                available_me_seats - available ME seats.
    '''
    current_user = get_object_or_404(User, username=request.user.username)
    user_details = ExtraInfo.objects.all().select_related('user','department').filter(user=current_user).first()
    desig_id = Designation.objects.all().filter(name='Upper Division Clerk')
    temp = HoldsDesignation.objects.all().select_related().filter(designation = desig_id).first()
    acadadmin = temp.working
    k = str(user_details).split()
    final_user = k[2]

    if ('acadadmin' != request.session.get('currentDesignationSelected')):
        return HttpResponseRedirect('/academic-procedures/')

    # year = datetime.datetime.now().year
    # month = datetime.datetime.now().month

    year = demo_date.year
    month = demo_date.month
    yearr = str(year) + "-" + str(year+1)
    semflag = 0
    queryflag = 0
    query_option1 = get_batch_query_detail(month, year)
    query_option2 = {"CSE": "CSE", "ECE": "ECE", "ME": "ME"}
    if(month >= 7):
        semflag = 1
    else:
        semflag = 2
    # TO DO Bdes
    date = {'year': yearr, 'month': month, 'semflag': semflag, 'queryflag': queryflag}


    change_queries = BranchChange.objects.select_related('branches','user','user__id','user__id__user','user__id__department').all()
    # Total seats taken as some random value
    total_cse_seats = 100
    total_ece_seats = 100
    total_me_seats = 100

    total_cse_filled_seats = 98
    total_ece_filled_seats = 98
    total_me_filled_seats = 98

    available_cse_seats = total_cse_seats - total_cse_filled_seats
    available_ece_seats = total_ece_seats - total_ece_filled_seats
    available_me_seats = total_me_seats - total_me_filled_seats

    initial_branch = []
    change_branch = []
    available_seats = []
    applied_by = []
    cpi = []

    for i in change_queries:
        applied_by.append(i.user.id)
        change_branch.append(i.branches.name)
        students = Student.objects.all().select_related('id','id__user','id__department').filter(id=i.user.id).first()
        user_branch = ExtraInfo.objects.all().select_related('user','department').filter(id=students.id.id).first()
        initial_branch.append(user_branch.department.name)
        cpi.append(students.cpi)
        if i.branches.name == 'CSE':
            available_seats.append(available_cse_seats)
        elif i.branches.name == 'ECE':
            available_seats.append(available_ece_seats)
        elif i.branches.name == 'ME':
            available_seats.append(available_me_seats)
        else:
            available_seats.append(0)
    lists = zip(applied_by, change_branch, initial_branch, available_seats, cpi)
    tag = False
    if len(initial_branch) > 0:
        tag = True
    context = {
        'list': lists,
        'total': len(initial_branch),
        'tag': tag
    }
    return render(
                request,
                '../templates/academic_procedures/academicadminforbranch.html',
                {
                    'context': context,
                    'lists': lists,
                    'date': date,
                    'query_option1': query_option1,
                    'query_option2': query_option2,
                    'result_year' : result_year
                }
            )


@login_required(login_url='/accounts/login')
def phd_details(request):
    '''
        This function is used to extract the details of the PHD details.
        @param:
                request - trivial

        @variables:
                current_user - logged in user
                student - details of the logged in student.
                thesis - gets the thesis details of the PhD student.
                faculty - gets the chosen faculty's details.
                user_details - details of the logged in user.
                total_thesis - total number of applied thesis.
    '''
    current_user = get_object_or_404(User, username=request.user.username)
    user_details = ExtraInfo.objects.all().select_related('user','department').filter(user=current_user).first()
    student = Student.objects.all().select_related('id','id__user','id__department').filter(id=user_details.id).first()
    thesis = Thesis.objects.all().filter(student_id=student).first()
    #Professor = Designation.objects.all().filter(name='Professor')
    #faculty = ExtraInfo.objects.all().filter(department=user_details.department,
    #                                         designation='Professor')
    f1 = HoldsDesignation.objects.select_related().filter(designation=Designation.objects.get(name = "Assistant Professor"))
    f2 = HoldsDesignation.objects.select_related().filter(designation=Designation.objects.get(name = "Professor"))
    f3 = HoldsDesignation.objects.select_related().filter(designation=Designation.objects.get(name = "Associate Professor"))

    faculty = list(chain(f1,f2,f3))
    faculties_list = []
    for i in faculty:
        faculties_list.append(str(i.user.first_name)+" "+str(i.user.last_name))
    total_thesis = True
    if(thesis is None):
        total_thesis = False

    context = {
            'total_thesis': total_thesis,
            'thesis': thesis,
            }
    return render(
            request,
            '../templates/academic_procedures/phdregistration.html',
            {'context': context, 'faculty': faculties_list, 'student': student}
            )





#
#
#
#
#
#
##

#
#
#
#
##
#
#
#
#
#
#

###

#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
def get_student_register(id):
    return Register.objects.all().select_related('curr_id','student_id','curr_id__course_id','student_id__id','student_id__id__user','student_id__id__department').filter(student_id = id)

def get_pre_registration_eligibility(current_date, user_sem, year):
    '''
        This function is used to extract the elgibility of pre-registration for a given semester
        for a given year from the Calendar table.
        
        @param:
                current_date - current date at the user end
                user_sem - current semester of the user(integer)
                year - current year at the user end

        @variables:
               pre_registration_date - stores the object returned from calendar table for a given description
               prd_start_date - holds start date of the pre registeration
               prd_end_date - holds end date of the pre registration
               
        #exception handling:
        In case calendar table has no row for the  given description pre_registration_date will store None value,
        Therefore from_date and to_date attributes cannot be accessed so the function will return False.
        
    '''
    try:
        # pre_registration_date = Calendar.objects.all().filter(description="Pre Registration").first()
        pre_registration_date = Calendar.objects.all().filter(description=f"Pre Registration {user_sem} {year}").first()
        prd_start_date = pre_registration_date.from_date
        prd_end_date = pre_registration_date.to_date
        if current_date>=prd_start_date and current_date<=prd_end_date:
            return True, None
        if current_date<prd_start_date:
            return False, prd_start_date
        else :
            return False, None
    except Exception as e:
        return False, None

def get_final_registration_eligibility(current_date):
    try:
        frd = Calendar.objects.all().filter(description="Physical Reporting at the Institute").first()
        frd_start_date = frd.from_date
        frd_end_date = frd.to_date
        if current_date>=frd_start_date and current_date<=frd_end_date:
            return True
        else :
            return False
    except Exception as e:
        return False

def get_add_or_drop_course_date_eligibility(current_date):
    try:
        add_drop_course_date = Calendar.objects.all().filter(description="Last Date for Adding/Dropping of course").first()
        adc_start_date = add_drop_course_date.from_date
        adc_end_date = add_drop_course_date.to_date
        if current_date>=adc_start_date and current_date<=adc_end_date:
            return True
        else :
            return False
    except Exception as e:
        return False

def get_course_verification_date_eligibilty(current_date):
    try:
        course_verification_date = Calendar.objects.all().filter(description="course verification date").first()
        verif_start_date = course_verification_date.from_date
        verif_end_date = course_verification_date.to_date
        if current_date>=verif_start_date and current_date<=verif_end_date:
            return True
        else :
            return False
    except Exception as e:
        return False

def get_user_branch(user_details):
    return user_details.department.name

def get_acad_year(user_sem, year):
        if user_sem%2 == 1:
            acad_year = str(year) + "-" + str(year+1)
        elif user_sem%2 == 0:
            acad_year = str(year-1) + "-" + str(year)
        return acad_year

@login_required(login_url='/accounts/login')
@transaction.atomic
def pre_registration(request):
    if request.method == 'POST':
        try:
            current_user = get_object_or_404(User, username=request.POST.get('user'))
            current_user = ExtraInfo.objects.all().select_related('user','department').filter(user=current_user).first()
            current_user = Student.objects.all().filter(id=current_user.id).first()
            sem_id = Semester.objects.get(id = request.POST.get('semester'))
            #print("sem id recerived from form is ",sem_id)

            course_slots=request.POST.getlist("course_slot")

            try:
                student_registeration_check=get_student_registrtion_check(current_user,sem_id)
                if(student_registeration_check.pre_registration_flag==True):
                    messages.error(request,"You have already registered for next semester")
                    return HttpResponseRedirect('/academic-procedures/main')
            except Exception as e:
                #print(e)
                pass

            reg_curr = []
            #print("---> printing request ",request.POST)

            for course_slot in course_slots :
                course_priorities = request.POST.getlist("course_priority-"+course_slot)
                if(course_priorities[0] == 'NULL'):
                    #print("NULL FOUND")
                    continue
                course_slot_id_for_model = CourseSlot.objects.get(id = int(course_slot))
                # print("=----> course_priorities ----- ",course_priorities)
                # print("------------>course slot id ",course_slot_id_for_model)
                for course_priority in course_priorities:
                    priority_of_current_course,course_id = map(int,course_priority.split("-"))

                    # get course id for the model
                    course_id_for_model = Courses.objects.get(id = course_id)
                    
                    p = InitialRegistration(
                        course_id = course_id_for_model,
                        semester_id = sem_id,
                        student_id = current_user,
                        course_slot_id = course_slot_id_for_model,
                        priority = priority_of_current_course
                    )
                    reg_curr.append(p)

            try:
                InitialRegistration.objects.bulk_create(reg_curr)
                registration_check = StudentRegistrationChecks(
                            student_id = current_user,
                            pre_registration_flag = True,
                            final_registration_flag = False,
                            semester_id = sem_id
                        )
                registration_check.save()
                messages.success(request, "Successfully Registered.")
                return HttpResponseRedirect('/academic-procedures/stu')
            except Exception as e:
                messages.error(request, "Error in Registration.")
                return HttpResponseRedirect('/academic-procedures/stu') 
        except Exception as e:
            messages.error(request, "Error in Registration.")
            return HttpResponseRedirect('/academic-procedures/main')
    else:
        return HttpResponseRedirect('/academic-procedures/main')

@login_required(login_url='/accounts/login')
@transaction.atomic
def auto_pre_registration(request):
    if request.method == 'POST':
        try:
            current_user = get_object_or_404(User, username=request.POST.get('user'))
            current_user = ExtraInfo.objects.all().select_related('user','department').filter(user=current_user).first()
            current_user = Student.objects.all().filter(id=current_user.id).first()
            sem_id = Semester.objects.get(id = request.POST.get('semester'))

            course_slots=request.POST.getlist("course_slot")             
            try:
                student_registeration_check=get_student_registrtion_check(current_user,sem_id)
                if(student_registeration_check and student_registeration_check.pre_registration_flag==True):
                    messages.error(request,"You have already registered for next semester")
                    return HttpResponseRedirect('/academic-procedures/main')
            except Exception as e:
                print(e)

            reg_curr = []
            final_reg_curr = []
            existing_entries = set()
            for course_slot in course_slots :
                course_priorities = request.POST.getlist("course_priority-"+course_slot)
                if(course_priorities[0] == 'NULL'):
                    continue
                course_slot_id_for_model = CourseSlot.objects.get(id = int(course_slot))
                print("=----> course_priorities ----- ",course_priorities)
                print("------------>course slot id ",course_slot_id_for_model)
                for course_priority in course_priorities:
                    if(course_priority == 'NULL'):
                        continue
                    priority_of_current_course,course_id = map(int,course_priority.split("-"))

                    course_id_for_model = Courses.objects.get(id = course_id)
                    current_combination = (course_slot_id_for_model.id, course_id_for_model.id)
                    if current_combination not in existing_entries:
                        p = InitialRegistration(
                            course_id = course_id_for_model,
                            semester_id = sem_id,
                            student_id = current_user,
                            course_slot_id = course_slot_id_for_model,
                            priority = priority_of_current_course
                        )
                        f =FinalRegistration(student_id=current_user ,course_slot_id=course_slot_id_for_model , course_id=course_id_for_model ,semester_id=sem_id)
                        final_reg_curr.append(f)
                        reg_curr.append(p)
                        existing_entries.add(current_combination)
            try:

                InitialRegistration.objects.bulk_create(reg_curr)
                FinalRegistration.objects.bulk_create(final_reg_curr)
                registration_check = StudentRegistrationChecks(
                            student_id = current_user,
                            pre_registration_flag = True,
                            final_registration_flag = False,
                            semester_id = sem_id
                        )
                registration_check.save()
                messages.info(request, 'Successfully Registered.')
                messages.success(request, "Successfully Registered.")
                return HttpResponseRedirect('/academic-procedures/stu')
            except Exception as e:
                messages.error(request, "Error in Registration.")
                return HttpResponseRedirect('/academic-procedures/stu') 
        except Exception as e:
            messages.error(request, "Error in Registration.")
            return HttpResponseRedirect('/academic-procedures/main')
    else:
        return HttpResponseRedirect('/academic-procedures/main')
    
def get_student_registrtion_check(obj, sem):
    return StudentRegistrationChecks.objects.all().filter(student_id = obj, semester_id = sem).first()


def final_registration(request):
    if request.method == 'POST':
        if request.POST.get('type_reg') == "register" :
            try:
                current_user = get_object_or_404(User, username=request.POST.get('user'))
                current_user = ExtraInfo.objects.all().select_related('user','department').filter(user=current_user).first()
                current_user = Student.objects.all().filter(id=current_user.id).first()

                sem_id = Semester.objects.get(id = request.POST.get('semester'))

                mode = str(request.POST.get('mode'))
                transaction_id = str(request.POST.get('transaction_id'))
                deposit_date = request.POST.get('deposit_date')
                utr_number = str(request.POST.get('utr_number'))
                fee_paid = request.POST.get('fee_paid')
                actual_fee = request.POST.get('actual_fee')
                reason = str(request.POST.get('reason'))
                if reason=="":
                    reason=None
                fee_receipt = request.FILES['fee_receipt']

                obj = FeePayments(
                    student_id = current_user,
                    semester_id = sem_id,
                    mode = mode,
                    transaction_id = transaction_id,
                    fee_receipt = fee_receipt,
                    deposit_date = deposit_date,
                    utr_number = utr_number,
                    fee_paid = fee_paid,
                    actual_fee = actual_fee,
                    reason = reason
                    )
                obj.save()
                try:
                    StudentRegistrationChecks.objects.filter(student_id = current_user, semester_id = sem_id).update(final_registration_flag = True)
                    messages.info(request, 'Final-Registration Successful')
                except Exception as e:
                    return HttpResponseRedirect('/academic-procedures/main')
                return HttpResponseRedirect('/academic-procedures/main')
            except Exception as e:
                return HttpResponseRedirect('/academic-procedures/main')
    else:
        return HttpResponseRedirect('/academic-procedures/main')

def allot_courses(request):
    if user_check(request):
        return HttpResponseRedirect('/academic-procedures/main')


    try:
        if request.method == 'POST' and request.FILES:
            profiles=request.FILES['allotedCourses']
            batch_id=request.POST['batch']
            sem_no=int(request.POST['semester'])
            
            batch=Batch.objects.get(id=batch_id)
            sem_id=Semester.objects.get(curriculum=batch.curriculum,semester_no=sem_no)
            print(batch , sem_id)
            #  format of excel sheet being uploaded should be xls only , otherwise error
            excel = xlrd.open_workbook(file_contents=profiles.read())
            sheet=excel.sheet_by_index(0)
            course_registrations=[]
            final_registrations=[]
            pre_registrations=[]
            student_checks=[]
            # print('>>>>>>>>>>>>>>>>>>>' , sheet.nrows)
            currroll=set()
            for i in range(1,sheet.nrows):
                roll_no = str(sheet.cell(i,0).value).split(".")[0]
                # print("Roll No from Excel:", roll_no)
                course_slot_name = sheet.cell_value(i,1)
                course_code = sheet.cell_value(i,2)
                course_name = sheet.cell_value(i,3)
                try:

                    user=User.objects.get(username=roll_no)
                    user_info = ExtraInfo.objects.get(user=user)
                    student = Student.objects.get(id=user_info)
                    course_slot=CourseSlot.objects.get(name=course_slot_name.strip(),semester=sem_id)
                    print(course_code.strip() , course_name.strip())
                    course = Courses.objects.get(code=course_code.strip(),name=course_name.strip())
                    if(roll_no not in currroll):
                        student_check=StudentRegistrationChecks(student_id = student, semester_id = sem_id, pre_registration_flag = True,final_registration_flag = False)
                        student_checks.append(student_check)
                        currroll.add(roll_no)
                    # print(">>>>>",roll_no,course_slot_name,course_code,course_name)
                except Exception as e:
                    print('----------------------' , e)
                pre_registration=InitialRegistration(student_id=student,course_slot_id=course_slot,
                                                    course_id=course,semester_id=sem_id,priority=1)
                pre_registrations.append(pre_registration)
                final_registration=FinalRegistration(student_id=student,course_slot_id=course_slot,
                                                    course_id=course,semester_id=sem_id)
                final_registrations.append(final_registration)
    
                courseregistration=course_registration(working_year=datetime.datetime.now().year,course_id=course,semester_id=sem_id,student_id=student,course_slot_id=course_slot)
                course_registrations.append(courseregistration)
                


            try:
                InitialRegistration.objects.bulk_create(pre_registrations)
                StudentRegistrationChecks.objects.bulk_create(student_checks)
                FinalRegistration.objects.bulk_create(final_registrations)
                course_registration.objects.bulk_create(course_registrations)
                messages.success(request, 'Successfully uploaded!')
                return HttpResponseRedirect('/academic-procedures/main')
                # return HttpResponse("Success")
            except Exception as e:
                messages.error(request, 'Error: '+str(e))
                return HttpResponseRedirect('/academic-procedures/main')
                # return HttpResponse("Success")
    except Exception as e:
        messages.error(request, 'Error: Query does not match. Please check if all the data input is in the correct format.')
        return HttpResponseRedirect('/academic-procedures/main')
        # return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        # return HttpResponse("Fail")





@login_required
def user_check(request):
    """
    This function is used to check the type of user.
    It checkes the authentication of the user.

    @param:
        request - contains metadata about the requested page

    @variables:
        current_user - get user from request 
        user_details - extract details of user from database
        desig_id - check for designation
        acadadmin - designation for Acadadmin
        final_user - final designation of request user

    """
    try:
        current_user = get_object_or_404(User, username=request.user.username)
        user_details = ExtraInfo.objects.all().select_related('user','department').filter(user=current_user).first()
        desig_id = Designation.objects.all().filter(name='acadadmin')
        temp = HoldsDesignation.objects.all().select_related().filter(designation = desig_id).first()
        acadadmin = temp.working
        k = str(user_details).split()
        final_user = k[2]
    except Exception as e:
        acadadmin=""
        final_user=""
        pass

    if ('acadadmin' != request.session.get('currentDesignationSelected')):
        return True
    else:
        return False

def get_cpi(id):
    obj =  Student.objects.select_related('id','id__user','id__department').get(id = id)
    return obj.cpi

def register(request):
    if request.method == 'POST':
        try:
            current_user = get_object_or_404(User, username=request.POST.get('user'))
            current_user = ExtraInfo.objects.all().select_related('user','department').filter(user=current_user).first()
            current_user = Student.objects.all().select_related('id','id__user','id__department').filter(id=current_user.id).first()

            values_length = 0
            values_length = len(request.POST.getlist('choice'))

            sem = request.POST.get('semester')

            for x in range(values_length):
                reg_curr=[]
                for key, values in request.POST.lists():
                    if (key == 'choice'):
                        try:
                            last_id = Register.objects.all().aggregate(Max('r_id'))
                            last_id = last_id['r_id__max']+1
                        except Exception as e:
                            last_id = 1
                        curr_id = get_object_or_404(Curriculum, curriculum_id=values[x])
                        p = Register(
                            r_id=last_id,
                            curr_id=curr_id,
                            year=current_user.batch,
                            student_id=current_user,
                            semester=sem
                            )
                        reg_curr.append(p)
                    else:
                        continue
                Register.objects.bulk_create(reg_curr)
            messages.info(request, 'Pre-Registration Successful')
            return HttpResponseRedirect('/academic-procedures/main')
        except Exception as e:
            return HttpResponseRedirect('/academic-procedures/main')
    else:
        return HttpResponseRedirect('/academic-procedures/main')


def add_courses(request):
    """
    This function is used to add courses for currernt semester
    @param:
        request - contains metadata about the requested page
    @variables:
        current_user - contains current logged in user
        sem_id - contains current semester id
        count - no of courses to be added
        course_id - contains course id for a particular course
        course_slot_id - contains course slot id for a particular course
        reg_curr - list of registered courses object
        choice - contains choice of a particular course
        slot - contains slot of a particular course
        # gg and cs
    """
    if request.method == 'POST':
        try:
            current_user = get_object_or_404(User, username=request.POST.get('user'))
            current_user = ExtraInfo.objects.all().filter(user=current_user).first()
            current_user = Student.objects.all().filter(id=current_user.id).first()

            sem_id = Semester.objects.get(id = request.POST.get('semester'))
            count = request.POST.get('ct')
            count = int(count)
            reg_curr=[]
            for i in range(1, count+1):
                choice = "choice["+str(i)+"]"
                slot = "slot["+str(i)+"]"
                try:
                    course_id = Courses.objects.get(id = request.POST.get(choice))
                    courseslot_id = CourseSlot.objects.get(id = request.POST.get(slot))
                    # Check if maximum course registration limit has not reached and student has not already registered for that course
                    if course_registration.objects.filter(student_id__batch_id__year = current_user.batch_id.year, course_id = course_id).count() < courseslot_id.max_registration_limit and (course_registration.objects.filter(course_id=course_id, student_id=current_user).count() == 0):
                        p = course_registration(
                            course_id = course_id,
                            student_id=current_user,
                            course_slot_id = courseslot_id,
                            semester_id=sem_id,
                            working_year = datetime.datetime.now().year,
                            )
                        if p not in reg_curr:
                            reg_curr.append(p)
                except Exception as e:
                    continue
            course_registration.objects.bulk_create(reg_curr)
            return HttpResponseRedirect('/academic-procedures/main')
        except Exception as e:
            return HttpResponseRedirect('/academic-procedures/main')
    else:
        return HttpResponseRedirect('/academic-procedures/main')


def drop_course(request):
    if request.method == 'POST':
        try:
            current_user = get_object_or_404(User, username=request.POST.get('user'))
            current_user = ExtraInfo.objects.all().select_related('user','department').filter(user=current_user).first()
            current_user = Student.objects.all().get(id=current_user.id)

            values_length = 0
            values_length = len(request.POST.getlist('choice'))

            sem_id = request.POST.get('semester')
            sem = Semester.objects.get(id = sem_id)
            for x in range(values_length):
                for key, values in request.POST.lists():
                    if (key == 'choice'):
                        course_id = get_object_or_404(Courses, id=values[x])
                        course_registration.objects.filter(course_id = course_id, student_id = current_user).delete()
                    else:
                        continue
            messages.info(request, 'Course Successfully Dropped')
            return HttpResponseRedirect('/academic-procedures/main')
        except Exception as e:
            return HttpResponseRedirect('/academic-procedures/main')
    else:
        return HttpResponseRedirect('/academic-procedures/main')

def replace_courses(request):
    """
    This function is used to replace elective courses which have been registered
    @param:
        request - contains metadata about the requested page
    @variables:
        current_user - contains current logged in user
        sem_id - contains current semester id
        count - no of courses to be replaced
        course_id - contains course id for a particular course
        course_slot_id - contains course slot id for a particular course
        choice - contains choice of a particular course
        slot - contains slot of a particular course
    """

    if request.method == 'POST' :       
        try:
            current_user = get_object_or_404(User, username=request.POST.get('user'))
            current_user = ExtraInfo.objects.all().filter(user=current_user).first()
            current_user = Student.objects.all().filter(id=current_user.id).first()

            # sem_id = Semester.objects.get(id = request.POST.get('semester'))
            count = request.POST.get('ct')
            count = int(count)

            for i in range(1, count+1):
                choice = "choice["+str(i)+"]"
                slot = "slot["+str(i)+"]"
                try :

                    course_id = Courses.objects.get(id = request.POST.get(choice))
                    courseslot_id = CourseSlot.objects.get(id = request.POST.get(slot))

                    registered_course = course_registration.objects.filter(student_id=current_user, course_slot_id = courseslot_id).first()

                    if registered_course:
                        registered_course.course_id = course_id 
                        registered_course.save()
                except Exception as e:
                    continue
            return HttpResponseRedirect('/academic-procedures/main')
        except Exception as e:
            return HttpResponseRedirect('/academic-procedures/main')
    else :
        return HttpResponseRedirect('/academic-procedures/main')




def add_thesis(request):
    if request.method == 'POST':
        try:
            if(str(request.POST.get('by'))=="st"):
                thesis_topic = request.POST.get('thesis_topic')
                research_area = request.POST.get('research_area')

                supervisor_faculty = get_object_or_404(User, username = request.POST.get('supervisor'))
                supervisor_faculty = ExtraInfo.objects.select_related('user','department').get(user = supervisor_faculty)
                supervisor_faculty = Faculty.objects.select_related('id','id__user','id__department').get(id = supervisor_faculty)

                try:
                    co_supervisor_faculty = get_object_or_404(User, username = request.POST.get('co_supervisor'))
                    co_supervisor_faculty = ExtraInfo.objects.select_related('user','department').get(user = co_supervisor_faculty)
                    co_supervisor_faculty = Faculty.objects.select_related('id','id__user','id__department').get(id = co_supervisor_faculty) 
                except Exception as e:
                    co_supervisor_faculty = None

                current_user = get_object_or_404(User, username=request.POST.get('user'))
                current_user = ExtraInfo.objects.all().select_related('user','department').filter(user=current_user).first()
                current_user = Student.objects.all().select_related('id','id__user','id__department').filter(id=current_user.id).first()

                try:
                    curr_id = request.POST.get('curr_id')
                    curr_id = Curriculum.objects.select_related().get(curriculum_id = curr_id)
                except Exception as e:
                    curr_id = None


                p = ThesisTopicProcess(
                    student_id = current_user,
                    research_area = research_area,
                    thesis_topic = thesis_topic,
                    curr_id = curr_id,
                    supervisor_id = supervisor_faculty,
                    co_supervisor_id = co_supervisor_faculty,
                    submission_by_student = True,
                    pending_supervisor = True,
                    )
                p.save()
                messages.info(request, 'Thesis Successfully Added')
                return HttpResponseRedirect('/academic-procedures/main/')

            elif(str(request.POST.get('by'))=="fac"):
                obj = request.POST.get('obj_id')
                obj = ThesisTopicProcess.objects.get(id = obj)

                member1 = get_object_or_404(User, username = request.POST.get('member1'))
                member1 = ExtraInfo.objects.select_related('user','department').get(user = member1)
                member1 = Faculty.objects.select_related('id','id__user','id__department').get(id = member1)

                member2 = get_object_or_404(User, username = request.POST.get('member2'))
                member2 = ExtraInfo.objects.select_related('user','department').get(user = member2)
                member2 = Faculty.objects.select_related('id','id__user','id__department').get(id = member2)

                try:
                    member3 = get_object_or_404(User, username = request.POST.get('member3'))
                    member3 = ExtraInfo.objects.select_related('user','department').get(user = member3)
                    member3 = Faculty.objects.select_related('id','id__user','id__department').get(id = member3)
                except Exception as e:
                    member3 = None
                if(str(request.POST.get('approval'))=="yes"):
                    obj.pending_supervisor = False
                    obj.member1 = member1
                    obj.member2 = member2
                    obj.member3 = member3
                    obj.approval_supervisor = True
                    obj.forwarded_to_hod = True
                    obj.pending_hod = True
                    obj.save()
                elif(request.POST.get('approval')=="no"):
                    obj.pending_supervisor = False
                    obj.member1 = member1
                    obj.member2 = member2
                    obj.member3 = member3
                    obj.approval_supervisor = False
                    obj.forwarded_to_hod = False
                    obj.pending_hod = False
                    obj.save()
                else:
                    logging.warning("Not approved till now")
                return HttpResponseRedirect('/academic-procedures/main')
        except Exception as e:
            return HttpResponseRedirect('/academic-procedures/main')
    else:
        return HttpResponseRedirect('/academic-procedures/main/')
    return HttpResponseRedirect('/academic-procedures/main/')


def get_final_registration_choices(branch_courses,batch):
    course_option = []
    unavailable_courses = []
    for courseslot in branch_courses:
        max_limit = courseslot.max_registration_limit
        lis = []
        for course in courseslot.courses.all():
            if FinalRegistration.objects.filter(student_id__batch_id__year = batch, course_id = course).count() < max_limit:
                lis.append(course)
            else:
                unavailable_courses.append(course)
        course_option.append((courseslot, lis))
    return course_option, unavailable_courses

def get_add_course_options(branch_courses, current_register, batch):

    course_option = []
    courses = current_register
    slots = []
    for c in current_register:
        slots.append(c[0])
    for courseslot in branch_courses:
        if courseslot.type == "Swayam":
            continue
        max_limit = courseslot.max_registration_limit
        if courseslot not in slots:
            lis = []
            for course in courseslot.courses.all():
                print(course)
                if course_registration.objects.filter(student_id__batch_id__year = batch, course_id = course).count() < max_limit:
                    lis.append(course)
            course_option.append((courseslot, lis))
    return course_option

def get_drop_course_options(current_register):
    courses = []
    for item in current_register:
        if item[0].type != "Professional Core":
            courses.append(item[1])
    return courses

def get_replace_course_options( current_register, batch):
    replace_options = []

    for registered_course in current_register:
        courseslot_id = registered_course[0]
        course_id = registered_course[1]

        courseslot = courseslot_id
        coursename = course_id.name
        lis = []

        if 'Elective' in courseslot.type:
            for course in courseslot.courses.all():
                if course != course_id:
                    lis.append(course)
            replace_options.append((courseslot, coursename, lis))

    return replace_options



def get_user_semester(roll_no, ug_flag, masters_flag, phd_flag):
    roll = str(roll_no)
    now = demo_date
    year, month = now.year, int(now.month)
    y = str(year)
    if(ug_flag):
        if(roll[2].isdigit()):
            roll = int(roll[:4])
        else:
            roll = int("20"+roll[:2])        
        user_year = year - roll
    elif(masters_flag or phd_flag):
        roll =  int(roll[:2])
        user_year = int(y[-2:]) - roll
    sem = 'odd'
    if month >= 7 and month<=12:
        sem = 'odd'
    else:
        sem = 'even'
    if sem == 'odd':
        return user_year * 2 + 1
    else:
        return user_year * 2



def get_branch_courses(roll_no, user_sem, branch):
    roll = str(roll_no)
    try:
        year = int(roll[:4])
    except:
        year = int(roll[:2])
        year = 2000 + year
    courses = Curriculum.objects.all().select_related().filter(batch=(year))
    courses = courses.filter(sem = user_sem)
    courses = courses.filter(floated = True)
    course_list = []
    for course in courses:
        if branch.lower() == course.branch.lower() :
            course_list.append(course)
        elif course.branch.lower() == 'common':
            course_list.append(course)
    return course_list


def get_sem_courses(sem_id, batch):
    courses = []
    course_slots = CourseSlot.objects.all().filter(semester_id = sem_id)
    for slot in course_slots:
        courses.append(slot)
    return courses


def get_currently_registered_courses(id, user_sem):
    obj = Register.objects.all().select_related('curr_id','student_id','curr_id__course_id','student_id__id','student_id__id__user','student_id__id__department').filter(student_id=id, semester=user_sem)
    ans = []
    for i in obj:
        course = Curriculum.objects.select_related().get(curriculum_id=i.curr_id.curriculum_id)
        ans.append(course)
    return ans

def get_currently_registered_course(id, sem_id):
    #  obj = course_registration.objects.all().filter(student_id = id, semester_id=sem_id)
    obj = course_registration.objects.all().filter(student_id = id)
    courses = []
    for i in obj:
        courses.append((i.course_slot_id,i.course_id))
    return courses


def get_current_credits(obj):
    credits = 0
    for i in obj:
        credits = credits + i[1].credit
    return credits



def get_faculty_list():
    f1 = HoldsDesignation.objects.select_related().filter(designation=Designation.objects.get(name = "Assistant Professor"))
    f2 = HoldsDesignation.objects.select_related().filter(designation=Designation.objects.get(name = "Professor"))
    f3 = HoldsDesignation.objects.select_related().filter(designation=Designation.objects.get(name = "Associate Professor"))

    faculty = list(chain(f1,f2,f3))
    faculty_list = []
    for i in faculty:
        faculty_list.append(i)
    return faculty_list


def get_thesis_flag(student):
    obj = ThesisTopicProcess.objects.all().select_related().filter(student_id = student)
    if(obj):
        return True
    else:
        return False



@login_required(login_url='/accounts/login')
def acad_person(request):

    current_user = get_object_or_404(User, username=request.user.username)

    user_details = ExtraInfo.objects.select_related('user','department').get(user = request.user)
    des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()


    if request.session.get('currentDesignationSelected') == "student":
       return HttpResponseRedirect('/academic-procedures/main/')

    elif request.session.get('currentDesignationSelected') == "Associate Professor" :
        return HttpResponseRedirect('/academic-procedures/main/')

    elif request.session.get('currentDesignationSelected')== "acadadmin" :


        # year = datetime.datetime.now().year
        # month = datetime.datetime.now().month

        year = demo_date.year
        month = demo_date.month
        yearr = str(year) + "-" + str(year+1)
        semflag = 0
        queryflag = 0
        query_option1 = get_batch_query_detail(month, year)
        query_option2 = {"CSE": "CSE", "ECE": "ECE", "ME": "ME"}
        if(month >= 7):
            semflag = 1
        else:
            semflag = 2
        date = {'year': yearr, 'month': month, 'semflag': semflag, 'queryflag': queryflag}
        result_year = []
        result_year = get_batch_all()
            # result_year = [1,2]
        change_queries = BranchChange.objects.select_related('branches','user','user__id','user__id__user','user__id__department').all()

        course_verification_date = get_course_verification_date_eligibilty(demo_date.date())


        initial_branch = []
        change_branch = []
        available_seats = []
        applied_by = []
        cpi = []

        for i in change_queries:
            applied_by.append(i.user.id)
            change_branch.append(i.branches.name)
            students = Student.objects.all().select_related('id','id__user','id__department').filter(id=i.user.id).first()
            user_branch = ExtraInfo.objects.all().select_related('user','department').filter(id=students.id.id).first()
            initial_branch.append(user_branch.department.name)
            cpi.append(students.cpi)
            if i.branches.name == 'CSE':
                available_seats.append(available_cse_seats)
            elif i.branches.name == 'ECE':
                available_seats.append(available_ece_seats)
            elif i.branches.name == 'ME':
                available_seats.append(available_me_seats)
        lists = zip(applied_by, change_branch, initial_branch, available_seats, cpi)
        tag = False
        if len(initial_branch) > 0:
            tag = True
        context = {
            'list': lists,
            'total': len(initial_branch),
            'tag': tag
        }

        submitted_course_list = []
        obj_list = MarkSubmissionCheck.objects.all().select_related().filter(verified= False,submitted = True)
        for i in obj_list:
            if int(i.curr_id.batch)+int(i.curr_id.sem)/2 == int(demo_date.year):
                submitted_course_list.append(i.curr_id)
            else:
                continue
        # submitted_course_list = SemesterMarks.objects.all().filter(curr_id__in = submitted_course_list)



        batch_grade_data = get_batch_grade_verification_data(result_year)

        return HttpResponseRedirect('/aims/')
    else:
        return HttpResponse('user not found')


def acad_proced_global_context():
    year = demo_date.year
    month = demo_date.month
    yearr = str(year) + "-" + str(year+1)
    semflag = 0
    queryflag = 0
    query_option1 = get_batch_query_detail(month, year)
    query_option2 = {"CSE": "CSE", "ECE": "ECE", "ME": "ME"}
    if(month >= 7):
        semflag = 1
    else:
        semflag = 2
    date = {'year': yearr, 'month': month, 'semflag': semflag, 'queryflag': queryflag}
    result_year = []
    result_year = get_batch_all()
        # result_year = [1,2]
    change_queries = BranchChange.objects.select_related('branches','user','user__id','user__id__user','user__id__department').all()

    course_verification_date = get_course_verification_date_eligibilty(demo_date.date())


    initial_branch = []
    change_branch = []
    available_seats = []
    applied_by = []
    cpi = []

    for i in change_queries:
        applied_by.append(i.user.id)
        change_branch.append(i.branches.name)
        students = Student.objects.all().select_related('id','id__user','id__department').filter(id=i.user.id).first()
        user_branch = ExtraInfo.objects.all().select_related('user','department').filter(id=students.id.id).first()
        initial_branch.append(user_branch.department.name)
        cpi.append(students.cpi)
        if i.branches.name == 'CSE':
            available_seats.append(available_cse_seats)
        elif i.branches.name == 'ECE':
            available_seats.append(available_ece_seats)
        elif i.branches.name == 'ME':
            available_seats.append(available_me_seats)
    lists = zip(applied_by, change_branch, initial_branch, available_seats, cpi)
    tag = False
    if len(initial_branch) > 0:
        tag = True
    context = {
        'list': lists,
        'total': len(initial_branch),
        'tag': tag
    }

    submitted_course_list = []
    obj_list = MarkSubmissionCheck.objects.all().select_related().filter(verified= False,submitted = True)
    for i in obj_list:
        if int(i.curr_id.batch)+int(i.curr_id.sem)/2 == int(demo_date.year):
            submitted_course_list.append(i.curr_id)
        else:
            submitted_course_list.append(i.curr_id)
            #continue
    # submitted_course_list = SemesterMarks.objects.all().filter(curr_id__in = submitted_course_list)

    batch_grade_data = get_batch_grade_verification_data(result_year)

    batch_branch_data = get_batch_branch_data(result_year)

    return {
            'context': context,
            'lists': lists,
            'date': date,
            'query_option1': query_option1,
            'query_option2': query_option2,
            'course_verification_date' : course_verification_date,
            'submitted_course_list' : submitted_course_list,
            'result_year' : result_year,
            'batch_grade_data' : batch_grade_data,
            'batch_branch_data': batch_branch_data
        }



def get_batch_all():
    result_year = []
    if demo_date.month >=7:
        result_year = [demo_date.year, demo_date.year-1, demo_date.year-2, demo_date.year-3]
            # result_year = [1,2]
    else :
        result_year = [demo_date.year-1,demo_date.year-2,  demo_date.year-3,  demo_date.year-4]
    return result_year

def announce_results(request):
    i = int(request.POST.get('id'))
    year = get_batch_all()

    acad = get_object_or_404(User, username="acadadmin")
    student_list = Student.objects.all().select_related('id','id__user','id__department').filter(batch = year[i-1])

    # for obj in student_list:
    #     academics_module_notif(acad, obj.id.user, 'result_announced')


    courses_list = Curriculum.objects.all().select_related().filter(batch = year[i-1])
    rsl = []
    for obj in courses_list:
        try :
            o = MarkSubmissionCheck.objects.select_related().get(curr_id = obj)
            o.announced = True
            rsl.append(o)
        except Exception as e:
            continue
    MarkSubmissionCheck.objects.bulk_update(rsl,['announced'])

    return JsonResponse({'status': 'success', 'message': 'Successfully Accepted'})



def get_batch_grade_verification_data(list):

    semester_marks = []

    batch_1_list_CSE = []
    batch_2_list_CSE = []
    batch_3_list_CSE = []
    batch_4_list_CSE = []

    batch_1_list_ECE = []
    batch_2_list_ECE = []
    batch_3_list_ECE = []
    batch_4_list_ECE = []

    batch_1_list_ME = []
    batch_2_list_ME = []
    batch_3_list_ME = []
    batch_4_list_ME = []

    c = Curriculum.objects.all().select_related().filter(batch = list[0]).filter(floated = True)
    c_cse = c.filter(branch = 'CSE')
    c_me = c.filter(branch = 'ME')
    c_ece = c.filter(branch = 'ECE')
    for i in c_cse:
        batch_1_list_CSE.append(i)
    for i in c_me:
        batch_1_list_ME.append(i)
    for i in c_ece:
        batch_1_list_ECE.append(i)
    for i in c:
        try:
            obj_sem = MarkSubmissionCheck.objects.select_related().get(curr_id = i)
            if obj_sem:
                semester_marks.append(obj_sem)
            else:
                continue
        except Exception as e:
            continue

    c = Curriculum.objects.all().select_related().filter(batch = list[1]).filter(floated = True)
    c_cse = c.filter(branch = 'CSE')
    c_me = c.filter(branch = 'ME')
    c_ece = c.filter(branch = 'ECE')
    for i in c_cse:
        batch_2_list_CSE.append(i)
    for i in c_me:
        batch_2_list_ME.append(i)
    for i in c_ece:
        batch_2_list_ECE.append(i)
    for i in c:
        try:
            obj_sem = MarkSubmissionCheck.objects.select_related().get(curr_id = i)
            if obj_sem:
                semester_marks.append(obj_sem)
            else:
                continue
        except Exception as e:
            continue

    c = Curriculum.objects.all().select_related().filter(batch = list[2]).filter(floated = True)
    c_cse = c.filter(branch = 'CSE')
    c_me = c.filter(branch = 'ME')
    c_ece = c.filter(branch = 'ECE')
    for i in c_cse:
        batch_3_list_CSE.append(i)
    for i in c_me:
        batch_3_list_ME.append(i)
    for i in c_ece:
        batch_3_list_ECE.append(i)
    for i in c:
        try:
            obj_sem = MarkSubmissionCheck.objects.select_related().get(curr_id = i)
            if obj_sem:
                semester_marks.append(obj_sem)
            else:
                continue
        except Exception as e:
            continue

    c = Curriculum.objects.all().select_related().filter(batch = list[3]).filter(floated = True)
    c_cse = c.filter(branch = 'CSE')
    c_me = c.filter(branch = 'ME')
    c_ece = c.filter(branch = 'ECE')
    for i in c_cse:
        batch_4_list_CSE.append(i)
    for i in c_me:
        batch_4_list_ME.append(i)
    for i in c_ece:
        batch_4_list_ECE.append(i)
    for i in c:
        try:
            obj_sem = MarkSubmissionCheck.objects.select_related().get(curr_id = i)
            if obj_sem:
                semester_marks.append(obj_sem)
            else:
                continue
        except Exception as e:
            continue


    batch_1_list = {
        'batch_list_year' : list[0],
        'batch_list_ME' :  batch_1_list_ME,
        'batch_list_ECE' : batch_1_list_ECE,
        'batch_list_CSE' : batch_1_list_CSE
    }

    batch_2_list = {
        'batch_list_year' : list[1],
        'batch_list_ME' :  batch_2_list_ME,
        'batch_list_ECE' : batch_2_list_ECE,
        'batch_list_CSE' : batch_2_list_CSE
    }

    batch_3_list = {
        'batch_list_year' : list[2],
        'batch_list_ME' :  batch_3_list_ME,
        'batch_list_ECE' : batch_3_list_ECE,
        'batch_list_CSE' : batch_3_list_CSE
    }

    batch_4_list = {
        'batch_list_year' : list[3],
        'batch_list_ME' :  batch_4_list_ME,
        'batch_list_ECE' : batch_4_list_ECE,
        'batch_list_CSE' : batch_4_list_CSE
    }


    batch_grade_data_set = {'batch_grade_data' : [batch_1_list, batch_2_list, batch_3_list, batch_4_list],
                            'batch_sub_check' : semester_marks}
    return batch_grade_data_set


def get_batch_branch_data(result_year):

    batches = []
    for batch in Batch.objects.all(): 
        if batch.year in result_year:
            batches.append(batch)
    
    return batches


@login_required(login_url='/accounts/login')
def student_list(request):
    if(request.POST and (request.GET["excel_export"] == "false")):
        batch = request.POST["batch"]

        year = demo_date.year
        month = demo_date.month
        yearr = str(year) + "-" + str(year+1)
        semflag = 0
        queryflag = 1
        if(month >= 7):
            semflag = 1
        else:
            semflag = 2
        batch_year_option = get_batch_query_detail(month, year)
        branch_option = {"CSE": "CSE", "ECE": "ECE", "ME": "ME"}
        date = {'year': yearr, 'month': month, 'semflag': semflag, 'queryflag': queryflag}


        batch_id = Batch.objects.get(id = batch)
        student_obj = FeePayments.objects.all().select_related('student_id').filter(student_id__batch_id = batch_id)
        if (student_obj):
            reg_table = student_obj.prefetch_related('student_id__studentregistrationchecks').filter(semester_id = student_obj[0].semester_id, student_id__studentregistrationchecks__final_registration_flag = True , student_id__finalregistration__verified=False , student_id__finalregistration__semester_id= student_obj[0].semester_id ).select_related(
                'student_id','student_id__id','student_id__id__user','student_id__id__department').values(
                    'student_id__id','student_id__id__user__first_name','student_id__id__user__last_name','student_id__batch','student_id__id__department__name',
                    'student_id__programme','student_id__curr_semester_no','student_id__id__sex','student_id__id__phone_no','student_id__category',
                    'student_id__specialization','mode','transaction_id','deposit_date','fee_paid','utr_number','reason','fee_receipt','actual_fee',
                    'student_id__id__user__username').order_by('student_id__id__user').distinct()
            # print('------------------------------------------------------------------------------------------------------------------------------------------',reg_table)
        else :
            reg_table = []

        html = render_to_string('academic_procedures/student_table.html',{'student': reg_table}, request)

        maindict = {'date': date,
                    'query_option1': batch_year_option,
                    'query_option2': branch_option,
                    'html': html,
                    'queryflag': queryflag}
        obj = json.dumps(maindict)
        return HttpResponse(obj, content_type='application/json')

    elif(request.POST) and (request.GET["excel_export"] == "true"):
        batch = request.POST["batch"]
        year = demo_date.year
        month = demo_date.month
        yearr = str(year) + "-" + str(year+1)
        semflag = 0
        queryflag = 1
        if(month >= 7):
            semflag = 1
        else:
            semflag = 2
        batch_year_option = get_batch_query_detail(month, year)
        branch_option = {"CSE": "CSE", "ECE": "ECE", "ME": "ME"}
        date = {'year': yearr, 'month': month, 'semflag': semflag, 'queryflag': queryflag}


        batch_id = Batch.objects.get(id = batch)
        student_obj = FeePayments.objects.all().select_related('student_id').filter(student_id__batch_id = batch_id)

        table=[("Admission Year","Semester","Roll Number","Full Name","Program","Discipline",
            "Specialization","Gender","Category","PWD Status","Mobile Number","Actual Fee","Fee Paid By Student",
            "Reason for Less or more feeReason for Less or more fee (Adjustement/MCM/MMVY/SC/ST Scholarship/Other Scholarship)",
            "Date for Fee deposition","Mode","If Loan account enter UTR Number","Upload Fee Receipt path")]
        
        if (student_obj):

            table += (student_obj.prefetch_related('student_id__studentregistrationchecks').filter(semester_id = student_obj[0].semester_id, student_id__studentregistrationchecks__final_registration_flag = True).select_related(
                'student_id','student_id__id','student_id__id__user','student_id__id__department').annotate(
                    admission_year = F('student_id__batch'),
                    semester = Sum('student_id__curr_semester_no') + 1,
                    roll_no = F('student_id__id__user__username'),
                    full_name = Concat('student_id__id__user__first_name',Value(' '),'student_id__id__user__last_name'),
                    program = F('student_id__programme'),
                    discipline = F('student_id__id__department__name'),
                    specialization = F('student_id__specialization'),
                    gender = F('student_id__id__sex'),
                    category = F('student_id__category'),
                    pwd_status = Value("YES", output_field = CharField()) if F('student_id__pwd_status') == True else Value("NO", output_field = CharField()),
                    phone_no = F('student_id__id__phone_no'),
                    date_deposited = Concat(Cast(ExtractDay('deposit_date'), CharField()), Value('/'), Cast(ExtractMonth('deposit_date'), CharField()), Value('/'), Cast(ExtractYear('deposit_date'), CharField()), output_field = CharField()),
                ).order_by('student_id__id__user__username').values_list(
                    'admission_year','semester','roll_no',
                    'full_name','program','discipline',
                    'specialization','gender','category',
                    'pwd_status','phone_no','actual_fee',
                    'fee_paid','reason','date_deposited',
                    'mode','utr_number','fee_receipt')).distinct()

            excel_response = BytesIO()

            final_register_workbook = Workbook(excel_response)
            final_register_worksheet = final_register_workbook.add_worksheet()
                
            for i in range(len(table)):
                for j in range(len(table[i])):
                    final_register_worksheet.write(i,j,table[i][j])

            final_register_workbook.close()
            excel_response.seek(0)

            response = HttpResponse(excel_response.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename="{batch_id.name}_{batch_id.discipline.acronym}_{batch_id.year}_final_registered.xlsx"'
            return response
        else:
            return HttpResponse(json.dumps({'error' : "No registered students found"}), content_type="application/json")

@login_required(login_url='/accounts/login')
def course_list(request):
    if(request.method == "POST"):
        request_body = json.loads(request.body)
        student_id = request_body['student_id']
        semester_id = request_body['semester_id']
 
        final_registration_table = FinalRegistration.objects.all().filter(semester_id = semester_id, verified = False)
        final = final_registration_table.filter(student_id = student_id, semester_id = semester_id)
        html = render_to_string('academic_procedures/student_course_list.html',{"course_list":final}, request)
 
        return HttpResponse(json.dumps({'html': html}),content_type="application/json")

def process_verification_request(request):
    if request.is_ajax():
        return verify_registration(request)
    return JsonResponse({'status': 'Failed'}, status=400)


def auto_process_verification_request(request):
    if request.is_ajax():
        return auto_verify_registration(request)
    return JsonResponse({'status': 'Failed'}, status=400)
    
@transaction.atomic
def verify_registration(request):

    if request.POST.get('status_req') == "accept" :
        student_id = request.POST.get('student_id')
        student = Student.objects.get(id = student_id)

        batch = student.batch_id
        curr_id = batch.curriculum
        
        if(student.curr_semester_no+1 >= 9):
            sem_no = 4
        else:
            sem_no = student.curr_semester_no+1

        sem_id = Semester.objects.get(curriculum = curr_id, semester_no = sem_no)

        final_register_list = FinalRegistration.objects.all().filter(student_id = student, verified = False, semester_id = sem_id)

        
        with transaction.atomic():
            ver_reg = []
            for obj in final_register_list:
                p = course_registration(
                    course_id=obj.course_id,
                    student_id=student,
                    semester_id=obj.semester_id,
                    course_slot_id = obj.course_slot_id,
                    working_year = datetime.datetime.now().year,
                    )
                ver_reg.append(p)
                o = FinalRegistration.objects.filter(id= obj.id).update(verified = True)
            course_registration.objects.bulk_create(ver_reg)
            # StudentRegistrationChecks.objects.filter(student_id = student_id, semester_id = sem_id).update(final_registration_flag = True)
            academics_module_notif(request.user, student.id.user, 'registration_approved')
            Student.objects.filter(id = student_id).update(curr_semester_no = sem_no)
            return JsonResponse({'status': 'success', 'message': 'Successfully Accepted'})
    elif request.POST.get('status_req') == "reject" :
        reject_reason = request.POST.get('reason')
        student_id = request.POST.get('student_id')
        student_id = Student.objects.get(id = student_id)

        batch = student_id.batch_id
        curr_id = batch.curriculum
        if(student.curr_semester_no+1 >= 9):
            sem_no = 4
        else:
            sem_no = student.curr_semester_no+1
        sem_id = Semester.objects.get(curriculum = curr_id, semester_no = sem_no)
        with transaction.atomic():
            academicadmin = get_object_or_404(User, username = request.user.username)
            FinalRegistration.objects.filter(student_id = student_id, verified = False, semester_id = sem_id).delete()
            StudentRegistrationChecks.objects.filter(student_id = student_id, semester_id = sem_id).update(final_registration_flag = False)
            FeePayments.objects.filter(student_id = student_id, semester_id = sem_id).delete()
            academics_module_notif(academicadmin, student_id.id.user, 'Registration Declined - '+reject_reason)
            return JsonResponse({'status': 'success', 'message': 'Successfully Rejected'})

@transaction.atomic
def auto_verify_registration(request):
    if request.POST.get('status_req') == "accept" :
        student_id = request.POST.get('student_id')
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
            for obj in final_register_list:
                o = FinalRegistration.objects.filter(id= obj.id).update(verified = True)
            academics_module_notif(request.user, student.id.user, 'registration_approved')
            
            Student.objects.filter(id = student_id).update(curr_semester_no = sem_no)
            return JsonResponse({'status': 'success', 'message': 'Successfully Accepted'})
         
    elif request.POST.get('status_req') == "reject" :
        reject_reason = request.POST.get('reason')
        student_id = request.POST.get('student_id')
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
            # FinalRegistration.objects.filter(student_id = student_id, verified = False, semester_id = sem_id).delete()
            StudentRegistrationChecks.objects.filter(student_id = student_id, semester_id = sem_id).update(final_registration_flag = False)
            FeePayments.objects.filter(student_id = student_id, semester_id = sem_id).delete()
            academics_module_notif(academicadmin, student_id.id.user, 'Registration Declined - '+reject_reason)
            return JsonResponse({'status': 'success', 'message': 'Successfully Rejected'})

def get_registration_courses(courses):
    x = [[]]
    
    for temp in courses:
        flag = False
        i = str(temp.course_code)
        i = i[:5]
        for j in x:
            if j:
                name = j[0]
                name = str(name.course_code)
                name = name[:5]
                if i.upper() == name.upper():
                    j.append(temp)
                    flag = True
                else :
                    continue
        if not flag:
            x.append([temp])
    return x


def teaching_credit_register(request) :
    if request.method == 'POST':
        try:
            roll = request.POST.get('roll')
            course1 = request.POST.get('course1')


            roll = str(roll)

            student_id = get_object_or_404(User, username=request.POST.get('roll'))
            student_id = ExtraInfo.objects.all().select_related('user','department').filter(user=student_id).first()
            student_id = Student.objects.all().select_related('id','id__user','id__department').filter(id=student_id.id).first()

            course1 = Curriculum.objects.select_related().get(curriculum_id = request.POST.get('course1'))
            course2 = Curriculum.objects.select_related().get(curriculum_id = request.POST.get('course2'))
            course3 = Curriculum.objects.select_related().get(curriculum_id = request.POST.get('course3'))
            course4 = Curriculum.objects.select_related().get(curriculum_id = request.POST.get('course4'))

            p = TeachingCreditRegistration(
                student_id = student_id,
                curr_1 = course1,
                curr_2 = course2,
                curr_3 = course3,
                curr_4 = course4
                )
            p.save()

            messages.info(request, ' Successful')
            return HttpResponseRedirect('/academic-procedures/main')
        except Exception as e:
            return HttpResponseRedirect('/academic-procedures/main')
    else:
        return HttpResponseRedirect('/academic-procedures/main')




def course_marks_data(request):
    try:
        course_id = request.POST.get('course_id')
        course = Courses.objects.select_related().get(id = course_id)
        # print(course)
        # print(course_id)
        student_list = course_registration.objects.filter(course_id__id=course_id).select_related(
            'student_id__id__user','student_id__id__department').only('student_id__batch', 
            'student_id__id__user__first_name', 'student_id__id__user__last_name',
            'student_id__id__department__name','student_id__id__user__username')
        mrks = []
        student_marks=[]
        for obj in student_list:
            o = SemesterMarks.objects.all().select_related('curr_id','student_id','curr_id','student_id__id','student_id__id__user','student_id__id__department').filter(curr_id = course_id)
            if o :
                student_marks=o
                continue
            else :
                p = SemesterMarks(
                        student_id = obj.student_id,
                        q1 = 0,
                        mid_term = 0,
                        q2 = 0,
                        end_term = 0,
                        other = 0,
                        grade = None,
                        curr_id = course
                    )
                mrks.append(p)
                student_marks=mrks
        SemesterMarks.objects.bulk_create(mrks)


        enrolled_student_list = SemesterMarks.objects.all().select_related('curr_id','student_id','student_id__id','student_id__id__user','student_id__id__department').filter(curr_id = course)
        grade_submission_date_eligibility = True
        enrolled_student_list=[]
        for i in student_list:
            #print("Rollno is:"+i.student_id.id.user.username)
            for item in student_marks:
                if(str(item.student_id)==i.student_id.id.user.username):
                    enrolled_student_list.append({"rollno":i.student_id.id.user.username, 
                    "name":i.student_id.id.user.first_name+" "+i.student_id.id.user.last_name, 
                    "department":i.student_id.id.department.name,
                    "q1":item.q1,"q2":item.q2,"mid_term":item.mid_term,"end_term":item.end_term,"other_marks":item.other})
                    break
        enrolled_student_list=sorted(enrolled_student_list, key = lambda i: i['rollno'])
        
        print(enrolled_student_list)
        print(len(enrolled_student_list))
        # try :
        #     d = Calendar.objects.get(description = "grade submission date")
        #     print(demo_date.date() >= d.from_date and demo_date.date() <= d.to_date)
        #     if demo_date.date() >= d.from_date and demo_date.date() <= d.to_date :
        #         grade_submission_date_eligibility = True
        # except Exception as e:
        #     grade_submission_date_eligibility = False
        #     print(e)
        data = render_to_string('academic_procedures/course_marks_data.html',
                                {'enrolled_student_list' : enrolled_student_list,
                                'course' : course,
                                'grade_submission_date_eligibility' : grade_submission_date_eligibility}, request)
        obj = json.dumps({'data' : data})
        return HttpResponse(obj, content_type = 'application/json')
    except Exception as e:
        print(e)
        return HttpResponseRedirect('/academic-procedures/main')




def submit_marks(request):
    try:
        print(request.POST)
        user = request.POST.getlist('user')
        q1 = request.POST.getlist('q1_marks')
        mid = request.POST.getlist('mid_marks')
        q2 = request.POST.getlist('q2_marks')
        end = request.POST.getlist('end_marks')
        other = request.POST.getlist('other_marks')
        try:
            grade = request.POST.getlist('grade')
        except Exception as e:
            grade = None
        messages.info(request, ' Successful')

        values_length = len(request.POST.getlist('user'))


        curr_id = Courses.objects.select_related().get(id = request.POST.get('course_id'))
        print(curr_id)
        for x in range(values_length):

            student_id = get_object_or_404(User, username = user[x])
            student_id = ExtraInfo.objects.select_related('user','department').get(id = student_id)
            student_id = Student.objects.select_related('id','id__user','id__department').get(id = student_id)

            if grade:
                g = grade[x]
            else :
                g = None

            st_existing = SemesterMarks.objects.all().select_related('curr_id','student_id','student_id__id','student_id__id__user','student_id__id__department').filter(student_id = student_id).filter(curr_id = curr_id).first()
            if st_existing :
                st_existing.q1 = q1[x] or 0
                st_existing.mid_term = mid[x] or 0
                st_existing.q2 = q2[x] or 0
                st_existing.end_term = end[x] or 0
                st_existing.other = other[x] or 0
                st_existing.grade = g
                st_existing.save()
            else :
                p = SemesterMarks(
                        student_id = student_id,
                        q1 = q1[x],
                        mid_term = mid[x],
                        q2 = q2[x],
                        end_term = end[x],
                        other = other[x],
                        grade = g,
                        curr_id = curr_id
                     )
                p.save()
                
            if request.POST.get('final_submit') == "True":
                try:
                    o_sub = MarkSubmissionCheck.objects.select_related().get(curr_id = curr_id)
                except Exception as e:
                    o_sub = None
                if o_sub:
                    o_sub.submitted = True
                    o_sub.save()
                else:
                    o_sub_create = MarkSubmissionCheck(
                        curr_id = curr_id,
                        verified = False,
                        submitted =True,
                        announced = False,)
                    o_sub_create.save()
            if request.POST.get('final_submit') == "False":
                try:
                    sub_obj = MarkSubmissionCheck.objects.select_related().get(curr_id = curr_id)
                except Exception as e:
                    sub_obj = None
                if sub_obj:
                    continue
                else :
                    sub_obj_create = MarkSubmissionCheck(
                        curr_id = curr_id,
                        verified = False,
                        submitted =False,
                        announced = False)
                    sub_obj_create.save()

        return HttpResponseRedirect('/academic-procedures/main')
    except Exception as e:
        print(e)
        return HttpResponseRedirect('/academic-procedures/main')




def verify_course_marks_data(request):
    try:
        curriculum_id = request.POST.get('curriculum_id')
        course = Curriculum.objects.select_related().get(curriculum_id = curriculum_id)


        enrolled_student_list = SemesterMarks.objects.all().select_related('curr_id','student_id','curr_id__course_id','student_id__id','student_id__id__user','student_id__id__department').filter(curr_id = course)

        grade_verification_date_eligibility = False
        try :
            d = Calendar.objects.get(description = "grade verification date")
            if demo_date.date() >= d.from_date and demo_date.date() <= d.to_date :
                grade_verification_date_eligibility = True
        except Exception as e:
            grade_verification_date_eligibility = False

        data = render_to_string('academic_procedures/verify_course_marks_data.html',
                                {'enrolled_student_list' : enrolled_student_list,
                                'course' : course,
                                'grade_verification_date_eligibility' : grade_verification_date_eligibility}, request)
        obj = json.dumps({'data' : data})
        return HttpResponse(obj, content_type = 'application/json')
    except Exception as e:
        return HttpResponseRedirect('/academic-procedures/main')


########################################
##########GLOBAL VARIABLE###############
########################################

verified_marks_students = [[]]
verified_marks_students_curr = None 

########################################
##########GLOBAL VARIABLE###############
########################################

def verify_marks(request):
    try:
        global verified_marks_students
        global verified_marks_students_curr
        verified_marks_students = [[]]
        verified_marks_students_curr = None

        user = request.POST.getlist('user')
        curr_id = Curriculum.objects.select_related().get(curriculum_id = request.POST.get('curriculum_id'))

        grade = request.POST.getlist('grade')

        values_length = len(request.POST.getlist('user'))
        ver_gr = []
        for x in range(values_length):
            student_id = get_object_or_404(User, username = user[x])
            student_id = ExtraInfo.objects.select_related('user','department').get(id = student_id)
            student_id = Student.objects.select_related('id','id__user','id__department').get(id = student_id)
            if grade:
                g = grade[x]
            else :
                g = None

            st_existing = SemesterMarks.objects.all().select_related('curr_id','student_id','curr_id__course_id','student_id__id','student_id__id__user','student_id__id__department').filter(student_id = student_id).filter(curr_id = curr_id).first()

            st_existing.grade = g
            ver_gr.append(st_existing)
            verified_marks_students.append([student_id,g]) 
        SemesterMarks.objects.bulk_update(ver_gr,['grade'])  
        verified_marks_students_curr = curr_id


        obj = MarkSubmissionCheck.objects.select_related().get(curr_id = curr_id)
        obj.verified = True
        obj.save()
        return HttpResponseRedirect('/aims/')
    except Exception as e:
        return HttpResponseRedirect('/aims/')



def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None

def generate_grade_pdf(request):
    instructor = Curriculum_Instructor.objects.all().select_related('curriculum_id','instructor_id','curriculum_id__course_id','instructor_id__department','instructor_id__user').filter(curriculum_id = verified_marks_students_curr).first()
    context = {'verified_marks_students' : verified_marks_students,
                'verified_marks_students_curr' : verified_marks_students_curr,
                'instructor' : instructor}
    pdf = render_to_pdf('academic_procedures/generate_pdf.html',context)
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="%s.pdf"' %(verified_marks_students_curr.course_code)
        return response
    return HttpResponse("PDF could not be generated")


def generate_result_pdf(request):
    batch = request.POST.get('batch')
    branch = request.POST.get('branch')
    programme = request.POST.get('programme')

    student_list = []
    branch_list = []
    result_list = [[]]   
    curriculum_list = []

    if programme == "":
        return HttpResponse("please insert programme")
    student_obj = Student.objects.all().select_related('id','id__user','id__department').filter(programme = programme)

    if batch == "":
        return HttpResponse("please insert batch")
    else:
        student_obj = student_obj.filter(batch = int(batch))
    
    if branch == "" :
        return HttpResponse("please insert branch")
    else :
        dep_objects = DepartmentInfo.objects.get(name = str(branch))
        branch_objects = ExtraInfo.objects.all().select_related('user','department').filter(department = dep_objects)

        for i in branch_objects:
            branch_list.append(i)

        for i in student_obj:
            if i.id in branch_list:
                student_list.append(i)
            else:
                continue



    curriculum_obj = Curriculum.objects.all().select_related().filter(batch = int(batch)).filter(branch = str(branch)).filter(programme = programme)
    curriculum_obj_common = Curriculum.objects.all().select_related().filter(batch = int(batch)).filter(branch = 'Common').filter(programme = programme)

    for i in curriculum_obj:
        curriculum_list.append(i)
    for i in curriculum_obj_common:
        curriculum_list.append(i)

    for i in student_list :
        x = []
        x.append(i.id.user.username)
        x.append(i.id.user.first_name+" "+i.id.user.last_name)
        for j in curriculum_list :
            grade_obj = SemesterMarks.objects.all().select_related('curr_id','student_id','curr_id__course_id','student_id__id','student_id__id__user','student_id__id__department').filter(curr_id = j).filter(student_id = i).first()
            if grade_obj :
                x.append(grade_obj.grade)
            else :
                x.append("-")
        spi = get_spi(curriculum_list ,x)
        x.append(spi)
        result_list.append(x)



    context = {'batch' : batch,
                'branch' : branch,
                'programme' : programme,
                'course_list' : curriculum_list,
                'result_list' : result_list}

    pdf = render_to_pdf('academic_procedures/generate_result_pdf.html',context)
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="%s.pdf"' %(programme + batch + branch)
        return response
    return HttpResponse("PDF could not be generated")


def generate_grade_sheet_pdf(request):
    batch = request.POST.get('batch')
    branch = request.POST.get('branch')
    programme = request.POST.get('programme')

    student_list = []
    branch_list = []
    result_list = [[]]   
    curriculum_list = []

    if programme == "":
        return HttpResponse("please insert programme")
    student_obj = Student.objects.all().select_related('id','id__user','id__department').filter(programme = programme)

    if batch == "":
        return HttpResponse("please insert batch")
    else:
        student_obj = student_obj.filter(batch = int(batch))
    
    if branch == "" :
        return HttpResponse("please insert branch")
    else :
        dep_objects = DepartmentInfo.objects.get(name = str(branch))
        branch_objects = ExtraInfo.objects.all().select_related('user','department').filter(department = dep_objects)

        for i in branch_objects:
            branch_list.append(i)

        for i in student_obj:
            if i.id in branch_list:
                student_list.append(i)
            else:
                continue



    curriculum_obj = Curriculum.objects.all().select_related().filter(batch = int(batch)).filter(branch = str(branch)).filter(programme = programme)
    curriculum_obj_common = Curriculum.objects.all().select_related().filter(batch = int(batch)).filter(branch = 'Common').filter(programme = programme)

    for i in curriculum_obj:
        curriculum_list.append(i)
    for i in curriculum_obj_common:
        curriculum_list.append(i)

    for i in student_list :
        x = []
        x.append(i.id.user.username)
        x.append(i.id.user.first_name+" "+i.id.user.last_name)
        for j in curriculum_list :
            grade_obj = SemesterMarks.objects.all().select_related('curr_id','student_id','curr_id__course_id','student_id__id','student_id__id__user','student_id__id__department').filter(curr_id = j).filter(student_id = i).first()
            if grade_obj :
                x.append(grade_obj.grade)
            else :
                x.append("-")
        spi = get_spi(curriculum_list ,x)
        x.append(spi)
        result_list.append(x)



    context = {'batch' : batch,
                'branch' : branch,
                'programme' : programme,
                'course_list' : curriculum_list,
                'result_list' : result_list}

    pdf = render_to_pdf('academic_procedures/generate_sheet.html',context)
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="%s.pdf"' %(programme + batch + branch)
        return response
    return HttpResponse("PDF could not be generated")


def get_spi(course_list,grade_list):
    spi = 0.0
    credits = 0
    total = 0
    earned = 0
    y = []
    for i in range(2,len(grade_list)) :
        x = {
            'grade' : grade_list[i],
            'credits' : None 
        }
        y.append(x)
    for  i in range(0,len(course_list)):
        y[i]['credits'] = course_list[i].credits

    for obj in y:
        if obj['grade'] == 'O':
            total = total + 10*obj['credits']
            credits = credits+ obj['credits']
            earned = earned + obj['credits']
        elif obj['grade'] == 'A+':
            total = total + 10*obj['credits']
            credits = credits+ obj['credits']
            earned = earned + obj['credits']
        elif obj['grade'] == 'A':
            total = total + 9*obj['credits']
            credits = credits+ obj['credits']
            earned = earned + obj['credits']
        elif obj['grade'] == 'B+':
            total = total + 8*obj['credits']
            credits = credits+ obj['credits']
            earned = earned + obj['credits']
        elif obj['grade'] == 'B':
            total = total + 7*obj['credits']
            credits = credits+ obj['credits']
            earned = earned + obj['credits']
        elif obj['grade'] == 'C+':
            total = total + 6*obj['credits']
            credits = credits+ obj['credits']
            earned = earned + obj['credits']
        elif obj['grade'] == 'C':
            total = total + 5*obj['credits']
            credits = credits+ obj['credits']
            earned = earned + obj['credits']
        elif obj['grade'] == 'D+':
            total = total + 4*obj['credits']
            credits = credits+ obj['credits']
            earned = earned + obj['credits']
        elif obj['grade'] == 'D':
            total = total + 3*obj['credits']
            credits = credits+ obj['credits']
            earned = earned + obj['credits']
        elif obj['grade'] == 'F':
            total = total + 2*obj['credits']
            credits = credits+ obj['credits']
            earned = earned + obj['credits']
        elif obj['grade'] == 'S':
            total = total 
            credits = credits
            earned = earned + obj['credits']
        elif obj['grade'] == 'X':
            total = total
            credits = credits
            earned = earned 
        elif obj['grade'] == '-':
            total = total
            credits = credits
            earned = earned 
    if credits == 0:
        return 0.0
    spi = total/credits
    return spi





def manual_grade_submission(request):
    if request.method == 'POST' and request.FILES:

        manual_grade_xsl=request.FILES['manual_grade_xsl']
        excel = xlrd.open_workbook(file_contents=manual_grade_xsl.read())
        sheet=excel.sheet_by_index(0)

        course_code = str(sheet.cell(0,1).value)
        course_name = str(sheet.cell(1,1).value)
        instructor = str(sheet.cell(2,1).value)
        batch = int(sheet.cell(3,1).value)
        sem = int(sheet.cell(4,1).value)
        branch = str(sheet.cell(5,1).value)
        programme = str(sheet.cell(6,1).value)
        credits = int(sheet.cell(7,1).value)
       

        curriculum_obj = Curriculum.objects.all().select_related().filter(course_code = course_code).filter(batch = batch).filter(programme = programme).first()
        
        if not curriculum_obj:
            course_obj = Course.objects.all().filter(course_name = course_name).first()
            if not course_obj :
                course_obj_create = Course(
                    course_name = course_name,
                    course_details = instructor)
                course_obj_create.save()

            course_obj = Course.objects.all().filter(course_name = course_name).first()
            curriculum_obj_create = Curriculum(
                course_code = course_code,
                course_id = course_obj,
                credits = credits,
                course_type = 'Professional Core',
                programme = programme,
                branch = branch,
                batch = batch,
                sem = sem,
                floated = True)
            curriculum_obj_create.save()
        curriculum_obj = Curriculum.objects.all().select_related().filter(course_code = course_code).filter(batch = batch).filter(programme = programme).first()

        marks_check_obj = MarkSubmissionCheck.objects.select_related().all().filter(curr_id = curriculum_obj).first()
        if marks_check_obj :
            marks_check_obj.submitted = True
            marks_check_obj.verified = True
            marks_check_obj.save()
        elif not marks_check_obj :
            marks_check_obj_create = MarkSubmissionCheck(
                curr_id = curriculum_obj,
                submitted = True,
                verified = False,
                announced = False)
            marks_check_obj_create.save()

        for i in range(11,sheet.nrows):
            roll = str(int(sheet.cell(i,0).value))
            q1 = float(sheet.cell(i,2).value)
            mid = float(sheet.cell(i,3).value)
            q2 = float(sheet.cell(i,4).value)
            end = float(sheet.cell(i,5).value)
            others = float(sheet.cell(i,6).value)
            grade = str(sheet.cell(i,8).value).strip()
            user = get_object_or_404(User, username = roll)
            extrainfo = ExtraInfo.objects.select_related('user','department').get(user = user)
            dep_objects = DepartmentInfo.objects.get(name = str(branch))
            extrainfo.department = dep_objects
            extrainfo.save()
            extrainfo = ExtraInfo.objects.select_related('user','department').get(user = user)
            student_obj = Student.objects.select_related('id','id__user','id__department').get(id = extrainfo)


            student_obj.programme = programme
            student_obj.batch = batch
            student_obj.category = 'GEN'
            student_obj.save()

            student_obj = Student.objects.select_related('id','id__user','id__department').get(id = extrainfo)
            register_obj = Register.objects.all().filter(curr_id = curriculum_obj, student_id = student_obj).first()
            if not register_obj:
                register_obj_create = Register(
                    curr_id = curriculum_obj,
                    year = batch,
                    student_id = student_obj,
                    semester = sem)
                register_obj_create.save()
            register_obj = Register.objects.all().filter(curr_id = curriculum_obj, student_id = student_obj).first()

            st_existing = SemesterMarks.objects.all().select_related('curr_id','student_id','curr_id__course_id','student_id__id','student_id__id__user','student_id__id__department').filter(student_id = student_obj).filter(curr_id = curriculum_obj).first()
            if st_existing :
                st_existing.grade = str(sheet.cell(i,8).value)
                st_existing.save()
            else :
                p = SemesterMarks(
                        student_id = student_obj,
                        q1 = q1,
                        mid_term = mid,
                        q2 = q2,
                        end_term = end,
                        other = others,
                        grade = grade,
                        curr_id = curriculum_obj
                     )
                p.save()

    return HttpResponseRedirect('/academic-procedures/')
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
##



def test(request):
    br_up = []
    st_list = Student.objects.select_related('id','id__user','id__department').all()
    for i in st_list :
        roll = i.id.user.username
        roll = str(roll)
        if i.programme.upper() == "B.DES" or i.programme.upper() == "B.TECH":
            batch = int(roll[:4])
            i.batch = batch
        elif i.programme.upper() == "M.DES" or i.programme.upper() == "M.TECH" or i.programme.upper() == "PH.D":
            batch = int('20'+roll[:2])
            i.batch = batch
        br_up.append(i)
    Student.objects.bulk_update(br_up,['batch'])
        
    return render(request,'../templates/academic_procedures/test.html',{})

def test_ret(request):
    try:
        data = render_to_string('academic_procedures/test_render.html',
                                {}, request)
        obj = json.dumps({'d' : data})
        return HttpResponse(obj, content_type = 'application/json')
    except Exception as e:
        return HttpResponseRedirect('/academic-procedures/main')


def Bonafide_form(request):
    template = get_template('academic_procedures/bonafide_pdf.html')
    current_user = get_object_or_404(User, username=request.user.username)

    user_details = ExtraInfo.objects.select_related('user','department').get(id = request.user)
    des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()

    name = ExtraInfo.objects.all().select_related('user','department').filter(id=request.user.username)[0].user

    if str(des.designation) == "student":
        obj = Student.objects.select_related('id','id__user','id__department').get(id = user_details.id)
    
        context = {
            'student_id' : request.user.username,
            'degree' : obj.programme.upper(),
            'name' : name.first_name +" "+ name.last_name,
            'branch' : get_user_branch(user_details),
            'purpose' : request.POST['purpose']
        }
        pdf = render_to_pdf('academic_procedures/bonafide_pdf.html',context)
        if pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename=Bonafide.pdf' 
            return response
        return HttpResponse("PDF could not be generated")


# def bonafide(request):
#     # if this is a POST request we need to process the form data
#     if request.method == 'POST':
#         # create a form instance and populate it with data from the request:
#         form = BonafideForm(request.POST)
#         # check whether it's valid:
#         if form.is_valid():
#             # process the data in form.cleaned_data as required
#             # ...
#             # redirect to a new URL:
#             print("vaild")

#     # if a GET (or any other method) we'll create a blank form
#     else:
#         form = BonafideForm()

#     return render(request, 'bonafide.html', {'form': form})

@login_required
def ACF(request):
        stu = Student.objects.get(id=request.user.username)
        month = request.POST.get('month')
        year= request.POST.get('year') 
        account = request.POST.get('bank_account')
        thesis = request.POST.get('thesis_supervisor')
        ta = request.POST.get('ta_supervisor')
        appli = request.POST.get('applicability')
        FACUL1 = None
        FACUL2 = None
        message = ""
        faculties = ExtraInfo.objects.all().filter(user_type = "faculty")
        res = "error"
        for j in range(2):
            for i in faculties:
                checkName = i.user.first_name + " " + i.user.last_name
                if j==0 and ta == checkName:
                    res = "success"
                    FACUL1 = i
                elif j==1 and thesis == checkName:
                    res = "success"
                    FACUL2 = i

            if (res == "error"):
                message = message + "The entered faculty incharge does not exist"
                content = {
                    'status' : res,
                    'message' : message
                } 
                content = json.dumps(content) 
                return HttpResponse(content)
               
            
        faculty_inc1 = get_object_or_404(Faculty, id = FACUL1)
        faculty_inc2 = get_object_or_404(Faculty, id = FACUL2)
        acf = AssistantshipClaim(student=stu,month=month, year=year, bank_account=account, thesis_supervisor=faculty_inc2, ta_supervisor=faculty_inc1, applicability= appli)
        acf.save()
        message= message + "Form submitted succesfully"
        content = {
        'status' : res,
        'message' : message
        } 
        sender1 = ExtraInfo.objects.get(id = str(FACUL1)[:4]).user
        sender2 = ExtraInfo.objects.get(id = str(FACUL2)[:4]).user
        content = json.dumps(content)
        AssistantshipClaim_faculty_notify(request.user,sender1)
        AssistantshipClaim_faculty_notify(request.user,sender2)
        return HttpResponse(content)


def update_assistantship(request):
    if request.method == 'POST':
        r = request.POST.get('remark')
        i = request.POST.get('obj_id')
        user = ExtraInfo.objects.get(user = request.user)
        recipient = User.objects.get(username = "acadadmin")
        assistantship_object = AssistantshipClaim.objects.get(id = i)
        sender = User.objects.get(username = assistantship_object.student)
        if user == assistantship_object.ta_supervisor.id and r == "Satisfactory":
            assistantship_object.ta_supervisor_remark=True
        elif user == assistantship_object.ta_supervisor.id and r == "Unsatisfactory":
            assistantship_object.ta_supervisor_remark=False
        if user == assistantship_object.thesis_supervisor.id and r == "Satisfactory":
            assistantship_object.thesis_supervisor_remark=True
        elif r == "Unsatisfactory" :
            assistantship_object.thesis_supervisor_remark=False
        assistantship_object.save()
        if  assistantship_object.thesis_supervisor_remark == True and  assistantship_object.ta_supervisor_remark == True :
            AssistantshipClaim_acad_notify(sender,recipient)
   
    return HttpResponseRedirect('/academic-procedures/main/')


def update_hod_assistantship(request):
    if request.method == 'POST':
        d = request.POST.get('dict')
        dic = json.loads(d)
        assisobj = AssistantshipClaim.objects.filter(ta_supervisor_remark = True).filter(thesis_supervisor_remark = True).filter(hod_approval = False)

        for obj in assisobj:
            if str(obj.student) in dic.keys():
                obj.hod_approval =True
                obj.save()
        return HttpResponse('success')



def update_acad_assis(request):
    if request.method == 'POST':
        d = request.POST.get('dict')
        dic = json.loads(d)
        aobj= AssistantshipClaim.objects.all()

        for obj in aobj:
            if obj.acad_approval == False and str(obj.student) in dic.keys():
                obj.stipend = dic[str(obj.student)]
                obj.acad_approval=True
                obj.save()
                              
        return HttpResponse('success')


def update_account_assistantship(request):
    if request.method == 'POST':
        di = request.POST.get('dict')
        dic = json.loads(di)

        acobj= AssistantshipClaim.objects.all()
        for obj in acobj:
            if obj.account_approval == False and str(obj.student) in dic.keys():
                obj.account_approval = True
                obj.save()
                recipient = User.objects.get(username = obj.student)
                AssistantshipClaim_notify(request.user,recipient,obj.month,obj.year)
                
            return HttpResponse('success')

def assis_stat(request):
    if request.method == 'POST':
        flag= request.POST.get('flag')
        assis_status = Assistantship_status.objects.all()
        for obj in assis_status:
            if flag == "studenttrue" :
                obj.student_status= True
            elif flag == "studentfalse":
                obj.student_status = False
            elif flag == "hodtrue" :
                obj.hod_status= True
            elif flag == "hodfalse":
                obj.hod_status = False
            elif flag == "accounttrue" :
                obj.account_status= True
            elif flag == "accountfalse":
                obj.account_status = False
            obj.save()
    return HttpResponse('success')


@login_required
def MTSGF(request):
    if request.method == 'POST':
        stu= Student.objects.get(id=request.user.username)
        theme = request.POST.get('theme_of_work')
        date = request.POST.get('date')
        place = request.POST.get('place')
        time = request.POST.get('time')
        work = request.POST.get('workdone')
        contribution = request.POST.get('specificcontri')
        future = request.POST.get('futureplan')
        report = request.POST.get('briefreport')
        publication_submitted = request.POST.get('publicationsubmitted')
        publication_accepted = request.POST.get('publicationaccepted')
        paper_presented = request.POST.get('paperpresented')
        paper_under_review = request.POST.get('paperunderreview')

        form=MTechGraduateSeminarReport(student=stu, theme_of_work=theme, date=date, place=place, time=time, work_done_till_previous_sem=work,
                                        specific_contri_in_cur_sem=contribution, future_plan=future, brief_report=report, publication_submitted=publication_submitted, 
                                        publication_accepted=publication_accepted, paper_presented=paper_presented, papers_under_review=paper_under_review)
        form.save()
        message= "Form submitted succesfully"
        res="success"
        content = {
            'status' : res,
            'message' : message
        } 
        
        content = json.dumps(content)
        return HttpResponse(content)


@login_required
def PHDPE(request):
    if request.method == 'POST':
        stu= Student.objects.get(id=request.user.username)
        theme = request.POST.get('theme_of_work')
        dateandtime = request.POST.get('date')
        place = request.POST.get('place')
        work = request.POST.get('workdone')
        contribution = request.POST.get('specificcontri')
        future = request.POST.get('futureplan')
        uploadfile = request.POST.get('Attachments')
        paper_submitted = request.POST.get('papersubmitted')
        paper_published = request.POST.get('paperaccepted')
        paper_presented = request.POST.get('paperpresented')
        

        form=PhDProgressExamination(student=stu, theme=theme, seminar_date_time=dateandtime, place=place, work_done=work,
                                        specific_contri_curr_semester=contribution, future_plan=future,details=uploadfile, 
                                        papers_published=paper_published, presented_papers=paper_presented,papers_submitted=paper_submitted)
        form.save()
        message= "Form submitted succesfully"
        res="success"
        content = {
            'status' : res,
            'message' : message
        } 
        
        content = json.dumps(content)
        return HttpResponse(content)


def update_mtechsg(request):
    if request.method == 'POST':
        i = request.POST.get('obj_id')
        ql=request.POST.get('quality')
        qn=request.POST.get('quantity')
        gr=request.POST.get('grade')
        pr=request.POST.get('panel_report')
        sg=request.POST.get('suggestion')
        
        mtech_object=MTechGraduateSeminarReport.objects.get(id = i)
        
        mtech_object.quality_of_work=ql
        mtech_object.quantity_of_work=qn
        mtech_object.Overall_grade=gr
        mtech_object.panel_report=pr
        mtech_object.suggestion=sg
        mtech_object.save()
    return HttpResponseRedirect('/academic-procedures/main/')

        

def update_phdform(request):
    if request.method == 'POST':
        i = request.POST.get('obj_id')
        ql = request.POST.get('quality')
        qn = request.POST.get('quantity')
        gr = request.POST.get('grade')
        continuationa = request.POST.get('continuationa')
        enhancementa = request.POST.get('enhancementa')
        completionperiod =  request.POST.get('completionperiod')
        pr = request.POST.get('pr')
        annualp = request.POST.get('annualp')
        sugg = request.POST.get('sugg')

        phd_object = PhDProgressExamination.objects.get(id = i)

        phd_object.quality_of_work=ql
        phd_object.quantity_of_work=qn
        phd_object.Overall_grade=gr
        phd_object.continuation_enhancement_assistantship=continuationa
        phd_object.enhancement_assistantship=enhancementa
        phd_object.completion_period=completionperiod
        phd_object.panel_report=pr
        phd_object.annual_progress_seminar=annualp
        phd_object.commments=sugg
        phd_object.save()
        content="success"
        content = json.dumps(content)
    return HttpResponse(content)


def update_dues(request):
    if request.method == "POST":
        i = request.POST.get('obj_id')
        md =int(request.POST.get('md'))
        hd = int(request.POST.get('hd'))
        ld = int(request.POST.get('ld'))
        pd = int(request.POST.get('pd'))
        ad = int(request.POST.get('ad'))
        
        dues_object = Dues.objects.get(id = i)
        message = ""
        if md < 0 and -1*md > dues_object.mess_due :
            message = message + "Subtracting more value than existing mess due<br>"
        if hd < 0 and -1*hd > dues_object.hostel_due :
            message = message + "Subtracting more value than existing hostel due<br>" 
        if ld < 0 and -1*ld > dues_object.library_due :
            message = message + "Subtracting more value than existing library due<br>" 
        if pd < 0 and -1*pd > dues_object.placement_cell_due :
            message = message + "Subtracting more value than existing placement cell due<br>"
        if ad < 0 and -1*ad > dues_object.academic_due :
            message = message + "Subtracting more value than existing academic due<br>"
        
        
        

        if (not message):
            message = "success"

    

        if message != "success":
            content = json.dumps(message)
            return HttpResponse(content)

         

        md += dues_object.mess_due
        hd += dues_object.hostel_due
        ld += dues_object.library_due
        pd += dues_object.placement_cell_due
        ad += dues_object.academic_due

        dues_object.mess_due = md
        dues_object.hostel_due = hd
        dues_object.library_due = ld
        dues_object.placement_cell_due = pd
        dues_object.academic_due = ad

        dues_object.save()
        content = json.dumps(message)
        return HttpResponse(content)


def mdue(request):
    if request.method == 'POST':
        rollno = request.POST.get('rollno')
        year = request.POST.get('year')
        month = request.POST.get('month')
        amount = int(request.POST.get('amount'))
        desc = request.POST.get('desc')
        amount1 = amount
        if desc == "due":
            amount1 = -1*amount
        
        Dues_mess = amount  
        student = Student.objects.get(id = rollno)
        
        messdue_list=MessDue.objects.all().filter(student = student)
        duesobj = Dues.objects.get(student_id = student)
        if(messdue_list):
            new_remaining = messdue_list[len(messdue_list)-1].remaining_amount + amount1
            Dues_mess = new_remaining
            messdueobj = MessDue(student = student, month = month, year = year,description = desc, amount = amount, remaining_amount = new_remaining)
        else:
            messdueobj=MessDue(student = student, month = month, year = year,description = desc, amount = amount, remaining_amount = amount1)
        messdueobj.save()

        if Dues_mess >= 0 :
            duesobj.mess_due = 0
        else :
            duesobj.mess_due = -1*Dues_mess
        duesobj.save()
        content = json.dumps("success")
        return HttpResponse(content)




def get_detailed_sem_courses(sem_id):
    course_slots = CourseSlot.objects.filter(semester_id=sem_id)
    # Serialize queryset of course slots into JSON
    course_slots_json = serialize('json', course_slots)
    # Convert JSON string into Python object
    course_slots_data = json.loads(course_slots_json)
    
    # Iterate over each course slot data and include associated course data
    for slot_data in course_slots_data:
        # Retrieve associated courses for the current course slot
        slot = CourseSlot.objects.get(id=slot_data['pk'])
        courses = list(slot.courses.all().values())
        # Add courses data to the course slot data
        slot_data['courses'] = courses
    
    return course_slots_data


def get_next_sem_courses(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        next_sem = data.get('next_sem')
        branch = data.get('branch')
        programme = data.get('programme')
        batch = data.get('batch')
        #  we go to student table and apply filters and get batch_id of the students with these filter
        batch_id = Student.objects.filter(programme = programme , batch = batch , specialization = branch)[0].batch_id

        curr_id = batch_id.curriculum
        # print('-----------------------------------------------------------------------------------------', curr_id)
        # curr_id = 1
        next_sem_id = Semester.objects.get(curriculum = curr_id, semester_no = next_sem)
        
        if next_sem_id:
            next_sem_registration_courses = get_detailed_sem_courses(next_sem_id )
            # print(next_sem_registration_courses)
            return JsonResponse(next_sem_registration_courses, safe=False)
    return JsonResponse({'error': 'Invalid request'})


def add_course_to_slot(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        course_slot_name = data.get('course_slot_name')
        course_code = data.get('course_name')
        # print('-----------------------------------------------------------------------------------------' , course_slot_name , course_code)
        try:
            course_slot = CourseSlot.objects.filter(name=course_slot_name).first()
            course = Courses.objects.filter(code=course_code).first()
            course_slot.courses.add(course)
            
            return JsonResponse({'message': f'Course {course_code} added to slot {course_slot_name} successfully.'}, status=200)
        except CourseSlot.DoesNotExist:
            return JsonResponse({'error': 'Course slot does not exist.'}, status=400)
        except Course.DoesNotExist:
            return JsonResponse({'error': 'Course does not exist.'}, status=400)

    return JsonResponse({'error': 'Invalid request method.'}, status=405)


def remove_course_from_slot(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        course_slot_name = data.get('course_slot_name')
        course_code = data.get('course_name')
        # print('-----------------------------------------------------------------------------------------' , course_slot_name , course_code)
        try:
            course_slot = CourseSlot.objects.filter(name=course_slot_name).first()
            course = Courses.objects.filter(code=course_code).first()
            course_slot.courses.remove(course)
            return JsonResponse({'message': f'Course {course_code} removed from slot {course_slot_name} successfully.'}, status=200)
        except CourseSlot.DoesNotExist:
            return JsonResponse({'error': 'Course slot does not exist.'}, status=400)
        except Course.DoesNotExist:
            return JsonResponse({'error': 'Course does not exist.'}, status=400)

    return JsonResponse({'error': 'Invalid request method.'}, status=405)       


def add_one_course(request):
    if request.method == 'POST':
        try:
            # print(request.POST)
            current_user = get_object_or_404(User, username=request.POST.get('user'))
            current_user = ExtraInfo.objects.all().filter(user=current_user).first()
            current_user = Student.objects.all().filter(id=current_user.id).first()

            sem_id = Semester.objects.get(id=request.POST.get('semester'))
            choice = request.POST.get('choice')
            slot = request.POST.get('slot')

            try:
                course_id = Courses.objects.get(id=choice)
                courseslot_id = CourseSlot.objects.get(id=slot)
                print(courseslot_id)
                print(courseslot_id.type)
                if course_registration.objects.filter(course_slot_id_id=courseslot_id, student_id=current_user).count() == 1 and courseslot_id.type != "Swayam":
                    already_registered_course_id = course_registration.objects.filter(course_slot_id_id=courseslot_id, student_id=current_user)[0].course_id
                    # print(already_registered_course_id)
                    msg = 'Already Registered in the course : ' +already_registered_course_id.code + '-'+ already_registered_course_id.name
                    return JsonResponse({'message' : msg})
                if((course_registration.objects.filter(course_id=course_id, student_id=current_user).count() >= 1)):
                    return JsonResponse({'message': 'Already registered in this course!'}, status=200)
                # Check if maximum course registration limit has not been reached
                if course_registration.objects.filter(student_id__batch_id__year=current_user.batch_id.year, course_id=course_id).count() < courseslot_id.max_registration_limit and \
                        (course_registration.objects.filter(course_id=course_id, student_id=current_user).count() == 0):
                    p = course_registration(
                        course_id=course_id,
                        student_id=current_user,
                        course_slot_id=courseslot_id,
                        semester_id=sem_id,
                        working_year = datetime.datetime.now().year,
                    )
                    p.save()
                    return JsonResponse({'message': 'Course added successfully'})
                else:
                    return JsonResponse({'message': 'Course not added because seats are full!'}, status=200)
            except Exception as e:
                return JsonResponse({'message': 'Error adding course'}, status=500)
        except Exception as e:
            return JsonResponse({'message': 'Error adding course'}, status=500)
    else:
        return JsonResponse({'message': 'Invalid request method'}, status=405)
    
def replace_one_course(request):
    if request.method == 'POST' :       
        try:
            current_user = get_object_or_404(User, username=request.POST.get('user'))
            current_user = ExtraInfo.objects.all().filter(user=current_user).first()
            current_user = Student.objects.all().filter(id=current_user.id).first()


            course_id = Courses.objects.get(id = request.POST.get('choice'))
            courseslot_id = CourseSlot.objects.get(id = request.POST.get('slot'))
            if course_registration.objects.filter(student_id__batch_id__year=current_user.batch_id.year, course_id=course_id).count() < courseslot_id.max_registration_limit and \
                (course_registration.objects.filter(course_id=course_id, student_id=current_user).count() == 0):
                # print('---------------------------------------------------------------------------------' , course_registration.objects.filter(student_id__batch_id__year=current_user.batch_id.year, course_id=course_id).count() ,  courseslot_id.max_registration_limit )
                registered_course = course_registration.objects.filter(student_id=current_user, course_slot_id = courseslot_id).first()

                if registered_course:
                    registered_course.course_id = course_id 
                    registered_course.save()
            else:
                return JsonResponse({'message': 'Cannot Replace to this course seats are full!'}, status=200)
                
            return JsonResponse({'message': 'Course Replaced Successfully'}, status=200)
        except Exception as e:
            return JsonResponse({'message': 'Error Replacing course'}, status=500)
    else :
        return JsonResponse({'message': 'Invalid request method'}, status=405)
    
def get_sem_swayam(sem_id, batch):
    courses = []
    course_slots = CourseSlot.objects.all().filter(type='Swayam')
    
    for slot in course_slots:
        courses.append(slot)
        
    return courses

def replaceSwayam(request):
    if(request.POST):
        # print(f"++++++++++++++++++++++++++++++++++++++++++++++++{request.POST}")
        
        current_user = get_object_or_404(User, username=request.user.username)
        user_details = ExtraInfo.objects.all().select_related(
            'user', 'department').filter(user=current_user).first()
        desig_id = Designation.objects.all().filter(name='acadadmin').first()
        temp = HoldsDesignation.objects.all().select_related().filter(
            designation=desig_id).first()
        acadadmin = temp.working
        k = str(user_details).split()
        final_user = k[2]

        if ('acadadmin' != request.session.get('currentDesignationSelected')):
            return HttpResponseRedirect('/academic-procedures/')
        roll_no = request.POST["rollNo"]
        obj = ExtraInfo.objects.all().select_related(
            'user', 'department').filter(id=roll_no).first()
        firstname = obj.user.first_name
        lastname = obj.user.last_name
        dict2 = {'roll_no': roll_no,
                 'firstname': firstname, 'lastname': lastname}
        
        
        details = []

        obj2 = Student.objects.all().select_related(
            'id', 'id__user', 'id__department').filter(id=roll_no).first()
        # obj = Register.objects.all().select_related('curr_id', 'student_id', 'curr_id__course_id',
        #                                             'student_id__id', 'student_id__id__user', 'student_id__id__department').filter(student_id=obj2)
        batch = obj2.batch_id
        curr_id = batch.curriculum
        curr_sem_id = Semester.objects.get(curriculum = curr_id, semester_no = obj2.curr_semester_no)

        current_sem_courses = get_currently_registered_elective(
            roll_no, curr_sem_id)
        current_sem_swayam = get_sem_swayam(curr_sem_id,2025)
        
        idd = obj2
        for z in current_sem_courses:
            eletive_id=z[2]
            z = z[1]
             
            course_code = z.code
            course_name = z.name

            k = {}
            # reg_ig has course registration id appended with the the roll number
            # so that when we have removed the registration we can be redirected to this view
            k['reg_id'] = roll_no+" - "+course_code
            k['rid'] = roll_no+" - "+course_code
            # Name ID Confusion here , be carefull
            courseobj2 = Courses.objects.all().filter(code=course_code)
            # if(str(z.student_id) == str(idd)):
            for p in courseobj2:
                k['course_id'] = course_code
                k['course_name'] = course_name
                k['sem'] = curr_sem_id.semester_no
                k['credits'] = p.credit
                k['eletive_id'] = eletive_id
            details.append(k)

        year = demo_date.year
        month = demo_date.month
        yearr = str(year) + "-" + str(year+1)
        semflag = 0
        if(month >= 7):
            semflag = 1
        else:
            semflag = 2
        # TO DO Bdes
        date = {'year': yearr, 'semflag': semflag}
        course_list = Courses.objects.all()
        semester_list = Semester.objects.all()
        html = render_to_string('academic_procedures/studentSwayam.html',
                                {'details': details,
                                 'dict2': dict2,
                                 'course_list': course_list,
                                 'current_sem_swayam':current_sem_swayam,
                                 'roll_no':roll_no,
                                 'semester_list': semester_list,
                                #  'csrf_token' : csrf_token,
                                 'date': date}, request)

        maindict = {'html': html}
        obj = json.dumps(maindict)
        return HttpResponse(obj, content_type='application/json')
    
def get_currently_registered_elective(student_id, semester_id):
    registrations = course_registration.objects.filter(student_id=student_id, semester_id=semester_id)
    courses = []
    for registration in registrations:
        if registration.course_slot_id.type == "Optional Elective":
            courses.append((registration.course_slot_id, registration.course_id, registration.id))
    return courses



def swayam_replace(request):
    if request.method == 'POST':
        csrf_token = request.POST.get('csrfmiddlewaretoken', None)

        # print(f"---------------------------------{csrf_token}")
        try:
            
            # print(f"djfhajjfsjfhajfhjdsfsdfj{request.POST}")
            csrf_token = request.POST.get('csrfmiddlewaretoken', None)

            # print(f"---------------------------------{csrf_token}")
            # Accessing individual values by key
            user_value = request.POST['user']
            course_id_value = request.POST['course_id']

            # print(user_value)  20BCS074
            # print(course_id_value) 8955

            elective_to_delete = course_registration.objects.get(id=course_id_value)
            sem = elective_to_delete.semester_id
            # print(elective_to_delete)
            # print(sem) cse ug curri v1


            swayam_course_id_value = request.POST['swayam_course_id']
            swayam_course_id_value_array = [int(id_str) for id_str in swayam_course_id_value.split(',')[:-1]]
            # print(swayam_course_id_value_array)
            # print(swayam_course_id_value)



            swayam_course_slot_id_value = request.POST['swayam_course_slot_id']
            swayam_course_slot_id_value_array = [int(slot_str) for slot_str in swayam_course_slot_id_value.split(',')[:-1]]
            # print(swayam_course_slot_id_value_array)
            # print(swayam_course_slot_id_value)


            swayam_semester_id_value = request.POST['swayam_semester_id']
            swayam_semester_id_value_array = [int(semester_str) for semester_str in swayam_semester_id_value.split(',')[:-1]]


            

            n = len(swayam_course_id_value_array)
            # print(n)
            # new_row_data = []
            for i in range(n):
                course_id_model = Courses.objects.get(id=swayam_course_id_value_array[i])
                # print(course_id_model)
                semester_id_model = Semester.objects.get(id=swayam_semester_id_value_array[i])
                student_id_model = Student.objects.get(id=user_value)
                course_slot_id_model = CourseSlot.objects.get(id=swayam_course_slot_id_value_array[i])
                obj = course_registration(
                    course_id = course_id_model,
                    semester_id = semester_id_model,
                    student_id = student_id_model,
                    course_slot_id = course_slot_id_model,
                    working_year = datetime.datetime.now().year,
                    )
                obj.save()
            
            # for j in range(n):
            #     SwayamCourses.objects.filter(course_id = swayam_course_id_value_array[j], student_id=user_value).update(course_used = True)

            elective_to_delete.delete()
           

            messages.success(request, "Your Courses have been replaced.")
            return HttpResponseRedirect('/academic-procedures/main')

            

            
        except Exception as e:
            error_message = str(e)
            print("Error:", error_message)
            messages.error(request, f"Error in Registration: {error_message}")
            return HttpResponseRedirect('/academic-procedures/main')
    else:
        return HttpResponseRedirect('/academic-procedures/main')
    
def register_backlog_course(request):
    if request.method == 'POST':
        try:
            current_user = request.user
            current_user = ExtraInfo.objects.all().filter(user=request.user).first()
            current_user = Student.objects.all().filter(id=current_user.id).first()
            sem_id = Semester.objects.filter(id = request.POST.get('semester')).first()
            course_id = Courses.objects.get(code = request.POST.get('courseCode') , version = request.POST.get('Version'))  
            course_slots = course_id.courseslots.all()
            course_slot_id = ''
            if course_slots:
                course_slot_id = CourseSlot.objects.filter(id = course_slots[0].id).first()
            if (sem_id.semester_no - course_slot_id.semester.semester_no)%2 != 0 :
                return JsonResponse({'message':'Wait for Next Semester !'}, status=200)
                # print('_____________________________________________________________________________________________' , course_id ,current_user , course_slot_id ,  sem_id)
            try:
                if course_registration.objects.filter(course_id=course_id, student_id=current_user , semester_id  = sem_id).count() == 0:
                    p = course_registration(
                            course_id=course_id,
                            student_id=current_user,
                            course_slot_id=course_slot_id,
                            semester_id=sem_id,
                            working_year = datetime.datetime.now().year,
                        )
                    p.save()
                    return JsonResponse({'message': 'Successfully Registered Backlog course' }, status=200)
                else:
                    return JsonResponse({'message': 'Already Registered Backlog course' }, status=200)
            except Exception as e:
                print(str(e))
                return JsonResponse({'message': 'Error Registering course ' + str(e)}, status=500)
        except Exception as e:
            print(str(e))
            return JsonResponse({'message': 'Adding Backlog Failed '  +str(e)}, status=500)