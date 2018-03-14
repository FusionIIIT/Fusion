from django.shortcuts import render


def officeOfDeanStudents(request):
    context = {}

    return render(request, "officeModule/officeOfDeanStudents/officeOfDeanStudents.html", context)


def officeOfPurchaseOfficr(request):
    return render(request, "officeModule/officeOfPurchaseOfficer/officeOfPurchaseOfficer.html", {})


def officeOfRegistrar(request):
    context = {}

    return render(request, "officeModule/officeOfRegistrar/officeOfRegistrar.html", context)


def officeOfDeanRSPC(request):
    context = {}

    return render(request, "officeModule/officeOfDeanRSPC/officeOfDeanRSPC.html", context)


def officeOfDeanPnD(request):
    context = {}

    return render(request, "officeModule/officeOfDeanPnD/officeOfDeanPnD.html", context)


def genericModule(request):
    context = {}

    return render(request, "officeModule/genericModule/genericModule.html", context)
