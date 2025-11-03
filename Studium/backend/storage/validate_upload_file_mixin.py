from rest_framework.exceptions import ValidationError
from storage.object_storage import S3Client
from studium_backend import settings
import logging

logger = logging.getLogger(__name__)


class ValidateUploadFileMixin:
    _TEMP_URL_PREFIX = 'temp_storage'
    _s3_client = None

    def __init__(self):
        self._user_id = None
        self._storage_type = getattr(self, "_storage_type", "private")

    def validate_files(self, files, user_id):
        if not user_id:
            raise ValidationError("User ID is required")

        self._user_id = user_id

        if not files:
            logger.warning("No files provided for validation")
            return

        for file in files:
            self._validate_single_file(file)

    def _validate_single_file(self, file):
        try:
            self._check_file_path(file)
            self._check_file_metadata(file)
        except Exception as e:
            logger.error(f"File validation failed: {e}", extra={"file": file, "user_id": self._user_id})
            raise ValidationError(f"File validation failed: {str(e)}")

    def _check_file_path(self, file):
        path = file.get('file_path')
        if not path:
            raise ValidationError("File path is required")

        expected_prefix = f"{self._TEMP_URL_PREFIX}/{self._user_id}/"
        if not path.startswith(expected_prefix):
            raise ValidationError(f"Invalid file path. Expected prefix: {expected_prefix}")

    def _check_file_metadata(self, file):
        path = file.get('file_path')

        if not self.s3_client.check_file_exists(path=path):
            raise ValidationError("File does not exist")

        try:
            metadata = self.s3_client.get_file_metadata(path=path)
            logger.debug(f"Retrieved metadata for file: {path}")
        except Exception as e:
            raise ValidationError(f"Failed to get file metadata: {str(e)}")

        validation_checks = [
            ('file_name', 'original_filename'),
            ('file_size', 'original_size'),
            ('file_type', 'original_type'),
            ('file_owner_id', 'file_owner_id')
        ]

        for file_field, metadata_field in validation_checks:
            file_value = file.get(file_field)
            metadata_value = metadata.get(metadata_field)

            if file_value != metadata_value:
                raise ValidationError(
                    f"Metadata mismatch for {file_field}. "
                    f"Expected: {file_value}, Got: {metadata_value}"
                )

    @property
    def s3_client(self):
        if self._s3_client is None:
            self._s3_client = self._create_s3_client()
        return self._s3_client

    def _create_s3_client(self):
        storage_config = self._get_storage_config()
        logger.info(f"Creating S3 client for storage type: {self._storage_type}")

        return S3Client(**storage_config)

    def _get_storage_config(self):
        if self._storage_type == 'public':
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
