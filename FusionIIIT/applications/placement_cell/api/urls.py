from django.conf.urls import url

from . import views

urlpatterns = [
    # generic profile endpoint
    # url(r'^projects/(?P<username>\w+)/', views.projects, name='projects-api'),
    # current user profile
    url(r'projects/', views.projects, name='projects-api'),
    url(r'experiences/',views.experiences,name="experiences-api"),
    url(r'skills/',views.skills,name="skills-api"),
    url(r'has/',views.has,name="has-api"),
    url(r'education/',views.education,name="eduaction-api"),
    url(r'courses/',views.courses,name="courses-api"),
    url(r'conference/',views.conference,name="conference-api"),
    url(r'publications/',views.publications,name="publications-api"),
    url(r'references/',views.references,name="references-api"),
    url(r'coauthor/',views.coauthor,name="coauthor-api"),
    url(r'patent/',views.patent,name="patent-api"),
    url(r'coinventor/',views.coinventor,name="coinventor-api"),
    url(r'interest/',views.interest,name="interest-api"),
    url(r'achievement/',views.achievement,name="achievement-api"),
    url(r'extracurricular/',views.extracurricular,name="extracurricular-api"),
    url(r'messageofficer/',views.messageofficer,name="messageofficer-api"),
    url(r'notifystudent/',views.notifystudent,name="notifystudent-api"),
    url(r'role/',views.role,name="role-api"),
    url(r'companydetails/',views.companydetails,name="companydetails-api"),
    url(r'placementstatus/',views.placementstatus,name="placementstatus-api"),
    url(r'placementrecord/',views.placementrecord,name="placementrecord-api"),
    url(r'studentrecord/',views.studentrecord,name="studentrecord-api"),
    url(r'chairmanvisit/',views.chairmanvisit,name="chairmanvisit-api"),
    url(r'placementschedule/',views.placementschedule,name="placementschedule-api"),
    url(r'studentplacement/',views.studentplacement,name="studentplacement-api"),
]