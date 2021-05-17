from  .models import (
    CounsellingFAQ,
    CounsellingIssueCategory,
    StudentCounsellingTeam
)
from applications.academic_information.models import Student,ExtraInfo
from django.contrib.auth.models import User

def add_counselling_faq(request, student):
    """
    This function is to record the feedback submitted
    :param request:
        description: Description of feedback
        feedback_type: Type of feedback
    :param student: Student placing the request
    :variable:
         extra_info: Extra information of the user
         date_today: Today's date
         feedback_object: Object of Feedback to store current variables
    :return:
        data: to record success or any errors
    """

    answer = request.POST.get('answer')
    category = CounsellingIssueCategory.objects.filter(category_id=request.POST.get('category')).first()
    question = request.POST.get('question')
    faq_object = CounsellingFAQ(counselling_answer=answer,counselling_question=question,counselling_category=category)

    faq_object.save()
    data = {
        'status': 1
    }
    return data

def add_student_counsellors(request):
    """
    This function is to record the feedback submitted
    :param request:
        description: Description of feedback
        feedback_type: Type of feedback
    :param student: Student placing the request
    :variable:
         extra_info: Extra information of the user
         date_today: Today's date
         feedback_object: Object of Feedback to store current variables
    :return:
        data: to record success or any errors
    """
    idd = position = request.POST.get('username')
    user = User(username=idd)
    
    extrainfo = ExtraInfo(user=user)
    student = Student(id=extrainfo)
    position = request.POST.get('position')
    # position="student_coordinator"
    student_counsellor_object = StudentCounsellingTeam(student_id=student,student_position=position)

    student_counsellor_object.save()
    data = {
        'status': 1
    }
    return data


def remove_student_coordinator(request):
    """
    This function is to record the feedback submitted
    :param request:
        description: Description of feedback
        feedback_type: Type of feedback
    :param student: Student placing the request
    :variable:
         extra_info: Extra information of the user
         date_today: Today's date
         feedback_object: Object of Feedback to store current variables
    :return:
        data: to record success or any errors
    """

    answer = request.POST.get('answer')
    category = CounsellingIssueCategory.objects.filter(category_id=request.POST.get('category')).first()
    question = request.POST.get('question')
    faq_object = CounsellingFAQ(counselling_answer=answer,counselling_question=question,counselling_category=category)

    faq_object.save()
    data = {
        'status': 1
    }
    return data

