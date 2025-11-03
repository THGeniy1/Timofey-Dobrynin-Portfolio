from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from payments.models import Wallet
from .models import *


class RegistrationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(max_length=128, min_length=4, write_only=True)
    name = serializers.CharField(write_only=True, required=False)
    gender = serializers.CharField(write_only=True, required=False)
    description = serializers.CharField(write_only=True, required=False)

    def validate(self, attrs):
        email = attrs.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError({'email': 'Пользователь с таким email уже зарегистрирован.'})
        return attrs

    def create(self, validated_data):
        user_data = {key: validated_data[key] for key in ['email', 'password']}
        user = CustomUser.objects.create_user(**user_data)

        client_data = {key: validated_data[key] for key in ['gender', 'description'] if key in validated_data}
        Client.objects.create(user=user, **client_data)
    
        Wallet.objects.create(user=user)

        return user

    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'name', 'gender', 'description']


class CookieTokenRefreshSerializer(TokenRefreshSerializer):
    refresh = None

    def validate(self, attrs):
        refresh_token = self.context['request'].COOKIES.get('refresh')

        if not refresh_token:
            raise ValidationError('No valid token found in cookie "refresh".')

        attrs['refresh'] = refresh_token
        return super().validate(attrs)
