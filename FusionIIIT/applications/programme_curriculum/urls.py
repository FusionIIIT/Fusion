from django.urls import path, include
from django.contrib import admin

app_name = 'programme_curriculum'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('applications.programme_curriculum.api.urls')),
]
