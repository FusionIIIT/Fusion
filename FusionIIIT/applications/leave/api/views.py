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

@api_view(['GET'])
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

@api_view(['GET'])
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

@api_view(['GET'])
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

@api_view(['GET'])
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

@api_view(['GET'])
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

@api_view(['GET'])
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

@api_view(['GET'])
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

@api_view(['GET'])
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

@api_view(['GET'])
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

@api_view(['GET'])
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

@api_view(['GET'])
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

@api_view(['GET'])
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

@api_view(['GET'])
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

@api_view(['GET'])
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