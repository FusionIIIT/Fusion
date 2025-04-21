#views.py
import datetime
from datetime import date, datetime, timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.shortcuts import get_object_or_404, render
from applications.globals.models import User, ExtraInfo, HoldsDesignation

from notifications.models import Notification
from .models import Caretaker, StudentComplain, Supervisor
from notification.views import complaint_system_notif

from applications.filetracking.sdk.methods import *
from applications.filetracking.models import *
from operator import attrgetter

# Import DRF classes
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import (
    StudentComplainSerializer,
    CaretakerSerializer,
    ExtraInfoSerializer,
)

# Converted to DRF APIView
class CheckUser(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        The function is used to check the type of user.
        There are three types of users: student, staff, or faculty.
        Returns the user type and the appropriate endpoint.
        """
        a = request.user
        b = ExtraInfo.objects.select_related("user", "department").filter(user=a).first()
        supervisor_list = Supervisor.objects.all()
        caretaker_list = Caretaker.objects.all()
        is_supervisor = False
        is_caretaker = False
        for i in supervisor_list:
            if b.id == i.sup_id_id:
                is_supervisor = True
                break
        for i in caretaker_list:
            if b.id == i.staff_id_id:
                is_caretaker = True
                break
        if is_supervisor:
            return Response({"user_type": "supervisor", "next_url": "/complaint/supervisor/"})
        elif is_caretaker:
            return Response({"user_type": "caretaker", "next_url": "/complaint/caretaker/"})
        elif b.user_type == "student":
            return Response({"user_type": "student", "next_url": "/complaint/user/"})
        elif b.user_type == "staff":
            return Response({"user_type": "staff", "next_url": "/complaint/user/"})
        elif b.user_type == "faculty":
            return Response({"user_type": "faculty", "next_url": "/complaint/user/"})
        else:
            return Response({"error": "wrong user credentials"}, status=400)

# Converted to DRF APIView
class UserComplaintView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Returns the list of complaints made by the user.
        """
        a = request.user
        y = ExtraInfo.objects.select_related("user", "department").filter(user=a).first()
        complaints = StudentComplain.objects.filter(complainer=y).order_by("-id")
        serializer = StudentComplainSerializer(complaints, many=True)
        return Response(serializer.data)

    def post(self, request):
        """
        Allows the user to register a new complaint.
        """
        a = request.user
        y = ExtraInfo.objects.select_related("user", "department").filter(user=a).first()
        data = request.data.copy()
        data["complainer"] = y.id
        data["status"] = 0
        comp_type = data.get("complaint_type", "")
        # Finish time is according to complaint type
        complaint_finish = datetime.now() + timedelta(days=2)
        if comp_type == "Electricity":
            complaint_finish = datetime.now() + timedelta(days=2)
        elif comp_type == "Carpenter":
            complaint_finish = datetime.now() + timedelta(days=2)
        elif comp_type == "Plumber":
            complaint_finish = datetime.now() + timedelta(days=2)
        elif comp_type == "Garbage":
            complaint_finish = datetime.now() + timedelta(days=1)
        elif comp_type == "Dustbin":
            complaint_finish = datetime.now() + timedelta(days=1)
        elif comp_type == "Internet":
            complaint_finish = datetime.now() + timedelta(days=4)
        elif comp_type == "Other":
            complaint_finish = datetime.now() + timedelta(days=3)
        data["complaint_finish"] = complaint_finish.date()

        serializer = StudentComplainSerializer(data=data)
        if serializer.is_valid():
            complaint = serializer.save()
            # Handle file uploads, notifications, etc.
            # Omitted for brevity.
            return Response(serializer.data, status=201)
        else:
            return Response(serializer.errors, status=400)

# Converted to DRF APIView
class CaretakerFeedbackView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Allows the user to submit feedback for a particular type of caretaker.
        """
        feedback = request.data.get("feedback", "")
        rating = request.data.get("rating", "")
        caretaker_type = request.data.get("caretakertype", "")
        try:
            rating = int(rating)
        except ValueError:
            return Response({"error": "Invalid rating"}, status=400)
        all_caretaker = Caretaker.objects.filter(area=caretaker_type).order_by("-id")
        for x in all_caretaker:
            rate = x.rating
            if rate == 0:
                newrate = rating
            else:
                newrate = (rate + rating) / 2
            x.myfeedback = feedback
            x.rating = newrate
            x.save()
        return Response({"success": "Feedback submitted"})

# Converted to DRF APIView
class SubmitFeedbackView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, complaint_id):
        """
        Allows the user to submit feedback for a complaint.
        """
        feedback = request.data.get("feedback", "")
        rating = request.data.get("rating", "")

        try:
            rating = int(rating)
        except ValueError:
            return Response({"error": "Invalid rating"}, status=400)
        
        try:
            StudentComplain.objects.filter(id=complaint_id).update(feedback=feedback, flag=rating)
            a = StudentComplain.objects.filter(id=complaint_id).first()
            care = Caretaker.objects.filter(area=a.location).first()
            rate = care.rating
            if rate == 0:
                newrate = rating
            else:
                newrate = int((rating + rate) / 2)
            care.rating = newrate
            care.save()
            return Response({"success": "Feedback submitted"})
        except:
            return Response({"error": "Internal server errror"}, status=500)

# Converted to DRF APIView
class ComplaintDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, detailcomp_id1):
        """
        Returns the details of a complaint.
        """
        try:
            complaint = StudentComplain.objects.select_related(
                "complainer", "complainer_user", "complainer_department"
            ).get(id=detailcomp_id1)
        except StudentComplain.DoesNotExist:
            return Response({"error": "Complaint not found"}, status=404)
        serializer = StudentComplainSerializer(complaint)
        return Response(serializer.data)
    # Import DRF classes
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

# Import necessary models and serializers
from .serializers import (
    StudentComplainSerializer,
    CaretakerSerializer,
    FeedbackSerializer,
    ResolvePendingSerializer,
)
# Other imports remain the same
import datetime
from datetime import datetime, timedelta
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.shortcuts import get_object_or_404, render
from applications.globals.models import User, ExtraInfo, HoldsDesignation
from notifications.models import Notification
from .models import Caretaker, StudentComplain, Supervisor
from notification.views import complaint_system_notif
from applications.filetracking.sdk.methods import *
from applications.filetracking.models import *
from operator import attrgetter

# Converted to DRF APIView
class CaretakerLodgeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Allows the caretaker to lodge a new complaint.
        """
        # Get the current user
        a = request.user
        y = ExtraInfo.objects.select_related('user', 'department').filter(user=a).first()

        data = request.data.copy()
        data['complainer'] = y.id
        data['status'] = 0
        comp_type = data.get('complaint_type', '')
        # Finish time is according to complaint type
        complaint_finish = datetime.now() + timedelta(days=2)
        if comp_type == 'Electricity':
            complaint_finish = datetime.now() + timedelta(days=2)
        elif comp_type == 'carpenter':
            complaint_finish = datetime.now() + timedelta(days=2)
        elif comp_type == 'plumber':
            complaint_finish = datetime.now() + timedelta(days=2)
        elif comp_type == 'garbage':
            complaint_finish = datetime.now() + timedelta(days=1)
        elif comp_type == 'dustbin':
            complaint_finish = datetime.now() + timedelta(days=1)
        elif comp_type == 'internet':
            complaint_finish = datetime.now() + timedelta(days=4)
        elif comp_type == 'other':
            complaint_finish = datetime.now() + timedelta(days=3)
        data['complaint_finish'] = complaint_finish.date()

        serializer = StudentComplainSerializer(data=data)
        if serializer.is_valid():
            complaint = serializer.save()

            # Notification logic (if any)
            location = data.get('location', '')
            if location == "hall-1":
                dsgn = "hall1caretaker"
            elif location == "hall-3":
                dsgn = "hall3caretaker"
            elif location == "hall-4":
                dsgn = "hall4caretaker"
            elif location == "CC1":
                dsgn = "cc1convener"
            elif location == "CC2":
                dsgn = "CC2 convener"
            elif location == "core_lab":
                dsgn = "corelabcaretaker"
            elif location == "LHTC":
                dsgn = "lhtccaretaker"
            elif location == "NR2":
                dsgn = "nr2caretaker"
            elif location == "Maa Saraswati Hostel":
                dsgn = "mshcaretaker"
            elif location == "Nagarjun Hostel":
                dsgn = "nhcaretaker"
            elif location == "Panini Hostel":
                dsgn = "phcaretaker"
            else:
                dsgn = "rewacaretaker"
            caretaker_name = HoldsDesignation.objects.select_related('user', 'working', 'designation').get(designation__name=dsgn)

            # Send notification
            student = 1
            message = "A New Complaint has been lodged"
            complaint_system_notif(request.user, caretaker_name.user, 'lodge_comp_alert', complaint.id, student, message)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        """
        Returns the list of complaints lodged by the caretaker.
        """
        a = request.user
        y = ExtraInfo.objects.select_related('user', 'department').filter(user=a).first()
        complaints = StudentComplain.objects.filter(complainer=y).order_by('-id')
        serializer = StudentComplainSerializer(complaints, many=True)
        return Response(serializer.data)

# Converted to DRF APIView
class CaretakerView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Returns the list of complaints assigned to the caretaker.
        """
        current_user = request.user
        y = ExtraInfo.objects.select_related('user', 'department').filter(user=current_user).first()
        try:
            a = Caretaker.objects.select_related('staff_id').get(staff_id=y.id)
            b = a.area
            complaints = StudentComplain.objects.filter(location=b).order_by('-id')
            serializer = StudentComplainSerializer(complaints, many=True)
            return Response(serializer.data)
        except Caretaker.DoesNotExist:
            return Response({'error': 'Caretaker does not exist'}, status=status.HTTP_404_NOT_FOUND)

# Converted to DRF APIView
class FeedbackCareView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, feedcomp_id):
        """
        Returns the feedback details for a specific complaint.
        """
        try:
            detail = StudentComplain.objects.select_related('complainer', 'complainer_user', 'complainer_department').get(id=feedcomp_id)
            serializer = StudentComplainSerializer(detail)
            return Response(serializer.data)
        except StudentComplain.DoesNotExist:
            return Response({'error': 'Complaint not found'}, status=status.HTTP_404_NOT_FOUND)

# Converted to DRF APIView
class ResolvePendingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, cid):
        """
        Allows the caretaker to resolve a pending complaint.
        """
        serializer = ResolvePendingSerializer(data=request.data)
        print("Incoming data:", request.data)
        if serializer.is_valid():
            newstatus = serializer.validated_data['yesorno']
            comment = serializer.validated_data.get('comment', '')
            intstatus = 2 if newstatus == 'Yes' else 3
            StudentComplain.objects.filter(id=cid).update(status=intstatus, comment=comment)

            # Send notification to the complainer
            try:
                complainer_details = StudentComplain.objects.select_related('complainer').get(id=cid)
                student = 0
                if newstatus == 'Yes':
                    message = "Congrats! Your complaint has been resolved"
                    notification_type = 'comp_resolved_alert'
                else:
                    message = "Your complaint has been declined"
                    notification_type = 'comp_declined_alert'
                
                complaint_system_notif(request.user, complainer_details.complainer.user, notification_type, complainer_details.id, student, message)
                return Response({'success': 'Complaint status updated'})
            except StudentComplain.DoesNotExist:
                return Response({'error': 'Complaint not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, cid):
        """
        Returns the details of the complaint to be resolved.
        """
        try:
            complaint = StudentComplain.objects.select_related('complainer', 'complainer_user', 'complainer_department').get(id=cid)
            serializer = StudentComplainSerializer(complaint)
            return Response(serializer.data)
        except StudentComplain.DoesNotExist:
            return Response({'error': 'Complaint not found'}, status=status.HTTP_404_NOT_FOUND)

# Converted to DRF APIView
class ComplaintDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, detailcomp_id1):
        """
        Returns the details of a complaint for the caretaker.
        """
        try:
            complaint = StudentComplain.objects.select_related().get(id=detailcomp_id1)
            serializer = StudentComplainSerializer(complaint)
            print(serializer.data)
            return Response(serializer.data)
        except StudentComplain.DoesNotExist:
            return Response({'error': 'Complaint not found'}, status=status.HTTP_404_NOT_FOUND)

# Converted to DRF APIView
class SearchComplaintView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Searches for complaints based on query parameters.
        """
        # Implement search logic based on query parameters
        # For now, return all complaints
        complaints = StudentComplain.objects.all()
        serializer = StudentComplainSerializer(complaints, many=True)
        return Response(serializer.data)

# Converted to DRF APIView
class SubmitFeedbackCaretakerView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, complaint_id):
        """
        Allows the caretaker to submit feedback for a complaint.
        """
        serializer = FeedbackSerializer(data=request.data)
        if serializer.is_valid():
            feedback = serializer.validated_data['feedback']
            rating = serializer.validated_data['rating']
            try:
                rating = int(rating)
            except ValueError:
                return Response({'error': 'Invalid rating'}, status=status.HTTP_400_BAD_REQUEST)
            StudentComplain.objects.filter(id=complaint_id).update(feedback=feedback, flag=rating)

            a = StudentComplain.objects.select_related('complainer', 'complainer_user', 'complainer_department').filter(id=complaint_id).first()
            care = Caretaker.objects.filter(area=a.location).first()
            rate = care.rating
            newrate = int((rating + rate) / 2) if rate != 0 else rating
            care.rating = newrate
            care.save()
            return Response({'success': 'Feedback submitted'})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, complaint_id):
        """
        Returns the complaint details for which feedback is to be submitted.
        """
        try:
            complaint = StudentComplain.objects.select_related('complainer', 'complainer_user', 'complainer_department').get(id=complaint_id)
            serializer = StudentComplainSerializer(complaint)
            return Response(serializer.data)
        except StudentComplain.DoesNotExist:
            return Response({'error': 'Complaint not found'}, status=status.HTTP_404_NOT_FOUND)
# views.py

# Import DRF classes
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

# Import necessary models and serializers
from .serializers import (
    StudentComplainSerializer,
    CaretakerSerializer,
    FeedbackSerializer,
    ResolvePendingSerializer,
)
# Other imports remain the same
import datetime
from datetime import datetime, timedelta
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.shortcuts import get_object_or_404, render
from applications.globals.models import User, ExtraInfo, HoldsDesignation
from notifications.models import Notification
from .models import Caretaker, StudentComplain, Supervisor
from notification.views import complaint_system_notif
from applications.filetracking.sdk.methods import *
from applications.filetracking.models import *
from operator import attrgetter

# Converted to DRF APIView
class SupervisorLodgeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Allows the supervisor to lodge a new complaint.
        """
        # Get the current user
        a = request.user
        y = ExtraInfo.objects.select_related('user', 'department').filter(user=a).first()

        data = request.data.copy()
        data['complainer'] = y.id
        data['status'] = 0

        comp_type = data.get('complaint_type', '')
        # Finish time is according to complaint type
        complaint_finish = datetime.now() + timedelta(days=2)
        if comp_type == 'Electricity':
            complaint_finish = datetime.now() + timedelta(days=2)
        elif comp_type == 'carpenter':
            complaint_finish = datetime.now() + timedelta(days=2)
        elif comp_type == 'plumber':
            complaint_finish = datetime.now() + timedelta(days=2)
        elif comp_type == 'garbage':
            complaint_finish = datetime.now() + timedelta(days=1)
        elif comp_type == 'dustbin':
            complaint_finish = datetime.now() + timedelta(days=1)
        elif comp_type == 'internet':
            complaint_finish = datetime.now() + timedelta(days=4)
        elif comp_type == 'other':
            complaint_finish = datetime.now() + timedelta(days=3)
        data['complaint_finish'] = complaint_finish.date()

        serializer = StudentComplainSerializer(data=data)
        if serializer.is_valid():
            complaint = serializer.save()

            # Notification logic (if any)
            location = data.get('location', '')
            if location == "hall-1":
                dsgn = "hall1caretaker"
            elif location == "hall-3":
                dsgn = "hall3caretaker"
            elif location == "hall-4":
                dsgn = "hall4caretaker"
            elif location == "CC1":
                dsgn = "cc1convener"
            elif location == "CC2":
                dsgn = "CC2 convener"
            elif location == "core_lab":
                dsgn = "corelabcaretaker"
            elif location == "LHTC":
                dsgn = "lhtccaretaker"
            elif location == "NR2":
                dsgn = "nr2caretaker"
            elif location == "Maa Saraswati Hostel":
                dsgn = "mshcaretaker"
            elif location == "Nagarjun Hostel":
                dsgn = "nhcaretaker"
            elif location == "Panini Hostel":
                dsgn = "phcaretaker"
            else:
                dsgn = "rewacaretaker"
            caretaker_name = HoldsDesignation.objects.select_related('user', 'working', 'designation').get(designation__name=dsgn)

            # Send notification
            student = 1
            message = "A New Complaint has been lodged"
            complaint_system_notif(request.user, caretaker_name.user, 'lodge_comp_alert', complaint.id, student, message)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        """
        Returns the history of complaints lodged by the supervisor.
        """
        a = request.user
        y = ExtraInfo.objects.select_related('user', 'department').filter(user=a).first()
        complaints = StudentComplain.objects.filter(complainer=y).order_by('-id')
        serializer = StudentComplainSerializer(complaints, many=True)
        return Response(serializer.data)

# Converted to DRF APIView
class SupervisorView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Returns the list of complaints assigned to the supervisor's area.
        """
        current_user = request.user
        y = ExtraInfo.objects.select_related('user', 'department').filter(user=current_user).first()
        try:
            supervisor = Supervisor.objects.select_related('sup_id').get(sup_id=y)
            type = supervisor.type
            complaints = StudentComplain.objects.filter(complaint_type=type, status=1).order_by('-id')
            serializer = StudentComplainSerializer(complaints, many=True)
            return Response(serializer.data)
        except Supervisor.DoesNotExist:
            return Response({'error': 'Supervisor does not exist'}, status=status.HTTP_404_NOT_FOUND)

# Converted to DRF APIView
class FeedbackSuperView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, feedcomp_id):
        """
        Returns the feedback details for a specific complaint for the supervisor.
        """
        try:
            complaint = StudentComplain.objects.select_related('complainer', 'complainer_user', 'complainer_department').get(id=feedcomp_id)
            caretaker = Caretaker.objects.select_related('staff_id', 'staff_id_user', 'staff_id_department').filter(area=complaint.location).first()
            complaint_data = StudentComplainSerializer(complaint).data
            caretaker_data = CaretakerSerializer(caretaker).data if caretaker else None
            return Response({'complaint': complaint_data, 'caretaker': caretaker_data})
        except StudentComplain.DoesNotExist:
            return Response({'error': 'Complaint not found'}, status=status.HTTP_404_NOT_FOUND)

# Converted to DRF APIView
class CaretakerIdKnowMoreView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, caretaker_id):
        """
        Returns the details of a caretaker and the list of pending complaints in their area.
        """
        try:
            caretaker = Caretaker.objects.select_related('staff_id', 'staff_id_user', 'staff_id_department').get(id=caretaker_id)
            area = caretaker.area
            pending_complaints = StudentComplain.objects.filter(location=area, status=0)
            caretaker_data = CaretakerSerializer(caretaker).data
            complaints_data = StudentComplainSerializer(pending_complaints, many=True).data
            return Response({'caretaker': caretaker_data, 'pending_complaints': complaints_data})
        except Caretaker.DoesNotExist:
            return Response({'error': 'Caretaker not found'}, status=status.HTTP_404_NOT_FOUND)

# Converted to DRF APIView
class SupervisorComplaintDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, detailcomp_id1):
        """
        Returns the details of a complaint for the supervisor, including caretaker info.
        """
        try:
            complaint = StudentComplain.objects.select_related('complainer', 'complainer_user', 'complainer_department').get(id=detailcomp_id1)
            caretaker = Caretaker.objects.select_related('staff_id', 'staff_id_user', 'staff_id_department').filter(area=complaint.location).first()
            complaint_data = StudentComplainSerializer(complaint).data
            caretaker_data = CaretakerSerializer(caretaker).data if caretaker else None
            return Response({'complaint': complaint_data, 'caretaker': caretaker_data})
        except StudentComplain.DoesNotExist:
            return Response({'error': 'Complaint not found'}, status=status.HTTP_404_NOT_FOUND)

# Converted to DRF APIView
class SupervisorResolvePendingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, cid):
        """
        Allows the supervisor to resolve a pending complaint.
        """
        serializer = ResolvePendingSerializer(data=request.data)
        if serializer.is_valid():
            newstatus = serializer.validated_data['yesorno']
            comment = serializer.validated_data.get('comment', '')
            intstatus = 2 if newstatus == 'Yes' else 3
            StudentComplain.objects.filter(id=cid).update(status=intstatus, comment=comment)

            # Send notification to the complainer
            try:
                complainer_details = StudentComplain.objects.select_related('complainer').get(id=cid)
                student = 0
                message = "Congrats! Your complaint has been resolved"
                complaint_system_notif(request.user, complainer_details.complainer.user, 'comp_resolved_alert', complainer_details.id, student, message)
                return Response({'success': 'Complaint status updated'})
            except StudentComplain.DoesNotExist:
                return Response({'error': 'Complaint not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, cid):
        """
        Returns the details of the complaint to be resolved.
        """
        try:
            complaint = StudentComplain.objects.select_related('complainer').get(id=cid)
            serializer = StudentComplainSerializer(complaint)
            return Response(serializer.data)
        except StudentComplain.DoesNotExist:
            return Response({'error': 'Complaint not found'}, status=status.HTTP_404_NOT_FOUND)

# Converted to DRF APIView
class SupervisorSubmitFeedbackView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, complaint_id):
        """
        Allows the supervisor to submit feedback for a complaint.
        """
        serializer = FeedbackSerializer(data=request.data)
        if serializer.is_valid():
            feedback = serializer.validated_data['feedback']
            rating = serializer.validated_data['rating']
            try:
                rating = int(rating)
            except ValueError:
                return Response({'error': 'Invalid rating'}, status=status.HTTP_400_BAD_REQUEST)
            StudentComplain.objects.filter(id=complaint_id).update(feedback=feedback, flag=rating)

            # Update caretaker's rating
            try:
                complaint = StudentComplain.objects.select_related('complainer', 'complainer_user', 'complainer_department').get(id=complaint_id)
                care = Caretaker.objects.filter(area=complaint.location).first()
                rate = care.rating
                newrate = int((rating + rate) / 2) if rate != 0 else rating
                care.rating = newrate
                care.save()
                return Response({'success': 'Feedback submitted'})
            except Caretaker.DoesNotExist:
                return Response({'error': 'Caretaker not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, complaint_id):
        """
        Returns the complaint details for which feedback is to be submitted.
        """
        try:
            complaint = StudentComplain.objects.select_related('complainer', 'complainer_user', 'complainer_department').get(id=complaint_id)
            serializer = StudentComplainSerializer(complaint)
            return Response(serializer.data)
        except StudentComplain.DoesNotExist:
            return Response({'error': 'Complaint not found'}, status=status.HTTP_404_NOT_FOUND)
# views.py

# Import DRF classes
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

# Import necessary models and serializers
from .models import Caretaker, StudentComplain, Supervisor, Workers, SectionIncharge
from .serializers import StudentComplainSerializer, WorkersSerializer  # Added WorkersSerializer
from applications.globals.models import User, ExtraInfo, HoldsDesignation

# Converted 'removew' function to DRF APIView 'RemoveWorkerView'
class RemoveWorkerView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, work_id):
        """
        Allows the caretaker to remove a worker if not assigned to any complaints.
        """
        try:
            worker = Workers.objects.get(id=work_id)
            assigned_complaints = StudentComplain.objects.filter(worker_id=worker).count()
            if assigned_complaints == 0:
                worker.delete()
                return Response({'success': 'Worker removed successfully'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Worker is assigned to some complaints'}, status=status.HTTP_400_BAD_REQUEST)
        except Workers.DoesNotExist:
            return Response({'error': 'Worker not found'}, status=status.HTTP_404_NOT_FOUND)

    # Optionally, accept DELETE method
    def delete(self, request, work_id):
        return self.post(request, work_id)

# Converted 'assign_worker' function to DRF APIView 'AssignWorkerView'
class ForwardCompaintView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, comp_id1):
        """
        Assigns a complaint to a supervisor.
        """
        current_user = request.user
        y = ExtraInfo.objects.filter(user=current_user).first()
        complaint_id = comp_id1

        try:
            complaint = StudentComplain.objects.get(id=complaint_id)
        except StudentComplain.DoesNotExist:
            return Response({'error': 'Complaint not found'}, status=status.HTTP_404_NOT_FOUND)

        complaint_type = complaint.complaint_type

        supervisors = Supervisor.objects.filter(type=complaint_type)
        if not supervisors.exists():
            return Response({'error': 'Supervisor does not exist for this complaint type'}, status=status.HTTP_404_NOT_FOUND)

        supervisor = supervisors.first()
        supervisor_details = ExtraInfo.objects.get(id=supervisor.sup_id.id)

        # Update complaint status
        complaint.status = 1
        complaint.save()

        # Forward file to supervisor
        sup_designations = HoldsDesignation.objects.filter(user=supervisor_details.user_id)

        files = File.objects.filter(src_object_id=complaint_id)

        if not files.exists():
            return Response({'error': 'No files associated with this complaint'}, status=status.HTTP_206_PARTIAL_CONTENT)

        supervisor_username = User.objects.get(id=supervisor_details.user_id).username

        file = forward_file(
            file_id=files.first().id,
            receiver=supervisor_username,
            receiver_designation=sup_designations.first().designation,
            file_extra_JSON={},
            remarks="",
            file_attachment=None
        )

        return Response({'success': 'Complaint assigned to supervisor'}, status=status.HTTP_200_OK)

    def get(self, request, comp_id1):
        """
        Retrieves complaint details.
        """
        try:
            complaint = StudentComplain.objects.get(id=comp_id1)
            serializer = StudentComplainSerializer(complaint)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except StudentComplain.DoesNotExist:
            return Response({'error': 'Not a valid complaint'}, status=status.HTTP_404_NOT_FOUND)

# Converted 'deletecomplaint' function to DRF APIView 'DeleteComplaintView'
class DeleteComplaintView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, comp_id1):
        """
        Deletes a complaint.
        """
        try:
            complaint = StudentComplain.objects.get(id=comp_id1)
            complaint.delete()
            return Response({'success': 'Complaint deleted successfully'}, status=status.HTTP_200_OK)
        except StudentComplain.DoesNotExist:
            return Response({'error': 'Complaint not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, comp_id1):
        return self.post(request, comp_id1)

# Converted 'changestatus' function to DRF APIView 'ChangeStatusView'
class ChangeStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, complaint_id, status):
        """
        Allows the caretaker to change the status of a complaint.
        """
        try:
            complaint = StudentComplain.objects.get(id=complaint_id)
            if status == '3' or status == '2':
                complaint.status = status
                complaint.worker_id = None
            else:
                complaint.status = status
            complaint.save()
            return Response({'success': 'Complaint status updated'}, status=status.HTTP_200_OK)
        except StudentComplain.DoesNotExist:
            return Response({'error': 'Complaint not found'}, status=status.HTTP_404_NOT_FOUND)

# Converted 'changestatussuper' function to DRF APIView 'ChangeStatusSuperView'
class ChangeStatusSuperView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, complaint_id, status):
        """
        Allows the supervisor to change the status of a complaint.
        """
        try:
            complaint = StudentComplain.objects.get(id=complaint_id)
            if status == '3' or status == '2':
                complaint.status = status
                complaint.worker_id = None
            else:
                complaint.status = status
            complaint.save()
            return Response({'success': 'Complaint status updated'}, status=status.HTTP_200_OK)
        except StudentComplain.DoesNotExist:
            return Response({'error': 'Complaint not found'}, status=status.HTTP_404_NOT_FOUND)
        
class GenerateReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Generates a report of complaints for the caretaker's area, warden's area, or supervisor's type.
        """
        user = request.user

        is_caretaker = hasattr(user, 'caretaker')
        is_supervisor = False
        is_warden = hasattr(user, 'warden')

        # Check if user is a supervisor
        try:
            supervisor = Supervisor.objects.get(sup_id=user.extrainfo)
            is_supervisor = True
        except Supervisor.DoesNotExist:
            is_supervisor = False

        if not is_caretaker and not is_supervisor and not is_warden:
            return Response({"detail": "Not authorized to generate report."}, status=403)

        complaints = None

        # Generate report for supervisor
        if is_supervisor:
            print(f"Generating report for Supervisor {supervisor}")
            complaints = StudentComplain.objects.filter(complaint_type=supervisor.type)

        # Generate report for caretaker
        if is_caretaker and not is_supervisor:
            caretaker = get_object_or_404(Caretaker, staff_id=user.extrainfo)
            complaints = StudentComplain.objects.filter(location=caretaker.area)

        # if is_warden:
        #     warden = get_object_or_404(Warden, staff_id=user.extrainfo)
        #     if complaints:
        #         complaints = complaints.filter(location=warden.area)
        #     else:
        #         complaints = StudentComplain.objects.filter(location=warden.area)

        # Serialize and return the complaints
        serializer = StudentComplainSerializer(complaints, many=True)
        return Response(serializer.data)
