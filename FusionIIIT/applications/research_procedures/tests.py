from django.test import TestCase
from django.shortcuts import render
from django.http import HttpResponse
from django.http   import JsonResponse
import json
from applications.research_procedures.models import  *
# Create your tests here .
def testfun(request):
    # received_json_data=json.loads(request.body)
    # print(received_json_data['name'])
    data = {}
   
    return  JsonResponse(list(data),safe=False)

 