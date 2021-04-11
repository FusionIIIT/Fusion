from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse,JsonResponse
from django.contrib.auth.models import User
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
    CounsellingIssueCategory
)
from .handlers import (
    add_counselling_faq
)
from applications.academic_information.models import Student,ExtraInfo
# Create your views here.

# user = User.objects.filter(username=2017167).first()
# extra_info = ExtraInfo.objects.get(user=user)
# student = Student.objects.get(id=extra_info)
# print(extra_info.user_type)

# category = CounsellingIssueCategory(category_id="others",category="Others")
# category.save()
# faq = CounsellingIssueCategory.objects.all()
# print(faq) 
def counselling_cell(request):
    faqs = CounsellingFAQ.objects.all()
    categories = CounsellingIssueCategory.objects.all()
    print(faqs)
    context = {
        "faqs":faqs,
        "categories":categories
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
