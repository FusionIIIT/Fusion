from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status

from applications.programme_curriculum.models import Programme, Discipline, Curriculum, Semester, Course, Batch, CourseSlot, CourseInstructor

from .serializers import ProgrammeSerializer, CurriculumSerializer,ProgrammePostSerializer, SemesterSerializer, DisciplineSerializer, CourseSerializer, CourseSlotSerializer, BatchSerializer, ProgrammeInfoSerializer

from applications.programme_curriculum.filters import CourseFilter, BatchFilter, CurriculumFilter
from rest_framework import generics





@api_view(['GET','POST'])
def view_ug_programmes(request):
    """
    This function is used to display all the ug programmes offered by the institute.
    """
    ug = Programme.objects.filter(category='UG')
    

    ug_serializer = ProgrammeSerializer(ug, many=True)
    

    return Response(ug_serializer.data)

@api_view(['GET','POST'])
def view_pg_programmes(request):
    """
    This function is used to display all the ug programmes offered by the institute.
    """
    ug = Programme.objects.filter(category='PG')
    

    ug_serializer = ProgrammeSerializer(ug, many=True)
    

    return Response(ug_serializer.data)

@api_view(['GET','POST'])
def view_phd_programmes(request):
    """
    This function is used to display all the ug programmes offered by the institute.
    """
    ug = Programme.objects.filter(category='PHD')
    

    ug_serializer = ProgrammeSerializer(ug, many=True)
    

    return Response(ug_serializer.data)

@api_view(['GET'])
def get_programme_info(request):
    if request.method == 'GET':
        # Fetch all programmes
        programmes = Programme.objects.all()
        
        # Serialize the data
        serializer = ProgrammeInfoSerializer(programmes, many=True)
        
        # Return the serialized data as response
        return Response(serializer.data)
    
@api_view(['GET'])
def view_curriculumns(request):
    if request.method == 'GET':
        # Fetch all programmes
        curriculums = Curriculum.objects.all()
        serializer = CurriculumSerializer(curriculums, many=True)
        return Response(serializer.data)


@api_view(['POST'])
def create_programme(request):
    if request.method == 'POST':
        serializer = ProgrammePostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)