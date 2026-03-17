from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'companies', views.CompanyViewSet, basename='api-company')
router.register(r'job-postings', views.JobPostingViewSet, basename='api-jobposting')
router.register(r'applications', views.JobApplicationViewSet, basename='api-application')
router.register(r'offers', views.JobOfferViewSet, basename='api-offer')
router.register(r'announcements', views.AnnouncementViewSet, basename='api-announcement')

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^stats/$', views.placement_stats_api, name='api-placement-stats'),
    url(r'^my-summary/$', views.my_application_summary_api, name='api-my-summary'),
]

