from django.shortcuts import render
from django.http import HttpResponse,JsonResponse
# Create your views here.


def counselling_cell(request):
    return render(request, "counselling_cell/counselling.html")


    
#hello