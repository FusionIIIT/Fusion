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
from django.template import loader
from django.template.loader import get_template
from io import BytesIO
from xhtml2pdf import pisa
from django.http import HttpResponse, HttpResponseRedirect
from html import escape
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
    all_extra_info = []
    # for user in all_user:
    curr_extra_info = ExtraInfo.objects.filter(user_type = 'faculty')
    for curr_info in curr_extra_info:  
        if(curr_info.user_type == 'faculty'):
            all_extra_info.append(curr_info.user.username)
    

    print(all_extra_info)


    all_extra_info = ExtraInfo.objects.filter()
    user = get_object_or_404(User, username= request.user)
    extra_info = get_object_or_404(ExtraInfo, user=user)
    if extra_info.user_type == 'student':
        return redirect('/')
    pf = user.id
    designations = HoldsDesignation.objects.filter(user_id=extra_info.user.id)
    flag_rspc = False
    for designation in designations:
        print(designation.designation_id)
        currDesig = get_object_or_404(Designation, id=designation.designation_id)
        print(currDesig.name)
        if(currDesig.name=="dean_rspc"):    
            flag_rspc = True
            break

    if flag_rspc != True:
        if extra_info.user_type == 'faculty' or extra_info.user_type == 'staff':
            return redirect('/eis/profile/')
        
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


    context = {'user': user,
               'pf':pf,
               'journal':journal,
               'conference': conference,
               'books': books,
               'projects': projects,
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
    username = request.POST.get('data')
    print(username)
    user = get_object_or_404(User, username= request.user)
    extra_info = get_object_or_404(ExtraInfo, user=user)
    user_faculty = get_object_or_404(User, username= username)
    extra_info_faculty = get_object_or_404(ExtraInfo, user=user_faculty)
    if extra_info_faculty.user_type == 'student':
        return redirect('/')
    pf = user.id
    pf_faculty = extra_info_faculty.id
    print(pf_faculty)
    designations = HoldsDesignation.objects.filter(user_id=extra_info.user.id)
    flag_rspc = False
    for designation in designations:
        print(designation.designation_id)
        currDesig = get_object_or_404(Designation, id=designation.designation_id)
        print(currDesig.name)
        if(currDesig.name=="dean_rspc"):    
            flag_rspc = True
            break

    if flag_rspc != True:
        if extra_info.user_type == 'faculty':
            return redirect('/eis/profile/')


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


    consymps = emp_confrence_organised.objects.filter(pf_no=pf_faculty).order_by('-date_entry')
    awards = emp_achievement.objects.filter(pf_no=pf_faculty).order_by('-date_entry')
    talks = emp_expert_lectures.objects.filter(pf_no=pf_faculty).order_by('-date_entry')
    chairs = emp_session_chair.objects.filter(pf_no=pf_faculty).order_by('-date_entry')
    keynotes = emp_keynote_address.objects.filter(pf_no=pf_faculty).order_by('-date_entry')
    events = emp_event_organized.objects.filter(pf_no=pf_faculty).order_by('-start_date')
    y=[]
    for r in range(1995, (datetime.datetime.now().year + 1)):
        y.append(r)

    context = {'user': user,
               'pf':pf,
               'journal':journal,
               'conference': conference,
               'books': books,
               'projects': projects,
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
               }
    return render(request, 'eisModulenew/rspc_profile.html', context)


def generate_citation(request):
    username = request.POST.get('data')
    print(username)
    user = get_object_or_404(User, username= request.user)
    extra_info = get_object_or_404(ExtraInfo, user=user)
    user_faculty = get_object_or_404(User, username= username)
    extra_info_faculty = get_object_or_404(ExtraInfo, user=user_faculty)
    if extra_info_faculty.user_type == 'student':
        return redirect('/')
    pf = user.id
    pf_faculty = extra_info_faculty.id
    print(pf_faculty)
    designations = HoldsDesignation.objects.filter(user_id=extra_info.user.id)
    flag_rspc = False
    for designation in designations:
        print(designation.designation_id)
        currDesig = get_object_or_404(Designation, id=designation.designation_id)
        print(currDesig.name)
        if(currDesig.name=="dean_rspc"):    
            flag_rspc = True
            break

    if flag_rspc != True:
        if extra_info.user_type == 'faculty':
            return redirect('/eis/profile/')
    
    projects = emp_research_projects.objects.filter(user=user_faculty).order_by('-start_date')
    context = {
        'projects' : projects
    }

    return render(request, 'rs/citation.html', context)

def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return HttpResponse('We had some errors<pre>%s</pre>' % escape(html))


def rspc_generate_report(request):
    user = get_object_or_404(ExtraInfo, user=request.user)
    pf = user.id
    start = request.POST.get('syear')
    star_date = start+'-01-01'
    end = request.POST.get('lyear')
    star = request.POST.get('smonth')
    star_date = start + '-01-01'
    en = request.POST.get('lmonth')
    if(request.POST.get('journal_select')=="journal"):
        journal = emp_research_papers.objects.filter(rtype='Journal').filter(year__range=[start,end]).order_by('-date_entry')
        journal_req="1"
    else:
        journal=""
        journal_req="0"

    if (request.POST.get('conference_select') == "conference"):
        conference = emp_research_papers.objects.filter(rtype='Conference').filter(year__range=[start,end]).order_by('-date_entry')
        conference_req = "1"
    else:
        conference=""
        conference_req = "0"

    if (request.POST.get('books_select') == "books"):
        books = emp_published_books.objects.all().order_by('-date_entry')
        books_req = "1"
    else:
        books=""
        books_req = "0"

    if (request.POST.get('projects_select') == "projects"):
        projects = emp_research_projects.objects.all().filter(start_date__year__range=[start,end]).filter(start_date__month__range=[star,en]).order_by('-start_date')
        projects_req = "1"
    else:
        projects = ""
        projects_req = "0"

    if (request.POST.get('consultancy_select') == "consultancy"):
        consultancy = emp_consultancy_projects.objects.all().filter(start_date__year__range=[start,end]).filter(start_date__month__range=[star,en]).order_by('-date_entry')
        consultancy_req = "1"
    else:
        consultancy = ""
        consultancy_req = "0"

    if (request.POST.get('patents_select') == "patents"):
        patents = emp_patents.objects.all().filter(p_year__range=[start,end]).filter(a_month__range=[star,en]).order_by('-date_entry')
        patents_req = "1"
    else:
        patents = ""
        patents_req = "0"

    if (request.POST.get('techtransfers_select') == "techtransfers"):
        techtransfers = emp_techtransfer.objects.all().filter(date_entry__year__range=[start,end]).filter(date_entry__month__range=[star,en]).order_by('-date_entry')
        techtransfers_req = "1"
    else:
        techtransfers=""
        techtransfers_req = "0"

    if (request.POST.get('mtechs_select') == "mtechs"):
        mtechs = emp_mtechphd_thesis.objects.filter(degree_type=1).filter(s_year__range=[start,end]).filter(a_month__range=[star,en]).order_by('-date_entry')
        mtechs_req = "1"
    else:
        mtechs=""
        mtechs_req = "0"

    if (request.POST.get('phds_select') == "phds"):
        phds = emp_mtechphd_thesis.objects.filter(degree_type=2).filter(s_year__range=[start,end]).filter(a_month__range=[star,en]).order_by('-date_entry')
        phds_req = "1"
    else:
        phds=""
        phds_req = "0"

    if (request.POST.get('fvisits_select') == "fvisits"):
        fvisits = emp_visits.objects.filter(v_type=2).filter(start_date__year__range=[start,end]).filter(start_date__month__range=[star,en]).order_by('-entry_date')
        fvisits_req = "1"
    else:
        fvisits=""
        fvisits_req = "0"
    countries = {
        'AF': 'Afghanistan',
        'AX': 'Aland Islands',
        'AL': 'Albania',
        'DZ': 'Algeria',
        'AS': 'American Samoa',
        'AD': 'Andorra',
        'AO': 'Angola',
        'AI': 'Anguilla',
        'AQ': 'Antarctica',
        'AG': 'Antigua And Barbuda',
        'AR': 'Argentina',
        'AM': 'Armenia',
        'AW': 'Aruba',
        'AU': 'Australia',
        'AT': 'Austria',
        'AZ': 'Azerbaijan',
        'BS': 'Bahamas',
        'BH': 'Bahrain',
        'BD': 'Bangladesh',
        'BB': 'Barbados',
        'BY': 'Belarus',
        'BE': 'Belgium',
        'BZ': 'Belize',
        'BJ': 'Benin',
        'BM': 'Bermuda',
        'BT': 'Bhutan',
        'BO': 'Bolivia',
        'BA': 'Bosnia And Herzegovina',
        'BW': 'Botswana',
        'BV': 'Bouvet Island',
        'BR': 'Brazil',
        'IO': 'British Indian Ocean Territory',
        'BN': 'Brunei Darussalam',
        'BG': 'Bulgaria',
        'BF': 'Burkina Faso',
        'BI': 'Burundi',
        'KH': 'Cambodia',
        'CM': 'Cameroon',
        'CA': 'Canada',
        'CV': 'Cape Verde',
        'KY': 'Cayman Islands',
        'CF': 'Central African Republic',
        'TD': 'Chad',
        'CL': 'Chile',
        'CN': 'China',
        'CX': 'Christmas Island',
        'CC': 'Cocos (Keeling) Islands',
        'CO': 'Colombia',
        'KM': 'Comoros',
        'CG': 'Congo',
        'CD': 'Congo, Democratic Republic',
        'CK': 'Cook Islands',
        'CR': 'Costa Rica',
        'CI': 'Cote D\'Ivoire',
        'HR': 'Croatia',
        'CU': 'Cuba',
        'CY': 'Cyprus',
        'CZ': 'Czech Republic',
        'DK': 'Denmark',
        'DJ': 'Djibouti',
        'DM': 'Dominica',
        'DO': 'Dominican Republic',
        'EC': 'Ecuador',
        'EG': 'Egypt',
        'SV': 'El Salvador',
        'GQ': 'Equatorial Guinea',
        'ER': 'Eritrea',
        'EE': 'Estonia',
        'ET': 'Ethiopia',
        'FK': 'Falkland Islands (Malvinas)',
        'FO': 'Faroe Islands',
        'FJ': 'Fiji',
        'FI': 'Finland',
        'FR': 'France',
        'GF': 'French Guiana',
        'PF': 'French Polynesia',
        'TF': 'French Southern Territories',
        'GA': 'Gabon',
        'GM': 'Gambia',
        'GE': 'Georgia',
        'DE': 'Germany',
        'GH': 'Ghana',
        'GI': 'Gibraltar',
        'GR': 'Greece',
        'GL': 'Greenland',
        'GD': 'Grenada',
        'GP': 'Guadeloupe',
        'GU': 'Guam',
        'GT': 'Guatemala',
        'GG': 'Guernsey',
        'GN': 'Guinea',
        'GW': 'Guinea-Bissau',
        'GY': 'Guyana',
        'HT': 'Haiti',
        'HM': 'Heard Island & Mcdonald Islands',
        'VA': 'Holy See (Vatican City State)',
        'HN': 'Honduras',
        'HK': 'Hong Kong',
        'HU': 'Hungary',
        'IS': 'Iceland',
        'IN': 'India',
        'ID': 'Indonesia',
        'IR': 'Iran, Islamic Republic Of',
        'IQ': 'Iraq',
        'IE': 'Ireland',
        'IM': 'Isle Of Man',
        'IL': 'Israel',
        'IT': 'Italy',
        'JM': 'Jamaica',
        'JP': 'Japan',
        'JE': 'Jersey',
        'JO': 'Jordan',
        'KZ': 'Kazakhstan',
        'KE': 'Kenya',
        'KI': 'Kiribati',
        'KR': 'Korea',
        'KW': 'Kuwait',
        'KG': 'Kyrgyzstan',
        'LA': 'Lao People\'s Democratic Republic',
        'LV': 'Latvia',
        'LB': 'Lebanon',
        'LS': 'Lesotho',
        'LR': 'Liberia',
        'LY': 'Libyan Arab Jamahiriya',
        'LI': 'Liechtenstein',
        'LT': 'Lithuania',
        'LU': 'Luxembourg',
        'MO': 'Macao',
        'MK': 'Macedonia',
        'MG': 'Madagascar',
        'MW': 'Malawi',
        'MY': 'Malaysia',
        'MV': 'Maldives',
        'ML': 'Mali',
        'MT': 'Malta',
        'MH': 'Marshall Islands',
        'MQ': 'Martinique',
        'MR': 'Mauritania',
        'MU': 'Mauritius',
        'YT': 'Mayotte',
        'MX': 'Mexico',
        'FM': 'Micronesia, Federated States Of',
        'MD': 'Moldova',
        'MC': 'Monaco',
        'MN': 'Mongolia',
        'ME': 'Montenegro',
        'MS': 'Montserrat',
        'MA': 'Morocco',
        'MZ': 'Mozambique',
        'MM': 'Myanmar',
        'NA': 'Namibia',
        'NR': 'Nauru',
        'NP': 'Nepal',
        'NL': 'Netherlands',
        'AN': 'Netherlands Antilles',
        'NC': 'New Caledonia',
        'NZ': 'New Zealand',
        'NI': 'Nicaragua',
        'NE': 'Niger',
        'NG': 'Nigeria',
        'NU': 'Niue',
        'NF': 'Norfolk Island',
        'MP': 'Northern Mariana Islands',
        'NO': 'Norway',
        'OM': 'Oman',
        'PK': 'Pakistan',
        'PW': 'Palau',
        'PS': 'Palestinian Territory, Occupied',
        'PA': 'Panama',
        'PG': 'Papua New Guinea',
        'PY': 'Paraguay',
        'PE': 'Peru',
        'PH': 'Philippines',
        'PN': 'Pitcairn',
        'PL': 'Poland',
        'PT': 'Portugal',
        'PR': 'Puerto Rico',
        'QA': 'Qatar',
        'RE': 'Reunion',
        'RO': 'Romania',
        'RU': 'Russian Federation',
        'RW': 'Rwanda',
        'BL': 'Saint Barthelemy',
        'SH': 'Saint Helena',
        'KN': 'Saint Kitts And Nevis',
        'LC': 'Saint Lucia',
        'MF': 'Saint Martin',
        'PM': 'Saint Pierre And Miquelon',
        'VC': 'Saint Vincent And Grenadines',
        'WS': 'Samoa',
        'SM': 'San Marino',
        'ST': 'Sao Tome And Principe',
        'SA': 'Saudi Arabia',
        'SN': 'Senegal',
        'RS': 'Serbia',
        'SC': 'Seychelles',
        'SL': 'Sierra Leone',
        'SG': 'Singapore',
        'SK': 'Slovakia',
        'SI': 'Slovenia',
        'SB': 'Solomon Islands',
        'SO': 'Somalia',
        'ZA': 'South Africa',
        'GS': 'South Georgia And Sandwich Isl.',
        'ES': 'Spain',
        'LK': 'Sri Lanka',
        'SD': 'Sudan',
        'SR': 'Suriname',
        'SJ': 'Svalbard And Jan Mayen',
        'SZ': 'Swaziland',
        'SE': 'Sweden',
        'CH': 'Switzerland',
        'SY': 'Syrian Arab Republic',
        'TW': 'Taiwan',
        'TJ': 'Tajikistan',
        'TZ': 'Tanzania',
        'TH': 'Thailand',
        'TL': 'Timor-Leste',
        'TG': 'Togo',
        'TK': 'Tokelau',
        'TO': 'Tonga',
        'TT': 'Trinidad And Tobago',
        'TN': 'Tunisia',
        'TR': 'Turkey',
        'TM': 'Turkmenistan',
        'TC': 'Turks And Caicos Islands',
        'TV': 'Tuvalu',
        'UG': 'Uganda',
        'UA': 'Ukraine',
        'AE': 'United Arab Emirates',
        'GB': 'United Kingdom',
        'US': 'United States',
        'UM': 'United States Outlying Islands',
        'UY': 'Uruguay',
        'UZ': 'Uzbekistan',
        'VU': 'Vanuatu',
        'VE': 'Venezuela',
        'VN': 'Viet Nam',
        'VG': 'Virgin Islands, British',
        'VI': 'Virgin Islands, U.S.',
        'WF': 'Wallis And Futuna',
        'EH': 'Western Sahara',
        'YE': 'Yemen',
        'ZM': 'Zambia',
        'ZW': 'Zimbabwe',
        'KP': 'Korea (Democratic Peoples Republic of)',
    }

    if (request.POST.get('ivisits_select') == "ivisits"):
        ivisits = emp_visits.objects.filter(v_type=1).filter(start_date__year__range=[start,end]).filter(start_date__month__range=[star,en]).order_by('-entry_date')
        ivisits_req = "1"
    else:
        ivisits=""
        ivisits_req = "0"
    for fvisit in fvisits:
        fvisit.countryfull = countries[fvisit.country]

    if (request.POST.get('consymps_select') == "consymps"):
        consymps = emp_confrence_organised.objects.all().filter(start_date__year__range=[start,end]).filter(start_date__month__range=[star,en]).order_by('-date_entry')
        consymps_req = "1"
    else:
        consymps=""
        consymps_req = "0"

    if (request.POST.get('awards_select') == "awards"):
        awards = emp_achievement.objects.all().filter(a_year__range=[start,end]).order_by('-date_entry')
        awards_req = "1"
    else:
        awards=""
        awards_req = "0"

    if (request.POST.get('talks_select') == "talks"):
        talks = emp_expert_lectures.objects.all().filter(l_date__year__range=[start,end]).filter(l_date__month__range=[star,en]).order_by('-date_entry')
        talks_req = "1"
    else:
        talks=""
        talks_req = "0"

    if (request.POST.get('chairs_select') == "chairs"):
        chairs = emp_session_chair.objects.all().filter(start_date__year__range=[start,end]).filter(start_date__month__range=[star,en]).order_by('-date_entry')
        chairs_req = "1"
    else:
        chairs=""
        chairs_req = "0"

    if (request.POST.get('keynotes_select') == "keynotes"):
        keynotes = emp_keynote_address.objects.all().filter(start_date__year__range=[start,end]).filter(start_date__month__range=[star,en]).order_by('-date_entry')
        keynotes_req = "1"
    else:
        keynotes=""
        keynotes_req = "0"

    if (request.POST.get('events_select') == "events"):
        events = emp_event_organized.objects.all().filter(start_date__year__range=[start,end]).filter(start_date__month__range=[star,en]).order_by('-start_date')
        events_req = "1"
    else:
        events=""
        events_req = "0"
    context = {'user': user,
               'pf':pf,
               'journal':journal,
               'journal_req':journal_req,
               'conference': conference,
               'conference_req': conference_req,
               'books': books,
               'books_req': books_req,
               'projects': projects,
               'projects_req': projects_req,
               'consultancy':consultancy,
               'consultancy_req': consultancy_req,
               'patents':patents,
               'patents_req': patents_req,
               'techtransfers':techtransfers,
               'techtransfers_req': techtransfers_req,
               'mtechs':mtechs,
               'mtechs_req': mtechs_req,
               'phds':phds,
               'phds_req': phds_req,
               'fvisits':fvisits,
               'fvisits_req': fvisits_req,
               'ivisits': ivisits,
               'ivisits_req': ivisits_req,
               'consymps':consymps,
               'consymps_req': consymps_req,
               'awards':awards,
               'awards_req': awards_req,
               'talks':talks,
               'talks_req': talks_req,
               'chairs':chairs,
               'chairs_req': chairs_req,
               'keynotes':keynotes,
               'keynotes_req': keynotes_req,
               'events':events,
               'events_req': events_req,
               'first_name':request.user.first_name,
               'last_name': request.user.last_name,
               }
    return render_to_pdf('eisModulenew/rspc_generatereportshow.html', context)
