import json

from django.contrib.auth import logout
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
                                         Issue, IssueImage)
from applications.placement_cell.forms import (AddAchievement, AddCourse,
                                               AddEducation, AddExperience,
                                               AddPatent, AddProfile,
                                               AddProject, AddPublication,
                                               AddSkill)
from applications.placement_cell.models import (Achievement, Course, Education,
                                                Experience, Has, Patent,
                                                Project, Publication, Skill)
from applications.eis.models import faculty_about,emp_research_papers, emp_published_books


def contextstudentmanage(current,profile,request,user,editable):
  student = get_object_or_404(Student, Q(id=profile.id))
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
          if form.is_valid():
              skill = form.cleaned_data['skill']
              skill_rating = form.cleaned_data['skill_rating']
              try:
                  skill_id = Skill.objects.get(skill=skill)
              except Exception as e:
                  skill_id = Skill.objects.create(skill=skill)
                  skill_id.save()
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
              achievement_obj.save()
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
      if 'deleteach' in request.POST:
          hid = request.POST['deleteach']
          hs = Achievement.objects.get(Q(pk=hid))
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
  skills = Has.objects.filter(Q(unique_id=student))
  education = Education.objects.filter(Q(unique_id=student))
  course = Course.objects.filter(Q(unique_id=student))
  experience = Experience.objects.filter(Q(unique_id=student))
  project = Project.objects.filter(Q(unique_id=student))
  achievement = Achievement.objects.filter(Q(unique_id=student))
  publication = Publication.objects.filter(Q(unique_id=student))
  patent = Patent.objects.filter(Q(unique_id=student))
  context = {'user': user, 'profile': profile, 'skills': skills,
             'educations': education, 'courses': course, 'experiences': experience,
             'projects': project, 'achievements': achievement, 'publications': publication,
             'patent': patent, 'form': form, 'form1': form1, 'form14': form14,
             'form5': form5, 'form6': form6, 'form7': form7, 'form8': form8,
             'form10':form10, 'form11':form11, 'form12':form12, 'current':current,
             'editable': editable
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
    }
  return context