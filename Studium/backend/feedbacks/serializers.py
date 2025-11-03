from rest_framework import serializers
from .models import Feedback
from users.serializers import FeedbackUserSerializer


class FeedbackSerializer(serializers.ModelSerializer):
    user = FeedbackUserSerializer(read_only=True)
    target_object = serializers.SerializerMethodField()

    class Meta:
        model = Feedback
        fields = '__all__'
        read_only_fields = ('user', 'reviewer', 'content_type', 'object_id', 'created_at')

    def get_target_object(self, obj):
        if obj.content_type and obj.object_id:
            try:
                target = obj.content_type.get_object_for_this_type(id=obj.object_id)
                return {
                    'id': target.id,
                    'name': getattr(target, 'name', str(target))
                }
            except:
                return None
        return None
