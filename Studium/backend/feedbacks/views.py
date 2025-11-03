import logging

from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework_simplejwt.authentication import JWTAuthentication

from studium_backend.exceptions import AppException
from studium_backend.decorators import catch_and_log_exceptions
from .serializers import *

from django.contrib.contenttypes.models import ContentType

from authentication.models import CustomUser
from ready_tasks.models import ReadyTask

from .models import Feedback

from .tasks import create_feedback

from django.core.paginator import Paginator

logger = logging.getLogger(__name__)


class FeedbackCreateAPIView(generics.CreateAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = FeedbackSerializer

    @catch_and_log_exceptions
    def create(self, request, *args, **kwargs):
        data = request.data
        evaluator = request.user

        object_id, reviewer, content_type, rating = self._prepare_for_create(data=data)

        if self._has_already_rated(evaluator.id, content_type, object_id):
            raise AppException(message='Эта работа уже оценена', status_code=status.HTTP_400_BAD_REQUEST)

        feedback_data = {
            "user": evaluator.id,
            "reviewer": reviewer.id,
            "content_type": content_type,
            "object_id": object_id,
            "rating": rating,
        }

        if "comment" in data:
            feedback_data["comment"] = data["comment"]

        serializer = self.get_serializer(data=feedback_data)

        if serializer.is_valid():
            create_feedback.delay(feedback_data=feedback_data)
            return Response({'message': 'Данные приняты, идет обработка.'}, status=status.HTTP_202_ACCEPTED)

        raise AppException(message='Данные не прошли проверку', status_code=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def _prepare_for_create(data):
        task = ReadyTask.objects.get(id=data["task_id"])
        reviewer = CustomUser.objects.get(id=task.owner.id)
        content_type = ContentType.objects.get_for_model(ReadyTask).id

        rating = round(float(data["rate"]), 2)
        rating = max(1, min(5, rating))

        return task.id, reviewer, content_type, rating

    @staticmethod
    def _has_already_rated(user_id, content_type_id, object_id):
        return Feedback.objects.filter(
            user=user_id,
            content_type=content_type_id,
            object_id=object_id
        ).exists()


class UserFeedbacksAPIView(generics.ListAPIView):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    permission_classes = (AllowAny,)

    @catch_and_log_exceptions
    def get(self, request, *args, **kwargs):

        pk = self.kwargs.get('pk')

        if not pk:
            raise AppException(message='Пользователь не найден', status_code=status.HTTP_400_BAD_REQUEST)

        page = int(request.query_params.get('page', 3))

        queryset = self.queryset.filter(reviewer=pk).order_by("-created_at")

        paginator = Paginator(queryset, 1)

        feedback_page = paginator.page(page)

        serializer = self.get_serializer(feedback_page, many=True)

        return Response({
            "feedback": serializer.data,
            "has_next": feedback_page.has_next(),
            "has_previous": feedback_page.has_previous()})


class ReadyTaskFeedbacksAPIView(generics.ListAPIView):
    serializer_class = FeedbackSerializer
    permission_classes = (AllowAny,)

    CONTENT_TYPE_MODEL = ReadyTask

    def get_queryset(self):
        pk = self.kwargs.get("pk")

        content_type = ContentType.objects.get_for_model(self.CONTENT_TYPE_MODEL)

        fixed_object = self.CONTENT_TYPE_MODEL.objects.order_by("id").first()
        if not fixed_object:
            return Feedback.objects.none()

        return Feedback.objects.filter(content_type=content_type, object_id=pk).order_by("-created_at")

    @catch_and_log_exceptions
    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")

        if not pk:
            raise AppException(message='Работа не найдена', status_code=status.HTTP_400_BAD_REQUEST)

        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 5))

        queryset = self.get_queryset()

        paginator = Paginator(queryset, page_size)

        feedback_page = paginator.page(page)

        serializer = self.get_serializer(feedback_page, many=True)

        return Response({
            "feedback": serializer.data,
            "has_next": feedback_page.has_next(),
            "has_previous": feedback_page.has_previous()})
