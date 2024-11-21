# from django.contrib.auth import get_user_model
# from django.shortcuts import get_object_or_404

# from rest_framework.permissions import IsAuthenticated
# from rest_framework.authentication import TokenAuthentication
# from rest_framework import status
# from rest_framework.decorators import api_view, permission_classes,authentication_classes
# from rest_framework.permissions import AllowAny
# from rest_framework.response import Response

# from applications.eis.models import *
# from applications.eis.views import countries
# from applications.globals.models import HoldsDesignation

# from . import serializers


# User = get_user_model()

# @api_view(['GET'])
# def profile(request, username=None):
#     user = get_object_or_404(User, username=username) if username else request.user
#     user_detail = serializers.UserSerializer(user).data
#     extra_info = serializers.ExtraInfoSerializer(user.extrainfo).data
#     if extra_info['user_type'] != 'faculty':
#         return Response(data={'message':'Not faculty'}, status=status.HTTP_400_BAD_REQUEST)

#     pf = extra_info['id']
#     journal = serializers.EmpResearchPapersSerializer(emp_research_papers.objects.filter(pf_no=pf, rtype='Journal').order_by('-year'),many=True).data
#     conference = serializers.EmpResearchPapersSerializer(emp_research_papers.objects.filter(pf_no=pf, rtype='Conference').order_by('-year'),many=True).data
#     books = serializers.EmpPublishedBooksSerializer(emp_published_books.objects.filter(pf_no=pf).order_by('-pyear'),many=True).data
#     projects = serializers.EmpResearchProjectsSerializer(emp_research_projects.objects.filter(pf_no=pf).order_by('-start_date'),many=True).data
#     consultancy = serializers.EmpConsultancyProjectsSerializer(emp_consultancy_projects.objects.filter(pf_no=pf).order_by('-date_entry'),many=True).data
#     patents = serializers.EmpPatentsSerializer(emp_patents.objects.filter(pf_no=pf).order_by('-date_entry'),many=True).data
#     techtransfers = serializers.EmpTechTransferSerializer(emp_techtransfer.objects.filter(pf_no=pf).order_by('-date_entry'),many=True).data
#     mtechs = serializers.EmpMtechPhdThesisSerializer(emp_mtechphd_thesis.objects.filter(pf_no=pf, degree_type=1).order_by('-date_entry'),many=True).data
#     phds = serializers.EmpMtechPhdThesisSerializer(emp_mtechphd_thesis.objects.filter(pf_no=pf, degree_type=2).order_by('-date_entry'),many=True).data
#     fvisits = serializers.EmpVisitsSerializer(emp_visits.objects.filter(pf_no=pf, v_type=2).order_by('-entry_date'),many=True).data
#     ivisits = serializers.EmpVisitsSerializer(emp_visits.objects.filter(pf_no=pf, v_type=1).order_by('-entry_date'),many=True).data
#     for fvisit in fvisits:
#         fvisit['countryfull'] = countries[fvisit['country']]
#     consymps = serializers.EmpConfrenceOrganisedSerializer(emp_confrence_organised.objects.filter(pf_no=pf).order_by('-date_entry'),many=True).data
#     awards = serializers.EmpAchievementSerializer(emp_achievement.objects.filter(pf_no=pf).order_by('-date_entry'),many=True).data
#     talks = serializers.EmpExpertLecturesSerializer(emp_expert_lectures.objects.filter(pf_no=pf).order_by('-date_entry'),many=True).data
#     chairs = serializers.EmpSessionChairSerializer(emp_session_chair.objects.filter(pf_no=pf).order_by('-date_entry'),many=True).data
#     keynotes = serializers.EmpKeynoteAddressSerializer(emp_keynote_address.objects.filter(pf_no=pf).order_by('-date_entry'),many=True).data
#     events = serializers.EmpEventOrganizedSerializer(emp_event_organized.objects.filter(pf_no=pf).order_by('-start_date'),many=True).data
#     year_range = []
#     for r in range(1995, (datetime.datetime.now().year + 1)):
#         year_range.append(r)
#     try:
#         faculty_about = serializers.FacultyAboutSerializer(user.faculty_about).data
#     except:
#         faculty_about = None

#     holds_desig = user.current_designation.all()
#     flag_rspc = 0
#     for i in holds_desig:
#         if(str(i.designation)=='Dean (RSPC)'):
#             flag_rspc = 1

#     designation = serializers.HoldsDesignationSerializer(holds_desig,many=True).data

#     resp = {'user' : user_detail,
#             'profile' : extra_info,
#             'designation' : designation,
#             'pf' : pf,
#             'flag_rspc' : flag_rspc,
#             'journal' : journal,
#             'conference' : conference,
#             'books' : books,
#             'projects' : projects,
#             'consultancy' : consultancy,
#             'patents' : patents,
#             'techtransfers' : techtransfers,
#             'mtechs' : mtechs,
#             'phds' : phds,
#             'fvisits' : fvisits,
#             'ivisits' : ivisits,
#             'consymps' : consymps,
#             'awards' : awards,
#             'talks' : talks,
#             'chairs' : chairs,
#             'keynotes' : keynotes,
#             'events' : events,
#             'year_range' : year_range,
#             'faculty_about' : faculty_about
#     }
#     return Response(data=resp, status=status.HTTP_200_OK)


import csv
from html import escape
from io import BytesIO

from django.contrib.auth.models import User
from django.http import FileResponse, HttpResponse, HttpResponseRedirect
from django.shortcuts import (get_object_or_404, redirect, render,
                              render)
from django.template import loader
from django.template.loader import get_template
from django.urls import reverse_lazy
from django.views import generic
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from xhtml2pdf import pisa

from .. import admin
from django.http import JsonResponse
from django.core.serializers import serialize
from ..forms import *
from ..models import *
from django.core.files.storage import FileSystemStorage
import logging
import json
from django.views.decorators.csrf import csrf_exempt
import google.generativeai as genai
import os
import pdfkit
import tempfile

countries = {
        'AF': 'Afghanistan',
        'AX': 'Aland Islands',
        'AL': 'Albania',
        'DZ': 'Algeria',
        'AS': 'American Samoa',
        'AD': 'Andorra',
        'AO': 'Angola',
        'AI': 'Anguilla',
        'AQ': 'Antarctica',
        'AG': 'Antigua And Barbuda',
        'AR': 'Argentina',
        'AM': 'Armenia',
        'AW': 'Aruba',
        'AU': 'Australia',
        'AT': 'Austria',
        'AZ': 'Azerbaijan',
        'BS': 'Bahamas',
        'BH': 'Bahrain',
        'BD': 'Bangladesh',
        'BB': 'Barbados',
        'BY': 'Belarus',
        'BE': 'Belgium',
        'BZ': 'Belize',
        'BJ': 'Benin',
        'BM': 'Bermuda',
        'BT': 'Bhutan',
        'BO': 'Bolivia',
        'BA': 'Bosnia And Herzegovina',
        'BW': 'Botswana',
        'BV': 'Bouvet Island',
        'BR': 'Brazil',
        'IO': 'British Indian Ocean Territory',
        'BN': 'Brunei Darussalam',
        'BG': 'Bulgaria',
        'BF': 'Burkina Faso',
        'BI': 'Burundi',
        'KH': 'Cambodia',
        'CM': 'Cameroon',
        'CA': 'Canada',
        'CV': 'Cape Verde',
        'KY': 'Cayman Islands',
        'CF': 'Central African Republic',
        'TD': 'Chad',
        'CL': 'Chile',
        'CN': 'China',
        'CX': 'Christmas Island',
        'CC': 'Cocos (Keeling) Islands',
        'CO': 'Colombia',
        'KM': 'Comoros',
        'CG': 'Congo',
        'CD': 'Congo, Democratic Republic',
        'CK': 'Cook Islands',
        'CR': 'Costa Rica',
        'CI': 'Cote D\'Ivoire',
        'HR': 'Croatia',
        'CU': 'Cuba',
        'CY': 'Cyprus',
        'CZ': 'Czech Republic',
        'DK': 'Denmark',
        'DJ': 'Djibouti',
        'DM': 'Dominica',
        'DO': 'Dominican Republic',
        'EC': 'Ecuador',
        'EG': 'Egypt',
        'SV': 'El Salvador',
        'GQ': 'Equatorial Guinea',
        'ER': 'Eritrea',
        'EE': 'Estonia',
        'ET': 'Ethiopia',
        'FK': 'Falkland Islands (Malvinas)',
        'FO': 'Faroe Islands',
        'FJ': 'Fiji',
        'FI': 'Finland',
        'FR': 'France',
        'GF': 'French Guiana',
        'PF': 'French Polynesia',
        'TF': 'French Southern Territories',
        'GA': 'Gabon',
        'GM': 'Gambia',
        'GE': 'Georgia',
        'DE': 'Germany',
        'GH': 'Ghana',
        'GI': 'Gibraltar',
        'GR': 'Greece',
        'GL': 'Greenland',
        'GD': 'Grenada',
        'GP': 'Guadeloupe',
        'GU': 'Guam',
        'GT': 'Guatemala',
        'GG': 'Guernsey',
        'GN': 'Guinea',
        'GW': 'Guinea-Bissau',
        'GY': 'Guyana',
        'HT': 'Haiti',
        'HM': 'Heard Island & Mcdonald Islands',
        'VA': 'Holy See (Vatican City State)',
        'HN': 'Honduras',
        'HK': 'Hong Kong',
        'HU': 'Hungary',
        'IS': 'Iceland',
        'IN': 'India',
        'ID': 'Indonesia',
        'IR': 'Iran, Islamic Republic Of',
        'IQ': 'Iraq',
        'IE': 'Ireland',
        'IM': 'Isle Of Man',
        'IL': 'Israel',
        'IT': 'Italy',
        'JM': 'Jamaica',
        'JP': 'Japan',
        'JE': 'Jersey',
        'JO': 'Jordan',
        'KZ': 'Kazakhstan',
        'KE': 'Kenya',
        'KI': 'Kiribati',
        'KR': 'Korea',
        'KW': 'Kuwait',
        'KG': 'Kyrgyzstan',
        'LA': 'Lao People\'s Democratic Republic',
        'LV': 'Latvia',
        'LB': 'Lebanon',
        'LS': 'Lesotho',
        'LR': 'Liberia',
        'LY': 'Libyan Arab Jamahiriya',
        'LI': 'Liechtenstein',
        'LT': 'Lithuania',
        'LU': 'Luxembourg',
        'MO': 'Macao',
        'MK': 'Macedonia',
        'MG': 'Madagascar',
        'MW': 'Malawi',
        'MY': 'Malaysia',
        'MV': 'Maldives',
        'ML': 'Mali',
        'MT': 'Malta',
        'MH': 'Marshall Islands',
        'MQ': 'Martinique',
        'MR': 'Mauritania',
        'MU': 'Mauritius',
        'YT': 'Mayotte',
        'MX': 'Mexico',
        'FM': 'Micronesia, Federated States Of',
        'MD': 'Moldova',
        'MC': 'Monaco',
        'MN': 'Mongolia',
        'ME': 'Montenegro',
        'MS': 'Montserrat',
        'MA': 'Morocco',
        'MZ': 'Mozambique',
        'MM': 'Myanmar',
        'NA': 'Namibia',
        'NR': 'Nauru',
        'NP': 'Nepal',
        'NL': 'Netherlands',
        'AN': 'Netherlands Antilles',
        'NC': 'New Caledonia',
        'NZ': 'New Zealand',
        'NI': 'Nicaragua',
        'NE': 'Niger',
        'NG': 'Nigeria',
        'NU': 'Niue',
        'NF': 'Norfolk Island',
        'MP': 'Northern Mariana Islands',
        'NO': 'Norway',
        'OM': 'Oman',
        'PK': 'Pakistan',
        'PW': 'Palau',
        'PS': 'Palestinian Territory, Occupied',
        'PA': 'Panama',
        'PG': 'Papua New Guinea',
        'PY': 'Paraguay',
        'PE': 'Peru',
        'PH': 'Philippines',
        'PN': 'Pitcairn',
        'PL': 'Poland',
        'PT': 'Portugal',
        'PR': 'Puerto Rico',
        'QA': 'Qatar',
        'RE': 'Reunion',
        'RO': 'Romania',
        'RU': 'Russian Federation',
        'RW': 'Rwanda',
        'BL': 'Saint Barthelemy',
        'SH': 'Saint Helena',
        'KN': 'Saint Kitts And Nevis',
        'LC': 'Saint Lucia',
        'MF': 'Saint Martin',
        'PM': 'Saint Pierre And Miquelon',
        'VC': 'Saint Vincent And Grenadines',
        'WS': 'Samoa',
        'SM': 'San Marino',
        'ST': 'Sao Tome And Principe',
        'SA': 'Saudi Arabia',
        'SN': 'Senegal',
        'RS': 'Serbia',
        'SC': 'Seychelles',
        'SL': 'Sierra Leone',
        'SG': 'Singapore',
        'SK': 'Slovakia',
        'SI': 'Slovenia',
        'SB': 'Solomon Islands',
        'SO': 'Somalia',
        'ZA': 'South Africa',
        'GS': 'South Georgia And Sandwich Isl.',
        'ES': 'Spain',
        'LK': 'Sri Lanka',
        'SD': 'Sudan',
        'SR': 'Suriname',
        'SJ': 'Svalbard And Jan Mayen',
        'SZ': 'Swaziland',
        'SE': 'Sweden',
        'CH': 'Switzerland',
        'SY': 'Syrian Arab Republic',
        'TW': 'Taiwan',
        'TJ': 'Tajikistan',
        'TZ': 'Tanzania',
        'TH': 'Thailand',
        'TL': 'Timor-Leste',
        'TG': 'Togo',
        'TK': 'Tokelau',
        'TO': 'Tonga',
        'TT': 'Trinidad And Tobago',
        'TN': 'Tunisia',
        'TR': 'Turkey',
        'TM': 'Turkmenistan',
        'TC': 'Turks And Caicos Islands',
        'TV': 'Tuvalu',
        'UG': 'Uganda',
        'UA': 'Ukraine',
        'AE': 'United Arab Emirates',
        'GB': 'United Kingdom',
        'US': 'United States',
        'UM': 'United States Outlying Islands',
        'UY': 'Uruguay',
        'UZ': 'Uzbekistan',
        'VU': 'Vanuatu',
        'VE': 'Venezuela',
        'VN': 'Viet Nam',
        'VG': 'Virgin Islands, British',
        'VI': 'Virgin Islands, U.S.',
        'WF': 'Wallis And Futuna',
        'EH': 'Western Sahara',
        'YE': 'Yemen',
        'ZM': 'Zambia',
        'ZW': 'Zimbabwe',
        'KP': 'Korea (Democratic Peoples Republic of)',
    }

# Create your views here

def index(request):
    return HttpResponse("Hello, world. You're at the FPF index.")

def view_all_extra_infos(request):
    
    # Retrieve all ExtraInfo objects
    """
    View to retrieve all ExtraInfo objects, and return them as a JSON response.

    The response will contain a list of dictionaries, each containing the following
    information about an ExtraInfo object:

    - id: The ID of the ExtraInfo object
    - user: The username of the User object associated with the ExtraInfo
    - title: The title of the ExtraInfo object
    - sex: The sex of the ExtraInfo object
    - date_of_birth: The date of birth of the ExtraInfo object as a string
    - user_status: The status of the ExtraInfo object
    - address: The address of the ExtraInfo object
    - phone_no: The phone number of the ExtraInfo object
    - user_type: The type of the ExtraInfo object
    - department: The name of the DepartmentInfo object associated with the ExtraInfo
    - profile_picture: The URL of the profile picture of the ExtraInfo object
    - about_me: The about me of the ExtraInfo object
    - date_modified: The date modified of the ExtraInfo object as a string
    - age: The age of the ExtraInfo object

    The response will be a JSON object with a single key, 'extra_info_list', which
    contains the list of dictionaries.
    """

    extra_infos = ExtraInfo.objects.all()

    # Serialize the queryset into a list of dictionaries
    extra_info_list = [
        {
            'id': info.id,
            'user': info.user.username,
            'title': info.title,
            'sex': info.sex,
            'date_of_birth': info.date_of_birth.isoformat(),  # Convert date to string
            'user_status': info.user_status,
            'address': info.address,
            'phone_no': info.phone_no,
            'user_type': info.user_type,
            'department': info.department.name if info.department else None,  # Assuming DepartmentInfo has a name field
            'profile_picture': info.profile_picture.url if info.profile_picture else None,
            'about_me': info.about_me,
            'date_modified': info.date_modified.isoformat() if info.date_modified else None,
            'age': info.age  # Custom property to get the user's age
        }
        for info in extra_infos
    ]

    # Return the data as a JSON response
    return JsonResponse(extra_info_list, safe=False)

# Main profile landing view
@csrf_exempt
def profile(request, username=None):

    """
    Main profile landing view that retrieves and returns detailed information
    about a faculty member based on their username. The information includes
    personal data, research activities, project management records, and designation
    details.

    Args:
        request (HttpRequest): The request object.
        username (str, optional): The username of the faculty member. Defaults to None.

    Returns:
        JsonResponse: A JSON response containing user information, research data, 
        project details, personal information, and designations.
    """
    
    if request.method == 'POST':
        user = get_object_or_404(User, username=request.POST.get('username'))
    else:
        if username:
            pass
        else:
            user = get_object_or_404(User, username=request.GET.get('username'))

    extra_info = get_object_or_404(ExtraInfo, user=user)

    pf = extra_info.user_id

    # Forms and project management data
    project_r = Project_Registration.objects.filter(PI_id=pf).order_by('PI_id__user')
    project_ext = Project_Extension.objects.filter(project_id__PI_id=pf).order_by('project_id__PI_id__user')
    project_closure = Project_Closure.objects.filter(project_id__PI_id=pf).order_by('project_id__PI_id__user')
    project_reall = Project_Reallocation.objects.filter(project_id__PI_id=pf).order_by('project_id__PI_id__user')

    # Research data
    journal = emp_research_papers.objects.filter(pf_no=pf, rtype='Journal').order_by('-year')
    conference = emp_research_papers.objects.filter(pf_no=pf, rtype='Conference').order_by('-year')
    books = emp_published_books.objects.filter(pf_no=pf).order_by('-pyear')
    projects = emp_research_projects.objects.filter(pf_no=pf).order_by('-start_date')
    consultancy = emp_consultancy_projects.objects.filter(pf_no=pf).order_by('-date_entry')
    patents = emp_patents.objects.filter(pf_no=pf).order_by('-date_entry')
    techtransfers = emp_techtransfer.objects.filter(pf_no=pf).order_by('-date_entry')
    mtechs = emp_mtechphd_thesis.objects.filter(pf_no=pf, degree_type=1).order_by('-date_entry')
    phds = emp_mtechphd_thesis.objects.filter(pf_no=pf, degree_type=2).order_by('-date_entry')
    fvisits = emp_visits.objects.filter(pf_no=pf, v_type=2).order_by('-entry_date')
    ivisits = emp_visits.objects.filter(pf_no=pf, v_type=1).order_by('-entry_date')
    consymps = emp_confrence_organised.objects.filter(pf_no=pf).order_by('-date_entry')
    awards = emp_achievement.objects.filter(pf_no=pf).order_by('-date_entry')
    talks = emp_expert_lectures.objects.filter(pf_no=pf).order_by('-date_entry')
    chairs = emp_session_chair.objects.filter(pf_no=pf).order_by('-date_entry')
    keynotes = emp_keynote_address.objects.filter(pf_no=pf).order_by('-date_entry')
    events = emp_event_organized.objects.filter(pf_no=pf).order_by('-start_date')

    # Get year range
    y = list(range(1995, datetime.datetime.now().year + 1))

    # Personal information
    try:
        pers = get_object_or_404(faculty_about, user_id=pf)
    except:
        pers = None

    # Designations
    a1 = HoldsDesignation.objects.select_related('user', 'working', 'designation').filter(working=user)
    flag_rspc = 0
    for i in a1:
        if str(i.designation) == 'Dean (RSPC)':
            flag_rspc = 1

    designations = [str(i.designation) for i in a1]

    # Prepare data to be returned in JSON format
    data = {
        'user': {
            'username': user.username,
            'email': user.email,
        },
        'designations': designations,
        'pf': pf,
        'flag_rspc': flag_rspc,
        'research': {
            'journal': list(journal.values()),  # Convert queryset to list of dictionaries
            'conference': list(conference.values()),
            'books': list(books.values()),
            'projects': list(projects.values()),
            'consultancy': list(consultancy.values()),
            'patents': list(patents.values()),
            'techtransfers': list(techtransfers.values()),
            'mtechs': list(mtechs.values()),
            'phds': list(phds.values()),
            'fvisits': list(fvisits.values()),
            'ivisits': list(ivisits.values()),
            'consymps': list(consymps.values()),
            'awards': list(awards.values()),
            'talks': list(talks.values()),
            'chairs': list(chairs.values()),
            'keynotes': list(keynotes.values()),
            'events': list(events.values()),
        },
        'year_range': y,
        'personal_info': {
            'faculty_about': pers.about if pers else None,
            'date_of_joining': pers.doj if pers else None,
            'contact': pers.contact if pers else None,
            'interest': pers.interest if pers else None,
            'education': pers.education if pers else None,
            'linkedin': pers.linkedin if pers else None,
            'github': pers.github if pers else None
        },
        'projects': {
            'registrations': list(project_r.values()),
            'extensions': list(project_ext.values()),
            'closures': list(project_closure.values()),
            'reallocations': list(project_reall.values()),
        },
    }

    # Return data as JSON response
    return JsonResponse(data, safe=False)

@csrf_exempt
def generate_report(request, username=None):

    """Generate a PDF report for a given faculty member based on their research data and personal information.

    Args:
        request (HttpRequest): The request object.
        username (str): The username of the faculty member.

    Returns:
        HttpResponse: The PDF report as a response."""
    
    if request.method == 'POST':
        user = get_object_or_404(User, username=request.POST.get('username'))
    else:
        return JsonResponse({'error': 'Only POST method is allowed.'}, status=405)

    extra_info = get_object_or_404(ExtraInfo, user=user)

    pf = extra_info.user_id

    # Forms and project management data
    project_r = Project_Registration.objects.filter(PI_id=pf).order_by('PI_id__user')
    project_ext = Project_Extension.objects.filter(project_id__PI_id=pf).order_by('project_id__PI_id__user')
    project_closure = Project_Closure.objects.filter(project_id__PI_id=pf).order_by('project_id__PI_id__user')
    project_reall = Project_Reallocation.objects.filter(project_id__PI_id=pf).order_by('project_id__PI_id__user')

    # Research data
    journal = emp_research_papers.objects.filter(pf_no=pf, rtype='Journal').order_by('-year')
    conference = emp_research_papers.objects.filter(pf_no=pf, rtype='Conference').order_by('-year')
    books = emp_published_books.objects.filter(pf_no=pf).order_by('-pyear')
    projects = emp_research_projects.objects.filter(pf_no=pf).order_by('-start_date')
    consultancy = emp_consultancy_projects.objects.filter(pf_no=pf).order_by('-date_entry')
    patents = emp_patents.objects.filter(pf_no=pf).order_by('-date_entry')
    techtransfers = emp_techtransfer.objects.filter(pf_no=pf).order_by('-date_entry')
    mtechs = emp_mtechphd_thesis.objects.filter(pf_no=pf, degree_type=1).order_by('-date_entry')
    phds = emp_mtechphd_thesis.objects.filter(pf_no=pf, degree_type=2).order_by('-date_entry')
    fvisits = emp_visits.objects.filter(pf_no=pf, v_type=2).order_by('-entry_date')
    ivisits = emp_visits.objects.filter(pf_no=pf, v_type=1).order_by('-entry_date')
    consymps = emp_confrence_organised.objects.filter(pf_no=pf).order_by('-date_entry')
    awards = emp_achievement.objects.filter(pf_no=pf).order_by('-date_entry')
    talks = emp_expert_lectures.objects.filter(pf_no=pf).order_by('-date_entry')
    chairs = emp_session_chair.objects.filter(pf_no=pf).order_by('-date_entry')
    keynotes = emp_keynote_address.objects.filter(pf_no=pf).order_by('-date_entry')
    events = emp_event_organized.objects.filter(pf_no=pf).order_by('-start_date')

    # Get year range
    y = list(range(1995, datetime.datetime.now().year + 1))

    # Personal information
    try:
        pers = get_object_or_404(faculty_about, user_id=pf)
    except:
        pers = None

    # Designations
    a1 = HoldsDesignation.objects.select_related('user', 'working', 'designation').filter(working=user)
    flag_rspc = 0
    for i in a1:
        if str(i.designation) == 'Dean (RSPC)':
            flag_rspc = 1

    designations = [str(i.designation) for i in a1]

    data = {
        'user': {
            'username': user.username,
            'email': user.email,
        },
        'designations': designations,
        'pf': pf,
        'flag_rspc': flag_rspc,
        'research': {
            'journal': list(journal.values()),  # Convert queryset to list of dictionaries
            'conference': list(conference.values()),
            'books': list(books.values()),
            'projects': list(projects.values()),
            'consultancy': list(consultancy.values()),
            'patents': list(patents.values()),
            'techtransfers': list(techtransfers.values()),
            'mtechs': list(mtechs.values()),
            'phds': list(phds.values()),
            'fvisits': list(fvisits.values()),
            'ivisits': list(ivisits.values()),
            'consymps': list(consymps.values()),
            'awards': list(awards.values()),
            'talks': list(talks.values()),
            'chairs': list(chairs.values()),
            'keynotes': list(keynotes.values()),
            'events': list(events.values()),
        },
        'year_range': y,
        'personal_info': {
            'faculty_about': pers.about if pers else None,
            'date_of_joining': pers.doj if pers else None,
            'contact': pers.contact if pers else None,
            'interest': pers.interest if pers else None,
            'education': pers.education if pers else None,
            'linkedin': pers.linkedin if pers else None,
            'github': pers.github if pers else None
        },
        'projects': {
            'registrations': list(project_r.values()),
            'extensions': list(project_ext.values()),
            'closures': list(project_closure.values()),
            'reallocations': list(project_reall.values()),
        },
    }

    # Generate HTML content using Gemini API
    model = genai.GenerativeModel("gemini-1.5-flash")
    json_input = f"Generate an HTML report for the following data: {data}"
    response = model.generate_content(json_input)
    html_content = response.text.strip("```html").strip("```")

    # Convert HTML to PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        pdfkit.from_string(html_content, temp_pdf.name)
        temp_pdf.seek(0)
        pdf_file_path = temp_pdf.name

    # Send the PDF as a response
    return FileResponse(open(pdf_file_path, 'rb'), content_type='application/pdf', as_attachment=True, filename="report.pdf")

# Dean RSPC Profile
@csrf_exempt
def rspc_profile(request):
    """
    Return a JSON response with the research data and personal information of the
    Dean RSPC profile.

    The research data includes the following elements:

    - Journal and conference papers
    - Books
    - Projects
    - Consultancy projects
    - Patents
    - Technology transfers
    - M.Tech and Ph.D theses supervised
    - Foreign and Indian visits
    - Conferences organized
    - Awards received
    - Talks given
    - Sessions chaired
    - Keynote addresses given
    - Events organized

    The personal information includes the following:

    - Faculty about
    - Date of joining
    - Contact information
    - Interests
    - Education
    - LinkedIn profile
    - GitHub profile

    The year range is also included in the response.

    The response is sent as a JSON object with the following keys:

    - user: a dictionary with the username and email of the user
    - desig: a list of strings representing the designations of the user
    - pf: the pf number of the user
    - research: a dictionary with the research data
    - year_range: a list of integers representing the year range
    - personal_info: a dictionary with the personal information of the user

    The research data is organized as follows:

    - Journal and conference papers are organized by year and month
    - Books are organized by year and authors
    - Projects are organized by start date
    - Consultancy projects are organized by start date
    - Patents are organized by year and month
    - Technology transfers are organized by date entry
    - M.Tech and Ph.D theses are organized by year and month
    - Foreign and Indian visits are organized by start date
    - Conferences organized are organized by start date
    - Awards are organized by year and month
    - Talks are organized by year and month
    - Sessions chaired are organized by start date
    - Keynote addresses are organized by start date
    - Events organized are organized by start date

    The personal information is organized as follows:

    - Faculty about is a string
    - Date of joining is a date
    - Contact information is a string
    - Interests is a string
    - Education is a string
    - LinkedIn profile is a string
    - GitHub profile is a string

    The year range is a list of integers representing the year range.
    """
    
    if request.method == 'POST':
        user = get_object_or_404(faculty_about, user=request.user)
        pf = user.user

        # Retrieve data for various research elements
        journal = emp_research_papers.objects.filter(rtype='Journal').order_by('-year', '-a_month')
        conference = emp_research_papers.objects.filter(rtype='Conference').order_by('-year', '-a_month')
        books = emp_published_books.objects.all().order_by('-pyear', '-authors')
        projects = emp_research_projects.objects.all().order_by('-start_date')
        consultancy = emp_consultancy_projects.objects.all().order_by('-start_date')
        patents = emp_patents.objects.all().order_by('-p_year', '-a_month')
        techtransfers = emp_techtransfer.objects.all().order_by('-date_entry')
        mtechs = emp_mtechphd_thesis.objects.filter(degree_type=1).order_by('-s_year', '-a_month')
        phds = emp_mtechphd_thesis.objects.filter(degree_type=2).order_by('-s_year', '-a_month')
        fvisits = emp_visits.objects.filter(v_type=2).order_by('-start_date')
        ivisits = emp_visits.objects.filter(v_type=1).order_by('-start_date')

        # Add countryfull to foreign visits
        for fvisit in fvisits:
            fvisit.countryfull = countries[fvisit.country]  # assuming `countries` is a valid dictionary

        consymps = emp_confrence_organised.objects.all().order_by('-start_date')
        awards = emp_achievement.objects.all().order_by('-a_year', '-a_month')
        talks = emp_expert_lectures.objects.all().order_by('-l_year', '-a_month')
        chairs = emp_session_chair.objects.all().order_by('-start_date')
        keynotes = emp_keynote_address.objects.all().order_by('-start_date')
        events = emp_event_organized.objects.all().order_by('-start_date')

        # Get year range
        y = list(range(1995, datetime.datetime.now().year + 1))

        # Get personal info
        pers = get_object_or_404(faculty_about, user=request.user)

        # Designation
        design = HoldsDesignation.objects.select_related('user', 'working', 'designation').filter(working=request.user)
        desig = [str(i.designation) for i in design]

        # Prepare data to be returned in JSON format
        data = {
            'user': {
                'username': user.username,  # Assuming `user` has a `username` attribute
                'email': user.email,        # Assuming `user` has an `email` attribute
            },
            'desig': desig,
            'pf': pf,
            'research': {
                'journal': list(journal.values()),  # Converting QuerySets to a list of dictionaries
                'conference': list(conference.values()),
                'books': list(books.values()),
                'projects': list(projects.values()),
                'consultancy': list(consultancy.values()),
                'patents': list(patents.values()),
                'techtransfers': list(techtransfers.values()),
                'mtechs': list(mtechs.values()),
                'phds': list(phds.values()),
                'fvisits': list(fvisits.values('country', 'countryfull', 'start_date')),  # Example fields
                'ivisits': list(ivisits.values('country', 'start_date')),
                'consymps': list(consymps.values()),
                'awards': list(awards.values()),
                'talks': list(talks.values()),
                'chairs': list(chairs.values()),
                'keynotes': list(keynotes.values()),
                'events': list(events.values()),
            },
            'year_range': y,
            'personal_info': {
                'faculty_about': pers.details if pers else None  # Assuming `details` field exists
            }
        }

        # Return data as JSON response
        return JsonResponse(data, safe=False)
    else:
        return JsonResponse({"x" : "You are not authorized to hit this URL", "status" : 400})

# View for editing persnal Information
@csrf_exempt
def persinfo(request):
    """
    Update the personal information of a faculty member.

    This view handles POST requests to update various fields of the faculty
    member's profile, including contact information, about section, interests,
    education, and social media links.

    Args:
        request (HttpRequest): The request object containing user data.

    Returns:
        JsonResponse: A JSON response indicating the success or failure of the 
        update operation. A successful update returns a message confirming the 
        data update, while an unauthorized attempt returns an error message.
    """
    if request.method == 'POST':
        try:
            faculty = get_object_or_404(faculty_about, user_id = request.POST.get('user_id'))
            contact = request.POST['contact']
            faculty.contact = contact
            faculty.about = request.POST['about']
            faculty.interest = request.POST['interest']
            faculty.education = request.POST['education']

            faculty.linkedin = request.POST['linkedin']
            faculty.github = request.POST['github']

            faculty.save()
            return JsonResponse({'x' : 'Your data is updated '})
        except:
            return JsonResponse({'x' : 'You are not authorized to update '})


@csrf_exempt
def update_personal_info(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_id = data.get("user_id")
            
            # Fetch the faculty_about entry
            faculty = faculty_about.objects.get(user_id=user_id)
            
            # Update fields
            faculty.about = data.get("aboutMe", faculty.about)
            faculty.doj = data.get("dateOfJoining", faculty.doj)
            faculty.education = data.get("education", faculty.education)
            faculty.interest = data.get("interestAreas", faculty.interest)
            faculty.contact = data.get("contact", faculty.contact)
            faculty.github = data.get("github", faculty.github)
            faculty.linkedin = data.get("linkedIn", faculty.linkedin)
            
            faculty.save()
            
            return JsonResponse({"message": "Details updated successfully."}, status=200)
        except faculty_about.DoesNotExist:
            return JsonResponse({"error": "Faculty not found."}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Invalid request method."}, status=405)


# Views for deleting the EIS fields
@csrf_exempt
def achievementDelete(request):
    """
    Delete an achievement entry from the database.

    This view handles POST requests to delete a specific achievement
    identified by its primary key ('pk') sent in the request data.

    Args:
        request (HttpRequest): The request object containing the primary key
        of the achievement to be deleted.

    Returns:
        JsonResponse: A JSON response indicating the success or failure of
        the delete operation. If successful, returns a success message. If the
        achievement is not found, returns an error message. If the request
        method is not POST, returns an invalid request method error.
    """
    if request.method == 'POST':
        try:
            instance = emp_achievement.objects.get(pk=request.POST['pk'])
            instance.delete()
            return JsonResponse({'success': True}, status=200)
        except emp_achievement.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Achievement not found.'}, status=404)
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=400)

@csrf_exempt
def emp_confrence_organisedDelete(request):
    """
    Delete an emp_confrence_organised entry from the database.

    This view handles POST requests to delete a specific
    emp_confrence_organised identified by its primary key ('pk') sent in
    the request data.

    Args:
        request (HttpRequest): The request object containing the primary key
        of the emp_confrence_organised to be deleted.

    Returns:
        JsonResponse: A JSON response indicating the success of the delete
        operation. If successful, returns a success message. If the
        emp_confrence_organised is not found, returns an error message. If the
        request method is not POST, returns an invalid request method error.
    """
    instance = emp_confrence_organised.objects.get(pk=request.POST['pk'])
    instance.delete()
    return JsonResponse({'success': True})

@csrf_exempt
def emp_consymDelete(request):
    """
    Delete an emp_consym entry from the database.

    This view handles POST requests to delete a specific
    emp_consym identified by its primary key ('pk') sent in
    the request data.

    Args:
        request (HttpRequest): The request object containing the primary key
        of the emp_consym to be deleted.

    Returns:
        JsonResponse: A JSON response indicating the success of the delete
        operation. If successful, returns a success message. If the
        emp_consym is not found, returns an error message. If the
        request method is not POST, returns an invalid request method error.
    """
    instance = emp_confrence_organised.objects.get(pk=request.POST['pk'])
    instance.delete()
    return JsonResponse({'success': True})

@csrf_exempt
def emp_consultancy_projectsDelete(request):
    """
    Delete an emp_consultancy_projects entry from the database.

    This view handles POST requests to delete a specific
    emp_consultancy_projects identified by its primary key ('pk') sent in
    the request data.

    Args:
        request (HttpRequest): The request object containing the primary key
        of the emp_consultancy_projects to be deleted.

    Returns:
        JsonResponse: A JSON response indicating the success of the delete
        operation. If successful, returns a success message. If the
        emp_consultancy_projects is not found, returns an error message. If the
        request method is not POST, returns an invalid request method error.
    """
    instance = emp_consultancy_projects.objects.get(pk=request.POST['pk'])
    instance.delete()
    return JsonResponse({'success': True})

@csrf_exempt
def emp_event_organizedDelete(request):
    """
    Delete an emp_event_organized entry from the database.

    This view handles POST requests to delete a specific
    emp_event_organized identified by its primary key ('pk') sent in
    the request data.

    Args:
        request (HttpRequest): The request object containing the primary key
        of the emp_event_organized to be deleted.

    Returns:
        JsonResponse: A JSON response indicating the success of the delete
        operation. If successful, returns a success message. If the
        emp_event_organized is not found, returns an error message. If the
        request method is not POST, returns an invalid request method error.
    """
    instance = emp_event_organized.objects.get(pk=request.POST['pk'])
    instance.delete()
    return JsonResponse({'success': True})

@csrf_exempt
def emp_expert_lecturesDelete(request):
    """
    Delete an emp_expert_lectures entry from the database.

    This view handles POST requests to delete a specific
    emp_expert_lectures identified by its primary key ('pk') sent in
    the request data.

    Args:
        request (HttpRequest): The request object containing the primary key
        of the emp_expert_lectures to be deleted.

    Returns:
        JsonResponse: A JSON response indicating the success of the delete
        operation. If successful, returns a success message. If the
        emp_expert_lectures is not found, returns an error message. If the
        request method is not POST, returns an invalid request method error.
    """
    instance = emp_expert_lectures.objects.get(pk=request.POST['pk'])
    instance.delete()
    return JsonResponse({'success': True})

@csrf_exempt
def emp_keynote_addressDelete(request):
    """
    Delete an emp_keynote_address entry from the database.

    This view handles POST requests to delete a specific
    emp_keynote_address identified by its primary key ('pk') sent in
    the request data.

    Args:
        request (HttpRequest): The request object containing the primary key
        of the emp_keynote_address to be deleted.

    Returns:
        JsonResponse: A JSON response indicating the success of the delete
        operation. If successful, returns a success message. If the
        emp_keynote_address is not found, returns an error message. If the
        request method is not POST, returns an invalid request method error.
    """
    instance = emp_keynote_address.objects.get(pk=request.POST['pk'])
    instance.delete()
    return JsonResponse({'success': True})

@csrf_exempt
def emp_mtechphd_thesisDelete(request):
    """
    Delete an emp_mtechphd_thesis entry from the database.

    This view handles POST requests to delete a specific
    emp_mtechphd_thesis identified by its primary key ('pk') sent in
    the request data.

    Args:
        request (HttpRequest): The request object containing the primary key
        of the emp_mtechphd_thesis to be deleted.

    Returns:
        JsonResponse: A JSON response indicating the success of the delete
        operation. If successful, returns a success message. If the
        emp_mtechphd_thesis is not found, returns an error message. If the
        request method is not POST, returns an invalid request method error.
    """
    instance = emp_mtechphd_thesis.objects.get(pk=request.POST['pk'])
    instance.delete()
    return JsonResponse({'success': True})

@csrf_exempt
def emp_patentsDelete(request):
    """
    Delete an emp_patents entry from the database.

    This view handles POST requests to delete a specific
    emp_patents identified by its primary key ('pk') sent in
    the request data.

    Args:
        request (HttpRequest): The request object containing the primary key
        of the emp_patents to be deleted.

    Returns:
        JsonResponse: A JSON response indicating the success of the delete
        operation. If successful, returns a success message. If the
        emp_patents is not found, returns an error message. If the
        request method is not POST, returns an invalid request method error.
    """
    instance = emp_patents.objects.get(pk=request.POST['pk'])
    instance.delete()
    return JsonResponse({'success': True})

@csrf_exempt
def emp_published_booksDelete(request):
    """
    Delete an emp_published_books entry from the database.

    This view handles POST requests to delete a specific
    emp_published_books identified by its primary key ('pk') sent in
    the request data.

    Args:
        request (HttpRequest): The request object containing the primary key
        of the emp_published_books to be deleted.

    Returns:
        JsonResponse: A JSON response indicating the success of the delete
        operation. If successful, returns a success message. If the
        emp_published_books is not found, returns an error message. If the
        request method is not POST, returns an invalid request method error.
    """
    instance = emp_published_books.objects.get(pk=request.POST['pk'])
    instance.delete()
    return JsonResponse({'success': True})

@csrf_exempt
def emp_research_papersDelete(request):
    """
    Delete an emp_research_papers entry from the database.

    This view handles POST requests to delete a specific
    emp_research_papers identified by its primary key ('pk') sent in
    the request data.

    Args:
        request (HttpRequest): The request object containing the primary key
        of the emp_research_papers to be deleted.

    Returns:
        JsonResponse: A JSON response indicating the success of the delete
        operation. If successful, returns a success message. If the
        emp_research_papers is not found, returns an error message. If the
        request method is not POST, returns an invalid request method error.
    """
    instance = emp_research_papers.objects.get(pk=request.POST['pk'])
    instance.delete()
    return JsonResponse({'success': True})

@csrf_exempt
def emp_research_projectsDelete(request):
    """
    Delete an emp_research_projects entry from the database.

    This view handles POST requests to delete a specific
    emp_research_projects identified by its primary key ('pk') sent in
    the request data.

    Args:
        request (HttpRequest): The request object containing the primary key
        of the emp_research_projects to be deleted.

    Returns:
        JsonResponse: A JSON response indicating the success of the delete
        operation. If successful, returns a success message. If the
        emp_research_projects is not found, returns an error message. If the
        request method is not POST, returns an invalid request method error.
    """
    instance = emp_research_projects.objects.get(pk=request.POST['pk'])
    instance.delete()
    return JsonResponse({'success': True})

@csrf_exempt
def emp_session_chairDelete(request):
    """
    Delete an emp_session_chair entry from the database.

    This view handles POST requests to delete a specific
    emp_session_chair identified by its primary key ('pk') sent in
    the request data.

    Args:
        request (HttpRequest): The request object containing the primary key
        of the emp_session_chair to be deleted.

    Returns:
        JsonResponse: A JSON response indicating the success of the delete
        operation. If successful, returns a success message. If the
        emp_session_chair is not found, returns an error message. If the
        request method is not POST, returns an invalid request method error.
    """
    instance = emp_session_chair.objects.get(pk=request.POST['pk'])
    instance.delete()
    return JsonResponse({'success': True})

@csrf_exempt
def emp_techtransferDelete(request):
    """
    Delete an emp_techtransfer entry from the database.

    This view handles POST requests to delete a specific
    emp_techtransfer identified by its primary key ('pk') sent in
    the request data.

    Args:
        request (HttpRequest): The request object containing the primary key
        of the emp_techtransfer to be deleted.

    Returns:
        JsonResponse: A JSON response indicating the success of the delete
        operation. If successful, returns a success message. If the
        emp_techtransfer is not found, returns an error message. If the
        request method is not POST, returns an invalid request method error.
    """
    instance = emp_techtransfer.objects.get(pk=request.POST['pk'])
    instance.delete()
    return JsonResponse({'success': True})

@csrf_exempt
def emp_visitsDelete(request):
    """
    Delete an emp_visits entry from the database.

    This view handles POST requests to delete a specific
    emp_visits identified by its primary key ('pk') sent in
    the request data.

    Args:
        request (HttpRequest): The request object containing the primary key
        of the emp_visits to be deleted.

    Returns:
        JsonResponse: A JSON response indicating the success of the delete
        operation. If successful, returns a success message. If the
        emp_visits is not found, returns an error message. If the
        request method is not POST, returns an invalid request method error.
    """
    instance = emp_visits.objects.get(pk=request.POST['pk'])
    instance.delete()
    return JsonResponse({'success': True})


# Views for inserting fields in EIS
@csrf_exempt
def pg_insert(request):
    """
    Insert a new or update an existing Post Graduate student entry in the emp_mtechphd_thesis table.

    This view handles POST requests to insert a new or update an existing
    Post Graduate student entry in the emp_mtechphd_thesis table. The
    request data should contain the primary key ('user_id') of the faculty
    about, the primary key ('pg_id') of the emp_mtechphd_thesis entry to be
    updated, the title of the thesis, the starting year, the month of
    completion, the supervisors, the roll number and the name of the student.

    If the 'pg_id' is not provided, a new emp_mtechphd_thesis entry is
    created. Otherwise, the existing entry is updated.

    Args:
        request (HttpRequest): The request object containing the primary key
        of the faculty about and the details of the Post Graduate student entry
        to be inserted or updated.

    Returns:
        JsonResponse: A JSON response indicating the success of the insert or
        update operation. If successful, returns a success message. If the
        request method is not POST, returns an invalid request method error.
    """
    user = get_object_or_404(faculty_about, user_id=request.POST.get('user_id'))
    pf = user.user_id

    if (request.POST.get('pg_id')==None or request.POST.get('pg_id')==""):
        eis = emp_mtechphd_thesis()
    else:
        eis = get_object_or_404(emp_mtechphd_thesis, id=request.POST.get('pg_id'))
    
    eis.pf_no = pf
    eis.title = request.POST.get('title')
    eis.s_year = request.POST.get('s_year')
    eis.a_month = request.POST.get('month')
    eis.supervisors = request.POST.get('supervisors')
    eis.rollno = request.POST.get('roll')
    eis.s_name = request.POST.get('name')

    eis.save()
    return JsonResponse({'success': True})

@csrf_exempt
def phd_insert(request):
    """
    Insert a new or update an existing PhD student entry in the emp_mtechphd_thesis table.

    This view handles POST requests to insert a new or update an existing
    PhD student entry in the emp_mtechphd_thesis table. The request data
    should contain the primary key ('user_id') of the faculty about, the
    primary key ('phd_id') of the emp_mtechphd_thesis entry to be updated,
    the title of the thesis, the starting year, the month of completion,
    the supervisors, the roll number, and the name of the student.

    If the 'phd_id' is not provided, a new emp_mtechphd_thesis entry is
    created. Otherwise, the existing entry is updated. The 'degree_type' is
    set to 2 for PhD entries.

    Args:
        request (HttpRequest): The request object containing the primary key
        of the faculty about and the details of the PhD student entry to be
        inserted or updated.

    Returns:
        JsonResponse: A JSON response indicating the success of the insert or
        update operation. If successful, returns a success message. If the
        request method is not POST, returns an invalid request method error.
    """
    user = get_object_or_404(faculty_about, user_id=request.POST.get('user_id'))
    pf = user.user_id

    if (request.POST.get('phd_id')==None or request.POST.get('phd_id')==""):
        eis = emp_mtechphd_thesis()
    else:
        eis = get_object_or_404(emp_mtechphd_thesis, id=request.POST.get('phd_id'))
    
    eis.pf_no = pf
    eis.degree_type = 2
    eis.title = request.POST.get('title')
    eis.s_year = request.POST.get('s_year')
    eis.a_month = request.POST.get('month')
    eis.supervisors = request.POST.get('supervisors')
    eis.rollno = request.POST.get('roll')
    eis.s_name = request.POST.get('name')

    eis.save()
    return JsonResponse({'success': True})

@csrf_exempt
def fvisit_insert(request):
    """
    Insert a new or update an existing foreign visit entry in the emp_visits table.

    This view handles POST requests to insert a new or update an existing
    foreign visit entry in the emp_visits table. The request data
    should contain the primary key ('user_id') of the faculty about, the
    primary key ('fvisit_id') of the emp_visits entry to be updated, the
    country of visit, the place of visit, the purpose of visit, the
    start date and end date of visit.

    If the 'fvisit_id' is not provided, a new emp_visits entry is
    created. Otherwise, the existing entry is updated. The 'v_type' is
    set to 2 for foreign visit entries.

    Args:
        request (HttpRequest): The request object containing the primary key
        of the faculty about and the details of the foreign visit entry to be
        inserted or updated.

    Returns:
        JsonResponse: A JSON response indicating the success of the insert or
        update operation. If successful, returns a success message. If the
        request method is not POST, returns an invalid request method error.
    """
    if request.method=='POST':
        user = get_object_or_404(faculty_about, user_id=request.POST.get('user_id'))
        pf = user.user_id

        if (request.POST.get('fvisit_id')==None or request.POST.get('fvisit_id')==""):
            eis = emp_visits()
        else:
            eis = get_object_or_404(emp_visits, id=request.POST.get('fvisit_id'))
        
        eis.pf_no = pf
        eis.v_type = 2
        eis.country = request.POST.get('country').upper()
        eis.place = request.POST.get('place')
        eis.purpose = request.POST.get('purpose')
        
        x = request.POST.get('start_date')
        x = x.split()
        x = x[1:4]
        x = ' '.join(x)

        eis.start_date = datetime.datetime.strptime(x, "%b %d %Y")

        x = request.POST.get('end_date')
        x = x.split()
        x = x[1:4]
        x = ' '.join(x)

        eis.end_date = datetime.datetime.strptime(x, "%b %d %Y")

        eis.save()
        return JsonResponse({'message' : 'Your data is saved '})

@csrf_exempt
def ivisit_insert(request):
    """
    API endpoint to insert or update a research data entry of type 'International Visit' in the database.

    Parameters:
        request (HttpRequest): The POST request containing the data to be inserted or updated.

    Returns:
        JsonResponse: A JSON response indicating the success of the insert or update operation. If successful, returns a success message. If the request method is not POST, returns an invalid request method error.
    """
    user = get_object_or_404(faculty_about, user_id=request.POST.get('user_id'))
    pf = user.user_id

    if (request.POST.get('ivisit_id')==None or request.POST.get('ivisit_id')==""):
        eis = emp_visits()
    else:
        eis = get_object_or_404(emp_visits, id=request.POST.get('ivisit_id'))
    
    eis.pf_no = pf
    eis.v_type = 1
    eis.country = "India"
    eis.place = request.POST.get('place')
    eis.purpose = request.POST.get('purpose')
    
    x = request.POST.get('start_date')
    x = x.split()
    x = x[1:4]
    x = ' '.join(x)

    eis.start_date = datetime.datetime.strptime(x, "%b %d %Y")

    x = request.POST.get('end_date')
    x = x.split()
    x = x[1:4]
    x = ' '.join(x)

    eis.end_date = datetime.datetime.strptime(x, "%b %d %Y")

    eis.save()
    return JsonResponse({'message' : 'Your data is saved '})


#Function to save journal of employee
@csrf_exempt
def journal_insert(request):
    """
    This function is used to create a journal for an employee.

    @param:
        request (HttpRequest): The POST request containing the data to be inserted or updated.

    Returns:
        JsonResponse: A JSON response indicating the success of the insert or update operation. If successful, returns a success message. If the request method is not POST, returns an invalid request method error.
    """
    if request.method=="POST":
        user = get_object_or_404(faculty_about, user_id=request.POST['user_id'])
        eis = emp_research_papers.objects.create(pf_no = user.user_id)
        eis.rtype = 'Journal'
        eis.authors = request.POST.get('authors')
        eis.title_paper = request.POST.get('title')
        try:
            myfile = request.FILES['journal']
            fs = FileSystemStorage()
            filename = fs.save(myfile.name, myfile)
            uploaded_file_url = fs.url(filename)
            eis.paper=uploaded_file_url
        except:
            eis.paper = None

        eis.co_authors = request.POST.get('co_author')
        eis.name = request.POST.get('name')
        eis.doc_id = request.POST.get('doc_id')
        eis.doc_description = request.POST.get('doc_description')
        eis.status = request.POST.get('status')
        eis.reference_number = request.POST.get('ref')
        eis.is_sci = request.POST.get('sci')
        volume_no = request.POST.get('volume')
        page_no = request.POST.get('page')
        year = request.POST.get('year')
        if volume_no != '':
            eis.volume_no=volume_no
        if page_no != '':
            eis.page_no=page_no
        if year != '':
            eis.year = year
        if(request.POST.get('doi') != None and request.POST.get('doi') != '' and request.POST.get('doi') != 'None'):
            try:
                eis.doi = datetime.datetime.strptime(
                    request.POST.get('doi'), "%B %d, %Y")
            except:
                try:
                    eis.doi = datetime.datetime.strptime(
                        request.POST.get('doi'), "%b. %d, %Y")
                except:
                    eis.doi = request.POST.get('doi')
        if (request.POST.get('doa') != None and request.POST.get('doa') != '' and request.POST.get('doa') != 'None'):
            try:
                eis.date_acceptance = datetime.datetime.strptime(
                    request.POST.get('doa'), "%B %d, %Y")
            except:
                eis.date_acceptance = datetime.datetime.strptime(
                    request.POST.get('doa'), "%b. %d, %Y")
        if (request.POST.get('dop') != None and request.POST.get('dop') != '' and request.POST.get('dop') != 'None'):
            try:
                eis.date_publication = datetime.datetime.strptime(
                    request.POST.get('dop'), "%B %d, %Y")
            except:
                eis.date_publication = datetime.datetime.strptime(
                    request.POST.get('dop'), "%b. %d, %Y")
        if (request.POST.get('dos') != None and request.POST.get('dos') != '' and request.POST.get('dos') != 'None'):
            try:
                eis.date_submission = datetime.datetime.strptime(
                    request.POST.get('dos'), "%B %d, %Y")
            except:
                eis.date_submission = datetime.datetime.strptime(
                    request.POST.get('dos'), "%b. %d, %Y")
        eis.save()
        return JsonResponse({'message' : 'Your data is saved '})
    
@csrf_exempt
def editjournal(request):
    """
    Update the details of an existing journal entry in the database with the provided data.

    The function retrieves a specific journal entry based on a primary key passed in the request,
    updates its fields with the new data from the request, and saves the changes to the database.
    If a new journal file is uploaded, it is saved and its URL is updated in the entry.

    Args:
        request (HttpRequest): The request object containing POST data with journal details and files.

    Returns:
        JsonResponse: A JSON response indicating the success of the update operation.
    """
    eis = emp_research_papers.objects.get(pk=request.POST.get('journalpk'))
    eis.authors = request.POST.get('authors')
    eis.title_paper = request.POST.get('title')
    try:
        myfile = request.FILES['journal']
        fs = FileSystemStorage()
        filename = fs.save(myfile.name, myfile)
        uploaded_file_url = fs.url(filename)
        eis.paper=uploaded_file_url
    except:
        logging.warning('No New Journal Found for Update, Older one will be kept.')
    eis.co_authors = request.POST.get('co_author')
    eis.name = request.POST.get('name')
    eis.doc_id = request.POST.get('doc_id')
    eis.doc_description = request.POST.get('doc_description')
    eis.status = request.POST.get('status')
    eis.reference_number = request.POST.get('ref')
    eis.is_sci = request.POST.get('sci')
    eis.volume_no = request.POST.get('volume')
    eis.page_no = request.POST.get('page')
    eis.year = request.POST.get('year')

    if(request.POST.get('doi') != None and request.POST.get('doi') != '' and request.POST.get('doi') != 'None'):
        x = request.POST.get('doi')



        if x[:5] == "Sept." :
            x = "Sep." + x[5:]
        try:
            eis.doi = datetime.datetime.strptime(
                x, "%B %d, %Y")
        except:
            try:
                eis.doi = datetime.datetime.strptime(
                    x, "%b. %d, %Y")
            except:
                eis.doi = x
    if (request.POST.get('doa') != None and request.POST.get('doa') != '' and request.POST.get('doa') != 'None'):
        x = request.POST.get('doa')
        if x[:-10] == ', midnight':
            x = x[0:-10]

        if x[:5] == "Sept." :
            x = "Sep." + x[5:]
        try:
            eis.date_acceptance = datetime.datetime.strptime(
                x, "%B %d, %Y")
        except:
            eis.date_acceptance = datetime.datetime.strptime(
                x, "%b. %d, %Y")

    if (request.POST.get('dop') != None and request.POST.get('dop') != '' and request.POST.get('dop') != 'None'):
        x = request.POST.get('dop')
        if x[:-10] == ', midnight':
            x = x[0:-10]
        if x[:5] == "Sept." :
            x = "Sep." + x[5:]
        try:
            eis.date_publication = datetime.datetime.strptime(
                x, "%B %d, %Y")
        except:
            eis.date_publication = datetime.datetime.strptime(
                x, "%b. %d, %Y")
    if (request.POST.get('dos') != None and request.POST.get('dos') != '' and request.POST.get('dos') != 'None'):
        x = request.POST.get('dos')
        if x[-10:] == ', midnight':
            x = x[0:-10]
        if x[:5] == "Sept." :
            x = "Sep." + x[5:]
        try:
            eis.date_submission = datetime.datetime.strptime(
                x, "%B %d, %Y")
        except:
            eis.date_submission = datetime.datetime.strptime(
                x, "%b. %d, %Y")
    eis.save()
    return JsonResponse({'message' : 'Your data is updated '})
    
@csrf_exempt
def editforeignvisit(request):
    """
    Edit a foreign visit entry in the emp_visits table.

    This view handles POST requests to edit a foreign visit entry in the
    emp_visits table. The request data should contain the primary key
    ('foreignvisitpk') of the emp_visits entry to be updated, the
    country of visit, the place of visit, the purpose of visit, the
    start date and end date of visit.

    If the 'foreignvisitpk' is not provided, a new emp_visits entry is
    created. Otherwise, the existing entry is updated. The 'v_type' is
    set to 2 for foreign visit entries.

    Args:
        request (HttpRequest): The request object containing the primary key
        of the faculty about and the details of the foreign visit entry to be
        inserted or updated.

    Returns:
        JsonResponse: A JSON response indicating the success of the insert or
        update operation. If successful, returns a success message. If the
        request method is not POST, returns an invalid request method error.
    """
    eis = emp_visits.objects.get(pk=request.POST.get('foreignvisitpk'))
    eis.country = request.POST.get('country')
    eis.place = request.POST.get('place')
    eis.purpose = request.POST.get('purpose')
    x = request.POST.get('start_date')
    if x and x[:5] == "Sept." :
            x = "Sep." + x[5:]
    try:
        eis.start_date = datetime.datetime.strptime(x, "%B %d, %Y") if x else None
    except:
        eis.start_date = datetime.datetime.strptime(x, "%b. %d, %Y") if x else None
    x = request.POST.get('end_date')
    if x and x[:5] == "Sept." :
            x = "Sep." + x[5:]
    try:
        eis.end_date = datetime.datetime.strptime(x, "%B %d, %Y") if x else None
    except:
        eis.end_date = datetime.datetime.strptime(x, "%b. %d, %Y") if x else None
    eis.save()
    return JsonResponse({'message' : 'Your data is updated '})

@csrf_exempt
def editindianvisit(request):
    """
    Edit an Indian visit entry in the emp_visits table.

    This view handles POST requests to edit an Indian visit entry in the
    emp_visits table. The request data should contain the primary key
    ('indianvisitpk') of the emp_visits entry to be updated, the
    country of visit, the place of visit, the purpose of visit, the
    start date and end date of visit.

    If the 'indianvisitpk' is not provided, a new emp_visits entry is
    created. Otherwise, the existing entry is updated. The 'v_type' is
    set to 1 for Indian visit entries.

    Args:
        request (HttpRequest): The request object containing the primary key
        of the faculty about and the details of the Indian visit entry to be
        inserted or updated.

    Returns:
        JsonResponse: A JSON response indicating the success of the insert or
        update operation. If successful, returns a success message. If the
        request method is not POST, returns an invalid request method error.
    """
    eis = emp_visits.objects.get(pk=request.POST.get('indianvisitpk'))
    eis.country = request.POST.get('country')
    eis.place = request.POST.get('place')
    eis.purpose = request.POST.get('purpose')
    x = request.POST.get('start_date')
    if x and x[:5] == "Sept." :
            x = "Sep." + x[5:]
    try:
        eis.start_date = datetime.datetime.strptime(x, "%B %d, %Y") if x else None
    except:
        eis.start_date = datetime.datetime.strptime(x, "%b. %d, %Y") if x else None
    x = request.POST.get('end_date')
    if x and x[:5] == "Sept." :
            x = "Sep." + x[5:]
    try:
        eis.end_date = datetime.datetime.strptime(x, "%B %d, %Y") if x else None
    except:
        eis.end_date = datetime.datetime.strptime(x, "%b. %d, %Y") if x else None
    eis.save()
    return JsonResponse({'success': True})


@csrf_exempt
def conference_insert(request):
    """
    Insert a conference paper entry in the emp_research_papers table.

    This view handles POST requests to insert a conference paper entry in the
    emp_research_papers table. The request data should contain the primary key
    ('user_id') of the faculty about, the authors, the co-authors, the title of
    the paper, the journal name, the venue, the page number, the isbn number,
    the year, the status, the date of acceptance, the date of publication, and
    the date of submission.

    The 'rtype' is set to 'Conference' for conference paper entries.

    Args:
        request (HttpRequest): The request object containing the primary key of
        the faculty about and the details of the conference paper entry to be
        inserted.

    Returns:
        JsonResponse: A JSON response indicating the success of the insert
        operation. If successful, returns a success message. If the request
        method is not POST, returns an invalid request method error.
    """
    if request.method == 'POST':
        user = get_object_or_404(faculty_about, user_id=request.POST.get('user_id'))
        pf = user.user_id
        eis = emp_research_papers()
        eis.pf_no = pf
        eis.rtype = 'Conference'
        eis.authors = request.POST.get('author')
        eis.co_authors = request.POST.get('co_authors')
        eis.title_paper = request.POST.get('title')
        try:
            myfile = request.FILES['journal']
            fs = FileSystemStorage()
            filename = fs.save(myfile.name, myfile)
            uploaded_file_url = fs.url(filename)
            eis.paper=uploaded_file_url
        except:
            logging.warning('Journal file not Uploaded')
        eis.name = request.POST.get('name')
        eis.venue = request.POST.get('venue')
        if request.POST.get('page_no') != '':
            eis.page_no = request.POST.get('page_no')
        if request.POST.get('isbn_no') != '':
            eis.isbn_no = request.POST.get('isbn_no')
        if request.POST.get('year') != '':
            eis.year = request.POST.get('year')
        eis.status = request.POST.get('status')
        if(request.POST.get('doi') != None and request.POST.get('doi') != '' and request.POST.get('doi') != 'None'):
            x = request.POST.get('doi')
            x = x.split()
            x = x[1:4]
            x = ' '.join(x)
            eis.doi = datetime.datetime.strptime(x, "%b %d %Y")

        if (request.POST.get('doa') != None and request.POST.get('doa') != '' and request.POST.get('doa') != 'None'):
            x = request.POST.get('doa')
            x = x.split()
            x = x[1:4]
            x = ' '.join(x)
            eis.date_acceptance = datetime.datetime.strptime(x, "%b %d %Y")

        if (request.POST.get('dop') != None and request.POST.get('dop') != '' and request.POST.get('dop') != 'None'):
            x = request.POST.get('dop')
            x = x.split()
            x = x[1:4]
            x = ' '.join(x)
            eis.date_publication = datetime.datetime.strptime(x, "%b %d %Y")

        if (request.POST.get('dos') != None and request.POST.get('dos') != '' and request.POST.get('dos') != 'None'):
            x = request.POST.get('dos')
            x = x.split()
            x = x[1:4]
            x = ' '.join(x)
            eis.date_submission = datetime.datetime.strptime(x, "%b %d %Y")

        eis.save()
        return JsonResponse({'message' : 'Your data is saved '})

@csrf_exempt
def editconference(request):
    """
    This function is used to update a conference for an employee.

    @param:
        request (HttpRequest): The POST request containing the data to be updated.

    Returns:
        JsonResponse: A JSON response indicating the success of the update operation. If successful, returns a success message. If the request method is not POST, returns an invalid request method error.
    """
    eis = emp_research_papers.objects.get(pk=request.POST.get('conferencepk'))
    eis.authors = request.POST.get('author')
    eis.co_authors = request.POST.get('co_authors')
    eis.title_paper = request.POST.get('title')
    try:
        myfile = request.FILES['journal']
        fs = FileSystemStorage()
        filename = fs.save(myfile.name, myfile)
        uploaded_file_url = fs.url(filename)
        eis.paper=uploaded_file_url
    except:
        logging.warning('Journal File not Uploaded.')

    eis.name = request.POST.get('name')
    eis.venue = request.POST.get('venue')
    isbn  = request.POST.get('isbn_no')

    eis.page_no = request.POST.get('page_no')

    eis.year = request.POST.get('year')
    eis.status = request.POST.get('status')
    if(request.POST.get('doi') != None and request.POST.get('doi') != '' and request.POST.get('doi') != 'None'):
        x = request.POST.get('doi')
        if x[:5] == "Sept." :
            x = "Sep." + x[5:]
        try:
            eis.doi = datetime.datetime.strptime(
                x, "%B %d, %Y")
        except:
            try:
                eis.doi = datetime.datetime.strptime(
                    x, "%b. %d, %Y")
            except:
                eis.doi = x
    if (request.POST.get('doa') != None and request.POST.get('doa') != '' and request.POST.get('doa') != 'None'):
        x = request.POST.get('doa')
        if x[:5] == "Sept." :
            x = "Sep." + x[5:]
        try:
            eis.date_acceptance = datetime.datetime.strptime(
                x, "%B %d, %Y")
        except:
            eis.date_acceptance = datetime.datetime.strptime(
                x, "%b. %d, %Y")

    if (request.POST.get('dop') != None and request.POST.get('dop') != '' and request.POST.get('dop') != 'None'):
        x = request.POST.get('dop')
        if x[:5] == "Sept." :
            x = "Sep." + x[5:]
        try:
            eis.date_publication = datetime.datetime.strptime(
                x, "%B %d, %Y")
        except:
            eis.date_publication = datetime.datetime.strptime(
                x, "%b. %d, %Y")
    if (request.POST.get('dos') != None and request.POST.get('dos') != '' and request.POST.get('dos') != 'None'):
        x = request.POST.get('dos')
        if x[-10:] == ', midnight':
            x = x[0:-10]
        if x[:5] == "Sept." :
            x = "Sep." + x[5:]
        try:
            eis.date_submission = datetime.datetime.strptime(
                x, "%B %d, %Y")
        except:
            eis.date_submission = datetime.datetime.strptime(
                x, "%b. %d, %Y")
    eis.save()
    return JsonResponse({'success': True})


@csrf_exempt
def book_insert(request):
    """
    Insert a book entry in the emp_published_books table.

    This view handles POST requests to insert a book entry in the
    emp_published_books table. The request data should contain the primary key
    ('user_id') of the faculty about, the type of publication, the title of
    the publication, the publisher of the publication, the year of publication,
    and the authors of the publication.

    Returns:
        JsonResponse: A JSON response indicating the success of the insert
        operation. If successful, returns a success message.
    """
    user = get_object_or_404(faculty_about, user_id=request.POST.get('user_id'))
    pf = user.user_id
    eis = emp_published_books()
    eis.pf_no = pf
    eis.p_type = request.POST.get('book_p_type')
    eis.title = request.POST.get('book_title')
    eis.publisher = request.POST.get('book_publisher')
    eis.pyear = request.POST.get('book_year')
    eis.authors = request.POST.get('book_author')
    eis.save()
    return JsonResponse({'message' : 'Your data is saved '})


@csrf_exempt
def editbooks(request):
    """
    Edit a book entry in the emp_published_books table.

    This view handles POST requests to edit a book entry in the
    emp_published_books table. The request data should contain the primary key
    ('pk') of the book entry, the type of publication, the title of the
    publication, the publisher of the publication, the year of publication,
    and the authors of the publication.

    Returns:
        JsonResponse: A JSON response indicating the success of the edit
        operation. If successful, returns a success message.
    """
    eis = emp_published_books.objects.get(pk=request.POST.get('bookspk'))
    eis.p_type = request.POST.get('book_p_type')
    eis.title = request.POST.get('book_title')
    eis.publisher = request.POST.get('book_publisher')
    eis.pyear = request.POST.get('book_year')
    eis.authors = request.POST.get('book_author')
    eis.save()
    return JsonResponse({'message' : 'Your data is updated '})

@csrf_exempt
def consym_insert(request):
    """
    Insert a new conference entry in the emp_confrence_organised table.

    This view handles POST requests to insert a new conference entry. The request
    data should include the primary key ('user_id') of the faculty about, the
    conference name, venue, role, and the start and end dates of the conference.

    The 'role1' is set based on the provided conference role and can be further
    specified with 'role2' if applicable.

    Args:
        request (HttpRequest): The request object containing the primary key
        of the faculty about and the details of the conference entry to be
        inserted.

    Returns:
        JsonResponse: A JSON response indicating the success of the insert
        operation. If successful, returns a success message.
    """
    user = get_object_or_404(faculty_about, user_id=request.POST.get('user_id'))
    pf = user.user_id
    eis = emp_confrence_organised()
    eis.pf_no = pf
    eis.name = request.POST.get('conference_name')
    eis.venue = request.POST.get('conference_venue')
    eis.role1 = request.POST.get('conference_role')
    if(eis.role1 == 'Any Other'):
        eis.role2 = request.POST.get('conference_organised')
    if(eis.role1 == 'Organised'):
        if(request.POST.get('conference_organised') == 'Any Other'):
            eis.role2 = request.POST.get('myDIV1')
        else:
            eis.role2 = request.POST.get('conference_organised')
    if (eis.role1 == "" or eis.role1==None):
        eis.role1 = "Any Other"
        eis.role2 = "Any Other"

    x = request.POST.get('conference_start_date')
    x = x.split()
    x = x[1:4]
    x = ' '.join(x)

    eis.start_date = datetime.datetime.strptime(x, "%b %d %Y")

    x = request.POST.get('conference_end_date')
    x = x.split()
    x = x[1:4]
    x = ' '.join(x)

    eis.end_date = datetime.datetime.strptime(x, "%b %d %Y")

    eis.save()
    return JsonResponse({ "success": True})

@csrf_exempt
def editconsym(request):
    """
    Edit a conference organised entry for a faculty member.

    Args:
        request (HttpRequest): The request object.

    Returns:
        JsonResponse: A JSON response indicating the success of the edit
        operation. If successful, returns a success message.
    """
    eis = emp_confrence_organised.objects.get(pk=request.POST.get('conferencepk2'))
    eis.name = request.POST.get('conference_name')
    eis.venue = request.POST.get('conference_venue')
    eis.role1 = request.POST.get('conference_role')
    if(eis.role1 == 'Any Other'):
        eis.role2 = request.POST.get('conference_organised')
    if(eis.role1 == 'Organised'):
        if(request.POST.get('conference_organised') == 'Any Other'):
            eis.role2 = request.POST.get('myDIV1')
        else:
            eis.role2 = request.POST.get('conference_organised')
    if (eis.role1 == "" or eis.role1==None):
        eis.role1 = "Any Other"
        eis.role2 = "Any Other"
    
    x = request.POST.get('conference_start_date')
    x = x.split()
    x = x[1:4]
    x = ' '.join(x)

    eis.start_date = datetime.datetime.strptime(x, "%b %d %Y")

    x = request.POST.get('conference_end_date')
    x = x.split()
    x = x[1:4]
    x = ' '.join(x)

    eis.end_date = datetime.datetime.strptime(x, "%b %d %Y")

    eis.save()
    return JsonResponse({'success': True})

@csrf_exempt
def event_insert(request):
    """
    Insert a new event organized entry for a faculty member.

    Args:
        request (HttpRequest): The request object.

    Returns:
        JsonResponse: A JSON response indicating the success of the insert
        operation. If successful, returns a success message.
    """
    
    user = get_object_or_404(faculty_about, user_id=request.POST.get('user_id'))
    pf = user.user_id
    eis = emp_event_organized()
    
    eis.pf_no = pf
    eis.type = request.POST.get('event_type')
    if(eis.type == 'Any Other'):
        if(request.POST.get('myDIV')!= None or request.POST.get('myDIV') != ""):
            eis.type = request.POST.get('myDIV')
    eis.sponsoring_agency = request.POST.get('sponsoring_agency')
    eis.name = request.POST.get('event_name')
    eis.venue = request.POST.get('event_venue')
    eis.role = request.POST.get('event_role')

    x = request.POST.get('event_start_date')
    x = x.split()
    x = x[1:4]
    x = ' '.join(x)

    eis.start_date = datetime.datetime.strptime(x, "%b %d %Y")

    x = request.POST.get('event_end_date')
    x = x.split()
    x = x[1:4]
    x = ' '.join(x)

    eis.end_date = datetime.datetime.strptime(x, "%b %d %Y")

    eis.save()
    return JsonResponse({'message' : 'Your data is saved '})

@csrf_exempt
def editevent(request):
    """
    Edit an event organized entry for a faculty member.

    Args:
        request (HttpRequest): The request object.

    Returns:
        JsonResponse: A JSON response indicating the success of the edit
        operation. If successful, returns a success message.
    """
    
    eis = emp_event_organized.objects.get(pk=request.POST.get('eventpk'))

    eis.type = request.POST.get('event_type')
    if(eis.type == 'Any Other'):
        if(request.POST.get('myDIV')!= None or request.POST.get('myDIV') != ""):
            eis.type = request.POST.get('myDIV')
    eis.sponsoring_agency = request.POST.get('sponsoring_agency')
    eis.name = request.POST.get('event_name')
    eis.venue = request.POST.get('event_venue')
    eis.role = request.POST.get('event_role')
    x = request.POST.get('event_start_date')
    x = x.split()
    x = x[1:4]
    x = ' '.join(x)

    eis.start_date = datetime.datetime.strptime(x, "%b %d %Y")

    x = request.POST.get('event_end_date')
    x = x.split()
    x = x[1:4]
    x = ' '.join(x)

    eis.end_date = datetime.datetime.strptime(x, "%b %d %Y")
    eis.save()
    return JsonResponse({'success': True})

@csrf_exempt
def award_insert(request):
    """
    Insert or update an award entry in the emp_achievement table.

    This view handles POST requests to insert a new or update an existing
    award entry in the emp_achievement table. The request data should
    contain the primary key ('user_id') of the faculty about, the award type,
    and other optional details such as the day, month, and year of the award.

    If the 'ach_id' is not provided, a new emp_achievement entry is created.
    Otherwise, the existing entry is updated.

    Args:
        request (HttpRequest): The request object containing the primary key
        of the faculty about and the details of the award entry to be
        inserted or updated.

    Returns:
        JsonResponse: A JSON response indicating the success of the insert or
        update operation. If successful, returns a success message. If the
        request method is not POST, returns an invalid request method error.
    """
    user = get_object_or_404(faculty_about, user_id=request.POST.get('user_id'))
    pf = user.user_id

    if (request.POST.get('ach_id')==None or request.POST.get('ach_id')==""):
        eis = emp_achievement()
    else:
        eis = get_object_or_404(emp_achievement, id=request.POST.get('ach_id'))
    
    eis.pf_no = pf
    eis.a_type = request.POST.get('type')
    if(request.POST.get('a_day') != None and request.POST.get('a_day') != ""): 
        eis.a_day = request.POST.get('a_day')
    if(request.POST.get('a_month') != None and request.POST.get('a_month') != ""):
        eis.a_month = request.POST.get('a_month')
    if(request.POST.get('a_year') != None and request.POST.get('a_year') != ""): 
        eis.a_year = request.POST.get('a_year')
    eis.details = request.POST.get('details')
    eis.save()
    return JsonResponse({'message' : 'Your data is saved '})

@csrf_exempt
def talk_insert(request):
    """
    This view handles POST requests to insert a new or update an existing
    expert lecture entry in the emp_expert_lectures table. The request data
    should contain the primary key ('user_id') of the faculty about, the
    lecture type, the place, title, and date of the lecture.

    If the 'lec_id' is not provided, a new emp_expert_lectures entry is
    created. Otherwise, the existing entry is updated.

    Args:
        request (HttpRequest): The request object containing the primary key
        of the faculty about and the details of the lecture entry to be
        inserted or updated.

    Returns:
        JsonResponse: A JSON response indicating the success of the insert or
        update operation. If successful, returns a success message. If the
        request method is not POST, returns an invalid request method error.
    """
    user = get_object_or_404(faculty_about, user_id=request.POST.get('user_id'))
    pf = user.user_id
    if (request.POST.get('lec_id')==None or request.POST.get('lec_id')=="" or request.POST.get('lec_id')==0):
        eis = emp_expert_lectures()
    else:
        eis = get_object_or_404(emp_expert_lectures, id=request.POST.get('lec_id'))
    
    eis.pf_no = pf
    eis.l_type = request.POST.get('type')
    eis.place = request.POST.get('place')
    eis.title = request.POST.get('title')
    x = request.POST.get('l_date')
    x = x.split()
    x = x[1:4]
    x = ' '.join(x)

    eis.l_date = datetime.datetime.strptime(x, "%b %d %Y")

    eis.save()
    return JsonResponse({'message' : 'Your data is saved '})

@csrf_exempt
def chaired_insert(request):
    """
    Insert a session chair entry in the emp_session_chair table.

    The request data should contain the primary key ('user_id') of the faculty about, the
    event name, the name of the session, and the start and end dates of the session.

    Args:
        request (HttpRequest): The request object containing the primary key of the
        faculty about and the details of the session chair entry to be inserted.

    Returns:
        JsonResponse: A JSON response indicating the success of the insert operation.
        If successful, returns a success message. If the request method is not POST,
        returns an invalid request method error.
    """
    user = get_object_or_404(faculty_about, user_id=request.POST.get('user_id'))
    pf = user.user_id

    eis = emp_session_chair()
    eis.pf_no = pf
    eis.event = request.POST.get('event')
    eis.name = request.POST.get('name')
    eis.s_year = request.POST.get('s_year')
    try:
        eis.start_date = datetime.datetime.strptime(request.POST.get('start'), "%B %d, %Y") if request.POST.get('start') else None
    except:
        eis.start_date = datetime.datetime.strptime(request.POST.get('start'), "%b. %d, %Y") if request.POST.get('start') else None
    try:
        eis.end_date = datetime.datetime.strptime(request.POST.get('end'), "%B %d, %Y") if request.POST.get('end') else None
    except:
        eis.end_date = datetime.datetime.strptime(request.POST.get('end'), "%b. %d, %Y") if request.POST.get('end') else None

    eis.save()
    return JsonResponse({'message' : 'Your data is saved '})

@csrf_exempt
def keynote_insert(request):
    """
    Insert a keynote address entry in the emp_keynote_address table.

    The request data should contain the primary key ('user_id') of the faculty about, the
    type of the address, the name of the event, the title of the address, the venue, the
    page number and isbn number of the address, and the year of the address.

    Args:
        request (HttpRequest): The request object containing the primary key of the
        faculty about and the details of the address entry to be inserted.

    Returns:
        JsonResponse: A JSON response indicating the success of the insert operation.
        If successful, returns a success message. If the request method is not POST,
        returns an invalid request method error.
    """
    user = get_object_or_404(faculty_about, user_id=request.POST.get('user_id'))
    pf = user.user_id

    eis = emp_keynote_address()
    eis.pf_no = pf
    eis.type = request.POST.get('type')
    eis.name = request.POST.get('name')
    eis.title = request.POST.get('title')
    eis.venue = request.POST.get('venue')
    eis.page_no = request.POST.get('page_no')
    eis.isbn_no = request.POST.get('isbn_no')
    eis.k_year = request.POST.get('k_year')
    try:
        eis.start_date = datetime.datetime.strptime(request.POST.get('start'), "%B %d, %Y") if request.POST.get('start') else None
    except:
        eis.start_date = datetime.datetime.strptime(request.POST.get('start'), "%b. %d, %Y") if request.POST.get('start') else None

    eis.save()
    return JsonResponse({'message' : 'Your data is saved '})

@csrf_exempt
def project_insert(request):
    """
    Insert a research project entry in the emp_research_projects table.

    The request data should contain the primary key ('user_id') of the faculty about, the
    primary key ('project_id') of the emp_research_projects entry to be updated, the
    principal investigator, the co-investigator, the title of the project, the financial
    outlay, the funding agency, the status of the project, the start date and end date of
    the project.

    If the 'project_id' is not provided, a new emp_research_projects entry is
    created. Otherwise, the existing entry is updated.

    Args:
        request (HttpRequest): The request object containing the primary key
        of the faculty about and the details of the research project entry to be
        inserted or updated.

    Returns:
        JsonResponse: A JSON response indicating the success of the insert or
        update operation. If successful, returns a success message. If the
        request method is not POST, returns an invalid request method error.
    """

    user = get_object_or_404(faculty_about, user_id=request.POST.get('user_id'))
    pf = user.user_id

    if (request.POST.get('project_id')==None or request.POST.get('project_id')==""):
        eis = emp_research_projects()
    else:
        eis = get_object_or_404(emp_research_projects, id=request.POST.get('project_id'))
    eis.pf_no = pf
    eis.pi = request.POST.get('pi')
    eis.co_pi = request.POST.get('co_pi')
    eis.title = request.POST.get('title')
    eis.financial_outlay = request.POST.get('financial_outlay')
    eis.funding_agency = request.POST.get('funding_agency')
    eis.status = request.POST.get('status')
    x = request.POST.get('start')
    x = x.split()
    x = x[1:4]
    x = ' '.join(x)

    eis.start_date = datetime.datetime.strptime(x, "%b %d %Y")

    x = request.POST.get('end')
    x = x.split()
    x = x[1:4]
    x = ' '.join(x)

    eis.finish_date = datetime.datetime.strptime(x, "%b %d %Y")

    x = request.POST.get('sub')
    x = x.split()
    x = x[1:4]
    x = ' '.join(x)

    eis.date_submission = datetime.datetime.strptime(x, "%b %d %Y")

    eis.save()
    return JsonResponse({'success': True})

@csrf_exempt
def consult_insert(request):
    """
    Insert a new consultancy project entry in the emp_consultancy_projects table.

    This view handles POST requests to insert a new consultancy project entry in the
    emp_consultancy_projects table. The request data should contain the primary key
    ('user_id') of the faculty about, the consultants, the client, the title of the
    project, the financial outlay, the start date and the end date of the project.

    If the 'consultancy_id' is not provided, a new emp_consultancy_projects entry is
    created. Otherwise, the existing entry is updated.

    Args:
        request (HttpRequest): The request object containing the primary key
        of the faculty about and the details of the consultancy project entry to be
        inserted or updated.

    Returns:
        JsonResponse: A JSON response indicating the success of the insert or
        update operation. If successful, returns a success message. If the
        request method is not POST, returns an invalid request method error.
    """
    user = get_object_or_404(faculty_about, user_id=request.POST.get('user_id'))
    pf = user.user_id

    if (request.POST.get('consultancy_id')==None or request.POST.get('consultancy_id')==""):
        eis = emp_consultancy_projects()
    else:
        eis = get_object_or_404(emp_consultancy_projects, id=request.POST.get('consultancy_id'))
    eis.pf_no = pf
    eis.consultants = request.POST.get('consultants')
    eis.client = request.POST.get('client')
    eis.title = request.POST.get('title')
    eis.financial_outlay = request.POST.get('financial_outlay')
    x = request.POST.get('start')
    x = x.split()
    x = x[1:4]
    x = ' '.join(x)

    eis.start_date = datetime.datetime.strptime(x, "%b %d %Y")
    x = request.POST.get('end')
    x = x.split()
    x = x[1:4]
    x = ' '.join(x)

    eis.end_date = datetime.datetime.strptime(x, "%b %d %Y")
    eis.save()
    return JsonResponse({'message' : 'Your data is saved '})

@csrf_exempt
def patent_insert(request):
    """
    Insert or update a patent entry in the emp_patents table.

    This view handles POST requests to insert a new patent entry or update an
    existing one in the emp_patents table. The request data should include the 
    primary key ('user_id') of the faculty, the patent number, earnings, title, 
    year, status, and application month.

    If the 'patent_id' is not provided, a new emp_patents entry is created. 
    Otherwise, the existing entry is updated.

    Args:
        request (HttpRequest): The request object containing the primary key
        of the faculty and the details of the patent entry to be inserted or 
        updated.

    Returns:
        JsonResponse: A JSON response indicating the success of the insert or 
        update operation. If successful, returns a success message. If the 
        request method is not POST, returns an invalid request method error.
    """
    user = get_object_or_404(faculty_about, user_id=request.POST.get('user_id'))
    pf = user.user_id

    if (request.POST.get('patent_id')==None or request.POST.get('patent_id')==""):
        eis = emp_patents()
    else:
        eis = get_object_or_404(emp_patents, id=request.POST.get('patent_id'))
    
    eis.pf_no = pf
    eis.p_no = request.POST.get('p_no')
    eis.earnings = request.POST.get('earnings')
    eis.title = request.POST.get('title')
    eis.p_year = request.POST.get('year')
    eis.status = request.POST.get('status')
    eis.a_month = request.POST.get('month')
    eis.save()
    return JsonResponse({'message' : 'Your data is saved '})

@csrf_exempt
def transfer_insert(request):
    """
    Insert a new technology transfer entry in the emp_techtransfer table.

    This view handles POST requests to insert a new technology transfer entry in the
    emp_techtransfer table. The request data should contain the primary key
    ('user_id') of the faculty about and the details of the technology transfer.

    Args:
        request (HttpRequest): The request object containing the primary key
        of the faculty about and the details of the technology transfer entry to be
        inserted.

    Returns:
        JsonResponse: A JSON response indicating the success of the insert
        operation. If successful, returns a success message. If the
        request method is not POST, returns an invalid request method error.
    """
    user = get_object_or_404(faculty_about, user_id=request.POST.get('user_id'))
    pf = user.user_id
    eis = emp_techtransfer()
    eis.pf_no = pf
    eis.details = request.POST.get('details')
    eis.save()
    return JsonResponse({'message' : 'Your data is saved '})

def get_personal_info(request):
    # Fetch all entries where pf_no is '5318'
    projects = faculty_about.objects.filter(user_id='5318').values()

    return JsonResponse(list(projects), safe=False)


def get_research_projects(request):
    # Fetch all entries where pf_no is '5318'
    projects = emp_research_projects.objects.filter(pf_no='5318').values()

    return JsonResponse(list(projects), safe=False)

def get_consultancy_projects(request):
    # Fetch all entries where pf_no is '5318'
    projects = emp_consultancy_projects.objects.filter(pf_no='5318').values()

    return JsonResponse(list(projects), safe=False)

def get_patents(request):
    # Fetch all entries where pf_no is '5318'
    projects = emp_patents.objects.filter(pf_no='5318').values()

    return JsonResponse(list(projects), safe=False)

def get_pg_thesis(request):
    # Fetch all entries where pf_no is '5318'
    projects = emp_mtechphd_thesis.objects.filter(pf_no='5318', degree_type='1').values()

    return JsonResponse(list(projects), safe=False)

def get_phd_thesis(request):
    # Fetch all entries where pf_no is '5318'
    projects = emp_mtechphd_thesis.objects.filter(pf_no='5318', degree_type='2').values()

    return JsonResponse(list(projects), safe=False)

def get_event(request):
    # Fetch all entries where pf_no is '5318'
    projects = emp_event_organized.objects.filter(pf_no='5318').values()

    return JsonResponse(list(projects), safe=False)

def get_fvisits(request):
    # Fetch all entries where pf_no is '5318'
    projects = emp_visits.objects.filter(pf_no='5318', v_type='2').values()

    return JsonResponse(list(projects), safe=False)

def get_ivisits(request):
    # Fetch all entries where pf_no is '5318'
    projects = emp_visits.objects.filter(pf_no='5318',  v_type='1').values()

    return JsonResponse(list(projects), safe=False)

def get_consym(request):
    # Fetch all entries where pf_no is '5318'
    projects = emp_confrence_organised.objects.filter(pf_no='5318').values()

    return JsonResponse(list(projects), safe=False)

def get_books(request):
    # Fetch all entries where pf_no is '5318'
    books = emp_published_books.objects.filter(pf_no="5318").order_by('-pyear').values()

    return JsonResponse(list(books), safe=False)

def get_journals(request):
    # Fetch all entries where pf_no is '5318'
    journals = emp_research_papers.objects.filter(pf_no="5318", rtype='Journal').order_by('-pyear').values()

    return JsonResponse(list(journals), safe=False)


def get_conference(request):
    # Fetch all entries where pf_no is '5318'
    conference = emp_research_papers.objects.filter(pf_no="5318", rtype='Conference').order_by('-year').values()

    return JsonResponse(list(conference), safe=False)

def get_achievements(request):
    # Fetch all entries where pf_no is '5318'
    achievements = emp_achievement.objects.filter(pf_no="5318").order_by('-a_year').values()

    return JsonResponse(list(achievements), safe=False)

def get_talks(request):
    # Fetch all entries where pf_no is '5318'
    talks = emp_expert_lectures.objects.filter(pf_no="5318").values()

    return JsonResponse(list(talks), safe=False)


def edit_research_project(request, pk):
    """
    Edit an existing research project entry in the emp_research_projects table.

    This view handles the editing of a research project based on the provided
    primary key (pk). The project details are updated using the data from a
    POST request. If the request method is not POST, an error response is returned.

    Args:
        request (HttpRequest): The request object containing POST data for the
        project to be updated.
        pk (int): The primary key of the research project to be edited.

    Returns:
        JsonResponse: A response indicating the success or failure of the update
        operation. On success, returns a success message with status 200.
        On failure, returns the form errors with status 400.
        If the request method is invalid, returns an error message with status 400.
    """
    project = get_object_or_404(emp_research_projects, pk=pk)

    if request.method == 'POST':
        form = emp_research_projects(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return JsonResponse({'message': 'Project updated successfully.'}, status=200)
        else:
            return JsonResponse({'errors': form.errors}, status=400)
    
    return JsonResponse({'error': 'Invalid request method.'}, status=400)