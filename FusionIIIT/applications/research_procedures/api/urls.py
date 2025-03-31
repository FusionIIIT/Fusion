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
      # path('projects',views.view_projects),
      # path('view_project_info/<id>/',views.view_project_info),
      url(r'^create-expenditure', views.create_expenditure, name='create_expenditure'),
      url(r'^create-staff', views.create_staff, name='create_staff'),
      url(r'^add-ad-committee', views.add_ad_committee, name='add_ad_committee'),
      url(r'^committee-action', views.committee_action, name='committee_action'),
      url(r'^staff-decision', views.staff_decision, name='staff_decision'),
      url(r'^project-decision', views.project_decision, name='project_decision'),
      url(r'^add-project', views.add_project, name='add_project'),
      url(r'^register-commence-project', views.register_commence_project, name='register_commence_project'),
      url(r'^project-closure', views.project_closure, name='project_closure'),
      url(r'^staff-document-upload', views.staff_document_upload, name='staff_document_upload'),
      url(r'^get-projects', views.get_projects, name='get_projects'),
      url(r'^get-copis', views.get_copis, name='get_copis'),
      url(r'^get-profIDs', views.get_profIDs, name='get_profIDs'),
      url(r'^staff-selection-report', views.staff_selection_report, name='staff-selection-report'),
      url(r'^get-staff-positions', views.get_staff_positions, name='get_staff_positions'),
      url(r'^get-budget', views.get_budget, name='get_budget'),
      url(r'^get-staff', views.get_staff, name='get_staff'),
      url(r'^get-expenditure', views.get_expenditure, name='get_expenditure'),
      url(r'^get-user', views.get_user, name='get_user'),
      url(r'^get-PIDs', views.get_PIDs, name='get_PIDs'),
      url(r'^get-inbox', views.get_inbox, name='get_inbox'),
      url(r'^get-processed', views.get_processed, name='get_processed'),
      url(r'^get-file', views.get_file, name='get_file'),
      url(r'^get-history', views.get_history, name='get_history'),
      url(r'^forward-file', views.forwarding_file, name='forwarding_file'),
      url(r'^reject-file', views.reject_file, name='reject_file'),
      url(r'^approve-file', views.approve_file, name='approve_file'),
      url(r'^accept-completion', views.accept_completion, name='accept_completion'),
      # path('submit_closure_report/<id>/',views.submit_closure_report, name="submit_closure_report"),
      # path('add_fund_requests/<pj_id>/',views.add_fund_requests, name="add_fund_requests"),
      # path('add_staff_requests/<pj_id>/',views.add_staff_requests, name="add_staff_requests"),
      # path('view_project_inventory/<pj_id>/',views.view_project_inventory, name="view_project_inventory"),
      # path('view_project_staff/<pj_id>/',views.view_project_staff, name="view_project_staff"),
      # path('add_financial_outlay/<pid>/',views.add_financial_outlay, name="add_financial_outlay"),
      # path('financial_outlay/<pid>/',views.financial_outlay_form, name="financial_outlay_form"),
      # path('view_financial_outlay/<pid>/',views.view_financial_outlay, name="view_financial_outlay"),
      # path('add_staff_details/<pid>/',views.add_staff_details, name="add_staff_details"),
      # path('view_staff_details/<pid>/',views.view_staff_details, name="view_staff_details"),
      # path('add_staff_request/<id>/',views.add_staff_request, name="add_staff_request"),
      # path('inbox',views.inbox, name="inbox"),
      # path('view_request_inbox',views.view_request_inbox, name="view_request_inbox"),
      # path('forward_request',views.forward_request, name="forward_request"),
      
      

]
print("URL patterns",urlpatterns)