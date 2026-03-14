from rest_framework.routers import DefaultRouter
from .views import *
from django.urls import include,path
from django.conf.urls import url
from . import views

app_name="research_procedures"

router = DefaultRouter()
# router.register(r'patent', PatentViewSet)

urlpatterns = router.urls

urlpatterns = [
      # url(r'^$', views.view_projects, name='patent_registration'),
      # url(r'^update$', views.patent_status_update, name='patent_status_update'),
      # url(r'^research_group$', views.research_group_create, name='research_group_create'),
      # url(r'^project_insert$',views.project_insert,name='project_insert'),
      # url(r'^consult_insert$',views.consult_insert,name='consult_insert'),
      # url(r'^add_projects$',views.add_projects,name='add_projects'),
      # url(r'^view_projects$',views.view_projects,name='view_projects'),
      # # path('add_requests/<id>/<pj_id>/',views.add_requests,name='add_requests'),
      # url(r'^api/',include('applications.research_procedures.api.urls')),
      # path('view_requests/<id>/',views.view_requests),
      path('projects',views.view_projects),
      path('view_project_info/<id>/',views.view_project_info),
      # path('submit_closure_report/<id>/',views.submit_closure_report, name="submit_closure_report"),
      # path('add_fund_requests/<pj_id>/',views.add_fund_requests, name="add_fund_requests"),
      # path('add_staff_requests/<pj_id>/',views.add_staff_requests, name="add_staff_requests"),
      path('view_project_inventory/<pj_id>/',views.view_project_inventory, name="view_project_inventory"),
      path('view_project_staff/<pj_id>/',views.view_project_staff, name="view_project_staff"),
      # path('add_financial_outlay/<pid>/',views.add_financial_outlay, name="add_financial_outlay"),
      # path('financial_outlay/<pid>/',views.financial_outlay_form, name="financial_outlay_form"),
      path('view_financial_outlay/<pid>/',views.view_financial_outlay, name="view_financial_outlay"),
      # path('add_staff_details/<pid>/',views.add_staff_details, name="add_staff_details"),
      path('view_staff_details/<pid>/',views.view_staff_details, name="view_staff_details"),
      # path('add_staff_request/<id>/',views.add_staff_request, name="add_staff_request"),
      # path('inbox',views.inbox, name="inbox"),
      # path('view_request_inbox',views.view_request_inbox, name="view_request_inbox"),
      # path('forward_request',views.forward_request, name="forward_request"),
      
      

]
print("URL patterns",urlpatterns)