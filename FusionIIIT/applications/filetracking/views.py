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
from notification.views import office_module_notif,file_tracking_notif
from .utils import *


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
                if(upload_file.size / 1000 > 10240):
                    messages.error(request,"File should not be greater than 10MB")
                    return redirect("/filetracking")               

                File.objects.create(
                    uploader=uploader,
                    description=description,
                    subject=subject,
                    designation=designation,
                    upload_file=upload_file
                )

                messages.success(request,'File Draft Saved Successfully')

            if 'send' in request.POST:
                uploader = request.user.extrainfo
                subject = request.POST.get('title')
                description = request.POST.get('desc')
                design = request.POST.get('design')
                designation = Designation.objects.get(id = HoldsDesignation.objects.select_related('user','working','designation').get(id = design).designation_id)

                upload_file = request.FILES.get('myfile')
                if(upload_file.size / 1000 > 10240):
                    messages.error(request,"File should not be greater than 10MB")
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
                #office_module_notif(request.user, receiver_id)
                file_tracking_notif(request.user,receiver_id,subject)
                messages.success(request,'File sent successfully')

        except IntegrityError:
            message = "FileID Already Taken.!!"
            return HttpResponse(message)



    file = File.objects.select_related('uploader__user','uploader__department','designation').all()
    extrainfo = ExtraInfo.objects.select_related('user','department').all()
    holdsdesignations = HoldsDesignation.objects.select_related('user','working','designation').all()
    designations = get_designation(request.user)

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
        The function is used to get the designation of the user and renders it on draft template.

        @param:
                request - trivial.

        @variables:
                
                
                context - Holds data needed to make necessary changes in the template.
    """
    designation = get_designation(request.user)
    context = {
        'designation': designation,
    }
    return render(request, 'filetracking/drafts.html', context)


@login_required(login_url = "/accounts/login")
def fileview(request,id):

    """
    This function is used to veiw all all created files by the user ordered by upload date.it collects all the created files from File object.

    @param:
      request - trivial
      id - user id 

    @parameters
      draft - file obeject containing all the files created by user
      context - holds data needed to render the template
      

    
    """
    # draft = File.objects.select_related('uploader__user','uploader__department','designation').filter(uploader=request.user.extrainfo).order_by('-upload_date')
    # extrainfo = ExtraInfo.objects.select_related('user','department').all()

    extrainfo = ExtraInfo.objects.select_related('user','department').all()
  
    ids = File.objects.filter(uploader=request.user.extrainfo).order_by('-upload_date').values_list('id', flat=True)
    draft_files_pk=[]
    
    for i in ids: 
       file_tracking_ids = Tracking.objects.filter(file_id=i).values_list('id', flat=True)
       if(len(file_tracking_ids)==0):
        draft_files_pk.append(i)
    
    draft_file_list=[]
    for i in draft_files_pk:
        draft_file_list.append(File.objects.get(pk=i))



    user_designation = HoldsDesignation.objects.select_related('user','working','designation').get(pk=id)
    s = str(user_designation).split(" - ")
    designations = s[1]
    context = {

        'draft': draft_file_list,
        'extrainfo': extrainfo,
        'designations': designations,
    }
    return render(request, 'filetracking/fileview.html', context)



@login_required(login_url = "/accounts/login")
def fileview1(request,id):

    """
         The function is used to get all the files sent by user(employee) to other employees
        which are filtered from Tracking(table) objects by current user i.e. current_id.
        It displays files sent by user to other employees of a Tracking(table) of filetracking(model)
        in the 'Outbox' tab of template.

        @param:
                request - trivial.
                id - user id 

        @variables:
                out - The Tracking object filtered by current_id i.e, present working user.
                context - Holds data needed to make necessary changes in the template.
    
    """

    outward_files = Tracking.objects.select_related('file_id__uploader__user','file_id__uploader__department','file_id__designation','current_id__user','current_id__department',
    'current_design__user','current_design__working','current_design__designation','receiver_id','receive_design').filter(current_id=request.user.extrainfo).order_by('-forward_date')

    user_designation = HoldsDesignation.objects.select_related('user','working','designation').get(pk=id)

    context = {

        'out': outward_files,
        'abcd': user_designation,
    }
    return render(request, 'filetracking/fileview1.html', context)


@login_required(login_url = "/accounts/login")
def fileview2(request,id):

    """
    The function is used to fetch the files received by the user form other employees. 
    These files are filtered by receiver id and ordered by receive date.

         @param:
                request - trivial.
                id - user id

        @variables: 
                inward_file - The Tracking object filtered by receiver_id i.e, present working user.
                context - Holds data needed to make necessary changes in the template. 

    """
    inward_file = Tracking.objects.select_related('file_id__uploader__user','file_id__uploader__department','file_id__designation','current_id__user','current_id__department',
    'current_design__user','current_design__working','current_design__designation','receiver_id','receive_design').filter(receiver_id=request.user).order_by('-receive_date')

    user_designation = HoldsDesignation.objects.select_related('user','working','designation').get(pk=id)
    s = str(user_designation).split(" - ")
    designations = s[1]

    context = {

        'in_file': inward_file,
        'designations': designations,
    }
    return render(request, 'filetracking/fileview2.html', context)


@login_required(login_url = "/accounts/login")
def outward(request):
    """ 
    This function fetches the different designations of the user and renders it on outward template 
     @param:
            request - trivial.

    @variables:
            context - Holds the different designation data of the user
      
    """
    designation = get_designation(request.user)

    context = {
        'designation': designation,
    }
    return render( request, 'filetracking/outward.html', context)


@login_required(login_url = "/accounts/login")
def inward(request):
    """
     This function fetches the different designations of the user and renders it on inward template 

    
     @param:
            request - trivial.

    @variables:
            context - Holds the different designation data of the user
    """
    designation = get_designation(request.user)
    context = {
        
        'designation': designation,
    }
    return render(request, 'filetracking/inward.html', context)


@login_required(login_url = "/accounts/login")
def confirmdelete(request,id):

    """
     The function is used to confirm the deletion of a file.
        @param:
                request - trivial.
                id - user id

        @variables:
                 context - Holds data needed to make necessary changes in the template.   
    """
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
    
    file = get_object_or_404(File, id=id)
    track = Tracking.objects.select_related('file_id__uploader__user','file_id__uploader__department','file_id__designation','current_id__user','current_id__department',
    'current_design__user','current_design__working','current_design__designation','receiver_id','receive_design').filter(file_id=file)
    
    if request.method == "POST":
            if 'finish' in request.POST:
                file.complete_flag = True
                file.save()

            if 'send' in request.POST:
                current_id = request.user.extrainfo
                remarks = request.POST.get('remarks')
                track.update(is_read=True)

                sender = request.POST.get('sender')
                current_design = HoldsDesignation.objects.select_related('user','working','designation').get(id=sender)

                receiver = request.POST.get('receiver')
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
                    return render(request, 'filetracking/forward.html', context)
                receive = request.POST.get('recieve')
                try:
                    receive_design = Designation.objects.get(name=receive)
                except Exception as e:
                    messages.error(request, 'Enter a valid Designation')
                    designations = get_designation(request.user)

                    context = {
                       
                        'designations': designations,
                        'file': file,
                        'track': track,
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
            messages.success(request, 'File sent successfully')
    
    
    designations = get_designation(request.user)

    context = {
        
        'designations':designations,
        'file': file,
        'track': track,
    }

    return render(request, 'filetracking/forward.html', context)


@login_required(login_url = "/accounts/login")
def archive_design(request):

    designation = HoldsDesignation.objects.select_related('user','working','designation').filter(user=request.user)

    context = {
        'designation': designation,
    }
    return render( request, 'filetracking/archive_design.html', context)
    
    



@login_required(login_url = "/accounts/login")
def archive(request , id):

    draft = File.objects.select_related('uploader__user','uploader__department','designation').filter(is_read=True).order_by('-upload_date')


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




    return render(request, 'filetracking/archive.html' , context)


@login_required(login_url = "/accounts/login")
def archive_finish(request, id):
    file1 = get_object_or_404(File, id=id) ##file = get_object_or_404(File, ref_id=id)
    track = Tracking.objects.filter(file_id=file1)
    


    return render(request, 'filetracking/archive_finish.html', {'file': file1, 'track': track})




@login_required(login_url = "/accounts/login")
def finish_design(request):

    designation = HoldsDesignation.objects.select_related('user','working','designation').filter(user=request.user)

    context = {
        'designation': designation,
    }
    return render( request, 'filetracking/finish_design.html', context)


@login_required(login_url = "/accounts/login")
def finish_fileview(request, id):

    out = Tracking.objects.select_related('file_id__uploader__user','file_id__uploader__department','file_id__designation','current_id__user','current_id__department',
    'current_design__user','current_design__working','current_design__designation','receiver_id','receive_design').filter(file_id__uploader=request.user.extrainfo, is_read=False).order_by('-forward_date')




    abcd = HoldsDesignation.objects.select_related('user','working','designation').get(pk=id)


    context = {

        'out': out,
        'abcd': abcd,
    }
    return render(request, 'filetracking/finish_fileview.html', context)




@login_required(login_url = "/accounts/login")
def finish(request, id):
    file1 = get_object_or_404(File, id=id) ##file = get_object_or_404(File, ref_id=id)
    track = Tracking.objects.filter(file_id=file1)
    

    if request.method == "POST":
            if 'Finished' in request.POST:
                File.objects.filter(pk=id).update(is_read=True)
                track.update(is_read=True)
                messages.success(request,'File Archived')

                
                


    
    
    return render(request, 'filetracking/finish.html', {'file': file1, 'track': track,'fileid':id})




def AjaxDropdown1(request):
    """
    This function returns the designation of receiver  on the forward or compose file template.

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
        'holds' : holds
        }

        return HttpResponse(JsonResponse(context), content_type='application/json')


def AjaxDropdown(request):

    """
    This function returns the usernames of receiver  on the forward or compose file template.

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


def test(request):
    return HttpResponse('success')



@login_required(login_url = "/accounts/login")
def delete(request,id):

    """ 
     The function is used the delete of a file and it returns to the drafts page. 

        @param:
            request - trivial.
            id - id of the file that is going to be deleted
    
    """
    file = File.objects.get(pk = id)
    file.delete()
    return redirect('/filetracking/drafts/')




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
    track = Tracking.objects.select_related('file_id__uploader__user','file_id__uploader__department','file_id__designation','current_id__user','current_id__department',
    'current_design__user','current_design__working','current_design__designation','receiver_id','receive_design').filter(file_id=file)
    designations = get_designation(request.user)

    context = {
       
        'designations':designations,
        'file': file,
        'track': track,
    }
    return render(request, 'filetracking/forward.html', context)


