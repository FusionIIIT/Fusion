from django.urls import path

from . import views

urlpatterns = [
    path('', views.estate, name="estate_module_home"),
    #new
    path('new/building', views.newBuilding, name="new_building"),
    path('new/work', views.newWork, name="new_work"),
    path('new/subWork', views.newSubWork, name="new_subWork"),
    path('new/inventoryType', views.newInventoryType, name="new_inventoryType"),
    path('new/inventory_consumable', views.newInventoryConsumable,
         name="new_inventory_consumable"),
    path('new/inventory_non_consumable', views.newInventoryNonConsumable,
         name="new_inventory_non_consumable"),

    #edit
    path('edit/building/<building_id>', views.editBuilding, name="edit_building"),
    path('edit/work/<work_id>', views.editWork, name="edit_work"),
    path('edit/subWork/<subWork_id>', views.editSubWork, name="edit_subWork"),
    path('edit/inventoryType/<inventoryType_id>',
         views.editInventoryType, name="edit_inventoryType"),
    path('edit/inventory_consumable/<inventory_consumable_id>',
         views.editInventoryConsumable, name="edit_inventory_consumable"),
    path('edit/inventory_non_consumable/<inventory_non_consumable_id>',
         views.editInventoryNonConsumable, name="edit_inventory_non_consumable"),

    #delete
    path('delete/building/<building_id>',
         views.deleteBuilding, name="delete_building"),
    path('delete/work/<work_id>', views.deleteWork, name="delete_work"),
    path('delete/subWork/<subWork_id>',
         views.deleteSubWork, name="delete_subWork"),
    path('delete/inventoryType/<inventoryType_id>', views.deleteInventoryType,
         name="delete_inventoryType"),
    path('delete/inventory_consumable/<inventory_consumable_id>',
         views.deleteInventoryConsumable, name="delete_inventory_consumable"),
    path('delete/inventory_non_consumable/<inventory_non_consumable_id>',
         views.deleteInventoryNonConsumable, name="delete_inventory_non_consumable"),

     #verify
     # path('verify_building/<building_id>',views.verifyBuilding,name="verify_building")
]

