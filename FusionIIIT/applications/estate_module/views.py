from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .forms import BuildingForm, WorkForm, SubWorkForm, InventoryTypeForm, InventoryConsumableForm, InventoryNonConsumableForm
from .models import Building, Work, SubWork, InventoryType, InventoryConsumable, InventoryNonConsumable


@login_required(login_url='/accounts/login/')
def estate(request):

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
    workForm = WorkForm()

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

    inventoryType_tabs = {
        'All': InventoryType.objects.all()
    }

    inventoryType_data = {
        'tabs': inventoryType_tabs,
        'form': InventoryTypeForm(),
        'template_dir': 'estate_module/InventoryType'
    }

    menuitems = {
        'Building': building_data,
        'Maintenance': maintenance_data,
        'Construction': construction_data,
        'Inventory List': inventoryType_data,
    }

    inventory_consumable_data = {
        'all': InventoryConsumable.objects.all(),
        'form': InventoryConsumableForm(),
        'template_dir': 'estate_module/Inventory/Consumable'
    }

    inventory_non_consumable_data = {
        'all': InventoryNonConsumable.objects.all(),
        'form': InventoryNonConsumableForm(),
        'template_dir': 'estate_module/Inventory/NonConsumable'
    }

    inventory_data = {
        'consumable': inventory_consumable_data,
        'non_consumable': inventory_non_consumable_data,
    }

    subWork_data = {
        'all': SubWork.objects.all(),
        'form': SubWorkForm(),
        'template_dir': 'estate_module/SubWork'
    }

    context = {
        'title': "Estate Module",
        'menuitems': menuitems,
        'inventory_data': inventory_data,
        'subWork_data': subWork_data,
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


@require_POST
def newSubWork(request):

    newSubWorkForm = SubWorkForm(request.POST)

    if newSubWorkForm.is_valid():
        new_SubWork = newSubWorkForm.save()
        messages.success(
            request, f'New SubWork Created: { new_SubWork.name }')
        return redirect('estate_module_home')

    for label, errors in newSubWorkForm.errors.items():
        for error in errors:
            messages.error(request, f'{ label }: { error }')
    return redirect('estate_module_home')


@require_POST
def editSubWork(request, subWork_id):

    subWork = SubWork.objects.get(pk=subWork_id)

    editSubWorkForm = SubWorkForm(request.POST, instance=subWork)

    if editSubWorkForm.is_valid():
        editedSubWork = editSubWorkForm.save()
        messages.success(request, f'SubWork Updated: { editedSubWork.name }')
        return redirect('estate_module_home')

    for label, errors in editSubWorkForm.errors.items():
        for error in errors:
            messages.error(request, f'{ label }: { error }')
    return redirect('estate_module_home')


@require_POST
def deleteSubWork(request, subWork_id):

    subWork = SubWork.objects.get(pk=subWork_id)
    subWork_name = subWork.name
    subWork.delete()
    messages.success(request, f'SubWork Deleted: { subWork_name }')
    return redirect('estate_module_home')


@require_POST
def newInventoryType(request):

    newInventoryTypeForm = InventoryTypeForm(request.POST)

    if newInventoryTypeForm.is_valid():
        new_InventoryType = newInventoryTypeForm.save()
        messages.success(
            request, f'New Inventory Type Created: { new_InventoryType.name }')
        return redirect('estate_module_home')

    for label, errors in newInventoryTypeForm.errors.items():
        for error in errors:
            messages.error(request, f'{ label }: { error }')
    return redirect('estate_module_home')


@require_POST
def editInventoryType(request, inventoryType_id):

    inventoryType = InventoryType.objects.get(pk=inventoryType_id)

    editInventoryTypeForm = InventoryTypeForm(
        request.POST, instance=inventoryType)

    if editInventoryTypeForm.is_valid():
        editedInventoryType = editInventoryTypeForm.save()
        messages.success(
            request, f'Inventory Type Updated: { editedInventoryType.name }')
        return redirect('estate_module_home')

    for label, errors in editInventoryTypeForm.errors.items():
        for error in errors:
            messages.error(request, f'{ label }: { error }')
    return redirect('estate_module_home')


@require_POST
def deleteInventoryType(request, inventoryType_id):

    inventoryType = InventoryType.objects.get(pk=inventoryType_id)
    inventoryType_name = inventoryType.name
    inventoryType.delete()
    messages.success(
        request, f'Inventory Type Deleted: { inventoryType_name }')
    return redirect('estate_module_home')


@require_POST
def newInventoryConsumable(request):

    newInventoryConsumableForm = InventoryConsumableForm(request.POST)

    if newInventoryConsumableForm.is_valid():
        new_InventoryConsumable = newInventoryConsumableForm.save()
        messages.success(
            request, f'New Consumable Inventory Created: { new_InventoryConsumable }')
        return redirect('estate_module_home')

    for label, errors in newInventoryConsumableForm.errors.items():
        for error in errors:
            messages.error(request, f'{ label }: { error }')
    return redirect('estate_module_home')


@require_POST
def editInventoryConsumable(request, inventory_consumable_id):

    inventory_consumable = InventoryConsumable.objects.get(
        pk=inventory_consumable_id)

    editInventoryConsumableForm = InventoryConsumableForm(
        request.POST, instance=inventory_consumable)

    if editInventoryConsumableForm.is_valid():
        editedInventoryConsumable = editInventoryConsumableForm.save()
        messages.success(
            request, f'Consumable Inventory Updated: { editedInventoryConsumable }')
        return redirect('estate_module_home')

    for label, errors in editInventoryConsumableForm.errors.items():
        for error in errors:
            messages.error(request, f'{ label }: { error }')
    return redirect('estate_module_home')


@require_POST
def deleteInventoryConsumable(request, inventory_consumable_id):

    inventory_consumable = InventoryConsumable.objects.get(
        pk=inventory_consumable_id)
    inventory_consumable_name = inventory_consumable.inventoryType
    inventory_consumable.delete()
    messages.success(
        request, f'Consumable Inventory Deleted: { inventory_consumable_name }')
    return redirect('estate_module_home')


@require_POST
def newInventoryNonConsumable(request):

    newInventoryNonConsumableForm = InventoryNonConsumableForm(request.POST)

    if newInventoryNonConsumableForm.is_valid():
        new_InventoryNonConsumable = newInventoryNonConsumableForm.save()
        messages.success(
            request, f'New Non-Consumable Inventory Created: { new_InventoryNonConsumable }')
        return redirect('estate_module_home')

    for label, errors in newInventoryNonConsumableForm.errors.items():
        for error in errors:
            messages.error(request, f'{ label }: { error }')
    return redirect('estate_module_home')


@require_POST
def editInventoryNonConsumable(request, inventory_non_consumable_id):

    inventory_non_consumable = InventoryNonConsumable.objects.get(
        pk=inventory_non_consumable_id)

    editInventoryNonConsumableForm = InventoryNonConsumableForm(
        request.POST, instance=inventory_non_consumable)

    if editInventoryNonConsumableForm.is_valid():
        editedInventoryNonConsumable = editInventoryNonConsumableForm.save()
        messages.success(
            request, f'Non-Consumable Inventory Updated: { editedInventoryNonConsumable }')
        return redirect('estate_module_home')

    for label, errors in editInventoryNonConsumableForm.errors.items():
        for error in errors:
            messages.error(request, f'{ label }: { error }')
    return redirect('estate_module_home')


@require_POST
def deleteInventoryNonConsumable(request, inventory_non_consumable_id):

    inventory_non_consumable = InventoryNonConsumable.objects.get(
        pk=inventory_non_consumable_id)
    inventory_non_consumable_name = inventory_non_consumable.inventoryType
    inventory_non_consumable.delete()
    messages.success(
        request, f'Non-Consumable Inventory Deleted: { inventory_non_consumable_name }')
    return redirect('estate_module_home')
