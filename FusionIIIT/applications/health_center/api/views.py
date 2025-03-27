# from django.contrib.auth import get_user_model
# from django.shortcuts import get_object_or_404, redirect
# from applications.globals.models import ExtraInfo, HoldsDesignation, Designation, DepartmentInfo
# from applications.health_center.models import *
# from datetime import datetime, timedelta, time,date
# from django.db import transaction
# from notification.views import  healthcare_center_notif
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.authentication import TokenAuthentication
# from rest_framework import status
# from rest_framework.decorators import api_view, permission_classes,authentication_classes
# from rest_framework.permissions import AllowAny
# from rest_framework.response import Response


# from . import serializers

# from notifications.models import Notification

# User = get_user_model()

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