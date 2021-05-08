from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse,JsonResponse
from django.contrib.auth.models import User
from applications.academic_information.models import Student
import django. utils. timezone as timezone
from django.views.generic import (
    ListView,
    DeleteView,
    DetailView,
    UpdateView,
    CreateView
)
from .models import (
    CounsellingFAQ,
    CounsellingIssue,
    CounsellingIssueCategory,
    StudentCounsellingTeam
)
from .handlers import (
    add_counselling_faq,
    add_student_counsellors
)
from applications.academic_information.models import Student,ExtraInfo
# Create your views here.

# user = User.objects.filter(username=2017167).first()
# extra_info = ExtraInfo.objects.get(user=user)
# student = Student.objects.get(id=extra_info)
# print(extra_info.user_type)
# StudentCounsellingTeam.objects.filter(student=)
# category = CounsellingIssueCategory(category_id="others",category="Others")
# category.save()
# faq = CounsellingIssueCategory.objects.all()
# print(faq) 
def counselling_cell(request):
    year = timezone.now().year
    third_year_students = Student.objects.filter(batch=year-3)
    second_year_students = Student.objects.filter(batch=year-2)
    faqs = CounsellingFAQ.objects.all()
    categories = CounsellingIssueCategory.objects.all()
    student_coordinators = StudentCounsellingTeam.objects.filter(student_position="student_coordinator")
    student_guide = StudentCounsellingTeam.objects.filter(student_position="student_guide")
    
    context = {
        "faqs":faqs,
        "categories":categories,
        "third_year_students":third_year_students,
        "second_year_students":second_year_students,
        "student_counsellors":student_coordinators,
        "student_guide":student_guide
    }
    return render(request, "counselling_cell/counselling.html",context)
    
def raise_issue(request):
    return render(request, "counselling_cell/issues.html")

@csrf_exempt
# @login_required
# @transaction.atomic
def submit_counselling_faq(request):
    """
    This function is to record new faq submitted
    :param request:
        user: Current logged in user
    :variable:
         extra_info: Extra information of the user
    :return:
        data: to record success or any errors
    """
    # print("dsdss")
    # return JsonResponse({
    #     "hello":"sdsds"
    # })
    # print("dsdsds")
    user = request.user
    extra_info = ExtraInfo.objects.get(user=user)
    student = Student.objects.get(id=extra_info)
    if extra_info.user_type == 'student':
        data = add_counselling_faq(request, student)
        return JsonResponse(data)

@csrf_exempt
# @login_required
# @transaction.atomic
def appoint_student_counsellors(request):
    data = add_student_counsellors(request)
    return JsonResponse(data)

@csrf_exempt
def dismiss_student_coordinator(request):
    data = remove_student_coordinator(request)
    return JsonResponse(data)



