from django.conf.urls import url 
from . import views

urlpatterns = [
 
    url(r'employee_details/$', views.employee_details_api,name='employee_details_api'),
    url(r'emp_confidential_details/$', views.emp_confidential_details_api,name='emp_confidential_details_api'),
    url(r'emp_dependents/$', views.emp_dependents_api,name='emp_dependents_api'),
    url(r'foreign_service/$', views.foreign_service_api,name='foreign_service_api'),
    url(r'emp_appraisal_form/$', views.emp_appraisal_form_api,name='emp_appraisal_form_api'),
    url(r'work_assignment/$', views.work_assignment_api,name='work_assignment_api'),
]
 