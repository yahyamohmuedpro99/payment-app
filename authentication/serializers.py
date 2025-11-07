from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import Merchant


class MerchantRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for merchant registration"""

    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = Merchant
        fields = ['email', 'password']

    def create(self, validated_data):
        """Create a new merchant"""
        merchant = Merchant.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password']
        )
        return merchant


class MerchantLoginSerializer(serializers.Serializer):
    """Serializer for merchant login"""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        """Validate and authenticate merchant"""
        email = data.get('email')
        password = data.get('password')

        if email and password:
            merchant = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password
            )

            if not merchant:
                raise serializers.ValidationError('Invalid email or password')

            if not merchant.is_active:
                raise serializers.ValidationError('Merchant account is inactive')

            data['merchant'] = merchant
        else:
            raise serializers.ValidationError('Must include "email" and "password"')

        return data


class MerchantSerializer(serializers.ModelSerializer):
    """Serializer for merchant details"""

    class Meta:
        model = Merchant
        fields = ['id', 'email', 'api_key', 'is_active', 'created_at']
        read_only_fields = ['id', 'api_key', 'created_at']
