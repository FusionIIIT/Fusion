from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .forms import BuildingForm, WorkForm, SubWorkForm, InventoryTypeForm, InventoryConsumableForm, InventoryNonConsumableForm
from .models import Building, Work, SubWork, InventoryType, InventoryConsumable, InventoryNonConsumable
from ..globals.models import ExtraInfo, User, HoldsDesignation

@login_required(login_url='/accounts/login/')
def estate(request):
    current_user = get_object_or_404(User, username=request.user.username)
    extraInfo = ExtraInfo.objects.get(user=current_user)
    if(extraInfo.user_type=="student"):
        return HttpResponseRedirect('/')
    
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
        'All': InventoryConsumable.objects.all(),
        'form': InventoryConsumableForm(),
        'template_dir': 'estate_module/Inventory/Consumable',
    }

    inventory_non_consumable_data = {
        'All': InventoryNonConsumable.objects.all(),
        'form': InventoryNonConsumableForm(),
        'template_dir': 'estate_module/Inventory/NonConsumable',
    }

    inventory_data = {
        'consumable': inventory_consumable_data,
        'non_consumable': inventory_non_consumable_data,
    }

    subWork_data = {
        'All': SubWork.objects.all(),
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
    new_building_form = BuildingForm(request.POST)
    if new_building_form.is_valid():
        new_building = new_building_form.save()
        messages.success(
            request, f'New Building Created: { new_building.name }')
        return redirect('estate_module_home')

    for label, errors in new_building_form.errors.items():
        for error in errors:
            messages.error(request, f'{ label }: { error }')
    return redirect('estate_module_home')


@require_POST
def editBuilding(request, building_id):

    building = Building.objects.get(pk=building_id)

    edit_building_form = BuildingForm(request.POST, instance=building)
    print(">>>>>",edit_building_form)
    if edit_building_form.is_valid():
        edited_building = edit_building_form.save()
        messages.success(request, f'Building Updated: { edited_building.name }')
        return redirect('estate_module_home')

    for label, errors in edit_building_form.errors.items():
        for error in errors:
            messages.error(request, f'{ label }: { error }')
    return redirect('estate_module_home')


@require_POST
def deleteBuilding(request, building_id):

    building = Building.objects.get(pk=building_id)
    print(">>>>>>",building)
    building_name = building.name
    # print(">>>>>>",building_name)
    building.delete()
    messages.success(request, f'Building Deleted: { building_name }')
    return redirect('estate_module_home')


@require_POST
def newWork(request):

    new_work_form = WorkForm(request.POST)

    if new_work_form.is_valid():
        new_work = new_work_form.save()
        messages.success(
            request, f'New { new_work.get_workType_display() } Work Created: { new_work.name }')
        return redirect('estate_module_home')

    for label, errors in new_work_form.errors.items():
        for error in errors:
            messages.error(request, f'{ label }: { error }')
    return redirect('estate_module_home')


@require_POST
def editWork(request, work_id):

    work = Work.objects.get(pk=work_id)

    edit_work_form = WorkForm(request.POST, instance=work)

    if edit_work_form.is_valid():
        edited_work = edit_work_form.save()
        messages.success(
            request, f'Updated { edited_work.get_workType_display() } Work: { edited_work.name }')
        return redirect('estate_module_home')

    for label, errors in edit_work_form.errors.items():
        for error in errors:
            messages.error(request, f'{ label }: { error }')
    return redirect('estate_module_home')


@require_POST
def deleteWork(request, work_id):

    work = Work.objects.get(pk=work_id)
    work_name = work.name
    work_type = work.get_workType_display()
    work.delete()

    messages.success(request, f'{ work_type } Work Deleted: { work_name }')
    return redirect('estate_module_home')


@require_POST
def newSubWork(request):

    new_sub_work_form = SubWorkForm(request.POST)

    if new_sub_work_form.is_valid():
        new_sub_work = new_sub_work_form.save()
        messages.success(
            request, f'New SubWork Created: { new_sub_work.name }')
        return redirect('estate_module_home')

    for label, errors in new_sub_work_form.errors.items():
        for error in errors:
            messages.error(request, f'{ label }: { error }')
    return redirect('estate_module_home')


@require_POST
def editSubWork(request, subWork_id):

    sub_work = SubWork.objects.get(pk=subWork_id)

    edit_sub_work_form = SubWorkForm(request.POST, instance=sub_work)

    if edit_sub_work_form.is_valid():
        edited_sub_work = edit_sub_work_form.save()
        messages.success(request, f'SubWork Updated: { edited_sub_work.name }')
        return redirect('estate_module_home')

    for label, errors in edit_sub_work_form.errors.items():
        for error in errors:
            messages.error(request, f'{ label }: { error }')
    return redirect('estate_module_home')


@require_POST
def deleteSubWork(request, subWork_id):

    sub_work = SubWork.objects.get(pk=subWork_id)
    sub_work_name = sub_work.name
    sub_work.delete()
    messages.success(request, f'SubWork Deleted: { sub_work_name }')
    return redirect('estate_module_home')


@require_POST
def newInventoryType(request):

    new_inventory_type_form = InventoryTypeForm(request.POST)

    if new_inventory_type_form.is_valid():
        new_inventory_type = new_inventory_type_form.save()
        messages.success(
            request, f'New Inventory Type Created: { new_inventory_type.name }')
        return redirect('estate_module_home')

    for label, errors in new_inventory_type_form.errors.items():
        for error in errors:
            messages.error(request, f'{ label }: { error }')
    return redirect('estate_module_home')


@require_POST
def editInventoryType(request, inventoryType_id):

    inventory_type = InventoryType.objects.get(pk=inventoryType_id)

    edit_inventory_type_form = InventoryTypeForm(
        request.POST, instance=inventory_type)

    if edit_inventory_type_form.is_valid():
        edited_inventory_type = edit_inventory_type_form.save()
        messages.success(
            request, f'Inventory Type Updated: { edited_inventory_type.name }')
        return redirect('estate_module_home')

    for label, errors in edit_inventory_type_form.errors.items():
        for error in errors:
            messages.error(request, f'{ label }: { error }')
    return redirect('estate_module_home')


@require_POST
def deleteInventoryType(request, inventoryType_id):

    inventory_type = InventoryType.objects.get(pk=inventoryType_id)
    inventory_type_name = inventory_type.name
    inventory_type.delete()
    messages.success(
        request, f'Inventory Type Deleted: { inventory_type_name }')
    return redirect('estate_module_home')


@require_POST
def newInventoryConsumable(request):

    new_inventory_consumable_form = InventoryConsumableForm(request.POST)

    if new_inventory_consumable_form.is_valid():
        new_inventory_consumable = new_inventory_consumable_form.save()
        messages.success(
            request, f'New Consumable Inventory Created: { new_inventory_consumable }')
        return redirect('estate_module_home')

    for label, errors in new_inventory_consumable_form.errors.items():
        for error in errors:
            messages.error(request, f'{ label }: { error }')
    return redirect('estate_module_home')


@require_POST
def editInventoryConsumable(request, inventory_consumable_id):

    inventory_consumable = InventoryConsumable.objects.get(
        pk=inventory_consumable_id)

    edit_inventory_consumable_form = InventoryConsumableForm(
        request.POST, instance=inventory_consumable)

    if edit_inventory_consumable_form.is_valid():
        edited_inventory_consumable = edit_inventory_consumable_form.save()
        messages.success(
            request, f'Consumable Inventory Updated: { edited_inventory_consumable }')
        return redirect('estate_module_home')

    for label, errors in edit_inventory_consumable_form.errors.items():
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

    new_inventory_non_consumable_form = InventoryNonConsumableForm(request.POST)

    if new_inventory_non_consumable_form.is_valid():
        new_inventory_non_consumable = new_inventory_non_consumable_form.save()
        messages.success(
            request, f'New Non-Consumable Inventory Created: { new_inventory_non_consumable }')
        return redirect('estate_module_home')

    for label, errors in new_inventory_non_consumable_form.errors.items():
        for error in errors:
            messages.error(request, f'{ label }: { error }')
    return redirect('estate_module_home')


@require_POST
def editInventoryNonConsumable(request, inventory_non_consumable_id):

    inventory_non_consumable = InventoryNonConsumable.objects.get(
        pk=inventory_non_consumable_id)

    edit_inventory_non_consumable_form = InventoryNonConsumableForm(
        request.POST, instance=inventory_non_consumable)

    if edit_inventory_non_consumable_form.is_valid():
        edited_inventory_non_consumable = edit_inventory_non_consumable_form.save()
        messages.success(
            request, f'Non-Consumable Inventory Updated: { edited_inventory_non_consumable }')
        return redirect('estate_module_home')

    for label, errors in edit_inventory_non_consumable_form.errors.items():
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

# @login_required
# def verifyBuilding(request,building_id):
#     try:   
#         print(">>>>>>>>>>",building_id)
#         building = Building.objects.get(pk=building_id)
#         building.verified=True
#         building.save()
#     except Exception as e:
#         messages.error(request,e)
#     return redirect('estate_module_home')


