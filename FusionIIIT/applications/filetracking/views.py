from django.shortcuts import render, get_object_or_404, redirect
from .models import File, Tracking
from applications.globals.models import ExtraInfo
from django.template.defaulttags import csrf_token
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError


@login_required(login_url="/accounts/login/")
def filetracking(request):
    if request.method == "POST":
        try:
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
        except IntegrityError:
            message = "FileID Already Taken.!!"
            return HttpResponse(message)

    else:
        print("")
    file = File.objects.all()
    extrainfo = ExtraInfo.objects.all()
    return render(request, 'filetracking/composefile.html', {'file': file, 'extrainfo': extrainfo})


@login_required(login_url="/accounts/login")
def drafts(request):
    draft = File.objects.filter(uploader=request.user.extrainfo)
    extrainfo = ExtraInfo.objects.all()
    return render(request, 'filetracking/drafts.html', {'draft': draft, 'extrainfo': extrainfo})


@login_required(login_url="/accounts/login")
def outward(request):
    out = Tracking.objects.filter(current_id=request.user.extrainfo)
    return render(request, 'filetracking/outward.html', {'out': out})


@login_required(login_url="/accounts/login")
def inward(request):
    in_file = Tracking.objects.filter(receiver_id=request.user.extrainfo)

    return render(request, 'filetracking/inward.html', {'in_file': in_file})


@login_required(login_url="/accounts/login")
def archive(request):
    arch = File.objects.filter(complete_flag=True)
    return render(request, 'filetracking/archive.html', {'arch': arch})


@login_required(login_url="/accounts/login")
def finish(request, id):
    file = get_object_or_404(File, ref_id=id)
    track = Tracking.objects.filter(file_id=file)

    return render(request, 'filetracking/finish.html', {'file': file, 'track': track})


@login_required(login_url="/accounts/login")
def forward(request, id):

    file = get_object_or_404(File, ref_id=id)
    track = Tracking.objects.filter(file_id=file)

    if request.method == "POST":
        if 'finish' in request.POST:
            file.complete_flag = True
            file.save()

        if 'send' in request.POST:
            current_id = request.user.extrainfo
            remarks = request.POST.get('remarks')
            receiver = request.POST.get('receiver')
            receiver_id = ExtraInfo.objects.get(id=receiver)
            upload_file = request.FILES.get('myfile')

            Tracking.objects.create(
                file_id=file,
                current_id=current_id,
                receiver_id=receiver_id,
                remarks=remarks,
                upload_file=upload_file,
            )

    extrainfo = ExtraInfo.objects.all()

    return render(request, 'filetracking/forward.html', {'extrainfo': extrainfo,
                                                         'file': file,
                                                         'track': track})
