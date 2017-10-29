from django.shortcuts import render


def healthcenter(request):
    context = {}

    return render(request, "phcModule/phc.html", context)
