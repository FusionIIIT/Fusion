from django.shortcuts import render


def officeOfDeanStudents(request):
    context = {}

    return render(request, "officeModule/officeOfDeanStudents/officeOfDeanStudents.html", context)
