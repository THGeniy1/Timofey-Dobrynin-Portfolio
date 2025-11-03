from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from .models import Report, ReportComment, Files


class FilesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Files
        fields = '__all__'


class ReportCommentSerializer(serializers.ModelSerializer):
    files = FilesSerializer(many=True, read_only=True)

    class Meta:
        model = ReportComment
        fields = ['id', 'report', 'user', 'comment', 'created_at', 'is_admin', 'files']
        read_only_fields = ['created_at']


class ReportSerializer(serializers.ModelSerializer):
    comments = ReportCommentSerializer(many=True, read_only=True)
    content_type = serializers.PrimaryKeyRelatedField(queryset=ContentType.objects.all(),
                                                      required=False, allow_null=True)
    object_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = Report
        fields = ['id', 'user', 'reported_user', 'content_type', 'object_id', 'status', 'type', 'created_at', 'comments']
        read_only_fields = ['created_at']

    def create(self, validated_data):
        return Report.objects.create(**validated_data)
