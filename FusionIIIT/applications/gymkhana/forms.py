from django import forms  
from .models import Event_info 
class EventForm(forms.ModelForm):  
    class Meta:  
        model = Event_info 
        fields = "__all__"  