from django.test import TestCase
from unittest.mock import patch
from .object_storage import S3Client


class S3ClientTests(TestCase):
    def test_init_requires_params(self):
        with self.assertRaises(ValueError):
            S3Client(access_key="", secret_key="", endpoint_url="", bucket_name="")

    @patch("storage.object_storage.boto3.client")
    def test_generate_permanent_url_none_when_no_file(self, mock_client):
        client = S3Client("a", "b", "http://example.com", "bucket", "http://public")
        with patch.object(client, "check_file_exists", return_value=False):
            self.assertIsNone(client.generate_permanent_url("nofile")) 