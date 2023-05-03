from . import models
from models import employee
from rest_framework import serializers

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = employee
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

