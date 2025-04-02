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

        # new_tracking = Tracking.objects.create(
        #     file_id=file_id,  # The newly created file object
        #     uploader=request.user.username,
        #     uploader_designation=obj,
        #     receiver=leave_hod,
        #     receive_design=receiver_designation_obj,  # Receiver's designation object
        #     tracking_extra_JSON=file_extra_JSON,  # Additional metadata in JSON format
        #     remarks=f"File with id:{file_id} created by {uploader} and sent to {receiver}"  # Remarks for this tracking event
        # )

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

        # new_tracking = Tracking.objects.create(
        #     file_id=file_id,  # The newly created file object
        #     uploader=request.user.username,
        #     uploader_designation=obj,
        #     receiver=leave_hod,
        #     receive_design=receiver_designation_obj,  # Receiver's designation object
        #     tracking_extra_JSON=file_extra_JSON,  # Additional metadata in JSON format
        #     remarks=f"File with id:{file_id} created by {uploader} and sent to {receiver}"  # Remarks for this tracking event
        # )

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
        files=request.FILES
        try:
            # Log received data for debugging
            print("Received data:", data)
            print("Received FILES:", files)

            # Parse dates using datetime.strptime()
            try:
                date_from = datetime.strptime(data.get('date_from'), '%Y-%m-%d').date()
                date_to = datetime.strptime(data.get('date_to'), '%Y-%m-%d').date()
                date_applied = datetime.strptime(data.get('date_applied'), '%Y-%m-%d').date()
            except ValueError:
                return Response({"error": "Invalid date format. Please use YYYY-MM-DD."}, status=400)

            # Validate dates
            if not date_from or not date_to or date_from > date_to:
                return Response({"error": "Invalid date range."}, status=400)
            #  Check for duplicate form submission
            if AssistantshipClaimFormStatusUpd.objects.filter(
                roll_no=request.user.extrainfo,
                dateFrom=date_from,
                dateTo=date_to
            ).exists():
                return Response({"error": "Form for this period already exists."}, status=400)

            # Validate HOD user
            #hod_user = User.objects.filter(username=data.get('hod')).first()
            #if not hod_user:
             #   return Response({"error": "HOD username not found."}, status=400)
            ta_supervisor_user = User.objects.filter(username=data.get('ta_supervisor')).first()
            if not ta_supervisor_user:
                return Response({"error": "TA Supervisor username not found."}, status=400)

            thesis_supervisor_user = User.objects.filter(username=data.get('thesis_supervisor')).first()
            if not thesis_supervisor_user:
                return Response({"error": "Thesis Supervisor username not found."}, status=400)
            # Handle signature file
            signature_file = files.get('signature')
            if not signature_file:
                return Response({"error": "Signature file is missing."}, status=400)



            # Create form
            assistantship_form = AssistantshipClaimFormStatusUpd.objects.create(
                roll_no=request.user.extrainfo,
                student_name=f"{request.user.first_name} {request.user.last_name}",
                discipline=data.get('discipline'),
                dateFrom=date_from,
                dateTo=date_to,
                bank_account=data.get('bank_account_no'),
                student_signature=signature_file,
                dateApplied=date_applied,
                ta_supervisor=data.get('ta_supervisor'),
                thesis_supervisor=data.get('thesis_supervisor'),
                hod=data.get('hod'),
                applicability=data.get('applicability'),
                
                # Existing approval/rejection fields
                TA_approved=False,
                TA_rejected=False,
                Ths_approved=False,
                Ths_rejected=False,
                HOD_approved=False,
                HOD_rejected=False,
                

                # Newly added approval/rejection fields
                Dean_approved=False,
                Dean_rejected=False,
                Director_approved=False,
                Director_rejected=False,
                AcadAdmin_approved=False,
                AcadAdmin_rejected=False,
            )

            # Notify TA Supervisor
            otheracademic_notif(
                request.user,
                ta_supervisor_user,
                "assistantship_form",
                assistantship_form.id,
                "student",
                "Assistantship form needs your (TA Supervisor) approval."
            )
            # Notify Thesis Supervisor
            otheracademic_notif(
                request.user,
                thesis_supervisor_user,
                "assistantship_form",
                assistantship_form.id,
                "student",
                "Assistantship form needs your (Thesis Supervisor) approval."
            )

            return Response({"message": "Form submitted successfully."}, status=201)

        except Exception as e:
            print("Error occurred:", e)  # Log error for debugging
            return Response({"error": "An unexpected error occurred."},status=500)
        

class TA_SupervisorFetchPendingAssistantshipRequests(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Fetch forms where both TA and Thesis Supervisor have approved but Dept Admin hasn't taken action
            pending_forms = AssistantshipClaimFormStatusUpd.objects.filter(
                TA_approved=False,
                TA_rejected=False
                # Ths_approved=False,
                # Ths_rejected=False    
            )

            response_data = []
            for form in pending_forms:
                response_data.append({
                    "id": form.id,
                    "student_name": form.student_name,
                    "roll_no": form.roll_no.id,
                    "discipline": form.discipline,
                    "dateFrom": form.dateFrom.strftime('%Y-%m-%d'),
                    "dateTo": form.dateTo.strftime('%Y-%m-%d'),
                    "applicability": form.applicability,
                    "dateApplied": form.dateApplied.strftime('%Y-%m-%d'),
                })

            return Response(response_data, status=200)

        except Exception as e:
            return Response({"error": "Error fetching pending forms", "details": str(e)}, status=500)

     
class TA_SupervisorUpdateAssistantshipStatus(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Update assistantship form status based on supervisor approval or rejection."""
        try:
            role ="thesis"  # Expecting 'ta' or 'thesis'
            approved_ids = request.data.get("approvedRequests", [])
            rejected_ids = request.data.get("rejectedRequests", [])

            if not role or role not in ["ta", "thesis"]:
                return Response({"error": "Invalid or missing role parameter. Use 'ta' or 'thesis'."}, status=400)

            if not approved_ids and not rejected_ids:
                return Response({"error": "No forms provided for update."}, status=400)

            # Approving requests
            if role == "thesis":
                AssistantshipClaimFormStatusUpd.objects.filter(id__in=approved_ids).update(TA_approved=True)
                AssistantshipClaimFormStatusUpd.objects.filter(id__in=rejected_ids).update(TA_rejected=True)

            else:
                AssistantshipClaimFormStatusUpd.objects.filter(id__in=approved_ids).update(Ths_approved=True)
                AssistantshipClaimFormStatusUpd.objects.filter(id__in=rejected_ids).update(Ths_rejected=True)

            return Response({"message": "Assistantship statuses updated successfully"}, status=200)

        except Exception as e:
            return Response({"error": "Error updating assistantship status", "details": str(e)}, status=500)

class Ths_SupervisorFetchPendingAssistantshipRequests(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Fetch forms where both TA and Thesis Supervisor have approved but Dept Admin hasn't taken action
            pending_forms = AssistantshipClaimFormStatusUpd.objects.filter(
                Ths_approved=False,
                Ths_rejected=False
                # Ths_approved=False,
                # Ths_rejected=False    
            )

            response_data = []
            for form in pending_forms:
                response_data.append({
                    "id": form.id,
                    "student_name": form.student_name,
                    "roll_no": form.roll_no.id,
                    "discipline": form.discipline,
                    "dateFrom": form.dateFrom.strftime('%Y-%m-%d'),
                    "dateTo": form.dateTo.strftime('%Y-%m-%d'),
                    "applicability": form.applicability,
                    "dateApplied": form.dateApplied.strftime('%Y-%m-%d'),
                })

            return Response(response_data, status=200)

        except Exception as e:
            return Response({"error": "Error fetching pending forms", "details": str(e)}, status=500)

     
class Ths_SupervisorUpdateAssistantshipStatus(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Update assistantship form status based on supervisor approval or rejection."""
        try:
            role ="thesis"  # Expecting 'ta' or 'thesis'
            approved_ids = request.data.get("approvedRequests", [])
            rejected_ids = request.data.get("rejectedRequests", [])

            if not role or role not in ["ta", "thesis"]:
                return Response({"error": "Invalid or missing role parameter. Use 'ta' or 'thesis'."}, status=400)

            if not approved_ids and not rejected_ids:
                return Response({"error": "No forms provided for update."}, status=400)

            # Approving requests
            if role == "ta":
                AssistantshipClaimFormStatusUpd.objects.filter(id__in=approved_ids).update(TA_approved=True)
                AssistantshipClaimFormStatusUpd.objects.filter(id__in=rejected_ids).update(TA_rejected=True)

            else:
                AssistantshipClaimFormStatusUpd.objects.filter(id__in=approved_ids).update(Ths_approved=True)
                AssistantshipClaimFormStatusUpd.objects.filter(id__in=rejected_ids).update(Ths_rejected=True)

            return Response({"message": "Assistantship statuses updated successfully"}, status=200)

        except Exception as e:
            return Response({"error": "Error updating assistantship status", "details": str(e)}, status=500)



class HODFetchPendingAssistantshipRequests(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Fetch forms where both TA and Thesis Supervisor have approved but Dept Admin hasn't taken action
            pending_forms = AssistantshipClaimFormStatusUpd.objects.filter(
                TA_approved=True,
                Ths_approved=True,
                HOD_approved=False,
                HOD_rejected=False
            )

            response_data = []
            for form in pending_forms:
                response_data.append({
                    "id": form.id,
                    "student_name": form.student_name,
                    "roll_no": form.roll_no.id,
                    "discipline": form.discipline,
                    "dateFrom": form.dateFrom.strftime('%Y-%m-%d'),
                    "dateTo": form.dateTo.strftime('%Y-%m-%d'),
                    "applicability": form.applicability,
                    "dateApplied": form.dateApplied.strftime('%Y-%m-%d'),
                })

            return Response(response_data, status=200)

        except Exception as e:
            return Response({"error": "Error fetching pending forms", "details": str(e)}, status=500)

class HODUpdateAssistantshipStatus(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Get the lists of approved and rejected bonafide request IDs from the request body
        approved_hod = request.data.get('approvedRequests', [])
        rejected_hod = request.data.get('rejectedRequests', [])

        # Update the approve/reject status based on the provided lists
        if approved_hod:
           AssistantshipClaimFormStatusUpd.objects.filter(id__in=approved_hod).update(HOD_approved=True, HOD_rejected=False)

        if rejected_hod:
            AssistantshipClaimFormStatusUpd.objects.filter(id__in=rejected_hod).update(HOD_approved=False, HOD_rejected=True)

        return Response({"message": "Bonafide statuses updated successfully."})

class AcadAdminFetchPendingAssistantshipRequests(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        pending_forms = AssistantshipClaimFormStatusUpd.objects.filter(
            TA_approved=True,
             Ths_approved=True,
            HOD_approved=True,
            AcadAdmin_approved=False,
            AcadAdmin_rejected=False
        )

        response_data = [{
            "id": form.id,
            "student_name": form.student_name,
            "roll_no": form.roll_no.id,
            "discipline": form.discipline,
            "dateFrom": form.dateFrom.strftime('%Y-%m-%d'),
            "dateTo": form.dateTo.strftime('%Y-%m-%d'),
            "applicability": form.applicability,
            "dateApplied": form.dateApplied.strftime('%Y-%m-%d'),
        } for form in pending_forms]

        return Response(response_data, status=200)
     
class AcadAdminUpdateAssistantshipStatus(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Get the lists of approved and rejected bonafide request IDs from the request body
        approved_bonafides_ids = request.data.get('approvedRequests', [])
        rejected_bonafides_ids = request.data.get('rejectedRequests', [])

        # Update the approve/reject status based on the provided lists
        if approved_bonafides_ids:
           AssistantshipClaimFormStatusUpd.objects.filter(id__in=approved_bonafides_ids).update(AcadAdmin_approved=True, AcadAdmin_rejected=False)

        if rejected_bonafides_ids:
            AssistantshipClaimFormStatusUpd.objects.filter(id__in=rejected_bonafides_ids).update(AcadAdmin_approved=False, AcadAdmin_rejected=True)

        return Response({"message": "Bonafide statuses updated successfully."})
class DeanAcadFetchPendingAssistantshipRequests(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        pending_forms = AssistantshipClaimFormStatusUpd.objects.filter(
            TA_approved=True,
            Ths_approved=True,
            HOD_approved=True,
            AcadAdmin_approved=True,
            Dean_approved=False,
            Dean_rejected=False
        )

        response_data = [{
            "id": form.id,
            "student_name": form.student_name,
            "roll_no": form.roll_no.id,
            "discipline": form.discipline,
            "dateFrom": form.dateFrom.strftime('%Y-%m-%d'),
            "dateTo": form.dateTo.strftime('%Y-%m-%d'),
            "applicability": form.applicability,
            "dateApplied": form.dateApplied.strftime('%Y-%m-%d'),
        } for form in pending_forms]

        return Response(response_data, status=200)

 
class DeanAcadUpdateAssistantshipStatus(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Get the lists of approved and rejected bonafide request IDs from the request body
        approved_hod = request.data.get('approvedRequests', [])
        rejected_hod = request.data.get('rejectedRequests', [])

        # Update the approve/reject status based on the provided lists
        if approved_hod:
           AssistantshipClaimFormStatusUpd.objects.filter(id__in=approved_hod).update(Dean_approved=True, Dean_rejected=False)

        if rejected_hod:
            AssistantshipClaimFormStatusUpd.objects.filter(id__in=rejected_hod).update(Dean_approved=False, Dean_rejected=True)

        return Response({"message": "Bonafide statuses updated successfully."})
    
class DirectorFetchPendingAssistantshipRequests(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        pending_forms = AssistantshipClaimFormStatusUpd.objects.filter(
            TA_approved=True,
             Ths_approved=True,
            HOD_approved=True,
            AcadAdmin_approved=True,
            Dean_approved=True,
            Director_approved=False,
            Director_rejected=False
        )

        response_data = [{
            "id": form.id,
            "student_name": form.student_name,
            "roll_no": form.roll_no.id,
            "discipline": form.discipline,
            "dateFrom": form.dateFrom.strftime('%Y-%m-%d'),
            "dateTo": form.dateTo.strftime('%Y-%m-%d'),
            "applicability": form.applicability,
            "dateApplied": form.dateApplied.strftime('%Y-%m-%d'),
        } for form in pending_forms]

        return Response(response_data, status=200)
    
class DirectorUpdateAssistantshipStatus(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Get the lists of approved and rejected bonafide request IDs from the request body
        approved_hod = request.data.get('approvedRequests', [])
        rejected_hod = request.data.get('rejectedRequests', [])

        # Update the approve/reject status based on the provided lists
        if approved_hod:
           AssistantshipClaimFormStatusUpd.objects.filter(id__in=approved_hod).update(Director_approved=True, Director_rejected=False)

        if rejected_hod:
            AssistantshipClaimFormStatusUpd.objects.filter(id__in=rejected_hod).update(Director_approved=False,Director_rejected=True)

        return Response({"message": "Bonafide statuses updated successfully."})



"""class GetAssistantshipStatus(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        roll_no = request.data.get("roll_no")
        username = request.data.get("username")

        if not roll_no or not username:
            return Response(
                {"error": "Roll number and username are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            assistantship_requests = AssistantshipClaimFormStatusUpd.objects.filter(roll_no_id=roll_no)

            response_data = []
            for form in assistantship_requests:
                # Check if ANY stage rejected the form
                is_rejected = any([
                    form.Director_rejected,
                    form.Dean_rejected,
                    form.AcadAdmin_rejected,
                    form.HOD_rejected,
                    form.TA_rejected,
                    form.Ths_rejected
                ])

                # If rejected at any stage, status is "Rejected" and cannot be changed later
                if is_rejected:
                    status_text = "Rejected"
                # If Director has approved and no rejections, it's "Approved"
                elif form.Director_approved:
                    status_text = "Approved"
                # Otherwise, it's still "Pending"
                else:
                    status_text = "Pending"

                response_data.append({
                    "rollNo": form.roll_no.id,
                    "name": form.student_name,
                    "discipline": form.discipline,
                    "dateApplied": form.dateApplied.strftime("%Y-%m-%d") if form.dateApplied else None,
                    "bank_account": form.bank_account,
                    "status": status_text,
                })

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": "An error occurred while fetching assistantship status.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
"""

class GetAssistantshipStatus(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        roll_no = request.data.get("roll_no")
        username = request.data.get("username")

        if not roll_no or not username:
            return Response({"error": "Roll number and username are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            assistantship_requests = AssistantshipClaimFormStatusUpd.objects.filter(roll_no_id=roll_no)

            response_data = [{
                "rollNo": form.roll_no.id,
                "name": form.student_name,
                "discipline": form.discipline,
                "dateApplied": form.dateApplied.strftime("%Y-%m-%d") if form.dateApplied else None,
                "bank_account": form.bank_account,
                "status": "Rejected" if any([form.Director_rejected, form.Dean_rejected, form.AcadAdmin_rejected, 
                                             form.HOD_rejected, form.TA_rejected, form.Ths_rejected]) 
                          else "Approved" if form.Director_approved else "Pending",
                "approvalStages": {stage: "Approved" if getattr(form, f"{prefix}_approved") else 
                                          "Rejected" if getattr(form, f"{prefix}_rejected") else "Pending"
                                   for stage, prefix in {
                                       "TA_Supervisor": "TA", "Thesis_Supervisor": "Ths", "HOD": "HOD", 
                                       "Academic_Admin": "AcadAdmin", "Dean_Academic": "Dean", "Director": "Director"
                                   }.items()}
            } for form in assistantship_requests]

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": "An error occurred while fetching assistantship status.", "details": str(e)}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
