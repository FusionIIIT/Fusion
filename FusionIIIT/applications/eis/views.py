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

from applications.eis import admin
from applications.globals.models import ExtraInfo, HoldsDesignation, DepartmentInfo
from django.http.response import JsonResponse
from applications.office_module.models import (Project_Closure, Project_Extension, Project_Reallocation,Project_Registration)
from .forms import *
from .models import *
from django.core.files.storage import FileSystemStorage
import logging

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

# Main profile landing view
def profile(request, username=None):
    user = get_object_or_404(User, username=username) if username else request.user
    extra_info = get_object_or_404(ExtraInfo, user=user)
    if extra_info.user_type != 'faculty':
        return redirect('/')
    pf = extra_info.id

    form = ConfrenceForm()

    # project management views

    project_r=Project_Registration.objects.filter(PI_id=pf).order_by('PI_id__user')
    project_ext=Project_Extension.objects.filter(project_id__PI_id=pf).order_by('project_id__PI_id__user')
    project_closure=Project_Closure.objects.filter(project_id__PI_id=pf).order_by('project_id__PI_id__user')
    project_reall=Project_Reallocation.objects.filter(project_id__PI_id=pf).order_by('project_id__PI_id__user')
    ############################

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
    for fvisit in fvisits:
        fvisit.countryfull = countries[fvisit.country]
    consymps = emp_confrence_organised.objects.filter(pf_no=pf).order_by('-date_entry')
    awards = emp_achievement.objects.filter(pf_no=pf).order_by('-date_entry')
    talks = emp_expert_lectures.objects.filter(pf_no=pf).order_by('-date_entry')
    chairs = emp_session_chair.objects.filter(pf_no=pf).order_by('-date_entry')
    keynotes = emp_keynote_address.objects.filter(pf_no=pf).order_by('-date_entry')
    events = emp_event_organized.objects.filter(pf_no=pf).order_by('-start_date')
    y=[]
    for r in range(1995, (datetime.datetime.now().year + 1)):
        y.append(r)
    try:
        pers = get_object_or_404(faculty_about, user = user)
    except:
        pers = None
    # edited 26March
    a1 = HoldsDesignation.objects.select_related('user','working','designation').filter(working = user)
    flag_rspc = 0
    for i in a1:
        if(str(i.designation)=='Dean (RSPC)'):
            flag_rspc = 1

    # done edit

    #design = HoldsDesignation.objects.filter(working=user)
    design=a1
    desig=[]
    for i in design:
        desig.append(str(i.designation))

    context = {'user': user,
               'desig':desig,
               'pf':pf,
               'flag_rspc':flag_rspc,
               'journal':journal,
               'conference': conference,
               'books': books,
               'projects': projects,
               'form':form,
               'consultancy':consultancy,
               'patents':patents,
               'techtransfers':techtransfers,
               'mtechs':mtechs,
               'phds':phds,
               'fvisits':fvisits,
               'ivisits': ivisits,
               'consymps':consymps,
               'awards':awards,
               'talks':talks,
               'chairs':chairs,
               'keynotes':keynotes,
               'events':events,
               'year_range':y,
               'pers':pers,
               'project_r':project_r,
               'project_ext':project_ext,
               'project_closure':project_closure,
               'project_reall':project_reall

               }
    return render(request, 'eisModulenew/profile.html', context)

# Dean RSPC Profile

def rspc_profile(request):
    user = get_object_or_404(faculty_about, user=request.user)
    pf = user.user

    form = ConfrenceForm()

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
    for fvisit in fvisits:
        fvisit.countryfull = countries[fvisit.country]
    consymps = emp_confrence_organised.objects.all().order_by('-start_date')
    awards = emp_achievement.objects.all().order_by('-a_year', '-a_month')
    talks = emp_expert_lectures.objects.all().order_by('-l_year', '-a_month')
    chairs = emp_session_chair.objects.all().order_by('-start_date')
    keynotes = emp_keynote_address.objects.all().order_by('-start_date')
    events = emp_event_organized.objects.all().order_by('-start_date')
    y=[]
    for r in range(1995, (datetime.datetime.now().year + 1)):
        y.append(r)

    pers = get_object_or_404(faculty_about, user = request.user)
    design = HoldsDesignation.objects.select_related('user','working','designation').filter(working=request.user)

    desig=[]
    for i in design:
        desig.append(str(i.designation))
    context = {'user': user,
               'desig':desig,
               'pf':pf,
               'journal':journal,
               'conference': conference,
               'books': books,
               'projects': projects,
               'form':form,
               'consultancy':consultancy,
               'patents':patents,
               'techtransfers':techtransfers,
               'mtechs':mtechs,
               'phds':phds,
               'fvisits':fvisits,
               'ivisits': ivisits,
               'consymps':consymps,
               'awards':awards,
               'talks':talks,
               'chairs':chairs,
               'keynotes':keynotes,
               'events':events,
               'year_range':y,
               'pers':pers
               }
    return render(request, 'eisModulenew/rspc_profile.html', context)

# View for editing persnal Information
def persinfo(request):
    if request.method == 'POST':
        try:
            faculty = get_object_or_404(faculty_about, user = request.user)
            contact = request.POST['contact']
            contact = contact[6:]
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
def achievementDelete(request, pk):
    instance = emp_achievement.objects.get(pk=pk)
    instance.delete()
    return redirect('/profile/?page14=1')

def emp_confrence_organisedDelete(request, pk):
    instance = emp_confrence_organised.objects.get(pk=pk)
    instance.delete()
    return redirect('globals:profile')

def emp_consymDelete(request, pk, sr, mark):
    instance = emp_confrence_organised.objects.get(pk=pk)
    page = int(sr)//10
    page = page+1
    url = ""
    if mark== '13':
        url = '/profile/?page13='+str(page)
    instance.delete()
    return redirect(url)

def emp_consultancy_projectsDelete(request, pk,sr,mark):
    instance = emp_consultancy_projects.objects.get(pk=pk)
    page = int(sr)//10
    page = page+1
    url = '/profile/?page5='+str(page)
    instance.delete()
    return redirect(url)

def emp_event_organizedDelete(request, pk, sr, mark):
    instance = emp_event_organized.objects.get(pk=pk)
    page = int(sr)//10
    page = page+1
    url = ""
    if mark== '12':
        url = '/profile/?page12='+str(page)
    instance.delete()
    return redirect(url)

def emp_expert_lecturesDelete(request, pk):
    instance = emp_expert_lectures.objects.get(pk=pk)
    instance.delete()
    return redirect('/profile/?page15=1')

def emp_keynote_addressDelete(request, pk):
    instance = emp_keynote_address.objects.get(pk=pk)
    instance.delete()
    return redirect('eis:profile')

def emp_mtechphd_thesisDelete(request, pk, sr,mark):
    instance = emp_mtechphd_thesis.objects.get(pk=pk)
    page = int(sr)//10
    page = page+1
    url = ""
    if mark == 1:
        url = '/profile/?page8='+str(page)
    else :
        url = '/profile/?page9='+str(page)
    instance.delete()
    return redirect(url)

def emp_patentsDelete(request, pk,sr,mark):
    instance = emp_patents.objects.get(pk=pk)
    page = int(sr)//10
    page = page+1
    url = '/profile/?page6='+str(page)
    instance.delete()
    return redirect(url)

def emp_published_booksDelete(request, pk, sr, mark):
    instance = emp_published_books.objects.get(pk=pk)
    page = int(sr)//10
    page = page+1
    url = '/profile/?page2='+str(page)
    instance.delete()
    return redirect(url)

def emp_research_papersDelete(request, pk, sr,mark):
    instance = emp_research_papers.objects.get(pk=pk)
    page = int(sr)//10
    page = page+1
    url = ""
    if mark== '1':
        url = '/profile/?page='+str(page)
    if mark== '2':
        url = '/profile/?page3='+str(page)
    instance.delete()
    return redirect(url)

def emp_research_projectsDelete(request, pk,sr,mark):
    instance = emp_research_projects.objects.get(pk=pk)
    page = int(sr)//10
    page = page+1
    url = '/profile/?page4='+str(page)
    instance.delete()
    return redirect(url)

def emp_session_chairDelete(request, pk):
    instance = emp_session_chair.objects.get(pk=pk)
    instance.delete()
    return redirect('eis:profile')

def emp_techtransferDelete(request, pk,sr,mark):
    instance = emp_techtransfer.objects.get(pk=pk)
    page = int(sr)//10
    page = page+1
    url = '/profile/?page7='+str(page)
    instance.delete()
    return redirect(url)

def emp_visitsDelete(request, pk, sr, mark):
    instance = emp_visits.objects.get(pk=pk)
    page = int(sr)//10
    page = page+1
    url = ""
    if mark== '10':
        url = '/profile/?page10='+str(page)
    if mark== '11':
        url = '/profile/?page11='+str(page)
    instance.delete()
    return redirect(url)


# Views for inserting fields in EIS
def pg_insert(request):
    user = get_object_or_404(ExtraInfo, user=request.user)
    pf = user.id

    if (request.POST.get('pg_id')==None or request.POST.get('pg_id')==""):
        eis = emp_mtechphd_thesis()
    else:
        eis = get_object_or_404(emp_mtechphd_thesis, id=request.POST.get('pg_id'))
    eis.user = request.user
    eis.pf_no = pf
    eis.title = request.POST.get('title')
    eis.s_year = request.POST.get('s_year')
    eis.a_month = request.POST.get('month')
    eis.supervisors = request.POST.get('sup')
    eis.rollno = request.POST.get('roll')
    eis.s_name = request.POST.get('name')

    eis.save()
    return redirect('/profile/?page8=1')

def phd_insert(request):
    user = get_object_or_404(ExtraInfo, user=request.user)
    pf = user.id

    if (request.POST.get('phd_id')==None or request.POST.get('phd_id')==""):
        eis = emp_mtechphd_thesis()
    else:
        eis = get_object_or_404(emp_mtechphd_thesis, id=request.POST.get('phd_id'))
    eis.user = request.user
    eis.pf_no = pf
    eis.degree_type = 2
    eis.title = request.POST.get('title')
    eis.s_year = request.POST.get('s_year')
    eis.a_month = request.POST.get('month')
    eis.supervisors = request.POST.get('sup')
    eis.rollno = request.POST.get('roll')
    eis.s_name = request.POST.get('name')

    eis.save()
    return redirect('/profile/?page9=1')

def fvisit_insert(request):
    user = get_object_or_404(ExtraInfo, user=request.user)
    pf = user.id

    if (request.POST.get('fvisit_id')==None or request.POST.get('fvisit_id')==""):
        eis = emp_visits()
    else:
        eis = get_object_or_404(emp_visits, id=request.POST.get('fvisit_id'))
    eis.user = request.user
    eis.pf_no = pf
    eis.v_type = 2
    eis.country = request.POST.get('country').upper()
    eis.place = request.POST.get('place')
    eis.purpose = request.POST.get('purpose')
    try:
        eis.start_date = datetime.datetime.strptime(request.POST.get('start_date'), "%B %d, %Y")
    except:
        eis.start_date = datetime.datetime.strptime(request.POST.get('start_date'), "%b. %d, %Y")
    try:
        eis.end_date = datetime.datetime.strptime(request.POST.get('end_date'), "%B %d, %Y")
    except:
        eis.end_date = datetime.datetime.strptime(request.POST.get('end_date'), "%b. %d, %Y")

    eis.save()
    return redirect('/profile/?page10=1')

def ivisit_insert(request):
    user = get_object_or_404(ExtraInfo, user=request.user)
    pf = user.id

    if (request.POST.get('ivisit_id')==None or request.POST.get('ivisit_id')==""):
        eis = emp_visits()
    else:
        eis = get_object_or_404(emp_visits, id=request.POST.get('ivisit_id'))
    eis.user = request.user
    eis.pf_no = pf
    eis.v_type = 1
    eis.country = request.POST.get('country2')
    eis.place = request.POST.get('place2')
    eis.purpose = request.POST.get('purpose2')
    try:
        eis.start_date = datetime.datetime.strptime(request.POST.get('start_date2'), "%B %d, %Y")
    except:
        eis.start_date = datetime.datetime.strptime(request.POST.get('start_date2'), "%b. %d, %Y")
    try:
        eis.end_date = datetime.datetime.strptime(request.POST.get('end_date2'), "%B %d, %Y")
    except:
        eis.end_date = datetime.datetime.strptime(request.POST.get('end_date2'), "%b. %d, %Y")

    eis.save()
    return redirect('/profile/?page11=1')


#Function to save journal of employee
def journal_insert(request):
    user = get_object_or_404(ExtraInfo, user=request.user)
    eis = emp_research_papers.objects.create(pf_no = user.id)
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
    return redirect('/profile/?page=1')


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
    page = int(request.POST.get('index'))//10
    page = page+1
    url = "/profile/?page="+str(page)
    return redirect(url)

def editforeignvisit(request):
    eis = emp_visits.objects.get(pk=request.POST.get('foreignvisitpk'))
    eis.country = request.POST.get('country')
    eis.place = request.POST.get('place')
    eis.purpose = request.POST.get('purpose')
    x = request.POST.get('start_date')
    if x[:5] == "Sept." :
            x = "Sep." + x[5:]
    try:
        eis.start_date = datetime.datetime.strptime(x, "%B %d, %Y")
    except:
        eis.start_date = datetime.datetime.strptime(x, "%b. %d, %Y")
    x = request.POST.get('end_date')
    if x[:5] == "Sept." :
            x = "Sep." + x[5:]
    try:
        eis.end_date = datetime.datetime.strptime(x, "%B %d, %Y")
    except:
        eis.end_date = datetime.datetime.strptime(x, "%b. %d, %Y")
    eis.save()
    page = int(request.POST.get('index10'))//10
    page = page+1
    url = "/profile/?page10="+str(page)
    return redirect(url)

def editindianvisit(request):
    eis = emp_visits.objects.get(pk=request.POST.get('indianvisitpk'))
    eis.country = request.POST.get('country2')
    eis.place = request.POST.get('place2')
    eis.purpose = request.POST.get('purpose2')
    x = request.POST.get('start_date2')
    if x[:5] == "Sept." :
            x = "Sep." + x[5:]
    try:
        eis.start_date = datetime.datetime.strptime(x, "%B %d, %Y")
    except:
        eis.start_date = datetime.datetime.strptime(x, "%b. %d, %Y")
    x = request.POST.get('end_date2')
    if x[:5] == "Sept." :
            x = "Sep." + x[5:]
    try:
        eis.end_date = datetime.datetime.strptime(x, "%B %d, %Y")
    except:
        eis.end_date = datetime.datetime.strptime(x, "%b. %d, %Y")
    eis.save()
    page = int(request.POST.get('index11'))//10
    page = page+1
    url = "/profile/?page11="+str(page)
    return redirect(url)



def conference_insert(request):
    user = get_object_or_404(ExtraInfo, user=request.user)
    pf = user.id
    eis = emp_research_papers()
    eis.user = request.user
    eis.pf_no = pf
    eis.rtype = 'Conference'
    eis.authors = request.POST.get('authors3')
    eis.co_authors = request.POST.get('co_author3')
    eis.title_paper = request.POST.get('title3')
    try:
        myfile = request.FILES['journal3']
        fs = FileSystemStorage()
        filename = fs.save(myfile.name, myfile)
        uploaded_file_url = fs.url(filename)
        eis.paper=uploaded_file_url
    except:
        logging.warning('Journal file not Uploaded')
    eis.name = request.POST.get('name3')
    eis.venue = request.POST.get('venue3')
    if request.POST.get('page_no3') != '':
        eis.page_no = request.POST.get('page_no3')
    if request.POST.get('isbn_no3') != '':
        eis.isbn_no = request.POST.get('isbn_no3')
    if request.POST.get('year3') != '':
        eis.year = request.POST.get('year3')
    eis.status = request.POST.get('status3')
    if(request.POST.get('doi3') != None and request.POST.get('doi3') != '' and request.POST.get('doi3') != 'None'):
        x = request.POST.get('doi3')
        if x[:-10] == ', midnight':
            x = x[0:-10]
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
    if (request.POST.get('doa3') != None and request.POST.get('doa3') != '' and request.POST.get('doa3') != 'None'):
        x = request.POST.get('doa3')
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

    if (request.POST.get('dop3') != None and request.POST.get('dop3') != '' and request.POST.get('dop3') != 'None'):
        x = request.POST.get('dop3')
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
    if (request.POST.get('dos3') != None and request.POST.get('dos3') != '' and request.POST.get('dos3') != 'None'):
        x = request.POST.get('dos3')

        if x[:5] == "Sept." :
            x = "Sep." + x[5:]
        try:
            eis.date_submission = datetime.datetime.strptime(
                x, "%B %d, %Y")
        except:
            eis.date_submission = datetime.datetime.strptime(
                x, "%b. %d, %Y")
    eis.save()
    return redirect('/profile/?page3=1')

def editconference(request):
    eis = emp_research_papers.objects.get(pk=request.POST.get('conferencepk'))
    eis.authors = request.POST.get('authors3')
    eis.co_authors = request.POST.get('co_author3')
    eis.title_paper = request.POST.get('title3')
    try:
        myfile = request.FILES['journal3']
        fs = FileSystemStorage()
        filename = fs.save(myfile.name, myfile)
        uploaded_file_url = fs.url(filename)
        eis.paper=uploaded_file_url
    except:
        logging.warning('Journal File not Uploaded.')

    eis.name = request.POST.get('name3')
    eis.venue = request.POST.get('venue3')
    isbn  = request.POST.get('isbn_no3')

    eis.page_no = request.POST.get('page_no3')

    eis.year = request.POST.get('year3')
    eis.status = request.POST.get('status3')
    if(request.POST.get('doi3') != None and request.POST.get('doi3') != '' and request.POST.get('doi3') != 'None'):
        x = request.POST.get('doi3')
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
    if (request.POST.get('doa3') != None and request.POST.get('doa3') != '' and request.POST.get('doa3') != 'None'):
        x = request.POST.get('doa3')
        if x[:5] == "Sept." :
            x = "Sep." + x[5:]
        try:
            eis.date_acceptance = datetime.datetime.strptime(
                x, "%B %d, %Y")
        except:
            eis.date_acceptance = datetime.datetime.strptime(
                x, "%b. %d, %Y")

    if (request.POST.get('dop3') != None and request.POST.get('dop3') != '' and request.POST.get('dop3') != 'None'):
        x = request.POST.get('dop3')
        if x[:5] == "Sept." :
            x = "Sep." + x[5:]
        try:
            eis.date_publication = datetime.datetime.strptime(
                x, "%B %d, %Y")
        except:
            eis.date_publication = datetime.datetime.strptime(
                x, "%b. %d, %Y")
    if (request.POST.get('dos3') != None and request.POST.get('dos3') != '' and request.POST.get('dos3') != 'None'):
        x = request.POST.get('dos3')
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
    page = int(request.POST.get('index3'))//10
    page = page+1
    url = "/profile/?page3="+str(page)
    return redirect(url)


def book_insert(request):
    user = get_object_or_404(ExtraInfo, user=request.user)
    pf = user.id
    eis = emp_published_books()
    eis.user = request.user
    eis.pf_no = pf
    eis.p_type = request.POST.get('book_p_type')
    eis.title = request.POST.get('book_title')
    eis.publisher = request.POST.get('book_publisher')
    eis.pyear = request.POST.get('book_year')
    eis.authors = request.POST.get('book_author')
    eis.save()
    return redirect('/profile/?page2=1')

def editbooks(request):
    eis = emp_published_books.objects.get(pk=request.POST.get('bookspk2'))
    eis.p_type = request.POST.get('book_p_type')
    eis.title = request.POST.get('book_title')
    eis.publisher = request.POST.get('book_publisher')
    eis.pyear = request.POST.get('book_')
    eis.authors = request.POST.get('book_author')
    eis.save()
    page = int(request.POST.get('index15'))//10
    page = page+1
    url = "/profile/?page2="+str(page)
    return redirect(url)

def consym_insert(request):
    user = get_object_or_404(ExtraInfo, user=request.user)
    pf = user.id
    eis = emp_confrence_organised()
    eis.user = request.user
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
    if x[:5] == "Sept." :
            x = "Sep." + x[5:]
    try:
        eis.start_date = datetime.datetime.strptime(x, "%B %d, %Y")
    except:
        eis.start_date = datetime.datetime.strptime(x, "%b. %d, %Y")
    x = request.POST.get('conference_end_date')
    if x[:5] == "Sept." :
            x = "Sep." + x[5:]
    try:
        eis.end_date = datetime.datetime.strptime(x, "%B %d, %Y")
    except:
        eis.end_date = datetime.datetime.strptime(x, "%b. %d, %Y")
    eis.save()
    return redirect('/profile/?page13=1')

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
    if x[:5] == "Sept." :
            x = "Sep." + x[5:]
    try:
        eis.start_date = datetime.datetime.strptime(x, "%B %d, %Y")
    except:
        eis.start_date = datetime.datetime.strptime(x, "%b. %d, %Y")
    x = request.POST.get('conference_end_date')
    if x[:5] == "Sept." :
            x = "Sep." + x[5:]
    try:
        eis.end_date = datetime.datetime.strptime(x, "%B %d, %Y")
    except:
        eis.end_date = datetime.datetime.strptime(x, "%b. %d, %Y")
    eis.save()
    page = int(request.POST.get('index13'))//10
    page = page+1
    url = "/profile/?page13="+str(page)

    return redirect('/profile/?page13=1')

def event_insert(request):
    user = get_object_or_404(ExtraInfo, user=request.user)
    pf = user.id

    if (request.POST.get('event_id')==None or request.POST.get('event_id')==""):
        eis = emp_event_organized()
    else:
        eis = get_object_or_404(emp_event_organized, id=request.POST.get('event_id'))
    eis.pf_no = pf
    eis.user = request.user
    eis.type = request.POST.get('event_type')
    if(eis.type == 'Any Other'):
        if(request.POST.get('myDIV')!= None or request.POST.get('myDIV') != ""):
            eis.type = request.POST.get('myDIV')
    eis.sponsoring_agency = request.POST.get('sponsoring_agency')
    eis.name = request.POST.get('event_name')
    eis.venue = request.POST.get('event_venue')
    eis.role = request.POST.get('event_role')
    try:
        eis.start_date = datetime.datetime.strptime(request.POST.get('event_start_date'), "%B %d, %Y")
    except:
        eis.start_date = datetime.datetime.strptime(request.POST.get('event_start_date'), "%b. %d, %Y")
    try:
        eis.end_date = datetime.datetime.strptime(request.POST.get('event_end_date'), "%B %d, %Y")
    except:
        eis.end_date = datetime.datetime.strptime(request.POST.get('event_end_date'), "%b. %d, %Y")
    eis.save()
    return redirect('/profile/?page12=1')

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
    if x[:5] == "Sept." :
        x = "Sep." + x[5:]
    try:
        eis.start_date = datetime.datetime.strptime(x, "%B %d, %Y")
    except:
        eis.start_date = datetime.datetime.strptime(x, "%b. %d, %Y")
    x = request.POST.get('event_end_date')
    if x[:5] == "Sept." :
        x = "Sep." + x[5:]
    try:
        eis.end_date = datetime.datetime.strptime(x, "%B %d, %Y")
    except:
        eis.end_date = datetime.datetime.strptime(x, "%b. %d, %Y")
    eis.save()
    page = int(request.POST.get('index12'))//10
    page = page+1
    url = "/profile/?page12="+str(page)
    return redirect(url)

def award_insert(request):
    user = get_object_or_404(ExtraInfo, user=request.user)
    pf = user.id

    if (request.POST.get('ach_id')==None or request.POST.get('ach_id')==""):
        eis = emp_achievement()
    else:
        eis = get_object_or_404(emp_achievement, id=request.POST.get('ach_id'))
    eis.pf_no = pf
    eis.user = request.user
    eis.a_type = request.POST.get('type')
    if(request.POST.get('a_day') != None and request.POST.get('a_day') != ""):
        eis.a_day = request.POST.get('a_day')
    if(request.POST.get('a_month') != None and request.POST.get('a_month') != ""):
        eis.a_month = request.POST.get('a_month')
    if(request.POST.get('a_year') != None and request.POST.get('a_year') != ""):
        eis.a_year = request.POST.get('a_year')
    eis.details = request.POST.get('details')

    eis.save()
    return redirect('/profile/?page14=1')

def talk_insert(request):
    user = get_object_or_404(ExtraInfo, user=request.user)
    pf = user.id

    if (request.POST.get('lec_id')==None or request.POST.get('lec_id')==""):
        eis = emp_expert_lectures()
    else:
        eis = get_object_or_404(emp_expert_lectures, id=request.POST.get('lec_id'))
    eis.user = request.user
    eis.pf_no = pf
    eis.l_type = request.POST.get('type')
    eis.place = request.POST.get('place')
    eis.title = request.POST.get('title')
    x = request.POST.get('l_date')
    if x[:5] == "Sept." :
            x = "Sep." + x[5:]
    try:
        eis.l_date = datetime.datetime.strptime(x, "%B %d, %Y")
    except:
        eis.l_date = datetime.datetime.strptime(x, "%b. %d, %Y")

    eis.save()
    return redirect('/profile/?page15=1')

def chaired_insert(request):
    user = get_object_or_404(ExtraInfo, user=request.user)
    pf = user.id

    if (request.POST.get('ses_id')==None or request.POST.get('ses_id')==""):
        eis = emp_session_chair()
    else:
        eis = get_object_or_404(emp_session_chair, id=request.POST.get('ses_id'))
    eis.user = request.user
    eis.pf_no = pf
    eis.event = request.POST.get('event')
    eis.name = request.POST.get('name')
    eis.s_year = request.POST.get('s_year')
    try:
        eis.start_date = datetime.datetime.strptime(request.POST.get('start'), "%B %d, %Y")
    except:
        eis.start_date = datetime.datetime.strptime(request.POST.get('start'), "%b. %d, %Y")
    try:
        eis.end_date = datetime.datetime.strptime(request.POST.get('end'), "%B %d, %Y")
    except:
        eis.end_date = datetime.datetime.strptime(request.POST.get('end'), "%b. %d, %Y")

    eis.save()
    return redirect('eis:profile')

def keynote_insert(request):
    user = get_object_or_404(ExtraInfo, user=request.user)
    pf = user.id

    if (request.POST.get('keyid')==None or request.POST.get('keyid')==""):
        eis = emp_keynote_address()
    else:
        eis = get_object_or_404(emp_keynote_address, id=request.POST.get('keyid'))
    eis.user = request.user
    eis.pf_no = pf
    eis.type = request.POST.get('type')
    eis.name = request.POST.get('name')
    eis.title = request.POST.get('title')
    eis.venue = request.POST.get('venue')
    eis.page_no = request.POST.get('page_no')
    eis.isbn_no = request.POST.get('isbn_no')
    eis.k_year = request.POST.get('k_year')
    try:
        eis.start_date = datetime.datetime.strptime(request.POST.get('start'), "%B %d, %Y")
    except:
        eis.start_date = datetime.datetime.strptime(request.POST.get('start'), "%b. %d, %Y")

    eis.save()
    return redirect('eis:profile')

def project_insert(request):
    user = get_object_or_404(ExtraInfo, user=request.user)
    pf = user.id

    if (request.POST.get('project_id')==None or request.POST.get('project_id')==""):
        eis = emp_research_projects()
    else:
        eis = get_object_or_404(emp_research_projects, id=request.POST.get('project_id'))
    eis.user = request.user
    eis.pf_no = pf
    eis.pi = request.POST.get('pi')
    eis.co_pi = request.POST.get('co_pi')
    eis.title = request.POST.get('title')
    eis.financial_outlay = request.POST.get('financial_outlay')
    eis.funding_agency = request.POST.get('funding_agency')
    eis.status = request.POST.get('status')
    x = request.POST.get('start')
    if x[:5] == "Sept." :
        x = "Sep." + x[5:]
    if (request.POST.get('start') != None and request.POST.get('start') != '' and request.POST.get('start') != 'None'):
        try:
            eis.start_date = datetime.datetime.strptime(x, "%B %d, %Y")
        except:
            eis.start_date = datetime.datetime.strptime(x, "%b. %d, %Y")
    x = request.POST.get('end')
    if x[:5] == "Sept." :
        x = "Sep." + x[5:]
    if (request.POST.get('end') != None and request.POST.get('end') != '' and request.POST.get('end') != 'None'):
        try:
            eis.finish_date = datetime.datetime.strptime(x, "%B %d, %Y")
        except:
            eis.finish_date = datetime.datetime.strptime(x, "%b. %d, %Y")
    x = request.POST.get('sub')
    if x[:5] == "Sept." :
        x = "Sep." + x[5:]
    if (request.POST.get('sub') != None and request.POST.get('sub') != '' and request.POST.get('sub') != 'None'):
        try:
            eis.date_submission = datetime.datetime.strptime(x, "%B %d, %Y")
        except:
            eis.date_submission = datetime.datetime.strptime(x, "%b. %d, %Y")
    eis.save()
    return redirect('/profile/?page4=1')

def consult_insert(request):
    print("=======================")
    user = get_object_or_404(ExtraInfo, user=request.user)
    pf = user.id
    print(">>>>>>>.",user,type(user))
    print(">>>>>>>",request.user,type(request.user))
    if (request.POST.get('consultancy_id')==None or request.POST.get('consultancy_id')==""):
        eis = emp_consultancy_projects()
    else:
        eis = get_object_or_404(emp_consultancy_projects, id=request.POST.get('consultancy_id'))
    eis.user = request.user
    eis.pf_no = pf
    eis.consultants = request.POST.get('consultants')
    eis.client = request.POST.get('client')
    eis.title = request.POST.get('title')
    eis.financial_outlay = request.POST.get('financial_outlay')
    x = request.POST.get('start')
    if x[:5] == "Sept." :
        x = "Sep." + x[5:]
    if (request.POST.get('start') != None and request.POST.get('start') != '' and request.POST.get('start') != 'None'):
        try:
            eis.start_date = datetime.datetime.strptime(x, "%B %d, %Y")
        except:
            eis.start_date = datetime.datetime.strptime(x, "%b. %d, %Y")
    x = request.POST.get('end')
    if x[:5] == "Sept." :
        x = "Sep." + x[5:]
    if (request.POST.get('end') != None and request.POST.get('end') != '' and request.POST.get('end') != 'None'):
        try:
            eis.end_date = datetime.datetime.strptime(x, "%B %d, %Y")
        except:
            eis.end_date = datetime.datetime.strptime(x, "%b. %d, %Y")
    eis.save()
    return redirect('/profile/?page5=1')

def patent_insert(request):
    user = get_object_or_404(ExtraInfo, user=request.user)
    pf = user.id

    if (request.POST.get('patent_id')==None or request.POST.get('patent_id')==""):
        eis = emp_patents()
    else:
        eis = get_object_or_404(emp_patents, id=request.POST.get('patent_id'))
    eis.user = request.user
    eis.pf_no = pf
    eis.p_no = request.POST.get('p_no')
    eis.earnings = request.POST.get('earnings')
    eis.title = request.POST.get('title')
    eis.p_year = request.POST.get('year')
    eis.status = request.POST.get('status')
    eis.a_month = request.POST.get('month')
    eis.save()
    return redirect('/profile/?page6=1')

def transfer_insert(request):
    user = get_object_or_404(ExtraInfo, user=request.user)
    pf = user.id

    if (request.POST.get('tech_id')==None or request.POST.get('tech_id')==""):
        eis = emp_techtransfer()
    else:
        eis = get_object_or_404(emp_techtransfer, id=request.POST.get('tech_id'))
    eis.pf_no = pf
    eis.details = request.POST.get('details')
    eis.save()
    return redirect('/profile/?page7=1')

def achievements(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['fileUpload']
            decoded_file = file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)
            c=1
            achieve = []
            for row in reader:
                e = emp_achievement()
                e.pf_no = row['pf_no']
                e.details = row['details']

                if (row['a_type'] == '1'):
                    e.a_type = 'Award'
                elif (row['a_type'] == '2'):
                    e.a_type = 'Honour'
                elif (row['a_type'] == '3'):
                    e.a_type = 'Prize'
                elif (row['a_type'] == '4'):
                    e.a_type = 'Other'

                if (row['a_day'] != '0' and row['a_day'] != None and row['a_day'] != ''):
                    e.a_day = int(row['a_day'])

                if (row['a_month'] != '0' and row['a_month'] != None and row['a_month'] != ''):
                    e.a_month = int(row['a_month'])

                if (row['a_year'] != '0' and row['a_year'] != None and row['a_year'] != ''):
                    e.a_year = int(row['a_year'])

                try:

                    if (row['date_entry'] == ' ' or row['date_entry'] == ''):
                        a = 1
                    else:
                        e.date_entry = row['date_entry']
                        e.date_entry=e.date_entry[:10]
                        e.date_entry = datetime.datetime.strptime(e.date_entry, "%Y-%m-%d").date()
                except:
                    a=1
                achieve.append(e)
            emp_achievement.objects.bulk_create(achieve)
            return HttpResponseRedirect('DONE')
    else:
        form = UploadFileForm()
    return render(request, 'eisModulenew/upload.html', {'form': form})


def confrence(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['fileUpload']
            decoded_file = file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)
            c=1
            confr = []
            for row in reader:
                e = emp_confrence_organised()
                e.pf_no = row['pf_no']
                e.venue = row['venue']
                e.name = row['name']
                e.k_year = int(row['k_year'])
                e.role1 = row['role1']
                e.role2 = row['role2']

                try:
                    if (row['start_date'] == ' ' or row['start_date'] == ''):
                        a=1
                    elif (row['start_date'] != '0000-00-00 00:00:00' and row['start_date'] != '0000-00-00'):
                        e.start_date = row['start_date']
                        e.start_date = e.start_date[:10]
                        if (row['start_date'] != '0000-00-00'):
                            e.start_date = datetime.datetime.strptime(e.start_date, "%Y-%m-%d").date()
                except:
                    a=1
                try:
                    if (row['end_date'] == ' ' or row['end_date'] == ''):
                        a = 1
                    elif (row['end_date']!='0000-00-00 00:00:00' and row['end_date'] != '0000-00-00'):
                        e.end_date = row['end_date']
                        e.end_date = e.end_date[:10]
                        if (row['end_date'] != '0000-00-00'):
                            e.end_date = datetime.datetime.strptime(e.end_date, "%Y-%m-%d").date()

                except:
                    a=1

                try:

                    if (row['date_entry'] == ' ' or row['date_entry'] == ''):
                        a = 1
                    else:
                        e.date_entry = row['date_entry']
                        e.date_entry=e.date_entry[:10]
                        e.date_entry = datetime.datetime.strptime(e.date_entry, "%Y-%m-%d").date()
                except:
                    a=1
                confr.append(e)
            emp_confrence_organised.objects.bulk_create(confr)
            return HttpResponseRedirect('DONE')
    else:
        form = UploadFileForm()
    return render(request, 'eisModulenew/upload.html', {'form': form})


def consultancy(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['fileUpload']
            decoded_file = file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)
            c=1
            consult = []
            for row in reader:
                e = emp_consultancy_projects()
                e.pf_no = row['pf_no']
                e.consultants = row['consultants']
                e.title = row['title']
                e.client = row['client']
                e.financial_outlay = row['financial_outlay']
                e.duration = row['duration']

                try:
                    if (row['start_date'] == ' ' or row['start_date'] == ''):
                        a=1
                    elif (row['start_date'] != '0000-00-00 00:00:00' and row['start_date'] != '0000-00-00'):
                        e.start_date = row['start_date']
                        e.start_date = e.start_date[:10]
                        if (row['start_date'] != '0000-00-00'):
                            e.start_date = datetime.datetime.strptime(e.start_date, "%Y-%m-%d").date()
                except:
                    a=1
                try:
                    if (row['end_date'] == ' ' or row['end_date'] == ''):
                        a = 1
                    elif (row['end_date']!='0000-00-00 00:00:00' and row['end_date'] != '0000-00-00'):
                        e.end_date = row['end_date']
                        e.end_date = e.end_date[:10]
                        if (row['end_date'] != '0000-00-00'):
                            e.end_date = datetime.datetime.strptime(e.end_date, "%Y-%m-%d").date()

                except:
                    a=1

                try:

                    if (row['date_entry'] == ' ' or row['date_entry'] == ''):
                        a = 1
                    else:
                        e.date_entry = row['date_entry']
                        e.date_entry=e.date_entry[:10]
                        e.date_entry = datetime.datetime.strptime(e.date_entry, "%Y-%m-%d").date()
                except:
                    a=1
                consult.append(e)
            emp_consultancy_projects.objects.bulk_create(consult)
            return HttpResponseRedirect('DONE')
    else:
        form = UploadFileForm()
    return render(request, 'eisModulenew/upload.html', {'form': form})



def event(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['fileUpload']
            decoded_file = file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)
            c=1
            organize = []
            for row in reader:
                e = emp_event_organized()
                e.pf_no = row['pf_no']
                e.type = row['type']
                e.name = row['name']
                e.sponsoring_agency = row['sponsoring_agency']
                e.venue = row['venue']
                e.role = row['role']

                try:
                    if (row['start_date'] != '0000-00-00 00:00:00' and row['start_date'] != '0000-00-00'):
                        e.start_date = row['start_date']
                        e.start_date = e.start_date[:10]
                        if (row['start_date'] != '0000-00-00'):
                            e.start_date = datetime.datetime.strptime(e.start_date, "%Y-%m-%d").date()
                except:
                    a=1
                try:
                    if (row['end_date']!='0000-00-00 00:00:00' and row['end_date'] != '0000-00-00'):
                        e.end_date = row['end_date']
                        e.end_date = e.end_date[:10]
                        if (row['end_date'] != '0000-00-00'):
                            e.end_date = datetime.datetime.strptime(e.end_date, "%Y-%m-%d").date()

                except:
                    a=1

                try:

                    if (row['date_entry'] == ' ' or row['date_entry'] == ''):
                        a = 1
                    else:
                        e.date_entry = row['date_entry']
                        e.date_entry=e.date_entry[:10]
                        e.date_entry = datetime.datetime.strptime(e.date_entry, "%Y-%m-%d").date()
                except:
                    a=1
                organize.append(e)
            emp_event_organized.objects.bulk_create(organize)
            return HttpResponseRedirect('DONE')
    else:
        form = UploadFileForm()
    return render(request, 'eisModulenew/upload.html', {'form': form})


def lectures(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['fileUpload']
            decoded_file = file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)
            c=1
            expert = []
            for row in reader:
                e = emp_expert_lectures()
                e.pf_no = row['pf_no']
                e.l_type = row['l_type']
                e.title = row['title']
                e.place = row['place']
                e.l_year = row['l_year']

                try:
                    if (row['l_date'] != '0000-00-00 00:00:00' and row['l_date'] != '0000-00-00'):
                        e.l_date = row['l_date']
                        e.l_date = e.l_date[:10]
                        if (row['l_date'] != '0000-00-00'):
                            e.l_date = datetime.datetime.strptime(e.l_date, "%Y-%m-%d").date()
                except:
                    a=1

                try:

                    if (row['date_entry'] == ' ' or row['date_entry'] == ''):
                        a = 1
                    else:
                        e.date_entry = row['date_entry']
                        e.date_entry=e.date_entry[:10]
                        e.date_entry = datetime.datetime.strptime(e.date_entry, "%Y-%m-%d").date()
                except:
                    a=1
                expert.append(e)
            emp_expert_lectures.objects.bulk_create(expert)
            return HttpResponseRedirect('DONE')
    else:
        form = UploadFileForm()
    return render(request, 'eisModulenew/upload.html', {'form': form})


def keynote(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['fileUpload']
            decoded_file = file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)
            c=1
            address = []
            for row in reader:
                e = emp_keynote_address()
                e.pf_no = row['pf_no']
                e.type = row['type']
                e.title = row['title']
                e.name = row['name']
                e.venue = row['venue']
                e.page_no = row['page_no']
                e.isbn_no = row['isbn_no']

                e.k_year = int(row['k_year'])

                try:
                    if (row['start_date'] != '0000-00-00 00:00:00' and row['start_date'] != '0000-00-00'):
                        e.start_date = row['start_date']
                        e.start_date = e.start_date[:10]
                        if (row['start_date'] != '0000-00-00'):
                            e.start_date = datetime.datetime.strptime(e.start_date, "%Y-%m-%d").date()
                except:
                    a=1
                try:
                    if (row['end_date']!='0000-00-00 00:00:00' and row['end_date'] != '0000-00-00'):
                        e.end_date = row['end_date']
                        e.end_date = e.end_date[:10]
                        if (row['end_date'] != '0000-00-00'):
                            e.end_date = datetime.datetime.strptime(e.end_date, "%Y-%m-%d").date()

                except:
                    a=1

                try:

                    if (row['date_entry'] == ' ' or row['date_entry'] == ''):
                        a = 1
                    else:
                        e.date_entry = row['date_entry']
                        e.date_entry=e.date_entry[:10]
                        e.date_entry = datetime.datetime.strptime(e.date_entry, "%Y-%m-%d").date()
                except:
                    a=1
                address.append(e)
            emp_keynote_address.objects.bulk_create(address)
            return HttpResponseRedirect('DONE')
    else:
        form = UploadFileForm()
    return render(request, 'eisModulenew/upload.html', {'form': form})


def thesis(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['fileUpload']
            decoded_file = file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)
            c=1
            mtech_phd_thesis = []
            for row in reader:
                e = emp_mtechphd_thesis()
                e.pf_no = row['pf_no']
                e.degree_type = int(row['degree_type'])
                e.title = row['title']
                e.supervisors = row['supervisors']
                e.co_supervisors = row['co_supervisors']
                e.rollno = row['rollno']
                e.s_name = row['s_name']

                if(row['s_year'] != '0'):
                    e.s_year = int(row['s_year'])

                try:

                    if (row['date_entry'] == ' ' or row['date_entry'] == ''):
                        a = 1
                    else:
                        e.date_entry = row['date_entry']
                        e.date_entry=e.date_entry[:10]
                        e.date_entry = datetime.datetime.strptime(e.date_entry, "%Y-%m-%d").date()
                except:
                    a=1
                mtech_phd_thesis.append(e)
            emp_mtechphd_thesis.objects.bulk_create(mtech_phd_thesis)
            return HttpResponseRedirect('DONE')
    else:
        form = UploadFileForm()
    return render(request, 'eisModulenew/upload.html', {'form': form})


def patents(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['fileUpload']
            decoded_file = file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)
            c=1
            patent = []
            for row in reader:
                e = emp_patents()
                e.pf_no = row['pf_no']
                e.p_no = row['p_no']
                e.title = row['title']
                e.earnings = row['earnings']
                e.p_year = int(row['p_year'])

                if(row['status'] == '1'):
                    e.status = 'Filed'
                elif(row['status'] == '2'):
                    e.status = 'Granted'
                elif(row['status'] == '3'):
                    e.status = 'Published'
                elif(row['status'] == '4'):
                    e.status = 'Owned'

                try:

                    if (row['date_entry'] == ' ' or row['date_entry'] == ''):
                        a = 1
                    else:
                        e.date_entry = row['date_entry']
                        e.date_entry=e.date_entry[:10]
                        e.date_entry = datetime.datetime.strptime(e.date_entry, "%Y-%m-%d").date()
                except:
                    a=1
                patent.append(e)
            emp_patents.objects.bulk_create(patent)
            return HttpResponseRedirect('DONE')
    else:
        form = UploadFileForm()
    return render(request, 'eisModulenew/upload.html', {'form': form})


def published_books(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['fileUpload']
            decoded_file = file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)
            c=1
            pub_books = []
            for row in reader:
                e = emp_published_books()
                e.pf_no = row['pf_no']
                e.title = row['title']
                e.publisher = row['publisher']
                e.co_authors = row['co_authors']
                e.pyear = int(row['pyear'])

                if(row['p_type'] == '1'):
                    e.p_type = 'Book'
                elif(row['p_type'] == '2'):
                    e.p_type = 'Monograph'
                elif(row['p_type'] == '3'):
                    e.p_type = 'Book Chapter'
                elif(row['p_type'] == '4'):
                    e.p_type = 'Handbook'
                elif(row['p_type'] == '5'):
                    e.p_type = 'Technical Report'

                try:

                    if (row['date_entry'] == ' ' or row['date_entry'] == ''):
                        a = 1
                    else:
                        e.date_entry = row['date_entry']
                        e.date_entry=e.date_entry[:10]
                        e.date_entry = datetime.datetime.strptime(e.date_entry, "%Y-%m-%d").date()
                except:
                    a=1
                pub_books.append(e)
            emp_published_books.objects.bulk_create(pub_books)
            return HttpResponseRedirect('DONE')
    else:
        form = UploadFileForm()
    return render(request, 'eisModulenew/upload.html', {'form': form})


def papers(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['fileUpload']
            decoded_file = file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)
            c=1
            research_papers = []
            for row in reader:
                e = emp_research_papers()
                e.pf_no = row['pf_no']
                e.authors = row['authors']
                e.rtype = row['rtype']
                e.title_paper = row['title_paper']
                e.name_journal = row['name_journal']
                e.volume_no = row['volume_no']
                e.venue = row['venue']
                e.page_no = row['page_no']
                e.issn_no = row['issn_no']
                e.doi = row['doi']
                e.doc_id = row['doc_id']
                e.doc_description = row['doc_description']
                e.reference_number = row['reference_number']
                e.year = int(row['year'])
                if(row['is_sci'] == 'Yes' or row['is_sci'] == 'No'):
                    e.is_sci = row['is_sci']

                if (row['status'] == 'Published' or row['status'] == 'Accepted' or row['status'] == 'Communicated'):
                    e.status = row['status']

                try:
                    if(str(row['date_submission']) == ' ' or str(row['date_submission']) == '' or row['date_submission'] == None):
                        a=1
                    else:
                        if (row['date_submission'] != '0000-00-00 00:00:00'  and row['date_submission'] != '0000-00-00'):
                            e.date_submission = row['date_submission']
                            e.date_submission = datetime.datetime.strptime(e.date_submission, "%Y-%m-%d").date()

                except:
                    a=1

                try:
                    if (row['start_date'] != '0000-00-00 00:00:00' and row['start_date'] != '0000-00-00'):
                        e.start_date = row['start_date']
                        e.start_date = e.start_date[:10]
                        if (row['start_date'] != '0000-00-00'):
                            e.start_date = datetime.datetime.strptime(e.start_date, "%Y-%m-%d").date()
                except:
                    a=1
                try:
                    if (row['end_date']!='0000-00-00 00:00:00' and row['end_date'] != '0000-00-00'):
                        e.end_date = row['end_date']
                        e.end_date = e.end_date[:10]
                        if (row['end_date'] != '0000-00-00'):
                            e.end_date = datetime.datetime.strptime(e.end_date, "%Y-%m-%d").date()

                except:
                    a=1

                try:
                    if (row['date_acceptance'] == ' ' or row['date_acceptance'] == ''):
                        a = 1
                    else:
                        if (row['date_acceptance'] != '0000-00-00 00:00:00'):
                            e.date_acceptance = row['date_acceptance']
                            e.date_acceptance = e.date_acceptance[:10]
                            e.date_acceptance = datetime.datetime.strptime(e.date_acceptance, "%Y-%m-%d").date()
                except:
                    a=1

                try:
                    if (row['date_publication'] == ' ' or row['date_publication'] == ''):
                        a = 1
                    else:
                        if(row['date_publication']!='0000-00-00 00:00:00'):
                            e.date_publication = row['date_publication']
                            e.date_publication = e.end_date[:10]
                            e.date_publication = row['date_publication']

                            e.date_publication = datetime.datetime.strptime(e.date_publication, "%Y-%m-%d").date()

                except:
                    a=1

                try:

                    if (row['date_entry'] == ' ' or row['date_entry'] == ''):
                        a = 1
                    else:
                        e.date_entry = row['date_entry']
                        e.date_entry=e.date_entry[:10]
                        e.date_entry = datetime.datetime.strptime(e.date_entry, "%Y-%m-%d").date()
                except:
                    a=1
                a = e.start_date
                b = e.end_date
                research_papers.append(e)
            emp_research_papers.objects.bulk_create(research_papers)
            return HttpResponseRedirect('DONE')
    else:
        form = UploadFileForm()
    return render(request, 'eisModulenew/upload.html', {'form': form})




def projects(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['fileUpload']
            decoded_file = file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)
            research_projects = []
            for row in reader:
                e = emp_research_projects()
                e.pf_no = row['pf_no']
                e.pi = row['pi']
                e.co_pi = row['co_pi']
                e.title = row['title']
                e.funding_agency = row['funding_agency']
                e.financial_outlay = row['financial_outlay']
                e.status = row['status']


                try:
                    if(str(row['date_submission']) == ' ' or str(row['date_submission']) == '' or row['date_submission'] == None):
                        a=1
                    else:
                        if (row['date_submission'] != '0000-00-00 00:00:00'):
                            e.date_submission = row['date_submission']
                            e.date_submission = datetime.datetime.strptime(e.date_submission, "%Y-%m-%d").date()

                except:
                    a=1

                try:
                    if (row['start_date'] != '0000-00-00 00:00:00'):
                        e.start_date = row['start_date']
                        e.start_date = e.start_date[:10]
                        e.start_date = datetime.datetime.strptime(e.start_date, "%Y-%m-%d").date()
                except:
                    a=1

                try:
                    if(row['finish_date']!='0000-00-00 00:00:00'):
                        e.finish_date = row['finish_date']
                        e.finish_date = e.finish_date[:10]
                        e.finish_date = row['finish_date']

                        e.finish_date = datetime.datetime.strptime(e.finish_date, "%Y-%m-%d").date()

                except:
                    a=1

                try:

                    if (row['date_entry'] == ' ' or row['date_entry'] == ''):
                        a = 1
                    else:
                        e.date_entry = row['date_entry']
                        e.date_entry=e.date_entry[:10]
                        e.date_entry = datetime.datetime.strptime(e.date_entry, "%Y-%m-%d").date()
                except:
                    a=1

                research_projects.append(e)
            emp_research_projects.objects.bulk_create(research_projects)
            return HttpResponseRedirect('DONE')
    else:
        form = UploadFileForm()
    return render(request, 'eisModulenew/upload.html', {'form': form})


def visits(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['fileUpload']
            decoded_file = file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)
            visit = []
            for row in reader:
                e = emp_visits()
                e.pf_no = row['pf_no']
                e.v_type = row['v_type']
                e.country = row['country']
                e.place = row['place']
                e.purpose = row['purpose']



                try:
                    if(str(row['v_date']) == ' ' or str(row['v_date']) == '' or row['v_date'] == None):
                        a=1
                    else:
                        e.v_date = row['v_date']
                        e.v_date = datetime.datetime.strptime(e.v_date, "%Y-%m-%d").date()

                except:
                    a=1

                try:

                    e.start_date = row['start_date']
                    e.start_date = datetime.datetime.strptime(e.start_date, "%Y-%m-%d").date()
                except:
                    a=1

                try:
                    if(row['end_date']!='0000-00-00 00:00:00'):
                        e.end_date = row['end_date']

                        e.end_date = datetime.datetime.strptime(e.end_date, "%Y-%m-%d").date()

                except:
                    a=1

                try:

                    if (row['date_entry'] == ' ' or row['date_entry'] == ''):
                        a = 1
                    else:
                        e.entry_date = row['date_entry']
                        e.entry_date=e.entry_date[:10]
                        e.entry_date = datetime.datetime.strptime(e.entry_date, "%Y-%m-%d").date()
                except:
                    a=1

                visit.append(e)
            emp_visits.objects.bulk_create(visit)
            return HttpResponseRedirect('DONE')
    else:
        form = UploadFileForm()
    return render(request, 'eisModulenew/upload.html', {'form': form})



def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['fileUpload']
            decoded_file = file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)
            session = []
            for row in reader:
                e = emp_session_chair()
                e.pf_no = row['pf_no']
                e.name = row['name']
                e.event = row['event']
                e.place = row['s_year']
                e.s_year=int(row['s_year'])

                try:
                    if (row['start_date'] != '0000-00-00 00:00:00'):
                        e.start_date = row['start_date']
                        e.start_date = datetime.datetime.strptime(e.start_date, "%Y-%m-%d").date()
                except:
                    a=1

                try:
                    if(row['end_date']!='0000-00-00 00:00:00'):
                        e.end_date = row['end_date']

                        e.end_date = datetime.datetime.strptime(e.end_date, "%Y-%m-%d").date()

                except:
                    a=1

                try:

                    if (row['date_entry'] == ' ' or row['date_entry'] == ''):
                        a = 1
                    else:
                        if (row['start_date'] != '0000-00-00 00:00:00'):
                            e.date_entry = row['date_entry']
                            e.date_entry=e.date_entry[:10]
                            e.date_entry = datetime.datetime.strptime(e.date_entry, "%Y-%m-%d").date()
                except:
                    a=1

                session.append(e)
            emp_session_chair.objects.bulk_create(session)
            return HttpResponseRedirect('DONE')
    else:
        form = UploadFileForm()
    return render(request, 'eisModulenew/upload.html', {'form': form})

def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return HttpResponse('We had some errors<pre>%s</pre>' % escape(html))


def generate_report(request):
    user = get_object_or_404(ExtraInfo, user=request.user)
    pf = user.id
    start = request.POST.get('syear')
    star_date = start+'-01-01'
    end = request.POST.get('lyear')
    star = request.POST.get('smonth')
    star_date = start + '-01-01'
    en = request.POST.get('lmonth')
    if(request.POST.get('journal_select')=="journal"):
        journal = emp_research_papers.objects.filter(pf_no=pf, rtype='Journal').filter(year__range=[start,end]).order_by('-date_entry')
        journal_req="1"
    else:
        journal=""
        journal_req="0"

    if (request.POST.get('conference_select') == "conference"):
        conference = emp_research_papers.objects.filter(pf_no=pf, rtype='Conference').filter(year__range=[start,end]).order_by('-date_entry')
        conference_req = "1"
    else:
        conference=""
        conference_req = "0"

    if (request.POST.get('books_select') == "books"):
        books = emp_published_books.objects.order_by('-date_entry')
        books_req = "1"
    else:
        books=""
        books_req = "0"

    if (request.POST.get('projects_select') == "projects"):
        projects = emp_research_projects.objects.filter(pf_no=pf).filter(start_date__year__range=[start,end]).filter(start_date__month__range=[star,en]).order_by('-start_date')
        projects_req = "1"
    else:
        projects = ""
        projects_req = "0"

    if (request.POST.get('consultancy_select') == "consultancy"):
        consultancy = emp_consultancy_projects.objects.filter(pf_no=pf).filter(start_date__year__range=[start,end]).filter(start_date__month__range=[star,en]).order_by('-date_entry')
        consultancy_req = "1"
    else:
        consultancy = ""
        consultancy_req = "0"

    if (request.POST.get('patents_select') == "patents"):
        patents = emp_patents.objects.filter(pf_no=pf).filter(p_year__range=[start,end]).filter(a_month__range=[star,en]).order_by('-date_entry')
        patents_req = "1"
    else:
        patents = ""
        patents_req = "0"

    if (request.POST.get('techtransfers_select') == "techtransfers"):
        techtransfers = emp_techtransfer.objects.filter(pf_no=pf).filter(date_entry__year__range=[start,end]).filter(date_entry__month__range=[star,en]).order_by('-date_entry')
        techtransfers_req = "1"
    else:
        techtransfers=""
        techtransfers_req = "0"

    if (request.POST.get('mtechs_select') == "mtechs"):
        mtechs = emp_mtechphd_thesis.objects.filter(pf_no=pf, degree_type=1).filter(s_year__range=[start,end]).filter(a_month__range=[star,en]).order_by('-date_entry')
        mtechs_req = "1"
    else:
        mtechs=""
        mtechs_req = "0"

    if (request.POST.get('phds_select') == "phds"):
        phds = emp_mtechphd_thesis.objects.filter(pf_no=pf, degree_type=2).filter(s_year__range=[start,end]).filter(a_month__range=[star,en]).order_by('-date_entry')
        phds_req = "1"
    else:
        phds=""
        phds_req = "0"

    if (request.POST.get('fvisits_select') == "fvisits"):
        fvisits = emp_visits.objects.filter(pf_no=pf, v_type=2).filter(start_date__year__range=[start,end]).filter(start_date__month__range=[star,en]).order_by('-entry_date')
        fvisits_req = "1"
    else:
        fvisits=""
        fvisits_req = "0"
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

    if (request.POST.get('ivisits_select') == "ivisits"):
        ivisits = emp_visits.objects.filter(pf_no=pf, v_type=1).filter(start_date__year__range=[start,end]).filter(start_date__month__range=[star,en]).order_by('-entry_date')
        ivisits_req = "1"
    else:
        ivisits=""
        ivisits_req = "0"
    for fvisit in fvisits:
        fvisit.countryfull = countries[fvisit.country]

    if (request.POST.get('consymps_select') == "consymps"):
        consymps = emp_confrence_organised.objects.filter(pf_no=pf).filter(start_date__year__range=[start,end]).filter(start_date__month__range=[star,en]).order_by('-date_entry')
        consymps_req = "1"
    else:
        consymps=""
        consymps_req = "0"

    if (request.POST.get('awards_select') == "awards"):
        awards = emp_achievement.objects.filter(pf_no=pf).filter(a_year__range=[start,end]).order_by('-date_entry')
        awards_req = "1"
    else:
        awards=""
        awards_req = "0"

    if (request.POST.get('talks_select') == "talks"):
        talks = emp_expert_lectures.objects.filter(pf_no=pf).filter(l_date__year__range=[start,end]).filter(l_date__month__range=[star,en]).order_by('-date_entry')
        talks_req = "1"
    else:
        talks=""
        talks_req = "0"

    if (request.POST.get('chairs_select') == "chairs"):
        chairs = emp_session_chair.objects.filter(pf_no=pf).filter(start_date__year__range=[start,end]).filter(start_date__month__range=[star,en]).order_by('-date_entry')
        chairs_req = "1"
    else:
        chairs=""
        chairs_req = "0"

    if (request.POST.get('keynotes_select') == "keynotes"):
        keynotes = emp_keynote_address.objects.filter(pf_no=pf).filter(start_date__year__range=[start,end]).filter(start_date__month__range=[star,en]).order_by('-date_entry')
        keynotes_req = "1"
    else:
        keynotes=""
        keynotes_req = "0"

    if (request.POST.get('events_select') == "events"):
        events = emp_event_organized.objects.filter(pf_no=pf).filter(start_date__year__range=[start,end]).filter(start_date__month__range=[star,en]).order_by('-start_date')
        events_req = "1"
    else:
        events=""
        events_req = "0"

    pers = get_object_or_404(faculty_about, user = request.user)
    design = HoldsDesignation.objects.select_related('user','working','designation').filter(working=request.user)
    desig=[]
    for i in design:
        desig.append(str(i.designation))
    context = {'user': user,
               'desig':desig,
               'pf':pf,
               'journal':journal,
               'journal_req':journal_req,
               'conference': conference,
               'conference_req': conference_req,
               'books': books,
               'books_req': books_req,
               'projects': projects,
               'projects_req': projects_req,
               'consultancy':consultancy,
               'consultancy_req': consultancy_req,
               'patents':patents,
               'patents_req': patents_req,
               'techtransfers':techtransfers,
               'techtransfers_req': techtransfers_req,
               'mtechs':mtechs,
               'mtechs_req': mtechs_req,
               'phds':phds,
               'phds_req': phds_req,
               'fvisits':fvisits,
               'fvisits_req': fvisits_req,
               'ivisits': ivisits,
               'ivisits_req': ivisits_req,
               'consymps':consymps,
               'consymps_req': consymps_req,
               'awards':awards,
               'awards_req': awards_req,
               'talks':talks,
               'talks_req': talks_req,
               'chairs':chairs,
               'chairs_req': chairs_req,
               'keynotes':keynotes,
               'keynotes_req': keynotes_req,
               'events':events,
               'events_req': events_req,
               'first_name':request.user.first_name,
               'last_name': request.user.last_name,
               }
    return render_to_pdf('eisModulenew/generatereportshow.html', context)


# report for dean rspc


def rspc_generate_report(request):
    user = get_object_or_404(ExtraInfo, user=request.user)
    pf = user.id
    start = request.POST.get('syear')
    star_date = start+'-01-01'
    end = request.POST.get('lyear')
    star = request.POST.get('smonth')
    star_date = start + '-01-01'
    en = request.POST.get('lmonth')
    if(request.POST.get('journal_select')=="journal"):
        journal = emp_research_papers.objects.filter(rtype='Journal').filter(year__range=[start,end]).order_by('-date_entry')
        journal_req="1"
    else:
        journal=""
        journal_req="0"

    if (request.POST.get('conference_select') == "conference"):
        conference = emp_research_papers.objects.filter(rtype='Conference').filter(year__range=[start,end]).order_by('-date_entry')
        conference_req = "1"
    else:
        conference=""
        conference_req = "0"

    if (request.POST.get('books_select') == "books"):
        books = emp_published_books.objects.all().order_by('-date_entry')
        books_req = "1"
    else:
        books=""
        books_req = "0"

    if (request.POST.get('projects_select') == "projects"):
        projects = emp_research_projects.objects.all().filter(start_date__year__range=[start,end]).filter(start_date__month__range=[star,en]).order_by('-start_date')
        projects_req = "1"
    else:
        projects = ""
        projects_req = "0"

    if (request.POST.get('consultancy_select') == "consultancy"):
        consultancy = emp_consultancy_projects.objects.all().filter(start_date__year__range=[start,end]).filter(start_date__month__range=[star,en]).order_by('-date_entry')
        consultancy_req = "1"
    else:
        consultancy = ""
        consultancy_req = "0"

    if (request.POST.get('patents_select') == "patents"):
        patents = emp_patents.objects.all().filter(p_year__range=[start,end]).filter(a_month__range=[star,en]).order_by('-date_entry')
        patents_req = "1"
    else:
        patents = ""
        patents_req = "0"

    if (request.POST.get('techtransfers_select') == "techtransfers"):
        techtransfers = emp_techtransfer.objects.all().filter(date_entry__year__range=[start,end]).filter(date_entry__month__range=[star,en]).order_by('-date_entry')
        techtransfers_req = "1"
    else:
        techtransfers=""
        techtransfers_req = "0"

    if (request.POST.get('mtechs_select') == "mtechs"):
        mtechs = emp_mtechphd_thesis.objects.filter(degree_type=1).filter(s_year__range=[start,end]).filter(a_month__range=[star,en]).order_by('-date_entry')
        mtechs_req = "1"
    else:
        mtechs=""
        mtechs_req = "0"

    if (request.POST.get('phds_select') == "phds"):
        phds = emp_mtechphd_thesis.objects.filter(degree_type=2).filter(s_year__range=[start,end]).filter(a_month__range=[star,en]).order_by('-date_entry')
        phds_req = "1"
    else:
        phds=""
        phds_req = "0"

    if (request.POST.get('fvisits_select') == "fvisits"):
        fvisits = emp_visits.objects.filter(v_type=2).filter(start_date__year__range=[start,end]).filter(start_date__month__range=[star,en]).order_by('-entry_date')
        fvisits_req = "1"
    else:
        fvisits=""
        fvisits_req = "0"
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

    if (request.POST.get('ivisits_select') == "ivisits"):
        ivisits = emp_visits.objects.filter(v_type=1).filter(start_date__year__range=[start,end]).filter(start_date__month__range=[star,en]).order_by('-entry_date')
        ivisits_req = "1"
    else:
        ivisits=""
        ivisits_req = "0"
    for fvisit in fvisits:
        fvisit.countryfull = countries[fvisit.country]

    if (request.POST.get('consymps_select') == "consymps"):
        consymps = emp_confrence_organised.objects.all().filter(start_date__year__range=[start,end]).filter(start_date__month__range=[star,en]).order_by('-date_entry')
        consymps_req = "1"
    else:
        consymps=""
        consymps_req = "0"

    if (request.POST.get('awards_select') == "awards"):
        awards = emp_achievement.objects.all().filter(a_year__range=[start,end]).order_by('-date_entry')
        awards_req = "1"
    else:
        awards=""
        awards_req = "0"

    if (request.POST.get('talks_select') == "talks"):
        talks = emp_expert_lectures.objects.all().filter(l_date__year__range=[start,end]).filter(l_date__month__range=[star,en]).order_by('-date_entry')
        talks_req = "1"
    else:
        talks=""
        talks_req = "0"

    if (request.POST.get('chairs_select') == "chairs"):
        chairs = emp_session_chair.objects.all().filter(start_date__year__range=[start,end]).filter(start_date__month__range=[star,en]).order_by('-date_entry')
        chairs_req = "1"
    else:
        chairs=""
        chairs_req = "0"

    if (request.POST.get('keynotes_select') == "keynotes"):
        keynotes = emp_keynote_address.objects.all().filter(start_date__year__range=[start,end]).filter(start_date__month__range=[star,en]).order_by('-date_entry')
        keynotes_req = "1"
    else:
        keynotes=""
        keynotes_req = "0"

    if (request.POST.get('events_select') == "events"):
        events = emp_event_organized.objects.all().filter(start_date__year__range=[start,end]).filter(start_date__month__range=[star,en]).order_by('-start_date')
        events_req = "1"
    else:
        events=""
        events_req = "0"

    pers = get_object_or_404(faculty_about, user = request.user)
    design = HoldsDesignation.objects.select_related('user','working','designation').filter(working=request.user)

    desig=[]
    for i in design:
        desig.append(str(i.designation))
    context = {'user': user,
               'pf':pf,
               'desig':desig,
               'journal':journal,
               'journal_req':journal_req,
               'conference': conference,
               'conference_req': conference_req,
               'books': books,
               'books_req': books_req,
               'projects': projects,
               'projects_req': projects_req,
               'consultancy':consultancy,
               'consultancy_req': consultancy_req,
               'patents':patents,
               'patents_req': patents_req,
               'techtransfers':techtransfers,
               'techtransfers_req': techtransfers_req,
               'mtechs':mtechs,
               'mtechs_req': mtechs_req,
               'phds':phds,
               'phds_req': phds_req,
               'fvisits':fvisits,
               'fvisits_req': fvisits_req,
               'ivisits': ivisits,
               'ivisits_req': ivisits_req,
               'consymps':consymps,
               'consymps_req': consymps_req,
               'awards':awards,
               'awards_req': awards_req,
               'talks':talks,
               'talks_req': talks_req,
               'chairs':chairs,
               'chairs_req': chairs_req,
               'keynotes':keynotes,
               'keynotes_req': keynotes_req,
               'events':events,
               'events_req': events_req,
               'first_name':request.user.first_name,
               'last_name': request.user.last_name,
               }
    return render_to_pdf('eisModulenew/rspc_generatereportshow.html', context)
