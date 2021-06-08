import datetime
from django import forms
from .models import *


class IncomeForm(forms.ModelForm):
	class Meta:
		model = Income
		fields = ['source', 'amount', 'date_added', 'granted_by', 'receipt']