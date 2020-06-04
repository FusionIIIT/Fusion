from django.contrib import admin
from .models import Estate, Work, WorkType, SubWork, Inventory, InventoryType

# Register your models here.

admin.site.register(Estate)
admin.site.register(Work)
admin.site.register(WorkType)
admin.site.register(SubWork)
admin.site.register(InventoryType)
admin.site.register(Inventory)
