import json
import pandas as pd
from django.http import FileResponse,Http404
from datetime import date, datetime, timedelta, time
import xlrd
import os
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation, DepartmentInfo
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core import serializers
from django.core.paginator import EmptyPage
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from notification.views import  healthcare_center_notif
# from applications.health_center.api.serializers import MedicalReliefSerializer
from .models import ( Constants,All_Medicine,All_Prescribed_medicine,All_Prescription,Prescription_followup,
                    Present_Stock,Doctor,Pathologist,
                    Doctors_Schedule,Pathologist_Schedule,Stock_entry,
                    medical_relief,MedicalProfile,Required_medicine,files,Required_tabel_last_updated)
from .utils import datetime_handler, compounder_view_handler, student_view_handler
from applications.filetracking.sdk.methods import *
from django.db.models import Q



@login_required
def healthcenter(request):
    '''
    This function is used to redirect user to different pages based on their roles.

    @param:
        request - contains metadata about the requested page
    @variables:
        usertype - get user data from request 

    '''
    design=request.session['currentDesignationSelected']
    if design!='Compounder':
        return HttpResponseRedirect("/healthcenter/student")
    elif design == 'Compounder':
        return HttpResponseRedirect("/healthcenter/compounder")


@login_required
def compounder_view(request):  
    
    '''
    This function handles post requests for compounder and render pages accordingly

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
    
    design=request.session['currentDesignationSelected']
    if design == 'Compounder':
        if request.method == 'POST':
            return compounder_view_handler(request)

        else:
            notifs = request.user.notifications.all()           
            # all_complaints = Complaint.objects.select_related('user_id','user_id__user','user_id__department').all()
            # all_hospitals = Hospital_admit.objects.select_related('user_id','user_id__user','user_id__department','doctor_id').all().order_by('-admission_date')
            # hospitals_list = Hospital.objects.all().order_by('hospital_name')
            # all_ambulances = Ambulance_request.objects.select_related('user_id','user_id__user','user_id__department').all().order_by('-date_request')
            # appointments_today =Appointment.objects.select_related('user_id','user_id__user','user_id__department','doctor_id','schedule','schedule__doctor_id').filter(date=datetime.now()).order_by('date')
            # appointments_future=Appointment.objects.select_related('user_id','user_id__user','user_id__department','doctor_id','schedule','schedule__doctor_id').filter(date__gt=datetime.now()).order_by('date')
            users = ExtraInfo.objects.select_related('user','department').filter(user_type='student')
            days = Constants.DAYS_OF_WEEK
            schedule=Doctors_Schedule.objects.select_related('doctor_id').all().order_by('doctor_id')
            schedule1=Pathologist_Schedule.objects.select_related('pathologist_id').all().order_by('pathologist_id')
            # expired=Expiry.objects.select_related('medicine_id').filter(expiry_date__lt=datetime.now(),returned=False).order_by('expiry_date')
            # live_meds=Expiry.objects.select_related('medicine_id').filter(returned=False).order_by('quantity')
            page_size=2
            fir=Required_tabel_last_updated.objects.first()
            if fir == None:
                exp = Stock_entry.objects.filter(Expiry_date__lt = date.today())
                for e in exp:
                    med=e.medicine_id
                    p_s = Present_Stock.objects.filter(Q(medicine_id = med) & Q(Expiry_date__gte = date.today()))
                    qty=0
                    for ps in p_s:
                        qty+=ps.quantity
                    if Required_medicine.objects.filter(medicine_id=med).exists() :
                        req=Required_medicine.objects.get(medicine_id=med)
                        if qty>=med.threshold  : req.delete()
                        else :
                            req.quantity = qty
                            req.save()
                    else :
                        if qty<med.threshold:
                            Required_medicine.objects.create(
                                medicine_id=med,
                                quantity = qty,
                                threshold = med.threshold
                            )
                Required_tabel_last_updated.objects.create(
                    date= date.today()
                )
            else :
                last_updated = fir.date
                exp = Stock_entry.objects.filter(Q(Expiry_date__gte = last_updated) & Q(Expiry_date__lt = date.today()))
                for e in exp:
                    med=e.medicine_id
                    p_s = Present_Stock.objects.filter(Q(medicine_id = med) & Q(Expiry_date__gte = date.today()))
                    qty=0
                    for ps in p_s:
                        qty+=ps.quantity
                    if Required_medicine.objects.filter(medicine_id=med).exists() :
                        req=Required_medicine.objects.get(medicine_id=med)
                        if(qty>med.threshold) : req.delete()
                        else :
                            req.quantity = qty
                            req.save()
                    else :
                        if qty<med.threshold:
                            Required_medicine.objects.create(
                                medicine_id=med,
                                quantity = qty,
                                threshold = med.threshold
                            )

            # stocks = Required_medicine.objects.all()
            current_required_page = 1
            page_size_required = page_size
            offset_stock_required = (current_required_page - 1 )* page_size_required
            required_data = Required_medicine.objects.filter()[offset_stock_required:offset_stock_required + page_size_required]
            total_pages_stock_required = (Required_medicine.objects.all().count() + page_size_required -1) // page_size_required
            stocks = {
                "count_stock_required" : total_pages_stock_required,
                "page_stock_required":{
                    "object_list":required_data,
                    'number' : current_required_page,
                    'has_previous' : current_required_page > 1 ,
                    'has_next': current_required_page < total_pages_stock_required,
                    'previous_page_number' :  current_required_page - 1 if current_required_page > 1 else None,
                    'next_page_number' :  current_required_page + 1 if current_required_page < total_pages_stock_required else None,      
                }
            }

            current_page_stock_expired = 1
            page_size_stock_expired = page_size
            offset_stock_expired = (current_page_stock_expired - 1 )* page_size_stock_expired
            expired=[]
            expiredData=Stock_entry.objects.filter(Expiry_date__lt=date.today()).order_by('Expiry_date')[offset_stock_expired:offset_stock_expired + page_size_stock_expired]
            total_pages_stock_expired = ( Stock_entry.objects.filter(Expiry_date__lt=date.today()).count()  + page_size_stock_expired - 1) // page_size_stock_expired
            for e in expiredData:
                obj={}
                obj['medicine_id']=e.medicine_id.brand_name
                obj['Expiry_date']=e.Expiry_date
                obj['supplier']=e.supplier
                try:
                    qty=Present_Stock.objects.get(stock_id=e).quantity
                except:
                    qty=0
                obj['quantity']=qty
                expired.append(obj)
            ExpiredstockContext = {
                     'count_stock_expired':total_pages_stock_expired,
                     'page_stock_expired':{
                           'object_list': expired,
                           'number': current_page_stock_expired,
                           'has_previous': current_page_stock_expired > 1,
                           'has_next': current_page_stock_expired < total_pages_stock_expired,
                           'previous_page_number': current_page_stock_expired - 1 if current_page_stock_expired > 1 else None,
                           'next_page_number': current_page_stock_expired + 1 if current_page_stock_expired < total_pages_stock_expired else None,
                     }
            }
                  
            
            current_page_stock = 1
            page_size_stock = page_size
            offset_stock = (current_page_stock - 1 )* page_size_stock
            live_meds=[]
            live=Stock_entry.objects.filter(Expiry_date__gte=date.today()).order_by('Expiry_date')[offset_stock:offset_stock + page_size_stock]
            total_pages_stock = ( Stock_entry.objects.filter(Expiry_date__gte=date.today()).count()  + page_size_stock - 1) // page_size_stock
            for e in live:
                obj={}
                obj['id']=e.id
                obj['medicine_id']=e.medicine_id.brand_name
                obj['Expiry_date']=e.Expiry_date
                obj['supplier']=e.supplier
                try:
                    qty=Present_Stock.objects.get(stock_id=e).quantity
                except:
                    qty=0
                obj['quantity']=qty
                live_meds.append(obj)
            stockContext = {
                     'count_stock_view':total_pages_stock,
                     'page_stock_view':{
                           'object_list': live_meds,
                           'number': current_page_stock,
                           'has_previous': current_page_stock > 1,
                           'has_next': current_page_stock < total_pages_stock,
                           'previous_page_number': current_page_stock - 1 if current_page_stock > 1 else None,
                           'next_page_number': current_page_stock + 1 if current_page_stock < total_pages_stock else None,
                     }
            }    
            
            
            schedule=Doctors_Schedule.objects.select_related('doctor_id').all().order_by('day','doctor_id')
            schedule1=Pathologist_Schedule.objects.select_related('pathologist_id').all().order_by('day','pathologist_id')
            
            doctors=Doctor.objects.filter(active=True).order_by('id')
            pathologists=Pathologist.objects.filter(active=True).order_by('id')
            medicine_presc = All_Prescribed_medicine.objects.all()
            
            #Logic for the padination and view prescriptions is below , used ajax for pagination
            current_page = 1
            page_size_prescription = page_size  # Default to 2 if not specified
            offset = (current_page - 1) * page_size_prescription
            # Fetch the prescriptions with limit and offset
            prescriptions = All_Prescription.objects.all().order_by('-date', '-id')[offset:offset + page_size_prescription]
            
            report = []
            for pre in prescriptions:
                dic = {
                    'id': pre.pk,
                    'user_id': pre.user_id,
                    'doctor_id': pre.doctor_id,
                    'date': pre.date,
                    'details': pre.details,
                    'test': pre.test,
                    'file_id': pre.file_id,
                    # 'file': view_file(file_id=pre.file_id)['upload_file'] if pre.file_id else None
                }
                report.append(dic)
            # Handle total count for pagination context
            total_count = All_Prescription.objects.count()
            # Calculate total number of pages
            total_pages = (total_count + page_size_prescription - 1) // page_size_prescription  # This ensures rounding up
            prescContext = {
                'count': total_pages,
                'page': {
                    'object_list': report,
                    'number': current_page,
                    'has_previous': current_page > 1,
                    'has_next': current_page < total_pages,
                    'previous_page_number': current_page - 1 if current_page > 1 else None,
                    'next_page_number': current_page + 1 if current_page < total_pages else None,
                }
            }
            

             
            #adding file tracking inbox part for compounder
            
            inbox_files=view_inbox(username=request.user.username,designation='Compounder',src_module='health_center')
            medicalrelief=medical_relief.objects.all()
                 
            inbox=[]
            for ib in inbox_files:
                dic={}
                for mr in medicalrelief:
                    if mr.file_id==int(ib['id']):   
                        dic['id']=ib['id'] 
                        dic['uploader']=ib['uploader']                   
                        dic['upload_date']=datetime.fromisoformat(ib['upload_date']).date()                   
                        dic['desc']=mr.description
                        # dic['file']=view_file(file_id=ib['id'])['upload_file']
                        dic['status']=mr.compounder_forward_flag
                        dic['status1']=mr.acc_admin_forward_flag
                inbox.append(dic)
                       
            # print(inbox_files)
                      
            return render(request, 'phcModule/phc_compounder.html',
                          {'days': days, 'users': users,'expired':ExpiredstockContext,
                           'stocks': stocks,
                            'doctors': doctors, 'pathologists':pathologists, 
                        'schedule': schedule, 'schedule1': schedule1, 'live_meds': stockContext, 'presc_hist': prescContext,'inbox_files':inbox,'medicines_presc':medicine_presc})
    else:
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
    
    design=request.session['currentDesignationSelected']
    if design != 'Compounder':
        if request.method == 'POST':
            return student_view_handler(request)

        else:
            notifs = request.user.notifications.all()
            users = ExtraInfo.objects.all()
            user_id = ExtraInfo.objects.select_related('user','department').get(user=request.user)
            hospitals = Hospital_admit.objects.select_related('user_id','user_id__user','user_id__department','doctor_id').filter(user_id=user_id).order_by('-admission_date')
            appointments = Appointment.objects.select_related('user_id','user_id__user','user_id__department','doctor_id','schedule','schedule__doctor_id').filter(user_id=user_id).order_by('-date')
            ambulances = Ambulance_request.objects.select_related('user_id','user_id__user','user_id__department').filter(user_id=user_id).order_by('-date_request')
            announcements_data=Announcements.objects.all().values()
            medical_profile=MedicalProfile.objects.filter(user_id=request.user.username)
            usrnm = get_object_or_404(User, username=request.user.username)
            user_info = ExtraInfo.objects.all().select_related('user','department').filter(user=usrnm).first()
            mp=[]
            for mr in medical_profile:                   
                # if mr.user_id == user_info: 
                dic={}
                # dic['user_id']=user_info
                dic['date_of_birth']=mr.date_of_birth                      
                dic['gender']=mr.gender
                dic['blood_type']=mr.blood_type                   
                dic['height']=mr.height
                dic['weight']=mr.weight
                    
                mp.append(dic)
                
            medicines = Prescribed_medicine.objects.select_related('prescription_id','prescription_id__user_id','prescription_id__user_id__user','prescription_id__user_id__department','prescription_id__doctor_id','medicine_id').all()
            complaints = Complaint.objects.select_related('user_id','user_id__user','user_id__department').filter(user_id=user_id).order_by('-date')
            days = Constants.DAYS_OF_WEEK
            schedule=Doctors_Schedule.objects.select_related('doctor_id').all().order_by('doctor_id')
            schedule1=Pathologist_Schedule.objects.select_related('pathologist_id').all().order_by('pathologist_id')
            doctors=Doctor.objects.filter(active=True)
            pathologists=Pathologist.objects.filter(active=True)
            
            #prescription
            prescription= Prescription.objects.filter(user_id=request.user.username)
            report=[]
            for pre in prescription:
                dic={}
                dic['id']=pre.id
                dic['doctor_id'] = pre.doctor_id  # Use dot notation
                dic['date'] = pre.date  # Use dot notation
                dic['details'] = pre.details  # Use dot notation
                dic['test'] = pre.test  # Use dot notation
                if pre.file_id:
                    dic['file'] = view_file(file_id=pre.file_id)['upload_file']
                else:
                    dic['file']=None 
                
                
                report.append(dic)
            
            count=Counter.objects.all()

            if count:
                Counter.objects.all().delete()
            Counter.objects.create(count=0,fine=0)
            count=Counter.objects.get()

            designations = Designation.objects.filter()
            holdsDesignations = []

            for d in designations:
                if d.name == "Compounder":
                    list = HoldsDesignation.objects.filter(designation=d)
                    holdsDesignations.append(list)
            
            acc_admin_inbox=view_inbox(username=request.user.username,designation='Accounts Admin',src_module='health_center')
            medicalrelief=medical_relief.objects.all()   
            acc_ib=[]    
            for ib in acc_admin_inbox:
                dic={}
                               
                for mr in medicalrelief:                   
                    if mr.file_id == int(ib['id']): 
                        dic['id']=ib['id']                       
                        dic['uploader']=ib['uploader']
                        dic['upload_date']=datetime.fromisoformat(ib['upload_date']).date()                   
                        dic['desc']=mr.description
                        dic['file']=view_file(file_id=ib['id'])['upload_file']
                        dic['status']=mr.acc_admin_forward_flag
                acc_ib.append(dic)
            uploader_outbox=view_outbox(username=request.user.username,designation=request.session['currentDesignationSelected'] ,src_module='health_center')
         
          
            uploader_inbox=view_inbox(username=request.user.username,designation=request.session['currentDesignationSelected'],src_module='health_center')
            medicalRelief=[]
           
            for out in uploader_outbox:
                dic={}
            
                for mr in medicalrelief:
                    if mr.file_id==int(out['id']):   
                        dic['id']=out['id']                    
                        dic['upload_date']=datetime.fromisoformat(out['upload_date']).date()                   
                        dic['desc']=mr.description
                        dic['file']=view_file(file_id=out['id'])['upload_file']
                        dic['status']=mr.acc_admin_forward_flag
                        dic['approval_date']=''
            
                for inb in uploader_inbox:
                    if dic['id']==inb['id']:
                        dic['approval_date']=datetime.fromisoformat(inb['upload_date']).date()
                medicalRelief.append(dic)                               
    
            
            return render(request, 'phcModule/phc_student.html',
                          {'complaints': complaints, 'medicines': medicines,
                           'ambulances': ambulances, 'doctors': doctors, 'pathologists':pathologists, 'days': days,'count':count,
                           'hospitals': hospitals, 'appointments': appointments,
                           'prescription': report, 'schedule': schedule,  'schedule1': schedule1,'users': users, 'curr_date': datetime.now().date(),'holdsDesignations':holdsDesignations,'acc_admin_inbox':acc_ib,'medicalRelief':medicalRelief,'announcements':announcements_data,'medical_profile':mp})
    else:
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

def pathologist_entry(request):
    '''
        This function inputs new pathologist' details into Doctor class in database 
        @param:
            request - contains metadata about the requested page

    '''
    excel = xlrd.open_workbook(os.path.join(os.getcwd(), 'dbinsertscripts/healthcenter/Pathologist-List.xlsx'))
    z = excel.sheet_by_index(0)

    for i in range(1, 5):
        try:
            name = str(z.cell(i,0).value)
            print(name)
            phone = str(int(z.cell(i,1).value))
            print(phone)
            spl = str(z.cell(i,2).value)
            u = Pathologist.objects.create(
                        pathologist_name = name,
                        pathologist_phone = phone,
                        specialization=spl
            )
            print("Pathologist done -> ")
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

@login_required(login_url='/accounts/login')      
def publish(request):
    return render(request,'../templates/health_center/publish.html' ,{})


def browse_announcements():
    """
    This function is used to browse Announcements Department-Wise
    made by different faculties and admin.

    @variables:
        cse_ann - Stores CSE Department Announcements
        ece_ann - Stores ECE Department Announcements
        me_ann - Stores ME Department Announcements
        sm_ann - Stores SM Department Announcements
        all_ann - Stores Announcements intended for all Departments
        context - Dictionary for storing all above data

    """
    cse_ann = Announcements.objects.filter(department="CSE")
    ece_ann = Announcements.objects.filter(department="ECE")
    me_ann = Announcements.objects.filter(department="ME")
    sm_ann = Announcements.objects.filter(department="SM")
    all_ann = Announcements.objects.filter(department="ALL")

    context = {
        "cse" : cse_ann,
        "ece" : ece_ann,
        "me" : me_ann,
        "sm" : sm_ann,
        "all" : all_ann
    }

    return context

def get_to_request(username):
    """
    This function is used to get requests for the receiver

    @variables:
        req - Contains request queryset

    """
    req = SpecialRequest.objects.filter(request_receiver=username)
    return req



@login_required(login_url='/accounts/login')
def announcement(request):
    """
    This function is contains data for Requests and Announcement Related methods.
    Data is added to Announcement Table using this function.

    @param:
        request - contains metadata about the requested page

    @variables:
        usrnm, user_info, ann_anno_id - Stores data needed for maker
        batch, programme, message, upload_announcement,
        department, ann_date, user_info - Gets and store data from FORM used for Announcements for Students.

    """
    usrnm = get_object_or_404(User, username=request.user.username)
    user_info = ExtraInfo.objects.all().select_related('user','department').filter(user=usrnm).first()
    num = 1
    ann_anno_id = user_info.id
    requests_received = get_to_request(usrnm)

    if request.method == 'POST':
        formObject = Announcements()
        # formObject.key = Projects.objects.get(id=request.session['projectId'])
        user_info = ExtraInfo.objects.all().select_related('user','department').get(id=ann_anno_id)
        getstudents = ExtraInfo.objects.select_related('user')
        recipients = User.objects.filter(extrainfo__in=getstudents)
        # formObject.anno_id=1
        formObject.anno_id=user_info
        # formObject.batch = request.POST['batch']
        # formObject.programme = request.POST['programme']
        formObject.message = request.POST['announcement']
        formObject. upload_announcement = request.FILES.get('upload_announcement')
        # formObject.department = request.POST['department']
        formObject.ann_date = date.today()
        #formObject.amount = request.POST['amount']
        formObject.save()
        healthcare_center_notif(usrnm, recipients , 'new_announce',formObject.message ) 
        return redirect('../../compounder/')    
        
    announcements_data=Announcements.objects.all().values()
    
    return render(request, 'health_center/make_announce_comp.html', {"user_designation":user_info.user_type,
                                                            'announcements':announcements_data,
                                                            "request_to":requests_received
                                                        })  
        # batch = request.POST.get('batch', '')
        # programme = request.POST.get('programme', '')
        # message = request.POST.get('announcement', '')
        # upload_announcement = request.FILES.get('upload_announcement')
        # department = request.POST.get('department')
        # ann_date = date.today()
        # user_info = ExtraInfo.objects.all().select_related('user','department').get(id=ann_anno_id)
        # getstudents = ExtraInfo.objects.select_related('user')
        # recipients = User.objects.filter(extrainfo__in=getstudents)

        # obj1, created = Announcements.objects.get_or_create(anno_id=user_info,
        #                             batch=batch,
        #                             programme=programme,
        #                             message=message,
        #                             upload_announcement=upload_announcement,
        #                             department = department,
        #                             ann_date=ann_date)
     
@login_required(login_url='/accounts/login')      
def medical_profile(request): 
    usrnm = get_object_or_404(User, username=request.user.username)
    user_id_info = ExtraInfo.objects.all().select_related('user','department').filter(user=usrnm).first()
    num = 1
    user_id = user_id_info.id
    requests_received = get_to_request(usrnm)
    user = request.user
    # medical_profile, created = MedicalProfile.objects.get_or_create(user_id==request.user.username)
    medical_profile=MedicalProfile.objects.filter(user_id=request.user.username)
    usrnm = get_object_or_404(User, username=request.user.username)
    user_info = ExtraInfo.objects.all().select_related('user','department').filter(user=usrnm).first()
    # mp=[]/
    cnt=0
    for mr in medical_profile:                   
        cnt += 1
    if request.method == 'POST':
        user_info = ExtraInfo.objects.all().select_related('user','department').get(id=user_id)
   
        if cnt==0:
            medical_profile = MedicalProfile()
            medical_profile.user_id = user_info
            medical_profile.date_of_birth = request.POST.get('date_of_birth')
            medical_profile.gender = request.POST.get('gender')
            medical_profile.blood_type = request.POST.get('blood_type')
            medical_profile.height = request.POST.get('height')
            medical_profile.weight = request.POST.get('weight')
            # medical_profile.form_submitted = True
            medical_profile.save()
            return redirect('../../compounder/')    
            
        else:
            # Process the form submission for the first time
            medical_profile1=MedicalProfile.objects.filter(user_id=user_info).first()
            
            medical_profile1.date_of_birth = request.POST.get('date_of_birth')
            medical_profile1.gender = request.POST.get('gender')
            medical_profile1.blood_type = request.POST.get('blood_type')
            medical_profile1.height = request.POST.get('height')
            medical_profile1.weight = request.POST.get('weight')
            # medical_profile.form_submitted = True
            medical_profile1.save()
            return redirect('../../compounder/')    
            
    return render(request, 'health_center/medical_profile.html', {"user_designation":user_info.user_type,
                                                            'medical_profile':medical_profile,
                                                            "request_to":requests_received
                                                        })

@login_required
def compounder_view_prescription(request,prescription_id):
    prescription = All_Prescription.objects.get(id=prescription_id)
    pre_medicine = All_Prescribed_medicine.objects.filter(prescription_id=prescription)
    doctors=Doctor.objects.filter(active=True).order_by('id')
    follow_presc =Prescription_followup.objects.filter(prescription_id=prescription).order_by('-id')
    if request.method == "POST":
        print("post")
    return render(request, 'phcModule/phc_compounder_view_prescription.html',{'prescription':prescription,
                            'pre_medicine':pre_medicine,'doctors':doctors,
                            "follow_presc":follow_presc})

@login_required
def view_file(request,file_id):
    file_id_int = int(file_id)
    if(file_id_int == -2):
        return FileResponse(open('static/health_center/add_stock_example.xlsx', 'rb'), as_attachment=True, filename="example_add_stock.xlsx")
    if(file_id_int == -1):
        return FileResponse(open('static/health_center/add_medicine_example.xlsx', 'rb'), as_attachment=True, filename="example_add_medicine.xlsx")  
    filepath = "applications/health_center/static/health_center/generated.pdf"

    file=files.objects.get(id=file_id)
    f=file.file_data
    
    with open("applications/health_center/static/health_center/generated.pdf", 'wb+') as destination:   
        destination.write(f)  
    
    pdf = open(filepath, 'rb')
    response = FileResponse(pdf, content_type="application/pdf")
    response['Content-Disposition'] = 'inline; filename="generated.pdf"'

    return response
