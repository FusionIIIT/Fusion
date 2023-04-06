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
    url(r'placementrecord',views.placementrecord,name="placement-record-api")
]