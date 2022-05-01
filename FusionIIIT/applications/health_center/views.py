import json
from datetime import datetime, timedelta, time
import xlrd
import os
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation, DepartmentInfo
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core import serializers
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from notification.views import  healthcare_center_notif
from .models import (Ambulance_request, Appointment, Complaint, Constants,
                     Counter, Doctor, Expiry, Hospital, Hospital_admit,
                     Medicine, Prescribed_medicine, Prescription, Schedule,
                     Stock)
from .utils import datetime_handler, compounder_view_handler, student_view_handler



@login_required
def healthcenter(request):
    '''
    This function is used to redirect user to different pages based on their roles.

    @param:
        request - contains metadata about the requested page
    @variables:
        usertype - get user data from request 

    '''
    usertype = ExtraInfo.objects.select_related('user','department').get(user=request.user).user_type

    if usertype == 'student' or usertype=='faculty' or usertype=='staff':
        return HttpResponseRedirect("/healthcenter/student")
    elif usertype == 'compounder':
        return HttpResponseRedirect("/healthcenter/compounder")


@login_required
def compounder_view(request):  
    
    '''
    This function handles post reques for compounder and render pages accordingly

    @param:
        request - contains metadata about the requested page
    @variables:
        all_complaints: retrieve Complaint class objects from database
        all_hospitals: retrieve Hospital_admit class objects from database
        hospital_list: retrieve Hospital class objects from database
        all_ambulances: retrieve Ambulance_request class objects from database
        appointments_today: retrieve Appointment class objects for today from database
        appointments_future: retrieve future Appointment class objects from database
        users: retrieve Student class objects from database 
        stocks: retrieve Stock class objects from database
        days: days of week
        schedule: retrieve schedule from doctor_id for doctor from database
        expired: retrieve expiry detailes for medicine_id from database
        count: retrieve Counter class objects from database
        presc_hist: retrieve Precription class objects from database based on user_id
        medicine_presc: retrieve Prescribed_medicine objects from database based on user_id
        hospitals: retrieve Hospital class objects from database 
        schedule: retrieve Schedule class objects from database based on doctor_id
        doctors: retrieve Doctor class objects from database 
    '''
                                                                # compounder view starts here
    usertype = ExtraInfo.objects.select_related('user','department').get(user=request.user).user_type
    if usertype == 'compounder':
        if request.method == 'POST':
            return compounder_view_handler(request)

        else:
            all_complaints = Complaint.objects.select_related('user_id','user_id__user','user_id__department').all()
            all_hospitals = Hospital_admit.objects.select_related('user_id','user_id__user','user_id__department','doctor_id').all().order_by('-admission_date')
            hospitals_list = Hospital.objects.all().order_by('hospital_name')
            all_ambulances = Ambulance_request.objects.select_related('user_id','user_id__user','user_id__department').all().order_by('-date_request')
            appointments_today =Appointment.objects.select_related('user_id','user_id__user','user_id__department','doctor_id','schedule','schedule__doctor_id').filter(date=datetime.now()).order_by('date')
            appointments_future=Appointment.objects.select_related('user_id','user_id__user','user_id__department','doctor_id','schedule','schedule__doctor_id').filter(date__gt=datetime.now()).order_by('date')
            users = ExtraInfo.objects.select_related('user','department').filter(user_type='student')
            stocks = Stock.objects.all()
            days = Constants.DAYS_OF_WEEK
            schedule=Schedule.objects.select_related('doctor_id').all().order_by('doctor_id')
            expired=Expiry.objects.select_related('medicine_id').filter(expiry_date__lt=datetime.now(),returned=False).order_by('expiry_date')
            live_meds=Expiry.objects.select_related('medicine_id').filter(returned=False).order_by('quantity')
            count=Counter.objects.all()
            presc_hist=Prescription.objects.select_related('user_id','user_id__user','user_id__department','doctor_id','appointment','appointment__user_id','appointment__user_id__user','appointment__user_id__department','appointment__doctor_id','appointment__schedule','appointment__schedule__doctor_id').all().order_by('-date')
            medicines_presc=Prescribed_medicine.objects.select_related('prescription_id','prescription_id__user_id','prescription_id__user_id__user','prescription_id__user_id__department','prescription_id__doctor_id','prescription_id__appointment','prescription_id__appointment__user_id','prescription_id__appointment__user_id__user','prescription_id__appointment__user_id__department','prescription_id__appointment__doctor_id','prescription_id__appointment__schedule','prescription_id__appointment__schedule__doctor_id','medicine_id').all()
            if count:
                Counter.objects.all().delete()
            Counter.objects.create(count=0,fine=0)
            count=Counter.objects.get()
            hospitals=Hospital.objects.all()
            schedule=Schedule.objects.select_related('doctor_id').all().order_by('day','doctor_id')
            doctors=Doctor.objects.filter(active=True).order_by('id')

            doct= ["Dr. G S Sandhu", "Dr. Jyoti Garg", "Dr. Arvind Nath Gupta"]
             

            return render(request, 'phcModule/phc_compounder.html',
                          {'days': days, 'users': users, 'count': count,'expired':expired,
                           'stocks': stocks, 'all_complaints': all_complaints,
                           'all_hospitals': all_hospitals, 'hospitals':hospitals, 'all_ambulances': all_ambulances,
                           'appointments_today': appointments_today, 'doctors': doctors, 'doct': doct,
                           'appointments_future': appointments_future, 'schedule': schedule, 'live_meds': live_meds, 'presc_hist': presc_hist, 'medicines_presc': medicines_presc, 'hospitals_list': hospitals_list})
    elif usertype == 'student':
        return HttpResponseRedirect("/healthcenter/student")                                      # compounder view ends


def student_view(request):   
    '''
    This function handles post reques for student and render pages accordingly

    @param:
        request - contains metadata about the requested page
    @variables:
        users: retrieve ExtraIfo class objects from database
        user_id: retrieve ExtraIfo class objects from database based on user and department
        hospitals: retrieve Hospital_admit class objects from database based on user_id
        appointments: retrieve Appointment class objects from database based on user_id
        amblances: retrieve Ambulance_request class objects from database based on user_id
        prescription: retrieve Prescription class objects from database based on user_id
        medicines: retrieve Prescribed_medicine class objects from database
        complaints: retrieve Complaint class objects from database based on user_id
        days: Days of week constant
        schedule: retrieve Schedule class objects from database
        doctors: retrieve Doctor class objects from database        

    '''                                                                 # student view starts here
    usertype = ExtraInfo.objects.select_related('user','department').get(user=request.user).user_type
    if usertype == 'student' or usertype == 'faculty' or usertype == 'staff':
        if request.method == 'POST':
            return student_view_handler(request)

        else:
            users = ExtraInfo.objects.all()
            user_id = ExtraInfo.objects.select_related('user','department').get(user=request.user)
            hospitals = Hospital_admit.objects.select_related('user_id','user_id__user','user_id__department','doctor_id').filter(user_id=user_id).order_by('-admission_date')
            appointments = Appointment.objects.select_related('user_id','user_id__user','user_id__department','doctor_id','schedule','schedule__doctor_id').filter(user_id=user_id).order_by('-date')
            ambulances = Ambulance_request.objects.select_related('user_id','user_id__user','user_id__department').filter(user_id=user_id).order_by('-date_request')
            prescription = Prescription.objects.select_related('user_id','user_id__user','user_id__department','doctor_id','appointment','appointment__user_id','appointment__user_id__user','appointment__user_id__department','appointment__doctor_id','appointment__schedule','appointment__schedule__doctor_id').filter(user_id=user_id).order_by('-date')
            medicines = Prescribed_medicine.objects.select_related('prescription_id','prescription_id__user_id','prescription_id__user_id__user','prescription_id__user_id__department','prescription_id__doctor_id','prescription_id__appointment','prescription_id__appointment__user_id','prescription_id__appointment__user_id__user','prescription_id__appointment__user_id__department','prescription_id__appointment__doctor_id','prescription_id__appointment__schedule','prescription_id__appointment__schedule__doctor_id','medicine_id').all()
            complaints = Complaint.objects.select_related('user_id','user_id__user','user_id__department').filter(user_id=user_id).order_by('-date')
            days = Constants.DAYS_OF_WEEK
            schedule=Schedule.objects.select_related('doctor_id').all().order_by('doctor_id')
            doctors=Doctor.objects.filter(active=True)
            count=Counter.objects.all()

            if count:
                Counter.objects.all().delete()
            Counter.objects.create(count=0,fine=0)
            count=Counter.objects.get()

            doct= ["Dr. G S Sandhu", "Dr. Jyoti Garg", "Dr. Arvind Nath Gupta"]
            

            return render(request, 'phcModule/phc_student.html',
                          {'complaints': complaints, 'medicines': medicines,
                           'ambulances': ambulances, 'doctors': doctors, 'days': days,'count':count,
                           'hospitals': hospitals, 'appointments': appointments,
                           'prescription': prescription, 'schedule': schedule, 'users': users,'doct': doct, 'curr_date': datetime.now().date()})
    elif usertype == 'compounder':
        return HttpResponseRedirect("/healthcenter/compounder")                                     # student view ends

def schedule_entry(request):
    '''
        This function inputs Schedule details into Schedule class in database 
        @param:
            request - contains metadata about the requested page

    '''
    excel = xlrd.open_workbook(os.path.join(os.getcwd(), 'dbinsertscripts/healthcenter/Doctor-Schedule.xlsx'))
    z = excel.sheet_by_index(0)

    for i in range(1, 19):
        try:
            doc_name = str(z.cell(i,0).value)
            print(doc_name)
            do=Doctor.objects.filter(doctor_name=doc_name)
            doc_id = do[0]
            print(doc_id)
            day = str(z.cell(i,1).value)
            days = Constants.DAYS_OF_WEEK
            for p,d in days:
                if d==day:
                    da=p
            print(da)
            x=z.cell(i,2).value
            x=int(x*24*3600)
            from_time=time(x//3600,(x%3600)//60,x%60)
            print(from_time)
            print(from_time)
            y=z.cell(i,3).value
            y=int(y*24*3600)
            to_time=time(y//3600,(y%3600)//60,y%60)
            print(to_time)
            room=int(z.cell(i,4).value)
            u = Schedule.objects.create(
                        doctor_id = doc_id,
                        day = da,
                        from_time=from_time,
                        to_time=to_time,
                        room=room,
                        date=datetime.now()
            )
            print("Schedule done -> ")
        except Exception as e:
            print(e)
            print(i)
            pass
    return HttpResponse("Hello")

def doctor_entry(request):
    '''
        This function inputs new doctors' details into Doctor class in database 
        @param:
            request - contains metadata about the requested page

    '''
    excel = xlrd.open_workbook(os.path.join(os.getcwd(), 'dbinsertscripts/healthcenter/Doctor-List.xlsx'))
    z = excel.sheet_by_index(0)

    for i in range(1, 5):
        try:
            name = str(z.cell(i,0).value)
            print(name)
            phone = str(int(z.cell(i,1).value))
            print(phone)
            spl = str(z.cell(i,2).value)
            u = Doctor.objects.create(
                        doctor_name = name,
                        doctor_phone = phone,
                        specialization=spl
            )
            print("Doctor done -> ")
        except Exception as e:
            print(e)
            print(i)
            pass
    return HttpResponse("Hello")

def compounder_entry(request):
    '''
        This function inputs new compounder details into Doctor class in database 
        @param:
            request - contains metadata about the requested page

    '''
    excel = xlrd.open_workbook(os.path.join(os.getcwd(), 'dbinsertscripts/healthcenter/Compounder-List.xlsx'))
    z = excel.sheet_by_index(0)

    for i in range(1, 4):
        try:
            empid = int(z.cell(i, 0).value)
            name = str(z.cell(i,1).value)
            dep = str(z.cell(i,2).value)
            email = str(z.cell(i,3).value)
            des = str(z.cell(i,4).value)
            print(dep,des)
            at = 0
            for i in range(0,len(email)):
                if(email[i]=='@'):
                    at = i
                    break
            username = str(email[0:at])
            print(username)
            dd = ""
            dess = ""
            try:
                dd = DepartmentInfo.objects.get(name = dep)
            except:
                dd = DepartmentInfo.objects.create(name = dep)
            try:
                dess = Designation.objects.get(name = des)
            except:
                dess = Designation.objects.create(name = des)
            name = name.split()
            last_name = name[len(name)-1]
            first_name = ""
            for i in range(0,len(name)-1):
                first_name += name[i]
            print(first_name,last_name)
            u = User.objects.create_user(
                        username = username,
                        password = 'hello123',
                        first_name = first_name,
                        last_name = last_name,
                        email = email,
            )
            sex = "M"
            print(str(i)+" user creation done")
            f = ExtraInfo.objects.create(
                sex = sex,
                user = u,
                id = empid,
                department = dd,
                age = 38,
                about_me = 'Hello I am ' + first_name + last_name,
                user_type = 'compounder',
                phone_no = 9999999999
            )
            print("extraInfoCreation done -> "+str(i))

            qz = HoldsDesignation.objects.create(
                user = u,
                working = u,
                designation = dess,
            )
            print("All done yippe -> " + str(i))
        except Exception as e:
            print(e)
            print(i)
            pass
    return HttpResponse("Hello")