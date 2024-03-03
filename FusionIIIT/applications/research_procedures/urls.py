from django.urls import include,path
from django.conf.urls import url
from . import views
from . import tests
app_name="research_procedures"

urlpatterns = [
      url(r'^$', views.patent_registration, name='patent_registration'),
      url(r'^update$', views.patent_status_update, name='patent_status_update'),
      url(r'^research_group$', views.research_group_create, name='research_group_create'),
      url(r'^project_insert$',views.project_insert,name='project_insert'),
      url(r'^consult_insert$',views.consult_insert,name='consult_insert'),
      url(r'^add_projects$',views.add_projects,name='add_projects'),
      url(r'^view_projects$',views.view_projects,name='view_projects'),
      path('add_requests/<id>/',views.add_requests,name='add_requests'),
      url(r'^api/',include('applications.research_procedures.api.urls')),
      path('view_requests/<id>/',views.view_requests),
      path('projects',views.projectss),
      path('submit_closure_report/<id>/',views.submit_closure_report, name="submit_closure_report"),
      path('add_fund_requests',views.add_fund_requests, name="add_fund_requests"),
      path('add_staff_requests',views.add_staff_requests, name="add_staff_requests"),
      
      
      url(r'^test/$',tests.testfun,name = 'test')

]