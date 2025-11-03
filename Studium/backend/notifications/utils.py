import logging
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.contenttypes.models import ContentType
from .models import Notification, FailureNotification
from .serializers import NotificationSerializer, FailureNotificationSerializer

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from studium_backend import settings

logger = logging.getLogger("django")


def _send_ws_notification(user_id, payload):
    channel_layer = get_channel_layer()
    try:
        async_to_sync(channel_layer.group_send)(
            f"user_{user_id}",
            {
                "type": "websocket_send_notification",
                "payload": payload
            }
        )
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления в WebSocket: {e}")


def create_notification(user, message, content_type=None, object_id=None,
                        content="user", auto_read=True, mark_read=False):
    if content_type and object_id:
        ct = content_type
    else:
        ct = ContentType.objects.get_for_model(user)
        object_id = user.id

    notification = Notification.objects.create(
        user=user,
        content_type=ct,
        object_id=object_id,
        message=message,
        content=content,
        auto_read=auto_read,
        is_read=mark_read
    )

    payload = NotificationSerializer(notification).data
    payload["type_name"] = "notification"

    _send_ws_notification(user.id, payload)
    return notification


def create_failure_notification(user, message, failure_message,
                                content="user", auto_read=True, mark_read=False):
    failure_notification = FailureNotification.objects.create(
        user=user,
        message=message,
        failure_message=failure_message,
        content=content,
        auto_read=auto_read,
        is_read=mark_read
    )

    payload = FailureNotificationSerializer(failure_notification).data
    payload["type_name"] = "failure"

    _send_ws_notification(user.id, payload)
    return failure_notification


def send_user_email(user, subject, message, template_name="notification", extra_context=None):

    if not getattr(user, "email", None):
        logger.warning(f"У пользователя {user} не указан email")
        logger.info(f"email пользователя {user}:{user.email}")
        return

    context = {
        "user": user,
        "message": message,
        "site_url": settings.BASE_URL,
    }

    if extra_context:
        context.update(extra_context)
        
    try:
        text_content = render_to_string(f"emails/{template_name}.txt", context)
        html_content = render_to_string(f"emails/{template_name}.html", context)

        email_msg = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )
        email_msg.attach_alternative(html_content, "text/html")
        email_msg.send()

        logger.info(f"Письмо успешно отправлено пользователю {user.email}")

    except Exception as e:
        logger.exception(f"Ошибка при отправке письма пользователю {user.email}: {e}")
