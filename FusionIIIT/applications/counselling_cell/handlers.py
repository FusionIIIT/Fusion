from  .models import FAQ
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
    # date_today = datetime.now().date()
    # mess_optn = Messinfo.objects.get(student_id=student)
    answer = request.POST.get('answer')
    category = request.POST.get('category')
    question = request.POST.get('question')
    print(answer)
    # faq_object = FAQ(answer=answer,question=question,category=category)

    # faq_object.save()
    # data = {
    #     'status': 1
    # }
    return data

