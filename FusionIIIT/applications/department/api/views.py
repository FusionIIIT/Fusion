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

        fac_view = user.holds_designations.filter(designation__name='faculty').exists()
        student = user.holds_designations.filter(designation__name='student').exists()
        staff = user.holds_designations.filter(designation__name='staff').exists()

        context = browse_announcements()
        context_f = faculty()
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
            "announcements": context,
            "fac_list": context_f
        }
        

        return Response(data = response_data, status=status.HTTP_200_OK)
        # return Response(data = response_data, status=status.HTTP_200_OK)
        
class FacAPIView(APIView):
    def get(self,request):
        usrnm = get_object_or_404(User, username=request.user.username)
        user_info = ExtraInfo.objects.all().select_related('user','department').filter(user=usrnm).first()


        context = browse_announcements()
        
        
        # Serialize the data into JSON formats
        data = {
            "user_designation": user_info.user_type,
            "announcements": list(context.values()),  # Assuming 'context' is a dictionary
        }

        return Response(data)
    
class StaffAPIView(APIView):
    def get(self,request):
        usrnm = get_object_or_404(User, username=request.user.username)
        user_info = ExtraInfo.objects.all().select_related('user','department').filter(user=usrnm).first()


        context = browse_announcements()
        
        
        # Serialize the data into JSON formats
        data = {
            "user_designation": user_info.user_type,
            "announcements": list(context.values()),  # Assuming 'context' is a dictionary
        }

        return Response(data)
    
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
        print(match)
        if match:
            level = match.group(1)  # e.g., 'btech'
            year = match.group(2)   # e.g., '1'
            specialization = match.group(3)  # e.g., 'CSE'
        
            # Map the level to program name and process year
            programme = {
                'btech': 'B.Tech',
                'mtech': 'M.Tech',
                'phd': 'PhD',  
            }.get(level.lower(), None)

            if programme:
                print(year, programme, specialization)
                return {
                    'programme': programme,
                    'batch': 2022 - int(year) + 1,  # Example: calculate batch based on year
                    'specialization': specialization.upper()  # Normalize specialization to uppercase
                }
    except (IndexError, KeyError):
        return None  # Handle malformed bid values
    
def browse_announcements():
    """
    This function is used to browse Announcements Department-Wise
    made by different faculties and admin.

    @variables:
        cse_ann - Stores CSE Department Announcements
        ece_ann - Stores ECE Department Announcements
        me_ann - Stores ME Department Announcements
        sm_ann - Stores SM Department Announcements
        all_ann - Stores Announcements intended for all Departments
        context - Dictionary for storing all above data

    """
    cse_ann = Announcements.objects.filter(department="CSE")
    ece_ann = Announcements.objects.filter(department="ECE")
    me_ann = Announcements.objects.filter(department="ME")
    sm_ann = Announcements.objects.filter(department="SM")
    all_ann = Announcements.objects.filter(department="ALL")
    
    # serailizing the data
    cse_ann_serialized = AnnouncementSerializer(cse_ann, many=True)
    ece_ann_serialized = AnnouncementSerializer(ece_ann, many=True)
    me_ann_serialized = AnnouncementSerializer(me_ann, many=True)
    sm_ann_serialized = AnnouncementSerializer(sm_ann, many=True)
    all_ann_serialized = AnnouncementSerializer(all_ann, many=True)

    context = {
        "cse" : cse_ann_serialized.data,
        "ece" : ece_ann_serialized.data,
        "me" : me_ann_serialized.data,
        "sm" : sm_ann_serialized.data,
        "all" : all_ann_serialized.data
    }

    return context

def faculty():
    """
    This function is used to Return data of Faculties Department-Wise.

    @variables:
        cse_f - Stores data of faculties from CSE Department
        ece_f - Stores data of faculties from ECE Department
        me_f - Stores data of faculties from ME Department
        sm_f - Stores data of faculties from ME Department
        context_f - Stores all above variables in Dictionary

    """
    cse_f=ExtraInfo.objects.filter(department__name='CSE',user_type='faculty')
    ece_f=ExtraInfo.objects.filter(department__name='ECE',user_type='faculty')
    me_f=ExtraInfo.objects.filter(department__name='ME',user_type='faculty')
    sm_f=ExtraInfo.objects.filter(department__name='SM',user_type='faculty')
    staff=ExtraInfo.objects.filter(user_type='staff')

    # serailizing the data
    cse_f = ExtraInfoSerializer(cse_f, many=True)
    ece_f = ExtraInfoSerializer(ece_f, many=True)
    me_f = ExtraInfoSerializer(me_f, many=True)
    sm_f = ExtraInfoSerializer(sm_f, many=True)
    staff = ExtraInfoSerializer(staff, many=True)
    

    context_f = {
        "cse_f" : cse_f.data,
        "ece_f" : ece_f.data,
        "me_f" : me_f.data,
        "sm_f" : sm_f.data,
        "staff" : staff.data,
    }
    return context_f