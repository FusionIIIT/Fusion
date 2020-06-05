from django.forms import ModelForm, Textarea, TextInput, DateInput, NumberInput
from .models import Estate, Work, Inventory


class EstateForm(ModelForm):
    class Meta:
        model = Estate
        fields = '__all__'
        widgets = {
            'name': TextInput(attrs={
                'placeholder': 'Enter name of estate'
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


class WorkForm(ModelForm):
    class Meta:
        model = Work
        fields = '__all__'
        widgets = {
            'name': TextInput(attrs={
                'placeholder': 'Enter name of work'
            }),
            'contractorName': TextInput(attrs={
                'placeholder': 'Enter name of contractor'
            }),
            'dateIssued': DateInput(attrs={
                'type': 'date'
            }),
            'dateStarted': DateInput(attrs={
                'type': 'date'
            }),
            'dateCompleted': DateInput(attrs={
                'type': 'date'
            }),
            'costEstimated': NumberInput(attrs={
                'placeholder': 'Enter estimated construction cost'
            }),
            'costActual': NumberInput(attrs={
                'placeholder': 'Enter actual construction cost'
            }),
            'remarks': Textarea(attrs={
                'placeholder': 'Enter remarks'
            }),
        }
        labels = {
            'name': 'Name of work',
            'workType': 'Type of Work',
            'estate': 'Estate',
            'contractorName': 'Name of contractor',
            'dateIssued': 'Date Issued',
            'dateStarted': 'Date Started',
            'dateCompleted': 'Date Completed',
            'costEstimated': 'Estimated cost',
            'costActual': 'Actual cost',
            'remarks': 'Remarks',
        }
