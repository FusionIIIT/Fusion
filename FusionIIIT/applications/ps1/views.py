from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from applications.filetracking.sdk.methods import *
from applications.ps1.models import IndentFile,StockEntry,StockItem,StockTransfer
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation
from django.template.defaulttags import csrf_token
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.core import serializers
from django.contrib.auth.models import User
from timeit import default_timer as time
from notification.views import office_module_notif
from django.utils import timezone
from datetime import datetime
from applications.globals.models import DepartmentInfo
import re
import json

from django.db.models import Q,Count

dept_admin_to_dept = {
    "deptadmin_cse": "CSE",
    "deptadmin_ece": "ECE",
    "deptadmin_me": "ME",
    "deptadmin_sm": "SM",
    "deptadmin_design": "Design",
    "deptadmin_liberalarts": "Liberal Arts",
    "deptadmin_ns": "Natural Science",
}

dept_admin_design = ["deptadmin_cse", "deptadmin_ece", "deptadmin_me","deptadmin_sm", "deptadmin_design", "deptadmin_liberalarts","deptadmin_ns" ]


@login_required(login_url = "/accounts/login/")
def ps1(request):
    des_obj = HoldsDesignation.objects.filter(user=request.user)

    if des_obj:
        designations = [des.designation.name for des in des_obj]
    
    # request.session['currentDesignationSelected']
    currentDes = request.session['currentDesignationSelected'] 
    
    print('currentDes : ',currentDes);

    isdept_admin = any(designation in dept_admin_to_dept for designation in designations)

    if(isdept_admin  or currentDes=="ps_admin"):
        return redirect('/purchase-and-store/entry/')
    elif not("student" in designations) and str((request.user.extrainfo.department.name)):
        return redirect('/purchase-and-store/create_proposal/')
    else:
        return redirect('/dashboard')


@login_required(login_url = "/accounts/login/")
def create_proposal(request):
    """
        The function is used to create indents by faculty.
        It adds the indent datails to the indet_table of Purchase and Store module
        @param:
                request - trivial.
        @variables:
                uploader - Employee who creates file.
                subject - Title of the file.
                description - Description of the file.
                upload_file - Attachment uploaded while creating file.
                file - The file object.
                extrainfo - The Extrainfo object.
                holdsdesignations - The HoldsDesignation object.
                context - Holds data needed to make necessary changes in the template.
                item_name- Name of the item to be procured
                quantity - Qunat of the item to be procured
                present_stock=request.POST.get('present_stock')
                estimated_cost=request.POST.get('estimated_cost')
                purpose=request.POST.get('purpose')
                specification=request.POST.get('specification')
                item_type=request.POST.get('item_type')
                nature=request.POST.get('nature')
                indigenous=request.POST.get('indigenous')
                replaced =request.POST.get('replaced')
                budgetary_head=request.POST.get('budgetary_head')
                expected_delivery=request.POST.get('expected_delivery')
                sources_of_supply=request.POST.get('sources_of_supply')
                head_approval=False
                director_approval=False
                financial_approval=False
                purchased =request.POST.get('purchased')
    """
    print("request.user.id : ", request.user.id) 
    
    if request.method =="POST":
        try:
            if 'save' in request.POST:
                uploader = request.user.extrainfo
                subject = request.POST.get('title')
                description = request.POST.get('desc')
                design = request.POST.get('design')
                designation = Designation.objects.get(id = HoldsDesignation.objects.select_related('user','working','designation').get(id = design).designation_id)
                upload_file = request.FILES.get('myfile')
                item_name=request.POST.get('item_name')
                quantity= request.POST.get('quantity')
                present_stock=request.POST.get('present_stock')
                estimated_cost=request.POST.get('estimated_cost')
                purpose=request.POST.get('purpose')
                specification=request.POST.get('specification')
                item_type=request.POST.get('item_type')
                nature=request.POST.get('nature')
                indigenous=request.POST.get('indigenous')
                replaced =request.POST.get('replaced')
                budgetary_head=request.POST.get('budgetary_head')
                expected_delivery=request.POST.get('expected_delivery')
                sources_of_supply=request.POST.get('sources_of_supply')
                head_approval=False
                director_approval=False
                financial_approval=False
                purchased =False

                file=File.objects.create(
                    uploader=uploader,
                    description=description,
                    subject=subject,
                    designation=designation,
                    upload_file=upload_file
                )

                IndentFile.objects.create(
                    file_info=file,
                    item_name= item_name,
                    quantity=quantity,      
                    present_stock=present_stock,             
                    estimated_cost=estimated_cost,
                    purpose=purpose,
                    specification=specification,
                    item_type=item_type,
                    nature=nature,
                    indigenous=indigenous, 
                    replaced = replaced ,
                    budgetary_head=budgetary_head,
                    expected_delivery=expected_delivery,
                    sources_of_supply=sources_of_supply,
                    head_approval=head_approval,
                    director_approval=director_approval,
                    financial_approval=financial_approval,
                    purchased =purchased,
                )

            if 'send' in request.POST:


                print('request.POST : ',request.POST);

                uploader = request.user.extrainfo
                subject = request.POST.get('title')
                description = request.POST.get('desc')
                design = request.POST.get('design')
                designation = Designation.objects.get(id = HoldsDesignation.objects.select_related('user','working','designation').get(id = design).designation_id)
                upload_file = request.FILES.get('myfile')
                item_name=request.POST.get('item_name')
                quantity= request.POST.get('quantity')
                present_stock=request.POST.get('present_stock')
                estimated_cost=request.POST.get('estimated_cost')
                purpose=request.POST.get('purpose')
                specification=request.POST.get('specification')
                item_type=request.POST.get('item_type')
                grade=request.POST.get('grade')
                nature=request.POST.get('nature')
                indigenous=request.POST.get('indigenous')
                replaced =request.POST.get('replaced')
                budgetary_head=request.POST.get('budgetary_head')
                expected_delivery=request.POST.get('expected_delivery')
                sources_of_supply=request.POST.get('sources_of_supply')
                head_approval=False
                director_approval=False
                financial_approval=False
                purchased = False
                designations = HoldsDesignation.objects.select_related('user','working','designation').filter(user = request.user)

                for des in designations:         
                    if request.session['currentDesignationSelected'] == "Director":
                        head_approval=True
                        director_approval=True
                        financial_approval=True
                        break




                # current_id = request.user.extrainfo
                # remarks = request.POST.get('remarks')

                sender = request.POST.get('design')
                current_design = HoldsDesignation.objects.select_related('user','working','designation').get(id=sender)


                receiver = request.POST.get('receiver')
                try:
                    receiver_id = User.objects.get(username=receiver)
                except Exception as e:
                    messages.error(request, 'Enter a valid Username')
                    return redirect('/filetracking/')
                recieve = request.POST.get('recieve')
                try:
                    receive_design = Designation.objects.get(name=recieve)
                except Exception as e:
                    receive_design = Designation.objects.get(name=recieve)
                    messages.error(request, 'Enter a valid Designation')
                    return redirect('/purchase-and-store/create_proposal/')


                file_id = create_file(
                    uploader=request.user,
                    uploader_designation=designation,
                    receiver= receiver_id,
                    receiver_designation=receive_design,
                    src_module="ps1",
                    src_object_id="",
                    file_extra_JSON={"value": 2},
                    attached_file=upload_file
                )

                IndentFile.objects.create(
                    file_info=get_object_or_404(File, pk=file_id),
                    item_name= item_name,
                    quantity=quantity,      
                    present_stock=present_stock,             
                    estimated_cost=estimated_cost,
                    purpose=purpose,
                    specification=specification,
                    item_type=item_type,
                    nature=nature,
                    grade=grade,
                    indigenous=indigenous, 
                    replaced = replaced ,
                    budgetary_head=budgetary_head,
                    expected_delivery=expected_delivery,
                    sources_of_supply=sources_of_supply,
                    head_approval=head_approval,
                    director_approval=director_approval,
                    financial_approval=financial_approval,
                    purchased =purchased,
                )

                office_module_notif(request.user, receiver_id)
                messages.success(request,'Indent Filed Successfully!')

        finally:
            message = "FileID Already Taken.!!"

    file = File.objects.select_related('uploader__user','uploader__department','designation').all()
    extrainfo = ExtraInfo.objects.select_related('user','department').all()
    holdsdesignations = HoldsDesignation.objects.select_related('user','working','designation').all()
    designations = HoldsDesignation.objects.select_related('user','working','designation').filter(user = request.user)
    today = timezone.now().strftime('%Y-%m-%d')

    currDesig = request.session['currentDesignationSelected']
    dept_admin_design = ['dept_admin1', 'dept_admin2', 'dept_admin3']  # Replace with actual department admin designations
    isAdmin = currDesig == 'ps_admin' or currDesig in dept_admin_design

    context = {
        'file': file,
        'extrainfo': extrainfo,
        'holdsdesignations': holdsdesignations,
        'designations': designations,
        'today': today,
        'isAdmin': isAdmin,
    }
    return render(request, 'ps1/composeIndent.html', context)

# @login_required(login_url = "/accounts/login")
# def compose_indent(request):
#     file = File.objects.select_related('uploader__user','uploader__department','designation').all()
#     extrainfo = ExtraInfo.objects.select_related('user','department').all()
#     holdsdesignations = HoldsDesignation.objects.select_related('user','working','designation').all()
#     designations = HoldsDesignation.objects.select_related('user','working','designation').filter(user = request.user)

#     context = {
#         'file': file,
#         'extrainfo': extrainfo,
#         'holdsdesignations': holdsdesignations,
#         'designations': designations,
#     }
#     return render(request, 'ps1/composeIndent.html', context)
    
    



@login_required(login_url = "/accounts/login")
def composed_indents(request):
    """
        The function is used to get all the files created by user(employee).
        It gets all files created by user by filtering file(table) object by user i.e, uploader.
        It displays user and file details of a file(table) of filetracking(model) in the
        template of 'Saved files' tab.

        @param:
                request - trivial.

        @variables:
                draft - The File object filtered by uploader(user).
                extrainfo - The Extrainfo object.
                context - Holds data needed to make necessary changes in the template.
    """

    # draft = File.objects.filter(uploader=request.user.extrainfo)
    # draft = File.objects.filter(uploader=request.user.extrainfo).order_by('-upload_date')

    # print(File.objects)
    # extrainfo = ExtraInfo.objects.all()
    # designation = Designation.objects.get(id=HoldsDesignation.objects.get(user=request.user).designation_id)
    des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()
    if  request.session['currentDesignationSelected'] == "student":
        return redirect('/dashboard')
    designation = HoldsDesignation.objects.filter(user=request.user)
    context = {
        # 'draft': draft,
        # 'extrainfo': extrainfo,
        'designation': designation,
    }
    return render(request, 'ps1/composed_indents.html', context)



@login_required(login_url = "/accounts/login")
def drafts_for_multiple_item(request):
    """
        The function is used to get all the designations hold by the user.

        @param:
                request - trivial.

        @variables:
                context - Holds data needed to make necessary changes in the template.
    """
    des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()
    if  request.session['currentDesignationSelected'] == "student":
        return redirect('/dashboard')
    designation = HoldsDesignation.objects.filter(user=request.user)
    context = {
        'designation': designation,
    }
    return render(request, 'ps1/drafts1.html', context)


def drafts(request):
    """
        The function is used to get all the files created by user(employee).
        It gets all files created by user by filtering file(table) object by user i.e, uploader.
        It displays user and file details of a file(table) of filetracking(model) in the
        template of 'Saved files' tab.

        @param:
                request - trivial.

        @variables:
                draft - The File object filtered by uploader(user).
                extrainfo - The Extrainfo object.
                context - Holds data needed to make necessary changes in the template.
    """

    # draft = File.objects.filter(uploader=request.user.extrainfo)
    # draft = File.objects.filter(uploader=request.user.extrainfo).order_by('-upload_date')

    # print(File.objects)
    # extrainfo = ExtraInfo.objects.all()
    # designation = Designation.objects.get(id=HoldsDesignation.objects.get(user=request.user).designation_id)
    des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()
    if  request.session['currentDesignationSelected'] == "student":
        return redirect('/dashboard')
    designation = HoldsDesignation.objects.filter(user=request.user)
    context = {
        # 'draft': draft,
        # 'extrainfo': extrainfo,
        'designation': designation,
    }
    return render(request, 'ps1/drafts.html', context)

@login_required(login_url = "/accounts/login")
def indentview(request,id):
    print("id : ",id);

    tracking_objects=Tracking.objects.all()
    tracking_obj_ids=[obj.file_id for obj in tracking_objects]
    draft_indent = IndentFile.objects.filter(file_info__in=tracking_obj_ids)
    draft=[indent.file_info.id for indent in draft_indent]
    draft_files=File.objects.filter(id__in=draft).order_by('-upload_date')
    indents=[file.indentfile for file in draft_files]
    extrainfo = ExtraInfo.objects.all()
    abcd = HoldsDesignation.objects.get(pk=id)
    s = str(abcd).split(" - ")
    designations = s[1]
    
    context = {
        'indents' : indents,
        'extrainfo': extrainfo,
        'designations': designations,
    }
    return render(request, 'ps1/indentview.html', context)


# @login_required(login_url = "/accounts/login")
# def draftview_multiple_items_indent(request,id):
#     """
#         The function is used to get all the files created by user(employee).
#         It gets all files created by user by filtering file(table) object by user i.e, uploader.
#         It displays user and file details of a file(table) of filetracking(model) in the
#         template of 'Saved files (new)' tab for indentfile with multiple items.

#         @param:
#                 request - trivial.

#         @variables:
#                 draft - The File object filtered by uploader(user).
#                 extrainfo - The Extrainfo object.
#                 context - Holds data needed to make necessary changes in the template.
#     """


#     des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()
#     if  request.session['currentDesignationSelected'] == "student":
#         return redirect('/dashboard')

#     indents= IndentFile2.objects.filter(file_info__in=request.user.extrainfo.uploaded_files.all()).select_related('file_info')
#     indent_ids=[indent.file_info for indent in indents]
#     filed_indents=Tracking.objects.filter(file_id__in=indent_ids)
#     filed_indent_ids=[indent.file_id for indent in filed_indents]
#     draft = list(set(indent_ids) - set(filed_indent_ids))
#     draft_indent=IndentFile2.objects.filter(file_info__in=draft).values("file_info")
#     draft_files=File.objects.filter(id__in=draft_indent).order_by('-upload_date')
#     extrainfo = ExtraInfo.objects.all()
#     abcd = HoldsDesignation.objects.get(pk=id)
#     s = str(abcd).split(" - ")
#     designations = s[1]
    
#     context = {
#         'draft':draft_files,
#         'extrainfo': extrainfo,
#         'designations': designations,
#     }
#     return render(request, 'ps1/draftview1.html', context)



@login_required(login_url = "/accounts/login")
def draftview(request,id):

    des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()
    if  request.session['currentDesignationSelected'] == "student":
        return redirect('/dashboard')

    indents= IndentFile.objects.filter(file_info__in=request.user.extrainfo.uploaded_files.all()).select_related('file_info')
    indent_ids=[indent.file_info for indent in indents]
    filed_indents=Tracking.objects.filter(file_id__in=indent_ids)
    filed_indent_ids=[indent.file_id for indent in filed_indents]
    draft = list(set(indent_ids) - set(filed_indent_ids))
    draft_indent=IndentFile.objects.filter(file_info__in=draft).values("file_info")
    draft_files=File.objects.filter(id__in=draft_indent).order_by('-upload_date')
    extrainfo = ExtraInfo.objects.all()
    abcd = HoldsDesignation.objects.get(pk=id)
    s = str(abcd).split(" - ")
    designations = s[1]
    
    context = {
        'draft': draft_files,
        'extrainfo': extrainfo,
        'designations': designations,
    }
    return render(request, 'ps1/draftview.html', context)

@login_required(login_url = "/accounts/login")
def indentview2(request,id):
    abcd = HoldsDesignation.objects.get(pk=id)
    s = str(abcd).split(" - ")
    designations = s[1]
    data = view_inbox(request.user.username, designations, "ps1")

    outboxd = view_outbox(request.user.username, designations, "ps1")

    data = sorted(data, key=lambda x: datetime.fromisoformat(x['upload_date']), reverse=True)

    for item in data:
        item['upload_date'] = datetime.fromisoformat(item['upload_date'])
        
    context = {
        'receive_design':abcd,
        'in_file': data,
    }
    return render(request, 'ps1/indentview2.html', context)










@login_required(login_url = "/accounts/login")
def inward(request):
    """
            The function is used to get all the Indent files received by user(employee) from other
            employees which are filtered from Tracking(table) objects by current user i.e.receiver_id.
            It displays files received by user from other employees of a Tracking(table) of
            filetracking(model) in the 'Inbox' tab of template.
            @param:
                    request - trivial.
            @variables:
                    in_file - The Tracking object filtered by receiver_id i.e, present working user.
                    context - Holds data needed to make necessary changes in the template.
    """
    des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()
    if  str(des.designation) == "student":
        return redirect('/dashboard')
    
    designation = HoldsDesignation.objects.filter(user=request.user)
    context = {
        'designation': designation,
    }

    return render(request, 'ps1/inwardIndent.html', context)






@login_required(login_url = "/accounts/login")
def confirmdelete(request,id):
    des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()
    if  request.session['currentDesignationSelected'] == "student":
        return redirect('/dashboard')
    file = File.objects.get(pk = id)

    context = {

        'j': file,
    }
    return render(request, 'ps1/confirmdelete.html',context)

@login_required(login_url = "/accounts/login")
def forwardindent(request, id):
    """
            The function is used to forward Indent files received by user(employee) from other
            employees which are filtered from Tracking(table) objects by current user
            i.e. receiver_id to other employees.
            It also gets track of file created by uploader through all users involved in file
            along with their remarks and attachments
            It displays details file of a File(table) and remarks and attachments of user involved
            in file of Tracking(table) of filetracking(model) in the template.
            @param:
                    request - trivial.
                    id - id of the file object which the user intends to forward to other employee.
            @variables:
                    file - The File object.
                    track - The Tracking object.
                    remarks = Remarks posted by user.
                    receiver = Receiver to be selected by user for forwarding file.
                    receiver_id = Receiver_id who has been selected for forwarding file.
                    upload_file = File attached by user.
                    extrainfo = ExtraInfo object.
                    holdsdesignations = HoldsDesignation objects.
                    context - Holds data needed to make necessary changes in the template.
    """
    # start = timer()
    
    # end = timer()
    if  request.session['currentDesignationSelected'] == "student":
        return redirect('/dashboard')
    indent=IndentFile.objects.select_related('file_info').get(file_info=id)
    file=indent.file_info
    # start = timer()
    track = Tracking.objects.select_related('file_id__uploader__user','file_id__uploader__department','file_id__designation','current_id__user','current_id__department',
'current_design__user','current_design__working','current_design__designation','receiver_id','receive_design').filter(file_id=file)
    # end = timer()
    
    if request.method == "POST":
            # print('Mohit Will Win : ' , request.POST);

            if 'finish' in request.POST:
                file.complete_flag = True
                file.save()

            if 'send' in request.POST:
                current_id = request.user.extrainfo
                remarks = request.POST.get('remarks')
                sender_design_id = request.POST.get('sender')
                sender_designationobj = HoldsDesignation.objects.get(id=sender_design_id).designation
                sender_designation_name = sender_designationobj.name

                receiverHdid = request.POST.get('receive')
                receiverHdobj = HoldsDesignation.objects.get(id=receiverHdid)
                receiver = receiverHdobj.user.username
                receive_design = receiverHdobj.designation.name

                try:
                    receiver_id = User.objects.get(username=receiver)
                except Exception as e:
                    messages.error(request, 'Enter a valid destination')
                    designations = HoldsDesignation.objects.select_related('user','working','designation').filter(user=request.user)

                    context = {
                        'designations': designations,
                        'file': file,
                        'track': track,
                    }
                    return render(request, 'ps1/forwardindent.html', context)
                try:
                    receive_design = Designation.objects.get(name=receive_design)
                except Exception as e:
                    messages.error(request, 'Enter a valid Designation')
                    designations = HoldsDesignation.objects.select_related('user','working','designation').filter(user=request.user)

                    context = {
                        'designations': designations,
                        'file': file,
                        'track': track,
                    }
                    return render(request, 'ps1/forwardindent.html', context)


                upload_file = request.FILES.get('myfile')
                forwarded_file_id = forward_file(
                    file_id=file.id,
                    receiver=receiver_id,
                    receiver_designation=receive_design,
                    file_extra_JSON={"key": 2},
                    remarks=remarks,
                    file_attachment=upload_file
                )



                if (str(receive_design) in dept_admin_design):
                        indent.head_approval=True
                elif ((
                    (sender_designation_name in dept_admin_design)
                      or
                      (sender_designation_name == "ps_admin")
                      )
                        and (str(receive_design) == "Accounts Admin")):
                        indent.director_approval=True
                        indent.financial_approval=True
                        indent.head_approval=True

                designs =[] 
                designations = HoldsDesignation.objects.select_related('user','working','designation').filter(user=request.user)
                for designation in designations :
                    s = str(designation).split(" - ")
                    designs.append(s[1]) 

                indent.save()


            messages.success(request, 'Indent File Forwarded successfully')
    extrainfo = ExtraInfo.objects.select_related('user','department').all()
    holdsdesignations = HoldsDesignation.objects.select_related('user','working','designation').all()
    designations = HoldsDesignation.objects.select_related('user','working','designation').filter(user=request.user)




    context = {
        'extrainfo': extrainfo,
        'holdsdesignations': holdsdesignations,
        'designations':designations,
        'file': file,
        'track': track,
        'indent':indent
    }

    return render(request, 'ps1/forwardindent.html', context)

@login_required(login_url = "/accounts/login")
def createdindent(request, id):
    """
            The function is used to forward created indent files by user(employee) .
            @param:
                    request - trivial.
                    id - id of the file object which the user intends to forward to other employee.
            @variables:
                    file - The File object.
                    track - The Tracking object.
                    remarks = Remarks posted by user.
                    receiver = Receiver to be selected by user for forwarding file.
                    receiver_id = Receiver_id who has been selected for forwarding file.
                    upload_file = File attached by user.
                    extrainfo = ExtraInfo object.
                    holdsdesignations = HoldsDesignation objects.
                    context - Holds data needed to make necessary changes in the template.
    """
    des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()
    if  request.session['currentDesignationSelected'] == "student":
        return redirect('/dashboard')
    # start = timer()
    
    # end = timer()
    indent=IndentFile.objects.select_related('file_info').get(file_info=id)
    file=indent.file_info
    # start = timer()
    track = Tracking.objects.select_related('file_id__uploader__user','file_id__uploader__department','file_id__designation','current_id__user','current_id__department',
'current_design__user','current_design__working','current_design__designation','receiver_id','receive_design').filter(file_id=file)
    # end = timer()
    



    if request.method == "POST":
            if 'finish' in request.POST:
                file.complete_flag = True
                file.save()

            if 'send' in request.POST:
                current_id = request.user.extrainfo
                remarks = request.POST.get('remarks')

                sender = request.POST.get('sender')
                current_design = HoldsDesignation.objects.select_related('user','working','designation').get(id=sender)

                receiver = request.POST.get('receiver')
                try:
                    receiver_id = User.objects.get(username=receiver)
                except Exception as e:
                    messages.error(request, 'Enter a valid destination')
                    designations = HoldsDesignation.objects.select_related('user','working','designation').filter(user=request.user)

                    context = {
                        # 'extrainfo': extrainfo,
                        # 'holdsdesignations': holdsdesignations,
                        'designations': designations,
                        'file': file,
                        'track': track,
                    }
                    return render(request, 'ps1/createdindent.html', context)
                receive = request.POST.get('recieve')
                try:
                    receive_design = Designation.objects.get(name=receive)
                except Exception as e:
                    messages.error(request, 'Enter a valid Designation')
                    designations = HoldsDesignation.objects.select_related('user','working','designation').filter(user=request.user)

                    context = {
                        # 'extrainfo': extrainfo,
                        # 'holdsdesignations': holdsdesignations,
                        'designations': designations,
                        'file': file,
                        'track': track,
                    }
                    return render(request, 'ps1/createdindent.html', context)
                upload_file = request.FILES.get('myfile')
                # return HttpResponse ("success")
                Tracking.objects.create(
                    file_id=file,
                    current_id=current_id,
                    current_design=current_design,
                    receive_design=receive_design,
                    receiver_id=receiver_id,
                    remarks=remarks,
                    upload_file=upload_file,
                )


            messages.success(request, 'Indent File sent successfully')
    designations = HoldsDesignation.objects.select_related('user','working','designation').filter(user=request.user)

    context = {
        'designations':designations,
        'file': file,
        'track': track,
        'indent':indent,
    }

    return render(request, 'ps1/createdindent.html', context)



def AjaxDropdown1(request):
    des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()
    if  request.session['currentDesignationSelected'] == "student":
        return redirect('/dashboard')
    if request.method == 'POST':
        value = request.POST.get('value')
        # print(value)

        hold = Designation.objects.filter(name__startswith=value)
        # for h in hold:
        #     print(h)
        print('secnod method')
        holds = serializers.serialize('json', list(hold))
        context = {
        'holds' : holds
        }

        return HttpResponse(JsonResponse(context), content_type='application/json')


def AjaxDropdown(request):
    # Name = ['student','co-ordinator','co co-ordinator']
    # design = Designation.objects.filter(~Q(name__in=(Name)))
    # hold = HoldsDesignation.objects.filter(Q(designation__in=(design)))

    # arr = []

    # for h in hold:
    #     arr.append(ExtraInfo.objects.filter(user=h.user))
    des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()
    if  request.session['currentDesignationSelected'] == "student":
        return redirect('/dashboard')

    if request.method == 'POST':
        value = request.POST.get('value')
        # print(value)

        users = User.objects.filter(username__startswith=value)
        users = serializers.serialize('json', list(users))

        context = {
            'users': users
        }
        return HttpResponse(JsonResponse(context), content_type='application/json')

def test(request):
    return HttpResponse('success')

@login_required(login_url = "/accounts/login")
def delete(request,id):

    if  request.session['currentDesignationSelected'] not in dept_admin_design + ["ps_admin"]:
        return redirect('/dashboard')
    file = File.objects.get(pk = id)
    file.delete()

    # Not required
    #draft = File.objects.filter(uploader=request.user.extrainfo)
    #extrainfo = ExtraInfo.objects.all()

    #context = {
     #   'draft': draft,
      #  'extrainfo': extrainfo,
    #}

    #problem over here no need of render since it doesnot affect the url
    #return render(request, 'filetracking/drafts.html', context)

    return redirect('/ps1/composed_indents/')



        
# stock Edit will provide the prepoulated form for updation of information.
@login_required(login_url = "/accounts/login")
def stock_edit(request): 
    
    if  request.session['currentDesignationSelected'] not in dept_admin_design + ["ps_admin"]:
        return redirect('/dashboard')

    if request.method =="POST":
            id=request.POST.get('id')
            temp=File.objects.get(id=id) 
            temp1=IndentFile.objects.get(file_info=temp)   
            Stock_Entry=StockEntry.objects.get(item_id=temp1)

            print(Stock_Entry.recieved_date);
            formatted_received_date = Stock_Entry.recieved_date.strftime("%Y-%m-%d")

            persons = ExtraInfo.objects.filter(user_type__in=["staff"])
            return render(request,'ps1/stock_edit.html',{'StockEntry':Stock_Entry,'persons':persons,'formatted_received_date': formatted_received_date})        

    return HttpResponseRedirect('../stock_entry_view')   
    #else: 
    #    print("ELSE")
    #    return render(request,'ps1/stock_edit.html',{'StockEntry':stocks})


# This view defines the logic for stock 
@login_required(login_url = "/accounts/login")
def stock_update(request):

    if  request.session['currentDesignationSelected'] not in dept_admin_design + ["ps_admin"]:
        return redirect('/dashboard')
    
    if request.method =="POST":
        if 'save' in request.POST:
            id=request.POST.get('id')
            temp=File.objects.get(id=id) 
            temp1=IndentFile.objects.get(file_info=temp)   
            stocks=StockEntry.objects.get(item_id=temp1)
            
            # Retrieve the ExtraInfo instance based on the provided string value

            print(request.POST);
            
            dealing_assistant_id_str = request.POST.get('dealing_assistant_id').split('-')[0].strip();
            print({dealing_assistant_id_str})

            dealing_assistant_instance = ExtraInfo.objects.get(id=dealing_assistant_id_str)

            stocks.dealing_assistant_id = dealing_assistant_instance
            
            stocks.vendor=request.POST.get('vendor')
            stocks.current_stock=request.POST.get('current_stock')
            # stocks.recieved_date=request.POST.get('recieved_date')
            stocks.bill=request.FILES.get('bill')
            stocks.location = request.POST.get('location')
            stocks.recieved_date = request.POST.get('recieved_date')

            stocks.save() 
    return HttpResponseRedirect('../stock_entry_view')   


# this is know the current situation of stocks present in any department.

@login_required(login_url = "/accounts/login")
def current_stock_view(request):

    if  request.session['currentDesignationSelected'] not in dept_admin_design + ["ps_admin"]:
        return redirect('/dashboard')
    
    # for handling the search after submission of filters form 
    if request.method=="POST":
        print('the requested data : ', request.POST)
        department = request.POST.get('department')
        grade = request.POST.get('grade')
        type = request.POST.get('type')

        # StockEntryId__item_id__file_info_grade
        StockItems = StockItem.objects.filter(
            department=department,
            StockEntryId__item_id__grade=grade,
            StockEntryId__item_id__item_type=type
        )

        grouped_items = StockItems.values('StockEntryId__item_id__item_type', 'StockEntryId__item_id__grade','department').annotate(total_quantity=Count('id'))

        grouped_items_list = [
            {
                'item_type': item['StockEntryId__item_id__item_type'],
                'grade': item['StockEntryId__item_id__grade'],
                'department': DepartmentInfo.objects.get(id=department),
                'total_quantity': item['total_quantity']
            }
            for item in grouped_items
        ]


        firstStock=StockItems.first()
        
        return render(request,'ps1/current_stock_view.html',{'stocks':grouped_items_list,'first_stock':firstStock,
                                                            'stockItems':StockItems})
        # return render(request,'ps1/current_stock_view.html',{'stocks':StockItems,'quantity':StockItems.count()})
    

    # THIS IS HARDCODED FOR NOW .
    itemsTypes=['Equipment','Machinery','Furniture','Fixture']
    grades=['A','B','C']
    departmentUser=request.user.extrainfo.department

    if  request.session['currentDesignationSelected'] in dept_admin_design:
        # if department admin then only show the stocks of that department to them

        print(dept_admin_to_dept[request.session['currentDesignationSelected']]);
        deptId = DepartmentInfo.objects.get(name=dept_admin_to_dept[request.session['currentDesignationSelected']])

        departments=[deptId]

        StockItems = StockItem.objects.filter(department=deptId)

    elif request.session['currentDesignationSelected'] == "ps_admin":
        departments=DepartmentInfo.objects.all()
        StockItems = StockItem.objects.all()
    else :
        return redirect('/dashboard')


    grouped_items = StockItems.values('StockEntryId__item_id__item_type', 'StockEntryId__item_id__grade','department').annotate(total_quantity=Count('id'))

    grouped_items_list = [
        {
            'item_type': item['StockEntryId__item_id__item_type'],
            'grade': item['StockEntryId__item_id__grade'],
            'department':  DepartmentInfo.objects.get(id=item['department']),
            'departmentId': item['department'],
            'total_quantity': item['total_quantity']
        }
        for item in grouped_items
    ]


    return render(request,'ps1/current_stock_view_filter.html',{'itemsTypes':itemsTypes,'grades':grades,'departments':departments,'stocks':grouped_items_list})

# to display stock items which are having similar item_type ,grade and department.(used in current_stock_view)

@login_required(login_url = "/accounts/login")
def stock_item_view(request):

    if  request.session['currentDesignationSelected'] not in dept_admin_design + ["ps_admin"]:
        return redirect('/dashboard')

    if request.method=="POST":
        departmentId = request.POST.get('departmentId')
        grade = request.POST.get('grade')
        type = request.POST.get('item_type')

        # StockEntryId__item_id__file_info_grade
        StockItems = StockItem.objects.filter(
            department=departmentId,
            StockEntryId__item_id__grade=grade,
            StockEntryId__item_id__item_type=type
        )
    
        return render(request,'ps1/stock_item_view.html',{'stocks':StockItems})


@login_required(login_url = "/accounts/login")
def stock_entry_view(request):

    # ! CHALLENGE HERE IS HOW TO SHOW THE TRANSFERRED STOCKS AND CURRENTLY PRESENT.
    if  request.session['currentDesignationSelected'] not in dept_admin_design + ["ps_admin"]:
        return redirect('/dashboard')

    department = request.user.extrainfo.department

    if  request.session['currentDesignationSelected'] in dept_admin_design:
        # if department admin then only show the stocks of that department to them
        print("I am a department admin ");
        deptId = DepartmentInfo.objects.get(name=dept_admin_to_dept[request.session['currentDesignationSelected']])
        stocks=StockEntry.objects.filter(item_id__file_info__uploader__department=deptId)
    elif request.session['currentDesignationSelected'] == "ps_admin":
        print("I am a PS admin ");
        stocks=StockEntry.objects.all()
    else :
        return redirect('/dashboard')

    print('stocks : ',stocks)
    
    return render(request,'ps1/stock_entry_view.html',{'stocks':stocks})

@login_required(login_url = "/accounts/login")
def stock_entry_item_view(request):

    if  request.session['currentDesignationSelected'] not in dept_admin_design + ["ps_admin"]:
        return redirect('/dashboard')

    department = request.user.extrainfo.department
    file_id = request.POST.get('id')
    temp=File.objects.get(id=file_id)
    temp1=IndentFile.objects.get(file_info=temp)
    Stock_Entry=StockEntry.objects.get(item_id=temp1)


    stocks=StockItem.objects.filter(StockEntryId=Stock_Entry)

    return render(request,'ps1/stock_entry_item_view.html',{'stocks':stocks,'first_stock':stocks.first()})




@login_required(login_url = "/accounts/login")    
def stock_delete(request):
    if  request.session['currentDesignationSelected'] not in dept_admin_design + ["ps_admin"]:
        return redirect('/dashboard')
    
    if request.method=='POST':
        
        id=request.POST.get('id')
        
        #temp1=IndentFile.objects.get(id=id)
        temp=File.objects.get(id=id)
        temp1=IndentFile.objects.get(file_info=temp)
        stocks=StockEntry.objects.get(item_id=temp1)
        stocks.delete()
    return HttpResponseRedirect('../stock_entry_view')





@login_required(login_url = "/accounts/login")   
def entry(request):
    if  request.session['currentDesignationSelected'] not in dept_admin_design + ["ps_admin"]:
        return redirect('/dashboard')
    
    # To Add stock corresponding to 'id' indent File. 
    if request.method=='POST':
        # id is the id of the File Object here
        id=request.POST.get('id')
        RequestFile = File.objects.select_related('uploader').get(id=id)

        # Requester is the person who uploaded the IndentFile Initially and you can access all of the requesters info available in User model (AbstractUser) like username ,email etc.
        Requester = RequestFile.uploader.user 
        
        # RequestFile.uploader contains the Extra information about the uploader of the RequestFile (using ExtraInfo Foreign key)


        persons = ExtraInfo.objects.filter(user_type__in=["staff"])

        CorrespondingIndentFile=IndentFile.objects.get(file_info=RequestFile)
        return render(request,'ps1/StockEntry.html',{'id':id, 'indent':CorrespondingIndentFile,'RequestFile':RequestFile,'persons':persons})
        
        

    # ent=IndentFile.objects.all()
    des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()
    department = request.user.extrainfo.department.name

    # this is to filter out the indent files only specific to a department like if A is a department Admin then he should only see the indent files corresponding to his department.
    if  request.session['currentDesignationSelected'] in dept_admin_design:
        IndentFiles=IndentFile.objects.filter(file_info__uploader__department__name=dept_admin_to_dept[request.session['currentDesignationSelected']])
    else :
        # otherwise all the indent files will be shown.
        IndentFiles=IndentFile.objects.all()
    return render(request,'ps1/entry.html',{'IndentFiles':IndentFiles})


@login_required(login_url = "/accounts/login")
def Stock_Entry(request):

    if  request.session['currentDesignationSelected'] not in dept_admin_design + ["ps_admin"]:
        return redirect('/dashboard')
    else :
        if request.method=='GET' :
            return HttpResponseRedirect('../stock_entry_view')
        
        if request.method =="POST":
            
            id=request.POST.get('id')
            temp1=File.objects.get(id=id)
            temp=IndentFile.objects.get(file_info=temp1)

            item_id=temp
            dealing_assistant_id=request.user.extrainfo
            vendor=request.POST.get('vendor')
            current_stock=request.POST.get('current_stock')
            recieved_date=request.POST.get('recieved_date')
            bill=request.FILES.get('bill')
            location= request.POST.get('location')

            StockEntry.objects.create(
                item_id=item_id,
                vendor=vendor,
                current_stock=current_stock,
                dealing_assistant_id=dealing_assistant_id,
                bill=bill,
                recieved_date=recieved_date,
                location=location
            )

            # marking the indent file as done 
            IndentFile.objects.filter(file_info=temp).update(purchased=True)         
        
            return HttpResponseRedirect('../stock_entry_view')


def dealing_assistant(request):
    des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()
    if  request.session['currentDesignationSelected'] == "student":
        return redirect('/dashboard')
    print(request.user.extrainfo.id)
    print(type(request.user.extrainfo.id))
    if request.user.extrainfo.id=='132' :
        return redirect('/purchase-and-store/entry/')   
    else:
        return redirect('/ps1')       


@login_required(login_url = "/accounts/login")
def generate_report(request):

    if  request.session['currentDesignationSelected'] not in dept_admin_design + ["ps_admin"]:
        return redirect('/dashboard')

    des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()
    department = request.user.extrainfo.department.name

    if  request.session['currentDesignationSelected'] in dept_admin_design:
        sto=StockEntry.objects.filter(item_id__file_info__uploader__department__name=dept_admin_to_dept[request.session['currentDesignationSelected']])
    else:
        sto=StockEntry.objects.all()

    return render(request,'ps1/generate_report.html',{'sto':sto})


@login_required(login_url = "/accounts/login")
def report(request):
    id=request.POST.get('id')
    designations = HoldsDesignation.objects.select_related('user','working','designation').filter(user=request.user)
    indent=IndentFile.objects.select_related('file_info').get(file_info=id)
    sto=StockEntry.objects.select_related('item_id').get(item_id=indent)
    file=indent.file_info
    total_stock = indent.quantity + indent.present_stock

    print(sto.recieved_date)

    context = {
        'designations':designations,
        'file': file,
        'indent':indent,
        'sto' : sto,
        'total_stock': total_stock
    }
        
    return render(request,'ps1/report.html',context)


def view_bill(request, stock_entry_id):
    if  request.session['currentDesignationSelected'] not in dept_admin_design + ["ps_admin"]:
        return redirect('/dashboard')
    
    print('Hello I am here ' , stock_entry_id)
    stock_entry = get_object_or_404(StockEntry, pk=stock_entry_id)
    
    print(stock_entry);

    # Check if the bill file exists
    if stock_entry.bill:
        # Read the contents of the bill file
        bill_content = stock_entry.bill.read()
        
        # Return the bill file as a response
        response = HttpResponse(bill_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{stock_entry.bill.name}"'
        return response
    else:
        # If the bill file does not exist, return a 404 response
        return HttpResponse("Bill not found", status=404)



#  This is to return a list of stocks available for transfer.
@login_required(login_url = "/accounts/login")
def perform_transfer(request):

    if  request.session['currentDesignationSelected'] not in dept_admin_design + ["ps_admin"]:
        return redirect('/dashboard')
    
    if request.method == "POST":
    
        selected_stock_items = request.POST.getlist('selected_stock_items[]')
        indentId = request.POST.get('indentId')
        dest_location = request.POST.get('dest_location')

        # print(selected_stock_items)
        # print('dest_location : ',dest_location);

        # Use regular expression to extract the number
        match = re.search(r'\((\d+)\)', indentId)

        number = match.group(1)  # Extract the number from the match

        myIndent = IndentFile.objects.get(file_info=number)

        moreStocksRequired = myIndent.quantity - len(selected_stock_items)  
        # print('dest_destination : ', myIndent.file_info.uploader.department)
        
        for item in selected_stock_items:
            stock_item  = StockItem.objects.get(id=item)
            # print('src dest : ', stock_item.department)

            store_cur_dept = stock_item.department;
            store_cur_location = stock_item.location;
            
            # changing the attributes for this stock item as being transferred.
            stock_item.department=myIndent.file_info.uploader.department;
            stock_item.location=dest_location;
            stock_item.inUse= True
            stock_item.isTransferred= True
            # if a stock_item is been transferred then obviously it will be put into use.
            stock_item.save();

            StockTransfer.objects.create(
                indent_file = myIndent,
                src_dept=store_cur_dept,
                dest_dept=myIndent.file_info.uploader.department,
                stockItem=stock_item,
                src_location=store_cur_location,
                dest_location=dest_location
            )

            messages.success(request,'Stock Transfer Done Successfully.!')
        # if the quantity required for this indent file is fulfilled we should mark this indentfile as done.
        if(moreStocksRequired<=0):
            myIndent.purchased=True
        else :
            myIndent.quantity=moreStocksRequired;
        
        myIndent.save();
        
        department = request.user.extrainfo.department.name
            
        return HttpResponseRedirect('../view_transfer') 

# This is to get the list of all the available stock items for transfer.
@login_required(login_url = "/accounts/login")
def stock_transfer(request): 
    if  request.session['currentDesignationSelected'] not in dept_admin_design + ["ps_admin"]:
        return redirect('/dashboard')

    if request.method =="POST":
            # id is the of File instance id in db.
            id=request.POST.get('id')

            temp=File.objects.get(id=id) 
            temp1=IndentFile.objects.get(file_info=temp)

            item_type_required =temp1.item_type
            item_grade_required = temp1.grade

            available_items = StockItem.objects.filter(
                StockEntryId__item_id__item_type=item_type_required,  # Foreign key traversal to IndentFile model
                StockEntryId__item_id__grade=item_grade_required,  # Foreign key traversal to IndentFile model
                inUse=False  # Filter for inUse=False
            )

            print(available_items)
            return render(request,'ps1/stock_transfer.html',{'indentFile': temp1,'available_items':available_items})        

    return HttpResponseRedirect('../stock_transfer') 


# to view the transfers
@login_required(login_url = "/accounts/login")
def view_transfer(request): 
    curr_desg = request.session['currentDesignationSelected']
    if curr_desg not in dept_admin_design + ["ps_admin"]:
        return redirect('/dashboard')
    
    if curr_desg=="ps_admin":
        stockTransfers = StockTransfer.objects.all(); 

    elif curr_desg in dept_admin_design:
        user_dept = DepartmentInfo.objects.get(name=dept_admin_to_dept[curr_desg])
        stockTransfers = StockTransfer.objects.filter(
            Q(src_dept=user_dept) | Q(dest_dept=user_dept)
        )

    # print('stock Transfers : ',stockTransfers);

    return render(request,'ps1/view_transfer.html',{'stockTransfers': stockTransfers})  


@login_required(login_url = "/accounts/login")
def outboxview2(request,id):
    abcd = HoldsDesignation.objects.get(pk=id)
    s = str(abcd).split(" - ")
    designations = s[1]
    data = view_outbox(request.user.username, designations, "ps1")
    data = sorted(data, key=lambda x: datetime.fromisoformat(x['upload_date']), reverse=True)

    for item in data:
        item['upload_date'] = datetime.fromisoformat(item['upload_date'])
        
    context = {
        'receive_design':abcd,
        'in_file': data,
    }
    return render(request, 'ps1/outboxview2.html', context)

@login_required(login_url = "/accounts/login")
def outboxview(request):

    designation = HoldsDesignation.objects.filter(user=request.user)
    context = {
        'designation': designation,
    }

    return render(request, 'ps1/outboxview.html', context)


@login_required(login_url="/accounts/login")
def updateStockItemInUse(request):
    if request.session['currentDesignationSelected'] not in dept_admin_design + ["ps_admin"]:
        return redirect('/dashboard')

    if request.method == "POST":

        # print(request.POST);

        # Get the JSON data from the request body
        json_data = json.loads(request.POST.get('selected_stock_items'))


        # print('jsondata : ', json_data)

        for item in json_data:
            item_id = item['id']
            checked = item['checked']
            stock_item = StockItem.objects.get(id=item_id)
            stock_item.inUse = checked
            stock_item.save()

        return redirect('/purchase-and-store/current_stock_view')