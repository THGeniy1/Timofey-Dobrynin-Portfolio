from rest_framework import serializers
from .models import Refund, Files


class RefundCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refund
        fields = ['reason', 'contact_info']
        extra_kwargs = {
            'reason': {'required': True, 'max_length': 1000},
            'contact_info': {'required': False, 'allow_blank': True, 'max_length': 255},
        }


class FilesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Files
        fields = '__all__'
