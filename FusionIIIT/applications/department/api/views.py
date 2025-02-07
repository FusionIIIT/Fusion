from rest_framework import generics
from rest_framework.views import APIView
from applications.department.models import Announcements
from applications.academic_information.models import Spi, Student
from applications.globals.models import (Designation, ExtraInfo,
                                         HoldsDesignation,Faculty)
from applications.eis.models import (faculty_about, emp_research_projects)
from .serializers import (AnnouncementSerializer,ExtraInfoSerializer,SpiSerializer,StudentSerializer,DesignationSerializer
                          ,HoldsDesignationSerializer,FacultySerializer,faculty_aboutSerializer,emp_research_projectsSerializer)
from rest_framework.permissions import IsAuthenticated
from .permissions import IsFacultyStaffOrReadOnly
from django.http import JsonResponse 
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from datetime import date
from notification.views import department_notif
from collections import defaultdict
import re

from applications.department.models import Information
from .serializers import InformationSerializer
from .serializers import LabSerializer
from applications.globals.models import DepartmentInfo
from applications.department.models import Lab
from .serializers import FeedbackSerializer
from applications.department.models import Feedback
from datetime import datetime

current_year = datetime.now().year
current_month = datetime.now().month
yearset = current_year if current_month > 8 else current_year - 1
class ListCreateAnnouncementView(generics.ListCreateAPIView):
    def post(self, request):
        # Get the current user from the request
        user = request.user
        usrnm = get_object_or_404(User, username=user.username)
        user_info = ExtraInfo.objects.select_related('user', 'department').filter(user=usrnm).first()
        
        if not user_info:
            return Response({'error': 'User information not found'}, status=status.HTTP_404_NOT_FOUND)
        
        ann_maker_id = user_info.id
        department = user_info.department.name  # Get department name
        
        # Get the data from the request
        data = request.data.copy()  # Copy request data to modify
        
        # Add the department and announcement maker to the data
        data['ann_maker'] = ann_maker_id
        
        # Instantiate the serializer with the modified data
        serializer = AnnouncementSerializer(data=data, context={'request': request})
        
        # Validate and save if the data is valid
        if serializer.is_valid():
            # Save the data to the Announcement model
            serializer.save()  # This automatically saves the data in the Announcements table
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        # If invalid, return the errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
class DepMainAPIView(APIView):
    def get(self, request):
        user = request.user
        usrnm = get_object_or_404(User, username=user.username)
        user_info = ExtraInfo.objects.all().select_related('user', 'department').filter(user=usrnm).first()
        ann_maker_id = user_info.id
        user_info = ExtraInfo.objects.all().select_related('user', 'department').get(id=ann_maker_id)
        department_name = user_info.department.name if user_info.department else "Unknown" 

        fac_view = user.holds_designations.filter(designation__name='faculty').exists()
        student = user.holds_designations.filter(designation__name='student').exists()
        staff = user.holds_designations.filter(designation__name='staff').exists()

        # context = browse_announcements()
        # context_f = faculty()
        user_designation = ""

        if fac_view:
            user_designation = "faculty"
        elif student:
            user_designation = "student"
        else:
            user_designation = "staff"
            
        # serailizing the data
        # announcements_serailizer = AnnouncementSerializer(context, many=True)
        

        response_data = {
            "user_designation": user_designation,
            "department": department_name,
            # "announcements": context,
            # "fac_list": context_f
        }
        

        return Response(data = response_data, status=status.HTTP_200_OK)
        # return Response(data = response_data, status=status.HTTP_200_OK)
        
class FacAPIView(APIView):
    def get(self,request):
        usrnm = get_object_or_404(User, username=request.user.username)
        user_info = ExtraInfo.objects.all().select_related('user','department').filter(user=usrnm).first()


        # context = browse_announcements()
        
        
        # Serialize the data into JSON formats
        data = {
            "user_designation": user_info.user_type,
            # "announcements": list(context.values()),  # Assuming 'context' is a dictionary
        }

        return Response(data)
    
class StaffAPIView(APIView):
    def get(self,request):
        usrnm = get_object_or_404(User, username=request.user.username)
        user_info = ExtraInfo.objects.all().select_related('user','department').filter(user=usrnm).first()


        # context = browse_announcements()
        
        
        # Serialize the data into JSON formats
        data = {
            "user_designation": user_info.user_type,
            # "announcements": list(context.values()),  # Assuming 'context' is a dictionary
        }

        return Response(data)
    
class AnnouncementsDataAPIView(APIView):
    def get(self,request,bid):
        filter_branch = decode_branch(bid)
        if not filter_branch:
            return Response({'detail': 'Invalid bid value'}, status=status.HTTP_400_BAD_REQUEST)
        
        ann = Announcements.objects.filter(department=filter_branch)
        ann_serialized = AnnouncementSerializer(ann, many=True).data
        return Response(ann_serialized, status=status.HTTP_200_OK)
    
class FacultyDataAPIView(APIView):
    def get(self, request, bid):
        filter_branch = decode_branch(bid)
        if not filter_branch:
            return Response({'detail': 'Invalid bid value'}, status=status.HTTP_400_BAD_REQUEST)
        
        fac=ExtraInfo.objects.filter(department__name=filter_branch,user_type='faculty')
        response_data = ExtraInfoSerializer(fac, many=True).data
        return Response(response_data, status=status.HTTP_200_OK)
    
def decode_branch(bid):
    try:
        branch = bid.replace('_', ' ')
        match = re.match(r"^([a-zA-Z]+)", branch)
        if match:
            return branch  # Return the branch name

    except (IndexError, KeyError):
        return None  # Handle malformed bid values
    
class AllStudentsAPIView(APIView):
    def get(self, request, bid):
        # Decode bid to filter criteria
        filter_criteria = decode_bid(bid)
        if not filter_criteria:
            return Response({'detail': 'Invalid bid value'}, status=status.HTTP_400_BAD_REQUEST)

        # Query the student list based on filter criteria
        student_list = Student.objects.filter(
            id__user_type='student',
            **filter_criteria
        ).select_related('id')

        # Create a nested dictionary with programme, year, and specialization
        response_data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

        # Populate the dictionary by programme, year, and department
        for student in student_list:
            programme = student.programme  # E.g., 'B.Tech'
            year = student.batch  # E.g., '2022'
            department = student.specialization  # E.g., 'CSE'
            serializer = StudentSerializer(student)
            response_data[programme][year][department].append(serializer.data)

        # Convert defaultdict to a regular dict for JSON response
        response_data = {prog: {yr: dict(depts) for yr, depts in years.items()} for prog, years in response_data.items()}

        return Response(response_data, status=status.HTTP_200_OK)

def decode_bid(bid):
    """Decode bid into filter criteria."""
    try:
        match = re.match(r"([a-zA-Z]+)(\d+)([a-zA-Z]+)", bid)
        if match:
            level = match.group(1)  # e.g., 'btech'
            year = match.group(2)   # e.g., '1'
            specialization = match.group(3)  # e.g., 'CSE'
        
            # Map the level to program name and process year
            programme = {
                'btech': 'B.Tech',
                'bdes': 'B.Des',
                'mtech': 'M.Tech',
                'phd': 'PhD',  
            }.get(level.lower(), None)

            if programme:
                return {
                    'programme': programme,
                    'batch': int(yearset) - int(year) + 1,  # Example: calculate batch based on year
                    'specialization': specialization.upper()  # Normalize specialization to uppercase
                }
    except (IndexError, KeyError):
        return None  # Handle malformed bid values

class InformationAPIView(generics.ListAPIView):
    queryset = Information.objects.all()
    serializer_class = InformationSerializer
    permission_classes = (IsFacultyStaffOrReadOnly,)
class InformationUpdateAPIView(APIView):
    def put(self, request):
        # Ensure the data only contains phone_number, email, and facilities
        data = request.data
        fields_to_update = {key: data[key] for key in ["phone_number", "email", "facilites"] if key in data}

        # Get the department string from the request
        department_name = data.get("department")

        # Get the department info using the department name string
        department_info = DepartmentInfo.objects.filter(name=department_name).first()

        if not department_info:
            return Response({"detail": "Department not found."}, status=status.HTTP_404_NOT_FOUND)

        # Update or create the Information entry for the department
        information_instance, created = Information.objects.update_or_create(
            department=department_info,
            defaults=fields_to_update
        )

        serializer = InformationSerializer(information_instance)
        if created:
            message = "Information created successfully."
        else:
            message = "Information updated successfully."

        return Response({"message": message, "data": serializer.data}, status=status.HTTP_200_OK)
# class UpdateOrCreateInformationAPIView(APIView):
#     """
#     This view will handle POST requests to either update or create
#     an Information entry for a department.
#     """
#     def post(self, request):
#         department_name = request.data.get('department')
#         phone_number = request.data.get('phone_number')
#         email = request.data.get('email')
#         facilities = request.data.get('facilities')

#         # Retrieve the department
#         department = DepartmentInfo.objects.filter(name=department_name).first()
#         if not department:
#             return Response({"error": "Department not found."}, status=status.HTTP_400_BAD_REQUEST)

#         # Check if an entry exists for the department
#         information_entry, created = Information.objects.update_or_create(
#             department=department,
#             defaults={
#                 'phone_number': phone_number,
#                 'email': email,
#                 'facilities': facilities
#             }
#         )

#         serializer = InformationSerializer(information_entry)
#         if created:
#             return Response({"message": "Information created successfully.", "data": serializer.data}, status=status.HTTP_201_CREATED)
#         else:
#             return Response({"message": "Information updated successfully.", "data": serializer.data}, status=status.HTTP_200_OK)

class LabListView(generics.ListAPIView):
    queryset = Lab.objects.all()  # Fetch all lab entries
    serializer_class = LabSerializer


class LabAPIView(APIView):
    def post(self, request):
        data = request.data

        # Ensure all required fields are in the data
        if not all(key in data for key in ["department", "location", "name", "capacity"]):
            return Response({"detail": "Missing required fields."}, status=status.HTTP_400_BAD_REQUEST)

        # Create the Lab instance directly with the data provided
        serializer = LabSerializer(data=data)
        if serializer.is_valid():
            lab = serializer.save()  # No need to set a department object
            return Response(LabSerializer(lab).data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LabDeleteAPIView(APIView):
    def delete(self, request):
        lab_ids = request.data.get('lab_ids', [])
        
        if not lab_ids:
            return Response({"detail": "No lab IDs provided."}, status=status.HTTP_400_BAD_REQUEST)

        deleted_count = 0
        for lab_id in lab_ids:
            try:
                lab = Lab.objects.get(id=lab_id)
                lab.delete()
                deleted_count += 1
            except Lab.DoesNotExist:
                return Response({"detail": f"Lab with id {lab_id} does not exist."}, status=status.HTTP_404_NOT_FOUND)

        return Response({"detail": f"Successfully deleted {deleted_count} labs."}, status=status.HTTP_204_NO_CONTENT)
    
class FeedbackCreateAPIView(generics.CreateAPIView):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer

class FeedbackListView(generics.ListAPIView):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
