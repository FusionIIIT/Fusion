from django.shortcuts import render,HttpResponse
from django.contrib import messages
from applications.research_procedures.models import Patent
from applications.academic_information.models import Student
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage


# Faculty can file patent and view status of it.
def IPR(request):
    user=request.user
    extrainfo=ExtraInfo.objects.get(user=user)
    holds_designations = HoldsDesignation.objects.filter(user=user)
    desig = holds_designations
    pat=Patent()
    context={}
    
    if request.method=='POST':
        pat.faculty_id=extrainfo
        pat.title=request.POST.get('title')
        pat.ipd_form=request.FILES['file1']
        file1=request.FILES['file1']
        fs=FileSystemStorage()
        name1=fs.save(file1.name,file1)
        pat.file1=fs.url(name1)

        pat.project_details=request.FILES['file2']
        file2=request.FILES['file2']
        fs=FileSystemStorage()
        name2=fs.save(file2.name,file2)
        pat.file2=fs.url(name2)

        pat.status='Pending'
        pat.save()

    pat=Patent.objects.all() 
    context['pat']=pat
    context['use']=extrainfo
    context['desig']=desig
    return render(request ,"rs/research.html",context)

 #dean_rspc can update status of patent.   
def update(request):
    user=request.user
    extrainfo=ExtraInfo.objects.get(user=user)
    holds_designations = HoldsDesignation.objects.filter(user=user)
    desig = holds_designations
    pat=Patent()
    if request.method=='POST':
        iid=request.POST.get('id')
        pat=Patent.objects.get(application_id=iid)
        pat.status=request.POST.get('status')
        pat.save()

    pat=Patent.objects.all() 
    return render(request ,"rs/research.html",{'pat':pat,'use':extrainfo,'desig':desig})

   