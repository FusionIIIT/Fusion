import datetime
import json
from itertools import chain
from io import BytesIO
from django.template.loader import get_template
from xlsxwriter.workbook import Workbook
from xhtml2pdf import pisa
import xlrd

from django.db import transaction
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Max
from django.http import HttpResponse, HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string


from applications.academic_information.models import Calendar, Course, Student,Curriculum_Instructor, Curriculum
from applications.globals.models import (DepartmentInfo, Designation,
                                         ExtraInfo, Faculty, HoldsDesignation)

from .models import (BranchChange, CoursesMtech, InitialRegistrations, StudentRegistrationCheck,
                     MinimumCredits, Register, Thesis, FinalRegistrations, ThesisTopicProcess,
                     Constants, FeePayment, TeachingCreditRegistration, SemesterMarks, MarkSubmissionCheck)

from notification.views import academics_module_notif


demo_date = datetime.datetime.now()
# demo_date = demo_date - datetime.timedelta(days = 180)
# demo_date = demo_date + datetime.timedelta(days = 3)
# demo_date = demo_date - datetime.timedelta(days = 5)

print(demo_date)


@login_required(login_url='/accounts/login')
def academic_procedures_redirect(request):
    return HttpResponseRedirect('/academic-procedures/main/')


@login_required(login_url='/accounts/login')
def main(request):
    return HttpResponseRedirect('/academic-procedures/main/')


@login_required(login_url='/accounts/login')
def academic_procedures(request):

    current_user = get_object_or_404(User, username=request.user.username)
    # print("current username : ")
    # print(current_user)
    print("current user id : request.user.id")
    # print(request.user.id)
    print("user detail id : request.user")
    # print(request.user)

    #mohit-these are extra info details , user id used as main id
    user_details = ExtraInfo.objects.get(user = request.user)
    # print(user_details)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    # print(des)
    # print("here is the designation")
    # print(des.designation)


    if str(des.designation) == "student":
        obj = Student.objects.get(id = user_details.id)
        print(obj.programme)
        return HttpResponseRedirect('/academic-procedures/stu/')
        # return HttpResponseRedirect('/logout/')
    elif str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/academic-procedures/fac/')
        # return HttpResponseRedirect('/logout/')

    elif str(request.user) == "acadadmin" :
        return HttpResponseRedirect('/aims/')

    else:
        return HttpResponse('person not found')
#
#
#
#
#
#
@login_required(login_url='/accounts/login')
def academic_procedures_faculty(request):

    current_user = get_object_or_404(User, username=request.user.username)
    # print("current username : ")
    # print(current_user)
    # print("current user id : request.user.id")
    # print(request.user.id)
    # print("user detail id : request.user")
    # print(request.user)

    #mohit-these are extra info details , user id used as main id
    user_details = ExtraInfo.objects.get(user = request.user)
    # print(user_details)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    # print(des)

    if str(des.designation) == "student":
        return HttpResponseRedirect('/academic-procedures/main/')

    elif str(request.user) == "acadadmin" :
        return HttpResponseRedirect('/academic-procedures/main/')

    elif str(des.designation) == "Associate Professor" :
        object_faculty = Faculty.objects.get(id = user_details)

        student_flag = False
        fac_flag = True

        print(Curriculum_Instructor.objects.all().filter(instructor_id = user_details).first())
        # temp = Curriculum.objects.all().filter(course_code = "CS315L").first()
        # Curriculum_Instructor.objects.create(curriculum_id = temp, instructor_id = user_details)
        #thesis_supervision_request_list = ThesisTopicProcess.objects.all()
        thesis_supervision_request_list = ThesisTopicProcess.objects.all().filter(supervisor_id = object_faculty)
        approved_thesis_request_list = thesis_supervision_request_list.filter(approval_supervisor = True)
        pending_thesis_request_list = thesis_supervision_request_list.filter(pending_supervisor = True)
        faculty_list = get_faculty_list()
        courses_list = Curriculum_Instructor.objects.filter(instructor_id=user_details)
        return render(
                        request,
                         '../templates/academic_procedures/academicfac.html' ,
                         {
                            'student_flag' : student_flag,
                            'fac_flag' : fac_flag,
                            'thesis_supervision_request_list' : thesis_supervision_request_list,
                            'pending_thesis_request_list' : pending_thesis_request_list,
                            'approved_thesis_request_list' : approved_thesis_request_list,
                            'faculty_list' : faculty_list,
                            'courses_list' : courses_list,
                         })
    else:
        HttpResponse("user not found")



@login_required(login_url='/accounts/login')
def academic_procedures_student(request):

    current_user = get_object_or_404(User, username=request.user.username)

    user_details = ExtraInfo.objects.get(id = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()

    if str(des.designation) == "student":
        obj = Student.objects.get(id = user_details.id)

        if obj.programme.upper() == "PH.D" :
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

        current_date = demo_date.date()
        year = demo_date.year
        
        registers = get_student_register(user_details.id)   
        user_sem = get_user_semester(request.user, ug_flag, masters_flag, phd_flag)      
        user_branch = get_user_branch(user_details)
        student_registration_check_pre = get_student_registrtion_check(obj,user_sem+1)
        student_registration_check_final = get_student_registrtion_check(obj,user_sem)
        cpi = get_cpi(user_details.id)


        pre_registration_date_flag = get_pre_registration_eligibility(current_date)
        final_registration_date_flag = get_final_registration_eligibility(current_date)
        add_or_drop_course_date_flag = get_add_or_drop_course_date_eligibility(current_date)
        pre_registration_flag = False
        final_registration_flag = False
        if(student_registration_check_pre):
            pre_registration_flag = student_registration_check_pre.pre_registration_flag
        if(student_registration_check_final):
            final_registration_flag = student_registration_check_final.final_registration_flag


        current_sem_branch_courses = get_branch_courses(request.user, user_sem, user_branch)
        next_sem_branch_courses = get_branch_courses(request.user, user_sem+1, user_branch)
        acad_year = get_acad_year(user_sem, year)
        currently_registered_courses = get_currently_registered_courses(user_details.id, user_sem)
        print(currently_registered_courses)
        current_credits = get_current_credits(currently_registered_courses)

        next_sem_branch_registration_courses = get_registration_courses(next_sem_branch_courses)
        final_registration_choices = get_registration_courses(get_branch_courses(request.user, user_sem, user_branch))
        print("these are courses")
        print(next_sem_branch_registration_courses)
        print(user_sem)


            # print("here id")
            # last_id = Register.objects.all().aggregate(Max('r_id'))
            # print(last_id)
            # Register.objects.filter(r_id = 7220).delete()
            # o = Register.objects.all().filter(student_id = obj, course_id= Course.objects.all().filter(course_id= "CS314a").first()).first()
            # print(o.r_id)
            # o = Register.objects.all().filter(r_id = 7245).first()
            # print(o)
            # Register.objects.filter(r_id = 7239).delete()
            # a = Student.objects.get(id = "1711003")
            # print(a.programme)
            #Register.objects.all().delete()
            # print(InitialRegistrations.objects.all().first().curr_id)
            #Student.objects.filter(id = user_details.id).update(cpi = 9.2)
            #FeePayment.objects.all().delete()
            #print(FeePayment.objects.all().first().transaction_id)

        details = {
                'current_user': current_user,
                'year': acad_year,
                'user_sem': user_sem,
                'user_branch' : str(user_branch),
                'cpi' : cpi,
                }



        try:
            pre_registered_courses = InitialRegistrations.objects.all().filter(student_id = obj,semester = user_sem)
            pre_registered_courses_show = InitialRegistrations.objects.all().filter(student_id = obj,semester = user_sem+1)
        except:
            pre_registered_courses =  None
        try:
            final_registered_courses = FinalRegistrations.objects.all().filter(student_id = obj,semester = user_sem)
            add_courses_options = get_add_course_options(current_sem_branch_courses, currently_registered_courses)
            added_course_count = get_added_course_count(currently_registered_courses, final_registered_courses)
            added_courses_list = get_added_courses_list(currently_registered_courses, final_registered_courses)
            print(added_course_count)
            drop_courses_options = currently_registered_courses
            dropped_courses_count = get_dropped_courses_count(currently_registered_courses, final_registered_courses)
            print(dropped_courses_count)
        except:
            final_registered_courses = None
            dropped_courses_count = 0
            drop_courses_options = None
            added_courses_list = None
            add_courses_options = None
            added_course_count = 0




        fee_payment_mode_list = dict(Constants.PaymentMode)


        performance_list = []
        result_announced = False
        for i in currently_registered_courses:
            try:
                performance_obj = SemesterMarks.objects.all().filter(student_id = obj, curr_id = i).first()
            except:
                performance_obj = None
            performance_list.append(performance_obj)
        for i in currently_registered_courses:
            try:
                result_announced_obj = MarkSubmissionCheck.objects.get(curr_id = i)
                if result_announced_obj:
                    print(result_announced_obj.announced)
                    if result_announced_obj.announced == True:
                        result_announced = result_announced_obj.announced
                else:
                    continue
            except:
                continue
        print("result")
        print(result_announced)

        faculty_list = None
        thesis_request_list = None
        pre_existing_thesis_flag = False
        teaching_credit_registration_course = None
        if masters_flag == True :
            faculty_list = get_faculty_list()    
            thesis_request_list = ThesisTopicProcess.objects.all().filter(student_id = obj)
            pre_existing_thesis_flag = get_thesis_flag(obj)
        if phd_flag == True:
            pre_existing_thesis_flag = get_thesis_flag(obj)
            teaching_credit_registration_course = Curriculum.objects.all().filter(batch = 2016, sem =6)
        return render(
                          request, '../templates/academic_procedures/academic.html',
                          {'details': details,
                           # 'calendar': calendar,
                            'currently_registered': currently_registered_courses,
                            'pre_registered_courses' : pre_registered_courses,
                            'pre_registered_courses_show' : pre_registered_courses_show,
                            'final_registered_courses' : final_registered_courses,
                            'current_credits' : current_credits,
                            'courses_list': next_sem_branch_courses,
                            'fee_payment_mode_list' : fee_payment_mode_list,
                            'next_sem_branch_registration_courses' : next_sem_branch_registration_courses,
                            'final_registration_choices' : final_registration_choices,
                            'performance_list' : performance_list,
                            'faculty_list' : faculty_list,
                            'thesis_request_list' : thesis_request_list,

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
                            'dropped_courses_count' : dropped_courses_count,
                            'added_course_count' : added_course_count,
                           # 'pre_register': pre_register,
                            'prd': pre_registration_date_flag,
                            'frd': final_registration_date_flag,
                            'adc_date_flag': add_or_drop_course_date_flag,
                            'pre_registration_flag' : pre_registration_flag,
                            'final_registration_flag': final_registration_flag,
                           # 'final_r': final_register_1,
                            
                            'teaching_credit_registration_course' : teaching_credit_registration_course,
                            
                           # 'mincr': minimum_credit,
                           }
                )

    elif str(des.designation) == "Associate Professor" :
        return HttpResponseRedirect('/academic-procedures/main/')

    elif str(request.user) == "acadadmin" :
        return HttpResponseRedirect('/academic-procedures/main/')

    else:
        return HttpResponse('user not found')









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
    print(initial_courses, final_register)
    for i in initial_courses:
        flag = 0
        for j in final_register:
            # print(i.course_id, "sdss", j.course_id)
            if(str(i.course_name) == str(j.course_id)):
                flag = 1
        if(flag == 0):
            x.append(i)
    # print(x)
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
    obj = CoursesMtech.objects.filter(specialization=specialization)
    obj3 = CoursesMtech.objects.filter(specialization="all")
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
    extraInfo_user = ExtraInfo.objects.all().filter(user=student).first()
    cpi_data = Student.objects.all().filter(id=extraInfo_user.id).first()
    # for i in range(len(branch_list)):
    #     branch_cut = branch_list[i].name
    #     branches.append(branch_cut)

    label_for_change = False

    semester = get_user_semester(extraInfo_user.id, ug_flag, masters_flag, phd_flag)
    semester = 2

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
                department - user's branch.
    '''
    if request.method == 'POST':
        current_user = get_object_or_404(User, username=request.user.username)
        extraInfo_user = ExtraInfo.objects.all().filter(user=current_user).first()
        student = Student.objects.all().filter(id=extraInfo_user.id).first()
        department = DepartmentInfo.objects.all().filter(name=request.POST['change']).first()
        # print(department)
        change_save = BranchChange(
            branches=department,
            user=student
            )
        change_save.save()
        messages.info(request, 'Apply for branch change successfull')
        return HttpResponseRedirect('/academic-procedures/main')
    else:
        messages.info(request, 'Unable to proceed')
        return HttpResponseRedirect('/academic-procedures/main')
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
        values_length = 0
        for key, values in request.POST.lists():
            values_length = len(values)
            break
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
                    # print(key, values[i])
        for i in range(len(branches)):
            get_student = ExtraInfo.objects.all().filter(id=choices[i][:7])
            get_student = get_student[0]
            branch = DepartmentInfo.objects.all().filter(name=branches[i])
            get_student.department = branch[0]
            get_student.save()
            student = Student.objects.all().filter(id=choices[i][:7]).first()
            change = BranchChange.objects.all().filter(user=student)
            change = change[0]
            change.delete()
        messages.info(request, 'Apply for branch change successfull')
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
    data = data.split("+")
    rid = data[0]
    # print(redirecturl)
    Register.objects.filter(r_id=rid).delete()
    response_data = {}
    return HttpResponse(json.dumps(response_data), content_type="application/json")


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
    current_user = get_object_or_404(User, username=request.user.username)
    user_details = ExtraInfo.objects.all().filter(user=current_user).first()
    desig_id = Designation.objects.all().filter(name='Upper Division Clerk')
    temp = HoldsDesignation.objects.all().filter(designation = desig_id).first()
    print (temp)
    print (current_user)
    acadadmin = temp.working
    k = str(user_details).split()
    print(k)
    final_user = k[2]

    if (str(acadadmin) != str(final_user)):
        return HttpResponseRedirect('/academic-procedures/')
    roll_no = request.GET.get('id')
    obj = ExtraInfo.objects.all().filter(id=roll_no)
    firstname = obj[0].user.first_name
    lastname = obj[0].user.last_name
    dict2 = {'roll_no': roll_no, 'firstname': firstname, 'lastname': lastname}
    obj2 = Student.objects.all().filter(id=roll_no)
    obj = Register.objects.all()

    details = []
    for a in obj2:
        idd = a.id
        for z in obj:
            k = {}
            # reg_ig has course registration id appended with the the roll number
            # so that when we have removed the registration we can be redirected to this view
            k['reg_id'] = str(z.r_id) + "+" + str(roll_no)
            k['rid'] = z.r_id
            # Name ID Confusion here , be carefull
            courseobj2 = Course.objects.all().filter(course_name=z.course_id)
            if(str(z.student_id) == str(idd)):
                for p in courseobj2:
                    k['course_id'] = p.course_id
                    k['course_name'] = p.course_name
                    k['sem'] = p.sem
                    k['credits'] = p.credits
                details.append(k)

    # year = datetime.datetime.now().year
    # month = datetime.datetime.now().month

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
    return render(
                    request,
                    '../templates/academic_procedures/show_courses.html',
                    {'details': details,
                        'dict2': dict2,
                        'date': date})


# view to generate all list of students



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
    user_details = ExtraInfo.objects.all().filter(user=current_user).first()
    desig_id = Designation.objects.all().filter(name='Upper Division Clerk')
    temp = HoldsDesignation.objects.all().filter(designation = desig_id).first()
    acadadmin = temp.working
    k = str(user_details).split()
    final_user = k[2]

    if (str(acadadmin) != str(final_user)):
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


    change_queries = BranchChange.objects.all()
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
        students = Student.objects.all().filter(id=i.user.id).first()
        user_branch = ExtraInfo.objects.all().filter(id=students.id.id).first()
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
    # print(lists)
    if len(initial_branch) > 0:
        tag = True
    context = {
        'list': lists,
        'total': len(initial_branch),
        'tag': tag
    }
    # print(context)
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
    # print(request.user.username)
    current_user = get_object_or_404(User, username=request.user.username)
    user_details = ExtraInfo.objects.all().filter(user=current_user).first()
    student = Student.objects.all().filter(id=user_details.id).first()
    thesis = Thesis.objects.all().filter(student_id=student).first()
    #Professor = Designation.objects.all().filter(name='Professor')
    # print(user_details.department.name)
    #faculty = ExtraInfo.objects.all().filter(department=user_details.department,
    #                                         designation='Professor')
    f1 = HoldsDesignation.objects.filter(designation=Designation.objects.get(name = "Assistant Professor"))
    f2 = HoldsDesignation.objects.filter(designation=Designation.objects.get(name = "Professor"))
    f3 = HoldsDesignation.objects.filter(designation=Designation.objects.get(name = "Associate Professor"))

    faculty = list(chain(f1,f2,f3))
    # print(Professor,faculty)
    faculties_list = []
    for i in faculty:
        faculties_list.append(str(i.user.first_name)+" "+str(i.user.last_name))
    # print (faculties_list)
    total_thesis = True
    if(thesis is None):
        total_thesis = False

    context = {
            'total_thesis': total_thesis,
            'thesis': thesis,
            }
    # print(total_thesis)
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
    return Register.objects.all().filter(student_id = id)

def get_pre_registration_eligibility(current_date):
    try:
        pre_registration_date = Calendar.objects.all().filter(description="Pre Registration").first()
        prd_start_date = pre_registration_date.from_date
        prd_end_date = pre_registration_date.to_date
        if current_date>=prd_start_date and current_date<=prd_end_date:
            return True
        else :
            return False
    except:
        return False

def get_final_registration_eligibility(current_date):
    try:
        frd = Calendar.objects.all().filter(description="Physical Reporting at the Institute").first()
        frd_start_date = frd.from_date
        frd_end_date = frd.to_date
        if current_date>=frd_start_date and current_date<=frd_end_date:
            return True
        else :
            return False
    except:
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
    except:
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
    except:
        return False

def get_user_branch(user_details):
    return user_details.department.name

def get_acad_year(user_sem, year):
        if user_sem%2 == 1:
            acad_year = str(year) + "-" + str(year+1)
        elif user_sem%2 == 0:
            acad_year = str(year-1) + "-" + str(year)
        return acad_year

def pre_registration(request):
    if request.method == 'POST':
        try:
            current_user = get_object_or_404(User, username=request.POST.get('user'))
            current_user = ExtraInfo.objects.all().filter(user=current_user).first()
            current_user = Student.objects.all().filter(id=current_user.id).first()

            sem = request.POST.get('semester')

            count = request.POST.get('ct')
            count = int(count)
            for i in range(2, count+1):
                i = str(i)
                choice = "choice["+i+"]"
                curr_id = get_object_or_404(Curriculum, curriculum_id = request.POST.get(choice))
                
                p = InitialRegistrations(
                    curr_id = curr_id,
                    semester = sem,
                    student_id = current_user,
                    batch = current_user.batch
                    )
                p.save()
            try:
                check = StudentRegistrationCheck(
                            student = current_user,
                            pre_registration_flag = True,
                            final_registration_flag = False,
                            semester = sem
                        )
                check.save()
                messages.info(request, 'Pre-Registration Successful')
            except:
                return HttpResponseRedirect('/academic-procedures/main')

            return HttpResponseRedirect('/academic-procedures/main')
        except:
            return HttpResponseRedirect('/academic-procedures/main')
    else:
        return HttpResponseRedirect('/academic-procedures/main')



def get_student_registrtion_check(obj, sem):
    return StudentRegistrationCheck.objects.all().filter(student = obj, semester = sem).first()


def final_registration(request):
    if request.method == 'POST':
        if request.POST.get('type_reg') == "register" :
            try:
                current_user = get_object_or_404(User, username=request.POST.get('user'))
                current_user = ExtraInfo.objects.all().filter(user=current_user).first()
                current_user = Student.objects.all().filter(id=current_user.id).first()

                sem = request.POST.get('semester')

                values_length = 0
                values_length = len(request.POST.getlist('choice'))

                print('here it is')
                print(request.POST.get('mode'))
                print('nhi mila')
                mode = str(request.POST.get('mode'))
                transaction_id = str(request.POST.get('transaction_id'))


                for x in range(values_length):
                    for key, values in request.POST.lists():
                        if (key == 'choice'):
                                        p = FinalRegistrations(
                                            curr_id= get_object_or_404(Curriculum, curriculum_id = values[x]),
                                            semester=sem,
                                            student_id= current_user,
                                            batch = current_user.batch,
                                            verified = False
                                            )
                                        p.save()
                        else:
                            continue
                obj = FeePayment(
                    student_id = current_user,
                    semester = sem,
                    batch = current_user.batch,
                    mode = mode,
                    transaction_id = transaction_id
                    )
                obj.save()
                try:
                    StudentRegistrationCheck.objects.filter(student = current_user, semester = sem).update(final_registration_flag = True)
                    messages.info(request, 'Final-Registration Successful')
                except:
                    return HttpResponseRedirect('/academic-procedures/main')
                return HttpResponseRedirect('/academic-procedures/main')
            except:
                return HttpResponseRedirect('/academic-procedures/main')

        elif request.POST.get('type_reg') == "change_register" :
            try:
                current_user = get_object_or_404(User, username=request.POST.get('user'))
                current_user = ExtraInfo.objects.all().filter(user=current_user).first()
                current_user = Student.objects.all().filter(id=current_user.id).first()

                sem = request.POST.get('semester')

                FinalRegistrations.objects.filter(student_id = current_user, semester = sem).delete()

                count = request.POST.get('ct')
                count = int(count)
                for i in range(2, count+1):
                    i = str(i)
                    choice = "choice["+i+"]"
                    curr_id = get_object_or_404(Curriculum, curriculum_id = request.POST.get(choice))
                    
                    p = FinalRegistrations(
                        curr_id = curr_id,
                        semester = sem,
                        student_id = current_user,
                        batch = current_user.batch,
                        verified = False
                        )
                    p.save()
                try:
                    StudentRegistrationCheck.objects.filter(student = current_user, semester = sem).update(final_registration_flag = True)
                    messages.info(request, 'registered course change Successful')
                except:
                    return HttpResponseRedirect('/academic-procedures/main')

                return HttpResponseRedirect('/academic-procedures/main')
            except:
                return HttpResponseRedirect('/academic-procedures/main')
    else:
        return HttpResponseRedirect('/academic-procedures/main')


def get_cpi(id):
    obj =  Student.objects.get(id = id)
    return obj.cpi

def register(request):
    if request.method == 'POST':
        try:
            current_user = get_object_or_404(User, username=request.POST.get('user'))
            current_user = ExtraInfo.objects.all().filter(user=current_user).first()
            current_user = Student.objects.all().filter(id=current_user.id).first()

            values_length = 0
            values_length = len(request.POST.getlist('choice'))

            sem = request.POST.get('semester')

            for x in range(values_length):
                for key, values in request.POST.lists():
                    if (key == 'choice'):
                        try:
                            last_id = Register.objects.all().aggregate(Max('r_id'))
                            last_id = last_id['r_id__max']+1
                        except:
                            last_id = 1
                        curr_id = get_object_or_404(Curriculum, curriculum_id=values[x])
                        p = Register(
                            r_id=last_id,
                            curr_id=curr_id,
                            year=current_user.batch,
                            student_id=current_user,
                            semester=sem
                            )
                        p.save()
                    else:
                        continue
            messages.info(request, 'Pre-Registration Successful')
            return HttpResponseRedirect('/academic-procedures/main')
        except:
            return HttpResponseRedirect('/academic-procedures/main')
    else:
        return HttpResponseRedirect('/academic-procedures/main')


def drop_course(request):
    if request.method == 'POST':
        try:
            current_user = get_object_or_404(User, username=request.POST.get('user'))
            current_user = ExtraInfo.objects.all().filter(user=current_user).first()
            current_user = Student.objects.all().filter(id=current_user.id).first()

            values_length = 0
            values_length = len(request.POST.getlist('choice'))

            sem = request.POST.get('semester')

            for x in range(values_length):
                for key, values in request.POST.lists():
                    if (key == 'choice'):
                        curr_id = get_object_or_404(Curriculum, curriculum_id=values[x])
                        Register.objects.filter(curr_id =curr_id, student_id = current_user).delete()
                    else:
                        continue
            messages.info(request, 'Course Successfully Dropped')
            return HttpResponseRedirect('/academic-procedures/main')
        except:
            return HttpResponseRedirect('/academic-procedures/main')
    else:
        return HttpResponseRedirect('/academic-procedures/main')


def add_thesis(request):
    if request.method == 'POST':
        try:
            if(str(request.POST.get('by'))=="st"):
                thesis_topic = request.POST.get('thesis_topic')
                research_area = request.POST.get('research_area')

                supervisor_faculty = get_object_or_404(User, username = request.POST.get('supervisor'))
                supervisor_faculty = ExtraInfo.objects.get(user = supervisor_faculty)
                supervisor_faculty = Faculty.objects.get(id = supervisor_faculty)

                try:
                    co_supervisor_faculty = get_object_or_404(User, username = request.POST.get('co_supervisor'))
                    co_supervisor_faculty = ExtraInfo.objects.get(user = co_supervisor_faculty)
                    co_supervisor_faculty = Faculty.objects.get(id = co_supervisor_faculty) 
                except:
                    co_supervisor_faculty = None

                current_user = get_object_or_404(User, username=request.POST.get('user'))
                current_user = ExtraInfo.objects.all().filter(user=current_user).first()
                current_user = Student.objects.all().filter(id=current_user.id).first()

                try:
                    curr_id = request.POST.get('curr_id')
                    curr_id = Curriculum.objects.get(curriculum_id = curr_id)
                except:
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
                print(request.POST.get('approval'))

                member1 = get_object_or_404(User, username = request.POST.get('member1'))
                member1 = ExtraInfo.objects.get(user = member1)
                member1 = Faculty.objects.get(id = member1)

                member2 = get_object_or_404(User, username = request.POST.get('member2'))
                member2 = ExtraInfo.objects.get(user = member2)
                member2 = Faculty.objects.get(id = member2)

                try:
                    member3 = get_object_or_404(User, username = request.POST.get('member3'))
                    member3 = ExtraInfo.objects.get(user = member3)
                    member3 = Faculty.objects.get(id = member3)
                except:
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
                    print("ho gya")
                elif(request.POST.get('approval')=="no"):
                    obj.pending_supervisor = False
                    obj.member1 = member1
                    obj.member2 = member2
                    obj.member3 = member3
                    obj.approval_supervisor = False
                    obj.forwarded_to_hod = False
                    obj.pending_hod = False
                    obj.save()
                    print("nhi hua")
                else:
                    print("approval hi nhi aaya")
                return HttpResponseRedirect('/academic-procedures/main')
        except:
            return HttpResponseRedirect('/academic-procedures/main')
    else:
        return HttpResponseRedirect('/academic-procedures/main/')
    return HttpResponseRedirect('/academic-procedures/main/')



def get_add_course_options(branch, current_register):
    x = []
    for i in current_register:
        x.append(i)
    total_course = []
    for i in branch:
        if i not in x:
            total_course.append(i)
    return total_course


def get_added_course_count(current_register, final_register):
    x = 0
    y = 0
    for i in current_register:
        x = x+1
    for i in final_register:
        y =y+1
    return (x-y)


def get_dropped_courses_count(current_register, final_register):
    x = []
    y = 0
    for i in current_register:
        x.append(i)
    for i in final_register:
        if i.curr_id not in x:
            y = y + 1
        else:
            continue
    return y



def get_user_semester(roll_no, ug_flag, masters_flag, phd_flag):
    roll = str(roll_no)
    now = demo_date
    year, month = now.year, int(now.month)
    y = str(year)
    if(ug_flag):        
        roll = int(roll[:4])        
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
    year = int(roll[:4])
    courses = Curriculum.objects.all().filter(batch=(year))
    courses = courses.filter(sem = user_sem)
    courses = courses.filter(floated = True)
    course_list = []
    for course in courses:
        if branch.lower() == course.branch.lower() :
            course_list.append(course)
        elif course.branch.lower() == 'common':
            course_list.append(course)
    return course_list


def get_currently_registered_courses(id, user_sem):
    obj = Register.objects.all().filter(student_id=id, semester=user_sem)
    ans = []
    for i in obj:
        course = Curriculum.objects.get(curriculum_id=i.curr_id.curriculum_id)
        ans.append(course)
    return ans


def get_current_credits(obj):
    credits = 0
    for i in obj:
        credits = credits + i.credits
    return credits


def get_added_courses_list(currently_registered_courses, final_registered_courses):
    x = []
    y = []
    for i in currently_registered_courses:
        x.append(i)
    for i in final_registered_courses:
        if i.curr_id not in x:
            y.append(i.curr_id)
    return y


def get_faculty_list():
    f1 = HoldsDesignation.objects.filter(designation=Designation.objects.get(name = "Assistant Professor"))
    f2 = HoldsDesignation.objects.filter(designation=Designation.objects.get(name = "Professor"))
    f3 = HoldsDesignation.objects.filter(designation=Designation.objects.get(name = "Associate Professor"))

    faculty = list(chain(f1,f2,f3))
    faculty_list = []
    for i in faculty:
        faculty_list.append(i)
    return faculty_list


def get_thesis_flag(student):
    obj = ThesisTopicProcess.objects.all().filter(student_id = student)
    if(obj):
        return True
    else:
        return False



@login_required(login_url='/accounts/login')
def acad_person(request):

    current_user = get_object_or_404(User, username=request.user.username)
    print(request.user.username)

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()


    if str(des.designation) == "student":
       return HttpResponseRedirect('/academic-procedures/main/')

    elif str(des.designation) == "Associate Professor" :
        return HttpResponseRedirect('/academic-procedures/main/')

    elif str(request.user) == "acadadmin" :


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
        change_queries = BranchChange.objects.all()

        course_verification_date = get_course_verification_date_eligibilty(demo_date.date())
        print("get_course_verification_date_eligibilty")
        print(course_verification_date)


        initial_branch = []
        change_branch = []
        available_seats = []
        applied_by = []
        cpi = []

        for i in change_queries:
            applied_by.append(i.user.id)
            change_branch.append(i.branches.name)
            students = Student.objects.all().filter(id=i.user.id).first()
            user_branch = ExtraInfo.objects.all().filter(id=students.id.id).first()
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
        # print(lists)
        if len(initial_branch) > 0:
            tag = True
        context = {
            'list': lists,
            'total': len(initial_branch),
            'tag': tag
        }
        # print(context)

        submitted_course_list = []
        obj_list = MarkSubmissionCheck.objects.all().filter(verified= False,submitted = True)
        for i in obj_list:
            if int(i.curr_id.batch)+int(i.curr_id.sem)/2 == int(demo_date.year):
                submitted_course_list.append(i.curr_id)
            else:
                continue
        print(submitted_course_list)
        # submitted_course_list = SemesterMarks.objects.all().filter(curr_id__in = submitted_course_list)
        # print(submitted_course_list)



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
    change_queries = BranchChange.objects.all()

    course_verification_date = get_course_verification_date_eligibilty(demo_date.date())
    print("get_course_verification_date_eligibilty")
    print(course_verification_date)


    initial_branch = []
    change_branch = []
    available_seats = []
    applied_by = []
    cpi = []

    for i in change_queries:
        applied_by.append(i.user.id)
        change_branch.append(i.branches.name)
        students = Student.objects.all().filter(id=i.user.id).first()
        user_branch = ExtraInfo.objects.all().filter(id=students.id.id).first()
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
    # print(lists)
    if len(initial_branch) > 0:
        tag = True
    context = {
        'list': lists,
        'total': len(initial_branch),
        'tag': tag
    }
    # print(context)

    submitted_course_list = []
    obj_list = MarkSubmissionCheck.objects.all().filter(verified= False,submitted = True)
    for i in obj_list:
        if int(i.curr_id.batch)+int(i.curr_id.sem)/2 == int(demo_date.year):
            submitted_course_list.append(i.curr_id)
        else:
            continue
    print(submitted_course_list)
    # submitted_course_list = SemesterMarks.objects.all().filter(curr_id__in = submitted_course_list)
    # print(submitted_course_list)



    batch_grade_data = get_batch_grade_verification_data(result_year)

    return {
            'context': context,
            'lists': lists,
            'date': date,
            'query_option1': query_option1,
            'query_option2': query_option2,
            'course_verification_date' : course_verification_date,
            'submitted_course_list' : submitted_course_list,
            'result_year' : result_year,
            'batch_grade_data' : batch_grade_data
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
    print(request.POST.get('id'))
    i = int(request.POST.get('id'))
    year = get_batch_all()
    print(year[i-1])

    acad = get_object_or_404(User, username="acadadmin")
    print(acad.username)
    student_list = Student.objects.all().filter(batch = year[i-1])

    # for obj in student_list:
    #     print(obj.id.user.username)
    #     academics_module_notif(acad, obj.id.user, 'result_announced')


    courses_list = Curriculum.objects.all().filter(batch = year[i-1])
    print(courses_list)
    for obj in courses_list:
        try :
            o = MarkSubmissionCheck.objects.get(curr_id = obj)
            o.announced = True
            o.save()
        except:
            continue

    return JsonResponse({'status': 'success', 'message': 'Successfully Accepted'})



def get_batch_grade_verification_data(list):
    print("check kre")
    print(list)

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

    print(list[0])
    c = Curriculum.objects.all().filter(batch = list[0]).filter(floated = True)
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
            obj_sem = MarkSubmissionCheck.objects.get(curr_id = i)
            if obj_sem:
                semester_marks.append(obj_sem)
            else:
                continue
        except:
            continue
    print(c)

    c = Curriculum.objects.all().filter(batch = list[1]).filter(floated = True)
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
            obj_sem = MarkSubmissionCheck.objects.get(curr_id = i)
            if obj_sem:
                semester_marks.append(obj_sem)
            else:
                continue
        except:
            continue
    print(c)

    c = Curriculum.objects.all().filter(batch = list[2]).filter(floated = True)
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
            obj_sem = MarkSubmissionCheck.objects.get(curr_id = i)
            if obj_sem:
                semester_marks.append(obj_sem)
            else:
                continue
        except:
            continue
    print(c)

    c = Curriculum.objects.all().filter(batch = list[3]).filter(floated = True)
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
            obj_sem = MarkSubmissionCheck.objects.get(curr_id = i)
            if obj_sem:
                semester_marks.append(obj_sem)
            else:
                continue
        except:
            continue
    print(c)
    print(semester_marks)

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

@login_required(login_url='/accounts/login')
def student_list(request):
    if(request.POST):
        batch = request.POST["batch"]
        branch = request.POST["branch"]
            # year = datetime.datetime.now().year
        # month = datetime.datetime.now().month

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


        
        student_objects = Student.objects.all().filter(batch = int(batch))
        dep_objects = DepartmentInfo.objects.get(name = str(branch))
        branch_objects = ExtraInfo.objects.all().filter(department = dep_objects)

        student_obj = []
        branch_obj = []

        for i in branch_objects:
            branch_obj.append(i)

        for i in student_objects:
            if i.id in branch_obj:
                student_obj.append(i)
            else:
                continue

        student = [[]]
        for obj in student_obj:
            sem=1
            roll_no = str(obj.id)
            if obj.programme.upper() == "PH.D":
                sem = get_user_semester(roll_no,False,False,True)
            elif obj.programme.upper() == "M.TECH":
                sem = get_user_semester(roll_no,False,True,False)
            elif obj.programme.upper() == "B.TECH":
                sem = get_user_semester(roll_no,True,False,False)
            try:
                reg = StudentRegistrationCheck.objects.all().filter(student = obj, semester = sem).first()
                pay = FeePayment.objects.all().filter(student_id = obj, semester = sem).first()
                final = FinalRegistrations.objects.all().filter(student_id = obj, semester = sem,verified = False)
            except:
                reg = None
                pay = None
                final = None
            if reg:
                if reg.final_registration_flag == True and final:
                        student.append((obj,pay,final))
                else:
                    continue
            else:
                continue

        print(student)

        html = render_to_string('academic_procedures/student_table.html',
                                {'student': student}, request)

        maindict = {'date': date,
                    'query_option1': batch_year_option,
                    'query_option2': branch_option,
                    'html': html,
                    'queryflag': queryflag}
        obj = json.dumps(maindict)
        return HttpResponse(obj, content_type='application/json')


def process_verification_request(request):
    if request.is_ajax():
        return verify_registration(request)
    return JsonResponse({'status': 'Failed'}, status=400)

@transaction.atomic
def verify_registration(request):
    if request.POST.get('status_req') == "accept" :
        roll_no = request.POST.get('roll')
        print("here comes the roll_no")
        print(roll_no)
        print(request.POST.get('status_req'))
        try:
            last_id = Register.objects.all().aggregate(Max('r_id'))
            last_id = last_id['r_id__max']+1
        except:
            last_id = 1

        student_id = Student.objects.get(id = str(roll_no))
        print(student_id)

        sem=1
        if student_id.programme.upper() == "PH.D":
            sem = get_user_semester(roll_no,False,False,True)
        elif student_id.programme.upper() == "M.TECH":
            sem = get_user_semester(roll_no,False,True,False)
        elif student_id.programme.upper() == "B.TECH":
            sem = get_user_semester(roll_no,True,False,False)

        final_register_list = FinalRegistrations.objects.all().filter(student_id = student_id)
        final_register_list = final_register_list.filter(semester = sem)
        final_register_list = final_register_list.filter(verified = False)
        print(final_register_list)

        with transaction.atomic():
            for obj in final_register_list:
                try:
                    last_id = Register.objects.all().aggregate(Max('r_id'))
                    last_id = last_id['r_id__max']+1
                except:
                    last_id = 1
                p = Register(
                    r_id=last_id,
                    curr_id=obj.curr_id,
                    year=obj.batch,
                    student_id=student_id,
                    semester=sem
                    )
                p.save()
                o = FinalRegistrations.objects.filter(id= obj.id).update(verified = True)
            academics_module_notif(request.user, student_id.id.user, 'registration_approved')
            return JsonResponse({'status': 'success', 'message': 'Successfully Accepted'})
    elif request.POST.get('status_req') == "reject" :
        roll_no = request.POST.get('roll')
        print("here comes the roll_no")
        print(roll_no)
        print(request.POST.get('status_req'))

        student_id = Student.objects.get(id = str(roll_no))
        print(student_id)

        sem=1
        if student_id.programme.upper() == "PH.D":
            sem = get_user_semester(roll_no,False,False,True)
        elif student_id.programme.upper() == "M.TECH":
            sem = get_user_semester(roll_no,False,True,False)
        elif student_id.programme.upper() == "B.TECH":
            sem = get_user_semester(roll_no,True,False,False)


        with transaction.atomic():
            academicadmin = get_object_or_404(User, username = "acadadmin")
            FinalRegistrations.objects.filter(student_id = student_id, semester = sem, verified = False).delete()
            StudentRegistrationCheck.objects.filter(student = student_id, semester = sem).update(final_registration_flag = False)
            FeePayment.objects.filter(student_id = student_id, semester = sem).delete()
            academics_module_notif(academicadmin, student_id.id.user, 'registration_declined_fee')
            return JsonResponse({'status': 'success', 'message': 'Successfully Accepted'})




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

            print(roll)
            print(course1)

            roll = str(roll)

            student_id = get_object_or_404(User, username=request.POST.get('roll'))
            student_id = ExtraInfo.objects.all().filter(user=student_id).first()
            student_id = Student.objects.all().filter(id=student_id.id).first()

            course1 = Curriculum.objects.get(curriculum_id = request.POST.get('course1'))
            print(course1.course_code)
            course2 = Curriculum.objects.get(curriculum_id = request.POST.get('course2'))
            course3 = Curriculum.objects.get(curriculum_id = request.POST.get('course3'))
            course4 = Curriculum.objects.get(curriculum_id = request.POST.get('course4'))

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
        except:
            return HttpResponseRedirect('/academic-procedures/main')
    else:
        return HttpResponseRedirect('/academic-procedures/main')




def course_marks_data(request):
    try:
        curriculum_id = request.POST.get('curriculum_id')
        course = Curriculum.objects.get(curriculum_id = curriculum_id)
        student_list = Register.objects.all().filter(curr_id = course)
        # print("shurru")
        for obj in student_list:
            o = SemesterMarks.objects.all().filter(student_id = obj.student_id).filter(curr_id = course).first()
            # print(o)
            if o :
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
                p.save()

        enrolled_student_list = SemesterMarks.objects.all().filter(curr_id = course)
        # print("khatam")
        grade_submission_date_eligibility = False
        try :
            d = Calendar.objects.get(description = "grade submission date")
            if demo_date.date() >= d.from_date and demo_date.date() <= d.to_date :
                grade_submission_date_eligibility = True
        except:
            grade_submission_date_eligibility = False
        data = render_to_string('academic_procedures/course_marks_data.html',
                                {'enrolled_student_list' : enrolled_student_list,
                                'course' : course,
                                'grade_submission_date_eligibility' : grade_submission_date_eligibility}, request)
        obj = json.dumps({'data' : data})
        return HttpResponse(obj, content_type = 'application/json')
    except:
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
        except:
            grade = None
        messages.info(request, ' Successful')

        values_length = len(request.POST.getlist('user'))


        curr_id = Curriculum.objects.get(curriculum_id = request.POST.get('curriculum_id'))
        print(curr_id)
        print("submit")
        print(request.POST.get('final_submit'))

        for x in range(values_length):

            student_id = get_object_or_404(User, username = user[x])
            student_id = ExtraInfo.objects.get(id = student_id)
            student_id = Student.objects.get(id = student_id)
            print(student_id)

            if grade:
                g = grade[x]
            else :
                g = None

            print('grade ke baad')
            st_existing = SemesterMarks.objects.all().filter(student_id = student_id).filter(curr_id = curr_id).first()
            print(st_existing.student_id)

            if st_existing :
                st_existing.q1 = q1[x]
                st_existing.mid_term = mid[x]
                st_existing.q2 = q2[x]
                st_existing.end_term = end[x]
                st_existing.other = other[x]
                st_existing.grade = g
                st_existing.save()
                print("update hua")
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
                    o_sub = MarkSubmissionCheck.objects.get(curr_id = curr_id)
                except:
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
                    sub_obj = MarkSubmissionCheck.objects.get(curr_id = curr_id)
                except:
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
                print("nahi chala")
        print("khatam")
        return HttpResponseRedirect('/academic-procedures/main')
    except:
        return HttpResponseRedirect('/academic-procedures/main')




def verify_course_marks_data(request):
    try:
        curriculum_id = request.POST.get('curriculum_id')
        course = Curriculum.objects.get(curriculum_id = curriculum_id)


        enrolled_student_list = SemesterMarks.objects.all().filter(curr_id = course)

        grade_verification_date_eligibility = False
        try :
            d = Calendar.objects.get(description = "grade verification date")
            if demo_date.date() >= d.from_date and demo_date.date() <= d.to_date :
                grade_verification_date_eligibility = True
        except:
            grade_verification_date_eligibility = False

        data = render_to_string('academic_procedures/verify_course_marks_data.html',
                                {'enrolled_student_list' : enrolled_student_list,
                                'course' : course,
                                'grade_verification_date_eligibility' : grade_verification_date_eligibility}, request)
        obj = json.dumps({'data' : data})
        return HttpResponse(obj, content_type = 'application/json')
    except:
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
        curr_id = Curriculum.objects.get(curriculum_id = request.POST.get('curriculum_id'))

        grade = request.POST.getlist('grade')

        values_length = len(request.POST.getlist('user'))
        for x in range(values_length):
            student_id = get_object_or_404(User, username = user[x])
            student_id = ExtraInfo.objects.get(id = student_id)
            student_id = Student.objects.get(id = student_id)
            if grade:
                g = grade[x]
            else :
                g = None

            st_existing = SemesterMarks.objects.all().filter(student_id = student_id).filter(curr_id = curr_id).first()

            st_existing.grade = g
            st_existing.save()
            verified_marks_students.append([student_id,g])   
        verified_marks_students_curr = curr_id


        obj = MarkSubmissionCheck.objects.get(curr_id = curr_id)
        obj.verified = True
        obj.save()
        return HttpResponseRedirect('/aims/')
    except:
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
    instructor = Curriculum_Instructor.objects.all().filter(curriculum_id = verified_marks_students_curr).first()
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
    print(programme)

    student_list = []
    branch_list = []
    result_list = [[]]   
    curriculum_list = []

    if programme == "":
        return HttpResponse("please insert programme")
    student_obj = Student.objects.all().filter(programme = programme)
    print(student_obj)

    if batch == "":
        return HttpResponse("please insert batch")
    else:
        student_obj = student_obj.filter(batch = int(batch))
        print(student_obj)
    
    if branch == "" :
        return HttpResponse("please insert branch")
    else :
        dep_objects = DepartmentInfo.objects.get(name = str(branch))
        branch_objects = ExtraInfo.objects.all().filter(department = dep_objects)

        for i in branch_objects:
            branch_list.append(i)

        for i in student_obj:
            if i.id in branch_list:
                student_list.append(i)
            else:
                continue



    curriculum_obj = Curriculum.objects.all().filter(batch = int(batch)).filter(branch = str(branch)).filter(programme = programme)
    curriculum_obj_common = Curriculum.objects.all().filter(batch = int(batch)).filter(branch = 'Common').filter(programme = programme)

    for i in curriculum_obj:
        curriculum_list.append(i)
    for i in curriculum_obj_common:
        curriculum_list.append(i)

    for i in student_list :
        x = []
        x.append(i.id.user.username)
        x.append(i.id.user.first_name+" "+i.id.user.last_name)
        for j in curriculum_list :
            grade_obj = SemesterMarks.objects.all().filter(curr_id = j).filter(student_id = i).first()
            if grade_obj :
                x.append(grade_obj.grade)
            else :
                x.append("-")
        spi = get_spi(curriculum_list ,x)
        x.append(spi)
        result_list.append(x)


    print(result_list)

    context = {'batch' : batch,
                'branch' : branch,
                'programme' : programme,
                'course_list' : curriculum_list,
                'result_list' : result_list}
    print(context)
    print(student_list)
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
    student_obj = Student.objects.all().filter(programme = programme)
    print(student_obj)

    if batch == "":
        return HttpResponse("please insert batch")
    else:
        student_obj = student_obj.filter(batch = int(batch))
        print(student_obj)
    
    if branch == "" :
        return HttpResponse("please insert branch")
    else :
        dep_objects = DepartmentInfo.objects.get(name = str(branch))
        branch_objects = ExtraInfo.objects.all().filter(department = dep_objects)

        for i in branch_objects:
            branch_list.append(i)

        for i in student_obj:
            if i.id in branch_list:
                student_list.append(i)
            else:
                continue



    curriculum_obj = Curriculum.objects.all().filter(batch = int(batch)).filter(branch = str(branch)).filter(programme = programme)
    curriculum_obj_common = Curriculum.objects.all().filter(batch = int(batch)).filter(branch = 'Common').filter(programme = programme)

    for i in curriculum_obj:
        curriculum_list.append(i)
    for i in curriculum_obj_common:
        curriculum_list.append(i)

    for i in student_list :
        x = []
        x.append(i.id.user.username)
        x.append(i.id.user.first_name+" "+i.id.user.last_name)
        for j in curriculum_list :
            grade_obj = SemesterMarks.objects.all().filter(curr_id = j).filter(student_id = i).first()
            if grade_obj :
                x.append(grade_obj.grade)
            else :
                x.append("-")
        spi = get_spi(curriculum_list ,x)
        x.append(spi)
        result_list.append(x)


    print(result_list)

    context = {'batch' : batch,
                'branch' : branch,
                'programme' : programme,
                'course_list' : curriculum_list,
                'result_list' : result_list}
    print(context)
    print(student_list)
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
    print(y)

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
        print("andar aaya")

        manual_grade_xsl=request.FILES['manual_grade_xsl']
        print(manual_grade_xsl)
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
        print(course_code)
        print(course_name)
        print(instructor)
        print(batch)
        print(sem)
        print(branch)
        print(programme)

        curriculum_obj = Curriculum.objects.all().filter(course_code = course_code).filter(batch = batch).filter(programme = programme).first()
        
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
        curriculum_obj = Curriculum.objects.all().filter(course_code = course_code).filter(batch = batch).filter(programme = programme).first()

        marks_check_obj = MarkSubmissionCheck.objects.all().filter(curr_id = curriculum_obj).first()
        if marks_check_obj :
            marks_check_obj.submitted = True
            marks_check_obj.verified = True
            marks_check_obj.save()
        elif not marks_check_obj :
            marks_check_obj_create = MarkSubmissionCheck(
                curr_id = curriculum_obj,
                submitted = True,
                verified = True,
                announced = False)
            marks_check_obj_create.save()

        for i in range(11,sheet.nrows):
            roll = str(int(sheet.cell(i,0).value))
            user = get_object_or_404(User, username = roll)
            extrainfo = ExtraInfo.objects.get(user = user)
            dep_objects = DepartmentInfo.objects.get(name = str(branch))
            extrainfo.department = dep_objects
            extrainfo.save()
            extrainfo = ExtraInfo.objects.get(user = user)
            student_obj = Student.objects.get(id = extrainfo)


            student_obj.programme = programme
            student_obj.batch = batch
            student_obj.category = 'GEN'
            student_obj.save()

            student_obj = Student.objects.get(id = extrainfo)
            register_obj = Register.objects.all().filter(curr_id = curriculum_obj, student_id = student_obj).first()
            if not register_obj:
                try:
                    last_id = Register.objects.all().aggregate(Max('r_id'))
                    last_id = last_id['r_id__max']+1
                except:
                    last_id = 1
                register_obj_create = Register(
                    r_id = last_id,
                    curr_id = curriculum_obj,
                    year = batch,
                    student_id = student_obj,
                    semester = sem)
                register_obj_create.save()
            register_obj = Register.objects.all().filter(curr_id = curriculum_obj, student_id = student_obj).first()

            st_existing = SemesterMarks.objects.all().filter(student_id = student_obj).filter(curr_id = curriculum_obj).first()
            if st_existing :
                st_existing.grade = str(sheet.cell(i,2).value)
                st_existing.save()
            else :
                p = SemesterMarks(
                        student_id = student_obj,
                        q1 = 0.0,
                        mid_term = 0.0,
                        q2 = 0.0,
                        end_term = 0.0,
                        other = 0.0,
                        grade = str(sheet.cell(i,2).value),
                        curr_id = curriculum_obj
                     )
                p.save()

    return HttpResponseRedirect('/aims/')
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
    st_list = Student.objects.all()
    for i in st_list :
        roll = i.id.user.username
        roll = str(roll)
        if i.programme.upper() == "B.DES" or i.programme.upper() == "B.TECH":
            print(roll)
            batch = int(roll[:4])
            print(batch)
            i.batch = batch
            i.save()
        elif i.programme.upper() == "M.DES" or i.programme.upper() == "M.TECH" or i.programme.upper() == "PH.D":
            print(roll)
            batch = int('20'+roll[:2])
            print(batch)
            i.batch = batch
            i.save()
    return render(request,'../templates/academic_procedures/test.html',{})

def test_ret(request):
    try:
        data = render_to_string('academic_procedures/test_render.html',
                                {}, request)
        obj = json.dumps({'d' : data})
        return HttpResponse(obj, content_type = 'application/json')
    except:
        return HttpResponseRedirect('/academic-procedures/main')



