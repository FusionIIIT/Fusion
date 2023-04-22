from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from applications.filetracking.models import File, Tracking
from applications.ps1.models import IndentFile,StockEntry,IndentFile2,Item
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation
from django.template.defaulttags import csrf_token
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.core import serializers
from django.contrib.auth.models import User
from timeit import default_timer as time
from notification.views import office_module_notif
from django.views.decorators.csrf import csrf_exempt
import json



@login_required(login_url = "/accounts/login/")
def create_indent_multiple(request):
    """
        The function is used to create indents by faculty.
        It adds the indent datails to the IndentFile2 table and Item details to Item table
        for tracking the indent we are using filetracking module 
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
                indent_type=request.POST.get('indent_type')
                nature=request.POST.get('nature')
                indigenous=request.POST.get('indigenous')
                replaced =request.POST.get('replaced')
                budgetary_head=request.POST.get('budgetary_head')
                expected_delivery=request.POST.get('expected_delivery')
                sources_of_supply=request.POST.get('sources_of_supply')
                approved=False
                purchased =request.POST.get('purchased')
                items= List of details of all the item
    """
    des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()
    if  str(des.designation) == "student":
        return redirect('/dashboard')
    if request.user.extrainfo.id == '132':
        return redirect("/purchase-and-store/entry/")   
    if request.method == 'POST':
        try:
            uploader = request.user.extrainfo
            upload_file = request.FILES.get('myfile')
            design = request.POST.get('design')
            designation = Designation.objects.get(id = HoldsDesignation.objects.select_related('user','working','designation').get(id = design).designation_id)
            description=request.POST.get('desc')
            subject=request.POST.get('title')
            budgetary_head = request.POST.get('budgetary_head')
            sources_of_supply = request.POST.get('sources_of_supply')
            expected_delivery = request.POST.get('expected_delivery')
            # information related to reciever
            remarks = request.POST.get('remarks')
            receiver = request.POST.get('receiver')
            reciever_designation = request.POST.get('reciever_designation')
            # items related information
            item_list = json.loads(request.POST.get('items')) # this will contain the list of all the item details

            # First we will create the file for IndentFile table
            file=File.objects.create(
                uploader=uploader,
                description=description,
                subject=subject,
                designation=designation,
                upload_file=upload_file
            )

            # Now we will create Indent Table and add to file

            created_indent_file = IndentFile2.objects.create(
                file_info = file,
                title = subject,
                budgetary_head = budgetary_head,
                expected_delivery = expected_delivery,
                sources_of_supply = sources_of_supply,
                description = description
            )
            for i in range(len(item_list)) :
                # upload_file = temp[i]['file']
                item_name = item_list[i]["item_name"]
                quantity = item_list[i]["quantity"]
                present_stock = item_list[i]["present_stock"]
                estimated_cost = item_list[i]["estimated_cost"]
                purpose = item_list[i]["purpose"]
                specification = item_list[i]["specification"]
                indent_type = item_list[i]["indent_type"]
                nature =item_list[i]["nature"]
                indigenous = item_list[i]["indigenous"]
                replaced = item_list[i]["replaced"]
                item_file = request.FILES.get(f"item_file{i}")
                Item.objects.create(
                    indent_file_id = created_indent_file,
                    item_name = item_name,
                    quantity = quantity,
                    present_stock = present_stock,
                    estimated_cost = estimated_cost,
                    purpose = purpose ,
                    specification = specification,
                    indent_type = indent_type,
                    nature = nature,
                    indigenous = indigenous,
                    replaced = replaced,
                    upload_file = item_file
                )
            
            if  (receiver is not None) and (reciever_designation is not None):
                    current_design = HoldsDesignation.objects.select_related('user','working','designation').get(id=design)
                    try:
                        receiver_id = User.objects.get(username=receiver)
                    except Exception as e:
                        messages.error(request, 'Enter a valid Username')
                        return redirect('/purchase-and-store/')
                    try:
                        receive_design = Designation.objects.get(name=reciever_designation)
                    except Exception as e:
                        messages.error(request, 'Enter a valid Designation')
                        return redirect('/purchase-and-store/')

                    Tracking.objects.create(
                        file_id=file,
                        current_id=uploader,
                        current_design=current_design,
                        receive_design=receive_design,
                        receiver_id=receiver_id,
                        remarks=remarks,
                        upload_file=upload_file,
                    )
                    office_module_notif(request.user, receiver_id)
                    messages.success(request,'Indent Filed Successfully!')
                    return redirect("/purchase-and-store/composed_indents_multiple/")
            else :
                return redirect('/purchase-and-store/drafts1/')
        finally:
            message = 'File Already taken'            

    file = File.objects.select_related('uploader__user','uploader__department','designation').all()
    extrainfo = ExtraInfo.objects.select_related('user','department').all()
    holdsdesignations = HoldsDesignation.objects.select_related('user','working','designation').all()
    designations = HoldsDesignation.objects.select_related('user','working','designation').filter(user = request.user)
    users = User.objects.all()
    username_with_1 = User.objects.filter(username__startswith='1') # batch from 2010-2019
    username_with_2 = User.objects.filter(username__startswith='2') # batch from 2020-2029
    users  = users.difference(username_with_1.union(username_with_2)) # users other than students
    context = {
        'users':users,
        'file': file,
        'extrainfo': extrainfo,
        'holdsdesignations': holdsdesignations,
        'designations': designations,
    }
    return render(request, 'ps1/ComposeIndentMultiple.html', context)
            

       



@login_required(login_url = "/accounts/login/")
def ps1(request):
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
                indent_type=request.POST.get('indent_type')
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
    des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()
    if  str(des.designation) == "student":
          return redirect('/dashboard')
    if request.user.extrainfo.id == '132':
          return redirect("/purchase-and-store/entry/")
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
                indent_type=request.POST.get('indent_type')
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
                    indent_type=indent_type,
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
                indent_type=request.POST.get('indent_type')
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

                file = File.objects.create(
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
                    indent_type=indent_type,
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


                current_id = request.user.extrainfo
                remarks = request.POST.get('remarks')

                sender = request.POST.get('design')
                current_design = HoldsDesignation.objects.select_related('user','working','designation').get(id=sender)

                receiver = request.POST.get('receiver')
                try:
                    receiver_id = User.objects.get(username=receiver)
                except Exception as e:
                    messages.error(request, 'Enter a valid Username')
                    return redirect('/filetracking/')
                receive = request.POST.get('recieve')
                try:
                    receive_design = Designation.objects.get(name=receive)
                except Exception as e:
                    messages.error(request, 'Enter a valid Designation')
                    return redirect('/purchase-and-store/')

                upload_file = request.FILES.get('myfile')

                Tracking.objects.create(
                    file_id=file,
                    current_id=current_id,
                    current_design=current_design,
                    receive_design=receive_design,
                    receiver_id=receiver_id,
                    remarks=remarks,
                    upload_file=upload_file,
                )
                office_module_notif(request.user, receiver_id)
                messages.success(request,'Indent Filed Successfully!')

        finally:
            message = "FileID Already Taken.!!"

    file = File.objects.select_related('uploader__user','uploader__department','designation').all()
    extrainfo = ExtraInfo.objects.select_related('user','department').all()
    holdsdesignations = HoldsDesignation.objects.select_related('user','working','designation').all()
    designations = HoldsDesignation.objects.select_related('user','working','designation').filter(user = request.user)
    users = User.objects.all()
    username_with_1 = User.objects.filter(username__startswith='1') # batch from 2010-2019
    username_with_2 = User.objects.filter(username__startswith='2') # batch from 2020-2029
    users  = users.difference(username_with_1.union(username_with_2)) # users other than students

    context = {
        'users':users,
        'file': file,
        'extrainfo': extrainfo,
        'holdsdesignations': holdsdesignations,
        'designations': designations,
    }
    return render(request, 'ps1/composeIndent.html', context)

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
    if  str(des.designation) == "student":
          return redirect('/dashboard')
    designation = HoldsDesignation.objects.filter(user=request.user)
    context = {
        # 'draft': draft,
        # 'extrainfo': extrainfo,
        'designation': designation,
    }
    return render(request, 'ps1/composed_indents.html', context)

@login_required(login_url = "/accounts/login")
def composed_indents_multiple(request):
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
    des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()
    if  str(des.designation) == "student":
          return redirect('/dashboard')
    designation = HoldsDesignation.objects.filter(user=request.user)
    context = {
        'designation': designation,
    }
    return render(request, 'ps1/composed_indents2.html', context)



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
    if  str(des.designation) == "student":
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
    if  str(des.designation) == "student":
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

    des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()
    if  str(des.designation) == "student":
        return redirect('/dashboard')

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

@login_required(login_url = "/accounts/login")
def filled_indent_list(request,id):
    des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()
    if  str(des.designation) == "student":
        return redirect('/dashboard')

    tracking_objects=Tracking.objects.all()
    tracking_obj_ids=[obj.file_id for obj in tracking_objects]
    draft_indent = IndentFile2.objects.filter(file_info__in=tracking_obj_ids)
    draft=[indent.file_info.id for indent in draft_indent]
    draft_files=File.objects.filter(id__in=draft).order_by('-upload_date')
    indents=[file.indentfile2 for file in draft_files]
    extrainfo = ExtraInfo.objects.all()
    abcd = HoldsDesignation.objects.get(pk=id)
    s = str(abcd).split(" - ")
    designations = s[1]
    print("hello world")
    context = {
        'username':str(request.user),
        'indents' : indents,
        'extrainfo': extrainfo,
        'designations': designations,
    }
    return render(request, 'ps1/indentViewList.html', context)


@login_required(login_url = "/accounts/login")
def draftview_multiple_items_indent(request,id):
    """
        The function is used to get all the files created by user(employee).
        It gets all files created by user by filtering file(table) object by user i.e, uploader.
        It displays user and file details of a file(table) of filetracking(model) in the
        template of 'Saved files (new)' tab for indentfile with multiple items.

        @param:
                request - trivial.

        @variables:
                draft - The File object filtered by uploader(user).
                extrainfo - The Extrainfo object.
                context - Holds data needed to make necessary changes in the template.
    """


    des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()
    if  str(des.designation) == "student":
        return redirect('/dashboard')

    indents= IndentFile2.objects.filter(file_info__in=request.user.extrainfo.uploaded_files.all()).select_related('file_info')
    indent_ids=[indent.file_info for indent in indents]
    filed_indents=Tracking.objects.filter(file_id__in=indent_ids)
    filed_indent_ids=[indent.file_id for indent in filed_indents]
    draft = list(set(indent_ids) - set(filed_indent_ids))
    draft_indent=IndentFile2.objects.filter(file_info__in=draft).values("file_info")
    draft_files=File.objects.filter(id__in=draft_indent).order_by('-upload_date')
    extrainfo = ExtraInfo.objects.all()
    abcd = HoldsDesignation.objects.get(pk=id)
    s = str(abcd).split(" - ")
    designations = s[1]
    
    context = {
        'draft':draft_files,
        'extrainfo': extrainfo,
        'designations': designations,
    }
    return render(request, 'ps1/draftview1.html', context)



@login_required(login_url = "/accounts/login")
def draftview(request,id):

    des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()
    if  str(des.designation) == "student":
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
def inboxlist(request,id):


    des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()
    if  str(des.designation) == "student":
        return redirect('/dashboard')
    indent_files = IndentFile2.objects.all().values('file_info')
    print(indent_files)
    in_file = Tracking.objects.filter(file_id__in=indent_files,receiver_id=request.user).order_by("-receive_date")

    #print (File.designation)
    abcd = HoldsDesignation.objects.get(pk=id)
    s = str(abcd).split(" - ")
    designations = s[1]

    context = {

        'in_file': in_file,
        'designations': designations,
    }
    return render(request, 'ps1/inboxIndentList.html', context)

@login_required(login_url = "/accounts/login")
def indentview2(request,id):


    des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()
    if  str(des.designation) == "student":
        return redirect('/dashboard')
    indent_files = IndentFile.objects.all().values('file_info')
    print(indent_files)
    in_file = Tracking.objects.filter(file_id__in=indent_files,receiver_id=request.user).order_by("-receive_date")

    #print (File.designation)
    abcd = HoldsDesignation.objects.get(pk=id)
    s = str(abcd).split(" - ")
    designations = s[1]

    context = {

        'in_file': in_file,
        'designations': designations,
    }
    return render(request, 'ps1/indentview2.html', context)




@login_required(login_url = "/accounts/login")
def inward_multiple(request):
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
    in_file=Tracking.objects.filter(receiver_id=request.user).order_by('-receive_date')


    context = {
        'in_file': in_file,
        'designation': designation,
    }

    return render(request, 'ps1/inwardIndentMultiple.html', context)

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
    in_file=Tracking.objects.filter(receiver_id=request.user).order_by('-receive_date')


    context = {
        'in_file': in_file,
        'designation': designation,
    }

    return render(request, 'ps1/inwardIndent.html', context)
@login_required(login_url = "/accounts/login")
def confirmdelete(request,id):
    des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()
    if  str(des.designation) == "student":
        return redirect('/dashboard')
    file = File.objects.get(pk = id)

    context = {

        'j': file,
    }
    return render(request, 'ps1/confirmdelete.html',context)
def confirmdeletemultiple(request,id):
    des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()
    if  str(des.designation) == "student":
        return redirect('/dashboard')
    file = File.objects.get(pk = id)

    context = {

        'j': file,
    }
    return render(request, 'ps1/confirmdeletemultiple.html',context)

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
    des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()
    if  str(des.designation) == "student":
        return redirect('/dashboard')
    indent=IndentFile.objects.select_related('file_info').get(file_info=id)
    file=indent.file_info
    track = Tracking.objects.select_related('file_id__uploader__user','file_id__uploader__department','file_id__designation','current_id__user','current_id__department',
'current_design__user','current_design__working','current_design__designation','receiver_id','receive_design').filter(file_id=file).order_by('-forward_date')
    # end = timer()
    users = User.objects.all()
    username_with_1 = User.objects.filter(username__startswith='1') # batch from 2010-2019
    username_with_2 = User.objects.filter(username__startswith='2') # batch from 2020-2029
    users  = users.difference(username_with_1.union(username_with_2)) # users other than students
    



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
                    return render(request, 'ps1/forwardindent.html', context)
                receive = request.POST.get('recieve')
                try:
                    receive_design = Designation.objects.get(name=receive)
                except Exception as e:
                    messages.error(request, 'Enter a valid Designation')
                    designations = HoldsDesignation.objects.select_related('user','working','designation').filter(user=request.user)
                    users = User.objects.all()
                    username_with_1 = User.objects.filter(username__startswith='1') # batch from 2010-2019
                    username_with_2 = User.objects.filter(username__startswith='2') # batch from 2020-2029
                    users  = users.difference(username_with_1.union(username_with_2)) # users other than students

                    context = {
                        # 'extrainfo': extrainfo,
                        # 'holdsdesignations': holdsdesignations,
                        'users':users,
                        'designations': designations,
                        'file': file,
                        'track': track,
                    }
                    return render(request, 'ps1/forwardindent.html', context)

                # receive_design = receive_designation[0]
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

                check=str(request.user)
                val=str(request.POST.get('approval'))
                designs =[] 
                designations = HoldsDesignation.objects.select_related('user','working','designation').filter(user=request.user)
                for designation in designations :
                    s = str(designation).split(" - ")
                    designs.append(s[1]) 


                if val=="accept":
                    if any(d in designs for d in ("HOD (ME)", "HOD (ECE)", "CSE HOD", "HOD (Design)", "HOD (NS)")):
                        indent.head_approval=True
                    elif "Director" in designs:
                        indent.director_approval=True
                        indent.financial_approval=True
                
                else:
                    if any(d in designs for d in ("HOD (ME)", "HOD (ECE)", "CSE HOD", "HOD (Design)", "HOD (NS)")):
                        indent.head_approval=False
                    elif "Director" in designs:
                        indent.director_approval=False
                        indent.financial_approval=False
                    

                indent.save()


            messages.success(request, 'Indent File sent successfully')
    extrainfo = ExtraInfo.objects.select_related('user','department').all()
    holdsdesignations = HoldsDesignation.objects.select_related('user','working','designation').all()
    designations = HoldsDesignation.objects.select_related('user','working','designation').filter(user=request.user)

    context = {
        'users':users,
        'designations':designations,
        'file': file,
        'track': track,
        'indent':indent,
    }

    return render(request, 'ps1/forwardindent.html', context)



@login_required(login_url='/accounts/login')
def view_my_indent(request,id):
    des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()

    if str(des.designation) == "student":
        return redirect('/dashboard')
    
    indent = IndentFile2.objects.select_related('file_info').get(file_info=id)
    indent_items = Item.objects.filter(indent_file_id=id).order_by('item_id')
    file = indent.file_info
    track = Tracking.objects.select_related('file_id__uploader__user','file_id__uploader__department','file_id__designation','current_id__user','current_id__department','current_design__user','current_design__working','current_design__designation','receiver_id','receive_design').filter(file_id=file).order_by('-forward_date')
    extrainfo = ExtraInfo.objects.select_related('user','department').all()
    holdsdesignations = HoldsDesignation.objects.select_related('user','working','designation').all()
    designations = HoldsDesignation.objects.select_related('user','working','designation').filter(user=request.user)
    context = {
        'items':indent_items,
        'designations':designations,
        'file':file,
        'track': track,
        'indent' : indent
    }
    return render(request,'ps1/viewMyIndentFile.html',context)




@login_required(login_url='/accounts/login')
def reject_indent(request,id):
    '''
        This endpoint is for rejecting a indent file.
    '''
    try :
        des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()
        if str(des.designation) == "student":
            return redirect('/dashboard')
        indent = IndentFile2.objects.select_related('file_info').get(file_info=id)

        indent.rejected = True 
        indent.save()
        messages.success(request, 'Indent File Rejected Successfully')
        context ={
            'success':True,
            'message':'file rejected successfully'
        }
        return HttpResponse(json.dumps(context), content_type="application/json")
    except Exception as e:
        context = {
            'success':False,
            'message':'Some Error occured'
        }
        return HttpResponse(json.dumps(context), content_type="application/json"),500

@login_required(login_url = '/accounts/login')
def item_purchase(request,id):
    '''
        This function is reponsible for making item purchased
    ''' 
    if request.method == 'POST':
        item = Item.objects.get(item_id=id)
        item.purchased = True 
        item.save()
        context = {
            'success' : True,
            'message' : 'Item purchage status changed successfully'
        }
        messages.success(request, 'Item Purchase status changed successfully')
        return HttpResponse(json.dumps(context), content_type="application/json")

    

    


@login_required(login_url='/accounts/login')
def inward_indent_details(request,id):
    des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()

    if str(des.designation) == "student":
        return redirect('/dashboard')
    
    indent = IndentFile2.objects.select_related('file_info').get(file_info=id)
    indent_items = Item.objects.filter(indent_file_id=id).order_by('item_id')
    purchased_items = indent_items.filter(purchased=True)
    indent_items_length = len(indent_items)
    purchaged_items_length = len(purchased_items)

    file = indent.file_info
    track = Tracking.objects.select_related('file_id__uploader__user','file_id__uploader__department','file_id__designation','current_id__user','current_id__department','current_design__user','current_design__working','current_design__designation','receiver_id','receive_design').filter(file_id=file).order_by('-forward_date')
    extrainfo = ExtraInfo.objects.select_related('user','department').all()
    holdsdesignations = HoldsDesignation.objects.select_related('user','working','designation').all()
    designations = HoldsDesignation.objects.select_related('user','working','designation').filter(user=request.user)
    users = User.objects.all()
    username_with_1 = User.objects.filter(username__startswith='1') # batch from 2010-2019
    username_with_2 = User.objects.filter(username__startswith='2') # batch from 2020-2029
    users  = users.difference(username_with_1.union(username_with_2)) # users other than students
    context = {
        'users':users,
        'items':indent_items,
        'designations':designations,
        'file':file,
        'track': track,
        'indent' : indent,
        'indent_items_length' : indent_items_length,
        'purchaged_items_length' : purchaged_items_length
    }
    if request.method == "POST":
            if 'approve' in request.POST:
                current_id = request.user.extrainfo
                remarks = request.POST.get('remarks')

                sender = request.POST.get('sender')
                current_design = HoldsDesignation.objects.select_related('user','working','designation').get(id=sender)

                receiver = request.POST.get('receiver')
                receive = request.POST.get('recieve')


                try:
                    receiver_id = User.objects.get(username=receiver)
                except Exception as e:
                    messages.error(request,'Some Error Occured')
                    indent = IndentFile2.objects.select_related('file_info').get(file_info=id)
                    indent_items = Item.objects.filter(indent_file_id=id)
                    purchased_items = indent_items.filter(purchased=True)
                    indent_items_length = len(indent_items)
                    purchaged_items_length = len(purchased_items)
                    file = indent.file_info
                    track = Tracking.objects.select_related('file_id__uploader__user','file_id__uploader__department','file_id__designation','current_id__user','current_id__department','current_design__user','current_design__working','current_design__designation','receiver_id','receive_design').filter(file_id=file).order_by('-forward_date')
                    extrainfo = ExtraInfo.objects.select_related('user','department').all()
                    holdsdesignations = HoldsDesignation.objects.select_related('user','working','designation').all()
                    designations = HoldsDesignation.objects.select_related('user','working','designation').filter(user=request.user)
                    users = User.objects.all()
                    username_with_1 = User.objects.filter(username__startswith='1') # batch from 2010-2019
                    username_with_2 = User.objects.filter(username__startswith='2') # batch from 2020-2029
                    users  = users.difference(username_with_1.union(username_with_2)) # users other than students
                    context = {
                        'users':users,
                        'items':indent_items,
                        'designations':designations,
                        'file':file,
                        'track': track,
                        'indent' : indent,
                        'indent_items_length' : indent_items_length,
                        'purchaged_items_length' : purchaged_items_length
                    }
                    return render(request,'ps1/viewInwardItemDetails.html',context)
                try:
                    receive_design = Designation.objects.get(name=receive)
                except Exception as e:
                    messages.error(request,'Enter Valid Designation')
                    indent = IndentFile2.objects.select_related('file_info').get(file_info=id)
                    indent_items = Item.objects.filter(indent_file_id=id)
                    purchased_items = indent_items.filter(purchased=True)
                    indent_items_length = len(indent_items)
                    purchaged_items_length = len(purchased_items)
                    file = indent.file_info
                    track = Tracking.objects.select_related('file_id__uploader__user','file_id__uploader__department','file_id__designation','current_id__user','current_id__department','current_design__user','current_design__working','current_design__designation','receiver_id','receive_design').filter(file_id=file).order_by('-forward_date')
                    extrainfo = ExtraInfo.objects.select_related('user','department').all()
                    holdsdesignations = HoldsDesignation.objects.select_related('user','working','designation').all()
                    designations = HoldsDesignation.objects.select_related('user','working','designation').filter(user=request.user)
                    users = User.objects.all()
                    username_with_1 = User.objects.filter(username__startswith='1') # batch from 2010-2019
                    username_with_2 = User.objects.filter(username__startswith='2') # batch from 2020-2029
                    users  = users.difference(username_with_1.union(username_with_2)) # users other than students
                    context = {
                        'users':users,
                        'items':indent_items,
                        'designations':designations,
                        'file':file,
                        'track': track,
                        'indent' : indent,
                        'indent_items_length' : indent_items_length,
                        'purchaged_items_length' : purchaged_items_length
                    }
                    return render(request,'ps1/viewInwardItemDetails.html',context)
                upload_file = request.FILES.get('myfile')
                remarks = remarks + f'\n Approved by :{str(request.user)}'
                Tracking.objects.create(
                    file_id=file,
                    current_id=current_id,
                    current_design=current_design,
                    receive_design=receive_design,
                    receiver_id=receiver_id,
                    remarks=remarks,
                    upload_file=upload_file,
                )

                indent.approved = True
                indent.save()
                messages.success(request, 'Indent File sent and approved successfully')
            elif 'forward' in request.POST:
                current_id = request.user.extrainfo
                remarks = request.POST.get('remarks')

                sender = request.POST.get('sender')
                current_design = HoldsDesignation.objects.select_related('user','working','designation').get(id=sender)

                receiver = request.POST.get('receiver')
                receive = request.POST.get('recieve')


                try:
                    receiver_id = User.objects.get(username=receiver)
                except Exception as e:
                    messages.error(request,'Some Error Occured')
                    indent = IndentFile2.objects.select_related('file_info').get(file_info=id)
                    indent_items = Item.objects.filter(indent_file_id=id)
                    purchased_items = indent_items.filter(purchased=True)
                    indent_items_length = len(indent_items)
                    purchaged_items_length = len(purchased_items)
                    file = indent.file_info
                    track = Tracking.objects.select_related('file_id__uploader__user','file_id__uploader__department','file_id__designation','current_id__user','current_id__department','current_design__user','current_design__working','current_design__designation','receiver_id','receive_design').filter(file_id=file).order_by('-forward_date')
                    extrainfo = ExtraInfo.objects.select_related('user','department').all()
                    holdsdesignations = HoldsDesignation.objects.select_related('user','working','designation').all()
                    designations = HoldsDesignation.objects.select_related('user','working','designation').filter(user=request.user)
                    users = User.objects.all()
                    username_with_1 = User.objects.filter(username__startswith='1') # batch from 2010-2019
                    username_with_2 = User.objects.filter(username__startswith='2') # batch from 2020-2029
                    users  = users.difference(username_with_1.union(username_with_2)) # users other than students
                    context = {
                        'users':users,
                        'items':indent_items,
                        'designations':designations,
                        'file':file,
                        'track': track,
                        'indent' : indent,
                        'indent_items_length' : indent_items_length,
                        'purchaged_items_length' : purchaged_items_length
                    }
                    return render(request,'ps1/viewInwardItemDetails.html',context)
                try:
                    receive_design = Designation.objects.get(name=receive)
                except Exception as e:
                    messages.error(request,'Enter Valid Designation')
                    indent = IndentFile2.objects.select_related('file_info').get(file_info=id)
                    indent_items = Item.objects.filter(indent_file_id=id)
                    purchased_items = indent_items.filter(purchased=True)
                    indent_items_length = len(indent_items)
                    purchaged_items_length = len(purchased_items)
                    file = indent.file_info
                    track = Tracking.objects.select_related('file_id__uploader__user','file_id__uploader__department','file_id__designation','current_id__user','current_id__department','current_design__user','current_design__working','current_design__designation','receiver_id','receive_design').filter(file_id=file).order_by('-forward_date')
                    extrainfo = ExtraInfo.objects.select_related('user','department').all()
                    holdsdesignations = HoldsDesignation.objects.select_related('user','working','designation').all()
                    designations = HoldsDesignation.objects.select_related('user','working','designation').filter(user=request.user)
                    users = User.objects.all()
                    username_with_1 = User.objects.filter(username__startswith='1') # batch from 2010-2019
                    username_with_2 = User.objects.filter(username__startswith='2') # batch from 2020-2029
                    users  = users.difference(username_with_1.union(username_with_2)) # users other than students
                    context = {
                        'users':users,
                        'items':indent_items,
                        'designations':designations,
                        'file':file,
                        'track': track,
                        'indent' : indent,
                        'indent_items_length' : indent_items_length,
                        'purchaged_items_length' : purchaged_items_length
                    }
                    return render(request,'ps1/viewInwardItemDetails.html',context)
                upload_file = request.FILES.get('myfile')
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
            elif 'reject' in request.POST:
                indent.rejected = True 
                indent.save()
                messages.success(request,'Indent Rejected Successfully')
            elif 'procure' in request.POST:
                current_id = request.user.extrainfo
                remarks = request.POST.get('remarks')

                sender = request.POST.get('sender')
                current_design = HoldsDesignation.objects.select_related('user','working','designation').get(id=sender)

                receiver = request.POST.get('receiver')
                receive = request.POST.get('recieve')


                try:
                    receiver_id = User.objects.get(username=receiver)
                except Exception as e:
                    messages.error(request,'Some Error Occured')
                    indent = IndentFile2.objects.select_related('file_info').get(file_info=id)
                    indent_items = Item.objects.filter(indent_file_id=id)
                    purchased_items = indent_items.filter(purchased=True)
                    indent_items_length = len(indent_items)
                    purchaged_items_length = len(purchased_items)
                    file = indent.file_info
                    track = Tracking.objects.select_related('file_id__uploader__user','file_id__uploader__department','file_id__designation','current_id__user','current_id__department','current_design__user','current_design__working','current_design__designation','receiver_id','receive_design').filter(file_id=file).order_by('-forward_date')
                    extrainfo = ExtraInfo.objects.select_related('user','department').all()
                    holdsdesignations = HoldsDesignation.objects.select_related('user','working','designation').all()
                    designations = HoldsDesignation.objects.select_related('user','working','designation').filter(user=request.user)
                    users = User.objects.all()
                    username_with_1 = User.objects.filter(username__startswith='1') # batch from 2010-2019
                    username_with_2 = User.objects.filter(username__startswith='2') # batch from 2020-2029
                    users  = users.difference(username_with_1.union(username_with_2)) # users other than students
                    context = {
                        'users':users,
                        'items':indent_items,
                        'designations':designations,
                        'file':file,
                        'track': track,
                        'indent' : indent,
                        'indent_items_length' : indent_items_length,
                        'purchaged_items_length' : purchaged_items_length
                    }
                    return render(request,'ps1/viewInwardItemDetails.html',context)
                try:
                    receive_design = Designation.objects.get(name=receive)
                except Exception as e:
                    messages.error(request,'Enter Valid Designation')
                    indent = IndentFile2.objects.select_related('file_info').get(file_info=id)
                    indent_items = Item.objects.filter(indent_file_id=id)
                    purchased_items = indent_items.filter(purchased=True)
                    indent_items_length = len(indent_items)
                    purchaged_items_length = len(purchased_items)
                    file = indent.file_info
                    track = Tracking.objects.select_related('file_id__uploader__user','file_id__uploader__department','file_id__designation','current_id__user','current_id__department','current_design__user','current_design__working','current_design__designation','receiver_id','receive_design').filter(file_id=file).order_by('-forward_date')
                    extrainfo = ExtraInfo.objects.select_related('user','department').all()
                    holdsdesignations = HoldsDesignation.objects.select_related('user','working','designation').all()
                    designations = HoldsDesignation.objects.select_related('user','working','designation').filter(user=request.user)
                    users = User.objects.all()
                    username_with_1 = User.objects.filter(username__startswith='1') # batch from 2010-2019
                    username_with_2 = User.objects.filter(username__startswith='2') # batch from 2020-2029
                    users  = users.difference(username_with_1.union(username_with_2)) # users other than students
                    context = {
                        'users':users,
                        'items':indent_items,
                        'designations':designations,
                        'file':file,
                        'track': track,
                        'indent' : indent,
                        'indent_items_length' : indent_items_length,
                        'purchaged_items_length' : purchaged_items_length
                    }
                    return render(request,'ps1/viewInwardItemDetails.html',context)
                upload_file = request.FILES.get('myfile')
                remarks = remarks + f'\n Approved by :{str(sender)}'
                Tracking.objects.create(
                    file_id=file,
                    current_id=current_id,
                    current_design=current_design,
                    receive_design=receive_design,
                    receiver_id=receiver_id,
                    remarks=remarks,
                    upload_file=upload_file,
                )

                indent.procured = True
                indent.save()
                messages.success(request, 'Indent File Procured successfully and went for stock entry')
                
    return render(request,'ps1/viewInwardItemDetails.html',context)


@login_required(login_url='/accounts/login')
def drafted_indent(request,id):
    des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()

    if str(des.designation) == "student":
        return redirect('/dashboard')
    
    indent = IndentFile2.objects.select_related('file_info').get(file_info=id)
    indent_items = Item.objects.filter(indent_file_id=id).order_by('item_id')
    print(indent_items)
    file = indent.file_info
    track = Tracking.objects.select_related('file_id__uploader__user','file_id__uploader__department','file_id__designation','current_id__user','current_id__department','current_design__user','current_design__working','current_design__designation','receiver_id','receive_design').filter(file_id=file).order_by('-forward_date')
    extrainfo = ExtraInfo.objects.select_related('user','department').all()
    holdsdesignations = HoldsDesignation.objects.select_related('user','working','designation').all()
    designations = HoldsDesignation.objects.select_related('user','working','designation').filter(user=request.user)
    users = User.objects.all()
    username_with_1 = User.objects.filter(username__startswith='1') # batch from 2010-2019
    username_with_2 = User.objects.filter(username__startswith='2') # batch from 2020-2029
    users  = users.difference(username_with_1.union(username_with_2)) # users other than students
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
                    indent = IndentFile2.objects.select_related('file_info').get(file_info=id)
                    indent_items = Item.objects.filter(indent_file_id=id).order_by('item_id')
                    print(indent_items)
                    file = indent.file_info
                    track = Tracking.objects.select_related('file_id__uploader__user','file_id__uploader__department','file_id__designation','current_id__user','current_id__department','current_design__user','current_design__working','current_design__designation','receiver_id','receive_design').filter(file_id=file).order_by('-forward_date')
                    extrainfo = ExtraInfo.objects.select_related('user','department').all()
                    holdsdesignations = HoldsDesignation.objects.select_related('user','working','designation').all()
                    designations = HoldsDesignation.objects.select_related('user','working','designation').filter(user=request.user)
                    users = User.objects.all()
                    username_with_1 = User.objects.filter(username__startswith='1') # batch from 2010-2019
                    username_with_2 = User.objects.filter(username__startswith='2') # batch from 2020-2029
                    users  = users.difference(username_with_1.union(username_with_2)) # users other than students
                    context = {
                        'users':users,
                        'items':indent_items,
                        'designations':designations,
                        'file':file,
                        'track': track,
                        'indent' : indent
                    }
                    return render(request, 'ps1/draftedIndentDetails.html', context)
                receive = request.POST.get('recieve')
                try:
                    receive_design = Designation.objects.get(name=receive)
                except Exception as e:
                    indent = IndentFile2.objects.select_related('file_info').get(file_info=id)
                    indent_items = Item.objects.filter(indent_file_id=id).order_by('item_id')
                    print(indent_items)
                    file = indent.file_info
                    track = Tracking.objects.select_related('file_id__uploader__user','file_id__uploader__department','file_id__designation','current_id__user','current_id__department','current_design__user','current_design__working','current_design__designation','receiver_id','receive_design').filter(file_id=file).order_by('-forward_date')
                    extrainfo = ExtraInfo.objects.select_related('user','department').all()
                    holdsdesignations = HoldsDesignation.objects.select_related('user','working','designation').all()
                    designations = HoldsDesignation.objects.select_related('user','working','designation').filter(user=request.user)
                    users = User.objects.all()
                    username_with_1 = User.objects.filter(username__startswith='1') # batch from 2010-2019
                    username_with_2 = User.objects.filter(username__startswith='2') # batch from 2020-2029
                    users  = users.difference(username_with_1.union(username_with_2)) # users other than students
                    context = {
                        'users':users,
                        'items':indent_items,
                        'designations':designations,
                        'file':file,
                        'track': track,
                        'indent' : indent
                    }
                    return render(request, 'ps1/draftedIndentDetails.html', context)

                # receive_design = receive_designation[0]
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

    context = {
        'users':users,
        'items':indent_items,
        'designations':designations,
        'file':file,
        'track': track,
        'indent' : indent
    }
    return render(request,'ps1/draftedIndentDetails.html',context)

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
    if  str(des.designation) == "student":
        return redirect('/dashboard')
    # start = timer()
    
    # end = timer()
    indent=IndentFile.objects.select_related('file_info').get(file_info=id)
    file=indent.file_info
    # start = timer()
    track = Tracking.objects.select_related('file_id__uploader__user','file_id__uploader__department','file_id__designation','current_id__user','current_id__department',
'current_design__user','current_design__working','current_design__designation','receiver_id','receive_design').filter(file_id=file).order_by('-forward_date')
    # end = timer()
    users = User.objects.all()
    username_with_1 = User.objects.filter(username__startswith='1') # batch from 2010-2019
    username_with_2 = User.objects.filter(username__startswith='2') # batch from 2020-2029
    users  = users.difference(username_with_1.union(username_with_2)) # users other than students
    



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

                # receive_design = receive_designation[0]
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
    # start = timer()
    extrainfo = ExtraInfo.objects.select_related('user','department').all()
    holdsdesignations = HoldsDesignation.objects.select_related('user','working','designation').all()
    designations = HoldsDesignation.objects.select_related('user','working','designation').filter(user=request.user)

    context = {
        'users':users,
        'designations':designations,
        'file': file,
        'track': track,
        'indent':indent,
    }

    return render(request, 'ps1/createdindent.html', context)






def AjaxDropdown1(request):
    des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()
    if  str(des.designation) == "student":
        return redirect('/dashboard')
    if request.method == 'POST':
        value = request.POST.get('value')
        hold = Designation.objects.filter(name__startswith=value)
        print('secnod method')
        holds = serializers.serialize('json', list(hold))
        context = {
        'holds' : holds
        }

        return HttpResponse(JsonResponse(context), content_type='application/json')


def AjaxDropdown(request):
    des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()
    if  str(des.designation) == "student":
        return redirect('/dashboard')

    if request.method == 'POST':
        value = request.POST.get('value')
        users = User.objects.filter(username__startswith=value)
        users = serializers.serialize('json', list(users))

        context = {
            'users': users
        }
        return HttpResponse(JsonResponse(context), content_type='application/json')

def test(request):
    return HttpResponse('success')


@login_required(login_url = "/accounts/login")
def delete_multiple(request,id):
    des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()
    if  str(des.designation) == "student":
        return redirect('/dashboard')
    file = File.objects.get(pk = id)
    file.delete()
    return redirect('/purchase-and-store/composed_indents_multiple/')
    
@login_required(login_url = "/accounts/login")
def delete(request,id):
    des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()
    if  str(des.designation) == "student":
        return redirect('/dashboard')
    file = File.objects.get(pk = id)
    file.delete()
    return redirect('/purchase-and-store/composed_indents/')


@login_required(login_url = "/accounts/login")
def Stock_Entry(request):
    des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()
    if  str(des.designation) == "student":
        return redirect('/dashboard')
    else :
        if request.method=='GET' :
            return HttpResponseRedirect('../stock_view')
        
        if request.method =="POST":
            
            id=request.POST.get('id')
            
            
            temp1=File.objects.get(id=id)
            temp=IndentFile.objects.get(file_info=temp1)
            

            
            dealing_assistant_id=request.user.extrainfo

            item_id=temp
            item_name=request.POST.get('item_name')
            vendor=request.POST.get('vendor')
            current_stock=request.POST.get('current_stock')
            recieved_date=request.POST.get('recieved_date')
            bill=request.FILES.get('bill')
            StockEntry.objects.create(item_id=item_id,item_name= item_name,vendor=vendor,current_stock=current_stock,dealing_assistant_id=dealing_assistant_id,bill=bill,recieved_date=recieved_date,)
            IndentFile.objects.filter(file_info=temp).update(purchased=True)         
        
            return HttpResponseRedirect('../stock_view')

       

@login_required(login_url="/accounts/login")
def get_designations(request):
    """
        This function is used for getting the all the designations associated with
        an user 
        request type : POST 
        body : 
        {
            value : "username",
        }
    """
    if request.method == 'POST':
        username = request.POST.get('value')
        user_value = User.objects.filter(username=username)
        holdsdesignations = HoldsDesignation.objects.select_related('user','working','designation').filter(user=user_value[0])
        holdsdesignations = serializers.serialize('json', list(holdsdesignations))
        holdsdesignations = json.loads(holdsdesignations)
        designations = Designation.objects.none()
        for value in holdsdesignations:
            qs = Designation.objects.filter(id=value['fields']['designation'])
            designations = designations.union(qs)
        designations = serializers.serialize('json', list(designations))
        context = {
            'designations' : designations
        }
        return HttpResponse(JsonResponse(context), content_type='application/json')


   
@login_required(login_url = "/accounts/login")
def stock_edit(request): 
    des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()
    if  str(des.designation) == "student":
        return redirect('/dashboard')
   

    if request.method =="POST":
            id=request.POST.get('id')
            temp=File.objects.get(id=id) 
            temp1=IndentFile.objects.get(file_info=temp)   
            stocks=StockEntry.objects.get(item_id=temp1)
            return render(request,'ps1/stock_edit.html',{'StockEntry':stocks})        

    return HttpResponseRedirect('../stock_view')   
        
def stock_update(request):
    des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()
    if  str(des.designation) == "student":
        return redirect('/dashboard')
    if request.method =="POST":
        if 'save' in request.POST:
            id=request.POST.get('id')
            temp=File.objects.get(id=id) 
            temp1=IndentFile.objects.get(file_info=temp)   
            stocks=StockEntry.objects.get(item_id=temp1)
            
            stocks.item_name=request.POST.get('item_name')
            stocks.vendor=request.POST.get('vendor')
            stocks.current_stock=request.POST.get('current_stock')
            #stocks.recieved_date=request.POST.get('recieved_date')
            stocks.bill=request.FILES.get('bill')
            stocks.save() 
    return HttpResponseRedirect('../stock_view')   
  


def stock_view(request):

    des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()
    if  str(des.designation) == "student":
        return redirect('/dashboard')
    
    sto=StockEntry.objects.all()
    if sto:
        temp=sto.first()
        
        if temp.item_id.purchased:
            print("Purchase Succesful")
            print()   
            print()   
        
    return render(request,'ps1/stock_view.html',{'sto':sto})

@login_required(login_url = "/accounts/login")    
def stock_delete(request):
    des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()
    if  str(des.designation) == "student":
        return redirect('/dashboard')
    
    if request.method=='POST':
        
        id=request.POST.get('id')
        
        #temp1=IndentFile.objects.get(id=id)
        temp=File.objects.get(id=id)
        temp1=IndentFile.objects.get(file_info=temp)
        stocks=StockEntry.objects.get(item_id=temp1)
        stocks.delete()
    return HttpResponseRedirect('../stock_view')   


@login_required(login_url = "/accounts/login")   
def entry(request):
    des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()
    if  str(des.designation) == "student":
        return redirect('/dashboard')

    if request.method=='POST':
        id=request.POST.get('id')
        temp=File.objects.get(id=id)
        temp1=IndentFile.objects.get(file_info=temp)
        return render(request,'ps1/StockEntry.html',{'id':id, 'indent':temp1})
        
        

    
    ent=IndentFile.objects.all()
    return render(request,'ps1/entry.html',{'ent':ent})
    
def dealing_assistant(request):
    des = HoldsDesignation.objects.all().select_related().filter(user = request.user).first()
    if  str(des.designation) == "student":
        return redirect('/dashboard')
    print(request.user.extrainfo.id)
    print(type(request.user.extrainfo.id))
    if request.user.extrainfo.id=='132' :
        return redirect('/purchase-and-store/entry/')   
    else:
        return redirect('/purchase-and-store')       
