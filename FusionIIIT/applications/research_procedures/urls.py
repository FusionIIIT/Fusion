from django.urls import include
from django.conf.urls import url
from . import views
from . import tests
app_name="research_procedures"

urlpatterns = [
      url(r'^$', views.rspc_profile, name='rspc_profile_main'),
      url(r'^user_profile', views.rspc_profile_faculty, name='rspc_profile_faculty'),
      url(r'^citation', views.generate_citation, name='generate_citation'),
      url(r'^report', views.rspc_generate_report, name='rspc_generate_report'),
      url(r'^update$', views.patent_status_update, name='patent_status_update'),
      url(r'^research_group$', views.research_group_create, name='research_group_create'),
      url(r'^project_insert$',views.project_insert,name='project_insert'),
      url(r'^consult_insert$',views.consult_insert,name='consult_insert'),
      url(r'^transfer_insert$',views.transfer_insert,name='transfer_insert'),
      url(r'^api/',include('applications.research_procedures.api.urls')),
      url(r'^test/$',tests.testfun,name = 'test')

]