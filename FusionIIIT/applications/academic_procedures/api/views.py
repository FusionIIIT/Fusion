import datetime

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect
from django.db import transaction

from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes,authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from applications.globals.models import HoldsDesignation, Designation, ExtraInfo
from applications.programme_curriculum.models import ( CourseSlot, Course as Courses, Batch, Semester)


from applications.academic_procedures.models import (Course, Student, Curriculum , ThesisTopicProcess, InitialRegistrations,
                                                     FinalRegistrations, SemesterMarks,backlog_course,
                                                     BranchChange , StudentRegistrationChecks, Semester , FeePayments , course_registration)

from applications.academic_information.models import (Curriculum_Instructor , Calendar)

from applications.academic_procedures.views import (get_user_semester, get_acad_year,
                                                    get_currently_registered_courses,
                                                    get_current_credits, get_branch_courses,
                                                    Constants, get_faculty_list,
                                                    get_registration_courses, get_add_course_options,
                                                    get_pre_registration_eligibility,
                                                    get_final_registration_eligibility,
                                                    get_add_or_drop_course_date_eligibility,
                                                    get_detailed_sem_courses,
                                                    InitialRegistration)

from . import serializers

User = get_user_model()

date_time = datetime.datetime.now()



#--------------------------------------- APIs of student----------------------------------------------------------


# with this student can get all his details in one api call 
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
        print(current_user, user_sem+1, user_branch)
        try:
            next_sem_branch_courses = get_branch_courses(current_user, user_sem+1, user_branch)
        except Exception as e:
            return Response(data = str(e))
        next_sem_branch_courses_data = serializers.CurriculumSerializer(next_sem_branch_courses, many=True).data

        fee_payment_mode_list = dict(Constants.PaymentMode)

        next_sem_branch_registration_courses = get_registration_courses(next_sem_branch_courses)
        next_sem_branch_registration_courses_data = []
        for choices in next_sem_branch_registration_courses:
            next_sem_branch_registration_courses_data.append(serializers.CurriculumSerializer(choices, many=True).data)
        # print(next_sem_branch_registration_courses_data)
        # next_sem_branch_registration_courses_data = serializers.CurriculumSerializer(next_sem_branch_registration_courses_data, many=True).data

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

        pre_registration_date_flag = get_pre_registration_eligibility(current_date , user_sem , acad_year)
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

        faculty_list = serializers.HoldsDesignationSerializer(get_faculty_list(), many=True).data

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
                        

            'student_flag' : student_flag,
            'ug_flag' : ug_flag,
            'masters_flag' : masters_flag,
            'phd_flag' : phd_flag,
            'fac_flag' : fac_flag,
            'des_flag' : des_flag,
            
            'drop_courses_options' : currently_registered_courses_data,
            'pre_registration_date_flag': pre_registration_date_flag,
            'final_registration_date_flag': final_registration_date_flag,
            'add_or_drop_course_date_flag': add_or_drop_course_date_flag,
            'pre_registration_flag' : pre_registration_flag,
            'final_registration_flag': final_registration_flag,
            'teaching_credit_registration_course' : teaching_credit_registration_course_data,
            
            'attendance': attendance_data,
            'Branch_Change_Flag':branchchange_flag
        }
    return Response(data=resp, status=status.HTTP_200_OK)


# api for student for adding courses  
@api_view(['POST'])
def add_course(request):
    try:
        current_user = request.user
        current_user = ExtraInfo.objects.all().filter(user=current_user).first()
        current_user = Student.objects.all().filter(id=current_user.id).first()

        sem_id_instance = Semester.objects.get(id = request.data['semester'])
        
        count = request.data['ct']
        count = int(count)
        reg_curr = []

        for i in range(1, count+1):
            choice = "choice["+str(i)+"]"
            slot = "slot["+str(i)+"]"
            try:
                course_id_instance = Courses.objects.get(id = request.data[choice])
                courseslot_id_instance = CourseSlot.objects.get(id = request.data[slot])
                
                print(courseslot_id_instance.max_registration_limit)
                if course_registration.objects.filter(working_year = current_user.batch_id.year, course_id = course_id_instance).count() < courseslot_id_instance.max_registration_limit and (course_registration.objects.filter(course_id=course_id_instance, student_id=current_user).count() == 0):
                    p = course_registration(
                        course_id=course_id_instance,
                        student_id=current_user,
                        course_slot_id=courseslot_id_instance,
                        semester_id=sem_id_instance
                    )
                    print(serializers.course_registration(p))
                    if p not in reg_curr:
                        reg_curr.append(p)
                    else:
                        print("already exist")
            except Exception as e:
                error_message = str(e) 
                resp = {'message': 'Course addition failed', 'error': error_message}
                return Response(resp, status=status.HTTP_400_BAD_REQUEST)
        print(reg_curr)
        course_registration_data = course_registration.objects.bulk_create(reg_curr)
        course_registration_data = serializers.CourseRegistrationSerializer(course_registration_data , many = True).data
        res = {'message' : 'Courses successfully added' , "courses_added" : course_registration_data }
        return Response(data = res , status = status.HTTP_200_OK)
    except Exception as e:
        return Response(data = str(e) , status= status.HTTP_500_INTERNAL_SERVER_ERROR)

    
@api_view(['POST'])
def drop_course(request):
    current_user = request.user
    current_user = ExtraInfo.objects.all().filter(user=current_user).first()
    current_user = Student.objects.all().filter(id = current_user.id).first()
    
    courses = request.data['courses']

    for course in courses:
        try:
            course_id = Courses.objects.all().filter(id=course).first()
            course_registration.objects.filter(course_id = course_id, student_id = current_user).delete()
        except Exception as e:
            resp = {"message" : "Course drop failed", "error" : str(e)}
            return Response(data = resp, status = status.HTTP_400_BAD_REQUEST)
    
    resp = {"message" : "Course successfully dropped"}
    return Response(data = resp , status = status.HTTP_200_OK)


# simple api for getting to know the details of user who have logined in the system
@api_view(['GET'])
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
@api_view(['GET'])
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
@api_view(['POST'])
@transaction.atomic
def student_pre_registration(request):
    try:
        current_user = request.user
        current_user_id = serializers.UserSerializer(current_user).data["id"]
        s_id = current_user.extrainfo.id

        current_user = ExtraInfo.objects.all().select_related('user','department').filter(user=current_user_id).first()
        current_user = serializers.ExtraInfoSerializer(current_user).data

        current_user_instance = Student.objects.all().filter(id=current_user["id"]).first()
        current_user = serializers.StudentSerializers(current_user_instance).data

        sem_id_instance = Semester.objects.get(id = request.data.get('semester'))
        sem_id = serializers.SemesterSerializer(sem_id_instance).data["id"]

        # filter based on the semester id and student id
        obj = StudentRegistrationChecks.objects.filter(semester_id_id = sem_id,  student_id = s_id)
        # serialize the data for displaying
        student_registration_check = serializers.StudentRegistrationChecksSerializer(obj, many=True).data

        try:
            # check if user have already done pre registration
            if(student_registration_check and student_registration_check[0]["pre_registration_flag"] ):
                return Response(data = {"message" : "You have already registered for this semester" }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(data = str(e) , status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        course_slots=request.data.get("course_slot")
        reg_curr = []
        

        for course_slot in course_slots :
            course_priorities = request.data.get("course_priority-"+course_slot)
            if(course_priorities[0] == 'NULL'):
                print("NULL FOUND")
                continue
            course_slot_id_for_model = CourseSlot.objects.get(id = int(course_slot))

            # return Response(data = course_slots , status=status.HTTP_200_OK)
            for course_priority in course_priorities:
                priority_of_current_course,course_id = map(int,course_priority.split("-"))
                # get course id for the model
                course_id_for_model = Courses.objects.get(id = course_id)
                print("check")
                p = InitialRegistration(
                    course_id = course_id_for_model,
                    semester_id = sem_id_instance,
                    student_id = current_user_instance,
                    course_slot_id = course_slot_id_for_model,
                    priority = priority_of_current_course
                )
                p.save()
                reg_curr.append(p)

        
        try:
            serialized_reg_curr = serializers.InitialRegistrationSerializer(reg_curr, many=True).data
            
            registration_check = StudentRegistrationChecks(
                        student_id = current_user_instance,
                        pre_registration_flag = True,
                        final_registration_flag = False,
                        semester_id = sem_id_instance
                    )
            registration_check.save()
            return Response(data={"message": "Successfully Registered for the courses.", "registrations": serialized_reg_curr}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(data = {"message" : "Error in Registration." , "error" : str(e)} , status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return Response(data = {"message" : "Error in Registration." , "error" : str(e)} , status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
        
# with this student can do his final registration for the upcoming semester
@api_view(['POST'])
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
        
        if(registration_status[0] and registration_status[0]["pre_registration_flag"] == False):
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
        fee_receipt = request.FILES['fee_receipt']

        print(fee_receipt)
        obj = FeePayments(
            student_id = current_user_instance,
            semester_id = sem_id_instance,
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
            registration_status = StudentRegistrationChecks.objects.filter(student_id = current_user["id"], semester_id = sem_id).update(final_registration_flag = True)
            return Response(data = {"message" : "Final Registration Successfull" } , status= status.HTTP_200_OK)
        except Exception as e:
            return Response(data = {"message" : "Final Registration Failed " , "error" : str(e)} , status = status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return Response(data = {"message" : "Final Registration Failed " , "error" : str(e)} , status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# with this api student can get his backlog courses list
@api_view(['GET'])
def student_backlog_courses(request):
    try : 
        stu_id = Student.objects.select_related('id','id__user','id__department').get(id=request.user.username)
        backlogCourseList = []
        backlogCourses = backlog_course.objects.select_related('course_id' , 'student_id' , 'semester_id' ).filter(student_id=stu_id)
        for i in backlogCourses:
            obj = {
                "course_id" : i.course_id.id,
                "course_name" : i.course_id.course_name,
                "faculty" : i.course_id.course_details,
                "semester" : i.semester_id.semester_no,
                "is_summer_course" : i.is_summer_course
            }
            backlogCourseList.append(obj)

        return Response(backlogCourseList, status=status.HTTP_200_OK)
    except Exception as e:
            return Response(data = str(e) , status=status.HTTP_500_INTERNAL_SERVER_ERROR)



#--------------------------------------- APIs of acad person----------------------------------------------------------


# with this acad admin can fetch the list of courses for any batch , semester and brach
@api_view(['GET'])
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
@api_view(['POST'])
def add_course_to_slot(request):
    course_code = request.data.get('course_code')
    course_slot_name = request.data.get('course_slot_name')
    try:
        course_slot = CourseSlot.objects.get(name=course_slot_name)
        course = Courses.objects.get(code=course_code)
        course_slot.courses.add(course)
        
        return JsonResponse({'message': f'Course {course_code} added to slot {course_slot_name} successfully.'}, status=200)
    except CourseSlot.DoesNotExist:
        return JsonResponse({'error': 'Course slot does not exist.'}, status=400)
    except Course.DoesNotExist:
        return JsonResponse({'error': 'Course does not exist.'}, status=400)

# with this api request acad person can remove any course from a specific slot   
@api_view(['POST'])
def remove_course_from_slot(request):
    course_code = request.data.get('course_code')
    course_slot_name = request.data.get('course_slot_name')
    try:
        course_slot = CourseSlot.objects.get(name=course_slot_name)
        course = Courses.objects.get(code=course_code)
        course_slot.courses.remove(course)
        return JsonResponse({'message': f'Course {course_code} removed from slot {course_slot_name} successfully.'}, status=200)
    except CourseSlot.DoesNotExist:
        return JsonResponse({'error': 'Course slot does not exist.'}, status=400)
    except Course.DoesNotExist:
        return JsonResponse({'error': 'Course does not exist.'}, status=400)
  


#--------------------------------------- APIs of faculty----------------------------------------------------------

# with this api faculty can know what are the courses assigned to him 
@api_view(['GET'])
def faculty_assigned_courses(request):
    try:
        current_user = request.user
        curriculum_ids = Curriculum_Instructor.objects.filter(instructor_id=current_user.id).values_list('curriculum_id', flat=True)
        course_infos = []
        print(current_user.id)
        for curriculum_id in curriculum_ids:
            course_info = Curriculum.objects.filter(curriculum_id=curriculum_id).values_list('course_code','course_type','programme','branch','sem','course_id_id').first()
            course_infos.append(course_info)
    
        return Response(data= course_infos , status=status.HTTP_200_OK)
    except Exception as e:
        return Response(data = {"error" : str(e)} , status= status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
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