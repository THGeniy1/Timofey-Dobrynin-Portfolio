import logging
from asgiref.sync import sync_to_async
from .models import Notification, FailureNotification
from .serializers import NotificationSerializer, FailureNotificationSerializer

logger = logging.getLogger('notification_handler')


class NotificationHandler:
    def __init__(self, consumer, user_id):
        self.consumer = consumer
        self.user_id = user_id

    async def send_notifications(self):
        notifications = await self._get_user_notifications()
        for notification in notifications:
            await self.consumer.send_json({"notification": notification})

    async def send_notification(self, notif_id, notif_type="notification"):
        if notif_type == "failure":
            notification = await sync_to_async(
                FailureNotification.objects.filter(user_id=self.user_id, id=notif_id).first
            )()
            serializer_class = FailureNotificationSerializer
        else:
            notification = await sync_to_async(
                Notification.objects.select_related("content_type")
                .filter(user_id=self.user_id, id=notif_id).first
            )()
            serializer_class = NotificationSerializer

        if notification:
            serialized = await self._serialize_with_serializer(notification, serializer_class)
            prepared = self.prepare_for_send(serialized)
            await self.consumer.send_json({"notification": prepared})

    async def mark_notification_read(self, notification_id, notif_type):
        notification = await self.set_notification_read(notification_id, notif_type)
        if notification:
            await self.send_notification(notification_id, notif_type)

    async def mark_all_notifications_read(self):
        await self.set_all_notifications_read()
        await self.send_notifications()

    async def _get_user_notifications(self):
        @sync_to_async
        def get_notifications():
            notifs = list(
                Notification.objects.select_related("content_type")
                .filter(user_id=self.user_id)
                .order_by("-created_at")
            )
            return notifs

        @sync_to_async
        def get_failures():
            fails = list(
                FailureNotification.objects
                .filter(user_id=self.user_id)
                .order_by("-created_at")
            )
            return fails

        notifs = await get_notifications()
        fails = await get_failures()

        notifications = await self._serialize_notifications_with_serializer(notifs, NotificationSerializer)
        failure_notifications = await self._serialize_notifications_with_serializer(fails,
                                                                                    FailureNotificationSerializer)

        all_notifications = notifications + failure_notifications
        return sorted(all_notifications, key=lambda n: n["created_at"], reverse=True)

    async def _serialize_notifications_with_serializer(self, notifications_list, serializer_class):
        result = []
        for notification in notifications_list:
            serialized = await self._serialize_with_serializer(notification, serializer_class)
            result.append(serialized)
        return result

    async def _serialize_with_serializer(self, notification, serializer_class):
        try:
            @sync_to_async
            def get_serialized_data():
                serializer = serializer_class(notification)
                return serializer.data

            serialized_data = await get_serialized_data()

            if serializer_class == NotificationSerializer:
                serialized_data["type_name"] = "notification"
            else:
                serialized_data["type_name"] = "failure"

            return serialized_data

        except Exception as e:
            logger.error(f"Error serializing notification {notification.id}: {e}")

            return self._serialize_single_notification_fallback(notification)

    @staticmethod
    def _serialize_single_notification_fallback(notification):
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
                "target_object": None,
                "type_name": "notification"
            })
        else:  
            base.update({
                "failure_message": notification.failure_message,
                "type_name": "failure"
            })
        return base

    @staticmethod
    def prepare_for_send(notification_dict):
        try:
            if notification_dict.get("content") == "purchased_task":
                target = notification_dict.get("target_object")

                if target and isinstance(target, dict):
                    if target.get("model") == "ready_task":
                        notification_dict["add_data"] = target.get("id")

                    if target.get("model") == "task" and target.get("id"):
                        notification_dict["task_id"] = target.get("id")

            return notification_dict

        except Exception as e:
            logger.error(f"Ошибка при подготовке уведомления: {e}")
            return notification_dict

    async def set_notification_read(self, notification_id, notif_type):
        model = FailureNotification if notif_type == "failure" else Notification

        @sync_to_async
        def mark_read():
            notif = model.objects.filter(
                id=notification_id,
                user_id=self.user_id,
                is_read=False
            ).first()
            if notif:
                notif.is_read = True
                notif.save()
                return notif
            return None

        return await mark_read()

    async def set_all_notifications_read(self):
        @sync_to_async
        def mark_all_read():
            Notification.objects.filter(
                user_id=self.user_id,
                is_read=False,
                auto_read=True
            ).update(is_read=True)

            FailureNotification.objects.filter(
                user_id=self.user_id,
                is_read=False,
                auto_read=True
            ).update(is_read=True)

        await mark_all_read()
