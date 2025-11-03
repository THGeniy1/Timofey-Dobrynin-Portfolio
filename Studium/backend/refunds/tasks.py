import os
import logging
from celery import shared_task
from django.db import transaction

from notifications.decorators import notify_on_task_failure
from payments.models import PurchasedReadyTask

from .serializers import RefundCreateSerializer, FilesSerializer
from .models import Files

from storage.object_storage import S3Client
from studium_backend.settings import (
    AWS_PRIVATE_STORAGE_BUCKET_NAME,
    AWS_PRIVATE_ENDPOINT_URL,
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
)

logger = logging.getLogger("django")

upload_direction = "refunds/"


@shared_task
@notify_on_task_failure(
    message="Не удалось разместить возврат",
    content="create_refund_celery",
)
def create_refund(task_data: dict):
    try:
        with transaction.atomic():
            refund_data = task_data.get('refund_data')
            files = task_data.get('files', [])

            purchase = PurchasedReadyTask.objects.get(id=refund_data.get('purchased_id'))

            serializer_data = {
                'reason': refund_data.get('reason'),
                'contact_info': refund_data.get('contact_info'),
            }
            
            serializer = RefundCreateSerializer(data=serializer_data)
            if serializer.is_valid():
                refund = serializer.save(purchase=purchase)
            else:
                raise Exception(f"Ошибка валидации Refund: {serializer.errors}")
                
            if files:
                handle_files(files, refund)

            return {"refund_id": refund.id, "status": "completed"}

    except Exception as e:
        print(f"Ошибка при создании возврата: {e}")
        logger.error(f"Ошибка при создании возврата: {e}", exc_info=True)
        raise


def handle_files(files, refund):
    if not files:
        return
        
    s3Client = S3Client(
        access_key=AWS_ACCESS_KEY_ID,
        secret_key=AWS_SECRET_ACCESS_KEY,
        endpoint_url=AWS_PRIVATE_ENDPOINT_URL,
        bucket_name=AWS_PRIVATE_STORAGE_BUCKET_NAME,
    )

    files_to_create = []
    for file_data in files:
        if not s3Client.check_file_exists(file_data['path']):
            logger.warning(f"Файл {file_data['name']} не найден в S3")
            continue
            
        try:
            new_path = os.path.join(upload_direction, f"{refund.id}/{file_data['name']}")
            if s3Client.move_between_folders(old_path=file_data['path'], new_path=new_path):
                serializer_data = {
                    'refund': refund.id,
                    'name': file_data['name'],
                    'path': new_path
                }
                
                serializer = FilesSerializer(data=serializer_data)
                if not serializer.is_valid():
                    logger.error(f"Ошибка валидации файла {file_data.get('name', 'unknown')}: {serializer.errors}")
                    continue
                
                files_to_create.append(Files(
                    refund=refund,
                    name=serializer.validated_data['name'],
                    path=serializer.validated_data['path']
                ))
            else:
                logger.error(f"Не удалось переместить файл {file_data['name']}")
                
        except Exception as e:
            logger.error(f"Ошибка при обработке файла {file_data.get('name', 'unknown')}: {e}")

    if files_to_create:
        Files.objects.bulk_create(files_to_create)
        logger.info(f"Создано {len(files_to_create)} файлов для Refund {refund.id}")
