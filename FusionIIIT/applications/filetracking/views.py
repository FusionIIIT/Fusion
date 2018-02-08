from django.shortcuts import render, get_object_or_404, redirect
from .models import File, Tracking
from applications.globals.models import ExtraInfo
from django.template.defaulttags import csrf_token
from django.http import HttpResponse,HttpResponseRedirect
from django.contrib.auth.decorators import login_required
import time


@login_required(login_url = "/accounts/login/")
def filetracking(request):
    if request.method=="POST":
        if 'save' in request.POST:
            uploader = request.user.extrainfo
            ref_id = request.POST.get('fileid')
            subject = request.POST.get('title')
            description = request.POST.get('desc')
            upload_file = request.FILES.get('myfile')

        File.objects.create(
            uploader=uploader,
            ref_id=ref_id,
            description=description,
            subject=subject,
            upload_file=upload_file
        )
        return HttpResponse('You have successfully composed a File')
    else:
        file = File.objects.all(),
        extrainfo = ExtraInfo.objects.all()
    return render(request, 'filetracking/composefile.html' , {'file' : file, 'extrainfo' : extrainfo})


@login_required(login_url = "/accounts/login")
def drafts(request):
    draft = File.objects.filter(uploader=request.user.extrainfo)
    extrainfo = ExtraInfo.objects.all()
    return render(request, 'filetracking/drafts.html', {'draft' : draft, 'extrainfo' : extrainfo})


@login_required(login_url = "/accounts/login")
def outward(request):
    out = Tracking.objects.filter(current_id=request.user.extrainfo)
    return render( request, 'filetracking/outward.html' , {'out':out})


@login_required(login_url = "/accounts/login")
def inward(request):
    in_file = Tracking.objects.filter(receiver_id=request.user.extrainfo)

    return render(request, 'filetracking/inward.html', {'in_file' : in_file})


@login_required(login_url = "/accounts/login")
def archive(request):
    # in_file = Tracking.objects.filter(receiver_id=request.user.extrainfo)
    return render(request, 'filetracking/archive.html')


@login_required(login_url = "/accounts/login")
def forward(request, id):
    file = get_object_or_404(File, id=id)
    if request.method=="POST":
        if 'send' in request.POST:
            current_id = request.user.extrainfo
            remarks = request.POST.get('remarks')
            receiver = request.POST.get('receiver')
            receiver_id= ExtraInfo.objects.get(id=receiver)

        Tracking.objects.create(
            current_id=current_id,
            remarks=remarks,
            receiver_id=receiver_id,
            file_id=file,
        )
        return HttpResponse('You have Successfully forwarded a File')
    else:
        tracking = Tracking.objects.all(),
    extrainfo = ExtraInfo.objects.all()
    return render(request, 'filetracking/forward.html', {'extrainfo' : extrainfo, 'file': file, 'tracking':tracking})


'''def track(request):

    if request.method=="POST":
        if 'track' in request.POST:
            sender = request.user.extrainfo
            fileid = request.POST.get('fileid')

        ReceiveFile.objects.create(
            sender=sender,
            file = fileid,
        )
    else:
        receivefile = ReceiveFile.objects.all()

    return render(request, 'filetracking/track.html', {'receivefile':receivefile})

def trackfile(request):
    if request.method=="POST":
        if 'track' in request.POST:
            sender = request.user.extrainfo
            fileid = request.POST.get('fileid')

        ReceiveFile.objects.create(
            sender=sender,
            file = fileid,
        )
    else:
        receivefile = ReceiveFile.objects.all()

    return render(request, 'filetracking/trackfile.html', {'receivefile':receivefile})
'''
