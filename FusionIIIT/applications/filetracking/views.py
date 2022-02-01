from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from .models import File, Tracking
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation
from django.template.defaulttags import csrf_token
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.core import serializers
from django.contrib.auth.models import User
from timeit import default_timer as time
from notification.views import office_module_notif


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
                subject = request.POST.get('title')
                description = request.POST.get('desc')
                design = request.POST.get('design')
                designation = Designation.objects.get(id = HoldsDesignation.objects.select_related('user','working','designation').get(id = design).designation_id)
                upload_file = request.FILES.get('myfile')

                File.objects.create(
                    uploader=uploader,
                    description=description,
                    subject=subject,
                    designation=designation,
                    upload_file=upload_file
                )

            if 'send' in request.POST:
                uploader = request.user.extrainfo
                subject = request.POST.get('title')
                description = request.POST.get('desc')
                design = request.POST.get('design')
                designation = Designation.objects.get(id = HoldsDesignation.objects.select_related('user','working','designation').get(id = design).designation_id)

                upload_file = request.FILES.get('myfile')

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
                office_module_notif(request.user, receiver_id)
                messages.success(request,'File sent successfully')

        except IntegrityError:
            message = "FileID Already Taken.!!"
            return HttpResponse(message)



    file = File.objects.select_related('uploader__user','uploader__department','designation').all()
    extrainfo = ExtraInfo.objects.select_related('user','department').all()
    holdsdesignations = HoldsDesignation.objects.select_related('user','working','designation').all()
    designations = HoldsDesignation.objects.select_related('user','working','designation').filter(user = request.user)

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

    # draft = File.objects.filter(uploader=request.user.extrainfo)
    # draft = File.objects.filter(uploader=request.user.extrainfo).order_by('-upload_date')

    # extrainfo = ExtraInfo.objects.all()
    # designation = Designation.objects.get(id=HoldsDesignation.objects.get(user=request.user).designation_id)
    designation = HoldsDesignation.objects.select_related('user','working','designation').filter(user=request.user)
    context = {
        # 'draft': draft,
        # 'extrainfo': extrainfo,
        'designation': designation,
    }
    return render(request, 'filetracking/drafts.html', context)

@login_required(login_url = "/accounts/login")
def fileview(request,id):



    draft = File.objects.select_related('uploader__user','uploader__department','designation').filter(uploader=request.user.extrainfo).order_by('-upload_date')


    extrainfo = ExtraInfo.objects.select_related('user','department').all()
    # designations = Designation.objects.filter(upload_designation=extrainfo.id)
    abcd = HoldsDesignation.objects.select_related('user','working','designation').get(pk=id)
    s = str(abcd).split(" - ")
    designations = s[1]
    #designations = HoldsDesignation.objects.filter(user=request.user)
    # for x in designations:
    #  if abcd==x:
    #      designations=abcd

    context = {

        'draft': draft,
        'extrainfo': extrainfo,
        'designations': designations,
    }
    return render(request, 'filetracking/fileview.html', context)
@login_required(login_url = "/accounts/login")
def fileview1(request,id):



    out = Tracking.objects.select_related('file_id__uploader__user','file_id__uploader__department','file_id__designation','current_id__user','current_id__department',
    'current_design__user','current_design__working','current_design__designation','receiver_id','receive_design').filter(current_id=request.user.extrainfo).order_by('-forward_date')




    abcd = HoldsDesignation.objects.select_related('user','working','designation').get(pk=id)


    context = {

        'out': out,
        'abcd': abcd,
    }
    return render(request, 'filetracking/fileview1.html', context)
@login_required(login_url = "/accounts/login")
def fileview2(request,id):



    in_file = Tracking.objects.select_related('file_id__uploader__user','file_id__uploader__department','file_id__designation','current_id__user','current_id__department',
'current_design__user','current_design__working','current_design__designation','receiver_id','receive_design').filter(receiver_id=request.user).order_by('-receive_date')




    abcd = HoldsDesignation.objects.select_related('user','working','designation').get(pk=id)
    s = str(abcd).split(" - ")
    designations = s[1]

    context = {

        'in_file': in_file,
        'designations': designations,
    }
    return render(request, 'filetracking/fileview2.html', context)
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
    designation = HoldsDesignation.objects.select_related('user','working','designation').filter(user=request.user)

    context = {
        'designation': designation,
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
    designation = HoldsDesignation.objects.select_related('user','working','designation').filter(user=request.user)
    in_file = Tracking.objects.select_related('file_id__uploader__user','file_id__uploader__department','file_id__designation','current_id__user','current_id__department',
'current_design__user','current_design__working','current_design__designation','receiver_id','receive_design').filter(receiver_id=request.user).order_by('-receive_date')

    context = {
        'in_file': in_file,
        'designation': designation,
    }

    return render(request, 'filetracking/inward.html', context)
@login_required(login_url = "/accounts/login")
def confirmdelete(request,id):
    file = File.objects.select_related('uploader__user','uploader__department','designation').get(pk = id)

    context = {

        'j': file,
    }
    return render(request, 'filetracking/confirmdelete.html',context)

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
    # start = timer()
    file = get_object_or_404(File, id=id)
    # end = timer()

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
                    return render(request, 'filetracking/forward.html', context)
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
                    return render(request, 'filetracking/forward.html', context)

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
            messages.success(request, 'File sent successfully')
    # start = timer()
    extrainfo = ExtraInfo.objects.select_related('user','department').all()
    holdsdesignations = HoldsDesignation.objects.select_related('user','working','designation').all()
    designations = HoldsDesignation.objects.select_related('user','working','designation').filter(user=request.user)

    context = {
        # 'extrainfo': extrainfo,
        # 'holdsdesignations': holdsdesignations,
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

def AjaxDropdown1(request):
    if request.method == 'POST':
        value = request.POST.get('value')

        hold = Designation.objects.filter(name__startswith=value)
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
def delete(request,id):
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

    return redirect('/filetracking/drafts/')

def forward_inward(request,id):
    file = get_object_or_404(File, id=id)
    file.is_read = True
    track = Tracking.objects.select_related('file_id__uploader__user','file_id__uploader__department','file_id__designation','current_id__user','current_id__department',
'current_design__user','current_design__working','current_design__designation','receiver_id','receive_design').filter(file_id=file)
    extrainfo = ExtraInfo.objects.select_related('user','department').all()
    holdsdesignations = HoldsDesignation.objects.select_related('user','working','designation').all()
    designations = HoldsDesignation.objects.select_related('user','working','designation').filter(user=request.user)

    context = {
        # 'extrainfo': extrainfo,
        # 'holdsdesignations': holdsdesignations,
        'designations':designations,
        'file': file,
        'track': track,
    }
    return render(request, 'filetracking/forward.html', context)


