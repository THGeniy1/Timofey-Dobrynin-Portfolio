from rest_framework import serializers
from .models import *


class FilesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Files
        fields = '__all__'


class ReadyTaskSerializer(serializers.ModelSerializer):
    files = FilesSerializer(many=True, read_only=True)

    class Meta:
        model = ReadyTask
        fields = [
            'id', 'owner', 'name', 'discipline', 'type', 'description',
            'city', 'university', 'faculty', 'direction', 'level',
            'tutor', 'score', 'price', 'create_date',
            'previous_version', 'status', 'views',
            'files',
        ]

    @staticmethod
    def get_education(obj):
        return {
            'city': obj.city,
            'university': obj.university,
            'faculty': obj.faculty,
            'direction': obj.direction,
            'level': obj.level
        }


class ShortInfoReadyTaskSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    
    class Meta:
        model = ReadyTask
        fields = ['id', 'owner', 'name', 'discipline', 'type', 'score', 'price', 'status', 'views', 'author']
    
    @staticmethod
    def get_author(obj):
        return obj.owner.name if obj.owner else None
