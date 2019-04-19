import datetime
from datetime import date, datetime
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect,JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from applications.academic_procedures.models import Thesis
from applications.globals.models import (Designation, ExtraInfo,
                                         HoldsDesignation, User)
from applications.scholarships.models import Mcm

from notification.views import office_dean_PnD_notif

from .forms import *
from .models import *
from .models import (Project_Closure, Project_Extension, Project_Reallocation,
                     Project_Registration)
from .views_office_students import *


def officeOfDeanRSPC(request):
    project=Project_Registration.objects.all()
    project1=Project_Extension.objects.all()
    project2=Project_Closure.objects.all()
    project3=Project_Reallocation.objects.all()

    design = HoldsDesignation.objects.filter(working=request.user)
    print(design)
    desig=[]
    for i in design:
        desig.append(str(i.designation))

    context = {'project':project, 'project1':project1, 'project2':project2, 'project3':project3, 'desig':desig}

    return render(request, "officeModule/officeOfDeanRSPC/officeOfDeanRSPC.html", context)

def _list_find(lst, predicate):
    """
    Find the first element in a list that satisfies the given predicate
    Arguments:
        - lst: List to search through
        - predicate: Predicate that determines what to return
    Returns:
        The first element that satisfies the predicate otherwise None
    """
    for v in lst:
        if predicate(v):
            return v
    return None

def _req_history(req):
    """
    Return requisition history: All tracking rows that are associated with the passet requisition
    """
    return Tracking.objects.filter(file_id=req.assign_file)

@login_required
def officeOfDeanPnD(request):
    """
        Main view for the office of dean (p&d) module.
        Generates four tabs:
            * Dashboard: Shows overview of requisitions and assignments
            * Create Requisition: Form to create new requisitions
            * View Requisitions: Lists all open requisitions and allows Junior Engg.
                to create work assignment from them.
            * View Assignments: Lists all assignments, incoming assignments and
                outgoing assignments. Allows performing actions on incoming assignments.
    """
    user = request.user
    extrainfo = ExtraInfo.objects.get(user=user)

    # Map designations to readable titles.
    deslist={
            'Civil_JE': 'Junior Engg. (Civil)',
            'Civil_AE':'Assistant Engg. (Civil)',
            'Electrical_JE': 'Junior Engg. (Electrical)',
            'Electrical_AE':'Assistant Engg. (Electrical)',
            'EE': 'Executive Engg.',
            'DeanPnD': 'Dean (P&D)',
            'Director': 'Director',
            'None':'Closed'
    }

    holds=HoldsDesignation.objects.filter(working=user)
    designations=[d.designation for d in HoldsDesignation.objects.filter(working=user)]

    # handle createassignment POST request
    if 'createassign' in request.POST:
        print("createassign", request)
        req_id=request.POST.get('req_id')
        requisition=Requisitions.objects.get(pk=req_id)
        description=request.POST.get('description')
        upload_file=request.FILES.get('estimate')
        sender_design=None
        for hold in holds:
            # only allow respective Civil/Electrical JE to create assignment.
            if str(hold.designation.name) == "Civil_JE":
                if requisition.department != "civil":
                    return HttpResponse('Unauthorized', status=401)
                sender_design=hold
                receive=HoldsDesignation.objects.get(designation__name="Civil_AE")
                #fdate = datetime.dat
            elif str(hold.designation.name)=="Electrical_JE":
                if requisition.department != "electrical":
                    return HttpResponse('Unauthorized', status=401)
                sender_design=hold
                receive=HoldsDesignation.objects.get(designation__name="Electrical_AE")
                #fdate = datetime.datetime.now().date()
        if not sender_design:
            return HttpResponse('Unauthorized', status=401)

        # Create file in the File table from filetracking module
        requisition.assign_file = File.objects.create(
                uploader=extrainfo,
                #ref_id=ref_id,
                description=requisition.description,
                subject=requisition.title,
                designation=sender_design.designation,
            )
        requisition.save()

        # Send notifications to all concerned users
        office_dean_PnD_notif(request.user, requisition.userid.user, 'request_accepted')
        office_dean_PnD_notif(request.user, request.user, 'assignment_created')
        office_dean_PnD_notif(request.user, receive.working, 'assignment_received')

        # Create tracking row to send the file to Assistant Engg.
        Tracking.objects.create(
                file_id=requisition.assign_file,
                current_id=extrainfo,
                current_design=sender_design,
                receive_design=receive.designation,
                receiver_id=receive.working,
                remarks=description,
                upload_file=upload_file,
            )
    # Handle delete requisition post request
    # Requisitions are "deleted" by hiding them from requisition lists, but are
    # kept in the database for record-keeping reasons.
    elif 'delete_requisition' in request.POST:
        print('delete requisition')
        hold = HoldsDesignation.objects.get(working=user, designation__name__in=deslist)
        if hold:
            req_id=request.POST.get('req_id')
            try:
                req = Requisitions.objects.get(pk=req_id)
                office_dean_PnD_notif(request.user, req.userid.user, 'request_rejected')
                req.tag = 1 # tag = 1 implies the requisition has been deleted
                req.save()
            except Requisitions.DoesNotExist:
                print('ERROR NOT FOUND 409404040', req_id)
        else:
            return HttpResponse('Unauthorized', status=401)

    # Requisitions that *don't* have as assignment
    req=Requisitions.objects.filter(assign_file__isnull=True, tag=0)
    # all requisitions
    all_req=Requisitions.objects.filter(tag=0)
    # list of all requisitions that have an assignment
    assigned_req=list(Requisitions.objects.filter(assign_file__isnull=False).select_related())
    # use list comprehension to create a list of pairs of (tracking file, corresponding requisition)
    # for incoming tracking files
    incoming_files=[(f, _list_find(assigned_req, lambda r: r.assign_file==f.file_id))
            for f in Tracking.objects.filter(receiver_id=user).filter(is_read=False)]
    # use list comprehension to create a list of pairs of (tracking file, corresponding requisition)
    # for outgoing tracking files
    outgoing_files=[(f, _list_find(assigned_req, lambda r: r.assign_file==f.file_id))
            for f in Tracking.objects.filter(current_id__user=user)]
    # history of assignment, list of pair of (requisition, history list)
    assign_history=[(r, _req_history(r)) for r in assigned_req]


    allfiles=None
    sentfiles=None
    files=''
    req_history = []
    # generate a list of requisitions history to render dashboard
    for r in all_req:
        # in case the requisition has an assignment file
        if r.assign_file:
            # Passed has a list of designations through which req. has passed
            # First element is the sender + each tracking's receieve
            # this way all history is generated
            passed = [r.assign_file.designation] + [t.receive_design for t in Tracking.objects.filter(file_id=r.assign_file)]
            # the last date the requisition was sent
            last_date = Tracking.objects.filter(file_id=r.assign_file).last().receive_date
            # map with readable titles from deslist
            passed = [deslist.get(str(d), d) for d in passed]
            req_history.append((r, passed, last_date))
        # in case there is no assignment, that means the history only contains the junior engg. 
        else:
            je = 'Civil_JE' if r.department == 'civil' else 'Electrical_JE'
            passed = [deslist[je]]
            req_history.append((r, passed, r.req_date))
    # sort based on last update, which is the element 2 in the 3-tuple
    req_history.sort(key=lambda t: t[2], reverse=True)
    # list of allowed actions filtered by designation
    for des in designations:
        if des.name == "DeanPnD":
            allowed_actions = ["Forward", "Revert", "Approve", "Reject"]
        elif des.name == "Director":
            allowed_actions = ["Revert", "Approve", "Reject"]
        elif des.name == "Electrical_JE" or des.name == "Civil_JE":
            allowed_actions = ["Forward", "Reject"]
        else:
            allowed_actions = ["Forward", "Revert", "Reject"]

    # Create context to render template
    context = {
            'files':files,
            'req':req,
            'incoming_files': incoming_files,
            'outgoing_files': outgoing_files,
            'assigned_req':assign_history,
            'desig':designations,
            'req_history': req_history,
            'allowed_actions': allowed_actions,
            'deslist': deslist,
    }
    return render(request, "officeModule/officeOfDeanPnD/officeOfDeanPnD.html", context)


@login_required
def submitRequest(request):
    """
        Endpoint used to create requisition
    """
    user = request.user
    extrainfo = ExtraInfo.objects.get(user=user)
    fdate = datetime.datetime.now().date()
    dept=request.POST.get('department')
    building = request.POST.get('building')
    title = request.POST.get('title')
    description = request.POST.get('description')

    request_obj = Requisitions(userid=extrainfo, req_date=fdate,
                               description=description, department=dept, title=title, building=building)
    request_obj.save()
    office_dean_PnD_notif(request.user, request.user, 'requisition_filed')

    # the cake is a lie
    context={}
    return HttpResponseRedirect("/office/officeOfDeanPnD#requisitions")


@login_required
def action(request):
    """
        Endpoint handling actions on assignment.
    """
    # deslist=['Civil_JE','Civil_AE','EE','DeanPnD','Electrical_JE','Electrical_AE']
    user = request.user
    extrainfo = ExtraInfo.objects.get(user=user)
    req_id=request.POST.get('req_id')
    requisition = Requisitions.objects.get(pk=req_id)
    description=request.POST.get('description')
    upload_file=request.FILES.get('estimate')
    track = Tracking.objects.filter(file_id=requisition.assign_file).filter(receiver_id=user).get(is_read=False)

    # current, previous and next Designation and HoldsDesignation found out
    current_design = track.receive_design
    current_hold_design = HoldsDesignation.objects.filter(user=user).get(designation=current_design)
    prev_design = track.current_design.designation
    prev_hold_design = track.current_design

    # This entire thing decides who is the next designation
    if current_design.name == "Civil_JE":
        next_hold_design = HoldsDesignation.objects.get(designation__name="Civil_AE")
    elif current_design.name == "Electrical_JE":
        next_hold_design = HoldsDesignation.objects.get(designation__name="Electrical_AE")
    elif current_design.name == "Civil_AE" or current_design.name == "Electrical_AE":
        next_hold_design = HoldsDesignation.objects.get(designation__name="EE")
    elif current_design.name == "EE":
        if requisition.building == "hostel":
            next_hold_design = HoldsDesignation.objects.get(designation__name="Dean_s")
        else:
            next_hold_design = HoldsDesignation.objects.get(designation__name="DeanPnD")
    elif current_design.name == "Dean_s":
        next_hold_design = HoldsDesignation.objects.get(designation__name="DeanPnD")
    # if estimate greater than 10 lacs, left to discretion of Dean PnD to forward when required
    elif "DeanPnD" in current_design.name: 
        next_hold_design = HoldsDesignation.objects.get(designation__name="Director")

    if 'Forward' in request.POST:
        Tracking.objects.create(
                file_id=requisition.assign_file,
                current_id=extrainfo,
                current_design=current_hold_design,
                receive_design=next_hold_design.designation,
                receiver_id=next_hold_design.working,
                remarks=description,
                upload_file=upload_file,
            )
        print("in forward, old track")
        print(vars(track))
        track.is_read = True
        track.save()
        office_dean_PnD_notif(request.user,next_hold_design.working, 'assignment_received')


    elif 'Revert' in request.POST:
        Tracking.objects.create(
                file_id=requisition.assign_file,
                current_id=extrainfo,
                current_design=current_hold_design,
                receive_design=prev_design,
                receiver_id=prev_hold_design.working,
                remarks=description,
                upload_file=upload_file,
            )
        print("in revert, old track")
        print(vars(track))
        track.is_read = True
        track.save()
        office_dean_PnD_notif(request.user,prev_hold_design.working, 'assignment_reverted')

    elif 'Reject' in request.POST:
        description = description + " This assignment has been rejected. No further changes to this assignment are possible. Please create new requisition if needed."
        Tracking.objects.create(
                file_id=requisition.assign_file,
                current_id=extrainfo,
                current_design=current_hold_design,
                receive_design=None,
                receiver_id=None,
                remarks=description,
                upload_file=upload_file,
                is_read = True,
            )
        track.is_read = True
        track.save()
        office_dean_PnD_notif(request.user,request.user, 'assignment_rejected')

    elif 'Approve' in request.POST:
        description = description + " This assignment has been approved. No further changes to this assignment are possible. Please create new requisition if needed."
        Tracking.objects.create(
                file_id=requisition.assign_file,
                current_id=extrainfo,
                current_design=current_hold_design,
                receive_design=None,
                receiver_id=None,
                remarks=description,
                upload_file=upload_file,
                is_read = True,
            )
        track.is_read = True
        track.save()
        office_dean_PnD_notif(request.user,request.user, 'assignment_approved')

    return HttpResponseRedirect("/office/officeOfDeanPnD/")


@login_required
def frequest(request):
    if request.method=='POST':
        form=Requisitionform(request.POST)
        print("hi")
    else:
        form=Requisitionform()

    return render(request,"officeModule/officeOfDeanPnD/viewRequisitions_content2.html",{'form':form})





def eisModulenew(request):
    project=Project_Registration.objects.all()
    project1=Project_Extension.objects.all()
    project2=Project_Closure.objects.all()
    project3=Project_Reallocation.objects.all()

    design = HoldsDesignation.objects.filter(working=request.user)
    print(design)
    desig=[]
    for i in design:
        desig.append(str(i.designation))

    context = {'project':project, 'project1':project1, 'project2':project2, 'project3':project3, 'desig':desig}

    return render(request, "eisModulenew/profile.html", context)



def officeOfPurchaseOfficr(request):
    return render(request, "officeModule/officeOfPurchaseOfficer/officeOfPurchaseOfficer.html", {})

def admin_reject(request):
    if request.method == "POST":
        marked = request.POST.getlist("selected")

        return HttpResponse("Done!")


def officeOfRegistrar(request):
    view = registrar_create_doc.objects.all()
    view2 = registrar_director_section.objects.all()
    view3 = registrar_establishment_section.objects.all()
    view4 = apply_for_purchase.objects.all()
    view5 = quotations.objects.all()
    general= registrar_general_section.objects.all()
    current_date = datetime.datetime.now()

    context = {"view":view,"view2":view2,"view3":view3,"view4":view4,"view5":view5, "current_date":current_date,"general":general}

    return render(request, "officeModule/officeOfRegistrar/officeOfRegistrar.html", context)


def upload(request):
    print("asdasdasdasd")
    docname = request.POST.get("docname")
    purpose = request.POST.get("purpose")
    description = request.POST.get("description")
    file = request.FILES['upload']
    print(file)
    request = registrar_create_doc(file_name=docname, purpose=purpose, Description=description, file=file)
    request.save()
    print(request)
    return HttpResponseRedirect("/office/officeOfRegistrar/")


@login_required(login_url='/accounts/login')
def officeOfHOD(request):
    pro = Teaching_credits1.objects.filter(tag=0)
    pro1 = Assigned_Teaching_credits.objects.all()

    context = {'pro':pro,'pro1':pro1}
    return render(request, "officeModule/officeOfHOD/officeOfHOD.html", context)


@login_required
def project_register(request):
    user = request.user
    extrainfo = ExtraInfo.objects.get(user=user)
    project_title = request.POST.get('project_title')
    sponsored_agency=request.POST.get('sponsored_agency')
    CO_PI = request.POST.get('copi_name')
   # start_date = datetime.strptime(request.POST.get('start_date'), "%Y-%m-%d")
    start_date = request.POST.get('start_date')
    duration = request.POST.get('duration')
    #duration = datetime.timedelta('duration')
    agreement=request.POST.get('agreement')
    amount_sanctioned = request.POST.get('amount_sanctioned')
    project_type = request.POST.get('project_type')
    remarks=request.POST.get('remarks')
    #fund_recieved_date=datetime.strptime(request.POST.get('fund_recieved_date'), "%Y-%m-%d")
    project_operated = request.POST.get('project_operated')
    fund_recieved_date = request.POST.get('fund_recieved_date')

    request_obj = Project_Registration(PI_id=extrainfo, project_title=project_title,
                               sponsored_agency=sponsored_agency, CO_PI=CO_PI, agreement=agreement,
                               amount_sanctioned=amount_sanctioned, project_type=project_type,
                               remarks=remarks,duration=duration,fund_recieved_date=fund_recieved_date,start_date=start_date)
    request_obj.save()
    context={}
    return render(request,"eisModulenew/profile.html",context)

# Project Registration Table End.................................................................................

def project_registration_permission(request):
    if 'approve' in request.POST:
        id=request.POST.get('id')
        obj=Project_Registration.objects.get(pk=id)
        if obj.DRSPC_response == 'Pending':
            obj.DRSPC_response='Approve'
            obj.save()
    elif 'forward' in request.POST:
        id=request.POST.get('id')
        obj=Project_Registration.objects.get(pk=id)
        if obj.DRSPC_response == 'Pending':
            obj.DRSPC_response='Forward'
            obj.save()
    elif 'reject' in request.POST:
        id=request.POST.get('id')
        obj=Project_Registration.objects.get(pk=id)
        print(obj.DRSPC_response)
        if obj.DRSPC_response == 'Pending':
            obj.DRSPC_response='Disapprove'
            obj.save()
    return HttpResponseRedirect('/office/officeOfDeanRSPC/')


def project_extension_permission(request):
    if 'approve' in request.POST:
        id=request.POST.get('id')
        obj=Project_Extension.objects.get(pk=id)
        if obj.DRSPC_response == 'Pending':
            obj.DRSPC_response='Approve'
            obj.save()
    elif 'forward' in request.POST:
        id=request.POST.get('id')
        obj=Project_Extension.objects.get(pk=id)
        if obj.DRSPC_response == 'Pending':
            obj.DRSPC_response='Forward'
            obj.save()
    elif 'reject' in request.POST:
        id=request.POST.get('id')
        obj=Project_Extension.objects.get(pk=id)
        print(obj.DRSPC_response)
        if obj.DRSPC_response == 'Pending':
            obj.DRSPC_response='Disapprove'
            obj.save()
    return HttpResponseRedirect('/office/officeOfDeanRSPC/')


def project_closure_permission(request):
    if 'approve' in request.POST:
        id=request.POST.get('id')
        obj=Project_Closure.objects.get(pk=id)
        if obj.DRSPC_response == 'Pending':
            print("bb")
            obj.DRSPC_response='Approve'
            obj.save()
    elif 'forward' in request.POST:
        id=request.POST.get('id')
        obj=Project_Closure.objects.get(pk=id)
        if obj.DRSPC_response == 'Pending':
            obj.DRSPC_response='Forward'
            obj.save()
    elif 'reject' in request.POST:
        id=request.POST.get('id')
        obj=Project_Closure.objects.get(pk=id)
        print(obj.DRSPC_response)
        if obj.DRSPC_response == 'Pending':
            obj.DRSPC_response='Disapprove'
            obj.save()
    return HttpResponseRedirect('/office/officeOfDeanRSPC/')



def project_reallocation_permission(request):
    if 'approve' in request.POST:
        id=request.POST.get('id')
        obj=Project_Reallocation.objects.get(pk=id)
        if obj.DRSPC_response == 'Pending':
            print("aa")
            obj.DRSPC_response='Approve'
            obj.save()
    elif 'forward' in request.POST:
        id=request.POST.get('id')
        obj=Project_Reallocation.objects.get(pk=id)
        if obj.DRSPC_response == 'Pending':
            obj.DRSPC_response='Forward'
            obj.save()
    elif 'reject' in request.POST:
        id=request.POST.get('id')
        obj=Project_Reallocation.objects.get(pk=id)
        print(obj.DRSPC_response)
        if obj.DRSPC_response == 'Pending':
            obj.DRSPC_response='Disapprove'
            obj.save()
    return HttpResponseRedirect('/office/officeOfDeanRSPC/')



def hod_action(request):
    if 'forward' in request.POST:
        id=request.POST.get('id')
        obj=Project_Registration.objects.get(pk=id)
        print(obj.HOD_response)
        if obj.HOD_response == 'Pending' or obj.HOD_response == 'pending' :
            obj.HOD_response='Forwarded'
            obj.save()

    return HttpResponseRedirect('/office/eisModulenew/profile/')

def hod_closure(request):
    if 'forward' in request.POST:
        id=request.POST.get('id')
        obj=Project_Closure.objects.get(pk=id)
        print(obj.HOD_response)
        if obj.HOD_response == 'Pending' or obj.HOD_response == 'pending' :
            obj.HOD_response='Forwarded'
            obj.save()

    return HttpResponseRedirect('/office/eisModulenew/profile/')

def hod_extension(request):
    if 'forward' in request.POST:
        id=request.POST.get('id')
        obj=Project_Extension.objects.get(pk=id)
        print(obj.HOD_response)
        if obj.HOD_response == 'Pending' or obj.HOD_response == 'pending' :
            obj.HOD_response='Forwarded'
            obj.save()

    return HttpResponseRedirect('/office/eisModulenew/profile/')

def hod_allocation(request):
    if 'forward' in request.POST:
        id=request.POST.get('id')
        obj=Project_Reallocation.objects.get(pk=id)
        print(obj.HOD_response)
        if obj.HOD_response == 'Pending' or obj.HOD_response == 'pending' :
            obj.HOD_response='Forwarded'
            obj.save()

    return HttpResponseRedirect('/office/eisModulenew/profile/')



def pdf(request,pr_id):
    obj=Project_Registration.objects.get(pk=pr_id)
    return render(request,"officeModule/officeOfDeanRSPC/view_details.html",{"obj":obj})




def genericModule(request):
    context = {}
    return render(request, "officeModule/genericModule/genericModule.html", context)





# Project Closure Table Start .......................................................................................


def project_closure(request):
    project_id = request.POST.get('project_id')
    extrainfo1 = Project_Registration.objects.get(id=project_id)
   # ob = Project_Registration.objects.filter(id = extrainfo1)
    completion_date = request.POST.get('date')
   # extended_duration = ob.duration
    expenses_dues = request.POST.get('committed')
    expenses_dues_description = request.POST.get('remark1')
    payment_dues = request.POST.get('payment')
    payment_dues_description = request.POST.get('remark2')
    salary_dues = request.POST.get('salary')
    salary_dues_description = request.POST.get('remark3')
    advances_dues = request.POST.get('advance')
    advances_description = request.POST.get('remark4')
    others_dues = request.POST.get('other')
    other_dues_description = request.POST.get('remark5')
    overhead_deducted = request.POST.get('overhead')
    overhead_description = request.POST.get('remark6')

    request_obj1 = Project_Closure(project_id=extrainfo1, completion_date=completion_date,
                                    expenses_dues=expenses_dues,expenses_dues_description=expenses_dues_description,
                                    payment_dues=payment_dues,payment_dues_description=payment_dues_description,salary_dues=salary_dues,
                                    salary_dues_description=salary_dues_description,advances_dues=advances_dues,advances_description=advances_description,
                                    others_dues=others_dues,other_dues_description=other_dues_description,overhead_deducted=overhead_deducted,
                                    overhead_description=overhead_description)
    request_obj1.save()
    context={}
    return render(request,"eisModulenew/profile.html",context)



# PROJECT CLOSURE TABLE END HERE .......................................................................................






#PROJECT EXTENSION TABLE START ...........................................................................................



def project_extension(request):
    project_id = request.POST.get('project_id')
    ob = Project_Registration.objects.get(id=project_id)
    date = ob.start_date
    sponser = ob.sponsored_agency
    extended_duration =  request.POST.get('extended_duration')
    extension_detail = request.POST.get('extension_details')

    request_obj2 = Project_Extension(project_id=ob, date=date, extended_duration=extended_duration, extension_details= extension_detail)
    request_obj2.save()
    context={}
    return render(request,"eisModulenew/profile.html",context)


#PROJECT EXTENSION TABLE END ...........................................................................................


def project_reallocation(request):
    project_id = request.POST.get('project_id')
    ob1 = Project_Registration.objects.get(id=project_id)
    date =  request.POST.get('date')
    pfno =  request.POST.get('pfno')
    pbh =   request.POST.get('p_budget_head')
    p_amount =  request.POST.get('p_amount')
    nbh =  request.POST.get('n_budget_head')
    n_amount =  request.POST.get('n_amount')
    reason =  request.POST.get('reason')

    request_obj3 = Project_Reallocation(project_id=ob1, date=date, previous_budget_head=pbh,previous_amount=p_amount,
                                        new_budget_head=nbh,new_amount=n_amount,transfer_reason=reason,pf_no=pfno)
    request_obj3.save()
    print("sbhaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaabbbbhaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
    context={}
    return render(request,"eisModulenew/profile.html",context)





@login_required
def teaching_form(request):
    roll_no=request.POST.get('roll_no')
    name=request.POST.get('name')
    programme=request.POST.get('programme')
    branch=request.POST.get('branch')
    course1=request.POST.get('course1')
    course2=request.POST.get('course2')
    course3=request.POST.get('course3')

    request_obj = Teaching_credits1(roll_no=roll_no,name=name, programme=programme, branch=branch,
                                     course1=course1, course2=course2, course3=course3)
    print("===================================================================")
    request_obj.save()
    context={}
    return render(request,"officeModule/officeOfHOD/tab4content4.html",context)

@login_required
def hod_work(request):
    roll_no=request.POST.get('roll_no')
    tc = Teaching_credits1.objects.get(roll_no=roll_no)
    assigned_course=request.POST.get('assigned_course')
    request_obj1 = Assigned_Teaching_credits(roll_no=tc,assigned_course=assigned_course)
    request_obj1.save()
    tc.tag=1
    tc.save()
    context={}
    return render(request,"officeModule/officeOfHOD/tab4content4.html",context)
    """return HttpResponseRedirect('')"""
    """return render(request,"officeModule/officeOfHOD/tab4content1.html",context)"""



def genericModule(request):
    context = {}

    return render(request, "ofricModule/genericModule.html", context)



def newordershod(request):
    print("hello2")
    #this one creates and stores the data in django forms
    print("new ord caled")
    if request.method=='POST':
        objid = request.POST.get('id')
        print(objid)
        #find the instance with this objid and set its hod_approve_bit to 1
        try:
            obj = apply_for_purchase.objects.get(id = objid)
            obj.HOD_approve_tag = 1
            obj.director_approve_tag = 0
            obj.save()
            print("work done")
            str = "order with id "+ objid +" has been approved by you"
            messages.info(request,str)
            #render()
        except apply_for_purchase.DoesNotExist:
            print("model not exists")
    return HttpResponse("you are the best ")

def newordersregistrar(request):
    print("hello2")
    #this one creates and stores the data in django forms
    print("new ord caled")
    if request.method=='POST':
        objid = request.POST.get('id')
        print(objid)
        #find the instance with this objid and set its hod_approve_bit to 1
        try:
            obj = apply_for_purchase.objects.get(id = objid)
            obj.registrar_approve_tag = 1
            obj.director_approve_tag = 1
            obj.save()
            print("work done")
            str = "order with id "+ objid +" has been approved by you"
            messages.info(request,str)
            return HttpResponse('work is being done')
        except apply_for_purchase.DoesNotExist:
            print("model not exists")
    return HttpResponse("you are the best ")

def newordersregistrar2(request):
    print("hello2")
    #this one creates and stores the data in django forms
    print("new ord caled")
    if request.method=='POST':
        objid = request.POST.get('id')
        print(objid)
        #find the instance with this objid and set its hod_approve_bit to 1
        try:
            obj = apply_for_purchase.objects.get(id = objid)
            obj.registrar_approve_tag = 1
            obj.save()
            print("work done")
            str = "order with id "+ objid +" has been approved by you"
            messages.info(request,str)
            return HttpResponse('work is being done')
        except apply_for_purchase.DoesNotExist:
            print("model not exists")
    return HttpResponse("you are the best ")


def newordersdirector(request):
    print("hello2")
    #this one creates and stores the data in django forms
    print("new ord caled")
    if request.method=='POST':
        objid = request.POST.get('id')
        print(objid)
        #find the instance with this objid and set its hod_approve_bit to 1
        try:
            obj = apply_for_purchase.objects.get(id = objid)
            obj.director_approve_tag = 1
            obj.save()
            print("work done")
            str = "order with id "+ objid +" has been approved by you"
            messages.info(request,str)
            return HttpResponse('work is being done')
        except apply_for_purchase.DoesNotExist:
            print("model not exists")
    return HttpResponse("you are the best ")

#on operation
def newordersdirectorview(request):
    print("metoo")
    #return HttpResponse("pis of")
    if request.method=='POST':
        objid = request.POST.get('id')
        print(objid)
    try:
        obj = apply_for_purchase.objects.get(id = objid)
        context ={"data":obj}
        print(context)
        return HttpResponse("abhi iska template nahi bana hai")
    except apply_for_purchase.DoesNotExist:
        print("model not exists")
    return render(request, "officeModule/officeOfPurchaseOfficer/viewordersdirector.html",context=context)



def newordersPO(request):
    if request.method=='POST':
        objid = request.POST.get('id')
        print(objid)
        try:
            obj = apply_for_purchase.objects.get(id = objid)
            obj.gem_tag=-1
            obj.save()
        except apply_for_purchase.DoesNotExist:
            print("model not exists")
    return HttpResponse("you are the best ")

def newordersPOonGem(request):
    if request.method=='POST':
        objid = request.POST.get('id')
        print(objid)
        try:
            obj = apply_for_purchase.objects.get(id = objid)
            obj.gem_tag=1
            obj.save()
        except apply_for_purchase.DoesNotExist:
            print("model not exists")
    return HttpResponse("you are the best ")



@login_required

def apply_purchase(request):
    print("hello")
    #
#    user = get_object_or_404(User,username=request.user.username)
#    user=ExtraInfo.objects.get(user=user)
    current_user = get_object_or_404(User, username=request.user.username)
    #print(current_user)
    user_details = ExtraInfo.objects.all().filter(user=current_user).first()
    #print(user_details)
    user_type = HoldsDesignation.objects.all().filter(user=current_user).first()
    #print(user_type)
    usertype=str.split(str(user_type))
    #print(usertype)
    # Academics Admin Check
    user=usertype[0]
    #desig_id = Designation.objects.all().filter(name='Faculty')
    #print(desig_id)
    #print ("yaha se")
    #print(user)
    #print(user_type)
    # user = request.user
    # user = User.objects.get(id=1).extrainfo
    #user=request.user
    if(user == "student"):
        return HttpResponse('You are not authorised to view this page')
    # user=ExtraInfo.objects.get(id=user)
    #print(hello)
    if request.method == 'POST':
        item_name=request.POST.get('item_name')
        quantity=request.POST.get('quantity')
        expected_cost=int(request.POST.get('expected_cost'))

        if  expected_cost >=25000 and expected_cost <= 250000 :
            local_comm_mem1_id=request.POST.get('local_comm_mem1_id')
            local_comm_mem2_id=request.POST.get('local_comm_mem2_id')
            local_comm_mem3_id=request.POST.get('local_comm_mem3_id')

        nature_of_item1= 1 if request.POST.get('nature_of_item1') == 'on' else 0
        nature_of_item2= 1 if request.POST.get('nature_of_item2') == 'on' else 0

        # extra = ExtraInfo.objects.all()
        # extraInfo = ExtraInfo.objects.get(id=inspecting_authority_id)

        purpose=request.POST.get('purpose')
        # budgetary_head_id=request.POST.get('budgetary_head_id')
        # inspecting_authority_id=request.POST.get('inspecting_authority_id')
        expected_purchase_date=request.POST.get('expected_purchase_date')
        # print(expected_purchase_date+"...........................")

    # xyz=apply_for_purchase(indentor_name=name,)
    # xyz.save()

        #print("hello1")

        a = apply_for_purchase.objects.create(
                item_name=item_name,
                quantity=int(quantity),
                expected_cost=expected_cost,
                nature_of_item1=nature_of_item1,
                nature_of_item2=nature_of_item2,
                purpose=purpose,
                # budgetary_head_id = budgetary_head_id,
                # inspecting_authority_id=inspecting_authority_id,
                expected_purchase_date= expected_purchase_date,
                indentor_name=user_details,

        )
        a.save()
        print("yahan tak toh pahunch gaya mai")
        messages.info(request, 'order placed successfully')
        if  expected_cost >=25000 and expected_cost <= 250000 :
            b = purchase_commitee.objects.create(

            local_comm_mem1_id=local_comm_mem1_id,
            local_comm_mem2_id=local_comm_mem2_id,
            local_comm_mem3_id=local_comm_mem3_id,
            )
            b.save()



            #right now its hard coded for pkhanna o/w  use utype : utype for context in both render
        #return render(request, "officeModule/officeOfPurchaseOfficer/officeOfPurchaseOfficer.html",{'utype':2})
        return HttpResponseRedirect('/office/officeOfPurchaseOfficer/')
    else:
        return HttpResponseRedirect('/office/officeOfPurchaseOfficer/')





@login_required

def add_items(request):
    current_user = get_object_or_404(User, username=request.user.username)
    print(current_user)
    user_details = ExtraInfo.objects.all().filter(user=current_user).first()
    print(user_details)
    user_type = HoldsDesignation.objects.all().filter(user=current_user).first()
    print(user_type)
    usertype=str.split(str(user_type))
    print(usertype)
    # Academics Admin Check
    user=usertype[0]
    #desig_id = Designation.objects.all().filter(name='Faculty')
    quantity=0
    #print(desig_id)
    print ("yaha se")
    print(user)
    if(user == "student"):
        return HttpResponse('You are not authorised to view this page')
    if request.method == 'POST':
        item_name=request.POST.get('item_name')
        nature_of_item2= 1 if request.POST.get('nature_of_item2') == 'on' else 0
        quantity=request.POST.get('quant')
        order_id=request.POST.get('order_id')
        print(quantity)
        a = stock.objects.create(
            item_type=nature_of_item2,
            item_name=item_name,
            quantity=quantity,
        )
        a.save()
        messages.info(request, 'item added in inventory successfully')
        return render(request, "officeModule/officeOfPurchaseOfficer/manageStore_content2.html",{})
    else:
        return render(request, "officeModule/officeOfPurchaseOfficer/manageStore_content2.html",{})



@login_required

def view_items(request):
    return HttpResponse(1)


def submit(request):
    context = {}

    return render(request, "officeModule/officeOfHOD/view_details.html", context)


@login_required
def after_purchase(request):
    if request.method == 'POST':
        '''if "submit" in request.POST:'''
        file_no=request.POST.get('file_no')
        amount=request.POST.get('amount')
        invoice=request.POST.get('invoice')
        apply_for_purchase.objects.filter(id=file_no).update(amount=amount, invoice=invoice)

        return render(request, "officeModule/officeOfPurchaseOfficer/after_purchase.html",{})
    else:
        return render(request, "officeModule/officeOfPurchaseOfficer/after_purchase.html",{})



def officeOfPurchaseOfficer(request):
    context={}
    current_user = get_object_or_404(User, username=request.user.username)
    #print(current_user)
    user_details = ExtraInfo.objects.all().filter(user=current_user).first()
    #print(user_details)
    user_type = HoldsDesignation.objects.all().filter(user=current_user).first()
    #print(user_type)
    usertype=str.split(str(user_type))
    print(usertype)
    # Academics Admin Check
    user_type=None
    user = usertype[2]

    if(user == "student"):
        return HttpResponse('You are not authorised to view this page')
    if(len(usertype)>3):
        user_type=usertype[2]+usertype[3]
    elif(len(usertype)>=2):
        user_type = usertype[2]
    print(user_type)
    p = None
    q = None
    ph = None
    #print ("yaha se")
    #print(user_type)
    #use user_type to check the designation of actor
    #utype is for rendering tags (templates)
    utype=0#this is for manage store and vendors
    utype2=0#this is for orders tag
    #but yahan par bhi divide as utype21 utype22(just a thought for.....)
    utype3=0#this is for indent forms
    utype4=0#this is for purchase history

    per_user=str(current_user)
    if(user_type=="DeputyRegistrar" or user_type=="Registrar" or user_type=="PurchaseOfficer"):
        utype=1
    #elif(user_type=="HOD(ME)" or user_type=="HOD(ECE)" or user_type=="CSE HOD" or user_type=="HOD"):
    #bug was that pkhanna was being recognized as associate professor not HOD
    if(per_user=="pkhanna" or user_type=="DeputyRegistrar" or user_type=="Registrar" or user_type=="HOD" or user_type=="PurchaseOfficer" or user_type =="Director" or user_type=="director"):
        utype2=1
        #print("hard code working hai yahan tak for HOD designation")

    if(user_type == "AssociateProfessor" or user_type == "AssistantProfessor" or user_type=="HOD" or user_type=="Director" or user_type=="director"):#give more such equivalent designations
        utype3=1
        #print("recognized actor assoc prof")


    #print("yahan tak sab sahi")

    if request.method == 'POST':

        if "submit" in request.POST:

            vendor_name=request.POST['vendor_name']
            vendor_item=request.POST['vendor_item']
            vendor_address=request.POST['vendor_address']

            vendor.objects.create(
                vendor_name=vendor_name,
                vendor_item=vendor_item,
                vendor_address=vendor_address,
            )
            messages.info(request, 'vendor added successfully')
            return render(request, "officeModule/officeOfPurchaseOfficer/officeOfPurchaseOfficer.html",{})


        elif "new_orders" in request.POST:
            #note when not in hard code, pkhanna to be replaced  by str(current_user)
            #render appropritate templates as per the actor like approvalHOD2 or approvalRegistrar2 etc
            #this is working through user_type not utype
            if(user_type=="HOD" or per_user=="pkhanna"):
                alldata = apply_for_purchase.objects.filter(HOD_approve_tag=0).order_by('-id')
                context={'alldata':alldata}
                print(context)
                return render(request, "officeModule/officeOfPurchaseOfficer/approvalHOD2.html",context=context)

            elif(user_type=="DeputyRegistrar" or user_type=="Registrar" or per_user=="swapnali"):
                alldata = apply_for_purchase.objects.filter(HOD_approve_tag=1,registrar_approve_tag=0).order_by('-id')
                #alldata2 = apply_for_purchase.objects.filter(HOD_approve_tag=1,registrar_approve_tag=0,expected_cost__gte = 50001)
                context = {'alldata':alldata,'des':user_type}
                return render(request, "officeModule/officeOfPurchaseOfficer/approvalRegistrar.html",context=context)

            elif(user_type=="director" or user_type=="Director"):
                #alldata = apply_for_purchase.objects.filter(HOD_approve_tag=1,registrar_approve_tag=1,expected_cost__gte = 50001)
                alldata = apply_for_purchase.objects.filter(expected_cost__gte = 50001,director_approve_tag=0).order_by('-id')
                print(alldata)
                context = {'alldata':alldata,'des':user_type}
                return render(request, "officeModule/officeOfPurchaseOfficer/approvaldirector.html",context=context)

            elif(user_type=="purchaseofficer" or user_type=="PurchaseOfficer"):
                print("entered purchase officer section")
                alldata = apply_for_purchase.objects.filter(director_approve_tag=1,gem_tag=0).order_by('-id')
                #alldata2 = apply_for_purchase.objects.filter(HOD_approve_tag=1,registrar_approve_tag=1,expected_cost__lte = 50000)
                #context = {'alldata':alldata,'alldata2':alldata2}SS

                context = {'alldata':alldata,'des':user_type}
                #print("data 0",context)
                return render(request, "officeModule/officeOfPurchaseOfficer/approvalpurchaseofficer.html",context=context)



        elif "approved_orders" in request.POST:
            if(user_type=="HOD" or per_user=="pkhanna"):
                alldata = apply_for_purchase.objects.filter(HOD_approve_tag=1).order_by('-id')
                context={'alldata':alldata}
                #print(context)
                return render(request, "officeModule/officeOfPurchaseOfficer/approvedHOD.html",context=context)

            elif(user_type=="DeputyRegistrar" or user_type=="Registrar" or per_user=="swapnali"):
                alldata = apply_for_purchase.objects.filter(registrar_approve_tag=1,expected_cost__lte = 50000).order_by('-id')
                context = {'alldata':alldata,'des':user_type}
                return render(request, "officeModule/officeOfPurchaseOfficer/approvedRegistrar.html",context=context)

            elif(user_type=="director" or user_type=="Director"):
                #alldata = apply_for_purchase.objects.filter(HOD_approve_tag=1,registrar_approve_tag=1,expected_cost__gte = 50001)
                alldata = apply_for_purchase.objects.filter(expected_cost__gte = 50001,director_approve_tag=1).order_by('-id')
                #print(alldata)
                context = {'alldata':alldata}
                return render(request, "officeModule/officeOfPurchaseOfficer/approvedDirector.html",context=context)

            #make the templates as per the actors




        elif "checked_orders" in request.POST:
            if(user_type == "PurchaseOfficer" or user_type == "purchseofficer"):
                #print("in checked orders")
                alldata = apply_for_purchase.objects.filter(director_approve_tag=1).exclude(gem_tag=0)
                context = {'alldata':alldata,'des':user_type}
                return render(request, "officeModule/officeOfPurchaseOfficer/checkedpurchaseofficer.html",context=context)

        elif "forwarded_orders" in request.POST:
            if(user_type == "Registrar" or user_type == "DeputyRegistrar"):
                #print("in checked orders")
                alldata = apply_for_purchase.objects.filter(expected_cost__gte = 50001,director_approve_tag=0).order_by('-id')
                context = {'alldata':alldata,'des':user_type}

                return render(request, "officeModule/officeOfPurchaseOfficer/forwardedRegistrar.html",context=context)


        elif "store" in request.POST:

            item_type=request.POST.get('item_type')
            item_name=request.POST.get('item_name')
            quantity=request.POST.get('qunatity')
            str2 = " "
            it = " "
            a = stock.objects.create(
                item_type=item_type,
                item_name=item_name,
                quantity=quantity,
            )
            a.save()
            if(item_type==0):
                it="consumable"
            else:
                it="non-consumable"
            str2 = "item " + item_name + "of type " + it + " has been added to the store"
            messages.info(request,str2)

        elif "manage_store" in request.POST:
            return render(request, "officeModule/officeOfPurchaseOfficer/manageStore_content2.html")

        elif "view_store" in request.POST:
            q=stock.objects.all()
            return render(request, "officeModule/officeOfPurchaseOfficer/manageStore_content1.html",{"q":q})
            #return HttpResponse(1)

        elif "item_search" in request.POST:
            srch = request.POST['item_name']
            print("this is the itemset")
            print(srch)
            #match = stock.objects.filter(Q(item_name__icontains=srch))
            match = stock.objects.filter(item_name=srch)
            print(match)
            return render(request, "officeModule/officeOfPurchaseOfficer/officeOfPurchaseOfficer.html",{'match':match})

        elif "vendor_search" in request.POST:
            sr = request.POST['item']
            matchv = vendor.objects.filter(Q(vendor_item__icontains=sr))
            return render(request, "officeModule/officeOfPurchaseOfficer/officeOfPurchaseOfficer.html",{'matchv':matchv})

        elif "viewhistory" in request.POST:
            alldata = apply_for_purchase.objects.filter(indentor_name = user_details)
            print(alldata)
            return render(request, "officeModule/officeOfPurchaseOfficer/purchaseHistory_content1.html",{'alldata':alldata})

        elif "viewstatus" in request.POST:
            alldata = apply_for_purchase.objects.filter(indentor_name = user_details)
            print(alldata)
            return render(request, "officeModule/officeOfPurchaseOfficer/purchaseHistory_content2.html",{'alldata':alldata})


        elif "purchase_search" in request.POST:
            pr = request.POST['file']
            phmatch = apply_for_purchase.objects.filter(Q(id=pr))
            return render(request, "officeModule/officeOfPurchaseOfficer/officeOfPurchaseOfficer.html",{'phmatch':phmatch})
        '''elif "delete_item" in request.POST:
            a = request.POST.getlist('box')
            for i in range(len(a)):
                k = stock.objects.get(id = a[i])
                k.delete()
            return HttpResponse("successflly deleted item")'''

    else:
        #this is the manage store and vendors section
        p=vendor.objects.all()
        q=stock.objects.all()
        ph=apply_for_purchase.objects.all()

    return render(request, "officeModule/officeOfPurchaseOfficer/officeOfPurchaseOfficer.html",{'p':p,'q':q,'ph':ph,'utype':utype,'utype2':utype2,'utype3':utype3,'des':user_type})

def delete_item(request,id):
    #template = 'officemodule/officeOfPurchaseOfficer/manageStore_content1.html'
    print("reached delete_item")
    if request.method=='POST':
        objid = request.POST.get('id')
        print(objid)
        item = get_object_or_404(stock,id=id)
        item.delete()


    return HttpResponse("Deleted successfully")

def delete_vendor(request,id):
    #template = 'officemodule/officeOfPurchaseOfficerr/manageStore_content1.html'
    print(">>>>>>>")
    print(id)
    ven = get_object_or_404(vendor,id=id)
    ven.delete()
    return HttpResponse("Deleted successfully")

def edit_vendor(request,id):


    p= get_object_or_404(vendor,id=id)
    context={
        'p' : p
    }
    return render(request,"officeModule/officeOfPurchaseOfficer/edit.html",context)
    return HttpResponseRedirect('/office/officeOfPurchaseOfficer')

def edit(request):

    ID=request.POST.get('vendor_id')
    name=request.POST.get('vendor_name')
    item=request.POST.get('vendor_item')
    add=request.POST.get('vendor_address')
    d=vendor(id=ID,vendor_name=name,vendor_item=item,vendor_address=add)
    d.save()
    return HttpResponseRedirect('/office/officeOfPurchaseOfficer')

def edit_item(request,id):


    p= get_object_or_404(stock,id=id)
    context={
        'p' : p
    }
    return render(request,"officeModule/officeOfPurchaseOfficer/edit1.html",context)
    return HttpResponseRedirect('/office/officeOfPurchaseOfficer')

def edit1(request):

    ID=request.POST.get('item_id')
    name=request.POST.get('item_name')
    add=request.POST.get('quantity')
    d=stock(id=ID,item_name=name,quantity=add)
    d.save()
    return HttpResponseRedirect('/office/officeOfPurchaseOfficer')


def directorOffice(request):
    faculty = Faculty.objects.all()
    student = Student.objects.all()
    facultysearch = " "
    if 'search' in request.POST:
        facult = request.POST.get('faculty')
        facultysearch = Faculty.objects.get(id=facult)

    studentsearch = " "

    if 'search_std' in request.POST:
        stud = request.POST.get('student')
        studentsearch = Student.objects.get(id=stud)

    context = {"faculty": faculty, "fsearch": facultysearch, "student": student, "ssearch": studentsearch}

    return render(request, "officeModule/directorOffice/directorOffice.html", context)


def appoint(request):
    print('there')
    purpose = request.POST.get('purpose')
    venue = request.POST.get('venue')
    adate = request.POST.get('adate')
    adate = adate.replace(",", "")
    print(adate)
    adate = str(datetime.datetime.strptime(adate, '%B %d %Y'))[:10]
    print(adate)
    # if (adate==""):
    #     adate = None
    # print(datetime.date.today())
    member = request.POST.get('member')
    print(purpose, venue, adate, member)
    print('here 1')
    meetobj = Meeting(venue=venue, agenda=purpose, date=adate)
    meetobj.save()
    print('here 2')
    user = User.objects.get(username=member)
    info = ExtraInfo.objects.get(user=user)
    mem = Faculty.objects.get(id=info)
    print('here 3')
    print(mem)
    # meeting = Meeting.objects.get(id=meetobj.id)
    # print(meeting)
    appointobj = Member(member_id=mem, meeting_id=meetobj)
    print(appointobj)
    appointobj.save()

    return HttpResponseRedirect("/office/directorOffice/")


def meeting(request):
    print("hi")
    agenda = request.POST.get('agenda')
    venue = request.POST.get('venue')
    adate = request.POST.get('adate')
    adate = adate.replace(",", "")
    print(adate)
    adate = str(datetime.datetime.strptime(adate, '%B %d %Y'))[:10]
    print(adate)
    member = request.POST.get('member')
    print(agenda, venue, adate, member)
    meetobj = Meeting(venue=venue, agenda=agenda, date=adate)
    meetobj.save()
    print('here 4')
    user = User.objects.get(username=member)
    info = ExtraInfo.objects.get(user=user)
    mem = Faculty.objects.get(id=info)
    print('here 5')
    print(mem)
    meetingobj = Member(member_id=mem, meeting_id=meetobj)
    print(meetingobj)
    meetingobj.save()

    return HttpResponseRedirect("/office/directorOffice/")


def profile(request):
    facult = request.POST.get('faculty')
    faculty = Faculty.objects.get(id=facult)
    # Id=request.POST.get('id')
    #    member=request.POST.get('member')
    #    Designation=request.POST.get('designation')
    #    Department=request.POST.get('dept')
    #    print(Id,member,Designation,Department)
    #    user = User.objects.get(username=member)
    #    info = ExtraInfo.objects.get(user=user)
    #    mem = Faculty.objects.get(id = info)

    return HttpResponseRedirect("/office/directorOffice/")


def officeOfDeanAcademics(request):
    student=Student.objects.all();
    instructor=Instructor.objects.all();
    spi=Spi.objects.all();
    grades=Grades.objects.all();
    course=Course.objects.all();
    thesis=Thesis.objects.all();
    minutes=Meeting.objects.all().filter(minutes_file="");
    final_minutes=Meeting.objects.all().exclude(minutes_file="");
    hall_allotment=hostel_allotment.objects.all();
    assistantship=Assistantship.objects.all();
    mcm=Mcm.objects.all();
    designation = HoldsDesignation.objects.all().filter(working=request.user)
    all_designation=[]
    for i in designation:
        all_designation.append(str(i.designation))




    context = {'student':student,
                'instructor':instructor,
                'assistantship':assistantship,
                #'hall': Constants.HALL_NO,
                'hall_allotment':hall_allotment,
                'mcm':mcm,
                'thesis':thesis,
                'meetingMinutes':minutes,
                'final_minutes':final_minutes,
                'all_desig':all_designation,}

    return render(request, "officeModule/officeOfDeanAcademics/officeOfDeanAcademics.html", context)

def assistantship(request):
    # print(request.POST.getlist('check'))
    ob=Assistantship.objects.all()
    # print(id[0])
    context = {'ob':ob}
    return HttpResponseRedirect('/office/officeOfDeanAcademics')


def init_assistantship(request):
    title= request.POST.get('title')
    date = request.POST.get('date')
    Time = request.POST.get('time')
    Venue = request.POST.get('venue')
    Agenda = request.POST.get('Agenda')
    p=Meeting(title=title,venue=Venue,date=date,time=Time,agenda=Agenda);
    p.save()
    return HttpResponseRedirect('/office/officeOfDeanAcademics')

def scholarshipform(request):
    file=request.FILES['hostel_file']
    hall_no=request.POST.get('hall_no')
    #description= request.POST.get('description')
    p=hostel_allotment(allotment_file=file,hall_no=hall_no)
    p.save()
    return HttpResponseRedirect('/office/officeOfDeanAcademics')

def formsubmit(request):
    a = request.POST.get('example');
    comment = request.POST.get('comment');
    obj = Assistantship.objects.get(pk=a)
    if "approve" in request.POST:
        obj.action=1
        obj.comments=comment
        obj.save()
    elif "reject" in request.POST:
        obj.action=2
        obj.comments=comment
        obj.save()

    return HttpResponseRedirect('/office/officeOfDeanAcademics')



    # elif "reject" in request.POST:

def scholarship(request):

    return HttpResponse('')

def courses(request):

    return HttpResponse('')

def applications(request):

    return HttpResponse('')

def semresults(request):

    return HttpResponse('')

def thesis(request):

    return HttpResponse('')
