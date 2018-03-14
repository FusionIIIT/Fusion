from django.shortcuts import render


def financeModule(request):
    context = {}

    return render(request, "financeAndAccountsModule/financeAndAccountsModule.html", context)
