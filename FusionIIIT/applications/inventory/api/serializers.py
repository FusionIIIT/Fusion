from rest_framework import serializers
from applications.inventory.models import Item, DepartmentInfo, SectionInfo

# Serializer for Item
class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['item_id', 'item_name', 'quantity', 'type', 'unit']  # Fields to serialize

# Serializer for DepartmentInfo
class DepartmentInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepartmentInfo
        fields = ['department_id', 'department_name', 'item_name', 'quantity']  # Fields to serialize

# Serializer for SectionInfo
class SectionInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = SectionInfo
        fields = ['section_id', 'section_name', 'item_name', 'quantity']  # Fields to serialize
