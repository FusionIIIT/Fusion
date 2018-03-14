from django.shortcuts import render


def libraryModule(request):
    context = {}

    return render(request, "libraryModule/libraryModule.html", context)
