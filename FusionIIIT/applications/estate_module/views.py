from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required(login_url='/accounts/login/')
def estate(request):

    return render(request, "estate/home.html")
