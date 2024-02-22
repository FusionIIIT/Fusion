# from django.conf.urls import url
# from django.urls import path, include
# from rest_framework.routers import DefaultRouter
# from . import views 

# router = DefaultRouter()
# # router.register(r'patent', PatentViewSet)

# urlpatterns = [
#     # url(r'^$', views.patent_registration, name='patent_registration-api'),
#     # url(r'^update$', views.patent_status_update, name='patent_status_update-api'),
#     # url(r'^research_group$', views.research_group_create, name='research_group_create-api'),
#     # url(r'^project_insert$', views.project_insert, name='project_insert-api'),
#     # url(r'^consult_insert$', views.consult_insert, name='consult_insert-api'),
#     url(r'^add_projects$', views.add_projects, name='add_projects-api'),
#     url(r'^view_projects$', views.view_projects, name='view_projects-api'),
#     path('add_requests/<id>/', views.add_requests, name='add_requests-api'),
#     url(r'^api/', include('applications.research_procedures.api.urls')),
#     path('view_requests/<id>/', views.view_requests, name='view_requests-api'),
#     path('projects', views.projectss, name='projects-api'),
#     path('submit_closure_report/<id>/', views.submit_closure_report, name="submit_closure_report-api"),
#     path('add_fund_requests', views.add_fund_requests, name="add_fund_requests-api"),
#     path('add_staff_requests', views.add_staff_requests, name="add_staff_requests-api"),
#     url(r'^test/$', tests.testfun, name='test-api'),
# ]


# # urlpatterns = router.urls
# # print("URL patterns",urlpatterns)