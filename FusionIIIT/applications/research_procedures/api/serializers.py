from rest_framework.serializers import ModelSerializer
<<<<<<< HEAD
from rest_framework import serializers

=======
>>>>>>> upstream/rspc
from applications.research_procedures.models import *

# Create a Serializer for Model Patent
class ProjectSerializer(ModelSerializer):
<<<<<<< HEAD
    class Meta:
        # model = projects
        fields = '__all__'

class Project_serializer(serializers.ModelSerializer):
    class Meta:
        model = projects
        fields = '__all__'

    def create(self, validated_data):
        return projects.objects.create(**validated_data)
    
class financial_outlay_serializer(serializers.ModelSerializer):
    class Meta:
        model = financial_outlay
        fields = '__all__'

    def create(self, validated_data):
        return financial_outlay.objects.create(**validated_data)

class category_serializer(serializers.ModelSerializer):
    class Meta:
        model = category
        fields = '__all__'

    def create(self, validated_data):
        return category.objects.create(**validated_data)

class staff_allocations_serializer(serializers.ModelSerializer):
    class Meta:
        model = staff_allocations
        fields = '__all__'

    def create(self, validated_data):
        return staff_allocations.objects.create(**validated_data)

class requests_serializer(serializers.ModelSerializer):
    class Meta:
        model = requests
        fields = '__all__'

    def create(self, validated_data):
        return requests.objects.create(**validated_data)
    
=======
    class Meta:
        model = projects
        fields = '__all__'

class PatentSerializer(ModelSerializer):
    class Meta:
        # model = projects
        fields = '__all__'
>>>>>>> upstream/rspc
