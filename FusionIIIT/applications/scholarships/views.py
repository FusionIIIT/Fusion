from django.shortcuts import render


def spacs(request):
    context = {}

    return render(request, "scholarshipsModule/scholarships.html", context)
