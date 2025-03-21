from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import LeaveFormSerializer  ,BonafideFormSerializer 
from datetime import date
from datetime import datetime
from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect,render
from rest_framework.permissions import IsAuthenticated  
from rest_framework.decorators import api_view, permission_classes
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from applications.otheracademic.models import (LeaveFormTable, BonafideFormTableUpdated, GraduateSeminarFormTable,AssistantshipClaimFormStatusUpd, LeavePG, NoDues)
from datetime import date
from applications.filetracking.models import File
from applications.filetracking.sdk.methods import create_file
from notification.views import otheracademic_notif
from applications.filetracking.models import *
from applications.filetracking.sdk.methods import *
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation
from django.http import JsonResponse
from django.db.models import F


class LeaveFormSubmitView(APIView):
    permission_classes = [IsAuthenticated] 

    def post(self, request):
        # Extract data from the request
        data = request.POST
        file = request.FILES.get('related_document')
        hodname = data.get('hod_credential')
        print(data.get('mobile_number'),data.get('parents_mobile'),"hello ab")
        
        # Create a new LeaveFormTable instance and save it to the database
        leave = LeaveFormTable.objects.create(
            student_name=request.user.first_name+request.user.last_name,
            roll_no=request.user.extrainfo,
            date_from=data.get('date_from'),
            date_to=data.get('date_to'),
            leave_type=data.get('leave_type'),
            upload_file=file,
            address=data.get('address'),
            purpose=data.get('purpose'),
            date_of_application=date.today(),
            # approved=False,  # Initially not approved
            # rejected=False,  # Initially not rejected
            stud_mobile_no=data.get('mobile_number'),
            parent_mobile_no=data.get('parents_mobile'),
            leave_mobile_no=data.get('mobile_during_leave'),
            curr_sem=int(data.get('semester')),
            hod=data.get('hod_credential')
        )
        print(data.get('mobile_number'),data.get('parents_mobile'))
        
        leave_hod = User.objects.get(username=hodname)
        receiver_value = User.objects.get(username=request.user.username)
        receiver_value_designation = HoldsDesignation.objects.filter(user=receiver_value)
        lis = list(receiver_value_designation)
        obj = lis[0].designation

        file_id = create_file(
            uploader=request.user.username,
            uploader_designation=obj,
            receiver=leave_hod,
            receiver_designation="student",
            src_module="otheracademic",
            src_object_id=leave.id,
            file_extra_JSON={"value": 2},
            attached_file=None,
            subject='ug_leave'
        )


        message = "A new leave application"
        otheracademic_notif(request.user, leave_hod, 'ug_leave_hod', leave.id, 'student', message)
    
        return Response({"message": "You successfully submitted your form"}, status=status.HTTP_201_CREATED)
    


class LeavePGSubmitView(APIView):
    permission_classes = [IsAuthenticated] 

    def post(self, request):
        # Extract data from the request
        data = request.POST
        file = request.FILES.get('related_document')
        hodname = data.get('hod_credential')
        ta_super = data.get('ta_superCredential')
        thesis_super = data.get('thesis_superCredential')
        print(data,"hello ab")
        
        leave = LeavePG.objects.create(
            student_name=request.user.first_name+request.user.last_name,
            roll_no=request.user.extrainfo,
            date_from=data.get('date_from'),
            date_to=data.get('date_to'),
            leave_type=data.get('leave_type'),
            upload_file=file,
            address=data.get('address'),
            purpose=data.get('purpose'),
            date_of_application=date.today(),
            stud_mobile_no=data.get('mobile_number'),
            parent_mobile_no=data.get('parents_mobile'),
            leave_mobile_no=data.get('mobile_during_leave'),
            curr_sem=int(data.get('semester')),
            hod=data.get('hod_credential'),
            ta_supervisor=data.get('ta_superCredential'),
            thesis_supervisor=data.get('thesis_superCredential'),
        )
        print(data.get('ta_superCredential'),data.get('thesis_supercredential'),"check point")
        
        leave_ta = User.objects.get(username=ta_super)
        leave_thesis = User.objects.get(username=thesis_super)
        leave_hod = User.objects.get(username=hodname)
        receiver_value = User.objects.get(username=request.user.username)
        receiver_value_designation = HoldsDesignation.objects.filter(user=receiver_value)
        lis = list(receiver_value_designation)
        obj = lis[0].designation

        file_id = create_file(
            uploader=request.user.username,
            uploader_designation=obj,
            receiver=leave_hod,
            receiver_designation="student",
            src_module="otheracademic",
            src_object_id=leave.id,
            file_extra_JSON={"value": 2},
            attached_file=None,
            subject='pg_leave'
        )

        message = "A new leave application"
        otheracademic_notif(request.user, leave_ta, 'pg_leave_at', leave.id, 'student', message)
    
        return Response({"message": "You successfully submitted your form"}, status=status.HTTP_201_CREATED)




class FetchPendingLeaveRequests(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):  # Add request as a parameter
        # Filter for pending leave requests
        pending_leaves = LeaveFormTable.objects.filter(status="Pending")
        pending_leaves_pg = LeavePG.objects.filter(status=F('thesis_supervisor'))

        # Serialize the data
        data = [
            {
                "id": leave.id,
                "rollNo": leave.roll_no.id,  # Assuming roll_number is the field in ExtraInfo
                "name": leave.student_name,
                "form": leave.upload_file.url if leave.upload_file else None,
                "details": {
                    "dateFrom": leave.date_from,
                    "dateTo": leave.date_to,
                    "leaveType": leave.leave_type,
                    "address": leave.address,
                    "purpose": leave.purpose,
                    "hodCredential": leave.hod,
                    "mobileNumber": leave.stud_mobile_no,
                    "parentsMobile": leave.parent_mobile_no,
                    "mobileDuringLeave": leave.leave_mobile_no,
                    "semester": leave.curr_sem,
                    "academicYear": leave.date_of_application.year,
                    "dateOfApplication": leave.date_of_application,
                },
            }
            for leave in pending_leaves
        ]

        for leave_pg in pending_leaves_pg:
            data.append({
            "id": leave_pg.id,
            "rollNo": leave_pg.roll_no.id,  # Adjust this field based on your model
            "name": leave_pg.student_name,
            "form": leave_pg.upload_file.url if leave_pg.upload_file else None,
            "details": {
                "dateFrom": leave_pg.date_from,
                "dateTo": leave_pg.date_to,
                "leaveType": leave_pg.leave_type,
                "address": leave_pg.address,
                "purpose": leave_pg.purpose,
                "hodCredential": leave_pg.hod,
                "mobileNumber": leave_pg.stud_mobile_no,
                "parentsMobile": leave_pg.parent_mobile_no,
                "mobileDuringLeave": leave_pg.leave_mobile_no,
                "semester": leave_pg.curr_sem,
                "academicYear": leave_pg.date_of_application.year,
                "dateOfApplication": leave_pg.date_of_application,
            },
        })

        return Response(data)
    

class FetchPendingLeaveRequestsTA(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):  # Add request as a parameter
        # Filter for pending leave requests
        pending_leaves = LeavePG.objects.filter(status="Pending")

        # Serialize the data
        data = [
            {
                "id": leave.id,
                "rollNo": leave.roll_no.id,  # Assuming roll_number is the field in ExtraInfo
                "name": leave.student_name,
                "form": leave.upload_file.url if leave.upload_file else None,
                "details": {
                    "dateFrom": leave.date_from,
                    "dateTo": leave.date_to,
                    "leaveType": leave.leave_type,
                    "address": leave.address,
                    "purpose": leave.purpose,
                    "hodCredential": leave.hod,
                    "mobileNumber": leave.stud_mobile_no,
                    "parentsMobile": leave.parent_mobile_no,
                    "mobileDuringLeave": leave.leave_mobile_no,
                    "semester": leave.curr_sem,
                    "academicYear": leave.date_of_application.year,
                    "dateOfApplication": leave.date_of_application,
                },
            }
            for leave in pending_leaves
        ]

        return Response(data)
    

class FetchPendingLeaveRequestsThesis(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):  # Add request as a parameter
        # Filter for pending leave requests
        pending_leaves = LeavePG.objects.filter(status=F('ta_supervisor'))

        # Serialize the data
        data = [
            {
                "id": leave.id,
                "rollNo": leave.roll_no.id,  # Assuming roll_number is the field in ExtraInfo
                "name": leave.student_name,
                "form": leave.upload_file.url if leave.upload_file else None,
                "details": {
                    "dateFrom": leave.date_from,
                    "dateTo": leave.date_to,
                    "leaveType": leave.leave_type,
                    "address": leave.address,
                    "purpose": leave.purpose,
                    "hodCredential": leave.hod,
                    "mobileNumber": leave.stud_mobile_no,
                    "parentsMobile": leave.parent_mobile_no,
                    "mobileDuringLeave": leave.leave_mobile_no,
                    "semester": leave.curr_sem,
                    "academicYear": leave.date_of_application.year,
                    "dateOfApplication": leave.date_of_application,
                },
            }
            for leave in pending_leaves
        ]

        return Response(data)
    
class UpdateLeaveStatus(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Get the list of approved and rejected leave ids from the request
        approved_leaves_ids = request.data.get('approvedLeaves', [])
        rejected_leaves_ids = request.data.get('rejectedLeaves', [])
        approved_leaves_ids1 = request.data.get('approvedLeaves', [])
        rejected_leaves_ids1 = request.data.get('rejectedLeaves', [])
        # Update the status of approved leaves
        approved_leaves = LeaveFormTable.objects.filter(id__in=approved_leaves_ids)
        approved_leaves.update(status="Approved")

        # Update the status of rejected leaves
        rejected_leaves = LeaveFormTable.objects.filter(id__in=rejected_leaves_ids)
        rejected_leaves.update(status="Rejected")

        approved_leaves1 = LeavePG.objects.filter(id__in=approved_leaves_ids1)
        approved_leaves1.update(status="Approved")

        # Update the status of rejected leaves
        rejected_leaves1 = LeavePG.objects.filter(id__in=rejected_leaves_ids1)
        rejected_leaves1.update(status="Rejected")

        return Response({"message": "Leave statuses updated successfully."})
    
class UpdateLeaveStatusTA(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Get the list of approved and rejected leave ids from the request
        approved_leaves_ids = request.data.get('approvedLeaves', [])
        rejected_leaves_ids = request.data.get('rejectedLeaves', [])

        # Update the status of approved leaves
        approved_leaves = LeavePG.objects.filter(id__in=approved_leaves_ids)
        approved_leaves.update(status=F('ta_supervisor'))

        # Update the status of rejected leaves
        rejected_leaves = LeavePG.objects.filter(id__in=rejected_leaves_ids)
        rejected_leaves.update(status="Rejected")

        return Response({"message": "Leave statuses updated successfully."})
    
class UpdateLeaveStatusThesis(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Get the list of approved and rejected leave ids from the request
        approved_leaves_ids = request.data.get('approvedLeaves', [])
        rejected_leaves_ids = request.data.get('rejectedLeaves', [])

        # Update the status of approved leaves
        approved_leaves = LeavePG.objects.filter(id__in=approved_leaves_ids)
        approved_leaves.update(status=F('thesis_supervisor'))

        # Update the status of rejected leaves
        rejected_leaves = LeavePG.objects.filter(id__in=rejected_leaves_ids)
        rejected_leaves.update(status="Rejected")

        return Response({"message": "Leave statuses updated successfully."})

class GetLeaveRequests(APIView):
    
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Get roll_no and username from query params
        
        roll_no_id = request.query_params.get('roll_no')
        username = request.query_params.get('username')
        print(roll_no_id,username)
        
        # print(f"Received roll_no: {roll_no_id}, username: {username}")


        # # Filter the leave requests based on roll_no and student_name (username)
        leave_requests = LeaveFormTable.objects.filter(
            roll_no=roll_no_id
        )

        # Serialize the data (assuming the serializer is defined for LeaveFormTable)
        data = [
            {
                "rollNo": roll_no_id,  # Assuming roll_number is the field in ExtraInfo
                "name": leave.student_name,
                "dateFrom": leave.date_from,
                "dateTo": leave.date_to,
                "leaveType": leave.leave_type,
                "attachment": leave.upload_file.url if leave.upload_file else None,
                "purpose": leave.purpose,
                "address": leave.address,
                "action": leave.status,
            }
            for leave in leave_requests
        ]
        print(data) 

        return Response(data, status=status.HTTP_200_OK)


class GetPGLeaveRequests(APIView):
    
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Get roll_no and username from query params
        
        roll_no_id = request.query_params.get('roll_no')
        username = request.query_params.get('username')
        print(roll_no_id,username)
        
        # print(f"Received roll_no: {roll_no_id}, username: {username}")


        # # Filter the leave requests based on roll_no and student_name (username)
        leave_requests = LeavePG.objects.filter(
            roll_no=roll_no_id
        )

        # Serialize the data (assuming the serializer is defined for LeaveFormTable)
        data = [
            {
                "rollNo": roll_no_id,  # Assuming roll_number is the field in ExtraInfo
                "name": leave.student_name,
                "dateFrom": leave.date_from,
                "dateTo": leave.date_to,
                "leaveType": leave.leave_type,
                "attachment": leave.upload_file.url if leave.upload_file else None,
                "purpose": leave.purpose,
                "address": leave.address,
                "action": leave.status,
            }
            for leave in leave_requests
        ]
        print(data) 

        return Response(data, status=status.HTTP_200_OK)
    


@csrf_exempt  # Exempt CSRF verification for this view
@login_required
def leave_form_submit(request):
    """
    View function for submitting a leave form.

    Description:
        This function handles form submission for leave requests, processes the data, and saves it to the database.
        It also notifies the relevant authority about the new leave application.
    """
    if request.method == 'POST':
        # Extract data from the request
        data = request.POST
        file = request.FILES.get('related_document')
        hodname = data.get('hod_credential')
        
        # Create a new LeaveFormTable instance and save it to the database
        leave = LeaveFormTable.objects.create(
            student_name=request.user.first_name+request.user.last_name,
            roll_no=request.user.extrainfo,
            date_from=data.get('date_from'),
            date_to=data.get('date_to'),
            leave_type=data.get('leave_type'),
            upload_file=file,
            address=data.get('address'),
            purpose=data.get('purpose'),
            date_of_application=date.today(),
            hod=data.get('hod_credential')
        )
        
        leave_hod = User.objects.get(username=hodname)
        receiver_value = User.objects.get(username=request.user.username)
        receiver_value_designation = HoldsDesignation.objects.filter(user=receiver_value)
        lis = list(receiver_value_designation)
        obj = lis[0].designation

        file_id = create_file(
            uploader=request.user.username,
            uploader_designation=obj,
            receiver=leave_hod,
            receiver_designation="student",
            src_module="otheracademic",
            src_object_id=leave.id,
            file_extra_JSON={"value": 2},
            attached_file=None,
            subject='ug_leave'
        )


        message = "A new leave application"
        otheracademic_notif(request.user, leave_hod, 'ug_leave_hod', leave.id, 'student', message)
        if leave:
            messages.success(request, "You successfully submitted your form")
            
        # return HttpResponseRedirect('/otheracademic/leaveform')


class BonafideFormSubmitView(APIView):
    """
    API view to handle Bonafide form submission.
    """

    permission_classes = [IsAuthenticated] 

    def post(self, request):
        # Extract data from the request

        data = request.POST
        file = request.FILES.get('related_document')  # Handle the file if uploaded

        try:
            # Create a new BonafideFormTableUpdated instance and save it to the database
            bonafide_form = BonafideFormTableUpdated.objects.create(
                student_names=f"{request.user.first_name} {request.user.last_name}",
                roll_nos=request.user.extrainfo,  # Assuming `extrainfo` is the user's ExtraInfo instance
                branch_types=data.get('branch'),
                semester_types=data.get('semester'),
                purposes=data.get('purpose'),
                date_of_applications=date.today(),
                download_file=file.name if file else "unavailable",
                approve=False,  # Default value
                reject=False,  # Default value
            )

            # Notify the academic admin about the new bonafide application
            acad_admin_des_id = Designation.objects.get(name="acadadmin")
            user_ids = HoldsDesignation.objects.filter(designation_id=acad_admin_des_id.id).values_list('user_id', flat=True)

            if user_ids.exists():
                bonafide_receiver = User.objects.get(id=user_ids[0])
                message = "A new Bonafide application has been submitted."
                otheracademic_notif(
                    request.user, 
                    bonafide_receiver, 
                    'bonafide', 
                    bonafide_form.id, 
                    'student', 
                    message
                )

            return Response(
                {"message": "Your bonafide form has been successfully submitted."},
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        


 

 

class FetchPendingBonafideRequests(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Fetch Bonafide requests where both approve and reject are False (unseen requests)
        pending_bonafides = BonafideFormTableUpdated.objects.filter(approve=False, reject=False)
        
        # Prepare response data
        data = [
            {
                "id": bonafide.id,
                "rollNo": bonafide.roll_nos_id,  # Assuming roll_no is a field in ExtraInfo
                "name": bonafide.student_names,
                "details": {
                    "purpose": bonafide.purposes,
                    "dateOfApplication": bonafide.date_of_applications,
                    "semester": bonafide.semester_types,
                },
            }
            for bonafide in pending_bonafides
        ]
        
        return Response(data)



 

 

class UpdateBonafideStatus(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Get the lists of approved and rejected bonafide request IDs from the request body
        approved_bonafides_ids = request.data.get('approvedBonafides', [])
        rejected_bonafides_ids = request.data.get('rejectedBonafides', [])

        try:
            # Update the approve/reject status based on the provided lists
            if approved_bonafides_ids:
                BonafideFormTableUpdated.objects.filter(id__in=approved_bonafides_ids).update(approve=True, reject=False)
                # Notify the respective students about approval
                for bonafide_id in approved_bonafides_ids:
                    bonafide_form = BonafideFormTableUpdated.objects.get(id=bonafide_id)
                    student = User.objects.get(extrainfo=bonafide_form.roll_nos_id)  # Assuming `extrainfo` is the student's unique identifier
                    # Send notification to the student about the approval
                    message = f"Your Bonafide application has been appr oved. Please check the status."
                    otheracademic_notif(
                        request.user,  # The sender (admin)
                        student,  # The receiver (student)
                        'bonafide_accept',  # Notification type
                        bonafide_form.id,  # The ID of the Bonafide form
                        'admin',  # The role of the sender
                        message  # The approval message
                    )

            if rejected_bonafides_ids:
                BonafideFormTableUpdated.objects.filter(id__in=rejected_bonafides_ids).update(approve=False, reject=True)

                # Notify the respective students about rejection
                for bonafide_id in rejected_bonafides_ids:
                    bonafide_form = BonafideFormTableUpdated.objects.get(id=bonafide_id)
                    student = User.objects.get(extrainfo=bonafide_form.roll_nos)  # Assuming `extrainfo` is the student's unique identifier

                    # Send notification to the student about the rejection
                    message = f"Your Bonafide application has been rejected. Please check the status for further details."
                    otheracademic_notif(
                        request.user,  # The sender (admin)
                        student,  # The receiver (student)
                        'bonafide_accept',  # Notification type
                        bonafide_form.id,  # The ID of the Bonafide form
                        'admin',  # The role of the sender
                        message  # The rejection message
                    )

            return Response({"message": "Bonafide statuses updated successfully."})

        except Exception as e:
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


class GetBonafideStatus(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Get roll number and username from the request
        roll_no = request.data.get("roll_no")
        username = request.data.get("username")

        # Check if roll number and username are provided
        if not roll_no or not username:
            return Response(
                {"error": "Roll number and username are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Query bonafide forms for the given roll number
            bonafide_requests = BonafideFormTableUpdated.objects.filter(roll_nos_id=roll_no)
            
            # Manually format the response data
            response_data = [
                {
                    "rollNo": bonafide.roll_nos_id,
                    "name": bonafide.student_names,
                    "branch": bonafide.branch_types,
                    "semester": bonafide.semester_types,
                    "purpose": bonafide.purposes,
                    "dateApplied": bonafide.date_of_applications.strftime("%Y-%m-%d") if bonafide.date_of_applications else None,
                    "status": (
                        "Approved" if bonafide.approve else "Rejected" if bonafide.reject else "Pending"
                    ),
                }
                for bonafide in bonafide_requests
            ]

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": "An error occurred while fetching bonafide status.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


            return Response({'message': 'Form submitted successfully', 'bonafide_id': bonafide.id}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@csrf_exempt  # Exempt CSRF verification for this view
@login_required
def leave_form_submit(request):
    """
    View function for submitting a leave form.

    Description:
        This function handles form submission for leave requests, processes the data, and saves it to the database.
        It also notifies the relevant authority about the new leave application.
    """
    if request.method == 'POST':
        # Extract data from the request
        data = request.POST
        file = request.FILES.get('related_document')
        hodname = data.get('hod_credential')
        
        # Create a new LeaveFormTable instance and save it to the database
        leave = LeaveFormTable.objects.create(
            student_name=request.user.first_name+request.user.last_name,
            roll_no=request.user.extrainfo,
            date_from=data.get('date_from'),
            date_to=data.get('date_to'),
            leave_type=data.get('leave_type'),
            upload_file=file,
            address=data.get('address'),
            purpose=data.get('purpose'),
            date_of_application=date.today(),
            hod=data.get('hod_credential')
        )
        
        leave_hod = User.objects.get(username=hodname)
        receiver_value = User.objects.get(username=request.user.username)
        receiver_value_designation = HoldsDesignation.objects.filter(user=receiver_value)
        lis = list(receiver_value_designation)
        obj = lis[0].designation

        file_id = create_file(
            uploader=request.user.username,
            uploader_designation=obj,
            receiver=leave_hod,
            receiver_designation="student",
            src_module="otheracademic",
            src_object_id=leave.id,
            file_extra_JSON={"value": 2},
            attached_file=None,
            subject='ug_leave'
        )


        message = "A new leave application"
        otheracademic_notif(request.user, leave_hod, 'ug_leave_hod', leave.id, 'student', message)
        if leave:
            messages.success(request, "You successfully submitted your form")
            
        # return HttpResponseRedirect('/otheracademic/leaveform')


        

class BonafideFormSubmitView(APIView):
    """
    API view to handle Bonafide form submission.
    """

    permission_classes = [IsAuthenticated] 

    def post(self, request):
        # Extract data from the request
        data = request.POST
        file = request.FILES.get('related_document')  # Handle the file if uploaded

        try:
            # Create a new BonafideFormTableUpdated instance and save it to the database
            bonafide_form = BonafideFormTableUpdated.objects.create(
                student_names=f"{request.user.first_name} {request.user.last_name}",
                roll_nos=request.user.extrainfo,  # Assuming `extrainfo` is the user's ExtraInfo instance
                branch_types=data.get('branch'),
                semester_types=data.get('semester'),
                purposes=data.get('purpose'),
                date_of_applications=date.today(),
                download_file=file.name if file else "unavailable",
                approve=False,  # Default value
                reject=False,  # Default value
            )

            # Notify the academic admin about the new bonafide application
            acad_admin_des_id = Designation.objects.get(name="acadadmin")
            user_ids = HoldsDesignation.objects.filter(designation_id=acad_admin_des_id.id).values_list('user_id', flat=True)

            if user_ids.exists():
                bonafide_receiver = User.objects.get(id=user_ids[0])
                message = "A new Bonafide application has been submitted."
                otheracademic_notif(
                    request.user, 
                    bonafide_receiver, 
                    'bonafide', 
                    bonafide_form.id, 
                    'student', 
                    message
                )

            return Response(
                {"message": "Your bonafide form has been successfully submitted."},
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        


 

 

class FetchPendingBonafideRequests(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Fetch Bonafide requests where both approve and reject are False (unseen requests)
        pending_bonafides = BonafideFormTableUpdated.objects.filter(approve=False, reject=False)
        
        # Prepare response data
        data = [
            {
                "id": bonafide.id,
                "rollNo": bonafide.roll_nos_id,  # Assuming roll_no is a field in ExtraInfo
                "name": bonafide.student_names,
                "details": {
                    "purpose": bonafide.purposes,
                    "dateOfApplication": bonafide.date_of_applications,
                    "semester": bonafide.semester_types,
                },
            }
            for bonafide in pending_bonafides
        ]
        
        return Response(data)



 

 

class UpdateBonafideStatus(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Get the lists of approved and rejected bonafide request IDs from the request body
        approved_bonafides_ids = request.data.get('approvedBonafides', [])
        rejected_bonafides_ids = request.data.get('rejectedBonafides', [])

        # Update the approve/reject status based on the provided lists
        if approved_bonafides_ids:
           BonafideFormTableUpdated.objects.filter(id__in=approved_bonafides_ids).update(approve=True, reject=False)

        if rejected_bonafides_ids:
            BonafideFormTableUpdated.objects.filter(id__in=rejected_bonafides_ids).update(approve=False, reject=True)

        return Response({"message": "Bonafide statuses updated successfully."})



class GetBonafideStatus(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Get roll number and username from the request
        roll_no = request.data.get("roll_no")
        username = request.data.get("username")

        # Check if roll number and username are provided
        if not roll_no or not username:
            return Response(
                {"error": "Roll number and username are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Query bonafide forms for the given roll number
            bonafide_requests = BonafideFormTableUpdated.objects.filter(roll_nos_id=roll_no)
            
            # Manually format the response data
            response_data = [
                {
                    "rollNo": bonafide.roll_nos_id,
                    "name": bonafide.student_names,
                    "branch": bonafide.branch_types,
                    "semester": bonafide.semester_types,
                    "purpose": bonafide.purposes,
                    "dateApplied": bonafide.date_of_applications.strftime("%Y-%m-%d") if bonafide.date_of_applications else None,
                    "status": (
                        "Approved" if bonafide.approve else "Rejected" if bonafide.reject else "Pending"
                    ),
                }
                for bonafide in bonafide_requests
            ]

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": "An error occurred while fetching bonafide status.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


            return Response({'message': 'Form submitted successfully', 'bonafide_id': bonafide.id}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AssistantshipFormSubmitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.POST
        try:
            # Log received data for debugging
            print("Received data:", data)

            # Parse dates using datetime.strptime()
            try:
                date_from = datetime.strptime(data.get('date_from'), '%Y-%m-%d').date()
                date_to = datetime.strptime(data.get('date_to'), '%Y-%m-%d').date()
            except ValueError:
                return Response({"error": "Invalid date format. Please use YYYY-MM-DD."}, status=400)

            # Validate dates
            if not date_from or not date_to or date_from > date_to:
                return Response({"error": "Invalid date range."}, status=400)

            # Validate HOD user
            hod_user = User.objects.filter(username=data.get('hod')).first()
            if not hod_user:
                return Response({"error": "HOD username not found."}, status=400)

            # Create form
            assistantship_form = AssistantshipClaimFormStatusUpd.objects.create(
                roll_no=request.user.extrainfo,
                student_name=f"{request.user.first_name} {request.user.last_name}",
                discipline=data.get('discipline'),
                dateFrom=date_from,
                dateTo=date_to,
                bank_account=data.get('bank_account_no'),
                student_signature="apple",
                dateApplied=datetime.strptime(data.get('date_applied'), '%Y-%m-%d').date(),
                ta_supervisor=data.get('ta_supervisor'),
                thesis_supervisor=data.get('thesis_supervisor'),
                hod=data.get('hod'),
                applicability=data.get('applicability'),
                TA_approved=False,
                TA_rejected=False,
                Ths_approved=False,
                Ths_rejected=False,
                HOD_approved=False,
                HOD_rejected=False,
                Acad_approved=False,
                Acad_rejected=False,
            )

            # Notify HOD
            otheracademic_notif(
                request.user,
                hod_user,
                "assistantship_form",
                assistantship_form.id,
                "student",
                "A new Assistantship Claim Form has been submitted.",
            )

            return Response({"message": "Form submitted successfully."}, status=201)

        except Exception as e:
            print("Error occurred:", e)  # Log error for debugging
            return Response({"error": "An unexpected error occurred."}, status=500)








 

class DeptAdminUpdateAssistantshipStatus(APIView):
    """
    API view to handle assistantship status updates and send notifications to the HOD.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request): 
        # Extract data from the request
        approved_requests = request.data.get("approvedRequests", [])
        rejected_requests = request.data.get("rejectedRequests", [])

        try:
            # Update approved requests
            approved_forms = AssistantshipClaimFormStatusUpd.objects.filter(id__in=approved_requests)
            approved_forms.update(TA_approved=True, TA_rejected=False)

            # Send notifications for approved forms
            for form in approved_forms:
                try:
                    hod_des_id = Designation.objects.get(name="hod")  # Fetch HOD designation
                    hod_user_ids = HoldsDesignation.objects.filter(
                        designation_id=hod_des_id.id,
                        working=request.user.extrainfo.department
                    ).values_list('user_id', flat=True)

                    if hod_user_ids.exists():
                        hod_user = User.objects.get(id=hod_user_ids[0])
                        message = (
                            f"A new Assistantship request has been approved by the TA and is "
                        )
                        otheracademic_notif(
                            request.user, 
                            hod_user, 
                            "assistantship", 
                            form.id, 
                            "hod", 
                            message
                        )
                except Exception as e:
                    print(f"Notification error for form {form.id}: {str(e)}")

            # Update rejected requests
            AssistantshipClaimFormStatusUpd.objects.filter(id__in=rejected_requests).update(
                TA_approved=False, TA_rejected=True
            )

            return Response(
                {"message": "Assistantship statuses updated successfully, HOD notified for approved requests."},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": f"Failed to update assistantship statuses: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )




 
  

class DeptAdminFetchPendingAssistantshipRequests(APIView):
    """
    Fetch all pending assistantship requests.
    """

    def get(self, request, *args, **kwargs):
        try:
            # Fetch pending forms
            pending_forms = AssistantshipClaimFormStatusUpd.objects.filter(
                TA_approved=False, TA_rejected=False
            )

            # Serialize the data
            data = []
            for form in pending_forms:
                try:
                    data.append({
                        "id": form.id,
                        "roll_no": form.roll_no_id,
                        "student_name": form.student_name,
                        "discipline": form.discipline,
                        "dateFrom": form.dateFrom,
                        "dateTo": form.dateTo,
                        "ta_supervisor": form.ta_supervisor,
                        "thesis_supervisor": form.thesis_supervisor,
                        "applicability": form.applicability,
                    })
                except AttributeError as e:
                    # Log problematic entries
                    print(f"Error serializing form ID {form.id}: {e}")
                    continue

            return Response(data, status=200)

        except Exception as e:
            # Return detailed error message for debugging
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=500
            )


class HodFetchPendingAssistantshipRequests(APIView):
    """
    Fetch all pending assistantship requests where TA is approved and HOD is not approved.
    """

    def get(self, request, *args, **kwargs):
        try:
            # Fetch pending forms where TA is approved and HOD is not approved
            pending_forms = AssistantshipClaimFormStatusUpd.objects.filter(
                TA_approved=True,  # TA has approved
                HOD_approved=False  # HOD has not approved
            )

            # Serialize the data
            data = []
            for form in pending_forms:
                try:
                    data.append({
                        "id": form.id,
                        "roll_no": form.roll_no_id,
                        "student_name": form.student_name,
                        "discipline": form.discipline,
                        "dateFrom": form.dateFrom,
                        "dateTo": form.dateTo,
                        "ta_supervisor": form.ta_supervisor,
                        "thesis_supervisor": form.thesis_supervisor,
                        "applicability": form.applicability,
                    })
                except AttributeError as e:
                    # Log problematic entries
                    print(f"Error serializing form ID {form.id}: {e}")
                    continue

            return Response(data, status=200)

        except Exception as e:
            # Return detailed error message for debugging
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=500
            )


class HodUpdateAssistantshipStatus(APIView):
    """
    API view to handle HOD approval/rejection of assistantship requests and notify the academic admin.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Extract data from the request
        data = request.data
        approved_requests = data.get('approvedRequests', [])
        rejected_requests = data.get('rejectedRequests', [])

        try:
            # Approve forms
            approved_forms = AssistantshipClaimFormStatusUpd.objects.filter(id__in=approved_requests)
            approved_forms.update(HOD_approved=True, HOD_rejected=False)

            # Notify academic admin for approved requests
            acad_admin_des_id = Designation.objects.get(name="acadadmin")
            acad_admin_user_ids = HoldsDesignation.objects.filter(
                designation_id=acad_admin_des_id.id
            ).values_list('user_id', flat=True)

            for form in approved_forms:
                try:
                    if acad_admin_user_ids.exists():
                        acad_admin_user = User.objects.get(id=acad_admin_user_ids[0])
                        message = (
                            f"The Assistantship request for {form.student_name} "
                            f"has been approved by the HOD and is forwarded for final review."
                        )
                        otheracademic_notif(
                             request.user,
                            acad_admin_user,
                            "assistantship",
                             form.id,
                            "hod",
                           "The Assistantship request for {form.student_name} ",
                        )
                except Exception as e:
                    print(f"Notification error for form {form.id}: {str(e)}")

            # Reject forms
            rejected_forms = AssistantshipClaimFormStatusUpd.objects.filter(id__in=rejected_requests)
            rejected_forms.update(HOD_approved=False, HOD_rejected=True)

            return Response(
                {"message": "HOD actions recorded successfully. Academic Admin notified for approved requests."},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        


class AcadAdminFetchPendingAssistantshipRequests(APIView):
    """
    Fetch all pending assistantship requests where TA and HOD have approved but Acad Admin has not approved/rejected.
    """
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access

    def get(self, request, *args, **kwargs):
        try:
            # Fetch pending forms where both TA and HOD are approved, but Acad Admin has not taken action
            pending_forms = AssistantshipClaimFormStatusUpd.objects.filter(
                TA_approved=True,  # TA has approved
                HOD_approved=True,  # HOD has approved
                Acad_approved=False,  # Acad Admin has not approved
                Acad_rejected=False  # Acad Admin has not rejected
            )

            # Serialize the data
            data = []
            for form in pending_forms:
                try:
                    data.append({
                        "id": form.id,
                        "roll_no": form.roll_no_id,
                        "student_name": form.student_name,
                        "discipline": form.discipline,
                        "dateFrom": form.dateFrom.strftime("%Y-%m-%d"),
                        "dateTo": form.dateTo.strftime("%Y-%m-%d"),
                        "ta_supervisor": form.ta_supervisor,
                        "thesis_supervisor": form.thesis_supervisor,
                        "applicability": form.applicability,
                    })
                except AttributeError as e:
                    # Log problematic entries
                    print(f"Error serializing form ID {form.id}: {e}")
                    continue

            return Response(data, status=200)

        except Exception as e:
            # Return detailed error message for debugging
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=500
            )



class AcadAdminUpdateAssistantshipStatus(APIView):
    """
    API view to handle Academic Admin's approval/rejection of assistantship requests.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Extract data from the request
        data = request.data
        approved_requests = data.get('approvedRequests', [])
        rejected_requests = data.get('rejectedRequests', [])

        try:
            # Approve forms
            AssistantshipClaimFormStatusUpd.objects.filter(id__in=approved_requests).update(
                Acad_approved=True,
                Acad_rejected=False
            )

            # Reject forms
            AssistantshipClaimFormStatusUpd.objects.filter(id__in=rejected_requests).update(
                Acad_approved=False,
                Acad_rejected=True
            )

            return Response(
                {"message": "Academic Admin actions recorded successfully."},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )




class GetAssistantshipStatus(APIView):
    """
    API to fetch the assistantship status of a student.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        roll_no = request.data.get("roll_no")

        if not roll_no:
            return Response(
                {"error": "roll_no is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Fetch all forms for the student
            forms = AssistantshipClaimFormStatusUpd.objects.filter(roll_no=roll_no)

            if not forms.exists():
                return Response(
                    {"message": "No assistantship forms found for the given roll number."},
                    status=status.HTTP_200_OK
                )

            # Serialize the data
            data = []
            for form in forms:
                data.append({
                    "id": form.id,
                    "dateApplied": form.dateApplied,
                    "applicability": form.applicability,
                    "ta_supervisor": form.ta_supervisor,
                    "thesis_supervisor": form.thesis_supervisor,
                    "Acad_approved": form.Acad_approved,
                    "Acad_rejected": form.Acad_rejected,
                    "HOD_rejected": form.HOD_rejected,
                    "TA_rejected": form.TA_rejected,
                })

            return Response(data, status=status.HTTP_200_OK)

        except Exception as e:
            import traceback
            print(traceback.format_exc())  # Log detailed error for debugging
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
