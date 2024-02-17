from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^stu/details', views.academic_procedures_student, name='student_procedures'),
    url(r'^stu/pre_registration' , views.student_pre_registration , name = 'pre_registration'),
    url(r'^stu/final_registration' , views.student_final_registration , name = 'final_registration'),
    url(r'^stu/view_registration' , views.student_view_registration , name = 'view_registration'),
    


    url(r'^stu/add_course' , views.add_course , name ='add_course') ,
    # url(r'^stu/dropCourse' , views.dropCourse , name = 'dropCourse'),
    # url(r'^stu/replaceCourse' , views.replaceCourse , name = 'replaceCourse')


    url(r'^acad/get_course_list' , views.get_course_list , name = 'get_course_list' ),
    url(r'^test/', views.test , name = 'test'),
    url(r'^get_user_info' , views.get_user_info , name  = 'get_user_info'),



    url(r'^fac/', views.academic_procedures_faculty, name='faculty_procedures'),

    #  these urls were designed previously and are not working any more

    # url(r'^stu', views.academic_procedures_student, name='student_procedures'),
    # url(r'^addThesis/', views.add_thesis, name='add_thesis'),
    # url(r'^approve_thesis/(?P<id>[0-9]+)/', views.approve_thesis, name='approve_thesis')

]