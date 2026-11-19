from django.urls import reverse
import json

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.core.files.storage import FileSystemStorage
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render
from django.conf import settings
from django.utils import timezone
from PIL import Image

from applications.academic_information.models import Student
from applications.globals.forms import IssueForm, WebFeedbackForm
from applications.globals.models import (ExtraInfo, Feedback, HoldsDesignation,
                                         Issue, IssueImage, DepartmentInfo,ModuleAccess)
from Fusion.settings.common import LOGIN_URL
from notifications.models import Notification
from .models import *


from django.contrib.auth.views import PasswordResetView
from django.shortcuts import render
from django.utils.timezone import now
from datetime import timedelta
from .models import PasswordResetTracker

class RateLimitedPasswordResetView(PasswordResetView):
    template_name = 'registration/password_reset_form.html'  # Customize as needed

    def post(self, request, *args, **kwargs):
        email = request.POST.get('email')
        if not email:
            return self.form_invalid(self.get_form())  # Default behavior for invalid forms

        # Check if the email exists in the tracker table
        tracker, created = PasswordResetTracker.objects.get_or_create(email=email)

        # Enforce rate limiting: Check if the reset was within the last 24 hours
        if tracker.last_reset and now() - tracker.last_reset < timedelta(days=1):
            # Pass error message to the template
            return render(
                request,
                self.template_name,
                {
                    'form': self.get_form(),  # Include the form for re-rendering
                    'error_message': "Password can only be reset once every 24 hours.",
                },
            )

        # Update the tracker with the current timestamp
        tracker.last_reset = now()
        tracker.save()

        # Proceed with the standard password reset process
        return super().post(request, *args, **kwargs)



@login_required(login_url='/accounts/login')
def index(request):
    context = {}
    if(str(request.user)!="AnonymousUser"):
        return HttpResponseRedirect('/dashboard/')
    else:
        return render(request, "globals/index1.html", context)

# Reset all passwords to 'user@123' in DEV environment
@login_required(login_url='/accounts/login')
def reset_all_pass(request):
    if settings.ALLOW_PASS_RESET:
        UserMod = get_user_model()
        arr = UserMod.objects.all()
        for e in arr:
            print(e.username)
            u = User.objects.get(username=e.username)
            u.set_password('user@123')
            u.save()
        context = {"done": len(arr)}
        return HttpResponse(json.dumps(context), "application/json")
    else:
        return HttpResponseNotFound("Not allowed")


@login_required(login_url=LOGIN_URL)
def about(request):
    teams = {
        'uiTeam': {
            'teamId': "uiTeam",
            'teamName': "Frontend Team",
        },

        'qaTeam': {
            'teamId': "qaTeam",
            'teamName': "Quality Analysis Team",
        },

        'academics_a_Team': {
            'teamId': "academics_a_Team",
            'teamName': "Academics (A) Module Team",
        },

        'academics_b_Team': {
            'teamId': "academics_b_Team",
            'teamName': "Academics (B) Module Team",
        },

        'spacsTeam': {
            'teamId': "spacsTeam",
            'teamName': "Awards & Scholarship Module Team",
        },

        'messTeam': {
            'teamId': "messTeam",
            'teamName': "Central Mess Module Team",
        },

        'complaintTeam': {
            'teamId': "complaintTeam",
            'teamName': "Complaint Module Team",
        },

        'eisTeam': {
            'teamId': "eisTeam",
            'teamName': "EIS Module Team",
        },

        'filetrackingTeam': {
            'teamId': "filetrackingTeam",
            'teamName': "File Tracking Module Team",
        },

        'gymkhanaTeam': {
            'teamId': "gymkhanaTeam",
            'teamName': "Gymkhana Module Team",
        },

        'leaveTeam': {
            'teamId': "leaveTeam",
            'teamName': "Leave Module Team",
        },

        'phcTeam': {
            'teamId': "phcTeam",
            'teamName': "Primary Health Center Module Team",
        },

        'placementTeam': {
            'teamId': "placementTeam",
            'teamName': "Placement Module Team",
        },

        'vhTeam': {
            'teamId': "vhTeam",
            'teamName': "Visitors Hostel Module Team",
        },
    }

    context = {'teams': teams,
               'psgTeam': {
                   'dev1': {'devName': 'Anuraag Singh',
                            'devImage': 'team/2015043.jpeg',
                            'devTitle': 'Developer'
                            },

                   'dev2': {'devName': 'Kanishka Munshi',
                            'devImage': 'team/2015121.jpg',
                            'devTitle': 'Head UI Developer'
                            },

                   'dev3': {'devName': 'M. Arshad Siddiqui',
                            'devImage': 'team/2015153.jpg',
                            'devTitle': 'Database Designer'
                            },

                   'dev4': {'devName': 'Pranjul Shukla',
                            'devImage': 'team/2015325.jpg',
                            'devTitle': 'Developer'
                            },

                   'dev5': {'devName': 'Saket Patel',
                            'devImage': 'team/2015329.jpg',
                            'devTitle': 'Head Developer'
                            },
               },

               'uiTeam': {
                   'dev1': {'devName': 'Kanishka Munshi',
                            'devImage': 'team/2015121.jpg',
                            'devTitle': 'Head UI Developer'
                            },

                   'dev2': {'devName': 'Ravuri Abhignya',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'Developer'
                            },
               },

               'qaTeam': {
                   'dev1': {'devName': 'Anuj Upadhaya',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'Member'
                            },

                   'dev2': {'devName': 'Avinash Kumar',
                            'devImage': 'team/2015058.jpg',
                            'devTitle': 'Head'
                            },

                   'dev3': {'devName': 'G. Vijay Ram',
                            'devImage': 'team/2015095.jpg',
                            'devTitle': 'Member'
                            },
               },

               'academics_a_Team': {
                   'dev1': {'devName': 'Anuraag Singh',
                            'devImage': 'team/2015043.jpeg',
                            'devTitle': '2015043'
                            },

                   'dev2': {'devName': 'Achint Mistry',
                            'devImage': 'zlatan.jpg',
                            'devTitle': '2015009'
                            },

                   'dev3': {'devName': 'Harshit Choubey',
                            'devImage': 'team/2015103.jpeg',
                            'devTitle': '2015103'
                            },

                   'dev4': {'devName': '',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'Rollnum'
                            },
               },

               'academics_b_Team': {
                   'dev1': {'devName': 'Mayank Saurabh',
                            'devImage': 'team/2015153.jpg',
                            'devTitle': 'UI Developer'
                            },

                   'dev2': {'devName': 'Narosenla Longkumer',
                            'devImage': 'team/2015165.jpg',
                            'devTitle': '2015165'
                            },

                   'dev3': {'devName': 'Rambha Sirisha',
                            'devImage': 'team/2015203.jpg',
                            'devTitle': '2015203'
                            },

                   'dev4': {'devName': '',
                            'devImage': 'zlatan.jpg',
                            'devTitle': '2015'
                            },

                   'dev5': {'devName': '',
                            'devImage': 'zlatan.jpg',
                            'devTitle': '2015'
                            },
               },


               'complaintTeam': {
                   'dev1': {'devName': 'Kanishka Munshi',
                            'devImage': 'team/2015121.jpg',
                            'devTitle': 'UI/UX Developer'
                            },

                   'dev2': {'devName': 'Amresh Kumar Verma',
                            'devImage': 'zlatan.jpg',
                            'devTitle': '2015027'
                            },

                   'dev3': {'devName': 'Rishti Gupta',
                            'devImage': 'zlatan.jpg',
                            'devTitle': '2015209'
                            },

                   'dev4': {'devName': 'Shubham Yadav',
                            'devImage': 'team/2015248.jpg',
                            'devTitle': '2015248'
                            },

                   'dev5': {'devName': '',
                            'devImage': 'zlatan.jpg',
                            'devTitle': ''
                            },
               },

               'eisTeam': {
                   'dev1': {'devName': 'Kanishka Munshi',
                            'devImage': 'team/2015121.jpg',
                            'devTitle': 'UI/UX Developer'
                            },

                   'dev2': {'devName': 'Mayank Saurabh',
                            'devImage': 'team/2015147.jpg',
                            'devTitle': 'UI Developer'
                            },

                   'dev3': {'devName': 'M. Arshad Siddiqui',
                            'devImage': 'team/2015153.jpg',
                            'devTitle': 'Backend Developer'
                            },
               },

               'filetrackingTeam': {
                   'dev1': {'devName': 'Mayank Saurabh',
                            'devImage': 'team/2015147.jpg',
                            'devTitle': 'UI/UX Developer'
                            },

                   'dev2': {'devName': 'Deepak Chhipa',
                            'devImage': 'team/2015076.jpg',
                            'devTitle': '2015076'
                            },

                   'dev3': {'devName': '',
                            'devImage': 'zlatan.jpg',
                            'devTitle': '2015'
                            },

                   'dev4': {'devName': '',
                            'devImage': 'zlatan.jpg',
                            'devTitle': '2015'
                            },

                   'dev5': {'devName': '',
                            'devImage': 'zlatan.jpg',
                            'devTitle': '2015'
                            },
               },

               'gymkhanaTeam': {
                   'dev1': {'devName': 'Kanishka Munshi',
                            'devImage': 'team/2015121.jpg',
                            'devTitle': 'UI/UX Developer'
                            },
               },


               'leaveTeam': {
                   'dev1': {'devName': 'Kanishka Munshi',
                            'devImage': 'team/2015121.jpg',
                            'devTitle': 'UI/UX Developer'
                            },

                   'dev2': {'devName': 'Saket Patel',
                            'devImage': 'team/2015329.jpg',
                            'devTitle': 'Backend Developer'
                            },
               },

               'messTeam': {
                   'dev1': {'devName': 'Kanishka Munshi',
                            'devImage': 'team/2015121.jpg',
                            'devTitle': 'UI/UX Developer'
                            },

                   'dev2': {'devName': 'Ankita Makker',
                            'devImage': 'team/2015034.jpg',
                            'devTitle': '2015034'
                            },

                   'dev3': {'devName': 'K. Venkateshwar Reddy',
                            'devImage': 'team/2015117.jpg',
                            'devTitle': '2015117'
                            },

                   'dev4': {'devName': 'Pratibha Singh',
                            'devImage': 'team/2015189.jpg',
                            'devTitle': '2015189'
                            },

                   'dev5': {'devName': 'Varnika Jain',
                            'devImage': 'team/2015268.jpg',
                            'devTitle': '2015268'
                            },
               },

               'phcTeam': {
                   'dev1': {'devName': 'Ravuri Abhignya',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'UI/UX Developer'
                            },

                   'dev2': {'devName': 'B. Krishnanjali',
                            'devImage': 'team/2015061.jpeg',
                            'devTitle': '2015061'
                            },

                   'dev3': {'devName': 'K. Jahnavi',
                            'devImage': 'team/2015120.jpeg',
                            'devTitle': '2015120'
                            },

                   'dev4': {'devName': 'K. Sai Srikar',
                            'devImage': 'team/2015127.jpg',
                            'devTitle': '2015127'
                            },

                   'dev5': {'devName': 'Priyanka Agarwal',
                            'devImage': 'team/2015192.jpg',
                            'devTitle': '2015192'
                            },
               },


               'placementTeam': {
                   'dev1': {'devName': 'Kanishka Munshi',
                            'devImage': 'team/2015121.jpg',
                            'devTitle': 'UI/UX Developer'
                            },

                   'dev2': {'devName': 'Avinash Kumar',
                            'devImage': 'team/2015058.jpg',
                            'devTitle': '2015058'
                            },

                   'dev3': {'devName': 'Arpit Jain',
                            'devImage': 'team/2015047.jpg',
                            'devTitle': '2015047'
                            },

                   'dev4': {'devName': 'Gautam Yadav',
                            'devImage': 'zlatan.jpg',
                            'devTitle': '2015093'
                            },

                   'dev5': {'devName': '',
                            'devImage': 'zlatan.jpg',
                            'devTitle': '2015'
                            },
               },

               'spacsTeam': {
                   'dev1': {'devName': 'Ravuri Abhignya',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'UI/UX Developer'
                            },

                   'dev2': {'devName': 'Atla Shashidhar Reddy',
                            'devImage': 'team/2015056.jpeg',
                            'devTitle': '2015056'
                            },

                   'dev3': {'devName': 'Gopisetti Pramod Kumar',
                            'devImage': 'team/2015314.jpg',
                            'devTitle': '2015314'
                            },

                   'dev4': {'devName': 'Segu Balaji',
                            'devImage': 'team/2015335.png',
                            'devTitle': '2015335'
                            },

                   'dev5': {'devName': '',
                            'devImage': 'zlatan.jpg',
                            'devTitle': ''
                            },
               },

               'vhTeam': {
                   'dev1': {'devName': 'Ravuri Abhignya',
                            'devImage': 'zlatan.jpg',
                            'devTitle': 'UI/UX Developer'
                            },

                   'dev2': {'devName': 'Imdad Ali',
                            'devImage': 'zlatan.jpg',
                            'devTitle': '2015'
                            },

                   'dev3': {'devName': 'Prashant Shivam',
                            'devImage': 'zlatan.jpg',
                            'devTitle': '2015'
                            },

                   'dev4': {'devName': 'Riya Goyal',
                            'devImage': 'team/2015210.png',
                            'devTitle': '2015210'
                            },

                   'dev5': {'devName': 'Anuj Upadhyay',
                            'devImage': 'zlatan.jpg',
                            'devTitle': '2015'
                            },
               },
               }
    return render(request, "globals/about.html", context)

@login_required(login_url='/accounts/login')
def login(request):
    context = {}
    return render(request, "globals/login.html", context)

@login_required(login_url='/accounts/login')
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
    # cse_faculty = ExtraInfo.objects.filter(user_type = 'faculty', department = DepartmentInfo.objects.get(name = 'CSE'))
    # ece_faculty = ExtraInfo.objects.filter(user_type = 'faculty', department = DepartmentInfo.objects.get(name = 'ECE'))
    # me_faculty = ExtraInfo.objects.filter(user_type = 'faculty', department = DepartmentInfo.objects.get(name = 'ME'))
    # des_faculty = ExtraInfo.objects.filter(user_type = 'faculty', department = DepartmentInfo.objects.get(name = 'Design'))
    # ns_faculty = ExtraInfo.objects.filter(user_type = 'faculty', department = DepartmentInfo.objects.get(name = 'Natural Science'))
    # cse_students = ExtraInfo.objects.filter(user_type = 'student', department = DepartmentInfo.objects.get(name = 'CSE'))
    # ece_students = ExtraInfo.objects.filter(user_type = 'student', department = DepartmentInfo.objects.get(name = 'ECE'))
    # me_students = ExtraInfo.objects.filter(user_type = 'student', department = DepartmentInfo.objects.get(name = 'ME'))
    # des_students = ExtraInfo.objects.filter(user_type = 'student', department = DepartmentInfo.objects.get(name = 'Design'))
    # ns_students = ExtraInfo.objects.filter(user_type = 'student', department = DepartmentInfo.objects.get(name = 'Natural Science'))
    # students_2017 = Student.objects.filter(batch = 2017)
    # students_2016 = Student.objects.filter(batch = 2016)
    # students_2015 = Student.objects.filter(batch = 2015)
    # students_2019 = Student.objects.filter(batch = 2019)
    # students_2018 = Student.objects.filter(batch = 2018)
    # data = {'cse': cse_faculty,
    #         'ece': ece_faculty,
    #         'me': me_faculty,
    #         'des': des_faculty,
    #         'ns': ns_faculty,
    #         'students_2019': students_2019,
    #         'students_2018': students_2018,
    #         'students_2017': students_2017,
    #         'students_2016': students_2016,
    #         'students_2015': students_2015}
    user=request.user
    notifs=request.user.notifications.all()
    name = request.user.first_name +"_"+ request.user.last_name
    desig = list(HoldsDesignation.objects.select_related('user','working','designation').all().filter(working = request.user).values_list('designation'))
    b = [i for sub in desig for i in sub]
    design = HoldsDesignation.objects.select_related('user','designation').filter(working=request.user)

    designation=[]
    for i in design:
        designation.append(str(i.designation))

    roll_ = []
    for i in b :
        name_ = get_object_or_404(Designation, id = i)
        roll_.append(str(name_.name))

    print("modules are")
    print(request.session.get('moduleAccessRights'))
    context={
        'notifications':notifs,
        'Curr_desig' : roll_,
        'designation' : designation,
        
    }
    # a=HoldsDesignation.objects.select_related('user','working','designation').filter(designation = user)
    print(context)
    print(type(user.extrainfo.user_type))
    if(request.user.get_username() == 'director'):
        return render(request, "dashboard/director_dashboard2.html", {})
    elif( "dean_rspc" in designation):
        return render(request, "dashboard/dashboard.html", context)
    elif user.extrainfo.user_type != "student":
        print ("inside")
        designat = HoldsDesignation.objects.select_related().filter(user=user)
        response = {'designat':designat}
        context.update(response)
        return render(request, "dashboard/dashboard.html", context)
    else:
        print ("inside2")
        
        return render(request, "dashboard/dashboard.html", context)


@login_required(login_url=LOGIN_URL)
def logout_view(request):
    logout(request)
    return redirect("/")


""" Views for Feedback and Issue reports """


@login_required(login_url=LOGIN_URL)
def feedback(request):
    feeds = Feedback.objects.select_related('user').all().order_by("rating").exclude(user=request.user)
    if feeds.count() > 5:
        feeds = feeds[:5]
    rated = []
    for feed in feeds:
        rated.append(range(feed.rating))
    feeds = zip(feeds, rated)
    if request.method == "POST":
        try:
            feedback = Feedback.objects.select_related('user').get(user=request.user)
        except Exception as e:
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
            rating = round(rating/Feedback.objects.all().count(),1)
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
        rating = round(rating/Feedback.objects.all().count(),1)
    try:
        feedback = Feedback.objects.select_related('user').get(user=request.user)
        form = WebFeedbackForm(instance=feedback)
    except Exception as e:
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
            openissue = Issue.objects.select_related('user').prefetch_related('images','support').filter(closed=False)
            closedissue = Issue.objects.select_related('user').prefetch_related('images','support').filter(closed=True)
            form = IssueForm()
            context = {"form": form, "openissue": openissue, "closedissue": closedissue, }
            return render(request, "globals/issue.html", context)
        openissue = Issue.objects.select_related('user').prefetch_related('images','support').filter(closed=False)
        closedissue = Issue.objects.select_related('user').prefetch_related('images','support').filter(closed=True)
        form = IssueForm(request.POST)
        context = {"form": form, "openissue": openissue, "closedissue": closedissue, }
        return render(request, "globals/issue.html", context)
    openissue = Issue.objects.select_related('user').prefetch_related('images','support').filter(closed=False)
    closedissue = Issue.objects.select_related('user').prefetch_related('images','support').filter(closed=True)
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

@login_required(login_url=LOGIN_URL)
def search(request):
    """
    Search endpoint.
    Renders search results populated with results from 'q' GET query.
    If length of the query is less than 3 or no results are found, shows a
    helpful message instead.
    Algorithm: Includes the first 15 users whose first/last name starts with the query words.
               Thus, searching 'Atu Gu' will return 'Atul Gupta' as one result.

               Note: All the words in the query must be matched.
               While, searching 'Atul Kumar', the word 'Kumar' won't match either 'Atul' or 'Gupta'
               and thus it won't be included in the search results.
    """
    key = request.GET['q']
    if len(key) < 3:
        return render(request, "globals/search.html", {'sresults': ()})
    words = (w.strip() for w in key.split())
    name_q = Q()
    for token in words:
        name_q = name_q & (Q(first_name__icontains=token) | Q(last_name__icontains=token))#search constraints
    search_results = User.objects.filter(name_q)[:15]
    if len(search_results) == 0:
        search_results = []
    context = {'sresults':search_results}
    return render(request, "globals/search.html", context),

@login_required(login_url=LOGIN_URL)
def update_global_variable(request):
    if request.method == 'POST':
        selected_option = request.POST.get('dropdown')
        request.session['currentDesignationSelected'] = selected_option
        module_access = ModuleAccess.objects.filter(designation=selected_option).first()
        if module_access:
            access_rights = {}
    
            field_names = [field.name for field in ModuleAccess._meta.get_fields() if field.name not in ['id', 'designation']]
    
            for field_name in field_names:
                access_rights[field_name] = getattr(module_access, field_name)
    
        request.session['moduleAccessRights'] = access_rights      
                
        print(selected_option)
        print(request.session['currentDesignationSelected'])
        return HttpResponseRedirect('/dashboard')
    # Redirect to home if not a POST request or some issue occurs
    return HttpResponseRedirect(reverse('home'))