from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.views import APIView

from studium_backend.decorators import catch_and_log_exceptions
from studium_backend.exceptions import AppException
from .models import JsonFile
from .json_service import JsonService


class JsonHintAPIView(APIView):
    permission_classes = (AllowAny,)
    json_service = JsonService()

    @catch_and_log_exceptions
    def get(self, request, file_name):
        """Получить подсказки из кеша или S3, если запись о файле есть в БД."""
        if not JsonFile.objects.filter(name=file_name).exists():
            raise AppException(message='Файл не найден', status_code=status.HTTP_400_BAD_REQUEST)

        hints = self.json_service.get_json(file_name)
        return Response({"jsons": hints})


class JsonMainAPIView(APIView):
    permission_classes = (AllowAny,)
    json_service = JsonService()

    FIXED_FILES = ["categories.json", "degree_level.json", "sorting.json", "withdraw_bank_data.json", 
    "place_study.json", "types.json", "types_conflict.json"]

    @catch_and_log_exceptions
    def get(self, request):
        json_files = {}

        for file_name in self.FIXED_FILES:

            if not JsonFile.objects.filter(name=file_name).exists():
                print("ЗАПИСЬ О JSON ФАЙЛЕ НЕ НАЙДЕНА")
                raise AppException(message='Файл не найден', status_code=status.HTTP_400_BAD_REQUEST)

            json_files[file_name] = self.json_service.get_json(file_name)

        return Response({"jsons": json_files})


class RefreshJsonAPIView(APIView):
    permission_classes = [IsAdminUser]
    json_service = JsonService()

    @catch_and_log_exceptions
    def post(self, request, file_name):
        """Принудительное обновление кеша, если запись о файле есть в БД."""

        if not JsonFile.objects.filter(name=file_name).exists():
            raise AppException(message='Файл не найден', status_code=status.HTTP_400_BAD_REQUEST)

        result = self.json_service.refresh_json(file_name)
        return Response(result)
