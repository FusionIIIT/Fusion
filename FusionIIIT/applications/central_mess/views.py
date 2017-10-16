from django.shortcuts import render


def mess(request):
    context = {}

    return render(request, "messModule/mess.html", context)
