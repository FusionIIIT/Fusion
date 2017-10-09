from __future__ import unicode_literals
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse


def index(request):
    return(request,'online_cms/index.html')
