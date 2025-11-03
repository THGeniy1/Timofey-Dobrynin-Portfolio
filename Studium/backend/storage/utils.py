import logging
import os
from django.db import transaction
from storage.object_storage import S3Client
from studium_backend import settings

logger = logging.getLogger("django")


def file_mover(upload_dir: str, instance, files, storage_type: str = 'private'):
    if not instance.id:
        raise ValueError("Instance must have an ID before moving files")

    s3_client = S3Client(**_get_storage_config(storage_type=storage_type))

    try:
        with transaction.atomic():
            for file in files:
                new_path = os.path.join(upload_dir, str(instance.id), file.name)

                if s3_client.move_between_folders(old_path=file.name, new_path=new_path):
                    file.name = new_path
                    file.save()
                else:
                    raise Exception("S3 move operation returned False")

    except Exception as e:
        logger.error(f"Транзакция прервана: {e}")


def _get_storage_config(storage_type):
    if storage_type == 'public':
        return {
            'access_key': settings.AWS_ACCESS_KEY_ID,
            'secret_key': settings.AWS_SECRET_ACCESS_KEY,
            'endpoint_url': settings.AWS_PUBLIC_ENDPOINT_URL,
            'bucket_name': settings.AWS_PUBLIC_STORAGE_BUCKET_NAME,
            'public_url': settings.AWS_PUBLIC_STORAGE_DOMAIN
        }
    else:
        return {
            'access_key': settings.AWS_ACCESS_KEY_ID,
            'secret_key': settings.AWS_SECRET_ACCESS_KEY,
            'endpoint_url': settings.AWS_PRIVATE_ENDPOINT_URL,
            'bucket_name': settings.AWS_PRIVATE_STORAGE_BUCKET_NAME,
        }
