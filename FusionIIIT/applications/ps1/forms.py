from django import forms 
from applications.ps1.models import StockEntry


class stockforms(forms.ModelForm):
	class Meta:
		model=StockEntry
		fields="__all__" 