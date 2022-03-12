from django.shortcuts import render,HttpResponse
from django.contrib import messages
from applications.research_procedures.models import Patent
from applications.academic_information.models import Student
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation
from django.core.files.storage import FileSystemStorage
from notification.views import research_procedures_notif


# Faculty can file patent and view status of it.
def patent_registration(request):

    """
        This function is used to register a patent and to retrieve all patents filed by the faculty.

        @param:
            request - contains metadata about the requested page.
        
        @variables:
            user - the user who is currently logged in.
            extrainfo - extra information of the user.
            user_designations - The designations of the user currently logged in.
            patent - The new patent to be registered.
            patents - All the patents filed by the faculty.
            dean_rspc_user - The Dean RSPC user who can modify status of the patent.
            ipd_form_pdf - The pdf file of the IPD form of the patent sent by the user.
            project_details_pdf - The pdf file of the project details of the patent sent by the user.
            file_system - The file system to store the files.


    """

    user = request.user
    user_extra_info = ExtraInfo.objects.get(user=user)
    user_designations = HoldsDesignation.objects.filter(user=user)
    patent = Patent()
    context = {}
    
    context['patents'] = Patent.objects.all()
    context['user_extra_info'] = user_extra_info
    context['user_designations'] = user_designations
    
    if request.method=='POST':
        if(user_extra_info.user_type == "faculty"):
            patent.faculty_id = user_extra_info
            patent.title = request.POST.get('title')
            ipd_form_pdf = request.FILES['ipd_form_file']
            if(ipd_form_pdf.name.endswith('.pdf')):
                patent.ipd_form = request.FILES['ipd_form_file']
                file_system = FileSystemStorage()
                ipd_form_pdf_name = file_system.save(ipd_form_pdf.name,ipd_form_pdf)
                patent.ipd_form_file = file_system.url(ipd_form_pdf_name)
            else:
                messages.error(request, 'Please upload pdf file')
                return render(request ,"rs/research.html",context)
            
            project_details_pdf = request.FILES['project_details_file']
            if(project_details_pdf.name.endswith('.pdf')):
                patent.project_details=request.FILES['project_details_file']
                file_system = FileSystemStorage()
                project_details_pdf_name = file_system.save(project_details_pdf.name,project_details_pdf)
                patent.project_details_file = file_system.url(project_details_pdf_name)
                messages.success(request, 'Patent filed successfully')
            else:
                messages.error(request, 'Please upload pdf file')
                return render(request ,"rs/research.html",context)

            # creating notifications for user and dean_rspc about the patent
            dean_rspc_user = HoldsDesignation.objects.get(designation=Designation.objects.filter(name='dean_rspc').first()).working
            research_procedures_notif(request.user,request.user,"submitted")
            research_procedures_notif(request.user,dean_rspc_user,"created")
            patent.status='Pending'
            patent.save()
    patents = Patent.objects.all() 
    context['patents'] = patents
    return render(request ,"rs/research.html",context)

#dean_rspc can update status of patent.   
def patent_status_update(request):
    """
        This function is used to update the status of the patent.
        @param:
            request - contains metadata about the requested page.
        @variables:
            user - the user who is currently logged in.
            extrainfo - extra information of the user.
            user_designations - The designations of the user currently logged in.
            patent - The patent whose status is to be updated.
            patents - All the patents filed by the faculty.
            dean_rspc_user - The Dean RSPC user who can modify status of the patent.
    
    """
    user = request.user
    user_extra_info = ExtraInfo.objects.get(user=user)
    user_designations = HoldsDesignation.objects.filter(user=user)
    if request.method=='POST':
        if(user_designations.exists()):
            if(user_designations.first().designation.name == "dean_rspc" and user_extra_info.user_type == "faculty"):
                patent_application_id = request.POST.get('id')
                patent = Patent.objects.get(application_id=patent_application_id)
                patent.status = request.POST.get('status')
                patent.save()

                # Create a notification for the user about the patent status update
                dean_rspc_user = HoldsDesignation.objects.get(designation=Designation.objects.filter(name='dean_rspc').first()).working
                research_procedures_notif(dean_rspc_user,patent.faculty_id.user,request.POST.get('status'))
    patents = Patent.objects.all() 
    return render(request ,"rs/research.html",{'patents':patents,'user_extra_info':user_extra_info,'user_designations':user_designations})

   