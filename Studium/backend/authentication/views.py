import logging
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.db import transaction

from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from rest_framework import status, generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.views import TokenRefreshView

from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.exceptions import TokenError

from studium_backend.decorators import catch_and_log_exceptions
from studium_backend.exceptions import AppException

from .serializers import *

from users.serializers import UserSerializer
from storage.mixins import PublicGetMixin, TempStorageClearMixin

logger = logging.getLogger(__name__)


class RegistrationOrTokenView(PublicGetMixin, TempStorageClearMixin, APIView):
    permission_classes = (AllowAny,)
    authentication_classes = [JWTAuthentication]

    @catch_and_log_exceptions
    @method_decorator(ratelimit(key='ip', rate='5/m', method=['POST'], block=True))
    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        password = request.data.get('password', '')

        if not email or not password:
            raise AppException(message='Логин и пароль обязательны', status_code=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(email=email)

            if not user.check_password(password):
                raise AppException(message='Неверный пароль', status_code=status.HTTP_401_UNAUTHORIZED)

            if not user.is_active:
                raise AppException(message='Профиль не активен', status_code=status.HTTP_401_UNAUTHORIZED)

            client = getattr(user, 'client', None)
            if client and client.is_banned:
                raise AppException(message='Профиль заблокирован', status_code=status.HTTP_423_LOCKED)

            return self.generate_tokens_response(request, user, status.HTTP_200_OK)

        except CustomUser.DoesNotExist:
            try:
                validate_password(password)
            except Exception as e:
                print("Ошибка в пароле", e)
                raise AppException(message='Слабый пароль', status_code=status.HTTP_400_BAD_REQUEST)

            serializer = RegistrationSerializer(data=request.data)

            if serializer.is_valid():
                user = serializer.save()
                logger.info(f"New user registered: {email}")
                return self.generate_tokens_response(request, user, status.HTTP_201_CREATED)

            raise AppException(message='Данные не прошли проверку', status_code=status.HTTP_400_BAD_REQUEST)

    def generate_tokens_response(self, request, user, status_code):
        access_token = AccessToken.for_user(user)
        refresh_token = RefreshToken.for_user(user)

        user_data = UserSerializer(user).data

        avatar = user_data.get('avatar')

        if avatar:
            try:
                user_data['avatar'] = self.handle_get_file(object_key=avatar)
            finally:
                pass

        self.clear_temp_storage(user_id=user_data.get('id'))

        response = Response(
            {
                'access': str(access_token),
                'user_data': user_data
            },
            status=status_code
        )

        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        response.set_cookie(
            key='refresh',
            value=str(refresh_token),
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax' if settings.DEBUG else 'Strict',
            max_age=7 * 24 * 60 * 60,  # 7 days
        )

        response.set_cookie(
            'csrftoken',
            get_token(request),
            secure=not settings.DEBUG,
            samesite='Lax' if settings.DEBUG else 'Strict',
            max_age=7 * 24 * 60 * 60  # 7 days
        )

        return response


class LogoutView(APIView):
    permission_classes = (AllowAny,)
    authentication_classes = [JWTAuthentication]

    @catch_and_log_exceptions
    def post(self, request):
        refresh_token = request.COOKIES.get("refresh")
        access_token = request.headers.get("Authorization", "").replace("Bearer ", "")
        user_id = request.user.id if request.user else None

        if refresh_token:
            token = RefreshToken(refresh_token)
            if user_id and token.get("user_id") != user_id:
                raise ValidationError({"refresh": ["Некорректный токен"]})

            token.blacklist()

        if access_token:
            token = AccessToken(access_token)
            if user_id and token.get("user_id") != user_id:
                raise ValidationError({"access": ["Некорректный токен"]})
            jti = token["jti"]
            outstanding = OutstandingToken.objects.filter(jti=jti).first()
            if outstanding:
                BlacklistedToken.objects.get_or_create(token=outstanding)

        response = Response({"message": "Выход выполнен успешно"}, status=status.HTTP_200_OK)

        response.set_cookie(
            key="refresh",
            value="",
            httponly=True,
            secure=not settings.DEBUG,
            samesite="Lax" if settings.DEBUG else "Strict",
            max_age=0,
        )
        response.set_cookie(
            "csrftoken",
            "",
            secure=not settings.DEBUG,
            samesite="Lax" if settings.DEBUG else "Strict",
            max_age=0,
        )

        response["X-Content-Type-Options"] = "nosniff"
        response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response["Pragma"] = "no-cache"

        return response


class CustomTokenRefreshView(TokenRefreshView):
    permission_classes = (AllowAny,)
    authentication_classes = [JWTAuthentication]
    serializer_class = CookieTokenRefreshSerializer

    @catch_and_log_exceptions
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh')

        if not refresh_token:
            return Response({"detail": "Refresh токен отсутствует"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            token = RefreshToken(refresh_token)
            jti = token.get('jti')

            if jti and BlacklistedToken.objects.filter(token__jti=jti).exists():
                return Response({"detail": "Токен недействителен"}, status=status.HTTP_401_UNAUTHORIZED)

            mutable = getattr(request.data, "_mutable", None)
            if mutable is not None:
                request.data._mutable = True
            request.data["refresh"] = refresh_token
            if mutable is not None:
                request.data._mutable = mutable

            return super().post(request, *args, **kwargs)

        except TokenError:
            return Response({"detail": "Refresh токен недействителен или истёк"}, status=status.HTTP_401_UNAUTHORIZED)

    def finalize_response(self, request, response, *args, **kwargs):
        return super().finalize_response(request, response, *args, **kwargs)


class MeView(PublicGetMixin, generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer
    authentication_classes = [JWTAuthentication]

    @catch_and_log_exceptions
    def get(self, request):
        user = request.user

        user_data = self.get_serializer(user).data

        avatar = user_data.get('avatar')
        if avatar:
            user_data['avatar'] = self.handle_get_file(object_key=avatar)

        return Response(user_data, status=status.HTTP_200_OK)


class PasswordResetAPIView(APIView):
    permission_classes = (AllowAny,)
    authentication_classes = []

    @catch_and_log_exceptions
    def post(self, request):
        token = request.data.get("token")
        password = request.data.get("password")

        if not token:
            raise ValidationError({"token": ["Отсутствует токен сброса"]})

        try:
            validate_password(password)
        except ValidationError as e:
            raise AppException(message=e.messages, status_code=status.HTTP_400_BAD_REQUEST)

        try:
            reset_request = AdminPasswordResetRequest.objects.select_related('client__user').get(token=token)
        except AdminPasswordResetRequest.DoesNotExist:
            raise ValidationError({"reset_request": ["Отсутствует запрос на сброс"]})

        if reset_request.is_used or reset_request.created_at + timezone.timedelta(hours=24) < timezone.now():
            raise ValidationError({"reset_request": ["Ссылка на сброс истекла"]})

        user = reset_request.client.user

        with transaction.atomic():
            user.set_password(password)
            user.save()

            reset_request.is_used = True
            reset_request.save()

            return Response({"success": True, "message": "Пароль успешно изменён"})
