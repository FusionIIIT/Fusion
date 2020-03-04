from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required(login_url='/accounts/login')
def establishment(request):
    response = render(request, 'establishment/establishment.html', {})
    return response
