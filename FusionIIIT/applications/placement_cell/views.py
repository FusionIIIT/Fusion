from django.shortcuts import render


def placement(request):
    context = {}

    return render(request, "placementModule/placement.html", context)
