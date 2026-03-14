from django.conf.urls import url
from django.urls import path
# from . import views
from . import form_views


app_name = 'hr2'

urlpatterns = [
    # LTC form
    url('ltc/', form_views.LTC.as_view(), name='LTC_form'),
    #  cpda advance form
    url('cpdaadv/', form_views.CPDAAdvance.as_view(), name='CPDAAdvance_form'),
    #  appraisal form
    url('appraisal/', form_views.Appraisal.as_view(), name='Appraisal_form'),
    # cpda reimbursement form
    url('cpdareim/', form_views.CPDAReimbursement.as_view(),
        name='CPDAReimbursement_form'),
    #  leave form
    url('leave/', form_views.Leave.as_view(), name='Leave_form'),
    url('formManagement/', form_views.FormManagement.as_view(), name='formManagement'),
    url('tracking/', form_views.TrackProgress.as_view(), name='tracking'),
    url('formFetch/', form_views.FormFetch.as_view(), name='fetch_form'),
    #  create for GetForms
    url('getForms/', form_views.GetFormHistory.as_view(), name='getForms'),
    url('leaveBalance/', form_views.CheckLeaveBalance.as_view(), name='leaveBalance'),
    url('getDesignations/', form_views.DropDown.as_view(), name="designations"),
    url('getOutbox/', form_views.GetOutbox.as_view(), name='outbox'),
    url('getArchive/', form_views.ViewArchived.as_view(), name='archive'),
    url('getuserbyid/', form_views.UserById.as_view(), name='userById'),
    # url(r'^$', views.service_book, name='hr2'),
    # url(r'^hradmin/$', views.hr_admin, name='hradmin'),
    # url(r'^edit/(?P<id>\d+)/$', views.edit_employee_details,
    #     name='editEmployeeDetails'),
    # url(r'^viewdetails/(?P<id>\d+)/$',
    #     views.view_employee_details, name='viewEmployeeDetails'),
    # url(r'^editServiceBook/(?P<id>\d+)/$',
    #     views.edit_employee_servicebook, name='editServiceBook'),
    # url(r'^administrativeProfile/$', views.administrative_profile,
    #     name='administrativeProfile'),
    # url(r'^addnew/$', views.add_new_user, name='addnew'),
]
