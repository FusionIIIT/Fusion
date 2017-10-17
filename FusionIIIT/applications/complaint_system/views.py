from django.shortcuts import render


def complaint(request):
    context = {}

    return render(request, "complaintModule/complaint.html", context)
