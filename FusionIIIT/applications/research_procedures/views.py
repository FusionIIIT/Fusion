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
    
    context['pat']=Patent.objects.all()
    context['use']=extrainfo
    context['desig']=desig
    
    if request.method=='POST':
        if(extrainfo.user_type == "faculty"):
            pat.faculty_id=extrainfo
            pat.title=request.POST.get('title')
            file1=request.FILES['file1']
            if(file1.name.endswith('.pdf')):
                pat.ipd_form=request.FILES['file1']
                fs=FileSystemStorage()
                name1=fs.save(file1.name,file1)
                pat.file1=fs.url(name1)
            else:
                messages.error(request, 'Please upload pdf file')
                return render(request ,"rs/research.html",context)
            
            file2=request.FILES['file2']
            if(file2.name.endswith('.pdf')):
                pat.project_details=request.FILES['file2']
                fs=FileSystemStorage()
                name2=fs.save(file2.name,file2)
                pat.file2=fs.url(name2)
                messages.success(request, 'Patent filed successfully')
            else:
                messages.error(request, 'Please upload pdf file')
                return render(request ,"rs/research.html",context)

            pat.status='Pending'
            pat.save()
    pat=Patent.objects.all() 
    context['pat']=pat
    return render(request ,"rs/research.html",context)

 #dean_rspc can update status of patent.   
def update(request):
    user=request.user
    extrainfo=ExtraInfo.objects.get(user=user)
    holds_designations = HoldsDesignation.objects.filter(user=user)
    desig = holds_designations
    pat=Patent()
    if request.method=='POST':
        if(desig.exists()):
            if(desig.first().designation.name == "dean_rspc" and extrainfo.user_type == "faculty"):
                iid=request.POST.get('id')
                pat=Patent.objects.get(application_id=iid)
                pat.status=request.POST.get('status')
                pat.save()
    pat=Patent.objects.all() 
    return render(request ,"rs/research.html",{'pat':pat,'use':extrainfo,'desig':desig})

   