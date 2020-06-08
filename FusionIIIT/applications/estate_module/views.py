from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .forms import BuildingForm, WorkForm, InventoryTypeForm
from .models import Building, Work, SubWork, Inventory, InventoryType


@login_required(login_url='/accounts/login/')
def estate(request):

    workForm = WorkForm()

    buildings = Building.objects.all()
    building_tabs = {
        'All': buildings,
        'Complete': buildings.exclude(dateConstructionCompleted=None),
        'Operational': buildings.exclude(dateOperational=None),
        'Incomplete': buildings.filter(dateConstructionCompleted=None),
        'On Schedule': buildings.filter(status=Building.ON_SCHEDULE),
        'Delayed': buildings.filter(status=Building.DELAYED),
    }
    building_data = {
        'tabs': building_tabs,
        'form': BuildingForm(),
        'template_dir': 'estate_module/Building',
    }

    works = Work.objects.all()

    maintenanceWorks = works.filter(workType=Work.MAINTENANCE_WORK)
    maintenance_tabs = {
        'All': maintenanceWorks,
        'Complete': maintenanceWorks.exclude(dateCompleted=None),
        'Incomplete': maintenanceWorks.filter(dateCompleted=None),
        'On Schedule': maintenanceWorks.filter(status=Building.ON_SCHEDULE),
        'Delayed': maintenanceWorks.filter(status=Building.DELAYED),
    }
    maintenance_data = {
        'tabs': maintenance_tabs,
        'form': workForm,
        'workType': Work.MAINTENANCE_WORK,
        'template_dir': 'estate_module/Work',
    }

    constructionWorks = works.filter(workType=Work.CONSTRUCTION_WORK)
    construction_tabs = {
        'All': constructionWorks,
        'Complete': constructionWorks.exclude(dateCompleted=None),
        'Incomplete': constructionWorks.filter(dateCompleted=None),
        'On Schedule': constructionWorks.filter(status=Building.ON_SCHEDULE),
        'Delayed': constructionWorks.filter(status=Building.DELAYED),
    }

    construction_data = {
        'tabs': construction_tabs,
        'form': workForm,
        'workType': Work.CONSTRUCTION_WORK,
        'template_dir': 'estate_module/Work',
    }

    menuitems = {
        'Building': building_data,
        'Maintenance': maintenance_data,
        'Construction': construction_data,
    }

    context = {
        'title': "Estate Module",
        'menuitems': menuitems,
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
        new_work = newWorkForm.save()
        messages.success(
            request, f'New { new_work.get_workType_display() } Work Created: { new_work.name }')
        return redirect('estate_module_home')

    for label, errors in newBuildingForm.errors.items():
        for error in errors:
            messages.error(request, f'{ label }: { error }')
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
