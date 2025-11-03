from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from .utils import create_failure_notification
import logging

logger = logging.getLogger(__name__)


def notify_on_api_failure(message="Произошла ошибка", content=None,
                          response_status=status.HTTP_400_BAD_REQUEST):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(self, *args, **kwargs):
            request = getattr(self, 'request', None)
            user = getattr(request, 'user', None)

            try:
                return view_func(self, *args, **kwargs)
            except Exception as e:
                logger.exception(f"Ошибка в {view_func.__name__}: {e}")

                if user and user.is_authenticated:
                    try:
                        create_failure_notification(
                            user=user,
                            failure_message=e,
                            message=message,
                            content=content or {},
                        )
                    except Exception as notify_err:
                        logger.error(f"Ошибка при создании уведомления: {notify_err}")

                return Response({'detail': message}, status=response_status)
        return _wrapped_view
    return decorator


def notify_on_task_failure(message="Ошибка при выполнении задачи", content=None):
    def decorator(task_func):
        @wraps(task_func)
        def wrapper(*args, **kwargs):
            feedback_data = kwargs.get("task_data") or (args[0] if args else {})
            user_id = feedback_data.get("user") if isinstance(feedback_data, dict) else None

            try:
                result = task_func(*args, **kwargs)
                return result

            except Exception as e:
                logger.exception(f"Ошибка в Celery задаче {task_func.__name__}: {e}")

                try:
                    if user_id:
                        from authentication.models import CustomUser
                        user = CustomUser.objects.get(id=user_id)

                        create_failure_notification(
                            user=user,
                            failure_message=e,
                            message=message,
                            content=content or {},
                        )

                except Exception as notify_err:
                    logger.error(f"Ошибка при создании уведомления в Celery: {notify_err}")

                raise
        return wrapper
    return decorator

