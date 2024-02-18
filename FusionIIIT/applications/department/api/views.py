from rest_framework import generics
from applications.department.models import Announcements
from .serializers import AnnouncementSerializer
from rest_framework.permissions import IsAuthenticated
from .permissions import IsFacultyStaffOrReadOnly


class ListCreateAnnouncementView(generics.ListCreateAPIView):
    queryset = Announcements.objects.all()
    serializer_class = AnnouncementSerializer
    permission_classes = (IsAuthenticated, IsFacultyStaffOrReadOnly)
