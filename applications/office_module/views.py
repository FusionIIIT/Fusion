import datetime
from datetime import date, datetime

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from applications.academic_procedures.models import Thesis
from applications.globals.models import (Designation, ExtraInfo,
                                         HoldsDesignation, User)
from applications.scholarships.models import Mcm

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

@login_required
def officeOfDeanPnD(request):
    user = request.user
    extrainfo = ExtraInfo.objects.get(user=user)
    requisitions=Requisitions.objects.filter(userid=extrainfo)
    holds=HoldsDesignation.objects.filter(user=user)
    civilreq=Requisitions.objects.filter(department='civil',assign_title=None)
    electricalreq = Requisitions.objects.filter(department='electrical')
    req=Requisitions.objects.all()
    deslist=['Civil_JE','Civil_AE','EE','DeanPnD','Electrical_JE','Electrical_AE']
    deslist1=['Civil_JE','Civil_AE']
    design=HoldsDesignation.objects.filter(working=user)
    desig=[]
    for i in design:
        desig.append(str(i.designation))
    print(desig)

    if 'createassign' in request.POST:
        id=request.POST.get('req_id')
        obj = Requisitions.objects.get(id=id)
        obj.assign_title = request.POST.get('title')
        obj.assign_description = request.POST.get('description')
        obj.estimate=request.FILES['estimate']
        print(obj.estimate)
        obj.assign_date=timezone.now()
        obj.save()

        for hold in holds:
            if str(hold.designation.name) in deslist1:
                if str(hold.designation.name) == "Civil_JE":
                    receive=HoldsDesignation.objects.get(designation__name="Civil_AE")
                    sent=HoldsDesignation.objects.get(designation__name="Civil_JE")
                    fdate = datetime.now().date()

                elif str(hold.designation.name)=="Electrical_JE":
                    receive=ExtraInfo.objects.get(designation__name="Electrical_AE")
                    fdate = datetime.now().date()
        moveobj=Filemovement(rid=obj,sentby=sent,receivedby=receive)
        moveobj.save()



    if 'asearch' in request.POST:
        check=request.POST.get('status')
        dept=request.POST.get('dept')
        if dept=="all":
            req=Requisitions.objects.all()
        elif dept=="civil":
            req=Requisitions.objects.filter(department='civil')
        elif dept=="electrical":
            req=Requisitions.objects.filter(department='electrical')
        if check=="1":
            req=req
        elif check=="2":
            req=req.filter(tag=0)
        elif check=="3":
            req=req.filter(tag=1)

    sentfiles=''
    for des in design:
        if str(des.designation) in deslist:
            sentfiles=Filemovement.objects.filter(Q(sentby=des)|Q(actionby_receiver='accept'))

    print(sentfiles)

    files=''
    for des in design:
        if str(des.designation) in deslist:
            files=Filemovement.objects.filter(receivedby=des,actionby_receiver='')
    allfiles=Filemovement.objects.all()

    context = {'civilreq':civilreq,'electricalreq':electricalreq,'files':files,'req':req,'sentfiles':sentfiles,'allfiles':allfiles,'requisitions':requisitions,'desig':desig}
    return render(request, "officeModule/officeOfDeanPnD/officeOfDeanPnD.html", context)


@login_required
def submitRequest(request):

    user = request.user
    extrainfo = ExtraInfo.objects.get(user=user)
    fdate = datetime.now().date()
    dept=request.POST.get('department')
    building = request.POST.get('building')
    title = request.POST.get('title')
    description = request.POST.get('description')

    request_obj = Requisitions(userid=extrainfo, req_date=fdate,
                               description=description, department=dept, title=title, building=building)
    request_obj.save()
    context={}
    return HttpResponseRedirect("/office/officeOfDeanPnD")


@login_required
def action(request):
    deslist=['Civil_JE','Civil_AE','EE','DeanPnD','Electrical_JE','Electrical_AE']
    user = request.user
    extrainfo = ExtraInfo.objects.get(user=user)
    design=HoldsDesignation.objects.filter(working=user)
    fdate = datetime.datetime.now().date()
    id=request.POST.get('select')
    fileobj=Filemovement.objects.get(pk=id)
    remarks=request.POST.get('remarks')
    sentby=''
    for des in deslist:
        try:
            sentby=HoldsDesignation.objects.get(working=user,designation__name=des)
        except :
            sentby=None

        if sentby :
            print(sentby)
            i=Designation.objects.get(name=des)
            i=i.id
            break

    reqobj=fileobj.rid

    if 'forward' in request.POST:
        fileobj.actionby_receiver="forward"
        fileobj.save()
        receive=HoldsDesignation.objects.get(designation__id=i+1)
        moveobj=Filemovement(rid=reqobj,sentby=sentby,receivedby=receive,date=fdate,remarks=remarks)
        moveobj.save()

    elif 'reject' in request.POST:
        fileobj.actionby_receiver="reject"
        fileobj.save()
        reqobj.tag=1
        reqobj.save()

    elif 'revert' in request.POST:
        fileobj.actionby_receiver="revert"
        fileobj.save()

        #   file=Requisitions.objects.get(pk=id)
        receive=HoldsDesignation.objects.get(designation__id=i-1)
        moveobj=Filemovement(rid=reqobj,sentby=sentby,receivedby=receive,date=fdate,remarks=remarks)
        moveobj.save()

    elif 'approve' in request.POST:
        fileobj.actionby_receiver="accept"
        fileobj.save()
        print(">>>>>>>>>>>>>")
        reqobj.tag=1
        reqobj.save()

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


@login_required
def apply_purchase(request):

    #
    # name=ExtraInfo.objects.get(user=user)

    # user = request.user
    # user = User.objects.get(id=1).extrainfo
    user=request.user.extrainfo
    # user=ExtraInfo.objects.get(id=user)

    if request.method == 'POST':
        '''if "submit" in request.POST:'''
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
                indentor_name=user,

        )
        a.save()
        if  expected_cost >=25000 and expected_cost <= 250000 :
            b = purchase_commitee.objects.create(

            local_comm_mem1_id=local_comm_mem1_id,
            local_comm_mem2_id=local_comm_mem2_id,
            local_comm_mem3_id=local_comm_mem3_id,
            )
            b.save()




        return render(request, "officeModule/officeOfPurchaseOfficer/officeOfPurchaseOfficer.html",{})
    else:
        return render(request, "officeModule/officeOfPurchaseOfficer/officeOfPurchaseOfficer.html",{})


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


@login_required
def officeOfPurchaseOfficer(request):
    context={}
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
            return HttpResponse("successflly added vendor")

        elif "store" in request.POST:
            item_type=request.POST.get('item_type')
            item_name=request.POST.get('item_name')
            quantity=request.POST.get('qunatity')

            stock.objects.create(
                item_type=item_type,
                item_name=item_name,
                quantity=quantity,
            )
            return HttpResponse("successflly added item")
        elif "item_search" in request.POST:
            srch = request.POST['item_name']
            match = stock.objects.filter(Q(item_name__icontains=srch))
            return render(request, "officeModule/officeOfPurchaseOfficer/officeOfPurchaseOfficer.html",{'match':match})
        elif "vendor_search" in request.POST:
            sr = request.POST['item']
            matchv = vendor.objects.filter(Q(vendor_item__icontains=sr))
            return render(request, "officeModule/officeOfPurchaseOfficer/officeOfPurchaseOfficer.html",{'matchv':matchv})
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
        p=vendor.objects.all()
        q=stock.objects.all()
        ph=apply_for_purchase.objects.all()
    return render(request, "officeModule/officeOfPurchaseOfficer/officeOfPurchaseOfficer.html",{'p':p,'q':q,'ph':ph})

def delete_item(request,id):
    #template = 'officemodule/officeOfPurchaseOfficer/manageStore_content1.html'
    print(">>>>>>>")
    print(id)
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
