from django.shortcuts import render


def phc(request):
    context = {}

    return render(request, "phcModule/phc.html", context)
