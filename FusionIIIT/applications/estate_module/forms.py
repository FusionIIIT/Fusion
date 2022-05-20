from django.forms import BooleanField, CheckboxInput, ModelForm, Textarea, TextInput, DateInput, NumberInput
from .models import Building, Work, SubWork, InventoryType, InventoryConsumable, InventoryNonConsumable
import datetime

class BuildingForm(ModelForm):
    class Meta:
        model = Building
        fields = '__all__'
        widgets = {
            'name': TextInput(attrs={
                'placeholder': 'Enter name of building'
            }),
            'dateIssued': DateInput(attrs={
                'placeholder': 'Enter date',
                # 'type': 'date',
            }),
            'dateConstructionStarted': DateInput(attrs={
                'placeholder': 'Enter date',
                # 'type': 'date',
            }),
            'dateConstructionCompleted': DateInput(attrs={
                'placeholder': 'Enter date',
                # 'type': 'date',
            }),
            'dateOperational': DateInput(attrs={
                'placeholder': 'Enter date',
                # 'type': 'date',
            }),
            'area': NumberInput(attrs={
                'placeholder': 'Enter area',
                'type': 'text'
            }),
            'constructionCostEstimated': NumberInput(attrs={
                'placeholder': 'Enter estimated construction cost',
                'type': 'text'  # made type=text because semantic UI's optional form validation doesn't work on type=number
                # if this changes in the future, you may remove this type=text line
            }),
            'constructionCostActual': NumberInput(attrs={
                'placeholder': 'Enter actual construction cost',
                'type': 'text'  # made type=text because semantic UI's optional form validation doesn't work on type=number
            }),
            'numRooms': NumberInput(attrs={
                'placeholder': 'Enter number of rooms',
                'type': 'text'  # made type=text because semantic UI's optional form validation doesn't work on type=number
            }),
            'numWashrooms': NumberInput(attrs={
                'placeholder': 'Enter number of washrooms',
                'type': 'text'  # made type=text because semantic UI's optional form validation doesn't work on type=number
            }),
            'remarks': Textarea(attrs={
                'placeholder': 'Enter remarks'
            }),
            'verified': CheckboxInput({
                'placeholder':'Verified'
            }),
        }
        labels = {
            'name': 'Building name',
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
            'verified':'Verified',
        }
        
    def clean(self):
        super(BuildingForm,self).clean()

        dateIssued=(self.cleaned_data.get('dateIssued'))
        dateConstructionStarted=(self.cleaned_data.get('dateConstructionStarted'))
        dateConstructionCompleted=(self.cleaned_data.get('dateConstructionCompleted'))
        dateOperational=(self.cleaned_data.get('dateOperational'))
        
        if(dateIssued!=None and dateConstructionStarted!=None and dateIssued>dateConstructionStarted):
            self._errors['dateConstructionStarted']=self.error_class(['Construction date must be after issue date'])
        if(dateConstructionCompleted!=None and dateConstructionStarted!=None and dateConstructionStarted>=dateConstructionCompleted):
            self._errors['dateConstructionCompleted']=self.error_class(['Construction completion date must be after start date'])
        if(dateConstructionCompleted!=None and dateOperational!=None and dateConstructionStarted>=dateOperational):
            self._errors['dateOperational']=self.error_class(['Operational date must be after completion date'])

        return self.cleaned_data




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
                'placeholder': 'Enter date',
                # 'type': 'date',
            }),
            'dateStarted': DateInput(attrs={
                'placeholder': 'Enter date',
                # 'type': 'date',
            }),
            'dateCompleted': DateInput(attrs={
                'placeholder': 'Enter date',
                # 'type': 'date',
            }),
            'costEstimated': NumberInput(attrs={
                'placeholder': 'Enter estimated construction cost',
                'type': 'text'
            }),
            'costActual': NumberInput(attrs={
                'placeholder': 'Enter actual construction cost',
                'type': 'text'
            }),
            'remarks': Textarea(attrs={
                'placeholder': 'Enter remarks'
            }),
        }
        labels = {
            'name': 'Name of work',
            'workType': 'Type of Work',
            'building': 'Building',
            'contractorName': 'Name of contractor',
            'dateIssued': 'Date Issued',
            'dateStarted': 'Date Started',
            'dateCompleted': 'Date Completed',
            'costEstimated': 'Estimated cost',
            'costActual': 'Actual cost',
            'remarks': 'Remarks',
        }


class SubWorkForm(ModelForm):
    class Meta:
        model = SubWork
        fields = '__all__'
        widgets = {
            'name': TextInput(attrs={
                'placeholder': 'Enter name of work'
            }),
            'dateIssued': DateInput(attrs={
                'placeholder': 'Enter date',
                # 'type': 'date',
            }),
            'dateStarted': DateInput(attrs={
                'placeholder': 'Enter date',
                # 'type': 'date',
            }),
            'dateCompleted': DateInput(attrs={
                'placeholder': 'Enter date',
                # 'type': 'date',
            }),
            'costEstimated': NumberInput(attrs={
                'placeholder': 'Enter estimated construction cost',
                'type': 'text'
            }),
            'costActual': NumberInput(attrs={
                'placeholder': 'Enter actual construction cost',
                'type': 'text'
            }),
            'remarks': Textarea(attrs={
                'placeholder': 'Enter remarks'
            }),
        }
        labels = {
            'name': 'Name of Sub-Work',
            'work': 'Part of Work',
            'dateIssued': 'Date Issued',
            'dateStarted': 'Date Started',
            'dateCompleted': 'Date Completed',
            'costEstimated': 'Estimated cost',
            'costActual': 'Actual cost',
            'remarks': 'Remarks',
        }


class InventoryTypeForm(ModelForm):
    class Meta:
        model = InventoryType
        fields = '__all__'
        widgets = {
            'name': TextInput(attrs={
                'placeholder': 'Enter name of Inventory Type'
            }),
            'manufacturer': TextInput(attrs={
                'placeholder': 'Enter name of manufacturer'
            }),
            'model': TextInput(attrs={
                'placeholder': 'Enter model name/number'
            }),
            'rate': NumberInput(attrs={
                'placeholder': 'Enter rate (cost per unit)'
            }),
            'remarks': Textarea(attrs={
                'placeholder': 'Enter remarks'
            }),
        }
        labels = {
            'name': 'Inventory name',
            'manufacuter': 'Manufactuer name',
            'model': 'Model name',
            'rate': 'Rate',
            'remarks': 'Remarks',
        }


class InventoryConsumableForm(ModelForm):
    class Meta:
        model = InventoryConsumable
        fields = '__all__'
        widgets = {
            'quantity': NumberInput(attrs={
                'placeholder': 'Enter quantity',
                'type': 'text',
            }),
            'presentQuantity': NumberInput(attrs={
                'placeholder': 'Enter present quantity',
                'type': 'text',
            }),
            'dateOrdered': DateInput(attrs={
                'placeholder': 'Enter date',
            }),
            'dateReceived': DateInput(attrs={
                'placeholder': 'Enter date',
            }),
            'remarks': Textarea(attrs={
                'placeholder': 'Enter remarks'
            }),
        }
        labels = {
            'inventoryType': 'Inventory Type',
            'building': 'Building',
            'work': 'Work',
            'quantity': 'Quantity',
            'presentQuantity': 'Present Quantity',
            'dateOrdered': 'Date Ordered',
            'dateReceived': 'Date Received',
            'remarks': 'Remarks',
        }


class InventoryNonConsumableForm(ModelForm):
    class Meta:
        model = InventoryNonConsumable
        fields = '__all__'
        widgets = {
            'serial_no': TextInput(attrs={
                'placeholder': 'Enter Serial Number'
            }),
            'quantity': NumberInput(attrs={
                'placeholder': 'Enter quantity',
                'type': 'text',
            }),
            'dateOrdered': DateInput(attrs={
                'placeholder': 'Enter date',
            }),
            'dateReceived': DateInput(attrs={
                'placeholder': 'Enter date',
            }),
            'dateLastVerified': DateInput(attrs={
                'placeholder': 'Enter date',
            }),
            'remarks': Textarea(attrs={
                'placeholder': 'Enter remarks'
            }),
        }
        labels = {
            'inventoryType': 'Inventory Type',
            'serial_no': 'Serial Number',
            'building': 'Building',
            'work': 'Work',
            'issued_to': 'Issued to',
            'quantity': 'Quantity',
            'dateOrdered': 'Date Ordered',
            'dateReceived': 'Date Received',
            'dateLastVerified': 'Date Last Verified',
            'remarks': 'Remarks',
        }
