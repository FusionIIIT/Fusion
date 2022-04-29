from rest_framework.serializers import ModelSerializer
from applications.research_procedures.models import Patent

# Create a Serializer for Model Patent
class PatentSerializer(ModelSerializer):
    class Meta:
        model = Patent
        fields = '__all__'