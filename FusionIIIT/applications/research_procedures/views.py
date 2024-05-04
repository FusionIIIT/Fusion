from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from applications.research_procedures.models import *
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation
from django.core.files.storage import FileSystemStorage
from django.core.exceptions import ObjectDoesNotExist
from notification.views import research_procedures_notif
from django.urls import reverse
from .forms import *
from django.contrib.auth.decorators import login_required
import datetime
from django.utils import timezone
from .models import *
from collections import defaultdict
from applications.filetracking.sdk.methods import *
from io import BytesIO
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle,Spacer
from .models import projects, financial_outlay

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

@login_required
def add_projects(request):

    # designation = getDesignation(request.user.username)
    # print("designation is " + designation)
    # if designation != 'rspc_admin':
    #     messages.error(request, 'Only RSPC Admin can add projects')
    #     return redirect("/research_procedures")
    if request.session.get('currentDesignationSelected') != 'rspc_admin':
        messages.error(request, 'Only RSPC Admin can add projects')
        return redirect("/research_procedures")

    if request.method== "POST":
        obj= request.POST

        projectname= obj.get('project_name')
        projecttype= obj.get('project_type')
        fo= obj.get('financial_outlay')
        pid= obj.get('project_investigator_id')
        copid=obj.get('co_project_investigator_id-1')
        sa= obj.get('sponsored_agency')
        startd= obj.get('start_date')
        subd= obj.get('finish_date')
        finishd= obj.get('finish_date')
        years= obj.get('number_of_years')
        # project_description= obj.get('description')
        project_info_file= request.FILES.get('project_info_file')



        check = User.objects.filter(username=pid) 

        # print(check[0].username)
        
        check= HoldsDesignation.objects.filter(user__username= pid, designation__name= "Professor") #checking for pid to exist

        if not check.exists():
                check= HoldsDesignation.objects.filter(user__username=pid , designation__name= "Assistant Professor")

                if not check.exists():
                    messages.error(request,"Request not added, no such project investigator exists ")
                    return render(request,"rs/projects.html")  

        
        
        check= HoldsDesignation.objects.filter(user__username= copid, designation__name= "Professor") #checking for copid to exist

        if not check.exists():
                check= HoldsDesignation.objects.filter(user__username=copid , designation__name= "Assistant Professor")

                if not check.exists():
                    messages.error(request,"Request not added, no such co project investigator exists ")
                    return render(request,"rs/projects.html")  

        

        copi_list = []

        for key, value in obj.items():
            if key.startswith('co_project_investigator_id-' ):
                if value not in copi_list:
                    check= HoldsDesignation.objects.filter(user__username= value, designation__name= "Professor") #checking for copid to exist
                    if not check.exists():
                        check= HoldsDesignation.objects.filter(user__username=value , designation__name= "Assistant Professor")
                        if not check.exists():
                            messages.error(request,"Request not added, no such co project investigator exists ")
                            return render(request,"rs/projects.html")
                    copi_list.append(value)

        obj= projects.objects.all()

        if len(obj)==0 :
            projectid=1
        
        else :
            projectid= obj[0].project_id+1

        for project in obj:
            if project.project_name==projectname:
                messages.error(request,"Request not added, project name already exists")
                return render(request,"rs/projects.html")
        

        for copi in copi_list:
            if copi == pid:
                messages.error(request,"Request not added, project investigator and co project investigator cannot be same")
                return render(request,"rs/projects.html")
        



        

        userpi_instance = User.objects.get(username=pid)
        usercpi_instance = User.objects.get(username=copid)

        projects.objects.create(
            project_id=projectid,
            project_name=projectname,
            project_type=projecttype, 
            status=0,
            project_investigator_id=userpi_instance,
            co_project_investigator_id=usercpi_instance,
            sponsored_agency=sa,
            start_date=startd,
            submission_date=finishd,
            finish_date=finishd,
            years=years,
            project_info_file=project_info_file
           
        )
        pi_designation= HoldsDesignation.objects.get(user=userpi_instance , designation__name="Professor")
        if not pi_designation:
            pi_designation= HoldsDesignation.objects.get(user=userpi_instance , designation__name="Assistant Professor")
        project_investigator_designation= pi_designation.designation


        file_x= create_file(
            uploader=request.user.username,
            uploader_designation="rspc_admin",
            receiver= pid,
            subject= projectname,
            receiver_designation=project_investigator_designation, 
            src_module="research_procedures",
            src_object_id= projectid,
            file_extra_JSON= { "message": "Project added successfully"},
            attached_file= project_info_file, 
        )
        
            
        for copi in copi_list:
            co_pis.objects.create(
                co_pi= User.objects.get(username=copi),
                project_id= projects.objects.get(project_id=projectid)
            )
        research_procedures_notif(request.user, userpi_instance, "Project Added")

        tracking_obj = Tracking.objects.get(file_id__id=file_x)
        file_obj= File.objects.get(id=file_x)
 
        tracking_obj.upload_file= file_obj.upload_file
        tracking_obj.remarks= "Project added by RSPC Admin" 
        tracking_obj.save()
        messages.success(request,"Project added successfully")
        categories = category.objects.all()

        notifs = request.user.notifications.all()
        data = {
            'notifications': notifs,
            "pid": pid,
            "years": list(range(1, int(years) + 1)),    
            "categories": categories,
        }
       
        return redirect("/research_procedures/financial_outlay/"+str(projectid))
    return render(request,"rs/projects.html")

@login_required
def add_fund_requests(request,pj_id):
    data= {
        "pj_id": pj_id
    }
    return render(request,"rs/add_fund_requests.html",context=data)

@login_required
def add_staff_requests(request,pj_id):
    data= {
        "pj_id": pj_id  
    }
    return render(request,"rs/add_staff_requests.html",context=data)

@login_required
def add_requests(request,id,pj_id):
    if request.method == 'POST':
        obj=request.POST


        if(id=='0') :  
            projectid = pj_id
            reqtype = obj.get('request_type')
            stats =0
            desc= obj.get('description')    
            amt= obj.get('amount')

            check= projects.objects.filter(project_id=projectid)
            if not check.exists():
                messages.error(request,"Request not added, no such project exists")
                return render(request,"rs/add_fund_requests.html")

            check= projects.objects.filter(project_id= projectid, project_investigator_id__username=pi_id)
            if not check.exists():
                messages.error(request,"Request not added, no such project investigator exists")
                return render(request,"rs/add_fund_requests.html")


            pi_id_instance=User.objects.get(username= request.user.username )
            project_instance=projects.objects.get(project_id=projectid)

            obj= requests.objects.all()
            if len(obj)==0 :
                requestid=1
            
            else :
                requestid= obj[0].request_id+1

            requests.objects.create(
                request_id=requestid,
                project_id=project_instance,
                request_type="funds",
                project_investigator_id=pi_id_instance,
                status=stats, description=desc, amount= amt
            )
            rspc_inventory.objects.create(
                inventory_id=requestid,
                project_id=project_instance,
                project_investigator_id=pi_id_instance,
                status=stats,
                description=desc, amount= amt
            )
            messages.success(request,"Request added successfully")
            return render(request,"rs/add_fund_requests.html")

        if(id=='1'):
            projectid = obj.get('project_id')
            pi_id = obj.get('project_investigator_id')
            stats = obj.get('status')
            desc= obj.get('description')

            obj= requests.objects.all()
            if len(obj)==0 :
                requestid=1
            
            else :
                requestid= obj[0].request_id+1


            check= projects.objects.filter(project_id=projectid)
            if not check.exists():
                messages.error(request,"Request not added, no such project exists")
                return render(request,"rs/add_fund_requests.html")

            check= projects.objects.filter(project_id= projectid, project_investigator_id__username=pi_id)
            if not check.exists():
                messages.error(request,"Request not added, no such project investigator exists")
                return render(request,"rs/add_fund_requests.html")

            pi_id_instance=User.objects.get(username=pi_id)
            project_instance=projects.objects.get(project_id=projectid)

            requests.objects.create(
                    request_id=requestid,
                    project_id=project_instance,
                    request_type="staff",
                    project_investigator_id=pi_id_instance,
                    description=desc
                )
        messages.success(request,"Request added successfully")
        return redirect("/research_procedures")
    return render(request, "rs/add_requests.html")    


@login_required
def view_projects(request):
    queryset= projects.objects.all()
    projects_per_page = 6
    page_number = request.GET.get('page')

    start_index = (int(page_number) - 1) * projects_per_page if page_number else 0
    end_index = start_index + projects_per_page

    paginated_projects = queryset[start_index:end_index]

    # Calculate total pages
    total_pages = (queryset.count() + projects_per_page - 1) // projects_per_page

    rspc_admin = HoldsDesignation.objects.get(designation__name="rspc_admin")
    rspc_admin =rspc_admin.user.username
    if request.user.username == rspc_admin:
        notifs = request.user.notifications.all()
        total_pages_list = [i for i in range(1, total_pages + 1)]
        data = {
        'notifications': notifs,
        'projects': paginated_projects,
        'total_pages': total_pages_list,
        'current_page': int(page_number) if page_number else 1,
        "username": request.user.username,
        }
        return render(request,"rs/view_projects_rspc.html", context= data)

    queryset= projects.objects.filter(project_investigator_id__username= request.user.username)
    start_index = (int(page_number) - 1) * projects_per_page if page_number else 0
    end_index = start_index + projects_per_page

    paginated_projects = queryset[start_index:end_index]

    # Calculate total pages
    total_pages = (queryset.count() + projects_per_page - 1) // projects_per_page
    total_pages_list = [i for i in range(1, total_pages + 1)]
    data= {
        'projects': paginated_projects,
        'total_pages': total_pages_list,
        'current_page': int(page_number) if page_number else 1,
        "username": request.user.username,
    }
    # print(data)
    # print(request.user.username)

    return render(request,"rs/view_projects_rspc.html", context= data)

@login_required
def view_requests(request,id):
        
    if id== '1':
        queryset= requests.objects.filter(request_type= "staff")
    elif id== '0':
        rspc_admin = HoldsDesignation.objects.get(designation__name="rspc_admin")
        rspc_admin =rspc_admin.user.username
        if request.user.username == rspc_admin :
            queryset= rspc_inventory.objects.all()
            notifs = request.user.notifications.all()
            data = {
            'notifications': notifs,
            "requests": queryset,
            "username": request.user.username
            }   
            return render(request,"rs/view_requests.html", context= data)
        
           
        queryset= rspc_inventory.objects.filter(project_investigator_id = request.user.username )
    else:
        render(request,"/404.html")

    data= {
        "requests": queryset,
        "username": request.user.username,
        "id":id,
    }

    # print(data)
    # print(request.user.username)
    
    return render(request,"rs/view_requests.html", context= data)

@login_required
def view_financial_outlay(request,pid):

    table_data=financial_outlay.objects.filter(project_id=pid).order_by('category', 'sub_category')
    project= projects.objects.get(project_id=pid);

    years = set(table_data.values_list('year', flat=True))

    category_data = {}
    for category in table_data.values_list('category', flat=True).distinct():
        category_data[category] = table_data.filter(category=category)


    data = {
        'table_title': 'Total Budget Outlay',
        'table_caption': '...',  # Add caption if needed
        'project_name':project.project_name,
        'years': list(years),
        'category_data': category_data,
    }

    # print(data)
    return render(request,"rs/view_financial_outlay.html", context= data)




@login_required
def submit_closure_report(request,id):
    id= int(id)
    obj= projects.objects.get(project_id=id)
    obj.status= 1; 
    obj.save()

    queryset= projects.objects.filter(project_investigator_id = request.user.username)

    # print(queryset)
    
    data= {
        "projects": queryset,
        "username": request.user.username
    }
    messages.success(request,"Closure report submitted successfully")
    return render(request,"rs/view_projects_rspc.html",context=data)

@login_required
def view_project_inventory(request,pj_id):
    pj_id=int(pj_id)
    queryset= requests.objects.filter(project_id=pj_id,request_type="funds")


    # print(queryset)
    
    data= {
        "requests": queryset,
        "username": request.user.username
    }
    return render(request,"rs/view_project_inventory.html",context=data)

@login_required
def view_project_staff(request,pj_id):
    pj_id=int(pj_id)
    queryset= requests.objects.filter(project_id=pj_id,request_type="staff")


    # print(queryset)
    
    data= {
        "requests": queryset,
        "username": request.user.username
    }
    return render(request,"rs/view_project_staff.html",context=data)



def view_project_info(request,id):
    id= int(id)
    obj= projects.objects.get(project_id=id)


    copis= co_pis.objects.filter(project_id__project_id=id)
    data = {
        "project": obj,
        "copis": copis
    }
    
    return render(request,"rs/view_project_info.html", context= data)

@login_required
def financial_outlay_form(request,pid):
    pid= int(pid)
    project= projects.objects.get(project_id=pid);
    categories = category.objects.all().distinct();

    categories_with_subcategories = category.objects.values('category_name', 'sub_category_name')

    # Organize the data into a dictionary
    category_subcategory_map = {}
    for item in categories_with_subcategories:
        category_name = item['category_name']
        subcategory = item['sub_category_name']
        if category_name in category_subcategory_map:
            category_subcategory_map[category_name].append(subcategory)
        else:
            category_subcategory_map[category_name] = [subcategory]

    # Pass the organized data to the template
    
    data = {
       "project_id": project.project_id,
       "project_name":project.project_name,
       "years": list(range(1, int(project.years) + 1)),
       "category_subcategory_map": category_subcategory_map
       
    }

    return render(request,"rs/add_financial_outlay.html", context= data)
# return render(request,"rs/add_financial_outlay.html", context= data)


@login_required
def add_staff_details(request, pid):
    if request.session.get('currentDesignationSelected') != 'rspc_admin':
        messages.error(request, 'Only RSPC Admin can add staff details')
        return redirect("/research_procedures")
    if request.method == 'POST':
        obj = request.POST
        for key, value in obj.items():
            if key.startswith('staff_id'):
                year_count = key.split('-')[-2]
                staff_count = key.split('-')[-1]
                staff_id_key = f'staff_id-{year_count}-{staff_count}'
                staff_name_key = f'staff_name-{year_count}-{staff_count}'
                qualification_key = f'qualification-{year_count}-{staff_count}'
                stipend_key = f'stipend-{year_count}-{staff_count}'
                year = year_count
                staff_id = obj.get(staff_id_key, '').strip()
                staff_name = obj.get(staff_name_key, '').strip()
                qualification = obj.get(qualification_key, '').strip()
                stipend = obj.get(stipend_key, '').strip()
                project_instance = projects.objects.get(project_id=pid)
                # print(type(staff_id))
                ob = staff_allocations.objects.all()

                if len(ob) == 0:
                    fid = 1
                else:
                    fid = ob[0].staff_allocation_id + 1

                if not User.objects.filter(username=staff_id).exists():

                    messages.error(request, "Staff with ID " + staff_id + " does not exist")
                    return redirect("/research_procedures/add_staff_details/"+str(pid))
                
                staff_id_instance = User.objects.get(username=staff_id)
                
         
                staff_allocations.objects.create(
                    staff_allocation_id=fid,
                    project_id=project_instance,
                    staff_id=staff_id_instance,
                    staff_name=staff_name,
                    qualification=qualification,
                    year=year,
                    stipend=stipend
                )

        return redirect("/research_procedures/view_staff_details/"+str(pid))

    project = projects.objects.get(project_id=pid)

    years_passed = int((datetime.datetime.now().date() - project.start_date).days / 365.25)

    data = {
        "project_id": project.project_id,
        "project_name" : project.project_name,
        "years": list(range(1, int(project.years) + 1)),
        "year": int(years_passed) + 1,
    }

    return render(request, "rs/add_staff_details.html", context=data)

@login_required
def view_staff_details(request,pid):

    staff_records = staff_allocations.objects.filter(project_id=pid)
    
    # Initialize a dictionary to hold data year-wise
    data_by_year = {}
    project = projects.objects.get(project_id=pid)

    # Iterate through each staff record
    for record in staff_records:
        year = record.year
        if year not in data_by_year:
            data_by_year[year] = []
        data_by_year[year].append({
            'staff_allocation_id': record.staff_allocation_id,
            'staff_id' : record.staff_id,
            'staff_name': record.staff_name,
            'qualification': record.qualification,
            'stipend': record.stipend,
            'start_date': record.start_date,
            'end_date': record.end_date,
        })
# Pass the organized data to the template
    context = {
        'data_by_year': data_by_year,
        'project_name':project.project_name
    }
    rspc_admin = HoldsDesignation.objects.get(designation__name="rspc_admin")
    

    return render(request, "rs/view_staff_details.html", context)


@login_required
def add_financial_outlay(request,pid):
    if request.method == 'POST':
        
        project = projects.objects.get(project_id=pid)
        project.financial_outlay_status = 1
        project.save()
        
        obj = request.POST
        for key, value in obj.items():
            if key.startswith('category-select'):                
                year_count = key.split('-')[-2]
                category_count = key.split('-')[-1]
                subcategory_key = f'subcategory-select-{year_count}-{category_count}'
                amount_key = f'amount-{year_count}-{category_count}'

                category = value
                subcategory = obj.get(subcategory_key, [''])
                amount = obj.get(amount_key, [''])
                year = int(year_count)  

                # print(year)
                # print(amount)
                # print(subcategory)
                # print(category)
                project_instance=projects.objects.get(project_id=pid)
                

                ob= financial_outlay.objects.all()
                if len(ob)==0 :
                    fid=1
                
                else :
                    fid= ob[0].financial_outlay_id+1
                financial_outlay.objects.create(
                    financial_outlay_id=fid,
                    project_id=project_instance,
                    category=category,
                    sub_category=subcategory,
                    amount=amount,
                    year=year,
                    status=0,
                    staff_limit=0
                )
    
                
    return redirect("/research_procedures/view_financial_outlay/"+str(pid))

@login_required
def inbox(request):
    
    projects_per_page = 6
    page_number = request.GET.get('page')

    start_index = (int(page_number) - 1) * projects_per_page if page_number else 0
    end_index = start_index + projects_per_page



    user_designation= request.session.get('currentDesignationSelected')
   
    print(user_designation)
    user_designation= get_designation_instance(user_designation)

    
    user_obj = get_user_by_username(request.user.username)
    
    # There was some issue using view_inbox function, so I had to write the code here
    
    data= Tracking.objects.filter(receiver_id=user_obj, receive_design=user_designation, file_id__src_module="research_procedures").order_by('-receive_date')
    print(data)
    files= []
    count =0
    for file  in data:
        count+=1
        files.append( File.objects.get(id=file.file_id.id) )

    print(files)
    paginated_projects = data[start_index:end_index]
    
    # Calculate total pages
    total_pages = (data.count() + projects_per_page - 1) // projects_per_page
    total_pages_list = [i for i in range(1, total_pages + 1)]
    data1={
        'inbox': paginated_projects,
        'total_pages': total_pages_list,
        'current_page': int(page_number) if page_number else 1,
        "files": paginated_projects,
    }
    # print(data)
    return render(request, "rs/inbox.html",context= data1)
  
def view_file(request, id):
    file1= File.objects.get(id=id)
    tracks= Tracking.objects.filter(file_id=file1)
    current_user = Tracking.objects.filter(file_id=file1).order_by('-receive_date')[0].current_id

    return render(request, "rs/view_file.html", context= {"file": file1, "tracks": tracks, "current_user": current_user})

@login_required
def add_staff_request(request,id):
    if request.method == 'POST':
        obj= request.POST
        projectid = int(id)
        receiver_designation = obj.get('receiver')
        
        receiver_designation= get_designation_instance(receiver_designation)
        receiver = get_user_by_designation(receiver_designation).username

        subject= obj.get('subject')
        sender = request.user.username
        file_to_forward= request.FILES.get('file_to_forward')
        project_instance=projects.objects.get(project_id=projectid)
        receiver_instance=User.objects.get(username=receiver)
        sender_designation= HoldsDesignation.objects.get(user= request.user).designation
        receiver_designation = receiver_designation

        file_x= create_file(
            uploader=sender,    
            uploader_designation=sender_designation,
            receiver= receiver_instance.username,
            receiver_designation=receiver_designation, 
            src_module="research_procedures",
            src_object_id= projectid,
            subject= subject,
            file_extra_JSON= { "message": "Request Added." },
            attached_file= file_to_forward, 
        )

        tracking_obj = Tracking.objects.get(file_id__id=file_x)
        file_obj= File.objects.get(id=file_x)
    
        tracking_obj.upload_file= file_obj.upload_file
        tracking_obj.remarks= "Request Added by " + request.user.username
        tracking_obj.save()
        

        messages.success(request,"request added successfully")

    return redirect("/research_procedures/view_project_info/"+ str(projectid))

@login_required
def view_request_inbox(request):
    user_designation= getDesignation(request.user.username)
    print(user_designation)
    data = view_inbox(request.user.username,user_designation, "research_procedures")
    print(data)
    files= []
    count =0
    for i in data:
        count+=1
        file1= File.objects.get(id=i['id'])
        files.append((count, file1))


    data={
        
        "inbox": data,
        "files": files
    }
    # print(data)
    return render(request, "rs/view_request_inbox.html",context= data)

@login_required
def forward_request(request,id):
    # forward_file(
    #     file_id: int,
    #     receiver: str,
    #     receiver_designation: str,
    #     file_extra_JSON: dict,
    #     remarks: str = "",
    #     file_attachment: Any = None) -> int:
    if request.method == 'POST':
        obj= request.POST
        
        fileid = int(id)
        filez= File.objects.get(id=fileid)
        
        remarks = obj.get('remarks')
        receiver_designation =obj.get('receiver_designation')
        if receiver_designation == 'project_investigator':
            project= projects.objects.get(project_id= filez.src_object_id )
            receiver_instance= project.project_investigator_id
            receiver_designation= getDesignation(receiver_instance.username)
        else:
            receiver_instance= HoldsDesignation.objects.get(designation__name=receiver_designation).user
        attachment= request.FILES.get('attachment')
        receiver= receiver_instance.username

        filex= forward_file(
            file_id= fileid,
            receiver= receiver,
            receiver_designation=receiver_designation, 
            file_extra_JSON= { "message": "Request forwarded."},
            remarks= remarks,
            file_attachment= attachment, 
        )
        if(receiver_designation == 'Professor' or receiver_designation == 'Assistant Professor' or receiver_designation == 'rspc_admin'):
            research_procedures_notif(request.user, receiver_instance, "Request update")
        messages.success(request,"Request forwarded successfully") 


    return redirect("/research_procedures/inbox")

    
    return redirect("/research_procedures/view_request_inbox")
        



def update_time_period(request,id):
    if request.method== "POST":

        obj = request.POST
        up_year= obj.get('updated_year')

        project = get_object_or_404(projects, project_id=id)

        project.years=up_year

        project.save()

        return redirect("/research_procedures/financial_outlay/"+str(id))


@login_required
def update_financial_outlay(request,pid):

    
    #post method
    if(request.session.get('currentDesignationSelected') != 'rspc_admin'):
        messages.error(request, 'Only RSPC Admin can update financial outlay')
        return redirect("/research_procedures")

    if request.method=="POST" :
        
        obj = request.POST
        financial_outlay_id = obj.get('financial_outlay_id')
        # print("sdfkjsdfd")
        used_amount = obj.get('used_amount')
        if used_amount is None or used_amount == '':
            messages.error(request,"Enter amount")
            return redirect("/research_procedures/update_financial_outlay/" + str(pid))
        financial_outlay_instance = financial_outlay.objects.get(financial_outlay_id=financial_outlay_id)
        # financial_outlay_instance.status = 1
        financial_outlay_instance.utilized_amount += int(used_amount)
        financial_outlay_instance.save()
        messages.success(request,"Financial Outlay updated successfully")
        return redirect("/research_procedures/update_financial_outlay/"+str(pid))
    
    
        
    #get method
    table_data=financial_outlay.objects.filter(project_id=pid).order_by('category', 'sub_category')
    project= projects.objects.get(project_id=pid);

    years = set(table_data.values_list('year', flat=True))

    category_data = {}
    for category in table_data.values_list('category', flat=True).distinct():
        category_data[category] = table_data.filter(category=category)


    data = {
        'table_title': 'Total Budget Outlay',
        'table_caption': '...',  # Add caption if needed
        'project_name':project.project_name,
        'years': list(years),
        'category_data': category_data,
        'project_id': pid,
    }

    # print(data)
    return render(request,"rs/update_financial_outlay.html", context= data)

@login_required
def approve_request(request,id):

    

    if request.method == 'POST':
        obj= request.POST
        fileid = id
        message= "Request approved by " + request.user.username
        designation = get_designation_instance("rspc_admin")
        receiver_instance= get_user_by_designation(designation)
        receiver_designation= designation
        receiver= receiver_instance.username
        sender = request.user.username
        filex= get_file_by_id(fileid)
        file2=create_file(
            uploader=sender,
            uploader_designation= getDesignation(sender),
            receiver= receiver,
            receiver_designation=receiver_designation, 
            src_module="research_procedures",
            src_object_id= filex.src_object_id,
            file_extra_JSON= { "message": message + " by "+ sender},
            attached_file= filex.upload_file, 
        )
        delete_file(fileid)
        messages.success(request,"Request approved successfully")
    return redirect("/research_procedures/inbox")



def download_project_pdf(request, project_id):
    # Retrieve project and financial outlay information
    project = projects.objects.get(project_id=project_id)
    financial_outlays = financial_outlay.objects.filter(project_id=project_id)

    # Create a buffer for the PDF
    buffer = BytesIO()

    # Create a PDF document
    pdf = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    # Construct project info table data
    project_data = [['Project ID', 'Project Name', 'Project Type', 'Sponsored Agency', 'Start Date', 'Finish Date'],
                    [project.project_id, project.project_name, project.project_type, project.sponsored_agency,
                     project.start_date, project.finish_date]]

    # Construct financial outlay table data
    financial_outlay_data = [['Financial Outlay ID', 'Category', 'Subcategory', 'Amount', 'Year']]
    for outlay in financial_outlays:
        financial_outlay_data.append([outlay.financial_outlay_id, outlay.category, outlay.sub_category, outlay.amount, outlay.year])

    # Create project info table
    project_table = Table(project_data)
    project_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                       ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                       ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                       ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                       ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                       ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                       ('GRID', (0, 0), (-1, -1), 1, colors.black)]))

    # Create financial outlay table
    financial_outlay_table = Table(financial_outlay_data)
    financial_outlay_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                                ('GRID', (0, 0), (-1, -1), 1, colors.black)]))

    # Add tables to elements
    elements.append(project_table)
    elements.append(Spacer(1, 20)) 
    elements.append(financial_outlay_table)

    # Build the PDF
    pdf.build(elements)

    # Close the PDF buffer and return the response with PDF content for download
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=project_{project_id}.pdf'
    return response


def change_year(request,id):
    if request.method == 'POST':
        obj= request.POST
        projectid = int(id)
        year = obj.get('year')
        project_instance=projects.objects.get(project_id=projectid)
        project_instance.years= year
        project_instance.save()
        messages.success(request,"Year changed successfully")
    return redirect("/research_procedures/view_financial_outlay/"+str(projectid))

def change_end_date(request,id):
    if request.method == "POST":
        obj= request.POST
        staff_allocations_id = int(id)
        end_date = obj.get('end_date')
        staff_allocation_instance = staff_allocations.objects.get(staff_allocation_id=staff_allocations_id)
        staff_allocation_instance.end_date = end_date
        staff_allocation_instance.save()
        messages.success(request,"End date changed successfully")
    return redirect("/research_procedures/view_staff_details/"+str(staff_allocation_instance.project_id.project_id))

def AjaxDropdown(request):

    if request.method == 'POST':
        value = request.POST.get('value')
        users = User.objects.filter(username__startswith=value)
        users = serializers.serialize('json', list(users))

        context = {
            'users': users
        }
        return HttpResponse(JsonResponse(context), content_type='application/json')


def getDesignation(us):
    user_inst = User.objects.get(username= us)

    user_designation= HoldsDesignation.objects.filter(user= user_inst)
    if user_designation.exists():
        user_designation= user_designation.first().designation.name
    
    return user_designation

def get_file_by_id(id):
    file1= File.objects.get(id=id)
    print(file1)
    return file1

def delete_file(id):
    file1= File.objects.get(id=id)
    tracking= Tracking.objects.get(file_id=file1)
    tracking.delete()
    file1.delete()
    return

def get_user_by_username(username):
    return User.objects.get(username=username)

def get_user_by_designation(designation):
    return HoldsDesignation.objects.get(designation=designation).user

def get_designation_instance(designation):
    return Designation.objects.get(name=designation)

def get_obj_by_username_and_designation(username,designation):
    user_instance = get_user_by_username(username)
    designation_instance = get_designation_instance(designation)
    
    return HoldsDesignation.objects.filter(user=user_instance, designation=designation_instance)



    



