from django import forms
from .models import Constants

dec = 'I hereby declare that I have uploaded & updated all my achievements (including publications, visits, projects etc.) on Institute\'s website and EIS module.'

class Cpda_Form(forms.Form):
    pf_number = forms.CharField(label='PF Number', required=True)
    purpose = forms.CharField(label='Purpose', widget=forms.TextInput, required=True)
    requested_advance = forms.IntegerField(label='Advance Requested', min_value=0, required=True)
    declaration = forms.BooleanField(label=dec, required=True)

    
class Cpda_Bills_Form(forms.Form):
    app_id = forms.IntegerField(widget = forms.HiddenInput(), required=True)
    adjustment_amount = forms.IntegerField(label='Adjustment Amount', min_value=0, required=True)
    bills = forms.FileField(label='Bills')
    total_bills_amount = forms.IntegerField(label='Total Bills Amount', min_value=0, required=True)

class Cpda_Assign_Form(forms.Form):
    app_id = forms.IntegerField(widget = forms.HiddenInput(), required=True)
    status = forms.ChoiceField(choices=Constants.STATUS)
    reviewer_id = forms.CharField(label="Reviewer ID", required=False)
    reviewer_design = forms.CharField(label="Reviewer Designation", required=False)
    remarks = forms.CharField(label="Remarks")