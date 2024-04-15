from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status

from applications.programme_curriculum.models import Programme, Discipline, Curriculum, Semester, Course, Batch, CourseSlot, CourseInstructor

from .serializers import ProgrammeSerializer, CurriculumSerializer, SemesterSerializer, DisciplineSerializer, CourseSerializer, CourseSlotSerializer, BatchSerializer, ProgrammeInfoSerializer

from applications.programme_curriculum.filters import CourseFilter, BatchFilter, CurriculumFilter


# @api_view(['GET','POST'])
# def view_all_programmes(request):
#     """
#     This function is used to display all the programmes offered by the institute.
#     """
#     ug = Programme.objects.filter(category='UG')
#     pg = Programme.objects.filter(category='PG')
#     phd = Programme.objects.filter(category='PHD')

#     ug_serializer = ProgrammeSerializer(ug, many=True)
#     pg_serializer = ProgrammeSerializer(pg, many=True)
#     phd_serializer = ProgrammeSerializer(phd, many=True)

#     return Response({'UG': ug_serializer.data, 'PG': pg_serializer.data, 'PHD': phd_serializer.data})


# @api_view(['GET','POST'])
# def view_curriculums_of_a_programme(request, programme_id):
#     """
#     This function is used to Display Curriculum of a specific Programmes.
#     """
#     program = get_object_or_404(Programme, id=programme_id)
#     curriculums = program.curriculums.all()

#     working_curriculums = curriculums.filter(working_curriculum=True)
#     past_curriculums = curriculums.filter(working_curriculum=False)

#     working_curriculum_serializer = CurriculumSerializer(
#         working_curriculums, many=True)
#     past_curriculum_serializer = CurriculumSerializer(
#         past_curriculums, many=True)

#     return Response({'program': program.name,
#                      'working_curriculums': working_curriculum_serializer.data,
#                      'past_curriculums': past_curriculum_serializer.data})


# @api_view(['GET','POST'])
# def view_all_working_curriculums(request):
#     """ Views all the working curriculums offered by the institute """

#     curriculums = Curriculum.objects.filter(working_curriculum=True)
#     curriculum_filter = CurriculumFilter(request.GET, queryset=curriculums)
#     filtered_curriculums = curriculum_filter.qs

#     serializer = CurriculumSerializer(filtered_curriculums, many=True)
#     return Response({'curriculums': serializer.data})


# @api_view(['GET','POST'])
# def view_semesters_of_a_curriculum(request, curriculum_id):
#     """
#     This function is used to Display all Semesters of a Curriculum.
#     """

#     curriculum = get_object_or_404(Curriculum, id=curriculum_id)
#     semesters = curriculum.semesters

#     semester_slots = []
#     for sem in semesters:
#         semester_slots.append(list(sem.courseslots.all()))

#     max_length = max(len(course_slots) for course_slots in semester_slots)
#     for course_slots in semester_slots:
#         course_slots += [""] * (max_length - len(course_slots))

#     semester_credits = []

#     for semester in semesters:
#         credits_sum = 0
#         for course_slot in semester.courseslots.all():
#             max_credit = course_slot.courses.aggregate(
#                 max_credit=models.Max('credit'))['max_credit']
#             credits_sum += max_credit if max_credit else 0
#         semester_credits.append(credits_sum)

#     return Response({'curriculum': CurriculumSerializer(curriculum).data,
#                      'semesters': [serializer.data for serializer in SemesterSerializer(semesters, many=True).data],
#                      'semester_slots': semester_slots,
#                      'semester_credits': semester_credits})


# @api_view(['GET','POST'])
# def view_a_semester_of_a_curriculum(request, semester_id):
#     """ Views a specific semester of a specific curriculum. """
#     semester = get_object_or_404(Semester, id=semester_id)
#     course_slots = semester.courseslots.all()
#     serializer = SemesterSerializer(semester)
#     return Response({'semester': serializer.data, 'course_slots': CourseSlotSerializer(course_slots, many=True).data})


# @api_view(['GET','POST'])
# def view_a_courseslot(request, courseslot_id):
#     """ View a course slot. """
#     course_slot = get_object_or_404(CourseSlot, id=courseslot_id)
#     serializer = CourseSlotSerializer(course_slot)
#     return Response({'course_slot': serializer.data})


# @api_view(['GET','POST'])
# def view_all_courses(request):
#     """ Views all the course slots of a specific semester. """
#     courses = Course.objects.all()
#     coursefilter = CourseFilter(request.GET, queryset=courses)
#     courses = coursefilter.qs
#     serializer = CourseSerializer(courses, many=True)
#     return Response({'courses': serializer.data, 'coursefilter': coursefilter.data})


# @api_view(['GET','POST'])
# def view_a_course(request, course_id):
#     """ Views the details of a Course. """
#     course = get_object_or_404(Course, id=course_id)
#     serializer = CourseSerializer(course)
#     return Response({'course': serializer.data})


# @api_view(['GET','POST'])
# def view_all_discplines(request):
#     """ Views all disciplines. """
#     disciplines = Discipline.objects.all()
#     serializer = DisciplineSerializer(disciplines, many=True)
#     return Response({'disciplines': serializer.data})


# @api_view(['GET','POST'])
# def view_all_batches(request):
#     """ Views all batches. """
#     batches = Batch.objects.all().order_by('year')
#     batchfilter = BatchFilter(request.GET, queryset=batches)
#     batches = batchfilter.qs
#     finished_batches = batches.filter(running_batch=False)
#     batches = batches.filter(running_batch=True)
#     serializer = BatchSerializer(batches, many=True)
#     return Response({'batches': serializer.data, 'finished_batches': finished_batches, 'batchfilter': batchfilter.data})


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
        # Extract data from request body
        category = request.data.get('category')
        name = request.data.get('name')
        programme_begin_year = request.data.get('begin_year')
        discipline_names = request.data.get('discipline', [])  # Assuming discipline is a list of discipline names
        
        # Search for existing discipline objects
        existing_disciplines = Discipline.objects.filter(name__in=discipline_names)
        
        # Create new discipline objects for those that don't exist
        new_disciplines = []
        for discipline_name in discipline_names:
            if discipline_name not in [discipline.name for discipline in existing_disciplines]:
                new_discipline = Discipline.objects.create(name=discipline_name)
                existing_disciplines.append(new_discipline)
                new_disciplines.append(new_discipline)
        
        # Create the programme instance
        programme = Programme.objects.create(
            category=category,
            name=name,
            programme_begin_year=programme_begin_year
        )
        
        # Assign associated discipline objects to the programme
        programme.disciplines.set(existing_disciplines)
        
        # Serialize the programme instance
        serializer = ProgrammeSerializer(programme)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)