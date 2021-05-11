from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework import serializers
from applications.gymkhana.models import Club_info

class ClubInfoSerializer(serializers.ModelSerializer):

    class Meta:
        model=Club_info
        fields=('__all__')


class EmptySerializer(serializers.Serializer):
    pass
