from django import forms

class FacultyCPDAForm(forms.Form):

    start_date = forms.DateField(label='From')
    end_date = forms.DateField(label='To')
    purpose = forms.CharField(label='Purpose', widget=forms.TextInput)
    address = forms.CharField(label='Address')
    document = forms.FileField(label='Related Document', required=False)
