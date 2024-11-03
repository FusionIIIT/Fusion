from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'announcements/$', views.ListCreateAnnouncementView.as_view(),name='announcements'),
    url(r'dep-main/$', views.DepMainAPIView.as_view(), name='depmain'),
    url(r'fac-view/$', views.FacAPIView.as_view(), name='facapi'),
    url(r'staff-view/$',views.StaffAPIView.as_view(),name='staffapi'),
    url(r'all-students/(?P<bid>[0-9]+)/$', views.AllStudentsAPIView.as_view() ,name='all_students'),
    url(r'information/$', views.InformationAPIView.as_view(), name='information'),  # New endpoint
    url(r'information/update-create/$', views.InformationUpdateAPIView.as_view(), name='update_create_information'),  # New endpoint
    url(r'^labs/$', views.LabListView.as_view(), name='lab-list'),
    url(r'labsadd/$', views.LabAPIView.as_view(), name='add_lab'),  # Add Lab endpoint
    url(r'labs/delete/$', views.LabDeleteAPIView.as_view(), name='delete_lab'),
    url(r'feedback/create/$', views.FeedbackCreateAPIView.as_view(), name='feedback_create'),
   url(r'feedback/$', views.FeedbackListView.as_view(), name='getfeedback'),
]
