import boto3
import logging
import os
from botocore.exceptions import ClientError
from botocore.client import Config
from django.conf import settings

logger = logging.getLogger('django')


class S3Client:
    def __init__(self, access_key: str, secret_key: str, endpoint_url: str, bucket_name: str, public_url: str = None):
        if not all([access_key, secret_key, endpoint_url, bucket_name]):
            raise ValueError("Все параметры конфигурации S3Client должны быть переданы явно!")

        self.bucket_name = bucket_name
        self.public_url = f'https://{public_url}' if public_url else None

        ssl_cert_path = os.path.expanduser('~/.selectels3/root.crt')
        verify_ssl = ssl_cert_path if os.path.exists(ssl_cert_path) else True

        try:
            self.s3_client = boto3.client(
                's3',
                region_name=settings.AWS_REGION_NAME,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                endpoint_url=endpoint_url,
                config=Config(s3={'addressing_style': 'virtual'}),##Включи если надо будет virtual_hosted ссылки на S3
                verify=verify_ssl
            )
        except Exception as e:
            logger.error(f"Ошибка подключения к S3: {e}")
            raise

    def upload_file(self, file_path: str, file):
        try:
            self.s3_client.put_object(Bucket=self.bucket_name, Key=file_path, Body=file)
            return True
        except Exception as e:
            print("Ошибка при загрузки файла в S3", e)
            logger.error(f"Ошибка загрузки файла {file_path}: {e}")
            return False

    def download_file(self, path: str):
        if not path or ".." in path or path.startswith("/"):
            logger.warning(f"Попытка доступа к запрещенному пути: {path}")
            raise ValueError("Неверный путь")

        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=path)
            file_content = response['Body'].read().decode('utf-8')
            return file_content
        except ClientError as e:
            print(f"[download_file] ClientError: {e}")
            logger.error(f"Ошибка скачивания файла {path}: {e}")
            return None

    def check_file_exists(self, path: str):
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=path)
            return True
        except ClientError:
            return False

    def delete_file(self, path: str):
        if not path or ".." in path or path.endswith("/"):
            logger.warning(f"Попытка удаления некорректного пути: {path}")
            return False

        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=path)
            return True
        except ClientError as e:
            logger.error(f"Ошибка удаления файла {path}: {e}")
            return False

    def copy_between_folders(self, old_path: str, new_path: str):
        if not old_path or not new_path:
            logger.warning("Ошибка копирования: пустой путь")
            return False

        try:
            copy_source = {'Bucket': self.bucket_name, 'Key': old_path}
            self.s3_client.copy_object(Bucket=self.bucket_name, CopySource=copy_source, Key=new_path)
            return True
        except ClientError as e:
            logger.error(f'Ошибка перемещения файла {old_path} -> {new_path}: {e}')
            return False

    def move_between_folders(self, old_path: str, new_path: str):
        try:
            self.copy_between_folders(old_path=old_path, new_path=new_path)
            self.delete_file(old_path)
            return True
        except ClientError as e:
            logger.error(f'Ошибка перемещения файла {old_path} -> {new_path}: {e}')
            return False

    def clear_temp_folder(self, user_id: int):
        prefix = f"temp_storage/{user_id}/"

        try:
            objects_to_delete = self.s3_client.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)
            if 'Contents' in objects_to_delete:
                delete_keys = {'Objects': [{'Key': obj['Key']} for obj in objects_to_delete['Contents']]}
                if delete_keys['Objects']:
                    self.s3_client.delete_objects(Bucket=self.bucket_name, Delete=delete_keys)
                    return True
            return False
        except ClientError as e:
            logger.error(f"Ошибка очистки временной папки {prefix}: {e}")
            return False

    def single_generate_temp_url(self, file_path: str):
        if not self.check_file_exists(file_path):
            logger.warning(f"Попытка создать ссылку на несуществующий файл: {file_path}")
            return None

        try:
            url = self.s3_client.generate_presigned_url(
                ClientMethod='get_object',
                Params={'Bucket': self.bucket_name, 'Key': file_path},
                ExpiresIn=300
            )
            return url
        except ClientError as e:
            logger.error(f"Ошибка генерации ссылки для {file_path}: {e}")
            return None

    def generate_temp_url(self, files: list):
        return [self.single_generate_temp_url(file['path']) for file in files if file.get('path')]

    def generate_permanent_url(self, object_key: str):
        if not object_key or not self.check_file_exists(object_key):
            logger.warning(f"Попытка получить публичный URL несуществующего файла: {object_key}")
            return None

        url = f"{self.public_url}/{object_key}" if self.public_url else None
        return url

    def generate_presigned_upload_url(self, file_meta_name: str, file_meta_size: str, file_meta_type: str,
                                      file_meta_user: int, file_path: str, content_type: str,
                                      expires_in: int = 600) -> str | None:
        try:
            presigned_url = self.s3_client.generate_presigned_url(
                ClientMethod='put_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': file_path,
                    'ContentType': content_type,
                    'Metadata': self._generate_file_metadata(file_meta_name, file_meta_size,
                                                             file_meta_type, file_meta_user)
                },
                ExpiresIn=expires_in
            )
            return presigned_url
        except ClientError as e:
            logger.error(f"Ошибка генерации presigned URL для загрузки {file_path}: {e}")
            return None

    def get_file_metadata(self, path: str):
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=path)
            return response.get('Metadata', {})
        except ClientError as e:
            logger.error(f"Ошибка получения метаданных для {path}: {e}")
            return {}

    @staticmethod
    def _generate_file_metadata(file_meta_name: str, file_meta_size: str,
                                file_meta_type: str, file_meta_user: int):
        Metadata = {
            'original_filename': file_meta_name,
            'original_size': file_meta_size,
            'original_type': file_meta_type,
            'file_owner_id': file_meta_user
        }

        return Metadata
