from celery import shared_task
from django.conf import settings

from storage.object_storage import S3Client

from ready_tasks.serializers import FilesSerializer as ReadyFilesSerializer
from reports.serializers import FilesSerializer as ReportFilesSerializer


def get_s3_client():
    return S3Client(
        access_key=getattr(settings, "AWS_ACCESS_KEY_ID", None),
        secret_key=getattr(settings, "AWS_SECRET_ACCESS_KEY", None),
        endpoint_url=settings.AWS_PRIVATE_ENDPOINT_URL,
        bucket_name=settings.AWS_PRIVATE_STORAGE_BUCKET_NAME,
    )


def clean_file_data(file_data, fields_to_remove):
    for field in fields_to_remove:
        file_data.pop(field, None)


@shared_task
def generate_temp_url(data):
    user_id = data.get("user_id")
    s3_client = get_s3_client()

    serializers_map = {
        "ready_task": ReadyFilesSerializer,
        "report": ReportFilesSerializer,
    }

    serializer_class = serializers_map.get(data["object"])
    if not serializer_class:
        raise ValueError(f"Недопустимое значение 'object': {data['object']}")

    serializer = serializer_class(data["files"], many=True)
    files_data = serializer.data

    files_urls = s3_client.generate_temp_url(files_data)

    fields_to_remove = {
        "ready_task": {"id", "task_id", "path", "create_date"},
        "report": {"id", "path", "create_date"},
    }.get(data["object"], set())

    for file_index, file_data in enumerate(files_data):
        clean_file_data(file_data, fields_to_remove)
        file_data["url"] = files_urls[file_index]

    return {"user_id": user_id, "files": files_data}
