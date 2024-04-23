from .serializers import LTC_serializer, CPDAAdvance_serializer, Appraisal_serializer, CPDAReimbursement_serializer, Leave_serializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import permission_classes, api_view
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import LTCform, CPDAAdvanceform, CPDAReimbursementform, Leaveform, Appraisalform
from django.contrib.auth import get_user_model
from django.core.exceptions import MultipleObjectsReturned
from applications.filetracking.sdk.methods import *
from applications.globals.models import Designation, HoldsDesignation

class LTC(APIView):
    serializer_class = LTC_serializer
    permission_classes = (AllowAny, )
    def post(self, request):
        if 'Mobile-OS' in request.META:
            user_info = request.data[0]
            serializer = self.serializer_class(data = request.data[1])
            if serializer.is_valid():
                serializer.save()
                file_id = create_file(uploader = user_info['uploader_name'], uploader_designation = user_info['uploader_designation'], receiver = "21BCS140", receiver_designation="hradmin", src_module="HR", src_object_id= str(serializer.data['id']), file_extra_JSON= {"type": "LTC"}, attached_file= None)
                return Response(serializer.data, status= status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status= status.HTTP_400_BAD_REQUEST)
        id = request.query_params.get("id")
        try:
            employee = ExtraInfo.objects.get(user__id=id)
        except:
            raise Http404("Post does not exist! id doesnt exist")

        print(employee.user_type)

        
        if(employee.user_type == 'faculty'):
            template = 'hr2Module/ltc_form.html'

            if request.method == "POST":
                family_mem_a = request.POST.get('id_family_mem_a', '')
                family_mem_b = request.POST.get('id_family_mem_b', '')
                family_mem_c = request.POST.get('id_family_mem_c', '')

            
                detailsOfFamilyMembers = ', '.join(filter(None, [family_mem_a, family_mem_b, family_mem_c]))

            
                request.POST = request.POST.copy()
                request.POST['detailsOfFamilyMembersAlreadyDone'] = detailsOfFamilyMembers

        
                family_members = []
                for i in range(1, 7):  # Loop through input fields for each family member
                    name = request.POST.get(f'info_{i}_2', '')  # Get the name
                    age = request.POST.get(f'info_{i}_3', '')   # Get the age
                    if name and age:  # Check if both name and age are provided
                        family_members.append(f"{name} ({age} years)")  # Concatenate name and age

                family_members_str = ', '.join(family_members)

                # Populate the form with concatenated family member details
                request.POST['familyMembersAboutToAvail'] = family_members_str

                dependents = []
                for i in range(1, 7):  # Loop through input fields for each dependent
                    name = request.POST.get(f'd_info_{i}_2', '')  # Get the name
                    age = request.POST.get(f'd_info_{i}_3', '')   # Get the age
                    why_dependent = request.POST.get(f'd_info_{i}_4', '')  # Get the reason for dependency
                    if name and age:  # Check if both name and age are provided
                        dependents.append(f"{name} ({age} years), {why_dependent}")  # Concatenate name, age, and reason
                

                # Concatenate all dependent strings into a single string
                dependents_str = ', '.join(dependents)

                # Populate the form with concatenated dependent details
                request.POST['detailsOfDependents'] = dependents_str

                # print("first",request.POST['familyMembersAboutToAvail'])
                pf_no = int(request.POST.get('pf_no')) if request.POST.get('pf_no') else None
                basicPay = int(request.POST.get('basicPay')) if request.POST.get('basicPay') else None
                amountOfAdvanceRequired = int(request.POST.get('amountOfAdvanceRequired')) if request.POST.get('amountOfAdvanceRequired') else None
                phoneNumberForContact = int(request.POST.get('phoneNumberForContact')) if request.POST.get('phoneNumberForContact') else None


                try:
                    ltc_request = LTCform.objects.create(
                        employee_id = id,
                        detailsOfFamilyMembersAlreadyDone=request.POST.get('detailsOfFamilyMembersAlreadyDone', ''),
                        familyMembersAboutToAvail=request.POST.get('familyMembersAboutToAvail', ''),
                        detailsOfDependents=request.POST.get('detailsOfDependents', ''),
                        name=request.POST.get('name', ''),
                        blockYear=request.POST.get('blockYear', ''),
                        pf_no=request.POST.get('pf_no', ''),
                        basicPay=request.POST.get('basicPay', ''),
                        designation=request.POST.get('designation', ''),
                        departmentInfo=request.POST.get('departmentInfo', ''),
                        leaveAvailability=request.POST.get('leaveAvailability', ''),
                        leaveStartDate=request.POST.get('leaveStartDate', ''),
                        leaveEndDate=request.POST.get('leaveEndDate', ''),
                        dateOfLeaveForFamily=request.POST.get('dateOfLeaveForFamily', ''),
                        natureOfLeave=request.POST.get('natureOfLeave', ''),
                        purposeOfLeave=request.POST.get('purposeOfLeave', ''),
                        hometownOrNot=request.POST.get('hometownOrNot', ''),
                        placeOfVisit=request.POST.get('placeOfVisit', ''),
                        addressDuringLeave=request.POST.get('addressDuringLeave', ''),
                        modeForVacation=request.POST.get('modeForVacation', ''),
                        detailsOfFamilyMembers=request.POST.get('detailsOfFamilyMembers', ''),
                        amountOfAdvanceRequired=request.POST.get('amountOfAdvanceRequired', ''),
                        certifiedFamilyDependents=request.POST.get('certifiedFamilyDependents', ''),
                        certifiedAdvance =request.POST.get('certifiedAdvance ', ''),
                        adjustedMonth=request.POST.get('adjustedMonth', ''),
                        date=request.POST.get('date', ''),
                        phoneNumberForContact=request.POST.get('phoneNumberForContact', '')
                    )
                    print("done")
                    messages.success(request, "Ltc form filled successfully")
                except Exception as e:
                    print("error" , e)
                    messages.warning(request, "Fill not correctly")
                    context = {'employee': employee}
                    return render(request, template, context)

                
            # Query all LTC requests
            ltc_requests = LTCform.objects.filter(employee_id=id)

            context = {'employee': employee, 'ltc_requests': ltc_requests}

            return render(request, template, context)
        else:
            return render(request, 'hr2Module/edit.html')
        


    def get(self, request, *args, **kwargs):
        pk = request.query_params.get("name")
        print(pk)
        try: 
            forms = LTCform.objects.get(name =  pk)           
            serializer = self.serializer_class(forms, many = False)
        except MultipleObjectsReturned:
            forms = LTCform.objects.filter(name =  pk)
            serializer = self.serializer_class(forms, many = True)
        return Response(serializer.data, status = status.HTTP_200_OK)
    
    def put(self, request, *args, **kwargs):
        pk = request.query_params.get("id")
        print(pk)
        form = LTCform.objects.get(id = pk)
        print(form)
        serializer = self.serializer_class(form, data = request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status = status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)

class FormManagement(APIView):
    permission_classes = (AllowAny, )
    def get(self, request, *args, **kwargs):
        username = request.query_params.get("username")
        designation = request.query_params.get("designation")
        inbox = view_inbox(username = username, designation = designation, src_module = "HR")
        return Response(inbox, status = status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        username = request.data['receiver']
        receiver_value = User.objects.get(username=username)
        receiver_value_designation= HoldsDesignation.objects.filter(user=receiver_value)
        lis = list(receiver_value_designation)
        obj=lis[0].designation
        forward_file(file_id = request.data['file_id'], receiver = request.data['receiver'], receiver_designation = obj.name, remarks = request.data['remarks'], file_extra_JSON = request.data['file_extra_JSON'])
        return Response(status = status.HTTP_200_OK)  


class CPDAAdvance(APIView):
    serializer_class = CPDAAdvance_serializer
    permission_classes = (AllowAny, )
    def post(self, request):
        user_info = request.data[0]
        serializer = self.serializer_class(data = request.data[1])
        if serializer.is_valid():
            serializer.save()
            file_id = create_file(uploader = user_info['uploader_name'], uploader_designation = user_info['uploader_designation'], receiver = "vkjain", receiver_designation="CSE HOD", src_module="HR", src_object_id= str(serializer.data['id']), file_extra_JSON= {"type": "CPDAAdvance"}, attached_file= None)
            return Response(serializer.data, status= status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status= status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        pk = request.query_params.get("name")
        print(pk)
        try: 
            forms = CPDAAdvanceform.objects.get(name =  pk)           
            serializer = self.serializer_class(forms, many = False)
        except MultipleObjectsReturned:
            forms = CPDAAdvanceform.objects.filter(name =  pk)
            serializer = self.serializer_class(forms, many = True)
        return Response(serializer.data, status = status.HTTP_200_OK)
    
    def put(self, request, *args, **kwargs):
        pk = request.query_params.get("id")
        print(pk)
        form = CPDAAdvanceform.objects.get(id = pk)
        print(form)
        serializer = self.serializer_class(form, data = request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status = status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)

class CPDAReimbursement(APIView):
    serializer_class = CPDAReimbursement_serializer
    permission_classes = (AllowAny, )
    def post(self, request):
        user_info = request.data[0]
        serializer = self.serializer_class(data = request.data[1])
        if serializer.is_valid():
            serializer.save()
            file_id = create_file(uploader = user_info['uploader_name'], uploader_designation = user_info['uploader_designation'], receiver = "vkjain", receiver_designation="CSE HOD", src_module="HR", src_object_id= str(serializer.data['id']), file_extra_JSON= {"type": "CPDAReimbursement"}, attached_file= None)
            return Response(serializer.data, status= status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status= status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        pk = request.query_params.get("name")
        print(pk)
        try: 
            forms = CPDAReimbursementform.objects.get(name =  pk)           
            serializer = self.serializer_class(forms, many = False)
        except MultipleObjectsReturned:
            forms = CPDAReimbursementform.objects.filter(name =  pk)
            serializer = self.serializer_class(forms, many = True)
        return Response(serializer.data, status = status.HTTP_200_OK)
    
    def put(self, request, *args, **kwargs):
        pk = request.query_params.get("id")
        print(pk)
        form = CPDAReimbursementform.objects.get(id = pk)
        print(form)
        serializer = self.serializer_class(form, data = request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status = status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)

class Leave(APIView):
    serializer_class = Leave_serializer
    permission_classes = (AllowAny, )
    def post(self, request):
        user_info = request.data[0]
        serializer = self.serializer_class(data = request.data[1])
        if serializer.is_valid():
            serializer.save()
            file_id = create_file(uploader = user_info['uploader_name'], uploader_designation = user_info['uploader_designation'], receiver = "vkjain", receiver_designation="CSE HOD", src_module="HR", src_object_id= str(serializer.data['id']), file_extra_JSON= {"type": "Leave"}, attached_file= None)
            return Response(serializer.data, status= status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status= status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        pk = request.query_params.get("name")
        print(pk)
        try: 
            forms = Leaveform.objects.get(name =  pk)           
            serializer = self.serializer_class(forms, many = False)
        except MultipleObjectsReturned:
            forms = Leaveform.objects.filter(name =  pk)
            serializer = self.serializer_class(forms, many = True)
        return Response(serializer.data, status = status.HTTP_200_OK)
    
    def put(self, request, *args, **kwargs):
        pk = request.query_params.get("id")
        print(pk)
        form = Leaveform.objects.get(id = pk)
        print(form)
        serializer = self.serializer_class(form, data = request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status = status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)

class Appraisal(APIView):
    serializer_class = Appraisal_serializer
    permission_classes = (AllowAny, )
    def post(self, request):
        user_info = request.data[0]
        serializer = self.serializer_class(data = request.data[1])
        if serializer.is_valid():
            serializer.save()
            file_id = create_file(uploader = user_info['uploader_name'], uploader_designation = user_info['uploader_designation'], receiver = "vkjain", receiver_designation="CSE HOD", src_module="HR", src_object_id= str(serializer.data['id']), file_extra_JSON= {"type": "Appraisal"}, attached_file= None)
            return Response(serializer.data, status= status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status= status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        pk = request.query_params.get("name")
        print(pk)
        try: 
            forms = Appraisalform.objects.get(name =  pk)           
            serializer = self.serializer_class(forms, many = False)
        except MultipleObjectsReturned:
            forms = Appraisalform.objects.filter(name =  pk)
            serializer = self.serializer_class(forms, many = True)
        return Response(serializer.data, status = status.HTTP_200_OK)
    
    def put(self, request, *args, **kwargs):
        pk = request.query_params.get("id")
        print(pk)
        form = Appraisalform.objects.get(id = pk)
        print(form)
        serializer = self.serializer_class(form, data = request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status = status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)
        
class AssignerReviewer(APIView):
    def post(self, request, *args, **kwargs):
        forward_file(file_id = request.data['file_id'], receiver = "21BCS140", receiver_designation = 'hradmin', remarks = request.data['remarks'], file_extra_JSON = request.data['file_extra_JSON'])
        return Response(status = status.HTTP_200_OK)