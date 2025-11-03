from rest_framework import serializers
from .models import JsonFile


class JsonFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = JsonFile
        fields = '__all__'
