from django.shortcuts import render


def gymkhana(request):
    context = {}

    return render(request, "gymkhanaModule/gymkhana.html", context)
