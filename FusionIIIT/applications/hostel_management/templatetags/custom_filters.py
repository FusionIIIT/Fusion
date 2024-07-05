# templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def filter_by_type(rooms, room_type):
    return [room for room in rooms if room.room_type == room_type]

@register.filter
def occupied_seats(rooms):
    return sum(room.occupants.count() for room in rooms)

@register.filter
def vacant_seats(rooms):
    return sum(room.available_seats for room in rooms)
