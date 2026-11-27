from django.conf.urls import url, include

# academic_procedures' own pages were replaced by the React app; only its API is served.
urlpatterns = [
    url(r'^api/', include('applications.academic_procedures.api.urls')),
]
