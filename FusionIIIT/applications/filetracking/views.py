from sqlite3 import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.core.paginator import Paginator

from .models import File, Tracking
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation
from .utils import *
from .sdk.methods import *
from .decorators import *
from datetime import datetime;

from timeit import default_timer as time
from notification.views import office_module_notif, file_tracking_notif

import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

import json
import zipfile
import os


@login_required(login_url="/accounts/login/")
@user_is_student
@dropdown_designation_valid
def filetracking(request):
    """
        The function is used to create files by current user(employee).
        It adds the employee(uploader) and file datails to a file(table) of filetracking(model)
        if he intends to create file.

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
    """

    if request.method == "POST":
        try:
            if 'save' in request.POST:
                uploader = request.user.extrainfo
                subject = request.POST.get('title')
                description = request.POST.get('desc')
                design = request.POST.get('design')
                designation = Designation.objects.get(id=HoldsDesignation.objects.select_related(
                    'user', 'working', 'designation').get(id=design).designation_id)
                upload_file = request.FILES.get('myfile')
                if upload_file and upload_file.size / 1000 > 10240:
                    messages.error(
                        request, "File should not be greater than 10MB")
                    return redirect("/filetracking")

                form_remarks = request.POST.get('remarks')
                extraJSON = {
                    'remarks': form_remarks if form_remarks is not None else '',
                }

                File.objects.create(
                    uploader=uploader,
                    description=description,
                    subject=subject,
                    designation=designation,
                    upload_file=upload_file,
                    file_extra_JSON=extraJSON
                )

                messages.success(request, 'File Draft Saved Successfully')

            if 'send' in request.POST:
                uploader = request.user.extrainfo
                subject = request.POST.get('title')
                description = request.POST.get('desc')
                design = request.POST.get('design')
                designation = Designation.objects.get(id=HoldsDesignation.objects.select_related(
                    'user', 'working', 'designation').get(id=design).designation_id)

                upload_file = request.FILES.get('myfile')
                if upload_file and upload_file.size / 1000 > 10240:
                    messages.error(
                        request, "File should not be greater than 10MB")
                    return redirect("/filetracking")

                file = File.objects.create(
                    uploader=uploader,
                    description=description,
                    subject=subject,
                    designation=designation,
                    upload_file=upload_file
                )

                current_id = request.user.extrainfo
                remarks = request.POST.get('remarks')

                sender = request.POST.get('design')
                current_design = HoldsDesignation.objects.select_related(
                    'user', 'working', 'designation').get(id=sender)

                receiver = request.POST.get('receiver')
                try:
                    receiver_id = User.objects.get(username=receiver)
                except Exception as e:
                    messages.error(request, 'Enter a valid Username')
                    return redirect('/filetracking/')
                receive = request.POST.get('receive')
                try:
                    receive_design = Designation.objects.get(name=receive)
                except Exception as e:
                    messages.error(request, 'Enter a valid Designation')
                    return redirect('/filetracking/')

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
                file_tracking_notif(request.user, receiver_id, subject)
                messages.success(request, 'File sent successfully')

        except IntegrityError:
            message = "FileID Already Taken.!!"
            return HttpResponse(message)

    file = File.objects.select_related(
        'uploader__user', 'uploader__department', 'designation').all()
    extrainfo = ExtraInfo.objects.select_related('user', 'department').all()
    holdsdesignations = HoldsDesignation.objects.select_related(
        'user', 'working', 'designation').all()

    designation_name = request.session.get('currentDesignationSelected', 'default_value')
    all_available_designations = request.session.get(
        'allDesignations', 'default_value2')


    username = request.user
    designation_id = get_HoldsDesignation_obj(
        username, designation_name).id

    context = {
        'file': file,
        'extrainfo': extrainfo,
        'holdsdesignations': holdsdesignations,
        'designation_name': designation_name,
        'designation_id': designation_id,
        'notifications': request.user.notifications.all(),
        'path_parent': 'compose'
    }
    return render(request, 'filetracking/composefile.html', context)


@login_required(login_url="/accounts/login")
@user_is_student
@dropdown_designation_valid
def draft_design(request):
    """ 
    This function redirects the user to the drafts page of designation selected in dropdown 
     @param:
            request - trivial.
    """

    dropdown_design = request.session.get(
        'currentDesignationSelected', 'default_value')
    username = request.user
    dropdown_HoldsDesignation_obj = get_HoldsDesignation_obj(
        username, dropdown_design)

    return redirect('/filetracking/drafts/' + str(dropdown_HoldsDesignation_obj.id))


@login_required(login_url="/accounts/login")
@user_is_student
@dropdown_designation_valid
def drafts_view(request, id):
    """
    This function is used to view all the drafts created by the user ordered by upload date.it collects all the created files from File object.

    @param:
      request - trivial
      id - user id 

    @parameters
      draft - file obeject containing all the files created by user
      context - holds data needed to render the template

    """
    user_HoldsDesignation_obj = HoldsDesignation.objects.select_related(
        'user', 'working', 'designation').get(pk=id)
    s = str(user_HoldsDesignation_obj).split(" - ")
    designation = s[1]
    draft_files = view_drafts(
        username=user_HoldsDesignation_obj.user, 
        designation=user_HoldsDesignation_obj.designation,
        src_module='filetracking'
        )

    # Correct upload_date type
    for f in draft_files:
        f['upload_date'] = parse_datetime(f['upload_date'])
        f['uploader'] = get_extra_info_object_from_id(f['uploader'])

    draft_files = add_uploader_department_to_files_list(draft_files)

    context = {
        'draft_files': draft_files,
        'designations': designation,
        'notifications': request.user.notifications.all(),
        'path_parent': 'draft'
    }
    return render(request, 'filetracking/drafts.html', context)


@login_required(login_url="/accounts/login")
@user_is_student
@dropdown_designation_valid
def outbox_view(request):
    """
    The function is used to get all the files sent by user(employee) to other employees
    which are filtered from Tracking(table) objects by current user i.e. current_id.
    It displays files sent by user to other employees of a Tracking(table) of filetracking(model)
    in the 'Outbox' tab of template.

    @param:
            request - trivial.
            id - user id 

    @variables:
            outward_files - File objects filtered by current_id i.e, present working user.
            context - Holds data needed to make necessary changes in the template.
    """
    dropdown_design = request.session.get('currentDesignationSelected', 'default_value')
    username = request.user
    user_HoldsDesignation_obj = get_HoldsDesignation_obj(username, dropdown_design)
    s = str(user_HoldsDesignation_obj).split(" - ")
    designation = s[1]

    outward_files = view_outbox(username=user_HoldsDesignation_obj.user,
                                designation=user_HoldsDesignation_obj.designation,
                                src_module='filetracking')

    for f in outward_files:
        last_forw_tracking = get_last_forw_tracking_for_user(file_id=f['id'],
                                                             username=user_HoldsDesignation_obj.user,
                                                             designation=user_HoldsDesignation_obj.designation)
        f['sent_to_user'] = last_forw_tracking.receiver_id
        f['sent_to_design'] = last_forw_tracking.receive_design
        f['last_sent_date'] = last_forw_tracking.forward_date
        f['upload_date'] = parse_datetime(f['upload_date'])
        f['uploader'] = get_extra_info_object_from_id(f['uploader'])

    subject_query = request.GET.get('subject', '')
    sent_to_query = request.GET.get('sent_to', '')
    date_query = request.GET.get('date', '')

    if subject_query:
        outward_files = [f for f in outward_files if subject_query.lower() in f['subject'].lower()]
    if sent_to_query:
        outward_files = [f for f in outward_files if sent_to_query.lower() in f['sent_to_user'].username.lower()]
    if date_query:
        try:
            search_date = datetime.strptime(date_query, '%Y-%m-%d')
            outward_files = [f for f in outward_files if f['last_sent_date'].date() == search_date.date()]
        except ValueError:
            outward_files = []  # Invalid date format

    paginator = Paginator(outward_files, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'viewer_designation': designation,
        'notifications': request.user.notifications.all(),
        'path_parent': 'outbox',
    }
    return render(request, 'filetracking/outbox.html', context)


@login_required(login_url="/accounts/login")
@user_is_student
@dropdown_designation_valid
def inbox_view(request):
    """
    The function is used to fetch the files received by the user form other employees. 
    These files are filtered by receiver id and ordered by receive date.

         @param:
                request - trivial.
                id - HoldsDesignation object id

        @variables: 
                inward_files - File object with additional sent by information
                context - Holds data needed to make necessary changes in the template. 

    """
    dropdown_design = request.session.get(
        'currentDesignationSelected', 'default_value')
    username = request.user
    user_HoldsDesignation_obj = get_HoldsDesignation_obj(
        username, dropdown_design)
    s = str(user_HoldsDesignation_obj).split(" - ")
    designation = s[1]
    inward_files = view_inbox(
        username=user_HoldsDesignation_obj.user, 
        designation=user_HoldsDesignation_obj.designation,
        src_module='filetracking'
        )

    # correct upload_date type and add recieve_date
    for f in inward_files:
        f['upload_date'] = parse_datetime(f['upload_date'])

        last_recv_tracking = get_last_recv_tracking_for_user(file_id=f['id'], 
                                                            username=user_HoldsDesignation_obj.user,
                                                            designation=user_HoldsDesignation_obj.designation)
        f['receive_date'] = last_recv_tracking.receive_date
        f['uploader'] = get_extra_info_object_from_id(f['uploader'])
        f['is_forwarded'] = (False if (str(get_current_file_owner(f['id']).username) == str(user_HoldsDesignation_obj.user)) else True)

        
    inward_files = add_uploader_department_to_files_list(inward_files)

    subject_query = request.GET.get('subject', '')
    sent_to_query = request.GET.get('sent_to', '')
    date_query = request.GET.get('date', '')

    if subject_query:
        inward_files = [f for f in inward_files if subject_query.lower() in f['subject'].lower()]
    if sent_to_query:
        inward_files = [f for f in inward_files if sent_to_query.lower() in f['sent_to_user'].username.lower()]
    if date_query:
        try:
            search_date = datetime.strptime(date_query, '%Y-%m-%d')
            inward_files = [f for f in inward_files if f['last_sent_date'].date() == search_date.date()]
        except ValueError:
            inward_files = []  # Invalid date format

    paginator = Paginator(inward_files, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'designations': designation,
        'notifications': request.user.notifications.all(),
        'path_parent': 'inbox'
    }
    return render(request, 'filetracking/inbox.html', context)


@login_required(login_url="/accounts/login")
@user_is_student
@dropdown_designation_valid
def outward(request):
    """ 
    This function redirects the user to the outbox page of designation selected in dropdown 
     @param:
            request - trivial.
    """

    dropdown_design = request.session.get(
        'currentDesignationSelected', 'default_value')
    username = request.user
    dropdown_HoldsDesignation_obj = get_HoldsDesignation_obj(
        username, dropdown_design)

    return redirect('/filetracking/outbox/' + str(dropdown_HoldsDesignation_obj.id))




@login_required(login_url="/accounts/login")
@user_is_student
@dropdown_designation_valid
def inward(request):
    """ 
    This function redirects the user to the inbox page of designation selected in dropdown 
     @param:
            request - trivial.
    """

    dropdown_design = request.session.get(
        'currentDesignationSelected', 'default_value')
    username = request.user
    dropdown_HoldsDesignation_obj = get_HoldsDesignation_obj(
        username, dropdown_design)

    return redirect('/filetracking/inbox/' + str(dropdown_HoldsDesignation_obj.id))


@login_required(login_url = "/accounts/login")
@user_is_student
@dropdown_designation_valid
def confirmdelete(request,id):
    """
     The function is used to confirm the deletion of a file.
        @param:
                request - trivial.
                id - user id

        @variables:
                 context - Holds data needed to make necessary changes in the template.   
    """
    file = File.objects.select_related(
        'uploader__user', 'uploader__department', 'designation').get(pk=id)

    context = {
        'j': file,
    }

    return render(request, 'filetracking/confirmdelete.html', context)

@login_required(login_url="/accounts/login")
@user_is_student
@dropdown_designation_valid
def view_file(request, id): 
    ''' 
    This function is used to view a particular file received by an employee from another.
    This function also conditionally renders two forms 'forward_file' and 'archive_file'
    based on if the user has necessary permissions or not. 
    The business permissions are as follows: 
        1. User can forward file only if they are the last recipient of the file 
        2. User can archive a file only if they have received it last and they are also the original owner of the file

    To forward the file and to archive the file separate views with POST request are called
        
    It displays the details file of a File and remarks as well as the attachments of all the users 
    who have been involved till that point of the workflow.

    @param:
        request - Trivial.
        id - ID of the file object which the user intends to forward to another employee.

    @variables:
        file - The File object.
        track - The Tracking object.
        designation - the designations of the user
    '''

    file = get_object_or_404(File, id=id)
    track = Tracking.objects.select_related('file_id__uploader__user', 'file_id__uploader__department', 'file_id__designation', 'current_id__user', 'current_id__department',
                                            'current_design__user', 'current_design__working', 'current_design__designation', 'receiver_id', 'receive_design').filter(file_id=file).order_by('receive_date')
    designations = get_designation(request.user)

    forward_enable = False
    archive_enable = False

    current_owner = get_current_file_owner(file.id)
    file_uploader = get_user_object_from_username(file.uploader.user.username) 

    last_receiver_designation = get_current_file_owner_designation(file.id).name

    if current_owner == request.user and file.is_read is False: 
        forward_enable = True
    if current_owner == request.user and last_receiver_designation == file.designation.name and file_uploader == request.user and file.is_read is False:
        archive_enable = True

    parent_of_prev_path = request.META.get('HTTP_REFERER').strip("/").split('/')[-2]
    context = {
        'designations': designations,
        'file': file,
        'track': track,
        'forward_enable': forward_enable, 
        'archive_enable': archive_enable,
        'notifications': request.user.notifications.all(),
        'path_parent': parent_of_prev_path
    }
    return render(request, 'filetracking/viewfile.html', context)

@login_required(login_url="/accounts/login")
@user_is_student
@dropdown_designation_valid
def archive_file(request, id): 
    '''This function is used to archive a file.
       It returns unauthorized access if the user is not file uploader 
       and the current owner of the file
    '''
    if request.method == "POST":
        file = get_object_or_404(File, id=id)
        current_owner = get_current_file_owner(file.id)
        file_uploader = get_user_object_from_username(file.uploader.user.username)
        if current_owner == request.user and file_uploader == request.user:
            file.is_read = True
            file.save()
            messages.success(request, 'File Archived')
        else: 
            messages.error(request, 'Unauthorized access')

        return render(request, 'filetracking/composefile.html')

@login_required(login_url="/accounts/login")
@user_is_student
@dropdown_designation_valid
def forward(request, id):
    """
            The function is used to forward files received by user(employee) from other
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

    file = get_object_or_404(File, id=id)
    track = Tracking.objects.select_related('file_id__uploader__user', 'file_id__uploader__department', 'file_id__designation', 'current_id__user', 'current_id__department',
                                            'current_design__user', 'current_design__working', 'current_design__designation', 'receiver_id', 'receive_design').filter(file_id=file).order_by('receive_date')

    designations = get_designation(request.user)

    designation_name = request.session.get('currentDesignationSelected', 'default_value')
    all_available_designations = request.session.get(
        'allDesignations', 'default_value2')

    username = request.user
    designation_id = get_HoldsDesignation_obj(
        username, designation_name).id

    if request.method == "POST":
        if 'finish' in request.POST:
            file.is_read = True
            file.save()
        if 'send' in request.POST:
            current_id = request.user.extrainfo
            remarks = request.POST.get('remarks')
            track.update(is_read=True)

            sender = request.POST.get('sender')
            current_design = HoldsDesignation.objects.select_related(
                'user', 'working', 'designation').get(id=sender)

            receiver = request.POST.get('receiver')
            try:
                receiver_id = User.objects.get(username=receiver)
            except Exception as e:
                messages.error(request, 'Enter a valid destination')
                designations = HoldsDesignation.objects.select_related(
                    'user', 'working', 'designation').filter(user=request.user)

                context = {
                    'designations': designations,
                    'file': file,
                    'track': track,
                    'designation_name': designation_name,
                    'designation_id': designation_id,
                    'notifications': request.user.notifications.all(),
                    'path_parent': 'inbox'
                }

                return render(request, 'filetracking/forward.html', context)
            receive = request.POST.get('receive')
            try:
                receive_design = Designation.objects.get(name=receive)
            except Exception as e:
                messages.error(request, 'Enter a valid Designation')
                designations = get_designation(request.user)

                context = {
                    'designations': designations,
                    'file': file,
                    'track': track,
                    'designation_name': designation_name,
                    'designation_id': designation_id,
                    'notifications': request.user.notifications.all(),
                    'path_parent': 'inbox'
                }

                return render(request, 'filetracking/forward.html', context)

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
        file_tracking_notif(request.user, receiver_id, file.subject)
        messages.success(request, 'File sent successfully')
        return redirect(reverse('filetracking:filetracking'))

    context = {
        'designations': designations,
        'file': file,
        'track': track,
        'designation_name': designation_name,
        'designation_id': designation_id,
        'notifications': request.user.notifications.all(),
        'path_parent': 'inbox'
    }

    return render(request, 'filetracking/forward.html', context)


@login_required(login_url="/accounts/login")
@user_is_student
@dropdown_designation_valid
def archive_design(request):
    """ 
    This function redirects the user to the archive page of designation selected in dropdown 
     @param:
            request - trivial.
    """

    dropdown_design = request.session.get(
        'currentDesignationSelected', 'default_value')
    username = request.user
    dropdown_HoldsDesignation_obj = get_HoldsDesignation_obj(
        username, dropdown_design)

    return redirect('/filetracking/archive/' + str(dropdown_HoldsDesignation_obj.id))


@login_required(login_url="/accounts/login")
@user_is_student
@dropdown_designation_valid
def archive_view(request, id):
    """
    The function is used to fetch the files in the user's archive 
    (those which have passed by user and been archived/finished) 

    @param:
        request - trivial.
        id - HoldsDesignation object id

    @variables: 
        archive_files - File object with additional information
        context - Holds data needed to make necessary changes in the template. 

    """
    user_HoldsDesignation_obj = HoldsDesignation.objects.select_related(
        'user', 'working', 'designation').get(pk=id)
    s = str(user_HoldsDesignation_obj).split(" - ")
    designation = s[1]

    archive_files = view_archived(
        username=user_HoldsDesignation_obj.user, 
        designation=user_HoldsDesignation_obj.designation,
        src_module='filetracking'
    )

    # correct upload_date type and add receive_date
    for f in archive_files:
        f['upload_date'] = parse_datetime(f['upload_date'])
        f['designation'] = Designation.objects.get(id=f['designation'])
        f['uploader'] = get_extra_info_object_from_id(f['uploader'])

    archive_files = add_uploader_department_to_files_list(archive_files)

    context = {
        'archive_files': archive_files,
        'designations': designation,
        'notifications': request.user.notifications.all(),
        'path_parent': 'archive'
    }
    return render(request, 'filetracking/archive.html', context)



@login_required(login_url="/accounts/login")
@user_is_student
@dropdown_designation_valid
def archive_finish(request, id):
    file1 = get_object_or_404(File, id=id)
    track = Tracking.objects.filter(file_id=file1)

    return render(request, 'filetracking/archive_finish.html', {'file': file1, 'track': track})


@login_required(login_url="/accounts/login")
@user_is_student
@dropdown_designation_valid
def finish_design(request):

    designation = HoldsDesignation.objects.select_related(
        'user', 'working', 'designation').filter(user=request.user)

    context = {
        'designation': designation,
        'notifications': request.user.notifications.all()
    }
    return render(request, 'filetracking/finish_design.html', context)


@login_required(login_url="/accounts/login")
@user_is_student
@dropdown_designation_valid
def finish_fileview(request, id):

    out = Tracking.objects.select_related('file_id__uploader__user', 'file_id__uploader__department', 'file_id__designation', 'current_id__user', 'current_id__department',
                                          'current_design__user', 'current_design__working', 'current_design__designation', 'receiver_id', 'receive_design').filter(file_id__uploader=request.user.extrainfo, is_read=False).order_by('-forward_date')

    abcd = HoldsDesignation.objects.select_related(
        'user', 'working', 'designation').get(pk=id)

    context = {

        'out': out,
        'abcd': abcd,
        'notifications': request.user.notifications.all()
    }
    return render(request, 'filetracking/finish_fileview.html', context)


@login_required(login_url="/accounts/login")
@user_is_student
@dropdown_designation_valid
def finish(request, id):
    # file = get_object_or_404(File, ref_id=id)
    file1 = get_object_or_404(File, id=id)
    track = Tracking.objects.filter(file_id=file1)

    if request.method == "POST":
        if 'Finished' in request.POST:
            File.objects.filter(pk=id).update(is_read=True)
            track.update(is_read=True)
            messages.success(request, 'File Archived')

    context = {
        'file': file1, 
        'track': track, 
        'fileid': id,
        'notifications': request.user.notifications.all()
        }

    return render(request, 'filetracking/finish.html', )

def AjaxDropdown1(request):

    """
    This function returns the designation of receiver on the forward or compose file template.

     @param:
            request - trivial.


    @variables: 
         context - return the httpresponce containing the matched designation of the user
    """
    if request.method == 'POST':
        value = request.POST.get('value')

        hold = Designation.objects.filter(name__startswith=value)
        holds = serializers.serialize('json', list(hold))
        context = {
            'holds': holds
        }

        return HttpResponse(JsonResponse(context), content_type='application/json')


def AjaxDropdown(request):
    """
    This function returns the usernames of receiver on the forward or compose file template.

     @param:
            request - trivial.


    @variables: 
         context - return the httpresponce containing the matched username
    """
    if request.method == 'POST':
        value = request.POST.get('value')
        users = User.objects.filter(username__startswith=value)
        users = serializers.serialize('json', list(users))

        context = {
            'users': users
        }
        return HttpResponse(JsonResponse(context), content_type='application/json')



@login_required(login_url = "/accounts/login")
@user_is_student
@dropdown_designation_valid
def delete(request,id):
    """ 
     The function is used the delete of a file and it returns to the drafts page. 

        @param:
            request - trivial.
            id - id of the file that is going to be deleted

    """
    file = File.objects.get(pk=id)
    file.delete()
    return redirect('/filetracking/draftdesign/')


@user_is_student
@dropdown_designation_valid
def forward_inward(request,id):
    """ This function is used forward the files which are available in the inbox of the user .

        @param:
            request - trivial
            id - id of the file that is going to forward

        @variables:
            file - file object 
            track - tracking object of the file
            context - necessary data to render

    """

    file = get_object_or_404(File, id=id)
    file.is_read = True
    track = Tracking.objects.select_related('file_id__uploader__user', 'file_id__uploader__department', 'file_id__designation', 'current_id__user', 'current_id__department',
                                            'current_design__user', 'current_design__working', 'current_design__designation', 'receiver_id', 'receive_design').filter(file_id=file)
    designations = get_designation(request.user)

    context = {

        'designations': designations,
        'file': file,
        'track': track,
        'notifications': request.user.notifications.all()
    }
    return render(request, 'filetracking/forward.html', context)

def get_designations_view(request, username):
    designations = get_designations(username)
    return JsonResponse(designations, safe=False)

def unarchive_file(request, id): 
    try:
        file = get_object_or_404(File, id=id)
        file.is_read = False
        file.save()
        messages.success(request, 'File unarchived')
    except File.DoesNotExist:
        messages.error(request, 'File does not exist')
    except Exception as e: 
        messages.error(request, 'Unable to unarchive: {}'.format(str(e)))

    return render(request, 'filetracking/archive.html')
    

@login_required(login_url="/accounts/login")
@user_is_student
@dropdown_designation_valid
def edit_draft_view(request, id, *args, **kwargs):
    """
            The function is used to edit and send drafted files, and also alter their title and subject 
            along with their remarks and attachments

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

    file = get_object_or_404(File, id=id)
    track = Tracking.objects.select_related('file_id__uploader__user', 'file_id__uploader__department', 'file_id__designation', 'current_id__user', 'current_id__department',
                                            'current_design__user', 'current_design__working', 'current_design__designation', 'receiver_id', 'receive_design').filter(file_id=file).order_by('receive_date')

    if request.method == "POST":
        if 'send' in request.POST:
            current_id = request.user.extrainfo
            remarks = request.POST.get('remarks')
            subject = request.POST.get('subject')
            description = request.POST.get('description')

            file.subject = subject
            file.description = description
            file.save()
            track.update(is_read=True)

            sender = request.POST.get('sender')
            current_design = HoldsDesignation.objects.select_related(
                'user', 'working', 'designation').get(id=sender)

            receiver = request.POST.get('receiver')
            try:
                receiver_id = User.objects.get(username=receiver)
            except Exception as e:
                messages.error(request, 'Enter a valid destination')
                designations = HoldsDesignation.objects.select_related(
                    'user', 'working', 'designation').filter(user=request.user)

                context = {

                    'designations': designations,
                    'file': file,
                    'track': track,
                    'notifications': request.user.notifications.all()
                }
                return redirect(reverse('filetracking:filetracking'))

            receive = request.POST.get('receive')
            try:
                receive_design = Designation.objects.get(name=receive)
            except Exception as e:
                messages.error(request, 'Enter a valid Designation')
                designations = get_designation(request.user)

                context = {

                    'designations': designations,
                    'file': file,
                    'notifications': request.user.notifications.all()
                }
                return redirect(reverse('filetracking:filetracking'))

            upload_file = request.FILES.get('myfile')

            if upload_file is None and file.upload_file is not None: 
                upload_file = file.upload_file

            # since frontend isnt reflecting uploaded file in edit draft, but upload_file may exist in File
            # (this feature isnt working atm, duplicate is still stored)
            #if upload_file == file.upload_file:
            #    upload_file = None

            Tracking.objects.create(
                file_id=file,
                current_id=current_id,
                current_design=current_design,
                receive_design=receive_design,
                receiver_id=receiver_id,
                remarks=remarks,
                upload_file=upload_file,
            )
            
        file_tracking_notif(request.user, receiver_id, subject)
        messages.success(request, 'File sent successfully')
        return render(request, 'filetracking/composefile.html')

    designations = get_designation(request.user)

    designation_name = request.session.get('currentDesignationSelected', 'default_value')
    all_available_designations = request.session.get(
        'allDesignations', 'default_value2')


    username = request.user
    designation_id = get_HoldsDesignation_obj(
        username, designation_name).id

    remarks = None
    receive = None
    receiver = None

    if file.file_extra_JSON and file.file_extra_JSON['remarks']:
        remarks = file.file_extra_JSON['remarks']

    context = {
        'designations': designations,
        'file': file,
        'track': track,        
        'designation_name': designation_name,
        'designation_id': designation_id,
        'remarks' : remarks,
        'notifications': request.user.notifications.all()
    }

    return render(request, 'filetracking/editdraft.html', context)


@login_required(login_url="/accounts/login/")
@user_is_student
@dropdown_designation_valid
@require_POST
def download_file(request, id):
    file = get_object_or_404(File, id=id)
    track = Tracking.objects.select_related('file_id__uploader__user', 'file_id__uploader__department', 'file_id__designation', 'current_id__user', 'current_id__department',
                                            'current_design__user', 'current_design__working', 'current_design__designation', 'receiver_id', 'receive_design').filter(file_id=id).order_by('receive_date')

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    style_heading = styles['Heading1']
    style_paragraph = styles['BodyText']

    elements.append(
        Paragraph(f"<center><b>Subject - {file.subject}</b></center>", style_heading))
    elements.append(Spacer(1, 12))
    elements.append(
        Paragraph(f"<b>Description:</b> {file.description}", style_paragraph))
    elements.append(Spacer(1, 12))

    for t in track:
        sent_by = f"<b>Sent by:</b> {t.current_design} - {t.forward_date.strftime('%B %d, %Y %I:%M %p')}"
        received_by = f"<b>Received by:</b> {t.receiver_id} - {t.receive_design}"
        combined_info = f"{sent_by} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {received_by}"
        elements.append(Paragraph(combined_info, style_paragraph))
        elements.append(Spacer(1, 12))
        remarks = f"<b>Remarks:</b> {t.remarks}" if t.remarks else "<b>Remarks:</b> No Remarks"
        elements.append(Paragraph(remarks, style_paragraph))
        elements.append(Spacer(1, 12))
        attachment = f"<b>Attachment:</b> {os.path.basename(t.upload_file.name)}" if t.upload_file else "<b>Attachment:</b> No attachments"
        elements.append(Paragraph(attachment, style_paragraph))
        elements.append(Paragraph('<hr width="100%" style="border-top: 1px solid #ccc;">', style_paragraph))
        elements.append(Spacer(2, 12))

    doc.build(elements)
    pdf_data = buffer.getvalue()
    buffer.close()

    formal_filename = f'{file.uploader.department.name}-{file.upload_date.year}-{file.upload_date.month}-#{file.id}'
    output_filename = f'iiitdmj-fts-{formal_filename}'

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        pdf_filename = f'{file.uploader.department.name}-{file.upload_date.year}-{file.upload_date.month}-#{file.id}-notesheet.pdf'
        zip_file.writestr(output_filename+'.pdf', pdf_data)
        for t in track:
            if t.upload_file:
                zip_file.write(t.upload_file.path,
                               os.path.basename(t.upload_file.name))

    zip_data = zip_buffer.getvalue()
    zip_buffer.close()

    response = HttpResponse(zip_data, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{output_filename}.zip"'

    return response
