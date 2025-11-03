from celery import shared_task
from django.db.models import Avg
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

from authentication.models import CustomUser
from .models import Feedback
from .serializers import FeedbackSerializer

from notifications.decorators import notify_on_task_failure


@shared_task
@notify_on_task_failure(
    message="Ошибка при сохранении отзыва с помощью задачи",    
    content="create_feedback_celery",
)
def create_feedback(feedback_data):
    try:
        user = CustomUser.objects.get(id=feedback_data.pop("user"))
        reviewer = CustomUser.objects.get(id=feedback_data.pop("reviewer"))
    except ObjectDoesNotExist as e:
        raise Exception({"error": f"Пользователь не найден: {e}"})

    serializer_data = {
        "user": user.id,
        "reviewer": reviewer.id,
        "content_type": feedback_data["content_type"],
        "object_id": feedback_data.get("object_id"),
        "rating": feedback_data["rating"],
        "comment": feedback_data.get("comment")
    }

    try:
        with transaction.atomic():
            serializer = FeedbackSerializer(data=serializer_data)
            if serializer.is_valid():
                feedback = serializer.save()
            else:
                raise Exception({"error": f"Ошибка валидации: {serializer.errors}"})

            client = CustomUser.objects.select_for_update().get(id=reviewer.id).client

            reviews = Feedback.objects.filter(reviewer=reviewer)
            if reviews.exists():
                average_rating = reviews.aggregate(Avg('rating'))['rating__avg']
                client.average_rating = average_rating
                client.reviews_count = reviews.count()
                client.save()

        return feedback.id

    except Exception as e:
        raise Exception({"error": str(e)})
