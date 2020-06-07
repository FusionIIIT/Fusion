from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .forms import BuildingForm, WorkForm, InventoryTypeForm
from .models import Building, Work, SubWork, Inventory, InventoryType


@login_required(login_url='/accounts/login/')
def estate(request):

    buildings = Building.objects.all()

    context = {
        'title': "Estate Module",
        'buildings': Building.objects.all(),
        # 'buildings': {
        #     'All': buildings,
        #     'Complete': buildings.exclude(dateConstructionCompleted=None),
        #     'Incomplete': buildings.filter(dateConstructionCompleted=None)
        # },
        'WORK_CHOICES': Work.WORK_CHOICES,
        'works': Work.objects.all(),
        'inventoryTypes': InventoryType.objects.all(),
        'buildingForm': BuildingForm(),
        'workForm': WorkForm(),
        'inventoryTypeForm': InventoryTypeForm(),
    }

    return render(request, "estate_module/home.html", context)


@require_POST
def newBuilding(request):

    newBuildingForm = BuildingForm(request.POST)

    if newBuildingForm.is_valid():
        new_Building = newBuildingForm.save()
        messages.success(
            request, f'New Building Created: { new_Building.name }')
        return redirect('estate_module_home')

    for label, errors in newBuildingForm.errors.items():
        for error in errors:
            messages.error(request, f'{ label }: { error }')
    return redirect('estate_module_home')


@require_POST
def editBuilding(request, building_id):

    building = Building.objects.get(pk=building_id)

    editBuildingForm = BuildingForm(request.POST, instance=building)

    if editBuildingForm.is_valid():
        editedBuilding = editBuildingForm.save()
        messages.success(request, f'Building Updated: { editedBuilding.name }')
        return redirect('estate_module_home')

    for label, errors in editBuildingForm.errors.items():
        for error in errors:
            messages.error(request, f'{ label }: { error }')
    return redirect('estate_module_home')


@require_POST
def deleteBuilding(request, building_id):

    building = Building.objects.get(pk=building_id)
    building_name = building.name
    building.delete()
    messages.success(request, f'Building Deleted: { building_name }')
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
