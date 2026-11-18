from django.conf.urls import include, url

app_name = 'spacs'

urlpatterns = [
    url(r'^api/', include('applications.scholarships.api.urls')),
]
