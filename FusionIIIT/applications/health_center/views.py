import json
from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from applications.globals.models import ExtraInfo

from .models import (Ambulance_request, Appointment, Complaint, Constants,
                     Doctor, Hospital_admit, Medicine, Prescribed_medicine,
                     Prescription, Schedule, Stock, Stockinventory)


def datetime_handler(x):
    if hasattr(x, 'isoformat'):
        return x.isoformat()
    else:
        raise TypeError


@login_required
def healthcenter(request):
    usertype = ExtraInfo.objects.get(user=request.user).user_type
    if usertype == 'student':
        return HttpResponseRedirect("/healthcenter/student")
    elif usertype == 'compounder':
        return HttpResponseRedirect("/healthcenter/compounder")


@login_required
def compounder_view(request):

    usertype = ExtraInfo.objects.get(user=request.user).user_type
    if usertype == 'compounder':
        if request.method == 'POST':

            if 'feed_com' in request.POST:
                print("anjali")
                pk = request.POST.get('com_id')
                feedback = request.POST.get('feed')
                Complaint.objects.filter(id=pk).update(feedback=feedback)
                data = {'feedback': feedback}
                return JsonResponse(data)
            elif 'end' in request.POST:
                pk = request.POST.get('id')
                Ambulance_request.objects.filter(
                    id=pk).update(end_date=datetime.now())
                amb = Ambulance_request.objects.filter(id=pk)
                for f in amb:
                    dateo = f.end_date
                data = {'datenow': dateo}
                return JsonResponse(data)
            elif 'discharge' in request.POST:
                pk = request.POST.get('id')
                Hospital_admit.objects.filter(id=pk).update(
                    discharge_date=datetime.now())
                hosp = Hospital_admit.objects.filter(id=pk)
                for f in hosp:
                    dateo = f.discharge_date
                data = {'datenow': dateo}
                return JsonResponse(data)
            elif 'add_stock' in request.POST:
                medicine = request.POST.get('medicine_id')
                medicine_name = Stock.objects.get(id=medicine)
                qty = int(request.POST.get('quantity'))
                Stockinventory.objects.create(
                    medicine_id=medicine_name,
                    quantity=qty,
                    date=datetime.now()
                )
                quantity = (Stock.objects.get(id=medicine)).quantity
                quantity = quantity + qty
                Stock.objects.filter(id=medicine).update(quantity=quantity)
                data = {'status': 1}
                return JsonResponse(data)
            elif 'edit' in request.POST:
                doctor = request.POST.get('doctor')
                day = request.POST.get('day')
                time_in = request.POST.get('time_in')
                time_out = request.POST.get('time_out')
                room = request.POST.get('room')
                sc = Schedule.objects.filter(doctor_id=doctor, day=day)
                doctor_id = Doctor.objects.get(id=doctor)
                if sc.count() == 0:
                    Schedule.objects.create(doctor_id=doctor_id, day=day, room=room,
                                            from_time=time_in, to_time=time_out)
                else:
                    Schedule.objects.filter(
                        doctor_id=doctor_id, day=day).update(room=room)
                    Schedule.objects.filter(
                        doctor_id=doctor_id, day=day).update(from_time=time_in)
                    Schedule.objects.filter(
                        doctor_id=doctor_id, day=day).update(to_time=time_out)
                data = {}
                return JsonResponse(data)
            elif 'add_medicine' in request.POST:
                medicine = request.POST.get('new_medicine')
                quantity = request.POST.get('new_quantity')
                threshold = request.POST.get('threshold')
                Stock.objects.create(
                    medicine_name=medicine,
                    quantity=quantity,
                    threshold=threshold
                )
                medicine_id = Stock.objects.get(medicine_name=medicine)
                Stockinventory.objects.create(
                    medicine_id=medicine_id,
                    quantity=quantity,
                    date=datetime.now()
                )
                data = {'status': 1}
                return JsonResponse(data)
            elif 'user_p' in request.POST:
                app = Appointment.objects.filter(
                    user_id=request.POST.get('user_p'), date=datetime.now())
                print(app)
                if app:
                    s = 1
                else:
                    s = 0
                data = {'status': s}
                return JsonResponse(data)
            elif 'admission' in request.POST:
                user = request.POST.get('user_id')
                user_id = ExtraInfo.objects.get(id=user)
                doctor = request.POST.get('doctor_id')
                doctor_id = Doctor.objects.get(id=doctor)
                admission_date = request.POST.get('admission_date')
                reason = request.POST.get('description')
                hospital_doctor = request.POST.get('hospital_doctor')
                hospital_name = request.POST.get('hospital_name')
                Hospital_admit.objects.create(
                    user_id=user_id,
                    doctor_id=doctor_id,
                    hospital_name=hospital_name,
                    admission_date=admission_date,
                    hospital_doctor=hospital_doctor,
                    discharge_date=None,
                    reason=reason
                )
                data = {'status': 1}
                return JsonResponse(data)
            elif 'medicine_name' in request.POST:
                app = request.POST.get('user')
                user = Appointment.objects.get(id=app).user_id
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
                schs = Medicine.objects.all()
                list = []
                for s in schs:
                    list.append({'medicine': s.medicine_id.medicine_name, 'quantity': s.quantity,
                                 'days': s.days, 'times': s.times})
                sches = json.dumps(list, default=datetime_handler)
                return HttpResponse(sches, content_type='json')
            elif 'day' in request.POST:
                day = request.POST.get('day')
                sche = Schedule.objects.filter(day=day)
                list = []
                for s in sche:
                    list.append({'room': s.room, 'id': s.id, 'doctor': s.doctor_id.doctor_name,
                                 'from_time': s.from_time, 'to_time': s.to_time})

                sches = json.dumps(list, default=datetime_handler)
                return HttpResponse(sches, content_type='json')
            elif 'medicine_name_b' in request.POST:
                user_id = request.POST.get('user')
                user = ExtraInfo.objects.get(id=user_id)
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
                schs = Medicine.objects.all()
                list = []
                for s in schs:
                    list.append({'medicine': s.medicine_id.medicine_name, 'quantity': s.quantity,
                                 'days': s.days, 'times': s.times})
                sches = json.dumps(list, default=datetime_handler)
                return HttpResponse(sches, content_type='json')
            elif 'day' in request.POST:
                day = request.POST.get('day')
                sche = Schedule.objects.filter(day=day)
                list = []
                for s in sche:
                    list.append({'room': s.room, 'id': s.id, 'doctor': s.doctor_id.doctor_name,
                                 'from_time': s.from_time, 'to_time': s.to_time})

                sches = json.dumps(list, default=datetime_handler)
                return HttpResponse(sches, content_type='json')
            elif 'main' in request.POST:
                data = {
                    'status': 1
                }
                return JsonResponse(data)
            elif 'doct' in request.POST:
                doctor_id = request.POST.get('doct')
                schedule = Schedule.objects.filter(doctor_id=doctor_id)
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
                appointment = Appointment.objects.get(id=app_id)
                user = appointment.user_id
                doctor = appointment.doctor_id
                Prescription.objects.create(
                    user_id=user,
                    doctor_id=doctor,
                    details=details,
                    date=datetime.now(),
                    test=tests,
                    appointment=appointment
                )
                query = Medicine.objects.filter(patient=user)
                prescribe = Prescription.objects.all().last()
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
                    qty = Stock.objects.get(medicine_name=medicine_id).quantity
                    qty = qty-quantity
                    Stock.objects.filter(
                        medicine_name=medicine_id).update(quantity=qty)
                    Medicine.objects.all().delete()
                    data = {
                        'status': 1
                    }
                return JsonResponse(data)
            elif 'prescribe_b' in request.POST:
                user_id = request.POST.get('user')
                user = ExtraInfo.objects.get(id=user_id)
                doctor_id = request.POST.get('doctor')
                if doctor_id == "":
                    doctor = None
                else:
                    doctor = Doctor.objects.get(id=doctor_id)
                details = request.POST.get('details')
                tests = request.POST.get('tests')
                app = Appointment.objects.filter(
                    user_id=user_id, date=datetime.now())
                print(app)
                if app:
                    appointment = Appointment.objects.get(
                        user_id=user_id, date=datetime.now())
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
                query = Medicine.objects.filter(patient=user)
                prescribe = Prescription.objects.all().last()
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
                    qty = Stock.objects.get(medicine_name=medicine_id).quantity
                    qty = qty-quantity
                    Stock.objects.filter(
                        medicine_name=medicine_id).update(quantity=qty)
                    Medicine.objects.all().delete()
                    data = {
                        'status': 1
                    }
                return JsonResponse(data)

        else:
            all_complaints = Complaint.objects.all()
            all_hospitals = Hospital_admit.objects.all().order_by('-admission_date')
            all_ambulances = Ambulance_request.objects.all().order_by('-date_request')
            appointments_today = Appointment.objects.filter(
                date=datetime.now()).order_by('date')
            appointments_future = Appointment.objects.filter(
                date__gt=datetime.now()).order_by('date')
            users = ExtraInfo.objects.filter(user_type='student')
            doctors = Doctor.objects.all()
            inventories = Stockinventory.objects.all().order_by('-date')
            stocks = Stock.objects.all()
            days = Constants.DAYS_OF_WEEK
            schedule = Schedule.objects.all()
            return render(request, 'phcModule/phc_compounder.html',
                          {'inventories': inventories, 'days': days, 'users': users,
                           'stocks': stocks, 'all_complaints': all_complaints,
                           'all_hospitals': all_hospitals, 'all_ambulances': all_ambulances,
                           'appointments_today': appointments_today, 'doctors': doctors,
                           'appointments_future': appointments_future, 'schedule': schedule})
    elif usertype == 'student':
        return HttpResponseRedirect("/healthcenter/student")


def student_view(request):
    usertype = ExtraInfo.objects.get(user=request.user).user_type
    if usertype == 'student':
        if request.method == 'POST':
            if 'amb_submit' in request.POST:
                user_id = ExtraInfo.objects.get(user=request.user)
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
                return JsonResponse(data)
            elif "appointment" in request.POST:
                user_id = ExtraInfo.objects.get(user=request.user)
                doctor_id = request.POST.get('doctor')
                doctor = Doctor.objects.get(id=doctor_id)
                date = request.POST.get('date')
                schedule = Schedule.objects.get(id=date)
                datei = schedule.date
                description = request.POST.get('description')
                Appointment.objects.create(
                    user_id=user_id,
                    doctor_id=doctor,
                    description=description,
                    schedule=schedule,
                    date=datei
                )
                data = {
                    'status': 1
                }
                return JsonResponse(data)
            elif 'doctor' in request.POST:
                doctor_id = request.POST.get('doctor')
                schedule = Schedule.objects.filter(doctor_id=doctor_id)
                days = Schedule.objects.filter(
                    doctor_id=doctor_id).values('day')
                for day in days:
                    for i in range(0, 7):
                        date = (datetime.today()+timedelta(days=i)).date()
                        dayi = date.weekday()
                        d = day.get('day')
                        if dayi == d:
                            Schedule.objects.filter(
                                doctor_id=doctor_id, day=dayi).update(date=date)
                schedule = Schedule.objects.filter(doctor_id=doctor_id)
                schedules = serializers.serialize('json', schedule)
                return HttpResponse(schedules, content_type='json')
            elif 'feed_submit' in request.POST:
                user_id = ExtraInfo.objects.get(user=request.user)
                feedback = request.POST.get('feedback')
                Complaint.objects.create(
                    user_id=user_id,
                    complaint=feedback,
                    date=datetime.now()
                )
                data = {'status': 1}
                return JsonResponse(data)
        else:
            users = ExtraInfo.objects.all()
            user_id = ExtraInfo.objects.get(user=request.user)
            hospitals = Hospital_admit.objects.filter(
                user_id=user_id).order_by('-admission_date')
            appointments = Appointment.objects.filter(
                user_id=user_id).order_by('-date')
            ambulances = Ambulance_request.objects.filter(
                user_id=user_id).order_by('-date_request')
            prescription = Prescription.objects.filter(
                user_id=user_id).order_by('-date')
            medicines = Prescribed_medicine.objects.all()
            schedule = Schedule.objects.all()
            complaints = Complaint.objects.filter(
                user_id=user_id).order_by('-date')
            doctors = Doctor.objects.all()
            days = Constants.DAYS_OF_WEEK

            return render(request, 'phcModule/phc_student.html',
                          {'complaints': complaints, 'medicines': medicines,
                           'ambulances': ambulances, 'doctors': doctors, 'days': days,
                           'hospitals': hospitals, 'appointments': appointments,
                           'prescription': prescription, 'schedule': schedule, 'users': users})
    elif usertype == 'compounder':
        return HttpResponseRedirect("/healthcenter/compounder")
