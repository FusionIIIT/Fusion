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
from django.http import HttpResponse, HttpResponseRedirect
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
from django.views.decorators.csrf import csrf_exempt

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

    print("here", extra_info_list)

    # Return the data as a JSON response
    return JsonResponse(extra_info_list, safe=False)

# Main profile landing view
@csrf_exempt
def profile(request, username=None):

    if request.method == 'POST':
        print(request.POST.get('username'))
        user = get_object_or_404(User, username=request.POST.get('username'))
    else:
        if username:
            print("eis", username)
        else:
            user = get_object_or_404(User, username=request.GET.get('username'))

    extra_info = get_object_or_404(ExtraInfo, user=user)

    pf = extra_info.user_id
    print("pf", pf)

    # Forms and project management data
    project_r = Project_Registration.objects.filter(PI_id=pf).order_by('PI_id__user')
    project_ext = Project_Extension.objects.filter(project_id__PI_id=pf).order_by('project_id__PI_id__user')
    project_closure = Project_Closure.objects.filter(project_id__PI_id=pf).order_by('project_id__PI_id__user')
    project_reall = Project_Reallocation.objects.filter(project_id__PI_id=pf).order_by('project_id__PI_id__user')

    # Research data
    journal = emp_research_papers.objects.filter(pf_no=pf, rtype='Journal').order_by('-year')
    print(pf, "journal", journal)
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

# Dean RSPC Profile
@csrf_exempt
def rspc_profile(request):
    if request.method == 'POST':
        user = get_object_or_404(faculty_about, user=request.user)
        pf = user.user

        form = ConfrenceForm()  # Form can be excluded if not needed in the frontend response

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
    if request.method == 'POST':
        try:
            print("here")
            faculty = get_object_or_404(faculty_about, user_id = request.POST.get('user_id'))
            print(faculty)
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




# Views for deleting the EIS fields
@csrf_exempt
def achievementDelete(request):
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
    instance = emp_confrence_organised.objects.get(pk=request.POST['pk'])
    instance.delete()
    return JsonResponse({'success': True})

@csrf_exempt
def emp_consymDelete(request):
    instance = emp_confrence_organised.objects.get(pk=request.POST['pk'])
    instance.delete()
    return JsonResponse({'success': True})

@csrf_exempt
def emp_consultancy_projectsDelete(request):
    instance = emp_consultancy_projects.objects.get(pk=request.POST['pk'])
    instance.delete()
    return JsonResponse({'success': True})

@csrf_exempt
def emp_event_organizedDelete(request):
    instance = emp_event_organized.objects.get(pk=request.POST['pk'])
    instance.delete()
    return JsonResponse({'success': True})

@csrf_exempt
def emp_expert_lecturesDelete(request):
    instance = emp_expert_lectures.objects.get(pk=request.POST['pk'])
    instance.delete()
    return JsonResponse({'success': True})

@csrf_exempt
def emp_keynote_addressDelete(request):
    instance = emp_keynote_address.objects.get(pk=request.POST['pk'])
    instance.delete()
    return JsonResponse({'success': True})

@csrf_exempt
def emp_mtechphd_thesisDelete(request):
    instance = emp_mtechphd_thesis.objects.get(pk=request.POST['pk'])
    instance.delete()
    return JsonResponse({'success': True})

@csrf_exempt
def emp_patentsDelete(request):
    instance = emp_patents.objects.get(pk=request.POST['pk'])
    instance.delete()
    return JsonResponse({'success': True})

@csrf_exempt
def emp_published_booksDelete(request):
    instance = emp_published_books.objects.get(pk=request.POST['pk'])
    instance.delete()
    return JsonResponse({'success': True})
@csrf_exempt
def emp_research_papersDelete(request):
    instance = emp_research_papers.objects.get(pk=request.POST['pk'])
    instance.delete()
    return JsonResponse({'success': True})

@csrf_exempt
def emp_research_projectsDelete(request):
    instance = emp_research_projects.objects.get(pk=request.POST['pk'])
    instance.delete()
    return JsonResponse({'success': True})

@csrf_exempt
def emp_session_chairDelete(request):
    instance = emp_session_chair.objects.get(pk=request.POST['pk'])
    instance.delete()
    return JsonResponse({'success': True})

@csrf_exempt
def emp_journal_delete(request):
    instance = emp_research_papers.objects.get(pk=request.POST['pk'])
    instance.delete()
    return JsonResponse({'success': True})

@csrf_exempt
def emp_techtransferDelete(request):
    instance = emp_techtransfer.objects.get(pk=request.POST['pk'])
    instance.delete()
    return JsonResponse({'success': True})

@csrf_exempt
def emp_visitsDelete(request):
    instance = emp_visits.objects.get(pk=request.POST['pk'])
    instance.delete()
    return JsonResponse({'success': True})


# Views for inserting fields in EIS
@csrf_exempt
def pg_insert(request):
    user = get_object_or_404(faculty_about, user_id=request.POST.get('user_id'))
    pf = user.user_id
    # eis = emp_mtechphd_thesis()

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
    user = get_object_or_404(faculty_about, user_id=request.POST.get('user_id'))
    pf = user.user_id
    # eis = emp_mtechphd_thesis()

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
    if request.method=='POST':
        user = get_object_or_404(faculty_about, user_id=request.POST.get('user_id'))
        pf = user.user_id

        # eis = emp_visits()

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
        return JsonResponse({'x' : 'Your data is saved '})

# View for editing persnal Information

@csrf_exempt
def ivisit_insert(request):
    user = get_object_or_404(faculty_about, user_id=request.POST.get('user_id'))
    pf = user.user_id

    # eis = emp_visits()

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
    return JsonResponse({'x' : 'Your data is saved '})


#Function to save journal of employee
@csrf_exempt
def journal_insert(request):
    if request.method=="POST":
        user = get_object_or_404(faculty_about, user_id=request.POST['user_id'])
        print(user.user_id)
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
        return JsonResponse({'x' : 'Your data is saved '})
    
@csrf_exempt
def editjournal(request):
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
    volume_no = request.POST.get('volume')
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
    return JsonResponse({'x' : 'Your data is updated '})
    
@csrf_exempt
def editforeignvisit(request):
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
    return JsonResponse({'x' : 'Your data is updated '})


@csrf_exempt
def editindianvisit(request):
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
        return JsonResponse({'x' : 'Your data is saved '})

@csrf_exempt
def editconference(request):
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
    print(request.POST)
    user = get_object_or_404(faculty_about, user_id=request.POST.get('user_id'))
    pf = user.user_id
    print(pf)
    eis = emp_published_books()
    eis.pf_no = pf
    eis.p_type = request.POST.get('book_p_type')
    eis.title = request.POST.get('book_title')
    eis.publisher = request.POST.get('book_publisher')
    eis.pyear = request.POST.get('book_year')
    eis.authors = request.POST.get('book_author')
    eis.save()
    return JsonResponse({'x' : 'Your data is saved '})


@csrf_exempt
def editbooks(request):
    eis = emp_published_books.objects.get(pk=request.POST.get('bookspk'))
    eis.p_type = request.POST.get('book_p_type')
    eis.title = request.POST.get('book_title')
    eis.publisher = request.POST.get('book_publisher')
    eis.pyear = request.POST.get('book_year')
    eis.authors = request.POST.get('book_author')
    eis.save()
    return JsonResponse({'x' : 'Your data is updated '})

@csrf_exempt
def consym_insert(request):
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

    print(x)

    eis.start_date = datetime.datetime.strptime(x, "%b %d %Y")

    x = request.POST.get('conference_end_date')
    x = x.split()
    x = x[1:4]
    x = ' '.join(x)
    print(x)

    eis.end_date = datetime.datetime.strptime(x, "%b %d %Y")

    eis.save()
    return JsonResponse({ "success": True})


@csrf_exempt
def editconsym(request):
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

    print(x)

    eis.start_date = datetime.datetime.strptime(x, "%b %d %Y")

    x = request.POST.get('conference_end_date')
    x = x.split()
    x = x[1:4]
    x = ' '.join(x)
    print(x)

    eis.end_date = datetime.datetime.strptime(x, "%b %d %Y")

    eis.save()
    return JsonResponse({'success': True})

@csrf_exempt
def event_insert(request):
    user = get_object_or_404(faculty_about, user_id=request.POST.get('user_id'))
    pf = user.user_id
    eis = emp_event_organized()

    # if (request.POST.get('event_id')==None or request.POST.get('event_id')==""):
    #     eis = emp_event_organized()
    # else:
    #     eis = get_object_or_404(emp_event_organized, id=request.POST.get('event_id'))
    
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
    return JsonResponse({'x' : 'Your data is saved '})

@csrf_exempt
def editevent(request):
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
    user = get_object_or_404(faculty_about, user_id=request.POST.get('user_id'))
    pf = user.user_id
    # eis = emp_achievement()

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
    return JsonResponse({'x' : 'Your data is saved '})

@csrf_exempt
def talk_insert(request):
    user = get_object_or_404(faculty_about, user_id=request.POST.get('user_id'))
    pf = user.user_id
    # eis = emp_expert_lectures()
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
    return JsonResponse({'x' : 'Your data is saved '})

@csrf_exempt
def chaired_insert(request):
    user = get_object_or_404(faculty_about, user_id=request.POST.get('user_id'))
    pf = user.user_id

    eis = emp_session_chair()

    # if (request.POST.get('ses_id')==None or request.POST.get('ses_id')==""):
    #     eis = emp_session_chair()
    # else:
    #     eis = get_object_or_404(emp_session_chair, id=request.POST.get('ses_id'))
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
    return JsonResponse({'x' : 'Your data is saved '})

@csrf_exempt
def keynote_insert(request):
    user = get_object_or_404(faculty_about, user_id=request.POST.get('user_id'))
    pf = user.user_id

    eis = emp_keynote_address()

    # if (request.POST.get('keyid')==None or request.POST.get('keyid')==""):
    #     eis = emp_keynote_address()
    # else:
    #     eis = get_object_or_404(emp_keynote_address, id=request.POST.get('keyid'))
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
    return JsonResponse({'x' : 'Your data is saved '})

@csrf_exempt
def project_insert(request):
    user = get_object_or_404(faculty_about, user_id=request.POST.get('user_id'))
    pf = user.user_id

    # eis = emp_research_projects()

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

    print(x)

    eis.start_date = datetime.datetime.strptime(x, "%b %d %Y")

    x = request.POST.get('end')
    x = x.split()
    x = x[1:4]
    x = ' '.join(x)
    print(x)

    eis.finish_date = datetime.datetime.strptime(x, "%b %d %Y")

    x = request.POST.get('sub')
    x = x.split()
    x = x[1:4]
    x = ' '.join(x)
    print(x)

    eis.date_submission = datetime.datetime.strptime(x, "%b %d %Y")

    eis.save()
    return JsonResponse({'success': True})

@csrf_exempt
def consult_insert(request):
    user = get_object_or_404(faculty_about, user_id=request.POST.get('user_id'))
    pf = user.user_id
    # eis = emp_consultancy_projects()
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

    print(x)

    eis.start_date = datetime.datetime.strptime(x, "%b %d %Y")
    x = request.POST.get('end')
    x = x.split()
    x = x[1:4]
    x = ' '.join(x)

    print(x)

    eis.end_date = datetime.datetime.strptime(x, "%b %d %Y")
    eis.save()
    return JsonResponse({'x' : 'Your data is saved '})

@csrf_exempt
def patent_insert(request):
    user = get_object_or_404(faculty_about, user_id=request.POST.get('user_id'))
    pf = user.user_id
    # eis = emp_patents()

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
    return JsonResponse({'x' : 'Your data is saved '})

@csrf_exempt
def transfer_insert(request):
    user = get_object_or_404(faculty_about, user_id=request.POST.get('user_id'))
    pf = user.user_id
    eis = emp_techtransfer()

    # if (request.POST.get('tech_id')==None or request.POST.get('tech_id')==""):
    #     eis = emp_techtransfer()
    # else:
    #     eis = get_object_or_404(emp_techtransfer, id=request.POST.get('tech_id'))
    eis.pf_no = pf
    eis.details = request.POST.get('details')
    eis.save()
    return JsonResponse({'x' : 'Your data is saved '})

def get_personal_info(request):
    # Fetch all entries where pf_no is '5318'
    projects = faculty_about.objects.filter(user_id=request.GET.get("pfNo")).values()

    return JsonResponse(list(projects), safe=False)


def get_research_projects(request):
    # Fetch all entries where pf_no is '5318'
    projects = emp_research_projects.objects.filter(pf_no=request.GET.get("pfNo")).values()

    return JsonResponse(list(projects), safe=False)

def get_consultancy_projects(request):
    # Fetch all entries where pf_no is '5318'
    projects = emp_consultancy_projects.objects.filter(pf_no=request.GET.get("pfNo")).values()

    return JsonResponse(list(projects), safe=False)

def get_patents(request):
    # Fetch all entries where pf_no is '5318'
    projects = emp_patents.objects.filter(pf_no=request.GET.get("pfNo")).values()

    return JsonResponse(list(projects), safe=False)

def get_pg_thesis(request):
    # Fetch all entries where pf_no is '5318'
    projects = emp_mtechphd_thesis.objects.filter(pf_no=request.GET.get("pfNo"), degree_type='1').values()

    return JsonResponse(list(projects), safe=False)

def get_phd_thesis(request):
    # Fetch all entries where pf_no is '5318'
    projects = emp_mtechphd_thesis.objects.filter(pf_no=request.GET.get("pfNo"), degree_type='2').values()

    return JsonResponse(list(projects), safe=False)

def get_event(request):
    # Fetch all entries where pf_no is '5318'
    projects = emp_event_organized.objects.filter(pf_no=request.GET.get("pfNo")).values()

    return JsonResponse(list(projects), safe=False)

def get_fvisits(request):
    # Fetch all entries where pf_no is '5318'
    projects = emp_visits.objects.filter(pf_no=request.GET.get("pfNo"), v_type='2').values()

    return JsonResponse(list(projects), safe=False)

def get_ivisits(request):
    # Fetch all entries where pf_no is '5318'
    projects = emp_visits.objects.filter(pf_no=request.GET.get("pfNo"),  v_type='1').values()

    return JsonResponse(list(projects), safe=False)

def get_consym(request):
    # Fetch all entries where pf_no is '5318'
    projects = emp_confrence_organised.objects.filter(pf_no=request.GET.get("pfNo")).values()

    return JsonResponse(list(projects), safe=False)

def get_books(request):
    # Fetch all entries where pf_no is '5318'
    books = emp_published_books.objects.filter(pf_no=request.GET.get("pfNo")).order_by('-pyear').values()
    
    return JsonResponse(list(books), safe=False)

def get_journals(request):
    journals = emp_research_papers.objects.filter(pf_no=request.GET.get("pfNo")).values()
    print(journals)

    return JsonResponse(list(journals), safe=False)

def get_conference(request):
    # Fetch all entries where pf_no is '5318'
    conference = emp_research_papers.objects.filter(pf_no=request.GET.get("pfNo")).order_by('-year').values()

    return JsonResponse(list(conference), safe=False)

def get_achievements(request):
    # Fetch all entries where pf_no is '5318'
    achievements = emp_achievement.objects.filter(pf_no=request.GET.get("pfNo")).order_by('-a_year').values()

    return JsonResponse(list(achievements), safe=False)

def get_talks(request):
    # Fetch all entries where pf_no is '5318'
    talks = emp_expert_lectures.objects.filter(pf_no=request.GET.get("pfNo")).values()

    return JsonResponse(list(talks), safe=False)


def edit_research_project(request, pk):
    project = get_object_or_404(emp_research_projects, pk=pk)

    if request.method == 'POST':
        form = emp_research_projects(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return JsonResponse({'message': 'Project updated successfully.'}, status=200)
        else:
            return JsonResponse({'errors': form.errors}, status=400)
    
    return JsonResponse({'error': 'Invalid request method.'}, status=400)