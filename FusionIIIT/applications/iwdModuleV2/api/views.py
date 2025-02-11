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

    '''
        to create a new request
    '''
    data = request.data
    data['requestCreatedBy'] = request.user.username
    serializer = CreateRequestsSerializer(data=data, context={'request': request})
    
    if serializer.is_valid():
        formObject = serializer.save()
        print(formObject.requestCreatedBy)
        request_object = Requests.objects.get(pk=formObject.pk)
        receiver_desg, receiver_user = data.get('designation').split('|')
        try:
            receiver_user_obj = User.objects.get(username=receiver_user)
        except User.DoesNotExist:
            return Response({'error': 'Receiver user does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        create_file(
            uploader=request.user.username,
            uploader_designation=data.get('role'),
            receiver=receiver_user,
            receiver_designation=receiver_desg,
            src_module="IWD",
            src_object_id=str(request_object.id),
            file_extra_JSON={"value": 2},
            attached_file=None
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
    print(inbox_files)
    for result in inbox_files:
        print("hello1")
        src_object_id = result['src_object_id']
        request_object = Requests.objects.filter(id=src_object_id).first()
        if request_object:
            print("hello")
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
    print(id)
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
def handle_engineer_process_requests(request):
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

    Requests.objects.filter(id=request_id).update(engineerProcessed=1)
    receiver_user_obj = get_object_or_404(User, username=receiver_user)
    iwd_notif(request.user, receiver_user_obj, "file_forward")

    return Response({
        "message": "File forwarded successfully",
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def handle_director_approval(request):

    '''
        This api is to approve or reject file based on director's action
    '''

    data = request.data
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
    print(data)
    if data.get('action') == 'approve':
        message = "Request_approved"
        print(message)
        Requests.objects.filter(id=request_id).update(directorApproval=1, status="Approved by the director")
    else:
        message = "Request_rejected"
        Requests.objects.filter(id=request_id).update(directorApproval=-1, status="Rejected by the director")

    return Response({'message': message})

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
    data = request.data
    request_id = data.get("id")
    desg = data.get('role')
    receiver_desg, receiver_user = data.get('designation').split('|')

    Requests.objects.filter(id=request_id).update(
        name=request.data.get('name'),
        description=request.data.get('description'),
        area=request.data.get('area'),
        engineerProcessed=0,
        directorApproval=0,
        deanProcessed=0,
        requestCreatedBy=request.user.username,
        status="Pending",
        issuedWorkOrder=0,
        workCompleted=0,
        billGenerated=0,
        billProcessed=0,
        billSettled=0
    )

    try:
        file_obj = File.objects.get(src_object_id=request_id, src_module="IWD")
        if file_obj:
            delete_file(file_obj.id)
    except:
        print("file doesnt exist")
    if request_id:
        create_file(
            uploader=request.user.username,
            uploader_designation=desg,
            receiver=receiver_user,
            receiver_designation=receiver_desg,
            src_module="IWD",
            src_object_id=str(request_id),
            file_extra_JSON={"value": 2},
            attached_file=None
        )
    else:
        print("request id is invalid")
    
    receiver_user_obj = User.objects.get(username=receiver_user)
    iwd_notif(request.user, receiver_user_obj, "Request_added")

    return Response({"message": "Request updated successfully"}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def director_approved_requests(request):
    
    '''
        requests approved by director and can issue work order
    '''

    requestsObject = Requests.objects.filter(directorApproval=1, issuedWorkOrder=0)
    serializer = DirectorApprovedRequestsSerializer(requestsObject, many=True)
    print(serializer.data)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def issue_work_order(request):
    
    '''
        issue work order
    '''
    
    request_id = request.data.get('request_id')
    request_instance = get_object_or_404(Requests, pk=request_id)
    serializer = WorkOrderFormSerializer(data=request.data)
    print(serializer)
    if serializer.is_valid():
        work_order = serializer.save(request_id=request_instance)

        request_instance.status = "Work Order issued"
        request_instance.issuedWorkOrder = 1
        request_instance.save()

        messages.success(request, "Work Order Issued")
        return Response(status=status.HTTP_200_OK)
    else:
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
    print(serializer.data)
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
    outbox_files = view_outbox(username=request.user, designation=desg, src_module="IWD")
    obj = []
    for result in outbox_files:
        src_object_id = result['src_object_id']
        request_object = Requests.objects.filter(id=src_object_id).first()
        file_obj = File.objects.get(src_object_id=src_object_id, src_module="IWD")
        print(request_object)
        if request_object:
            element = {
                'request_id': request_object.id,
                'name': request_object.name,
                'area': request_object.area,
                'description': request_object.description,
                'requestCreatedBy': request_object.requestCreatedBy,
                'file_id': file_obj.id,
                'processed_by_director': request_object.directorApproval,
                'processed_by_dean': request_object.deanProcessed,
                'status': request_object.status,
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

    print(obj)
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
    
    request_instance = Requests.objects.get(pk=request_id)

    formObject = Bills()
    formObject.request_id = request_instance
    formObject.file = attachment
    formObject.save()
    receiver_user_obj = User.objects.get(username=receiver_user)
    iwd_notif(request.user, receiver_user_obj, "file_forward")

    return Response({'obj': obj}, status=status.HTTP_200_OK)


@api_view(['POST'])
def page1_1(request):
    project_id = request.data.get('name')
    request.session['projectId'] = project_id
    project = Projects(id=project_id)
    project.save()
        
    serializer = PageOneDetailsSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(id=project)  # Assign the project instance
        return Response({'message': 'Page One Details Saved!'}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def AESForm(request):
    serializer = AESDetailsSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(key=Projects.objects.get(id=request.session['projectId']))
        return Response({'message': 'AES Details Saved!'}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def page2_1(request):
    request.session['projectId'] = request.data.get('id')
    serializer = PageTwoDetailsSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(id=Projects.objects.get(id=request.session['projectId']))
        return Response({'message': 'Page Two Details Saved!'}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def corrigendumInput(request):
    existingObject = CorrigendumTable.objects.filter(key=Projects.objects.get(id=request.session['projectId']))
    if existingObject.count() == 1:
        existingObject.delete()

    serializer = CorrigendumTableSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(key=Projects.objects.get(id=request.session['projectId']))
        return Response({'message': 'Corrigendum Input Saved!'}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def addendumInput(request):
    existingObject = Addendum.objects.filter(key=Projects.objects.get(id=request.session['projectId']))
    if existingObject.count() == 1:
        existingObject.delete()

    serializer = AddendumSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(key=Projects.objects.get(id=request.session['projectId']))
        return Response({'message': 'Addendum Input Saved!'}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def PreBidForm(request):
    existingObject = PreBidDetails.objects.filter(key=Projects.objects.get(id=request.session['projectId']))
    if existingObject.count() == 1:
        existingObject.delete()

    serializer = PreBidDetailsSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(key=Projects.objects.get(id=request.session['projectId']))
        return Response({'message': 'PreBid Form Saved!'}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def noOfEntriesTechnicalBid(request):
    existingObject = NoOfTechnicalBidTimes.objects.filter(key=Projects.objects.get(id=request.session['projectId']))
    if existingObject.count() == 1:
        existingObject.delete()
        
    serializer = NoOfTechnicalBidTimesSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(key=Projects.objects.get(id=request.session['projectId']))
        return Response({'message': 'Number of Entries for Technical Bid Saved!'}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def TechnicalBidForm(request):
    numberOfTechnicalBidTimes = NoOfTechnicalBidTimes.objects.get(key=Projects.objects.get(id=request.session['projectId'])).number
    existingObject = TechnicalBidDetails.objects.filter(key=Projects.objects.get(id=request.session['projectId']))
    if existingObject.count() == 1:
        existingObject.delete()

    serializer = TechnicalBidDetailsSerializer(data=request.data)
    if serializer.is_valid():
        technical_bid = serializer.save(key=Projects.objects.get(id=request.session['projectId']))
            
        TechnicalBidContractorDetails.objects.filter(key=technical_bid).all().delete()
        for w in range(numberOfTechnicalBidTimes):
            contractor_serializer = TechnicalBidContractorDetailsSerializer(data={
                'key': technical_bid,
                'name': request.data.get(f'{w}name'),
                'description': request.data.get(f'{w}Description'),
            })
            if contractor_serializer.is_valid():
                contractor_serializer.save()
            
        return Response({'message': 'Technical Bid Form Saved!'}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST', 'GET'])
def noOfEntriesFinancialBid(request):
    project_id = request.session['projectId']
    objectTechnicalBid = TechnicalBidDetails.objects.get(key=Projects.objects.get(id=project_id))
    objects = TechnicalBidContractorDetails.objects.filter(key=objectTechnicalBid)

    listOfContractors = [t.name for t in objects]

    if request.method == 'POST':
        existingObject = FinancialBidDetails.objects.filter(key=Projects.objects.get(id=project_id))
        if existingObject.count() == 1:
            existingObject.delete()

        serializer = FinancialBidDetailsSerializer(data=request.data)
        if serializer.is_valid():
            financial_bid = serializer.save(key=Projects.objects.get(id=project_id))
            for contractor in listOfContractors:
                contractor_serializer = FinancialContractorDetailsSerializer(data={
                    'key': financial_bid,
                    'name': contractor,
                    'totalCost': request.data[contractor + 'totalCost'],
                    'estimatedCost': request.data[contractor + 'estimatedCost'],
                    'percentageRelCost': request.data[contractor + 'percentageRelCost'],
                    'perFigures': request.data[contractor + 'perFigures'],
                })
                if contractor_serializer.is_valid():
                    contractor_serializer.save()
            return Response({"message": "Financial bid details saved successfully."}, status=status.HTTP_201_CREATED)

    return Response({'list': listOfContractors}, status=status.HTTP_200_OK)

@api_view(['POST', 'GET'])
def letterOfIntent(request):
    if request.method == 'POST':
        existingObject = LetterOfIntentDetails.objects.filter(key=Projects.objects.get(id=request.session['projectId']))
        if existingObject.count() == 1:
            existingObject.delete()

        serializer = LetterOfIntentDetailsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(key=Projects.objects.get(id=request.session['projectId']))
            return Response({"message": "Letter of Intent saved successfully."}, status=status.HTTP_201_CREATED)

    return Response({}, status=status.HTTP_200_OK)

@api_view(['POST', 'GET'])
def AgreementInput(request):
    project_id = request.session.get('projectId')
    if request.method == 'POST':
        existingObject = Agreement.objects.filter(key=Projects.objects.get(id=project_id))
        if existingObject.exists():
            existingObject.delete()

        serializer = AgreementSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(key=Projects.objects.get(id=project_id))
            return Response({"message": "Agreement saved successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    return Response({}, status=status.HTTP_200_OK)

@api_view(['POST', 'GET'])
def milestonesForm(request):
    project_id = request.session.get('projectId')
    if request.method == 'POST':
        serializer = MilestonesSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(key=Projects.objects.get(id=project_id))
            return Response({"message": "Milestone saved successfully."}, status=status.HTTP_201_CREATED)

    Milestones.objects.filter(key=Projects.objects.get(id=project_id)).delete()
    return Response({}, status=status.HTTP_200_OK)


@api_view(['POST', 'GET'])
def page3_1(request):
    if request.method == 'POST':
        request.session['projectId'] = request.data['id']
        serializer = PageThreeDetailsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(id=Projects.objects.get(id=request.session['projectId']))
            return Response({"message": "Page 3 details saved successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    return Response({}, status=status.HTTP_200_OK)

@api_view(['POST', 'GET'])
def ExtensionOfTimeForm(request):
    project_id = request.session.get('projectId')
    if request.method == 'POST':
        serializer = ExtensionOfTimeDetailsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(key=Projects.objects.get(id=project_id))
            return Response({"message": "Extension of Time details saved successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    return Response({}, status=status.HTTP_200_OK)

@api_view(['POST'])
def page1View(request):
    request.session['projectId'] = request.data['id']
    projectPageOne = PageOneDetails.objects.get(id=Projects.objects.get(id=request.session['projectId']))
    return Response({'x': projectPageOne}, status=status.HTTP_200_OK)

@api_view(['POST'])
def page2View(request):
    projectPageTwo = PageTwoDetails.objects.get(id=Projects.objects.get(id=request.session['projectId']))
    return Response({'x': projectPageTwo}, status=status.HTTP_200_OK)

@api_view(['GET'])
def AESView(request):
    objects = AESDetails.objects.filter(key=Projects.objects.get(id=request.session['projectId']))
    serializer = AESDetailsSerializer(objects, many=True)
    return Response({'AES': serializer.data}, status=status.HTTP_200_OK)

@api_view(['GET'])
def financialBidView(request):
    elements = []
    objects = FinancialBidDetails.objects.filter(key=Projects.objects.get(id=request.session['projectId']))
    for f in objects:
        contractorObjects = FinancialContractorDetails.objects.filter(key=f)
        for w in contractorObjects:
            obj = [f.sNo, f.description, w.name, w.estimatedCost, w.percentageRelCost, w.perFigures, w.totalCost]
            elements.append(obj)
    return Response({'financial': elements}, status=status.HTTP_200_OK)

@api_view(['GET'])
def technicalBidView(request):
    elements = []
    objects = TechnicalBidDetails.objects.filter(key=Projects.objects.get(id=request.session['projectId']))
    for f in objects:
        contractorObjects = TechnicalBidContractorDetails.objects.filter(key=f)
        for w in contractorObjects:
            obj = [f.sNo, f.requirements, w.name, w.description]
            elements.append(obj)
    return Response({'technical': elements}, status=status.HTTP_200_OK)

@api_view(['GET'])
def preBidDetailsView(request):
    preBidObjects = PreBidDetails.objects.filter(key=Projects.objects.get(id=request.session['projectId']))
    serializer = PreBidDetailsSerializer(preBidObjects, many=True)
    return Response({'preBidDetails': serializer.data}, status=status.HTTP_200_OK)

@api_view(['GET'])
def corrigendumView(request):
    try:
        corrigendumObject = CorrigendumTable.objects.get(key=Projects.objects.get(id=request.session['projectId']))
        serializer = CorrigendumTableSerializer(corrigendumObject)
        return Response({'corrigendum': serializer.data}, status=status.HTTP_200_OK)
    except CorrigendumTable.DoesNotExist:
        return Response({'error': 'Corrigendum not found.'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def addendumView(request):
    try:
        addendumObject = Addendum.objects.get(key=Projects.objects.get(id=request.session['projectId']))
        serializer = AddendumSerializer(addendumObject)
        return Response({'addendum': serializer.data}, status=status.HTTP_200_OK)
    except Addendum.DoesNotExist:
        return Response({'error': 'Addendum not found.'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def letterOfIntentView(request):
    try:
        letterOfIntentObject = LetterOfIntentDetails.objects.get(key=Projects.objects.get(id=request.session['projectId']))
        serializer = LetterOfIntentDetailsSerializer(letterOfIntentObject)
        return Response({'letterOfIntent': serializer.data}, status=status.HTTP_200_OK)
    except LetterOfIntentDetails.DoesNotExist:
        return Response({'error': 'Letter of Intent not found.'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def agreementView(request):
    try:
        agreementObject = Agreement.objects.get(key=Projects.objects.get(id=request.session['projectId']))
        serializer = AgreementSerializer(agreementObject)
        return Response({'agreement': serializer.data}, status=status.HTTP_200_OK)
    except Agreement.DoesNotExist:
        return Response({'error': 'Agreement not found.'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def milestoneView(request):
    milestoneObjects = Milestones.objects.filter(key=Projects.objects.get(id=request.session['projectId']))
    serializer = MilestonesSerializer(milestoneObjects, many=True)
    return Response({'milestones': serializer.data}, status=status.HTTP_200_OK)

@api_view(['GET'])
def page3View(request):
    try:
        pageThreeDetails = PageThreeDetails.objects.get(key=Projects.objects.get(id=request.session['projectId']))
        serializer = PageThreeDetailsSerializer(pageThreeDetails)
        return Response({'pageThreeDetails': serializer.data}, status=status.HTTP_200_OK)
    except PageThreeDetails.DoesNotExist:
        return Response({'error': 'Page Three Details not found.'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def extensionFormView(request):
    extensionObjects = ExtensionOfTimeDetails.objects.filter(key=Projects.objects.get(id=request.session['projectId']))
    serializer = ExtensionOfTimeDetailsSerializer(extensionObjects, many=True)
    return Response({'extension': serializer.data}, status=status.HTTP_200_OK)

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
def generateFinalBill(request):
    request_id = request.data.get("id", 0)

    # Fetch the related work order
    work_order = WorkOrder.objects.get(request_id=request_id)

    # Fetch IWD items
    iwd_items = StockItem.objects.filter(department=34)

    items_list = []

    # Collecting items related to the request
    for x in iwd_items:
        stock_entry_id = x.StockEntryId.item_id.file_info
        indent_file_objects = IndentFile.objects.filter(file_info=stock_entry_id)
        for item in indent_file_objects:
            if item.purpose == request_id:
                element = [item.item_name, item.quantity, item.estimated_cost, item.file_info.upload_date]
                items_list.append(element)

    filename = f"Request_id_{request_id}_final_bill.pdf"

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Helvetica", 12)

    y_position = 750
    rid = f"Request Id : {request_id}"
    agency = f"Agency : {work_order.agency}"
    
    c.drawString(100, y_position, rid)
    y_position -= 20
    c.drawString(100, y_position, agency)
    y_position -= 20
    c.drawString(100, y_position - 40, "Items:")

    # Prepare data for the table
    data = [["Item Name", "Quantity", "Cost (in Rupees)", "Date of Purchase", "Total Amount"]]
    for item in items_list:
        data.append([item[0], str(item[1]), "{:.2f}".format(item[2]), item[3], "{:.2f}".format(item[1] * item[2])])

    total_amount_to_be_paid = sum(item[1] * item[2] for item in items_list)
    c.drawString(100, y_position - 80, f"Total Amount (in Rupees): {total_amount_to_be_paid:.2f}")

    # Create a table for the PDF
    table = Table(data)
    table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                ('GRID', (0, 0), (-1, -1), 1, colors.black)]))

    table.wrapOn(c, 400, 600)
    table.drawOn(c, 100, y_position - 60)
    c.save()

    buffer.seek(0)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write(buffer.getvalue())

    return response

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def handleBillGeneratedRequests(request):
    request_id = request.data.get("id", 0)
    # if request_id:
    #     Requests.objects.filter(id=request_id).update(status="Bill Generated", billGenerated=1)

    # requests_object = Requests.objects.filter(issuedWorkOrder=1, billGenerated=0)
    # obj = []
    # for x in requests_object:
    #     element = {
    #         "id": x.id,
    #         "name": x.name,
    #         "area": x.area,
    #         "description": x.description,
    #         "requestCreatedBy": x.requestCreatedBy,
    #         "workCompleted": x.workCompleted,
    #     }
    #     obj.append(element)

    # return Response({'obj': obj}, status=status.HTTP_200_OK)


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
    data["created_by"] = str(request.user)
    print(data)
    print(data.get('role'))
    data["request"] = data.get('id')
    # print(Requests.objects.get(id=data.get('id')))
    # print(request.user)
    receiver_desg, receiver_user = data.get('designation').split('|')
    serializer = ProposalSerializer(data=data)
    if serializer.is_valid():
        proposal = serializer.save()
        file_id = create_file(
            uploader=request.user.username,
            uploader_designation=data.get('role'),
            receiver=receiver_user,
            receiver_designation=receiver_desg,
            src_module="IWD",
            src_object_id=str(proposal.id),
            file_extra_JSON={"value": 2},
            attached_file=None
        )
        file_instance = File.objects.get(id=file_id)
        proposal.file = file_instance
        proposal.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_proposals(request):
    data=request.data;
    proposals = Proposal.objects.filter(request_id=data["request_id"])
    serializer = ProposalSerializer(proposals, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


