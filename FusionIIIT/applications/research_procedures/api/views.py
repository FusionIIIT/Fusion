from rest_framework.viewsets import ModelViewSet
from applications.research_procedures.models import Patent
from .serializers import PatentSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly 

class PatentViewSet(ModelViewSet):
    queryset = Patent.objects.all()
    serializer_class = PatentSerializer
    permission_classes = [ IsAuthenticatedOrReadOnly ]