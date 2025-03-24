import json
import os
import pandas as pd
from django.db import transaction
from datetime import datetime, timedelta,date
from applications.globals.models import ExtraInfo
from django.core import serializers
from applications.filetracking.models import File
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation, DepartmentInfo
from django.http import HttpResponse, JsonResponse
from notification.views import  healthcare_center_notif
from .models import ( Doctor, Stock_entry,Present_Stock,All_Medicine, 
                     Doctors_Schedule,Pathologist_Schedule,
                    Pathologist, medical_relief, MedicalProfile,All_Prescription,All_Prescribed_medicine,
                    Prescription_followup,files,Required_medicine,Announcements,Complaint)
from applications.filetracking.sdk.methods import *
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from django.db.models import Q
from applications.globals.models import ExtraInfo
from applications.hr2.models import EmpDependents

def datetime_handler(date):
    '''
        Checks datetime format
    '''
    if hasattr(date, 'isoformat'):
        return date.isoformat()
    else:
        raise TypeError

def compounder_view_handler(request):
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
    elif 'add_doctor' in request.POST:                                         
        doctor=request.POST.get('new_doctor')
        specialization=request.POST.get('specialization')
        phone=request.POST.get('phone')
        Doctor.objects.create(
        doctor_name=doctor,
        doctor_phone=phone,
        specialization=specialization,
        active=True
        )
        data={'status':1, 'doctor':doctor, 'specialization':specialization, 'phone':phone}
        return JsonResponse(data)
    
    # updating new pathologist info in db    
    elif 'add_pathologist' in request.POST:                                         
        doctor=request.POST.get('new_pathologist')
        specialization=request.POST.get('specialization')
        phone=request.POST.get('phone')
        Pathologist.objects.create(
        pathologist_name=doctor,
        pathologist_phone=phone,
        specialization=specialization,
        active=True
        )
        data={'status':1, 'pathologist_name':doctor, 'specialization':specialization, 'pathologist_phone':phone}
        return JsonResponse(data)
    
    

    # remove doctor by changing active status
    elif 'remove_doctor' in request.POST:                              
        doctor=request.POST.get('doctor_active')
        Doctor.objects.filter(id=doctor).update(active=False)
        doc=Doctor.objects.get(id=doctor).doctor_name
        data={'status':1, 'id':doctor, 'doc':doc}
        return JsonResponse(data)
    
    # remove pathologist by changing active status
    elif 'remove_pathologist' in request.POST:                              
        doctor=request.POST.get('pathologist_active')
        Pathologist.objects.filter(id=doctor).update(active=False)
        doc=Pathologist.objects.get(id=doctor).pathologist_name
        data={'status':1, 'id':doctor, 'doc':doc}
        return JsonResponse(data)
    
    elif 'add_stock' in request.POST:
        try:
            medicine = request.POST.get('medicine_id')
            # threshold_a = request.POST.get('threshold_a')
            med_brand_name = medicine.split(',')[0]
            id = medicine.split(',')[1]
            medicine_id = All_Medicine.objects.get(id = id)
            qty = int(request.POST.get('quantity'))
            supplier=request.POST.get('supplier')
            expiry=request.POST.get('expiry_date')
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
    elif 'edit_threshold' in request.POST:
        try:
            medicine_with_id = request.POST.get('medicine_id')
            medicine = medicine_with_id.split(',')[0]
            new_threshold = int(request.POST.get('threshold'))
            threshold_med=All_Medicine.objects.get(brand_name = medicine)
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
    elif 'edit_1' in request.POST:                                             
        doctor = request.POST.get('doctor')
        day = request.POST.get('day')
        time_in = request.POST.get('time_in')
        time_out = request.POST.get('time_out')
        room = request.POST.get('room')
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
    elif 'rmv' in request.POST:  
        doctor = request.POST.get('doctor')
        
        day = request.POST.get('day')
        Doctors_Schedule.objects.select_related('doctor_id').filter(doctor_id=doctor, day=day).delete()
        data = {'status': 1}
        return JsonResponse(data)
    
    
     # edit schedule for pathologists
    elif 'edit12' in request.POST:                                             
        doctor = request.POST.get('pathologist')
        day = request.POST.get('day')
        time_in = request.POST.get('time_in')
        time_out = request.POST.get('time_out')
        room = request.POST.get('room')
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
    elif 'rmv1' in request.POST:  
        doctor = request.POST.get('pathologist')
        
        day = request.POST.get('day')
        Pathologist_Schedule.objects.select_related('pathologist_id').filter(pathologist_id=doctor, day=day).delete()
        data = {'status': 1}
        return JsonResponse(data)
    

    elif 'add_medicine' in request.POST:
        medicine = request.POST.get('new_medicine')
        threshold = request.POST.get('threshold')
        brand_name = request.POST.get('brand_name')
        constituents = request.POST.get('constituents')
        manufacture_name = request.POST.get('manufacture_name')
        packsize = request.POST.get('packsize')
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
        data = {'medicine':  medicine, 'threshold': threshold,}
        return JsonResponse(data)

    elif 'get_stock' in request.POST:
        try:
            medicine_name_and_id = request.POST.get('medicine_name_for_stock')
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
    
    elif 'user_for_dependents' in request.POST:
        user = request.POST.get('user_for_dependents')
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
    elif 'prescribe_b' in request.POST:
        user_id = request.POST.get('user')
        doctor_id = request.POST.get('doctor')
        if not User.objects.filter(username__iexact = user_id).exists():
            return JsonResponse({"status":-1}) 
        if doctor_id == 'null' :
            doctor = None
        else:
            doctor = Doctor.objects.get(id=doctor_id)

        
        is_dependent=request.POST.get('is_dependent')
        fid=0
        uploaded_file = request.FILES.get('file')
        if uploaded_file != None :
            f=uploaded_file.read()
            new_file=files.objects.create(
                file_data=f
            )
            fid=new_file.id  
        if is_dependent == "self":
            pres=All_Prescription.objects.create(
                user_id = user_id,
                doctor_id=doctor,
                details = request.POST.get('details'), 
                date=date.today(),
                test=request.POST.get('tests'),
                file_id=fid
            )
        else :
            pres=All_Prescription.objects.create(
                user_id = user_id,
                doctor_id=doctor,
                details = request.POST.get('details'), 
                date=date.today(),
                test=request.POST.get('tests'),
                is_dependent = True,
                dependent_name = request.POST.get('dependent_name'),
                dependent_relation = request.POST.get('dependent_relation'),
                file_id=fid
            )

        pre_medicine = request.POST.get('pre_medicine')

        medicine=eval('('+pre_medicine+')')

        for med in medicine:
            med_name = med["brand_name"]
            id=med_name.split(",")[1]
            quant = int(med['quantity'])
            days = med['Days'] 
            times = med['Times']
            stock = med['stock']
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
                p_stock = Present_Stock.objects.get(id=int(stk[2]))
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
                            quantity = qty,
                            threshold = med_id.threshold
                        )
        return JsonResponse({"status":1})
    
    elif 'presc_followup' in request.POST:
        pre_id=request.POST.get("pre_id")
        presc = All_Prescription.objects.get(id=int(pre_id))

        doctor_id = request.POST.get('doctor')
        if doctor_id == "null":
            doctor = None
        else:
            doctor = Doctor.objects.get(id=doctor_id)
        
        fid=0
        uploaded_file = request.FILES.get('file')
        if uploaded_file != None :
            f=uploaded_file.read()
            new_file=files.objects.create(
                file_data=f
            )
            fid=new_file.id

        followup = Prescription_followup.objects.create(
            prescription_id=presc,
            Doctor_id=doctor,
            details = request.POST.get('details'),
            test = request.POST.get('tests'),
            date = date.today(),
            file_id = fid
        )

        pre_medicine = request.POST.get('pre_medicine')

        medicine=eval('('+pre_medicine+')')
        for med in medicine:
            med_name = med["med_name"]
            id = med_name.split(',')[1]
            quant = int(med['quantity'])
            days = med['Days'] 
            times = med['Times']
            stock = med['stock']
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
                p_stock = Present_Stock.objects.get(id=int(stk[2]))
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
                            quantiy = qty,
                            threshold = med_id.threshold
                        )
        revoked = request.POST.get('revoked')
        r_medicine = eval('(' + revoked+')')
        for med in r_medicine:
            med_id=med["med_id"]
            checked = med['checked']
            if checked == 'true' :
                presc_med_id = All_Prescribed_medicine.objects.get(id=med_id)
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
    elif 'compounder_forward' in request.POST:
        acc_admin_des_id = Designation.objects.get(name="Accounts Admin")        
        user_ids = HoldsDesignation.objects.filter(designation_id=acc_admin_des_id.id).values_list('user_id', flat=True)    
        acc_admins = ExtraInfo.objects.get(user_id=user_ids[0])
        user=ExtraInfo.objects.get(pk=acc_admins.id)
        forwarded_file_id=forward_file(
            file_id=request.POST['file_id'],
            receiver=acc_admins.id, 
            receiver_designation="Accounts Admin",
            file_extra_JSON= {"value": 2},            
            remarks="Forwarded File with id: "+ str(request.POST['file_id'])+"to Accounts Admin "+str(acc_admins.id), 
            file_attachment=None,
        )
       
        medical_relief_instance = medical_relief.objects.get(file_id=request.POST['file_id'])        
        medical_relief_instance.compounder_forward_flag = True
        medical_relief_instance.save()        
        healthcare_center_notif(request.user,user.user,'rel_approve','')      
        data = {'status': 1}
        return JsonResponse(data)
    elif 'compounder_reject' in request.POST:
        file_id = request.POST.get('file_id')
        relief = medical_relief.objects.get(file_id=file_id)
        relief.compounder_reject_flag = True
        relief.save()
        rejected_user = request.POST.get('rejected_user')
        user=User.objects.get(username__iexact = rejected_user)
        rejected_user_info = ExtraInfo.objects.get(user_id = user)
        healthcare_center_notif(request.user,rejected_user_info.user,'reject_relief','')
        data = {'status': 1}
        return JsonResponse(data)
    elif 'comp_announce' in request.POST:
        usrnm = get_object_or_404(User, username=request.user.username)
        user_info = ExtraInfo.objects.all().select_related('user','department').filter(user=usrnm).first()
        num = 1
        ann_anno_id = user_info.id        
        formObject = Announcements()       
        user_info = ExtraInfo.objects.all().select_related('user','department').get(id=ann_anno_id)
        getstudents = ExtraInfo.objects.select_related('user')
        recipients = User.objects.filter(extrainfo__in=getstudents)       
        formObject.anno_id=user_info     
        formObject.message = request.POST['announcement']
        formObject. upload_announcement = request.FILES.get('upload_announcement')       
        formObject.ann_date = date.today()     
        formObject.save()
        print("before")
        healthcare_center_notif(usrnm, recipients , 'new_announce',formObject.message )
        print("after")
        data = {'status': 1}
        return JsonResponse(data)
    elif 'datatype' in request.POST and request.POST['datatype'] == 'patientlog':
                 search = request.POST.get('search_patientlog')
                 page_size = 2
                 new_current_page = int(request.POST.get('page'))
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
    elif 'datatype' in request.POST and request.POST['datatype'] == 'manage_stock_view':
                search = request.POST.get('search_view_stock')
                page_size_stock = 2
                new_current_page_stock = int(request.POST.get('page_stock_view'))
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
    elif 'datatype' in request.POST and request.POST['datatype'] == 'manage_stock_expired':
                search = request.POST.get('search_view_expired')
                new_page_size_stock_expired = 2
                new_current_page_stock_expired = int(request.POST.get('page_stock_expired'))
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
    elif 'datatype' in request.POST and request.POST['datatype'] == 'manage_stock_required':
                search = request.POST.get('search_view_required')
                new_page_size_stock_required = 2
                new_current_page_stock_required = int(request.POST.get('page_stock_required'))
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

def student_view_handler(request):
    
    
    if 'feed_submit' in request.POST:
        user_id = ExtraInfo.objects.select_related('user','department').get(user=request.user)
        feedback = request.POST.get('feedback')
        Complaint.objects.create(
            user_id=user_id,
            complaint=feedback,
            date=datetime.now()
        )
        data = {'status': 1}
        healthcare_center_notif(request.user, request.user,'feedback_submitted','')
        
        return JsonResponse(data)

    elif 'medical_relief_submit' in request.POST:
        designation = request.POST.get('designation')
        # print("# #")
        # print(designation)
        user=ExtraInfo.objects.get(pk=designation)
        description = request.POST.get('description')
         
        # Retrieve the uploaded file from request.FILES
        uploaded_file = request.FILES.get('file')

        # Create an instance of the medical_relief model
        form_object = medical_relief(
            description=description,
            file=uploaded_file
        )

        # Save the form object
        form_object.save()
        
        # Retrieve the form object you just saved
        request_object = medical_relief.objects.get(pk=form_object.pk)
        
        # Retrieve HoldsDesignation instances
        d = HoldsDesignation.objects.get(user__username=designation)
        d1 = HoldsDesignation.objects.get(user__username=request.user)
        print(request.session['currentDesignationSelected'])

        # Create a file entry using the create_file utility function
        send_file_id = create_file(
            uploader=request.user.username,
            uploader_designation=request.session['currentDesignationSelected'],
            receiver=designation,
            receiver_designation=d.designation,
            src_module="health_center",
            src_object_id=str(request_object.id),
            file_extra_JSON={"value": 2},
            attached_file=uploaded_file  
        )  
        healthcare_center_notif(request.user,user.user,'rel_forward','')
        request_object.file_id = send_file_id
        request_object.save()
        
        # file_details_dict = view_file(file_id=send_file_id)    
        # print(file_details_dict)   
        return JsonResponse({'status': 1})
    
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
    elif 'datatype' in request.POST and request.POST['datatype'] == 'patientlog':
                 search = request.POST.get('search_patientlog')
                 print("patient")
                 page_size = 2
                 new_current_page = int(request.POST.get('page'))
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
            # Handle total count for pagination context
        total_count = All_Prescription.objects.filter(Q(user_id__iexact = request.user.extrainfo.id) & Q( Q(user_id__icontains = search) | Q(details__icontains = search) | (Q(dependent_name__icontains = search)))).count()
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