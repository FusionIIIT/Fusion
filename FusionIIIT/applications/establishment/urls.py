from django.urls import path, include
from . import views

app_name = 'establishment'

urlpatterns = [
    path('', views.establishment, name='establishment'),
    path('cpda/', views.cpda, name='cpda'),
    path('ltc/', views.ltc, name='ltc'),
    path('appraisal/', views.appraisal, name='appraisal'),
    path('api/', include('applications.establishment.api.urls')),
]
