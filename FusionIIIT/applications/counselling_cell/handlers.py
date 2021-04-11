from  .models import (
    CounsellingFAQ,
    CounsellingIssueCategory
)

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
    category = CounsellingIssueCategory.objects.filter(category_id=request.POST.get('category'))[0]
    question = request.POST.get('question')
    faq_object = CounsellingFAQ(counselling_answer=answer,counselling_question=question,counseliing_category=category)

    faq_object.save()
    data = {
        'status': 1
    }
    return data

