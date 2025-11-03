import os

from celery import shared_task
from django.db import transaction
from authentication.models import CustomUser
from notifications.decorators import notify_on_task_failure
from .models import Report, ReportComment, Files
from .serializers import ReportSerializer, ReportCommentSerializer, FilesSerializer

from storage.object_storage import S3Client
from studium_backend.settings import AWS_PRIVATE_STORAGE_BUCKET_NAME, AWS_PRIVATE_ENDPOINT_URL, \
    AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

upload_direction = "reports/"

keys_to_remove = ['id', 'is_recreate', 'update_id', 'is_removed']


@shared_task
@notify_on_task_failure(
    message="Не удалось создать жалобу",
    content="create_report_with_comment",
)
def create_report_with_comment(task_data: dict):
    comment_data = task_data.pop("comment_data", {})
    report_data = task_data.copy()

    user_id = report_data.get("user")
    reported_user = report_data.get("reported_user")
    content_type = report_data.get("content_type")
    object_id = report_data.get("object_id")

    files = comment_data.pop("files", [])
    comment_user_id = comment_data.pop("user_id", None)

    if comment_user_id is None:
        comment_user_id = user_id

    comment_user = CustomUser.objects.get(id=comment_user_id)

    with transaction.atomic():
        if content_type and object_id:
            exists = Report.objects.filter(
                user=user_id,
                content_type=content_type,
                object_id=object_id,
            ).exists()
            if exists:
                raise Exception("Вы уже оставляли жалобу")

        report_serializer_data = {
            'user': user_id,
            'reported_user': reported_user,
            'content_type': content_type,
            'object_id': object_id,
            'type': report_data.get("type", "report"),
        }
        
        report_serializer = ReportSerializer(data=report_serializer_data)
        if report_serializer.is_valid():
            report = report_serializer.save()
        else:
            raise Exception(f"Ошибка валидации Report: {report_serializer.errors}")

        comment_serializer_data = {
            'report': report.id,
            'user': comment_user.id,
            'comment': comment_data.get("comment", ""),
        }
        
        comment_serializer = ReportCommentSerializer(data=comment_serializer_data)
        if comment_serializer.is_valid():
            report_comment = comment_serializer.save()
        else:
            raise Exception(f"Ошибка валидации ReportComment: {comment_serializer.errors}")

        if files:
            handle_files(files, report_comment)

    return {"report_id": report.id, "comment_id": report_comment.id}


def handle_files(files, report_comment):
    if not files:
        return
        
    s3Client = S3Client(
        access_key=AWS_ACCESS_KEY_ID,
        secret_key=AWS_SECRET_ACCESS_KEY,
        endpoint_url=AWS_PRIVATE_ENDPOINT_URL,
        bucket_name=AWS_PRIVATE_STORAGE_BUCKET_NAME
    )

    files_to_create = []
    for file_data in files:
        if not s3Client.check_file_exists(file_data['path']):
            logger.warning(f"Файл {file_data['name']} не найден в S3")
            continue
            
        try:
            new_path = os.path.join(upload_direction, f"{report_comment.id}/{file_data['name']}")
            if s3Client.move_between_folders(old_path=file_data['path'], new_path=new_path):
                serializer_data = {
                    'comment': report_comment.id,
                    'name': file_data['name'],
                    'path': new_path
                }
                
                serializer = FilesSerializer(data=serializer_data)
                if not serializer.is_valid():
                    logger.error(f"Ошибка валидации файла {file_data.get('name', 'unknown')}: {serializer.errors}")
                    continue
                
                files_to_create.append(Files(
                    comment=report_comment,
                    name=serializer.validated_data['name'],
                    path=serializer.validated_data['path']
                ))
            else:
                logger.error(f"Не удалось переместить файл {file_data['name']}")
                
        except Exception as e:
            logger.error(f"Ошибка при обработке файла {file_data.get('name', 'unknown')}: {e}")

    if files_to_create:
        Files.objects.bulk_create(files_to_create)
        logger.info(f"Создано {len(files_to_create)} файлов для ReportComment {report_comment.id}")
