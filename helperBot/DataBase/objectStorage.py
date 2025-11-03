import aioboto3

import configparser

config = configparser.ConfigParser()

config.read(r'D:\pythonProject\helperBot\config.ini')

aws_access_key_id = config.get('OBJECT_STORAGE_DATA', 'aws_access_key_id')

aws_secret_access_key = config.get('OBJECT_STORAGE_DATA', 'aws_secret_access_key')


async def load_object(file_path: str, file_name: str, bucket_name: str):
    session = aioboto3.Session()

    async with session.client(service_name="s3",
                              endpoint_url="https://helper-backet.s3.storage.selcloud.ru",
                              aws_access_key_id=aws_access_key_id,
                              aws_secret_access_key=aws_secret_access_key) as client:

        await client.upload_file(file_path, bucket_name, file_name)


async def get_object(file_path: str, file_name: str, bucket_name: str):
    session = aioboto3.Session()

    async with session.client(service_name="s3",
                              endpoint_url="https://helper-backet.s3.storage.selcloud.ru",
                              aws_access_key_id=aws_access_key_id,
                              aws_secret_access_key=aws_secret_access_key) as client:

        await client.download_file(bucket_name, file_name, file_path)
