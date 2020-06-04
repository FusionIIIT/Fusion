from django.forms import ModelForm, Textarea, TextInput, DateInput, NumberInput
from .models import Estate


class EstateForm(ModelForm):
    class Meta:
        model = Estate
        fields = '__all__'
        widgets = {
            'name': TextInput(attrs={
                'placeholder': 'Enter name'
            }),
            'dateIssued': DateInput(attrs={
                'type': 'date'
            }),
            'dateConstructionStarted': DateInput(attrs={
                'type': 'date'
            }),
            'dateConstructionCompleted': DateInput(attrs={
                'type': 'date'
            }),
            'dateOperational': DateInput(attrs={
                'type': 'date'
            }),
            'area': NumberInput(attrs={
                'placeholder': 'Enter area'
            }),
            'constructionCostEstimated': NumberInput(attrs={
                'placeholder': 'Enter estimated construction cost'
            }),
            'constructionCostActual': NumberInput(attrs={
                'placeholder': 'Enter actual construction cost'
            }),
            'numRooms': NumberInput(attrs={
                'placeholder': 'Enter number of rooms'
            }),
            'numWashrooms': NumberInput(attrs={
                'placeholder': 'Enter number of washrooms'
            }),
            'remarks': Textarea(attrs={
                'placeholder': 'Enter remarks'
            }),
        }
        labels = {
            'name': 'Estate name',
            'dateIssued': 'Date Issued',
            'dateConstructionStarted': 'Construction Started',
            'dateConstructionCompleted': 'Construction Completed',
            'dateOperational': 'Date Operational',
            'area': 'Area',
            'constructionCostEstimated': 'Estimated Construction Cost',
            'constructionCostActual': 'Actual Construction Cost',
            'numRooms': 'Number of Rooms',
            'numWashrooms': 'Number of Washrooms',
            'remarks': 'Remarks',

        }
# type = "text" placeholder = "Enter name" id = "name" name = "name" { % if estate.name % } value = "{{ estate.name }}"
