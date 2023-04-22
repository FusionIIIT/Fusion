
import datetime

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect

from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes,authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


from applications.globals.models import HoldsDesignation, Designation, ExtraInfo


from . import serializers
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from applications.filetracking.models import File
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation
from django.template.defaulttags import csrf_token
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.core import serializers
from django.contrib.auth.models import User
from timeit import default_timer as time
from notification.views import office_module_notif,file_tracking_notif
from applications.filetracking.utils import *
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation
from django.template.defaulttags import csrf_token
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.core import serializers
from django.contrib.auth.models import User
from timeit import default_timer as time
from notification.views import office_module_notif,file_tracking_notif
from .utils import *
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from applications.globals.models import (HoldsDesignation,Designation)
from django.shortcuts import get_object_or_404
from django.forms.models import model_to_dict
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes,authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from applications.globals.models import User,ExtraInfo
from applications.complaint_system.models import Caretaker, StudentComplain, Supervisor, Workers
from . import serializers
from rest_framework.parsers import JSONParser
import json
from rest_framework.views import APIView


class MyOwnView(APIView):
    def get(self, request):
        return Response({'status': 'ok'})

@api_view(['POST', 'GET']) 
# @permission_classes([IsAuthenticated])
# @authentication_classes([TokenAuthentication])
def filetracking(request):
    
    authentication_classes = [] #disables authentication
    permission_classes = [] #disables permission
    rcv = 'AG'


    if request.method =="POST":
        try:


            if 'reciever_submit' in request.POST:
                 rcv = request.POST.get('receiver')
                
            
            if 'save' in request.POST:
                uploader = request.user.extrainfo
                subject = request.POST.get('title')
                description = request.POST.get('desc')
                design = request.POST.get('design')
                designation = Designation.objects.get(id = HoldsDesignation.objects.select_related('user','working','designation').get(id = design).designation_id)
                upload_file = request.FILES.get('myfile')
                if(upload_file.size / 1000 > 10240):
                    messages.error(request,"File should not be greater than 10MB")
                    return redirect("/filetracking")               

                File.objects.create(
                    uploader=uploader,
                    description=description,
                    subject=subject,
                    designation=designation,
                    upload_file=upload_file
                )

                messages.success(request,'File Draft Saved Successfully')

            if 'send' in request.POST:
                uploader = request.user.extrainfo
                subject = request.POST.get('title')
                description = request.POST.get('desc')
                design = request.POST.get('design')
                designation = Designation.objects.get(id = HoldsDesignation.objects.select_related('user','working','designation').get(id = design).designation_id)

                upload_file = request.FILES.get('myfile')
                # if(upload_file.size / 1000 > 10240):
                #     messages.error(request,"File should not be greater than 10MB")
                #     return redirect("/filetracking")

                file = File.objects.create(
                    uploader=uploader,
                    description=description,
                    subject=subject,
                    designation=designation,
                    upload_file=upload_file
                )


                current_id = request.user.extrainfo
                remarks = request.POST.get('remarks')

                sender = request.POST.get('design')
                current_design = HoldsDesignation.objects.select_related('user','working','designation').get(id=sender)

                receiver = request.POST.get('receiver')
                try:
                    receiver_id = User.objects.get(username=receiver)
                except Exception as e:
                    return Response({'message':'error'}, status=status.HTTP_400_BAD_REQUEST)
                receive = request.POST.get('recieve')
                try:
                    receive_design = Designation.objects.get(name=receive)
                except Exception as e:
                    return Response({'message':'error'}, status=status.HTTP_400_BAD_REQUEST)

                upload_file = request.FILES.get('myfile')

                Tracking.objects.create(
                    file_id=file,
                    current_id=current_id,
                    current_design=current_design,
                    receive_design=receive_design,
                    receiver_id=receiver_id,
                    remarks=remarks,
                    upload_file=upload_file,
                )
                #office_module_notif(request.user, receiver_id)
                file_tracking_notif(request.user,receiver_id,subject)
                messages.success(request,'File sent successfully')

        except IntegrityError:
           
            return Response({'message':'FileID Already Taken.!!'}, status=status.HTTP_400_BAD_REQUEST)



    file = File.objects.select_related('uploader_user','uploader_department','designation').all()
    extrainfo = ExtraInfo.objects.select_related('user','department').all()
    holdsdesignations = HoldsDesignation.objects.select_related('user','working','designation').all()
    designations = get_designation(request.user)
    
    receiverr = User.objects.get(username=rcv)
    receiverr = get_designation(receiverr)
    resp = {
        'file': file,
        'extrainfo': extrainfo,
        'holdsdesignations': holdsdesignations,
        'designations': designations,
        'reciever_designation': receiverr,
        
    }
    json_object = json.dumps(resp, indent = 5) 
    return Response(data=resp, status=status.HTTP_200_OK)


@login_required(login_url = "/accounts/login")
@api_view(['GET']) 
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def drafts(request):
    """
        The function is used to get the designation of the user and renders it on draft template.
        @param:
                request - trivial.
        @variables:
                
                
                context - Holds data needed to make necessary changes in the template.
    """
    designation = get_designation(request.user)
    resp = {
        'designation': designation,
    }
    return Response(data=resp, status=status.HTTP_200_OK)

def fileview(request,id):

    """
    This function is used to veiw all all created files by the user ordered by upload date.it collects all the created files from File object.
    @param:
      request - trivial
      id - user id 
    @parameters
      draft - file obeject containing all the files created by user
      context - holds data needed to render the template
      
    
    """
    # draft = File.objects.select_related('uploader__user','uploader__department','designation').filter(uploader=request.user.extrainfo).order_by('-upload_date')
    # extrainfo = ExtraInfo.objects.select_related('user','department').all()

    extrainfo = ExtraInfo.objects.select_related('user','department').all()
  
    ids = File.objects.filter(uploader=request.user.extrainfo).order_by('-upload_date').values_list('id', flat=True)
    draft_files_pk=[]
    
    for i in ids: 
       file_tracking_ids = Tracking.objects.filter(file_id=i).values_list('id', flat=True)
       if(len(file_tracking_ids)==0):
        draft_files_pk.append(i)
    
    draft_file_list=[]
    for i in draft_files_pk:
        draft_file_list.append(File.objects.get(pk=i))



    user_designation = HoldsDesignation.objects.select_related('user','working','designation').get(pk=id)
    s = str(user_designation).split(" - ")
    designations = s[1]
    resp = {

        'draft': draft_file_list,
        'extrainfo': extrainfo,
        'designations': designations,
    }
    return  Response(data=resp, status=status.HTTP_200_OK)


