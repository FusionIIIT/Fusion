from django.conf.urls import url
from . import views

urlpatterns = [
    
    url(r'^new_consultant_project',views.consultant_api,name='consultant-post-api'),
    url(r'^new_research_project',views.research_api,name='research-post-api'),
    url(r'^get_research_projects',views.get_research_project_api,name='research-project-get-api'),
    url(r'^get_consultancy_projects',views.get_consultancy_project_api,name='consultancy-project-get-api'),
 
]