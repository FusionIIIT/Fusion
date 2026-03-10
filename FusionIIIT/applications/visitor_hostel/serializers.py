from rest_framework import serializers
from .models import Inventory, InventoryBill
from .models import BookingDetail, Bill

class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = '__all__'

class InventoryBillSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryBill
        fields = '__all__'

class BillSerializer(serializers.ModelSerializer):
    total_bill = serializers.SerializerMethodField()

    class Meta:
        model = Bill
        fields = ['id', 'booking', 'meal_bill', 'room_bill', 'payment_status', 'bill_date', 'total_bill']

    def get_total_bill(self, obj):
        return obj.meal_bill + obj.room_bill

class BookingDetailSerializer(serializers.ModelSerializer):
    intender_name = serializers.CharField(source='intender.username')  # Assuming User model has a username field
    bill = BillSerializer()

    class Meta:
        model = BookingDetail
        fields = ['intender_name', 'booking_from', 'booking_to', 'bill']
