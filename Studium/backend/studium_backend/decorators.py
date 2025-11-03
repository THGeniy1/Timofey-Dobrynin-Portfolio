from functools import wraps
import logging
import uuid
import traceback

from django.core.mail import mail_admins
from rest_framework.response import Response
from rest_framework import status
from .exceptions import AppException

logger = logging.getLogger(__name__)


def catch_and_log_exceptions(view_method):
    @wraps(view_method)
    def _wrapped_view(self, request, *args, **kwargs):
        try:
            return view_method(self, request, *args, **kwargs)

        except AppException as e:
            return Response({
                "error": e.message,
                "message": e.message,
                "code": e.code
            }, status=e.status_code)

        except Exception as e:
            view_name = f"{view_method.__module__}.{view_method.__name__}"
            error_id = str(uuid.uuid4())
            print(f"[DEBUG] Ошибка в {view_name}: {str(e)}")
            logger.exception(f"[{error_id}] Ошибка в {view_name}: {str(e)}")

            mail_admins(
                subject=f"[{error_id}] Непредусмотренная ошибка в {view_name}",
                message=f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}",
                fail_silently=True
            )
            
            return Response({
                "error": "Произошла внутренняя ошибка сервера. "
                         "Пожалуйста, попробуйте позже.",
                "message": "Произошла внутренняя ошибка сервера. Пожалуйста, попробуйте позже."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return _wrapped_view
