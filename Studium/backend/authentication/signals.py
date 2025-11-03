import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from .models import Client
from ready_tasks.models import ReadyTask

User = get_user_model()
logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def add_user_to_client_group(sender, instance, created, **kwargs):
    if not created:
        return

    try:
        instance.user_permissions.clear()

        client_group = Group.objects.get(name='Client')
        instance.groups.add(client_group)
        
        print(f"Пользователь {instance.email} (ID: {instance.id}) добавлен в группу 'Client'")
    except Exception as e:
        print(f"Ошибка при добавлении пользователя {instance.email} (ID: {instance.id}) в группу 'Client': {str(e)}")
        return


@receiver(post_save, sender=Client)
def ban_client_tasks(sender, instance, created, **kwargs):
    if instance.is_banned:
        if instance.user:
            ReadyTask.objects.filter(owner=instance.user, status='active').update(status='unpublished')
