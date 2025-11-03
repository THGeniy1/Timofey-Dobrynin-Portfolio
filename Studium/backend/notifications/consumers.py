import json
import logging
import asyncio
from datetime import datetime, timezone
from urllib.parse import parse_qs

from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer
from channels.generic.websocket import AsyncWebsocketConsumer
from rest_framework_simplejwt.tokens import AccessToken

from notifications.models import Notification, FailureNotification

logger = logging.getLogger("django")


class NotificationConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_group_name = None
        self.channel_layer = None
        self.token_expiry_task = None
        self.token = None
        self.user_id = None

    async def websocket_connect(self, message):
        logger.info("Запрос на подключение")
        self.channel_layer = get_channel_layer()
        self.token = self._get_token_from_scope()

        if not self.token:
            await self.close(code=4001)
            return

        self.user_id, expiry_time = self._authenticate_user(self.token)
        if not self.user_id:
            await self.close(code=4001)
            return

        await self._setup_channel_layer()
        await self.accept()

        await self.send_notifications()

        self._start_token_expiry_timer(expiry_time)

    async def websocket_disconnect(self, message):
        if self.room_group_name and self.channel_layer:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        if self.token_expiry_task:
            self.token_expiry_task.cancel()
        logger.info(f"WebSocket отключен: {self.user_id}")

    async def websocket_receive(self, message):
        try:
            data = json.loads(message["text"])
            action = data.get("action")

            if action == "update_token":
                await self._update_token(data.get("token"))
            elif action == "mark_read":
                if data.get("id"):
                    notif_type = await self._get_notification_type(data["id"])
                    if notif_type:
                        await self.mark_notification_read(data["id"], notif_type)
            elif action == "mark_all_read":
                await self.mark_all_notifications_read()
            else:
                await self.send_json({"message": f"Неизвестное действие: {action}"})
        except json.JSONDecodeError:
            await self.send_json({"error": "Неверный формат JSON"})

    async def websocket_send_notification(self, event):
        payload = event.get("payload")
        if not payload:
            logger.warning("Получено событие без payload")
            return

        await self.send_json({"notification": payload})

    async def send_json(self, message):
        await self.send(text_data=json.dumps(message))

    async def close_after_expiry(self, timeout):
        await asyncio.sleep(timeout)
        await self.close(code=4002)

    async def _update_token(self, new_token):
        self.user_id, expiry_time = self._authenticate_user(new_token)
        if not self.user_id:
            await self.send_json({"error": "Неверный или истекший токен"})
            return

        self.token = new_token
        if self.token_expiry_task:
            self.token_expiry_task.cancel()
        self._start_token_expiry_timer(expiry_time)

    def _get_token_from_scope(self):
        query_string = self.scope.get("query_string", b"").decode()
        query_params = parse_qs(query_string)
        return query_params.get("token", [None])[0]

    @staticmethod
    def _authenticate_user(token):
        try:
            access_token = AccessToken(token)
            user_id = access_token["user_id"]
            exp_timestamp = access_token["exp"]
            expiry_time = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
            remaining_time = (expiry_time - datetime.now(timezone.utc)).total_seconds()

            if remaining_time <= 0:
                return None, None
            return user_id, remaining_time + 10
        except Exception:
            return None, None

    async def _setup_channel_layer(self):
        self.room_group_name = f"user_{self.user_id}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

    def _start_token_expiry_timer(self, expiry_time):
        if expiry_time:
            self.token_expiry_task = asyncio.create_task(self.close_after_expiry(expiry_time))

    async def send_notifications(self):
        notifications = await self.get_notifications()
        for notification in notifications:
            notification = await self.prepare_for_send(notification)
            await self.send_json({"notification": notification})

    async def mark_notification_read(self, notification_id, notif_type):
        notification = await self.set_notification_read(notification_id, notif_type)
        if notification:
            updated_notification = await self.get_notification(notification_id, notif_type)
            if updated_notification:
                prepared = await self.prepare_for_send(updated_notification)
                await self.send_json({"notification": prepared})

    async def mark_all_notifications_read(self):
        await self.set_all_notifications_read()
        await self.send_notifications()

    @sync_to_async
    def fetch_notifications(self):
        notifs = list(
            Notification.objects.select_related("content_type")
            .filter(user_id=self.user_id)
            .order_by("-created_at")
        )
        fails = list(
            FailureNotification.objects.filter(user_id=self.user_id)
            .order_by("-created_at")
        )
        merged = notifs + fails
        merged.sort(key=lambda n: n.created_at, reverse=True)
        return merged

    async def get_notifications(self):
        notifications = await self.fetch_notifications()
        return [await self.serialize_notification(n) for n in notifications]

    @sync_to_async
    def fetch_notification(self, notif_id, notif_type="notification"):
        if notif_type == "failure":
            return FailureNotification.objects.filter(user_id=self.user_id, id=notif_id).first()
        return Notification.objects.select_related("content_type").filter(user_id=self.user_id, id=notif_id).first()

    async def get_notification(self, notif_id, notif_type="notification"):
        notif = await self.fetch_notification(notif_id, notif_type)
        return await self.serialize_notification(notif)

    @sync_to_async
    def serialize_notification(self, notification):
        if not notification:
            return None
        base = {
            "id": notification.id,
            "message": notification.message,
            "content": notification.content,
            "is_read": notification.is_read,
            "auto_read": notification.auto_read,
            "created_at": notification.created_at.isoformat(),
        }
        if isinstance(notification, Notification):
            base.update({
                "object_id": notification.object_id,
                "target_object": notification.target_object or None,
                "type_name": "notification"
            })
        else:  
            base.update({
                "failure_message": notification.failure_message,
                "type_name": "failure"
            })
        return base

    @sync_to_async
    def set_notification_read(self, notification_id, notif_type):
        model = FailureNotification if notif_type == "failure" else Notification
        notif = model.objects.filter(id=notification_id, user_id=self.user_id, is_read=False).first()
        if notif:
            notif.is_read = True
            notif.save()
            return notif
        return None

    @sync_to_async
    def set_all_notifications_read(self):
        Notification.objects.filter(user_id=self.user_id, is_read=False, auto_read=True).update(is_read=True)
        FailureNotification.objects.filter(user_id=self.user_id, is_read=False, auto_read=True).update(is_read=True)

    async def _get_notification_type(self, notification_id):
        notif = await self.fetch_notification(notification_id, "notification")
        if notif:
            return "notification"
        
        notif = await self.fetch_notification(notification_id, "failure")
        if notif:
            return "failure"
        
        return None

    @sync_to_async
    def prepare_for_send(self, notification):
        try:
            if notification.get("content") == "purchased_task":
                target = notification.get("target_object")
                if target and isinstance(target, dict):
                    if target.get("model") == "ready_task":
                        notification["add_data"] = target.get("id")
                    elif target.get("model") == "task":
                        notification["task_id"] = target.get("id")
            return notification
        except Exception as e:
            logger.error(f"Ошибка при подготовке уведомления: {e}")
            return notification
