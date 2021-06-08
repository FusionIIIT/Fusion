from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.forms.models import model_to_dict
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes,authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from applications.globals.models import User,ExtraInfo
from applications.leave.models import LeaveType,LeavesCount,Leave,ReplacementSegment,ReplacementSegmentOffline,LeaveSegment,LeaveRequest
from applications.leave.models import LeaveAdministrators,LeaveMigration,RestrictedHoliday,ClosedHoliday,VacationHoliday,LeaveOffline,LeaveSegmentOffline
from . import serializers

@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def leave_type_api(request):

    if request.method == 'GET':
        leave_type = LeaveType.objects.all()
        leave_type = serializers.LeaveTypeSerializers(leave_type,many=True).data
        resp = {
            'leavetype' : leave_type,
        }
        return Response(data=resp,status=status.HTTP_200_OK)
    elif request.method == 'POST':
        serializer = serializers.LeaveTypeSerializers(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def leaves_count_api(request):

    if request.method == 'GET':
        leaves_count = LeavesCount.objects.all()
        leaves_count = serializers.LeavesCountSerializers(leaves_count,many=True).data
        resp = {
            'leavescount' : leaves_count,
        }
        return Response(data=resp,status=status.HTTP_200_OK)
    elif request.method == 'POST':
        serializer = serializers.LeaveCountSerializers(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def leave_api(request):

    if request.method == 'GET':
        leave = Leave.objects.all()
        leave = serializers.LeaveSerializers(leave,many=True).data
        resp = {
            'leave' : leave,
        }
        return Response(data=resp,status=status.HTTP_200_OK)
    elif request.method == 'POST':
        serializer = serializers.LeaveSerializers(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def replacement_segment_api(request):

    if request.method == 'GET':
        replacement_segment = ReplacementSegment.objects.all()
        replacement_segment = serializers.ReplacementSegmentSerializers(replacement_segment,many=True).data
        resp = {
            'replacement_segment' : replacement_segment,
        }
        return Response(data=resp,status=status.HTTP_200_OK)
    elif request.method == 'POST':
        serializer = serializers.ReplacementSegmentSerializers(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def replacement_segment_offline_api(request):

    if request.method == 'GET':
        replacement_segment_offline = ReplacementSegmentOffline.objects.all()
        replacement_segment_offline = serializers.ReplacementSegmentOfflineSerializers(replacement_segment_offline,many=True).data
        resp = {
            'replacement_segment_offline' : replacement_segment_offline,
        }
        return Response(data=resp,status=status.HTTP_200_OK)
    elif request.method == 'POST':
        serializer = serializers.ReplacementSegmentOfflineSerializers(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def leave_segment_offline_api(request):

    if request.method == 'GET':
        leave_segment_offline = LeaveSegmentOffline.objects.all()
        leave_segment_offline = serializers.LeaveSegmentOfflineSerializers(leave_segment_offline,many=True).data
        resp = {
            'leave_segment_offline' : leave_segment_offline,
        }
        return Response(data=resp,status=status.HTTP_200_OK)
    elif request.method == 'POST':
        serializer = serializers.LeaveSegmentOfflineSerializers(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def leave_segment_api(request):

    if request.method == 'GET':
        leave_segment = LeaveSegment.objects.all()
        leave_segment = serializers.LeaveSegmentSerializers(leave_segment,many=True).data
        resp = {
            'leave_segment' : leave_segment,
        }
        return Response(data=resp,status=status.HTTP_200_OK)
    elif request.method == 'POST':
        serializer = serializers.LeaveSegmentSerializers(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def leave_request_api(request):

    if request.method == 'GET':
        leave_request = LeaveRequest.objects.all()
        leave_request = serializers.LeaveRequestSerializers(leave_request,many=True).data
        resp = {
            'leave_request' : leave_request,
        }
        return Response(data=resp,status=status.HTTP_200_OK)
    elif request.method == 'POST':
        serializer = serializers.LeaveRequestSerializers(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def leave_administrators_api(request):

    if request.method == 'GET':
        leave_administrators = LeaveAdministrators.objects.all()
        leave_administrators = serializers.LeaveAdministratorsSerializers(leave_administrators,many=True).data
        resp = {
            'leave_administrators' : leave_administrators,
        }
        return Response(data=resp,status=status.HTTP_200_OK)
    elif request.method == 'POST':
        serializer = serializers.LeaveAdministratorsSerializers(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def leave_migration_api(request):

    if request.method == 'GET':
        leave_migration = LeaveMigration.objects.all()
        leave_migration = serializers.LeaveMigrationSerializers(leave_migration,many=True).data
        resp = {
            'leave_migration' : leave_migration,
        }
        return Response(data=resp,status=status.HTTP_200_OK)
    elif request.method == 'POST':
        serializer = serializers.LeaveMigrationSerializers(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def restricted_holiday_api(request):

    if request.method == 'GET':
        restricted_holiday = RestrictedHoliday.objects.all()
        restricted_holiday = serializers.RestrictedHolidaySerializers(restricted_holiday,many=True).data
        resp = {
            'restricted_holiday' : restricted_holiday,
        }
        return Response(data=resp,status=status.HTTP_200_OK)
    elif request.method == 'POST':
        serializer = serializers.RestrictedHolidaySerializers(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def closed_holiday_api(request):

    if request.method == 'GET':
        closed_holiday = ClosedHoliday.objects.all()
        closed_holiday = serializers.ClosedHolidaySerializers(closed_holiday,many=True).data
        resp = {
            'closed_holiday' : closed_holiday,
        }
        return Response(data=resp,status=status.HTTP_200_OK)
    elif request.method == 'POST':
        serializer = serializers.ClosedHolidaySerializers(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def vacation_holiday_api(request):

    if request.method == 'GET':
        vacation_holiday = VacationHoliday.objects.all()
        vacation_holiday = serializers.VacationHolidaySerializers(vacation_holiday,many=True).data
        resp = {
            'vacation_holiday' : vacation_holiday,
        }
        return Response(data=resp,status=status.HTTP_200_OK)
    elif request.method == 'POST':
        serializer = serializers.VacationHolidaySerializers(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def leave_offline_api(request):

    if request.method == 'GET':
        leave_offline = LeaveOffline.objects.all()
        leave_offline = serializers.LeaveOfflineSerializers(leave_offline,many=True).data
        resp = {
            'leave_offline' : leave_offline,
        }
        return Response(data=resp,status=status.HTTP_200_OK)
    elif request.method == 'POST':
        serializer = serializers.LeaveOfflineSerializers(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE','PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def edit_leave_type_api(request,c_id):
    try: 
        obj = LeaveType.objects.get(id = c_id) 
    except LeaveType.DoesNotExist: 
        return Response({'message': 'The Leave Type does not exist'}, status=status.HTTP_404_NOT_FOUND)
    if request.method == 'DELETE':
        obj.delete()
        return Response({'message': 'Leave Type deleted'},status=status.HTTP_200_OK)
    elif request.method == 'PUT':
        serializer = serializers.LeaveTypeSerializers(complain,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE','PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def edit_leave_count_api(request,c_id):
    try: 
        obj = LeaveCount.objects.get(id = c_id) 
    except LeaveCount.DoesNotExist: 
        return Response({'message': 'The Leave Count does not exist'}, status=status.HTTP_404_NOT_FOUND)
    if request.method == 'DELETE':
        obj.delete()
        return Response({'message': 'Leave Count deleted'},status=status.HTTP_200_OK)
    elif request.method == 'PUT':
        serializer = serializers.LeaveCountSerializers(complain,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE','PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def edit_leave_api(request,c_id):
    try: 
        obj = Leave.objects.get(id = c_id) 
    except Leave.DoesNotExist: 
        return Response({'message': 'The Leave does not exist'}, status=status.HTTP_404_NOT_FOUND)
    if request.method == 'DELETE':
        obj.delete()
        return Response({'message': 'Leave deleted'},status=status.HTTP_200_OK)
    elif request.method == 'PUT':
        serializer = serializers.LeaveSerializers(complain,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE','PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def edit_replacement_segment_api(request,c_id):
    try: 
        obj = ReplacementSegment.objects.get(id = c_id) 
    except ReplacementSegment.DoesNotExist: 
        return Response({'message': 'The Replacement Segment does not exist'}, status=status.HTTP_404_NOT_FOUND)
    if request.method == 'DELETE':
        obj.delete()
        return Response({'message': 'Replacement Segment deleted'},status=status.HTTP_200_OK)
    elif request.method == 'PUT':
        serializer = serializers.ReplacementSegmentSerializers(complain,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE','PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def edit_replacement_segment_offline_api(request,c_id):
    try: 
        obj = ReplacementSegmentOffline.objects.get(id = c_id) 
    except ReplacementSegmentOffline.DoesNotExist: 
        return Response({'message': 'The Replacement Segment Offline does not exist'}, status=status.HTTP_404_NOT_FOUND)
    if request.method == 'DELETE':
        obj.delete()
        return Response({'message': 'Replacement Segment Offline deleted'},status=status.HTTP_200_OK)
    elif request.method == 'PUT':
        serializer = serializers.ReplacementSegmentOfflineSerializers(complain,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE','PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def edit_leave_segment_api(request,c_id):
    try: 
        obj = LeaveSegment.objects.get(id = c_id) 
    except LeaveSegment.DoesNotExist: 
        return Response({'message': 'The Leave Segment does not exist'}, status=status.HTTP_404_NOT_FOUND)
    if request.method == 'DELETE':
        obj.delete()
        return Response({'message': 'Leave Segment deleted'},status=status.HTTP_200_OK)
    elif request.method == 'PUT':
        serializer = serializers.LeaveSegmentSerializers(complain,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE','PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def edit_leave_segment_offline_api(request,c_id):
    try: 
        obj = LeaveSegmentOffline.objects.get(id = c_id) 
    except LeaveSegmentOffline.DoesNotExist: 
        return Response({'message': 'The Leave Segment Offline does not exist'}, status=status.HTTP_404_NOT_FOUND)
    if request.method == 'DELETE':
        obj.delete()
        return Response({'message': 'Leave Segment Offline deleted'},status=status.HTTP_200_OK)
    elif request.method == 'PUT':
        serializer = serializers.LeaveSegmentOfflineSerializers(complain,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE','PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def edit_leave_request_api(request,c_id):
    try: 
        obj = LeaveRequest.objects.get(id = c_id) 
    except LeaveRequest.DoesNotExist: 
        return Response({'message': 'The Leave Request does not exist'}, status=status.HTTP_404_NOT_FOUND)
    if request.method == 'DELETE':
        obj.delete()
        return Response({'message': 'Leave Request deleted'},status=status.HTTP_200_OK)
    elif request.method == 'PUT':
        serializer = serializers.LeaveRequestSerializers(complain,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE','PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def edit_leave_administrators_api(request,c_id):
    try: 
        obj = LeaveAdministrators.objects.get(id = c_id) 
    except LeaveAdministrators.DoesNotExist: 
        return Response({'message': 'The Leave Administrators does not exist'}, status=status.HTTP_404_NOT_FOUND)
    if request.method == 'DELETE':
        obj.delete()
        return Response({'message': 'Leave Administrators deleted'},status=status.HTTP_200_OK)
    elif request.method == 'PUT':
        serializer = serializers.LeaveAdministratorsSerializers(complain,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE','PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def edit_leave_migration_api(request,c_id):
    try: 
        obj = LeaveMigration.objects.get(id = c_id) 
    except LeaveMigration.DoesNotExist: 
        return Response({'message': 'The Leave Migration does not exist'}, status=status.HTTP_404_NOT_FOUND)
    if request.method == 'DELETE':
        obj.delete()
        return Response({'message': 'Leave Migration deleted'},status=status.HTTP_200_OK)
    elif request.method == 'PUT':
        serializer = serializers.LeaveMigrationSerializers(complain,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE','PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def edit_restricted_holiday_api(request,c_id):
    try: 
        obj = RestrictedHoliday.objects.get(id = c_id) 
    except RestrictedHoliday.DoesNotExist: 
        return Response({'message': 'The Restricted Holiday does not exist'}, status=status.HTTP_404_NOT_FOUND)
    if request.method == 'DELETE':
        obj.delete()
        return Response({'message': 'Restricted Holiday deleted'},status=status.HTTP_200_OK)
    elif request.method == 'PUT':
        serializer = serializers.RestrictedHolidaySerializers(complain,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE','PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def edit_closed_holiday_api(request,c_id):
    try: 
        obj = ClosedHoliday.objects.get(id = c_id) 
    except ClosedHoliday.DoesNotExist: 
        return Response({'message': 'The Closed Holiday does not exist'}, status=status.HTTP_404_NOT_FOUND)
    if request.method == 'DELETE':
        obj.delete()
        return Response({'message': 'Closed Holiday deleted'},status=status.HTTP_200_OK)
    elif request.method == 'PUT':
        serializer = serializers.ClosedHolidaySerializers(complain,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE','PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def edit_vacation_holiday_api(request,c_id):
    try: 
        obj = VacationHoliday.objects.get(id = c_id) 
    except VacationHoliday.DoesNotExist: 
        return Response({'message': 'The Vacation Holiday does not exist'}, status=status.HTTP_404_NOT_FOUND)
    if request.method == 'DELETE':
        obj.delete()
        return Response({'message': 'Vacation Holiday deleted'},status=status.HTTP_200_OK)
    elif request.method == 'PUT':
        serializer = serializers.VacationHolidaySerializers(complain,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE','PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def edit_leave_offline_api(request,c_id):
    try: 
        obj = LeaveOffline.objects.get(id = c_id) 
    except LeaveOffline.DoesNotExist: 
        return Response({'message': 'The Leave Offline does not exist'}, status=status.HTTP_404_NOT_FOUND)
    if request.method == 'DELETE':
        obj.delete()
        return Response({'message': 'Leave Offline deleted'},status=status.HTTP_200_OK)
    elif request.method == 'PUT':
        serializer = serializers.LeaveOfflineSerializers(complain,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)