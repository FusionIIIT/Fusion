from django.contrib.auth import authenticate
from rest_framework import serializers


def get_and_authenticate_user(username, password):
    user = authenticate(username=username, password=password)
    if user is None:
        raise serializers.ValidationError("Invalid credentials.")
    return user
