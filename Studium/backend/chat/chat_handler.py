import logging

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import *
from .serializers import MessageSerializer, FilesSerializer

from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer

from storage.validate_upload_file_mixin import ValidateUploadFileMixin
from storage.utils import file_mover

logger = logging.getLogger('chat_handler')


class ChatHandler:
    def __init__(self, consumer, user_id):
        self.consumer = consumer
        self.user_id = user_id
        self.channel_layer = get_channel_layer()

    async def join_chat(self, chat_id):
        has_access = await self._check_chat_access(chat_id=chat_id)

        if not has_access:
            await self.consumer.send_json({
                "error": f"Нет доступа к чату {chat_id}",
                "type": "chat_error"
            })
            return False

        try:
            group_name = f"chat_{chat_id}"
            await self.channel_layer.group_add(
                group_name,
                self.consumer.channel_name
            )

            history = await self._get_chat_history(chat_id)
            await self.consumer.send_json({
                "type": "chat_joined",
                "chat_id": chat_id,
                "messages": history
            })

            return True

        except Exception as e:
            logger.error(f"Error joining chat {chat_id}: {e}")
            return False

    async def leave_chat(self, chat_id):
        try:
            group_name = f"chat_{chat_id}"
            await self.channel_layer.group_discard(
                group_name,
                self.consumer.channel_name
            )
            return True
        except Exception as e:
            logger.error(f"Error leaving chat {chat_id}: {e}")
            return False

    async def send_message(self, message_data):
        try:
            has_access = await self._check_chat_access(message_data.get('chat_id'))
            if not has_access:
                return False

            saved_message = await self._create_message_with_files(message_data)
            if not saved_message:
                return False

            await self._broadcast_message(saved_message)

            return True

        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False

    async def _check_chat_access(self, chat_id):
        try:
            @sync_to_async
            def check_access():
                chat = Chat.objects.filter(
                    id=chat_id,
                    participants__id=self.user_id
                ).first()
                return chat is not None
            
            return await check_access()
        except Exception as e:
            logger.error(f"Error checking chat access: {e}")
            return False

    @staticmethod
    async def _get_chat_history(chat_id, limit=100):
        try:
            @sync_to_async
            def get_history():
                messages = Message.objects.filter(
                    chat=chat_id
                ).select_related('sender', 'chat').prefetch_related(
                    'files'
                ).order_by('created_at')[:limit]

                serializer = MessageSerializer(messages, many=True)
                return serializer.data
            
            return await get_history()
        except Exception as e:
            logger.error(f"Error getting chat history for chat {chat_id}: {e}")
            return []

    async def _create_message_with_files(self, message_data):
        try:
            @sync_to_async
            def create_message():
                with transaction.atomic():
                    text = message_data.get('message', '').strip()
                    if not text:
                        raise ValidationError

                    message_data_with_sender = {
                        **message_data,
                        'sender_id': self.user_id
                    }

                    serializer = MessageSerializer(data=message_data_with_sender)
                    if not serializer.is_valid():
                        raise ValidationError

                    message_instance = serializer.save()

                    files = message_data.get('files', [])
                    if files:
                        self._attach_files_to_message_sync(files, message_instance)

                    return message_instance

            return await create_message()
        except Exception as e:
            logger.error(f"Error creating message with files: {e}")
            return None

    def _attach_files_to_message_sync(self, files: list, message: Message):
        if not files:
            return
            
        validate_file_mixin = ValidateUploadFileMixin()
        validate_file_mixin.validate_files(files=files, user_id=self.user_id)

        files_to_create = []
        for file_data in files:
            serializer_data = {
                'message': message.id,
                'name': file_data['name'],
                'size': file_data['size'],
                'path': file_data['path']
            }
            
            serializer = FilesSerializer(data=serializer_data)
            if not serializer.is_valid():
                logger.error(f"Ошибка валидации файла {file_data.get('name', 'unknown')}: {serializer.errors}")
                raise ValidationError(f"Неверные данные файла: {serializer.errors}")
            
            files_to_create.append(Files(
                message=message,
                name=serializer.validated_data['name'],
                size=serializer.validated_data['size'],
                path=serializer.validated_data['path']
            ))

        if files_to_create:
            Files.objects.bulk_create(files_to_create)
            logger.info(f"Создано {len(files_to_create)} файлов для сообщения {message.id}")

        file_mover('chats', instance=message, files=files, storage_type='public')

    async def _broadcast_message(self, message_instance):
        try:
            serialized_message = await self._serialize_single_message(message_instance)

            await self.channel_layer.group_send(
                f"chat_{message_instance.chat.id}",
                {
                    "type": "websocket_send_message",
                    "message": serialized_message
                }
            )
        except Exception as e:
            logger.error(f"Error broadcasting message: {e}")

    @staticmethod
    async def _serialize_single_message(message_data):
        try:
            @sync_to_async
            def serialize_message():
                serializer = MessageSerializer(message_data)
                return serializer.data
            
            return await serialize_message()
        except Exception as e:
            logger.error(f"Error serializing message {message_data}: {e}")
            return None
