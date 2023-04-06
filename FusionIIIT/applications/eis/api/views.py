from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes,authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from applications.eis.models import *
from applications.eis.views import countries
from applications.globals.models import HoldsDesignation

from . import serializers


User = get_user_model()

@api_view(['GET'])
def profile(request, username=None):
    user = get_object_or_404(User, username=username) if username else request.user
    user_detail = serializers.UserSerializer(user).data
    extra_info = serializers.ExtraInfoSerializer(user.extrainfo).data
    if extra_info['user_type'] != 'faculty':
        return Response(data={'message':'Not faculty'}, status=status.HTTP_400_BAD_REQUEST)

    pf = extra_info['id']
    journal = serializers.EmpResearchPapersSerializer(emp_research_papers.objects.filter(pf_no=pf, rtype='Journal').order_by('-year'),many=True).data
    conference = serializers.EmpResearchPapersSerializer(emp_research_papers.objects.filter(pf_no=pf, rtype='Conference').order_by('-year'),many=True).data
    books = serializers.EmpPublishedBooksSerializer(emp_published_books.objects.filter(pf_no=pf).order_by('-pyear'),many=True).data
    projects = serializers.EmpResearchProjectsSerializer(emp_research_projects.objects.filter(pf_no=pf).order_by('-start_date'),many=True).data
    consultancy = serializers.EmpConsultancyProjectsSerializer(emp_consultancy_projects.objects.filter(pf_no=pf).order_by('-date_entry'),many=True).data
    patents = serializers.EmpPatentsSerializer(emp_patents.objects.filter(pf_no=pf).order_by('-date_entry'),many=True).data
    techtransfers = serializers.EmpTechTransferSerializer(emp_techtransfer.objects.filter(pf_no=pf).order_by('-date_entry'),many=True).data
    mtechs = serializers.EmpMtechPhdThesisSerializer(emp_mtechphd_thesis.objects.filter(pf_no=pf, degree_type=1).order_by('-date_entry'),many=True).data
    phds = serializers.EmpMtechPhdThesisSerializer(emp_mtechphd_thesis.objects.filter(pf_no=pf, degree_type=2).order_by('-date_entry'),many=True).data
    fvisits = serializers.EmpVisitsSerializer(emp_visits.objects.filter(pf_no=pf, v_type=2).order_by('-entry_date'),many=True).data
    ivisits = serializers.EmpVisitsSerializer(emp_visits.objects.filter(pf_no=pf, v_type=1).order_by('-entry_date'),many=True).data
    for fvisit in fvisits:
        fvisit['countryfull'] = countries[fvisit['country']]
    consymps = serializers.EmpConfrenceOrganisedSerializer(emp_confrence_organised.objects.filter(pf_no=pf).order_by('-date_entry'),many=True).data
    awards = serializers.EmpAchievementSerializer(emp_achievement.objects.filter(pf_no=pf).order_by('-date_entry'),many=True).data
    talks = serializers.EmpExpertLecturesSerializer(emp_expert_lectures.objects.filter(pf_no=pf).order_by('-date_entry'),many=True).data
    chairs = serializers.EmpSessionChairSerializer(emp_session_chair.objects.filter(pf_no=pf).order_by('-date_entry'),many=True).data
    keynotes = serializers.EmpKeynoteAddressSerializer(emp_keynote_address.objects.filter(pf_no=pf).order_by('-date_entry'),many=True).data
    events = serializers.EmpEventOrganizedSerializer(emp_event_organized.objects.filter(pf_no=pf).order_by('-start_date'),many=True).data
    year_range = []
    for r in range(1995, (datetime.datetime.now().year + 1)):
        year_range.append(r)
    try:
        faculty_about = serializers.FacultyAboutSerializer(user.faculty_about).data
    except:
        faculty_about = None

    holds_desig = user.current_designation.all()
    flag_rspc = 0
    for i in holds_desig:
        if(str(i.designation)=='Dean (RSPC)'):
            flag_rspc = 1

    designation = serializers.HoldsDesignationSerializer(holds_desig,many=True).data

    resp = {'user' : user_detail,
            'profile' : extra_info,
            'designation' : designation,
            'pf' : pf,
            'flag_rspc' : flag_rspc,
            'journal' : journal,
            'conference' : conference,
            'books' : books,
            'projects' : projects,
            'consultancy' : consultancy,
            'patents' : patents,
            'techtransfers' : techtransfers,
            'mtechs' : mtechs,
            'phds' : phds,
            'fvisits' : fvisits,
            'ivisits' : ivisits,
            'consymps' : consymps,
            'awards' : awards,
            'talks' : talks,
            'chairs' : chairs,
            'keynotes' : keynotes,
            'events' : events,
            'year_range' : year_range,
            'faculty_about' : faculty_about
    }
    return Response(data=resp, status=status.HTTP_200_OK)
