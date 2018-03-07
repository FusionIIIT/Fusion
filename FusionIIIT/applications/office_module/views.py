from django.shortcuts import render


def officeOfDeanStudents(request):
    context = {}

    return render(request, "officeModule/officeOfDeanStudents/officeOfDeanStudents.html", context)


def officeOfPurchaseOfficer(request):
    context = {}

    return render(request, "officeModule/officeOfPurchaseOfficer/officeOfPurchaseOfficer.html", context)

def officeOfRegistrar(request):
    context = {}

    return render(request, "officeModule/officeOfRegistrar/officeOfRegistrar.html", context)


def genericModule(request):
    context = {}

    return render(request, "officeModule/genericModule/genericModule.html", context)
