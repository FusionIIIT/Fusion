from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status

from applications.programme_curriculum.models import (
    Programme,
    Discipline,
    Curriculum,
    Semester,
    Course,
    Batch,
    CourseSlot,
    CourseInstructor,
)

from .serializers import (
    ProgrammeSerializer,
    CurriculumSerializer,
    ProgrammePostSerializer,
    SemesterSerializer,
    DisciplineSerializer,
    CourseSerializer,
    CourseSlotSerializer,
    BatchSerializer,
    ProgrammeInfoSerializer,
)

from applications.programme_curriculum.filters import (
    CourseFilter,
    BatchFilter,
    CurriculumFilter,
)
from rest_framework import generics


@api_view(["GET", "POST"])
def view_ug_programmes(request):
    """
    This function is used to display all the ug programmes offered by the institute.
    """
    ug = Programme.objects.filter(category="UG")

    ug_serializer = ProgrammeSerializer(ug, many=True)

    return Response(ug_serializer.data)


@api_view(["GET", "POST"])
def view_pg_programmes(request):
    """
    This function is used to display all the ug programmes offered by the institute.
    """
    ug = Programme.objects.filter(category="PG")

    ug_serializer = ProgrammeSerializer(ug, many=True)

    return Response(ug_serializer.data)


@api_view(["GET", "POST"])
def view_phd_programmes(request):
    """
    This function is used to display all the ug programmes offered by the institute.
    """
    ug = Programme.objects.filter(category="PHD")

    ug_serializer = ProgrammeSerializer(ug, many=True)

    return Response(ug_serializer.data)


@api_view(["GET"])
def get_programme_info(request):
    if request.method == "GET":
        # Fetch all programmes
        programmes = Programme.objects.all()

        # Serialize the data
        serializer = ProgrammeInfoSerializer(programmes, many=True)

        # Return the serialized data as response
        return Response(serializer.data)


@api_view(["GET"])
def view_curriculumns(request):
    if request.method == "GET":
        # Fetch all programmes
        curriculums = Curriculum.objects.all()
        serializer = CurriculumSerializer(curriculums, many=True)
        return Response(serializer.data)


@api_view(["POST"])
def create_programme(request):
    if request.method == "POST":
        # Extract data from the request
        category = request.data.get("category")
        name = request.data.get("name")
        programme_begin_year = request.data.get("programme_begin_year")
        discipline_names = request.data.get(
            "discipline"
        )  # Assuming discipline names are sent as a list

        # Validate data
        if not category or not name or not programme_begin_year or not discipline_names:
            return Response(
                {
                    "message": "Please provide category, name, programme_begin_year, and discipline in the request body"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create Programme object
        programme = Programme.objects.create(
            category=category, name=name, programme_begin_year=programme_begin_year
        )

        # Find Discipline objects and associate them with the Programme
        disciplines = []
        for discipline_name in discipline_names:
            try:
                discipline = Discipline.objects.get(name=discipline_name)
                discipline.programmes.add(programme)
                disciplines.append(discipline)
            except Discipline.DoesNotExist:
                # If discipline does not exist, you may handle it according to your application's logic
                # For example, you can create the discipline here
                pass

        # Serialize the Programme object
        serializer = ProgrammePostSerializer(programme)

        return Response(
            {
                "programme": serializer.data,
                "disciplines": [discipline.name for discipline in disciplines],
            },
            status=status.HTTP_201_CREATED,
        )
