from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .forms import FacultyCPDAForm

@login_required(login_url='/accounts/login')
def establishment(request):

    form = FacultyCPDAForm(request.POST)
    response = render(request, 'establishment/establishment.html', {'form': form})
    return response
