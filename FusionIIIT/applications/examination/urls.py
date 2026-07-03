from django.urls import include, path

app_name = 'examination'

urlpatterns = [
    path('api/', include('applications.examination.api.urls')),
]
