from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework import serializers
from notifications.models import Notification
from applications.leave.models import LeaveType,LeavesCount,Leave,ReplacementSegment,ReplacementSegmentOffline,LeaveSegment,LeaveRequest
from applications.leave.models import LeaveAdministrators,LeaveMigration,RestrictedHoliday,ClosedHoliday,VacationHoliday,LeaveOffline,LeaveSegmentOffline
from applications.globals.models import ExtraInfo,User

class LeaveTypeSerializers(serializers.ModelSerializer):

    class Meta:
        model=LeaveType
        fields=('__all__')

class LeavesCountSerializers(serializers.ModelSerializer):

    class Meta:
        model=LeavesCount
        fields=('__all__')

class LeaveSerializers(serializers.ModelSerializer):

    class Meta:
        model=Leave
        fields=('__all__')

class ReplacementSegmentSerializers(serializers.ModelSerializer):

    class Meta:
        model=ReplacementSegment
        fields=('__all__')

class ReplacementSegmentOfflineSerializers(serializers.ModelSerializer):

    class Meta:
        model=ReplacementSegmentOffline
        fields=('__all__')

class LeaveSegmentSerializers(serializers.ModelSerializer):

    class Meta:
        model=LeaveSegment
        fields=('__all__')

class LeaveRequestSerializers(serializers.ModelSerializer):

    class Meta:
        model=LeaveRequest
        fields=('__all__')

class LeaveAdministratorsSerializers(serializers.ModelSerializer):

    class Meta:
        model=LeaveAdministrators
        fields=('__all__')

class LeaveMigrationSerializers(serializers.ModelSerializer):

    class Meta:
        model=LeaveMigration
        fields=('__all__')

class RestrictedHolidaySerializers(serializers.ModelSerializer):

    class Meta:
        model=RestrictedHoliday
        fields=('__all__')

class ClosedHolidaySerializers(serializers.ModelSerializer):

    class Meta:
        model=ClosedHoliday
        fields=('__all__')

class VacationHolidaySerializers(serializers.ModelSerializer):

    class Meta:
        model=VacationHoliday
        fields=('__all__')

class LeaveOfflineSerializers(serializers.ModelSerializer):

    class Meta:
        model=LeaveOffline
        fields=('__all__')

class LeaveSegmentOfflineSerializers(serializers.ModelSerializer):

    class Meta:
        model=LeaveSegmentOffline
        fields=('__all__')
