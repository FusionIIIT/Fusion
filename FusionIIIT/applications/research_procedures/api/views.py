from rest_framework.viewsets import ModelViewSet
from applications.research_procedures.models import *
from .serializers import *
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticatedOrReadOnly 
from django.shortcuts import redirect, render, get_object_or_404
from rest_framework.response import Response
from django.http import JsonResponse
from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from applications.research_procedures.models import *
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation, Faculty
from django.core.files.storage import FileSystemStorage
from django.core.exceptions import ObjectDoesNotExist
from notification.views import RSPC_notif
from django.urls import reverse
from django.contrib.auth.decorators import login_required
import datetime
import json
from django.utils import timezone
from collections import defaultdict
from applications.filetracking.sdk.methods import *
from applications.filetracking.models import *
from applications.filetracking.api.serializers import FileHeaderSerializer
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
# # # Faculty can file patent and view status of it.

# # @login_required
# # def patent_registration(request):

   
# #     return render(request ,"rs/research.html")

# # @login_required
# # #dean_rspc can update status of patent.   
# # def patent_status_update(request):
    
# #     user = request.user
# #     user_extra_info = ExtraInfo.objects.get(user=user)
# #     user_designations = HoldsDesignation.objects.filter(user=user)
# #     if request.method=='POST':
# #         if(user_designations.exists()):
# #             if(user_designations.first().designation.name == "dean_rspc" and user_extra_info.user_type == "faculty"):
# #                 patent_application_id = request.POST.get('id')
# #                 patent = Patent.objects.get(application_id=patent_application_id)
# #                 patent.status = request.POST.get('status')
# #                 patent.save()
# #                 messages.success(request, 'Patent status updated successfully')
# #                 # Create a notification for the user about the patent status update
# #                 dean_rspc_user = HoldsDesignation.objects.get(designation=Designation.objects.filter(name='dean_rspc').first()).working
# #                 research_procedures_notif(dean_rspc_user,patent.faculty_id.user,request.POST.get('status'))
# #             else:
# #                 messages.error(request, 'Only Dean RSPC can update status of patent')
# #     return redirect(reverse("research_procedures:patent_registration"))

# # @login_required
# # def research_group_create(request):
    
# #     user = request.user
# #     user_extra_info = ExtraInfo.objects.get(user=user)
# #     if request.method=='POST':
# #         if user_extra_info.user_type == "faculty":
# #             form = ResearchGroupForm(request.POST)
            
# #             if form.is_valid():
# #                 form.save()
# #                 messages.success(request, 'Research group created successfully')
# #         else:
# #             messages.error(request, 'Only Faculty can create research group')
# #     return redirect(reverse("research_procedures:patent_registration"))

# # @login_required
# # def project_insert(request):
# #     user = get_object_or_404(ExtraInfo, user=request.user)
# #     pf = user.id

# #     research_project = ResearchProject()
# #     research_project.user = request.user
# #     research_project.pf_no = pf
# #     research_project.pi = request.POST.get('pi')
# #     research_project.co_pi = request.POST.get('co_pi')
# #     research_project.title = request.POST.get('title')
# #     research_project.financial_outlay = request.POST.get('financial_outlay')
# #     research_project.funding_agency = request.POST.get('funding_agency')
# #     research_project.status = request.POST.get('status')
# #     x = request.POST.get('start')
# #     if x[:5] == "Sept." :
# #         x = "Sep." + x[5:]
# #     if (request.POST.get('start') != None and request.POST.get('start') != '' and request.POST.get('start') != 'None'):
# #         try:
# #             research_project.start_date = datetime.datetime.strptime(x, "%B %d, %Y")
# #         except:
# #             research_project.start_date = datetime.datetime.strptime(x, "%b. %d, %Y")
# #     x = request.POST.get('end')
# #     if x[:5] == "Sept." :
# #         x = "Sep." + x[5:]
# #     if (request.POST.get('end') != None and request.POST.get('end') != '' and request.POST.get('end') != 'None'):
# #         try:
# #             research_project.finish_date = datetime.datetime.strptime(x, "%B %d, %Y")
# #         except:
# #             research_project.finish_date = datetime.datetime.strptime(x, "%b. %d, %Y")
# #     x = request.POST.get('sub')
# #     if x[:5] == "Sept." :
# #         x = "Sep." + x[5:]
# #     if (request.POST.get('sub') != None and request.POST.get('sub') != '' and request.POST.get('sub') != 'None'):
# #         try:
# #             research_project.date_submission = datetime.datetime.strptime(x, "%B %d, %Y")
# #         except:
# #             research_project.date_submission = datetime.datetime.strptime(x, "%b. %d, %Y")
# #     research_project.save()
# #     messages.success(request, 'Successfully created research project')
# #     return redirect(reverse("research_procedures:patent_registration"))

# # @login_required
# # def consult_insert(request):
# #     user = get_object_or_404(ExtraInfo, user=request.user)
# #     pf = user.id
# #     consultancy_project = ConsultancyProject()
# #     consultancy_project.user = request.user
# #     consultancy_project.pf_no = pf
# #     consultancy_project.consultants = request.POST.get('consultants')
# #     consultancy_project.client = request.POST.get('client')
# #     consultancy_project.title = request.POST.get('title')
# #     consultancy_project.financial_outlay = request.POST.get('financial_outlay')
# #     x = request.POST.get('start')
# #     if x[:5] == "Sept." :
# #         x = "Sep." + x[5:]
# #     if (request.POST.get('start') != None and request.POST.get('start') != '' and request.POST.get('start') != 'None'):
# #         try:
# #             consultancy_project.start_date = datetime.datetime.strptime(x, "%B %d, %Y")
# #         except:
# #             consultancy_project.start_date = datetime.datetime.strptime(x, "%b. %d, %Y")
# #     x = request.POST.get('end')
# #     if x[:5] == "Sept." :
# #         x = "Sep." + x[5:]
# #     if (request.POST.get('end') != None and request.POST.get('end') != '' and request.POST.get('end') != 'None'):
# #         try:
# #             consultancy_project.end_date = datetime.datetime.strptime(x, "%B %d, %Y")
# #         except:
# #             consultancy_project.end_date = datetime.datetime.strptime(x, "%b. %d, %Y")
# #     consultancy_project.save()
# #     messages.success(request,"Successfully created consultancy project")
# #     return redirect(reverse("research_procedures:patent_registration"))

# def add_projects(request):
#     if request.method== "POST":
#         obj= request.POST
#         projectname= obj.get('project_name')
#         projecttype= obj.get('project_type')
#         fo= obj.get('financial_outlay')
#         pid= obj.get('project_investigator_id')
#         copid=obj.get('co_project_investigator_id')
#         sa= obj.get('sponsored_agency')
#         startd= obj.get('start_date')
#         subd= obj.get('finish_date')
#         finishd= obj.get('finish_date')
#         years= obj.get('number_of_years')
#         # project_description= obj.get('description')
#         project_info_file= request.FILES.get('project_info_file')

#         check = User.objects.filter(username=pid) 
#         # print(check[0].username)

       
        
#         check= HoldsDesignation.objects.filter(user__username=pid , designation__name= "Professor")
#         if not check.exists():
#                 check= HoldsDesignation.objects.filter(user__username=pid , designation__name= "Assistant Professor")

#                 if not check.exists():
#                     messages.error(request,"Request not added, no such project investigator exists 2")
#                     return render(request,"rs/projects.html")  

        
#         check= HoldsDesignation.objects.filter(user__username=copid , designation__name= "Professor")
#         if not check.exists():
#                 check= HoldsDesignation.objects.filter(user__username=copid , designation__name= "Assistant Professor")

#                 if not check.exists():
#                     messages.error(request,"Request not added, no such project investigator exists 2")
#                     return render(request,"rs/projects.html")  

        
#         obj= projects.objects.all()
#         if len(obj)==0 :
#             projectid=1
        
#         else :
#             projectid= obj[0].project_id+1

#         userpi_instance = User.objects.get(username=pid)
#         usercpi_instance = User.objects.get(username=copid)

#         projects.objects.create(
#             project_id=projectid,
#             project_name=projectname,
#             project_type=projecttype, 
#             status=0,
#             project_investigator_id=userpi_instance,
#             co_project_investigator_id=usercpi_instance,
#             sponsored_agency=sa,
#             start_date=startd,
#             submission_date=finishd,
#             finish_date=finishd,
#             years=years,
#             project_info_file=project_info_file
           
#         )
#         project_investigator_designation = HoldsDesignation.objects.get(user=userpi_instance).designation

#         file_x= create_file(
#             uploader=request.user.username,
#             uploader_designation="rspc_admin",
#             receiver= pid,
#             receiver_designation=project_investigator_designation, 
#             src_module="research_procedures",
#             src_object_id= projectid,
#             file_extra_JSON= { "message": "Project added successfully"},
#             attached_file= project_info_file, 
#         )

#         messages.success(request,"Project added successfully")
#         categories = category.objects.all()

#         data = {
#             "pid": pid,
#             "years": list(range(1, int(years) + 1)),    
#             "categories": categories,
#         }
       
#         return redirect("/research_procedures/financial_outlay/"+str(projectid))
#     return render(request,"rs/projects.html")

# def add_fund_requests(request,pj_id):
#     data= {
#         "pj_id": pj_id
#     }
#     return render(request,"rs/add_fund_requests.html",context=data)

# def add_staff_requests(request,pj_id):
#     data= {
#         "pj_id": pj_id  
#     }
#     return render(request,"rs/add_staff_requests.html",context=data)

# def add_projects(request):

#     # designation = getDesignation(request.user.username)
#     # print("designation is " + designation)
#     # if designation != 'rspc_admin':
#     #     messages.error(request, 'Only RSPC Admin can add projects')
#     #     return redirect("/research_procedures")

#     if request.method== "POST":
#         obj= request.POST
#         projectname= obj.get('project_name')
#         projecttype= obj.get('project_type')
#         fo= obj.get('financial_outlay')
#         pid= obj.get('project_investigator_id')
#         copid=obj.get('co_project_investigator_id')
#         sa= obj.get('sponsored_agency')
#         startd= obj.get('start_date')
#         subd= obj.get('finish_date')
#         finishd= obj.get('finish_date')
#         years= obj.get('number_of_years')
#         # project_description= obj.get('description')
#         project_info_file= request.FILES.get('project_info_file')

#         check = User.objects.filter(username=pid) 

#         # print(check[0].username)


       
        
#         check= get_obj_by_username_and_designation(pid, "Professor") #checking for pid to exist

#         if not check.exists():
#                 check= HoldsDesignation.objects.filter(user__username=pid , designation__name= "Assistant Professor")

#                 if not check.exists():
#                     messages.error(request,"Request not added, no such project investigator exists ")
#                     return render(request,"rs/projects.html")  

        
        
#         check= get_obj_by_username_and_designation(copid, "Professor") #checking for copid to exist

#         if not check.exists():
#                 check= HoldsDesignation.objects.filter(user__username=copid , designation__name= "Assistant Professor")

#                 if not check.exists():
#                     messages.error(request,"Request not added, no such co project investigator exists ")
#                     return render(request,"rs/projects.html")  

        
#         obj= projects.objects.all()


#         if len(obj)==0 :
#             projectid=1
        
#         else :
#             projectid= obj[0].project_id+1

#         for project in obj:
#             if project.project_name==projectname:
#                 messages.error(request,"Request not added, project name already exists")
#                 return render(request,"rs/projects.html")
        


        

#         userpi_instance = User.objects.get(username=pid)
#         usercpi_instance = User.objects.get(username=copid)

#         projects.objects.create(
#             project_id=projectid,
#             project_name=projectname,
#             project_type=projecttype, 
#             status=0,
#             project_investigator_id=userpi_instance,
#             co_project_investigator_id=usercpi_instance,
#             sponsored_agency=sa,
#             start_date=startd,
#             submission_date=finishd,
#             finish_date=finishd,
#             years=years,
#             project_info_file=project_info_file
           
#         )
#         project_investigator_designation = HoldsDesignation.objects.get(user=userpi_instance).designation

#         file_x= create_file(
#             uploader=request.user.username,
#             uploader_designation="rspc_admin",
#             receiver= pid,
#             receiver_designation=project_investigator_designation, 
#             src_module="research_procedures",
#             src_object_id= projectid,
#             file_extra_JSON= { "message": "Project added successfully"},
#             attached_file= project_info_file, 
#         )

#         messages.success(request,"Project added successfully")
#         categories = category.objects.all()

#         data = {
#             "pid": pid,
#             "years": list(range(1, int(years) + 1)),    
#             "categories": categories,
#         }
       
#         return redirect("/research_procedures/financial_outlay/"+str(projectid))
#     return render(request,"rs/projects.html")
# @api_view(['GET'])
# def view_projects(request):
#     queryset= projects.objects.all()
#     print('---------------------------------------------------------------')
#     rspc_admin = HoldsDesignation.objects.get(designation__name="rspc_admin")
#     rspc_admin =rspc_admin.user.username
#     data = Project_serializer(queryset, many=True).data
#     if request.user.username == rspc_admin:
#         data= {
#         "projects": data,
#         "username": request.user.username,
#         }
#         return JsonResponse(data,safe=False)

#     queryset= projects.objects.filter(project_investigator_id__username= request.user.username)
#     data2 = Project_serializer(queryset, many=True).data
#     data= {
#         "projects": data2,
#         "username": request.user.username,
#     }
#     # print(data)
#     # print(request.user.username)
    
#     return JsonResponse(data,safe=False)
# def view_project_info(request,id):
#     id= int(id)
#     obj= projects.objects.filter(project_id=id)
#     data = Project_serializer(obj, many=True).data


#     # data = {
#     #     "project": obj,
#     # }
#     data = {
#         "project": data,
#     }
    
#     return JsonResponse(data , safe=False)

# # def view_requests(request,id):
        
# #     if id== '1':
# #         queryset= requests.objects.filter(request_type= "staff")
# #     elif id== '0':
# #         rspc_admin = HoldsDesignation.objects.get(designation__name="rspc_admin")
# #         rspc_admin =rspc_admin.user.username
# #         if request.user.username == rspc_admin :
# #             queryset= rspc_inventory.objects.all()
# #             data= {
# #             "requests": queryset,
# #             "username": request.user.username
# #             }   
# #             return render(request,"rs/view_requests.html", context= data)
        
           
# #         queryset= rspc_inventory.objects.filter(project_investigator_id = request.user.username )
# #     else:
# #         render(request,"/404.html")

# #     data= {
# #         "requests": queryset,
# #         "username": request.user.username,
# #         "id":id,
# #     }

# #     # print(data)
# #     # print(request.user.username)
    
# #     return render(request,"rs/view_requests.html", context= data)

# def view_financial_outlay(request,pid):

#     table_data=financial_outlay.objects.filter(project_id=pid).order_by('category', 'sub_category')
#     project= projects.objects.get(project_id=pid)

#     years = set(table_data.values_list('year', flat=True))
    
#     category_data = {}
#     for category in table_data.values_list('category', flat=True).distinct():
#         category_data[category] = financial_outlay_serializer(table_data.filter(category=category) , many=True).data
#     # category_data =  category_serializer(category_data , many=True).data
    

#     data = {
#         'table_title': 'Total Budget Outlay',
#         'table_caption': '...',  # Add caption if needed
#         'project_name':project.project_name,
#         'years': list(years),
#         'category_data': category_data,
#     }

#     # print(data)
#     return JsonResponse(data , safe=False)

# # def submit_closure_report(request,id):
# #     id= int(id)
# #     obj= projects.objects.get(project_id=id)
# #     obj.status= 1; 
# #     obj.save()

# #     queryset= projects.objects.filter(project_investigator_id = request.user.username)

# #     # print(queryset)
    
# #     data= {
# #         "projects": queryset,
# #         "username": request.user.username
# #     }
# #     messages.success(request,"Closure report submitted successfully")
# #     return render(request,"rs/view_projects_rspc.html",context=data)
# @api_view(['GET'])
# def view_project_inventory(request,pj_id):
#     pj_id=int(pj_id)
#     queryset= (requests.objects.filter(project_id=pj_id,request_type="funds"))
#     queryset = requests_serializer(queryset , many=True).data
    
#     # print(queryset)
    
#     data= {
#         "requests": queryset,
#         "username": request.user.username
#     }
#     return JsonResponse(data , safe=True)

# def view_project_staff(request,pj_id):
#     pj_id=int(pj_id)
#     queryset= requests.objects.filter(project_id=pj_id,request_type="staff")
#     queryset = requests_serializer(queryset , many = True).data


#     # print(queryset)
    
#     data= {
#         "requests": queryset,
#         "username": request.user.username
#     }
#     return JsonResponse(data , safe = True)

# # def projectss(request):
# #     return render(request,"rs/projects.html")

# # def view_project_info(request,id):
# #     id= int(id)
# #     obj= projects.objects.get(project_id=id)



# #     data = {
# #         "project": obj,
# #     }
    
# #     return render(request,"rs/view_project_info.html", context= data)

# # def financial_outlay_form(request,pid):
# #     pid= int(pid)
# #     project= projects.objects.get(project_id=pid);
# #     categories = category.objects.all().distinct();

# #     categories_with_subcategories = category.objects.values('category_name', 'sub_category_name')

# #     # Organize the data into a dictionary
# #     category_subcategory_map = {}
# #     for item in categories_with_subcategories:
# #         category_name = item['category_name']
# #         subcategory = item['sub_category_name']
# #         if category_name in category_subcategory_map:
# #             category_subcategory_map[category_name].append(subcategory)
# #         else:
# #             category_subcategory_map[category_name] = [subcategory]

# #     # Pass the organized data to the template
    
# #     data = {
# #        "project_id": project.project_id,
# #        "project_name":project.project_name,
# #        "years": list(range(1, int(project.years) + 1)),
# #        "category_subcategory_map": category_subcategory_map
       
# #     }

# #     return render(request,"rs/add_financial_outlay.html", context= data)
# # # return render(request,"rs/add_financial_outlay.html", context= data)



# # def add_staff_details(request, pid):
# #     if request.method == 'POST':
# #         obj = request.POST
# #         for key, value in obj.items():
# #             if key.startswith('staff_id'):
# #                 year_count = key.split('-')[-2]
# #                 staff_count = key.split('-')[-1]
# #                 staff_id_key = f'staff_id-{year_count}-{staff_count}'
# #                 staff_name_key = f'staff_name-{year_count}-{staff_count}'
# #                 qualification_key = f'qualification-{year_count}-{staff_count}'
# #                 stipend_key = f'stipend-{year_count}-{staff_count}'
# #                 year = year_count
# #                 staff_id = obj.get(staff_id_key, '').strip()
# #                 staff_name = obj.get(staff_name_key, '').strip()
# #                 qualification = obj.get(qualification_key, '').strip()
# #                 stipend = obj.get(stipend_key, '').strip()
# #                 project_instance = projects.objects.get(project_id=pid)
# #                 # print(type(staff_id))
# #                 ob = staff_allocations.objects.all()

# #                 if len(ob) == 0:
# #                     fid = 1
# #                 else:
# #                     fid = ob[0].staff_allocation_id + 1

# #                 staff_id_instance = User.objects.get(username=staff_id)
         

# #                 staff_allocations.objects.create(
# #                     staff_allocation_id=fid,
# #                     project_id=project_instance,
# #                     staff_id=staff_id_instance,
# #                     staff_name=staff_name,
# #                     qualification=qualification,
# #                     year=year,
# #                     stipend=stipend
# #                 )

# #         return redirect("/research_procedures/view_staff_details/"+str(pid))

# #     project = projects.objects.get(project_id=pid)

# #     years_passed = int((datetime.datetime.now().date() - project.start_date).days / 365.25)

# #     data = {
# #         "project_id": project.project_id,
# #         "project_name" : project.project_name,
# #         "years": list(range(1, int(project.years) + 1)),
# #         "year": int(years_passed) + 1,
# #     }

# #     return render(request, "rs/add_staff_details.html", context=data)

# @api_view(['GET'])
# def view_staff_details(request, pid):
#     staff_records = staff_allocations.objects.filter(project_id=pid)
#     data_by_year = {}
#     project = projects.objects.get(project_id=pid)
#     # project = Project_serializer(project , many=True).data

#     for record in staff_records:
#         year = record.year
#         if year not in data_by_year:
#             data_by_year[year] = []
#         data_by_year[year].append({
#             'staff_id': int(record.staff_id.id),
#             'staff_name': record.staff_name,
#             'qualification': record.qualification,
#             'stipend': record.stipend
#         })

#     context = {
#         'data_by_year': data_by_year,
#         'project_name': project.project_name
#         # Add other necessary fields from project here
#     }

#     rspc_admin = HoldsDesignation.objects.get(designation__name="rspc_admin")

#     return JsonResponse(context, safe=True)


# # def add_financial_outlay(request,pid):
# #     if request.method == 'POST':
        
# #         project = projects.objects.get(project_id=pid)
# #         project.financial_outlay_status = 1
# #         project.save()
        
# #         obj = request.POST
# #         for key, value in obj.items():
# #             if key.startswith('category-select'):                
# #                 year_count = key.split('-')[-2]
# #                 category_count = key.split('-')[-1]
# #                 subcategory_key = f'subcategory-select-{year_count}-{category_count}'
# #                 amount_key = f'amount-{year_count}-{category_count}'

# #                 category = value
# #                 subcategory = obj.get(subcategory_key, [''])
# #                 amount = obj.get(amount_key, [''])
# #                 year = int(year_count)

# #                 # print(year)
# #                 # print(amount)
# #                 # print(subcategory)
# #                 # print(category)
# #                 project_instance=projects.objects.get(project_id=pid)
                

# #                 ob= financial_outlay.objects.all()
# #                 if len(ob)==0 :
# #                     fid=1
                
# #                 else :
# #                     fid= ob[0].financial_outlay_id+1
# #                 financial_outlay.objects.create(
# #                     financial_outlay_id=fid,
# #                     project_id=project_instance,
# #                     category=category,
# #                     sub_category=subcategory,
# #                     amount=amount,
# #                     year=year,
# #                     status=0,
# #                     staff_limit=0
# #                 )
    
                
# #     return redirect("/research_procedures/view_financial_outlay/"+str(pid))

# # def inbox(request):
    
    
# #     user_designation= getDesignation(request.user.username)
# #     print(user_designation)
# #     data = view_inbox(request.user.username,user_designation, "research_procedures")
# #     files= []
# #     count =0
# #     for i in data:
# #         count+=1
# #         file1= File.objects.get(id=i['id'])
# #         files.append((count, file1))


# #     data={
        
# #         "inbox": data,
# #         "files": files
# #     }
# #     # print(data)
# #     return render(request, "rs/inbox.html",context= data)

# # def add_staff_request(request,id):
# #     if request.method == 'POST':
# #         obj= request.POST
# #         projectid = int(id)
# #         receiver = obj.get('receiver')


# #         sender = request.user.username
# #         file_to_forward= request.FILES.get('file_to_forward')
# #         project_instance=projects.objects.get(project_id=projectid)
# #         receiver_instance=User.objects.get(username=receiver)
# #         sender_designation= HoldsDesignation.objects.get(user= request.user).designation
# #         receiver_designation = HoldsDesignation.objects.get(user= receiver_instance).designation

# #         file_x= create_file(
# #             uploader=sender,    
# #             uploader_designation=sender_designation,
# #             receiver= receiver_instance.username,
# #             receiver_designation=receiver_designation, 
# #             src_module="research_procedures",
# #             src_object_id= projectid,
# #             file_extra_JSON= { "message": "Staff request added ("+ str(projectid)+ ")"},
# #             attached_file= file_to_forward, 
# #         )
# #         messages.success(request,"Staff request added successfully")

# #     return redirect("/research_procedures/view_project_info/"+ str(projectid))

# # def view_request_inbox(request):
# #     user_designation= getDesignation(request.user.username)
# #     print(user_designation)
# #     data = view_inbox(request.user.username,user_designation, "research_procedures")
# #     files= []
# #     count =0
# #     for i in data:
# #         count+=1
# #         file1= File.objects.get(id=i['id'])
# #         files.append((count, file1))


# #     data={
        
# #         "inbox": data,
# #         "files": files
# #     }
# #     # print(data)
# #     # return render(request, "rs/view_request_inbox.html",context= data)
# #     return Response(data, status=status.HTTP_200_OK)


# # def forward_request(request):
# #     if request.method == 'POST':
# #         obj= request.POST
# #         fileid = int(obj.get('file_id'))
# #         receiver = obj.get('receiver')
# #         message= obj.get('message')
# #         receiver_instance= User.objects.get(username=receiver)
# #         receiver_designation= HoldsDesignation.objects.get(user=receiver_instance).designation
# #         sender = request.user.username
        
# #         filex= get_file_by_id(fileid)

# #         file2=create_file(
# #             uploader=sender,
# #             uploader_designation= getDesignation(sender),
# #             receiver= receiver,
# #             receiver_designation=receiver_designation, 
# #             src_module="research_procedures",
# #             src_object_id= filex.src_object_id,
# #             file_extra_JSON= { "message": message},
# #             attached_file= filex.upload_file, 
# #         )
        
# #         delete_file(fileid)
# #         messages.success(request,"Request forwarded successfully")
# #     return redirect("/research_procedures/view_request_inbox")


# #     return redirect("/research_procedures/view_request_inbox")

# # def getDesignation(us):
# #     user_inst = User.objects.get(username= us)
# #     user_designation= HoldsDesignation.objects.get(user= user_inst).designation
# #     return user_designation

# # def get_file_by_id(id):
# #     file1= File.objects.get(id=id)
# #     print(file1)
# #     return file1

# # def delete_file(id):
# #     file1= File.objects.get(id=id)
# #     tracking= Tracking.objects.get(file_id=file1)
# #     tracking.delete()
# #     file1.delete()
# #     return

# @csrf_exempt
@api_view(['POST'])
def create_expenditure(request):
    if request.method == 'POST':
        uploader_designation = request.query_params.get('u_d')
        receiver = request.query_params.get('r')
        receiver_designation = request.query_params.get('r_d')
        if not all([uploader_designation, receiver, receiver_designation]):
            return Response(
                {"Error": "Missing required query parameters."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            file_id = create_file(
                uploader=request.user.username,
                uploader_designation=uploader_designation,
                receiver=receiver,
                receiver_designation=receiver_designation,
                subject="New Expenditure Request Created",
                description=f"Expenditure request has been created for #{request.data['item']}.",
                src_module="RSPC",
                src_object_id="",
                file_extra_JSON={
                    "pid": request.data['pid'],
                    "request_type": "Expenditure",
                    "cost": request.data['cost'],
                    "approval": request.data.get('approval'),
                    "exptype": request.data['exptype'],
                    "lastdate": request.data['lastdate'],
                    "inventory": request.data.get('inventory'),
                    "desc": request.data.get('desc'),
                    "mode": request.data['mode'],
                    "receiver": receiver,
                    "tracker heading": f"Expenditure Request For {request.data['item']}",
                },
                attached_file=request.FILES.get('file', None)
            )
            print(f"File created successfully with ID: {file_id}")
        except Exception as e:
            print(f"Failed to create file: {e}")
            return Response({"Error": "Failed to create file"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            expenditure_data = request.data.copy()
            expenditure_data['file_id'] = file_id
            serializer = expenditure_serializer(data=expenditure_data)
            if serializer.is_valid():
                expenditure_instance=serializer.save()
                print(f"Expenditure created with ID: {expenditure_instance.id}")
            else:
                print("Expenditure Serializer Errors:", serializer.errors)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Error creating expenditure: {e}")
            return Response({"Error": "Failed to create expenditure"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            file_instance = File.objects.get(id=file_id)
            file_instance.src_object_id = str(expenditure_instance.id)
            file_instance.save()
            sender_notif = User.objects.get(username=request.user.username)
            recipient_notif = User.objects.get(username=receiver)
            RSPC_notif(sender=sender_notif, recipient=recipient_notif, type="Processing")
            print(f"File updated with src_object_id or failed to find user for notifications: {expenditure_instance.id}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            print(f"Failed to update file with src_object_id: {e}")
            return Response({"Error": "Failed to update file with src_object_id"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def create_staff(request):
     if request.method == 'POST':
        uploader_designation = request.query_params.get('u_d')
        receiver = request.query_params.get('r')
        receiver_designation = request.query_params.get('r_d')
        if not all([uploader_designation, receiver, receiver_designation]):
            return Response(
                {"Error": "Missing required query parameters."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            file_id = create_file(
                uploader=request.user.username,
                uploader_designation=uploader_designation,
                receiver=receiver,
                receiver_designation=receiver_designation,
                subject="New Staff Request Created",
                description=f"Staff request has been created for #{request.data['person']}.",
                src_module="RSPC",
                src_object_id="",
                file_extra_JSON={
                    "pid": request.data['pid'],
                    "request_type": "Staff",
                    "stipend": request.data['stipend'],
                    "approval": request.data.get('approval'),
                    "qualification": request.data['qualification'],
                    "designation": request.data['designation'],
                    "lastdate": request.data['lastdate'],
                    "startdate": request.data['startdate'],
                    "uname": request.data.get('uname'),
                    "desc": request.data.get('desc'),
                    "dept": request.data['dept'],
                    "receiver": receiver,
                    "tracker heading": f"Staff Request For {request.data['person']}",
                },
                attached_file=request.FILES.get('file', None)
            )
            print(f"File created successfully with ID: {file_id}")
        except Exception as e:
            print(f"Failed to create file: {e}")
            return Response({"Error": "Failed to create file"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            staff_data = request.data.copy()
            staff_data['file_id'] = file_id
            serializer = staff_serializer(data=staff_data)
            if serializer.is_valid():
                staff_instance=serializer.save()
                print(f"Staff created with ID: {staff_instance.id}")
            else:
                print("Staff Serializer Errors:", serializer.errors)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Error creating staff: {e}")
            return Response({"Error": "Failed to create staff"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            file_instance = File.objects.get(id=file_id)
            file_instance.src_object_id = str(staff_instance.id)
            file_instance.save()
            sender_notif = User.objects.get(username=request.user.username)
            recipient_notif = User.objects.get(username=receiver)
            RSPC_notif(sender=sender_notif, recipient=recipient_notif, type="Processing")
            print(f"File updated with src_object_id: {staff_instance.id}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            print(f"Failed to update file with src_object_id or failed to find user for notifications: {e}")
            return Response({"Error": "Failed to update file with src_object_id"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def designation_user(designation):
    designation_id = Designation.objects.filter(name=designation).values_list('id', flat=True).first()
    if not designation_id:
        return None
    user_id = HoldsDesignation.objects.filter(designation=designation_id).values_list('working', flat=True).first()
    if not user_id:
        return None
    return User.objects.filter(id=user_id).first()

@api_view(['POST'])
def staff_document_upload(request):
    if request.method == 'POST':
        sid = request.data.get("sid")
        try:
            staff_instance = staff.objects.get(sid=sid)
            for file_field in ["joining_report", "id_card"]:
                if file_field in request.FILES:
                    setattr(staff_instance, file_field, request.FILES[file_field])
            staff_instance.salary_per_month = request.data.get("salary_per_month")
            staff_instance.start_date = request.data.get("start_date")
            staff_instance.doc_approval = "Pending"
            RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=designation_user(designation="SectionHead_RSPC"), type="Doc Created")
            staff_instance.save()
            return Response(staff_serializer(staff_instance).data, status=status.HTTP_200_OK)
        except staff.DoesNotExist:
            return Response({"Error": "Staff not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def staff_selection_report(request):
    if request.method == 'POST':
        sid = request.data.get("sid")
        try:
            staff_instance = staff.objects.get(sid=sid)
            required_fields = ["candidates_applied", "candidates_called", "candidates_interviewed"]
            if not all(request.data.get(field) for field in required_fields):
                return Response({"Error": "Missing required candidate numbers"}, status=status.HTTP_400_BAD_REQUEST)
        
            final_selection = json.loads(request.data.get("final_selection", "[]"))
            waiting_list = json.loads(request.data.get("waiting_list", "[]"))
            biodata_final = request.FILES.getlist("biodata_final")
            biodata_waiting = request.FILES.getlist("biodata_waiting")
            if (len(biodata_final) != len(final_selection) or len(biodata_waiting) != len(waiting_list)):
                return Response({"Error": "Mismatch between candidate list and resume files"}, status=status.HTTP_400_BAD_REQUEST)

            for field in required_fields:
                setattr(staff_instance, field, request.data.get(field))
            for file_field in ["ad_file", "comparative_file"]:
                if file_field in request.FILES:
                    setattr(staff_instance, file_field, request.FILES[file_field])
            staff_instance.approval = "Committee Approval"
            staff_instance.final_selection = final_selection
            staff_instance.waiting_list = waiting_list
            staff_instance.biodata_final = [
                f"{settings.MEDIA_URL}{default_storage.save(f'RSPC/biodatas/{file.name}', ContentFile(file.read()))}"
                for file in biodata_final
            ]
            staff_instance.biodata_waiting = [
                f"{settings.MEDIA_URL}{default_storage.save(f'RSPC/biodatas/{file.name}', ContentFile(file.read()))}"
                for file in biodata_waiting
            ]

            staff_instance.save()
            for role, members in staff_instance.selection_committee.items():
                if isinstance(members, list):
                    for name in members:
                        recipient = User.objects.filter(username=name).first()
                        if recipient:
                            RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=recipient, type="Report Created")
                else:
                    recipient = User.objects.filter(username=members).first()
                    if recipient:
                        RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=recipient, type="Report Created")
            return Response(staff_serializer(staff_instance).data, status=status.HTTP_200_OK)
        except staff.DoesNotExist:
            return Response({"Error": "Staff not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def committee_action(request):
    if request.method == 'POST':
        sid = request.data.get("sid")
        action = request.data.get("action")
        username = request.user.username
        if not sid or not action:
            return Response({"Error": "Missing staff ID or action"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            staff_instance = staff.objects.get(sid=sid)
            if action == "approve":
                if username not in staff_instance.gave_verdict:
                    staff_instance.gave_verdict.append(username)
                committee_members = set()
                for key, members in staff_instance.selection_committee.items():
                    if key == "Co-PI":
                        if isinstance(members, list):
                            for copi in members:
                                if project_access.objects.filter(pid=staff_instance.pid_id, copi_id=copi, type="Internal").exists():
                                    committee_members.add(copi)
                        else:
                            if project_access.objects.filter(pid=staff_instance.pid_id, copi_id=members, type="Internal").exists():
                                committee_members.add(members)
                    else:
                        if isinstance(members, list):
                            committee_members.update(members)
                        else:
                            committee_members.add(members)
                if committee_members.issubset(set(staff_instance.gave_verdict)):
                    staff_instance.approval = "HoD Forward"
                    RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=designation_user(f"HOD ({projects.objects.filter(pid=staff_instance.pid_id).first().dept})"), type="Committee Complete")
                RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=User.objects.filter(username=projects.objects.filter(pid=staff_instance.pid_id).first().pi_id).first(), type="Committee Approved")
            
            elif action == "reject":
                if staff_instance.biodata_final:
                    for file_path in staff_instance.biodata_final:
                        default_storage.delete(file_path)  # Delete stored files
                if staff_instance.biodata_waiting:
                    for file_path in staff_instance.biodata_waiting:
                        default_storage.delete(file_path)
                if staff_instance.ad_file:
                    default_storage.delete(staff_instance.ad_file.path)
                if staff_instance.comparative_file:
                    default_storage.delete(staff_instance.comparative_file.path)
                staff_instance.candidates_applied = None
                staff_instance.candidates_called = None
                staff_instance.candidates_interviewed = None
                staff_instance.final_selection = []
                staff_instance.waiting_list = []
                staff_instance.biodata_final = []
                staff_instance.gave_verdict = []
                staff_instance.biodata_waiting = []
                staff_instance.approval = "Hiring"
                RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=User.objects.filter(username=projects.objects.filter(pid=staff_instance.pid_id).first().pi_id).first(), type="Report Rejected")

            staff_instance.save()
            return Response({"message": "Verdict recorded. Selection report will be approved once all committee members have voted."}, status=status.HTTP_200_OK)
        except staff.DoesNotExist:
            return Response({"Error": "Staff not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def get_budget(request):
    pid = request.GET.get('pid') 
    if pid is not None:
        details = budget.objects.filter(pid=pid).first()
        if details:
            response_data = {
                    "manpower": details.manpower,
                    "travel": details.travel,
                    "contingency": details.contingency,
                    "consumables": details.consumables,
                    "equipments": details.equipments,
                    "overhead": details.overhead,
                    "current_funds": details.current_funds
                }
            return Response(response_data, status=status.HTTP_200_OK)
        return Response({}, status=status.HTTP_200_OK)
    else:
        return Response({"Error": "pid is required"}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET'])
def get_staff_positions(request):
    pid = request.GET.get('pid') 
    if pid is not None:
        details = staff_positions.objects.filter(pid=pid).first()
        if details:
            response_data = {
                "positions": details.positions,
                "incumbents": details.incumbents
            }
            return Response(response_data, status=status.HTTP_200_OK)
        return Response({}, status=status.HTTP_200_OK)
    else:
        return Response({"Error": "pid is required"}, status=status.HTTP_400_BAD_REQUEST)

def create_staff_positions(pid, positions_data):
    positions = {}
    incumbents = {}
    try:
        project_instance = projects.objects.get(pid=pid)  # Get the project instance
    except projects.DoesNotExist:
        raise ValueError(f"Project with pid {pid} does not exist.")
    for pos in positions_data:
        type_name = pos.get("type")
        available_count = int(pos.get("available") or 0)
        occupied_count = int(pos.get("occupied") or 0)
        positions[type_name] = [available_count, occupied_count]
        incumbents[type_name] = pos.get("incumbents", [])
    staff_positions_data = {
        "pid": project_instance,
        "positions": positions,
        "incumbents": incumbents,
    }

    staff_position, created = staff_positions.objects.update_or_create(
        pid=project_instance, defaults=staff_positions_data
    )
    staff_positions_data["pid"]=pid
    serializer = staff_positions_serializer(instance=staff_position, data=staff_positions_data)
    if serializer.is_valid():
        serializer.save()
    else:
        print("Staff Positions Serializer Errors:", serializer.errors)
        raise ValueError(serializer.errors)

# def create_staff_file(request, ad, selection_committee):
#     try:
#         uploader_designation = request.query_params.get('u_d')
#         receiver = request.query_params.get('r')
#         receiver_designation = request.query_params.get('r_d')
#         if not all([uploader_designation, receiver, receiver_designation]):
#             raise ValueError("Missing required query parameters.")

#         file_id = create_file(
#             uploader=request.user.username,
#             uploader_designation=uploader_designation,
#             receiver=receiver,
#             receiver_designation=receiver_designation,
#             subject="New Staff Request",
#             description=f"Staff request created for {ad.get('type')}.",
#             src_module="RSPC",
#             src_object_id="",
#         )
#         print(f"File created successfully with ID: {file_id}")
#         return file_id
#     except Exception as e:
#         print(f"Failed to create file: {e}")
#         raise ValueError("Failed to create file")
    
@api_view(['POST'])
def add_ad_committee(request):
    if request.method == 'POST':
        data=request.data.copy()
        positions_data = json.loads(data.pop('positions', [''])[0])
        advertisements_data = json.loads(data.pop("advertisements", [''])[0])

        members_data = json.loads(data.pop("members", [''])[0])
        selection_committee = {}
        for member in members_data:
            role = member.get("role")
            name = member.get("name")
            recipient = User.objects.filter(username=name).first()
            if recipient:
                RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=recipient, type="Selection Committee")
            if role in selection_committee:
                if isinstance(selection_committee[role], list):
                    selection_committee[role].append(name)
                else:
                    selection_committee[role] = [selection_committee[role], name]
            else:
                selection_committee[role] = name
        try:
            create_staff_positions(int(data.get("pid")), positions_data)
        except ValueError as e:
            return Response({"Error": f"Failed in adding staff positions - {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        for ad in advertisements_data:
            staff_data = {
                "pid": int(data.get("pid")),
                "type": ad.get("type", ""),
                "duration": int(ad.get("duration")),
                "salary": float(ad.get("salary")),
                "eligibility": ad.get("eligibility", ""),
                "has_funds": data.get("has_funds"),
                "submission_date": ad.get("submission_date"),
                "interview_date": ad.get("interview_date"),
                "test_date": ad.get("test_date"),
                "test_mode": ad.get("test_mode"),
                "interview_place": ad.get("interview_place"),
                "approval": "HoD Forward",
                "selection_committee": selection_committee,  # Store members in selection_committee JSON field
            }
            serializer = staff_serializer(data=staff_data)

            if serializer.is_valid():
                staff_instance = serializer.save()
                if request.FILES.get('post_on_website'):
                    staff_instance.post_on_website = request.FILES.get('post_on_website')
                    staff_instance.save()
                RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=designation_user(f"HOD ({projects.objects.filter(pid=staff_data['pid']).first().dept})"), type="Ad Created")
        return Response({"message":"Data added successfully"}, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def staff_decision(request):
    if request.method == 'POST':
        sid = request.data.get("sid")
        action = request.data.get("action")
        form = request.data.get("form")
        if not sid or not action:
            return Response({"Error": "Missing staff ID or action"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            staff_instance = staff.objects.get(sid=sid)
            if action == "forward":
                staff_instance.approval = "RSPC Approval"
                staff_instance.current_approver = "rspc_admin"
                staff_instance.save()
                type = "Ad Forwarded" if form == "ad" else "Report Forwarded"
                RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=designation_user(designation="rspc_admin"), type=type)

            elif action == "approve":
                if form == "ad":
                    if staff_instance.current_approver == "rspc_admin":
                        staff_instance.current_approver = "SectionHead_RSPC"
                        staff_instance.save()
                        RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=designation_user(designation="SectionHead_RSPC"), type="Ad Forwarded")
                    else:
                        staff_instance.approval = "Hiring"
                        staff_instance.current_approver = None
                        staff_instance.save()
                        RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=User.objects.filter(username=projects.objects.filter(pid=staff_instance.pid_id).first().pi_id).first(), type="Hiring")
                elif form == "doc":
                    staff_instance.doc_approval = "Approved"
                    staff_instance.save()
                    RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=User.objects.filter(username=projects.objects.filter(pid=staff_instance.pid_id).first().pi_id).first(), type="Doc Approved")
                elif form == "report":
                    if staff_instance.current_approver == "rspc_admin":
                        staff_instance.current_approver = "SectionHead_RSPC"
                        staff_instance.save()
                        RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=designation_user(designation="SectionHead_RSPC"), type="Report Forwarded")
                    else:
                        staff_instance.approval = "Approved"
                        staff_instance.current_approver = None
                        staff_instance.save()
                        final_selections = staff_instance.final_selection
                        for index, candidate in enumerate(final_selections):
                            name, salary, duration, begin, end = (
                                candidate.get("name"),
                                candidate.get("salary"),
                                candidate.get("duration"),
                                candidate.get("begin"),
                                candidate.get("end"),
                            )
                            if index == 0:
                                staff_instance.person = name
                                staff_instance.salary = salary
                                staff_instance.duration = duration
                                staff_instance.start_date = begin
                                staff_instance.biodata_number = index
                                staff_instance.save()
                            else:
                                final_staff_data = staff_instance.__dict__.copy()
                                final_staff_data.pop("_state")
                                final_staff_data.pop("sid")
                                final_staff_data.update({
                                    "person": name,
                                    "salary": salary,
                                    "duration": duration,
                                    "start_date": begin,
                                    "biodata_number": index,
                                })
                                new_staff_instance = staff.objects.create(**final_staff_data)
                                new_staff_instance.save()
                    
                        staff_pos_instance = staff_positions.objects.filter(pid=staff_instance.pid).first()
                        positions = staff_pos_instance.positions or {}
                        incumbents = staff_pos_instance.incumbents or {}
                        staff_type = staff_instance.type
                        if staff_type in positions:
                            positions[staff_type][1] += len(final_selections)
                        else:
                            positions[staff_type] = [0, len(final_selections)]
                        new_incumbents = [{"name": candidate.get("name"), "date": candidate.get("end")} for candidate in final_selections]
                        if staff_type in incumbents:
                            incumbents[staff_type].extend(new_incumbents)
                        else:
                            incumbents[staff_type] = new_incumbents
                        staff_pos_instance.positions = positions
                        staff_pos_instance.incumbents = incumbents
                        staff_pos_instance.save()
                        RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=User.objects.filter(username=projects.objects.filter(pid=staff_instance.pid_id).first().pi_id).first(), type="Approved")

            elif action == "reject":
                type=""
                if form == "ad":
                    if staff_instance.post_on_website:
                        default_storage.delete(staff_instance.post_on_website.path)
                    staff_instance.delete()
                    type="Ad Rejected"
                elif form == "doc":
                    if staff_instance.joining_report:
                        default_storage.delete(staff_instance.joining_report.path)
                    if staff_instance.id_card:
                        default_storage.delete(staff_instance.id_card.path)
                    staff_instance.doc_approval=None
                    staff_instance.salary_per_month=0
                    staff_instance.save()
                    type="Doc Rejected"
                elif form == "report":
                    if staff_instance.biodata_final:
                        for file_path in staff_instance.biodata_final:
                            default_storage.delete(file_path)  # Delete stored files
                    if staff_instance.biodata_waiting:
                        for file_path in staff_instance.biodata_waiting:
                            default_storage.delete(file_path)
                    if staff_instance.ad_file:
                        default_storage.delete(staff_instance.ad_file.path)
                    if staff_instance.comparative_file:
                        default_storage.delete(staff_instance.comparative_file.path)
                    staff_instance.candidates_applied = None
                    staff_instance.candidates_called = None
                    staff_instance.candidates_interviewed = None
                    staff_instance.final_selection = []
                    staff_instance.waiting_list = []
                    staff_instance.biodata_final = []
                    staff_instance.gave_verdict = []
                    staff_instance.biodata_waiting = []
                    staff_instance.approval = "Hiring"
                    staff_instance.save()
                    type="Report Rejected"
                RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=User.objects.filter(username=projects.objects.filter(pid=staff_instance.pid_id).first().pi_id).first(), type=type)

            return Response({"message": "Action successful"}, status=status.HTTP_200_OK)
        except staff.DoesNotExist:
            return Response({"Error": "Staff not found"}, status=status.HTTP_404_NOT_FOUND)

def get_copis(pid):
    if pid is not None:
        return list(project_access.objects.filter(pid=pid).values_list('copi_id', flat=True))
    return []

def create_budget(pid, budget_data, overhead):
    parsed_budget = {
        "pid": pid, 
        "manpower": [int(year["manpower"]) if year["manpower"] else 0 for year in budget_data],
        "travel": [int(year["travel"]) if year["travel"] else 0 for year in budget_data],
        "contingency": [int(year["contingency"]) if year["contingency"] else 0 for year in budget_data],
        "consumables": [int(year["consumables"]) if year["consumables"] else 0 for year in budget_data],
        "equipments": [int(year["equipments"]) if year["equipments"] else 0 for year in budget_data],
        "overhead": int(overhead) if overhead else 0
    }
    serializer = budget_serializer(data=parsed_budget)
    if serializer.is_valid():
        serializer.save()
    else:
        print("Budget Serializer Errors:", serializer.errors)
        raise ValueError(serializer.errors)

def create_copis(pid, coPIs_data, sender_username):
     for copi in coPIs_data:
        copi["pid"] = pid
        serializer = project_access_serializer(data=copi)
        if serializer.is_valid():
            if(copi["type"]=="Internal"):
                RSPC_notif(sender=User.objects.filter(username=sender_username).first(), recipient=User.objects.filter(username=copi["copi_id"]).first(), type="Co-PI")
            serializer.save()
        else:
            print("Co-PIs Serializer Errors:", serializer.errors)
            raise ValueError(serializer.errors)

@api_view(['POST'])
def add_project(request):
    if request.method == 'POST':
        data=request.data.copy()
        budget_data = json.loads(data.pop('budget', [''])[0])
        coPIs_data = json.loads(data.pop('coPIs', [''])[0])
        overhead = data.pop('overhead', ['0'])[0]

        pi = User.objects.filter(username=data["pi_id"]).first()
        pi_name = f"{pi.first_name} {pi.last_name}"
        data["pi_name"] = pi_name
        serializer = projects_serializer(data=data)
        
        if serializer.is_valid():
            new_project=serializer.save()
            try:
                create_budget(new_project.pid, budget_data, overhead)
                create_copis(new_project.pid, coPIs_data, request.user.username)
            except ValueError as e:
                new_project.delete()
                return Response({"Error": f"Failed in adding CoPIs or Budget - {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
            
            RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=designation_user(designation=f"HOD ({data['dept']})"), type="Proposal Created")
            return Response(serializer.data, status=status.HTTP_201_CREATED)      
        print("Project Serializer Errors:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def register_commence_project(request):
    if request.method == 'POST':
        pid = request.POST.get("pid")
        if pid is not None:
            try:
                project_instance = projects.objects.get(pid=pid)
                updatable_fields = ["name", "type", "access", "sponsored_agency", "sanction_date", "sanctioned_amount", "status"] if "sanction_date" in request.POST else ["start_date", "initial_amount", "status"]
                for field in updatable_fields:
                    value = request.POST.get(field)
                    setattr(project_instance, field, value)
                if request.FILES.get('file'):
                    project_instance.file=request.FILES.get('file')
                if request.FILES.get('registration_form'):
                    project_instance.registration_form=request.FILES.get('registration_form')
                if "initial_amount" in request.POST:
                    budget_instance = budget.objects.filter(pid=pid).first()
                    if budget_instance:
                        budget_instance.current_funds = request.POST.get("initial_amount")
                        budget_instance.save()
                project_instance.save()
                
                if "sanction_date" in request.POST:
                    RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=designation_user(designation=f"HOD ({project_instance.dept})"), type="Registration Created")
                else:
                    RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=User.objects.filter(username=project_instance.pi_id).first(), type="Project Commenced")
                return Response({"message": "Project Details Updated Successfully"}, status=status.HTTP_200_OK)
            except projects.DoesNotExist:
                return Response({"Error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({"Error": f"Failed to update project details - {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({"Error": "pid is required"}, status=status.HTTP_400_BAD_REQUEST)    

@api_view(['POST'])
def project_closure(request):
    if request.method == 'POST':
        pid = request.data.get('pid')
        if pid is not None:
            try:
                project_instance = projects.objects.get(pid=pid)
                project_instance.end_report=request.FILES.get('end_report', None)
                project_instance.end_approval="Pending"
                project_instance.save()
                RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=designation_user(designation="SectionHead_RSPC"), type="UC/SE Created")
                return Response({"message": "Project Closure Successful"}, status=status.HTTP_200_OK)
            except projects.DoesNotExist:
                return Response({"Error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({"Error": f"Failed to close project: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({"Error": "pid is required"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def project_decision(request):
    if request.method == 'POST':
        pid = request.data.get("pid")
        action = request.data.get("action")
        form = request.data.get("form")
        if not pid or not action:
            return Response({"Error": "Missing project ID or action"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            project_instance = projects.objects.get(pid=pid)
            if action == "forward":
                project_instance.status = "RSPC Approval"
                project_instance.save()
                type = "Proposal Forwarded" if form == "proposal" else "Registration Forwarded"
                RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=designation_user(designation="SectionHead_RSPC"), type=type)

            elif action == "approve":
                if form == "proposal":
                    project_instance.status = "Submitted"
                elif form == "registration":
                    project_instance.status = "Registered"
                elif form == "uc/se":
                    project_instance.status = "Completed"
                    project_instance.end_approval="Approved"
                project_instance.save()
                RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=User.objects.filter(username=project_instance.pi_id).first(), type=project_instance.status)

            elif action == "reject":
                type=""
                if form == "proposal":
                    project_instance.delete()
                    type="Proposal Rejected"
                elif form == "registration":
                    if project_instance.file:
                        default_storage.delete(project_instance.file.path)
                    project_instance.sanctioned_amount = 0
                    project_instance.sanction_date = None
                    project_instance.status = "Submitted"
                    project_instance.save()
                    type="Registration Rejected"
                elif form == "uc/se":
                    if project_instance.end_report:
                        default_storage.delete(project_instance.end_report.path)
                    project_instance.end_approval = None
                    project_instance.save()
                    type="UC/SE Rejected"
                RSPC_notif(sender=User.objects.filter(username=request.user.username).first(), recipient=User.objects.filter(username=project_instance.pi_id).first(), type=type)

            return Response({"message": "Action successful"}, status=status.HTTP_200_OK)
        except projects.DoesNotExist:
            return Response({"Error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def get_projects(request):
    pid_list = request.GET.getlist('pids[]')  # Fetching multiple PIDs from query parameters
    all_projects = projects.objects.filter(pid__in=pid_list) if pid_list else projects.objects.all()
    serializer = projects_serializer(all_projects, many=True)
    project_data = serializer.data
    for project in project_data:
        project["copis"] = get_copis(project["pid"])
    return Response(project_data, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_PIDs(request):
    pi_id=request.user.username
    role = request.GET.get('role')
    if pi_id is not None and "Professor" in role:
        PIDs = projects.objects.filter(pi_id=pi_id).values_list('pid', flat=True)
        return Response(PIDs, status=status.HTTP_200_OK)
    elif pi_id is not None and "HOD" in role:
        dept = role.split("(")[-1].strip(")")
        PIDs = projects.objects.filter(dept=dept).values_list('pid', flat=True)
        return Response(PIDs, status=status.HTTP_200_OK)
    elif pi_id is not None and role in {"rspc_admin", "SectionHead_RSPC"}:
        PIDs = projects.objects.values_list('pid', flat=True)
        return Response(PIDs, status=status.HTTP_200_OK)
    else:
        return Response({"Error": "pi_id is required"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_staff(request):
    role = request.GET.get('role')
    if role is not None and "Professor" in role:
        pid_list = request.GET.getlist('pids[]')
        mem_id=request.user.username
        all_staff = staff.objects.filter(pid__in=pid_list)
        all_project = projects.objects.filter(pid__in=pid_list).values('pid', 'name', 'sponsored_agency', 'duration', 'pi_name', 'start_date')
        project_dict = {proj['pid']: proj for proj in all_project}
        serializer = staff_serializer(all_staff, many=True)
        staff_data = serializer.data
        for entry in staff_data:
            pid = entry["pid"]
            project = project_dict.get(pid, {})
            entry["project_title"] = project.get("name", "")
            entry["sponsor_agency"] = project.get("sponsored_agency", "")
            entry["pi_name"] = project.get("pi_name", "")
            entry["duration_project"] = project.get("duration", "")
            entry["project_start_date"] = project.get("start_date", "")

        additional_staff = staff.objects.filter(
            Q(approval="Committee Approval") &
            ~Q(gave_verdict__icontains=mem_id) &
            (Q(selection_committee__icontains=f'"{mem_id}"') | Q(selection_committee__icontains=f"'{mem_id}'"))
        )
        additional_pids = additional_staff.values_list('pid', flat=True).distinct()
        additional_projects = projects.objects.filter(pid__in=additional_pids).values('pid', 'name', 'sponsored_agency', 'duration', 'start_date')
        additional_project_dict = {proj['pid']: proj for proj in additional_projects}
        additional_serializer = staff_serializer(additional_staff, many=True)
        additional_staff_data = additional_serializer.data
        for entry in additional_staff_data:
            pid = entry["pid"]
            project = additional_project_dict.get(pid, {})
            entry["project_title"] = project.get("name", "")
            entry["sponsor_agency"] = project.get("sponsored_agency", "")
            entry["duration_project"] = project.get("duration", "")
            entry["project_start_date"] = project.get("start_date", "")
        staff_data.extend(additional_staff_data)
        return Response(staff_data, status=status.HTTP_200_OK)
    
    elif role is not None and "HOD" in role:
        pid_list = request.GET.getlist('pids[]')
        mem_id=request.user.username
        all_staff = staff.objects.filter(pid__in=pid_list)
        all_project = projects.objects.filter(pid__in=pid_list).values('pid', 'name', 'sponsored_agency', 'duration', 'pi_name', 'sanction_date', 'start_date')
        project_dict = {proj['pid']: proj for proj in all_project}
        serializer = staff_serializer(all_staff, many=True)
        staff_data = serializer.data
        for entry in staff_data:
            pid = entry["pid"]
            project = project_dict.get(pid, {})
            entry["project_title"] = project.get("name", "")
            entry["sponsor_agency"] = project.get("sponsored_agency", "")
            entry["sanction_date"] = project.get("sanction_date", "")
            entry["project_start_date"] = project.get("start_date", "")
            entry["pi_name"] = project.get("pi_name", "")
            entry["duration_project"] = project.get("duration", "")
        return Response(staff_data, status=status.HTTP_200_OK)
    
    elif role is not None and role in {"rspc_admin", "SectionHead_RSPC"}:
        all_staff = staff.objects.all()
        # all_staff = staff.objects.filter(approval="Submitted")
        staff_pids = all_staff.values_list('pid', flat=True)
        all_project = projects.objects.filter(pid__in=staff_pids).values('pid', 'name', 'sponsored_agency', 'duration', 'pi_name', 'sanction_date', 'start_date')
        project_dict = {proj['pid']: proj for proj in all_project}
        serializer = staff_serializer(all_staff, many=True)
        staff_data = serializer.data
        for entry in staff_data:
            pid = entry["pid"]
            project = project_dict.get(pid, {})
            entry["project_title"] = project.get("name", "")
            entry["sponsor_agency"] = project.get("sponsored_agency", "")
            entry["sanction_date"] = project.get("sanction_date", "")
            entry["project_start_date"] = project.get("start_date", "")
            entry["pi_name"] = project.get("pi_name", "")
            entry["duration_project"] = project.get("duration", "")
        return Response(staff_data, status=status.HTTP_200_OK)
    return Response({"Error": "Role is required"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_profIDs(request):
    faculty_entries = Faculty.objects.all()
    prof_ids = [faculty.id.user.username for faculty in faculty_entries]  # Assuming ExtraInfo has a user field
    return Response({"profIDs": prof_ids}, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_user(request):
    user=request.user
    username=request.user.username
    resp={
        'username': username,
    }
    return Response(data=resp,status=status.HTTP_200_OK)

@api_view(['GET'])
def get_expenditure(request):
    pid = request.GET.get('pid')  
    if pid is not None:
        expenditures = expenditure.objects.filter(pid=pid)  
        serializer = expenditure_serializer(expenditures, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response({"Error": "pid is required"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_inbox(request):
    username = request.GET.get('username')
    designation=request.GET.get('designation')
    if username and designation:
        try:
            inboxData = view_inbox(username=username, designation=designation, src_module="RSPC")
            finalInbox=[]
            for file in inboxData:
                file_id = file.get('id')
                try:
                    owner = get_current_file_owner(file_id=file_id)
                    if owner.username == username:
                        sender=get_last_file_sender(file_id=file_id)
                        sender_designation=get_last_file_sender_designation(file_id=file_id)
                        data = {
                        "fileData": file,
                        "sender": sender.username,
                        "sender_designation": sender_designation.name,
                        }
                        finalInbox.append(data)
                except Exception as e:
                    return Response({"Error": f"Failed to retrieve file owner: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response(finalInbox, status=status.HTTP_200_OK)
        except Exception as e:
            print("Exception occurred:", str(e))
            return Response({"Error": f"Failed to retrieve file data: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response({"Error": "Username and Designation is required"}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET'])
def get_processed(request):
    username = request.GET.get('username')
    designation=request.GET.get('designation')
    if username and designation:
        try:
            outboxData = view_outbox(username=username, designation=designation, src_module="RSPC")
            archivedData = view_archived(username=username, designation=designation, src_module="RSPC")
            processedData=outboxData+archivedData
            return Response(processedData, status=status.HTTP_200_OK)
        except Exception as e:
            print("Exception occurred:", str(e))
            return Response({"Error": f"Failed to retrieve file data: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response({"Error": "Username and Designation is required"}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET'])
def get_file(request):
    file_id = request.GET.get('file_id') 
    if file_id is not None:
        try:
            fileData = view_file(file_id=file_id)
            return Response(fileData, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"Error": f"Failed to retrieve file data: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response({"Error": "file_id is required"}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET'])
def get_history(request):
    file_id = request.GET.get('file_id') 
    if file_id is not None:
        try:
            historyData = view_history(file_id=file_id)
            file_instance = File.objects.get(id=file_id)
            approval = file_instance.file_extra_JSON.get('approval') if file_instance.file_extra_JSON else "Pending"
            response_data = {
                "historyData": historyData,
                "approval": approval
            }
            return Response(response_data, status=status.HTTP_200_OK) 
        except Exception as e:
            return Response({"Error": f"Failed to retrieve file tracking history: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response({"Error": "file_id is required"}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['POST'])
def forwarding_file(request):
    if request.method == 'POST':
        file_id = request.data.get('file_id')
        receiver = request.data.get('receiver')
        receiver_designation = request.data.get('receiver_designation')
        remarks = request.data.get('remarks')
        tracking_extra_JSON = {"receiver":receiver}

        if not file_id or not receiver or not receiver_designation:
            return Response(
                {"Error": "Missing required fields"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            file_instance = File.objects.get(id=file_id)
            uploader = file_instance.uploader.user
            result = forward_file(
                file_id=int(file_id),
                receiver=receiver,
                receiver_designation=receiver_designation,
                file_extra_JSON=tracking_extra_JSON,
                remarks=remarks,
            )
            sender_notif = User.objects.get(username=request.user.username)
            recipient_notif = User.objects.get(username=receiver)
            uploader_notif=User.objects.get(username=uploader)
            RSPC_notif(sender=sender_notif, recipient=recipient_notif, type="Processing")
            RSPC_notif(sender=recipient_notif, recipient=uploader_notif, type="Forwarding")
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            print("Exception occurred:", str(e))
            return Response({"Error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def reject_file(request):
    file_id = request.GET.get('file_id') 
    if file_id is not None:
        try:
            file_instance = File.objects.get(id=file_id)
            uploader = file_instance.uploader.user
            if file_instance.file_extra_JSON is not None:
                file_instance.file_extra_JSON['approval'] = "Rejected"
                file_instance.save()
                request_instance=None
                if file_instance.file_extra_JSON['request_type'] == 'Expenditure':
                    request_instance=expenditure.objects.get(file_id=file_id)
                else:
                    request_instance=staff.objects.get(file_id=file_id)
                if request_instance is not None:
                    request_instance.approval = "Rejected"
                    request_instance.save()
            archive_file(file_id=file_id)
            sender_notif = User.objects.get(username=request.user.username)
            recipient_notif = User.objects.get(username=uploader)
            RSPC_notif(sender=sender_notif, recipient=recipient_notif, type="Rejected")
            return Response({"message": "File Rejected Successfully"}, status=status.HTTP_200_OK)
        except File.DoesNotExist:
            return Response({"Error": "File not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"Error": f"Failed to reject file: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response({"Error": "file_id is required"}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET'])
def approve_file(request):
    file_id = request.GET.get('file_id') 
    if file_id is not None:
        try:
            file_instance = File.objects.get(id=file_id)
            uploader = file_instance.uploader.user
            if file_instance.file_extra_JSON is not None:
                if file_instance.file_extra_JSON['request_type'] == 'Expenditure':
                    pid=(int)(file_instance.file_extra_JSON['pid'])
                    cost=(int)(file_instance.file_extra_JSON['cost'])
                    try:
                        project_instance = projects.objects.get(pid=pid)
                    except projects.DoesNotExist:
                        return Response({"Error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)
                    remaining_budget=project_instance.rem_budget
                    if cost > remaining_budget:
                        return Response({"Error": "Failed to approve file: Expenditure demand is more than the project's remaining budget"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    else:
                        project_instance.rem_budget=remaining_budget-cost
                        project_instance.save()
                file_instance.file_extra_JSON['approval'] = "Approved"
                file_instance.save()
                request_instance=None
                if file_instance.file_extra_JSON['request_type'] == 'Expenditure':
                    request_instance=expenditure.objects.get(file_id=file_id)
                else:
                    request_instance=staff.objects.get(file_id=file_id)
                if request_instance is not None:
                    request_instance.approval = "Approved"
                    request_instance.save()
            archive_file(file_id=file_id)
            sender_notif = User.objects.get(username=request.user.username)
            recipient_notif = User.objects.get(username=uploader)
            RSPC_notif(sender=sender_notif, recipient=recipient_notif, type="Approved")
            return Response({"message": "File Approved Successfully"}, status=status.HTTP_200_OK)
        except File.DoesNotExist:
            return Response({"Error": "File not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"Error": f"Failed to approve file: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response({"Error": "file_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
@api_view(['GET'])
def accept_completion(request):
    pid = request.GET.get('pid') 
    if pid is not None:
        try:
            project_instance = projects.objects.get(pid=pid)
            project_instance.status = "Completed"
            project_instance.save()
            sender_notif = User.objects.get(username=request.user.username)
            recipient_notif = User.objects.get(username=project_instance.pi_id)
            RSPC_notif(sender=sender_notif, recipient=recipient_notif, type="Over")
            return Response({"message": "Project Ending Successful"}, status=status.HTTP_200_OK)
        except projects.DoesNotExist:
            return Response({"Error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"Error": f"Failed to complete project: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response({"Error": "pid is required"}, status=status.HTTP_400_BAD_REQUEST)