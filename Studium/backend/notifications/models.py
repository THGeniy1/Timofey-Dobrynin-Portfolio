from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from authentication.models import CustomUser


class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField()

    content = models.CharField(max_length=20, default='user')

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    target_object = GenericForeignKey("content_type", "object_id")

    is_read = models.BooleanField(default=False)
    auto_read = models.BooleanField(default=True,
                                    help_text="Если True, уведомление читается автоматически при загрузке.")

    created_at = models.DateTimeField(auto_now_add=True)


class FailureNotification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='failure_notification')
    message = models.TextField()
    content = models.CharField(max_length=100, default='user')

    failure_message = models.TextField()

    is_read = models.BooleanField(default=False)
    auto_read = models.BooleanField(default=True,
                                    help_text="Если True, уведомление читается автоматически при загрузке.")

    created_at = models.DateTimeField(auto_now_add=True)
