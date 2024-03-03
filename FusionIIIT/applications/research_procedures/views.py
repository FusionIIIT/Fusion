from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from applications.research_procedures.models import *
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation
from django.core.files.storage import FileSystemStorage
from notification.views import research_procedures_notif
from django.urls import reverse
from .forms import *
from django.contrib.auth.decorators import login_required
import datetime
from .models import *

# Faculty can file patent and view status of it.
@login_required
def patent_registration(request):

   
    return render(request ,"rs/research.html")

@login_required
#dean_rspc can update status of patent.   
def patent_status_update(request):
    
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


def add_projects(request):
    if request.method== "POST":
        obj= request.POST
        projectid= obj.get('project_id')
        projectname= obj.get('project_name')
        projecttype= obj.get('project_type')
        stats= obj.get('status')
        fo= obj.get('financial_outlay')
        pid= obj.get('project_investigator_id')
        rspc= obj.get('rspc_admin_id')
        copid=obj.get('co_project_investigator_id')
        sa= obj.get('sponsored_agency')
        startd= obj.get('start_date')
        subd= obj.get('submission_date')
        finishd= obj.get('finish_date')

        # check= HoldsDesignation.objects.get(user=pid , designation= "Professor")
        # if not check.exists():
        #         check= HoldsDesignation.objects.get(user=pid , designation= "Assistant Professor")

        #         if not check.exists():
        #             messages.error(request,"Request not added, no such project investigator exists")
        #             return redirect("rs/projects.html")    
        
        # check= User.objects.filter(username=rspc)
        # if not check.exists():
        #     messages.error(request,"Project not added, no such rspc admin exists")
        #     return render(request,"rs/projects.html")

        # check= HoldsDesignation.objects.get(user=copid , designation= "Professor")
        # if not check.exists():
        #         check= HoldsDesignation.objects.get(user=copid , designation= "Assistant Professor")

        #         if not check.exists():
        #             messages.error(request,"Request not added, no such project investigator exists")
        #             return redirect("rs/projects.html")   


        projects.objects.create(
            project_id=projectid,
            project_name=projectname,
            project_type=projecttype, 
            status=stats,
            financial_outlay=fo,
            project_investigator_id=pid,
            rspc_admin_id=rspc,
            co_project_investigator_id=copid,
            sponsored_agency=sa,
            start_date=startd,
            submission_date=subd,
            finish_date=finishd
        )

        messages.success(request,"Project added successfully")
    return render(request,"rs/projects.html")

def add_fund_requests(request):
    return render(request,"rs/add_fund_requests.html")

def add_staff_requests(request):
    return render(request,"rs/add_staff_requests.html")

def add_requests(request,id):
    if request.method == 'POST':
        obj=request.POST


        if(id=='0') :  
            requestid = obj.get('request_id')
            projectid = obj.get('project_id')
            reqtype = obj.get('request_type')
            pi_id = obj.get('project_investigator_id')
            stats = obj.get('status')
            desc= obj.get('description')    
            amt= obj.get('amount')

            check= projects.objects.filter(project_id=projectid)
            if not check.exists():
                messages.error(request,"Request not added, no such project exists")
                return render(request,"rs/add_fund_requests.html")

            check= projects.objects.filter(project_id= projectid, project_investigator_id=pi_id)
            if not check.exists():
                messages.error(request,"Request not added, no such project investigator exists")
                return render(request,"rs/add_fund_requests.html")

            requests.objects.create(
                request_id=requestid,
                project_id=projectid,
                request_type=reqtype,
                project_investigator_id=pi_id,
                status=stats, description=desc, amount= amt
            )
            rspc_inventory.objects.create(
                inventory_id=requestid,
                project_id=projectid,
                project_investigator_id=pi_id,
                status=stats,
                description=desc, amount= amt
            )
            messages.success(request,"Request added successfully")
            return render(request,"rs/add_fund_requests.html")

        if(id=='1'):
            requestid = obj.get('request_id')
            projectid = obj.get('project_id')
            reqtype = obj.get('request_type')
            pi_id = obj.get('project_investigator_id')
            stats = obj.get('status')

            check= projects.objects.filter(project_id=projectid)
            if not check.exists():
                messages.error(request,"Request not added, no such project exists")
                return render(request,"rs/add_fund_requests.html")

            check= projects.objects.filter(project_id= projectid, project_investigator_id=pi_id)
            if not check.exists():
                messages.error(request,"Request not added, no such project investigator exists")
                return render(request,"rs/add_fund_requests.html")


            requests.objects.create(
            request_id=requestid,
            project_id=projectid,
            request_type=reqtype,
            project_investigator_id=pi_id,
            status=stats,description= "staff request", amount= 0
            )
        messages.success(request,"Request added successfully")
        # print("prudvi lanja")
        return redirect("/research_procedures")
    return render(request, "rs/add_requests.html")    

    # return redirect("/")





def view_projects(request):
    # context= 
    queryset= projects.objects.all()


    if request.user.username == "21bcs3000":
        data= {
        "projects": queryset,
        "username": request.user.username,
        }
        return render(request,"rs/view_projects_rspc.html", context= data)

    queryset= projects.objects.filter(project_investigator_id= request.user.username)
   
    data= {
        "projects": queryset,
        "username": request.user.username,
       
    }
    print(data)

    print(request.user.username)
    if request.user.username != "atul":
        return redirect("/")

    return render(request,"rs/view_projects_rspc.html", context= data)

def view_requests(request,id):
    # context=  
        
    if id== '1':
        queryset= requests.objects.filter(request_type= "staff")
    elif id== '0':
        if request.user.username == "21bcs3000" :
            queryset= rspc_inventory.objects.all()
            data= {
            "requests": queryset,
            "username": request.user.username
            }   
            return render(request,"rs/view_requests.html", context= data)
        
           
        queryset= rspc_inventory.objects.filter(project_investigator_id = request.user.username)
    else:
        render(request,"/404.html")

    data= {
        "requests": queryset,
        "username": request.user.username,
        "id":id,
    }

    print(data)
    print(request.user.username)

    return render(request,"rs/view_requests.html", context= data)

def submit_closure_report(request,id):
    id= int(id)
    obj= projects.objects.get(project_id=id)
    obj.status= 1; 
    obj.save()

    queryset= projects.objects.filter(project_investigator_id = request.user.username)

    print(queryset)
    
    data= {
        "projects": queryset,
        "username": request.user.username
    }
    messages.success(request,"Closure report submitted successfully")
    return render(request,"rs/view_projects_rspc.html",context=data)

def projectss(request):
    return render(request,"rs/projects.html")