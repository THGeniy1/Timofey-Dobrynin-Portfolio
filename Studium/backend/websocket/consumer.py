import json
import logging
from channels.layers import get_channel_layer

from channels.generic.websocket import AsyncWebsocketConsumer

from chat.chat_handler import ChatHandler
from notifications.notification_handler import NotificationHandler

from .auth_handler import AuthHandler

logger = logging.getLogger("websocket")


class BaseWebsocketConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auth_handler = None
        self.notification_handler = None
        self.chat_handler = None
        self.user_id = None
        self.channel_layer = None
        self.user_layer_groups = []

    async def websocket_connect(self, message):
        self.auth_handler = AuthHandler(self)

        if not await self.auth_handler.authenticate_user():
            return

        self.user_id = self.auth_handler.user_id
        self.notification_handler = NotificationHandler(self, self.user_id)
        self.chat_handler = ChatHandler(self, self.user_id)
        self.channel_layer = get_channel_layer()

        self.user_layer_groups = [
            f"user_{self.user_id}_notifications",
            f"user_{self.user_id}_chat_notifications"
        ]

        for group_name in self.user_layer_groups:
            await self.channel_layer.group_add(
                group_name,
                self.channel_name
            )

        await self.accept()
        await self.notification_handler.send_notifications()

    async def websocket_disconnect(self, close_code):
        if self.auth_handler:
            self.auth_handler.cleanup()

        if self.user_id and self.channel_layer:
            for group_name in self.user_layer_groups:
                await self.channel_layer.group_discard(
                    group_name,
                    self.channel_name
                )

    async def websocket_receive(self, message):
        try:
            data = json.loads(message["text"])
            action = data.get("action")

            if action == "update_token":
                await self.auth_handler.update_token(data.get("token"))
            elif action in ['join_chat', 'send_message', 'leave_chat']:
                await self._handle_chat_action(data=data, action=action)
            elif action == ['mark_read', 'mark_all_read']:
                await self._handle_notification_action(data=data, action=action)
            else:
                await self.send_json({"message": f"Неизвестное действие: {action}"})
        except json.JSONDecodeError:
            await self.send_json({"error": "Неверный формат JSON"})

    async def _handle_chat_action(self, data, action):
        if action == "join_chat":
            await self.chat_handler.join_chat(chat_id=data['chat_id'])
        elif action == "send_message":
            await self.chat_handler.send_message(message_data=data)
        elif action == "leave_chat":
            await self.chat_handler.leave_chat(chat_id=data['chat_id'])

    async def _handle_notification_action(self, data, action):
        if action == "mark_read":
            await self.notification_handler.mark_notification_read(data["id"], data['type_name'])
        elif action == "mark_all_read":
            await self.notification_handler.mark_all_notifications_read()

    async def send_json(self, message):
        await self.send(text_data=json.dumps(message))

    async def websocket_send_notification(self, event):
        notif_id = event.get("id")
        notif_type = event.get("type_name", "notification")

        if not notif_id:
            logger.warning("Получено событие без ID уведомления")
            return

        await self.notification_handler.send_notification(notif_id, notif_type)

    async def websocket_send_message(self, event):
        try:
            await self.send_json({
                "type": "websocket_send_message",
                "message": event["message"]
            })
        except Exception as e:
            logger.error(f"Error sending chat message: {e}")
