from django.shortcuts import render


def profile(request):
    context = {}

    return render(request, "eisModule/profile.html", context)
