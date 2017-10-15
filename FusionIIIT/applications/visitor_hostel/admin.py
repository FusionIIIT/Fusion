# from django.contrib import admin
from .models import (Visitor, Book_room, Visitor_bill, Room, Visitor_room, Meal, Inventory)


admin.site.register(Visitor)
admin.site.register(Book_room)
admin.site.register(Visitor_bill)
admin.site.register(Room)
admin.site.register(Visitor_room)
admin.site.register(Meal)
admin.site.register(Inventory)
