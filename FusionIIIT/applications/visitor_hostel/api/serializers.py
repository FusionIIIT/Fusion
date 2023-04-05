from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework import serializers
from applications.visitor_hostel.models import VisitorDetail,  BookingDetail, InventoryBill, MealRecord, RoomDetail, Bill, Inventory
from applications.globals.models import ExtraInfo,User

class VisitorDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model=VisitorDetail
        fields=('__all__')

class BookingDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingDetail
        fields=('__all__')

class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields=('__all__')

class InventoryBillSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryBill
        fields=('__all__')

class MealRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model=MealRecord
        fields=('__all__')

class RoomDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model=RoomDetail
        fields=('__all__')

class BillSerializer(serializers.ModelSerializer):
    class Meta:
        model=Bill
        fields=('__all__')

class ExtraInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model=ExtraInfo
        fields=('__all__')

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        fields=('__all__')

class BookingDetailListSerializer(serializers.ListSerializer):
    child = BookingDetailSerializer()