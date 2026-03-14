import datetime
from datetime import date, datetime, timedelta

from django.contrib import messages
from django import forms
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from applications.globals.models import User , ExtraInfo, HoldsDesignation

from notifications.models import Notification
from .models import Caretaker, StudentComplain, Supervisor, Workers, SectionIncharge
from notification.views import  complaint_system_notif


from applications.filetracking.sdk.methods import *
from applications.filetracking.models import *
from operator import attrgetter

#function for reassign to another worker
# @login_required
# def complaint_reassign(request,wid,iid):
    # current_user = get_object_or_404(User, username=request.user.username)
    # y = ExtraInfo.objects.all().select_related('user','department').filter(user=current_user).first()
    # if request.method == 'POST':
    #     type = request.POST.get('submit', '')
    #     a = get_object_or_404(User, username=request.user.username)
    #     y = ExtraInfo.objects.all().select_related('user','department').filter(user=a).first()
    #     comp_id = y.id
    #     if type == 'assign':

    #         complaint_finish = request.POST.get('complaint_finish', '')
    #         worker_id = request.POST.get('assign_worker', '')
    #         w = Workers.objects.select_related('secincharge_id','secincharge_id__staff_id','secincharge_id__staff_id__user','secincharge_id__staff_id__department').get(id=worker_id)
    #         StudentComplain.objects.select_for_update().filter(id=iid).\
    #             update(worker_id=w, status=1)
    #         url = '/complaint/secincharge/worker_id_know_more/'+wid;
    #         complainer_details = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department').get(id=iid)
    #         student=0
    #         message = "Your complaint has been re-assigned"
    #         complaint_system_notif(request.user, complainer_details.complainer.user ,'reassign_worker_alert',complainer_details.id,student,message)
    #         return HttpResponseRedirect(url)
        
    # else:
    #     y = ExtraInfo.objects.all().select_related('user','department').get(id=y.id)
    #     a = SectionIncharge.objects.select_related('staff_id','staff_id__user','staff_id__department').get(staff_id=y)
    #     b = a.work_type
    #     comp_id = y.id
    #     try:
    #         detail = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department').filter(id=iid).first()
    #         total_secincharge = SectionIncharge.objects.select_related('staff_id','staff_id__user','staff_id__department').all()
    #         total_secincharges_in_area = SectionIncharge.objects.select_related('staff_id','staff_id__user','staff_id__department').filter(work_type=b)
    #         worker = []
    #         workertemp = []
    #         flag = ''
    #         temp = detail.location
    #         try:
            
    #             if Workers.objects.select_related('secincharge_id','secincharge_id__staff_id','secincharge_id__staff_id__user','secincharge_id__staff_id__department').filter(secincharge_id=a).count() == 0:
    #                 flag = 'no_worker'
    #             else:
    #                 workertemp = Workers.objects.select_related('secincharge_id','secincharge_id__staff_id','secincharge_id__staff_id__user','secincharge_id__staff_id__department').filter(secincharge_id=a)
    #                 j = 1
    #                 for i in workertemp:
    #                     worker.append(i)

    #         except SectionIncharge.DoesNotExist:
    #             flag = 'no_worker'

    #     except StudentComplain.DoesNotExist:
    #         return HttpResponse("<H1>Not a valid complaint </H1>")
    #     return render(request, "complaintModule/reassignworker.html",
    #                   {'detail': detail, 'worker': worker, 'flag':
    #                       flag, 'total_secincharge': total_secincharge,'a':a, 'wid':wid, 'total_secincharges_in_area':total_secincharges_in_area})



# @login_required
# def complaint_reassign_super(request,caretaker_id,iid):
    # current_user = get_object_or_404(User, username=request.user.username)
    # y = ExtraInfo.objects.all().select_related('user','department').filter(user=current_user).first()
    # sup = Supervisor.objects.select_related('sup_id','sup_id__user','sup_id__department').get(sup_id = y)
    # this_area = sup.area
    # if request.method == 'POST':
    #     a = get_object_or_404(User, username=request.user.username)
    #     y = ExtraInfo.objects.all().select_related('user','department').filter(user=a).first()
    #     comp_id = y.id


#for SectionIncharge
@login_required
def assign_worker(request, comp_id1):
    current_user = get_object_or_404(User, username=request.user.username)
    y = ExtraInfo.objects.all().select_related('user','department').filter(user=current_user).first()
    """
    The function is used to assign workers to complaints.
    @param:
            request - trivial.
            comp_idl - id of the complaint which the user intends to support/unsupport.

    @variables:
            type - takes the value either assign or redirect.
            a - To handle error.
            y - Foreign key .
            context - Holds data needed to make necessary changes in the template.
    """
    if request.method == 'POST':
        type = request.POST.get('submit', '')
        a = get_object_or_404(User, username=request.user.username)
        y = ExtraInfo.objects.all().select_related('user','department').filter(user=a).first()
        comp_id = y.id
       
        
        complaint_details = StudentComplain.objects.all().filter(id=comp_id1)
        
        
        
        complaint_type=complaint_details[0].complaint_type
        
        supervisor=Supervisor.objects.all().filter(type=complaint_type)
        if not supervisor.exists():
            return HttpResponse("<H1>Supervisor does not exist of this complaint type </H1>")
       
        supervisor_details=ExtraInfo.objects.all().filter(id=supervisor[0].sup_id.id)
        
        StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').filter(id=comp_id1).\
        update(status=1)
        
        sup = HoldsDesignation.objects.select_related('user','working','designation').filter(user = supervisor_details[0].user_id)
        
       
        files=File.objects.all().filter(src_object_id=comp_id1)
       
        supervisor_username=User.objects.all().filter(id=supervisor_details[0].user_id)
        file=forward_file(file_id= files.first().id,
        receiver=supervisor_username[0].username,
        receiver_designation=sup[0].designation, 
        file_extra_JSON= {}, 
        remarks = "",
        file_attachment= None)
        print(file)


        return HttpResponseRedirect('/complaint/caretaker/')
    else:
        y = ExtraInfo.objects.all().select_related('user','department').get(id=y.id)
        # a = SectionIncharge.objects.select_related('staff_id','staff_id__user','staff_id__department').get(staff_id=y)
       
        comp_id = y.id
        try:
            detail = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department').filter(id=comp_id1).first()
            # total_caretaker = Caretaker.objects.select_related('staff_id','staff_id__user','staff_id__department').all()
            # total_caretakers_in_area = Supervisor.objects.select_related('sup_id')
            # supervisors_in_area=  HoldsDesignation.objects.select_related('user','working','designation').get(total_caretakers_in_area = dsgn)
            # workertemp = []
            # worker = []
            # flag = ''
            # temp = detail.location
            # try:
                # if Workers.objects.select_related('secincharge_id','secincharge_id__staff_id','secincharge_id__staff_id__user','secincharge_id__staff_id__department').filter(secincharge_id=a).count() == 0:
                #     flag = 'no_worker'
                # else:
                #     workertemp1 = Workers.objects.select_related('secincharge_id','secincharge_id__staff_id','secincharge_id__staff_id__user','secincharge_id__staff_id__department').filter(secincharge_id=a)
                #     workertemp = workertemp1.filter(worker_type=detail.complaint_type)
                #     j = 1
                #     for i in workertemp:
                #         worker.append(i)
                      
            # except SectionIncharge.DoesNotExist:
            #     flag = 'no_worker'

        except StudentComplain.DoesNotExist:
            return HttpResponse("<H1>Not a valid complaint </H1>")
        return render(request, "complaintModule/assignworker.html",
                      {'detail': detail})
                        

#for SectionIncharge
@login_required
def discharge_worker(request,wid,cid):
    current_user = get_object_or_404(User, username=request.user.username)
    y = ExtraInfo.objects.all().select_related('user','department').filter(user=current_user).first()

    this_worker = Workers.objects.select_related('secincharge_id','secincharge_id__staff_id','secincharge_id__staff_id__user','secincharge_id__staff_id__department').get(id=wid)
    com_in_concern= StudentComplain.objects.select_related('complainer','complainer__user','complainer__department').get(id=cid);
    com_in_concern.worker_id=None;
    com_in_concern.status=0;
    StudentComplain.objects.select_for_update().filter(id=cid).\
                update(worker_id=None, status=0)
    url='/complaint/secincharge/detail2/'+cid;
    return HttpResponseRedirect(url)



@login_required
def caretaker_feedback(request):
    """
    This function deals with submission of complaints for a particular type of caretaker 

    """
    a = get_object_or_404(User, username=request.user.username)
    if request.method == 'POST':
        
        feedback = request.POST.get('feedback', '')
        rating = request.POST.get('rating', '')
        caretaker_type = request.POST.get('caretakertype','')
        all_caretaker = Caretaker.objects.select_related('staff_id','staff_id__user','staff_id__department').filter(area=caretaker_type).order_by('-id')
        newrate=0
        for x in all_caretaker:
            rate=x.rating
            if(rate==0):
                newrate=int(rating)
            else:
                a1=int(rate)
                b1=int(rating)
                c1=(a1+b1)/2
                newrate=c1
            Caretaker.objects.select_related('staff_id','staff_id__user','staff_id__department').filter(area=caretaker_type).\
                update(myfeedback=feedback, rating=newrate)
        return HttpResponseRedirect('/complaint/user/')    
    else:
        
        return render(request, "complaintModule/submit_feedback_caretaker.html", {'a': a})


#for SectionIncharge
@login_required
def worker_id_know_more(request, work_id):
    """
    function to know pending complaints assigned to the worker
    """
    this_worker = Workers.objects.select_related('secincharge_id','secincharge_id__staff_id','secincharge_id__staff_id__user','secincharge_id__staff_id__department').get(id=work_id)
    num = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department').filter(worker_id=this_worker).count();
    complaints_list = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department').filter(worker_id=this_worker);
    complaints_list_onhold = []
    for i in complaints_list:
        if i.status == 1:
            complaints_list_onhold.append(i)
    numpend = len(complaints_list_onhold)
    work_under_secincharge1 = this_worker.secincharge_id.staff_id.user.first_name
    work_under_secincharge2 = this_worker.secincharge_id.staff_id.user.last_name
    return render(request, "complaintModule/worker_id_know_more.html",{'this_worker':this_worker,'work_under_secincharge1':work_under_secincharge1,'work_under_secincharge2':work_under_secincharge2, 'num':num, 'complaints_list':complaints_list, 'complaints_list_onhold':complaints_list_onhold, 'numpend':numpend})



@login_required
def check(request):
    """
    The function is used to check the type of user .
    There are three types of users student,staff or faculty.
    @param:
            request - trivial.


    @variables:
            issue - The issue object.
            supported - True if the user's intention is to support the issue.
            support_count - Total supporters of the above issue.
            context - Holds data needed to make necessary changes in the template.
    """
    if request.user.is_authenticated:
        a = get_object_or_404(User, username=request.user.username)
        b = ExtraInfo.objects.all().select_related('user','department').filter(user=a).first()
        temp = ExtraInfo.objects.all().select_related('user','department').filter(user_type='faculty')
        print('----------------------------')
        print(len(temp))
        temp = ExtraInfo.objects.all().select_related('user','department').filter(user_type='fx')
        print('----------------------------')
        print(len(temp))
        print('----------------------------')
        print(b.user_type)
        print('----------------------------')
        print('----------------------------')
        print('----------------------------')
        supervisor_list=Supervisor.objects.all()
        caretaker_list=Caretaker.objects.all()
        is_supervisor=False
        is_caretaker=False
        for i in supervisor_list:
            if b.id==i.sup_id_id:
                is_supervisor=True
                break
        for i in caretaker_list:
            if b.id==i.staff_id_id:
                is_caretaker=True
                break
        if is_supervisor:
           return HttpResponseRedirect('/complaint/supervisor/')
        elif is_caretaker:
           return HttpResponseRedirect('/complaint/caretaker/')

        elif b.user_type == 'student':
            return HttpResponseRedirect('/complaint/user/')
        # elif b.user_type == 'fx':
        #    return HttpResponseRedirect('/complaint/supervisor/')
        elif b.user_type == 'staff':
            return HttpResponseRedirect('/complaint/user/')
        elif b.user_type == 'faculty':
            return HttpResponseRedirect('/complaint/user/')
        else:
            return HttpResponse("<h1>wrong user credentials</h1>")
    else:
        return HttpResponseRedirect('/')


@login_required

def user(request):
    """
    The function is used to register a complaint
    @param:
            request - trivial.


    @variables:
            issue - The issue object.
            supported - True if the user's intention is to support the issue.
            support_count - Total supporters of the above issue.
            context - Holds data needed to make necessary changes in the template.
    """
    a = get_object_or_404(User, username=request.user.username)
    y = ExtraInfo.objects.all().select_related('user','department').filter(user=a).first()
    num = 1
    comp_id = y.id
    if request.method == 'POST':
        comp_type = request.POST.get('complaint_type', '')
        location = request.POST.get('Location', '')
        specific_location = request.POST.get('specific_location', '')
        comp_file = request.FILES.get('myfile')
           
        details = request.POST.get('details', '')
        status = 0
        # finish time is according to complaint type
        complaint_finish = datetime.now() + timedelta(days=2)
        if comp_type == 'Electricity':
            complaint_finish = datetime.now() + timedelta(days=2)
        elif comp_type == 'carpenter':
            complaint_finish = datetime.now() + timedelta(days=2)
        elif comp_type == 'plumber':
            complaint_finish = datetime.now() + timedelta(days=2)
        elif comp_type == 'garbage':
            complaint_finish = datetime.now() + timedelta(days=1)
        elif comp_type == 'dustbin':
            complaint_finish = datetime.now() + timedelta(days=1)
        elif comp_type == 'internet':
            complaint_finish = datetime.now() + timedelta(days=4)
        elif comp_type == 'other':
            complaint_finish = datetime.now() + timedelta(days=3)
        
        if location!="":
           
            user_details=User.objects.get(id=y.user_id)

            obj1, created = StudentComplain.objects.get_or_create(complainer=y,
                                complaint_type=comp_type,
                                location=location,
                                specific_location=specific_location,
                                details=details,
                                status=status,
                                complaint_finish=complaint_finish,
                                upload_complaint=comp_file)


        
        
       
       
        if location == "hall-1":
          dsgn ="hall1caretaker"
        elif location =="hall-3":
          dsgn ="hall3caretaker"
        elif location =="hall-4":
          dsgn ="hall4caretaker"
        elif location =="CC1":
          dsgn ="cc1convener"
        elif location =="CC2":
          dsgn ="CC2 convener"
        elif location == "core_lab":
          dsgn = "corelabcaretaker"
        elif location =="LHTC":
          dsgn ="lhtccaretaker"
        elif location =="NR2":
          dsgn ="nr2caretaker"
        elif location =="Maa Saraswati Hostel":
          dsgn ="mshcaretaker"
        elif location =="Nagarjun Hostel":
          dsgn ="nhcaretaker"
        elif location =="Panini Hostel":
          dsgn ="phcaretaker"
        else:
          dsgn = "rewacaretaker"
        caretaker_name = HoldsDesignation.objects.select_related('user','working','designation').get(designation__name = dsgn)
    
        c1=HoldsDesignation.objects.filter(user_id=y.user_id).all()
        print(c1[0].designation)
        file_id = create_file(uploader=user_details.username, 
        uploader_designation=c1[0].designation, 
        receiver=caretaker_name.user.username,
        receiver_designation=caretaker_name.designation, 
        src_module="complaint", 
        src_object_id= str(obj1.id), 
        file_extra_JSON= {}, 
        attached_file = None)
            
        # print("  wertyuioiuhygfdsdfghjk")
        print(file_id)

        # This is to allow the student
        student = 0
        message = "A New Complaint has been lodged"
        complaint_system_notif(request.user, caretaker_name.user,'lodge_comp_alert',obj1.id,student,message)
        # complaint_system_notif(request.user, secincharge_name.staff_id.user,'lodge_comp_alert',obj1.id,1,message)

        messages.success(request,message)

        

        return HttpResponseRedirect('/complaint/user')

    else:
        a = get_object_or_404(User, username=request.user.username)
        y = ExtraInfo.objects.all().select_related('user','department').filter(user=a).first()
        
        user_details=User.objects.get(id=y.user_id)


        notification = Notification.objects.filter(recipient=a.id)
        notification = notification.filter(data__exact={'url':'complaint:detail','module':'Complaint System'})
        # notification_message = []
        # for notification in x:
        #     to = User.objects.get(id=notification.actor_object_id).username
        #     from django.utils.timesince import timesince as timesince_
        #     duration = timesince_(notification.timestamp,None)
        #     notification_message.append(notification.verb+' by '+ to + ' ' + duration + ' ago ')
        

        c1=HoldsDesignation.objects.filter(user_id=y.user_id).all()
        print(c1[0].designation)
        # c2=Designation.objects.filter(i)

       
         
        
        outbox_files = view_outbox(
            username=user_details.username,
            designation=c1[0].designation,
            src_module="complaint"
        )
        print(outbox_files)

        outbox=[]
        comp_list=set()
        for i in outbox_files:
            
            outbox.append(i)
        print(outbox)
        for i in outbox:
            file_history = view_history(file_id=i['id'])
            print(i['id'])
            comp=File.objects.filter(id=i['id'])
            print(comp[0].src_object_id)
            complaint=StudentComplain.objects.all().filter(id=comp[0].src_object_id)
            print(complaint)
            if complaint[0].complainer.user.username == user_details.username :
                comp_list.add(complaint)
            # file_history = view_history(file_id=i['id'])

            # comp=File.objects.filter(uploader=file_history[0]['current_id'])
            # for j in comp:
            #     c=StudentComplain.objects.all().filter(id=j.src_object_id)
            #     comp_list.add(c)
            #     print(c[0])
                
            # break    
        complaint_final_list=[]
        for i in comp_list:
            complaint_final_list.append(i[0])
        
        sorted_history = sorted(complaint_final_list, key=attrgetter('complaint_date'), reverse=True)
        print(complaint_final_list)
        return render(request, "complaintModule/complaint_user.html",
                      {'outbox': sorted_history,'notification':notification, 'comp_id': y.id, 'history':outbox})


@login_required
def save_comp(request):
    """
    The function is used to save the complaint entered by the user
    @param:
            request - trivial.


    @variables:
            issue - The issue object.
            supported - True if the user's intention is to support the issue.
            support_count - Total supporters of the above issue.
            context - Holds data needed to make necessary changes in the template.
    """
    if request.method == 'POST':
        comp_id = request.POST.get('comp_id', '')
        comp_type = request.POST.get('complaint_type', '')
        location = request.POST.get('Location', '')
        specific_location = request.POST.get('specific_location', '')
        comp_file = request.FILES.get('myfile')
        details = request.POST.get('details', '')
        complaint_finish = datetime.now() + timedelta(days=2)
        if comp_type == 'Electricity':
            complaint_finish = datetime.now() + timedelta(days=2)
        elif comp_type == 'carpenter':
            complaint_finish = datetime.now() + timedelta(days=2)
        elif comp_type == 'plumber':
            complaint_finish = datetime.now() + timedelta(days=2)
        elif comp_type == 'garbage':
            complaint_finish = datetime.now() + timedelta(days=1)
        elif comp_type == 'dustbin':
            complaint_finish = datetime.now() + timedelta(days=1)
        elif comp_type == 'internet':
            complaint_finish = datetime.now() + timedelta(days=4)
        elif comp_type == 'other':
            complaint_finish = datetime.now() + timedelta(days=3)

        y = ExtraInfo.objects.all().select_related('user','department').get(id=comp_id)
        x = StudentComplain(complainer=y,
                            complaint_type=comp_type,
                            location=location,
                            specific_location=specific_location,
                            details=details,
                            complaint_finish=complaint_finish,
                            upload_complaint =comp_file)

        x.save()
       
        return HttpResponseRedirect('/complaint/user/')



@login_required
def caretaker(request):
    """
    The function is used to display details to the caretaker such as registered complaints 
    @param:
            request - trivial.


    @variables:
            issue - The issue object.
            supported - True if the user's intention is to support the issue.
            support_count - Total supporters of the above issue.
            context - Holds data needed to make necessary changes in the template.
    """
    current_user = get_object_or_404(User, username=request.user.username)
    y = ExtraInfo.objects.all().select_related('user','department').filter(user=current_user).first()
    
    if request.method == 'POST':
        # type = request.POST.get('submit', '')
        # worker_type = request.POST.get('complaint_type', '')
        # name = request.POST.get('name', '')
        # phone = request.POST.get('phone_no', '')
        # age = request.POST.get('age', '')
        # try:
        #     y = ExtraInfo.objects.all().select_related('user','department').get(id=y.id)
        #     a = Caretaker.objects.select_related('staff_id','staff_id__user','staff_id__department').get(staff_id=y)
        # except Exception as e:
        #     a = None
        #     y = None
        # intage = int(age)
        # intphone = int(phone)
        # if len(phone) == 10 and intage > 20 and intage < 50 and intphone > 1999999999:
        #     x = Workers(caretaker_id=a,
        #                 name=name,
        #                 age=age,
        #                 phone=phone,
        #                 worker_type=worker_type)
        #     if not Workers.objects.filter(caretaker_id=a,name=name, age=age,phone=phone,worker_type=worker_type).exists():
        #         x.save()

        # if len(phone) == 10 and intage > 20 and intage < 50 and intphone > 1999999999:
        #     obj, created = Workers.objects.get_or_create(caretaker_id=a,
        #                 name=name,
        #                 age=age,
        #                 phone=phone,
        #                 worker_type=worker_type)
        
        # b = a.area
        # historytemp = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').filter(location=b).order_by('-id')
        # history = []
        # j = 1
        # k = 1
        # for i in historytemp:
        #     history.append(i)
        #     # if j%2 == 1:
        #     #     history.append(i)
        #     # j = j+1

        # for h in history:
        #     h.serial_no = k
        #     k=k+1
        user_details=User.objects.get(id=y.user_id)
        # if user_details.username=="shyams":
        #     desgn="hall3caretaker"
        # if user_details.username=="hall4caretaker":
        #     desgn="hall4caretaker"

        # total_worker = []
            

        # total_workertemp = Workers.objects.select_related('caretaker_id','caretaker_id__staff_id','caretaker_id__staff_id__user','caretaker_id__staff_id__department').filter(caretaker_id=a)
        # j = 1
        # for i in total_workertemp:
        #     if j%2 != 0:
        #         total_worker.append(i)
        #     j = j + 1
        

        # for i in total_workertemp:
            # total_worker.append(i)

        complaint_assign_no = []
        comp_type = request.POST.get('complaint_type', '')
        location = request.POST.get('Location', '')
        specific_location = request.POST.get('specific_location', '')
        comp_file = request.FILES.get('myfile')
           
        details = request.POST.get('details', '')
        status = 0
        # finish time is according to complaint type
        complaint_finish = datetime.now() + timedelta(days=2)
        if comp_type == 'Electricity':
            complaint_finish = datetime.now() + timedelta(days=2)
        elif comp_type == 'carpenter':
            complaint_finish = datetime.now() + timedelta(days=2)
        elif comp_type == 'plumber':
            complaint_finish = datetime.now() + timedelta(days=2)
        elif comp_type == 'garbage':
            complaint_finish = datetime.now() + timedelta(days=1)
        elif comp_type == 'dustbin':
            complaint_finish = datetime.now() + timedelta(days=1)
        elif comp_type == 'internet':
            complaint_finish = datetime.now() + timedelta(days=4)
        elif comp_type == 'other':
            complaint_finish = datetime.now() + timedelta(days=3)
        # y = ExtraInfo.objects.all().select_related('user','department').get(id=comp_id)
        #check if location given
        if location!="":
            user_details=User.objects.get(id=y.user_id)
            obj1, created = StudentComplain.objects.get_or_create(complainer=y,
                                complaint_type=comp_type,
                                location=location,
                                specific_location=specific_location,
                                details=details,
                                status=status,
                                complaint_finish=complaint_finish,
                                upload_complaint=comp_file)
         
        
        if location == "hall-1":
          dsgn ="hall1caretaker"
        elif location =="hall-3":
          dsgn ="hall3caretaker"
        elif location =="hall-4":
          dsgn ="hall4caretaker"
        elif location =="CC1":
          dsgn ="cc1convener"
        elif location =="CC2":
          dsgn ="CC2 convener"
        elif location == "core_lab":
          dsgn = "corelabcaretaker"
        elif location =="LHTC":
          dsgn ="lhtccaretaker"
        elif location =="NR2":
          dsgn ="nr2caretaker"
        elif location =="Maa Saraswati Hostel":
          dsgn ="mshcaretaker"
        elif location =="Nagarjun Hostel":
          dsgn ="nhcaretaker"
        elif location =="Panini Hostel":
          dsgn ="phcaretaker"
        else:
          dsgn = "rewacaretaker"
        caretaker_name = HoldsDesignation.objects.select_related('user','working','designation').get(designation__name = dsgn)
        print(caretaker_name.user.username)
        print(user_details.username)
        print(caretaker_name.designation)
        
        user_details=User.objects.get(id=y.user_id)
        des=HoldsDesignation.objects.filter(user=user_details).all()
        file_id = create_file(uploader=user_details.username, 
        uploader_designation=des[0].designation, 
        receiver=caretaker_name.user.username,
        receiver_designation=dsgn, 
        src_module="complaint", 
        src_object_id= str(obj1.id), 
        file_extra_JSON= {}, 
        attached_file = None)  


        # This is to allow the student
        student = 1
        message = "A New Complaint has been lodged"
        complaint_system_notif(request.user, caretaker_name.user,'lodge_comp_alert',obj1.id,student,message)

        # return render(request, "complaintModule/complaint_user.html",
        #               {'history': history, 'comp_id': comp_id })
        # next = request.POST.get('next', '/')

        messages.success(request,message)
        # return HttpResponseRedirect('/complaint/user')


        # for x in total_worker:
        #     worker = Workers.objects.select_related('caretaker_id','caretaker_id__staff_id','caretaker_id__staff_id__user','caretaker_id__staff_id__department').get(id=x.id)
        #     temp = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').filter(worker_id=worker).count()
        #     worker.total_complaint = temp
        #     complaint_assign_no.append(worker)

        notification = Notification.objects.filter(recipient=current_user.id)
        notification = notification.filter(data__exact={'url':'complaint:detail2','module':'Complaint System'})
        
        return HttpResponseRedirect('/complaint/caretaker')
        


    else:
        # y = ExtraInfo.objects.all().select_related('user','department').get(id=y.id)  

        a = Caretaker.objects.select_related('staff_id','staff_id__user','staff_id__department').get(staff_id=y.id)
        b = a.area
        history = []
        
        
        complaint_assign_no = []
        user_details=User.objects.get(id=y.user_id)
        
        notification = Notification.objects.filter(recipient=current_user.id)
        notification = notification.filter(data__exact={'url':'complaint:detail2','module':'Complaint System'})
        user_details=User.objects.get(id=y.user_id)
       
        
        des=HoldsDesignation.objects.filter(user=user_details).all()
        print("######")
        print(user_details.username)
        print(des[0].designation)
        print("&&&&&")
        outbox_files = view_outbox(
            username=user_details.username,
            designation=des[0].designation,
            src_module="complaint"
        )

        outbox=[]
        comp_list=set()
        for i in outbox_files:
            # print(i)
            outbox.append(i)
        
        for i in outbox:
            file_history = view_history(file_id=i['id'])
            print(i['id'])
            print("********")
            comp=File.objects.filter(id=i['id'])
            print(comp[0].src_object_id)
            print("------")
            complaint=StudentComplain.objects.all().filter(id=comp[0].src_object_id)
            print(complaint[0].complainer.user.username)

            print("......")
            if complaint[0].complainer.user.username== user_details.username :
                comp_list.add(complaint)
            
            # break    
        complaint_final_list=[]
        for i in comp_list:
            complaint_final_list.append(i[0])
        
        sorted_history_out = sorted(complaint_final_list, key=attrgetter('complaint_date'), reverse=True)

        inbox_files = view_inbox(
            username=user_details.username,
            designation=des[0].designation,
            src_module="complaint"
        )
        print(inbox_files)

        inbox=[]
        comp_list_in=set()
        for i in inbox_files:
            # print(i)
            inbox.append(i)
        file_history_list=[]
        for i in inbox:
            file_history = view_history(file_id=i['id'])
            print(i['id'])
            comp=File.objects.filter(id=i['id'])
            print(comp[0].src_object_id)
            complaint=StudentComplain.objects.all().filter(id=comp[0].src_object_id)
            print(complaint)
            comp_list_in.add(complaint)
           
        complaint_final_list_in=[]
        for i in comp_list_in:
            complaint_final_list_in.append(i[0])

        # print(complaint_final_list_in)
        sorted_history = sorted(complaint_final_list_in, key=attrgetter('complaint_date'), reverse=True)

        return render(request, "complaintModule/complaint_caretaker.html",
                      { 'history': sorted_history, 
                       'comp_id': y.id, 
                       'carehistory':sorted_history_out,
                        'notification':notification, 
                        'care_id': a})

@login_required
def remove_worker_from_complaint(request,complaint_id):
    """
    The function is used by secincharge to remove a worker
    already assigned to a complaint
    @param:
       request - trivial
       complaint_id - used to get complaint_id registered
    """
    complaint = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department').filter(complaint_id=complaint_id).update(worker_id='')
    return HttpResponseRedirect('/complaint/caretaker/')




@login_required
def changestatus(request, complaint_id, status):
    """
    The function is used by caretaker to change the status of a complaint.
    @param:
            request - trivial.
            complaint_id - used to get complaint_id registered.
            status-used to get the current status of complaints

    @variables:
            issue - The issue object.
            supported - True if the user's intention is to support the issue.
            support_count - Total supporters of the above issue.
            context - Holds data needed to make necessary changes in the template.
    """
    if status == '3':
        StudentComplain.objects.select_related('complainer','complainer__user','complainer__department').filter(id=complaint_id).\
            update(status=status, worker_id='')
        return HttpResponseRedirect('/complaint/caretaker/')
    elif status == '2':
        StudentComplain.objects.select_related('complainer','complainer__user','complainer__department').filter(id=complaint_id).\
            update(status=status, worker_id='')
        return HttpResponseRedirect('/complaint/caretaker/')
    else:
        StudentComplain.objects.select_related('complainer','complainer__user','complainer__department').filter(id=complaint_id).\
            update(status=status)
        return HttpResponseRedirect('/complaint/caretaker/')




@login_required
def changestatussuper(request, complaint_id, status):
    """
    The function is used by caretaker to change the status of a complaint.
    @param:
            request - trivial.
            complaint_id - used to get complaint_id registered.
            status-used to get the current status of complaints

    @variables:
            issue - The issue object.
            supported - True if the user's intention is to support the issue.
            support_count - Total supporters of the above issue.
            context - Holds data needed to make necessary changes in the template.
    """
    if status == '3':
        StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').filter(id=complaint_id).\
            update(status=status, worker_id='')
        return HttpResponseRedirect('/complaint/supervisor/')
    elif status == '2':
        StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').filter(id=complaint_id).\
            update(status=status, worker_id='')
        return HttpResponseRedirect('/complaint/supervisor/')
    else:
        StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').filter(id=complaint_id).\
            update(status=status)
        return HttpResponseRedirect('/complaint/supervisor/')


@login_required
def removew(request, work_id):
    """
    The function is used by secincharge to remove workers.
    @param:
            request - trivial.
            work_id - id of the issue object which the user intends to support/unsupport.

    @variables:
            issue - The issue object.
            supported - True if the user's intention is to support the issue.
            support_count - Total supporters of the above issue.
            context - Holds data needed to make necessary changes in the template.
    """
    worker = Workers.objects.select_related('secincharge_id','secincharge_id__staff_id','secincharge_id__staff_id__user','secincharge_id__staff_id__department').get(id=work_id)
    temp = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department').filter(worker_id=worker).count()
    if temp == 0:
        worker.delete()
        return HttpResponseRedirect('/complaint/secincharge/')
    else:
        return HttpResponse('<H1> Worker is assign some complaint</h1>')





@login_required
def submitfeedback(request, complaint_id):
    """
    The function is used by the complainant to enter feedback after the complaint has been resolved
    @param:
            request - trivial.
            complaint_id - id of the registerd complaint.

    @variables:
            issue - The issue object.
            supported - True if the user's intention is to support the issue.
            support_count - Total supporters of the above issue.
            context - Holds data needed to make necessary changes in the template.
    """

    if request.method == 'POST':
        feedback = request.POST.get('feedback', '')
        rating = request.POST.get('rating', '')
        StudentComplain.objects.select_related('complainer','complainer__user','complainer__department').filter(id=complaint_id).\
        update(feedback=feedback, flag=rating)
        a = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department').filter(id=complaint_id).first()
        care = Caretaker.objects.select_related('staff_id','staff_id__user','staff_id__department').filter(area=a.location).first()
        rate = care.rating
        newrate = 0
        if rate == 0:
            newrate = rating
        else:
            a1 = int(rating)
            b1 = int(rate)
            c1 = int((a1+b1)/2)
            newrate = c1

        Caretaker.objects.select_related('staff_id','staff_id__user','staff_id__department').filter(area=a.location).update(rating=newrate)
        return HttpResponseRedirect('/complaint/user/')
        
    else:
        a = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department').get(id=complaint_id)
        return render(request, "complaintModule/submit_feedback.html", {'a': a})




#for SectionIncharge
@login_required
def deletecomplaint(request, comp_id1):
    """
    function to delete complaint
    """
    StudentComplain.objects.get(id=comp_id1).delete()
    return HttpResponseRedirect('/complaint/secincharge/')



def testEntry():
    list1 = [('eecivil','NR2'),('eecivil','Rewa_Residency'),('eecivil','LHTC'),('eecivil','core_lab')]

    # to delete supervisors
    # all_ent = Supervisor.objects.all()
    # for ent in all_ent:
    #     ent.delete()
    
    # adding all supervisors
    for n in list1:
        user = User.objects.all().get(username=n[0])
        ei_obj = ExtraInfo.objects.all().get(user =user)
        print(ei_obj.user.username)
        test =  Supervisor(sup_id=ei_obj, area = n[1])
        test.save()

@login_required 
def supervisor(request):
    """
    The function is used to display all registered complaints to the supervisor
    @param:
            request - trivial.


    @variables:
            issue - The issue object.
            supported - True if the user's intention is to support the issue.
            support_count - Total supporters of the above issue.
            context - Holds data needed to make necessary changes in the template.
    """
    # print("--------------------------")
    # testEntry()
    # print(request.type)
    location = request.POST.get('Location', '')
    current_user = get_object_or_404(User, username=request.user.username)
    y = ExtraInfo.objects.all().select_related('user','department').filter(user=current_user).first()
    comp_id = y.id
    if request.method == 'POST' :
        try:
            y = ExtraInfo.objects.all().select_related('user','department').get(id=y.id)
            a = Supervisor.objects.select_related('sup_id','sup_id__user','sup_id__department').get(sup_id=y)
        except Exception as e:
            a = None
            y = None
        all_caretaker = Caretaker.objects.select_related('staff_id','staff_id__user','staff_id__department').filter(area=location).order_by('-id')
        area = all_caretaker[0].area
        # ExtraInfo.objects.get(id=sup_id)
        all_complaint = []
        numtemp = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department').filter(location =  area).filter(status = 0).count()
        num = int(numtemp/2+0.5)
        
        
        
    
        

        comp_type = request.POST.get('complaint_type', '')
        location = request.POST.get('Location', '')
        specific_location = request.POST.get('specific_location', '')
        comp_file = request.FILES.get('myfile')
           
        details = request.POST.get('details', '')
        status = 0
        # finish time is according to complaint type
        complaint_finish = datetime.now() + timedelta(days=2)
        if comp_type == 'Electricity':
            complaint_finish = datetime.now() + timedelta(days=2)
        elif comp_type == 'carpenter':
            complaint_finish = datetime.now() + timedelta(days=2)
        elif comp_type == 'plumber':
            complaint_finish = datetime.now() + timedelta(days=2)
        elif comp_type == 'garbage':
            complaint_finish = datetime.now() + timedelta(days=1)
        elif comp_type == 'dustbin':
            complaint_finish = datetime.now() + timedelta(days=1)
        elif comp_type == 'internet':
            complaint_finish = datetime.now() + timedelta(days=4)
        elif comp_type == 'other':
            complaint_finish = datetime.now() + timedelta(days=3)
        y = ExtraInfo.objects.all().select_related('user','department').get(id=comp_id)
        #check if location given
        if location!="":
            # x = StudentComplain(complainer=y,
            #                     complaint_type=comp_type,
            #                     location=location,
            #                     specific_location=specific_location,
            #                     details=details,
            #                     status=status,
            #                     complaint_finish=complaint_finish,
            #                     upload_complaint=comp_file)
            
            
            # x.save()
            obj1, created = StudentComplain.objects.get_or_create(complainer=y,
                                complaint_type=comp_type,
                                location=location,
                                specific_location=specific_location,
                                details=details,
                                status=status,
                                complaint_finish=complaint_finish,
                                upload_complaint=comp_file)

            
        
        if location == "hall-1":
          dsgn ="hall1caretaker"
        elif location =="hall-3":
          dsgn ="hall3caretaker"
        elif location =="hall-4":
          dsgn ="hall4caretaker"
        elif location =="CC1":
          dsgn ="cc1convener"
        elif location =="CC2":
          dsgn ="CC2 convener"
        elif location == "core_lab":
          dsgn = "corelabcaretaker"
        elif location =="LHTC":
          dsgn ="lhtccaretaker"
        elif location =="NR2":
          dsgn ="nr2caretaker"
        elif location =="Maa Saraswati Hostel":
          dsgn ="mshcaretaker"
        elif location =="Nagarjun Hostel":
          dsgn ="nhcaretaker"
        elif location =="Panini Hostel":
          dsgn ="phcaretaker"
        else:
          dsgn = "rewacaretaker"
        caretaker_name = HoldsDesignation.objects.select_related('user','working','designation').get(designation__name = dsgn)
        user_details=User.objects.get(id=y.user_id)
        # c2=Supervisor.objects.all().filter(area=location)
        print(caretaker_name.user.username)
        print(user_details.username)
        print(caretaker_name.designation)

        # sup = HoldsDesignation.objects.select_related('user','working','designation').get(user = y.id)
        # print(sup.designation)

        user_details=User.objects.get(id=y.user_id)
        des=HoldsDesignation.objects.filter(user=user_details).all()
        

        file_id = create_file(uploader=user_details.username, 
        uploader_designation=des[0].designation, 
        receiver=caretaker_name.user.username,
        receiver_designation=str(caretaker_name.designation), 
        src_module="complaint", 
        src_object_id= str(obj1.id), 
        file_extra_JSON= {}, 
        attached_file = None)  


        # This is to allow the student
        student = 1
        message = "A New Complaint has been lodged"
        complaint_system_notif(request.user, caretaker_name.user,'lodge_comp_alert',obj1.id,student,message)

        # return render(request, "complaintModule/complaint_user.html",
        #               {'history': history, 'comp_id': comp_id })
        # next = request.POST.get('next', '/')

        messages.success(request,message)
        # return HttpResponseRedirect('/complaint/user')
        
        return HttpResponseRedirect('/complaint/supervisor')

    else:
        
       
        all_caretaker = Caretaker.objects.select_related('staff_id','staff_id__user','staff_id__department').order_by('-id')
        area = all_caretaker[0].area
        
        numtemp = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').filter(location =  area).filter(status = 0).count()
        num = int(numtemp/2+0.5)
        all_complaint = []
        user_details=User.objects.get(id=y.user_id)
        

        

        
        current_user = get_object_or_404(User, username=request.user.username)
        y = ExtraInfo.objects.all().select_related('user','department').filter(user=current_user).first()
        user_details=User.objects.get(id=y.user_id)
        des=HoldsDesignation.objects.filter(user=user_details).all()
        # print(y.user_id)
        # print(user_details.username)
        # print(des[0].user)
        outbox_files = view_outbox(
            username=user_details.username,
            designation=des[0].designation,
            src_module="complaint"
        )

        outbox=[]
        comp_list=set()
        for i in outbox_files:
            # print(i)
            outbox.append(i)

        for i in outbox:
            file_history = view_history(file_id=i['id'])
            print(i['id'])
            comp=File.objects.filter(id=i['id'])
            print(comp[0].src_object_id)
            complaint=StudentComplain.objects.all().filter(id=comp[0].src_object_id)
            print(complaint)
            comp_list.add(complaint)
            # file_history = view_history(file_id=i['id'])

            # comp=File.objects.filter(uploader=file_history[0]['current_id'])
            # for j in comp:
            #     c=StudentComplain.objects.all().filter(id=j.src_object_id)
            #     comp_list.add(c)
                # print(c[0])
                
            # break    
        complaint_final_list=[]
        for i in comp_list:
            complaint_final_list.append(i[0])
        sorted_history_out = sorted(complaint_final_list, key=attrgetter('complaint_date'), reverse=True)

        inbox_files = view_inbox(
            username=user_details.username,
            designation=des[0].designation,
            src_module="complaint"
        )
        inbox=[]
        comp_list_in=set()
        for i in inbox_files:
            inbox.append(i)
        # print(inbox[0]['id'])

        for i in inbox:
            file_history = view_history(file_id=i['id'])
            print(i['id'])
            comp=File.objects.filter(id=i['id'])
            print(comp[0].src_object_id)
            complaint=StudentComplain.objects.all().filter(id=comp[0].src_object_id)
            print(complaint)
            comp_list_in.add(complaint)
            # print(complaint[0])
            # for j in comp:
            #     c=StudentComplain.objects.all().filter(id=j.src_object_id)
            #     comp_list_in.add(c)
            #     print(c[0])
                
            # break    
        complaint_final_list_in=[]
        for i in comp_list_in:
            complaint_final_list_in.append(i[0])

        sorted_history = sorted(complaint_final_list_in, key=attrgetter('complaint_date'), reverse=True)
        print(complaint_final_list_in)
        return render(request, "complaintModule/supervisor1.html",
                      
                    {'history':sorted_history,'all_caretaker': all_caretaker, 'all_complaint': all_complaint,'outbox':sorted_history_out})

@login_required
def caretaker_id_know_more(request,caretaker_id):
    this_caretaker = Caretaker.objects.select_related('staff_id','staff_id__user','staff_id__department').get(id = caretaker_id)
    this_caretaker_area = this_caretaker.area
    list_pending_complaints = []
    list_pending_complaintstemp = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department').filter(location = this_caretaker_area).filter(status = 0)
    j = 1
    for i in list_pending_complaintstemp:
        list_pending_complaints.append(i)
        

    num = len(list_pending_complaints)
    return render(request, "complaintModule/caretaker_id_know_more.html",{'this_caretaker':this_caretaker , 'list_pending_complaints':list_pending_complaints, 'num':num})


def search_complaint(request):
    return HttpResponseRedirect('/login/')

@login_required
def resolvepending(request, cid):
    a = get_object_or_404(User, username=request.user.username)
    y = ExtraInfo.objects.all().select_related('user','department').filter(user=a).first()
    thiscomplaint = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department').get(id=cid)
    if request.method == 'POST':
        newstatus = request.POST.get('yesorno','')
        comment = request.POST.get('comment')
        intstatus = 0
        if newstatus == 'Yes':
            intstatus = 2
        else:
            intstatus = 3
        StudentComplain.objects.select_related('complainer','complainer__user','complainer__department').filter(id=cid).\
        update(status=intstatus)
        StudentComplain.objects.select_related('complainer','complainer__user','complainer__department').filter(id=cid).\
        update(comment=comment)
        complainer_details = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department').get(id=cid)
        student=0
        message = "Congrats! Your complaint has been resolved"
        complaint_system_notif(request.user, complainer_details.complainer.user ,'comp_resolved_alert',complainer_details.id,student,message)
        return HttpResponseRedirect("/complaint/caretaker/")
    else:
        # complainer_details = StudentComplain.objects.get(id=cid)
        # complaint_system_notif(request.user, complainer_details.complainer.user ,'comp_resolved_alert')
        return render(request,"complaintModule/resolve_pending.html",{"a" : a,"thiscomplaint" : thiscomplaint})
    



@login_required
def resolvependingsuper(request, cid):
    a = get_object_or_404(User, username=request.user.username)
    y = ExtraInfo.objects.all().select_related('user','department').filter(user=a).first()
    thiscomplaint = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').get(id=cid)
    if request.method == 'POST':
        newstatus = request.POST.get('yesorno','')
        comment = request.POST.get('comment')
        intstatus = 0
        if newstatus == 'Yes':
            intstatus = 2
        else:
            intstatus = 3
        StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').filter(id=cid).\
        update(status=intstatus)
        StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').filter(id=cid).\
        update(comment=comment)
        complainer_details = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').get(id=cid)
        student=0
        message = "Congrats! Your complaint has been resolved"
        complaint_system_notif(request.user, complainer_details.complainer.user ,'comp_resolved_alert',complainer_details.id,student,message)
        return HttpResponseRedirect("/complaint/supervisor/")
    else:
        # complainer_details = StudentComplain.objects.get(id=cid)
        # complaint_system_notif(request.user, complainer_details.complainer.user ,'comp_resolved_alert')
        return render(request,"complaintModule/resolve_pending.html",{"a" : a,"thiscomplaint" : thiscomplaint})
    



@login_required
def resolvependingsuper(request, cid):
    a = get_object_or_404(User, username=request.user.username)
    y = ExtraInfo.objects.all().select_related('user','department').filter(user=a).first()
    thiscomplaint = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department').get(id=cid)
    if request.method == 'POST':
        newstatus = request.POST.get('yesorno','')
        comment = request.POST.get('comment')
        intstatus = 0
        if newstatus == 'Yes':
            intstatus = 2
        else:
            intstatus = 3
        StudentComplain.objects.select_related('complainer','complainer__user','complainer__department').filter(id=cid).\
        update(status=intstatus)
        StudentComplain.objects.select_related('complainer','complainer__user','complainer__department').filter(id=cid).\
        update(comment=comment)
        complainer_details = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department').get(id=cid)
        student=0
        message = "Congrats! Your complaint has been resolved"
        complaint_system_notif(request.user, complainer_details.complainer.user ,'comp_resolved_alert',complainer_details.id,student,message)
        return HttpResponseRedirect("/complaint/supervisor/")
    else:
        # complainer_details = StudentComplain.objects.get(id=cid)
        # complaint_system_notif(request.user, complainer_details.complainer.user ,'comp_resolved_alert')
        return render(request,"complaintModule/resolve_pending.html",{"a" : a,"thiscomplaint" : thiscomplaint})




def login1(request):
    if request.method == 'POST':
        u = request.POST.get('username', '')
        p = request.POST.get('password', '')
        user = authenticate(username=u, password=p)
        if user is not None:
            if user.is_active:
                login(request, user)
                a = User.objects.get(username=u)
                b = ExtraInfo.objects.all().select_related('user','department').get(user=a)
                return HttpResponseRedirect('/complaint/')
        else:
            return HttpResponse("<h1>wrong user credentials</h1>")
    else:
        return HttpResponseRedirect('/login/')

@login_required
def feedback_super(request, feedcomp_id):
    detail3 = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department').get(id=feedcomp_id)
    a=User.objects.get(username=detail3.complainer.user.username)           
    y=ExtraInfo.objects.all().select_related('user','department').get(user=a)
    temp=StudentComplain.objects.select_related('complainer','complainer__user','complainer__department').filter(complainer=y).first()                                                                  
    comp_id=temp.id 
    loc = detail3.location
    care = Caretaker.objects.select_related('staff_id','staff_id__user','staff_id__department').filter(area=loc).first()
    return render(request, "complaintModule/feedback_super.html", {"detail3": detail3,"comp_id":comp_id,"care":care})


@login_required
def feedback_care(request, feedcomp_id):
    detail2 = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department').get(id=feedcomp_id)
    a=User.objects.get(username=detail2.complainer.user.username)           
    y=ExtraInfo.objects.all().select_related('user','department').get(user=a)
    temp=StudentComplain.objects.select_related('complainer','complainer__user','complainer__department').filter(complainer=y).first()                                                                  
    comp_id=temp.id 
    return render(request, "complaintModule/feedback_care.html", {"detail2": detail2,"comp_id":comp_id})


#for complainaint and caretaker
@login_required
def detail(request, detailcomp_id1):
    """
    function that shows detail about complaint
    """
    detail = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department').get(id=detailcomp_id1)
    if(detail.worker_id is None):
        worker_name = None
        worker_id = detail.worker_id  
    else:
        worker_id = detail.worker_id.id
        worker = Workers.objects.select_related('secincharge_id','secincharge_id__staff_id','secincharge_id__staff_id__user','secincharge_id__staff_id__department').get(id=worker_id)
        worker_name = worker.name
    a=User.objects.get(username=detail.complainer.user.username)           
    y=ExtraInfo.objects.all().select_related('user','department').get(user=a)
    num=0
    if detail.upload_complaint != "":
        num = 1
    temp=StudentComplain.objects.select_related('complainer','complainer__user','complainer__department').filter(complainer=y).first()                                                                  
    comp_id=temp.id 
    return render(request, "complaintModule/complaint_user_detail.html", {"detail": detail, "comp_id":detail.id,"num":num,"worker_name":worker_name})



#for SectionIncharge
@login_required
def detail2(request, detailcomp_id1):
    detail2 = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department').get(id=detailcomp_id1)
    if(detail2.worker_id is None):
        worker_name = None
        worker_id = detail2.worker_id  
    else:
        worker_id = detail2.worker_id.id
        worker = Workers.objects.select_related('secincharge_id','secincharge_id__staff_id','secincharge_id__staff_id__user','secincharge_id__staff_id__department').get(id=worker_id)
        worker_name = worker.name
    a=User.objects.get(username=detail2.complainer.user.username)           
    y=ExtraInfo.objects.all().select_related('user','department').get(user=a)
    num=0
    
    if detail2.upload_complaint != "":
        num = 1
    temp=StudentComplain.objects.select_related('complainer','complainer__user','complainer__department').filter(complainer=y).first()                                                               
    comp_id=temp.id 
    return render(request, "complaintModule/complaint_secincharge_detail.html", {"detail2": detail2, "comp_id":detail2.id,"num":num,"worker_name":worker_name,"wid":worker_id})


@login_required
def detail3(request, detailcomp_id1):
    detail3 = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department').get(id=detailcomp_id1)
    a=User.objects.get(username=detail3.complainer.user.username)           
    y=ExtraInfo.objects.all().select_related('user','department').get(user=a)
    num=0
    if detail3.upload_complaint != "":
        num = 1
    temp=StudentComplain.objects.select_related('complainer','complainer__user','complainer__department').filter(complainer=y).first()                                                                  
    comp_id=temp.id 
    loc = detail3.location
    care = Caretaker.objects.select_related('staff_id','staff_id__user','staff_id__department').filter(area=loc).first()
    return render(request, "complaintModule/complaint_supervisor_detail.html", {"detail3": detail3,"comp_id":comp_id,"care":care,"num":num})




@login_required

def supervisorlodge(request):
    """
    The function is used to register a complaint
    @param:
            request - trivial.


    @variables:
            issue - The issue object.
            supported - True if the user's intention is to support the issue.
            support_count - Total supporters of the above issue.
            context - Holds data needed to make necessary changes in the template.
    """
    a = get_object_or_404(User, username=request.user.username)
    y = ExtraInfo.objects.all().select_related('user','department').filter(user=a).first()
    num = 1
    comp_id = y.id
    if request.method == 'POST':
        comp_type = request.POST.get('complaint_type', '')
        location = request.POST.get('Location', '')
        specific_location = request.POST.get('specific_location', '')
        comp_file = request.FILES.get('myfile')
           
        details = request.POST.get('details', '')
        status = 0
        # finish time is according to complaint type
        complaint_finish = datetime.now() + timedelta(days=2)
        if comp_type == 'Electricity':
            complaint_finish = datetime.now() + timedelta(days=2)
        elif comp_type == 'carpenter':
            complaint_finish = datetime.now() + timedelta(days=2)
        elif comp_type == 'plumber':
            complaint_finish = datetime.now() + timedelta(days=2)
        elif comp_type == 'garbage':
            complaint_finish = datetime.now() + timedelta(days=1)
        elif comp_type == 'dustbin':
            complaint_finish = datetime.now() + timedelta(days=1)
        elif comp_type == 'internet':
            complaint_finish = datetime.now() + timedelta(days=4)
        elif comp_type == 'other':
            complaint_finish = datetime.now() + timedelta(days=3)
        y = ExtraInfo.objects.all().select_related('user','department').get(id=comp_id)
        #check if location given
        if location!="":
            # x = StudentComplain(complainer=y,
            #                     complaint_type=comp_type,
            #                     location=location,
            #                     specific_location=specific_location,
            #                     details=details,
            #                     status=status,
            #                     complaint_finish=complaint_finish,
            #                     upload_complaint=comp_file)
            
            
            # x.save()
            obj1, created = StudentComplain.objects.get_or_create(complainer=y,
                                complaint_type=comp_type,
                                location=location,
                                specific_location=specific_location,
                                details=details,
                                status=status,
                                complaint_finish=complaint_finish,
                                upload_complaint=comp_file)

            
        historytemp = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').filter(complainer=y).order_by('-id')
        history = []
        j = 1
        k = 1
        for i in historytemp:
            history.append(i)
            # if j%2 != 0:
            #     history.append(i)
            # j = j+1


        for h in history:
            h.serial_no = k
            k = k+1
        # if location == "hall1":
        #     dsgn = "hall1caretaker"
        # elif location == "hall3":
        #     dsgn = "hall3caretaker"
        # else :
        #     dsgn = "hall4caretaker"
        if location == "hall-1":
          dsgn ="hall1caretaker"
        elif location =="hall-3":
          dsgn ="hall3caretaker"
        elif location =="hall-4":
          dsgn ="hall4caretaker"
        elif location =="CC1":
          dsgn ="cc1convener"
        elif location =="CC2":
          dsgn ="CC2 convener"
        elif location == "core_lab":
          dsgn = "corelabcaretaker"
        elif location =="LHTC":
          dsgn ="lhtccaretaker"
        elif location =="NR2":
          dsgn ="nr2caretaker"
        elif location =="Maa Saraswati Hostel":
          dsgn ="mshcaretaker"
        elif location =="Nagarjun Hostel":
          dsgn ="nhcaretaker"
        elif location =="Panini Hostel":
          dsgn ="phcaretaker"
        else:
          dsgn = "rewacaretaker"
        caretaker_name = HoldsDesignation.objects.select_related('user','working','designation').get(designation__name = dsgn)
    

        # This is to allow the student
        student = 1
        message = "A New Complaint has been lodged"
        complaint_system_notif(request.user, caretaker_name.user,'lodge_comp_alert',obj1.id,student,message)

        # return render(request, "complaintModule/complaint_user.html",
        #               {'history': history, 'comp_id': comp_id })
        # next = request.POST.get('next', '/')

        messages.success(request,message)
        return HttpResponseRedirect('/complaint/supervisor')

    else:
        a = get_object_or_404(User, username=request.user.username)
        y = ExtraInfo.objects.all().select_related('user','department').filter(user=a).first()
        historytemp = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').filter(complainer=y).order_by('-id')
        history=[]

        notification = Notification.objects.filter(recipient=a.id)
        notification = notification.filter(data__exact={'url':'complaint:detail','module':'Complaint System'})
        # notification_message = []
        # for notification in x:
        #     to = User.objects.get(id=notification.actor_object_id).username
        #     from django.utils.timesince import timesince as timesince_
        #     duration = timesince_(notification.timestamp,None)
        #     notification_message.append(notification.verb+' by '+ to + ' ' + duration + ' ago ')
        



        j = 1
        for i in historytemp:
            history.append(i)
            # if j%2 != 0:
            #     history.append(i)
            # j = j+1

        for i in history:
            i.serial_no = j
            j = j+1

        # if location == "hall-1":
        #   dsgn ="hall1caretaker"
        # elif location =="hall-3":
        #   dsgn ="hall3caretaker"
        # elif location =="hall-4":
        #   dsgn ="hall4caretaker"
        # elif location =="CC1":
        #   dsgn ="CC convenor"
        # elif location =="CC2":
        #   dsgn ="CC2 convener"
        # elif location == "core_lab":
        #   dsgn = "corelabcaretaker"
        # elif location =="LHTC":
        #   dsgn ="lhtccaretaker"
        # elif location =="NR2":
        #   dsgn ="nr2caretaker"
        # else:
        #   dsgn = "rewacaretaker"
        # caretaker_name = HoldsDesignation.objects.get(designation__name = dsgn)
        
        # complaint_system_notif(request.user, caretaker_name.user,'lodge_comp_alert')
        return render(request, "complaintModule/supervisor1.html",
                      {'history': history,'notification':notification, 'comp_id': y.id})

    return render(request, "complaintModule/complaint_user.html",
                      {'history': history, 'comp_id': comp_id })




@login_required
def submitfeedbacksuper(request, complaint_id):
    """
    The function is used by the complainant to enter feedback after the complaint has been resolved
    @param:
            request - trivial.
            complaint_id - id of the registerd complaint.

    @variables:
            issue - The issue object.
            supported - True if the user's intention is to support the issue.
            support_count - Total supporters of the above issue.
            context - Holds data needed to make necessary changes in the template.
    """

    if request.method == 'POST':
        feedback = request.POST.get('feedback', '')
        rating = request.POST.get('rating', '')
        StudentComplain.objects.select_related('complainer','complainer__user','complainer__department').filter(id=complaint_id).\
        update(feedback=feedback, flag=rating)
        a = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department').filter(id=complaint_id).first()
        care = Caretaker.objects.select_related('staff_id','staff_id__user','staff_id__department').filter(area=a.location).first()
        rate = care.rating
        newrate = 0
        if rate == 0:
            newrate = rating
        else:
            a1 = int(rating)
            b1 = int(rate)
            c1 = int((a1+b1)/2)
            newrate = c1

        Caretaker.objects.select_related('staff_id','staff_id__user','staff_id__department').filter(area=a.location).update(rating=newrate)
        return HttpResponseRedirect('/complaint/supervisor/')
        return render(request,"complaintModule/feedback.html",{'a' : a})
        
    else:
        a = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department').get(id=complaint_id)
        return render(request, "complaintModule/submit_feedback.html", {'a': a})



@login_required

def caretakerlodge(request):
    """
    The function is used to register a complaint
    @param:
            request - trivial.


    @variables:
            issue - The issue object.
            supported - True if the user's intention is to support the issue.
            support_count - Total supporters of the above issue.
            context - Holds data needed to make necessary changes in the template.
    """
    a = get_object_or_404(User, username=request.user.username)
    y = ExtraInfo.objects.all().select_related('user','department').filter(user=a).first()
    num = 1
    comp_id = y.id
    if request.method == 'POST':
        comp_type = request.POST.get('complaint_type', '')
        location = request.POST.get('Location', '')
        specific_location = request.POST.get('specific_location', '')
        comp_file = request.FILES.get('myfile')
           
        details = request.POST.get('details', '')
        status = 0
        # finish time is according to complaint type
        complaint_finish = datetime.now() + timedelta(days=2)
        if comp_type == 'Electricity':
            complaint_finish = datetime.now() + timedelta(days=2)
        elif comp_type == 'carpenter':
            complaint_finish = datetime.now() + timedelta(days=2)
        elif comp_type == 'plumber':
            complaint_finish = datetime.now() + timedelta(days=2)
        elif comp_type == 'garbage':
            complaint_finish = datetime.now() + timedelta(days=1)
        elif comp_type == 'dustbin':
            complaint_finish = datetime.now() + timedelta(days=1)
        elif comp_type == 'internet':
            complaint_finish = datetime.now() + timedelta(days=4)
        elif comp_type == 'other':
            complaint_finish = datetime.now() + timedelta(days=3)
        y = ExtraInfo.objects.all().select_related('user','department').get(id=comp_id)
        #check if location given
        if location!="":
            # x = StudentComplain(complainer=y,
            #                     complaint_type=comp_type,
            #                     location=location,
            #                     specific_location=specific_location,
            #                     details=details,
            #                     status=status,
            #                     complaint_finish=complaint_finish,
            #                     upload_complaint=comp_file)
            
            
            # x.save()
            obj1, created = StudentComplain.objects.get_or_create(complainer=y,
                                complaint_type=comp_type,
                                location=location,
                                specific_location=specific_location,
                                details=details,
                                status=status,
                                complaint_finish=complaint_finish,
                                upload_complaint=comp_file)

            
        historytemp = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').filter(complainer=y).order_by('-id')
        history = []
        j = 1
        k = 1
        for i in historytemp:
            history.append(i)
            # if j%2 != 0:
            #     history.append(i)
            # j = j+1


        for h in history:
            h.serial_no = k
            k = k+1
        # if location == "hall1":
        #     dsgn = "hall1caretaker"
        # elif location == "hall3":
        #     dsgn = "hall3caretaker"
        # else :
        #     dsgn = "hall4caretaker"
        if location == "hall-1":
          dsgn ="hall1caretaker"
        elif location =="hall-3":
          dsgn ="hall3caretaker"
        elif location =="hall-4":
          dsgn ="hall4caretaker"
        elif location =="CC1":
          dsgn ="cc1convener"
        elif location =="CC2":
          dsgn ="CC2 convener"
        elif location == "core_lab":
          dsgn = "corelabcaretaker"
        elif location =="LHTC":
          dsgn ="lhtccaretaker"
        elif location =="NR2":
          dsgn ="nr2caretaker"
        elif location =="Maa Saraswati Hostel":
          dsgn ="mshcaretaker"
        elif location =="Nagarjun Hostel":
          dsgn ="nhcaretaker"
        elif location =="Panini Hostel":
          dsgn ="phcaretaker"
        else:
          dsgn = "rewacaretaker"
        caretaker_name = HoldsDesignation.objects.select_related('user','working','designation').get(designation__name = dsgn)
    

        # This is to allow the student
        student = 1
        message = "A New Complaint has been lodged"
        complaint_system_notif(request.user, caretaker_name.user,'lodge_comp_alert',obj1.id,student,message)

        # return render(request, "complaintModule/complaint_user.html",
        #               {'history': history, 'comp_id': comp_id })
        # next = request.POST.get('next', '/')

        messages.success(request,message)
        return HttpResponseRedirect('/complaint/caretaker')

    else:
        a = get_object_or_404(User, username=request.user.username)
        y = ExtraInfo.objects.all().select_related('user','department').filter(user=a).first()
        historytemp = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').filter(complainer=y).order_by('-id')
        history=[]

        notification = Notification.objects.filter(recipient=a.id)
        notification = notification.filter(data__exact={'url':'complaint:detail','module':'Complaint System'})
        # notification_message = []
        # for notification in x:
        #     to = User.objects.get(id=notification.actor_object_id).username
        #     from django.utils.timesince import timesince as timesince_
        #     duration = timesince_(notification.timestamp,None)
        #     notification_message.append(notification.verb+' by '+ to + ' ' + duration + ' ago ')
        



        j = 1
        for i in historytemp:
            history.append(i)
            # if j%2 != 0:
            #     history.append(i)
            # j = j+1

        for i in history:
            i.serial_no = j
            j = j+1

        # if location == "hall-1":
        #   dsgn ="hall1caretaker"
        # elif location =="hall-3":
        #   dsgn ="hall3caretaker"
        # elif location =="hall-4":
        #   dsgn ="hall4caretaker"
        # elif location =="CC1":
        #   dsgn ="CC convenor"
        # elif location =="CC2":
        #   dsgn ="CC2 convener"
        # elif location == "core_lab":
        #   dsgn = "corelabcaretaker"
        # elif location =="LHTC":
        #   dsgn ="lhtccaretaker"
        # elif location =="NR2":
        #   dsgn ="nr2caretaker"
        # else:
        #   dsgn = "rewacaretaker"
        # caretaker_name = HoldsDesignation.objects.get(designation__name = dsgn)
        
        # complaint_system_notif(request.user, caretaker_name.user,'lodge_comp_alert')
        return render(request, "complaintModule/complaint_caretaker.html",
                      {'history': history,'notification':notification, 'comp_id': y.id})

    return render(request, "complaintModule/complaint_user.html",
                      {'history': history, 'comp_id': comp_id })


@login_required
def submitfeedbackcaretaker(request, complaint_id):
    """
    The function is used by the complainant to enter feedback after the complaint has been resolved
    @param:
            request - trivial.
            complaint_id - id of the registerd complaint.

    @variables:
            issue - The issue object.
            supported - True if the user's intention is to support the issue.
            support_count - Total supporters of the above issue.
            context - Holds data needed to make necessary changes in the template.
    """

    if request.method == 'POST':
        feedback = request.POST.get('feedback', '')
        rating = request.POST.get('rating', '')
        StudentComplain.objects.select_related('complainer','complainer__user','complainer__department').filter(id=complaint_id).\
        update(feedback=feedback, flag=rating)
        a = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department').filter(id=complaint_id).first()
        care = Caretaker.objects.select_related('staff_id','staff_id__user','staff_id__department').filter(area=a.location).first()
        rate = care.rating
        newrate = 0
        if rate == 0:
            newrate = rating
        else:
            a1 = int(rating)
            b1 = int(rate)
            c1 = int((a1+b1)/2)
            newrate = c1

        Caretaker.objects.select_related('staff_id','staff_id__user','staff_id__department').filter(area=a.location).update(rating=newrate)
        return HttpResponseRedirect('/complaint/caretaker/')
        return render(request,"complaintModule/feedback.html",{'a' : a})
        
    else:
        a = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department').get(id=complaint_id)
        return render(request, "complaintModule/submit_feedback.html", {'a': a})