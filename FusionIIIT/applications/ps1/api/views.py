from django.contrib import messages
from rest_framework.permissions import IsAuthenticated #type:ignore
from rest_framework.response import Response #type:ignore
from rest_framework import status #type:ignore
from rest_framework.decorators import api_view, permission_classes #type:ignore
from applications.ps1.models import IndentFile, File,StockTransfer,StockEntry,StockItem,IndentItem
from applications.globals.models import HoldsDesignation, Designation,ExtraInfo,DepartmentInfo,Faculty
from applications.filetracking.models import Tracking
from .serializers import IndentItemSerializer,IndentFileSerializer ,FileSerializer,ExtraInfoSerializer,HoldsDesignationSerializer,TrackingSerializer,StockEntrySerializer,StockItemSerializer,StockTransferSerializer
from django.utils import timezone
from notification.views import office_module_notif
from django.contrib import messages
from django.contrib.auth.models import User
from notification.views import purchase_notif,iwd_notif
from applications.filetracking.sdk.methods import *
from datetime import datetime
from django.http import HttpResponseForbidden,JsonResponse
from django.db.models import Q,Count
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
import ast
from datetime import datetime

dept_admin_to_dept = {
    "deptadmin_cse": "CSE",
    "deptadmin_ece": "ECE",
    "deptadmin_me": "ME",
    "deptadmin_sm": "SM",
    "deptadmin_design": "Design",
    "deptadmin_liberalarts": "Liberal Arts",
    "deptadmin_ns": "Natural Science",
}

dept_admin_design = ["deptadmin_cse", "deptadmin_ece", "deptadmin_me","deptadmin_sm", "deptadmin_design", "deptadmin_liberalarts","deptadmin_ns" ]


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getDesignations(request):
    try:
        if request.method == 'GET':
            designations = HoldsDesignation.objects.filter(user=request.user)
            if not designations.exists():
                return Response({"error": "No designations found for the user."}, status=status.HTTP_404_NOT_FOUND)

            designations_serialized = HoldsDesignationSerializer(designations, many=True)
            return Response(designations_serialized.data, status=status.HTTP_200_OK)

        return Response({"message": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    except Exception as e:
        return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def getOneFiledIndent(request):
    try:
        file_id = request.data.get('file_id')
        indent = IndentFile.objects.get(file_info_id=file_id)
        fileinfo = File.objects.get(pk=file_id)
        items = IndentItem.objects.filter(indent_file_id=file_id)  # Fetch related items
        
        # Serialize data
        serializer = IndentFileSerializer(indent)
        serializer_file = FileSerializer(fileinfo)
        serializer_items = IndentItemSerializer(items, many=True)  # Serialize multiple items
        
        department = request.user.extrainfo.department.name
        
        return Response({
            'indent': serializer.data,
            'file': serializer_file.data,
            'department': department,
            'items': serializer_items.data  # Include items in response
        }, status=status.HTTP_200_OK)
    
    except IndentFile.DoesNotExist:
        return Response({"error": "Indent not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



    
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete_indent(request):
    try:
        file_id = request.data.get('file_id')  
        indent = IndentFile.objects.get(file_info_id=file_id)
        indent.delete()
        return Response({"message": "Indent deleted successfully."}, status=status.HTTP_200_OK)
    except IndentFile.DoesNotExist:
        return Response({"error": "Indent not found."}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createDraft(request):
    try:
        if request.method == 'POST':
            uploader = request.user.extrainfo
            subject = request.data.get('title')
            description = request.data.get('description')
            # design = request.data.get('designation')
            uname = "atul"
            # username = request.data.get('uploaderUsername')
            user = User.objects.get(username=uname)
            user_id = user.id
            print(user_id)
            # Ensure the design exists or raise a 404 error
            holds_designation = get_object_or_404(HoldsDesignation, user_id=user_id)
            print(holds_designation)
            idd = 1
            designation = get_object_or_404(Designation, id=holds_designation.designation_id)
            print(designation)

            upload_file = request.FILES.get('file')
            item_name = request.data.get('item_name')
            quantity = request.data.get('quantity')
            present_stock = request.data.get('present_stock')
            estimated_cost = request.data.get('estimated_cost')
            purpose = request.data.get('purpose')
            specification = request.data.get('specification')
            item_type = request.data.get('item_type')
            # nature = request.data.get('nature')
            # equipment = request.data.get('indigenous')
            # replaced = request.data.get('replaced')
            budgetary_head = request.data.get('budgetary_head')
            expected_delivery = request.data.get('expected_delivery')
            sources_of_supply = request.data.get('sources_of_supply')
            head_approval=False
            director_approval=False
            financial_approval=False
            purchased =False
            # Create File object

            uploader = request.user.username
            # designation = 1;
            print("uploader : ",uploader)
            file_id=create_draft(
                uploader=uploader,
                uploader_designation=designation,
                src_module="ps1",
                src_object_id="",
                file_extra_JSON={"value": 2},
                attached_file=upload_file
            )
            # Create IndentFile object
            indent_file = IndentFile.objects.create(
                file_info=get_object_or_404(File, pk=file_id),
                item_name=item_name,
                quantity=quantity,
                present_stock=present_stock,
                estimated_cost=estimated_cost,
                purpose=purpose,
                specification=specification,
                item_type=item_type,
                # nature=nature,
                # equipment=equipment,
                # replaced=replaced,
                budgetary_head=budgetary_head,
                expected_delivery=expected_delivery,
                sources_of_supply=sources_of_supply,
                head_approval=head_approval,
                director_approval=director_approval,
                financial_approval=financial_approval,
                purchased=purchased,
            )

            # Serialize response data
            # file_serializer = FileSerializer(file)
            indent_file_serializer = IndentFileSerializer(indent_file)

            # Return response
            return Response({
                # 'file': file_serializer.data,
                'indent_file': indent_file_serializer.data,
                'message': 'Indent Filed Successfully!',
            }, status=status.HTTP_201_CREATED)

    
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def indentView(request, username):
    print(username)
    user = User.objects.get(username=username)
    user_id = user.id

    hold_designation = HoldsDesignation.objects.filter(user_id=user_id)
    id = hold_designation[0].id
    print(id)
    currentDesignation = request.GET.get('role')  # Capture role from headers
    if currentDesignation=="student":
        return Response({'error': 'Student are not allowd to access this view'}, status=403)
    
    designation = HoldsDesignation.objects.filter(user=request.user, designation__name=currentDesignation).first()

    tracking_objects = Tracking.objects.all()
    tracking_obj_ids = [obj.file_id for obj in tracking_objects]
    draft_indent = IndentFile.objects.filter(file_info__in=tracking_obj_ids)
    draft = [indent.file_info.id for indent in draft_indent]
    draft_files = File.objects.filter(id__in=draft).order_by('-upload_date')
    indents = [file.indentfile for file in draft_files]
    serializer = IndentFileSerializer(indents, many=True)
    serializer_draft = FileSerializer(draft_files, many=True)

    combined_data = []
    for indent_data, draft_file_data in zip(serializer.data, serializer_draft.data):
        combined_data.append({
            'indent': indent_data,
            'draft_file': draft_file_data
        })
    extrainfo = list(ExtraInfo.objects.all().values())
    abcd = HoldsDesignation.objects.get(pk=id)
    s = str(abcd).split(" - ")
    designations = s[1]
    notifs = list(request.user.notifications.all().values())

    response_data = {
        'Data': combined_data,
        'notifications': list(notifs),
    }
    
    return Response(response_data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def indentView2(request, username):
    user = User.objects.get(username=username)
    user_id = user.id

    # Capture role from request parameters
    current_designation_name = request.GET.get('role')
    if current_designation_name == "student":
        return Response({'error': 'Students are not allowed to access this view'}, status=403)

    # Check if the current designation is associated with the user
    designation = HoldsDesignation.objects.filter(user=request.user, designation__name=current_designation_name).first()
    if not designation:
        return Response({'error': 'Designation not found'}, status=404)

    # Assuming the HoldsDesignation for the role is needed to access the view
    abcd = HoldsDesignation.objects.filter(user_id=user_id, designation__name=current_designation_name).first()
    if not abcd:
        return Response({'error': 'User does not hold the specified designation.'}, status=404)

    designations = abcd.designation.name

    # Fetch inbox data and filter Tracking records based on username and role
    data = view_inbox(request.user.username, designations, "ps1")
    for item in data:
        file_id = item['id']
        
        # Filter Tracking entries where receiver_id matches the user and receive_design matches the role
        tracking_entry = Tracking.objects.filter(
            file_id=file_id,
            receiver_id=user,
            receive_design__name=current_designation_name
        ).first()
        
        if tracking_entry:
            item['receiver_id_id'] = tracking_entry.receiver_id.id if tracking_entry.receiver_id else None
            item['receiver_design_id'] = tracking_entry.receive_design.id if tracking_entry.receive_design else None
            item['receiver_designation_name'] = tracking_entry.receive_design.name if tracking_entry.receive_design else None
    
    outboxd = view_outbox(request.user.username, designations, "ps1")

    # Sort the inbox data by upload_date
    data = sorted(data, key=lambda x: datetime.fromisoformat(x['upload_date']), reverse=True)

    # Convert upload_date to a datetime object for each item in the data
    for item in data:
        item['upload_date'] = datetime.fromisoformat(item['upload_date'])

    # Fetch user notifications if any
    notifs = request.user.notifications.all().values()  # Assuming notifications are a related field

    context = {
        'receive_design': HoldsDesignationSerializer(abcd).data,
        'in_file': data,
        'department': request.user.extrainfo.department.name,
        'notifications': list(notifs),
    }

    return Response(context)


# TO GET ALL THE USER DRAFTS USING HOLDS DESIGNATION ID 
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def draftView(request, username):

    print(username)
    user = User.objects.get(username=username)
    user_id = user.id

    hold_designation = HoldsDesignation.objects.filter(user_id=user_id)
    id = hold_designation[0].id
    print(id)
    if request.method == 'GET':
        designation = str(Designation.objects.get(id=HoldsDesignation.objects.select_related('user', 'working', 'designation').get(id=id).designation_id))
        if designation == "student":
            return Response({"message": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        indents = IndentFile.objects.filter(file_info__in=request.user.extrainfo.uploaded_files.all()).select_related('file_info')
        department = request.user.extrainfo.department.name
        # print("gaurva")
        print(department) 
        indent_ids = [indent.file_info for indent in indents]
        filed_indents = Tracking.objects.filter(file_id__in=indent_ids)
        filed_indent_ids = [indent.file_id for indent in filed_indents]
        draft = list(set(indent_ids) - set(filed_indent_ids))
        draft_indent = IndentFile.objects.filter(file_info__in=draft).values("file_info")
        draft_files = File.objects.filter(id__in=draft_indent).order_by('-upload_date')
        print(draft_files)
        abcd = HoldsDesignation.objects.get(pk=id)
        s = str(abcd).split(" - ")
        serializer = FileSerializer(draft_files, many=True)
        return Response({
            "department": department,
            "files": serializer.data
        })
    else:
        return Response({"message": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def inwardIndents(request, id):
    if request.method == 'GET':
        designation = str(Designation.objects.get(id=HoldsDesignation.objects.select_related('user', 'working', 'designation').get(id=id).designation_id))
        abcd = HoldsDesignation.objects.get(pk=id)
        
        data = view_inbox(request.user.username, designation, "ps1")
        # outboxd = view_outbox(request.user.username, designations, "ps1")
        
        data = sorted(data, key=lambda x: datetime.fromisoformat(x['upload_date']), reverse=True)
        for item in data:
            item['upload_date'] = datetime.fromisoformat(item['upload_date'])
            
        response_data = {
            'receive_design': str(abcd),
            'in_file': data
        }
        
        return Response(response_data)
    else:
        return Response({"message": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def indentFile(request, id):
    if request.method == 'GET':
        try:
            indent_file = IndentFile.objects.select_related('file_info').get(file_info=id)
        except IndentFile.DoesNotExist:
            return Response({"message": "Indent file does not exist"}, status=status.HTTP_404_NOT_FOUND)
        
        # Retrieve tracking details for the indent file
        track = Tracking.objects.select_related('file_id__uploader__user','file_id__uploader__department','file_id__designation','current_id__user','current_id__department','current_design__user','current_design__working','current_design__designation','receiver_id','receive_design').filter(file_id=indent_file.file_info)
        
        # Retrieve ExtraInfo, HoldsDesignation, and filtered designations
        extrainfo = ExtraInfo.objects.select_related('user','department').all()
        holdsdesignations = HoldsDesignation.objects.select_related('user','working','designation').all()
        designations = HoldsDesignation.objects.select_related('user','working','designation').filter(user=request.user)

        
        # Serialize the data
        indent_serializer = IndentFileSerializer(indent_file)
        track_serializer = TrackingSerializer(track, many=True)
        extrainfo_serializer = ExtraInfoSerializer(extrainfo, many=True)
        holdsdesignations_serializer = HoldsDesignationSerializer(holdsdesignations, many=True)
        designations_serializer = HoldsDesignationSerializer(designations, many=True)
        
        # Construct response data
        response_data = {
            'indent_file': indent_serializer.data,
            'track': track_serializer.data,
            'extrainfo': extrainfo_serializer.data,
            'holdsdesignations': holdsdesignations_serializer.data,
            'designations': designations_serializer.data
        }
        
        return Response(response_data)
    else:
        return Response({"message": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ForwardIndentFile(request, id):
    
    if request.method == 'POST':
        print('hdfjaldfalk' , request.data)
        try:
            indent = IndentFile.objects.select_related('file_info').get(file_info=id)
            file = indent.file_info_id
            track = Tracking.objects.select_related('file_id__uploader__user','file_id__uploader__department','file_id__designation','current_id__user','current_id__department','current_design__user','current_design__working','current_design__designation','receiver_id','receive_design').filter(file_id=file)
        except IndentFile.DoesNotExist:
            return Response({"message": "Indent file does not exist"}, status=status.HTTP_404_NOT_FOUND)
        
        # Extracting data from request.POST
        remarks = request.data.get('remarks')
        sender_design_id = request.data.get('sender')
        receiverHdid = request.data.get('receive')
        upload_file = request.FILES.get('myfile')

        # Retrieving sender and receiver designations
        sender_designationobj = HoldsDesignation.objects.get(id=sender_design_id).designation
        sender_designation_name = sender_designationobj.name
        receiverHdobj = HoldsDesignation.objects.get(id=receiverHdid)
        receiver = receiverHdobj.user.username
        receive_design = receiverHdobj.designation.name

        try:
            receiver_id = User.objects.get(username=receiver)
        except User.DoesNotExist:
            return Response({"message": "Enter a valid destination"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            receive_design = Designation.objects.get(name=receive_design)
        except Designation.DoesNotExist:
            return Response({"message": "Enter a valid designation"}, status=status.HTTP_400_BAD_REQUEST)

        # Forwarding the file
        forwarded_file_id = forward_file(
            file_id=file.id,
            receiver=receiver_id,
            receiver_designation=receive_design,
            file_extra_JSON={"key": 2},
            remarks=remarks,
            file_attachment=upload_file
        )
        office_module_notif(request.user, receiver_id)
        # Updating indent approvals if necessary
        if (str(receive_design) in dept_admin_design):
                        indent.head_approval=True
        elif ((
                (sender_designation_name in dept_admin_design)
                    or
                    (sender_designation_name == "ps_admin")
                    )
                    and (str(receive_design) == "Accounts Admin")):
                    indent.director_approval=True
                    indent.financial_approval=True
                    indent.head_approval=True

        indent.save()

        # Serializing the data
        indent_serializer = IndentFileSerializer(indent)
        track_serializer = TrackingSerializer(track, many=True)

        # Constructing response data
        response_data = {
            'indent_file': indent_serializer.data,
            'track': track_serializer.data,
            'message': 'Indent File Forwarded successfully'
        }

        return Response(response_data, status=status.HTTP_200_OK)
    else:
        return Response({"message": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def archieve_file(request,id):
    file_id=request.GET.get('file_id')
    print(file_id)
    res = archive_file(file_id)
    if res:
        return Response({"message": "File has been archived successfully"})
    else:
        return Response({"message": "Unsuccessful in archiving file"})


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def entry(request,id):

    designation = str(Designation.objects.get(id=HoldsDesignation.objects.select_related('user', 'working', 'designation').get(id=id).designation_id))
    if request.method == 'GET': 

        if  designation not in dept_admin_design + ["ps_admin"]:
            return Response({"message": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)

        # Get department name
        department = request.user.extrainfo.department.name

        # Filter indent files based on user's designation
        if request.session.get('currentDesignationSelected') == "dept_admin":
            indent_files = IndentFile.objects.filter(file_info__uploader__department__name=department)
        else:
            indent_files = IndentFile.objects.all()

        serializer = IndentFileSerializer(indent_files, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        print(designation)
        if str(designation) not in dept_admin_design + ["ps_admin"]:
            return Response({"message": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)

        id = request.data.get('id')
        if not id:
            return Response({"message": "ID parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            request_file = File.objects.select_related('uploader').get(id=id)
            requester = request_file.uploader.user
            # persons = ExtraInfo.objects.filter(user_type__in=["staff"])
            corresponding_indent_file = IndentFile.objects.get(file_info=request_file)
            
            serializer = {
                'request_file': FileSerializer(request_file).data,
                'requester': requester.username,
                # 'persons': persons.values(),
                'corresponding_indent_file': IndentFileSerializer(corresponding_indent_file).data
            }
            return Response(serializer)
        except File.DoesNotExist:
            return Response({"message": "File with given ID does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except IndentFile.DoesNotExist:
            return Response({"message": "Corresponding indent file does not exist"}, status=status.HTTP_404_NOT_FOUND)
        
        
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def stockEntryView(request,id):
    # print(request.user.id); 

    designation =str(Designation.objects.get(id=HoldsDesignation.objects.select_related('user', 'working', 'designation').get(id=id).designation_id))
    if str(designation) not in dept_admin_design + ["ps_admin"]:
            return Response({"message": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)

    department = request.user.extrainfo.department

    if designation in dept_admin_design:
        stocks = StockEntry.objects.filter(item_id__file_info__uploader__department=department)
    elif designation == "ps_admin":
        stocks = StockEntry.objects.all()
    else:
        return Response({"message": "Invalid designation"}, status=status.HTTP_400_BAD_REQUEST)

    serializer = StockEntrySerializer(stocks, many=True)
    return Response(serializer.data)


# to check the current stock situation in the module 
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def currentStockView(request,id):

    designation =str(Designation.objects.get(id=HoldsDesignation.objects.select_related('user', 'working', 'designation').get(id=id).designation_id))

    if request.method == 'GET':
        # Check if the user is authorized
        if str(designation) not in dept_admin_design + ["ps_admin"]:
            return Response({"message": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)

        # Handle GET request
        department = request.user.extrainfo.department

        if designation in dept_admin_design:
            # Only show stocks of the department for department admin
            stocks = StockItem.objects.filter(department=department)
        elif designation == "ps_admin":
            # Show all stocks for PS admin
            stocks = StockItem.objects.all()
        else:
            return Response({"message": "Invalid designation"}, status=status.HTTP_403_FORBIDDEN)

        grouped_items = stocks.values('StockEntryId__item_id__item_type', 'department').annotate(total_quantity=Count('id'))

        grouped_items_list = [
            {
                'item_type': item['StockEntryId__item_id__item_type'],
                'department': DepartmentInfo.objects.get(id=item['department']).name,
                'total_quantity': item['total_quantity']
            }
            for item in grouped_items
        ]

        return Response(grouped_items_list)

    elif request.method == 'POST':
        # Handle POST request
        department = request.data.get('department')
        item_type = request.data.get('item_type')

        if not department or not item_type:
            return Response({"message": "Missing required parameters"}, status=status.HTTP_400_BAD_REQUEST)

        # Filter StockItem based on provided filters
        StockItems = StockItem.objects.filter(
            department=department,
            StockEntryId__item_id__item_type=item_type
        )

        grouped_items = StockItems.values('StockEntryId__item_id__item_type', 'department').annotate(total_quantity=Count('id'))

        grouped_items_list = [
            {
                'item_type': item['StockEntryId__item_id__item_type'],
                'department': DepartmentInfo.objects.get(id=department).name,
                'total_quantity': item['total_quantity']
            }
            for item in grouped_items
        ]

        # Serialize the data
        # serializer = StockItemSerializer(grouped_items_list, many=True)

        firstStock = StockItemSerializer(StockItems.first())

        return Response({'stocks': grouped_items_list, 'first_stock': firstStock.data})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def stock_entry_item_view(request,id):
    designation = str(Designation.objects.get(id=HoldsDesignation.objects.select_related('user', 'working', 'designation').get(id=id).designation_id))

    if str(designation) not in dept_admin_design + ["ps_admin"]:
            return Response({"message": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)
    department = request.data.get('department')
    file_id=request.data.get('file_id')
    temp=File.objects.get(id=file_id)
    temp1=IndentFile.objects.get(file_info=temp)
    stock_entry=StockEntry.objects.get(item_id=temp1)

    stocks=StockItem.objects.filter(StockEntryId=stock_entry)
    serializer = StockItemSerializer(stocks, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def stockDelete(request,id):
    designation = str(Designation.objects.get(id=HoldsDesignation.objects.select_related('user', 'working', 'designation').get(id=id).designation_id))

    if str(designation) not in dept_admin_design + ["ps_admin"]:
            return Response({"message": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)

    
    id = request.POST.get('id')
    try:
        stock = StockItem.objects.get(id=id)
    except StockItem.DoesNotExist:
        return Response({"message": 'Stock item with given ID does not exist',"id":id}, status=status.HTTP_404_NOT_FOUND)

    stock.delete()
    return Response({"message": "Stock item deleted successfully"}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def stockTransfer(request,id):
    designation = str(Designation.objects.get(id=HoldsDesignation.objects.select_related('user', 'working', 'designation').get(id=id).designation_id))

    if str(designation) not in dept_admin_design + ["ps_admin"]:
            return Response({"message": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)
    
    id=request.POST.get('id')
    temp=File.objects.get(id=id)
    temp1=IndentFile.objects.get(file_info=temp)

    item_type_required =temp1.item_type

    available_items=StockItem.objects.filter(
        StockEntryId__item_id__item_type=item_type_required,
        inUse=False  
    )

    print(available_items)
    serializer = StockItemSerializer(available_items, many=True)
    return Response(serializer.data)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def performTransfer(request,id):
    designation = str(Designation.objects.get(id=HoldsDesignation.objects.select_related('user', 'working', 'designation').get(id=id).designation_id))

    if str(designation) not in dept_admin_design + ["ps_admin"]:
        return Response({"message": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)
    
    selected_stock_items = request.data.getlist('selected_stock_items[]')
    indentId = request.data.get('indentId')
    dest_location = request.data.get('dest_location')

    list = selected_stock_items[0];
    stock_items_list = ast.literal_eval(list)
    
    myIndent = IndentFile.objects.get(file_info=indentId)

    moreStocksRequired = myIndent.quantity - len(stock_items_list)  
    # print('dest_destination : ', myIndent.file_info.uploader.department)
    
    stock_transfers = []
    for item in stock_items_list:
        stock_item  = StockItem.objects.get(id=item)
        # print('src dest : ', stock_item.department)

        store_cur_dept = stock_item.department;
        store_cur_location = stock_item.location;
        
        # changing the attributes for this stock item as being transferred.
        stock_item.department=myIndent.file_info.uploader.department;
        stock_item.location=dest_location;
        stock_item.inUse= True
        stock_item.isTransferred= True
        # if a stock_item is been transferred then obviously it will be put into use.
        stock_item.save();


        stock_transfer = StockTransfer.objects.create(
            indent_file=myIndent,
            src_dept=store_cur_dept,
            dest_dept=myIndent.file_info.uploader.department,
            stockItem=stock_item,
            src_location=store_cur_location,
            dest_location=dest_location
        )

        stock_transfers.append(stock_transfer)


    if(moreStocksRequired==0):
        myIndent.purchased=True
    else:
        myIndent.quantity=moreStocksRequired;
        
    myIndent.save();

    
    serializer = StockTransferSerializer(stock_transfers,many=True)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def archieveview(request,username):
    # retrieves user id from username
    user = User.objects.get(username=username)
    user_id = user.id
    currentDesignation = request.GET.get('role')  # Capture role from headers
    if currentDesignation=="student":
        return Response({'error': 'Student are not allowd to access this view'}, status=403)
    
    designation = HoldsDesignation.objects.filter(user=request.user, designation__name=currentDesignation).first()
    if not designation:
        return Response({'error': 'Designation not found or mismatch'}, status=404)
    print("id : ",id);
    print("request.user : ",request.user);
    
    abcd = HoldsDesignation.objects.filter(user_id=user_id, designation__name=currentDesignation).first()
    designations = abcd.designation.name
    if not abcd:
        return Response({'error': 'User does not hold the specified designation.'}, status=404)
    print("designations : ",designations)
    
    archived_files = view_archived(
    username=request.user,
    designation=designations,
    src_module="ps1"
    )

    print("archived_files : ",archived_files);
    for files in archived_files:
        files['upload_date']=datetime.fromisoformat(files['upload_date'])
        files['upload_date']=files['upload_date'].strftime("%B %d, %Y, %I:%M %p") 
    
    notifs = request.user.notifications.all().values()
    context = {
        'archieves' : archived_files,
        'designations': designations,
        'notifications':list(notifs)
    }
    return Response(context)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def outboxview2(request, username):
    user = User.objects.get(username=username)
    user_id = user.id
    currentDesignation = request.GET.get('role')
    
    if currentDesignation == "student":
        return Response({'error': 'Students are not allowed to access this view'}, status=403)
    
    designation = HoldsDesignation.objects.filter(user=request.user, designation__name=currentDesignation).first()
    if not designation:
        return Response({'error': 'Designation not found'}, status=404)
    
    abcd = HoldsDesignation.objects.filter(user_id=user_id, designation__name=currentDesignation).first()
    if not abcd:
        return Response({'error': 'User does not hold the specified designation.'}, status=404)
    
    designations = abcd.designation.name
    data = view_outbox(request.user.username, designations, "ps1")
    
    data = sorted(data, key=lambda x: datetime.fromisoformat(x['upload_date']), reverse=True)
    
    file_ids = [item['id'] for item in data]
    indent_files = IndentFile.objects.filter(file_info_id__in=file_ids).values(
        'file_info_id', 'description', 'indent_name', 'head_approval', 'director_approval', 'financial_approval'
    )
    indent_files_dict = {item['file_info_id']: item for item in indent_files}
    
    for item in data:
        file_id = item['id']
        tracking = Tracking.objects.filter(file_id=file_id).select_related('receiver_id').last()
        
        if tracking and tracking.receiver_id:
            receiver_user = tracking.receiver_id
            item['receiver_username'] = receiver_user.username
        else:
            item['receiver_username'] = None
        
        item['upload_date'] = datetime.fromisoformat(item['upload_date'])
        
        if file_id in indent_files_dict:
            item.update(indent_files_dict[file_id])
    
    notifs = request.user.notifications.all().values()

    print("in_file",data);
    
    context = {
        'receive_design': HoldsDesignationSerializer(abcd).data,
        'in_file': data,
        'department': request.user.extrainfo.department.name,
        'notifications': list(notifs),
    }
    
    return Response(context)

# def outboxview2(request, username):
#     # retrieves user id from user object which is retrieved using username from User class
#     user = User.objects.get(username=username)
#     user_id = user.id
#     currentDesignation = request.GET.get('role')  # Capture role from headers
#     if currentDesignation=="student":
#         return Response({'error': 'Student are not allowd to access this view'}, status=403)
 
#     designation = HoldsDesignation.objects.filter(user=request.user, designation__name=currentDesignation).first()

#     if not designation:
#         return Response({'error': 'Designation not found'}, status=404)

#     abcd = HoldsDesignation.objects.filter(user_id=user_id, designation__name=currentDesignation).first()
#     if not abcd:
#         return Response({'error': 'User does not hold the specified designation.'}, status=404)


#     designations = abcd.designation.name

#     # Fetch inbox and outbox data
#     data = view_outbox(request.user.username, designations, "ps1")

#     # Sort the inbox data by upload_date
#     data = sorted(data, key=lambda x: datetime.fromisoformat(x['upload_date']), reverse=True)

#     # Format the upload_date to datetime object
#     for item in data:
#         file_id = item['id']  # Assumes id is the primary key in the serialized file data
#         tracking = Tracking.objects.filter(file_id=file_id).select_related('receiver_id').last()

#         if tracking and tracking.receiver_id:
#             receiver_user = tracking.receiver_id  # Assuming receiver_id points to ExtraInfo
#             item['receiver_username'] = receiver_user.username
#         else:
#             item['receiver_username'] = None

#     for item in data:
#         item['upload_date'] = datetime.fromisoformat(item['upload_date'])

#     notifs = request.user.notifications.all().values()  # Assuming notifications are a related field

#     file_ids = [item['id'] for item in data]
#     print("file_ids",file_ids);
#     indent_files = IndentFile.objects.filter(file_info_id__in=file_ids).values(
#         'file_info_id','indent_name','description','head_approval', 'director_approval', 'financial_approval'
#     )
#     print(indent_files);
#     context = {
#         'receive_design': HoldsDesignationSerializer(abcd).data,
#         'in_file': data,
#         'department': request.user.extrainfo.department.name,
#         'indent_files': list(indent_files),
#         'notifications': list(notifs),
#     }

#     return Response(context)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def stockEntry(request,username):
    # retrieves id from username
    user = User.objects.get(username=username)
    user_id = user.id
    # print(request.data);
    currentDesignation = request.FILES.get('role')
    designation = HoldsDesignation.objects.filter(user=request.user, designation__name=currentDesignation).first()
    # if str(designation) not in dept_admin_design + ["ps_admin"]:
    #         return Response({"message": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'POST':

        id = request.POST.get('id')
        print(type(id))
        print(id)
        vendor = request.POST.get('vendor')
        current_stock = request.POST.get('current_stock')
        # received_date = request.POST.get('received_date')
        bill = request.FILES.get('bill')
        recieved_date = request.data.get('received_date')
        location = request.POST.get('location')
        print("location-",location)
        try:
            # temp1 = File.objects.get(id=id)
            temp = IndentItem.objects.get(id=id)
        except (File.DoesNotExist, IndentFile.DoesNotExist):
            return Response({"message": "File with given ID does not exist"}, status=status.HTTP_404_NOT_FOUND)

        item_id = temp
        print(type(item_id))
        print(item_id)
        dealing_assistant_id = request.user.extrainfo


        stock_entry = StockEntry.objects.create(
                item_id=item_id,
                vendor=vendor,
                current_stock=current_stock,
                dealing_assistant_id=dealing_assistant_id,
                bill=bill,
                recieved_date=recieved_date,
                location=location
            )

        # Marking the indent file as done
        temp.purchased = True
        temp.save()

        serializer = StockEntrySerializer(stock_entry)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
@api_view(['POST'])
# @permission_classes([IsAuthenticated])
def forwardIndent(request, id):
    try:
        indent=IndentFile.objects.select_related('file_info').get(file_info=id)
        file=indent.file_info
        print("file details",file);
        upload_file = request.FILES.get('file')
        receiverName = request.data.get('forwardTo')
        receiver_id = User.objects.get(username=receiverName)
        receive_design = request.data.get('receiverDesignation')
        remarks = request.data.get('remarks')
        print("remarks",remarks);
        sender_designation_name = request.data.get('role')
        # vkjain -> director
        print(receiver_id) #bhartenduks 
        # print(receive_design) #Director
        # print(remarks) #None
        # print(upload_file) #filename
        # print(file) #file object
        print(receiverName) #bhartenduks
        print("uploader role"+sender_designation_name) #HOD (CSE)
        print("receive designation" + receive_design) #Director
  
        forwarded_file_id = forward_file(
                    file_id=file.id,
                    receiver=receiver_id,
                    receiver_designation=receive_design,
                    file_extra_JSON={"key": 2},
                    remarks=remarks,
                    file_attachment=upload_file
                )
        print("noti",request.user);
        print("noti2",receiver_id);
        # iwd_notif(request.user, receiver_id, "Request_added")
        purchase_notif(request.user,receiver_id)
        # office_module_notif(request.user, receiver_id)
        if((sender_designation_name in ["HOD (CSE)", "HOD (ECE)", "HOD (ME)", "HOD (SM)", "HOD (Design)", "HOD (Liberal Arts)", "HOD (Natural Science)"]) and (str(receive_design) in ["Director","Registrar"])):
            indent.head_approval=True
        elif ((sender_designation_name in ["Director","Registrar"]) and (str(receive_design) in ["ps_admin"]) ):
            indent.director_approval=True
        elif ((sender_designation_name in ["Professor","Assistant Professor"]) and (str(receive_design) in ["ps_admin"] )):
            indent.purchased=True
        elif ((sender_designation_name in ["Director","Registrar"]) and (str(receive_design) in ["Professor","Accounts Admin","Assistant Professor"]) and indent.purchased==True):
            print("financial approval");
            indent.director_approval=True
            indent.financial_approval=True

        # elif ((sender_designation_name in ["ps_admin"]) and str(receive_design) in ["Director","Registrar"]):
        #     indent.head_approval=True
        #     indent.director_approval=True
        elif ((sender_designation_name == "Accounts Admin") and ((str(receive_design) in dept_admin_design) or str(receive_design) == "ps_admin")):
            indent.financial_approval=True

        indent.save()

        # office_module_notif(receiverName, receiver_id)
        # messages.success(request, 'Indent File Forwarded successfully')
        return Response({"message": "File forwarded successfully.", "forwarded_file_id": forwarded_file_id}, status=status.HTTP_200_OK)
    except IndentFile.DoesNotExist:
        return Response({"error": "Indent not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createProposal(request):
    try:
        if request.method == 'POST':
            print("Processing indent request...")
            
            # Extract data from request
            uploader = request.user.extrainfo  # Fetch ExtraInfo of the uploader
            print( uploader)
            subject = request.data.get('title')
            print("subject :"+subject)
            description = request.data.get('description')
            print("description :"+description)
            username = request.data.get('forwardTo')
            print("username :"+username)
            designation_name = request.data.get('role')  # Fetch role from request.data
            print("designation_name :"+designation_name)
            receiver_designation = request.data.get('receiverDesignation')
            print("receiver_designation :"+receiver_designation)
            
            # Fetch Designation and User objects
            designation = get_object_or_404(Designation, name=designation_name)
            receiver = get_object_or_404(User, username=username)
            
            # Handle file upload
            upload_file = request.FILES.get('file')
            
            # Create File object
            file_id = create_file(
                uploader=request.user.username,
                uploader_designation=designation,
                receiver=username,
                receiver_designation=receiver_designation,
                src_module="ps1",
                src_object_id="",
                file_extra_JSON={"value": 2},
                attached_file=upload_file
            )
            
            # Create IndentFile object
            indent_file = IndentFile.objects.create(
                file_info=get_object_or_404(File, pk=file_id),
                indent_name=subject,  # Use the subject as the indent name
                description=description,  # Use the description from the request
                head_approval=False,
                director_approval=False,
                financial_approval=False,
                purchased=False,
            )
            
            # Handle multiple items in the proposal
            items = request.data.get('items', [])  # Expecting a list of item dictionaries
            for item in items:
                IndentItem.objects.create(
                    indent_file=indent_file,
                    item_name=item.get('item_name', ''),
                    quantity=item.get('quantity', 1),
                    present_stock=item.get('present_stock', 0),
                    estimated_cost=item.get('estimated_cost', 0),
                    purpose=item.get('purpose', ''),
                    specification=item.get('specification', ''),
                    item_type=item.get('item_type', ''),
                    item_subtype=item.get('item_subtype', 'computers'),
                    nature=item.get('nature', False),
                    indigenous=item.get('indigenous', False),
                    replaced=item.get('replaced', False),
                    budgetary_head=item.get('budgetary_head', ''),
                    expected_delivery=item.get('expected_delivery', None),  # Handle DateField
                    sources_of_supply=item.get('sources_of_supply', ''),
                )
            
            purchase_notif(request.user,receiver)
            
            # Auto-approve if receiver is 'ps_admin'
            if receiver_designation == "ps_admin":
                indent_file.purchased = True
                indent_file.save()
            
            # Serialize the IndentFile object
            indent_file_serializer = IndentFileSerializer(indent_file)
            
            print("Indent Filed Successfully!")
            return Response({
                'indent_file': indent_file_serializer.data,
                'message': 'Indent Filed Successfully!',
            }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    
def user_suggestions(request):
    # query = request.GET.get('q', '')  # Get the query parameter
    users = User.objects.all().values('username')
    # user = Faculty.objects.all().values('id')
    # print(users)
    # print(user)
    return JsonResponse({'users': list(users)})

def user_suggestions(request):
    # query = request.GET.get('q', '')  # Get the query parameter
    users = User.objects.all().values('username')
    # user = Faculty.objects.all().values('id')
    # print(users)
    # print(user)
    return JsonResponse({'users': list(users)})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_indents_view(request, username):
    try:
        # Validate user
        user = User.objects.get(username=username)
        if user != request.user:
            return Response({'error': 'Unauthorized access'}, status=status.HTTP_403_FORBIDDEN)

        # Get all files created by this user
        created_files = File.objects.filter(uploader=user.extrainfo).order_by('-upload_date')
        
        # Get associated indent files
        indent_files = IndentFile.objects.filter(
            file_info__in=created_files
        ).select_related(
            'file_info'
        ).prefetch_related(
            'items'
        ).order_by('-file_info__upload_date')

        # Serialize the data
        data = []
        for indent in indent_files:
            # Get last tracking info if exists
            tracking = Tracking.objects.filter(file_id=indent.file_info_id).select_related(
                'receiver_id'
            ).last()
            
            indent_data = {
                'id': indent.file_info_id,
                'indent_name': indent.indent_name,
                'description': indent.description,
                'upload_date': indent.file_info.upload_date,
                'status': {
                    'head_approval': indent.head_approval,
                    'director_approval': indent.director_approval,
                    'financial_approval': indent.financial_approval,
                    'purchased': indent.purchased
                },
                'current_receiver': tracking.receiver_id.username if tracking else None,
                'items': [{
                    'name': item.item_name,
                    'quantity': item.quantity,
                    'estimated_cost': item.estimated_cost
                } for item in indent.items.all()]
            }
            data.append(indent_data)

        return Response({
            'count': len(data),
            'results': data,
            'department': user.extrainfo.department.name
        })

    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)