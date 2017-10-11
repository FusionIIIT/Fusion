from django import forms
from django.contrib.admin.widgets import AdminDateWidget
from django.core.exceptions import ValidationError


class AddDocuments(forms.Form):
    doc=forms.FileField(required=True)
    description=forms.CharField(label='Description', max_length=100,widget=forms.TextInput(attrs={'placeholder':'Type something here'}))
    def __init__(self, *args, **kwargs):
        super(AddDocuments, self).__init__(*args, **kwargs)
        self.fields['doc'].widget.attrs.update({'accept': '.pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx'})
