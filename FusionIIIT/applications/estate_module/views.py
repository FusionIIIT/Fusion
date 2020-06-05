from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from .forms import EstateForm, WorkForm
from .models import Estate, WorkType, Work, SubWork

buildings = [
    {
        'id': 'p',
        'name': 'Core Lab Complex',
        'status': 'incomplete',
        'date_approval': '30-12-05',
        'date_start': '30-12-05',
        'amount': 9999999
    },
    {
        'id': 'q',
        'name': 'LHTC',
        'status': 'incomplete',
        'date_approval': '15-11-05',
        'date_start': '05-12-05',
        'amount': 8960099
    },
    {
        'id': 'r',
        'name': 'Central Mess',
        'status': 'occupied',
        'date_approval': '21-06-06',
        'date_start': '13-11-06',
        'amount': 8899999
    },
    {
        'id': 's',
        'name': 'Hall 4',
        'status': 'complete',
        'date_approval': '22-08-07',
        'date_start': '12-10-08',
        'date_end': '24-07-08',
        'amount': 9085990
    }
]
projects = [
    {
        'name': 'Cricket Ground',
        'status': 'complete',
        'date_approval': '22-08-07',
        'date_start': '12-10-08',
        'date_end': '18-05-09',
        'amount': 9085999,
    },
    {
        'name': 'Boundary Wall',
        'status': 'incomplete',
        'date_approval': '22-08-07',
        'date_start': '12-10-08',
        'date_end': '18-05-09',
        'amount': 9085999,
    }
]


@login_required(login_url='/accounts/login/')
def oldEstate(request):

    context = {
        'buildings': buildings,
        'projects': projects
    }

    return render(request, "estate/home.html", context)


@login_required(login_url='/accounts/login/')
def estate(request):

    context = {
        'title': "Estate Module",
        'estates': Estate.objects.all(),
        'works': Work.objects.all(),
        'WORK_CHOICES': Work.WORK_CHOICES,
        'estateForm': EstateForm(),
        'workForm': WorkForm()
    }

    return render(request, "estate_module/home.html", context)


@require_POST
def newEstate(request):

    newEstateForm = EstateForm(request.POST)

    if newEstateForm.is_valid():
        new_Estate = newEstateForm.save()
        return redirect('estate')

    return redirect('estate')


@require_POST
def editEstate(request, estate_id):

    estate = Estate.objects.get(pk=estate_id)

    editEstateForm = EstateForm(request.POST, instance=estate)

    if editEstateForm.is_valid():
        editEstateForm.save()
        return redirect('estate')

    return redirect('estate')


@require_POST
def deleteEstate(request, estate_id):

    estate = Estate.objects.get(pk=estate_id)
    estate.delete()
    return redirect('estate')


@require_POST
def newWork(request):

    newWorkForm = WorkForm(request.POST)

    if newWorkForm.is_valid():
        new_Work = newWorkForm.save()
        return redirect('estate')

    return redirect('estate')


@require_POST
def editWork(request, work_id):

    work = Work.objects.get(pk=work_id)

    editWorkForm = WorkForm(request.POST, instance=work)

    if editWorkForm.is_valid():
        editWorkForm.save()
        return redirect('estate')

    return redirect('estate')


@require_POST
def deleteWork(request, work_id):

    work = Work.objects.get(pk=work_id)
    work.delete()
    return redirect('estate')
