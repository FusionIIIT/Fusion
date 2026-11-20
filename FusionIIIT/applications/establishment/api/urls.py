from django.urls import path
from . import views

urlpatterns = [
    # CPDA endpoints
    path('cpda/balance/', views.cpda_balance_api, name='api-cpda-balance'),
    path('cpda/applications/', views.cpda_applications_api, name='api-cpda-applications'),

    # LTC endpoints
    path('ltc/eligibility/', views.ltc_eligibility_api, name='api-ltc-eligibility'),
    path('ltc/applications/', views.ltc_applications_api, name='api-ltc-applications'),

    # Appraisal endpoints
    path('appraisals/', views.appraisal_list_api, name='api-appraisal-list'),
    path('appraisals/<int:pk>/', views.appraisal_detail_api, name='api-appraisal-detail'),
]
