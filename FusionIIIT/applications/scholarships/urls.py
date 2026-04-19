from django.http import JsonResponse
from django.urls import path


def spacs_root(_request):
    return JsonResponse({
        'message': 'SPACS backend is active. Use /scholarships/api/ endpoints.'
    })


urlpatterns = [
    path('', spacs_root, name='spacs_root'),
]
