from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Item, DepartmentInfo, SectionInfo
from applications.inventory.api.serializers import ItemSerializer, DepartmentInfoSerializer, SectionInfoSerializer

# Item ViewSet - Handles CRUD operations for Item
class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access

# DepartmentInfo ViewSet - Handles CRUD operations for DepartmentInfo
class DepartmentInfoViewSet(viewsets.ModelViewSet):
    queryset = DepartmentInfo.objects.all()
    serializer_class = DepartmentInfoSerializer
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access

# SectionInfo ViewSet - Handles CRUD operations for SectionInfo
class SectionInfoViewSet(viewsets.ModelViewSet):
    queryset = SectionInfo.objects.all()
    serializer_class = SectionInfoSerializer
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access
