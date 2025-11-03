from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import Notification, FailureNotification


class NotificationSerializer(serializers.ModelSerializer):
    target_object = serializers.SerializerMethodField()
    content_type = serializers.SlugRelatedField(
        queryset=ContentType.objects.all(),
        slug_field='model'
    )

    class Meta:
        model = Notification
        fields = [
            'id',
            'user',
            'message',
            'content',
            'content_type',
            'object_id',
            'target_object',
            'is_read',
            'auto_read',
            'created_at'
        ]
        read_only_fields = ['created_at']

    @staticmethod
    def get_target_object(obj):
        if obj.target_object is None:
            return None

        return {
            'id': obj.object_id,
            'repr': str(obj.target_object),
            'model': obj.content_type.model
        }


class FailureNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FailureNotification
        fields = [
            'id',
            'user',
            'message',
            'content',
            'failure_message',
            'is_read',
            'auto_read',
            'created_at'
        ]
        read_only_fields = ['created_at']