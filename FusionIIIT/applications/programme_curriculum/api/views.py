from django.db.models.query_utils import Q
from django.http import request
from django.shortcuts import get_object_or_404, render, HttpResponse,redirect
from django.http import HttpResponse, HttpResponseRedirect,JsonResponse
import datetime
# import itertools
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from ..models import Programme, Discipline, Curriculum, Semester, Course, Batch, CourseSlot,NewProposalFile,Proposal_Tracking,CourseInstructor
from ..forms import ProgrammeForm, DisciplineForm, CurriculumForm, SemesterForm, CourseForm, BatchForm, CourseSlotForm, ReplicateCurriculumForm,NewCourseProposalFile,CourseProposalTrackingFile, CourseInstructor, CourseInstructorForm
from ..filters import CourseFilter, BatchFilter, CurriculumFilter

from .serializers import CourseSerializer,CurriculumSerializer,BatchSerializer
from django.core.serializers import serialize
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.forms.models import model_to_dict
import json, xlrd
from django.db.models import F
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated 
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
import re

from notification.views import prog_and_curr_notif
# from applications.academic_information.models import Student
from applications.globals.models import (DepartmentInfo, Designation,ExtraInfo, Faculty, HoldsDesignation)
# ------------module-functions---------------#

@login_required(login_url='/accounts/login')
def programme_curriculum(request):
    """
    This function is used to Differenciate acadadmin and all other user.

    @param:
        request - contains metadata about the requested page

    @variables:
        user_details - Gets the information about the logged in user.
        des - Gets the designation about the looged in user.
    """
    user=request.user
    
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if request.session['currentDesignationSelected']== "student" or request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" or request.session['currentDesignationSelected']== "Dean Academic":
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif 'hod' in request.session['currentDesignationSelected'].lower() :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif request.session['currentDesignationSelected'] == "acadadmin" :
        return HttpResponseRedirect('/programme_curriculum/admin_programmes')
    
    return HttpResponseRedirect('/programme_curriculum/programmes/')



# ------------all-user-functions---------------#



def view_all_programmes(request):
    """
    This function is used to display all the programmes offered by the institute.
    @variables:
        ug - UG programmes
        pg - PG programmes
        phd - PHD programmes 
    """
    url='programme_curriculum/'
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if  request.session['currentDesignationSelected']== "acadadmin":
        return render(request, 'programme_curriculum/admin_programmes/')
        
    elif request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" or request.session['currentDesignationSelected']== "Dean Academic" :
        url+='faculty/'
        
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        url+='faculty/'
    notifs = request.user.notifications.all()

    ug = Programme.objects.filter(category='UG')
    pg = Programme.objects.filter(category='PG')
    phd = Programme.objects.filter(category='PHD')
    url+='view_all_programmes.html'

    return render(request, url, {'ug': ug, 'pg': pg, 'phd': phd,'notifications': notifs,})


def view_curriculums_of_a_programme(request, programme_id):
    """
    This function is used to Display Curriculum of a specific Programmes in JSON format.

    @param:
        programme_id - Id of a specific programme
        
    @variables:
        curriculums - Curriculums of a specific programmes
        working_curriculum - Curriculums that are active
        past_curriculum - Curriculums that are obsolete
    """
    # user_details = ExtraInfo.objects.get(user=request.user)
    # des = HoldsDesignation.objects.filter(user=request.user).first()
    
    # Commented out role-based URL adjustments
    # if request.session['currentDesignationSelected'] == "acadadmin":
    #     return render(request, 'programme_curriculum/admin_programmes/')
        
    # elif request.session['currentDesignationSelected'] in ["Associate Professor", "Professor", "Assistant Professor", "Dean Academic"]:
    #     url += 'faculty/'
        
    # elif 'hod' in request.session['currentDesignationSelected'].lower():
    #     url += 'faculty/'

    # Fetch program and related curriculums
    program = get_object_or_404(Programme, id=programme_id)
    print(program.name)
    curriculums = program.curriculums.all()  # Adjust if it's a related name


    # Apply filters
    curriculumfilter = CurriculumFilter(request.GET, queryset=curriculums)
    curriculums = curriculumfilter.qs

    # Separate working and past curriculums
    batches = Batch.objects.all()
    working_curriculums = curriculums.filter(working_curriculum=1)
    past_curriculums = curriculums.filter(working_curriculum=0)

    # Prepare JSON data
    data = {
        'program': model_to_dict(program),
        'name':program.name,
        # 'working_curriculums': [model_to_dict(c) for c in working_curriculums],
        'working_curriculums': [
            {
                **model_to_dict(c),
                'batches': [model_to_dict(b) for b in c.batches.all()]
                # Add batches for each curriculum
            }
            for c in working_curriculums
        ],
        'past_curriculums': [model_to_dict(c) for c in past_curriculums],
        # 'notifications': [model_to_dict(n) for n in request.user.notifications.all()]
    }

    return JsonResponse(data)


def view_all_working_curriculums(request):
    
    """ views all the working curriculums offered by the institute """
    url='programme_curriculum/'
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if  request.session['currentDesignationSelected']== "acadadmin":
        return render(request, 'programme_curriculum/admin_programmes/')

    elif request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" or request.session['currentDesignationSelected']== "Dean Academic" :

        url+='faculty/'
    
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        url+='faculty/'
    curriculums = Curriculum.objects.filter(working_curriculum=1)
    notifs = request.user.notifications.all()
    curriculumfilter = CurriculumFilter(request.GET, queryset=curriculums)

    curriculums = curriculumfilter.qs
    return render(request,url+'view_all_working_curriculums.html',{'curriculums':curriculums, 'curriculumfilter': curriculumfilter,'notifications': notifs,})

def view_semesters_of_a_curriculum(request, curriculum_id):
    """ API to get all the semesters of a specific curriculum """

    # user_details = ExtraInfo.objects.get(user=request.user)
    # des = HoldsDesignation.objects.all().filter(user=request.user).first()

    # # Redirect logic based on user designation
    # if request.session['currentDesignationSelected'] in ["student", "Associate Professor", "Professor", "Assistant Professor"]:
    #     return HttpResponseRedirect('/programme_curriculum/programmes/')
    # elif str(request.user) == "acadadmin":
    #     pass
    # elif 'hod' in request.session['currentDesignationSelected'].lower():
    #     return HttpResponseRedirect('/programme_curriculum/programmes/')

    curriculum = get_object_or_404(Curriculum, Q(id=curriculum_id))
    semesters = curriculum.semesters.all()

    semester_slots = []
    for sem in semesters:
        a = list(sem.courseslots.all())
        semester_slots.append(a)

    # Pad the course slots to ensure even length
    max_length = max(len(course_slots) for course_slots in semester_slots)
    for course_slots in semester_slots:
        course_slots += [""] * (max_length - len(course_slots))

    # Calculate total credits for each semester
    semester_credits = []
    for semester in semesters:
        credits_sum = 0
        for course_slot in semester.courseslots.all():
            max_credit = max(course.credit for course in course_slot.courses.all())
            credits_sum += max_credit
        semester_credits.append(credits_sum)

    # Transpose the semester slots for easy tabular representation
    transpose_semester_slots = list(zip(*semester_slots))

    # Get all batches excluding the current curriculum
    all_batches = Batch.objects.filter(running_batch=True, curriculum=curriculum_id).order_by('year')

    # Prepare the response data structure
    data = {
        'name': curriculum.name,
        'no_of_semester': len(semesters),
        'semesters': [{
            'id': sem.id,
            'semester_no': sem.semester_no,
            'start_semester': sem.start_semester,  # Add any other fields needed by the frontend
            'end_semester': sem.end_semester,
            'instigate_semester': sem.instigate_semester,
        } for sem in semesters],
        'semester_slots': [
            [{
                'id': course_slot.id,
                'name': course_slot.name,
                # 'code':course_slot.code,
                'courses': [{'name': course.name, 'code':course.code,'lecture_hours': course.lecture_hours, 'tutorial_hours': course.tutorial_hours, 'credit': course.credit} for course in course_slot.courses.all()]
            } if course_slot else None for course_slot in course_slots]
            for course_slots in transpose_semester_slots
        ],
        'semester_credits': semester_credits,
        'batches': list(all_batches.values_list('name', 'year'))
    }

    # Return the data as a JSON response for the frontend
    return JsonResponse(data)


def view_a_semester_of_a_curriculum(request, semester_id):
    """
    Retrieve and return details of a specific semester of a specific curriculum in JSON format.
    
    Args:
    - semester_id: The ID of the semester to fetch.
    
    Returns:
    - JSON response containing semester details and associated course slots.
    """
    # Fetch the specific semester or return a 404 if not found
    semester = get_object_or_404(Semester, id=semester_id)

    # Fetch the associated course slots for the semester
    course_slots = semester.courseslots  # Using the property defined in the Semester model
    
    # Prepare data for the semester and its course slots
    semester_data = {
        'id': semester.id,
        'curriculum': semester.curriculum.name,  # Get the curriculum name
        'semester_no': semester.semester_no,  # Use semester_no from the Semester model
        'start_semester': semester.start_semester.isoformat() if semester.start_semester else None,
        'end_semester': semester.end_semester.isoformat() if semester.end_semester else None,
        'instigate_semester': semester.instigate_semester,
        'semester_info': semester.semester_info,
        'course_slots': [
            {
                'id': slot.id,
                'type': slot.type,  # Assuming the CourseSlot model has a 'type' field
                'course_slot_info': slot.course_slot_info,  # Assuming this field exists in CourseSlot
                'duration': slot.duration,  # Assuming this field exists
                'name': slot.name,
                'courses': [
                    {
                        'id': course.id,
                        'code': course.code,
                        'name': course.name,
                        'credits': course.credit,
                    } for course in slot.courses.all()  # Fetch related courses for each slot
                ]
            } for slot in course_slots
        ]
    }

    # Return the semester and course slot details as JSON
    return JsonResponse({'semester': semester_data})


def view_a_courseslot(request, courseslot_id):
    """ view a course slot """
    # user_details = ExtraInfo.objects.get(user=request.user)
    # des = HoldsDesignation.objects.all().filter(user=request.user).first()
    
    # if request.session['currentDesignationSelected'] == "acadadmin":
    #     # Return relevant response for 'acadadmin'
    #     return JsonResponse({'message': 'Unauthorized for this operation'}, status=403)
    
    # elif request.session['currentDesignationSelected'] in ["Associate Professor", "Professor", "Assistant Professor", "Dean Academic"]:
    #     # Handling for faculty members
    #     user_type = "faculty"
    
    # elif 'hod' in request.session['currentDesignationSelected'].lower():
    #     # Handling for hod
    #     user_type = "faculty"
    
    # else:
    #     # Default case if no designation matched
    #     return JsonResponse({'message': 'Invalid designation'}, status=403)

    # Fetch the course slot details
    course_slot = get_object_or_404(CourseSlot, id=courseslot_id)
    
    # Prepare the course slot data to return in JSON format
    data = {
        'id': course_slot.id,
        'name': course_slot.name,
        'semester': course_slot.semester.__str__(),  # You can use str or a specific field from the semester
        'type': course_slot.type,
        'course_slot_info': course_slot.course_slot_info,
        'min_registration_limit': course_slot.min_registration_limit,
        'max_registration_limit': course_slot.max_registration_limit,
        'duration': course_slot.duration,
        'courses': [
            {
                'id': course.id,
                'code': course.code,
                'name': course.name,
                'credit': course.credit,
            } for course in course_slot.courses.all()
        ]
    }
    
    # Return the course slot data as a JSON response
    return JsonResponse(data)


def view_all_courses(request):
    """
    Retrieve and return details of all courses in JSON format.
    
    Returns:
    - JSON response containing a list of courses.
    """
    # Fetch all courses
    courses = Course.objects.all()

    # Apply filtering based on request parameters (if any)
    coursefilter = CourseFilter(request.GET, queryset=courses)
    filtered_courses = coursefilter.qs

    # Prepare the data to return in JSON format
    courses_data = [
        {
            'id': course.id,
            'code': course.code,
            'name': course.name,
            'credit': course.credit,
            'department': course.department.name,  # Assuming course has a department relation
            'semester': course.semester.__str__(),  # You can change this based on the relation structure
        } for course in filtered_courses
    ]

    # Return the filtered courses as a JSON response
    return JsonResponse({'courses': courses_data})


def view_a_course(request, course_id):
    """ views the details of a Course """
    url='programme_curriculum/'
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if  request.session['currentDesignationSelected']== "acadadmin":
        return render(request, 'programme_curriculum/admin_programmes/')
    elif request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" or request.session['currentDesignationSelected']== "Dean Academic" :

        url+='faculty/'
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        url+='faculty/'
    course = get_object_or_404(Course, Q(id=course_id))
    notifs = request.user.notifications.all()
    return render(request, url+'view_a_course.html', {'course': course,'notifications': notifs,})


def view_all_discplines(request):
    """ views the details of a Course """
    url='programme_curriculum/'
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if  request.session['currentDesignationSelected']== "acadadmin":
        return render(request, 'programme_curriculum/admin_programmes/')
    elif request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" or request.session['currentDesignationSelected']== "Dean Academic" :
        url+='faculty/'
    
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        url+='faculty/'

    disciplines = Discipline.objects.all()
    notifs = request.user.notifications.all()
    return render(request, url+'view_all_disciplines.html', {'disciplines': disciplines,'notifications': notifs,})


def view_all_batches(request):
    """ views the details of a Course """
    url='programme_curriculum/'
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if  request.session['currentDesignationSelected']== "acadadmin":
        return render(request, 'programme_curriculum/admin_programmes/')
    elif request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" or request.session['currentDesignationSelected']== "Dean Academic" :

        url+='faculty/'
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        url+='faculty/'

    batches = Batch.objects.all().order_by('year')

    batchfilter = BatchFilter(request.GET, queryset=batches)

    batches = batchfilter.qs

    finished_batches = batches.filter(running_batch=False)

    batches = batches.filter(running_batch=True)
    notifs = request.user.notifications.all()

    return render(request, url+'view_all_batches.html', {'batches': batches, 'finished_batches': finished_batches, 'batchfilter': batchfilter,'notifications': notifs,})




# ------------Acad-Admin-functions---------------#


# @api_view(['GET'])
# @login_required(login_url='/accounts/login')
def admin_view_all_programmes(request):
    """
    API to return all programmes (UG, PG, PhD) for an admin user.
    """
    # Fetch programmes based on their category
    ug = Programme.objects.filter(category='UG').prefetch_related('discipline_set').values(
        'id', 'name', 'category', 'programme_begin_year', 'discipline__name'
    )
    pg = Programme.objects.filter(category='PG').prefetch_related('discipline_set').values(
        'id', 'name', 'category', 'programme_begin_year', 'discipline__name'
    )
    phd = Programme.objects.filter(category='PHD').prefetch_related('discipline_set').values(
        'id', 'name', 'category', 'programme_begin_year', 'discipline__name'
    )
    print(ug)
    # Prepare the JSON response data
    response_data = {
        'ug_programmes': list(ug),
        'pg_programmes': list(pg),
        'phd_programmes': list(phd)
    }

    # Return a JsonResponse
    return JsonResponse(response_data, status=200, safe=False)

@api_view(['GET'])
def admin_view_curriculums_of_a_programme(request, programme_id):
    program = get_object_or_404(Programme, id=programme_id)
    curriculums = program.curriculums.all()

    # Filtering working and past curriculums
    working_curriculums = curriculums.filter(working_curriculum=1)
    past_curriculums = curriculums.filter(working_curriculum=0)

    data = {
        'program': {
            'id': program.id,
            'name': program.name,
            'category': program.category,
            'beginyear': program.programme_begin_year,
        },
        'working_curriculums': CurriculumSerializer(working_curriculums, many=True).data,
        'past_curriculums': CurriculumSerializer(past_curriculums, many=True).data,
    }
    return JsonResponse(data)

@api_view(['GET'])
def Admin_view_all_working_curriculums(request):
    """API view to return all working curriculums offered by the institute as JSON"""

    user_details = ExtraInfo.objects.get(user=request.user)
    des = HoldsDesignation.objects.filter(user=request.user).first()

    # Access control: redirect non-admin users
    # if request.session['currentDesignationSelected'] in ["student", "Associate Professor", "Professor", "Assistant Professor"]:
    #     return JsonResponse({'error': 'Access denied'}, status=403)
    # elif str(request.user) != "acadadmin" and 'hod' not in request.session['currentDesignationSelected'].lower():
    #     return JsonResponse({'error': 'Access denied'}, status=403)

    # Fetch all working curriculums
    curriculums = Curriculum.objects.filter(working_curriculum=1)

    # Filter based on GET parameters if any (curriculum filter)
    curriculumfilter = CurriculumFilter(request.GET, queryset=curriculums)
    curriculums = curriculumfilter.qs

    # Manually serialize the curriculums into a list of dictionaries
    curriculum_data = []
    for curriculum in curriculums:
        curriculum_data.append({
            'id':curriculum.id,
            'name': curriculum.name,
            'version': str(curriculum.version),  # Convert Decimal to string for JSON compatibility
            'batch': [str(batch) for batch in curriculum.batches],  # Use batches property from model
            'semesters': curriculum.no_of_semester,
        })

    # Return the data as JSON response
    return JsonResponse({'curriculums': curriculum_data}, safe=False)

def admin_view_semesters_of_a_curriculum(request, curriculum_id):
    """API endpoint to get all semesters of a specific curriculum for React frontend."""
        
    # Check user permissions
    # if request.session['currentDesignationSelected'] in ["student", "Associate Professor", "Professor", "Assistant Professor"] or ('hod' in request.session['currentDesignationSelected'].lower() and str(request.user) != "acadadmin"):
    #     return JsonResponse({'error': 'Unauthorized access'}, status=403)

    curriculum = get_object_or_404(Curriculum, Q(id=curriculum_id))
    semesters = curriculum.semesters.all()

    # Prepare semesters data
    semester_slots = []
    semester_credits = []

    semester_data = []
    for semester in semesters:
        # For each slot in the semester, retrieve associated courses
        slots = []
        for slot in semester.courseslots.all():
            courses = list(slot.courses.values('id', 'name', 'code', 'credit','tutorial_hours','lecture_hours'))  # Adjust fields as needed
            slots.append({
                'id': slot.id,
                'type': slot.type,
                'name': slot.name,
                'courses': courses
            })
        
        # Calculate total credits for the semester based on maximum credit of each course slot
        credits_sum = sum(max(course['credit'] for course in slot['courses']) if slot['courses'] else 0 for slot in slots)
        
        semester_data.append({
            'id':semester.id,
            'semester_no': semester.semester_no,
            'start_semester': semester.start_semester,
            'end_semester': semester.end_semester,
            'slots': slots,
            'credits': credits_sum
        })
    all_batches = Batch.objects.filter(running_batch=True, curriculum=curriculum_id).order_by('year')
    batch_data = [
        {
            'id': batch.id,
            'name': batch.name,
            'discipline': batch.discipline.acronym,  # Use acronym or other attributes if available in Discipline
            'year': batch.year,
            'running_batch': batch.running_batch
        } for batch in all_batches
    ]
    batches_without_curriculum = Batch.objects.filter(curriculum__isnull=True)
    unlinked_batch_data=[
        {
            'id': batch.id,
            'name': batch.name,
            'discipline': batch.discipline.acronym,  # Use acronym or other attributes if available in Discipline
            'year': batch.year,
            'running_batch': batch.running_batch
        } for batch in batches_without_curriculum
    ]
    curriculum_data = {
        'curriculum_id': curriculum.id,
        'curriculum_name': curriculum.name,
        'version': curriculum.version,
        'programme_id': curriculum.programme.id,
        'batches':batch_data,
        'semesters': semester_data,
        'unlikedbatches':unlinked_batch_data,
        'working_curriculum':curriculum.working_curriculum
    }

    return JsonResponse(curriculum_data)

def admin_view_a_semester_of_a_curriculum(request, semester_id):
    # user_details = ExtraInfo.objects.get(user=request.user)
    # des = HoldsDesignation.objects.filter(user=request.user).first()

    # # Access Control
    # if request.session['currentDesignationSelected'] in ["student", "Associate Professor", "Professor", "Assistant Professor"]:
    #     return JsonResponse({'error': 'Access denied'}, status=403)
    # elif str(request.user) == "acadadmin" or 'hod' in request.session['currentDesignationSelected'].lower():
    #     pass
    # else:
    #     return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Get semester and course slots
    semester = get_object_or_404(Semester, id=semester_id)
    course_slots = semester.courseslot_set.all()

    # Prepare JSON response
    # print(semester.curriculum)
    semester_data = {
        'id': semester.id,
        'semester_no':semester.semester_no,
        'curriculum':semester.curriculum.name,
        'curriculum_version':semester.curriculum.version,
        'instigate_semester':semester.instigate_semester,
        'start_semester':semester.start_semester,
        'end_semester':semester.end_semester,
        'semester_info':semester.semester_info,
        'course_slots': [
            {
                'id': slot.id,
                'name': slot.name,
                'type': slot.type,
                'course_slot_info': slot.course_slot_info,
                'duration': slot.duration,
                'min_registration_limit': slot.min_registration_limit,
                'max_registration_limit': slot.max_registration_limit,
                'courses': [
                    {
                        'id': course.id,
                        'code': course.code,
                        'name': course.name,
                        'credit': course.credit
                    } for course in slot.courses.all()
                ]
            }
            for slot in course_slots
        ]
    }

    return JsonResponse(semester_data, safe=False)

def admin_view_a_courseslot(request, courseslot_id):
    """API to view a course slot"""

    # # Check user designation and role
    # user_details = ExtraInfo.objects.get(user=request.user)
    # des = HoldsDesignation.objects.filter(user=request.user).first()
    # current_designation = request.session.get('currentDesignationSelected', '').lower()

    # if current_designation in ["student", "associate professor", "professor", "assistant professor"]:
    #     return JsonResponse({'redirect': '/programme_curriculum/programmes/'}, status=302)
    # elif str(request.user) == "acadadmin":
    #     pass
    # elif 'hod' in current_designation:
    #     return JsonResponse({'redirect': '/programme_curriculum/programmes/'}, status=302)

    # Get course slot and check for edit mode
    course_slot = get_object_or_404(CourseSlot, Q(id=courseslot_id))
    edit = request.POST.get('edit', -1)

    if edit == str(course_slot.id):
        # Return edit information
        return JsonResponse({
            'course_slot': {
                'id': course_slot.id,
                'name': course_slot.name,
                'semester':course_slot.semester,
                'type':course_slot.type,
                'course_slot_info':course_slot.course_slot_info,
                'duration':course_slot.duration,
                'min_registration_limit':course_slot.min_registration_limit,
                'max_registration_limit':course_slot.max_registration_limit,
                
                # Add other fields as necessary
            },
            'edit': True
        })

    # Default response if not in edit mode
    print(course_slot.semester.curriculum)
    return JsonResponse({
        'course_slot': {
            'id': course_slot.id,
            'name': course_slot.name,
            'type':course_slot.type,
            'course_slot_info':course_slot.course_slot_info,
            'duration':course_slot.duration,
            'min_registration_limit':course_slot.min_registration_limit,
            'max_registration_limit':course_slot.max_registration_limit,
            "courses": [
            {
                "id": course.id,
                "code":course.code,
                "name": course.name,
                "credit": course.credit,
               
            } for course in course_slot.courses.all()
            ],
            "curriculum": {
                "id": course_slot.semester.curriculum.id,
                "name": course_slot.semester.curriculum.name,
                "version": course_slot.semester.curriculum.version,
                "semester_no":course_slot.semester.semester_no,
            }
                
        },
        'edit': False
    })

@api_view(['GET'])
def admin_view_all_courses(request):
    """Returns all courses with required fields as JSON data."""

    # Ensure that only authorized users can access this data (based on your logic)
    # if request.session['currentDesignationSelected'] in ["student", "Associate Professor", "Professor", "Assistant Professor"]:
    #     return JsonResponse({'error': 'Unauthorized access'}, status=403)
    # elif str(request.user) == "acadadmin":
    #     pass
    # elif 'hod' in request.session['currentDesignationSelected'].lower():
    #     return JsonResponse({'error': 'Unauthorized access'}, status=403)

    # Get all courses
    courses = Course.objects.all()
    
    # Apply filters if necessary
    coursefilter = CourseFilter(request.GET, queryset=courses)
    courses = coursefilter.qs

    # Prepare data for JSON response (only include relevant fields)
    courses_data = [
        {
            "id": course.id,
            "code": course.code,
            "name": course.name,
            "version": str(course.version),
            "credits": course.credit
        }
        for course in courses
    ]

    return JsonResponse({'courses': courses_data})

@api_view(['GET'])
def admin_view_a_course(request, course_id):
    """View to handle the details of a Course as an API"""

    # Get user details
    user_details = ExtraInfo.objects.get(user=request.user)
    des = HoldsDesignation.objects.filter(user=request.user).first()

    # Check if the user is authorized to view the course details
    # if request.session['currentDesignationSelected'] in [
    #     "student", 
    #     "Associate Professor", 
    #     "Professor", 
    #     "Assistant Professor"
    # ]:
    #     return JsonResponse({'error': 'Unauthorized access'}, status=403)
    
    # if str(request.user) == "acadadmin":
    #     pass  # Acadadmin can view the course
    # elif 'hod' in request.session['currentDesignationSelected'].lower():
    #     return JsonResponse({'error': 'Unauthorized access'}, status=403)

    # Fetch the course based on the course_id
    course = get_object_or_404(Course, Q(id=course_id))
    course_serializer = CourseSerializer(course)
   
    

    # Send the course data as JSON
    return JsonResponse(course_serializer.data, safe=False)
# def admin_view_all_discplines(request):
#     """ views the details of a Course """

#     user_details = ExtraInfo.objects.get(user = request.user)
#     des = HoldsDesignation.objects.all().filter(user = request.user).first()
#     if request.session['currentDesignationSelected']== "student" or request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" :
#         return HttpResponseRedirect('/programme_curriculum/programmes/')
#     elif str(request.user) == "acadadmin" :
#         pass
#     elif 'hod' in request.session['currentDesignationSelected'].lower():
#         return HttpResponseRedirect('/programme_curriculum/programmes/')

#     disciplines = Discipline.objects.all()
#     return render(request, 'programme_curriculum/acad_admin/admin_view_all_disciplines.html', {'disciplines': disciplines})
@api_view(['GET'])
def admin_view_all_discplines(request):
    """API to view all disciplines with related programmes"""

    user_details = ExtraInfo.objects.get(user=request.user)
    des = HoldsDesignation.objects.filter(user=request.user).first()

    # Ensure only authorized users can access
    # if request.session['currentDesignationSelected'] in ["student", "Associate Professor", "Professor", "Assistant Professor"]:
    #     return HttpResponseRedirect('/programme_curriculum/programmes/')
    # elif str(request.user) == "acadadmin":
    #     pass
    # elif 'hod' in request.session['currentDesignationSelected'].lower():
    #     return HttpResponseRedirect('/programme_curriculum/programmes/')

    # Get all disciplines and related programmes
    disciplines = Discipline.objects.all().prefetch_related('programmes')

    # Prepare the data to return in JSON format
    data = []
    for discipline in disciplines:
        programmes = discipline.programmes.all()  # Get programmes related to the discipline
        programme_list = [
            {'name': programme.name,'id':programme.id} for programme in programmes
        ]  # Assuming Programme has name and acronym attributes

        data.append({
            'name': discipline.name,
            'acronym':discipline.acronym,
            'id': discipline.id,
            'programmes': programme_list
        })

    return JsonResponse({'disciplines': data}, safe=False)



@api_view(['GET'])
def admin_view_all_batches(request):
    """ views the details of a Course """

    user_details = ExtraInfo.objects.get(user=request.user)
    des = HoldsDesignation.objects.all().filter(user=request.user).first()

    # Check user role
    # if request.session['currentDesignationSelected'] in ["student", "Associate Professor", "Professor", "Assistant Professor"]:
    #     return JsonResponse({'error': 'Access Denied'}, status=403)
    # elif str(request.user) == "acadadmin":
    #     pass
    # elif 'hod' in request.session['currentDesignationSelected'].lower():
    #     return JsonResponse({'error': 'Access Denied'}, status=403)
    
    # Fetch batches
    batches = Batch.objects.all().order_by('year')
    batchfilter = BatchFilter(request.GET, queryset=batches)
    batches = batchfilter.qs

    finished_batches = batches.filter(running_batch=False)
    running_batches = batches.filter(running_batch=True)

    # Serialize the batch data
    batch_data = [
        {
            'batch_id':batch.id,
            'name': batch.name,
            'discipline': str(batch.discipline.acronym),
            'year': batch.year,
            'curriculum': batch.curriculum.name if batch.curriculum else None,
            'id': batch.curriculum.id if batch.curriculum else None,
            'curriculumVersion': batch.curriculum.version if batch.curriculum else None,
            'running_batch': batch.running_batch
        }
        for batch in running_batches
    ]

    finished_batch_data = [
        {
            'batch_id':batch.id,
            'name': batch.name,
            'discipline': str(batch.discipline.acronym),
            'year': batch.year,
            'curriculum': batch.curriculum.name if batch.curriculum else None,
            'id': batch.curriculum.id if batch.curriculum else None,
            'curriculumVersion': batch.curriculum.version if batch.curriculum else None,
            'running_batch': batch.running_batch
        }
        for batch in finished_batches
    ]

    return JsonResponse({
        'batches': batch_data,
        'finished_batches': finished_batch_data,
        'filter': batchfilter.data
    })


# def add_discipline_form(request):

#     user_details = ExtraInfo.objects.get(user = request.user)
#     des = HoldsDesignation.objects.all().filter(user = request.user).first()
#     if request.session['currentDesignationSelected']== "student" or request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" :
#         return HttpResponseRedirect('/programme_curriculum/programmes/')
#     elif str(request.user) == "acadadmin" :
#         pass
#     elif 'hod' in request.session['currentDesignationSelected'].lower():
#         return HttpResponseRedirect('/programme_curriculum/programmes/')
    
#     form = DisciplineForm()
#     submitbutton= request.POST.get('Submit')
#     if submitbutton:
#         if request.method == 'POST':
#             form = DisciplineForm(request.POST)  
#             if form.is_valid():
#                 form.save()
#                 messages.success(request, "Added Discipline successful")
#                 return HttpResponseRedirect('/programme_curriculum/admin_disciplines/')    
#     return render(request, 'programme_curriculum/acad_admin/add_discipline_form.html',{'form':form})

@csrf_exempt  
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_discipline_form(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)  # Parse JSON from the request
            form = DisciplineForm(data)  # Populate the form with the data

            if form.is_valid():
                form.save()
                return JsonResponse({"message": "Discipline added successfully!"}, status=201)
            else:
                return JsonResponse({"errors": form.errors}, status=400)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Invalid HTTP method. Use POST."}, status=405)

@csrf_exempt
@permission_classes([IsAuthenticated])
def edit_discipline_form(request, discipline_id):

    # user_details = ExtraInfo.objects.get(user = request.user)
    # des = HoldsDesignation.objects.all().filter(user = request.user).first()
    # if request.session['currentDesignationSelected']== "student" or request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" :
    #     return HttpResponseRedirect('/programme_curriculum/programmes/')
    # elif str(request.user) == "acadadmin" :
    #     pass
    # elif 'hod' in request.session['currentDesignationSelected'].lower():
    #     return HttpResponseRedirect('/programme_curriculum/programmes/')
    
    discipline = get_object_or_404(Discipline, Q(id=discipline_id))
    if request.method == 'GET':
        # Return initial form data
        form_data = {
            'id': discipline.id,
            'name': discipline.name,
            'acronym': discipline.acronym,
            'programmes': [programme.id for programme in discipline.programmes.all()],
        }
        return JsonResponse(form_data)

    elif request.method == 'POST':
        # Handle form submission
        try:
            data = json.loads(request.body)
            form = DisciplineForm(data, instance=discipline)
            if form.is_valid():
                form.save()
                return JsonResponse({
                    "message": f"Updated {discipline.name} successfully."
                }, status=201)
            else:
                # Return form errors
                return JsonResponse({
                    'status': 'error',
                    'message': form.errors,
                }, status=400)
        
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data.',
            }, status=400)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method.',
    }, status=405)


# def add_programme_form(request):

#     user_details = ExtraInfo.objects.get(user = request.user)
#     des = HoldsDesignation.objects.all().filter(user = request.user).first()
#     if request.session['currentDesignationSelected']== "student" or request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" :
#         return HttpResponseRedirect('/programme_curriculum/programmes/')
#     elif str(request.user) == "acadadmin" :
#         pass
#     elif 'hod' in request.session['currentDesignationSelected'].lower():
#         return HttpResponseRedirect('/programme_curriculum/programmes/')
    
#     form = ProgrammeForm()
#     submitbutton= request.POST.get('Submit')
#     if submitbutton:
#         if request.method == 'POST':
#             form = ProgrammeForm(request.POST)  

#             if form.is_valid():
#                 form.save()
#                 programme = Programme.objects.last()
#                 messages.success(request, "Added successful")
#                 return HttpResponseRedirect('/programme_curriculum/admin_curriculums/' + str(programme.id) + '/')  
#     return render(request,'programme_curriculum/acad_admin/add_programme_form.html',{'form':form, 'submitbutton': submitbutton})

# @permission_classes([IsAuthenticated])
# @api_view(['POST'])
@csrf_exempt
def add_programme_form(request):
    if request.method == 'POST':
        # print(request.body)
        data = json.loads(request.body)
        print(data)
        form_data={
            'name': data.get('name'),
            'category': data.get('category'),
            'programme_begin_year': data.get('programme_begin_year'),
            # 'discipline': data.get('discipline')
        }
        form = ProgrammeForm(form_data)

        if form.is_valid():
            form.save()
            programme = Programme.objects.last()
            return JsonResponse({
                "message": "Programme added successfully",
                "programme_id": programme.id,
            })
        else:
            return JsonResponse({
                "error": "Invalid form data",
                "details": form.errors,
            }, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)


@csrf_exempt
@permission_classes([IsAuthenticated])
def edit_programme_form(request, programme_id):

    # user_details = ExtraInfo.objects.get(user = request.user)
    # des = HoldsDesignation.objects.all().filter(user = request.user).first()
    # if request.session['currentDesignationSelected']== "student" or request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" :
    #     return HttpResponseRedirect('/programme_curriculum/programmes/')
    # elif str(request.user) == "acadadmin" :
    #     pass
    # elif 'hod' in request.session['currentDesignationSelected'].lower():
    #     return HttpResponseRedirect('/programme_curriculum/programmes/')
    
    programme = get_object_or_404(Programme, Q(id=programme_id))
    if request.method == 'GET':
        # Return initial form data
        form_data = {
            'id': programme.id,
            'name': programme.name,
            'category': programme.category,
            'programme_begin_year': programme.begin_year,
        }
        return JsonResponse(form_data)

    elif request.method == 'POST':
        # Handle form submission
        try:
            data = json.loads(request.body)
            form = ProgrammeForm(data, instance=programme)
            
            if form.is_valid():
                form.save()
                return JsonResponse({
                    "message": "Updated successfully."
                }, status=201)
            else:
                # Return form errors
                return JsonResponse({
                    'status': 'error',
                    'message': form.errors,
                }, status=401)
        
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data.',
            }, status=400)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method.',
    }, status=405)


@permission_classes([IsAuthenticated])
@api_view(['POST'])
def add_curriculum_form(request):
    """
    This function is used to add Curriculum and Semester into Curriculum and Semester table.
        
    @variables:
        no_of_semester - Get number of Semesters from form.
        NewSemester - For initializing a new semester.
    """
    if request.method == 'POST':
        try:
            # Parse the incoming JSON data
            data = json.loads(request.body)
            curriculum_name = data.get('curriculum_name')
            programme_id = data.get('programme')
            working_curriculum = data.get('working_curriculum', False)
            version_no = data.get('version_no', 1.0)
            num_semesters = data.get('no_of_semester', 1)
            num_credits = data.get('num_credits', 0)

            # Validate that the programme exists
            try:
                programme = Programme.objects.get(id=programme_id)
            except Programme.DoesNotExist:
                return JsonResponse({'error': 'Invalid programme ID'}, status=400)

            # Mark the previous versions as non-latest for this curriculum name
            Curriculum.objects.filter(name=curriculum_name, programme=programme).update(latest_version=False)

            # Create the new Curriculum instance
            curriculum = Curriculum(
                name=curriculum_name,
                programme=programme,
                working_curriculum=working_curriculum,
                version=version_no,
                no_of_semester=num_semesters,
                min_credit=num_credits,
                latest_version=True
            )
            curriculum.save()

            # Add Semesters for the Curriculum
            semesters = [
                Semester(curriculum=curriculum, semester_no=semester_no)
                for semester_no in range(1, num_semesters + 1)
            ]
            Semester.objects.bulk_create(semesters)

            return JsonResponse({'message': 'Curriculum added successfully!'}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method.'}, status=405)


@permission_classes([IsAuthenticated])
@api_view(['PUT'])
def edit_curriculum_form(request, curriculum_id):
    """
    Handle updating Curriculum and Semesters through an API endpoint.
    """
    if request.method == 'PUT':
        try:
            # Parse the incoming JSON data
            data = json.loads(request.body)
            curriculum_name = data.get('curriculum_name')
            programme_id = data.get('programme')
            working_curriculum = data.get('working_curriculum', False)
            version_no = data.get('version_no', 1.0)
            num_semesters = data.get('no_of_semester', 1)
            num_credits = data.get('num_credits', 0)

            # Fetch the existing curriculum
            curriculum = get_object_or_404(Curriculum, id=curriculum_id)

            # Validate that the programme exists
            try:
                programme = Programme.objects.get(id=programme_id)
            except Programme.DoesNotExist:
                return JsonResponse({'error': 'Invalid programme ID'}, status=status.HTTP_400_BAD_REQUEST)

            # Update the curriculum fields
            curriculum.name = curriculum_name
            curriculum.programme = programme
            curriculum.working_curriculum = working_curriculum
            curriculum.version = version_no
            curriculum.no_of_semester = num_semesters
            curriculum.min_credit = num_credits
            curriculum.save()

            # Handle semester updates
            old_no_of_semesters = Semester.objects.filter(curriculum=curriculum).count()
            new_no_of_semesters = num_semesters

            if old_no_of_semesters != new_no_of_semesters:
                if old_no_of_semesters > new_no_of_semesters:
                    # Remove extra semesters
                    for semester_no in range(new_no_of_semesters + 1, old_no_of_semesters + 1):
                        try:
                            Semester.objects.filter(curriculum=curriculum, semester_no=semester_no).delete()
                        except Exception as e:
                            return JsonResponse({'error': f'Failed to remove old semester: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                elif old_no_of_semesters < new_no_of_semesters:
                    # Add new semesters
                    semesters = [
                        Semester(curriculum=curriculum, semester_no=semester_no)
                        for semester_no in range(old_no_of_semesters + 1, new_no_of_semesters + 1)
                    ]
                    Semester.objects.bulk_create(semesters)

            return JsonResponse({'message': 'Curriculum updated successfully!'}, status=status.HTTP_200_OK)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return JsonResponse({'error': 'Invalid request method.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
@csrf_exempt
@permission_classes([IsAuthenticated])
def add_course_form(request):

    # user_details = ExtraInfo.objects.get(user = request.user)
    # des = HoldsDesignation.objects.all().filter(user = request.user).first()
    # if request.session['currentDesignationSelected']== "student" or request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" :
    #     return HttpResponseRedirect('/programme_curriculum/programmes/')
    # elif str(request.user) == "acadadmin" :
    #     pass
    # elif 'hod' in request.session['currentDesignationSelected'].lower():
    #     return HttpResponseRedirect('/programme_curriculum/programmes/')
    
    try:
        if request.method == 'POST':
            data = json.loads(request.body.decode('utf-8'))
            form = CourseForm(data)
            if form.is_valid():
                new_course = form.save(commit=False)
                # new_course.version = 1.0
                new_course.save()
                course = Course.objects.last()
                return JsonResponse({'success': True, 'message': 'Course added successfully', 'course_id': course.id}, status=201)
            else:
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)

        return JsonResponse({'error': 'Invalid request method. Use POST.'}, status=405)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
  

@csrf_exempt
@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def update_course_form(request, course_id):
    """
    Handle getting and updating Course through an API endpoint.
    """
    try:
        course = get_object_or_404(Course, id=course_id)
        
        if request.method == 'GET':
            # Return course data for editing
            data = {
                'name': course.name,
                'code': course.code,
                'credit': course.credit,
                'version': course.version,
                'lecture_hours': course.lecture_hours,
                'tutorial_hours': course.tutorial_hours,
                'pratical_hours': course.pratical_hours,
                'discussion_hours': course.discussion_hours,
                'project_hours': course.project_hours,
                'disciplines': [d.id for d in course.disciplines.all()],
                'pre_requisits': course.pre_requisits,
                'pre_requisit_courses': [c.id for c in course.pre_requisit_courses.all()],
                'syllabus': course.syllabus,
                'ref_books': course.ref_books,
                'percent_quiz_1': course.percent_quiz_1,
                'percent_midsem': course.percent_midsem,
                'percent_quiz_2': course.percent_quiz_2,
                'percent_endsem': course.percent_endsem,
                'percent_project': course.percent_project,
                'percent_lab_evaluation': course.percent_lab_evaluation,
                'percent_course_attendance': course.percent_course_attendance,
            }
            return Response(data, status=status.HTTP_200_OK)
        
        elif request.method == 'PUT':
            # Handle course update
            print("gaurav")
            data = json.loads(request.body)
            print(data)
            previous_version = Course.objects.filter(code=course.code).order_by('version').last()
            print(previous_version)
            # Validate version
            new_version = data.get('version', course.version)
            if float(new_version) <= float(previous_version.version):
                return Response(
                    {'error': f'Version must be greater than current version ({previous_version.version})'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update basic course fields
            update_fields = [
                'code', 'name', 'credit', 'lecture_hours', 'tutorial_hours',
                'pratical_hours', 'discussion_hours', 'project_hours',
                'pre_requisits', 'syllabus', 'percent_quiz_1', 'percent_midsem',
                'percent_quiz_2', 'percent_endsem', 'percent_project',
                'percent_lab_evaluation', 'percent_course_attendance', 'ref_books'
            ]
            
            for field in update_fields:
                if field in data:
                    setattr(course, field, data[field])
            
            # Set version and latest version flags
            course.version = new_version
            previous_version.latest_version = False
            previous_version.save()
            course.latest_version = True
            
            course.save()
            
            # Update many-to-many relationships
            if 'disciplines' in data:
                discipline_ids = data['disciplines']
                disciplines = Discipline.objects.filter(id__in=discipline_ids)
                course.disciplines.set(disciplines)
            
            if 'pre_requisit_courses' in data:
                prereq_course_ids = data['pre_requisit_courses']
                prereq_courses = Course.objects.filter(id__in=prereq_course_ids)
                course.pre_requisit_courses.set(prereq_courses)
            
            return Response(
                {
                    'message': 'Course updated successfully!',
                    'course_id': course.id,
                    'code': course.code,
                    'name': course.name
                },
                status=status.HTTP_200_OK
            )
    
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

@permission_classes([IsAuthenticated])
@api_view(['POST'])
def add_courseslot_form(request):
    try:
        # Check permissions
        # user_details = ExtraInfo.objects.get(user=request.user)
        # des = HoldsDesignation.objects.filter(user=request.user).first()
        
        # if request.session['currentDesignationSelected'] not in ["acadadmin"]:
        #     return JsonResponse({
        #         'status': 'error',
        #         'message': 'Permission denied'
        #     }, status=403)

        # Parse the JSON data
        data = json.loads(request.body)
        
        # Create the course slot
        course_slot = CourseSlot.objects.create(
            semester_id=data['semester'],
            name=data['name'],
            type=data['type'],
            course_slot_info=data.get('course_slot_info', ''),
            duration=data.get('duration', 1),
            min_registration_limit=data.get('min_registration_limit', 0),
            max_registration_limit=data.get('max_registration_limit', 1000)
        )
        
        # Add courses if provided
        if 'courses' in data and data['courses']:
            course_slot.courses.set(data['courses'])

        return JsonResponse({
            'status': 'success',
            'message': 'Course slot created successfully',
            'id': course_slot.id
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@csrf_exempt  # Use this decorator if you're not using CSRF tokens in your API calls
@permission_classes([IsAuthenticated])
def edit_courseslot_form(request, courseslot_id):
    # print(courseslot_id)
    
    courseslot = get_object_or_404(CourseSlot, Q(id=courseslot_id))
    curriculum_id = courseslot.semester.curriculum.id
    # print("gaurav")
    # print("gaurav")
    # print("gaurav")
    # print("gaurav")
    # print("gaurav")
    # print("gaurav")
    if request.method == 'GET':
        # Prepare the course slot data for the frontend
        courseslot_data = {
            'id': courseslot.id,
            'semester': courseslot.semester.id,
            'name': courseslot.name,
            'type': courseslot.type,
            'course_slot_info': courseslot.course_slot_info,
            'courses': [course.id for course in courseslot.courses.all()],
            'duration': courseslot.duration,
            'min_registration_limit': courseslot.min_registration_limit,
            'max_registration_limit': courseslot.max_registration_limit,
            'curriculum_id': curriculum_id,
        }
        print(courseslot_data)
        return JsonResponse({'status': 'success', 'courseslot': courseslot_data})

    elif request.method == 'PUT':
        # Handle updating the course slot
        try:
            data = json.loads(request.body)  # Parse JSON data from the request body
            form = CourseSlotForm(data, instance=courseslot)
            if form.is_valid():
                form.save()
                return JsonResponse({'status': 'success', 'message': 'Course slot updated successfully', 'redirect_url': f'/programme_curriculum/admin_curriculum_semesters/{curriculum_id}/'})
            else:
                return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
    


@csrf_exempt
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_courseslot(request, courseslot_id):
    print(request.session.keys())
    try:
        # Check if the user has the required session key
        # if 'currentDesignationSelected' not in request.session:
        #     return JsonResponse({'error': 'User role not defined in session'}, status=403)
        
        # Check user permissions
        user_details = ExtraInfo.objects.get(user=request.user)
        des = HoldsDesignation.objects.all().filter(user=request.user).first()
        
        # Restrict access based on user role
        # print(request.session.keys())
        # print(request.session['currentDesignationSelected'])
        # current_designation = request.session['currentDesignationSelected']
        # if current_designation == "student" or \
        #    current_designation == "Associate Professor" or \
        #    current_designation == "Professor" or \
        #    current_designation == "Assistant Professor":
        #     return JsonResponse({'error': 'Permission denied'}, status=403)
        # elif str(request.user) == "acadadmin":
        #     pass  # Allow access for academic admin
        # elif 'hod' in current_designation.lower():
        #     return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Fetch the course slot
        courseslot = get_object_or_404(CourseSlot, id=courseslot_id)
        
        # Delete the course slot
        courseslotname = courseslot.name
        curriculum_id = courseslot.semester.curriculum.id
        courseslot.delete()
        
        return JsonResponse({'message': f"Deleted {courseslotname} successfully"}, status=200)
    except Exception as e:
        # Return a generic error message without logging
        return JsonResponse({'error': 'Internal server error'}, status=500)


@permission_classes([IsAuthenticated])
@api_view(['POST'])
@csrf_exempt  # Use this decorator if CSRF is not handled elsewhere
def add_batch_form(request):
    """
    Handle adding a new Batch through an API endpoint.
    """
    if request.method == 'POST':
        data = request.data

        # Map frontend fields to the correct model fields
        batch_data = {
            "name": data.get("batch_name"),  
            "discipline": data.get("discipline"),
            "year": data.get("batchYear"),
            "curriculum": data.get("disciplineBatch"),  # Assuming curriculum is disciplineBatch
            "running_batch": data.get("runningBatch"),  # Assuming running_batch is a field in the model
        }
        # data = json.loads(request.body)
        serializer = BatchSerializer(data=batch_data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Added Batch successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    return Response({"error": "Invalid request method"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


@csrf_exempt  # Use this decorator if you're not using CSRF tokens in your API calls
@permission_classes([IsAuthenticated])
def edit_batch_form(request, batch_id):

    # user_details = ExtraInfo.objects.get(user = request.user)
    # des = HoldsDesignation.objects.all().filter(user = request.user).first()
    # if request.session['currentDesignationSelected']== "student" or request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" :
    #     return HttpResponseRedirect('/programme_curriculum/programmes/')
    # elif str(request.user) == "acadadmin" :
    #     pass
    # elif 'hod' in request.session['currentDesignationSelected'].lower():
    #     return HttpResponseRedirect('/programme_curriculum/programmes/')
    print('gaurav',batch_id)
    # Fetch the course slot
    batch = get_object_or_404(Batch, Q(id=batch_id))
    if request.method == 'GET':
        # Prepare the course slot data for the frontend
        batch_data = {
            'id': batch.id,
            'discipline': batch.discipline_id,
            'name': batch.name,
            'year': batch.year,
            'curriculum_id': batch.curriculum_id,
            'running_batch':batch.running_batch,
        }

        curricula_data = None

        if batch.curriculum_id is not None:
            # Fetch the curriculum object
            curriculum = get_object_or_404(Curriculum, Q(id=batch.curriculum_id))
            
            # Serialize the curriculum data
            curricula_data = [{
                'id': curriculum.id,
                'name': curriculum.name,
                'version': curriculum.version,
                # Uncomment these if you want to include discipline and programme details
                # 'discipline': curriculum.discipline.name,
                # 'programme': curriculum.programme.name,
            }]
        
        print(batch_data)
        print(curricula_data)
        return JsonResponse({'status': 'success', 'batch': batch_data,'curriculum':curricula_data if curricula_data is not None else None})
    
    elif request.method == 'PUT':
        print("put is used")
        try:
            # Fetch the existing batch instance
            try:
                batch = Batch.objects.get(id=batch_id)
            except Batch.DoesNotExist:
                return JsonResponse({'error': 'Batch not found'}, status=status.HTTP_404_NOT_FOUND)

            # Parse the incoming JSON data
            data = json.loads(request.body)

            # Update batch fields
            batch.name = data.get('batch_name', batch.name)  # Use existing value if not provided
            batch.year = data.get('batchYear', batch.year)  # Use existing value if not provided
            batch.running_batch = data.get('runningBatch', batch.running_batch)  # Use existing value if not provided

            # Update discipline (if provided)
            discipline_id = data.get('discipline')
            if discipline_id:
                try:
                    discipline = Discipline.objects.get(id=discipline_id)
                    batch.discipline = discipline
                except Discipline.DoesNotExist:
                    return JsonResponse({'error': 'Invalid discipline ID'}, status=status.HTTP_400_BAD_REQUEST)

            # Update curriculum (if provided)
            curriculum_id = data.get('disciplineBatch')
            if curriculum_id:
                try:
                    curriculum = Curriculum.objects.get(id=curriculum_id)
                    batch.curriculum = curriculum
                except Curriculum.DoesNotExist:
                    return JsonResponse({'error': 'Invalid curriculum ID'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                batch.curriculum = None  # Set curriculum to None if not provided

            # Save the updated batch
            batch.save()

            return JsonResponse({'status': status.HTTP_200_OK, 'message': 'Batch updated successfully'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return JsonResponse({'error': 'Invalid request method'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


def instigate_semester(request, semester_id):
    """
    This function is used to add the semester information.
        
    @variables:
        no_of_semester - Get number of Semesters from form.
        OldSemester - For Removing dropped Semester.
        NewSemester - For initializing a new semester.
    """    
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if request.session['currentDesignationSelected']== "student" or request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    
    
    semester = get_object_or_404(Semester, Q(id=semester_id))
    sdate = semester.start_semester
    edate = semester.end_semester
    isem = semester.instigate_semester
    info = semester.semester_info
    form = SemesterForm(initial={'start_semester': sdate ,'end_semester': edate ,'instigate_semester': isem , 'semester_info': info, })
    curriculum_id = semester.curriculum.id
    submitbutton = request.POST.get('Submit')
    if submitbutton:
        if request.method == 'POST':
            form = SemesterForm(request.POST or None)
            if form.is_valid():
                semester.start_semester = form.cleaned_data['start_semester']
                semester.end_semester = form.cleaned_data['end_semester']
                semester.instigate_semester = form.cleaned_data['instigate_semester']
                semester.semester_info = form.cleaned_data['semester_info']
                semester.save()
                messages.success(request, "Instigated "+ str(semester) +" successful")
                return HttpResponseRedirect('/programme_curriculum/admin_curriculum_semesters/' + str(semester.curriculum.id) + '/')

    return render(request,'programme_curriculum/acad_admin/instigate_semester_form.html',{'semester':semester, 'form':form, 'submitbutton':submitbutton, 'curriculum_id':curriculum_id})

@csrf_exempt  # Use this decorator if you're not using CSRF tokens in your API calls
@permission_classes([IsAuthenticated])
def replicate_curriculum(request, curriculum_id):
    """
    This function is used to replicate the previous curriculum into a new curriculum.
    It accepts data from a React frontend via a POST request.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST requests are allowed'}, status=405)

    try:
        # Parse JSON data from the request body
        data = json.loads(request.body)
        
        # Extract data from the request
        # curriculum_id = data.get('curriculum_id')
        curriculum_name = data.get('curriculum_name')
        programme_id = data.get('programme')
        working_curriculum = data.get('working_curriculum')
        version_no = data.get('version_no')
        num_semesters = data.get('num_semesters')
        num_credits = data.get('num_credits')

        # Fetch the old curriculum
        old_curriculum = get_object_or_404(Curriculum, Q(id=curriculum_id))

        # Create a new curriculum
        #  curriculum = Curriculum(
        #         name=curriculum_name,
        #         programme=programme,
        #         working_curriculum=working_curriculum,
        #         version=version_no,
        #         no_of_semester=num_semesters,
        #         min_credit=num_credits,
        #         latest_version=True
        #     )
        try:
            programme = Programme.objects.get(id=programme_id)
        except Programme.DoesNotExist:
            return JsonResponse({'error': 'Invalid programme ID'}, status=400)
        

        new_curriculum = Curriculum(
            programme=programme,
            name=curriculum_name,
            version=version_no,
            working_curriculum=working_curriculum,
            no_of_semester=num_semesters,
            min_credit=num_credits,
            latest_version=True
        )
        new_curriculum.save()

        # Replicate semesters and course slots
        old_semesters = old_curriculum.semesters.all()
        for semester_no in range(1, num_semesters + 1):
            new_semester = Semester(curriculum=new_curriculum, semester_no=semester_no)
            new_semester.save()

            for old_sem in old_semesters:
                if old_sem.semester_no == semester_no:
                    for slot in old_sem.courseslots.all():
                        courses = slot.courses.all()
                        slot.pk = None
                        slot.semester = new_semester
                        slot.save(force_insert=True)
                        slot.courses.set(courses)

        return JsonResponse({'status': 'success', 'message': 'Curriculum replicated successfully', 'curriculum_id': new_curriculum.id})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
#new

@permission_classes([IsAuthenticated])
@csrf_exempt  # Use this decorator if you're not using CSRF tokens in your API calls
def view_course_proposal_forms(request):
    data = {}
    username = request.GET.get('username')  # Get username from query parameters
    des = request.GET.get('des')  # Get designation from query parameters

    if not username or not des:
        return JsonResponse({'error': 'Username and designation are required'}, status=400)

    # Check the user's designation
    if des not in ["Associate Professor", "Professor", "Assistant Professor"]:
        if des == "student":
            return JsonResponse({'redirect': '/programme_curriculum/programmes/'}, status=302)
        elif des == "acadadmin":
            return JsonResponse({'redirect': '/programme_curriculum/admin_programmes/'}, status=302)
        else:
            data['error'] = 'Files Cannot be sent with current Designation. Switch to "Professor or Assistant Professor or Associate Professor"'
            return JsonResponse(data, status=403)

    # Fetch course proposals
    courseProposal = NewProposalFile.objects.filter(uploader=username, designation=des, is_update=False)
    updatecourseProposal = NewProposalFile.objects.filter(uploader=username, designation=des, is_update=True)

    # Serialize the querysets to JSON
    courseProposal_data = json.loads(serialize('json', courseProposal))
    updatecourseProposal_data = json.loads(serialize('json', updatecourseProposal))

    # Prepare the response data
    response_data = {
        'courseProposals': courseProposal_data,
        'updateProposals': updatecourseProposal_data,
        'message': 'Data fetched successfully',
    }

    return JsonResponse(response_data, status=200)

@login_required(login_url='/accounts/login')
def faculty_view_all_courses(request):
    """ views all the course slots of a specfic semester """

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if request.session['currentDesignationSelected'] == "student" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif request.session['currentDesignationSelected'] == "acadadmin" :
        return HttpResponseRedirect('/programme_curriculum/admin_programmes')
    elif request.session['currentDesignationSelected'] == "Associate Professor" or request.session['currentDesignationSelected'] == "Professor" or request.session['currentDesignationSelected'] == "Assistant Professor":
        pass
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        pass

    courses = Course.objects.all()
    notifs = request.user.notifications.all()
    coursefilter = CourseFilter(request.GET, queryset=courses)

    courses = coursefilter.qs

    return render(request, 'programme_curriculum/faculty/faculty_view_all_courses.html', {'courses': courses, 'coursefilter': coursefilter,'notifications': notifs,})


def faculty_view_a_course(request, course_id):
    """ views the details of a Course """

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if request.session['currentDesignationSelected'] == "student" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif request.session['currentDesignationSelected'] == "acadadmin" :
        return HttpResponseRedirect('/programme_curriculum/admin_programmes')
    elif request.session['currentDesignationSelected'] == "Associate Professor" or request.session['currentDesignationSelected'] == "Professor" or request.session['currentDesignationSelected'] == "Assistant Professor" :
        pass
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        pass
    course = get_object_or_404(Course, Q(id=course_id))
    notifs = request.user.notifications.all()
    return render(request, 'programme_curriculum/faculty/faculty_view_a_course.html', {'course': course,'notifications': notifs,})

@csrf_exempt
@permission_classes([IsAuthenticated])
def view_a_course_proposal_form(request,CourseProposal_id):
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()

    if request.session['currentDesignationSelected'] == "Associate Professor" or request.session['currentDesignationSelected'] == "Professor" or request.session['currentDesignationSelected'] == "Assistant Professor":
        pass
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        pass
    elif request.session['currentDesignationSelected'] == "acadadmin" :
        return HttpResponseRedirect('/programme_curriculum/admin_programmes')
    else:
        return HttpResponseRedirect('/programme_curriculum/programmes')

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    proposalform = get_object_or_404(NewProposalFile, Q(id=CourseProposal_id))
    notifs = request.user.notifications.all()
    return render(request, 'programme_curriculum/faculty/view_a_course_proposal.html', {'proposal': proposalform,'notifications': notifs,})


@permission_classes([IsAuthenticated])
@csrf_exempt  # Only for development, remove in production with proper CSRF handling
def new_course_proposal_file(request):
    # des = HoldsDesignation.objects.all().filter(user = request.user).first()
    # if request.session['currentDesignationSelected'] == "Associate Professor" or request.session['currentDesignationSelected'] == "Professor" or request.session['currentDesignationSelected'] == "Assistant Professor":
    #     pass
    # elif request.session['currentDesignationSelected'] == "acadadmin" :
    #     return HttpResponseRedirect('/programme_curriculum/admin_programmes')
    # else:
    #     return HttpResponseRedirect('/programme_curriculum/programmes')
    print("new course proposal file")
    
    if request.method == 'POST':
        try:
            # Parse JSON data from request body
            data = json.loads(request.body)
            
            # Create form data dictionary mapping frontend fields to model fields
            form_data = {
                'name': data.get('name'),
                'code': data.get('code'),
                'credit': data.get('credit'),
                'version': data.get('version'),
                'lecture_hours': data.get('lecture_hours'),
                'tutorial_hours': data.get('tutorial_hours'),
                'pratical_hours': data.get('pratical_hours'),
                'project_hours': data.get('project_hours'),
                'discussion_hours': data.get('discussion_hours'),
                'syllabus': data.get('syllabus'),
                'percent_quiz_1': data.get('percent_quiz_1'),
                'percent_midsem': data.get('percent_midsem'),
                'percent_quiz_2': data.get('percent_quiz_2'),
                'percent_endsem': data.get('percent_endsem'),
                'percent_project': data.get('percent_project'),
                'percent_lab_evaluation': data.get('percent_lab_evaluation'),
                'percent_course_attendance': data.get('percent_course_attendance'),
                'ref_books': data.get('ref_books'),
                'disciplines': data.get('disciplines'),
                # 'pre_requisit_courses': data.get('pre_requisit_courses'),
                'pre_requisits': data.get('pre_requisits'),
                'max_seats': data.get('maxSeats'),
                'subject': data.get('Title'),
                'description': data.get('Description'),
                'uploader': data.get('uploader'),
                'designation': data.get('Designation'),
                'is_update': data.get('isUpdate', False),
                # 'designation': request.session.get('currentDesignationSelected', ''),
            }
            prerequisite_course_ids = data.get('pre_requisit_courses', [])
            valid_courses = Course.objects.filter(id__in=prerequisite_course_ids)
            if len(valid_courses) != len(prerequisite_course_ids):
                invalid_ids = set(prerequisite_course_ids) - set(c.id for c in valid_courses)
                return JsonResponse({
                    'status': 'error',
                    'message': f'Invalid prerequisite course IDs: {invalid_ids}'
                }, status=400)
            # Create and validate form
            form = NewCourseProposalFile(form_data)
            
            if form.is_valid():
                new_course = form.save(commit=False)
                new_course.is_read = False
                new_course.save()

                if prerequisite_course_ids:
                    new_course.pre_requisit_courses.add(*valid_courses)
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Course added successfully',
                    'course_id': new_course.id,
                    'prerequisite_courses_added': len(prerequisite_course_ids)
                }, status=201)
            else:
                print(form.errors)
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid form data',
                    'errors': form.errors
                }, status=400)
                
        except json.JSONDecodeError:
            print("error")

            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Only POST requests are allowed'
    }, status=405)

@permission_classes([IsAuthenticated])
@csrf_exempt  # Remove in production and use proper CSRF handling
def filetracking(request, proposal_id):
    if request.method == 'POST':
        try:
            # Parse JSON data from request body
            data = json.loads(request.body)
            
            # Get the file being tracked
            file = get_object_or_404(NewProposalFile, id=proposal_id)

            print(file)
            # Get user objects from IDs
            try:
                receiver_id=data.get('receiverId')
                receiver_des=data.get('receiverDesignation')
                receiver_user = User.objects.get(username=data.get('receiverId'))
                uploader_user=User.objects.get(username=data.get('uploader'))

                # print("uploader_user",uploader_user)
                # print('type',type(uploader_user))

                receiver_designation = Designation.objects.get(name=data.get('receiverDesignation'))

                # print("receiver_user",receiver_user)
                # print('type',type(receiver_user))

                discipline = Discipline.objects.get(id=data.get('discipline'))  # Assuming single discipline
                print(discipline)
            except (User.DoesNotExist, Designation.DoesNotExist, Discipline.DoesNotExist) as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Invalid reference: {str(e)}'
                }, status=400)
            
            # Create tracking record
            tracking_data = {
                'file_id': proposal_id,
                'current_id': data.get('uploader'),
                'current_design': data.get('designation'),
                'receive_id': receiver_user.id,
                'receive_design': receiver_designation.id,
                'disciplines': discipline.id,
                'remarks': data.get('remarks', ''),
                # 'is_submitted': True
            }
            print(tracking_data)
            form = CourseProposalTrackingFile(tracking_data)
            
            if form.is_valid():
                try:
                    tracking = form.save(commit=False)
                    tracking.save()
                    
                    # Prepare notification data
                    file_data = f"{file.name} {file.code}"
                    print('file data',file_data)
                    notification_data = (
                        f"Received as {receiver_id} - {receiver_des} "
                        f"Course Proposal Form '{file_data}' "
                        f"By {data.get('uploader')} - {data.get('designation')}"
                    )
                    print('notification data',notification_data)    
                    prog_and_curr_notif(uploader_user,receiver_user,notification_data)
                    print('success')
                    
                    return JsonResponse({
                        'status': 'success',
                        'message': 'File tracking submitted successfully',
                        'notification': notification_data
                    }, status=201)
                    
                except IntegrityError:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'This file tracking record already exists'
                    }, status=400)
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid form data',
                    'errors': form.errors
                }, status=400)
            print("till here is okay")       
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Only POST requests are allowed'
    }, status=405)


@permission_classes([IsAuthenticated])
@csrf_exempt
def inward_files(request):

    try:

        username = request.GET.get('username')
        designation_name = request.GET.get('des')
        print("username ",username)
        print("designation ",designation_name)
        if not username or not designation_name:
            return JsonResponse({
                'status': 'error',
                'message': 'Username and designation are required'
            }, status=400)
        
        # Get user and designation objects
        user = User.objects.get(username=username)
        print('user',user)
        designation = Designation.objects.get(name=designation_name)
        print('des',designation)
        # Get inward files
        course_proposals = Proposal_Tracking.objects.filter(
            receive_design=designation.id,
            receive_id=user.id
        ).values(
            'id',
            'file_id',
            'current_id',
            'current_design',
            'receive_id__username',
            'receive_design__name',
            'remarks',
            'receive_date',
            'forward_date',
            'sender_archive',
            'receiver_archive',
            'disciplines',
            'is_rejected'
        )
        
        return JsonResponse({
            'status': 'success',
            'courseProposals': list(course_proposals),
            'designation': designation_name
        })
        
    except User.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'User not found'
        }, status=404)
    except Designation.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Designation not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@permission_classes([IsAuthenticated])
@csrf_exempt
def outward_files(request):
    try:
        # Get user details
        # user_details = ExtraInfo.objects.get(user=request.user)
        
        # Get current designation
        current_designation = request.GET.get('des', '')
        current_username = request.GET.get('username', '') 
       
        if not current_designation:
            return JsonResponse({
                'status': 'error',
                'message': 'Designation is required'
            }, status=400)

        # Check permissions based on designation
        if current_designation.lower() == "dean academic":
            return JsonResponse({
                'status': 'success',
                'message': f'As a "{current_designation}" you cannot have any outgoing files',
                'courseProposals': []
            })
        
        try:
            designation = Designation.objects.get(name=current_designation)
        except Designation.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid designation'
            }, status=400)

        # Get outward files
        course_proposals = Proposal_Tracking.objects.filter(
            current_design=current_designation,
            current_id=current_username # Changed from des.user to username
        ).values(
            'id',
            'file_id',
            'current_id',
            'current_design',
            'receive_id__username',
            'receive_design__name',
            'remarks',
            'receive_date',
            'forward_date',
            'sender_archive',
            'is_rejected'
        )

        return JsonResponse({
            'status': 'success',
            'courseProposals': list(course_proposals),
            'designation': current_designation
        })

    except ExtraInfo.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'User details not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
    
@csrf_exempt
def update_course_proposal_file(request, course_id):
    # Fetch user designation (will break if request.user is Anonymous)
    # try:
    #     des = HoldsDesignation.objects.filter(user=request.user).first()
    # except Exception:
    #     return JsonResponse({'error': 'Could not determine designation. Are you logged in?'}, status=400)

    # current_designation = request.session.get('currentDesignationSelected', None)
    # if current_designation in ["Associate Professor", "Professor", "Assistant Professor"]:
    #     pass
    # elif current_designation == "acadadmin":
    #     return HttpResponseRedirect('/programme_curriculum/admin_programmes')
    # else:
    #     return HttpResponseRedirect('/programme_curriculum/programmes/')

    uploader = getattr(request.user, 'extrainfo', None)
    # design = current_designation
    course = get_object_or_404(Course, Q(id=course_id))
    file_data = course.code + ' - ' + course.name

    if request.method == "PUT":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        form = NewCourseProposalFile(data, instance=course)
        if form.is_valid():
            previous = Course.objects.filter(code=course.code).order_by('version').last()
            course.version = previous.version

            new_course = form.save(commit=False)
            new_course.is_read = False
            new_course.is_update = True

            add = True
            ver = 0

            old_course = Course.objects.filter(
                code=new_course.code,
                name=new_course.name,
                credit=new_course.credit,
                lecture_hours=new_course.lecture_hours,
                tutorial_hours=new_course.tutorial_hours,
                pratical_hours=new_course.pratical_hours,
                discussion_hours=new_course.discussion_hours,
                project_hours=new_course.project_hours,
                pre_requisits=new_course.pre_requisits,
                syllabus=new_course.syllabus,
                percent_quiz_1=new_course.percent_quiz_1,
                percent_midsem=new_course.percent_midsem,
                percent_quiz_2=new_course.percent_quiz_2,
                percent_endsem=new_course.percent_endsem,
                percent_project=new_course.percent_project,
                percent_lab_evaluation=new_course.percent_lab_evaluation,
                percent_course_attendance=new_course.percent_course_attendance,
                ref_books=new_course.ref_books
            )

            if old_course.exists():
                for i in old_course:
                    if set(form.cleaned_data['pre_requisit_courses']) != set(i.pre_requisit_courses.all()):
                        add = True
                    else:
                        add = False
                        ver = i.version
                        break

            if add:
                new_course.save()
                new_course.pre_requisit_courses.set(form.cleaned_data['pre_requisit_courses'])
                return JsonResponse({"message": "Course updated successfully", "course_id": new_course.id}, status=200)
            else:
                return JsonResponse({"error": f"A Course with the same values already exists at Version Number {ver}"}, status=400)
        else:
            return JsonResponse({"error": form.errors}, status=400)

    # For GET (rendering form in browser), fallback
    form = NewCourseProposalFile(initial={'uploader': des.user, 'designation': design}, instance=course)
    return render(request, 'programme_curriculum/faculty/course_proposal_form.html', {
        'form': form,
        'submitbutton': None,
        'file_info': file_data,
    })



# def forward_course_forms(request,ProposalId):
#     de= ProposalId
#     des = HoldsDesignation.objects.all().filter(user = request.user).first()

#     courseform = Proposal_Tracking.objects.all().filter(id=ProposalId)
    
#     uploader = request.user.extrainfo
#     design=request.session['currentDesignationSelected']
#     file = get_object_or_404(Proposal_Tracking, Q(id=ProposalId))
#     file_id = int(file.file_id)
#     file2 = get_object_or_404(NewProposalFile, Q(id=file_id))
#     file_data=file2.code + ' ' + file2.name
#     Proposal_D = file.id
            
#     if request.session['currentDesignationSelected'] == "Dean Academic" :
#         file = get_object_or_404(Proposal_Tracking, Q(id=ProposalId))
#         file_id = int(file.file_id)
#         file2 = get_object_or_404(NewProposalFile, Q(id=file_id))
#         course =Course.objects.all().filter(code=file2.code).last()
#         version_error=''
#         if(course):
#             previous = Course.objects.all().filter(code=course.code).order_by('version').last()
#             course.version=previous.version
#             form = CourseForm(instance=file2,initial={'disciplines':file.disciplines})
#             submitbutton= request.POST.get('Submit')
#             if submitbutton:
#                 if request.method == 'POST':
#                     form = CourseForm(request.POST)  
#                     if form.is_valid() :
                        
#                         new_course = form.save(commit=False)
#                         if(new_course.version>previous.version):
#                             previous.latest_version=False
#                             previous.save()
#                             file.is_added=True
#                             file.is_submitted=True
#                             file.save()
#                             form.latest_version=True
#                             form.save()
#                             course = Course.objects.last()
                        
#                             receiver=file2.uploader
#                             receiver_id = User.objects.get(username=receiver)
#                             data=f'The Course " {file2.code} -{file2.name}" Updated Successfully'
#                             # data=file.subject
#                             prog_and_curr_notif(request.user,receiver_id,data)
#                             messages.success(request, "Updated "+ file2.code+'-'+file2.name +" successful")
#                             return HttpResponseRedirect("/programme_curriculum/course/" + str(course.id) + "/")
#                         else:
#                             version_error+=f'The version should be greater than {previous.version}'
                    
#             return render(request,'programme_curriculum/faculty/dean_view_a_course_proposal.html',{'course':course, 'form':form, 'submitbutton': submitbutton,'version_error':version_error,'id':Proposal_D})
#         else:
#             form = CourseForm(instance=file2,initial={'disciplines':file.disciplines})
#             # course1 =Course.objects.filter(code=file2.code,name=file2.name,credit=file2.credit,lecture_hours=file2.lecture_hours,tutorial_hours=file2.tutorial_hours,pratical_hours=file2.pratical_hours,discussion_hours=file2.discussion_hours,project_hours=file2.project_hours,pre_requisits=file2.pre_requisits,syllabus=file2.syllabus,percent_quiz_1=file2.percent_quiz_1,percent_midsem=file2.percent_midsem,percent_quiz_2=file2.percent_quiz_2,percent_project=file2.percent_project,percent_endsem=file2.percent_endsem,percent_lab_evaluation=file2.percent_lab_evaluation,percent_course_attendance=file2.percent_course_attendance,ref_books=file2.ref_books)
#             submitbutton= request.POST.get('Submit')
            
#             if submitbutton:
#                 if request.method == 'POST':
#                     form = CourseForm(request.POST)
                    
#                     if form.is_valid():
#                         file.is_added=True
#                         file.is_submitted=True
#                         file.save()
#                         form.save()
#                         receiver=file2.uploader
#                         receiver_id = User.objects.get(username=receiver)
#                         data='The Course "'+ file2.code+ ' - '+ file2.name + '" Added Successfully'
#                         # data=file.subject
#                         prog_and_curr_notif(request.user,receiver_id,data)
#                         course =Course.objects.all().filter(code=file2.code).last()
#                         messages.success(request, "Added "+ file2.name +" successful")
#                         return HttpResponseRedirect("/programme_curriculum/course/" + str(course.id) + "/")
                            
                           
                        
#             return render(request, 'programme_curriculum/faculty/dean_view_a_course_proposal.html', {'course': file2 ,'form':form,'submitbutton': submitbutton,'id':Proposal_D})
    
#     elif 'hod' in request.session['currentDesignationSelected'].lower():
        
#         form=CourseProposalTrackingFile(initial={'current_id':des.user,'current_design':request.session['currentDesignationSelected'],'file_id':file.file_id,'disciplines':file.disciplines})
        
#         # The above code is trying to retrieve the value of the 'Submit' key from the POST request
#         # data. It is using the `get` method on the `request.POST` dictionary to access the value
#         # associated with the 'Submit' key.
#         submitbutton= request.POST.get('Submit')
        
#         if submitbutton:
#             if request.method == 'POST':
#                 form = CourseProposalTrackingFile(request.POST)
#                 if form.is_valid():
#                     try:
#                         file.is_submitted=True
#                         file.save()
#                         form.is_read=False
#                         form.save()
                        
#                         receiver=request.POST.get('receive_id')
                        
#                         uploader=request.POST.get('current_id')
#                         uploader_design=request.POST.get('current_design')
                        
                        
#                         receiver_design=request.POST.get('receive_design')
#                         receiver_des= Designation.objects.get(id=receiver_design)
#                         receiver_id = User.objects.get(id=receiver)
#                         messages.success(request, "Added successful")
#                         data='Received as '+ str(receiver_id) +'-'+str(receiver_des) +' Course Proposal of Course '+file_data +' By   '+str(uploader)+' - '+str(uploader_design)

#                         prog_and_curr_notif(request.user,receiver_id,data)
#                         return HttpResponseRedirect('/programme_curriculum/outward_files/')
#                     except IntegrityError as e:
#                         form.add_error(None, 'Proposal_ tracking with this File id, Current id, Current design and Disciplines already exists.')
#     elif request.session['currentDesignationSelected'] == "acadadmin" :
#         return HttpResponseRedirect('/programme_curriculum/admin_programmes')
#     else:
#         return HttpResponseRedirect('/programme_curriculum/programmes')
        
        
        
#     return render(request,'programme_curriculum/faculty/forward.html',{'form':form,'receive_date':file.receive_date,'proposal':file2,'submitbutton': submitbutton,'id':Proposal_D})

@csrf_exempt
@permission_classes([IsAuthenticated])
def forward_course_forms(request, ProposalId):
    try:
        # Parse JSON data from request body
        data = json.loads(request.body)
        print(data)
        username = request.GET.get('username')
        designation = request.GET.get('des')
        print(designation)
        if not username or not designation:
            return JsonResponse({
                'status': 'error',
                'message': 'Username and designation are required'
            }, status=400)
        
        # Get the tracking record
        file = get_object_or_404(Proposal_Tracking, id=ProposalId)
        file_id = int(file.file_id)
        file2 = get_object_or_404(NewProposalFile, id=file_id)
        file_data = f"{file2.name} {file2.code}"

        
        # Handle different designation cases
        if designation == "Dean Academic":
            print("gaurav 1")
            course = Course.objects.filter(code=file2.code).last()
            print(course)
            previous = None
            version_error = None
            
            if course:
                previous = Course.objects.filter(code=course.code).order_by('version').last()
                if data.get('version') <= previous.version:
                    version_error = f'The version should be greater than {previous.version}'
                    return JsonResponse({
                        'status': 'error',
                        'message': version_error
                    }, status=400)
            
            # Update course and tracking
            # print("gaurav 2")
            course_data = {
                'code': data.get('code'),
                'name': data.get('name'),
                'version': data.get('version'),
                'credit': data.get('credit'),
                'lecture_hours': data.get('lecture_hours'),
                'tutorial_hours': data.get('tutorial_hours'),
                'pratical_hours': data.get('pratical_hours'),
                'discussion_hours': data.get('discussion_hours'),
                'project_hours': data.get('project_hours'),
                'pre_requisits': data.get('pre_requisits'),
                'pre_requisit_courses': data.get('pre_requisit_courses'),
                'syllabus': data.get('syllabus'),
                'percent_quiz_1': data.get('percent_quiz_1'),
                'percent_midsem': data.get('percent_midsem'),
                'percent_quiz_2': data.get('percent_quiz_2'),
                'percent_endsem': data.get('percent_endsem'),
                'percent_project': data.get('percent_project'),
                'percent_lab_evaluation': data.get('percent_lab_evaluation'),
                'percent_course_attendance': data.get('percent_course_attendance'),
                'ref_books': data.get('ref_books'),
                'working_course': data.get('working_course'),
                # 'disciplines': data.get('disciplines'),
                'latest_version': True,
                'max_seats': data.get('maxSeats')
            }
            prerequisite_course_ids = data.get('pre_requisit_courses', [])
            discipline_ids = data.get('disciplines',[])
            # if discipline_ids:
            #     valid_disciplines = Discipline.objects.filter(id__in=discipline_ids)
            #     if len(valid_disciplines) != len(discipline_ids):
            #         invalid_ids = set(discipline_ids) - set(d.id for d in valid_disciplines)
            #         return JsonResponse({
            #             'status': 'error',
            #             'message': f'Invalid discipline IDs: {invalid_ids}'
            #         }, status=400)

            valid_courses = Course.objects.filter(id__in=prerequisite_course_ids)
            if len(valid_courses) != len(prerequisite_course_ids):
                invalid_ids = set(prerequisite_course_ids) - set(c.id for c in valid_courses)
                return JsonResponse({
                    'status': 'error',
                    'message': f'Invalid prerequisite course IDs: {invalid_ids}'
                }, status=400)
            
            form = CourseForm(course_data)
            
            if form.is_valid():
                
                new_course = form.save(commit=False)
                # new_course.is_read = False
                new_course.save()
                file.is_added = True
                file.is_submitted = True
                file.save()

                receiver=file2.uploader
                receiver_id = User.objects.get(username=receiver)
                uploader_id=  User.objects.get(username=username)
                flag_updated = file2.is_update
                notification_data = (
                    f'The updated version of course "{file_data}" was added successfully' 
                    if flag_updated 
                    else f'The course "{file_data}" was added successfully'
                )
                prog_and_curr_notif(uploader_id, receiver_id, notification_data)

                if prerequisite_course_ids:
                    new_course.pre_requisit_courses.add(*valid_courses)
                if discipline_ids:
                    new_course.disciplines.add(*discipline_ids)
                return JsonResponse({
                    'status': 'success',
                    'message': 'Course added successfully',
                    'course_id': new_course.id,
                    'prerequisite_courses_added': len(prerequisite_course_ids)
                }, status=201)
            else:
                print(form.errors)
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid form data',
                    'errors': form.errors
                }, status=400)
            
        elif 'hod' in designation.lower():
            try:
                receiver_user = User.objects.get(username=data.get('receiverId'))
                uploader_user = User.objects.get(username=data.get('uploader'))
                receiver_designation = Designation.objects.get(name=data.get('receiverDesignation'))
                # print("receiver_user ff",receiver_user)
                # print("receiver des ff",receiver_designation)
                # print(data.get('discipline'))
                discipline = Discipline.objects.get(id=data.get('discipline'))  # Assuming single discipline
                # print(discipline)
            except (User.DoesNotExist, Designation.DoesNotExist, Discipline.DoesNotExist) as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Invalid reference: {str(e)}'
                }, status=400)
            
            # Create tracking record
            tracking_data = {
                'file_id': data.get('fileId'),
                'current_id': data.get('uploader'),
                'current_design': data.get('designation'),
                'receive_id': receiver_user.id,
                'receive_design': receiver_designation.id,
                'disciplines': discipline.id,
                'remarks': data.get('remarks', ''),
                # 'is_submitted': True
            }
            # print("traking data ff",tracking_data)
            # Validate form data
            # print("gaurav 1")
            required_fields = ['receiverId', 'receiverDesignation']
            if not all(field in data for field in required_fields):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Missing required fields'
                }, status=400)
            
            # Update tracking
           
            form = CourseProposalTrackingFile(tracking_data)
            
            if form.is_valid():
                try:
                    tracking = form.save(commit=False)
                    tracking.save()
                    file.is_submitted = True
                    file.save()
                    
                    # Prepare notification data
                    # file_data = f"{file.name} {file.code}"
                    notification_data = (
                        f"Received as {receiver_user} - {receiver_designation} "
                        f"Course Proposal Form '{file_data}' "
                        f"By {data.get('uploader')} - {data.get('designation')}"
                    )
                    prog_and_curr_notif(uploader_user,receiver_user,notification_data)
                    
                except IntegrityError:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'This file tracking record already exists'
                    }, status=400)
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid form data',
                    'errors': form.errors
                }, status=400)
            
            # Create notification
            # notification_data = {
            #     'sender': username,
            #     'receiver': data['receiverId'],
            #     'message': f'Received as {data["receiverId"]}-{data["receiverDesignation"]} Course Proposal of Course {file2.code} {file2.name} By {username} - {designation}',
            #     'course_id': file2.id
            # }
            
            return JsonResponse({
                    'status': 'success',
                    'message': 'File tracking submitted successfully',
                    # 'notification': notification_data
                }, status=201)
                
            
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Unauthorized designation'
            }, status=403)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        print(str(e))
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
    

@csrf_exempt
@permission_classes([IsAuthenticated])
def forward_course_forms_II(request):
    try:
        id=request.GET.get('id')
        if not id:
            return JsonResponse({
                'status': 'error',
                'message': 'ProposalId is required'
            }, status=400)
        # Get the tracking record
        file = get_object_or_404(Proposal_Tracking, id=id)
        file_id = int(file.file_id)
        file2 = get_object_or_404(NewProposalFile, id=file_id)

        response_data = {
            'proposal': {
                'id': file2.id,
                'name': file2.name,
                'code': file2.code,
                'credit': file2.credit,
                'uploader': file2.uploader,
                'designation': file2.designation,
                'lecture_hours': file2.lecture_hours,
                'tutorial_hours': file2.tutorial_hours,
                'pratical_hours': file2.pratical_hours,
                'project_hours': file2.project_hours,
                'discussion_hours': file2.discussion_hours,
                'syllabus': file2.syllabus,
                'percent_quiz_1': file2.percent_quiz_1,
                'percent_midsem': file2.percent_midsem,
                'percent_quiz_2': file2.percent_quiz_2,
                'percent_endsem': file2.percent_endsem,
                'percent_project': file2.percent_project,
                'percent_lab_evaluation': file2.percent_lab_evaluation,
                'percent_course_attendance': file2.percent_course_attendance,
                'ref_books': file2.ref_books,
                'pre_requisits': file2.pre_requisits,
                'max_seats': file2.max_seats,
                'pre_requisits_courses': list(file2.pre_requisit_courses.values('id', 'name','code','version')),
                'discipline':[file.disciplines.id],
            },
            # Add other fields as needed
        }
        return JsonResponse({
            'status': 'success',
            'data': response_data
        })
    except Exception as e:
        print(str(e))
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
   

@csrf_exempt
@permission_classes([IsAuthenticated])
def view_inward_files(request,ProposalId):
    try:
        # Get parameters from frontend
        # proposal_id = request.GET.get('proposalId')
        username = request.GET.get('username')
        designation = request.GET.get('des')
        
        if not all([ProposalId, username, designation]):
            return JsonResponse({
                'status': 'error',
                'message': 'proposalId, username and designation are required'
            }, status=400)
        
        # Get the tracking record
        file = get_object_or_404(Proposal_Tracking, id=ProposalId)
        file_id = int(file.file_id)
        proposal_file = get_object_or_404(NewProposalFile, id=file_id)
        
        # Get user details
        # user = request.user
        # user_details = ExtraInfo.objects.get(user=username)
        # user_designation = HoldsDesignation.objects.filter(user=username).first()
        
        # Prepare response data
        response_data = {
            'proposal': {
                'id': proposal_file.id,
                'name': proposal_file.name,
                'code': proposal_file.code,
                'credit': proposal_file.credit,
                'uploader': proposal_file.uploader,
                'designation': proposal_file.designation,
                'lecture_hours': proposal_file.lecture_hours,
                'tutorial_hours': proposal_file.tutorial_hours,
                'pratical_hours': proposal_file.pratical_hours,
                'project_hours': proposal_file.project_hours,
                'discussion_hours': proposal_file.discussion_hours,
                'syllabus': proposal_file.syllabus,
                'percent_quiz_1': proposal_file.percent_quiz_1,
                'percent_midsem': proposal_file.percent_midsem,
                'percent_quiz_2': proposal_file.percent_quiz_2,
                'percent_endsem': proposal_file.percent_endsem,
                'percent_project': proposal_file.percent_project,
                'percent_lab_evaluation': proposal_file.percent_lab_evaluation,
                'percent_course_attendance': proposal_file.percent_course_attendance,
                'ref_books': proposal_file.ref_books,
                'pre_requisits': proposal_file.pre_requisits,
                'max_seats': proposal_file.max_seats,
                'pre_requisit_courses': list(proposal_file.pre_requisit_courses.values('id', 'name','code','version')),
                'subject': proposal_file.subject,
                'description': proposal_file.description,

            },
            'tracking': {
                'id': file.id,
                'file_id': file.file_id,
                'receive_date': file.receive_date,
                'forward_date': file.forward_date,
                'is_rejected': file.is_rejected,
                'is_added': file.is_added,
                'receive_id': file.receive_id.username,
                'receive_design': file.receive_design.name,
                'current_id': file.current_id,
                'current_design': file.current_design,
                'remarks': file.remarks,
                'disciplines_name': file.disciplines.name,
                'disciplines_acronym': file.disciplines.acronym,
            },
            'trackings': list(Proposal_Tracking.objects.filter(
                file_id=file.file_id,
                disciplines=file.disciplines
            ).values(
                'id',
                'current_id',
                'current_design',
                'receive_date',
                'forward_date',
                'remarks',
                'is_rejected',
                'is_added'
            )),
            'status_info': {
                'rejected_message': f'"{proposal_file.name}" Course Rejected by {file.receive_id} - {file.receive_design}' 
                                    if file.is_rejected else None,
                'added_message': f'"{proposal_file.code} - {proposal_file.name}" Course Added Successfully' 
                                if (file.is_added and not file.is_rejected) else None
            }
        }
        
        return JsonResponse({
            'status': 'success',
            'data': response_data
        })
        
    except Exception as e:
        print(str(e))
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reject_form(request, ProposalId):
    try:
        # Debugging - print incoming request data
        print(f"Incoming request - User: {request.user}, Method: {request.method}")
        print(f"Query params: {request.GET}")
        
        # Get query parameters
        username = request.GET.get('username', '')
        designation = request.GET.get('des', '')
        
        if not username or not designation:
            return JsonResponse({
                'status': 'error',
                'message': 'Missing username or designation parameters'
            }, status=400)

        # Get the tracking and file objects
        try:
            track = Proposal_Tracking.objects.get(id=ProposalId)
            file2 = NewProposalFile.objects.get(id=track.file_id)
        except Proposal_Tracking.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Proposal not found'
            }, status=404)
        except NewProposalFile.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Proposal file not found'
            }, status=404)

        if track.is_added:
            return JsonResponse({
                'status': 'error',
                'message': 'Course already forwarded or added, cannot be rejected'
            }, status=400)

        # Update tracking
        track.is_rejected = True
        track.is_submitted = True
        track.save()
        
        # Send notification
        try:
            receiver_user = User.objects.get(username=file2.uploader)
            notification_message = (
                f'The Course "{file2.code} - {file2.name}" was Rejected by '
                f'{username} ({designation})'
            )
            prog_and_curr_notif(request.user, receiver_user, notification_message)
        except User.DoesNotExist:
            # Continue even if notification fails
            pass

        return JsonResponse({
            'status': 'success',
            'message': 'Course Proposal Form Rejected',
            'data': {
                'proposal_id': ProposalId,
                'rejected_by': username,
                'designation': designation
            }
        }, status=200)
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': 'Server error: ' + str(e)
        }, status=500)


    
@csrf_exempt
@permission_classes([IsAuthenticated])
def tracking_unarchive(request,ProposalId):
    try:
        # Parse JSON data from request body
        # data = json.loads(request.body)
        # proposal_id = request.GET.get('proposalId')
        username = request.GET.get('username',' ')
        designation = request.GET.get('des',' ')
        
        if not all([username, designation]):
            return JsonResponse({
                'status': 'error',
                'message': 'Missing required fields'
            }, status=400)
        
        # Get the tracking record
        track = get_object_or_404(Proposal_Tracking, id=ProposalId)
        
        # Check if current user is the sender or receiver
        if (str(track.current_design) == designation and 
            str(track.current_id) == username):
            # Current user is the sender
            track.sender_archive = False
            action = 'sender_archive'
        else:
            # Current user is the receiver
            track.receiver_archive = False
            action = 'receiver_archive'
        
        track.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'File Unarchived successfully',
            'action': action,
            'proposal_id': ProposalId
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@permission_classes([IsAuthenticated])
def tracking_archive(request,ProposalId):
    try:
        # Parse JSON data from request body
        # data = json.loads(request.body)
        # proposal_id = request.GET.get('proposalId')
        username = request.GET.get('username',' ')
        designation = request.GET.get('des',' ')
        
        if not all([username, designation]):
            return JsonResponse({
                'status': 'error',
                'message': 'Missing required fields'
            }, status=400)
        
        # Get the tracking record
        track = get_object_or_404(Proposal_Tracking, id=ProposalId)
        
        # Check if current user is the sender or receiver
        if (str(track.current_design) == designation and 
            str(track.current_id) == username):
            # Current user is the sender
            track.sender_archive = True
            action = 'sender_archive'
        else:
            # Current user is the receiver
            track.receiver_archive = True
            action = 'receiver_archive'
        
        track.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'File archived successfully',
            'action': action,
            'proposal_id': ProposalId
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt  # Use this decorator if you're not using CSRF tokens in your API calls
@permission_classes([IsAuthenticated])
def file_archive(request,FileId):
    print("ID:", FileId)
    try:
        file = get_object_or_404(NewProposalFile, Q(id=FileId))
        file.is_archive = True
        file.save()
        return JsonResponse({
            'status': 'success',
            'message': 'File archived successfully',
            'file_id': FileId
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@csrf_exempt  # Use this decorator if you're not using CSRF tokens in your API calls
@permission_classes([IsAuthenticated])
def file_unarchive(request,FileId):
    
    print("ID:", FileId)
    try:
        file = get_object_or_404(NewProposalFile, Q(id=FileId))
        file.is_archive = False
        file.save()
        return JsonResponse({
            'status': 'success',
            'message': 'File archived successfully',
            'file_id': FileId
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@csrf_exempt
@permission_classes([IsAuthenticated])
def course_slot_type_choices(request):
    """
    API endpoint to return the list of course slot type choices from the CourseSlot model.
    """
    choices = [{'value': key, 'label': label} for key, label in CourseSlot._meta.get_field('type').choices]
    # print(choices)
    return JsonResponse({'choices': choices})

@csrf_exempt
@permission_classes([IsAuthenticated])
def semester_details(request):
    curriculum_id = request.GET.get('curriculum_id')

    if not curriculum_id:
        return JsonResponse({'error': 'Missing curriculum_id parameter'}, status=400)

    curriculum = get_object_or_404(Curriculum, id=curriculum_id)

    # Retrieve curriculum details
    curriculum_name = curriculum.name
    curriculum_version = curriculum.version  # Ensure this field exists in the model

    # Get all semesters related to the given curriculum ID
    semesters = Semester.objects.filter(curriculum_id=curriculum_id).order_by('semester_no')
    semester_list = [
        {
            "semester_id": semester.id,
            "semester_number": semester.semester_no
        }
        for semester in semesters
    ]

    data = {
        "curriculum_name": curriculum_name,
        "curriculum_version": curriculum_version,
        "semesters": semester_list,
    }

    print("data:", data)
    return JsonResponse(data)

@api_view(['GET'])
@csrf_exempt
@permission_classes([IsAuthenticated])
def get_programme(request, programme_id):
    program = get_object_or_404(Programme, id=programme_id)
    # curriculums = program.curriculums.all()

    # Filtering working and past curriculums
    # working_curriculums = curriculums.filter(working_curriculum=1)
    # past_curriculums = curriculums.filter(working_curriculum=0)

    data = {
        'program': {
            # 'id': program.id,
            'category': program.category,
            'name': program.name,
            # 'beginyear': program.programme_begin_year,
        },
        # 'working_curriculums': CurriculumSerializer(working_curriculums, many=True).data,
        # 'past_curriculums': CurriculumSerializer(past_curriculums, many=True).data,
    }
    return JsonResponse(data)

@csrf_exempt
@permission_classes([IsAuthenticated])
def get_batch_names(request):
    choices = [{'value': key, 'label': label} for key, label in Batch._meta.get_field('name').choices]
    # print('choices',choices)

    # batch_names = Batch.objects.values_list('name', flat=True).distinct()
    # print(batch_names)
    # # Convert the QuerySet to a list
    # batch_names_list = list(batch_names)
    # print(batch_names_list)
    # Return the list as a JSON response
    return JsonResponse({'choices': choices})

@csrf_exempt
@permission_classes([IsAuthenticated])
def get_all_disciplines(request):
    # Fetch all disciplines from the database
    disciplines = Discipline.objects.all()
    
    # Serialize the disciplines into a list of dictionaries
    disciplines_data = [
        {
            'id': discipline.id,
            'name': discipline.name,
            'acronym': discipline.acronym,
            'programmes': [programme.name for programme in discipline.programmes.all()]
        }
        for discipline in disciplines
    ]
    
    # Return the serialized data as a JSON response
    return JsonResponse(disciplines_data, safe=False)
@csrf_exempt
@permission_classes([IsAuthenticated])
def get_unused_curriculam(request):
    # Fetch all curriculum IDs that are present in the Batch table
    used_curriculum_ids = Batch.objects.exclude(curriculum__isnull=True).values_list('curriculum_id', flat=True)

    # Fetch curricula whose IDs are not in the used_curriculum_ids list
    unused_curricula = Curriculum.objects.exclude(id__in=used_curriculum_ids)

    # Serialize the unused curricula
    unused_curricula_data = [
        {
            'id': curriculum.id,
            'name': curriculum.name,
            'version': curriculum.version,
            # 'discipline': curriculum.discipline.name,
            # 'programme': curriculum.programme.name,
        }
        for curriculum in unused_curricula
    ]
    print(unused_curricula_data)

    # Return the serialized data as a JSON response
    return JsonResponse(unused_curricula_data, safe=False)
@csrf_exempt
@permission_classes([IsAuthenticated])
def admin_view_all_course_instructor(request):
    # Fetch all records from the CourseInstructor table
    course_instructors = CourseInstructor.objects.select_related(
        'course_id', 'instructor_id__id__user'  # Traversing Faculty → ExtraInfo → User
    ).annotate(
        course_name=F('course_id__name'),
        course_code = F('course_id__code'),
        course_version=F('course_id__version'),
        faculty_first_name=F('instructor_id__id__user__first_name'),
        faculty_last_name=F('instructor_id__id__user__last_name')
    ).values(
        'course_id', 'course_name', 'course_code', 'course_version', 
        'instructor_id','semester_type', 'faculty_first_name', 'faculty_last_name', 
        'year', 'id'
    )
    for instructor in course_instructors:
        obj = CourseInstructor(
            year=instructor['year'],
            semester_type=instructor['semester_type']
        )
        instructor['academic_year'] = obj.academic_year

    # Convert queryset to a list
    course_instructors_data = list(course_instructors)

    # Convert queryset to a list
    # course_instructors_data = list(course_instructors)
    return JsonResponse({'course_instructors': course_instructors_data})
@csrf_exempt
@permission_classes([IsAuthenticated])
def admin_view_all_faculties(request):
    # Fetch all faculties with their user details
    faculties = Faculty.objects.select_related('id__user').annotate(
        faculty_first_name=F('id__user__first_name'),
        faculty_last_name=F('id__user__last_name')
    ).values(
        'id',  # Faculty ID from globals_faculty
        'faculty_first_name',  # First name from auth.user
        'faculty_last_name'  # Last name from auth.user
    )

    # Convert queryset to a list
    faculties_data = list(faculties)

    return JsonResponse({'faculties': faculties_data})

def parse_academic_year(academic_year, semester_type):
    """
    Parse academic_year string (e.g., "2024-25") and determine the working_year based on semester type.
    For Odd Semester, working_year = first part (e.g., 2024).
    For Even Semester, working_year = second part prefixed by '20' (e.g., 2025 if academic_year is "2024-25").
    The session is set to the academic_year string.
    """
    parts = academic_year.split("-")
    if len(parts) != 2:
        raise ValueError("Invalid academic year format. Expected format like '2024-25'.")
    first_year = parts[0].strip()
    second_year = parts[1].strip()
    if semester_type == "Odd Semester":
        working_year = int(first_year)
    elif semester_type == "Even Semester":
        working_year = int("20" + second_year)
    else:
        # For any other semester type (e.g., Summer Semester) use the first year by default.
        working_year = int("20"+second_year)
    return working_year

@csrf_exempt
@permission_classes([IsAuthenticated])
def add_course_instructor(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    # 1) JSON branch (manual form)
    if request.body and request.content_type == "application/json":
        try:
            data = json.loads(request.body)
            # convert academic_year + semester_type → year
            if "semester_type" not in data:
                return JsonResponse(
                    {"error": "Must include semester_type"},
                    status=400,
                )

            data["year"] = parse_academic_year(
                data["academic_year"], data["semester_type"]
            )
            data.pop("academic_year", None)
            form = CourseInstructorForm(data)
            print(data)
            if form.is_valid():
                form.save()
                return JsonResponse(
                    {"success": "Instructor added successfully"}, status=201
                )
            return JsonResponse(
                {"error": "Invalid form", "details": form.errors}, status=400
            )
        except ValueError as ve:
            return JsonResponse({"error": str(ve)}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"Unexpected error: {e}"}, status=500)

    # 2) Excel branch
    if request.FILES.get("manual_instructor_xsl") and request.POST.get(
        "excel_submit"
    ):
        f = request.FILES["manual_instructor_xsl"]
        try:
            book = xlrd.open_workbook(file_contents=f.read())
            sheet = book.sheet_by_index(0)
        except Exception as e:
            return JsonResponse({"error": f"Excel read error: {e}"}, status=400)

        errors = []
        rows = []
        with transaction.atomic():
            for i in range(1, sheet.nrows):
                try:
                    code = str(sheet.cell(i, 0).value).strip()
                    version = float(sheet.cell(i, 1).value)
                    instr_id = str(sheet.cell(i, 2).value).strip()
                    acad_year = str(sheet.cell(i, 3).value).strip()
                    sem_type = str(sheet.cell(i, 4).value).strip()

                    # convert year
                    year = parse_academic_year(acad_year, sem_type)

                    # validate semester type choice
                    if sem_type not in dict(CourseInstructor.SEMESTER_TYPE_CHOICES):
                        raise ValueError(f"Bad semester_type '{sem_type}'")

                    course = Course.objects.filter(code__iexact=code, version=version).first()
                    if not course:
                        raise ValueError(f"Course {code} v{version} not found")

                    fac = Faculty.objects.filter(id=instr_id).first()
                    if not fac:
                        raise ValueError(f"Instructor {instr_id} not found")

                    if CourseInstructor.objects.filter(
                        course_id=course, instructor_id=fac, year=year
                    ).exists():
                        raise ValueError("Duplicate entry")

                    rows.append((course, fac, year, sem_type))
                except Exception as e:
                    errors.append({"row": i + 1, "error": str(e)})

            if errors:
                return JsonResponse({"error": "Validation failed", "details": errors}, status=400)

            # bulk insert
            for course, fac, year, sem_type in rows:
                CourseInstructor.objects.create(
                    course_id=course,
                    instructor_id=fac,
                    year=year,
                    semester_type=sem_type,
                    version = version
                )

        return JsonResponse({"success": f"{len(rows)} instructors added"}, status=201)

    return JsonResponse({"error": "Unrecognized request"}, status=400)



@csrf_exempt
@permission_classes([IsAuthenticated])
def update_course_instructor_form(request, instructor_id):
    # Retrieve the CourseInstructor object or return 404 if not found
    course_instructor = get_object_or_404(CourseInstructor, id=instructor_id)

    if request.method == 'POST':
        # Parse the JSON data from the request body
        try:
            payload = json.loads(request.body)
            form = CourseInstructorForm(payload, instance=course_instructor)
            if form.is_valid():
                form.save()  # Save the updated data to the database
                return JsonResponse({'status': 'success', 'message': 'Course Instructor updated successfully!'})
            else:
                # Return validation errors if the form is invalid
                return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)

    # Handle unsupported HTTP methods
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

@csrf_exempt  # Use this decorator if you're not using CSRF tokens in your API calls
@permission_classes([IsAuthenticated])
def get_superior_data(request):
    try:
        # Get parameters from request
        username = request.GET.get('uploaderId')
        print("username",username)
        designation = request.GET.get('uploaderDes', '').lower()
        print("designation",designation)
        
        if not username:
            return JsonResponse({'error': 'Username is required'}, status=400)
        
        # Get the user object
        user = User.objects.get(username=username)
        print("user",user)
        
        # Get user's extra info and department
        extra_info = ExtraInfo.objects.get(user=user)
        print("extra_info",extra_info)
        user_department = extra_info.department
        print("user_department",user_department)
        
        # Initialize response data
        response_data = {
            'user': username,
            'department': user_department.name if user_department else None,
            'superior_data': None
        }
        
        # Check if user is Professor/Associate Professor/Assistant Professor
        professor_designations = ['professor', 'associate professor', 'assistant professor']
        is_professor = designation in professor_designations
        print("is_professor",is_professor)
        
        # Check if user is HOD (using regex to match HOD (DEPT) pattern)
        is_hod = bool(re.match(r'^hod\s*\(.*\)$', designation, re.IGNORECASE))
        print("is_hod",is_hod)
        
        if is_professor and user_department:
            # Get HOD of the same department
            hod_designation_name = f"HOD ({user_department.name})"
            try:
                hod_designation = Designation.objects.get(name__iexact=hod_designation_name)
                hod = HoldsDesignation.objects.filter(
                    designation=hod_designation
                ).select_related('working', 'working__extrainfo').first()
                
                if hod:
                    hod_user = hod.working
                    hod_extra_info = hod_user.extrainfo
                    response_data['superior_data'] = {
                        'username': hod_user.username,
                        'name': f"{hod_user.first_name} {hod_user.last_name}",
                        'designation': hod_designation_name,
                        'department': user_department.name,
                        'department_id': user_department.id,
                        'email': hod_user.email,
                        'phone': hod_extra_info.phone_no
                    }
            except Designation.DoesNotExist:
                pass  # HOD designation for this department doesn't exist
        
        elif is_hod:
            # Get Dean Academic
            try:
                dean_designation = Designation.objects.get(name__iexact='Dean Academic')
                dean = HoldsDesignation.objects.filter(
                    designation=dean_designation
                ).select_related('working', 'working__extrainfo').first()
                
                if dean:
                    dean_user = dean.working
                    dean_extra_info = dean_user.extrainfo
                    response_data['superior_data'] = {
                        'username': dean_user.username,
                        'name': f"{dean_user.first_name} {dean_user.last_name}",
                        'designation': 'Dean Academic',
                        'department': dean_extra_info.department.name if dean_extra_info.department else None,
                        'department_id': dean_extra_info.department.id if dean_extra_info.department else None,
                        'email': dean_user.email,
                        'phone': dean_extra_info.phone_no
                    }
            except Designation.DoesNotExist:
                pass  # Dean Academic designation doesn't exist
        
        return JsonResponse(response_data)
    
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except ExtraInfo.DoesNotExist:
        return JsonResponse({'error': 'User extra info not found'}, status=404)
    except Exception as e:
        print(str(e))   
        return JsonResponse({'error': str(e)}, status=500)
