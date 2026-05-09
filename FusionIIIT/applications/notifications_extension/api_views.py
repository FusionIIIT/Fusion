from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from applications.notifications_extension.models import Announcement
from django.utils import timezone
from applications.globals.models import ExtraInfo

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def system_announcements_api(request):
    if request.method == 'GET':
        announcements = Announcement.objects.filter(is_archived=False)
        data = []
        for ann in announcements:
            data.append({
                'id': ann.id,
                'title': ann.title,
                'message': ann.message,
                'announcer_id': ann.announcer.id if ann.announcer else None,
                'timestamp': ann.timestamp,
                'is_archived': ann.is_archived
            })
        return Response({'payload': data}, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        title = request.data.get('title')
        message = request.data.get('message')
        
        if not title or not message:
            return Response({'error': 'Title and message are required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        extrainfo = ExtraInfo.objects.filter(user=request.user).first()
        announcement = Announcement.objects.create(
            title=title,
            message=message,
            announcer=extrainfo,
            timestamp=timezone.now(),
            is_archived=False
        )
        return Response({'message': 'Announcement created', 'id': announcement.id}, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def archive_announcement_api(request, pk):
    try:
        announcement = Announcement.objects.get(pk=pk)
        announcement.is_archived = True
        announcement.save()
        return Response({'message': 'Announcement archived successfully'}, status=status.HTTP_200_OK)
    except Announcement.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
