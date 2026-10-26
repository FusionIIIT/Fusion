from django.urls import path

from . import views_assistantship

# Reached at /spacs/api/... — the path carries /api/, which is what nginx
# proxies to Django in production.
urlpatterns = [
    path('assistantship/sheet/', views_assistantship.assistantship_sheet,
         name='assistantship_sheet'),
    path('assistantship/save/', views_assistantship.assistantship_save,
         name='assistantship_save'),
    path('assistantship/signatory/', views_assistantship.assistantship_signatory,
         name='assistantship_signatory'),
    path('assistantship/remove/', views_assistantship.assistantship_remove,
         name='assistantship_remove'),
]
