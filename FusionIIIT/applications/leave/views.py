from django.shortcuts import render


def leave(request):
    context = {}

    return render(request, "leaveModule/leave.html", context)
