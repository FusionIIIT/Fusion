from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from applications.research_procedures.models import Patent, ResearchGroup, ResearchProject, ConsultancyProject, TechTransfer
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation
from django.contrib.auth.models import User
from applications.eis.models import *
from django.core.files.storage import FileSystemStorage
from notification.views import research_procedures_notif
from django.urls import reverse
from .forms import ResearchGroupForm
from django.contrib.auth.decorators import login_required
import datetime

# Faculty can file patent and view status of it.
@login_required
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
        if ("ipd_form_file" in request.FILES) and ("project_details_file" in request.FILES) and ("title" in request.POST):  
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
            else:
                messages.error(request, 'Only Faculty can file patent')
        else:
            messages.error(request,"All fields are required")
    patents = Patent.objects.all() 
    context['patents'] = patents
    context['research_groups'] = ResearchGroup.objects.all()
    context['research_group_form'] = ResearchGroupForm()
    return render(request ,"rs/research.html",context)

@login_required
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
                messages.success(request, 'Patent status updated successfully')
                # Create a notification for the user about the patent status update
                dean_rspc_user = HoldsDesignation.objects.get(designation=Designation.objects.filter(name='dean_rspc').first()).working
                research_procedures_notif(dean_rspc_user,patent.faculty_id.user,request.POST.get('status'))
            else:
                messages.error(request, 'Only Dean RSPC can update status of patent')
    return redirect(reverse("research_procedures:patent_registration"))

@login_required
def research_group_create(request):
    """
        This function is used to create a research group.
        @param:
            request - contains metadata about the requested page.
        @variables:
            user - the user who is currently logged in.
            extrainfo - extra information of the user.
            user_designations - The designations of the user currently logged in.
            research_group - The research group to be created.
            research_groups - All the research groups.
            dean_rspc_user - The Dean RSPC user who can modify status of the patent.
    
    """
    user = request.user
    user_extra_info = ExtraInfo.objects.get(user=user)
    if request.method=='POST':
        if user_extra_info.user_type == "faculty":
            form = ResearchGroupForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Research group created successfully')
        else:
            messages.error(request, 'Only Faculty can create research group')
    return redirect(reverse("research_procedures:patent_registration"))

@login_required
def project_insert(request):
    user = get_object_or_404(ExtraInfo, user=request.user)
    pf = user.id

    research_project = ResearchProject()
    research_project.user = request.user
    research_project.pf_no = pf
    research_project.pi = request.POST.get('pi')
    research_project.co_pi = request.POST.get('co_pi')
    research_project.title = request.POST.get('title')
    research_project.financial_outlay = request.POST.get('financial_outlay')
    research_project.funding_agency = request.POST.get('funding_agency')
    research_project.status = request.POST.get('status')
    x = request.POST.get('start')
    if x[:5] == "Sept." :
        x = "Sep." + x[5:]
    if (request.POST.get('start') != None and request.POST.get('start') != '' and request.POST.get('start') != 'None'):
        try:
            research_project.start_date = datetime.datetime.strptime(x, "%B %d, %Y")
        except:
            research_project.start_date = datetime.datetime.strptime(x, "%b. %d, %Y")
    x = request.POST.get('end')
    if x[:5] == "Sept." :
        x = "Sep." + x[5:]
    if (request.POST.get('end') != None and request.POST.get('end') != '' and request.POST.get('end') != 'None'):
        try:
            research_project.finish_date = datetime.datetime.strptime(x, "%B %d, %Y")
        except:
            research_project.finish_date = datetime.datetime.strptime(x, "%b. %d, %Y")
    x = request.POST.get('sub')
    if x[:5] == "Sept." :
        x = "Sep." + x[5:]
    if (request.POST.get('sub') != None and request.POST.get('sub') != '' and request.POST.get('sub') != 'None'):
        try:
            research_project.date_submission = datetime.datetime.strptime(x, "%B %d, %Y")
        except:
            research_project.date_submission = datetime.datetime.strptime(x, "%b. %d, %Y")
    research_project.save()
    messages.success(request, 'Successfully created research project')
    return redirect(reverse("research_procedures:patent_registration"))

@login_required
def consult_insert(request):
    user = get_object_or_404(ExtraInfo, user=request.user)
    pf = user.id
    consultancy_project = ConsultancyProject()
    consultancy_project.user = request.user
    consultancy_project.pf_no = pf
    consultancy_project.consultants = request.POST.get('consultants')
    consultancy_project.client = request.POST.get('client')
    consultancy_project.title = request.POST.get('title')
    consultancy_project.financial_outlay = request.POST.get('financial_outlay')
    x = request.POST.get('start')
    if x[:5] == "Sept." :
        x = "Sep." + x[5:]
    if (request.POST.get('start') != None and request.POST.get('start') != '' and request.POST.get('start') != 'None'):
        try:
            consultancy_project.start_date = datetime.datetime.strptime(x, "%B %d, %Y")
        except:
            consultancy_project.start_date = datetime.datetime.strptime(x, "%b. %d, %Y")
    x = request.POST.get('end')
    if x[:5] == "Sept." :
        x = "Sep." + x[5:]
    if (request.POST.get('end') != None and request.POST.get('end') != '' and request.POST.get('end') != 'None'):
        try:
            consultancy_project.end_date = datetime.datetime.strptime(x, "%B %d, %Y")
        except:
            consultancy_project.end_date = datetime.datetime.strptime(x, "%b. %d, %Y")
    consultancy_project.save()
    messages.success(request,"Successfully created consultancy project")
    return redirect(reverse("research_procedures:patent_registration"))


def transfer_insert(request):
    user = get_object_or_404(ExtraInfo, user=request.user)
    pf = user.id

    tech_transfer = TechTransfer()
    tech_transfer.pf_no = pf
    tech_transfer.details = request.POST.get('details')
    tech_transfer.save()
    messages.success(request,"Successfully created Technology Transfer")
    return redirect(reverse("research_procedures:patent_registration"))

# Dean RSPC Profile

def rspc_profile(request):
    # user = get_object_or_404(faculty_about, user=request.user)
    # pf = user.user

    user = get_object_or_404(User, username= request.user)
    extra_info = get_object_or_404(ExtraInfo, user=user)
    if extra_info.user_type == 'student':
        return redirect('/')
    pf = extra_info.id
    designations = HoldsDesignation.objects.filter(user_id=extra_info.user.id)
    flag_rspc = False
    for designation in designations:
        # print(designation.designation_id)
        # currDesig = Designation.objects.filter(id=designation.designation_id)
        print(designation.designation_id)
        currDesig = get_object_or_404(Designation, id=designation.designation_id)
        print(currDesig.name)
        if(currDesig.name=="dean_rspc"):    
            flag_rspc = True
            break

    if flag_rspc != True:
        if extra_info.user_type == 'faculty':
            return redirect('/eis/profile/')
    # form = ConfrenceForm()

    journal = emp_research_papers.objects.filter(rtype='Journal').order_by('-year', '-a_month')
    conference = emp_research_papers.objects.filter(rtype='Conference').order_by('-year', '-a_month')
    books = emp_published_books.objects.all().order_by('-pyear', '-authors')
    projects = emp_research_projects.objects.all().order_by('-start_date')
    consultancy = emp_consultancy_projects.objects.all().order_by('-start_date')
    patents = emp_patents.objects.all().order_by('-p_year', '-a_month')
    techtransfers = emp_techtransfer.objects.all().order_by('-date_entry')
    mtechs = emp_mtechphd_thesis.objects.filter(degree_type=1).order_by('-s_year', '-a_month')
    phds = emp_mtechphd_thesis.objects.filter(degree_type=2).order_by('-s_year', '-a_month')
    fvisits = emp_visits.objects.filter(v_type=2).order_by('-start_date')
    ivisits = emp_visits.objects.filter(v_type=1).order_by('-start_date')
    # for fvisit in fvisits:
    #     fvisit.countryfull = countries[fvisit.country]
    consymps = emp_confrence_organised.objects.all().order_by('-start_date')
    awards = emp_achievement.objects.all().order_by('-a_year', '-a_month')
    talks = emp_expert_lectures.objects.all().order_by('-l_year', '-a_month')
    chairs = emp_session_chair.objects.all().order_by('-start_date')
    keynotes = emp_keynote_address.objects.all().order_by('-start_date')
    events = emp_event_organized.objects.all().order_by('-start_date')
    y=[]
    for r in range(1995, (datetime.datetime.now().year + 1)):
        y.append(r)

    # pers = get_object_or_404(faculty_about, user = request.user)
    # design = HoldsDesignation.objects.select_related('user','working','designation').filter(working=request.user)

    # desig=[]
    # for i in design:
    #     desig.append(str(i.designation))
    context = {'user': user,
            #    'desig':desig,
               'pf':pf,
               'journal':journal,
               'conference': conference,
               'books': books,
               'projects': projects,
            #    'form':form,
               'consultancy':consultancy,
               'patents':patents,
               'techtransfers':techtransfers,
               'mtechs':mtechs,
               'phds':phds,
               'fvisits':fvisits,
               'ivisits': ivisits,
               'consymps':consymps,
               'awards':awards,
               'talks':talks,
               'chairs':chairs,
               'keynotes':keynotes,
               'events':events,
               'year_range':y,
            #    'pers':pers
               }
    return render(request, 'eisModulenew/rspc_profile.html', context)


# generating rspc profile of a faculty
def rspc_profile_faculty(request):
    # user = get_object_or_404(faculty_about, user=request.user)
    # pf = user.user
    username = request.GET.get('param')
    user = get_object_or_404(User, username= request.user)
    extra_info = get_object_or_404(ExtraInfo, user=user)
    user_faculty = get_object_or_404(User, username= username)
    extra_info_faculty = get_object_or_404(ExtraInfo, user=user_faculty)
    if extra_info_faculty.user_type == 'student':
        return redirect('/')
    pf = extra_info.id
    pf_faculty = extra_info_faculty.id
    print(pf_faculty)
    designations = HoldsDesignation.objects.filter(user_id=extra_info.user.id)
    flag_rspc = False
    for designation in designations:
        # print(designation.designation_id)
        # currDesig = Designation.objects.filter(id=designation.designation_id)
        print(designation.designation_id)
        currDesig = get_object_or_404(Designation, id=designation.designation_id)
        print(currDesig.name)
        if(currDesig.name=="dean_rspc"):    
            flag_rspc = True
            break

    if flag_rspc != True:
        if extra_info.user_type == 'faculty':
            return redirect('/eis/profile/')
    # form = ConfrenceForm()

    journal = emp_research_papers.objects.filter(pf_no=pf_faculty, rtype='Journal').order_by('-year', '-a_month')
    conference = emp_research_papers.objects.filter(pf_no=pf_faculty, rtype='Conference').order_by('-year', '-a_month')
    books = emp_published_books.objects.filter(pf_no=pf_faculty).order_by('-pyear', '-authors')
    projects = emp_research_projects.objects.filter(user=user_faculty).order_by('-start_date')  
    print(projects)
    consultancy = emp_consultancy_projects.objects.filter(pf_no=pf_faculty).order_by('-start_date')
    patents = emp_patents.objects.filter(pf_no=pf_faculty).order_by('-p_year', '-a_month')
    techtransfers = emp_techtransfer.objects.filter(pf_no=pf_faculty).order_by('-date_entry')
    mtechs = emp_mtechphd_thesis.objects.filter(pf_no=pf_faculty, degree_type=1).order_by('-s_year', '-a_month')
    phds = emp_mtechphd_thesis.objects.filter(pf_no=pf_faculty, degree_type=2).order_by('-s_year', '-a_month')
    fvisits = emp_visits.objects.filter(pf_no=pf_faculty, v_type=2).order_by('-start_date')
    ivisits = emp_visits.objects.filter(pf_no=pf_faculty, v_type=1).order_by('-start_date')

    # journal = emp_research_papers.objects.filter(rtype='Journal').order_by('-year', '-a_month')
    # conference = emp_research_papers.objects.filter(rtype='Conference').order_by('-year', '-a_month')
    # books = emp_published_books.objects.all().order_by('-pyear', '-authors')
    # projects = emp_research_projects.objects.all().order_by('-start_date')
    # consultancy = emp_consultancy_projects.objects.all().order_by('-start_date')
    # patents = emp_patents.objects.all().order_by('-p_year', '-a_month')
    # techtransfers = emp_techtransfer.objects.all().order_by('-date_entry')
    # mtechs = emp_mtechphd_thesis.objects.filter(degree_type=1).order_by('-s_year', '-a_month')
    # phds = emp_mtechphd_thesis.objects.filter(degree_type=2).order_by('-s_year', '-a_month')
    # fvisits = emp_visits.objects.filter(v_type=2).order_by('-start_date')
    # ivisits = emp_visits.objects.filter(v_type=1).order_by('-start_date')
    # for fvisit in fvisits:
    #     fvisit.countryfull = countries[fvisit.country]

    consymps = emp_confrence_organised.objects.filter(pf_no=pf_faculty).order_by('-date_entry')
    awards = emp_achievement.objects.filter(pf_no=pf_faculty).order_by('-date_entry')
    talks = emp_expert_lectures.objects.filter(pf_no=pf_faculty).order_by('-date_entry')
    chairs = emp_session_chair.objects.filter(pf_no=pf_faculty).order_by('-date_entry')
    keynotes = emp_keynote_address.objects.filter(pf_no=pf_faculty).order_by('-date_entry')
    events = emp_event_organized.objects.filter(pf_no=pf_faculty).order_by('-start_date')
    y=[]
    for r in range(1995, (datetime.datetime.now().year + 1)):
        y.append(r)
    # try:
    #     pers = get_object_or_404(faculty_about, user = user)
    # except:
    #     pers = None

    # consymps = emp_confrence_organised.objects.all().order_by('-start_date')
    # awards = emp_achievement.objects.all().order_by('-a_year', '-a_month')
    # talks = emp_expert_lectures.objects.all().order_by('-l_year', '-a_month')
    # chairs = emp_session_chair.objects.all().order_by('-start_date')
    # keynotes = emp_keynote_address.objects.all().order_by('-start_date')
    # events = emp_event_organized.objects.all().order_by('-start_date')
    # y=[]
    # for r in range(1995, (datetime.datetime.now().year + 1)):
    #     y.append(r)

    # pers = get_object_or_404(faculty_about, user = request.user)
    # design = HoldsDesignation.objects.select_related('user','working','designation').filter(working=request.user)

    # desig=[]
    # for i in design:
    #     desig.append(str(i.designation))
    context = {'user': user,
            #    'desig':desig,
               'pf':pf,
               'journal':journal,
               'conference': conference,
               'books': books,
               'projects': projects,
            #    'form':form,
               'consultancy':consultancy,
               'patents':patents,
               'techtransfers':techtransfers,
               'mtechs':mtechs,
               'phds':phds,
               'fvisits':fvisits,
               'ivisits': ivisits,
               'consymps':consymps,
               'awards':awards,
               'talks':talks,
               'chairs':chairs,
               'keynotes':keynotes,
               'events':events,
               'year_range':y,
            #    'pers':pers
               }
    return render(request, 'eisModulenew/rspc_profile.html', context)
