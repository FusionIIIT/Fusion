from datetime import datetime, date
from django.shortcuts import get_object_or_404, render
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Avg, Count, Min, Sum, Q
from django.http import HttpResponse, HttpResponseRedirect
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation
from applications.academic_information.models import Curriculum_Instructor
from applications.eis.models import (
    emp_consultancy_projects, emp_research_projects,
    emp_mtechphd_thesis, emp_patents, emp_techtransfer,
    emp_published_books, emp_confrence_organised,
    emp_achievement, emp_event_organized
)
from applications.establishment.models import (
    Appraisal, CoursesInstructed, NewCoursesOffered,
    NewCourseMaterial, ThesisResearchSupervision, SponsoredProjects,
    AppraisalRequest, AppraisalAdministrators, Constants
)
from .permissions import is_admin, is_eligible, is_hod, is_director, is_faculty, is_staff

@transaction.atomic
def handle_appraisal(request):
    """
        This function is used to handle various requests in the
        Appraisal module.
        request: HttpRequest object that contains metadata of
                 Appraisal requests.
    """
    # Condition to handle the Appraisal Request generated from
    # the faculty end by submitting a form.
    if 'appraisal_request' in request.POST:
        try:
            applicant = request.user
            # Query to find the designation of the user
            user_dsg = list(HoldsDesignation.objects.filter(user=request.user))
            designation = user_dsg[0].designation
            # Query to find the department/discipline of the user
            user_dep = list(ExtraInfo.objects.filter(user=request.user))
            discipline = user_dep[0].department
            # handling form data
            knowledge_field = request.POST.get('specific_field_knowledge')
            research_interest = request.POST.get('current_research_interest')
            status = 'requested'
            timestamp = datetime.now()
            other_research_element = request.POST.get('other_research_element')
            publications = request.POST.get('publications')
            conferences_meeting_attended = request.POST.get('conferences_meeting_attended')
            conferences_meeting_organized = request.POST.get('conferences_meeting_organized')
            admin_assign = request.POST.get('admin_assign')
            sevice_to_ins = request.POST.get('sevice_to_ins')
            extra_info = request.POST.get('extra_info')
            faculty_comments = request.POST.get('faculty_comments')
            start_date = date.fromisoformat(request.POST.get('start_date'))
            end_date   = date.fromisoformat(request.POST.get('end_date'))
            # Creating Appraisal Object
            application = Appraisal.objects.create(
                    applicant = applicant,
                    designation = designation,
                    discipline = discipline,
                    knowledge_field = knowledge_field,
                    research_interest = research_interest,
                    status = status,
                    timestamp = timestamp,
                    other_research_element = other_research_element,
                    publications = publications,
                    conferences_meeting_attended = conferences_meeting_attended,
                    conferences_meeting_organized = conferences_meeting_organized,
                    admin_assign = admin_assign,
                    sevice_to_ins = sevice_to_ins,
                    extra_info = extra_info,
                    faculty_comments = faculty_comments,
                    start_date = start_date,
                    end_date = end_date
            )
            # NewCoursesOffered
            count = 1
            while(1):
                course_name = request.POST.get('Course-Name1.1.2'+str(count))
                course_num = request.POST.get('Course Number1.1.2'+str(count))
                UGorPG = request.POST.get('UG/PG1.1.2'+str(count))
                tutorial_hrs_wk = request.POST.get('Tutorial (Hours/week)1.1.2'+str(count))
                year = request.POST.get('YEAR1.1.2'+str(count))
                semester = request.POST.get('Semester1.1.2'+str(count))
                if(semester == None):
                    break
                new_course = NewCoursesOffered.objects.create(
                                appraisal = application,
                                course_name = course_name,
                                course_num = course_num,
                                ug_or_pg = UGorPG,
                                tutorial_hrs_wk = tutorial_hrs_wk,
                                year = year,
                                semester = semester
                )
        
                count += 1


            # NewCourseMaterial
            count = 1
            while(1):
                course_name = request.POST.get('Course-Name' + '1.1.3' + str(count))
                course_num = request.POST.get('Course Number' + '1.1.3' + str(count))
                ug_or_pg = request.POST.get('UG/PG' + '1.1.3' + str(count))
                activity_type = request.POST.get('Type of Activity' + '1.1.3' + str(count))
                availiability = request.POST.get('Web/Public' + '1.1.3' + str(count))
                if(course_num == None):
                    break
        
                new_courses_material = NewCourseMaterial.objects.create(
                                        appraisal = application,
                                        course_name = course_name,
                                        course_num = course_num,
                                        ug_or_pg = ug_or_pg,
                                        activity_type = activity_type,
                                        availiability = availiability
                )
        
                count += 1
            
            # Finding the user with designation "HOD" of the department to which the applicant belongs.
            user_info = ExtraInfo.objects.filter(user = applicant)
            user_info = user_info[0]
            designation = None
            if(user_info.department.name == 'CSE'):
                designation = Designation.objects.filter(name = 'CSE HOD')
            elif(user_info.department.name == 'ECE'):
                designation = Designation.objects.filter(name = 'HOD (ECE)')
            elif(user_info.department.name == 'ME'):
                designation = Designation.objects.filter(name = 'HOD (ME)')
            elif(user_info.department.name == 'Design'):
                designation = Designation.objects.filter(name = 'HOD (Design)')
            else:
                designation = Designation.objects.filter(name = 'HOD (NS)')
            holds_designation = HoldsDesignation.objects.filter(designation = designation[0])
            hod = holds_designation[0].user
            # Finding the user with designation "Director"
            designation = Designation.objects.filter(name = 'Director')
            holds_designation = HoldsDesignation.objects.filter(designation = designation[0])
            director = holds_designation[0].user
            # Creating AppraisalRequest Object to track the application
            appraisal_request = AppraisalRequest.objects.create(
                    appraisal = application,
                    hod = hod,
                    director = director
            )
            messages.success(request, 'Appraisal Request sent successfully!')
            return application
        except Exception as e:
            messages.error(request,e)

    # Condition to handle the Appraisal Review Request generated from
    # the HOD end by reviewing a application.
    if 'hod_appraisal_review' in request.POST:
        try:
            app_id = int(request.POST.get('app_id'))
            review_comment = request.POST.get('remarks_hod')
            result = request.POST.get('result')
            application = Appraisal.objects.get(id=app_id)
            request_object = AppraisalRequest.objects.filter(appraisal = application)
            appraisal_track = request_object[0]
            appraisal_track.remark_hod = review_comment
            appraisal_track.status_hod = result
            appraisal_track.save()
            messages.success(request, 'Review submitted successfully!')
        except Exception as e:
            messages.error(request,e)

    # Condition to handle the Appraisal Review Request generated from
    # the Director end by reviewing a application.
    if 'director_appraisal_review' in request.POST:
        try:
            app_id = int(request.POST.get('app_id'))
            review_comment = request.POST.get('remarks_director')
            result = request.POST.get('result')
            application = Appraisal.objects.select_related('applicant').get(id=app_id)
            application.status = "Processed"
            request_object = AppraisalRequest.objects.select_related('appraisal').filter(appraisal = application)
            appraisal_track = request_object[0]
            appraisal_track.remark_director = review_comment
            appraisal_track.status_director = result
            appraisal_track.save()
            application.save()
            messages.success(request, 'Review submitted successfully!')
        except Exception as e:
            messages.error(request,e)


def generate_appraisal_lists(request):
    """
        Generating JSON object to get data from the front-end.
    """
    try:
        response = {}
        user_courses = []
        course_objects = Curriculum_Instructor.objects.all()
        for course in course_objects:
            if(course.instructor_id.user == request.user):
                user_courses.append(course)
        consultancy_projects = emp_consultancy_projects.objects.filter(user = request.user)
        research_projects = emp_research_projects.objects.filter(user = request.user)
        thesis = emp_mtechphd_thesis.objects.filter(user = request.user)
        patents = emp_patents.objects.filter(user = request.user)
        tech_transfer = emp_techtransfer.objects.filter(user = request.user)
        publications = emp_published_books.objects.filter(user = request.user)
        conferences = emp_confrence_organised.objects.filter(user = request.user)
        achievments = emp_achievement.objects.filter(user = request.user)
        events = emp_event_organized.objects.filter(user = request.user)
        active_apps = (Appraisal.objects.select_related('applicant').filter(applicant=request.user).exclude(status='Processed').order_by('-timestamp'))
        archive_apps = Appraisal.objects.select_related('applicant').filter(applicant=request.user).exclude(status='requested').order_by('-timestamp')
        request_active = (AppraisalRequest.objects.select_related('appraisal').filter(appraisal__applicant=request.user).filter(appraisal__status='requested'))
        request_archived = (AppraisalRequest.objects.select_related('appraisal').filter(appraisal__applicant=request.user).exclude(appraisal__status='requested'))
        new_courses_offered = NewCoursesOffered.objects.filter(appraisal__applicant=request.user)
        new_courses_material = NewCourseMaterial.objects.filter(appraisal__applicant=request.user)
        response.update({
                'user_courses': user_courses,
                'consultancy_projects': consultancy_projects,
                'research_projects': research_projects,
                'thesis': thesis,
                'patents': patents,
                'tech_transfer': tech_transfer,
                'publications': publications,
                'conferences': conferences,
                'achievments': achievments,
                'events': events,
                'appraisal_active_apps':active_apps,
                'appraisal_archive_apps':archive_apps,
                'appraisal_requests_active':request_active,
                'appraisal_requests_archived':request_archived,
                'new_courses_offered': new_courses_offered,
                'new_courses_material': new_courses_material,
                'start_date': False,
                'end_date': False
        })
        return response
    except Exception as e:
            messages.error(request,e)    


def generate_appraisal_lists_hod(request):
    """
        Generating JSON object to get data from the front-end for user
        with designation "HOD".
    """
    try:
        response = {}
        review_apps_hod = AppraisalRequest.objects.select_related('appraisal').filter(hod = request.user).filter(status_hod = 'pending').order_by('-request_timestamp')
        reviewed_apps_hod = AppraisalRequest.objects.select_related('appraisal').filter(hod = request.user).exclude(status_hod = 'pending').order_by('-request_timestamp')
        course_objects_all = Curriculum_Instructor.objects.all()
        consultancy_projects_all = emp_consultancy_projects.objects.all()
        research_projects_all = emp_research_projects.objects.all()
        thesis_all = emp_mtechphd_thesis.objects.all()
        events_all = emp_event_organized.objects.all()
        patents_all = emp_patents.objects.all()
        tech_transfer_all = emp_techtransfer.objects.all()
        publications_all = emp_published_books.objects.all()
        conferences_all = emp_confrence_organised.objects.all()
        achievments_all = emp_achievement.objects.all()
        appraisal_all = Appraisal.objects.select_related('applicant').all()
        new_courses_offered_all = NewCoursesOffered.objects.all()
        new_courses_material_all = NewCourseMaterial.objects.all()
        response.update({
            'hod': True,
            'reviewed_apps_hod': reviewed_apps_hod,
            'course_objects_all': course_objects_all,
            'review_apps_hod': review_apps_hod,
            'thesis_all': thesis_all,
            'events_all': events_all,
            'patents_all': patents_all,
            'tech_transfer_all': tech_transfer_all,
            'publications_all': publications_all,
            'conferences_all': conferences_all,
            'achievments_all': achievments_all,
            'consultancy_projects_all': consultancy_projects_all,
            'research_projects_all': research_projects_all,
            'appraisal_all': appraisal_all,
            'new_courses_offered_all': new_courses_offered_all,
            'new_courses_material_all': new_courses_material_all
        })
        return response
    except Exception as e:
            messages.error(request,e)    


def generate_appraisal_lists_director(request):
    """
        Generating JSON object to get data from the front-end for user
        with designation "Director".
    """
    try:
        response = {}
        review_apps_director = AppraisalRequest.objects.select_related('appraisal').filter(director = request.user).filter(status_director = 'pending').exclude(status_hod = 'pending').order_by('-request_timestamp')
        reviewed_apps_director = AppraisalRequest.objects.select_related('appraisal').filter(director = request.user).exclude(status_director = 'pending').order_by('-request_timestamp')
        course_objects_all = Curriculum_Instructor.objects.all()
        consultancy_projects_all = emp_consultancy_projects.objects.all()
        research_projects_all = emp_research_projects.objects.all()
        thesis_all = emp_mtechphd_thesis.objects.all()
        events_all = emp_event_organized.objects.all()
        patents_all = emp_patents.objects.all()
        tech_transfer_all = emp_techtransfer.objects.all()
        publications_all = emp_published_books.objects.all()
        conferences_all = emp_confrence_organised.objects.all()
        achievments_all = emp_achievement.objects.all()
        appraisal_all = Appraisal.objects.select_related('applicant').all()
        new_courses_offered_all = NewCoursesOffered.objects.all()
        new_courses_material_all = NewCourseMaterial.objects.all()
        response.update({
            'director': True,
            'course_objects_all': course_objects_all,
            'review_apps_director': review_apps_director,
            'reviewed_apps_director': reviewed_apps_director,
            'thesis_all': thesis_all,
            'events_all': events_all,
            'patents_all': patents_all,
            'tech_transfer_all': tech_transfer_all,
            'publications_all': publications_all,
            'conferences_all': conferences_all,
            'achievments_all': achievments_all,
            'consultancy_projects_all': consultancy_projects_all,
            'research_projects_all': research_projects_all,
            'appraisal_all': appraisal_all,
            'new_courses_offered_all': new_courses_offered_all,
            'new_courses_material_all': new_courses_material_all
        })
        return response
    except Exception as e:
            messages.error(request,e)


def generate_appraisal_lists_admin(request):
    """
        Generating JSON object to get data from the front-end for user
        with designation "Admin".
    """
    try:
        response = {}
        appraisal_requests = AppraisalRequest.objects.exclude(status_director = 'pending').exclude(status_hod = 'pending')
        course_objects_all = Curriculum_Instructor.objects.all()
        consultancy_projects_all = emp_consultancy_projects.objects.all()
        research_projects_all = emp_research_projects.objects.all()
        thesis_all = emp_mtechphd_thesis.objects.all()
        events_all = emp_event_organized.objects.all()
        patents_all = emp_patents.objects.all()
        tech_transfer_all = emp_techtransfer.objects.all()
        publications_all = emp_published_books.objects.all()
        conferences_all = emp_confrence_organised.objects.all()
        achievments_all = emp_achievement.objects.all()
        appraisal_all = Appraisal.objects.select_related('applicant').all()
        new_courses_offered_all = NewCoursesOffered.objects.all()
        new_courses_material_all = NewCourseMaterial.objects.all()
        
        response.update({
            'admin': True,
            'course_objects_all': course_objects_all,
            'appraisal_requests': appraisal_requests,
            'thesis_all': thesis_all,
            'events_all': events_all,
            'patents_all': patents_all,
            'tech_transfer_all': tech_transfer_all,
            'publications_all': publications_all,
            'conferences_all': conferences_all,
            'achievments_all': achievments_all,
            'consultancy_projects_all': consultancy_projects_all,
            'research_projects_all': research_projects_all,
            'appraisal_all': appraisal_all,
            'new_courses_offered_all': new_courses_offered_all,
            'new_courses_material_all': new_courses_material_all
        })
        return response
    except Exception as e:
            messages.error(request,e)


def update_appraisal_lists(request):
    try:
        start = request.POST.get('start_date')
        start_date = date.fromisoformat(start)
        end = request.POST.get('end_date')
        end_date = date.fromisoformat(end)
        
        response = {}
        achievments = emp_achievement.objects.filter(user = request.user)
        achievments_date = []
        for obj in achievments:
            if(obj.achievment_date is not None):
                if(start_date <= obj.achievment_date <= end_date):
                    achievments_date.append(obj)
        consultancy_projects = emp_consultancy_projects.objects.filter(user = request.user)
        consultancy_projects_date = []
        for obj in consultancy_projects:
            if((obj.start_date is not None) and (obj.end_date is not None)):
                if(start_date <= obj.start_date <= end_date or start_date <= obj.end_date <= end_date):
                    consultancy_projects_date.append(obj)
        research_projects = emp_research_projects.objects.filter(user = request.user)
        research_projects_date = []
        for obj in research_projects:
            if((obj.start_date is not None) and (obj.finish_date is not None) and (obj.date_submission is not None)):
                if(start_date <= obj.start_date <= end_date or start_date <= obj.finish_date <= end_date or start_date <= obj.date_submission <= end_date):
                    research_projects_date.append(obj)
        thesis = emp_mtechphd_thesis.objects.filter(user = request.user)
        thesis_date = []
        for obj in thesis:
            if((obj.start_date is not None) and (obj.end_date is not None)):
                if(start_date <= obj.start_date <= end_date or start_date <= obj.end_date <= end_date):
                    thesis_date.append(obj)
        patents = emp_patents.objects.filter(user = request.user)
        patents_date = []
        for obj in patents:
            if((obj.start_date is not None) and (obj.end_date is not None)):
                if(start_date <= obj.start_date <= end_date or start_date <= obj.end_date <= end_date):
                    patents_date.append(obj)
        tech_transfer = emp_techtransfer.objects.filter(user = request.user)
        tech_transfer_date = []
        for obj in tech_transfer:
            if((obj.start_date is not None) and (obj.end_date is not None)):
                if(start_date <= obj.start_date <= end_date or start_date <= obj.end_date <= end_date):
                    tech_transfer_date.append(obj)
        publications = emp_published_books.objects.filter(user = request.user)
        publications_date = []
        for obj in publications:
            if(obj.publication_date is not None):
                if(start_date <= obj.publication_date <= end_date):
                    publications_date.append(obj)
        conferences = emp_confrence_organised.objects.filter(user = request.user)
        conferences_date = []
        for obj in conferences:
            if((obj.start_date is not None) and (obj.end_date is not None)):
                if(start_date <= obj.start_date <= end_date or start_date <= obj.end_date <= end_date):
                    conferences_date.append(obj)
        
        events = emp_event_organized.objects.filter(user = request.user)
        events_date = []
        for obj in events:
            if((obj.start_date is not None) and (obj.end_date is not None)):
                if(start_date <= obj.start_date <= end_date or start_date <= obj.end_date <= end_date):
                    events_date.append(obj)
        response.update({
                'achievments': achievments_date,
                'consultancy_projects': consultancy_projects_date,
                'research_projects': research_projects_date,
                'thesis': thesis_date,
                'patents': patents_date,
                'tech_transfer': tech_transfer_date,
                'publications': publications_date,
                'conferences': conferences_date,
                'events': events_date,
                'start_date': start_date,
                'end_date': end_date
        })
        return response
    except Exception as e:
            messages.error(request,e)
