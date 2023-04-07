import datetime

from django import forms
from django.forms import ModelForm

from applications.visitor_hostel.models import *

#class booking_request(forms.Form):
CHOICES = (('A', 'A',), ('B', 'B',), ('C', 'C',), ('D', 'D',))

class ViewBooking(forms.Form):
        date_from = forms.DateField(initial=datetime.date.today)
        date_to = forms.DateField(initial=datetime.date.today)


class RoomAvailability(forms.Form):
        date_from = forms.DateField(initial=datetime.date.today)
        date_to = forms.DateField(initial=datetime.date.today)


# class InventoryForm(forms.Form):
#         # class Meta:
#         #     model = Inventory
#         #     fields = ["item_name", "quantity"]
#         item_name = forms.CharField(max_length=20)
#         quantity = forms.IntegerField(min_value=0)
#         consumable = forms.BooleanField(initial=False)
#         # checkbox = ["consumable"]


class Room_booking(forms.Form):
        name = forms.CharField(max_length=100)
        mob = forms.CharField(max_length=12)
        email = forms.CharField(max_length=40)
        address = forms.CharField(max_length=200)
        country = forms.CharField(max_length=25)
        category = forms.ChoiceField(widget=forms.RadioSelect, choices=CHOICES)
        total_persons = forms.IntegerField()
        purpose = forms.CharField(widget=forms.Textarea)
        date_from = forms.DateField(initial=datetime.date.today)
        date_to = forms.DateField(initial=datetime.date.today)
