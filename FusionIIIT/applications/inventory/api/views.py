from rest_framework import viewsets
from rest_framework import filters
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from ..models import Item, DepartmentInfo, SectionInfo
from .serializers import ItemSerializer, DepartmentInfoSerializer, SectionInfoSerializer

class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer

class DepartmentInfoViewSet(viewsets.ModelViewSet):
    queryset = DepartmentInfo.objects.all()
    serializer_class = DepartmentInfoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['department_name']

    def get_queryset(self):
        queryset = super().get_queryset()
        department = self.request.query_params.get('department', None)
        
        if department:
            # Case-insensitive filtering
            queryset = queryset.filter(department_name=department)
        else:
            # Return an empty queryset if no department is provided
            queryset = queryset.none()

        return queryset


class SectionInfoViewSet(viewsets.ModelViewSet):
    queryset = SectionInfo.objects.all()
    serializer_class = SectionInfoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['section_name']

    def get_queryset(self):
        queryset = super().get_queryset()
        section = self.request.query_params.get('section', None)
        
        if section:
            # Case-insensitive filtering
            queryset = queryset.filter(section_name=section)
        else:
            # Return an empty queryset if no department is provided
            queryset = queryset.none()

        return queryset
