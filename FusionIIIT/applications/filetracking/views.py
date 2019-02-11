from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.template.defaulttags import csrf_token

from applications.globals.models import (Designation, ExtraInfo,
                                         HoldsDesignation)

from .models import File, Tracking


@login_required(login_url = "/accounts/login/")
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
    if request.method =="POST":
        try:
            if 'save' in request.POST:
                uploader = request.user.extrainfo
                #ref_id = request.POST.get('fileid')
                subject = request.POST.get('title')
                description = request.POST.get('desc')
                design = request.POST.get('design')
                designation = Designation.objects.get(name=design)
                upload_file = request.FILES.get('myfile')

                File.objects.create(
                    uploader=uploader,
                    #ref_id=ref_id,
                    description=description,
                    subject=subject,
                    designation=designation,
                    upload_file=upload_file
                )
        except IntegrityError:
            message = "FileID Already Taken.!!"
            return HttpResponse(message)

    else:
        print("")
    file = File.objects.all()
    extrainfo = ExtraInfo.objects.all()
    holdsdesignations = HoldsDesignation.objects.all()
    designations = HoldsDesignation.objects.filter(user = request.user)

    context = {
        'file': file,
        'extrainfo': extrainfo,
        'holdsdesignations': holdsdesignations,
        'designations': designations,
    }
    return render(request, 'filetracking/composefile.html', context)


@login_required(login_url = "/accounts/login")
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

    draft = File.objects.filter(uploader=request.user.extrainfo)
    extrainfo = ExtraInfo.objects.all()

    context = {
        'draft': draft,
        'extrainfo': extrainfo,
    }
    return render(request, 'filetracking/drafts.html', context)


@login_required(login_url = "/accounts/login")
def outward(request):
    """
        The function is used to get all the files sent by user(employee) to other employees
        which are filtered from Tracking(table) objects by current user i.e. current_id.
        It displays files sent by user to other employees of a Tracking(table) of filetracking(model)
        in the 'Outbox' tab of template.

        @param:
                request - trivial.

        @variables:
                out - The Tracking object filtered by current_id i.e, present working user.
                context - Holds data needed to make necessary changes in the template.
    """
    out = Tracking.objects.filter(current_id=request.user.extrainfo)

    context = {
        'out': out,
    }
    return render( request, 'filetracking/outward.html', context)


@login_required(login_url = "/accounts/login")
def inward(request):
    """
            The function is used to get all the files received by user(employee) from other
            employees which are filtered from Tracking(table) objects by current user i.e.receiver_id.
            It displays files received by user from other employees of a Tracking(table) of
            filetracking(model) in the 'Inbox' tab of template.

            @param:
                    request - trivial.

            @variables:
                    in_file - The Tracking object filtered by receiver_id i.e, present working user.
                    context - Holds data needed to make necessary changes in the template.
    """

    in_file = Tracking.objects.filter(receiver_id=request.user.extrainfo)

    context = {
        'in_file': in_file,
    }

    return render(request, 'filetracking/inward.html', context)


@login_required(login_url = "/accounts/login")
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
    track = Tracking.objects.filter(file_id=file)

    if request.method == "POST":
            if 'finish' in request.POST:
                file.complete_flag = True
                file.save()

            if 'send' in request.POST:
                current_id = request.user.extrainfo
                remarks = request.POST.get('remarks')
                sender = request.POST.get('sender')
                current_design = HoldsDesignation.objects.get(id=sender)
                receiver = request.POST.get('receiver')
                receiver_id = ExtraInfo.objects.get(id=receiver)
                receive = request.POST.get('receive')
                receive_design = HoldsDesignation.objects.get(id=receive)
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

    extrainfo = ExtraInfo.objects.all()
    holdsdesignations = HoldsDesignation.objects.all()
    designations = HoldsDesignation.objects.filter(user=request.user)

    context = {
        'extrainfo': extrainfo,
        'holdsdesignations': holdsdesignations,
        'designations':designations,
        'file': file,
        'track': track,
    }

    return render(request, 'filetracking/forward.html', context)

@login_required(login_url = "/accounts/login")
def archive(request):
    return render(request, 'filetracking/archive.html')


@login_required(login_url = "/accounts/login")
def finish(request, id):
    file = get_object_or_404(File, ref_id=id)
    track = Tracking.objects.filter(file_id=file)

    return render(request, 'filetracking/finish.html', {'file': file, 'track': track})
