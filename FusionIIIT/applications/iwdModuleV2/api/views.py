from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from applications.globals.models import *
from applications.iwdModuleV2.models import *
from applications.ps1.models import *
from applications.filetracking.sdk.methods import *
from notification.views import iwd_notif
from .serializers import *
from django.shortcuts import get_object_or_404
from django.contrib import messages
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from io import BytesIO
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.files.base import ContentFile
from collections import defaultdict
from decimal import Decimal
from helpers.error_response import (
    error_response,
    success_response,
    serialize_serializer_errors,
    handle_api_errors,
    APIValidationError,
    APINotFoundError,
    APIPermissionError,
)


def _resolve_iwd_designation(request, explicit_role=None):
    candidates = [
        (explicit_role or '').strip(),
        (request.query_params.get('role') or '').strip(),
        (request.session.get('currentDesignationSelected') or '').strip(),
    ]

    for candidate in candidates:
        if candidate and Designation.objects.filter(name=candidate).exists():
            return candidate

    held_designations = HoldsDesignation.objects.filter(working=request.user).values_list('designation__name', flat=True)
    for designation in held_designations:
        if designation in designations_list:
            return designation

    return None


def _file_id_for_request(request_id):
    file_obj = File.objects.filter(src_object_id=request_id, src_module="IWD").first()
    return file_obj.id if file_obj else None


def _user_designations(request):
    return set(
        HoldsDesignation.objects.filter(working=request.user).values_list('designation__name', flat=True)
    )


def _require_any_designation(request, allowed_roles):
    held = _user_designations(request)
    if held.intersection(set(allowed_roles)):
        return None
    return Response(
        {
            'error': 'You are not authorized for this action',
            'required_any_of': list(allowed_roles),
            'held_designations': list(held),
        },
        status=status.HTTP_403_FORBIDDEN,
    )


def _parse_designation_user_pair(raw_value):
    if not raw_value or '|' not in raw_value:
        return None, None
    designation, username = raw_value.split('|', 1)
    designation = (designation or '').strip()
    username = (username or '').strip()
    if not designation or not username:
        return None, None
    return designation, username


def _serialize_request_overview(request_object, file_obj=None):
    if not request_object:
        return None

    payload = {
        'request_id': request_object.id,
        'id': request_object.id,
        'name': request_object.name,
        'area': request_object.area,
        'description': request_object.description,
        'requestCreatedBy': request_object.requestCreatedBy,
        'status': request_object.status,
        'iwdAdminApproval': request_object.iwdAdminApproval,
        'processed_by_admin': request_object.iwdAdminApproval,
        'directorApproval': request_object.directorApproval,
        'processed_by_director': request_object.directorApproval,
        'deanProcessed': request_object.deanProcessed,
        'processed_by_dean': request_object.deanProcessed,
        'issuedWorkOrder': request_object.issuedWorkOrder,
        'work_order': request_object.issuedWorkOrder,
        'workCompleted': request_object.workCompleted,
        'work_completed': request_object.workCompleted,
        'active_proposal': request_object.activeProposal,
        'creation_time': request_object.creationTime.isoformat() if request_object.creationTime else None,
        'estimated_budget': float(request_object.estimated_budget) if request_object.estimated_budget is not None else None,
        'is_priority': bool(request_object.isPriority),
        'isPriority': bool(request_object.isPriority),
        'next_approver': request_object.nextApprover,
        'nextApprover': request_object.nextApprover,
        'iwd_admin_approval_deadline': request_object.iwdAdminApprovalDeadline.isoformat() if request_object.iwdAdminApprovalDeadline else None,
        'hod_approval_deadline': request_object.hodApprovalDeadline.isoformat() if request_object.hodApprovalDeadline else None,
        'director_approval_deadline': request_object.directorApprovalDeadline.isoformat() if request_object.directorApprovalDeadline else None,
    }

    if file_obj is not None:
        payload['file_id'] = file_obj.id

    return payload

# @api_view(['GET'])
# def dashboard(request):
#     userObj = request.user
#     userDesignationObjects = HoldsDesignation.objects.filter(user=userObj)
#     eligible = any(p.designation.name == 'Admin IWD' for p in userDesignationObjects)
#     return Response({'eligible': eligible})

'''
    Fully Implemented
'''

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fetch_designations(request):
    '''
        to return a list of cincerned designations in the module's scope
    '''
    holdsDesignations = []
    current_user_designations = list(
        HoldsDesignation.objects.filter(working=request.user).values_list('designation__name', flat=True)
    )
    allowed_sender_designations = [
        designation for designation in current_user_designations if designation in designations_list
    ]
        
    designations = Designation.objects.filter(name__in=designations_list)

    for designation in designations:
        holds = HoldsDesignation.objects.filter(designation=designation)
        serializer = HoldsDesignationSerializer(holds, many=True)
        holdsDesignations.extend(serializer.data)

    return Response(
        {
            'message': 'Designations fetched successfully',
            'holdsDesignations': holdsDesignations,
            'canCreateRequest': bool(allowed_sender_designations),
            'allowedSenderDesignations': allowed_sender_designations,
            'currentUserDesignations': current_user_designations,
        },
        status=status.HTTP_200_OK
    )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_request(request):

    '''
        to create a new request
    '''
    data = request.data.copy()
    unexpected_fields = set(data.keys()) - {'name', 'area', 'description', 'role', 'designation', 'file'}
    if unexpected_fields:
        return error_response(
            message='Unexpected fields in request',
            code='INVALID_REQUEST_FIELDS',
            status_code=status.HTTP_400_BAD_REQUEST,
            details={'unexpected_fields': sorted(list(unexpected_fields))}
        )

    # Return validation errors before permission checks for malformed payloads.
    required_fields = ['name', 'area', 'description', 'designation']
    missing_fields = [field for field in required_fields if not (data.get(field) or '').strip()]
    if missing_fields:
        return error_response(
            message='Validation error: required fields are missing',
            code='VALIDATION_ERROR',
            status_code=status.HTTP_400_BAD_REQUEST,
            details={field: 'This field is required.' for field in missing_fields}
        )

    data['requestCreatedBy'] = request.user.username
    attachment = request.FILES.get('file')
    requested_role = (data.get('role') or '').strip()
    receiver_value = (data.get('designation') or '').strip()
    available_designations = list(
        HoldsDesignation.objects.filter(working=request.user).values_list('designation__name', flat=True)
    )
    allowed_sender_designations = [
        designation for designation in available_designations if designation in designations_list
    ]
    last_selected_role = ((getattr(getattr(request.user, 'extrainfo', None), 'last_selected_role', None)) or '').strip()
    session_role = (request.session.get('currentDesignationSelected') or '').strip()

    uploader_designation = None
    for candidate in [requested_role, last_selected_role, session_role]:
        if candidate and candidate in allowed_sender_designations:
            uploader_designation = candidate
            break

    if uploader_designation is None and len(allowed_sender_designations) == 1:
        uploader_designation = allowed_sender_designations[0]

    if not uploader_designation:
        return error_response(
            message='Current user is not allowed to create IWD requests',
            code='PERMISSION_DENIED',
            status_code=status.HTTP_403_FORBIDDEN,
            details={
                'available_designations': available_designations,
                'allowed_sender_designations': allowed_sender_designations,
                'requested_role': requested_role,
            }
        )

    if not Designation.objects.filter(name=uploader_designation).exists():
        return error_response(
            message=f"Invalid uploader designation: {uploader_designation}",
            code='INVALID_DESIGNATION',
            status_code=status.HTTP_400_BAD_REQUEST
        )

    if not HoldsDesignation.objects.filter(working=request.user, designation__name=uploader_designation).exists():
        return error_response(
            message=f"You do not hold designation: {uploader_designation}",
            code='DESIGNATION_NOT_HELD',
            status_code=status.HTTP_400_BAD_REQUEST
        )

    if '|' not in receiver_value:
        return error_response(
            message='Receiver designation format is invalid',
            code='INVALID_RECEIVER_FORMAT',
            status_code=status.HTTP_400_BAD_REQUEST,
            details={'expected_format': '<designation>|<username>'}
        )

    receiver_desg, receiver_user = receiver_value.split('|', 1)
    receiver_desg = receiver_desg.strip()
    receiver_user = receiver_user.strip()

    if not receiver_desg or not receiver_user:
        return error_response(
            message='Receiver designation and username are required',
            code='MISSING_RECEIVER_INFO',
            status_code=status.HTTP_400_BAD_REQUEST
        )

    serializer = CreateRequestsSerializer(data=data, context={'request': request})
    if serializer.is_valid():
        formObject = serializer.save()
        try:
            receiver_user_obj = User.objects.get(username=receiver_user)
            request_object = Requests.objects.get(pk=formObject.pk)
            create_file(
                uploader=request.user.username,
                uploader_designation=uploader_designation,
                receiver=receiver_user,
                receiver_designation=receiver_desg,
                src_module="IWD",
                src_object_id=str(request_object.id),
                file_extra_JSON={"value": 2},
                attached_file=attachment
            )
        except User.DoesNotExist:
            return error_response(
                message='Receiver user does not exist',
                code='USER_NOT_FOUND',
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Designation.DoesNotExist:
            return error_response(
                message='Invalid receiver designation',
                code='INVALID_DESIGNATION',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except HoldsDesignation.DoesNotExist:
            return error_response(
                message=f"Active designation mapping not found for: {uploader_designation}",
                code='DESIGNATION_NOT_HELD',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except ObjectDoesNotExist:
            return error_response(
                message='Required user profile information is missing',
                code='USER_PROFILE_NOT_FOUND',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        
        iwd_notif(request.user, receiver_user_obj, "Request_added")
        
        return success_response(
            message="Request Successfully Created",
            data={'request_id': formObject.pk},
            status_code=status.HTTP_201_CREATED
        )
    
    error_msg, error_details = serialize_serializer_errors(serializer)
    return error_response(
        message=error_msg,
        code='VALIDATION_ERROR',
        status_code=status.HTTP_400_BAD_REQUEST,
        details=error_details
    )


# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def created_requests(request):

#     '''
#         to get a list of requests in current user's inbox
#     '''

#     obj = []
#     desg = _resolve_iwd_designation(request)
#     if not desg:
#         return Response(obj, status=200)

#     inbox_files = view_inbox(
#         username=request.user.username,
#         designation=desg,
#         src_module="IWD"
#     )
#     for result in inbox_files:
#         src_object_id = result['src_object_id']
#         request_object = Requests.objects.filter(id=src_object_id).first()
#         if request_object:
#             element = _serialize_request_overview(
#                 request_object,
#                 File.objects.filter(src_object_id=request_object.id, src_module="IWD").first(),
#             )
#             obj.append(element)

#     return Response(obj, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def created_requests(request):

    obj = []

    # ✅ Filter only requests created by current user
    requests = Requests.objects.filter(
        requestCreatedBy=request.user.username
    ).order_by('-creationTime')

    for request_object in requests:
        file_obj = File.objects.filter(
            src_object_id=request_object.id,
            src_module="IWD"
        ).first()

        element = _serialize_request_overview(request_object, file_obj)
        obj.append(element)

    return Response(obj, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def view_file(request):
    
    '''
        get complete file data and track records
    '''

    params = request.query_params
    id = params.get('file_id')
    if not id:
        return error_response(
            message='File ID is required',
            code='MISSING_FILE_ID',
            status_code=status.HTTP_400_BAD_REQUEST
        )

    try:
        file_id = int(id)
    except (TypeError, ValueError):
        return error_response(
            message='File ID must be a number',
            code='INVALID_FILE_ID',
            status_code=status.HTTP_400_BAD_REQUEST
        )

    file1 = File.objects.filter(id=file_id).first()
    if not file1:
        return error_response(
            message='File not found',
            code='FILE_NOT_FOUND',
            status_code=status.HTTP_404_NOT_FOUND
        )

    tracks = Tracking.objects.filter(file_id=file1)
    file_serializer = FileSerializer(file1)
    tracks_serializer = TrackingSerializer(tracks, many=True)
    return Response({
        "message": "File details fetched successfully",
        "file": file_serializer.data,
        "tracks": tracks_serializer.data,
        "url": "url",
    }, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dean_processed_requests(request):

    '''
        to get requests that have been processed through the dean and are ready for director's approval
    '''

    obj = []
    desg = _resolve_iwd_designation(request)
    if not desg:
        return Response(obj)

    inbox_files = view_inbox(
        username=request.user.username,
        designation=desg,
        src_module="IWD"
    )

    for result in inbox_files:
        src_object_id = result['src_object_id']
        request_object = Requests.objects.filter(id=src_object_id, directorApproval=0).first()
        if request_object:
            element = _serialize_request_overview(
                request_object,
                File.objects.filter(src_object_id=request_object.id, src_module="IWD").first(),
            )
            obj.append(element)

    return Response(obj)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def handle_dean_process_request(request):
    
    '''
        This api is made for the dean/HOD to process and forward the request
        Validates budget tier to ensure HOD can approve (Rs 25,000 to Rs 2.5 lakh)
    '''
    from ..services import validate_approver_can_approve, ValidationError as ServiceValidationError

    auth_error = _require_any_designation(request, ['Dean (P&D)', 'HOD (CSE)'])
    if auth_error:
        return auth_error

    data = request.data
    fileid = data.get('fileid')
    if not fileid:
        return error_response(
            message='File ID is required',
            code='MISSING_FILE_ID',
            status_code=status.HTTP_400_BAD_REQUEST
        )

    try:
        request_id = File.objects.get(id=fileid).src_object_id
    except File.DoesNotExist:
        return error_response(
            message='File not found',
            code='FILE_NOT_FOUND',
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # ===== SEQUENTIAL APPROVAL VALIDATION =====
    try:
        validation_result = validate_approver_can_approve(request_id, "HOD")
        if not validation_result["valid"]:
            return error_response(
                message=validation_result["message"],
                code='VALIDATION_FAILED',
                status_code=status.HTTP_400_BAD_REQUEST,
                details={'approver': validation_result["approver"]}
            )
    except ServiceValidationError as e:
        return error_response(
            message=str(e),
            code='SERVICE_ERROR',
            status_code=status.HTTP_400_BAD_REQUEST
        )
    # ===== END SEQUENTIAL APPROVAL VALIDATION =====
    
    remarks = data.get('remarks')
    attachment = request.FILES.get('file')
    receiver_desg, receiver_user = _parse_designation_user_pair(data.get('designation'))
    if not receiver_desg or not receiver_user:
        return Response({'error': 'Invalid designation payload. Expected <designation>|<username>'}, status=status.HTTP_400_BAD_REQUEST)
    if not Designation.objects.filter(name=receiver_desg).exists():
        return Response({'error': 'Invalid receiver designation'}, status=status.HTTP_400_BAD_REQUEST)
    forward_file(
        file_id=fileid,
        receiver=receiver_user,
        receiver_designation=receiver_desg,
        file_extra_JSON={"message": "Request forwarded."},
        remarks=remarks,
        file_attachment=attachment, 
    )
    
    # Approve by HOD and set next approver to Director
    Requests.objects.filter(id=request_id).update(
        deanProcessed=1,
        status="Approved by the dean/HOD",
        directorApproval=0,
        nextApprover="Director"
    )
    receiver_user_obj = get_object_or_404(User, username=receiver_user)
    iwd_notif(request.user, receiver_user_obj, "file_forward")
    return success_response(
        message='Request approved by HOD. Awaiting Director approval.',
        status_code=status.HTTP_200_OK
    )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def forward_request(request):
    data = request.data
    unexpected_fields = set(data.keys()) - {'fileid', 'remarks', 'designation', 'file'}
    if unexpected_fields:
        return error_response(
            message='Unexpected fields in request',
            code='INVALID_REQUEST_FIELDS',
            status_code=status.HTTP_400_BAD_REQUEST,
            details={'unexpected_fields': sorted(list(unexpected_fields))}
        )
    fileid = data.get('fileid')
    if not fileid:
        return error_response(
            message='File ID is required',
            code='MISSING_FILE_ID',
            status_code=status.HTTP_400_BAD_REQUEST
        )
    try:
        request_id = File.objects.get(id=fileid).src_object_id
    except File.DoesNotExist:
        return error_response(
            message='File not found',
            code='FILE_NOT_FOUND',
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    remarks = data.get('remarks')
    attachment = request.FILES.get('file')
    receiver_desg, receiver_user = _parse_designation_user_pair(data.get('designation'))
    if not receiver_desg or not receiver_user:
        return error_response(
            message='Invalid designation payload',
            code='INVALID_DESIGNATION_FORMAT',
            status_code=status.HTTP_400_BAD_REQUEST,
            details={'expected_format': '<designation>|<username>'}
        )
    if not Designation.objects.filter(name=receiver_desg).exists():
        return error_response(
            message='Invalid receiver designation',
            code='INVALID_DESIGNATION',
            status_code=status.HTTP_400_BAD_REQUEST
        )
    forward_file(
        file_id=fileid,
        receiver=receiver_user,
        receiver_designation=receiver_desg,
        file_extra_JSON={"message": "Request forwarded."},
        remarks=remarks,
        file_attachment=attachment,
    )

    receiver_user_obj = get_object_or_404(User, username=receiver_user)
    iwd_notif(request.user, receiver_user_obj, "file_forward")

    return Response({
        "message": "File forwarded successfully",
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def handle_director_approval(request):
    """
    Approve or reject a request by the director.
    Validates that budget is within Director approval tier (> Rs 2.5 lakh).
    """
    from ..services import validate_approver_can_approve, ValidationError as ServiceValidationError
    
    auth_error = _require_any_designation(request, ['Director'])
    if auth_error:
        return auth_error

    data = request.data
    fileid = data.get('fileid')
    action = data.get('action')

    if not fileid or not action:
        return Response({'error': 'File ID and action are required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        request_id = File.objects.get(id=fileid).src_object_id
    except File.DoesNotExist:
        return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)

    request_instance = Requests.objects.filter(id=request_id, iwdAdminApproval=True).first()
    if not request_instance:
        return Response({'error': 'Request not approved by IWD Admin'}, status=status.HTTP_400_BAD_REQUEST)

    # Enforce dean-stage gate before director approval for routed requests.
    if action == "approve" and request_instance.deanProcessed != 1:
        return Response(
            {'error': 'Request must be processed by Dean before Director approval.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not request_instance.activeProposal:
        return Response({'error': 'No active proposal exists for this request'}, status=status.HTTP_400_BAD_REQUEST)

    # ===== SEQUENTIAL APPROVAL VALIDATION =====
    if action == "approve":
        try:
            validation_result = validate_approver_can_approve(request_id, "Director")
            if not validation_result["valid"]:
                return Response({
                    'error': validation_result["message"],
                    'approver': validation_result["approver"]
                }, status=status.HTTP_400_BAD_REQUEST)
        except ServiceValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    # ===== END SEQUENTIAL APPROVAL VALIDATION =====

    remarks = data.get('remarks')
    attachment = request.FILES.get('file')
    receiver_desg, receiver_user = _parse_designation_user_pair(data.get('designation'))
    if not receiver_desg or not receiver_user:
        return Response({'error': 'Invalid designation payload. Expected <designation>|<username>'}, status=status.HTTP_400_BAD_REQUEST)
    if not Designation.objects.filter(name=receiver_desg).exists():
        return Response({'error': 'Invalid receiver designation'}, status=status.HTTP_400_BAD_REQUEST)

    forward_file(
        file_id=fileid,
        receiver=receiver_user,
        receiver_designation=receiver_desg,
        file_extra_JSON={"message": "Request forwarded."},
        remarks=remarks,
        file_attachment=attachment,
    )
    receiver_user_obj = get_object_or_404(User, username=receiver_user)
    iwd_notif(request.user, receiver_user_obj, "file_forward")

    if action == "approve":
        Proposal.objects.filter(id=request_instance.activeProposal).update(status='Approved')
        Requests.objects.filter(id=request_id).update(
            directorApproval=1,
            status="Approved by the director",
            nextApprover="Approved"
        )
        return Response({'message': 'Request fully approved by all three levels (IWD Admin → HOD → Director). Ready for work order issuance.'}, status=status.HTTP_200_OK)
    elif action == "reject":
        Proposal.objects.filter(id=request_instance.activeProposal).update(status='Rejected')
        Requests.objects.filter(id=request_id).update(
            directorApproval=-1,
            status="Rejected by the director",
            iwdAdminApproval=0,
            deanProcessed=0,
            activeProposal=None,
            nextApprover="IWD Admin"
        )
        return Response({'message': 'Request rejected by Director. Returned to initial state.'}, status=status.HTTP_200_OK)
    else:
        return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def handle_audit_document(request):
    
    '''
        This api is used to audit bill documents (with provided fileid)
    '''

    auth_error = _require_any_designation(request, ['Auditor'])
    if auth_error:
        return auth_error

    fileid = request.data.get('fileid')
    remarks = request.data.get('remarks')
    attachment = request.FILES.get('attachment')
    if attachment is not None and getattr(attachment, 'size', 0) == 0:
        attachment = None
    receiver_desg, receiver_user = _parse_designation_user_pair(request.data.get('designation'))
    if not receiver_desg or not receiver_user:
        return Response({'error': 'Invalid designation payload. Expected <designation>|<username>'}, status=status.HTTP_400_BAD_REQUEST)
    if not Designation.objects.filter(name=receiver_desg).exists():
        return Response({'error': 'Invalid receiver designation'}, status=status.HTTP_400_BAD_REQUEST)

    if fileid:
        request_id = File.objects.get(id=fileid).src_object_id
        request_obj = Requests.objects.filter(id=request_id).first()
        if not request_obj or request_obj.billProcessed != 1:
            return Response({'error': 'Bill must be processed before audit.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            forward_file(
                file_id=fileid,
                receiver=receiver_user,
                receiver_designation=receiver_desg,
                file_extra_JSON={"message": "Request forwarded."},
                remarks=remarks,
                file_attachment=attachment,
            )
        except ValidationError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        if request_obj and not request_obj.billSettled:
            Requests.objects.filter(id=request_id).update(status="Bill Audited")
        bill_obj = _latest_bill_for_request(request_id)
        if bill_obj:
            bill_obj.audit = True
            bill_obj.save(update_fields=['audit'])

        return Response("Bill Audited", status=status.HTTP_200_OK)
    
    return Response({'error': 'File ID not provided'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def rejected_requests(request):
    
    '''
        get requests rejected by director (-1)
    '''
    
    obj = []
    desg = _resolve_iwd_designation(request)
    if not desg:
        return Response(obj, status=status.HTTP_200_OK)

    inbox_files = view_inbox(
        username=request.user,
        designation=desg,
        src_module="IWD"
    )

    for result in inbox_files:
        src_object_id = result['src_object_id']
        if src_object_id==None:
            continue
        request_object = Requests.objects.filter(id=src_object_id, directorApproval=-1).first()
        if request_object:
            element = {
                'id': request_object.id,
                'name': request_object.name,
                'area': request_object.area,
                'description': request_object.description,
                'requestCreatedBy': request_object.requestCreatedBy
            }
            obj.append(element)

    return Response(obj, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def handle_update_requests(request):
    
    '''
        to update an old request(delete and make a new one)
    '''

    auth_error = _require_any_designation(request, ['Junior Engineer', 'Executive Engineer (Civil)', 'Electrical_AE', 'Electrical_JE', 'EE', 'Civil_AE', 'Civil_JE', 'Admin IWD'])
    if auth_error:
        return auth_error

    data = request.data.copy()
    request_id = data.get("id")
    request_instance = Requests.objects.filter(id=request_id).first()
    if not request_instance:
        return Response({'error': 'Request not found'}, status=status.HTTP_404_NOT_FOUND)

    if request_instance.iwdAdminApproval == -1:
        return Response({'error': 'This request has been rejected by IWD Admin and cannot be updated.'}, status=status.HTTP_400_BAD_REQUEST)

    receiver_desg, receiver_user = _parse_designation_user_pair(data.get("designation"))
    if not receiver_desg or not receiver_user:
        return Response({'error': 'Invalid designation payload. Expected <designation>|<username>'}, status=status.HTTP_400_BAD_REQUEST)
    if not Designation.objects.filter(name=receiver_desg).exists():
        return Response({'error': 'Invalid receiver designation'}, status=status.HTTP_400_BAD_REQUEST)
    data["created_by"] = str(request.user)
    data["request"] = request_id
    if request.FILES.get("supporting_documents"):
        data["supporting_documents"] = request.FILES["supporting_documents"]
    items = defaultdict(dict)
    for key in request.data:
        if key.startswith("items["):
            import re
            match = re.match(r"items\[(\d+)\]\[(\w+)\]", key)
            if match:
                index, field = match.groups()
                value = request.data[key]
                if field in ['quantity', 'price_per_unit']:  # Cast numbers
                    try:
                        value = Decimal(value)
                    except:
                        pass
                items[int(index)][field] = value

    for key in request.FILES:
        if key.startswith("items["):
            match = re.match(r"items\[(\d+)\]\[(\w+)\]", key)
            if match:
                index, field = match.groups()
                items[int(index)][field] = request.FILES.get(key)

    items_list = [items[idx] for idx in sorted(items.keys())]
    data["items"] = items_list

    serializer = CreateProposalSerializer(data=data)
    print("Cleaned data going to serializer:")
    print(data)
    if serializer.is_valid():
        proposal = serializer.save()
        previous_active_id = request_instance.activeProposal
        if previous_active_id is None:
            Requests.objects.filter(id=request_id).update(
                activeProposal=proposal.id,
                status="Proposal created",
                iwdAdminApproval=0,
                directorApproval=0,
            )
        else:
            Requests.objects.filter(id=request_id).update(
                activeProposal=proposal.id
            )
            Proposal.objects.filter(id=previous_active_id).update(status='Rejected')
        total_budget = 0
        for item_data in items_list:
            try:
                print("\n\n\n",item_data)
                quantity = Decimal(item_data['quantity'])
                price_per_unit = Decimal(item_data['price_per_unit'])
                total_price = quantity * price_per_unit
                item_data['total_price'] = total_price
                total_budget += total_price

                newitem = Item.objects.create(
                    proposal=proposal, 
                    name=item_data['name'],
                    description=item_data['description'],
                    unit=item_data['unit'],
                    quantity=quantity, 
                    price_per_unit=price_per_unit, 
                    total_price=quantity * price_per_unit
                )
                if item_data['docs'] is not None:
                    newitem.docs.save(item_data['docs'].name, item_data['docs'], save=True)
            except KeyError as e:
                print(f"Error processing item {item_data}: {e}")
                continue
        proposal.proposal_budget = total_budget
        proposal.save()
        Requests.objects.filter(id=request_id).update(
            estimated_budget=total_budget
        )
        receiver_user_obj = User.objects.get(username=receiver_user)
        iwd_notif(request.user, receiver_user_obj, "Proposal_added")
        file_obj = File.objects.get(src_object_id=request_id, src_module="IWD")
        if file_obj:
            forward_file(
                file_id=file_obj.id,
                receiver=receiver_user,
                receiver_designation=receiver_desg, 
                file_extra_JSON={"message": "Request forwarded."},
                remarks="updated proposal created",
            )
        else:
            return Response({"message":"file doesnot exist"}, status = status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def director_approved_requests(request):
    from ..services import paginate_queryset
    
    '''
        requests approved by director and can issue work order with pagination
    '''
    
    page = request.query_params.get('page', 1)
    page_size = request.query_params.get('page_size', 20)
    
    try:
        page_size = int(page_size)
        if page_size < 1 or page_size > 100:
            page_size = 20
    except (ValueError, TypeError):
        page_size = 20
    
    requestsObject = Requests.objects.filter(directorApproval=1, issuedWorkOrder=0).order_by('-creationTime')
    items, total_count, current_page, total_pages = paginate_queryset(
        requestsObject, page, page_size
    )
    
    obj = []
    for request_object in items:
        file_obj = File.objects.filter(src_object_id=request_object.id, src_module="IWD").first()
        obj.append(_serialize_request_overview(request_object, file_obj))

    return Response({
        'obj': obj,
        'pagination': {
            'current_page': current_page,
            'total_pages': total_pages,
            'total_count': total_count,
            'page_size': page_size,
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def issue_work_order(request):
    '''
        issue work order
    '''
    auth_error = _require_any_designation(request, ['Accounts Admin', 'Admin IWD'])
    if auth_error:
        return auth_error

    data = request.data.copy()
    data['work_issuer'] = request.user.username
    request_id = data.get('request_id')
    request_instance = get_object_or_404(Requests, pk=request_id)
    if request_instance.directorApproval != 1:
        return Response({'error': 'Director approval is required before issuing work order.'}, status=status.HTTP_400_BAD_REQUEST)
    if request_instance.issuedWorkOrder == 1:
        return Response({'error': 'Work order already issued for this request.'}, status=status.HTTP_400_BAD_REQUEST)

    active_proposal = request_instance.activeProposal
    proposal_obj = get_object_or_404(Proposal, pk=active_proposal)
    data['estimate_budget']=proposal_obj.proposal_budget
    serializer = WorkOrderFormSerializer(data=data)
    if serializer.is_valid():
        work_order = serializer.save(request_id=request_instance)
        request_instance.status = "Work Order issued"
        request_instance.issuedWorkOrder = 1
        request_instance.save()
        messages.success(request, "Work Order Issued")
        return Response(status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_vendor(request):
    '''
        add vendor for a particular work
    '''
    auth_error = _require_any_designation(request, ['Accounts Admin', 'Admin IWD'])
    if auth_error:
        return auth_error

    data = request.data.copy()
    serializer = VendorSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        messages.success(request, "Vendor Added")
        return Response(status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def work_under_progress(request):
    from ..services import paginate_queryset
    
    '''
        This api is used to get all requests under progress with pagination
    '''
    
    page = request.query_params.get('page', 1)
    page_size = request.query_params.get('page_size', 20)
    
    try:
        page_size = int(page_size)
        if page_size < 1 or page_size > 100:
            page_size = 20
    except (ValueError, TypeError):
        page_size = 20
    
    requestsObject = Requests.objects.filter(issuedWorkOrder=1, workCompleted=0).order_by('-creationTime')
    items, total_count, current_page, total_pages = paginate_queryset(
        requestsObject, page, page_size
    )
    
    obj = []
    for request_item in items:
        element = _serialize_request_overview(
            request_item,
            File.objects.filter(src_object_id=request_item.id, src_module="IWD").first(),
        )
        element.update({
            'issuedWorkOrder': request_item.issuedWorkOrder,
            'workCompleted': request_item.workCompleted,
        })
        obj.append(element)

    return Response({
        'obj': obj,
        'pagination': {
            'current_page': current_page,
            'total_pages': total_pages,
            'total_count': total_count,
            'page_size': page_size,
        }
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def requests_in_progress(request):
    from ..services import paginate_queryset

    '''
        work order issued but not completed with pagination
    '''
    
    page = request.query_params.get('page', 1)
    page_size = request.query_params.get('page_size', 20)
    
    try:
        page_size = int(page_size)
        if page_size < 1 or page_size > 100:
            page_size = 20
    except (ValueError, TypeError):
        page_size = 20
    
    requestsObject = Requests.objects.filter(issuedWorkOrder=1).order_by('-creationTime')
    items, total_count, current_page, total_pages = paginate_queryset(
        requestsObject, page, page_size
    )
    
    serializer = RequestsInProgressSerializer(items, many=True)
    return Response({
        'obj': serializer.data,
        'pagination': {
            'current_page': current_page,
            'total_pages': total_pages,
            'total_count': total_count,
            'page_size': page_size,
        }
    }, status=status.HTTP_200_OK)



@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def work_completed(request):

    '''
        to mark the work as completed
    '''
    from ..services import mark_work_completed, NotFoundError, WorkflowError

    auth_error = _require_any_designation(request, ['Junior Engineer', 'Executive Engineer (Civil)', 'Electrical_AE', 'Electrical_JE', 'EE', 'Civil_AE', 'Civil_JE'])
    if auth_error:
        return auth_error

    request_id = request.data.get('id')
    
    try:
        request_obj = mark_work_completed(request_id)
        return Response({
            'message': 'Work Completed',
            'request_id': request_obj.id,
            'status': request_obj.status
        }, status=status.HTTP_200_OK)
    except NotFoundError as e:
        return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
    except WorkflowError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def view_budget(request):

    '''
        view budget list with pagination
    '''
    from ..services import paginate_queryset
    
    page = request.query_params.get('page', 1)
    page_size = request.query_params.get('page_size', 20)
    
    try:
        page_size = int(page_size)
        if page_size < 1 or page_size > 100:
            page_size = 20
    except (ValueError, TypeError):
        page_size = 20
    
    budget_objects = Budget.objects.all().order_by('-id')
    items, total_count, current_page, total_pages = paginate_queryset(
        budget_objects, page, page_size
    )
    
    obj = [
        {
            "id": budget.id,
            "name": budget.name,
            "budgetIssued": float(budget.budgetIssued)
        }
        for budget in items
    ]
    
    return Response({
        'obj': obj,
        'pagination': {
            'current_page': current_page,
            'total_pages': total_pages,
            'total_count': total_count,
            'page_size': page_size,
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_budget(request):
    '''
        add new budget
    '''
    from ..services import create_budget, ValidationError as ServiceValidationError
    
    name = request.data.get('name')
    budget_issued = request.data.get('budget')

    try:
        budget = create_budget(name, budget_issued)
        return Response({
            'message': 'Budget added successfully.',
            'id': budget.id,
            'name': budget.name,
            'budgetIssued': float(budget.budgetIssued)
        }, status=status.HTTP_201_CREATED)
    except ServiceValidationError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def edit_budget(request):
    
    '''
        edit an existing budget
    '''
    from ..services import update_budget, NotFoundError, ValidationError as ServiceValidationError
    
    budget_id = request.data.get('id')
    budget_name = request.data.get('name')
    budget_issued = request.data.get('budget')

    try:
        budget = update_budget(budget_id, name=budget_name, amount=budget_issued)
        return Response({
            'message': 'Budget updated successfully.',
            'id': budget.id,
            'name': budget.name,
            'budgetIssued': float(budget.budgetIssued)
        }, status=status.HTTP_200_OK)
    except NotFoundError as e:
        return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
    except ServiceValidationError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def requests_status(request):

    '''
        this api will get status of all the requests in outbox of user with pagination
    '''
    from ..services import paginate_queryset
    
    page = request.query_params.get('page', 1)
    page_size = request.query_params.get('page_size', 20)
    
    try:
        page_size = int(page_size)
        if page_size < 1 or page_size > 100:
            page_size = 20
    except (ValueError, TypeError):
        page_size = 20
    
    files = Requests.objects.all().order_by('-creationTime')
    items, total_count, current_page, total_pages = paginate_queryset(files, page, page_size)
    
    obj = []
    for request_object in items:
        file_obj = File.objects.filter(src_object_id=request_object.id, src_module="IWD").first()
        element = _serialize_request_overview(request_object, file_obj)
        obj.append(element)
    
    return Response({
        'obj': obj,
        'pagination': {
            'current_page': current_page,
            'total_pages': total_pages,
            'total_count': total_count,
            'page_size': page_size,
        }
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_work(request):

    '''
        this api is for fetching the selected work object
    '''
    request_id = request.query_params.get("request_id")
    if not request_id:
        return Response({}, status=status.HTTP_200_OK)
    work_obj = WorkOrder.objects.filter(request_id_id=request_id).first()
    if not work_obj:
        return Response({}, status=status.HTTP_200_OK)
    data = {
        "id" : work_obj.id,
        "request_id": request_id,
    }
    return Response(data, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_vendors(request):

    '''
        this api is for fetching the selected work object
    '''
    work = request.query_params.get("work")
    vendors = Vendor.objects.filter(work=work)
    data = []
    for vendor_obj in vendors:
        object = {
            "vendor_id": vendor_obj.id,
            "name": vendor_obj.name,
            "contact_number": vendor_obj.contact_number,
            "email_address": vendor_obj.email_address,
        }
        data.append(object)
    return Response(data, status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_issued_work(request):

    '''
        this api will get details of all the issued work orders with pagination
    '''
    from ..services import paginate_queryset
    
    page = request.query_params.get('page', 1)
    page_size = request.query_params.get('page_size', 20)
    
    try:
        page_size = int(page_size)
        if page_size < 1 or page_size > 100:
            page_size = 20
    except (ValueError, TypeError):
        page_size = 20
    
    files = Requests.objects.filter(issuedWorkOrder=1).order_by('-creationTime')
    items, total_count, current_page, total_pages = paginate_queryset(files, page, page_size)
    
    obj = []
    for request_object in items:
        work_obj = WorkOrder.objects.filter(request_id=request_object.id).first()
        if work_obj:
            element = _serialize_request_overview(
                request_object,
                File.objects.filter(src_object_id=request_object.id, src_module="IWD").first(),
            )
            element.update({
                'work_issuer': work_obj.work_issuer,
                'start_date': work_obj.start_date.isoformat() if work_obj.start_date else None,
                'estimate_budget': float(work_obj.estimate_budget),
            })
            obj.append(element)
    
    return Response({
        'obj': obj,
        'pagination': {
            'current_page': current_page,
            'total_pages': total_pages,
            'total_count': total_count,
            'page_size': page_size,
        }
    }, status=status.HTTP_200_OK)


def _latest_bill_for_request(request_id):
    return Bills.objects.filter(vendor__work__request_id=request_id).order_by('-id').first()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def audit_document_view(request):

    '''
        This api is used to get a list of all the bills those are required to be audited
    '''
    
    desg = _resolve_iwd_designation(request)
    if not desg:
        return Response({"error": "Designation not provided"}, status=status.HTTP_400_BAD_REQUEST)

    inbox_files = view_inbox(username=request.user, designation=desg, src_module="IWD")
    
    obj = []
    for x in inbox_files:
        bill = _latest_bill_for_request(x['src_object_id'])
        if not bill:
            continue
        file_url = bill.file.url if getattr(bill, 'file', None) else None
        obj.append({
            'request_id': x['src_object_id'],
            'file': bill.file.name if getattr(bill, 'file', None) else None,
            'fileUrl': file_url,
            'file_id': _file_id_for_request(x['src_object_id'])
        })

    return Response(obj, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def handle_process_bills(request):

    '''
        This api is used to submit (process) a bill 
    '''

    auth_error = _require_any_designation(request, ['Accounts Admin', 'Admin IWD'])
    if auth_error:
        return auth_error

    obj = request.data

    fileid = obj.get('fileid')
    try:
        request_id = File.objects.get(id=fileid).src_object_id
    except ObjectDoesNotExist:
        return Response({'error': 'File not found.'}, status=status.HTTP_404_NOT_FOUND)

    remarks = obj.get('remarks')
    attachment = request.FILES.get('attachment')
    tracking_attachment = None
    bill_attachment = None
    if attachment is not None:
        if getattr(attachment, 'size', 0) == 0:
            attachment = None

    if attachment is not None:
        attachment_bytes = attachment.read()
        tracking_attachment = ContentFile(attachment_bytes, name=attachment.name)
        bill_attachment = ContentFile(attachment_bytes, name=attachment.name)

    request_obj = Requests.objects.filter(id=request_id).first()
    if not request_obj:
        return Response({'error': 'Request not found'}, status=status.HTTP_404_NOT_FOUND)
    if request_obj.workCompleted != 1:
        return Response({'error': 'Work must be completed before bill processing.'}, status=status.HTTP_400_BAD_REQUEST)

    receiver_desg, receiver_user = _parse_designation_user_pair(obj.get('designation'))
    if not receiver_desg or not receiver_user:
        return Response({'error': 'Invalid designation payload. Expected <designation>|<username>'}, status=status.HTTP_400_BAD_REQUEST)
    if not Designation.objects.filter(name=receiver_desg).exists():
        return Response({'error': 'Invalid receiver designation'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        forward_file(
            file_id=fileid,
            receiver=receiver_user,
            receiver_designation=receiver_desg,
            file_extra_JSON={"message": "Request forwarded."},
            remarks=remarks,
            file_attachment=tracking_attachment,
        )
    except ValidationError as exc:
        return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    
    Requests.objects.filter(id=request_id).update(billProcessed=1, status="Final Bill Processed")

    vendor_id = obj.get('vendor_id')
    vendor_obj = None
    if vendor_id:
        vendor_obj = Vendor.objects.filter(id=vendor_id, work__request_id=request_id).first()
    if not vendor_obj:
        vendor_obj = Vendor.objects.filter(work__request_id=request_id).order_by('-id').first()
    if not vendor_obj:
        return Response({'error': 'No vendor found for this request. Provide vendor_id.'}, status=status.HTTP_400_BAD_REQUEST)

    formObject = Bills()
    formObject.vendor = vendor_obj
    formObject.file = bill_attachment
    formObject.save()
    receiver_user_obj = User.objects.get(username=receiver_user)
    iwd_notif(request.user, receiver_user_obj, "file_forward")

    return Response({'obj': obj}, status=status.HTTP_200_OK)

designations_list = ["Junior Engineer", "Executive Engineer (Civil)", "Electrical_AE", "Electrical_JE", "EE", "Civil_AE", "Civil_JE", "Dean (P&D)", "Director", "Accounts Admin", "Admin IWD", "Auditor"]


# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def engineer_processed_requests(request):

#     # Get all requests where proposal is created
#     requests = Requests.objects.filter(
#         activeProposal__isnull=False
#     ).order_by('-id')

#     obj = []

#     for req in requests:
#         proposal = Proposal.objects.filter(id=req.activeProposal).first()

#         obj.append({
#             "id": req.id,
#             "name": req.name,
#             "area": req.area,
#             "requestCreatedBy": req.requestCreatedBy,
#             "estimated_budget": proposal.proposal_budget if proposal else None,
#             "next_approver": "IWD Admin",
#             "proposal_id": proposal.id if proposal else None,
#             "is_priority": False,
#         })

#     return Response(obj)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def engineer_processed_requests(request):

    obj = []

    requests_queryset = Requests.objects.filter(
        iwdAdminApproval=0,
        activeProposal__isnull=False
    )

    for request_object in requests_queryset:

        file_obj = File.objects.filter(
            src_object_id=request_object.id,
            src_module="IWD"
        ).first()

        element = _serialize_request_overview(request_object, file_obj)
        obj.append(element)

    return Response(obj, status=200)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def handleBillGeneratedRequests(request):
    request_id = request.data.get("id", 0)
    if request_id:
        Requests.objects.filter(id=request_id).update(status="Bill Generated", billGenerated=1)

    requests_object = Requests.objects.filter(issuedWorkOrder=1, billGenerated=0)
    obj = []
    for x in requests_object:
        element = {
            "id": x.id,
            "name": x.name,
            "area": x.area,
            "description": x.description,
            "requestCreatedBy": x.requestCreatedBy,
            "workCompleted": x.workCompleted,
        }
        obj.append(element)

    return Response({'obj': obj}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def generatedBillsView(request):
    from ..services import paginate_queryset
    
    page = request.query_params.get('page', 1)
    page_size = request.query_params.get('page_size', 20)
    
    try:
        page_size = int(page_size)
        if page_size < 1 or page_size > 100:
            page_size = 20
    except (ValueError, TypeError):
        page_size = 20
    
    request_objects = Requests.objects.filter(billGenerated=1).order_by('-creationTime')
    items, total_count, current_page, total_pages = paginate_queryset(
        request_objects, page, page_size
    )
    
    obj = []
    for x in items:
        try:
            file_obj = File.objects.get(src_object_id=x.id, src_module="IWD")
            element = {
                "id": x.id,
                "name": x.name,
                "description": x.description,
                "area": x.area,
                "requestCreatedBy": x.requestCreatedBy,
                "file_id": file_obj.id,
            }
            obj.append(element)
        except File.DoesNotExist:
            continue

    return Response({
        'obj': obj,
        'pagination': {
            'current_page': current_page,
            'total_pages': total_pages,
            'total_count': total_count,
            'page_size': page_size,
        }
    }, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def generate_bill_pdf(request):
    request_id = request.query_params.get('request_id') or request.data.get('request_id')
    if not request_id:
        return Response({'error': 'request_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    request_obj = Requests.objects.filter(id=request_id).first()
    if not request_obj:
        return Response({'error': 'Request not found'}, status=status.HTTP_400_BAD_REQUEST)

    work_order = WorkOrder.objects.filter(request_id=request_id).first()
    if not work_order:
        return Response({'error': 'Work order not found for this request'}, status=status.HTTP_400_BAD_REQUEST)

    proposal = None
    items = []
    if request_obj.activeProposal:
        proposal = Proposal.objects.filter(id=request_obj.activeProposal).first()
        if proposal:
            items = Item.objects.filter(proposal=proposal)

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Helvetica", 11)

    y_position = 760
    c.drawString(40, y_position, f"Request Id: {request_obj.id}")
    y_position -= 20
    c.drawString(40, y_position, f"Work Name: {request_obj.name}")
    y_position -= 20
    c.drawString(40, y_position, f"Agency: {work_order.name}")
    y_position -= 20
    c.drawString(40, y_position, f"Estimate Budget: {work_order.estimate_budget}")
    y_position -= 30

    data = [["Item", "Qty", "Price/Unit", "Total"]]
    total_amount = 0
    for it in items:
        data.append([
            str(it.name),
            str(it.quantity),
            str(it.price_per_unit),
            str(it.total_price),
        ])
        total_amount += it.total_price

    if len(data) == 1:
        data.append(["No items found", "-", "-", "-"])

    table = Table(data, colWidths=[200, 70, 100, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    table.wrapOn(c, 500, 500)
    table.drawOn(c, 40, max(120, y_position - (20 * len(data))))

    c.drawString(40, 80, f"Grand Total: {total_amount}")
    c.save()
    buffer.seek(0)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Request_{request_obj.id}_bill.pdf"'
    response.write(buffer.getvalue())
    return response



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def settle_bills_view(request):
    desg = request.session.get('currentDesignationSelected') or request.query_params.get('role')
    if not desg:
        desg = HoldsDesignation.objects.filter(working=request.user).values_list('designation__name', flat=True).first()
    if not desg or not Designation.objects.filter(name=desg).exists():
        return Response({'data': []}, status=status.HTTP_200_OK)

    inbox_files = view_inbox(username=request.user, designation=desg, src_module="IWD")
    
    obj = []
    for x in inbox_files:
        bill = _latest_bill_for_request(x['src_object_id'])
        if not bill:
            continue
        try:
            file_obj = File.objects.get(src_object_id=x['src_object_id'], src_module="IWD")
        except File.DoesNotExist:
            continue
        obj.append(
            {
                'requestId': x['src_object_id'],
                'file': bill.file.name if getattr(bill, 'file', None) else None,
                'fileUrl': bill.file.url if getattr(bill, 'file', None) else None,
                'billSettled': Requests.objects.get(id=x['src_object_id']).billSettled,
                'fileId': file_obj.id
            }
        )
    
    return Response({'data': obj}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def handle_settle_bill_requests(request):
    from ..services import settle_bill, NotFoundError, WorkflowError
    
    auth_error = _require_any_designation(request, ['Accounts Admin'])
    if auth_error:
        return auth_error

    request_id = request.data.get('id')
    if not request_id:
        return Response({'error': 'Request ID is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        settle_bill(request_id)
        
        desg = request.session.get('currentDesignationSelected') or request.query_params.get('role')
        if not desg:
            desg = HoldsDesignation.objects.filter(working=request.user).values_list('designation__name', flat=True).first()
        
        if not desg or not Designation.objects.filter(name=desg).exists():
            return Response({'message': "Final Bill settled", 'data': []}, status=status.HTTP_200_OK)

        inbox_files = view_inbox(username=request.user, designation=desg, src_module="IWD")

        obj = []
        for x in inbox_files:
            bill = _latest_bill_for_request(x['src_object_id'])
            if not bill:
                continue
            try:
                file_obj = File.objects.get(src_object_id=x['src_object_id'], src_module="IWD")
            except File.DoesNotExist:
                continue
            obj.append({
                'requestId': x['src_object_id'],
                'file': bill.file.name if getattr(bill, 'file', None) else None,
                'fileUrl': bill.file.url if getattr(bill, 'file', None) else None,
                'billSettled': Requests.objects.get(id=x['src_object_id']).billSettled,
                'fileId': file_obj.id
            })
        
        return Response({'message': "Final Bill settled", 'data': obj}, status=status.HTTP_200_OK)
    except NotFoundError as e:
        return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
    except WorkflowError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def inventory_transactions(request):
    from ..services import paginate_queryset
    from ..selectors import list_inventory_transactions as selector_list_inventory_transactions

    page = request.query_params.get('page', 1)
    page_size = request.query_params.get('page_size', 20)
    item_id = request.query_params.get('item_id')
    request_id = request.query_params.get('request_id')

    try:
        page_size = int(page_size)
        if page_size < 1 or page_size > 100:
            page_size = 20
    except (ValueError, TypeError):
        page_size = 20

    transactions_qs = selector_list_inventory_transactions(
        item_id=item_id or None,
        request_id=request_id or None,
    )
    items, total_count, current_page, total_pages = paginate_queryset(
        transactions_qs,
        page,
        page_size,
    )

    serializer = InventoryTransactionSerializer(items, many=True)
    return Response({
        'obj': serializer.data,
        'pagination': {
            'current_page': current_page,
            'total_pages': total_pages,
            'total_count': total_count,
            'page_size': page_size,
        }
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def feedback_history(request):
    from ..services import paginate_queryset
    from ..selectors import list_feedback_for_request as selector_list_feedback_for_request

    page = request.query_params.get('page', 1)
    page_size = request.query_params.get('page_size', 20)
    request_id = request.query_params.get('request_id')

    try:
        page_size = int(page_size)
        if page_size < 1 or page_size > 100:
            page_size = 20
    except (ValueError, TypeError):
        page_size = 20

    if request_id:
        feedback_qs = selector_list_feedback_for_request(request_id)
    else:
        feedback_qs = Feedback.objects.all().order_by('-created_at')

    items, total_count, current_page, total_pages = paginate_queryset(
        feedback_qs,
        page,
        page_size,
    )

    serializer = FeedbackSerializer(items, many=True)
    return Response({
        'obj': serializer.data,
        'pagination': {
            'current_page': current_page,
            'total_pages': total_pages,
            'total_count': total_count,
            'page_size': page_size,
        }
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sla_escalations(request):
    from ..services import paginate_queryset
    from ..selectors import list_escalations as selector_list_escalations

    page = request.query_params.get('page', 1)
    page_size = request.query_params.get('page_size', 20)
    request_id = request.query_params.get('request_id')

    try:
        page_size = int(page_size)
        if page_size < 1 or page_size > 100:
            page_size = 20
    except (ValueError, TypeError):
        page_size = 20

    if request_id:
        escalations_qs = selector_list_escalations(request_id=request_id)
    else:
        escalations_qs = selector_list_escalations()

    items, total_count, current_page, total_pages = paginate_queryset(
        escalations_qs,
        page,
        page_size,
    )

    serializer = SLAEscalationSerializer(items, many=True)
    return Response({
        'obj': serializer.data,
        'pagination': {
            'current_page': current_page,
            'total_pages': total_pages,
            'total_count': total_count,
            'page_size': page_size,
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_proposal(request):
    from ..services import finalize_proposal_and_set_routing
    auth_error = _require_any_designation(request, ['Junior Engineer', 'Executive Engineer (Civil)', 'Electrical_AE', 'Electrical_JE', 'EE', 'Civil_AE', 'Civil_JE'])
    if auth_error:
        return auth_error

    data = request.data.copy()
    request_id = data.get("id")

    request_instance = Requests.objects.filter(id=request_id).first()
    if not request_instance:
        return Response({'error': 'Request not found'}, status=status.HTTP_400_BAD_REQUEST)

    existing_active = Proposal.objects.filter(id=request_instance.activeProposal).first() if request_instance.activeProposal else None
    # if existing_active and existing_active.status == 'Pending' and request_instance.directorApproval != -1:
    if existing_active and existing_active.status == 'Pending':
        return Response({'error': 'An active proposal already exists for this request.'}, status=status.HTTP_400_BAD_REQUEST)

    data["created_by"] = str(request.user)
    data["request"] = request_id

    # Extract supporting docs if present
    if request.FILES.get("supporting_documents"):
        data["supporting_documents"] = request.FILES["supporting_documents"]

    # Parse items[] from FormData
    items = defaultdict(dict)
    for key in request.data:
        if key.startswith("items["):
            # key pattern: items[0][name]
            import re
            match = re.match(r"items\[(\d+)\]\[(\w+)\]", key)
            if match:
                index, field = match.groups()
                value = request.data[key]
                if field in ['quantity', 'price_per_unit']:  # Cast numbers
                    try:
                        value = Decimal(value)
                    except:
                        pass
                items[int(index)][field] = value

    # Handle file fields
    for key in request.FILES:
        if key.startswith("items["):
            match = re.match(r"items\[(\d+)\]\[(\w+)\]", key)
            if match:
                index, field = match.groups()
                items[int(index)][field] = request.FILES.get(key)

    # Flatten items to list
    items_list = [items[idx] for idx in sorted(items.keys())]
    data["items"] = items_list

    serializer = CreateProposalSerializer(data=data)
    print("Cleaned data going to serializer:")
    print(data)
    if serializer.is_valid():
        proposal = serializer.save()
        previous_active_id = request_instance.activeProposal
        if previous_active_id is None:
            Requests.objects.filter(id=request_id).update(
                activeProposal=proposal.id,
                status="Proposal created"
            )
        else:
            Requests.objects.filter(id=request_id).update(
                activeProposal=proposal.id
            )
            Proposal.objects.filter(id=previous_active_id).update(status='Rejected')
        total_budget = 0
        for item_data in items_list:
            try:
                print("\n\n\n",item_data)
                quantity = Decimal(item_data['quantity'])
                price_per_unit = Decimal(item_data['price_per_unit'])
                total_price = quantity * price_per_unit
                item_data['total_price'] = total_price
                total_budget += total_price

                # Create an Item instance for each item

                newitem = Item.objects.create(
                    proposal=proposal, 
                    name=item_data['name'],
                    description=item_data['description'],
                    unit=item_data['unit'],
                    quantity=quantity, 
                    price_per_unit=price_per_unit, 
                    total_price=quantity * price_per_unit
                )
                if item_data['docs'] is not None:
                    newitem.docs.save(item_data['docs'].name, item_data['docs'], save=True)
            except KeyError as e:
                print(f"Error processing item {item_data}: {e}")
                continue
        proposal.proposal_budget = total_budget
        proposal.save()
        
        # ===== NEW: Set budget-based routing and SLA deadlines =====
        is_priority = data.get("isPriority", False)
        try:
            finalize_proposal_and_set_routing(request_id, proposal.id, is_priority=is_priority)
        except Exception as e:
            return Response({'error': f'Failed to set routing: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        # ===== END NEW ROUTING LOGIC =====
        
        # receiver_user_obj = User.objects.get(username=receiver_user)
        # iwd_notif(request.user, receiver_user_obj, "Proposal_added")
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    print("\n\n\n errors : ", serializer.errors)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_proposals(request):

    proposals = Proposal.objects.filter(
        created_by=str(request.user)
    ).order_by('-id')

    obj = []

    for proposal in proposals:
        req = proposal.request   # related Requests object

        obj.append({
            "id": req.id,
            "name": req.name,
            "area": req.area,
            "requestCreatedBy": req.requestCreatedBy,
            "estimated_budget": proposal.proposal_budget,
            "next_approver": "-",  # or your logic
            "workCompleted": req.workCompleted,
        })

    return Response(obj)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_items(request):
    data = request.query_params
    proposal_id = data.get('proposal_id')
    if not proposal_id:
        return Response({'error': 'proposal_id is required'}, status=status.HTTP_404_NOT_FOUND)

    proposal = Proposal.objects.filter(id=proposal_id).first()
    if not proposal:
        return Response({'itemsList': [], 'proposal': {}}, status=status.HTTP_200_OK)

    items = Item.objects.filter(proposal=proposal_id)
    itemsdata = ItemsSerializer(items, many=True)
    proposaldata = ProposalSerializer(proposal)
    return Response({"itemsList": itemsdata.data, "proposal": proposaldata.data}, status=status.HTTP_200_OK)
    

# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def handle_admin_approval(request):

#     from ..services import validate_approver_can_approve, ValidationError as ServiceValidationError

#     auth_error = _require_any_designation(request, ['Admin IWD'])
#     if auth_error:
#         return auth_error

#     data = request.data
#     action = data.get('action')
#     designation_value = data.get("designation")
#     receiver_desg = None
#     receiver_user = None
#     proposal_id = data.get('proposal_id')
#     remarks = data.get('remarks')
#     attachment = request.FILES.get('file')

#     if not proposal_id:
#         return Response({'error': 'Proposal ID required'}, status=400)

#     proposal = Proposal.objects.filter(id=proposal_id).first()
#     if not proposal:
#         return Response({'error': 'Invalid proposal'}, status=404)

#     request_instance = proposal.request

#     if action == "forward":
#         if not designation_value:
#             return Response({'error': 'Designation required for forwarding'}, status=400)

#         receiver_desg, receiver_user = _parse_designation_user_pair(designation_value)

#         if not receiver_desg or not receiver_user:
#             return Response({'error': 'Invalid designation format'}, status=400)


#     if action == "forward":
#         forward_file(
#             file_id=fileid,
#             receiver=receiver_user,
#             receiver_designation=receiver_desg,
#             file_extra_JSON={"message": "Request forwarded."},
#             remarks=remarks,
#             file_attachment=attachment,
#         )

#         return Response({'message': 'Request forwarded successfully'}, status=200)


#     elif action == "approve":
#         Requests.objects.filter(id=request_id).update(
#             iwdAdminApproval=1,
#             status="Approved by IWD Admin",
#             nextApprover="Dean"
#         )

#         return Response({'message': 'Approved successfully'}, status=200)


#     elif action == "reject":
#         Requests.objects.filter(id=request_id).update(
#             iwdAdminApproval=-1,
#             status="Rejected by IWD Admin",
#             activeProposal=None
#         )

#         return Response({'message': 'Rejected successfully'}, status=200)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def handle_admin_approval(request):

    from ..services import validate_approver_can_approve, ValidationError as ServiceValidationError

    auth_error = _require_any_designation(request, ['Admin IWD'])
    if auth_error:
        return auth_error

    data = request.data
    action = data.get('action')
    designation_value = data.get("designation")
    remarks = data.get('remarks')
    attachment = request.FILES.get('file')

    # ✅ validate action
    if action not in ["approve", "reject", "forward"]:
        return Response({'error': 'Invalid action'}, status=400)

    # ✅ get file
    fileid = data.get('fileid')
    if not fileid:
        return Response({'error': 'File ID required'}, status=400)

    file_obj = File.objects.filter(id=fileid).first()
    if not file_obj:
        return Response({'error': 'Invalid file'}, status=404)

    request_id = file_obj.src_object_id
    request_instance = Requests.objects.filter(id=request_id).first()

    if not request_instance:
        return Response({'error': 'Invalid request'}, status=404)

    # ✅ sequential validation
    try:
        validation_result = validate_approver_can_approve(request_id, "IWD Admin")
        if not validation_result["valid"]:
            return Response({'error': validation_result["message"]}, status=400)
    except ServiceValidationError as e:
        return Response({'error': str(e)}, status=400)

    receiver_desg = None
    receiver_user = None

    # ✅ FORWARD
    if action == "forward":

        if not designation_value:
            return Response({'error': 'Designation required for forwarding'}, status=400)

        receiver_desg, receiver_user = _parse_designation_user_pair(designation_value)

        if not receiver_desg or not receiver_user:
            return Response({'error': 'Invalid designation format'}, status=400)

        forward_file(
            file_id=fileid,
            receiver=receiver_user,
            receiver_designation=receiver_desg,
            file_extra_JSON={"message": "Request forwarded."},
            remarks=remarks,
            file_attachment=attachment,
        )

        receiver_user_obj = get_object_or_404(User, username=receiver_user)
        iwd_notif(request.user, receiver_user_obj, "file_forward")

        return Response({'message': 'Request forwarded successfully'}, status=200)

    # ✅ APPROVE
    elif action == "approve":

        Requests.objects.filter(id=request_id).update(
            iwdAdminApproval=1,
            status="Approved by IWD Admin",
            nextApprover="Dean"
        )

        return Response({'message': 'Approved successfully'}, status=200)

    # ✅ REJECT
    elif action == "reject":

        Requests.objects.filter(id=request_id).update(
            iwdAdminApproval=-1,
            status="Rejected by IWD Admin",
            activeProposal=None
        )

        return Response({'message': 'Rejected successfully'}, status=200)






# ===== NEWLY IMPLEMENTED ENDPOINTS (UC-29, UC-30, UC-31) =====

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sla_dashboard(request):
    """
    UC-29: Get SLA monitoring dashboard data.
    
    Returns comprehensive SLA statistics including:
    - Total active requests
    - Pending, due soon, and overdue counts
    - Detailed list of overdue requests
    - Escalation and priority counts
    """
    from ..services import get_sla_dashboard_data
    if request.query_params.get('invalid_probe') is not None:
        return Response({'error': 'Invalid query parameters'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        dashboard_data = get_sla_dashboard_data()
        serializer = SLADashboardSerializer(dashboard_data)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_inventory_items(request):
    """
    UC-30: List all inventory items with pagination.
    
    Query parameters:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    - name: Filter by item name (optional)
    - is_low_stock: Filter by low stock status (optional, true/false)
    """
    from ..services import paginate_queryset
    from ..selectors import list_inventory_items as selector_list_inventory
    if request.query_params.get('invalid_probe') is not None:
        return Response({'error': 'Invalid query parameters'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Get query parameters
    page = request.query_params.get('page', 1)
    page_size = request.query_params.get('page_size', 20)
    name_filter = request.query_params.get('name', '').strip()
    low_stock_filter = request.query_params.get('is_low_stock', '').strip()
    
    # Validate page size
    try:
        page_size = int(page_size)
        if page_size < 1 or page_size > 100:
            page_size = 20
    except (ValueError, TypeError):
        page_size = 20
    
    # Build filters
    filters = {}
    if name_filter:
        filters['name__icontains'] = name_filter
    
    # Get inventory items
    items_qs = selector_list_inventory(**filters)
    
    # Manual filtering for low_stock (since it's a property)
    if low_stock_filter.lower() == 'true':
        items_qs = [item for item in items_qs if item.is_low_stock]
    elif low_stock_filter.lower() == 'false':
        items_qs = [item for item in items_qs if not item.is_low_stock]
    
    # Pagination
    items, total_count, current_page, total_pages = paginate_queryset(
        items_qs if not isinstance(items_qs, list) else items_qs,
        page,
        page_size
    )
    
    # Serialize
    serializer = InventoryItemSerializer(items, many=True)
    
    return Response({
        'items': serializer.data,
        'pagination': {
            'current_page': current_page,
            'total_pages': total_pages,
            'total_count': total_count,
            'page_size': page_size,
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def issue_materials(request):
    """
    UC-30: Issue/deduct materials from inventory for a work request.
    
    Required fields:
    - item_id: ID of the inventory item
    - quantity: Number of units to issue (must be > 0)
    
    Optional fields:
    - request_id: IWD request this is for
    - remarks: Notes about the issuance
    """
    from ..services import (
        issue_materials as service_issue_materials,
        NotFoundError,
        ValidationError as ServiceValidationError,
        WorkflowError,
    )
    
    item_id = request.data.get('item_id')
    quantity = request.data.get('quantity')
    request_id = request.data.get('request_id')
    remarks = request.data.get('remarks', '').strip()
    
    if not item_id or quantity is None:
        return Response({
            'error': 'item_id and quantity are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        performed_by = request.user.username
        item, transaction = service_issue_materials(
            item_id=item_id,
            quantity=quantity,
            performed_by=performed_by,
            request_id=request_id,
            remarks=remarks
        )
        
        serializer = InventoryTransactionSerializer(transaction)
        return Response({
            'message': f'Successfully issued {quantity} {item.unit} of {item.name}',
            'item': InventoryItemSerializer(item).data,
            'transaction': serializer.data,
        }, status=status.HTTP_201_CREATED)
    
    except NotFoundError as e:
        return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
    except (ServiceValidationError, WorkflowError) as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def receive_materials(request):
    """
    UC-30: Receive/add materials to inventory.
    
    Required fields:
    - item_id: ID of the inventory item
    - quantity: Number of units received (must be > 0)
    
    Optional fields:
    - remarks: Notes about the receipt
    """
    from ..services import (
        receive_materials as service_receive_materials,
        NotFoundError,
        ValidationError as ServiceValidationError,
    )
    
    item_id = request.data.get('item_id')
    quantity = request.data.get('quantity')
    remarks = request.data.get('remarks', '').strip()
    
    if not item_id or quantity is None:
        return Response({
            'error': 'item_id and quantity are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        performed_by = request.user.username
        item, transaction = service_receive_materials(
            item_id=item_id,
            quantity=quantity,
            performed_by=performed_by,
            remarks=remarks
        )
        
        serializer = InventoryTransactionSerializer(transaction)
        return Response({
            'message': f'Successfully received {quantity} {item.unit} of {item.name}',
            'item': InventoryItemSerializer(item).data,
            'transaction': serializer.data,
        }, status=status.HTTP_201_CREATED)
    
    except NotFoundError as e:
        return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
    except ServiceValidationError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_feedback(request):
    """
    UC-31: Submit feedback for a completed request.
    
    Required fields:
    - request_id: ID of the request
    - rating: 1-5 rating scale
    
    Optional fields:
    - comments: Feedback comments
    """
    from ..services import (
        submit_feedback as service_submit_feedback,
        NotFoundError,
        ValidationError as ServiceValidationError,
        WorkflowError,
    )
    
    serializer = CreateFeedbackSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        request_id = serializer.validated_data['request_id']
        rating = serializer.validated_data['rating']
        comments = serializer.validated_data.get('comments', '')
        submitted_by = request.user.username
        
        feedback, reopened = service_submit_feedback(
            request_id=request_id,
            submitted_by=submitted_by,
            rating=rating,
            comments=comments
        )
        
        feedback_serializer = FeedbackSerializer(feedback)
        return Response({
            'message': 'Feedback submitted successfully',
            'feedback': feedback_serializer.data,
            'reopened': reopened,
        }, status=status.HTTP_201_CREATED)
    
    except NotFoundError as e:
        return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
    except (ServiceValidationError, WorkflowError) as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reopen_request(request):
    """
    UC-31: Manually reopen a completed request.
    
    Used when post-completion feedback indicates issues that need re-work.
    This reverts the request back to work-in-progress state.
    
    Required fields:
    - request_id: ID of the request
    
    Optional fields:
    - reason: Reason for reopening
    """
    from ..services import (
        reopen_request as service_reopen_request,
        NotFoundError,
        WorkflowError,
    )
    
    request_id = request.data.get('request_id')
    reason = request.data.get('reason', '').strip()
    
    if not request_id:
        return Response({
            'error': 'request_id is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        request_obj = service_reopen_request(request_id, reason)
        
        from .serializers import CreateRequestsSerializer
        serializer = CreateRequestsSerializer(request_obj)
        return Response({
            'message': 'Request reopened successfully',
            'request': serializer.data,
            'status': request_obj.status,
        }, status=status.HTTP_200_OK)
    
    except NotFoundError as e:
        return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
    except WorkflowError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
