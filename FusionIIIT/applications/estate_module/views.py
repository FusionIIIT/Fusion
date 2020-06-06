from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .forms import EstateForm, WorkForm, InventoryTypeForm
from .models import Estate, WorkType, Work, SubWork, Inventory, InventoryType


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
        editWorkForm.save()
        return redirect('estate_module_home')

    return redirect('estate_module_home')


@require_POST
def deleteWork(request, work_id):

    work = Work.objects.get(pk=work_id)
    work.delete()
    return redirect('estate_module_home')


@require_POST
def newInventoryType(request):

    newInventoryTypeForm = InventoryTypeForm(request.POST)

    if newInventoryTypeForm.is_valid():
        new_InventoryType = newInventoryTypeForm.save()
        return redirect('estate_module_home')

    return redirect('estate_module_home')


@require_POST
def editInventoryType(request, inventoryType_id):

    inventoryType = InventoryType.objects.get(pk=inventoryType_id)

    editInventoryTypeForm = InventoryTypeForm(
        request.POST, instance=inventoryType)

    if editInventoryTypeForm.is_valid():
        editInventoryTypeForm.save()
        return redirect('estate_module_home')

    return redirect('estate_module_home')


@require_POST
def deleteInventoryType(request, inventoryType_id):

    inventoryType = InventoryType.objects.get(pk=inventoryType_id)
    inventoryType.delete()
    return redirect('estate_module_home')
