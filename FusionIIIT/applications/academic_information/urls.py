from django.conf.urls import url, include

app_name = 'academic_information'

# academic_information's own pages were replaced by the React app; only its API is served.
urlpatterns = [
    url(r'^api/', include('applications.academic_information.api.urls')),
]
