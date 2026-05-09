from django.urls import path, include

app_name = 'hr2'

urlpatterns = [
    path('api/', include('applications.hr2.api.urls')),
]
