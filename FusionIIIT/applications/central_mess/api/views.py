    #APIs
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import *
from django.shortcuts import get_object_or_404
from applications.central_mess.models import *
from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation
from django.http import JsonResponse

class FeedbackApi(APIView):

    def get(self, request):
        feedback_obj = Feedback.objects.all();
        serialized_obj = FeedbackSerializer(feedback_obj, many=True)
        return Response({'status':200, 'payload':serialized_obj.data})

    def post(self, request):
        data = request.data
        
        mess = data['mess']
        _type = data['type']
        desc = data['desc']
        username = get_object_or_404(User,username=request.user.username)
        idd = ExtraInfo.objects.get(user=username)
        student = Student.objects.get(id=idd.id)
        obj = Feedback(
            student_id = student,
            mess =mess,
            feedback_type=_type,
            description=desc
        )
        obj.save()
        return Response({'status':200})


class MessinfoApi(APIView):
    def get(self, request):
        messinfo_obj = Messinfo.objects.all();
        serialized_obj = MessinfoSerializer(messinfo_obj, many=True)
        return Response({'status':200, 'payload':serialized_obj.data})  

    def post(self, request):
        data = request.data
        
        mess_option = data['mess_option']
        
        username = get_object_or_404(User,username=request.user.username)
        idd = ExtraInfo.objects.get(user=username)
        student = Student.objects.get(id=idd.id)
        obj = Messinfo(
            student_id = student,
            mess_option =mess_option,
        )
        obj.save()
        return Response({'status':200})          

class Mess_regApi(APIView):
    def get(self, request):
        mess_reg_obj = Mess_reg.objects.all();
        serialized_obj = Mess_regSerializer(mess_reg_obj, many=True)
        return Response({'status':200, 'payload':serialized_obj.data})    

    def post(self, request):
        data = request.data
        
        sem = data['sem']
        start_reg = data['start_reg']
        end_reg= data['end_reg']
        
        obj = Mess_reg(
            sem = sem,
            start_reg = start_reg,
            end_reg = end_reg
        )
        obj.save()
        return Response({'status':200})              

class MessBillBaseApi(APIView):
    def get(self, request):
        messBillBase_obj = MessBillBase.objects.all();
        serialized_obj = MessBillBaseSerializer(messBillBase_obj, many=True)
        return Response({'status':200, 'payload':serialized_obj.data})  

    def post(self, request):
        data = request.data
        
        bill_amount = data['bill_amount']
        # timestamp = data['timestamp']
        
        obj = MessBillBase(
            bill_amount = bill_amount,
            # timestamp = timestamp,
        )
        obj.save()
        return Response({'status':200})      

class Monthly_billApi(APIView):
    def get(self, request):
        monthly_bill_obj = Monthly_bill.objects.all();
        serialized_obj = Monthly_billSerializer(monthly_bill_obj, many=True)
        return Response({'status':200, 'payload':serialized_obj.data})    

    def post(self, request):
        data = request.data
        
        month = data['month']
        year = data['year']
        amount = data['amount']
        rebate_count = data['rebate_count']
        rebate_amount = data['rebate_amount']
        #nonveg_total_bill = data['nonveg_total_bill']
        paid = data['paid']

        username = get_object_or_404(User,username=request.user.username)
        idd = ExtraInfo.objects.get(user=username)
        student = Student.objects.get(id=idd.id)

        
        obj = Monthly_bill(
            student_id = student,
            month = month,
            year = year,
            amount = amount,
            rebate_count = rebate_count,
            rebate_amount = rebate_amount,
            # nonveg_total_bill = nonveg_total_bill,
            paid = paid
        )
        obj.save()
        return Response({'status':200})                       

class PaymentsApi(APIView):
    def get(self, request):
        payments_obj = Payments.objects.all();
        serialized_obj = PaymentsSerializer(payments_obj, many=True)
        return Response({'status':200, 'payload':serialized_obj.data})   

    def post(self, request):
        data = request.data
        
        # sem = data['sem']
        # year = data['year']
        amount_paid = data['amount_paid']


        username = get_object_or_404(User,username=request.user.username)
        idd = ExtraInfo.objects.get(user=username)
        student = Student.objects.get(id=idd.id)

        
        obj = Payments(
            student_id = student,
            # sem = sem,
            # year = year,
            amount_paid = amount_paid,
        )
        obj.save()
        return Response({'status':200}) 
class MenuApi(APIView):
    def get(self, request):
        menu_obj = Menu.objects.all();
        serialized_obj = MenuSerializer(menu_obj, many=True)
        return Response({'status':200, 'payload':serialized_obj.data})

    def post(self, request):
        data = request.data
        
        mess_option = data['mess_option']
        meal_time = data['meal_time']
        dish = data['dish']

        
        obj = Menu(
            mess_option = mess_option,
            meal_time = meal_time,
            dish = dish,
        )
        obj.save()
        return Response({'status':200})     
class RebateApi(APIView):
    def get(self, request):
        rebate_obj = Rebate.objects.all();
        serialized_obj = RebateSerializer(rebate_obj, many=True)
        return Response({'status':200, 'payload':serialized_obj.data}) 

    def post(self, request):
        data = request.data

        # student_id = data['mess_option']
        start_date = data['start_date']
        end_date = data['end_date']
        purpose = data['purpose']
        status = data['status']
        app_date = data['app_date']
        leave_type = data['leave_type']

        username = get_object_or_404(User,username=request.user.username)
        idd = ExtraInfo.objects.get(user=username)
        student = Student.objects.get(id=idd.id)

        
        obj = Rebate(
            student_id = student,
            leave_type = leave_type,
            app_date = app_date,
            status = status,
            purpose = purpose,
            end_date= end_date,
            start_date = start_date
        )
        obj.save()
        return Response({'status':200})       
class Vacation_foodApi(APIView):
    def get(self, request):
        vacation_food_obj = Vacation_food.objects.all();
        serialized_obj = Vacation_foodSerializer(vacation_food_obj, many=True)
        return Response({'status':200, 'payload':serialized_obj.data}) 

    def post(self, request):
        data = request.data
        
        start_date = data['start_date']
        end_date = data['end_date']
        purpose = data['purpose']
        status = data['status']
        app_date = data['app_date']


        username = get_object_or_404(User,username=request.user.username)
        idd = ExtraInfo.objects.get(user=username)
        student = Student.objects.get(id=idd.id)

        
        obj = Vacation_food(
            student_id = student,
            app_date = app_date,
            status = status,
            purpose = purpose,
            end_date= end_date,
            start_date = start_date
        )
        obj.save()
        return Response({'status':200})       

class Nonveg_menuApi(APIView):
    def get(self, request):
        nonveg_menu_obj = Nonveg_menu.objects.all();
        serialized_obj = Nonveg_menuSerializer(nonveg_menu_obj, many=True)
        return Response({'status':200, 'payload':serialized_obj.data})   

    def post(self, request):
        data = request.data
        
        dish= data['dish']
        price = data['price']
        order_interval = data['order_interval']

        
        obj = Nonveg_menu(
            dish = dish,
            price = price,
            order_interval = order_interval,
        )
        obj.save()
        return Response({'status':200})     

class Nonveg_dataApi(APIView):
    def get(self, request):
        nonveg_data_obj = Nonveg_data.objects.all();
        serialized_obj = Nonveg_dataSerializer(nonveg_data_obj, many=True)
        return Response({'status':200, 'payload':serialized_obj.data})   

    def post(self, request):
        data = request.data
        
        dish= data['dish']
        order_date = data['order_date']
        app_date = data['app_date']
        order_interval = data['order_interval']

        username = get_object_or_404(User,username=request.user.username)
        idd = ExtraInfo.objects.get(user=username)
        student = Student.objects.get(id=idd.id)

        dish_obj = Nonveg_menu.objects.get(dish=dish)
        
        obj = Nonveg_data(
            student_id = student,
            order_date = order_date,
            app_date = app_date,
            dish = dish_obj,
            order_interval = order_interval,
        )
        obj.save()
        return Response({'status':200})        

class Special_requestApi(APIView):
    def get(self, request):
        special_request_obj = Special_request.objects.all();
        serialized_obj = Special_requestSerializer(special_request_obj, many=True)
        return Response({'status':200, 'payload':serialized_obj.data})  

        
    def post(self, request):
        data = request.data
        
      
        start_date = data['start_date']
        end_date = data['end_date']
        status = data['status']
        app_date = data['app_date']
        request_= data['request']
        item1 = data['item1']
        item2 = data['item2']



        username = get_object_or_404(User,username=request.user.username)
        idd = ExtraInfo.objects.get(user=username)
        student = Student.objects.get(id=idd.id)
        
        obj = Special_request(
            student_id = student,
            app_date = app_date,
            status = status,
            item1 = item1,
            item2 = item2,
            end_date= end_date,
            start_date = start_date,
            request = request_
        )
        obj.save()
        return Response({'status':200})        

class Mess_meetingApi(APIView):
    def get(self, request):
        mess_meeting_obj = Mess_meeting.objects.all();
        serialized_obj = Mess_meetingSerializer(mess_meeting_obj, many=True)
        return Response({'status':200, 'payload':serialized_obj.data})    

    def post(self, request):
        data = request.data
        meet_date = data['meet_date']
        agenda  = data['agenda']
        venue = data['venue']
        meeting_time = data['meeting_time']

        obj = Mess_meeting(
            meet_date = meet_date,
            meeting_time = meeting_time,
            agenda = agenda,
            venue = venue,
        )
        obj.save()
        return Response({'status':200})      

class Mess_minutesApi(APIView):
    def get(self, request):
        mess_minutes_obj = Mess_minutes.objects.all();
        serialized_obj = Mess_minutesSerializer(mess_minutes_obj, many=True)
        return Response({'status':200, 'payload':serialized_obj.data})    

    def post(self, request):
        data = request.data

        # meeting_date  = data['meeting_date']
        mess_minutes  = data['mess_minutes']
        meeting_date_obj = Mess_meeting.objects.get(meet_date=meeting_date)

        obj = Mess_minutes(
            # meeting_date = meeting_date_obj,
            mess_minutes = mess_minutes,
        )
        obj.save()
        return Response({'status':200})   
  
class Menu_change_requestApi(APIView):
    def get(self, request):
        menu_change_request_obj = Menu_change_request.objects.all();
        serialized_obj = Menu_change_requestSerializer(menu_change_request_obj, many=True)
        return Response({'status':200, 'payload':serialized_obj.data})   

    def post(self, request):
        data = request.data
        dish = data['dish']
        reason = data['reason']
        status = data['status']
        app_date = data['app_date']
        request_ = data['request']


        dish_obj = Menu.objects.get(dish=dish)
        username = get_object_or_404(User,username=request.user.username)
        idd = ExtraInfo.objects.get(user=username)
        student = Student.objects.get(id=idd.id)
        
        obj = Menu_change_request(
            student_id = student,
            app_date = app_date,
            status = status,
            reason = reason,
            request = request_,
            dish = dish_obj
        )
        obj.save()
        return Response({'status':200})      

class Get_Filtered_Students(APIView): 

    def post(self,request):
        type = request.data['type']
        if(type=='filter'):
            reg_main = Reg_main.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department').all()
            status=request.data['status']
            program=request.data['program']
            mess_option=request.data['mess_option']

            if(status!='all'):

                reg_main=reg_main.filter(current_mess_status=status)

            if(program!='all'):
                reg_main=reg_main.filter(program=program)

            if(mess_option!='all'):

                reg_main=reg_main.filter(mess_option=mess_option)        

            serialized_obj = GetFilteredSerialzer(reg_main,many=True)
            return Response({'payload':serialized_obj.data})

        elif(type=='search'):
            student = request.data['student_id']
            student = str(student).upper()
            try:
                reg_main = Reg_main.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department').get(student_id=student)
                serialized_obj = GetFilteredSerialzer(reg_main)
                return Response({'payload':serialized_obj.data})
            except:
                response = JsonResponse({"error": "student does not exist"})
                response.status_code = 404 
                return response

class Get_Reg_Records(APIView):

    def post(self,request):
        student = request.data['student_id']
        reg_record = Reg_records.objects.filter(student_id=student)

        serialized_obj = reg_recordSerialzer(reg_record,many=True)
        return Response({'payload':serialized_obj.data}) 


class Get_Student_bill(APIView):

    def post(self,request):
        student = request.data['student_id'] 
        bill_details = Monthly_bill.objects.filter(student_id=student)

        serialized_obj = Monthly_billSerializer(bill_details,many=True)
        return Response({'payload':serialized_obj.data}) 


class Get_Student_Payments(APIView):

    def post(self,request):
        student = request.data['student_id'] 
        payment_details = Payments.objects.filter(student_id=student)

        serialized_obj = PaymentsSerializer(payment_details,many=True)
        return Response({'payload':serialized_obj.data}) 
    
class Get_Student_Details(APIView):

    def post(self,request):
        student = request.data['student_id'] 
        bill_details = Monthly_bill.objects.filter(student_id=student)
        payment_details = Payments.objects.filter(student_id=student)
        reg_record = Reg_records.objects.filter(student_id=student)
        payment_serialized_obj = PaymentsSerializer(payment_details,many=True)
        bill_serialized_obj = Monthly_billSerializer(bill_details,many=True)
        reg_record_serialized_obj = reg_recordSerialzer(reg_record,many=True)
        reg_main = Reg_main.objects.select_related('student_id','student_id__id','student_id__id__user','student_id__id__department').get(student_id=student)
        serialized_obj = GetFilteredSerialzer(reg_main)
        data={'payment':payment_serialized_obj.data,'bill':bill_serialized_obj.data,'reg_records':reg_record_serialized_obj.data,'student_details':serialized_obj.data}
        return Response({'payload':data}) 