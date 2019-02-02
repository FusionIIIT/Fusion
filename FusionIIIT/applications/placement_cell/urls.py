from django.conf.urls import url
from . import views

app_name = 'placement'

urlpatterns = [
    url(r'^$', views.Placement, name='placement'),
    url(r'^student_records/invitation_status$', views.InvitationStatus, name='invitation_status'),
    url(r'^student_records/$', views.StudentRecords, name='student_records'),
    url(r'^manage_records/$', views.ManageRecords, name='manage_records'),
    url(r'^statistics/$', views.PlacementStatistics, name='placement_statistics'),
    url(r'^cv/(?P<username>[a-zA-Z0-9\.]{1,20})/$', views.cv, name="cv"),

]
