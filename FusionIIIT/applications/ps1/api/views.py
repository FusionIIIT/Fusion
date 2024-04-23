from rest_framework.permissions import IsAuthenticated #type:ignore
from rest_framework.response import Response #type:ignore
from rest_framework import status #type:ignore
from rest_framework.decorators import api_view, permission_classes #type:ignore
from applications.ps1.models import IndentFile, File,StockTransfer,StockEntry,StockItem
from applications.globals.models import HoldsDesignation, Designation,ExtraInfo,DepartmentInfo
from applications.filetracking.models import Tracking
from .serializers import IndentFileSerializer ,FileSerializer,ExtraInfoSerializer,HoldsDesignationSerializer,TrackingSerializer,StockEntrySerializer,StockItemSerializer,StockTransferSerializer
from django.utils import timezone
from applications.filetracking.sdk.methods import *
from datetime import datetime
from django.http import HttpResponseForbidden
from django.db.models import Q,Count
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
import ast

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
    if request.method == 'GET':
        designations = HoldsDesignation.objects.filter(user=request.user)
        designations_serialized = HoldsDesignationSerializer(designations,many=True)
        return Response(designations_serialized.data)
    else:
        return Response({"message": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createProposal(request):
    if request.method == 'POST':
        # print('our requested data :',request.data)
        # Process the POST request data
        uploader = request.user.extrainfo
        subject = request.data.get('title')
        description = request.data.get('desc')
        design = request.data.get('design')
        designation = Designation.objects.get(id=HoldsDesignation.objects.select_related('user', 'working', 'designation').get(id=design).designation_id)
        upload_file = request.FILES.get('myfile')
        item_name = request.data.get('item_name')
        quantity = request.data.get('quantity')
        present_stock = request.data.get('present_stock')
        estimated_cost = request.data.get('estimated_cost')
        purpose = request.data.get('purpose')
        specification = request.data.get('specification')
        item_type = request.data.get('item_type')
        nature = request.data.get('nature')
        indigenous = request.data.get('indigenous')
        replaced = request.data.get('replaced')
        budgetary_head = request.data.get('budgetary_head')
        expected_delivery = request.data.get('expected_delivery')
        sources_of_supply = request.data.get('sources_of_supply')
        head_approval = False
        director_approval = False
        financial_approval = False
        purchased = False
        
        # Create File object
        file = File.objects.create(
            uploader=uploader,
            description=description,
            subject=subject,
            designation=designation,
            upload_file=upload_file
        )

        # Create IndentFile object
        indent_file = IndentFile.objects.create(
            file_info=file,
            item_name=item_name,
            quantity=quantity,
            present_stock=present_stock,
            estimated_cost=estimated_cost,
            purpose=purpose,
            specification=specification,
            item_type=item_type,
            nature=nature,
            indigenous=indigenous,
            replaced=replaced,
            budgetary_head=budgetary_head,
            expected_delivery=expected_delivery,
            sources_of_supply=sources_of_supply,
            head_approval=head_approval,
            director_approval=director_approval,
            financial_approval=financial_approval,
            purchased=purchased,
        )

        # Serialize response data
        file_serializer = FileSerializer(file)
        indent_file_serializer = IndentFileSerializer(indent_file)

        # Return response
        return Response({
            'file': file_serializer.data,
            'indent_file': indent_file_serializer.data,
            'message': 'Indent Filed Successfully!'
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def indentView(request, id):
    if request.method == 'GET':
        tracking_objects = Tracking.objects.all()
        tracking_obj_ids = [obj.file_id for obj in tracking_objects]
        draft_indent = IndentFile.objects.filter(file_info__in=tracking_obj_ids)
        draft = [indent.file_info.id for indent in draft_indent]
        draft_files = File.objects.filter(id__in=draft).order_by('-upload_date')
        indents = [file.indentfile for file in draft_files]
        abcd = HoldsDesignation.objects.get(pk=id)
        s = str(abcd).split(" - ")

        serializer = IndentFileSerializer(indents, many=True)
        return Response(serializer.data)
    else:
        return Response({"message": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


# TO GET ALL THE USER DRAFTS USING HOLDS DESIGNATION ID 
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def draftView(request, id):
    if request.method == 'GET':
        designation = str(Designation.objects.get(id=HoldsDesignation.objects.select_related('user', 'working', 'designation').get(id=id).designation_id))
        if designation == "student":
            return Response({"message": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        indents = IndentFile.objects.filter(file_info__in=request.user.extrainfo.uploaded_files.all()).select_related('file_info')
        indent_ids = [indent.file_info for indent in indents]
        filed_indents = Tracking.objects.filter(file_id__in=indent_ids)
        filed_indent_ids = [indent.file_id for indent in filed_indents]
        draft = list(set(indent_ids) - set(filed_indent_ids))
        draft_indent = IndentFile.objects.filter(file_info__in=draft).values("file_info")
        draft_files = File.objects.filter(id__in=draft_indent).order_by('-upload_date')
        abcd = HoldsDesignation.objects.get(pk=id)
        s = str(abcd).split(" - ")
        serializer = FileSerializer(draft_files, many=True)
        return Response(serializer.data)
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
    


# Forwarding Indent 
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ForwardIndentFile(request, id):
    
    if request.method == 'POST':
        # print('hdfjaldfalk' , request.data);
        try:
            indent = IndentFile.objects.select_related('file_info').get(file_info=id)
            file = indent.file_info
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
        

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def stockEntry(request,id):

    # print(request.data);
    
    designation = str(Designation.objects.get(id=HoldsDesignation.objects.select_related('user', 'working', 'designation').get(id=id).designation_id))
    # print(designation)
    if str(designation) not in dept_admin_design + ["ps_admin"]:
            return Response({"message": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'POST':

        id = request.POST.get('id')
        vendor = request.POST.get('vendor')
        current_stock = request.POST.get('current_stock')
        # received_date = request.POST.get('received_date')
        bill = request.FILES.get('bill')
        location = request.POST.get('location')

        try:
            temp1 = File.objects.get(id=id)
            temp = IndentFile.objects.get(file_info=temp1)
        except (File.DoesNotExist, IndentFile.DoesNotExist):
            return Response({"message": "File with given ID does not exist"}, status=status.HTTP_404_NOT_FOUND)

        item_id = temp
        dealing_assistant_id = request.user.extrainfo

        print(request.data)

        stock_entry = StockEntry.objects.create(
                item_id=item_id,
                vendor=vendor,
                current_stock=current_stock,
                dealing_assistant_id=dealing_assistant_id,
                bill=bill,
                # received_date=received_date,
                location=location
            )

        # Marking the indent file as done
        temp.purchased = True
        temp.save()

        serializer = StockEntrySerializer(stock_entry)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    

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
