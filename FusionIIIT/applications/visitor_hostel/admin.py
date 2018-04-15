from django.contrib import admin

from .models import (VisitorDetail, BookingDetail, RoomDetail,
                     MealRecord, Bill, Inventory, InventoryBill)

admin.site.register(VisitorDetail)
admin.site.register(BookingDetail)
admin.site.register(RoomDetail)
admin.site.register(MealRecord)
admin.site.register(Bill)
admin.site.register(Inventory)
admin.site.register(InventoryBill)
