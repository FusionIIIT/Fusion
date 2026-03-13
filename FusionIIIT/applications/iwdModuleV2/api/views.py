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
from django.core.exceptions import ObjectDoesNotExist
from collections import defaultdict

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
        return Response(
            {
                'error': 'Current user is not allowed to create IWD requests',
                'available_designations': available_designations,
                'allowed_sender_designations': allowed_sender_designations,
                'requested_role': requested_role,
            },
            status=status.HTTP_403_FORBIDDEN
        )

    if not Designation.objects.filter(name=uploader_designation).exists():
        return Response(
            {'error': f"Invalid uploader designation: {uploader_designation}"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not HoldsDesignation.objects.filter(working=request.user, designation__name=uploader_designation).exists():
        return Response(
            {'error': f"You do not hold designation: {uploader_designation}"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if '|' not in receiver_value:
        return Response(
            {'error': 'Receiver designation format is invalid. Expected <designation>|<username>'},
            status=status.HTTP_400_BAD_REQUEST
        )

    receiver_desg, receiver_user = receiver_value.split('|', 1)
    receiver_desg = receiver_desg.strip()
    receiver_user = receiver_user.strip()

    if not receiver_desg or not receiver_user:
        return Response(
            {'error': 'Receiver designation and username are required'},
            status=status.HTTP_400_BAD_REQUEST
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
            return Response({'error': 'Receiver user does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        except Designation.DoesNotExist:
            return Response({'error': 'Invalid receiver designation'}, status=status.HTTP_400_BAD_REQUEST)
        except HoldsDesignation.DoesNotExist:
            return Response(
                {'error': f"Active designation mapping not found for: {uploader_designation}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        
        iwd_notif(request.user, receiver_user_obj, "Request_added")
        
        return Response({'message': "Request Successfully Created"}, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def created_requests(request):

    '''
        to get a list of requests in current user's inbox
    '''

    params = request.query_params
    obj = []
    inbox_files = view_inbox(
        username=request.user,
        designation=params.get('role'),
        src_module="IWD"
    )
    for result in inbox_files:
        src_object_id = result['src_object_id']
        request_object = Requests.objects.filter(id=src_object_id).first()
        if request_object:
            file_obj = get_object_or_404(File, src_object_id=request_object.id, src_module="IWD")
            element = {
                'request_id': request_object.id,
                'name': request_object.name,
                'area': request_object.area,
                'description': request_object.description,
                'requestCreatedBy': request_object.requestCreatedBy,
                'file_id': file_obj.id,
                'directorApproval': request_object.directorApproval,
                'processed_by_dean': request_object.deanProcessed,
            }
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
    file1 = get_object_or_404(File, id=id)

    tracks = Tracking.objects.filter(file_id=file1)
    file_serializer = FileSerializer(file1)
    tracks_serializer = TrackingSerializer(tracks, many=True)
    return Response({
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
    params = request.query_params
    desg = params.get('role')

    inbox_files = view_inbox(
        username=request.user.username,
        designation=desg,
        src_module="IWD"
    )

    for result in inbox_files:
        src_object_id = result['src_object_id']
        request_object = Requests.objects.filter(id=src_object_id, directorApproval=0).first()
        file_obj = File.objects.get(src_object_id=src_object_id, src_module="IWD")
        if request_object:
            element = {
                'request_id': request_object.id,
                'name': request_object.name,
                'area': request_object.area,
                'description': request_object.description,
                'requestCreatedBy': request_object.requestCreatedBy,
                'file_id': file_obj.id,
                'directorApproval': request_object.directorApproval,
            }
            obj.append(element)

    return Response(obj)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def handle_dean_process_request(request):
    
    '''
        This api is made for the dean to process and forward the request
    '''

    data = request.data
    fileid = data.get('fileid')
    request_id = File.objects.get(id=fileid).src_object_id
    
    remarks = data.get('remarks')
    attachment = request.FILES.get('file')
    receiver_desg, receiver_user = data.get('designation').split('|')
    forward_file(
        file_id=fileid,
        receiver=receiver_user,
        receiver_designation=receiver_desg,
        file_extra_JSON={"message": "Request forwarded."},
        remarks=remarks,
        file_attachment=attachment, 
    )
    
    Requests.objects.filter(id=request_id).update(deanProcessed=1, status="Approved by the dean", directorApproval=0)
    receiver_user_obj = get_object_or_404(User, username=receiver_user)
    iwd_notif(request.user, receiver_user_obj, "file_forward")
    return Response({'message': 'File Forwarded'}, status=200)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def forward_request(request):
    data = request.data
    fileid = data.get('fileid')
    request_id = File.objects.get(id=fileid).src_object_id
    
    remarks = data.get('remarks')
    attachment = request.FILES.get('file')
    receiver_desg, receiver_user = data.get('designation').split('|')
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
    """
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

    if not request_instance.activeProposal:
        return Response({'error': 'No active proposal exists for this request'}, status=status.HTTP_400_BAD_REQUEST)

    remarks = data.get('remarks')
    attachment = request.FILES.get('file')
    receiver_desg, receiver_user = data.get('designation').split('|')

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
        Requests.objects.filter(id=request_id).update(directorApproval=1, status="Approved by the director")
        return Response({'message': 'Request approved by Director'}, status=status.HTTP_200_OK)
    elif action == "reject":
        Requests.objects.filter(id=request_id).update(directorApproval=-1, status="Rejected by the director", iwdAdminApproval=0, activeProposal=None)
        return Response({'message': 'Request rejected by Director'}, status=status.HTTP_200_OK)
    else:
        return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def handle_audit_document(request):
    
    '''
        This api is used to audit bill documents (with provided fileid)
    '''

    fileid = request.data.get('fileid')
    remarks = request.data.get('remarks')
    attachment = request.FILES.get('attachment')
    receiver_desg, receiver_user = request.data['designation'].split('|')

    if fileid:
        request_id = File.objects.get(id=fileid).src_object_id

        forward_file(
            file_id=fileid,
            receiver=receiver_user,
            receiver_designation=receiver_desg,
            file_extra_JSON={"message": "Request forwarded."},
            remarks=remarks,
            file_attachment=attachment,
        )
        
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
    desg = request.query_params.get('role')

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

    data = request.data.copy()
    request_id = data.get("id")
    request_instance = Requests.objects.filter(id=request_id).first()
    if not request_instance:
        return Response({'error': 'Request not found'}, status=status.HTTP_404_NOT_FOUND)

    if request_instance.iwdAdminApproval == -1:
        return Response({'error': 'This request has been rejected by IWD Admin and cannot be updated.'}, status=status.HTTP_403_FORBIDDEN)

    receiver_desg, receiver_user = data.get("designation").split('|')
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
        if request_instance.activeProposal is None:
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
    
    '''
        requests approved by director and can issue work order
    '''

    requestsObject = Requests.objects.filter(directorApproval=1, issuedWorkOrder=0)
    serializer = DirectorApprovedRequestsSerializer(requestsObject, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def issue_work_order(request):
    '''
        issue work order
    '''
    data = request.data.copy()
    data['work_issuer'] = request.user.username
    request_id = data.get('request_id')
    request_instance = get_object_or_404(Requests, pk=request_id)
    active_proposal = request_instance.activeProposal
    proposal_obj = get_object_or_404(Proposal, pk=active_proposal)
    data['estimate_budget']=proposal_obj.proposal_budget
    print(data)
    serializer = WorkOrderFormSerializer(data=data)
    if serializer.is_valid():

        work_order = serializer.save(request_id=request_instance)

        request_instance.status = "Work Order issued"
        request_instance.issuedWorkOrder = 1
        request_instance.save()

        messages.success(request, "Work Order Issued")
        return Response(status=status.HTTP_200_OK)
    print("wow")
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_vendor(request):
    '''
        add vendor for a particular work
    '''
    data = request.data.copy()
    serializer = VendorSerializer(data=data)
    print("test 1\n\n\n\n\n")
    print(serializer)
    if serializer.is_valid():
        print("test 2\n\n\n\n\n")
        serializer.save()
        print("test 3\n\n\n\n\n")
        messages.success(request, "Vendor Added")
        return Response(status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def work_under_progress(request):
    
    '''
        This api is used to get all requests under progress
    '''
    
    obj = []
    requestsObject = Requests.objects.filter(issuedWorkOrder=1, workCompleted=0)
    serializer = WorkUnderProgressSerializer(requestsObject, many=True)
    for result in serializer.data:
        src_object_id = result['id']
        file_obj = File.objects.get(src_object_id=src_object_id, src_module="IWD")
        if file_obj:
            element = {
                'id': result['id'],
                'file_id': file_obj.id,
                'name': result['name'],
                'area': result['area'],
                'description': result['description'],
                'issuedWorkOrder': result['issuedWorkOrder'],
                'workCompleted': result['workCompleted'],
                'requestCreatedBy': result['requestCreatedBy']
            }
            obj.append(element)

    return Response(obj, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def requests_in_progress(request):

    '''
        work order issued but not completed
    '''
    
    requestsObject = Requests.objects.filter(issuedWorkOrder=1)
    serializer = RequestsInProgressSerializer(requestsObject, many=True)
    return Response(serializer.data, status=200)



@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def work_completed(request):

    '''
        to mark the work as completed
    '''

    request_id = request.data.get('id')
    Requests.objects.filter(id=request_id).update(workCompleted=1, status="Work Completed")
    return Response(
        {
            'message': 'Work Completed',
        },
        status=status.HTTP_200_OK
    )



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def view_budget(request):

    '''
        view budget list
    '''

    budget_objects = Budget.objects.all()
    obj = []

    for x in budget_objects:
        element = {
            "id": x.id,
            "name": x.name,
            "budgetIssued": x.budgetIssued
        }
        obj.append(element)
    
    return Response({'obj': obj}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_budget(request):
    '''
        add new budget
    '''
    name = request.data.get('name')
    budget_issued = request.data.get('budget')

    if name and budget_issued:
        formObject = Budget(name=name, budgetIssued=budget_issued)
        formObject.save()
        return Response({'message': 'Budget added successfully.'}, status=status.HTTP_201_CREATED)
    else:
        return Response({'error': 'Name and budget are required.'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def edit_budget(request):
    
    '''
        edit an existing budget
    '''
    
    budget_id = request.data.get('id')
    budget_name = request.data.get('name')
    budget_issued = request.data.get('budget')

    if budget_id and budget_name and budget_issued:
        Budget.objects.filter(id=budget_id).update(name=budget_name, budgetIssued=budget_issued)
        return Response({'message': 'Budget updated successfully.'}, status=status.HTTP_200_OK)
    else:
        return Response({'error': 'ID, name, and budget are required.'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def requests_status(request):

    '''
        this api will get status of all the requests in outbox of user
    '''
    params = request.query_params
    desg = params.get('role')
    files = Requests.objects.all()
    obj = []
    for request_object in files:
        file_obj = File.objects.filter(src_object_id=request_object.id, src_module="IWD").first()
        if request_object:
            element = {
                'request_id': request_object.id,
                'name': request_object.name,
                'area': request_object.area,
                'description': request_object.description,
                'requestCreatedBy': request_object.requestCreatedBy,
                'file_id': file_obj.id,
                'processed_by_admin': request_object.iwdAdminApproval,
                'processed_by_director': request_object.directorApproval,
                'work_order': request_object.issuedWorkOrder,
                'work_completed': request_object.workCompleted,
                'processed_by_dean': request_object.deanProcessed,
                'status': request_object.status,
                'active_proposal': request_object.activeProposal,
                'creatiion_time' : request_object.creationTime,
            }
            obj.append(element)
    return Response(obj, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_work(request):

    '''
        this api is for fetching the selected work object
    '''
    request_id = request.query_params.get("request_id")
    print(request.query_params)
    print(request_id)
    work_obj = get_object_or_404(WorkOrder, request_id_id=request_id)
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
        this api will get details of all the issued work orders
    '''

    params = request.query_params
    desg = params.get('role')
    files = Requests.objects.filter(issuedWorkOrder=1)
    obj = []
    for request_object in files:
        work_obj = WorkOrder.objects.filter(request_id=request_object.id).first()
        if work_obj:
            file_obj = File.objects.filter(src_object_id=request_object.id, src_module="IWD").first()
            element = {
                'request_id': request_object.id,
                'name': request_object.name,
                'area': request_object.area,
                'description': request_object.description,
                'work_issuer': work_obj.work_issuer,
                'start_date': work_obj.start_date,
                'estimate_budget': work_obj.estimate_budget,
                'file_id': file_obj.id,
                'work_completed': request_object.workCompleted,
                'active_proposal': request_object.activeProposal,
                'processed_by_admin': request_object.iwdAdminApproval,
                'processed_by_director': request_object.directorApproval,
                'work_order': request_object.issuedWorkOrder,
            }
            obj.append(element)
    return Response(obj, status=200)


def _latest_bill_for_request(request_id):
    return Bills.objects.filter(vendor__work__request_id=request_id).order_by('-id').first()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def audit_document_view(request):

    '''
        This api is used to get a list of all the bills those are required to be audited
    '''
    
    params = request.query_params
    desg = params.get('role')
    if not desg:
        return Response({"error": "Designation not provided"}, status=status.HTTP_400_BAD_REQUEST)

    inbox_files = view_inbox(username=request.user, designation=desg, src_module="IWD")
    
    obj = []
    for x in inbox_files:
        try:
            bill = _latest_bill_for_request(x['src_object_id'])
            if not bill:
                continue
            file_obj = File.objects.get(src_object_id=x['src_object_id'], src_module="IWD")  # Ensure this object exists
            obj.append({
                'request_id': x['src_object_id'],
                'file': bill.file,
                'fileUrl': bill.file.url,
                'file_id': file_obj.id
            })
        except Bills.DoesNotExist:
            print('bill with request_id ', x['src_object_id'], " not found")
        except File.DoesNotExist:
            print('file with request_id ', x['src_object_id'], " not found")

    return Response(obj, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def handle_process_bills(request):

    '''
        This api is used to submit (process) a bill 
    '''

    obj = request.data

    fileid = obj.get('fileid')
    try:
        request_id = File.objects.get(id=fileid).src_object_id
    except ObjectDoesNotExist:
        return Response({'error': 'File not found.'}, status=status.HTTP_404_NOT_FOUND)

    remarks = obj.get('remarks')
    attachment = request.FILES.get('attachment')
    receiver_desg, receiver_user = obj['designation'].split('|')

    forward_file(
        file_id=fileid,
        receiver=receiver_user,
        receiver_designation=receiver_desg, 
        file_extra_JSON={"message": "Request forwarded."},
        remarks=remarks,
        file_attachment=attachment, 
    )
    
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
    formObject.file = attachment
    formObject.save()
    receiver_user_obj = User.objects.get(username=receiver_user)
    iwd_notif(request.user, receiver_user_obj, "file_forward")

    return Response({'obj': obj}, status=status.HTTP_200_OK)

designations_list = ["Junior Engineer", "Executive Engineer (Civil)", "Electrical_AE", "Electrical_JE", "EE", "Civil_AE", "Civil_JE", "Dean (P&D)", "Director", "Accounts Admin", "Admin IWD", "Auditor"]

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def engineer_processed_requests(request):
    obj = []
    desg = request.session.get('currentDesignationSelected')
    
    inbox_files = view_inbox(
        username=request.user.username,
        designation=desg,
        src_module="IWD"
    )

    for result in inbox_files:
        src_object_id = result['src_object_id']
        request_object = Requests.objects.filter(id=src_object_id).first()
        file_obj = File.objects.get(src_object_id=src_object_id, src_module="IWD")
        if request_object:
            element = {
                'id': request_object.id,
                'name': request_object.name,
                'area': request_object.area,
                'description': request_object.description,
                'requestCreatedBy': request_object.requestCreatedBy,
                'file_id': file_obj.id
            }
            obj.append(element)

    return Response(obj)


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
    request_objects = Requests.objects.filter(billGenerated=1)
    obj = []
    for x in request_objects:
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

    return Response({'obj': obj}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def generate_bill_pdf(request):
    request_id = request.query_params.get('request_id')
    if not request_id:
        return Response({'error': 'request_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    request_obj = Requests.objects.filter(id=request_id).first()
    if not request_obj:
        return Response({'error': 'Request not found'}, status=status.HTTP_404_NOT_FOUND)

    work_order = WorkOrder.objects.filter(request_id=request_id).first()
    if not work_order:
        return Response({'error': 'Work order not found for this request'}, status=status.HTTP_404_NOT_FOUND)

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
    desg = request.session.get('currentDesignationSelected')
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
                'file': bill.file,
                'fileUrl': bill.file.url,
                'billSettled': Requests.objects.get(id=x['src_object_id']).billSettled,
                'fileId': file_obj.id
            }
        )
    
    return Response({'data': obj}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def handle_settle_bill_requests(request):
    request_id = request.data.get('id')
    if request_id:
        latest_bill = _latest_bill_for_request(request_id)
        if not latest_bill or not latest_bill.audit:
            return Response({'error': 'Bill must be audited before settlement.'}, status=status.HTTP_400_BAD_REQUEST)
        if Requests.objects.filter(id=request_id, status="Bill Audited").count() == 0:
            return Response({'error': 'Request status must be Bill Audited before settlement.'}, status=status.HTTP_400_BAD_REQUEST)

        Requests.objects.filter(id=request_id).update(status="Final Bill Settled", billSettled=1)
        latest_bill.settle = True
        latest_bill.save(update_fields=['settle'])

        desg = request.session.get('currentDesignationSelected')
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
                    'file': bill.file,
                    'fileUrl': bill.file.url,
                    'billSettled': Requests.objects.get(id=x['src_object_id']).billSettled,
                    'fileId': file_obj.id
                }
            )

        return Response({'message': "Final Bill settled", 'data': obj}, status=status.HTTP_200_OK)
    
    return Response({'error': 'Request ID not provided'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_proposal(request):
    data = request.data.copy()
    request_id = data.get("id")

    request_instance = Requests.objects.filter(id=request_id, iwdAdminApproval=True).first()
    if not request_instance:
        return Response({'error': 'Request not approved by IWD Admin'}, status=status.HTTP_400_BAD_REQUEST)

    # Extract user and request info
    receiver_desg, receiver_user = data.get("designation").split('|')
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
        if request_instance.activeProposal is None:
            Requests.objects.filter(id=request_id).update(
                activeProposal=proposal.id,
                status="Proposal created"
            )
        else:
            Requests.objects.filter(id=request_id).update(
                activeProposal=proposal.id
            )
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
        # Proposal.objects.filter(id=proposal.id).update(proposal_budget=total_budget)
        receiver_user_obj = User.objects.get(username=receiver_user)
        iwd_notif(request.user, receiver_user_obj, "Proposal_added")
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    print("\n\n\n errors : ", serializer.errors)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_proposals(request):
    data = request.query_params
    proposals = Proposal.objects.filter(request_id=data.get("request_id"))
    serializer = ProposalSerializer(proposals, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_items(request):
    try:
        data = request.query_params
        proposal = Proposal.objects.filter(id = data['proposal_id']).first()
        items = Item.objects.filter(proposal=data['proposal_id'])
        itemsdata = ItemsSerializer(items, many=True)
        proposaldata = ProposalSerializer(proposal)
        return Response({"itemsList": itemsdata.data, "proposal":proposaldata.data}, status=status.HTTP_200_OK)
    except Proposal.DoesNotExist:
        return Response({'error': 'Proposal not found'}, status=status.HTTP_404_NOT_FOUND)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def handle_admin_approval(request):
    """
    Approve or reject a request by the IWD Admin.
    """
    data = request.data
    action = data.get('action')

    fileid = data.get('fileid')
    request_id = File.objects.get(id=fileid).src_object_id

    remarks = data.get('remarks')
    attachment = request.FILES.get('file')
    receiver_desg, receiver_user = data.get('designation').split('|')
    if not fileid:
        return Response({'error': 'File ID not provided'}, status=status.HTTP_400_BAD_REQUEST)
    
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
    message = ""

    if not request_id or not action:
        return Response({'error': 'Request ID and action are required'}, status=status.HTTP_400_BAD_REQUEST)

    request_instance = Requests.objects.filter(id=request_id).first()
    if not request_instance:
        return Response({'error': 'Request not found'}, status=status.HTTP_404_NOT_FOUND)

    if action == "approve":
        if request_instance.activeProposal:
            Requests.objects.filter(id=request_id).update(iwdAdminApproval=1, status="Proposal created")
        else:
            Requests.objects.filter(id=request_id).update(iwdAdminApproval=1, status="Approved by the IWD Admin")
        return Response({'message': 'Request approved by IWD Admin'}, status=status.HTTP_200_OK)
    elif action == "reject":
        Requests.objects.filter(id=request_id).update(iwdAdminApproval=-1, status="Rejected", activeProposal=None)
        return Response({'message': 'Request rejected by IWD Admin'}, status=status.HTTP_200_OK)
    else:
        return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)
