from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from applications.visitor_hostel.models import Inventory, InventoryBill
from .serializers import InventorySerializer, InventoryBillSerializer, InventoryItemSerializer
from rest_framework.generics import ListAPIView
class AddToInventory(APIView):
    def post(self, request):
        # Extract data from request
        item_name = request.data.get('item_name')
        bill_number = request.data.get('bill_number')
        quantity = request.data.get('quantity')
        cost = request.data.get('cost')
        consumable = request.data.get('consumable')
        
        # Validate and save Inventory item
        inventory_data = {
            'item_name': item_name,
            'quantity': quantity,
            'consumable': consumable,
        }
        inventory_serializer = InventorySerializer(data=inventory_data)

        if inventory_serializer.is_valid():
            inventory_item = Inventory.objects.filter(item_name=item_name).first()
            if inventory_item:
                inventory_item.quantity = quantity
                inventory_item.consumable = consumable
                inventory_item.save()
            else:
                inventory_item = inventory_serializer.save()

            # Save InventoryBill
            bill_data = {
                'item_name': inventory_item.id,  # Link to inventory item
                'bill_number': bill_number,
                'cost': cost,
            }
            bill_serializer = InventoryBillSerializer(data=bill_data)
            if bill_serializer.is_valid():
                bill_serializer.save()
                return Response({"message": "Item added successfully!"}, status=status.HTTP_201_CREATED)
            else:
                return Response(bill_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(inventory_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
class InventoryListView(ListAPIView):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer