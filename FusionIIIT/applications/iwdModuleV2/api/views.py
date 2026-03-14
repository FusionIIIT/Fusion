from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from applications.iwdModuleV2.models import Requests, File, Tracking, Budget, Vendor, WorkOrder, Bills, Proposal, Item
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
from django.db import transaction
import logging  
from .services import *

logger = logging.getLogger(__name__)
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
        
    designations = Designation.objects.filter(name__in=designations_list)

    for designation in designations:
        holds = HoldsDesignation.objects.filter(designation=designation)
        serializer = HoldsDesignationSerializer(holds, many=True)
        holdsDesignations.extend(serializer.data)

    return Response({'holdsDesignations': holdsDesignations}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_request(request):

    data = request.data.copy()
    data['requestCreatedBy'] = request.user.username
    attachment = request.FILES.get('file')

    serializer = CreateRequestsSerializer(data=data, context={'request': request})

    if serializer.is_valid():
        create_request_service(request, serializer, attachment, data.get("role"))

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

    data = request.data

    fileid = data.get('fileid')
    remarks = data.get('remarks')
    attachment = request.FILES.get('file')

    receiver_desg, receiver_user = data.get('designation').split('|')

    handle_dean_process_service(
        request,
        fileid,
        remarks,
        attachment,
        receiver_user,
        receiver_desg
    )

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
    forward_request_service(
        request,
        fileid,
        receiver_user,
        receiver_desg,
        remarks,
        attachment
    )

    return Response({
        "message": "File forwarded successfully",
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def handle_director_approval(request):

    data = request.data

    fileid = data.get('fileid')
    action = data.get('action')

    remarks = data.get('remarks')
    attachment = request.FILES.get('file')

    receiver_desg, receiver_user = data.get('designation').split('|')

    handle_director_approval_service(
        request,
        fileid,
        action,
        remarks,
        attachment,
        receiver_user,
        receiver_desg
    )

    return Response({'message': 'Processed successfully'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def handle_audit_document(request):

    fileid = request.data.get('fileid')
    remarks = request.data.get('remarks')
    attachment = request.FILES.get('attachment')

    receiver_desg, receiver_user = request.data['designation'].split('|')

    audit_document_service(
        request,
        fileid,
        remarks,
        attachment,
        receiver_user,
        receiver_desg
    )

    return Response("Bill Audited", status=status.HTTP_200_OK)


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

    data = request.data.copy()
    request_id = data.get("id")

    request_instance = Requests.objects.filter(id=request_id).first()

    if not request_instance:
        return Response({'error': 'Request not found'}, status=status.HTTP_404_NOT_FOUND)

    if request_instance.iwdAdminApproval == -1:
        return Response({'error': 'This request has been rejected by IWD Admin'}, status=status.HTTP_403_FORBIDDEN)

    receiver_desg, receiver_user = data.get("designation").split('|')

    result = update_request_service(
        request,
        data,
        request_instance,
        receiver_user,
        receiver_desg
    )

    return Response(result, status=status.HTTP_201_CREATED)


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

    data = request.data.copy()
    data['work_issuer'] = request.user.username

    result = issue_work_order_service(request, data)

    if result["success"]:
        return Response(status=status.HTTP_200_OK)

    return Response(result["error"], status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_vendor(request):

    data = request.data.copy()

    logger.info("Add vendor request received")

    serializer = VendorSerializer(data=data)

    logger.debug(f"Vendor serializer initialized: {serializer}")

    if serializer.is_valid():

        logger.info("Vendor serializer validation successful")

        serializer.save()

        logger.info("Vendor saved successfully")

        messages.success(request, "Vendor Added")

        return Response(status=status.HTTP_200_OK)

    logger.warning(f"Vendor serializer validation failed: {serializer.errors}")

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

    request_id = request.data.get('id')

    work_completed_service(request_id)

    return Response({'message': 'Work Completed'})



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
            bill = Bills.objects.get(request_id=x['src_object_id'])  # Efficient single query
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

    obj = request.data

    fileid = obj.get('fileid')
    remarks = obj.get('remarks')
    attachment = request.FILES.get('attachment')

    receiver_desg, receiver_user = obj['designation'].split('|')

    process_bill_service(
        request,
        fileid,
        remarks,
        attachment,
        receiver_user,
        receiver_desg
    )

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


# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def generateFinalBill(request):
#     request_id = request.data.get("id", 0)

#     # Fetch the related work order
#     work_order = WorkOrder.objects.get(request_id=request_id)

#     # Fetch IWD items
#     iwd_items = StockItem.objects.filter(department=34)

#     items_list = []

#     # Collecting items related to the request
#     for x in iwd_items:
#         stock_entry_id = x.StockEntryId.item_id.file_info
#         indent_file_objects = IndentFile.objects.filter(file_info=stock_entry_id)
#         for item in indent_file_objects:
#             if item.purpose == request_id:
#                 element = [item.item_name, item.quantity, item.estimated_cost, item.file_info.upload_date]
#                 items_list.append(element)

#     filename = f"Request_id_{request_id}_final_bill.pdf"

#     buffer = BytesIO()
#     c = canvas.Canvas(buffer, pagesize=letter)
#     c.setFont("Helvetica", 12)

#     y_position = 750
#     rid = f"Request Id : {request_id}"
#     agency = f"Agency : {work_order.agency}"
    
#     c.drawString(100, y_position, rid)
#     y_position -= 20
#     c.drawString(100, y_position, agency)
#     y_position -= 20
#     c.drawString(100, y_position - 40, "Items:")

#     # Prepare data for the table
#     data = [["Item Name", "Quantity", "Cost (in Rupees)", "Date of Purchase", "Total Amount"]]
#     for item in items_list:
#         data.append([item[0], str(item[1]), "{:.2f}".format(item[2]), item[3], "{:.2f}".format(item[1] * item[2])])

#     total_amount_to_be_paid = sum(item[1] * item[2] for item in items_list)
#     c.drawString(100, y_position - 80, f"Total Amount (in Rupees): {total_amount_to_be_paid:.2f}")

#     # Create a table for the PDF
#     table = Table(data)
#     table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
#                                 ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
#                                 ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
#                                 ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
#                                 ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
#                                 ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
#                                 ('GRID', (0, 0), (-1, -1), 1, colors.black)]))

#     table.wrapOn(c, 400, 600)
#     table.drawOn(c, 100, y_position - 60)
#     c.save()

#     buffer.seek(0)

#     response = HttpResponse(content_type='application/pdf')
#     response['Content-Disposition'] = f'attachment; filename="{filename}"'
#     response.write(buffer.getvalue())

#     return response
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def handleBillGeneratedRequests(request):

    request_id = request.data.get("id")

    obj = bill_generated_service(request_id)

    return Response({'obj': obj})


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
def settle_bills_view(request):
    desg = request.session.get('currentDesignationSelected')
    inbox_files = view_inbox(username=request.user, designation=desg, src_module="IWD")
    
    obj = [
        {
            'requestId': x['src_object_id'],
            'file': Bills.objects.get(request_id=x['src_object_id']).file,
            'fileUrl': Bills.objects.get(request_id=x['src_object_id']).file.url,
            'billSettled': Requests.objects.get(id=x['src_object_id']).billSettled,
            'fileId': File.objects.get(src_object_id=x['src_object_id'], src_module="IWD").id
        }
        for x in inbox_files
    ]
    
    return Response({'data': obj}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def handle_settle_bill_requests(request):
    request_id = request.data.get('id')
    if request_id:
        Requests.objects.filter(id=request_id).update(status="Final Bill Settled", billSettled=1)

        desg = request.session.get('currentDesignationSelected')
        inbox_files = view_inbox(username=request.user, designation=desg, src_module="IWD")

        obj = [
            {
                'requestId': x['src_object_id'],
                'file': Bills.objects.get(request_id=x['src_object_id']).file,
                'fileUrl': Bills.objects.get(request_id=x['src_object_id']).file.url,
                'billSettled': Requests.objects.get(id=x['src_object_id']).billSettled,
                'fileId': File.objects.get(src_object_id=x['src_object_id'], src_module="IWD").id
            }
            for x in inbox_files
        ]

        return Response({'message': "Final Bill settled", 'data': obj}, status=status.HTTP_200_OK)
    
    return Response({'error': 'Request ID not provided'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_proposal(request):

    data = request.data.copy()

    request_id = data.get("id")

    request_instance = Requests.objects.filter(
        id=request_id,
        iwdAdminApproval=True
    ).first()

    if not request_instance:
        return Response(
            {'error': 'Request not approved by IWD Admin'},
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer = CreateProposalSerializer(data=data)

    if serializer.is_valid():

        create_proposal_service(
            request,
            serializer,
            request_instance
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

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

    data = request.data

    fileid = data.get('fileid')
    action = data.get('action')

    remarks = data.get('remarks')
    attachment = request.FILES.get('file')

    receiver_desg, receiver_user = data.get('designation').split('|')

    admin_approval_service(
        request,
        fileid,
        action,
        remarks,
        attachment,
        receiver_user,
        receiver_desg
    )

    return Response({'message': 'Processed successfully'})
