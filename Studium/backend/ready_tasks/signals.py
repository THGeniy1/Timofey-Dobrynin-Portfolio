from django.db.models.signals import pre_save
from django.dispatch import receiver

from ready_tasks.models import ReadyTask
from .tasks import move_file_between_folders


@receiver(pre_save, sender=ReadyTask)
def signal_task_move_file(sender, instance, **kwargs):
    print(f"[INFO] Signal triggered for task {instance.id}")

    try:
        old_instance = ReadyTask.objects.get(pk=instance.pk)
        print(f"[DEBUG] Retrieved old instance for task {instance.id}")
        
        if old_instance.status != instance.status:
            print(f"[INFO] Status change detected for task {instance.id}: {old_instance.status} -> {instance.status}")
            
            if instance.status == 'active':
                print(f"[INFO] Task {instance.id} status changed to active, checking for files")

                if instance.files.exists():
                    file_count = instance.files.count()
                    print(f"[INFO] Found {file_count} files for task {instance.id}, initiating move")
                    move_file_between_folders.delay(task_id=instance.id)
                    print(f"[INFO] File move task initiated for task {instance.id}")
                else:
                    print(f"[INFO] No files found for task {instance.id}, skipping move")
            else:
                print(f"[DEBUG] Task {instance.id} status changed to {instance.status}, no action needed")
        else:
            print(f"[DEBUG] No status change for task {instance.id}, current status: {instance.status}")

    except ReadyTask.DoesNotExist:
        print(f"[ERROR] Old instance not found for task {instance.id}")
    except Exception as e:
        print(f"[ERROR] Error in signal_task_move_file for task {instance.id}: {str(e)}")
