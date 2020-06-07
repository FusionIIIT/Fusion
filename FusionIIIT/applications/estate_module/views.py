from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .forms import EstateForm, WorkForm, InventoryTypeForm
from .models import Estate, WorkType, Work, SubWork, Inventory, InventoryType


@login_required(login_url='/accounts/login/')
def estate(request):

    estates = Estate.objects.all()

    context = {
        'title': "Estate Module",
        'estates': Estate.objects.all(),
        # 'estates': {
        #     'All': estates,
        #     'Complete': estates.exclude(dateConstructionCompleted=None),
        #     'Incomplete': estates.filter(dateConstructionCompleted=None)
        # },
        'WORK_CHOICES': Work.WORK_CHOICES,
        'works': Work.objects.all(),
        'inventoryTypes': InventoryType.objects.all(),
        'estateForm': EstateForm(),
        'workForm': WorkForm(),
        'inventoryTypeForm': InventoryTypeForm(),
    }

    return render(request, "estate_module/home.html", context)


@require_POST
def newEstate(request):

    newEstateForm = EstateForm(request.POST)

    if newEstateForm.is_valid():
        new_Estate = newEstateForm.save()
        messages.success(
            request, f'New Estate Created: { new_Estate.name }')
        return redirect('estate_module_home')

    for label, errors in newEstateForm.errors.items():
        for error in errors:
            messages.error(request, f'{ label }: { error }')
    return redirect('estate_module_home')


@require_POST
def editEstate(request, estate_id):

    estate = Estate.objects.get(pk=estate_id)

    editEstateForm = EstateForm(request.POST, instance=estate)

    if editEstateForm.is_valid():
        editedEstate = editEstateForm.save()
        messages.success(request, f'Estate Updated: { editedEstate.name }')
        return redirect('estate_module_home')

    for label, errors in editEstateForm.errors.items():
        for error in errors:
            messages.error(request, f'{ label }: { error }')
    return redirect('estate_module_home')


@require_POST
def deleteEstate(request, estate_id):

    estate = Estate.objects.get(pk=estate_id)
    estate_name = estate.name
    estate.delete()
    messages.success(request, f'Estate Deleted: { estate_name }')
    return redirect('estate_module_home')


@require_POST
def newWork(request):

    newWorkForm = WorkForm(request.POST)

    if newWorkForm.is_valid():
        new_Work = newWorkForm.save()
        return redirect('estate_module_home')

    return redirect('estate_module_home')


@require_POST
def editWork(request, work_id):

    work = Work.objects.get(pk=work_id)

    editWorkForm = WorkForm(request.POST, instance=work)

    if editWorkForm.is_valid():
        editedWork = editWorkForm.save()
        messages.success(
            request, f'Updated { editedWork.get_workType_display() } Work: { editedWork.name }')
        return redirect('estate_module_home')

    for label, errors in editWorkForm.errors.items():
        for error in errors:
            messages.error(request, f'{ label }: { error }')
    return redirect('estate_module_home')


@require_POST
def deleteWork(request, work_id):

    work = Work.objects.get(pk=work_id)
    work_name = work.name
    work_Type = work.get_workType_display()
    work.delete()

    messages.success(request, f'{ work_Type } Work Deleted: { work_name }')
    return redirect('estate_module_home')
