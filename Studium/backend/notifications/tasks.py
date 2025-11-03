from celery import shared_task
from django.utils import timezone
from datetime import timedelta

from .models import Notification


@shared_task
def delete_old_notifications():
    threshold_date = timezone.now() - timedelta(days=5)
    deleted_count, _ = Notification.objects.filter(created_at__lt=threshold_date).delete()
    return f"Deleted {deleted_count} old notifications"
