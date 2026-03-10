from django.conf.urls import url

from . import views

urlpatterns = [
    # url(r'^trial/$', views.trial,),
    # url(r'^test/$',views.vamshi,),
    url(r'^compounder/$',views.compounder_api_handler,),
    url(r'^student/$',views.student_api_handler,),
    # url(r'^compounder/$', views.compounder_view_api, name='compounder_view_api'),
    # url(r'^compounder/request$', views.compounder_request_api , name='compounder_request_api'),
    # url(r'^student/$', views.student_view_api, name='student_view'),
    # url(r'^student/request$', views.student_request_api, name='student_request_api')    
]