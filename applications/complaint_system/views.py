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
from .models import Caretaker, StudentComplain, Supervisor, Workers
from notification.views import  complaint_system_notif
#function for reassign to another worker
@login_required
def complaint_reassign(request,wid,iid):
    current_user = get_object_or_404(User, username=request.user.username)
    y = ExtraInfo.objects.all().select_related('user','department').filter(user=current_user).first()
    if request.method == 'POST':
        type = request.POST.get('submit', '')
        a = get_object_or_404(User, username=request.user.username)
        y = ExtraInfo.objects.all().select_related('user','department').filter(user=a).first()
        comp_id = y.id
        if type == 'assign':

            complaint_finish = request.POST.get('complaint_finish', '')
            worker_id = request.POST.get('assign_worker', '')
            w = Workers.objects.select_related('caretaker_id','caretaker_id__staff_id','caretaker_id__staff_id__user','caretaker_id__staff_id__department').get(id=worker_id)
            StudentComplain.objects.select_for_update().filter(id=iid).\
                update(worker_id=w, status=1)
            url = '/complaint/caretaker/worker_id_know_more/'+wid;
            complainer_details = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').get(id=iid)
            student=0
            message = "Your complaint has been re-assigned"
            complaint_system_notif(request.user, complainer_details.complainer.user ,'reassign_worker_alert',complainer_details.id,student,message)
            return HttpResponseRedirect(url)
        elif type == 'redirect':
            assign_caretaker = request.POST.get('assign_caretaker', '')
            c = Caretaker.objects.select_related('staff_id','staff_id__user','staff_id__department').get(id=assign_caretaker)
            c1 = Caretaker.objects.select_related('staff_id','staff_id__user','staff_id__department').get(id=iid)
            remark = 'Redirect complaint from ' + c1.area
            StudentComplain.objects.select_for_update().filter(id=iid).\
                update(location=c.area, remarks=remark)
            url = '/complaint/caretaker/worker_id_know_more/'+wid;
            complainer_details = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').get(id=iid)
            student=0
            message = "Your complaint has been redirected to another caretaker"
            complaint_system_notif(request.user, complainer_details.complainer.user ,'comp_redirect_alert',complainer_details.id,student,message)
            return HttpResponseRedirect(url)
        
    else:
        y = ExtraInfo.objects.all().select_related('user','department').get(id=y.id)
        a = Caretaker.objects.select_related('staff_id','staff_id__user','staff_id__department').get(staff_id=y)
        b = a.area
        comp_id = y.id
        try:
            detail = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').filter(id=iid).first()
            total_caretaker = Caretaker.objects.select_related('staff_id','staff_id__user','staff_id__department').all()
            total_caretakers_in_area = Caretaker.objects.select_related('staff_id','staff_id__user','staff_id__department').filter(area=b)
            worker = []
            workertemp = []
            flag = ''
            temp = detail.location
            try:
            
                if Workers.objects.select_related('caretaker_id','caretaker_id__staff_id','caretaker_id__staff_id__user','caretaker_id__staff_id__department').filter(caretaker_id=a).count() == 0:
                    flag = 'no_worker'
                else:
                    workertemp = Workers.objects.select_related('caretaker_id','caretaker_id__staff_id','caretaker_id__staff_id__user','caretaker_id__staff_id__department').filter(caretaker_id=a)
                    j = 1
                    for i in workertemp:
                        worker.append(i)
                        # if j%2 != 0:
                        #     worker.append(i)
                        # j = j + 1


            except Caretaker.DoesNotExist:
                flag = 'no_worker'

        except StudentComplain.DoesNotExist:
            return HttpResponse("<H1>Not a valid complaint </H1>")
        return render(request, "complaintModule/reassignworker.html",
                      {'detail': detail, 'worker': worker, 'flag':
                          flag, 'total_caretaker': total_caretaker,'a':a, 'wid':wid, 'total_caretakers_in_area':total_caretakers_in_area})

@login_required
def complaint_reassign_super(request,caretaker_id,iid):
    current_user = get_object_or_404(User, username=request.user.username)
    y = ExtraInfo.objects.all().select_related('user','department').filter(user=current_user).first()
    sup = Supervisor.objects.select_related('sup_id','sup_id__user','sup_id__department').get(sup_id = y)
    this_area = sup.area
    if request.method == 'POST':
        a = get_object_or_404(User, username=request.user.username)
        y = ExtraInfo.objects.all().select_related('user','department').filter(user=a).first()
        comp_id = y.id





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
        if type == 'assign':
            complaint_finish = request.POST.get('complaint_finish', '')
            worker_id = request.POST.get('assign_worker', '')
            w = Workers.objects.select_related('caretaker_id','caretaker_id__staff_id','caretaker_id__staff_id__user','caretaker_id__staff_id__department').get(id=worker_id)
            StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').select_for_update().filter(id=comp_id1).\
                update(worker_id=w, status=1)
            complainer_details = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').get(id=comp_id1)
            student = 0
            message = "Worker has been assigned to your complaint"
            complaint_system_notif(request.user, complainer_details.complainer.user ,'assign_worker_alert',complainer_details.id,student,message)

            return HttpResponseRedirect('/complaint/caretaker/')
        elif type == 'redirect':
            assign_caretaker = request.POST.get('assign_caretaker', '')
            c = Caretaker.objects.select_related('staff_id','staff_id__user','staff_id__department').get(id=assign_caretaker)
            c1 = Caretaker.objects.select_related('staff_id','staff_id__user','staff_id__department').get(id=comp_id)
            remark = 'Redirect complaint from ' + c1.area
            StudentComplain.objects.select_for_update().filter(id=comp_id1).\
                update(location=c.area, remarks=remark)
            complainer_details = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').get(id=comp_id1)
            student=0
            message = "Your Complaint has been redirected to another caretaker"
            complaint_system_notif(request.user, complainer_details.complainer.user ,'comp_redirect_alert',complainer_details.id,student,message)
            return HttpResponseRedirect('/complaint/caretaker/')
    else:
        y = ExtraInfo.objects.all().select_related('user','department').get(id=y.id)
        a = Caretaker.objects.select_related('staff_id','staff_id__user','staff_id__department').get(staff_id=y)
        b = a.area
        comp_id = y.id
        try:
            detail = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').filter(id=comp_id1).first()
            total_caretaker = Caretaker.objects.select_related('staff_id','staff_id__user','staff_id__department').all()
            total_caretakers_in_area = Caretaker.objects.select_related('staff_id','staff_id__user','staff_id__department').filter(area=b and id!=a.id)
            workertemp = []
            worker = []
            flag = ''
            temp = detail.location
            try:
                #care = Caretaker.objects.filter(area=temp).first()
                if Workers.objects.select_related('caretaker_id','caretaker_id__staff_id','caretaker_id__staff_id__user','caretaker_id__staff_id__department').filter(caretaker_id=a).count() == 0:
                    flag = 'no_worker'
                else:
                    workertemp1 = Workers.objects.select_related('caretaker_id','caretaker_id__staff_id','caretaker_id__staff_id__user','caretaker_id__staff_id__department').filter(caretaker_id=a)
                    workertemp = workertemp1.filter(worker_type=detail.complaint_type)
                    j = 1
                    for i in workertemp:
                        worker.append(i)
                        # if j%2 != 0:
                        #     worker.append(i)
                        # j = j + 1


            except Caretaker.DoesNotExist:
                flag = 'no_worker'

        except StudentComplain.DoesNotExist:
            return HttpResponse("<H1>Not a valid complaint </H1>")
        return render(request, "complaintModule/assignworker.html",
                      {'detail': detail, 'worker': worker, 'flag':
                          flag, 'total_caretaker': total_caretaker,'a':a, 'total_caretakers_in_area':total_caretakers_in_area})

@login_required
def discharge_worker(request,wid,cid):
    current_user = get_object_or_404(User, username=request.user.username)
    y = ExtraInfo.objects.all().select_related('user','department').filter(user=current_user).first()

    this_worker = Workers.objects.select_related('caretaker_id','caretaker_id__staff_id','caretaker_id__staff_id__user','caretaker_id__staff_id__department').get(id=wid)
    com_in_concern= StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').get(id=cid);
    com_in_concern.worker_id=None;
    com_in_concern.status=0;
    StudentComplain.objects.select_for_update().filter(id=cid).\
                update(worker_id=None, status=0)
    #StudentComplain.objects.get(id=cid).delete()
    url='/complaint/caretaker/detail2/'+cid;
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


@login_required
def worker_id_know_more(request, work_id):
    """
    function to know pending complaints assigned to the worker
    """
    this_worker = Workers.objects.select_related('caretaker_id','caretaker_id__staff_id','caretaker_id__staff_id__user','caretaker_id__staff_id__department').get(id=work_id)
    num = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').filter(worker_id=this_worker).count();
    complaints_list = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').filter(worker_id=this_worker);
    complaints_list_onhold = []
    for i in complaints_list:
        if i.status == 1:
            complaints_list_onhold.append(i)
    numpend = len(complaints_list_onhold)
    work_under_caretaker1 = this_worker.caretaker_id.staff_id.user.first_name
    work_under_caretaker2 = this_worker.caretaker_id.staff_id.user.last_name
    return render(request, "complaintModule/worker_id_know_more.html",{'this_worker':this_worker,'work_under_caretaker1':work_under_caretaker1,'work_under_caretaker2':work_under_caretaker2, 'num':num, 'complaints_list':complaints_list, 'complaints_list_onhold':complaints_list_onhold, 'numpend':numpend})




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
        if b.user_type == 'student':
            return HttpResponseRedirect('/complaint/user/')
        elif b.user_type == 'staff':
            return HttpResponseRedirect('/complaint/caretaker/')
        elif b.user_type == 'faculty':
            return HttpResponseRedirect('/complaint/supervisor/')
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
        return HttpResponseRedirect('/complaint/user')

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
        return render(request, "complaintModule/complaint_user.html",
                      {'history': history,'notification':notification, 'comp_id': y.id})

    return render(request, "complaintModule/complaint_user.html",
                      {'history': history, 'comp_id': comp_id })
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
       # messages.info(request,'Complaint successfully launched.')
        # return HttpResponseRedirect('/complaint/user/')
        return HttpResponseRedirect('/complaint/user/')

@login_required
def caretaker(request):
    """
    The function is used to display details to the caretaker such as registered complaints and allows to assign workers
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
        type = request.POST.get('submit', '')
        worker_type = request.POST.get('complaint_type', '')
        name = request.POST.get('name', '')
        phone = request.POST.get('phone_no', '')
        age = request.POST.get('age', '')
        try:
            y = ExtraInfo.objects.all().select_related('user','department').get(id=y.id)
            a = Caretaker.objects.select_related('staff_id','staff_id__user','staff_id__department').get(staff_id=y)
        except Exception as e:
            a = None
            y = None
        intage = int(age)
        intphone = int(phone)
        # if len(phone) == 10 and intage > 20 and intage < 50 and intphone > 1999999999:
        #     x = Workers(caretaker_id=a,
        #                 name=name,
        #                 age=age,
        #                 phone=phone,
        #                 worker_type=worker_type)
        #     if not Workers.objects.filter(caretaker_id=a,name=name, age=age,phone=phone,worker_type=worker_type).exists():
        #         x.save()

        if len(phone) == 10 and intage > 20 and intage < 50 and intphone > 1999999999:
            obj, created = Workers.objects.get_or_create(caretaker_id=a,
                        name=name,
                        age=age,
                        phone=phone,
                        worker_type=worker_type)
        
        b = a.area
        historytemp = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').filter(location=b).order_by('-id')
        history = []
        j = 1
        k = 1
        for i in historytemp:
            history.append(i)
            # if j%2 == 1:
            #     history.append(i)
            # j = j+1
        for h in history:
            h.serial_no = k
            k=k+1
        

        total_worker = []
        total_workertemp = Workers.objects.select_related('caretaker_id','caretaker_id__staff_id','caretaker_id__staff_id__user','caretaker_id__staff_id__department').filter(caretaker_id=a)
        j = 1
        # for i in total_workertemp:
        #     if j%2 != 0:
        #         total_worker.append(i)
        #     j = j + 1
        

        for i in total_workertemp:
            total_worker.append(i)

        complaint_assign_no = []

        for x in total_worker:
            worker = Workers.objects.select_related('caretaker_id','caretaker_id__staff_id','caretaker_id__staff_id__user','caretaker_id__staff_id__department').get(id=x.id)
            temp = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').filter(worker_id=worker).count()
            worker.total_complaint = temp
            complaint_assign_no.append(worker)

        notification = Notification.objects.filter(recipient=current_user.id)
        notification = notification.filter(data__exact={'url':'complaint:detail2','module':'Complaint System'})
        return render(request, "complaintModule/complaint_caretaker.html",
                      {'history': history, 'comp_id': y.id, 
                      'notification': notification, 'total_worker':
                        total_worker, 'complaint_assign_no': complaint_assign_no})
        


    else:
        y = ExtraInfo.objects.all().select_related('user','department').get(id=y.id)  
        a = Caretaker.objects.select_related('staff_id','staff_id__user','staff_id__department').get(staff_id=y)
        b = a.area
        history = []
        historytemp = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').filter(location=b).order_by('-id')
        total_worker = []
        total_workertemp = Workers.objects.select_related('caretaker_id','caretaker_id__staff_id','caretaker_id__staff_id__user','caretaker_id__staff_id__department').filter(caretaker_id=a)
        j = 1
        for i in total_workertemp:
            total_worker.append(i)
            
        complaint_assign_no = []
        complaint_assign_no = []

        for x in total_worker:
            worker = Workers.objects.select_related('caretaker_id','caretaker_id__staff_id','caretaker_id__staff_id__user','caretaker_id__staff_id__department').get(id=x.id)
            temp = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').filter(worker_id=worker).count()
            worker.total_complaint = temp
            complaint_assign_no.append(worker)

        overduecomplaint = []
        j = 1
        k = 1
        for i in historytemp:
            history.append(i)
            # if j%2 != 0:
            #     history.append(i)
            # j=j+1
        for i in history:
            i.serial_no = k
            k = k + 1

            if i.status != 2 and i.status !=3:
                if i.complaint_finish < date.today():
                    i.delay = date.today() - i.complaint_finish
                    overduecomplaint.append(i)
        
        notification = Notification.objects.filter(recipient=current_user.id)
        notification = notification.filter(data__exact={'url':'complaint:detail2','module':'Complaint System'})
        

        
        return render(request, "complaintModule/complaint_caretaker.html",
                      { 'history': history, 'comp_id': y.id, 'total_worker': total_worker,
                        'complaint_assign_no': total_worker,
                        'notification':notification,
                        'overduecomplaint': overduecomplaint, 'care_id': a})

@login_required
def remove_worker_from_complaint(request,complaint_id):
    """
    The function is used by caretaker to remove a worker
    already assigned to a complaint
    @param:
       request - trivial
       complaint_id - used to get complaint_id registered
    """
    complaint = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').filter(complaint_id=complaint_id).update(worker_id='')
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
        StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').filter(id=complaint_id).\
            update(status=status, worker_id='')
        return HttpResponseRedirect('/complaint/caretaker/')
    elif status == '2':
        StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').filter(id=complaint_id).\
            update(status=status, worker_id='')
        return HttpResponseRedirect('/complaint/caretaker/')
    else:
        StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').filter(id=complaint_id).\
            update(status=status)
        return HttpResponseRedirect('/complaint/caretaker/')


@login_required
def removew(request, work_id):
    """
    The function is used by caretaker to remove workers.
    @param:
            request - trivial.
            work_id - id of the issue object which the user intends to support/unsupport.

    @variables:
            issue - The issue object.
            supported - True if the user's intention is to support the issue.
            support_count - Total supporters of the above issue.
            context - Holds data needed to make necessary changes in the template.
    """
    worker = Workers.objects.select_related('caretaker_id','caretaker_id__staff_id','caretaker_id__staff_id__user','caretaker_id__staff_id__department').get(id=work_id)
    temp = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').filter(worker_id=worker).count()
    if temp == 0:
        worker.delete()
        return HttpResponseRedirect('/complaint/caretaker/')
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
        StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').filter(id=complaint_id).\
        update(feedback=feedback, flag=rating)
        a = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').filter(id=complaint_id).first()
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
        return render(request,"complaintModule/feedback.html",{'a' : a})
        
    else:
        a = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').get(id=complaint_id)
        return render(request, "complaintModule/submit_feedback.html", {'a': a})






@login_required
def deletecomplaint(request, comp_id1):
    """
    function to delete complaint
    """
    StudentComplain.objects.get(id=comp_id1).delete()
    return HttpResponseRedirect('/complaint/caretaker/')

def testEntry():
    # list1 = [('SKM','hall-1'),('HS','hall-3'),('PS','hall-4'),('MSR','Maa Saraswati Hostel'),('KKB','Maa Saraswati Hostel'), ('RP','Nagarjun Hostel'),('DS','Nagarjun Hostel'),('AV','Panini Hostel')]
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
    current_user = get_object_or_404(User, username=request.user.username)
    
    y = ExtraInfo.objects.all().select_related('user','department').filter(user=current_user).first()
    if request.method == 'POST' :
        try:
            y = ExtraInfo.objects.all().select_related('user','department').get(id=y.id)
            a = Supervisor.objects.select_related('sup_id','sup_id__user','sup_id__department').get(sup_id=y)
        except Exception as e:
            a = None
            y = None
        all_caretaker = Caretaker.objects.select_related('staff_id','staff_id__user','staff_id__department').filter(area=a.area).order_by('-id')
        area = all_caretaker[0].area
        # ExtraInfo.objects.get(id=sup_id)
        all_complaint = []
        numtemp = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').filter(location =  area).filter(status = 0).count()
        num = int(numtemp/2+0.5)
        all_complainttemp = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').filter(location=a.area).order_by('-id')
        j = 1
        for i in all_complainttemp:
            all_complaint.append(i)
            # if j%2 != 0:
            #     all_complaint.append(i)
            # j = j + 1
        overduecomplaint = []
        for i in all_complaint:
            if i.status != 2 and i.status != 3:
                if i.complaint_finish < date.today():
                    i.delay = date.today() - i.complaint_finish
                    overduecomplaint.append(i)

        return render(request, "complaintModule/supervisor1.html",
                    {'all_caretaker': all_caretaker, 'all_complaint': all_complaint,
                   'overduecomplaint': overduecomplaint, 'area': area,'num':num})
    else:
        print('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
        y = ExtraInfo.objects.all().select_related('user','department').get(id=y.id)
        try:
            a = get_object_or_404(Supervisor, sup_id=y)
        except :
            return HttpResponseRedirect('/')

        #print(a)
        # if(len(a)==0) :
        #     return render('../dashboard/')
        a = Supervisor.objects.select_related('sup_id','sup_id__user','sup_id__department').get(sup_id=y)
        all_caretaker = Caretaker.objects.select_related('staff_id','staff_id__user','staff_id__department').filter(area=a.area).order_by('-id')
        area = all_caretaker[0].area
        numtemp = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').filter(location =  area).filter(status = 0).count()
        num = int(numtemp/2+0.5)
        all_complaint = []
        all_complainttemp = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').filter(location=a.area).order_by('-id')
        j = 1
        for i in all_complainttemp:
            all_complaint.append(i)
            # if j%2 != 0:
            #     all_complaint.append(i)
            # j = j + 1
        overduecomplaint = []
        for i in all_complaint:
            if i.status != 2 and i.status != 3:
                if i.complaint_finish < date.today():
                    i.delay = date.today() - i.complaint_finish
                    overduecomplaint.append(i)

        return render(request, "complaintModule/supervisor1.html",
                    {'all_caretaker': all_caretaker, 'all_complaint': all_complaint,
                   'overduecomplaint': overduecomplaint, 'area': area, 'num' : num})

@login_required
def caretaker_id_know_more(request,caretaker_id):
    this_caretaker = Caretaker.objects.select_related('staff_id','staff_id__user','staff_id__department').get(id = caretaker_id)
    this_caretaker_area = this_caretaker.area;
    list_pending_complaints = []
    list_pending_complaintstemp = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').filter(location = this_caretaker_area).filter(status = 0)
    j = 1
    for i in list_pending_complaintstemp:
        list_pending_complaints.append(i)
        # if j%2 != 0:
        #     list_pending_complaints.append(i)
        # j = j + 1

    # num = StudentComplain.objects.filter(location = this_caretaker_area).filter(status = 0).count();
    num = len(list_pending_complaints)
    return render(request, "complaintModule/caretaker_id_know_more.html",{'this_caretaker':this_caretaker , 'list_pending_complaints':list_pending_complaints, 'num':num})


def search_complaint(request):
    return HttpResponseRedirect('/login/')

@login_required
def resolvepending(request, cid):
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
        return HttpResponseRedirect("/complaint/caretaker/")
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
    detail3 = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').get(id=feedcomp_id)
    a=User.objects.get(username=detail3.complainer.user.username)           
    y=ExtraInfo.objects.all().select_related('user','department').get(user=a)
    temp=StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').filter(complainer=y).first()                                                                  
    comp_id=temp.id 
    loc = detail3.location
    care = Caretaker.objects.select_related('staff_id','staff_id__user','staff_id__department').filter(area=loc).first()
    return render(request, "complaintModule/feedback_super.html", {"detail3": detail3,"comp_id":comp_id,"care":care})


@login_required
def feedback_care(request, feedcomp_id):
    detail2 = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').get(id=feedcomp_id)
    a=User.objects.get(username=detail2.complainer.user.username)           
    y=ExtraInfo.objects.all().select_related('user','department').get(user=a)
    temp=StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').filter(complainer=y).first()                                                                  
    comp_id=temp.id 
    return render(request, "complaintModule/feedback_care.html", {"detail2": detail2,"comp_id":comp_id})




@login_required
def detail(request, detailcomp_id1):
    """
    function that shows detail about complaint
    """
    detail = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').get(id=detailcomp_id1)
    if(detail.worker_id is None):
        worker_name = None
        worker_id = detail.worker_id  
    else:
        worker_id = detail.worker_id.id
        worker = Workers.objects.select_related('caretaker_id','caretaker_id__staff_id','caretaker_id__staff_id__user','caretaker_id__staff_id__department').get(id=worker_id)
        worker_name = worker.name
    a=User.objects.get(username=detail.complainer.user.username)           
    y=ExtraInfo.objects.all().select_related('user','department').get(user=a)
    num=0
    if detail.upload_complaint != "":
        num = 1
    temp=StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').filter(complainer=y).first()                                                                  
    comp_id=temp.id 
    return render(request, "complaintModule/complaint_user_detail.html", {"detail": detail, "comp_id":detail.id,"num":num,"worker_name":worker_name})

@login_required
def detail2(request, detailcomp_id1):
    detail2 = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').get(id=detailcomp_id1)
    if(detail2.worker_id is None):
        worker_name = None
        worker_id = detail2.worker_id  
    else:
        worker_id = detail2.worker_id.id
        worker = Workers.objects.select_related('caretaker_id','caretaker_id__staff_id','caretaker_id__staff_id__user','caretaker_id__staff_id__department').get(id=worker_id)
        worker_name = worker.name
    a=User.objects.get(username=detail2.complainer.user.username)           
    y=ExtraInfo.objects.all().select_related('user','department').get(user=a)
    num=0
    
    if detail2.upload_complaint != "":
        num = 1
    temp=StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').filter(complainer=y).first()                                                               
    comp_id=temp.id 
    return render(request, "complaintModule/complaint_caretaker_detail.html", {"detail2": detail2, "comp_id":detail2.id,"num":num,"worker_name":worker_name,"wid":worker_id})

@login_required
def detail3(request, detailcomp_id1):
    detail3 = StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').get(id=detailcomp_id1)
    a=User.objects.get(username=detail3.complainer.user.username)           
    y=ExtraInfo.objects.all().select_related('user','department').get(user=a)
    num=0
    if detail3.upload_complaint != "":
        num = 1
    temp=StudentComplain.objects.select_related('complainer','complainer__user','complainer__department','worker_id','worker_id__caretaker_id__staff_id','worker_id__caretaker_id__staff_id__user','worker_id__caretaker_id__staff_id__department').filter(complainer=y).first()                                                                  
    comp_id=temp.id 
    loc = detail3.location
    care = Caretaker.objects.select_related('staff_id','staff_id__user','staff_id__department').filter(area=loc).first()
    return render(request, "complaintModule/complaint_supervisor_detail.html", {"detail3": detail3,"comp_id":comp_id,"care":care,"num":num})
