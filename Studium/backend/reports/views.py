from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework_simplejwt.authentication import JWTAuthentication

from studium_backend.decorators import catch_and_log_exceptions
from studium_backend.exceptions import AppException
from .serializers import *

from django.contrib.contenttypes.models import ContentType

from ready_tasks.models import ReadyTask
from authentication.models import CustomUser

from .tasks import create_report_with_comment


class ReportCreateAPIView(generics.CreateAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ReportSerializer

    keys_to_remove = ["file_names", "file_sizes", "file_paths", "file_is_public"]

    @catch_and_log_exceptions
    def create(self, request, *args, **kwargs):
        print("\n=== Starting Report Creation ===")
        data = request.data
        print(f"Received request data: {data}")

        initiator = request.user
        print(f"Initiator user data: {initiator}")

        content_type, opponent, object_id, report_type = self._prepare_content_data(data=data)
        print(f"Content data prepared - content_type: {content_type}, opponent: {opponent}, object_id: {object_id}, report_type: {report_type}")

        upload_data = self._prepare_file_data(data)
        print(f"File data prepared: {upload_data}")

        task_data = {
            "user": initiator.id,
            "reported_user": opponent,
            "content_type": content_type,
            "object_id": object_id,
            "type": report_type
        }
        print(f"Prepared report data: {task_data}")

        serializer = self.get_serializer(data=task_data)
        print(f"Serializer validation result: {serializer.is_valid()}")

        if not serializer.is_valid():
            raise AppException(message='Данные не прошли проверку', status_code=status.HTTP_400_BAD_REQUEST)

        task_data['comment_data'] = {
            "comment": data["comment"],
            "user_id": initiator.id,
            "files": upload_data['files']
        }

        create_report_with_comment.delay(task_data=task_data)
        print("Report and comment creation task queued")
        return Response({'message': 'Спор создан'}, status=status.HTTP_202_ACCEPTED)

    @staticmethod
    def _prepare_file_data(data):
        print("\n=== Preparing File Data ===")
        file_names = data.getlist("file_names")
        file_paths = data.getlist("file_paths")
        print(f"File names: {file_names}")
        print(f"File paths: {file_paths}")

        if len(file_names) == len(file_paths):
            result = {
                'files': [
                    {'name': name, 'path': path}
                    for name, path in zip(file_names, file_paths)
                ]
            }
            print(f"Prepared file data: {result}")
            return result
        print("No files to process")
        return {'files': []}

    @staticmethod
    def _prepare_content_data(data):
        print("\n=== Preparing Content Data ===")
        object_type = data["object"]
        print(f"Object type: {object_type}")

        if object_type == "ready_task":
            object_id = int(data["object_id"])
            content = ReadyTask.objects.get(id=object_id)
            content_type_id = ContentType.objects.get_for_model(ReadyTask).id
            opponent = content.owner.id
            report_type = "report"
            print(f"Ready task data - object_id: {object_id}, opponent: {opponent}")

        elif object_type == "user":
            object_id = int(data["object_id"])
            content = CustomUser.objects.get(id=object_id)
            content_type_id = ContentType.objects.get_for_model(CustomUser).id
            opponent = content.id
            report_type = "report"
            print(f"User data - object_id: {object_id}, opponent: {opponent}")

        else:
            object_id = None
            content_type_id = None
            opponent = None
            report_type = data["category"]
            print(f"Other type data - report_type: {report_type}")

        return content_type_id, opponent, object_id, report_type


# class ReportCommentView(generics.ListCreateAPIView):
#     queryset = ReportComment.objects.all()
#     serializer_class = ReportCommentSerializer
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated]
#
#     def get_queryset(self):
#         complaint_id = self.kwargs['complaint_id']
#         return self.queryset.filter(complaint_id=complaint_id)
#
#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user)
#
#
# class ReportView(generics.RetrieveAPIView):
#     queryset = CustomUser.objects.all()
#     serializer_class = ReportSerializer
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated]
#
#     retrieve_fields = ["awaiting_response", "awaiting_from", "awaiting_since", "content_type", "object_id"]
#
#     def retrieve(self, request, *args, **kwargs):
#         try:
#             report = self.get_object()
#             report_data = self.get_serializer(report).data
#         except ReadyTask.DoesNotExist:
#             return Response({"error": "Спор не найден"}, status=404)
#
#         user = get_user_data(request.headers.get('Authorization'))
#
#         is_participant = user and (user.id == report_data.get('user') or user.id == report_data.get('reported_user'))
#
#         if not is_participant:
#             return Response("Не участник или не авторизован", status=status.HTTP_400_BAD_REQUEST)
#
#         if user.id == report_data.get('user'):
#             comments = report_data.comments.filter(user=user.id)
#         else:
#             comments = report_data.comments.filter(reported_user=user.id)
#
#         report_data = self.clear_fields(report_data)
#         report_data["comments"] = comments
#
#         return Response(report_data, status=status.HTTP_200_OK)
#
#     def clear_fields(self, report_data):
#         for field in self.retrieve_fields:
#             report_data.pop(field, None)
#         return report_data
