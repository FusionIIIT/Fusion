# views.py
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from notifications.utils import slug2id
from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView
from notifications.models import Notification
from rest_framework import status
from .serializers import NotificationSerializer
from notification.views import (leave_module_notif,
    placement_cell_notif,
    academics_module_notif,
    office_module_notif,
    central_mess_notif,
    visitors_hostel_notif,
    healthcare_center_notif,
    file_tracking_notif,
    scholarship_portal_notif,
    complaint_system_notif,
    office_dean_PnD_notif,
    office_module_DeanS_notif,
    gymkhana_voting,
    gymkhana_session,
    gymkhana_event,
    AssistantshipClaim_notify,
    AssistantshipClaim_faculty_notify,
    AssistantshipClaim_acad_notify,
    AssistantshipClaim_account_notify,
    department_notif,
    office_module_DeanRSPC_notif,
    research_procedures_notif,
    hostel_notifications)



class LeaveModuleNotificationAPIView(APIView):
    def post(self, request, *args, **kwargs):
        # Extract data from the request, you can customize this based on your needs
        sender = request.user
        recipient_id = request.data.get('recipient')
        type = request.data.get('type')
        date = request.data.get('date')
        User = get_user_model()
        recipient = User.objects.get(pk=recipient_id)            
        # Trigger the notification function
        leave_module_notif(sender, recipient, type, date)

        return Response({'message': 'Notification sent successfully'}, status=status.HTTP_201_CREATED)

class PlacementCellNotificationAPIView(APIView):
    def post(self, request, *args, **kwargs):
        # Extract data from the request, you can customize this based on your needs
        sender = request.user
        recipient_id = request.data.get('recipient')
        type = request.data.get('type')
        User = get_user_model()
        recipient = User.objects.get(pk=recipient_id)
        # Trigger the notification function
        placement_cell_notif(sender, recipient, type)

        return Response({'message': 'Notification sent successfully'}, status=status.HTTP_201_CREATED)

class AcademicsModuleNotificationAPIView(APIView):
    def post(self, request, *args, **kwargs):
        # Extract data from the request, you can customize this based on your needs
        sender = request.user
        recipient_id = request.data.get('recipient')
        type = request.data.get('type')
        User = get_user_model()
        recipient = User.objects.get(pk=recipient_id)
        # Trigger the notification function
        academics_module_notif(sender, recipient, type)

        return Response({'message': 'Notification sent successfully'}, status=status.HTTP_201_CREATED)

class OfficeModuleNotificationAPIView(APIView):
    def post(self, request, *args, **kwargs):
        # Extract data from the request, you can customize this based on your needs
        sender = request.user
        recipient_id = request.data.get('recipient')
        User = get_user_model()
        recipient = User.objects.get(pk=recipient_id)
        # Trigger the notification function
        office_module_notif(sender, recipient)

        return Response({'message': 'Notification sent successfully'}, status=status.HTTP_201_CREATED)
class CentralMessNotificationAPIView(APIView):
    def post(self, request, *args, **kwargs):
        # Extract data from the request, you can customize this based on your needs
        sender = request.user
        recipient_id = request.data.get('recipient')
        type = request.data.get('type')
        message = request.data.get('message')

        User = get_user_model()
        recipient = User.objects.get(pk=recipient_id)

        # Trigger the notification function
        central_mess_notif(sender, recipient, type, message)

        return Response({'message': 'Notification sent successfully'}, status=status.HTTP_201_CREATED)

class VisitorsHostelNotificationAPIView(APIView):
    def post(self, request, *args, **kwargs):
        # Extract data from the request, you can customize this based on your needs
        sender = request.user
        recipient_id = request.data.get('recipient')
        type = request.data.get('type')
        User = get_user_model()
        recipient = User.objects.get(pk=recipient_id)
        # Trigger the notification function
        visitors_hostel_notif(sender, recipient, type)

        return Response({'message': 'Notification sent successfully'}, status=status.HTTP_201_CREATED)

class HealthcareCenterNotificationAPIView(APIView):
    def post(self, request, *args, **kwargs):
        # Extract data from the request, you can customize this based on your needs
        sender = request.user
        recipient_id = request.data.get('recipient')
        type = request.data.get('type')

        # Trigger the notification function
        healthcare_center_notif(sender, recipient, type)

        return Response({'message': 'Notification sent successfully'}, status=status.HTTP_201_CREATED)

class FileTrackingNotificationAPIView(APIView):
    def post(self, request, *args, **kwargs):
        # Extract data from the request, you can customize this based on your needs
        sender = request.user
        recipient_id = request.data.get('recipient')
        title = request.data.get('title')
        User = get_user_model()
        recipient = User.objects.get(pk=recipient_id)
        # Trigger the notification function
        file_tracking_notif(sender, recipient, title)

        return Response({'message': 'Notification sent successfully'}, status=status.HTTP_201_CREATED)    
class ScholarshipPortalNotificationAPIView(APIView):
    def post(self, request, *args, **kwargs):
        # Extract data from the request, you can customize this based on your needs
        sender = request.user
        recipient_id = request.data.get('recipient')
        type = request.data.get('type')
        User = get_user_model()
        recipient = User.objects.get(pk=recipient_id)
        # Trigger the notification function
        scholarship_portal_notif(sender, recipient, type)

        return Response({'message': 'Notification sent successfully'}, status=status.HTTP_201_CREATED)

class ComplaintSystemNotificationAPIView(APIView):
    def post(self, request, *args, **kwargs):
        # Extract data from the request, you can customize this based on your needs
        sender = request.user
        recipient_id = request.data.get('recipient')
        type = request.data.get('type')
        complaint_id = request.data.get('complaint_id')
        student = request.data.get('student')
        message = request.data.get('message')
        User = get_user_model()
        recipient = User.objects.get(pk=recipient_id)
        # Trigger the notification function
        complaint_system_notif(sender, recipient, type, complaint_id, student, message)

        return Response({'message': 'Notification sent successfully'}, status=status.HTTP_201_CREATED)

class OfficeDeanPnDNotificationAPIView(APIView):
    def post(self, request, *args, **kwargs):
        # Extract data from the request, you can customize this based on your needs
        sender = request.user
        recipient_id = request.data.get('recipient')
        type = request.data.get('type')
        User = get_user_model()
        recipient = User.objects.get(pk=recipient_id)
        # Trigger the notification function
        office_dean_PnD_notif(sender, recipient, type)

        return Response({'message': 'Notification sent successfully'}, status=status.HTTP_201_CREATED)

class OfficeDeanSNotificationAPIView(APIView):
    def post(self, request, *args, **kwargs):
        # Extract data from the request, you can customize this based on your needs
        sender = request.user
        recipient_id = request.data.get('recipient')
        type = request.data.get('type')
        User = get_user_model()
        recipient = User.objects.get(pk=recipient_id)
        # Trigger the notification function
        office_module_DeanS_notif(sender, recipient, type)

        return Response({'message': 'Notification sent successfully'}, status=status.HTTP_201_CREATED)
    
class GymkhanaVotingNotificationAPIView(APIView):
    def post(self, request, *args, **kwargs):
        # Extract data from the request, you can customize this based on your needs
        sender = request.user
        recipient_id = request.data.get('recipient')
        type = request.data.get('type')
        title = request.data.get('title')
        desc = request.data.get('desc')
        User = get_user_model()
        recipient = User.objects.get(pk=recipient_id)
        # Trigger the notification function
        gymkhana_voting(sender, recipient, type, title, desc)

        return Response({'message': 'Notification sent successfully'}, status=status.HTTP_201_CREATED)

class GymkhanaSessionNotificationAPIView(APIView):
    def post(self, request, *args, **kwargs):
        # Extract data from the request, you can customize this based on your needs
        sender = request.user
        recipient_id = request.data.get('recipient')
        type = request.data.get('type')
        club = request.data.get('club')
        desc = request.data.get('desc')
        venue = request.data.get('venue')
        User = get_user_model()
        recipient = User.objects.get(pk=recipient_id)
        # Trigger the notification function
        gymkhana_session(sender, recipient, type, club, desc, venue)

        return Response({'message': 'Notification sent successfully'}, status=status.HTTP_201_CREATED)

class GymkhanaEventNotificationAPIView(APIView):
    def post(self, request, *args, **kwargs):
        # Extract data from the request, you can customize this based on your needs
        sender = request.user
        recipient_id = request.data.get('recipient')
        type = request.data.get('type')
        club = request.data.get('club')
        event_name = request.data.get('event_name')
        desc = request.data.get('desc')
        venue = request.data.get('venue')
        User = get_user_model()
        recipient = User.objects.get(pk=recipient_id)
        # Trigger the notification function
        gymkhana_event(sender, recipient, type, club, event_name, desc, venue)

        return Response({'message': 'Notification sent successfully'}, status=status.HTTP_201_CREATED)

class AssistantshipClaimNotificationAPIView(APIView):
    def post(self, request, *args, **kwargs):
        # Extract data from the request, you can customize this based on your needs
        sender = request.user
        recipient_id = request.data.get('recipient')
        month = request.data.get('month')
        year = request.data.get('year')
        User = get_user_model()
        recipient = User.objects.get(pk=recipient_id)
        # Trigger the notification function
        AssistantshipClaim_notify(sender, recipient, month, year)

        return Response({'message': 'Notification sent successfully'}, status=status.HTTP_201_CREATED)
class AssistantshipClaimFacultyNotificationAPIView(APIView):
    def post(self, request, *args, **kwargs):
        # Extract data from the request, you can customize this based on your needs
        sender = request.user
        recipient_id = request.data.get('recipient')
        User = get_user_model()
        recipient = User.objects.get(pk=recipient_id)
        # Trigger the notification function
        AssistantshipClaim_faculty_notify(sender, recipient)

        return Response({'message': 'Notification sent successfully'}, status=status.HTTP_201_CREATED)

class AssistantshipClaimAcadNotificationAPIView(APIView):
    def post(self, request, *args, **kwargs):
        # Extract data from the request, you can customize this based on your needs
        sender = request.user
        recipient_id = request.data.get('recipient')
        User = get_user_model()
        recipient = User.objects.get(pk=recipient_id)
        # Trigger the notification function
        AssistantshipClaim_acad_notify(sender, recipient)

        return Response({'message': 'Notification sent successfully'}, status=status.HTTP_201_CREATED)

class AssistantshipClaimAccountNotificationAPIView(APIView):
    def post(self, request, *args, **kwargs):
        # Extract data from the request, you can customize this based on your needs
        sender = request.user
        stu = request.data.get('stu')
        recipient_id = request.data.get('recipient')
        User = get_user_model()
        recipient = User.objects.get(pk=recipient_id)
        # Trigger the notification function
        AssistantshipClaim_account_notify(sender, stu, recipient)

        return Response({'message': 'Notification sent successfully'}, status=status.HTTP_201_CREATED)

class DepartmentNotificationAPIView(APIView):
    def post(self, request, *args, **kwargs):
        # Extract data from the request, you can customize this based on your needs
        sender = request.user
        recipient_id = request.data.get('recipient')
        type = request.data.get('type')
        User = get_user_model()
        recipient = User.objects.get(pk=recipient_id)
        # Trigger the notification function
        department_notif(sender, recipient, type)

        return Response({'message': 'Notification sent successfully'}, status=status.HTTP_201_CREATED)
class OfficeDeanRSPCNotificationAPIView(APIView):
    def post(self, request, *args, **kwargs):
        # Extract data from the request, you can customize this based on your needs
        sender = request.user
        recipient_id = request.data.get('recipient')
        type = request.data.get('type')
        User = get_user_model()
        recipient = User.objects.get(pk=recipient_id)
        # Trigger the notification function
        office_module_DeanRSPC_notif(sender, recipient, type)

        return Response({'message': 'Notification sent successfully'}, status=status.HTTP_201_CREATED)

class ResearchProceduresNotificationAPIView(APIView):
    def post(self, request, *args, **kwargs):
        # Extract data from the request, you can customize this based on your needs
        sender = request.user
        recipient_id = request.data.get('recipient')
        type = request.data.get('type')
        User = get_user_model()
        recipient = User.objects.get(pk=recipient_id)
        # Trigger the notification function
        research_procedures_notif(sender, recipient, type)

        return Response({'message': 'Notification sent successfully'}, status=status.HTTP_201_CREATED)

class HostelModuleNotificationAPIView(APIView):
    def post(self, request, *args, **kwargs):
        # Extract data from the request, you can customize this based on your needs
        sender = request.user
        recipient_id = request.data.get('recipient')
        type = request.data.get('type')
        User = get_user_model()
        recipient = User.objects.get(pk=recipient_id)
        # Trigger the notification function
        hostel_notifications(sender, recipient, type)
        
        return Response({'message': 'Notification sent successfully'}, status=status.HTTP_201_CREATED)

class MarkAsRead(APIView):

    def put(self,request,**args):
        notification_id = self.request.query_params.get('id')
        notification = get_object_or_404(
            Notification, recipient=request.user, id=notification_id)       

        notification.mark_as_read()

        return Response({'message': "Successfully marked as read"}, status=status.HTTP_200_OK)
    
class Delete(APIView):

    def delete(self,request, **args):
        notification_id = self.request.query_params.get('id')
        notification = get_object_or_404(
            Notification, recipient=request.user, id=notification_id)       

        notification.delete()

        return Response({'message': "Notification deleted succesfully"}, status=status.HTTP_200_OK)
    
class NotificationsList(ListAPIView):
    # queryset = Notification.objects.all(actor_object_id=)
    serializer_class = NotificationSerializer
    def get_queryset(self):
        return Notification.objects.all().filter(recipient_id=self.request.user.id)