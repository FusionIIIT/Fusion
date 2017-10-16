from django.shortcuts import render


def visitorhostel(request):
    context = {}

    return render(request, "vhModule/visitorhostel.html", context)
