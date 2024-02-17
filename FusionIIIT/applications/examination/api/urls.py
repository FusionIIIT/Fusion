
from django.conf.urls import url
from django.urls import path, include
from . import views


urlpatterns = [
    url(r'^registered_student_details/', views.fetch_student_details, name='fetch_student_details'),
    
    # url(r'^add_student/', views.add_student, name='add_student'),

    url(r'^update_hidden_grade/', views.update_hidden_grade, name='update_hidden_grade'),


    url(r'^update_authenticator/', views.update_authenticator, name='update_authenticator'),

    url(r'^publish_grade/' , views.publish_grade , name='publish_grade')

]