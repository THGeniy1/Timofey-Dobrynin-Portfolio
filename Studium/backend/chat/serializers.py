from rest_framework import serializers
from django.db import transaction
from .models import Chat, Message, ChatUnread, Files
from authentication.models import CustomUser


class ChatCreateSerializer(serializers.ModelSerializer):
    participant_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Chat
        fields = ['participant_id']
        read_only_fields = ['created_at', 'updated_at', 'user1_read', 'user2_read']

    def validate_participant_id(self, value):
        try:
            CustomUser.objects.get(id=value)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("Пользователь не найден")

        if value == self.context['request'].user.id:
            raise serializers.ValidationError("Нельзя создать чат с самим собой")

        return value

    def validate(self, attrs):
        request = self.context['request']
        participant_id = attrs['participant_id']

        existing_chat = Chat.objects.filter(
            participants=request.user
        ).filter(participants=participant_id).first()

        if existing_chat:
            raise serializers.ValidationError(
                f"Чат между вами и этим пользователем уже существует (ID: {existing_chat.id})"
            )

        return attrs

    def create(self, validated_data):
        request = self.context['request']
        participant_id = validated_data.pop('participant_id')

        with transaction.atomic():
            chat = Chat.objects.create()

            chat.participants.add(request.user, participant_id)

            participants = list(chat.participants.all().order_by('id'))
            if len(participants) == 2:
                user1, user2 = participants

                if request.user.id == user1.id:
                    chat.user1_read = True
                    chat.user2_read = False
                else:
                    chat.user1_read = False
                    chat.user2_read = True

                chat.save()

            return chat


class ChatListSerializer(serializers.ModelSerializer):
    other_user = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    is_online = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = [
            'id',
            'other_user',
            'unread_count',
            'last_message',
            'created_at',
            'updated_at',
            'user1_read',
            'user2_read',
            'is_online'
        ]

    def get_other_user(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None

        other_user = obj.participants.exclude(id=request.user.id).first()
        if other_user:
            return {
                'id': other_user.id,
                'username': other_user.name,
                'email': other_user.email,
            }
        return None

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0

        try:
            unread_obj = ChatUnread.objects.get(chat=obj, user=request.user)
            return unread_obj.unread_count
        except ChatUnread.DoesNotExist:
            return 0


class MessageSerializer(serializers.ModelSerializer):
    chat_id = serializers.IntegerField(source='chat.id', read_only=True)
    sender_id = serializers.IntegerField(source='sender.id', read_only=True)
    
    class Meta:
        model = Message
        fields = [
            "id",
            "chat",
            "sender", 
            "chat_id",
            "sender_id",
            "message",
            "file_path",
            "created_at",
            "read_at",
            "delivered_at"
        ]
        read_only_fields = ["id", "created_at", "read_at", "delivered_at"]


class FilesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Files
        fields = '__all__'
