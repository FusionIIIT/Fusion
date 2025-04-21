from rest_framework.routers import DefaultRouter
from .views import *
from django.urls import include,path
from django.conf.urls import url
from . import views

app_name="research_procedures"
router = DefaultRouter()
urlpatterns = router.urls

urlpatterns = [
      url(r'^add-ad-committee', views.add_ad_committee, name='add_ad_committee'),
      url(r'^committee-action', views.committee_action, name='committee_action'),
      url(r'^staff-decision', views.staff_decision, name='staff_decision'),
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
      url(r'^get-PIDs', views.get_PIDs, name='get_PIDs'),
]
print("URL patterns",urlpatterns)