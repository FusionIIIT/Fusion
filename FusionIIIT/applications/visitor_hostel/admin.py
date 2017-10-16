from django.contrib import admin

from .models import (Book_room, Inventory, Meal, Room, Visitor, Visitor_bill,
                     Visitor_room)

admin.site.register(Visitor)
admin.site.register(Book_room)
admin.site.register(Visitor_bill)
admin.site.register(Room)
admin.site.register(Visitor_room)
admin.site.register(Meal)
admin.site.register(Inventory)
