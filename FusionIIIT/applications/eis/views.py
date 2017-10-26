from django.shortcuts import render


def profile(request):
    context = {}

    return render(request, "eisModulenew/profile.html", context)
