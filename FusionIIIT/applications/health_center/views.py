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
#from notification_channels.models import Notification

from .models import (Ambulance_request, Appointment, Complaint, Constants,
                     Counter, Doctor, Expiry, Hospital, Hospital_admit,
                     Medicine, Prescribed_medicine, Prescription, Schedule,
                     Stock)


def datetime_handler(x):
    if hasattr(x, 'isoformat'):
        return x.isoformat()
    else:
        raise TypeError

@login_required
def healthcenter(request):
    usertype = ExtraInfo.objects.select_related('user','department').get(user=request.user).user_type

    if usertype == 'student' or usertype=='faculty' or usertype=='staff':
        return HttpResponseRedirect("/healthcenter/student")
    elif usertype == 'compounder':
        return HttpResponseRedirect("/healthcenter/compounder")


@login_required
def compounder_view(request):                                                              # compounder view starts here
    usertype = ExtraInfo.objects.select_related('user','department').get(user=request.user).user_type
    if usertype == 'compounder':
        if request.method == 'POST':

            if 'feed_com' in request.POST:                                    # compounder response to patients feedback
                pk = request.POST.get('com_id')
                feedback = request.POST.get('feed')
                Complaint.objects.select_related('user_id','user_id__user','user_id__department').filter(id=pk).update(feedback=feedback)
                data = {'feedback': feedback}
                return JsonResponse(data)
            elif 'end' in request.POST:
                pk = request.POST.get('id')
                Ambulance_request.objects.select_related('user_id','user_id__user','user_id__department').filter(id=pk).update(end_date=datetime.now())
                amb=Ambulance_request.objects.select_related('user_id','user_id__user','user_id__department').filter(id=pk)
                for f in amb:
                    dateo=f.end_date
                data={'datenow':dateo}
                return JsonResponse(data)
            elif 'returned' in request.POST:                                     # return expired medicine and update db
                pk = request.POST.get('id')
                Expiry.objects.select_related('medicine_id').filter(id=pk).update(returned=True,return_date=datetime.now())
                qty=Expiry.objects.select_related('medicine_id').get(id=pk).quantity
                med=Expiry.objects.select_related('medicine_id').get(id=pk).medicine_id.id
                quantity=Stock.objects.get(id=med).quantity
                quantity=quantity-qty
                Stock.objects.filter(id=med).update(quantity=quantity)
                data={'status':1}
                return JsonResponse(data)
            elif 'add_doctor' in request.POST:                                         # updating new doctor info in db
                doctor=request.POST.get('new_doctor')
                specialization=request.POST.get('specialization')
                phone=request.POST.get('phone')
                Doctor.objects.create(
                doctor_name=doctor,
                doctor_phone=phone,
                specialization=specialization,
                active=True
                )
                a=User.objects.all()
#                for user in a:
#                    Notification.objects.create(notif_type='healthcenter',recipient=user,action_verb='appoiinted',display_text='New Doctor has been appointed : Dr.'+doctor)
                data={'status':1, 'doctor':doctor, 'specialization':specialization, 'phone':phone}
                return JsonResponse(data)
            elif 'remove_doctor' in request.POST:                              # remove doctor by changing active status
                doctor=request.POST.get('doctor_active')
                Doctor.objects.filter(id=doctor).update(active=False)
                doc=Doctor.objects.get(id=doctor).doctor_name
                a=User.objects.all()
#                for user in a:
#                    Notification.objects.create(notif_type='healthcenter',recipient=user,action_verb='removed',display_text='Dr.'+doc+'will not be available from now')
                data={'status':1, 'id':doctor, 'doc':doc}
                return JsonResponse(data)
            elif 'discharge' in request.POST:                                        #
                pk = request.POST.get('discharge')
                Hospital_admit.objects.select_related('user_id','user_id__user','user_id__department','doctor_id').filter(id=pk).update(discharge_date=datetime.now())
                hosp=Hospital_admit.objects.select_related('user_id','user_id__user','user_id__department','doctor_id').filter(id=pk)
                for f in hosp:
                    dateo=f.discharge_date
                data={'datenow':dateo, 'id':pk}
                return JsonResponse(data)
            elif 'add_stock' in request.POST:
                medicine = request.POST.get('medicine_id')
                threshold_a = request.POST.get('threshold_a')
                medicine_name = Stock.objects.get(id=medicine)
                qty = int(request.POST.get('quantity'))
                supplier=request.POST.get('supplier')
                expiry=request.POST.get('expiry_date')
                Expiry.objects.create(
                    medicine_id=medicine_name,
                    quantity=qty,
                    supplier=supplier,
                    expiry_date=expiry,
                    date=datetime.now(),
                )
                quantity = (Stock.objects.get(id=medicine)).quantity
                quantity = quantity + qty
                Stock.objects.filter(id=medicine).update(quantity=quantity)
                Stock.objects.filter(id=medicine).update(threshold=threshold_a)
                #data = {'medicine': medicine_name, 'quantity': qty, 'new_supplier': supplier, 'new_expiry_date': expiry}
                data = {'status': 1}
                return JsonResponse(data)
            elif 'edit' in request.POST:                                              # edit schedule for doctors
                doctor = request.POST.get('doctor')
                day = request.POST.get('day')
                time_in = request.POST.get('time_in')
                time_out = request.POST.get('time_out')
                room = request.POST.get('room')
                sc = Schedule.objects.select_related('doctor_id').filter(doctor_id=doctor, day=day)
                doctor_id = Doctor.objects.get(id=doctor)
                if sc.count() == 0:
                    Schedule.objects.create(doctor_id=doctor_id, day=day, room=room,
                                            from_time=time_in, to_time=time_out)
                else:
                    Schedule.objects.select_related('doctor_id').filter(doctor_id=doctor_id, day=day).update(room=room)
                    Schedule.objects.select_related('doctor_id').filter(doctor_id=doctor_id, day=day).update(from_time=time_in)
                    Schedule.objects.select_related('doctor_id').filter(doctor_id=doctor_id, day=day).update(to_time=time_out)
                a=User.objects.all()
#                for user in a:
#                    Notification.objects.create(notif_type='healthcenter',recipient=user,action_verb='changed',display_text='Doctor Schedule has been changed')
                data={'status':1}
                return JsonResponse(data)
            elif 'rmv' in request.POST:  # remove schedule for a doctor
                doctor = request.POST.get('doctor')
                day = request.POST.get('day')
                Schedule.objects.select_related('doctor_id').filter(doctor_id=doctor, day=day).delete()
                #doctor_id = Doctor.objects.get(id=doctor)

                a = User.objects.all()
                #                for user in a:
                #                    Notification.objects.create(notif_type='healthcenter',recipient=user,action_verb='changed',display_text='Doctor Schedule has been changed')
                data = {'status': 1}
                return JsonResponse(data)

            elif 'add_medicine' in request.POST:
                medicine = request.POST.get('new_medicine')
                quantity = request.POST.get('new_quantity')
                threshold = request.POST.get('threshold')
                new_supplier = request.POST.get('new_supplier')
                new_expiry_date = request.POST.get('new_expiry_date')
                Stock.objects.create(
                    medicine_name=medicine,
                    quantity=quantity,
                    threshold=threshold
                )
                medicine_id = Stock.objects.get(medicine_name=medicine)
                Expiry.objects.create(
                    medicine_id=medicine_id,
                    quantity=quantity,
                    supplier=new_supplier,
                    expiry_date=new_expiry_date,
                    returned=False,
                    return_date=None,
                    date=datetime.now()
                )
                data = {'medicine':  medicine, 'quantity': quantity, 'threshold': threshold,
                        'new_supplier': new_supplier, 'new_expiry_date': new_expiry_date  }
                # data={'status': 1}
                return JsonResponse(data)
            elif 'admission' in request.POST:
                user = request.POST.get('user_id')
                user_id = ExtraInfo.objects.select_related('user','department').get(id=user)
                doctor = request.POST.get('doctor_id')
                doctor_id = Doctor.objects.get(id=doctor)
                admission_date = request.POST.get('admission_date')
                reason = request.POST.get('description')
                hospital_doctor = request.POST.get('hospital_doctor')
                hospital_id = request.POST.get('hospital_name')
                hospital_name = Hospital.objects.get(id=hospital_id)
                Hospital_admit.objects.create(
                     user_id=user_id,
                     doctor_id=doctor_id,
                     hospital_name=hospital_name,
                     admission_date=admission_date,
                     hospital_doctor=hospital_doctor,
                     discharge_date=None,
                     reason=reason
                 )
                user=user_id.user
                hname=hospital_name.hospital_name
#                Notification.objects.create(notif_type='healthcenter',recipient=user,action_verb='admitted',display_text='You have been admitted in '+hname)
                data={'status':1}
                return JsonResponse(data)
            elif 'medicine_name' in request.POST:
                app = request.POST.get('user')
                user = Appointment.objects.select_related('user_id','user_id__user','user_id__department','doctor_id','schedule','schedule__doctor_id').get(id=app).user_id
                quantity = int(request.POST.get('quantity'))
                days = int(request.POST.get('days'))
                times = int(request.POST.get('times'))
                medicine_id = request.POST.get('medicine_name')
                medicine = Stock.objects.get(id=medicine_id)
                Medicine.objects.create(
                    patient=user,
                    medicine_id=medicine,
                    quantity=quantity,
                    days=days,
                    times=times
                )
                schs = Medicine.objects.filter(patient=user)
                list = []
                for s in schs:
                    list.append({'medicine': s.medicine_id.medicine_name, 'quantity': s.quantity,
                                 'days': s.days, 'times': s.times})
                sches = json.dumps(list, default=datetime_handler)
                return HttpResponse(sches, content_type='json')
            # elif 'day' in request.POST:
            #     day = request.POST.get('day')
            #     sche = Schedule.objects.filter(day=day)
            #     list = []
            #     for s in sche:
            #         list.append({'room': s.room, 'id': s.id, 'doctor': s.doctor_id.doctor_name,
            #                      'from_time': s.from_time, 'to_time': s.to_time})
            #
            #     sches = json.dumps(list, default=datetime_handler)
            #     return HttpResponse(sches, content_type='json')
            elif 'medicine_name_b' in request.POST:
                user_id = request.POST.get('user')
                user = ExtraInfo.objects.select_related('user','department').get(id=user_id)
                quantity = int(request.POST.get('quantity'))
                days = int(request.POST.get('days'))
                times = int(request.POST.get('times'))
                medicine_id = request.POST.get('medicine_name_b')
                medicine = Stock.objects.get(id=medicine_id)
                Medicine.objects.create(
                    patient=user,
                    medicine_id=medicine,
                    quantity=quantity,
                    days=days,
                    times=times
                )
                schs = Medicine.objects.filter(patient=user)
                list = []
                for s in schs:
                    list.append({'medicine': s.medicine_id.medicine_name, 'quantity': s.quantity,
                                 'days': s.days, 'times': s.times})
                sches = json.dumps(list, default=datetime_handler)
                return HttpResponse(sches, content_type='json')
            # elif 'day' in request.POST:
            #     day = request.POST.get('day')
            #     sche = Schedule.objects.filter(day=day)
            #     list = []
            #     for s in sche:
            #         list.append({'room': s.room, 'id': s.id, 'doctor': s.doctor_id.doctor_name,
            #                      'from_time': s.from_time, 'to_time': s.to_time})
            #
            #     sches = json.dumps(list, default=datetime_handler)
            #     return HttpResponse(sches, content_type='json')
            # elif 'main' in request.POST:
            #     data = {
            #             'status': 1
            #             }
            #     return JsonResponse(data)
            elif 'doct' in request.POST:
                doctor_id = request.POST.get('doct')
                schedule = Schedule.objects.select_related('doctor_id').filter(doctor_id=doctor_id)
                list = []
                for s in schedule:
                    list.append({'room': s.room, 'id': s.id, 'doctor': s.doctor_id.doctor_name,
                                 'day': s.get_day_display(), 'from_time': s.from_time,
                                 'to_time': s.to_time})

                sches = json.dumps(list, default=datetime_handler)
                return HttpResponse(sches, content_type='json')

            elif 'prescribe' in request.POST:
                app_id = request.POST.get('user')
                details = request.POST.get('details')
                tests = request.POST.get('tests')
                appointment = Appointment.objects.select_related('user_id','user_id__user','user_id__department','doctor_id','schedule','schedule__doctor_id').get(id=app_id)
                user=appointment.user_id
                doctor=appointment.doctor_id
                Prescription.objects.create(
                    user_id=user,
                    doctor_id=doctor,
                    details=details,
                    date=datetime.now(),
                    test=tests,
                    appointment=appointment
                )
                query = Medicine.objects.select_related('patient','patient__user','patient__department').objects.filter(patient=user)
                prescribe = Prescription.objects.select_related('user_id','user_id__user','user_id__department','doctor_id','appointment','appointment__user_id','appointment__user_id__user','appointment__user_id__department','appointment__doctor_id','appointment__schedule','appointment__schedule__doctor_id').objects.all().last()
                for medicine in query:
                    medicine_id = medicine.medicine_id
                    quantity = medicine.quantity
                    days = medicine.days
                    times = medicine.times
                    Prescribed_medicine.objects.create(
                        prescription_id=prescribe,
                        medicine_id=medicine_id,
                        quantity=quantity,
                        days=days,
                        times=times
                    )
                    today=datetime.now()
                    expiry=Expiry.objects.select_related('medicine_id').filter(medicine_id=medicine_id,quantity__gt=0,returned=False,expiry_date__gte=today).order_by('expiry_date')
                    stock=Stock.objects.get(medicine_name=medicine_id).quantity
                    if stock>quantity:
                        for e in expiry:
                            q=e.quantity
                            em=e.id
                            if q>quantity:
                                q=q-quantity
                                Expiry.objects.select_related('medicine_id').filter(id=em).update(quantity=q)
                                qty = Stock.objects.get(medicine_name=medicine_id).quantity
                                qty = qty-quantity
                                Stock.objects.filter(medicine_name=medicine_id).update(quantity=qty)
                                break
                            else:
                                quan=Expiry.objects.select_related('medicine_id').get(id=em).quantity
                                Expiry.objects.select_related('medicine_id').filter(id=em).update(quantity=0)
                                qty = Stock.objects.get(medicine_name=medicine_id).quantity
                                qty = qty-quan
                                Stock.objects.filter(medicine_name=medicine_id).update(quantity=qty)
                                quantity=quantity-quan
                        status = 1
                    else:
                        status = 0
                    Medicine.objects.select_related('patient','patient__user','patient__department').all().delete()

                healthcare_center_notif(request.user, user.user, 'presc')
#                   Notification.objects.create(notif_type='healthcenter',recipient=user.user,action_verb='prescribed',display_text='You have been prescribed for '+details)
                data = {'status': status, 'stock': stock}
                return JsonResponse(data)
            elif 'prescribe_b' in request.POST:
                user_id = request.POST.get('user')
                user = ExtraInfo.objects.select_related('user','department').get(id=user_id)
                doctor_id = request.POST.get('doctor')
                if doctor_id == "":
                    doctor = None
                else:
                    doctor = Doctor.objects.get(id=doctor_id)
                details = request.POST.get('details')
                tests = request.POST.get('tests')
                app = Appointment.objects.select_related('user_id','user_id__user','user_id__department','doctor_id','schedule','schedule__doctor_id').filter(user_id=user_id,date=datetime.now())
                if app:
                    appointment = Appointment.objects.select_related('user_id','user_id__user','user_id__department','doctor_id','schedule','schedule__doctor_id').get(user_id=user_id,date=datetime.now())
                else:
                    appointment = None
                Prescription.objects.create(
                    user_id=user,
                    doctor_id=doctor,
                    details=details,
                    date=datetime.now(),
                    test=tests,
                    appointment=appointment
                )
                query = Medicine.objects.select_related('patient','patient__user','patient__department').filter(patient=user)
                prescribe = Prescription.objects.select_related('user_id','user_id__user','user_id__department','doctor_id','appointment','appointment__user_id','appointment__user_id__user','appointment__user_id__department','appointment__doctor_id','appointment__schedule','appointment__schedule__doctor_id').all().last()
                for medicine in query:
                    medicine_id = medicine.medicine_id
                    quantity = medicine.quantity
                    days = medicine.days
                    times = medicine.times
                    Prescribed_medicine.objects.create(
                        prescription_id=prescribe,
                        medicine_id=medicine_id,
                        quantity=quantity,
                        days=days,
                        times=times
                    )
                    today=datetime.now()
                    expiry=Expiry.objects.select_related('medicine_id').filter(medicine_id=medicine_id,quantity__gt=0,returned=False,expiry_date__gte=today).order_by('expiry_date')
                    stock=Stock.objects.get(medicine_name=medicine_id).quantity
                    if stock>quantity:
                        for e in expiry:
                            q=e.quantity
                            em=e.id
                            if q>quantity:
                                q=q-quantity
                                Expiry.objects.select_related('medicine_id').filter(id=em).update(quantity=q)
                                qty = Stock.objects.get(medicine_name=medicine_id).quantity
                                qty = qty-quantity
                                Stock.objects.filter(medicine_name=medicine_id).update(quantity=qty)
                                break
                            else:
                                quan=Expiry.objects.select_related('medicine_id').get(id=em).quantity
                                Expiry.objects.select_related('medicine_id').filter(id=em).update(quantity=0)
                                qty = Stock.objects.get(medicine_name=medicine_id).quantity
                                qty = qty-quan
                                Stock.objects.filter(medicine_name=medicine_id).update(quantity=qty)
                                quantity=quantity-quan
                        status = 1

                    else:
                        status = 0
                    Medicine.objects.select_related('patient','patient__user','patient__department').all().delete()

                healthcare_center_notif(request.user, user.user, 'presc')
#                    Notification.objects.create(notif_type='healthcenter',recipient=user.user,action_verb='prescribed',display_text='You have been prescribed for '+details)
                data = {'status': status}
                return JsonResponse(data)
            elif 'cancel_presc' in request.POST:
                presc_id = request.POST.get('cancel_presc')
                Prescription.objects.select_related('user_id','user_id__user','user_id__department','doctor_id','appointment','appointment__user_id','appointment__user_id__user','appointment__user_id__department','appointment__doctor_id','appointment__schedule','appointment__schedule__doctor_id').filter(pk=presc_id).delete()
                #a = User.objects.all()
                #                for user in a:
                #                    Notification.objects.create(notif_type='healthcenter',recipient=user,action_verb='removed',display_text='Dr.'+doc+'will not be available from now')
                data = {'status': 1}
                return JsonResponse(data)
            elif 'medicine' in request.POST:
                med_id = request.POST.get('medicine')
                thresh = Stock.objects.get(id=med_id).threshold
                data = {'thresh': thresh}
                return JsonResponse(data)


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
            return render(request, 'phcModule/phc_compounder.html',
                          {'days': days, 'users': users, 'count': count,'expired':expired,
                           'stocks': stocks, 'all_complaints': all_complaints,
                           'all_hospitals': all_hospitals, 'hospitals':hospitals, 'all_ambulances': all_ambulances,
                           'appointments_today': appointments_today, 'doctors': doctors,
                           'appointments_future': appointments_future, 'schedule': schedule, 'live_meds': live_meds, 'presc_hist': presc_hist, 'medicines_presc': medicines_presc, 'hospitals_list': hospitals_list})
    elif usertype == 'student':
        return HttpResponseRedirect("/healthcenter/student")                                      # compounder view ends


def student_view(request):                                                                    # student view starts here
    usertype = ExtraInfo.objects.select_related('user','department').get(user=request.user).user_type
    if usertype == 'student' or usertype == 'faculty' or usertype == 'staff':
        if request.method == 'POST':
            if 'amb_submit' in request.POST:
                user_id = ExtraInfo.objects.select_related('user','department').get(user=request.user)
                comp_id = ExtraInfo.objects.select_related('user','department').filter(user_type='compounder')
                reason = request.POST.get('reason')
                start_date = request.POST.get('start_date')
                end_date = request.POST.get('end_date')
                if end_date == '':
                    end_date = None
                Ambulance_request.objects.create(
                     user_id=user_id,
                     date_request=datetime.now(),
                     start_date=start_date,
                     end_date=end_date,
                     reason=reason
                 )
                data = {'status': 1}
                healthcare_center_notif(request.user, request.user, 'amb_request')
                for cmp in comp_id:
                     healthcare_center_notif(request.user, cmp.user, 'amb_req')

                return JsonResponse(data)
            elif "amb_submit1" in request.POST:
                user_id = ExtraInfo.objects.select_related('user','department').get(user=request.user)
                comp_id = ExtraInfo.objects.select_related('user','department').filter(user_type='compounder')
                doctor_id = request.POST.get('doctor')
                doctor = Doctor.objects.get(id=doctor_id)
                date = request.POST.get('date')
                schedule = Schedule.objects.select_related('doctor_id').get(id=date)
                datei = schedule.date
                app_time = schedule.to_time
                description = request.POST.get('description')
                Appointment.objects.create(
                    user_id=user_id,
                    doctor_id=doctor,
                    description=description,
                    schedule=schedule,
                    date=datei
                )
                data = {
                        'app_time': app_time, 'dt': datei , 'status' : 1
                        }
                healthcare_center_notif(request.user, request.user, 'appoint')
                for cmp in comp_id:
                     healthcare_center_notif(request.user, cmp.user, 'appoint_req')

                return JsonResponse(data)
            elif 'doctor' in request.POST:
                doctor_id = request.POST.get('doctor')
                #app_time = Schedule.objects.get(doctor_id=doctor_id)
                days = Schedule.objects.select_related('doctor_id').filter(doctor_id=doctor_id).values('day')
                today = datetime.today()
                time = datetime.today().time()
                sch = Schedule.objects.select_related('doctor_id').filter(date__gte=today)

                for day in days:
                    for i in range(0, 7):
                        date = (datetime.today()+timedelta(days=i)).date()
                        dayi = date.weekday()
                        d = day.get('day')
                        if dayi == d:

                            Schedule.objects.select_related('doctor_id').filter(doctor_id=doctor_id, day=dayi).update(date=date)

                sch.filter(date=today, to_time__lt=time).delete()
                schedule = sch.filter(doctor_id=doctor_id).order_by('date')
                schedules = serializers.serialize('json', schedule)
                return HttpResponse(schedules, content_type='json')
            elif 'feed_submit' in request.POST:
                user_id = ExtraInfo.objects.select_related('user','department').get(user=request.user)
                feedback = request.POST.get('feedback')
                Complaint.objects.create(
                    user_id=user_id,
                    complaint=feedback,
                    date=datetime.now()
                )
                data = {'status': 1}
                return JsonResponse(data)
            elif 'cancel_amb' in request.POST:
                amb_id = request.POST.get('cancel_amb')
                Ambulance_request.objects.select_related('user_id','user_id__user','user_id__department').filter(pk=amb_id).delete()
                #a = User.objects.all()
                #                for user in a:
                #                    Notification.objects.create(notif_type='healthcenter',recipient=user,action_verb='removed',display_text='Dr.'+doc+'will not be available from now')
                data = {'status': 1}
                return JsonResponse(data)
            elif 'cancel_app' in request.POST:
                app_id = request.POST.get('cancel_app')
                Appointment.objects.select_related('user_id','user_id__user','user_id__department','doctor_id','schedule','schedule__doctor_id').filter(pk=app_id).delete()
                #a = User.objects.all()
                #                for user in a:
                #                    Notification.objects.create(notif_type='healthcenter',recipient=user,action_verb='removed',display_text='Dr.'+doc+'will not be available from now')
                data = {'status': 1}
                return JsonResponse(data)

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

            return render(request, 'phcModule/phc_student.html',
                          {'complaints': complaints, 'medicines': medicines,
                           'ambulances': ambulances, 'doctors': doctors, 'days': days,'count':count,
                           'hospitals': hospitals, 'appointments': appointments,
                           'prescription': prescription, 'schedule': schedule, 'users': users})
    elif usertype == 'compounder':
        return HttpResponseRedirect("/healthcenter/compounder")                                     # student view ends

def schedule_entry(request):
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
