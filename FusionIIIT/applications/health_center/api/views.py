from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation, DepartmentInfo
from django.db import transaction
from notification.views import  healthcare_center_notif
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes,authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.csrf import csrf_exempt
import pandas as pd
from django.db import transaction
from datetime import datetime, timedelta,date
from django.core import serializers
from applications.filetracking.models import File
from django.http import HttpResponse, JsonResponse
from notification.views import  healthcare_center_notif
from applications.health_center.models import ( Doctor, Stock_entry,Present_Stock,All_Medicine, 
                     Doctors_Schedule,Pathologist_Schedule,
                    Pathologist, medical_relief, MedicalProfile,All_Prescription,All_Prescribed_medicine,
                    Prescription_followup,files,Required_medicine,Announcements,Complaint)
from applications.filetracking.sdk.methods import *
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from django.db.models import Q
from applications.globals.models import ExtraInfo
from applications.hr2.models import EmpDependents
import json
from . import serializers

from notifications.models import Notification

User = get_user_model()

def convert_to_am_pm(time_str):
    """Converts time in HH:MM:SS format to AM/PM format."""

    time_obj = datetime.strptime(time_str, "%H:%M:%S")
    return time_obj.strftime("%I:%M %p")
    
@api_view(['POST'])
def compounder_api_handler(request):
    request_body = request.body.decode('utf-8')
    request_body = json.loads(request_body)
    '''
        handles rendering of pages for compounder view
    '''
    # compounder response to patients feedback
    if 'feed_com' in request.POST:
        pk = request.POST.get('com_id')
        feedback = request.POST.get('feed')
        comp_id = ExtraInfo.objects.select_related('user','department').filter(user_type='compounder')
        Complaint.objects.select_related('user_id','user_id__user','user_id__department').filter(id=pk).update(feedback=feedback)
        data = {'feedback': feedback}
        for cmp in comp_id:
                healthcare_center_notif(request.user, cmp.user, 'feedback_res','')
        return JsonResponse(data)

    # updating new doctor info in db    
    elif 'add_doctor' in request_body:                                         
        doctor=request_body['new_doctor']
        specialization=request_body['specialization']
        phone=request_body['phone']
        Doctor.objects.create(
        doctor_name=doctor,
        doctor_phone=phone,
        specialization=specialization,
        active=True
        )
        data={'status':1, 'doctor':doctor, 'specialization':specialization, 'phone':phone}
        return JsonResponse(data)
    
    # updating new pathologist info in db    
    elif 'add_pathologist' in request_body:                                         
        doctor=request_body['new_pathologist']
        specialization=request_body['specialization']
        phone=request_body['phone']
        Pathologist.objects.create(
        pathologist_name=doctor,
        pathologist_phone=phone,
        specialization=specialization,
        active=True
        )
        data={'status':1, 'pathologist_name':doctor, 'specialization':specialization, 'pathologist_phone':phone}
        return JsonResponse(data)
    
    

    # remove doctor by changing active status
    elif 'remove_doctor' in request_body:                              
        doctor=request_body['doctor_active']
        Doctor.objects.filter(id=doctor).update(active=False)
        doc=Doctor.objects.get(id=doctor).doctor_name
        data={'status':1, 'id':doctor, 'doc':doc}
        return JsonResponse(data)
    
    # remove pathologist by changing active status
    elif 'remove_pathologist' in request_body:                              
        doctor=request_body['pathologist_active']
        Pathologist.objects.filter(id=doctor).update(active=False)
        doc=Pathologist.objects.get(id=doctor).pathologist_name
        data={'status':1, 'id':doctor, 'doc':doc}
        return JsonResponse(data)
    
    elif "get_annoucements" in request_body:
        announcements_data=Announcements.objects.all().order_by('-id').values()
        serializer = serializers.AnnouncementSerializer(announcements_data,many=True)
        return JsonResponse({'status':1, 'announcements' : serializer.data})
    
    elif "get_feedback" in request_body:
        all_complaints = Complaint.objects.select_related('user_id','user_id__user','user_id__department').all().order_by('-id')
        serializer = serializers.ComplaintSerializer(all_complaints,many=True)
        return JsonResponse({'status':1,"complaints":serializer.data})
    
    elif "get_relief" in request_body:
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
                    dic['status2']=mr.compounder_reject_flag
            inbox.append(dic)
            
        return JsonResponse({'status':1, 'relief': inbox})
    
    elif 'get_application' in request_body:
        inbox_files=view_inbox(username=request.user.username,designation='Compounder',src_module='health_center')
        medicalrelief=medical_relief.objects.all()
        relief_id = request_body['aid']
        inbox=[]
        for ib in inbox_files:
            if int(ib['id']) == int(relief_id) :
                dic={}
                for mr in medicalrelief:
                    if mr.file_id==int(ib['id']):   
                        dic['id']=ib['id'] 
                        dic['uploader']=ib['uploader']                   
                        dic['upload_date']=datetime.fromisoformat(ib['upload_date']).date()                   
                        dic['desc']=mr.description
                        # dic['file']=view_file(file_id=ib['id'])['upload_file']
                        status = "Pending"
                        if mr.acc_admin_forward_flag :
                            status = "Approved"
                        elif mr.compounder_forward_flag :
                            status = "Forwarded"
                        elif mr.compounder_reject_flag :
                            status = "Rejected"
                        dic['status']=status
                    inbox.append(dic)
        return JsonResponse({'status':1,'inbox':inbox[0]})
    
    elif 'get_doctors' in request_body :
        doctors = Doctor.objects.filter(active=True).order_by('id')
        serializer = serializers.DoctorSerializer(doctors,many=True)
        return JsonResponse({ 'status':1 , 'doctors':serializer.data })
    
    elif 'get_pathologists' in request_body :
        pathologists = Pathologist.objects.filter(active=True).order_by('id')
        serializer = serializers.PathologistSerializer(pathologists,many=True)
        return JsonResponse({'status':1,'pathologists':serializer.data})
    
    elif 'get_doctor_schedule' in request_body :
        # schedule=Doctors_Schedule.objects.select_related('doctor_id').all().order_by('day','doctor_id')
        doctors=Doctor.objects.filter(active=True).order_by('id')
        schedules = []
        for doctor in doctors :
            obj1 = {}
            schedule = Doctors_Schedule.objects.filter(doctor_id = doctor.id)
            availability = []
            for sch in schedule : 
                obj = {}
                obj['day'] = sch.day
                obj['time'] = str(convert_to_am_pm(str(sch.from_time))) + "-" +str(convert_to_am_pm(str(sch.to_time)))
                availability.append(obj)
            obj1['name'] = doctor.doctor_name
            obj1['specialization'] = doctor.specialization
            obj1['availability'] = availability
            schedules.append(obj1)
                        
        return JsonResponse({ 'status':1, 'schedule':schedules })
    
    elif 'get_pathologist_schedule' in request_body :
        # schedule=Doctors_Schedule.objects.select_related('doctor_id').all().order_by('day','doctor_id')
        pathologists=Pathologist.objects.filter(active=True).order_by('id')
        schedules = []
        for pathologist in pathologists :
            obj1 = {}
            schedule = Pathologist_Schedule.objects.filter(pathologist_id = pathologist.id)
            availability = []
            for sch in schedule : 
                obj = {}
                obj['day'] = sch.day
                obj['time'] = str(convert_to_am_pm(str(sch.from_time))) + "-" +str(convert_to_am_pm(str(sch.to_time)))
                availability.append(obj)
            obj1['name'] = pathologist.pathologist_name
            obj1['specialization'] = pathologist.specialization
            obj1['availability'] = availability
            schedules.append(obj1)
                        
        return JsonResponse({ 'status':1, 'schedule':schedules })
        
        

    elif 'add_stock' in request_body:
        try:
            id = request_body['medicine_id']
            medicine_id = All_Medicine.objects.get(id = id)
            qty = int(request_body['quantity'])
            supplier=request_body['supplier']
            expiry=request_body['expiry_date']
            tot_rows = Stock_entry.objects.all().count()
            tot_rows1 = Present_Stock.objects.all().count()
            stk=Stock_entry.objects.create(
                id = tot_rows+1,
                quantity=qty,
                medicine_id=medicine_id,
                supplier=supplier,
                Expiry_date=expiry,
                date=date.today()
            )
            Present_Stock.objects.create(
                id = tot_rows1+1,
                quantity=qty,
                stock_id=stk,
                medicine_id=medicine_id,
                Expiry_date=expiry
            )
            if Required_medicine.objects.filter(medicine_id = medicine_id).exists():
                req=Required_medicine.objects.get(medicine_id = medicine_id)
                req.quantity+=qty
                if(req.quantity<req.threshold) : req.save()
                else : req.delete() 
            status=1
        except:
            status=0
        finally:
            data = {'status': status,'medicine':medicine_id.brand_name,'supplier':supplier,'expiry_date':expiry,'quantity':qty}
            return JsonResponse(data)
    # edit Threshold
    elif 'edit_threshold' in request_body:
        try:
            medicine_id = request_body['medicine_id']
            new_threshold = int(request_body['threshold'])
            threshold_med=All_Medicine.objects.get(id = medicine_id)
            threshold_med.threshold=new_threshold
            threshold_med.save()
            if Required_medicine.objects.filter(medicine_id = threshold_med).exists():
                Req=Required_medicine.objects.get(medicine_id = threshold_med)
                Req.threshold = threshold_med.threshold
                if Req.quantity > Req.threshold :
                    Req.delete()
                else : Req.save()
            else :
                medicine_stock = Present_Stock.objects.filter(Q(medicine_id = threshold_med) & Q(Expiry_date__gt = date.today()))
                qty=0
                for med in medicine_stock:
                    qty+=med.quantity
                if qty < threshold_med.threshold :
                    Required_medicine.objects.create(
                        medicine_id = threshold_med,
                        quantity = qty,
                        threshold = threshold_med.threshold 
                    )
            status=1
        except:
            status=0
        finally:
            data={'status':status}
            return JsonResponse(data)
    # edit schedule for doctors
    elif 'edit_1' in request_body:                                             
        doctor = request_body['doctor']
        day = request_body['day']
        time_in = request_body['time_in']
        time_out = request_body['time_out']
        room = request_body['room']
        schedule = Doctors_Schedule.objects.select_related('doctor_id').filter(doctor_id=doctor, day=day)
        doctor_id = Doctor.objects.get(id=doctor)
        if schedule.count() == 0:
            Doctors_Schedule.objects.create(doctor_id=doctor_id, day=day, room=room,
                                    from_time=time_in, to_time=time_out)
        else:
            Doctors_Schedule.objects.select_related('doctor_id').filter(doctor_id=doctor_id, day=day).update(room=room)
            Doctors_Schedule.objects.select_related('doctor_id').filter(doctor_id=doctor_id, day=day).update(from_time=time_in)
            Doctors_Schedule.objects.select_related('doctor_id').filter(doctor_id=doctor_id, day=day).update(to_time=time_out)
        data={'status':1}
        return JsonResponse(data)


    # remove schedule for a doctor
    elif 'rmv' in request_body:  
        doctor = request_body['doctor']
        day = request_body['day']
        Doctors_Schedule.objects.select_related('doctor_id').filter(doctor_id=doctor, day=day).delete()
        data = {'status': 1}
        return JsonResponse(data)
    
    
     # edit schedule for pathologists
    elif 'edit12' in request_body:                                             
        doctor = request_body['pathologist']
        day = request_body['day']
        time_in = request_body['time_in']
        time_out = request_body['time_out']
        room = request_body['room']
        pathologist_id = Pathologist.objects.get(id=doctor)
        schedule = Pathologist_Schedule.objects.select_related('pathologist_id').filter(pathologist_id=doctor, day=day)
        if schedule.count() == 0:
            Pathologist_Schedule.objects.create(pathologist_id=pathologist_id, day=day, room=room,
                                    from_time=time_in, to_time=time_out)
        else:
            Pathologist_Schedule.objects.select_related('pathologist_id').filter(pathologist_id=pathologist_id, day=day).update(room=room)
            Pathologist_Schedule.objects.select_related('pathologist_id').filter(pathologist_id=pathologist_id, day=day).update(from_time=time_in)
            Pathologist_Schedule.objects.select_related('pathologist_id').filter(pathologist_id=pathologist_id, day=day).update(to_time=time_out)
        data={'status':1}
        return JsonResponse(data)
    
    
    # remove schedule for a doctor
    elif 'rmv1' in request_body:  
        doctor = request_body['pathologist']
        day = request_body['day']
        Pathologist_Schedule.objects.select_related('pathologist_id').filter(pathologist_id=doctor, day=day).delete()
        data = {'status': 1}
        return JsonResponse(data)
    

    elif 'add_medicine' in request_body:
        medicine = request_body['new_medicine']
        # quantity = request.POST.get('new_quantity')
        threshold = request_body['threshold']
        brand_name = request_body['brand_name']
        constituents = request_body['constituents']
        manufacture_name = request_body['manufacture_name']
        packsize = request_body['packsize']
        # new_supplier = request.POST.get('new_supplier')
        # new_expiry_date = request.POST.get('new_expiry_date')
        tot_rows = All_Medicine.objects.all().count()
        All_Medicine.objects.create(
            id = tot_rows+1,
            medicine_name=medicine,
            brand_name=brand_name,
            constituents=constituents,
            threshold=threshold,
            manufacturer_name=manufacture_name,
            pack_size_label=packsize
        )
        # Stock.objects.create(
        #     medicine_name=medicine,
        #     quantity=quantity,
        #     threshold=threshold
        # )
        # medicine_id = Stock.objects.get(medicine_name=medicine)
        # Expiry.objects.create(
        #     medicine_id=medicine_id,
        #     quantity=quantity,
        #     supplier=new_supplier,
        #     expiry_date=new_expiry_date,
        #     returned=False,
        #     return_date=None,
        #     date=datetime.now()
        # )
        data = {'medicine':  medicine, 'threshold': threshold,}
        return JsonResponse(data)
    
    elif 'get_prescription' in request_body:
        prescription_id = request_body['presc_id']
        prescription = All_Prescription.objects.get(id=prescription_id)
        pre_medicine = All_Prescribed_medicine.objects.filter(prescription_id=prescription)
        doctors=Doctor.objects.filter(active=True).order_by('id')
        follow_presc =Prescription_followup.objects.filter(prescription_id=prescription).order_by('-id')
        prescriptions=[]
        for f_presc in follow_presc:
            obj={}
            obj['id'] = f_presc.id
            obj['doctor'] = f_presc.Doctor_id.doctor_name
            obj['diseaseDetails'] = f_presc.details
            obj['followUpDate'] = f_presc.date
            revoked=[]
            for med in pre_medicine :
                if med.revoked == True and med.revoked_prescription.id == f_presc.id :
                    obj1={}
                    obj1['medicine'] = med.medicine_id.brand_name
                    obj1['quantity'] = med.quantity
                    obj1['days'] = med.days
                    obj1['times'] = med.times
                    revoked.append(obj1)
            obj['revoked_medicines'] = revoked
            presc_med = []
            for med in pre_medicine :
                if med.prescription_followup_id == f_presc :
                    obj1={}
                    obj1['medicine'] = med.medicine_id.brand_name
                    obj1['quantity'] = med.quantity
                    obj1['days'] = med.days
                    obj1['times'] = med.times
                    presc_med.append(obj1)
            obj['medicines'] = presc_med
            tests = "No Test suggested"
            if f_presc.test!="" :
                tests = f_presc.test
            obj['tests'] = tests
            obj['file_id'] = f_presc.file_id
            prescriptions.append(obj)
        obj={}
        obj['id'] = 0
        obj['doctor'] = prescription.doctor_id.doctor_name
        obj['diseaseDetails'] = prescription.details
        obj['followUpDate'] = prescription.date
        revoked=[]
        obj['revoked_medicines'] = revoked
        presc_med = []
        for med in pre_medicine :
            if med.prescription_followup_id == None :
                obj1={}
                obj1['medicine'] = med.medicine_id.brand_name
                obj1['quantity'] = med.quantity
                obj1['days'] = med.days
                obj1['times'] = med.times
                presc_med.append(obj1)
        obj['medicines'] = presc_med
        tests = "No Test suggested"
        if prescription.test!="" :
            tests = prescription.test
        obj['tests'] = tests
        obj['file_id'] = prescription.file_id
        prescriptions.append(obj)
        presc_serializer = serializers.PrescriptionSerializer(prescription)
        
        not_revoked=[]
        for med in pre_medicine:
            if med.revoked==False:
                obj1={}
                obj1['id'] = med.id
                obj1['medicine'] = med.medicine_id.brand_name
                obj1['quantity'] = med.quantity
                obj1['days'] = med.days
                obj1['times'] = med.times
                not_revoked.append(obj1)
        return JsonResponse({'status':1, 'prescription':presc_serializer.data, 'prescriptions':prescriptions , 'not_revoked' : not_revoked})



    elif 'get_stock' in request_body:
        try:
            medicine_name_and_id = request_body['medicine_name_for_stock']
            medicine_name = medicine_name_and_id.split(",")[0]
            id=0
            if(len(medicine_name_and_id.split(",")) > 1) :
                id=medicine_name_and_id.split(",")[1]
            if id == 0:
                status=1
                similar_name_qs = All_Medicine.objects.filter(brand_name__istartswith=medicine_name)[:10]
            else :
                status=2
                similar_name_qs = All_Medicine.objects.filter(id=id)
            similar_name = list(similar_name_qs.values('id', 'medicine_name','constituents','manufacturer_name','pack_size_label','brand_name','threshold'))
            val_to_return = []

            try:
                med = All_Medicine.objects.get(id = id)
                stk = Stock_entry.objects.filter(medicine_id=med).order_by('Expiry_date')
                for s in stk:
                    if s.Expiry_date > date.today():
                        obj = {}
                        obj['brand_name'] = s.medicine_id.brand_name
                        obj['supplier'] = s.supplier
                        obj['expiry'] = s.Expiry_date
                        p_s = Present_Stock.objects.get(stock_id=s)
                        if p_s.quantity > 0:
                            obj['quantity'] = p_s.quantity
                            obj['id'] = p_s.id
                            val_to_return.append(obj)
            except All_Medicine.DoesNotExist:
                val_to_return = []
            except Present_Stock.DoesNotExist:
                val_to_return = []
        except Exception as e:
            val_to_return = []
        finally:
            return JsonResponse({"val": val_to_return, "sim": similar_name, "status": status})
    elif 'medicine_name_b' in request.POST:
        user_id = request.POST.get('user')
        if not User.objects.filter(username__iexact = user_id).exists():
            return JsonResponse({"status":-2}) 
        quantity = int(request.POST.get('quantity'))
        days = int(request.POST.get('days'))
        times = int(request.POST.get('times'))
        medicine_id = request.POST.get('medicine_name_b')
        stock = request.POST.get('stock')
        medicine_brand_name = medicine_id.split(",")[0]
        id= medicine_id.split(",")[1]
        med_name = All_Medicine.objects.get(id=id).brand_name
        if(stock == "" or stock == "N/A at moment") :
            return JsonResponse({"status":1,"med_name":med_name,"id":id})
        stk=stock.split(",")
        qty = int(stk[2])
        status=1
        if quantity>qty : status=0
        return JsonResponse({"status":status,"med_name":med_name,"id":id})
    

    elif 'user_for_dependents' in request_body:
        user = request_body['user_for_dependents']
        if not User.objects.filter(username__iexact = user).exists():
            return JsonResponse({"status":-1})
        user_id = User.objects.get(username__iexact = user)
        info = ExtraInfo.objects.get(user = user_id)
        dep_info = EmpDependents.objects.filter(extra_info = info)
        dep=[]
        for d in dep_info:
            obj={}
            obj['name'] = d.name
            obj['relation'] = d.relationship 
            dep.append(obj)
        if(len(dep) == 0) :
            return JsonResponse({'status':-2})
        return JsonResponse({'status':1,'dep':dep}) 
    elif 'prescribe_b' in request_body:
        user_id = request_body['user']
        doctor_id = request_body['doctor']
        if not User.objects.filter(username__iexact = user_id).exists():
            return JsonResponse({"status":-1}) 
        if doctor_id == 'null' :
            doctor = None
        else:
            doctor = Doctor.objects.get(doctor_name=doctor_id)

        
        is_dependent=request_body['is_dependent']
        fid=0
        # uploaded_file = request.FILES.get('file')
        # if uploaded_file != None :
        #     f=uploaded_file.read()
        #     new_file=files.objects.create(
        #         file_data=f
        #     )
        #     fid=new_file.id
        # with open(uploaded_file.name, 'wb+') as destination:   
        #         destination.write(f)  
        if is_dependent == "self":
            pres=All_Prescription.objects.create(
                user_id = user_id,
                doctor_id=doctor,
                details = request_body['details'], 
                date=date.today(),
                test=request_body['tests'],
                file_id=fid
            )
        else :
            pres=All_Prescription.objects.create(
                user_id = user_id,
                doctor_id=doctor,
                details = request_body['details'], 
                date=date.today(),
                test=request_body['tests'],
                is_dependent = True,
                dependent_name = request_body['dependent_name'],
                dependent_relation = request_body['dependent_relation'],
                file_id=fid
            )
        # designation=request.POST.get('user')
        # d = HoldsDesignation.objects.get(user__username=designation)
        # send_file_id = create_file(
        #     uploader=request.user.username,
        #     uploader_designation=request.session['currentDesignationSelected'],
        #     receiver=designation,
        #     receiver_designation=d.designation,
        #     src_module="health_center",
        #     src_object_id=str(pres.id),
        #     file_extra_JSON={"value": 2},
        #     attached_file=uploaded_file  
        # )
        # pres.file_id=send_file_id
        # pres.save()

        medicine = request_body['pre_medicine']

        for med in medicine:
            med_name = med["brand_name"]
            id=med_name.split(",")[1]
            quant = int(med['quantity'])
            days = med['Days'] 
            times = med['Times']
            stock = med['astock']
            med_id = All_Medicine.objects.get(id=id)
            if(stock == "," or stock == 'N/A at moment,') :
                All_Prescribed_medicine.objects.create(
                    prescription_id = pres,
                    medicine_id = med_id,
                    quantity = quant,
                    days = days,
                    times=times
                )
            else :
                stk = stock.split(",")
                p_stock = Present_Stock.objects.get(id=int(stk[1]))
                All_Prescribed_medicine.objects.create(
                    prescription_id = pres,
                    medicine_id = med_id,
                    stock = p_stock,
                    quantity = quant,
                    days = days,
                    times=times
                )
                p_stock.quantity -= quant
                p_stock.save()
                stock_of_medicine = Present_Stock.objects.filter(Q(medicine_id = med_id) & Q( Expiry_date__gt = date.today()))
                qty=0
                for stk in stock_of_medicine :
                    qty+=stk.quantity

                if qty<med_id.threshold :
                    if Required_medicine.objects.filter(medicine_id = med_id).exists():
                        req= Required_medicine.objects.get(medicine_id = med_id)
                        req.quantity = qty
                        req.save()
                    else :
                        Required_medicine.objects.create(
                            medicine_id = med_id,
                            quantiy = qty,
                            threshold = med_id.threshold
                        )
        # pre_medicine = request.POST.get_json('pre_medicine')
        # print(pre_medicine)
        # details = request.POST.get('details')
        # tests = request.POST.get('tests')
        # # app = Appointment.objects.select_related('user_id','user_id__user','user_id__department','doctor_id','schedule','schedule__doctor_id').filter(user_id=user_id,date=datetime.now())
        # # if app:
        # #     appointment = Appointment.objects.select_related('user_id','user_id__user','user_id__department','doctor_id','schedule','schedule__doctor_id').get(user_id=user_id,date=datetime.now())
        # # else:
        # #     appointment = None
        # form_object=Prescription(
        #     user_id=user,
        #     doctor_id=doctor,
        #     details=details,
        #     date=datetime.now(),
        #     test=tests,          
        #     # appointment=appointment
        # )
        # form_object.save()

        # request_object.save()
        
        # query = Medicine.objects.select_related('patient','patient__user','patient__department').filter(patient=user)
        # prescribe = Prescription.objects.select_related('user_id','user_id__user','user_id__department','doctor_id').all().last()
        # for medicine in query:
        #     medicine_id = medicine.medicine_id
        #     quantity = medicine.quantity
        #     days = medicine.days
        #     times = medicine.times
        #     Prescribed_medicine.objects.create(
        #         prescription_id=prescribe,
        #         medicine_id=medicine_id,
        #         quantity=quantity,
        #         days=days,
        #         times=times
        #     )
        #     today=datetime.now()
        #     expiry=Expiry.objects.select_related('medicine_id').filter(medicine_id=medicine_id,quantity__gt=0,returned=False,expiry_date__gte=today).order_by('expiry_date')
        #     stock=Stock.objects.get(medicine_name=medicine_id).quantity
        #     if stock>quantity:
        #         for e in expiry:
        #             q=e.quantity
        #             em=e.id
        #             if q>quantity:
        #                 q=q-quantity
        #                 Expiry.objects.select_related('medicine_id').filter(id=em).update(quantity=q)
        #                 qty = Stock.objects.get(medicine_name=medicine_id).quantity
        #                 qty = qty-quantity
        #                 Stock.objects.filter(medicine_name=medicine_id).update(quantity=qty)
        #                 break
        #             else:
        #                 quan=Expiry.objects.select_related('medicine_id').get(id=em).quantity
        #                 Expiry.objects.select_related('medicine_id').filter(id=em).update(quantity=0)
        #                 qty = Stock.objects.get(medicine_name=medicine_id).quantity
        #                 qty = qty-quan
        #                 Stock.objects.filter(medicine_name=medicine_id).update(quantity=qty)
        #                 quantity=quantity-quan
        #         status = 1

        #     else:
        #         status = 0
            # Medicine.objects.select_related('patient','patient__user','patient__department').all().delete()
          

        # healthcare_center_notif(request.user, user.user, 'presc','')
        # data = {'status': status}
        # return JsonResponse(data)
        return JsonResponse({"status":1})
    
    elif 'presc_followup' in request_body:
        pre_id=request_body["pre_id"]
        presc = All_Prescription.objects.get(id=int(pre_id))

        doctor_id = request_body['doctor']
        if doctor_id == 'null' :
            doctor = None
        else:
            doctor = Doctor.objects.get(doctor_name=doctor_id)
        
        fid=0
        # uploaded_file = request.FILES.get('file')
        # if uploaded_file != None :
        #     f=uploaded_file.read()
        #     new_file=files.objects.create(
        #         file_data=f
        #     )
        #     fid=new_file.id

        followup = Prescription_followup.objects.create(
            prescription_id=presc,
            Doctor_id=doctor,
            details = request_body['details'],
            test = request_body['tests'],
            date = date.today(),
            file_id = fid
        )
        medicine= request_body['pre_medicine']
        for med in medicine:
            med_name = med["brand_name"]
            id = med_name.split(',')[1]
            quant = int(med['quantity'])
            days = med['Days'] 
            times = med['Times']
            stock = med['astock']
            med_id = All_Medicine.objects.get(id = id)
            if(stock == ',' or stock == "N/A at moment,"):
                All_Prescribed_medicine.objects.create(
                    prescription_id = presc,
                    medicine_id = med_id,
                    quantity = quant,
                    days = days,
                    times=times,
                    prescription_followup_id = followup
                )
            else :    
                stk = stock.split(",")
                p_stock = Present_Stock.objects.get(id=int(stk[1]))
                All_Prescribed_medicine.objects.create(
                    prescription_id = presc,
                    medicine_id = med_id,
                    stock = p_stock,
                    quantity = quant,
                    days = days,
                    times=times,
                    prescription_followup_id = followup
                )
                p_stock.quantity -= quant
                p_stock.save()
                stock_of_medicine = Present_Stock.objects.filter(Q(medicine_id = med_id) & Q(Expiry_date__gt = date.today()))
                qty=0
                for stk in stock_of_medicine :
                    qty+=stk.quantity

                if qty<med_id.threshold :
                    if Required_medicine.objects.filter(medicine_id = med_id).exists():
                        req= Required_medicine.objects.get(medicine_id = med_id)
                        req.quantity = qty
                        req.save()
                    else :
                        Required_medicine.objects.create(
                            medicine_id = med_id,
                            quantity = qty,
                            threshold = med_id.threshold
                        )
        r_medicine = request_body['revoked']
        for med in r_medicine:
            presc_med_id = All_Prescribed_medicine.objects.get(id=int(med))
            presc_med_id.revoked = True
            presc_med_id.revoked_date = date.today()
            presc_med_id.revoked_prescription = followup
            presc_med_id.save()
        
        return JsonResponse({"status":1})
    
    elif 'add_medicine_excel' in request.POST:
        excel_file = request.FILES.get('file')
        df = pd.read_excel(excel_file)
        tot_rows = All_Medicine.objects.all().count()
        t = 1
        try:
            required_columns = ['medicine_name', 'brand_name', 'manufacturer_name', 'packsize', 'constituents' , 'threshold']
            if not all(column in df.columns for column in required_columns):
                return JsonResponse({"status":0})
            with transaction.atomic():
                for _, row in df.iterrows():
                    All_Medicine.objects.create(
                        id = tot_rows+t,
                        medicine_name=row['medicine_name'],
                        brand_name=row['brand_name'],
                        manufacturer_name=row['manufacturer_name'],
                        pack_size_label=row['packsize'],
                        constituents = row['constituents'],
                        threshold = row['threshold']
                    )
                    t+=1
            return JsonResponse({"status":1})
        except Exception as e:
            return JsonResponse({"status":0})

    elif 'add_stock_excel' in request.POST:
        excel_file = request.FILES.get('file')
        df = pd.read_excel(excel_file)
        try:
            tot_rows = All_Medicine.objects.all().count()
            tot_rows1 = Present_Stock.objects.all().count()
            t = 1
            required_columns = ['brand_name', 'manufacturer_name', 'packsize','quantity','supplier','Expiry_date']
            if not all(column in df.columns for column in required_columns):
                return JsonResponse({"status":0})
            with transaction.atomic():
                for _, row in df.iterrows():
                    med=All_Medicine.objects.get(
                        Q(brand_name=row['brand_name']) & Q(manufacturer_name=row['manufacturer_name']) & Q(pack_size_label=row['packsize'])
                    )
                    stk=Stock_entry.objects.create(
                        id = tot_rows+t,
                        quantity=row['quantity'],
                        medicine_id=med,
                        supplier=row['supplier'],
                        Expiry_date=row['Expiry_date'],
                        date=date.today()
                    )
                    Present_Stock.objects.create(
                        id = tot_rows1+t,
                        quantity=row['quantity'],
                        stock_id=stk,
                        medicine_id=med,
                        Expiry_date=row['Expiry_date'],
                    )
                    t+=1
                    if Required_medicine.objects.filter(medicine_id = med).exists():
                        req=Required_medicine.objects.get(medicine_id = med)
                        req.quantity+=qty
                        if(req.quantity<req.threshold) : req.save()
                        else : req.delete() 
            return JsonResponse({"status":1})
        except Exception as e:
            return JsonResponse({"status":0})

    elif 'medicine' in request.POST:
        med_id = request.POST.get('medicine')
        try:
            thresh = All_Medicine.objects.get(brand_name=med_id).threshold
        except:
            thresh = ""
        data = {'thresh': thresh}
        return JsonResponse(data)
    elif 'compounder_forward' in request_body:
        acc_admin_des_id = Designation.objects.get(name="Accounts Admin")        
        user_ids = HoldsDesignation.objects.filter(designation_id=acc_admin_des_id.id).values_list('user_id', flat=True)    
        acc_admins = ExtraInfo.objects.get(user_id=user_ids[0])
        user=ExtraInfo.objects.get(pk=acc_admins.id)
        forwarded_file_id=forward_file(
            file_id=request_body['file_id'],
            receiver=acc_admins.id, 
            receiver_designation="Accounts Admin",
            file_extra_JSON= {"value": 2},            
            remarks="Forwarded File with id: "+ str(request_body['file_id'])+"to Accounts Admin "+str(acc_admins.id), 
            file_attachment=None,
        )
       
        medical_relief_instance = medical_relief.objects.get(file_id=request_body['file_id'])        
        medical_relief_instance.compounder_forward_flag = True
        medical_relief_instance.save()        
        healthcare_center_notif(request.user,user.user,'rel_approve','')      
        data = {'status': 1}
        return JsonResponse(data)
    elif 'compounder_reject' in request_body:
        file_id = request_body['file_id']
        relief = medical_relief.objects.get(file_id=file_id)
        relief.compounder_reject_flag = True
        relief.save()
        rejected_user = request_body['rejected_user']
        user=User.objects.get(username__iexact = rejected_user)
        rejected_user_info = ExtraInfo.objects.get(user_id = user)
        healthcare_center_notif(request.user,rejected_user_info.user,'reject_relief','')
        data = {'status': 1}
        return JsonResponse(data)
    elif 'comp_announce' in request_body:
        usrnm = get_object_or_404(User, username=request.user.username)
        user_info = ExtraInfo.objects.all().select_related('user','department').filter(user=usrnm).first()
        num = 1
        ann_anno_id = user_info.id        
        formObject = Announcements()       
        user_info = ExtraInfo.objects.all().select_related('user','department').get(id=ann_anno_id)
        getstudents = ExtraInfo.objects.select_related('user')
        recipients = User.objects.filter(extrainfo__in=getstudents)       
        formObject.anno_id=user_info     
        formObject.message = request_body['announcement']
        formObject. upload_announcement = request.FILES.get('upload_announcement')       
        formObject.ann_date = date.today()     
        formObject.save()
        print("before")
        healthcare_center_notif(usrnm, recipients , 'new_announce',formObject.message )
        print("after")
        data = {'status': 1}
        return JsonResponse(data)
    elif 'datatype' in request_body and request_body['datatype'] == 'patientlog':
                 search = request_body['search_patientlog']
                 page_size = 2
                 new_current_page = int(request_body['page'])
                 new_offset = (new_current_page - 1) * page_size
                 new_report = []
                 new_prescriptions = All_Prescription.objects.filter(Q(user_id__icontains = search) | Q(details__icontains = search)).order_by('-date', '-id')[new_offset:new_offset + page_size]
                 total_count = All_Prescription.objects.filter(Q(user_id__icontains = search) | Q(details__icontains = search)).count()
                 total_pages = (total_count + page_size - 1) // page_size
                 for pre in new_prescriptions:
                      doc = None
                      if pre.doctor_id != None : doc=pre.doctor_id.doctor_name 
                      dic = {
                          'id': pre.pk,
                          'user_id': pre.user_id,
                          'date': pre.date,
                          'doctor_id':doc,
                          'details': pre.details,
                          'test': pre.test,
                          'file_id': pre.file_id,
                          # 'file': view_file(file_id=pre.file_id)['upload_file'] if pre.file_id else None
                      }
                      new_report.append(dic)
                 return JsonResponse({
                         'report': new_report,
                         'page': new_current_page,
                         'total_pages': total_pages,
                         'has_previous': new_current_page > 1,
                         'has_next': new_current_page < total_pages,
                         'previous_page_number': new_current_page - 1 if new_current_page > 1 else None,
                         'next_page_number': new_current_page + 1 if new_current_page < total_pages else None,
                         })     
    elif 'datatype' in request_body and request_body['datatype'] == 'manage_stock_view':
                search = request_body['search_view_stock']
                page_size_stock = 2
                new_current_page_stock = int(request_body['page_stock_view'])
                new_offset_stock = (new_current_page_stock - 1) * page_size_stock
                new_live_meds = []
                new_live =Stock_entry.objects.filter(Q(Expiry_date__gte=date.today()) & Q( Q(medicine_id__brand_name__icontains = search) | Q(supplier__icontains = search))).order_by('Expiry_date')[new_offset_stock:new_offset_stock + page_size_stock]
                total_pages_stock = ( Stock_entry.objects.filter(Q(Expiry_date__gte=date.today()) & Q( Q(medicine_id__brand_name__icontains = search) | Q(supplier__icontains = search))).count()  + page_size_stock - 1) // page_size_stock
                for e in new_live:
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
                    new_live_meds.append(obj)
                return JsonResponse({
                        'report_stock_view': new_live_meds,
                        'page_stock_view': new_current_page_stock,
                        'total_pages_stock_view': total_pages_stock,
                        'has_previous': new_current_page_stock > 1,
                        'has_next': new_current_page_stock < total_pages_stock,
                        'previous_page_number': new_current_page_stock - 1 if new_current_page_stock > 1 else None,
                        'next_page_number': new_current_page_stock + 1 if new_current_page_stock < total_pages_stock else None,
                        })
    elif 'datatype' in request_body and request_body['datatype'] == 'manage_stock_expired':
                search = request_body['search_view_expired']
                new_page_size_stock_expired = 2
                new_current_page_stock_expired = int(request_body['page_stock_expired'])
                new_offset_stock_expired = (new_current_page_stock_expired - 1 )* new_page_size_stock_expired
                new_expired=[]
                new_expiredData=Stock_entry.objects.filter(Q(Expiry_date__lt=date.today())&Q( Q(medicine_id__brand_name__icontains = search) | Q(supplier__icontains = search))).order_by('Expiry_date')[new_offset_stock_expired:new_offset_stock_expired + new_page_size_stock_expired]
                new_total_pages_stock_expired = ( Stock_entry.objects.filter(Q(Expiry_date__lt=date.today())&Q( Q(medicine_id__brand_name__icontains = search) | Q(supplier__icontains = search))).count()  + new_page_size_stock_expired - 1) // new_page_size_stock_expired
                for e in new_expiredData:
                    obj={}
                    obj['medicine_id']=e.medicine_id.brand_name
                    obj['Expiry_date']=e.Expiry_date
                    obj['supplier']=e.supplier
                    try:
                        qty=Present_Stock.objects.get(stock_id=e).quantity
                    except:
                        qty=0
                    obj['quantity']=qty
                    new_expired.append(obj)
                return JsonResponse({
                         'report_stock_expired': new_expired,
                         'page_stock_expired': new_current_page_stock_expired,
                         'total_pages_stock_view': new_total_pages_stock_expired,
                         'has_previous': new_current_page_stock_expired > 1,
                         'has_next': new_current_page_stock_expired < new_total_pages_stock_expired,
                         'previous_page_number': new_current_page_stock_expired - 1 if new_current_page_stock_expired > 1 else None,
                         'next_page_number': new_current_page_stock_expired + 1 if new_current_page_stock_expired < new_total_pages_stock_expired else None,
                         })
    elif 'datatype' in request_body and request_body['datatype'] == 'manage_stock_required':
                search = request_body['search_view_required']
                new_page_size_stock_required = 2
                new_current_page_stock_required = int(request_body['page_stock_required'])
                new_offset_stock_required = (new_current_page_stock_required - 1 )* new_page_size_stock_required
                new_required=[]
                new_requiredData=Required_medicine.objects.filter( Q(medicine_id__brand_name__icontains = search))[new_offset_stock_required:new_offset_stock_required + new_page_size_stock_required]
                new_total_pages_stock_required = (Required_medicine.objects.filter( Q(medicine_id__brand_name__icontains = search)).count() + new_page_size_stock_required - 1) // new_page_size_stock_required
                for e in new_requiredData:
                    obj={}
                    obj['medicine_id']=e.medicine_id.brand_name
                    obj['quantity']=e.quantity
                    obj['threshold']=e.threshold 
                    new_required.append(obj)
                return JsonResponse({
                         'report_stock_required': new_required,
                         'page_stock_required': new_current_page_stock_required,
                         'total_pages_stock_required': new_total_pages_stock_required,
                         'has_previous': new_current_page_stock_required > 1,
                         'has_next': new_current_page_stock_required < new_total_pages_stock_required,
                         'previous_page_number': new_current_page_stock_required - 1 if new_current_page_stock_required > 1 else None,
                         'next_page_number': new_current_page_stock_required + 1 if new_current_page_stock_required < new_total_pages_stock_required else None,
                         })
    
    elif 'search_patientlog' in request.POST:
        search = request.POST.get('search_patientlog')
        current_page = 1
        page_size_prescription = 2  # Default to 2 if not specified
        offset = (current_page - 1) * page_size_prescription
        prescriptions = All_Prescription.objects.filter(Q(user_id__icontains = search) | Q(details__icontains = search)).order_by('-date', '-id')[offset:offset + page_size_prescription]
            
        report = []
        for pre in prescriptions:
            doc = None
            if pre.doctor_id != None : doc=pre.doctor_id.doctor_name
            dic = {
                'id': pre.pk,
                'user_id': pre.user_id,
                'doctor_id': doc,
                'date': pre.date,
                'details': pre.details,
                'test': pre.test,
                'file_id': pre.file_id,
                    # 'file': view_file(file_id=pre.file_id)['upload_file'] if pre.file_id else None
                }
            report.append(dic)
            # Handle total count for pagination context
        total_count = All_Prescription.objects.filter(Q(user_id__icontains = search) | Q(details__icontains = search)).count()
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
        return JsonResponse({'status':1,"presc_context":prescContext})
    elif 'search_view_stock' in request.POST:
        search = request.POST.get('search_view_stock')
        current_page_stock = 1
        page_size_stock = 2
        offset_stock = (current_page_stock - 1 )* page_size_stock
        live_meds=[]
        live=Stock_entry.objects.filter(Q(Expiry_date__gte=date.today()) & Q( Q(medicine_id__brand_name__icontains = search) | Q(supplier__icontains = search))).order_by('Expiry_date')[offset_stock:offset_stock + page_size_stock]
        total_pages_stock = ( Stock_entry.objects.filter(Q(Expiry_date__gte=date.today()) & Q(Q(medicine_id__brand_name__icontains = search) | Q(supplier__icontains = search))).count()  + page_size_stock - 1) // page_size_stock
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
        return JsonResponse({'status':1,'stock_context':stockContext})
    elif 'search_view_expired' in request.POST:
        search = request.POST.get('search_view_expired')
        current_page_stock_expired = 1
        page_size_stock_expired = 2
        offset_stock_expired = (current_page_stock_expired - 1 )* page_size_stock_expired
        expired=[]
        expiredData=Stock_entry.objects.filter(Q(Expiry_date__lt=date.today())&Q( Q(medicine_id__brand_name__icontains = search) | Q(supplier__icontains = search))).order_by('Expiry_date')[offset_stock_expired:offset_stock_expired + page_size_stock_expired]
        total_pages_stock_expired = ( Stock_entry.objects.filter(Q(Expiry_date__lt=date.today())&Q( Q(medicine_id__brand_name__icontains = search) | Q(supplier__icontains = search))).count()  + page_size_stock_expired - 1) // page_size_stock_expired
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
        return JsonResponse({'status':1,'expired_context':ExpiredstockContext})
    elif 'search_view_required' in request.POST:
        search = request.POST.get('search_view_required')
        current_required_page = 1
        page_size_required = 2
        offset_stock_required = (current_required_page - 1 )* page_size_required
        required_data = Required_medicine.objects.filter( Q(medicine_id__brand_name__icontains = search) )[offset_stock_required:offset_stock_required + page_size_required]
        total_pages_stock_required = (Required_medicine.objects.filter( Q(medicine_id__brand_name__icontains = search) ).count() + page_size_required -1) // page_size_required
        required=[]
        for e in required_data:
            obj={}
            obj['medicine_id']=e.medicine_id.brand_name
            obj['quantity']=e.quantity
            obj['threshold'] = e.threshold
            required.append(obj)
        stocks = {
            "count_stock_required" : total_pages_stock_required,
            "page_stock_required":{
                "object_list":required, 
                'number' : current_required_page,
                'has_previous' : current_required_page > 1 ,
                'has_next': current_required_page < total_pages_stock_required,
                'previous_page_number' :  current_required_page - 1 if current_required_page > 1 else None,
                'next_page_number' :  current_required_page + 1 if current_required_page < total_pages_stock_required else None,      
            }
        }
        return JsonResponse({'status':1,'stocks':stocks})
    return JsonResponse({'status':1 , 'name':"bharadwaj"})

@api_view(['POST'])
def student_api_handler(request):
    request_body = request.body.decode('utf-8')
    request_body = json.loads(request_body)
    if 'feed_submit' in request_body:
        user_id = ExtraInfo.objects.select_related('user','department').get(user=request.user)
        feedback = request_body['feedback']
        Complaint.objects.create(
            user_id=user_id,
            complaint=feedback,
            date=datetime.now()
        )
        data = {'status': 1}
        healthcare_center_notif(request.user, request.user,'feedback_submitted','')
        
        return JsonResponse(data)

    elif 'medical_relief_submit' in request_body:
        # print(request_body)
        designation = request_body['designation']
        # print("# #")
        # print(designation)
        user=ExtraInfo.objects.get(pk=designation)
        description = request_body['description']
         
        # Retrieve the uploaded file from request.FILES
        # uploaded_file = request.FILES.get('file')

        # Create an instance of the medical_relief model
        form_object = medical_relief(
            description=description,
            # file=uploaded_file
        )

        # Save the form object
        form_object.save()
        
        # Retrieve the form object you just saved
        request_object = medical_relief.objects.get(pk=form_object.pk)
        
        # Retrieve HoldsDesignation instances
        d = HoldsDesignation.objects.get(user__username=designation)
        d1 = HoldsDesignation.objects.get(user__username=request.user)

        # Create a file entry using the create_file utility function
        send_file_id = create_file(
            uploader=request.user.username,
            uploader_designation=request_body['selected_role'],
            receiver=designation,
            receiver_designation=d.designation,
            src_module="health_center",
            src_object_id=str(request_object.id),
            file_extra_JSON={"value": 2},
            # attached_file=uploaded_file  
        )  
        healthcare_center_notif(request.user,user.user,'rel_forward','')
        request_object.file_id = send_file_id
        request_object.save()
        
        # file_details_dict = view_file(file_id=send_file_id)    
        # print(file_details_dict)   
        return JsonResponse({'status': 1})
    
    elif 'get_prescription' in request_body:
        prescription_id = request_body['presc_id']
        prescription = All_Prescription.objects.get(id=prescription_id)
        pre_medicine = All_Prescribed_medicine.objects.filter(prescription_id=prescription)
        doctors=Doctor.objects.filter(active=True).order_by('id')
        follow_presc =Prescription_followup.objects.filter(prescription_id=prescription).order_by('-id')
        prescriptions=[]
        for f_presc in follow_presc:
            obj={}
            obj['id'] = f_presc.id
            obj['doctor'] = f_presc.Doctor_id.doctor_name
            obj['diseaseDetails'] = f_presc.details
            obj['followUpDate'] = f_presc.date
            revoked=[]
            for med in pre_medicine :
                if med.revoked == True and med.revoked_prescription.id == f_presc.id :
                    obj1={}
                    obj1['medicine'] = med.medicine_id.brand_name
                    obj1['quantity'] = med.quantity
                    obj1['days'] = med.days
                    obj1['times'] = med.times
                    revoked.append(obj1)
            obj['revoked_medicines'] = revoked
            presc_med = []
            for med in pre_medicine :
                if med.prescription_followup_id == f_presc :
                    obj1={}
                    obj1['medicine'] = med.medicine_id.brand_name
                    obj1['quantity'] = med.quantity
                    obj1['days'] = med.days
                    obj1['times'] = med.times
                    presc_med.append(obj1)
            obj['medicines'] = presc_med
            tests = "No Test suggested"
            if f_presc.test!="" :
                tests = f_presc.test
            obj['tests'] = tests
            obj['file_id'] = f_presc.file_id
            prescriptions.append(obj)
        obj={}
        obj['id'] = 0
        obj['doctor'] = prescription.doctor_id.doctor_name
        obj['diseaseDetails'] = prescription.details
        obj['followUpDate'] = prescription.date
        revoked=[]
        obj['revoked_medicines'] = revoked
        presc_med = []
        for med in pre_medicine :
            if med.prescription_followup_id == None :
                obj1={}
                obj1['medicine'] = med.medicine_id.brand_name
                obj1['quantity'] = med.quantity
                obj1['days'] = med.days
                obj1['times'] = med.times
                presc_med.append(obj1)
        obj['medicines'] = presc_med
        tests = "No Test suggested"
        if prescription.test!="" :
            tests = prescription.test
        obj['tests'] = tests
        obj['file_id'] = prescription.file_id
        prescriptions.append(obj)
        presc_serializer = serializers.PrescriptionSerializer(prescription)
        
        not_revoked=[]
        for med in pre_medicine:
            if med.revoked==False:
                obj1={}
                obj1['id'] = med.id
                obj1['medicine'] = med.medicine_id.brand_name
                obj1['quantity'] = med.quantity
                obj1['days'] = med.days
                obj1['times'] = med.times
                not_revoked.append(obj1)
        return JsonResponse({'status':1, 'prescription':presc_serializer.data, 'prescriptions':prescriptions , 'not_revoked' : not_revoked})


    elif 'acc_admin_forward' in request.POST:
        file_id=request.POST['file_id']
        rec=File.objects.get(id=file_id)
        des=Designation.objects.get(pk=rec.designation_id)      
        user=ExtraInfo.objects.get(pk=rec.uploader_id)
        
        forwarded_file_id=forward_file(
            file_id=request.POST['file_id'],
            receiver=rec.uploader_id, 
            receiver_designation=des.name,
            file_extra_JSON= {"value": 2},            
            remarks="Forwarded File with id: "+ str(request.POST['file_id'])+"to"+str(rec.id), 
            file_attachment=None,
        )
        medical_relief_instance = medical_relief.objects.get(file_id=request.POST['file_id'])        
        medical_relief_instance.acc_admin_forward_flag = True
        medical_relief_instance.save()
        
        healthcare_center_notif(request.user,user.user,'rel_approved','')
        
        return JsonResponse({'status':1})
        
    elif 'announcement' in request.POST:
        anno_id = request.POST.get('anno_id')
        Announcements.objects.select_related('user_id','user_id__user','user_id__department', 'message', 'upload_announcement').filter(pk=anno_id).delete()
        data = {'status': 1}
        healthcare_center_notif(request.user,user.user,'new_announce','')
        return JsonResponse({'status':1})
    
    elif 'medical_profile' in request.POST:
        user_id = request.POST.get('user_id')
        MedicalProfile.objects.select_related('user_id','user_id__user','user_id__department', 'date_of_birth', 'gender', 'blood_type', 'height', 'weight').filter(pk=user_id).delete()
        data = {'status': 1}
        return JsonResponse({'status':1})
    elif 'datatype' in request_body and request_body['datatype'] == 'patientlog':
                 search = request_body['search_patientlog']
                 print("patient")
                 page_size = 2
                 new_current_page = int(request_body['page'])
                 new_offset = (new_current_page - 1) * page_size
                 new_report = []
                 new_prescriptions = All_Prescription.objects.filter(Q(user_id__iexact = request.user.extrainfo.id) & Q( Q(user_id__icontains = search) | Q(details__icontains = search) | (Q(dependent_name__icontains = search)))).order_by('-date', '-id')[new_offset:new_offset + page_size]
                 total_count = All_Prescription.objects.filter(Q(user_id__iexact = request.user.extrainfo.id) & Q( Q(user_id__icontains = search) | Q(details__icontains = search) | (Q(dependent_name__icontains = search)))).count()
                 total_pages = (total_count + page_size - 1) // page_size
                 for pre in new_prescriptions:
                      doc = None
                      if pre.doctor_id != None : doc=pre.doctor_id.doctor_name 
                      dic = {
                          'id': pre.pk,
                          'user_id': pre.user_id,
                          'date': pre.date,
                          'doctor_id':doc,
                          'details': pre.details,
                          'test': pre.test,
                          'file_id': pre.file_id,
                          'dependent_name':pre.dependent_name
                          # 'file': view_file(file_id=pre.file_id)['upload_file'] if pre.file_id else None
                      }
                      new_report.append(dic)
                 return JsonResponse({
                         'report': new_report,
                         'page': new_current_page,
                         'total_pages': total_pages,
                         'has_previous': new_current_page > 1,
                         'has_next': new_current_page < total_pages,
                         'previous_page_number': new_current_page - 1 if new_current_page > 1 else None,
                         'next_page_number': new_current_page + 1 if new_current_page < total_pages else None,
                         })
    elif 'search_patientlog' in request.POST:
        search = request.POST.get('search_patientlog')
        current_page = 1
        page_size_prescription = 2  # Default to 2 if not specified
        offset = (current_page - 1) * page_size_prescription
        prescriptions = All_Prescription.objects.filter(Q(user_id__iexact = request.user.extrainfo.id) & Q( Q(user_id__icontains = search) | Q(details__icontains = search) | (Q(dependent_name__icontains = search)))).order_by('-date', '-id')[offset:offset + page_size_prescription]
            
        report = []
        for pre in prescriptions:
            doc = None
            if pre.doctor_id != None : doc=pre.doctor_id.doctor_name
            dic = {
                'id': pre.pk,
                'user_id': pre.user_id,
                'doctor_id': doc,
                'date': pre.date,
                'details': pre.details,
                'test': pre.test,
                'file_id': pre.file_id,
                'dependent_name':pre.dependent_name
                    # 'file': view_file(file_id=pre.file_id)['upload_file'] if pre.file_id else None
                }
            report.append(dic)
        print(report)
            # Handle total count for pagination context
        total_count = All_Prescription.objects.filter(Q(user_id__iexact = request.user.extrainfo.id) & Q( Q(user_id__icontains = search) | Q(details__icontains = search) | (Q(dependent_name__icontains = search)))).count()
        print(total_count)
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
        return JsonResponse({'status':1,"presc_context":prescContext})
    elif "get_annoucements" in request_body:
        announcements_data=Announcements.objects.all().order_by('-id').values()
        serializer = serializers.AnnouncementSerializer(announcements_data,many=True)
        return JsonResponse({'status':1, 'announcements' : serializer.data})
    elif "get_relief" in request_body:
        uploader_outbox=view_outbox(username=request.user.username,designation=request_body['selected_role'] ,src_module='health_center')
        medicalrelief=medical_relief.objects.all()
        uploader_inbox=view_inbox(username=request.user.username,designation=request_body['selected_role'],src_module='health_center')
        medicalRelief=[]
        for out in uploader_outbox:
                dic={}
            
                for mr in medicalrelief:
                    if mr.file_id==int(out['id']):   
                        dic['id']=out['id']                    
                        dic['upload_date']=datetime.fromisoformat(out['upload_date']).date()                   
                        dic['desc']=mr.description
                        # dic['file']=view_file(file_id=out['id'])['upload_file']       
                        dic['status']=mr.acc_admin_forward_flag
                        dic['approval_date']=''
            
                for inb in uploader_inbox:
                    if dic['id']==inb['id']:
                        dic['approval_date']=datetime.fromisoformat(inb['upload_date']).date()
                medicalRelief.append(dic)
            
        return JsonResponse({'status':1, 'relief': medicalRelief})
    elif 'get_doctors' in request_body :
        doctors = Doctor.objects.filter(active=True).order_by('id')
        serializer = serializers.DoctorSerializer(doctors,many=True)
        return JsonResponse({ 'status':1 , 'doctors':serializer.data })
    
    elif 'get_pathologists' in request_body :
        pathologists = Pathologist.objects.filter(active=True).order_by('id')
        serializer = serializers.PathologistSerializer(pathologists,many=True)
        return JsonResponse({'status':1,'pathologists':serializer.data})
    
    elif 'get_doctor_schedule' in request_body :
        # schedule=Doctors_Schedule.objects.select_related('doctor_id').all().order_by('day','doctor_id')
        doctors=Doctor.objects.filter(active=True).order_by('id')
        schedules = []
        for doctor in doctors :
            obj1 = {}
            schedule = Doctors_Schedule.objects.filter(doctor_id = doctor.id)
            availability = []
            for sch in schedule : 
                obj = {}
                obj['day'] = sch.day
                obj['time'] = str(convert_to_am_pm(str(sch.from_time))) + "-" +str(convert_to_am_pm(str(sch.to_time)))
                availability.append(obj)
            obj1['name'] = doctor.doctor_name
            obj1['specialization'] = doctor.specialization
            obj1['availability'] = availability
            schedules.append(obj1)
                        
        return JsonResponse({ 'status':1, 'schedule':schedules })
    
    elif 'get_pathologist_schedule' in request_body :
        # schedule=Doctors_Schedule.objects.select_related('doctor_id').all().order_by('day','doctor_id')
        pathologists=Pathologist.objects.filter(active=True).order_by('id')
        schedules = []
        for pathologist in pathologists :
            obj1 = {}
            schedule = Pathologist_Schedule.objects.filter(pathologist_id = pathologist.id)
            availability = []
            for sch in schedule : 
                obj = {}
                obj['day'] = sch.day
                obj['time'] = str(convert_to_am_pm(str(sch.from_time))) + "-" +str(convert_to_am_pm(str(sch.to_time)))
                availability.append(obj)
            obj1['name'] = pathologist.pathologist_name
            obj1['specialization'] = pathologist.specialization
            obj1['availability'] = availability
            schedules.append(obj1)
                        
        return JsonResponse({ 'status':1, 'schedule':schedules })

# def getDesignation(request):
#     user = request.user
#     design = HoldsDesignation.objects.select_related('user','designation').filter(working=user)

#     designation=[]

#     if str(user.extrainfo.user_type) == "student":
#         designation.append(str(user.extrainfo.user_type))
        
#     for i in design:
#         if str(i.designation) != str(user.extrainfo.user_type):
#             # print('-------')
#             # print(i.designation)
#             # print(user.extrainfo.user_type)
#             # print('')
#             designation.append(str(i.designation))
#     # for i in designation:
#     #     print(i)
#     return designation

# @api_view(['POST','DELETE'])
# def student_request_api(request):
#     # design=request.session['currentDesignationSelected']
#     usertype = ExtraInfo.objects.get(user=request.user).user_type
#     design = getDesignation(request)
#     if 'student' in design or 'Compounder' not in design:
#     # if design == 'student' or usertype == 'faculty' or usertype == 'staff':
#         # if 'ambulancerequest' in request.data and request.method=='POST':
#         #     comp_id = ExtraInfo.objects.filter(user_type='compounder')
#         #     request.data['user_id'] = get_object_or_404(User,username=request.user.username)
#         #     request.data['date_request']=datetime.now()
#         #     serializer = serializers.AmbulanceRequestSerializer(data=request.data)
#         #     if serializer.is_valid():
#         #         serializer.save()
#         #         healthcare_center_notif(request.user, request.user, 'amb_request')
#         #         for cmp in comp_id:
#         #             healthcare_center_notif(request.user, cmp.user, 'amb_req')
#         #         return Response(serializer.data, status=status.HTTP_201_CREATED)
#         #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
#         # elif 'ambulancecancel' in request.data and request.method == 'DELETE':
#         #     try:
#         #         amb_id=int(request.data['amb_id'])
#         #     except:
#         #         return Response({'message': 'Please enter ambulance id'}, status=status.HTTP_404_NOT_FOUND)
#         #     ambulance = get_object_or_404(Ambulance_request,pk=amb_id)
#         #     ambulance.delete()
#         #     resp = {'message': 'ambulance request is cancelled'}
#         #     return Response(data=resp,status=status.HTTP_200_OK)
        
#         # elif 'appointmentadd' in request.data and request.method == 'POST':
#         #     request.data['user_id'] = get_object_or_404(User,username=request.user.username)
#         #     try:
#         #         day = datetime.strptime(request.data['date'], "%Y-%m-%d").weekday()
#         #     except:
#         #         return Response({'message': 'Please enter valid date'}, status=status.HTTP_404_NOT_FOUND)
#         #     try:
#         #         doctor_id = request.data['doctor_id']
#         #     except:
#         #         return Response({'message': 'Please enter doctor id'}, status=status.HTTP_404_NOT_FOUND)
#         #     request.data['schedule'] =get_object_or_404(Doctors_Schedule,doctor_id=request.data['doctor_id'],day=day).id
#         #     comp_id = ExtraInfo.objects.filter(user_type='compounder')
#         #     serializer = serializers.AppointmentSerializer(data=request.data)
#         #     if serializer.is_valid():
#         #         serializer.save()
#         #         healthcare_center_notif(request.user, request.user, 'appoint')
#         #         for cmp in comp_id:
#         #              healthcare_center_notif(request.user, cmp.user, 'appoint_req')
#         #         return Response(serializer.data, status=status.HTTP_201_CREATED)
#         #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         # elif 'appointmentdelete' in request.data and request.method == 'DELETE':
#         #     try:
#         #         app_id = request.data['app_id']
#         #     except:
#         #         return Response({'message': 'Please enter valid appointment id'}, status=status.HTTP_404_NOT_FOUND)
#         #     appointment=get_object_or_404(Appointment,pk=app_id)
#         #     appointment.delete()
#         #     resp = {'message': 'Your appointment is cancelled'}
#         #     return Response(data=resp,status=status.HTTP_200_OK)
        

#         if 'complaintadd' in request.data and request.method == 'POST':
#             request.data['user_id'] = get_object_or_404(User,username=request.user.username)
#             serializer = serializers.ComplaintSerializer(data=request.data)
#             if serializer.is_valid():
#                 serializer.save()
#                 return Response(serializer.data, status=status.HTTP_201_CREATED)
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#         else: 
#             resp = {'message': 'invalid request'}
#             return Response(data=resp,status=status.HTTP_404_NOT_FOUND)

#     elif 'Compounder' in design:
#         return redirect('/healthcenter/api/compounder/request/')
#     else:
#         resp = {'message': 'invalid request'}
#         return Response(data=resp,status=status.HTTP_404_NOT_FOUND)


# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# @authentication_classes([TokenAuthentication])
# def student_view_api(request):
#     # student view starts here
#     # design=request.session['currentDesignationSelected']
#     # usertype = ExtraInfo.objects.get(user=request.user).user_type
#     design = getDesignation(request)
#     if 'student' in design or 'Compounder' not in design:
#         # users = ExtraInfo.objects.all()
#         user_id = ExtraInfo.objects.get(user=request.user)
#         # hospitals = serializers.HospitalAdmitSerializer(Hospital_admit.objects.filter(user_id=user_id).order_by('-admission_date'),many=True).data
#         # appointments = serializers.AppointmentSerializer(Appointment.objects.filter(user_id=user_id).order_by('-date'),many=True).data
#         # ambulances = serializers.AmbulanceRequestSerializer(Ambulance_request.objects.filter(user_id=user_id).order_by('-date_request'),many=True).data
#         prescription = serializers.PrescriptionSerializer(Prescription.objects.filter(user_id=user_id).order_by('-date'),many=True).data
#         medicines_presc = serializers.PrescribedMedicineSerializer(Prescribed_medicine.objects.all(),many=True).data
#         complaints = serializers.ComplaintSerializer(Complaint.objects.filter(user_id=user_id).order_by('-date'),many=True).data
#         days = Constants.DAYS_OF_WEEK
#         # schedule=serializers.ScheduleSerializer(Doctors_Schedule.objects.all().order_by('doctor_id'),many=True).data
#         doctor_schedule=serializers.DoctorsScheduleSerializer(Doctors_Schedule.objects.all().order_by('doctor_id'),many=True).data
#         pathologist_schedule=serializers.PathologistScheduleSerializer(Pathologist_Schedule.objects.all().order_by('pathologist_id'), many=True).data
#         doctors=serializers.DoctorSerializer(Doctor.objects.filter(active=True),many=True).data
#         pathologists=serializers.PathologistSerializer(Pathologist.objects.filter(active=True),many=True).data
#         count=Counter.objects.all()
#         if count:
#             Counter.objects.all().delete()
#         Counter.objects.create(count=0,fine=0)
#         count= serializers.CounterSerializer(Counter.objects.get()).data
#         resp={
#             'complaints': complaints, 
#             'medicines_presc': medicines_presc,
#             # 'ambulances': ambulances, 
#             'doctors': doctors, 
#             'pathologists': pathologists,
#             'days': days,
#             'count':count,
#             # 'hospitals': hospitals, 
#             # 'appointments': appointments,
#             'prescription': prescription, 
#             # 'schedule': schedule
#             'doctor_schedule': doctor_schedule,
#             'pathologist_schedule': pathologist_schedule,
#         }
#         return Response(data=resp,status=status.HTTP_200_OK)
#     elif 'Compounder' in design:
#         return redirect('/healthcenter/api/compounder/') 
#     else:
#         resp = {'message': 'invalid request'}
#         return Response(data=resp,status=status.HTTP_404_NOT_FOUND)

# @api_view(['POST','PATCH','DELETE'])
# @permission_classes([IsAuthenticated])
# @authentication_classes([TokenAuthentication]) 
# def compounder_request_api(request):
#     design = getDesignation(request)
#     if 'Compounder' in design:
#         if 'doctoradd' in request.data and request.method == 'POST':
#             request.data['active']=True
#             serializer = serializers.DoctorSerializer(data=request.data)
#             if serializer.is_valid():
#                 serializer.save()
#                 return Response(serializer.data, status=status.HTTP_201_CREATED)
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         elif 'doctorremove' in request.data and request.method == 'PATCH':
#             try:
#                 doctor=request.data['id']
#             except:
#                 return Response({'message': 'Please enter valid doctor id'}, status=status.HTTP_404_NOT_FOUND)
#             request.data['active']=False
#             doctor= get_object_or_404(Doctor,id=doctor)
#             serializer = serializers.DoctorSerializer(doctor,data=request.data,partial=True)
#             if serializer.is_valid():
#                 serializer.save()
#                 return Response(serializer.data, status=status.HTTP_201_CREATED)
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         elif 'doctorscheduleadd' in request.data and request.method == 'POST':
#             try:
#                 doctor_id = int(request.data['doctor_id'])
#             except:
#                 return Response({'message': 'Please enter valid doctor id'}, status=status.HTTP_404_NOT_FOUND)
#             try:
#                 day = request.data['day']
#             except:
#                 return Response({'message': 'Please enter valid day'}, status=status.HTTP_404_NOT_FOUND)
#             sc =  Doctor.objects.filter(doctor_id=doctor_id, day=day)
#             if sc.count() == 0:
#                 serializer = serializers.DoctorsScheduleSerializer(data=request.data)
#             else:
#                 sc = get_object_or_404(Doctors_Schedule,doctor_id=doctor_id,day=day)
#                 serializer = serializers.DoctorsScheduleSerializer(sc,data=request.data,partial=True)
#             if serializer.is_valid():
#                 serializer.save()
#                 return Response(serializer.data, status=status.HTTP_201_CREATED)
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         elif 'doctorscheduleremove' in request.data and request.method == 'DELETE':
#             try:
#                 doctor_id = request.data['doctor_id']
#             except:
#                 return Response({'message': 'Please enter valid doctor id'}, status=status.HTTP_404_NOT_FOUND)
#             try:
#                 day = request.data['day']
#             except:
#                 return Response({'message': 'Please enter valid day'}, status=status.HTTP_404_NOT_FOUND)
#             sc = get_object_or_404(Doctors_Schedule,doctor_id=doctor_id,day=day)
#             sc.delete()
#             resp={'message':'Schedule Deleted successfully'}
#             return Response(data=resp,status=status.HTTP_200_OK)

#         # elif 'hospitaladmit' in request.data and request.method == 'POST':
#         #     serializer = serializers.HospitalAdmitSerializer(data=request.data)
#         #     if serializer.is_valid():
#         #         serializer.save()
#         #         return Response(serializer.data, status=status.HTTP_201_CREATED)
#         #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 

#         # elif 'hospitaldischarge' in request.data and request.method == 'PATCH':
#         #     try:
#         #         pk = request.data['id']
#         #     except:
#         #         return Response({'message': 'Please enter valid id'}, status=status.HTTP_404_NOT_FOUND)
#         #     request.data['discharge_date']=date.today()
#         #     Ha = get_object_or_404(Hospital_admit,id=pk)
#         #     serializer = serializers.HospitalAdmitSerializer(Ha,data=request.data,partial=True)
#         #     if serializer.is_valid():
#         #         serializer.save()
#         #         return Response(serializer.data, status=status.HTTP_201_CREATED)
#         #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
#         elif 'medicineadd' in request.data and request.method =='POST':
#             stock = serializers.StockSerializer(data=request.data)
#             if stock.is_valid():
#                 stock.save()
#             else:
#                 return Response(stock.errors,status=status.HTTP_400_BAD_REQUEST)
#             request.data['medicine_id'] = (Stock.objects.get(medicine_name=request.data['medicine_name'])).id
#             expiry = serializers.ExpirySerializer(data=request.data)
#             if expiry.is_valid():
#                 expiry.save()
#             else:
#                 return Response(expiry.errors,status=status.HTTP_400_BAD_REQUEST)
#             return Response(stock.data,status=status.HTTP_201_CREATED)

#         elif 'stockadd' in request.data and request.method == 'POST':
#             serializer = serializers.ExpirySerializer(data=request.data)
#             if serializer.is_valid():
#                 serializer.save()
#             else:
#                 return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#             quantity = (Stock.objects.get(id=request.data['medicine_id'])).quantity
#             quantity = quantity + int(request.data['quantity'])
#             stock = get_object_or_404(Stock,id=request.data['medicine_id'])
#             serializer = serializers.StockSerializer(stock,data={'quantity': quantity,'threshold':request.data['threshold']},partial=True)
#             if serializer.is_valid():
#                 serializer.save()
#             else:
#                 return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#             resp = {'message': 'stock added successfully'}
#             return Response(data=resp,status=status.HTTP_200_OK)

#         elif 'prescriptionsubmit' in request.data and request.method == 'POST':
#             serializer = serializers.PrescriptionSerializer(data=request.data)
#             user = ExtraInfo.objects.get(id=request.data['user_id'])
#             if serializer.is_valid():
#                 serializer.save()
#                 healthcare_center_notif(request.user, user.user, 'Presc')
#                 return Response(serializer.data, status=status.HTTP_201_CREATED)
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         elif 'prescripmedicineadd' in request.data and request.method == 'POST':
#             with transaction.atomic():
#                 medicine_id=request.data['medicine_id']
#                 quantity = int(request.data['quantity'])
#                 expiry=Expiry.objects.filter(medicine_id=medicine_id,quantity__gt=0,returned=False,expiry_date__gte=date.today()).order_by('expiry_date')
#                 stock=(Stock.objects.get(id=medicine_id)).quantity
#                 if stock>quantity:
#                     for e in expiry:
#                         q=e.quantity
#                         em=e.id
#                         if q>quantity:
#                             q=q-quantity
#                             Expiry.objects.filter(id=em).update(quantity=q)
#                             qty = Stock.objects.get(id=medicine_id).quantity
#                             qty = qty-quantity
#                             Stock.objects.filter(id=medicine_id).update(quantity=qty)
#                             break
#                         else:
#                             quan=Expiry.objects.get(id=em).quantity
#                             Expiry.objects.filter(id=em).update(quantity=0)
#                             qty = Stock.objects.get(id=medicine_id).quantity
#                             qty = qty-quan
#                             Stock.objects.filter(id=medicine_id).update(quantity=qty)
#                             quantity=quantity-quan
#                     serializer = serializers.PrescribedMedicineSerializer(data=request.data)
#                     if serializer.is_valid():
#                         serializer.save()
#                         return Response(serializer.data,status=status.HTTP_200_OK)
#                     else:
#                         transaction.set_rollback(True)
#                         return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
#                 else:
#                     resp= {'message': 'Required Medicines is not available'}
#                     return Response(data=resp,status=status.HTTP_400_BAD_REQUEST)

#         elif 'complaintresponse' in request.data and request.method == 'PATCH':
#             try:
#                 pk = request.data['complaint_id']
#             except:
#                 return Response({'message': 'Please enter valid complaint id'}, status=status.HTTP_404_NOT_FOUND)
#             try: 
#                 complain = Complaint.objects.get(id = pk) 
#             except Complaint.DoesNotExist: 
#                 return Response({'message': 'Complaint does not exist'}, status=status.HTTP_404_NOT_FOUND)
#             serializer = serializers.ComplaintSerializer(complain,data=request.data,partial=True)
#             if serializer.is_valid():
#                 serializer.save()
#                 return Response(serializer.data, status=status.HTTP_201_CREATED)
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#         else:
#             resp = {'message': 'invalid request'}
#             return Response(data=resp,status=status.HTTP_404_NOT_FOUND)

#     else:
#         resp = {'message': 'invalid request'}
#         return Response(data=resp,status=status.HTTP_404_NOT_FOUND)

# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# @authentication_classes([TokenAuthentication])                                  
# def compounder_view_api(request):                                                              # compounder view starts here
#     # usertype = ExtraInfo.objects.get(user=request.user).user_type
#     design = getDesignation(request)
#     if 'Compounder' in design:  
#         all_complaints = serializers.ComplaintSerializer(Complaint.objects.all(),many=True).data
#         # all_hospitals = serializers.HospitalAdmitSerializer(Hospital_admit.objects.all().order_by('-admission_date'),many=True).data
#         # hospitals_list = serializers.HospitalSerializer(Hospital.objects.all().order_by('hospital_name'),many=True).data
#         # all_ambulances = serializers.AmbulanceRequestSerializer(Ambulance_request.objects.all().order_by('-date_request'),many=True).data
#         # appointments_today = serializers.AppointmentSerializer(Appointment.objects.filter(date=datetime.now()).order_by('date'),many=True).data
#         # appointments_future= serializers.AppointmentSerializer(Appointment.objects.filter(date__gt=datetime.now()).order_by('date'),many=True).data
#         stocks = serializers.StockSerializer(Stock.objects.all(),many=True).data
#         days = Constants.DAYS_OF_WEEK
#         # schedule= serializers.ScheduleSerializer(Doctors_Schedule.objects.all().order_by('doctor_id'),many=True).data
#         expired= serializers.ExpirySerializer(Expiry.objects.filter(expiry_date__lt=datetime.now(),returned=False).order_by('expiry_date'),many=True).data
#         live_meds= serializers.ExpirySerializer(Expiry.objects.filter(returned=False).order_by('quantity'),many=True).data
#         count= Counter.objects.all()
#         presc_hist= serializers.PrescriptionSerializer(Prescription.objects.all().order_by('-date'),many=True).data
#         medicines_presc= serializers.PrescribedMedicineSerializer(Prescribed_medicine.objects.all(),many=True).data

#         if count:
#             Counter.objects.all().delete()
#         Counter.objects.create(count=0,fine=0)
#         count= serializers.CounterSerializer(Counter.objects.get()).data
#         # hospitals=serializers.HospitalSerializer(Hospital.objects.all(),many=True).data
#         doctor_schedule=serializers.DoctorsScheduleSerializer(Doctors_Schedule.objects.all().order_by('doctor_id'),many=True).data
#         pathologist_schedule=serializers.PathologistScheduleSerializer(Pathologist_Schedule.objects.all().order_by('pathologist_id'), many=True).data
#         doctors=serializers.DoctorSerializer(Doctor.objects.filter(active=True),many=True).data
#         pathologists=serializers.PathologistSerializer(Pathologist.objects.filter(active=True),many=True).data

#         resp= {
#                 'days': days, 
#                 'count': count,
#                 'expired':expired,
#                 'stocks': stocks, 
#                 'all_complaints': all_complaints,
#                 # 'all_hospitals': all_hospitals, 
#                 # 'hospitals':hospitals, 
#                 # 'all_ambulances': all_ambulances,
#                 # 'appointments_today': appointments_today, 
#                 'doctors': doctors,
#                 # 'appointments_future': appointments_future, 
#                 # 'schedule': schedule, 
#                 'doctor_schedule': doctor_schedule,
#                 'pathologist_schedule': pathologist_schedule,
#                 'pathologists': pathologists,
#                 'live_meds': live_meds, 
#                 'presc_hist': presc_hist, 
#                 'medicines_presc': medicines_presc, 
#                 # 'hospitals_list': hospitals_list
#             }
#         return Response(data=resp,status=status.HTTP_200_OK) 

#     else:
#         resp = {'message': 'invalid request'}
#         return Response(data=resp,status=status.HTTP_404_NOT_FOUND)                                   # compounder view ends