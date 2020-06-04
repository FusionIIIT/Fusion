from django.contrib import admin

from .models import (Bill, BookingDetail, Inventory, InventoryBill, MealRecord,
                     RoomDetail, VisitorDetail)

admin.site.register(VisitorDetail)
admin.site.register(BookingDetail)
admin.site.register(RoomDetail)
admin.site.register(MealRecord)
admin.site.register(Bill)
admin.site.register(Inventory)
admin.site.register(InventoryBill)
