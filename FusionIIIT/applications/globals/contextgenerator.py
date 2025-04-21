import json

from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.core import serializers
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from PIL import Image
from applications.academic_information.models import Student
from applications.globals.forms import IssueForm, WebFeedbackForm
from applications.globals.models import (ExtraInfo, Feedback, HoldsDesignation,
                                         Issue, IssueImage, Faculty)
from applications.placement_cell.forms import (AddAchievement, AddCourse,
                                               AddEducation, AddExperience,
                                               AddPatent, AddProfile, AddConference,
                                               AddProject, AddPublication,
                                               AddSkill, AddReference, AddExtracurricular)
from applications.placement_cell.models import (Achievement, Course, Education, Conference,
                                                Experience, Has, Patent, Extracurricular,
                                                Project, Publication, Skill, Reference, PlacementStatus)
from applications.eis.models import *
from applications.academic_procedures.models import Thesis


def contextstudentmanage(current,profile,request,user,editable):
  student = get_object_or_404(Student, Q(id=profile.id))
  reference_tab = 0

  if editable and request.method == 'POST':
      if 'studentapprovesubmit' in request.POST:
          status = PlacementStatus.objects.filter(pk=request.POST['studentapprovesubmit']).update(invitation='ACCEPTED', timestamp=timezone.now())
      if 'studentdeclinesubmit' in request.POST:
          status = PlacementStatus.objects.filter(Q(pk=request.POST['studentdeclinesubmit'])).update(invitation='REJECTED', timestamp=timezone.now())
      if 'educationsubmit' in request.POST:
          form = AddEducation(request.POST)
          if form.is_valid():
              institute = form.cleaned_data['institute']
              degree = form.cleaned_data['degree']
              grade = form.cleaned_data['grade']
              stream = form.cleaned_data['stream']
              sdate = form.cleaned_data['sdate']
              edate = form.cleaned_data['edate']
              education_obj = Education.objects.create(unique_id=student, degree=degree,
                                                       grade=grade, institute=institute,
                                                       stream=stream, sdate=sdate, edate=edate)
              education_obj.save()
      if 'profilesubmit' in request.POST:
          about_me = request.POST.get('about')
          age = request.POST.get('age')
          address = request.POST.get('address')
          contact = request.POST.get('contact')
          extrainfo_obj = ExtraInfo.objects.get(user=user)
          extrainfo_obj.about_me = about_me
          extrainfo_obj.date_of_birth = age
          extrainfo_obj.address = address
          extrainfo_obj.phone_no = contact
          extrainfo_obj.save()
          profile = get_object_or_404(ExtraInfo, Q(user=user))
      if 'picsubmit' in request.POST:
          form = AddProfile(request.POST, request.FILES)
          extrainfo_obj = ExtraInfo.objects.get(user=user)
          extrainfo_obj.profile_picture = form.cleaned_data["pic"]
          extrainfo_obj.save()
      if 'skillsubmit' in request.POST:
          form = AddSkill(request.POST)
          print('skill coming----------------\n\n')
          if form.is_valid():
              skill = form.cleaned_data['skill']
              skill_rating = form.cleaned_data['skill_rating']
              try:
                  skill_id = Skill.objects.get(skill=skill)
                  skill_id = None
              except Exception as e:
                  print(e)
                  skill_id = Skill.objects.create(skill=skill)
                  skill_id.save()

              if skill_id is not None:
                has_obj = Has.objects.create(unique_id=student,
                                           skill_id=skill_id,
                                           skill_rating = skill_rating)
                has_obj.save()
      if 'achievementsubmit' in request.POST:
          form = AddAchievement(request.POST)
          if form.is_valid():
              achievement = form.cleaned_data['achievement']
              achievement_type = form.cleaned_data['achievement_type']
              description = form.cleaned_data['description']
              issuer = form.cleaned_data['issuer']
              date_earned = form.cleaned_data['date_earned']
              achievement_obj = Achievement.objects.create(unique_id=student,
                                                           achievement=achievement,
                                                           achievement_type=achievement_type,
                                                           description=description,
                                                           issuer=issuer,
                                                           date_earned=date_earned)
      if 'extracurricularsubmit' in request.POST:
          form = AddExtracurricular(request.POST)
          if form.is_valid():
              event_name = form.cleaned_data['event_name']
              event_type = form.cleaned_data['event_type']
              description = form.cleaned_data['description']
              name_of_position = form.cleaned_data['name_of_position']
              date_earned = form.cleaned_data['date_earned']
              extracurricular_obj = Extracurricular.objects.create(unique_id=student,
                                                           event_name=event_name,
                                                           event_type=event_type,
                                                           description=description,
                                                           name_of_position=name_of_position,
                                                           date_earned=date_earned)
              extracurricular_obj.save()
      if 'publicationsubmit' in request.POST:
          form = AddPublication(request.POST)
          if form.is_valid():
              publication_title = form.cleaned_data['publication_title']
              description = form.cleaned_data['description']
              publisher = form.cleaned_data['publisher']
              publication_date = form.cleaned_data['publication_date']
              publication_obj = Publication.objects.create(unique_id=student,
                                                           publication_title=
                                                           publication_title,
                                                           publisher=publisher,
                                                           description=description,
                                                           publication_date=publication_date)
              publication_obj.save()
      if 'patentsubmit' in request.POST:
          form = AddPatent(request.POST)
          if form.is_valid():
              patent_name = form.cleaned_data['patent_name']
              description = form.cleaned_data['description']
              patent_office = form.cleaned_data['patent_office']
              patent_date = form.cleaned_data['patent_date']
              patent_obj = Patent.objects.create(unique_id=student, patent_name=patent_name,
                                                 patent_office=patent_office,
                                                 description=description,
                                                 patent_date=patent_date)
              patent_obj.save()
      if 'coursesubmit' in request.POST:
          form = AddCourse(request.POST)
          if form.is_valid():
              course_name = form.cleaned_data['course_name']
              description = form.cleaned_data['description']
              license_no = form.cleaned_data['license_no']
              sdate = form.cleaned_data['sdate']
              edate = form.cleaned_data['edate']
              course_obj = Course.objects.create(unique_id=student, course_name=course_name,
                                                 license_no=license_no,
                                                 description=description,
                                                 sdate=sdate, edate=edate)
              course_obj.save()

      if 'conferencesubmit' in request.POST:
          form = AddConference(request.POST)
          if form.is_valid():
              conference_name = form.cleaned_data['conference_name']
              description = form.cleaned_data['description']
              sdate = form.cleaned_data['sdate']
              edate = form.cleaned_data['edate']
              conference_obj = Conference.objects.create(unique_id=student, conference_name=conference_name,
                                                 description=description,
                                                 sdate=sdate, edate=edate)
              conference_obj.save()
      if 'projectsubmit' in request.POST:
          form = AddProject(request.POST)
          if form.is_valid():
              project_name = form.cleaned_data['project_name']
              project_status = form.cleaned_data['project_status']
              summary = form.cleaned_data['summary']
              project_link = form.cleaned_data['project_link']
              sdate = form.cleaned_data['sdate']
              edate = form.cleaned_data['edate']
              project_obj = Project.objects.create(unique_id=student, summary=summary,
                                                   project_name=project_name,
                                                   project_status=project_status,
                                                   project_link=project_link,
                                                   sdate=sdate, edate=edate)
              project_obj.save()
      if 'experiencesubmit' in request.POST:
          form = AddExperience(request.POST)
          if form.is_valid():
              title = form.cleaned_data['title']
              status = form.cleaned_data['status']
              company = form.cleaned_data['company']
              location = form.cleaned_data['location']
              description = form.cleaned_data['description']
              sdate = form.cleaned_data['sdate']
              edate = form.cleaned_data['edate']
              experience_obj = Experience.objects.create(unique_id=student, title=title,
                                                         company=company, location=location,
                                                         status=status,
                                                         description=description,
                                                         sdate=sdate, edate=edate)
              experience_obj.save()

      if 'addreference' in request.POST:
          form = AddReference(request.POST)
          reference_tab = 1
          print(form.errors)
          if form.is_valid():
              reference_name = form.cleaned_data['reference_name']
              post = form.cleaned_data['post']
              email = form.cleaned_data['email']
              mobile_number = form.cleaned_data['mobile_number']

              Reference.objects.create(
                  unique_id=student,
                  reference_name=reference_name,
                  post=post,
                  email=email,
                  mobile_number=mobile_number)
              messages.success(request, "Successfully added your reference!")

      if 'deleteskill' in request.POST:
          hid = request.POST['deleteskill']
          hs = Has.objects.get(Q(pk=hid))
          hs.delete()
      if 'deleteedu' in request.POST:
          hid = request.POST['deleteedu']
          hs = Education.objects.get(Q(pk=hid))
          hs.delete()
      if 'deletecourse' in request.POST:
          hid = request.POST['deletecourse']
          hs = Course.objects.get(Q(pk=hid))
          hs.delete()
      if 'deleteexp' in request.POST:
          hid = request.POST['deleteexp']
          hs = Experience.objects.get(Q(pk=hid))
          hs.delete()
      if 'deletepro' in request.POST:
          hid = request.POST['deletepro']
          hs = Project.objects.get(Q(pk=hid))
          hs.delete()
      if 'deletereference' in request.POST:
          hid = request.POST['deletereference']
          hs = Reference.objects.get(Q(pk=hid))
          hs.delete()
      if 'deleteach' in request.POST:
          hid = request.POST['deleteach']
          hs = Achievement.objects.get(Q(pk=hid))
          hs.delete()
      if 'deleteconference' in request.POST:
          hid = request.POST['deleteconference']
          hs = Conference.objects.get(Q(pk=hid))
          hs.delete()
      if 'deletextra' in request.POST:
          hid = request.POST['deletextra']
          hs = Extracurricular.objects.get(Q(pk=hid))
          hs.delete()
      if 'deletepub' in request.POST:
          hid = request.POST['deletepub']
          hs = Publication.objects.get(Q(pk=hid))
          hs.delete()
      if 'deletepat' in request.POST:
          hid = request.POST['deletepat']
          hs = Patent.objects.get(Q(pk=hid))
          hs.delete()
  form = AddEducation(initial={})
  form1 = AddProfile(initial={})
  form10 = AddSkill(initial={})
  form11 = AddCourse(initial={})
  form12 = AddAchievement(initial={})
  form5 = AddPublication(initial={})
  form6 = AddProject(initial={})
  form7 = AddPatent(initial={})
  form8 = AddExperience(initial={})
  form14 = AddProfile()
  form15 = AddReference()
  form88 = AddExtracurricular()
  form62 = AddConference()
  skills = Has.objects.filter(Q(unique_id=student))
  education = Education.objects.filter(Q(unique_id=student))
  course = Course.objects.filter(Q(unique_id=student))
  conferences = Conference.objects.filter(Q(unique_id=student))
  experience = Experience.objects.filter(Q(unique_id=student))
  project = Project.objects.filter(Q(unique_id=student))
  achievement = Achievement.objects.filter(Q(unique_id=student))
  reference = Reference.objects.filter(Q(unique_id=student))
  extracurriculars = Extracurricular.objects.filter(Q(unique_id=student))
  publication = Publication.objects.filter(Q(unique_id=student))
  patent = Patent.objects.filter(Q(unique_id=student))
  context = {
    'user': user, 'profile': profile, 'skills': skills, 'extracurriculars': extracurriculars,
    'educations': education, 'courses': course, 'experiences': experience, 'conferences': conferences,
    'projects': project, 'achievements': achievement, 'publications': publication,
    'patent': patent, 'form': form, 'form1': form1, 'form14': form14, 'form62': form62,
    'form5': form5, 'form6': form6, 'form7': form7, 'form8': form8, 'form88': form88,
    'form10':form10, 'form11':form11, 'form12':form12, 'current':current,  'form15': form15,
    'editable': editable,  'reference_tab': reference_tab, 'references': reference
  }
  return context



def contextfacultymanage(request,user,profile):
  detail = faculty_about.objects.get(user=user)

  #pagiantion for Journal
  publications = emp_research_papers.objects.filter(pf_no=profile.id,rtype='Journal').order_by("-date_entry")

  paginator = Paginator(publications, 10)
  page = request.GET.get('page')
  mark=0;
  if page != None:
    mark=1
  else:
    mark=0
  if page == None:
    page=1
  publications = paginator.page(page)
  sr = (publications.number-1)*10


  #pagination for book
  books = emp_published_books.objects.filter(pf_no=profile.id).order_by("-date_entry")
  paginator2 = Paginator(books, 10)
  page2 = request.GET.get('page2')
  mark2=0;
  if page2 != None:
    mark2=1
  else:
    mark2=0
  if page2 == None:
    page2=1
  books = paginator2.page(page2)
  sr2 = (books.number-1)*10

  #pagination for conference
  conferences = emp_research_papers.objects.filter(pf_no=profile.id,rtype='Conference').order_by("-date_entry")
  paginator3 = Paginator(conferences, 10)
  page3 = request.GET.get('page3')
  mark3=0;
  if page3 != None:
    mark3=1
  else:
    mark3=0
  if page3 == None:
    page3=1
  conferences = paginator3.page(page3)
  sr3 = (conferences.number-1)*10


  #pagination for research project
  research_projects = emp_research_projects.objects.filter(pf_no=profile.id).order_by("-date_entry")
  paginator4 = Paginator(research_projects, 10)
  page4 = request.GET.get('page4')
  mark4=0;
  if page4 != None:
    mark4=1
  else:
    mark4=0
  if page4 == None:
    page4=1
  research_projects = paginator4.page(page4)
  sr4 = (research_projects.number-1)*10

  #pagination for Consultancy Project
  consultancy_projects = emp_consultancy_projects.objects.filter(pf_no=profile.id).order_by("-date_entry")
  paginator5 = Paginator(consultancy_projects, 20)
  page5 = request.GET.get('page5')
  mark5=0;
  if page5 != None:
    mark5=1
  else:
    mark5=0
  if page5 == None:
    page5=1
  consultancy_projects = paginator5.page(page5)
  print(consultancy_projects,page5)
  sr5 = (consultancy_projects.number-1)*10

  #pagination for patents
  patents = emp_patents.objects.filter(pf_no=profile.id).order_by("-date_entry")
  paginator6 = Paginator(patents, 10)
  page6 = request.GET.get('page6')
  mark6=0;
  if page6 != None:
    mark6=1
  else:
    mark6=0
  if page6 == None:
    page6=1
  patents = paginator6.page(page5)
  sr6 = (patents.number-1)*10

  #pagination for technology transfer
  techtransfer = emp_techtransfer.objects.filter(pf_no=profile.id).order_by("-date_entry")
  paginator7 = Paginator(techtransfer, 10)
  page7 = request.GET.get('page7')
  mark7=0;
  if page7 != None:
    mark7=1
  else:
    mark7=0
  if page7 == None:
    page7=1
  techtransfer = paginator7.page(page7)
  sr7 = (techtransfer.number-1)*10


  #pagination for  thesis
  thesis = emp_mtechphd_thesis.objects.filter(pf_no=profile.id, degree_type=1).order_by('-date_entry')
  paginator8 = Paginator(thesis, 10)
  page8 = request.GET.get('page8')
  mark8=0;
  if page8 != None:
    mark8=1
  else:
    mark8=0
  if page8 == None:
    page8=1
  thesis = paginator8.page(page8)
  sr8 = (thesis.number-1)*10
  y=[]
  for r in range(1995, (datetime.datetime.now().year + 1)):
        y.append(r)


  #pagination for phdthesis
  phdthesis = emp_mtechphd_thesis.objects.filter(pf_no=profile.id, degree_type=2).order_by('-date_entry')
  paginator9 = Paginator(phdthesis, 10)
  page9 = request.GET.get('page9')
  mark9=0;
  if page9 != None:
    mark9=1
  else:
    mark9=0
  if page9 == None:
    page9=1
  phdthesis = paginator9.page(page9)
  sr9 = (phdthesis.number-1)*10


  #paginator for foreign visit
  foreign_visits = emp_visits.objects.filter(pf_no=profile.id,v_type=2).order_by("-start_date")
  paginator10 = Paginator(foreign_visits, 10)
  page10 = request.GET.get('page10')
  mark10=0;
  if page10 != None:
    mark10=1
  else:
    mark10=0
  if page10 == None:
    page10=1
  foreign_visits = paginator10.page(page10)
  sr10 = (foreign_visits.number-1)*10

  #paginator for indian visit
  indian_visits = emp_visits.objects.filter(pf_no=profile.id,v_type=1).order_by("-start_date")
  paginator11 = Paginator(indian_visits, 10)
  page11 = request.GET.get('page11')
  mark11=0;
  if page11 != None:
    mark11=1
  else:
    mark11=0
  if page11 == None:
    page11=1
  indian_visits = paginator11.page(page11)
  sr11 = (indian_visits.number-1)*10

  #paginator for event organized
  events = emp_event_organized.objects.filter(pf_no=profile.id).order_by("-date_entry")
  paginator12 = Paginator(events, 10)
  page12 = request.GET.get('page12')
  mark12=0;
  if page12 != None:
    mark12=1
  else:
    mark12=0
  if page12 == None:
    page12=1
  events = paginator12.page(page12)
  sr12 = (events.number-1)*10

  #paginator for conference
  confs = emp_confrence_organised.objects.filter(pf_no=profile.id).order_by("-date_entry")
  paginator13 = Paginator(confs, 10)
  page13 = request.GET.get('page13')
  mark13=0;
  if page13 != None:
    mark13=1
  else:
    mark13=0
  if page13 == None:
    page13=1
  confs = paginator13.page(page13)
  sr13 = (confs.number-1)*10


  awards = emp_achievement.objects.filter(pf_no=profile.id).order_by("-date_entry")
  paginator14 = Paginator(awards, 10)
  page14 = request.GET.get('page14')
  mark14=0;
  if page14 != None:
    mark14=1
  else:
    mark14=0
  if page14 == None:
    page14=1
  awards = paginator14.page(page14)
  sr14 = (awards.number-1)*10



  talks = emp_expert_lectures.objects.filter(pf_no=profile.id).order_by("-date_entry")
  paginator15 = Paginator(talks, 10)
  page15 = request.GET.get('page15')
  mark15=0;
  if page15 != None:
    mark15=1
  else:
    mark15=0
  if page15 == None:
    page15=1
  talks = paginator15.page(page15)
  sr15 = (talks.number-1)*10


  talks = emp_expert_lectures.objects.filter(pf_no=profile.id).order_by("-date_entry")
  paginator15 = Paginator(talks, 10)
  page15 = request.GET.get('page15')
  mark15=0;
  if page15 != None:
    mark15=1
  else:
    mark15=0
  if page15 == None:
    page15=1
  talks = paginator15.page(page15)
  sr15 = (talks.number-1)*10


  context = {'about':detail.about,
    'user' : user,
    'detail' : detail,
    'publications' : publications,
    'mark' : mark,
    'sr' : sr,
    'books' : books,
    'mark2' : mark2,
    'sr2' : sr2,
    'conferences' : conferences,
    'mark3' : mark3,
    'sr3' : sr3,
    'thesis' : thesis,
    'mark4' : mark4,
    'sr4' : sr4,
    'research_projects' : research_projects,
    'mark4' : mark4,
    'sr4' : sr4,
    'thesis' : thesis,
    'consultancy_projects' : consultancy_projects,
    'mark5' : mark5,
    'sr5' : sr5,
    'patents' : patents,
    'sr6' : sr6,
    'mark6' : mark6,
    'techtransfers' : techtransfer,
    'sr7' : sr7,
    'mark7' : mark7,
    'thesis' : thesis,
    'mark8' : mark8,
    'sr8' : sr8,
    'phdthesis' : phdthesis,
    'mark9' : mark9,
    'sr9' : sr9,
    'year_range' : y,
    'foreign_visits' : foreign_visits,
    'mark10' : mark10,
    'sr10' : sr10,
    'indian_visits' : indian_visits,
    'mark11' : mark11,
    'sr11' : sr11,
    'events' : events,
    'mark12' : mark12,
    'sr12' : sr12,
    'confs' : confs,
    'mark13' : mark13,
    'sr13' : sr13,
    'awards' : awards,
    'mark14' : mark14,
    'sr14' : sr14,
    'talks' : talks,
    'mark15' : mark15,
    'sr15' : sr15,
    }
  return context
