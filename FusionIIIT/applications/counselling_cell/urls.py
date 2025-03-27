from django.conf.urls import url

from . import views

app_name = 'counselling_cell'

urlpatterns = [
    url(r'^$',views.counselling_cell,name="counselling"),
    url(r'^raise_issue/',views.raise_issue,name="raiseissue"),
    url(r'^respond_issue/',views.respond_issue,name="respondissue"),
    url(r'^appoint_student_counsellors/',views.appoint_student_counsellors,name="appoint_student_counsellors"),
    url(r'^submitfaq/',views.submit_counselling_faq,name="submitfaq"),
    url(r'^assign_student_to_sg/',views.assign_student_to_sg,name="assign_student_to_sg"),
    url(r'^schedule_meeting/',views.schedule_meeting,name="schedule_meeting"),
]
