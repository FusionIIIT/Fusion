from rest_framework.authtoken.models import Token
from rest_framework import serializers
from applications.filetracking.models import *

class FileSerializer(serializers.ModelSerializer):

    class Meta:
        model = File
        fields = ('__all__')


