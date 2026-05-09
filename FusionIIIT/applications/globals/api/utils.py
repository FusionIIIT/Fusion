from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from rest_framework import serializers


def get_and_authenticate_user(username, password):
    username = (username or '').strip()
    User = get_user_model()
    backend = ModelBackend()

    matched_user = User.objects.filter(username__iexact=username).first()
    if matched_user is not None and not matched_user.is_active:
        raise serializers.ValidationError("This account is inactive. Please contact the administrator.")

    exact_username_user = User.objects.filter(username=username).first()
    if exact_username_user is not None:
        user = backend.authenticate(
            request=None,
            username=exact_username_user.username,
            password=password,
        )
        if user is not None:
            return user
    else:
        username_matches = list(User.objects.filter(username__iexact=username)[:2])
        if len(username_matches) == 1:
            user = backend.authenticate(
                request=None,
                username=username_matches[0].username,
                password=password,
            )
            if user is not None:
                return user
        elif len(username_matches) > 1:
            raise serializers.ValidationError(
                "Multiple accounts match this username. Please enter the username with the correct letter case."
            )

    email_matches = list(User.objects.filter(email__iexact=username)[:2])
    if len(email_matches) == 1:
        matched_user = email_matches[0]
        if not matched_user.is_active:
            raise serializers.ValidationError("This account is inactive. Please contact the administrator.")
        user = backend.authenticate(
            request=None,
            username=matched_user.username,
            password=password,
        )
        if user is not None:
            return user
    elif len(email_matches) > 1:
        raise serializers.ValidationError(
            "Multiple accounts use this email address. Please sign in with your username instead."
        )

    raise serializers.ValidationError("Invalid credentials.")
