from rest_framework import serializers
from .models import OrderTask, Files


class FilesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Files
        fields = ['id', 'name', 'size', 'path', 'is_public', 'create_date']
        read_only_fields = ['id', 'create_date']


class OrderTaskCreateSerializer(serializers.ModelSerializer):
    files = FilesSerializer(many=True, required=False)

    class Meta:
        model = OrderTask
        fields = [
            'id', 'owner', 'name', 'description', 'discipline', 'type',
            'city', 'university', 'faculty', 'direction', 'level', 'tutor',
            'price', 'deadline', 'status', 'executor', 'views',
            'publish_date', 'updated_at', 'files'
        ]
        read_only_fields = ['id', 'status', 'executor', 'views', 'publish_date', 'updated_at']

    @staticmethod
    def get_education(obj):
        return {
            'city': obj.city,
            'university': obj.university,
            'faculty': obj.faculty,
            'direction': obj.direction,
            'level': obj.level
        }


class ShortInfoOrderTaskSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()

    class Meta:
        model = OrderTask
        fields = ['id', 'owner', 'name', 'discipline', 'type', 'price', 'status', 'views', 'author', 'deadline']

    @staticmethod
    def get_author(obj):
        return obj.owner.name if obj.owner else None
