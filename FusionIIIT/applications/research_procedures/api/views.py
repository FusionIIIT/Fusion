# from rest_framework.viewsets import ModelViewSet
# from applications.research_procedures.models import *
# from .serializers import *
# from rest_framework.permissions import IsAuthenticatedOrReadOnly 


# @api_view(['GET', 'POST'])
# def add_projects(request):
#     if request.method== "POST":
#         obj= request.POST
#         projectid= obj.get('project_id')
#         projectname= obj.get('project_name')
#         projecttype= obj.get('project_type')
#         stats= obj.get('status')
#         fo= obj.get('financial_outlay')
#         pid= obj.get('project_investigator_id')
#         rspc= obj.get('rspc_admin_id')
#         copid=obj.get('co_project_investigator_id')
#         sa= obj.get('sponsored_agency')
#         startd= obj.get('start_date')
#         subd= obj.get('submission_date')
#         finishd= obj.get('finish_date')

#         check= HoldsDesignation.objects.get(user=pid , designation= "Professor")
#         if not check.exists():
#                 check= HoldsDesignation.objects.get(user=pid , designation= "Assistant Professor")

#                 if not check.exists():
#                     return JsonResponse({'error': 'Request not added, no such Professor exists'}, status=400)
        
#         check= User.objects.filter(username=rspc)
#         if not check.exists():
#             return JsonResponse({'error': 'Project not added, no such rspc admin exists'}, status=400)

#         check= HoldsDesignation.objects.get(user=copid , designation= "Professor")
#         if not check.exists():
#                 check= HoldsDesignation.objects.get(user=copid , designation= "Assistant Professor")

#                 if not check.exists():
#                     return JsonResponse({'error': 'Request not added, no such project investigator exists'}, status=400)


#         projects.objects.create(
#             project_id=projectid,
#             project_name=projectname,
#             project_type=projecttype,  # Assuming project_type is a field in your model
#             status=stats,
#             financial_outlay=fo,
#             project_investigator_id=pid,
#             rspc_admin_id=rspc,
#             co_project_investigator_id=copid,
#             sponsored_agency=sa,
#             start_date=startd,
#             submission_date=subd,
#             finish_date=finishd
#         )

#         return Response({'message': 'Hidden grade added successfully'}, status=status.HTTP_201_CREATED)

# def add_fund_requests(request):
#     return render(request,"rs/add_fund_requests.html")

# def add_staff_requests(request):
#     return render(request,"rs/add_staff_requests.html")

# def add_requests(request,id):
#     if request.method == 'POST':
#         obj=request.POST


#         if(id=='0') :  
#             requestid = obj.get('request_id')
#             projectid = obj.get('project_id')
#             reqtype = obj.get('request_type')
#             pi_id = obj.get('project_investigator_id')
#             stats = obj.get('status')
#             desc= obj.get('description')
#             amt= obj.get('amount')

#             check= projects.objects.filter(project_id=projectid)
#             if not check.exists():
#                 messages.error(request,"Request not added, no such project exists")
#                 return render(request,"rs/add_fund_requests.html")

#             check= projects.objects.filter(project_id= projectid, project_investigator_id=pi_id)
#             if not check.exists():
#                 messages.error(request,"Request not added, no such project investigator exists")
#                 return render(request,"rs/add_fund_requests.html")

#             requests.objects.create(
#                 request_id=requestid,
#                 project_id=projectid,
#                 request_type=reqtype,
#                 project_investigator_id=pi_id,
#                 status=stats, description=desc, amount= amt
#             )
#             rspc_inventory.objects.create(
#                 inventory_id=requestid,
#                 project_id=projectid,
#                 project_investigator_id=pi_id,
#                 status=stats,
#                 description=desc, amount= amt
#             )
#             messages.success(request,"Request added successfully")
#             return render(request,"rs/add_fund_requests.html")

#         if(id=='1'):
#             requestid = obj.get('request_id')
#             projectid = obj.get('project_id')
#             reqtype = obj.get('request_type')
#             pi_id = obj.get('project_investigator_id')
#             stats = obj.get('status')

#             check= projects.objects.filter(project_id=projectid)
#             if not check.exists():
#                 messages.error(request,"Request not added, no such project exists")
#                 return render(request,"rs/add_fund_requests.html")

#             check= projects.objects.filter(project_id= projectid, project_investigator_id=pi_id)
#             if not check.exists():
#                 messages.error(request,"Request not added, no such project investigator exists")
#                 return render(request,"rs/add_fund_requests.html")


#             requests.objects.create(
#             request_id=requestid,
#             project_id=projectid,
#             request_type=reqtype,
#             project_investigator_id=pi_id,
#             status=stats,description= "staff request", amount= 0
#             )
#         messages.success(request,"Request added successfully")
#         # print("prudvi lanja")
#         return redirect("/research_procedures")
#     return render(request, "rs/add_requests.html")    

#     # return redirect("/")





# def view_projects(request):
#     # context= 
#     queryset= projects.objects.all()

#     if request.user.username == "21bcs3000":
#         data= {
#         "projects": queryset,
#         "username": request.user.username,
#         }
#         return render(request,"rs/view_projects_rspc.html", context= data)

#     queryset= projects.objects.filter(project_investigator_id= request.user.username)
   
#     data= {
#         "projects": queryset,
#         "username": request.user.username,
       
#     }
#     print(data)

#     print(request.user.username)
#     if request.user.username != "atul":
#         return redirect("/")

#     data= {
#         "requests": queryset,
#         "username": request.user.username
#     }
#     obj_serialized = serializers.ResearchProceduresSerializer(data, many=True).data

#     resp = {
#         'objt': obj_serialized
#     }

#     return Response(data=resp, status=status.HTTP_200_OK)



# def view_requests(request,id):
#     # context=  
        
#     if id== '1':
#         queryset= requests.objects.filter(request_type= "staff")
#     elif id== '0':
#         if request.user.username == "21bcs3000" :
#             queryset= rspc_inventory.objects.all()
#             data= {
#             "requests": queryset,
#             "username": request.user.username
#             }   
#             obj_serialized = serializers.ResearchProceduresSerializer(data, many=True).data

#             resp = {
#             'objt': obj_serialized
#             }

#             return Response(data=resp, status=status.HTTP_200_OK)
        
           
#         queryset= rspc_inventory.objects.filter(project_investigator_id = request.user.username)

#     data= {
#         "requests": queryset,
#         "username": request.user.username
#     }
#     obj_serialized = serializers.ResearchProceduresSerializer(data, many=True).data

#     resp = {
#         'objt': obj_serialized
#     }

#     return Response(data=resp, status=status.HTTP_200_OK)


# def submit_closure_report(request,id):
#     id= int(id)
#     obj= projects.objects.get(project_id=id)
#     obj.status= 1; 
#     obj.save()

#     queryset= projects.objects.filter(project_investigator_id = request.user.username)

#     print(queryset)
    
#     data= {
#         "projects": queryset,
#         "username": request.user.username
#     }
#     messages.success(request,"Closure report submitted successfully")
#     return render(request,"rs/view_projects_rspc.html",context=data)

# def projectss(request):
#     return render(request,"rs/projects.html")