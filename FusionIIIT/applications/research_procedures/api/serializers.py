from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from django.conf import settings
from applications.research_procedures.models import *

class budget_serializer(serializers.ModelSerializer):
    class Meta:
        model = budget
        fields = '__all__'


class project_access_serializer(serializers.ModelSerializer):
    class Meta:
        model = project_access
        fields = '__all__'

class projects_serializer(serializers.ModelSerializer):
    class Meta:
        model = projects
        fields = '__all__'
  


# class projects_serializer(serializers.ModelSerializer):
#     class Meta:
#         model = projects
#         fields = '__all__'
#     def create(self, validated_data):
#         return projects.objects.create(**validated_data)

# class requests_serializer(serializers.ModelSerializer):
#     class Meta:
#         model = requests
#         fields = '__all__'

# class requests_serializer(serializers.ModelSerializer):
#     class Meta:
#         model = requests
#         fields = '__all__'

#     def create(self, validated_data):
#         return requests.objects.create(**validated_data)
    
class expenditure_serializer(serializers.ModelSerializer):
    class Meta:
        model = expenditure
        fields = '__all__'

class staff_serializer(serializers.ModelSerializer):
    # biodata_final = serializers.SerializerMethodField()
    # biodata_waiting = serializers.SerializerMethodField()

    # def get_biodata_final(self, obj):
    #     request = self.context.get("request")
    #     return [request.build_absolute_uri(f"{settings.MEDIA_URL}{file}") for file in obj.biodata_final] if obj.biodata_final else []

    # def get_biodata_waiting(self, obj):
    #     request = self.context.get("request")
    #     return [request.build_absolute_uri(f"{settings.MEDIA_URL}{file}") for file in obj.biodata_waiting] if obj.biodata_waiting else []
    
    class Meta:
        model = staff
        fields = '__all__'

class staff_positions_serializer(serializers.ModelSerializer):
    class Meta:
        model = staff_positions
        fields = '__all__'
