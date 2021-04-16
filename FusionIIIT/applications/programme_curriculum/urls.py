from django.conf.urls import url
from django.urls import path, include
from . import views
from django.contrib import admin

app_name = 'programme_curriculum'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.main_page),
    path('programmes/', views.view_all_programmes, name='view_all_programmes'),
    path('working_curriculums/', views.view_all_working_curriculums, name='view_all_working_curriculums'),
    path('curriculums/<programme_id>/', views.view_curriculums_of_a_programme, name='view_curriculums_of_a_programme'),
    path('curriculum_semesters/<curriculum_id>/', views.view_semesters_of_a_curriculum, name='view_semesters_of_a_curriculum'),
    path('semester/<semester_id>/', views.view_a_semester_of_a_curriculum, name='view_a_semester_of_a_curriculum'),
    path('courses/', views.view_all_courses, name='view_all_courses'),
    path('course/<course_id>/', views.view_a_course, name='view_a_course'),
    # url(r'', views.programme_curriculum, name='programme_curriculum'),
    # path('programme',views.programme, name='program_and_curriculum_management'),
    # url(r'^programme/$', views.programme, name='programme'),
# """     url(r'^$', views.programme_curriculum, name='programme_curriculum'),
#     url(r'^admin/$', views.programme_curriculum_admin, name='programme_curriculum_admin'),
#     url(r'^programme/$', views.programme, name='programme'),
#     url(r'^working_curriculum/$', views.working_curriculum, name='working_curriculum'),
#     url(r'^curriculum_semester/(?P<cur_id>[0-9]+)$', views.curriculum_semester, name='curriculum_semester'),
#     url(r'^curriculum/(?P<pro_id>[0-9]+)$', views.curriculum, name='curriculum'),
#     url(r'^courses/(?P<cour_id>[0-9]+)$', views.courses, name='courses'), """
    # url(r'^semester/(?P<cur_id>[0-9]+)$', views.semester, name='semester'),
# """     url(r'^add_programme/$', views.add_programme, name='add_programme'),
#     url(r'^add_course/$', views.add_course, name='add_course'),
#     url(r'^add_curriculum_semester/$', views.add_curriculum_semester, name='add_curriculum_semester'),
#     url(r'^add_course_curriculum/$', views.add_course_curriculum, name='add_course_curriculum'),
#     url(r'^update_course/(?P<cour_id>[0-9]+)$', views.update_course, name='update_course') """

    # path('programme',views.programme, name='program_and_curriculum_management'),
    # path('curriculum/<pro_id>',views.curriculum, name='curriculum'),
    # path('courses/<cour_id>',views.courses, name='courses'),
    # path('semester/<cur_id>',views.semester, name='semester'),
    # path('add_programme',views.add_programme, name='add_programme'),
    # path('add_course',views.add_course, name='add_course'),
    # path('add_curriculum_semester',views.add_curriculum_semester, name='add_curriculum_semester'),
    # path('add_course_curriculum',views.add_course_curriculum, name='add_course_curriculum'),
    # path('update_course/<cour_id>',views.update_course, name='update_course')       
]

# from programme_curriculum import views

# urlpatterns = [
#     #path('admin/', admin.site.urls),
#     path('programme',views.programme, name='program_and_curriculum_management'),
#     path('curriculum/<pro_id>',views.curriculum, name='curriculum'),
#     path('courses/<cour_id>',views.courses, name='courses'),
#     path('semester/<cur_id>',views.semester, name='semester'),
#     path('add_programme',views.add_programme, name='add_programme'),
#     path('add_course',views.add_course, name='add_course'),
#     path('add_curriculum_semester',views.add_curriculum_semester, name='add_curriculum_semester'),
#     path('add_course_curriculum',views.add_course_curriculum, name='add_course_curriculum'),
#     path('update_course/<cour_id>',views.update_course, name='update_course')   
# ]
