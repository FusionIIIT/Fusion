from django.contrib import admin
from .models import Building, Work, SubWork, InventoryType, InventoryConsumable, InventoryNonConsumable

# Register your models here.

admin.site.register(Building)
admin.site.register(Work)
admin.site.register(SubWork)
admin.site.register(InventoryType)
admin.site.register(InventoryConsumable)
admin.site.register(InventoryNonConsumable)
