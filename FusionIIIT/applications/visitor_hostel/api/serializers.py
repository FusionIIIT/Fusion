from rest_framework import serializers
from applications.visitor_hostel.models import Inventory, InventoryBill

class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = ['item_name', 'quantity', 'consumable']

class InventoryBillSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryBill
        fields = ['item_name', 'bill_number', 'cost']
class InventoryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = ['item_name', 'quantity']