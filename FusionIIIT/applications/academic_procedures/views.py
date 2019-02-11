import datetime
import json
from itertools import chain

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Max
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string

# from applications.academic_procedures.models import Register
from applications.academic_information.models import Calendar, Course, Student
from applications.globals.models import (DepartmentInfo, Designation,
                                         ExtraInfo, Faculty, HoldsDesignation)

from .models import (BranchChange, CoursesMtech, FinalRegistrations,
                     MinimumCredits, Register, Thesis)


@login_required(login_url='/accounts/login')
def academic_procedures_redirect(request):
    return HttpResponseRedirect('/academic-procedures/main')


@login_required(login_url='/accounts/login')
def main(request):
    return HttpResponseRedirect('/academic-procedures/main/')


@login_required(login_url='/accounts/login')
def academic_procedures(request):
    '''
        This function does the following things:
        1. Checks whether the User is Academic Admin or not.
        2. Gets the current semster of the Student.
        3. Gets the pre-registration and final-registration date.
        4. Gets add/drop course date.
        5. Gets the current user's branch.
        6. Get all the courses related to the user's branch.
        7. Checks whether Final Registration is done or not.
        8. Brange change is implemented here.

        @param:
                request - trivial.

        @variables:
                current_user - details of the current user.
                extraInfo_user - gets the user details from the extrainfo model.
                desig_id - Finds the Acad admin whose designation is "Upper Division Clerk"
                acadadmin - acad-admin's data required to process.
                student - Details of the currently logged in user.
                user_sem - Curent semester of the current user.
                registered_or_not - Checks whether the logged in student has registered or not.
                pre_registration_date - Gets the Pre-registration Date form the Academic Calendar.
                minimum_credit - Minimum Credits required to apply for branch change.
                branch_courses - Gets the current semester courses branchwise.
                add_courses - Courses for the next semester for which the student can apply.
    '''
    current_user = get_object_or_404(User, username=request.user.username)
    print(current_user)
    user_details = ExtraInfo.objects.all().filter(user=current_user).first()
    print(user_details)
    # user_type = Designation.objects.all().filter(name=user_details.designation).first()
    # Academics Admin Check

    desig_id = Designation.objects.all().filter(name='Upper Division Clerk')
    print ("yaha se")
    print (desig_id)
    temp = HoldsDesignation.objects.all().filter(designation = desig_id).first()
    acadadmin = temp.working
    print (temp)
    print(user_details)
    k = str(user_details).split()
    print("Temp variable", k)

    final_user = k[2]
    print ("Final User", final_user)

    print (str(acadadmin) == str(final_user))
    # print(acadadmin, user_details)
    # IF user is academic admin
    if (str(acadadmin) == str(final_user)):
        return HttpResponseRedirect('/aims')

    obj1 = Student.objects.all().filter(id=user_details.id)
    print (obj1)
    count = 0
    for i in obj1:
        count += 1
    if(count == 0):
            return HttpResponseRedirect('/dashboard')
    pgflag = 0
    for i in obj1:
        if(i.programme[0] == "M" or i.programme[0] == "P"):
            pgflag = 1

    change_branch_flag = 1

    student = Student.objects.all().filter(id=user_details.id).first()
    # Fuction Call to get the current semster of the Student
    user_sem = get_user_semester(user_details.id)
    # print(student.programme)
    if student.programme == 'PhD':
        return HttpResponseRedirect('/academic-procedures/PhD/')
    registered_or_not = Register.objects.all().filter(student_id=student, semester = (user_sem + 1)).first()
    # Get the pre-registration and final-registration date
    regflag = True
    if(registered_or_not):
        regflag = True
    else:
        regflag = False
    pre_registration_date = Calendar.objects.all().filter(description="Pre Registration").first()
    final_registration_date = Calendar.objects.all().filter(description="Physical Reporting at the Institute").first()
    # print("Pre-Registration", pre_registration_date, final_registration_date)
    prd_start_date = pre_registration_date.from_date
    prd_end_date = pre_registration_date.to_date
    frd_start_date = final_registration_date.from_date
    frd_end_date   = final_registration_date.to_date
    prd, frd = False, False
    current_date = datetime.datetime.now().date()
    if current_date>=prd_start_date and current_date<=prd_end_date:
        prd = True
    if current_date>=frd_start_date and current_date<=frd_end_date:
        frd = True
    # print(prd, frd)
    # Get add/drop course date
    add_drop_course = Calendar.objects.all().filter(description="Last Date for Adding/Dropping of course").first()
    print(add_drop_course)
    adc_start_date = add_drop_course.from_date
    adc_end_date = add_drop_course.to_date
    adc_flag = False
    if current_date>=adc_start_date and current_date<=adc_end_date:
        adc_flag = True
    # Function call to get the current user's branch
    user_branch = get_user_branch(user_details)
    get_courses = Course.objects.all().filter(sem=(user_sem+1), optional=False)
    get_sel_courses = Course.objects.all().filter(sem=(user_sem+1), optional=True, acad_selection=True)
    # get_courses = get_courses + get_sel_courses
    get_courses = list(chain(get_courses, get_sel_courses))
    # Fucntion Call to get the courses related to the branch
    branch_courses = get_branch_courses(get_courses, user_branch)
    calendar = Calendar.objects.all()
    year = datetime.datetime.now().year
    yearr = str(year) + "-" + str(year+1)
    details = {
            'current_user': current_user,
            'year': yearr,
            'user_sem': user_sem,
            'check_pre_register': registered_or_not,
            'regflag':regflag,
            }
    final_register = Register.objects.all().filter(student_id=user_details.id)
    final_register_count = FinalRegistrations.objects.all().filter(
                                                student_id=user_details.id).first()
    add_course = get_add_course(branch_courses, final_register)
    # print("branchh Cousr",branch_courses, final_register)
    show_list = get_course_to_show(branch_courses, final_register)
    # print(show_list)
    pre_register_found = Register.objects.all().filter(student_id=user_details.id, semester=(user_sem+1)).first()
    pre_register = True
    # Final Registration Found or not
    final_register_found = FinalRegistrations.objects.all().filter(student_id=user_details.id).first()
    final_register_1 = True
    if final_register_found is None:
        final_register_1 = False
    else:
        final_register_1 = True
    currently_registered = get_currently_registered_courses(user_details.id, user_sem)
    if (pre_register_found):
        pre_register = True
    else:
        pre_register = False

    # print(pre_register_found)
    # Branch Change Code starts here
    change_branch = apply_branch_change(request)
    # ENDCHANGE BY ANURAAG
    show_list = get_course_to_show(branch_courses, final_register)
    # print(show_list)
    # pre_register_found = Register.objects.all().filter(student_id=user_details.id).first()
    # pre_register = True
    # # print(final_register)
    # if (pre_register_found) is None:
    #     pre_register = False
    # else:
    #     pre_register = True
    # # print(pre_register_found)

    if(pgflag == 1):
        specialization = ""
        user_sem = 2
        for i in obj1:
            if(i.programme[0] == "M" or i.programme[0] == "P"):
                change_branch_flag = 0
            specialization = i.specialization
        branch_courses = get_pg_course(user_sem, specialization)
        add_courses = get_pg_course(user_sem, specialization)
        # print("karde")
        show_list = get_course_to_show_pg(add_courses, final_register)

    details['change_branch_flag'] = change_branch_flag
    # Get the Minimum Credits
    minimum_credit = MinimumCredits.objects.all().filter(semester=(user_sem+1)).first()

    return render(
                  request, '../templates/academic_procedures/academic.html',
                  {'details': details,
                   'calendar': calendar,
                   'currently_registered': currently_registered,
                   'courses_list': branch_courses,
                   'final_register': final_register,
                   'final_count': final_register_count,
                   'change_branch': change_branch,
                   'add_course': add_course,
                   'show_list': show_list,
                   'pre_register': pre_register,
                   'prd': prd,
                   'frd': frd,
                   'final_r': final_register_1,
                   'adc_flag': adc_flag,
                   'mincr': minimum_credit,}
        )


def get_currently_registered_courses(user_details, user_sem):
    '''
        This function fetches the currently registered courses from the database and store
        them into list ans.
        @param:
                user_details - Has the details of the logged in user(student).
                user_sem - Has the semester of the user(student).

        @variables:
                obj1 - Gets all the registered courses of the logged in user(student).
                ans - has the registered courses details of the logged in user.
    '''
    obj1 = Register.objects.all().filter(student_id=user_details, semester=user_sem)
    # obj2 = Register.objects.all()
    # ans2 = []
    # for i in obj2:
    #    for j in obj1:
    #        if(j.course_id==i.course_name);
    #            ans2.append(j)
    ans = []
    for i in obj1:
        obj2 = Course.objects.get(course_name=i.course_id)
        ans.append(obj2)
    # print(ans)
    return ans


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


def get_course_to_show(branch, final_register):
    '''
        This function fetches the UG courses from the database and store them into list x.
        @param:
                branch - Branch of the user.
                final_register - finally registered courses.

        @variables:
                total_course - The courses that are not being finally registered.
    '''
    x = []
    for i in final_register:
        x.append(i.course_id)
    total_course = []
    for i in branch:
        if i not in x:
            total_course.append(i)
    return total_course


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


@login_required(login_url='/accounts/login')
def drop_course(request):
    '''
        This function drops the course that were added after pre-registration.
        @param:
                request - trivial

        @variables:
                c_id - course id of the dropped course.
                user_id - logged in user ID.
                instance - Deletes the selected to be dropped course and deletes it from the database.
    '''
    # current_user = get_object_or_404(User, username=request.user.username)
    if request.method == 'POST':
        try:
            c_id = request.POST.getlist('course_id')
            user_id = request.POST.getlist('user')
            for i in range(len(c_id)):
                cour_id = Course.objects.all().filter(course_id=c_id[i]).first()
                s_id = ExtraInfo.objects.all().filter(id=user_id[i][:7]).first()
                s_id = Student.objects.all().filter(id=s_id)
                instance = Register.objects.filter(course_id=cour_id).filter(student_id=s_id)
                instance = instance[0]
                # print('ind=s', instance)
                instance.delete()
            messages.info(request, 'Successfully Dropped')
            return HttpResponseRedirect('/academic-procedures/main')
        except:
            return HttpResponseRedirect('/academic-procedures/main')
    else:
        messages.info(request, 'Problem in dropping')
        return HttpResponseRedirect('/academic-procedures/main')


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


# function to get user semester
def get_user_semester(roll_no):
    '''
        This function is used to get the current semester of the user.
        @param:
                roll_no - roll number of the logged in user.

        @variables:
                roll - roll number of the logged in user.
                now - today's date
                year - current year.
                month - current month
                user_year - user's academic year.
                sem - logged in user's semester.
    '''
    roll = str(roll_no)
    roll = int(roll[:4])
    now = datetime.datetime.now()
    year, month = now.year, int(now.month)
    user_year = int(year) - roll
    sem = 'odd'
    if month >= 7 and month <= 12:
        sem = 'odd'
    else:
        sem = 'even'
    if sem == 'odd':
        return user_year * 2 + 1
    else:
        return user_year * 2


def get_branch_courses(courses, branch):
    '''
        This function is used to get the branch wise courses and return them into course_list.
        @param:
                courses - all the branchwise courses.
                branch - user's branch

        @variables:
                course_list - all the courses of the current(logged in) user.
    '''
    course_list = []
    # print(branch)
    for course in courses:
        # print (course.course_id)
        if branch[:2].lower() == course.course_id[:2].lower() and len(course.course_id) >= 5:
            course_list.append(course)
        elif branch[:2].lower() == course.course_id[:2].lower() and len(course.course_id) > 5:
            course_list.append(course)
        elif (str(course.course_id[:2]) == "HS" or str(course.course_id[:2]) == "ES"
                or str(course.course_id[:2]) == "MN" or str(course.course_id[:2]) == "NS"
                or str(course.course_id[:2]) == "DS"):
            course_list.append(course)
    return course_list


def get_user_branch(user_details):
    '''
        This function retuns the branch of the user.
        @param:
                user_details - all the details of the logged in user.

    '''
    return user_details.department.name


def register(request):
    '''
        This function is used to pre-register the courses of the logged in user the entry in the database is store by variable list 'p'.
        @param:
                request - trivial

        @variables:
                current_user - logged in user's details.
                values_length - selected courses by the user.
                sem - user's next semester.
                course_id - details of the selected courses.
                student_id - details of the current user.
                p - object to save data in the database.
    '''
    if request.method == 'POST':
        try:
            # print(request.POST)
            current_user = get_object_or_404(User, username=request.POST.get('user'))
            current_user = ExtraInfo.objects.all().filter(user=current_user).first()
            current_user = Student.objects.all().filter(id=current_user.id).first()
            # current_user = get_object_or_404(ExtraInfo, user=current_user.username)
            values_length = 0
            values_length = len(request.POST.getlist('choice'))
            # Get the semester for the registration
            sem = request.POST.get('semester')

            for x in range(values_length):
                for key, values in request.POST.lists():
                    if (key == 'choice'):
                        last_id = Register.objects.all().aggregate(Max('r_id'))

                        try:
                            last_id = last_id['r_id__max']+1
                        except:
                            # print("nahi hua")
                            last_id = 1
                        course_id = get_object_or_404(Course, course_id=values[x])
                        p = Register(
                            r_id=last_id,
                            course_id=course_id,
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
        # print('not okay')
        return HttpResponseRedirect('/academic-procedures/main')


def final_register(request):
    '''
        This function is used to register finally the courses of the logged in user the entry in the database is store by variable list 'p'.
        @param:
                request - trivial

        @variables:
                current_user - details of the current user.
                extraInfo_user - gets the user details from the extrainfo model.
                user_sem - user's semester
                p - object to save data in the database.
    '''
    if request.method == 'POST':
        current_user = get_object_or_404(User, username=request.user.username)
        extraInfo_user = ExtraInfo.objects.all().filter(user=current_user).first()
        current_user = Student.objects.all().filter(id=extraInfo_user.id).first()
        # Fuction Call to get the current semster of the Student
        user_sem = get_user_semester(extraInfo_user.id)
        p = FinalRegistrations(
            reg_id=extraInfo_user,
            semester=user_sem+1,
            student_id=current_user,
            registration=True
            )
        p.save()
        messages.info(request, 'Registration Successful')
    return HttpResponseRedirect('/academic-procedures/main')


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

    semester = get_user_semester(extraInfo_user.id)
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


@login_required(login_url='/accounts/login')
def acad_person(request):
    '''
        Function for academic user
        @param:
                request - trivial

        @variables:
                current_user - get request user of curent variable
                user_details - taking his details from ExtraInfo
                desig_id - taking his details from Designation
                temp - temporary variable for getting information of real academic uservso that tha can be matched with the current user
                acadadmin - temporary variable for getting information of real academic user
                k - temporary variable
                year - today's year
                month - today's month
                available_cse_seats - available cse seats
                available_ece_seats - available ece seats
                available_me_seats - available me seats
                total_cse_seats - total cse seats
                total_ece_seats - total ece seats
                total_me_seats - totala me seats
                initial_branch - temporary variable to store branch change request
                change_branch - final variable to change branch
                available_seats - temporary variable to save available seats
                applied_by - id of the applied student
                cpi - cpi of the student
                lists - combining arrays applied_by
                context - final context variable to be shown on html page
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

    year = datetime.datetime.now().year
    month = datetime.datetime.now().month
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
                '../templates/academic_procedures/academicadmin.html',
                {
                    'context': context,
                    'lists': lists,
                    'date': date,
                    'query_option1': query_option1,
                    'query_option2': query_option2
                }
            )


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

    year = datetime.datetime.now().year
    month = datetime.datetime.now().month
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
@login_required(login_url='/accounts/login')
def student_list(request):
    '''
        This function is used to generate all list of students.
        @param:
                request - trivial

        @variables:
                query_option1 - get queries of the students from extrainfo.
                query_option2 - get quesries of the studens from student.
                dep_id - get the department ID of the logged in student.
                year - current year
                month - current month
    '''
    if(request.POST):
        # Branch Stream Year options
        # print (request.POST)
        option1 = request.POST["d1"]
        option2 = request.POST["d2"]
        # print (option1, option2)
        year = datetime.datetime.now().year
        month = datetime.datetime.now().month
        yearr = str(year) + "-" + str(year+1)
        semflag = 0
        queryflag = 1
        if(month >= 7):
            semflag = 1
        else:
            semflag = 2
        query_option1 = get_batch_query_detail(month, year)
        query_option2 = {"CSE": "CSE", "ECE": "ECE", "ME": "ME"}
        date = {'year': yearr, 'month': month, 'semflag': semflag, 'queryflag': queryflag}
        dep_id = DepartmentInfo.objects.all().filter(name=option2)
        obj1 = ExtraInfo.objects.all().filter(department=dep_id)
        queryflag = 1
        # obj2 = Student.objects.filter(programme='B.Tech').select_related()
        obj2 = Student.objects.filter(programme=option1[:6]).select_related()
        student_obj = []
        # print(obj2,dep_id)
        # print(obj1)
        cnt = 1
        for k in obj2:
            p = str(k.id)
            tempobj = {}
            for z in obj1:
                if(p[0:7] == z.id and p[0:4] == option1[7:]):
                    tempobj['roll_no'] = p[0:7]
                    tempobj['name'] = str(z.user.first_name) + " " + str(z.user.last_name)
                    tempobj['branch'] = option2
                    # student_obj[str(cnt)]=tempobj
                    student_obj.append(tempobj)
                    cnt += 1
                elif(p[0:7] == z.id and p[0:2] == option1[9:]):
                    tempobj['roll_no'] = p[0:7]
                    tempobj['name'] = str(z.user.first_name) + " " + str(z.user.last_name)
                    tempobj['branch'] = option2
                    # student_obj[str(cnt)]=tempobj
                    student_obj.append(tempobj)
                    cnt += 1

        html = render_to_string('academic_procedures/student_table.html',
                                {'student_obj': student_obj}, request)

        maindict = {'date': date,
                    'query_option1': query_option1,
                    'query_option2': query_option2,
                    'html': html,
                    'queryflag': queryflag}
        obj = json.dumps(maindict)
        return HttpResponse(obj, content_type='application/json')


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

    year = datetime.datetime.now().year
    month = datetime.datetime.now().month
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
                    'query_option2': query_option2
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


def add_thesis(request):
    '''
        This function is used to add thesis topic for the post graduate students in the database by using the list vaiable 'p'.
        @param:
                request - trivial

        @variables:
                student - details of the logged in student.
                thesis - gets the thesis details of the PhD student.
                faculty - gets the chosen faculty's details.
                user_details - details of the logged in user.
                fac - object to get all the faculties.
                p - thesis object to save the details in the database.
    '''
    if request.method == 'POST':
        # print (request.POST)
        faculty = request.POST.get('faculty')
        student = request.POST.get('student')
        thesis = request.POST.get('thesis')
        faculty = faculty.split()
        f_user = get_object_or_404(User, last_name=faculty[len(faculty)-1])
        fac = ExtraInfo.objects.all().filter(user=f_user).first()
        fac = Faculty.objects.all().filter(id=fac).first()

        # print(student)
        s_user = get_object_or_404(User, username=student)
        user_details = ExtraInfo.objects.all().filter(user=s_user).first()
        student = Student.objects.all().filter(id=user_details.id).first()

        # print(fac, student)

        p = Thesis(
                reg_id=user_details,
                student_id=student,
                supervisor_id=fac,
                topic=thesis
            )
        p.save()
        messages.info(request, 'Thesis Topic Selected')
        return HttpResponseRedirect('/academic-procedures/PhD')
    else:
        return HttpResponseRedirect('/academic_procedures/PhD/')
