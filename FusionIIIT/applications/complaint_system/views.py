from datetime import date, datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render

from applications.globals.models import ExtraInfo, User

from .models import Caretaker, StudentComplain, Supervisor, Workers
from django.contrib.auth import authenticate, login


@login_required
def assign_worker(request, comp_id1):
    if request.method == 'POST':
        type = request.POST.get('submit', '')
        a = get_object_or_404(User, username=request.user.username)
        y = ExtraInfo.objects.all().filter(user=a).first()
        comp_id = y.id
        if type == 'assign':

            complaint_finish = request.POST.get('complaint_finish', '')
            worker_id = request.POST.get('assign_worker', '')
            w = Workers.objects.get(id=worker_id)


            # StudentComplain.objects.get(id=comp_id).update
            # (complaint_finish='complaint_finish', worker_id='worker_id')
            StudentComplain.objects.select_for_update().filter(id=comp_id1).\
                update(worker_id=w, status=1)
            return HttpResponseRedirect('/complaint/caretaker/')
        elif type == 'redirect':
            assign_caretaker = request.POST.get('assign_caretaker', '')
            c = Caretaker.objects.get(id=assign_caretaker)
            c1 = Caretaker.objects.get(id=comp_id)
            remark = 'Redirect complaint from ' + c1.area
            StudentComplain.objects.select_for_update().filter(id=comp_id1).\
                update(location=c.area, remarks=remark)
            return HttpResponseRedirect('/complaint/caretaker/')
    else:
        a = get_object_or_404(User, username=request.user.username)
        y = ExtraInfo.objects.all().filter(user=a).first()
        comp_id = y.id
        try:
            detail = StudentComplain.objects.get(id=comp_id1)
            total_caretaker = Caretaker.objects.all()
            worker = ''
            flag = ''
            temp = detail.location
            try:
                care = Caretaker.objects.get(area=temp)
                if Workers.objects.filter(caretaker_id=care).count() == 0:
                    flag = 'no_worker'
                else:
                    worker = Workers.objects.filter(caretaker_id=care)

            except Caretaker.DoesNotExist:
                flag = 'no_worker'

        except StudentComplain.DoesNotExist:
            return HttpResponse("<H1>Not a valid complaint </H1>")
        return render(request, "complaintModule/assignworker.html",
                      {'detail': detail, 'worker': worker, 'flag':
                          flag, 'total_caretaker': total_caretaker})


@login_required
def check(request):
    if request.user.is_authenticated:
        a = get_object_or_404(User, username=request.user.username)
        # a = User.objects.get(username=request.user.username)
        b = ExtraInfo.objects.all().filter(user=a).first()
        # b = ExtraInfo.objects.get(user=a)
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
    a = get_object_or_404(User, username=request.user.username)
    y = ExtraInfo.objects.all().filter(user=a).first()
    comp_id = y.id
    if request.method == 'POST':
        comp_type = request.POST.get('complaint_type', '')
        location = request.POST.get('Location', '')
        specific_location = request.POST.get('specific_location', '')
        details = request.POST.get('details', '')

        y = ExtraInfo.objects.get(id=comp_id)

        x = StudentComplain(complainer=y,
                            complaint_type=comp_type,
                            location=location,
                            specific_location=specific_location,
                            details=details)

        x.save()
        history = StudentComplain.objects.filter(complainer=y).order_by('-id')
        j = '1'
        for i in history:
            i.serial_no = j
            j = j+1

        return render(request, "complaintModule/complaint_user.html",
                      {'history': history, 'comp_id': comp_id})

    else:
        a = get_object_or_404(User, username=request.user.username)
        y = ExtraInfo.objects.all().filter(user=a).first()
        # y = ExtraInfo.objects.get(id=comp_id)
        history = StudentComplain.objects.filter(complainer=y).order_by('-id')
        j = 1
        for i in history:
            i.serial_no = j
            j = j+1
        return render(request, "complaintModule/complaint_user.html",
                      {'history': history, 'comp_id': y.id})


@login_required
def save_comp(request):
    if request.method == 'POST':
        comp_id = request.POST.get('comp_id', '')
        comp_type = request.POST.get('complaint_type', '')
        location = request.POST.get('Location', '')
        specific_location = request.POST.get('specific_location', '')
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

        y = ExtraInfo.objects.get(id=comp_id)
        x = StudentComplain(complainer=y,
                            complaint_type=comp_type,
                            location=location,
                            specific_location=specific_location,
                            details=details,
                            complaint_finish=complaint_finish)

        x.save()
        return HttpResponseRedirect('/complaint/user/')


@login_required
def caretaker(request):
    current_user = get_object_or_404(User, username=request.user.username)
    y = ExtraInfo.objects.all().filter(user=current_user).first()

    if request.method == 'POST':
        worker_type = request.POST.get('complaint_type', '')
        name = request.POST.get('name', '')
        phone = request.POST.get('phone_no', '')
        age = request.POST.get('age', '')

        y = ExtraInfo.objects.get(id=y.id)
    
        a = Caretaker.objects.get(staff_id=y)
        x = Workers(caretaker_id=a,
                    name=name,
                    age=age,
                    phone=phone,
                    worker_type=worker_type)

        x.save()
        b = a.area
        history = StudentComplain.objects.filter(location=b).order_by('-id')
        j = 1
        for i in history:
            i.serial_no = j
            j = j+1

        total_worker = Workers.objects.filter(caretaker_id=a)
        complaint_assign_no = []

        for x in total_worker:
            worker = Workers.objects.get(id=x.id)
            temp = StudentComplain.objects.filter(worker_id=worker).count()
            worker.total_complaint = temp
            complaint_assign_no.append(worker)
        return render(request, "complaintModule/complaint_caretaker.html",
                      {'history': history, 'comp_id': y.id, 'total_worker':
                          total_worker, 'complaint_assign_no': complaint_assign_no})

    else:
        # y = ExtraInfo.objects.get(id=comp_id)
        a = Caretaker.objects.get(staff_id=y)
        b = a.area
        history = []
        history = StudentComplain.objects.filter(location=b).order_by('-id')
        total_worker = Workers.objects.filter(caretaker_id=a)
        complaint_assign_no = []

        for x in total_worker:
            worker = Workers.objects.get(id=x.id)
            temp = StudentComplain.objects.filter(worker_id=worker).count()
            worker.total_complaint = temp
            complaint_assign_no.append(worker)

        overduecomplaint = []
        j = 1
        for i in history:
            i.serial_no = j
            j=j+1
            if i.status != 0:
                if i.complaint_finish < date.today():
                    i.delay = date.today() - i.complaint_finish
                    overduecomplaint.append(i)

        return render(request, "complaintModule/complaint_caretaker.html",
                      {'history': history, 'comp_id': y.id, 'total_worker': total_worker,
                       'complaint_assign_no': complaint_assign_no,
                       'overduecomplaint': overduecomplaint, 'care_id': a})


@login_required
def changestatus(request, complaint_id, status):
    if status == '3':
        StudentComplain.objects.filter(id=complaint_id).\
            update(status=status, worker_id='')
        return HttpResponseRedirect('/complaint/caretaker/')
    elif status == '2':
        StudentComplain.objects.filter(id=complaint_id).\
            update(status=status, worker_id='')
        return HttpResponseRedirect('/complaint/caretaker/')
    else:
        StudentComplain.objects.filter(id=complaint_id).\
            update(status=status)
        return HttpResponseRedirect('/complaint/caretaker/')


@login_required
def removew(request, work_id):
    worker = Workers.objects.get(id=work_id)
    temp = StudentComplain.objects.filter(worker_id=worker).count()
    if temp == 0:
        worker.delete()
        return HttpResponseRedirect('/complaint/caretaker/')
    else:

        return HttpResponse('<H1> Worker is assign some complaint</h1>')


@login_required
def submitfeedback(request, complaint_id):
    if request.method == 'POST':
        feedback = request.POST.get('feedback', '')
        rating = request.POST.get('rating', '')
        StudentComplain.objects.filter(id=complaint_id).\
            update(feedback=feedback, flag=rating)
        a = StudentComplain.objects.filter(id=complaint_id).first()
        care = Caretaker.objects.filter(area=a.location).first()
        rate = care.rating
        newrate = 0
        if rate == 0:
            newrate = rating
        else:
            a1 = int(rating)
            b1 = int(rate)
            c1 = int((a1+b1)/2)
            newrate = c1

        Caretaker.objects.select_related().filter(area=a.location).update(rating=newrate)
        return HttpResponseRedirect('/complaint/user/')
    else:
        a = StudentComplain.objects.get(id=complaint_id)
        return render(request, "complaintModule/submit_feedback.html", {'a': a})


@login_required
def deletecomplaint(request, comp_id1):
    StudentComplain.objects.get(id=comp_id1).delete()
    return HttpResponseRedirect('/complaint/caretaker/')


@login_required
def supervisor(request):
    current_user = get_object_or_404(User, username=request.user.username)
    y = ExtraInfo.objects.all().filter(user=current_user).first()

    y = ExtraInfo.objects.get(id=y.id)
    a = Supervisor.objects.get(sup_id=y)
    all_caretaker = Caretaker.objects.filter(area=a.area).order_by('-id')
    area = all_caretaker[0].area
    # ExtraInfo.objects.get(id=sup_id)
    all_complaint = StudentComplain.objects.filter(location=a.area).order_by('-id')
    overduecomplaint = []
    for i in all_complaint:
        if i.status != 0:
            if i.complaint_finish < date.today():
                i.delay = date.today() - i.complaint_finish
                overduecomplaint.append(i)

    return render(request, "complaintModule/supervisor1.html",
                  {'all_caretaker': all_caretaker, 'all_complaint': all_complaint,
                   'overduecomplaint': overduecomplaint, 'area': area})


def search_complaint(request):
    return HttpResponseRedirect('/login/')

def login1(request):
    if request.method == 'POST':
        u = request.POST.get('username', '')
        p = request.POST.get('password', '')
        user = authenticate(username=u, password=p)
        if user is not None:
            if user.is_active:
                login(request, user)
                a = User.objects.get(username=u)
                b = ExtraInfo.objects.get(user=a)
                return HttpResponseRedirect('/complaint/')
        else:
            return HttpResponse("<h1>wrong user credentials</h1>")
    else:
        return HttpResponseRedirect('/login/')
