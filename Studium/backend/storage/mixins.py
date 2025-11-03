import math
import mimetypes
import os
import uuid
import zipfile
from io import BytesIO

from django.conf import settings
from django.http import Http404, StreamingHttpResponse
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from ready_tasks.models import ReadyTask
from reports.models import ReportComment
from rules.models import Rules
from refunds.models import Refund
from storage.object_storage import S3Client
from .validate_mixin import SimpleFileValidationMixin


class FileUploadMixin(SimpleFileValidationMixin):
    _upload_direction = ''

    MIN_UPLOAD_EXPIRY = 60
    MAX_UPLOAD_EXPIRY = 3600
    UPLOAD_SPEED_KBPS = 500
    BUFFER_TIME = 60

    @property
    def upload_direction(self):
        return self._upload_direction

    @property
    def _s3Client(self):
        return self._get_s3_client()

    def _calculate_upload_expiry(self, file_size):
        print("[FileUploadMixin._calculate_upload_expiry] Начало расчёта времени истечения для файла размером:", file_size)
        try:
            file_size_kb = file_size / 1024

            estimated_time = (file_size_kb / self.UPLOAD_SPEED_KBPS) + self.BUFFER_TIME

            expiry_time = max(self.MIN_UPLOAD_EXPIRY, min(estimated_time, self.MAX_UPLOAD_EXPIRY))

            print("[FileUploadMixin._calculate_upload_expiry] Расчёт завершён, время истечения:", expiry_time)
            return math.ceil(expiry_time / 60) * 60

        except Exception as e:
            print("[FileUploadMixin._calculate_upload_expiry] Ошибка при расчёте:", e)
            return self.MIN_UPLOAD_EXPIRY

    def generate_file_upload_url(self, file_meta):
        print("[FileUploadMixin.generate_file_upload_url] Генерация presigned URL для:", file_meta)
        if not file_meta:
            print("[FileUploadMixin.generate_file_upload_url] Нет данных для file_meta")
            return Response(
                {"error": "Данных нет"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            validate_meta = self.validate_file_metadata(
                name=file_meta['name'],
                size=file_meta['size'],
                mime_type=file_meta['type']
            )

            file_extension = os.path.splitext(validate_meta['name'])[-1].lower()
            file_name = f"{uuid.uuid4()}{file_extension}"
            file_path = f"{self.upload_direction}/{file_meta['user'].id}/{file_name}"

            expires_in = self._calculate_upload_expiry(validate_meta['size'])

            upload_url = self._s3Client.generate_presigned_upload_url(
                file_meta_name=file_meta['name'],
                file_meta_size=file_meta['size'],
                file_meta_type=file_meta['type'],
                file_meta_user=file_meta['user'],
                file_path=file_meta['name'],
                content_type=validate_meta["type"],
                expires_in=expires_in
            )
            if not upload_url:
                raise RuntimeError("Не удалось сгенерировать presigned URL для загрузки")

            return Response(
                {
                    "status": "success",
                    "message": "Presigned URL сгенерирован. Используйте его для загрузки файла.",
                    "file_path": file_path,
                    "upload_url": upload_url,
                    "expires_in": expires_in
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": f"Ошибка при генерации ссылки для загрузки: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def upload_file(self, user, file):
        print(f"[FileUploadMixin.upload_file] Загрузка файла для пользователя {user}")
        try:
            validate_file = self.validate_upload_file(file)

            file_extension = os.path.splitext(validate_file.name)[-1].lower()
            file_name = f"{uuid.uuid4()}{file_extension}"
            file_path = f"{self.upload_direction}/{user.id}/{file_name}"

            self._s3Client.upload_file(file_path=file_path, file=validate_file)

            url = self.get_file_url(file_path)

            return Response(
                {
                    "status": "success",
                    "url": url,
                    "file_path": file_path
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": f"Ошибка при загрузки файла: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_file_url(self, file_path):
        print(f"[FileUploadMixin.get_file_url] Получение url для файла: {file_path}")
        url = self._s3Client.generate_permanent_url(object_key=file_path)

        if not url:
            print(f"[FileUploadMixin.get_file_url] Ошибка получения ссылки на файл: {file_path}")
            raise RuntimeError(f"Ошибка получения ссылки на файл: {file_path}")
        print(f"[FileUploadMixin.get_file_url] Получен url: {url}")
        return url

    def _get_s3_client(self):
        storage_type = getattr(self, "_storage_type", "private")
        print(f"[FileUploadMixin._get_s3_client] Выбор клиента S3 для типа: {storage_type}")

        if storage_type == 'public':
            return S3Client(
                access_key=settings.AWS_ACCESS_KEY_ID,
                secret_key=settings.AWS_SECRET_ACCESS_KEY,
                endpoint_url=settings.AWS_PUBLIC_ENDPOINT_URL,
                bucket_name=settings.AWS_PUBLIC_STORAGE_BUCKET_NAME,
                public_url=settings.AWS_PUBLIC_STORAGE_DOMAIN
            )
        else:
            return S3Client(
                access_key=settings.AWS_ACCESS_KEY_ID,
                secret_key=settings.AWS_SECRET_ACCESS_KEY,
                endpoint_url=settings.AWS_PRIVATE_ENDPOINT_URL,
                bucket_name=settings.AWS_PRIVATE_STORAGE_BUCKET_NAME,
            )


class PublicGetMixin:
    _ALLOWED_FILE_EXTENSIONS = ['.jpg', '.jpeg', '.png']
    _upload_direction = 'public/'

    @property
    def allowed_file_extensions(self):
        return self._ALLOWED_FILE_EXTENSIONS

    @property
    def upload_direction(self):
        return self._upload_direction

    @property
    def _s3Client(self):
        return self._get_s3_client()

    def handle_get_file(self, object_key: str) -> str:
        print(f"[PublicGetMixin.handle_get_file] Получение файла по ключу: {object_key}")
        if not object_key:
            print("[PublicGetMixin.handle_get_file] object_key пустой")
            return None

        try:
            url = self._s3Client.generate_permanent_url(object_key=object_key)
            print(f"[PublicGetMixin.handle_get_file] Получен url: {url}")
            return url if url else None
        except Exception as e:
            print(f"[PublicGetMixin.handle_get_file] Ошибка: {e}")
            return None

    @staticmethod
    def _get_s3_client():
        return S3Client(
            access_key=settings.AWS_ACCESS_KEY_ID,
            secret_key=settings.AWS_SECRET_ACCESS_KEY,
            endpoint_url=settings.AWS_PUBLIC_ENDPOINT_URL,
            bucket_name=settings.AWS_PUBLIC_STORAGE_BUCKET_NAME,
            public_url=settings.AWS_PUBLIC_STORAGE_DOMAIN
        )


class PrivateUploadMixin:#Чисто админская для загрузки JSON
    _ALLOWED_FILE_EXTENSIONS = ['.json']

    @property
    def allowed_file_extensions(self):
        return self._ALLOWED_FILE_EXTENSIONS

    @property
    def _s3Client(self):
        return self._get_s3_client()

    def upload_file(self, path: str, file) -> str:
        print(f"[PrivateUploadMixin.upload_file] Загрузка файла по пути: {path}")
        if not path:
            print("[PrivateUploadMixin.upload_file] Пустой путь к файлу")
            raise ValueError("Пустой путь к файлу")

        try:
            result = self._s3Client.upload_file(file_path=path, file=file)
            print(f"[PrivateUploadMixin.upload_file] Результат загрузки: {result}")
            return result
        except Exception as e:
            print(f"[PrivateUploadMixin.upload_file] Ошибка загрузки файла: {e}")
            raise Exception(f"Ошибка загрузки файла: {str(e)}")

    @staticmethod
    def _get_s3_client():
        return S3Client(
            access_key=settings.AWS_ACCESS_KEY_ID,
            secret_key=settings.AWS_SECRET_ACCESS_KEY,
            endpoint_url=settings.AWS_PRIVATE_ENDPOINT_URL,
            bucket_name=settings.AWS_PRIVATE_STORAGE_BUCKET_NAME,
        )


class PrivateGetMixin:
    @property
    def _s3Client(self):
        return self._get_s3_client()

    def download_file(self, path: str) -> str:
        if not path:
            print("[PrivateGetMixin.download_file] Пустой путь к файлу")
            raise ValueError("Пустой путь к файлу")

        print(f"[PrivateGetMixin.download_file] Скачивание файла по пути: {path}")
        try:
            result = self._s3Client.download_file(path=path)
            print(f"[PrivateGetMixin.download_file] Результат скачивания: {result is not None}")
            return result
        except Exception as e:
            print(f"[PrivateGetMixin.download_file] Ошибка при скачивании файла: {e}")
            raise Exception(f"Ошибка при скачивании файла: {str(e)}")

    @staticmethod
    def _get_s3_client():
        return S3Client(
            access_key=settings.AWS_ACCESS_KEY_ID,
            secret_key=settings.AWS_SECRET_ACCESS_KEY,
            endpoint_url=settings.AWS_PRIVATE_ENDPOINT_URL,
            bucket_name=settings.AWS_PRIVATE_STORAGE_BUCKET_NAME,
        )


class ArchiveDownloadMixin:
    @property
    def _s3Client(self):
        return self._get_s3_client()

    def stream_archive(self, obj_type, pk):
        print(f"[ArchiveDownloadMixin.stream_archive] Архивация файлов для типа: {obj_type}, pk: {pk}")
        if obj_type == 'ready_task':
            obj = get_object_or_404(ReadyTask, pk=pk)
            archive_filename = f"ready_task_{obj.id}_archive.zip"
        elif obj_type == 'report_comment':
            obj = get_object_or_404(ReportComment, pk=pk)
            archive_filename = f"report_comment_{obj.id}_archive.zip"
        elif obj_type == 'refund':
            obj = get_object_or_404(Refund, pk=pk)
            archive_filename = f"refund_{obj.id}_archive.zip"
        else:
            print("[ArchiveDownloadMixin.stream_archive] Неверный тип объекта")
            raise Http404("Неверный тип объекта")

        files = obj.files.all()

        if not files.exists():
            print("[ArchiveDownloadMixin.stream_archive] Нет файлов для архивации")
            raise Http404("Нет файлов для архивации")

        def zip_generator():
            with BytesIO() as tmp_buffer:
                with zipfile.ZipFile(tmp_buffer, mode='w', compression=zipfile.ZIP_DEFLATED) as archive:
                    for file in files:
                        s3_path = file.path
                        try:
                            file_content = self._s3Client.s3_client.get_object(
                                Bucket=self._s3Client.bucket_name,
                                Key=s3_path
                            )['Body'].read()
                            archive.writestr(file.name, file_content)
                            print(f"[ArchiveDownloadMixin.stream_archive.zip_generator] Добавлен файл {file.name} в архив")
                        except Exception as e:
                            print("[ArchiveDownloadMixin.stream_archive.zip_generator] Ошибка при добавлении файла в архив:", e)

                tmp_buffer.seek(0)
                print("[ArchiveDownloadMixin.stream_archive.zip_generator] Архив готов к отправке")
                yield from tmp_buffer

        response = StreamingHttpResponse(zip_generator(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename={archive_filename}'
        print(f"[ArchiveDownloadMixin.stream_archive] Архив отправлен: {archive_filename}")
        return response

    @staticmethod
    def _get_s3_client():
        return S3Client(
            access_key=settings.AWS_ACCESS_KEY_ID,
            secret_key=settings.AWS_SECRET_ACCESS_KEY,
            endpoint_url=settings.AWS_PRIVATE_ENDPOINT_URL,
            bucket_name=settings.AWS_PRIVATE_STORAGE_BUCKET_NAME,
        )


class PublicFileDownloadMixin:

    @property
    def _s3Client(self):
        return self._get_s3_client()

    @staticmethod
    def _get_s3_client():
        return S3Client(
            access_key=settings.AWS_ACCESS_KEY_ID,
            secret_key=settings.AWS_SECRET_ACCESS_KEY,
            endpoint_url=settings.AWS_PUBLIC_ENDPOINT_URL,
            bucket_name=settings.AWS_PUBLIC_STORAGE_BUCKET_NAME,
        )

    def download_public_file(self, obj_type, pk):
        print(f"[PublicFileDownloadMixin.download_public_file] Скачивание публичного файла для типа: {obj_type}, pk: {pk}")
        if obj_type == 'rules':
            obj = get_object_or_404(Rules, pk=pk)
        else:
            print("[PublicFileDownloadMixin.download_public_file] Неверный тип объекта")
            raise Http404("Неверный тип объекта")

        try:
            s3_object = self._s3Client.s3_client.get_object(
                Bucket=self._s3Client.bucket_name,
                Key=obj.path
            )
            file_content = s3_object['Body'].read()

            file_name = os.path.basename(obj.path)
            content_type, _ = mimetypes.guess_type(file_name)
            if content_type is None:
                content_type = 'application/octet-stream'

        except Exception as e:
            print("[PublicFileDownloadMixin.download_public_file] Ошибка при скачивании файла из публичного S3:", e)
            raise Http404("Ошибка при скачивании файла")

        response = StreamingHttpResponse(BytesIO(file_content), content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'
        print(f"[PublicFileDownloadMixin.download_public_file] Файл отправлен: {file_name}")
        return response


class TempStorageClearMixin:
    @property
    def _s3Client(self):
        return self._get_s3_client()

    def clear_temp_storage(self, user_id: int):
        print(f"[TempStorageClearMixin.clear_temp_storage] Очистка временного хранилища для пользователя: {user_id}")
        if not user_id:
            print("[TempStorageClearMixin.clear_temp_storage] Нет ID пользователя")
            raise ValueError("Нет ID пользователя")

        self._s3Client.clear_temp_folder(user_id=user_id)
        print(f"[TempStorageClearMixin.clear_temp_storage] Временное хранилище очищено для пользователя: {user_id}")

    @staticmethod
    def _get_s3_client():
        return S3Client(
            access_key=settings.AWS_ACCESS_KEY_ID,
            secret_key=settings.AWS_SECRET_ACCESS_KEY,
            endpoint_url=settings.AWS_PRIVATE_ENDPOINT_URL,
            bucket_name=settings.AWS_PRIVATE_STORAGE_BUCKET_NAME,
        )
