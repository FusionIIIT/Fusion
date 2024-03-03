from rest_framework.serializers import ModelSerializer
from applications.research_procedures.models import *

# Create a Serializer for Model Patent
class PatentSerializer(ModelSerializer):
    class Meta:
        model = projects
        fields = '__all__'