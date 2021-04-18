from django.conf.urls import url

from . import views

app_name = 'counselling_cell'

urlpatterns = [
    url(r'^$',views.counselling_cell,name="counselling"),
    url(r'^raise_issue/',views.raise_issue,name="raiseissue"),
    url(r'^appoint_student_counsellors/',views.appoint_student_counsellors,name="appoint_student_counsellors"),
    url(r'^submitfaq/',views.submit_counselling_faq,name="submitfaq")
    
]
