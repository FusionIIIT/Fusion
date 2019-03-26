from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.defaulttags import csrf_token
from django.contrib.auth.models import User
from django.core import serializers

from applications.globals.models import (Designation, ExtraInfo,
                                         HoldsDesignation)

from .models import File, Tracking
from django.db.models  import Q


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

    if request.method == "POST":

        #form = userform(request.POST or None)
        # if form.is_valid():
        #     uploader = request.user.extrainfo
        #     #ref_id = request.POST.get('fileid')
        #     subject = request.POST.get('title')
        #     description = request.POST.get('desc')
        #     design = request.POST.get('design')
        #     designation = Designation.objects.get(name=design)
        #     upload_file = request.FILES.get('myfile')

        #     File.objects.create(
        #         uploader=uploader,
        #         #ref_id=ref_id,
        #         description=description,
        #         subject=subject,
        #         designation=designation,
        #         upload_file=upload_file
        #     )

    # return render(request, 'your_template.html', {'form': form})
        try:
            if 'save' in request.POST:
                print(request.POST.get('design'))
                # print("656+5+656+56+5656+56+56+5+656+56+56+56+56+566+56+5")

                #ref_id = request.POST.get('fileid')

                if request.POST.get('design')=="Select":
                    messages.error(request,'Fill the required details to create the file')
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



                else :
                    # print("5646464654564564")
                    uploader = request.user.extrainfo
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
                    messages.success(request,'File created successfully')
        except IntegrityError:
            message = "FileID Already Taken.!!"
            return HttpResponse(message)




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
    # draft = File.objects.order_by('upload_date')
    draft = File.objects.filter(uploader=request.user.extrainfo).order_by('-upload_date')


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

    # if request.method == "POST" :

    #     remarks = request.POST.get('remarks')
    #     reciever = request.POST.get('reciever')
    #     reciever_designation = request.POST.get('reciever_designation')
    #     sender = request.user
    #     sender_designation = request.POST.get('sender')
    #     attached_files = request.FILES['myfile']

    #     Tracking.objects.create(
    #         remarks = remarks,
    #         upload_file = attached_files,
    #         )



    out = Tracking.objects.filter(current_id=request.user.extrainfo)

    context = {
        'out': out,
    }
    return render( request, 'filetracking/outward.html', context)


@login_required(login_url = "/accounts/login")
def delete(request,id):
    file = File.objects.get(pk = id)
    file.delete()
    draft = File.objects.filter(uploader=request.user.extrainfo)
    extrainfo = ExtraInfo.objects.all()

    context = {
            'draft': draft,
        'extrainfo': extrainfo,
    }
    return render(request, 'filetracking/drafts.html', context)




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

def AjaxDropdown1(request):
    print('brefore post')
    if request.method == 'POST':
        value = request.POST.get('value')
        print(value)

        hold = Designation.objects.filter(name__startswith=value)
        # for h in hold:
        #     print(h)
        print('secnod method')
        holds = serializers.serialize('json', list(hold))
        context = {
        'holds' : holds
        }

        return HttpResponse(JsonResponse(context), content_type='application/json')



def AjaxDropdown(request, id):
    print('\n\n')
    # Name = ['student','co-ordinator','co co-ordinator']
    # design = Designation.objects.filter(~Q(name__in=(Name)))
    # hold = HoldsDesignation.objects.filter(Q(designation__in=(design)))

    # arr = []

    # for h in hold:
    #     arr.append(ExtraInfo.objects.filter(user=h.user))

    if request.method == 'POST':
        value = request.POST.get('value')
        print(value)

        users = User.objects.filter(username__startswith=value)
        users = serializers.serialize('json', list(users))

        context = {
            'users': users
        }
        return HttpResponse(JsonResponse(context), content_type='application/json')




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

    # extra = ExtraInfo.objects.get(id=2016226)
    # extra = User.objects.filter(Q(holdsdesignation__user=HoldsDesignation.objects.all()))
    # extra = get_object_or_404(User, id=request.user.id)
    # print(extra.holds_designations.all().count())
    # # for e in extra:
    # #     all_ = e.holds_designations.all()

    file = get_object_or_404(File, id=id)
    track = Tracking.objects.filter(file_id=file)
    design = (Designation.objects.all())
    # for d in design :
    #     print(d)
    Name = ['student','co-ordinator','co co-ordinator']
    design = Designation.objects.filter(~Q(name__in=(Name)))
    # print(design.count())
    # for d in design :
    #     print(d)
    hold = HoldsDesignation.objects.filter(Q(designation__in=(design)))
    # print(hold.count())

    # print(hold.filter(Q(user==User.objects.all())).distinct().count())

    # for h in hold:
    #     print(ExtraInfo.objects.filter(user=h.user))

    if request.method == "POST":
            # if 'finish' in request.POST:
            #     file.complete_flag = True
            #     file.save()

            if 'send' in request.POST:
                print("sucess")
                print(request.user)
                # getting user current information
                current_user_info = request.user.extrainfo
                remarks = request.POST.get('remarks')
                # id of sender designation
                sender_designation = request.POST.get('sender')
                print(sender_designation)
                # sender's current designation
                current_design = HoldsDesignation.objects.get(designation__id=sender_designation)
                print(current_design)
                # id of  receiver extrainfo
                receiver = request.POST.get('receiver')
                receiver_info = ExtraInfo.objects.get(user__username=receiver)
                # id of  reciever designation
                receive = request.POST.get('receive')
                print(receive)
                # receive_design = HoldsDesignation.objects.get(id=receive)
                # print(receive_design)
                upload_file = request.FILES.get('myfile')

                # Tracking.objects.create(
                #     file_id=file,
                #     current_id=current_user_info,
                #     current_design=current_design,
                #     receive_design=receive_design,
                #     receiver_id=receiver_info,
                #     remarks=remarks,
                #     upload_file=upload_file,
                # )

                return HttpResponse ("success")

    # extrainfo = ExtraInfo.objects.all()
    holdsdesignations = HoldsDesignation.objects.all()
    # print(holdsdesignations)
    print("take a break.....!!!!")
    # return JsonResponse(context)

    designations = HoldsDesignation.objects.filter(user=request.user)
    print(designations)
    print('coming')
    context = {
        # 'extrainfo': extrainfo,
        'holdsdesignations': hold,
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
