from django.http import Http404
from rest_framework import status

from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from rest_framework.views import APIView
from celery.result import AsyncResult

from studium_backend.decorators import catch_and_log_exceptions
from studium_backend.exceptions import AppException

from .tasks import generate_temp_url
from .mixins import FileUploadMixin, ArchiveDownloadMixin, PublicFileDownloadMixin

from ready_tasks.models import ReadyTask
from payments.models import PurchasedReadyTask
from reports.models import ReportComment


class TempStorageUploadFileView(FileUploadMixin, APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    upload_direction = 'temp_storage'

    def __init__(self, **kwargs):
        super().__init__(kwargs)
        self._storage_type = None

    @staticmethod
    def _determine_storage_type(purpose=None):
        if purpose == 'chat':
            return 'public'
        elif purpose == 'task':
            return 'private'
        else:
            return 'private'

    @catch_and_log_exceptions
    def post(self, request):
        user = request.user

        required_fields = ['name', 'size', 'type']
        missing_fields = [field for field in required_fields if field not in request.data]

        if missing_fields:
            raise ValidationError({
                "temp_storage_upload_file": f"Отсутствуют обязательные поля: {', '.join(missing_fields)}"})

        storage_type = self._determine_storage_type(request.data.get('purpose'))

        self._storage_type = storage_type

        file_meta = {
            'name': request.data['name'],
            'size': request.data['size'],
            'type': request.data['type'],
            'user': user
        }

        return self.generate_file_upload_url(file_meta=file_meta)


class StartUpdateFileTemporaryLinksView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @catch_and_log_exceptions
    def post(self, request):
        source_type = request.data.get("source_type")
        object_id = request.data.get("object_id")

        if not source_type or not object_id:
            raise ValidationError({
                "start_upload_file_temp_links": "source_type или object_id не передан"})

        user = request.user

        if source_type == "ready_task":
            task_id = self._update_ready_task_links(user, object_id)
        elif source_type == "comment":
            task_id = self._update_comment_links(user, object_id)
        else:
            raise ValidationError({
                "start_upload_file_temp_links": "Некорректный source_type"})

        if task_id is None:
            raise ValidationError({
                "start_upload_file_temp_links": "task_id не найден"})

        return Response({"task_id": task_id}, status=200)

    @staticmethod
    def _update_ready_task_links(user, work_id):
        task = ReadyTask.objects.get(id=work_id)

        bought_tasks = PurchasedReadyTask.objects.filter(buyer=user.id).values_list("task_id", flat=True)

        if user == task.owner or work_id in bought_tasks:
            files = task.files.all()
        else:
            files = task.files.filter(is_public=True)

        file_ids = list(files.values_list("id", flat=True))

        if not file_ids:
            return None

        celery_task = generate_temp_url.delay({"user_id": user.id, "object": "ready_task", "files": file_ids})

        return celery_task.id

    @staticmethod
    def _update_comment_links(user, comment_id):
        comment = ReportComment.objects.get(id=comment_id)

        report = comment.report
        if user == report.initiator or user == report.opponent:
            files = comment.files.all()
            file_ids = list(files.values_list("id", flat=True))

            if not file_ids:
                return None

            celery_task = generate_temp_url.delay({"user_id": user.id, "object": "report", "files": file_ids})

            return celery_task.id
        return None


class CeleryUpdateLinksStatusView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @catch_and_log_exceptions
    def get(self, request):
        user = request.user

        task = AsyncResult(request.query_params.get("task_id"))

        if task.state == "PENDING":
            raise AppException(message='Задача в процессе обработки', status_code=status.HTTP_202_ACCEPTED)

        if task.state == "SUCCESS":
            task_result = task.result

            if task_result.get("user_id") != user.id:
                raise ValidationError({
                    "celery_update_links":
                        f"Нет доступа к этой задаче: id владельца {task_result.get('user_id')} id обратившегося {user.id}"})

            return Response({"status": "success", "files": task_result.get("files", [])}, status=200)

        if task.state == "FAILURE":
            raise ValidationError({
                "celery_update_links": f"Не удалось обновить ссылки: {str(task.result)}"})


class ArchiveDownloadView(APIView, ArchiveDownloadMixin):
    permission_classes = (IsAdminUser,)

    @catch_and_log_exceptions
    def get(self, request, pk):
        obj_type = request.query_params.get('type')
        print("OBJECT TYPE", obj_type, "PK", pk)
        if obj_type not in ('ready_task', 'report_comment', 'refund'):
            raise Http404("Тип объекта не указан или недопустим")

        return self.stream_archive(obj_type, pk)


class PublicFileDownloadView(APIView, PublicFileDownloadMixin):
    permission_classes = (IsAdminUser,)

    @catch_and_log_exceptions
    def get(self, request, pk):
        obj_type = request.query_params.get('type')
        return self.download_public_file(obj_type, pk)
