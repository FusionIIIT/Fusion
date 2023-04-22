from applications.hr2.models import models, Employee, EmpConfidentialDetails, EmpDependents, WorkAssignemnt, EmpAppraisalForm, ForeignService
from rest_framework import serializers

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ( 'extra_info' ,
                    'father_name' , 
                    'mother_name' , 
                    'religion', 
                    'category', 
                    'cast' , 
                    'home_district', 
                    'date_of_joining', 
                    'designation', 
                    'blood_group'
        )

class EmpConfidentialDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmpConfidentialDetails
        fields=('__all__')

class EmpDependentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmpDependents
        fields=('__all__')

class ForeignServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForeignService
        fields=('__all__')

class EmpAppraisalFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmpAppraisalForm
        fields=('__all__')

class WorkAssignemntSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkAssignemnt
        fields=('__all__')

