from django.urls import path, include

app_name = 'database'

urlpatterns = [
    path('api/', include('applications.database_backend.api.urls')),
]