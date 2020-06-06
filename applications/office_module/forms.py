from django import forms

from .models import *


class Requisitionform(forms.ModelForm):
	class Meta:
		model=Requisitions
		fields=['title','department','building','description']
