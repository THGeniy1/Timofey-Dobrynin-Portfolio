import logging
from django.db import transaction
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from celery import shared_task

from authentication.models import CustomUser
from notifications.decorators import notify_on_task_failure
from storage.validate_upload_file_mixin import ValidateUploadFileMixin
from .models import OrderTask, Files
from .serializers import OrderTaskCreateSerializer, FilesSerializer
from storage.object_storage import S3Client
from studium_backend.settings import (
    AWS_PUBLIC_STORAGE_BUCKET_NAME,
    AWS_PUBLIC_ENDPOINT_URL,
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
)
from filters.validator import TextValidator

logger = logging.getLogger("django")

UPLOAD_DIR = "order_tasks/"
IGNORE_KEYS = {'id', 'owner', 'is_active', 'is_recreate', 'previous_version'}
REMOVE_KEYS = {'id', 'is_recreate'}


def _validate_task_data(data: dict):
    name = data.get("name", "").strip()
    description = data.get("description", "").strip()
    price = data.get("price", 0)
    deadline = data.get("deadline")

    if not name or len(name) < 5:
        raise ValidationError("Название задания должно содержать не менее 5 символов.")

    if not description or len(description) < 20:
        raise ValidationError("Описание должно содержать не менее 20 символов.")

    if not data.get("discipline"):
        raise ValidationError("Не указана дисциплина.")

    if not data.get("type"):
        raise ValidationError("Не указан тип работы.")

    if price <= 0:
        raise ValidationError("Цена должна быть положительной.")

    if deadline is None:
        raise ValidationError("Не указан дедлайн выполнения.")


def _create_task(validated_data: dict, files: list) -> OrderTask:
    filtered_data = {k: v for k, v in validated_data.items() if k not in REMOVE_KEYS}
    filtered_data['price'] = _calculate_adjusted_price(filtered_data['price'])

    serializer = OrderTaskCreateSerializer(data=filtered_data)
    if not serializer.is_valid():
        raise ValidationError(f"Ошибка валидации OrderTask: {serializer.errors}")

    order_task = serializer.save()

    if files:
        _attach_files_to_task(files, order_task)

    return order_task


def _update_task(existing_task: OrderTask, updated_data: dict, files: list = None) -> OrderTask:
    updated_fields = []

    for key, new_value in updated_data.items():
        if key in REMOVE_KEYS or not hasattr(existing_task, key):
            continue

        old_value = getattr(existing_task, key)
        if old_value != new_value:
            if key == "price":
                new_value = _calculate_adjusted_price(new_value)

            setattr(existing_task, key, new_value)
            updated_fields.append(key)

    if not updated_fields and not files:
        raise ValidationError("Нет изменений для обновления.")

    existing_task.save(update_fields=updated_fields)

    if files:
        _attach_files_to_task(files, existing_task)

    return existing_task


def _attach_files_to_task(files: list, order_task: OrderTask):
    if not files:
        return
        
    validate_file_mixin = ValidateUploadFileMixin()
    validate_file_mixin.validate_files(files=files, user_id=order_task.owner.id)

    files_to_create = []
    for file_data in files:
        serializer_data = {
            'task': order_task.id,
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
            task=order_task,
            name=serializer.validated_data['name'],
            size=serializer.validated_data['size'],
            path=serializer.validated_data['path'],
            is_public=serializer.validated_data['is_public']
        ))

    if files_to_create:
        Files.objects.bulk_create(files_to_create)
        logger.info(f"Создано {len(files_to_create)} файлов для OrderTask {order_task.id}")


def _has_updates(new_data: dict, old_task: OrderTask) -> bool:
    return any(
        new_data.get(k) != getattr(old_task, k, None) and k not in IGNORE_KEYS
        for k in new_data
    )


def _calculate_adjusted_price(price: float) -> float:
    adjusted = price * 1.2
    return round(adjusted, 2)


@shared_task
@notify_on_task_failure(
    message="Не удалось разместить или обновить заказ на выполнение работы",
    content="create_order_task_celery",
)
def create_order_task_with_files(task_data: dict):
    try:
        owner_id = task_data.pop("user", None)
        files = task_data.pop("files", [])

        if not owner_id:
            raise ValidationError("Не указан идентификатор пользователя (owner).")

        _validate_task_data(task_data)

        with transaction.atomic():
            owner = CustomUser.objects.select_for_update().get(id=owner_id)
            task_data["owner"] = owner.id

            if not task_data.get("is_recreate"):
                order_task = _create_task(task_data, files)

                return {"id": order_task.id, "status": "created"}

            try:
                existing_task = OrderTask.objects.select_for_update().get(id=task_data["id"])
            except ObjectDoesNotExist:
                raise ValidationError(f"Задача с ID {task_data['id']} не найдена.")

            if owner != existing_task.owner:
                raise ValidationError("Невозможно обновить задачу: вы не являетесь её владельцем.")

            updated_task = _update_task(existing_task, task_data, files)

            return {"id": updated_task.id, "status": "updated"}

    except Exception as e:
        logger.error(f"Ошибка при создании/обновлении OrderTask: {e}", exc_info=True)
        raise


@shared_task
def move_file_between_folders(task_id):
    try:
        instance = OrderTask.objects.get(id=task_id)
        files = Files.objects.filter(task=instance)

        s3_client = S3Client(
            access_key=AWS_ACCESS_KEY_ID,
            secret_key=AWS_SECRET_ACCESS_KEY,
            endpoint_url=AWS_PUBLIC_ENDPOINT_URL,
            bucket_name=AWS_PUBLIC_STORAGE_BUCKET_NAME
        )

        failed_files = []

        with transaction.atomic():
            for file in files:
                try:
                    new_path = f"{UPLOAD_DIR}{instance.id}/{file.name}"

                    if s3_client.move_between_folders(old_path=file.path, new_path=new_path):
                        file.path = new_path
                        file.save(update_fields=["path"])
                    else:
                        failed_files.append(file.name)
                except Exception as e:
                    logger.error(f"Ошибка при перемещении файла {file.name}: {e}", exc_info=True)
                    failed_files.append(file.name)

            if failed_files:
                logger.warning(f"Не удалось переместить: {', '.join(failed_files)}")

    except Exception as e:
        logger.error(f"Ошибка при перемещении файлов OrderTask: {e}", exc_info=True)
        raise
