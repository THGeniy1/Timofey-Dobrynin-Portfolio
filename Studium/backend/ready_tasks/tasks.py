import logging
from django.db import transaction
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from celery import shared_task

from authentication.models import CustomUser
from notifications.decorators import notify_on_task_failure
from .models import ReadyTask, Files
from .serializers import ReadyTaskSerializer, FilesSerializer
from storage.utils import file_mover

from storage.validate_upload_file_mixin import ValidateUploadFileMixin

logger = logging.getLogger("django")

IGNORE_KEYS = {'id', 'owner', 'is_active', 'is_recreate', 'previous_version'}
REMOVE_KEYS = {'id', 'is_recreate'}


def _validate_task_data(data: dict):
    if not data.get("name") or len(data["name"].strip()) < 5:
        raise ValidationError("Название работы должно содержать минимум 5 символов")

    if not data.get("description") or len(data["description"].strip()) < 20:
        raise ValidationError("Описание должно содержать минимум 20 символов")

    if data.get("price", 0) <= 0:
        raise ValidationError("Цена должна быть положительной")


def _create_task(validated_data: dict, files: list) -> ReadyTask:
    filtered_data = {k: v for k, v in validated_data.items() if k not in REMOVE_KEYS}
    filtered_data['price'] = _calculate_adjusted_price(filtered_data['price'])

    serializer = ReadyTaskSerializer(data=filtered_data)
    if serializer.is_valid():
        ready_task = serializer.save()
    else:
        raise ValidationError(f"Ошибка валидации ReadyTask: {serializer.errors}")

    if files:
        _attach_files_to_task(files, ready_task)

    return ready_task


def _attach_files_to_task(files: list, ready_task: ReadyTask):
    if not files:
        return
        
    validate_file_mixin = ValidateUploadFileMixin()
    validate_file_mixin.validate_files(files=files, user_id=ready_task.owner.id)

    files_to_create = []
    for file_data in files:
        serializer_data = {
            'task': ready_task.id,
            'name': file_data['name'],
            'size': file_data['size'],
            'path': file_data['path'],
            'is_public': file_data['is_public']
        }
        
        serializer = FilesSerializer(data=serializer_data)
        if not serializer.is_valid():
            logger.error(f"Ошибка валидации файла {file_data.get('name', 'unknown')}: {serializer.errors}")
            raise ValidationError(f"Неверные данные файла: {serializer.errors}")
        
        files_to_create.append(Files(
            task=ready_task,
            name=serializer.validated_data['name'],
            size=serializer.validated_data['size'],
            path=serializer.validated_data['path'],
            is_public=serializer.validated_data['is_public']
        ))

    if files_to_create:
        Files.objects.bulk_create(files_to_create)
        logger.info(f"Создано {len(files_to_create)} файлов для ReadyTask {ready_task.id}")


def _has_updates(new_data: dict, old_task: ReadyTask) -> bool:
    return any(
        new_data.get(k) != getattr(old_task, k, None) and k not in IGNORE_KEYS
        for k in new_data
    )


def _calculate_adjusted_price(price: float) -> int:
    adjusted = price * 1.2
    return round(adjusted) 


@shared_task
@notify_on_task_failure(
    message="Не удалось разместить или обновить выполненную работу",
    content="create_ready_task_celery",
)
def create_ready_task_with_files(task_data: dict):
    try:
        owner_id = task_data.pop("user", None)
        files = task_data.pop("files", [])

        if not owner_id:
            raise ValidationError("Owner ID is required")

        _validate_task_data(task_data)

        with transaction.atomic():
            owner = CustomUser.objects.select_for_update().get(id=owner_id)
            task_data["owner"] = owner.id

            if not task_data.get("is_recreate"):
                if owner.client.free_slots is None or owner.client.free_slots <= 0:
                    raise ValidationError(f"Недостаточно слотов")

                ready_task = _create_task(task_data, files)

                owner.client.free_slots -= 1
                owner.client.save(update_fields=["free_slots"])
                return {"id": ready_task.id, "status": "created"}

            try:
                existing_task = ReadyTask.objects.select_for_update().get(id=task_data["id"])
            except ObjectDoesNotExist:
                raise ValidationError(f"Задача с ID {task_data['id']} не найдена")

            if owner != existing_task.owner or not _has_updates(task_data, existing_task):
                raise ValidationError("Невозможно обновить задачу: недостаточно прав или нет изменений")

            task_data["previous_version"] = existing_task.id
            task_data["status"] = "review"

            new_task = _create_task(task_data, files)

            existing_task.status = "unpublished"
            existing_task.save()

            return {"id": new_task.id, "status": "updated"}

    except Exception as e:
        logger.error(f"Ошибка при создании задачи: {e}", exc_info=True)
        raise


@shared_task
def move_file_between_folders(task_id):
    try:
        instance = ReadyTask.objects.get(id=task_id)
        files = Files.objects.filter(task=instance)

        file_mover(upload_dir='ready_tasks', instance=instance, files=files)

    except Exception as e:
        logger.error(f"Ошибка при перемещении файлов задачи: {e}", exc_info=True)
        raise


# def handle_files(files, owner_id, ready_task): Консервация от 05.06.2025
#     s3_client = S3Client(
#         access_key=AWS_ACCESS_KEY_ID,
#         secret_key=AWS_SECRET_ACCESS_KEY,
#         endpoint_url=AWS_PRIVATE_ENDPOINT_URL,
#         bucket_name=AWS_PRIVATE_STORAGE_BUCKET_NAME
#     )
#
#     successful_files = []
#     failed_files = []
#
#     for file_data in files:
#         if s3_client.check_file_exists(file_data['path']):
#             try:
#                 new_path = os.path.join(UPLOAD_DIR, f"{ready_task.id}/{file_data['name']}")
#                 if s3_client.move_between_folders(old_path=file_data['path'], new_path=new_path):
#                     file_data['task'] = ready_task
#                     file_data['path'] = new_path
#                     Files.objects.create(**file_data)
#                     successful_files.append(file_data['name'])
#                 else:
#                     failed_files.append(file_data['name'])
#             except Exception as e:
#                 logger.error(f"Ошибка при загрузке файла {file_data['name']}: {e}", exc_info=True)
#                 failed_files.append(file_data['name'])
#
#     if failed_files:
#         logger.warning(f"Не удалось загрузить следующие файлы: {', '.join(failed_files)}")
#
#     s3_client.clear_temp_folder(user_id=owner_id)
#
#     return successful_files
