import json

from django.db.models import Q
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from PIL import Image

from applications.globals.forms import IssueForm, WebFeedbackForm
from applications.globals.models import Feedback, Issue, IssueImage, ExtraInfo, HoldsDesignation
from applications.placement_cell.models import (Achievement, Course, Education, Experience, Has,
                                                Project, Publication, Skill, Patent)
from applications.academic_information.models import Student
from applications.placement_cell.forms import (AddEducation, AddProfile, AddSkill, AddCourse,
                                               AddAchievement, AddProject, AddPublication, AddPatent, AddExperience)
from Fusion.settings import LOGIN_URL


def index(request):
    context = {}
    print(request.user)
    if(str(request.user)!="AnonymousUser"):
        return HttpResponseRedirect('/dashboard/')
    else:
        return render(request, "globals/index1.html", context)


def login(request):
    context = {}
    return render(request, "globals/login.html", context)

def about(request):

    teams = {


        'uiTeam': {
            'teamId': "uiTeam",
            'teamName': "UI/UX",
        },

        'AcademicsTeam': {
            'teamId': "AcademicsTeam",
            'teamName': "Academics Module",
        },

        'eisTeam': {
            'teamId': "eisTeam",
            'teamName': "EIS Module",
        },

        'leaveTeam': {
            'teamId': "leaveTeam",
            'teamName': "Leave Module",
        },

        'CourseManagementTeam': {
            'teamId': "CourseManagementTeam",
            'teamName': "Course Management Module",
        },

        'complaintTeam': {
            'teamId': "complaintTeam",
            'teamName': "Complaint Module",
        },

        'CentralMessTeam': {
            'teamId': "CentralMessTeam",
            'teamName': "Mess Module",
        },

        'PlacementTeam': {
            'teamId': "PlacementTeam",
            'teamName': "Placement Module",
        },

        'ScholarshipTeam': {
            'teamId': "ScholarshipTeam",
            'teamName': "Awards and Scholarship Module",
        },
    }

    context = {'teams': teams,
               'psgTeam': {
                   'dev1': {'devName': 'Anuraag Singh',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'Developer'
                            },

                   'dev2': {'devName': 'Kanishka Munshi',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'UI/UX Developer'
                            },

                   'dev3': {'devName': 'M. Arshad Siddiqui',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'Database Designer'
                            },

                   'dev4': {'devName': 'Pranjul Shukla',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'Developer'
                            },

                   'dev5': {'devName': 'Saket Patel',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'Developer'
                            },
               },
               'AcademicsTeam': {
                   'dev1': {'devName': 'Anuraag Singh',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'Steering Group'
                            },

                   'dev2': {'devName': 'Achint Mistri',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'Developer'
                            },

                   'dev3': {'devName': 'Harshit Choubey',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'Developer'
                            },

                   'dev4': {'devName': 'Narosena Longkumar',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'Developer'
                            },
               },
               'uiTeam': {
                   'dev1': {'devName': 'Kanishka Munshi',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'Head UI Developer'
                            },

                   'dev2': {'devName': 'Mayank Saurabh',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'UI Developer'
                            },

                   'dev3': {'devName': 'Ravuri Abhignya',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'UI Developer'
                            },
               },

               'complaintTeam': {
                   'dev1': {'devName': 'Saksham Agarwal',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'Developer'
                            },

                   'dev2': {'devName': 'Rishti Gupta',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'Developer'
                            },

                   'dev3': {'devName': 'Shubham Yadav',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'Developer'
                            },

                   'dev4': {'devName': 'Amresh Kumar Verma',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'Developer'
                            },
               },
               'eisTeam': {

                   'dev1': {'devName': 'M. Arshad Siddiqui',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'Developer'
                            },
               },

               'leaveTeam': {
                   'dev1': {'devName': 'Pranjul Shukla',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'Developer'
                            },

                   'dev2': {'devName': 'Saket Patel',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'Developer'
                            },
               },

               'CentralMessTeam': {
                   'dev1': {'devName': 'Ankita Makker',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'Developer'
                            },

                   'dev2': {'devName': 'Vernika Jain',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'Developer'
                            },
               },

               'PlacementTeam': {
                   'dev1': {'devName': 'Arpit Jain',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'Developer'
                            },

                   'dev2': {'devName': 'Gautam Yadav',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'Developer'
                            },
               },

               'ComplaintTeam': {
                   'dev1': {'devName': 'Srigari Avilash Kumar',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'Developer'
                            },

                   'dev2': {'devName': 'NakulArya',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'Developer'
                            },
               },

               'ScholarshipTeam': {
                   'dev1': {'devName': 'Segu Balaji',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'Developer'
                            },

                   'dev2': {'devName': 'M. Shrisha',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'Developer'
                            },

                   'dev3': {'devName': 'Atla Shashidar Reddy',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'Developer'
                            },
               },

               'CourseManagementTeam': {
                   'dev1': {'devName': 'Animesh Pandey',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'Developer'
                            },

                   'dev2': {'devName': 'Paras Rastogi',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'Developer'
                            },
               },
               }
    return render(request, "globals/about.html", context)

@login_required(login_url=LOGIN_URL)
def dashboard(request):
    user = request.user
    profile = get_object_or_404(ExtraInfo, Q(user=user))
    if(str(request.user.extrainfo.user_type)=='faculty'):
        return HttpResponseRedirect('/eis/profile')
    print(str(request.user.extrainfo.department))
    if(str(request.user.extrainfo.department)=='department: Academics'):
        return HttpResponseRedirect('/aims')
    current = HoldsDesignation.objects.filter(Q(working=user, designation__name="student"))
    if current:
        student = get_object_or_404(Student, Q(id=profile.id))
        if request.method == 'POST':
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
                fut = request.POST.get('fut')
                # futu = request.POST.get('futu')
                studentplacement_obj = StudentPlacement.objects.get(unique_id=profile.id)
                # print(studentplacement_obj.future_aspect)
                # print('fut=', fut)
                # print('futu=', futu)
                # if studentplacement_obj.future_aspect == "HIGHER STUDIES":
                #     if futu == 2:
                #         studentplacement_obj.future_aspect = "PLACEMENT"
                # elif studentplacement_obj.future_aspect == "PLACEMENT":
                #     if futu == None:
                #         studentplacement_obj.future_aspect = "HIGHER STUDIES"
                if(fut==None):
                    studentplacement_obj.future_aspect="HIGHER STUDIES"
                else:
                    studentplacement_obj.future_aspect = "PLACEMENT"

                studentplacement_obj.save()
                extrainfo_obj = ExtraInfo.objects.get(user=user)
                extrainfo_obj.about_me = about_me
                extrainfo_obj.age = age
                extrainfo_obj.address = address
                extrainfo_obj.phone_no = contact
                extrainfo_obj.save()
                profile = get_object_or_404(ExtraInfo, Q(user=user))
            if 'skillsubmit' in request.POST:
                form = AddSkill(request.POST)
                if form.is_valid():
                    skill = form.cleaned_data['skill']
                    skill_rating = form.cleaned_data['skill_rating']
                    has_obj = Has.objects.create(unique_id=student,
                                                 skill_id=Skill.objects.get(skill=skill),
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
                   'patent': patent, 'form': form, 'form1': form1,
                   'form5': form5, 'form6': form6, 'form7': form7, 'form8': form8,
                   'form10':form10, 'form11':form11, 'form12':form12, 'current':current}
        return render(request, "dashboard/dashboard.html", context)
    else:
        context = {}
        return render(request, "dashboard/dashboard.html", context)

@login_required(login_url=LOGIN_URL)
def logout_view(request):
    logout(request)
    return redirect("/")


""" Views for Feedback and Issue reports """


@login_required(login_url=LOGIN_URL)
def feedback(request):
    feeds = Feedback.objects.all().order_by("rating").exclude(user=request.user)
    if feeds.count() > 5:
        feeds = feeds[:5]
    rated = []
    for feed in feeds:
        rated.append(range(feed.rating))
    feeds = zip(feeds, rated)
    if request.method == "POST":
        try:
            feedback = Feedback.objects.get(user=request.user)
        except:
            feedback = None
        if feedback:
            form = WebFeedbackForm(request.POST or None, instance=feedback)
        else:
            form = WebFeedbackForm(request.POST or None)
        feedback = form.save(commit=False)
        user_rating = request.POST.get("rating")
        feedback.user = request.user
        if int(user_rating) > 0 and int(user_rating) < 6:
            feedback.rating = user_rating
            feedback.save()
        form = WebFeedbackForm(instance=feedback)
        stars = []
        for i in range(0, int(feedback.rating)):
            stars.append(1)
        rating = 0
        for feed in Feedback.objects.all():
            rating = rating + feed.rating
        if Feedback.objects.all().count() > 0:
            rating = rating/Feedback.objects.all().count()
        context = {
            'form': form,
            "feedback": feedback,
            'rating': rating,
            "stars": stars,
            "reviewed": True,
            "feeds": feeds
        }
        return render(request, "globals/feedback.html", context)
    rating = 0
    for feed in Feedback.objects.all():
        rating = rating + feed.rating
    if Feedback.objects.all().count() > 0:
        rating = rating/Feedback.objects.all().count()
    try:
        feedback = Feedback.objects.get(user=request.user)
        form = WebFeedbackForm(instance=feedback)
    except:
        form = WebFeedbackForm()
        context = {"form": form, "rating": rating, "feeds": feeds}
        return render(request, "globals/feedback.html", context)
    stars = []
    for i in range(0, int(feedback.rating)):
        stars.append(1)
    context = {
        "rating": rating,
        "feedback": feedback,
        "stars": stars,
        "form": form,
        "reviewed": True,
        "feeds": feeds
    }
    return render(request, "globals/feedback.html", context)


@login_required(login_url=LOGIN_URL)
def issue(request):
    if request.method == "POST":
        form = IssueForm(request.POST or None)
        if form.is_valid():
            issue = form.save(commit=False)
            issue.user = request.user
            issue.save()
            for image in request.FILES.getlist('images'):
                try:
                    Image.open(image)
                    image = IssueImage.objects.create(image=image, user=request.user)
                    issue.images.add(image)
                except Exception as e:
                    pass
            issue.save()
            openissue = Issue.objects.filter(closed=False)
            closedissue = Issue.objects.filter(closed=True)
            form = IssueForm()
            context = {"form": form, "openissue": openissue, "closedissue": closedissue, }
            return render(request, "globals/issue.html", context)
        openissue = Issue.objects.filter(closed=False)
        closedissue = Issue.objects.filter(closed=True)
        form = IssueForm(request.POST)
        context = {"form": form, "openissue": openissue, "closedissue": closedissue, }
        return render(request, "globals/issue.html", context)
    openissue = Issue.objects.filter(closed=False)
    closedissue = Issue.objects.filter(closed=True)
    form = IssueForm()
    context = {"form": form, "openissue": openissue, "closedissue": closedissue, }
    return render(request, "globals/issue.html", context)


@login_required(login_url=LOGIN_URL)
def view_issue(request, id):
    if request.method == "POST":
        issue = get_object_or_404(Issue, id=id, user=request.user)
        form = IssueForm(request.POST or None, instance=issue)
        if form.is_valid():
            issue.save()
            remove = request.POST.get("remove-images")
            if remove:
                for img in issue.images.all():
                    img.delete()
            for image in request.FILES.getlist('images'):
                try:
                    Image.open(image)
                    image = IssueImage.objects.create(image=image, user=request.user)
                    issue.images.add(image)
                except Exception as e:
                    pass
            issue.save()
            form = IssueForm(instance=issue)
            context = {
                "form": form,
                "issue": issue,
            }
            return render(request, "globals/view_issue.html", context)
        form = IssueForm(request.POST or None)
        context = {
            "form": form,
            "issue": issue,
        }
        return render(request, "globals/view_issue.html", context)
    issue = get_object_or_404(Issue, id=id)
    form = None
    if request.user == issue.user:
        form = IssueForm(instance=issue)
    context = {
        "form": form,
        "issue": issue,
    }
    return render(request, "globals/view_issue.html", context)


@login_required(login_url=LOGIN_URL)
def support_issue(request, id):
    issue = get_object_or_404(Issue, id=id)
    supported = True
    if request.user in issue.support.all():
        issue.support.remove(request.user)
        supported = False
    else:
        issue.support.add(request.user)
    support_count = issue.support.all().count()
    context = {
        "supported": supported,
        "support_count": support_count,
    }
    return HttpResponse(json.dumps(context), "application/json")
