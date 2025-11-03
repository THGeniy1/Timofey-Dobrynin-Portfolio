import os
from io import BytesIO
from typing import Dict, Any, List

from django.core.files.base import ContentFile
from django.core.paginator import Paginator

from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from PIL import Image

from authentication.models import CustomUser
from storage.mixins import FileUploadMixin, PublicGetMixin

from studium_backend.decorators import catch_and_log_exceptions

from .serializers import UserSerializer, ShortInfoUserSerializer, PublicUserSerializer

# Constants
MAX_FILE_SIZE_MB = 2
ALLOWED_UPDATE_FIELDS = ['name', 'description', 'educations', 'gender', 'inn', 'is_foreign_citizen']
DEFAULT_PAGE_SIZE = 10
AVATAR_SIZE = (256, 256)
ALLOWED_IMAGE_FORMATS = ('JPEG', 'JPG', 'PNG')


class UserView(PublicGetMixin, generics.RetrieveAPIView):
    
    queryset = CustomUser.objects.all()
    serializer_class = PublicUserSerializer
    permission_classes = (AllowAny,)

    @catch_and_log_exceptions
    def retrieve(self, request, *args, **kwargs):
        user = self.get_object()
        user_data = self.get_serializer(user).data
        
        user_data['average_rating'] = round(user_data['average_rating'], 2)
        
        avatar = user_data.get('avatar')
        if avatar:
            user_data['avatar'] = self.handle_get_file(object_key=avatar)

        return Response(user_data, status=status.HTTP_200_OK)


class UserUpdateView(PublicGetMixin, generics.UpdateAPIView):
    serializer_class = UserSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def _extract_update_data(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        data = {
            field: request_data.get(field)
            for field in ALLOWED_UPDATE_FIELDS
            if field in request_data and request_data.get(field) is not None
        }

        if 'educations' in request_data:
            data['educations'] = self._clean_educations(request_data.get('educations', []))

        return data

    @staticmethod
    def _clean_educations(educations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        cleaned = []
        for edu in educations:
            if isinstance(edu, dict) and all(v if isinstance(v, str) else True for v in edu.values()):
                cleaned.append(edu)
        return cleaned

    @catch_and_log_exceptions
    def update(self, request, *args, **kwargs):
        user = request.user

        if user.client.is_banned:
            return Response({'detail': 'Пользователь заблокирован'}, status=423)

        data = self._extract_update_data(request.data)

        serializer = self.get_serializer(user, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        user_data = serializer.data

        if user_data.get('avatar'):
            user_data['avatar'] = self.handle_get_file(object_key=user_data['avatar'])

        return Response({'user_data': user_data}, status=status.HTTP_200_OK)


class UserUpdateAvatarView(FileUploadMixin, generics.UpdateAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    _storage_type = 'public'
    _upload_direction = 'users'

    @catch_and_log_exceptions
    def update(self, request, *args, **kwargs):
        user = self.request.user

        if user.client.is_banned:
            return Response({'detail': 'Пользователь заблокирован'}, status=423)

        avatar_file = request.FILES.get('file')

        if not avatar_file:
            raise ValidationError({"user_update_avatar": "Не передан файл аватара"})

        content_file = self._process_image(avatar_file)
        response = self.upload_file(user=user, file=content_file)

        if response.status_code != 200:
            return response

        file_path = response.data["file_path"]
        user.avatar = file_path
        user.save(update_fields=["avatar"])

        avatar_url = self.get_file_url(file_path=file_path)

        return Response({
            'message': 'Аватар успешно обновлен',
            'url': avatar_url
        }, status=status.HTTP_200_OK)

    @staticmethod
    def _process_image(avatar_file) -> ContentFile: 
        img = Image.open(avatar_file).resize(AVATAR_SIZE)

        format_type = img.format if img.format in ALLOWED_IMAGE_FORMATS else 'JPEG'
        
        if img.mode == 'RGBA' and format_type == 'JPEG':
            img = img.convert('RGB')

        content_type = 'image/png' if format_type == 'PNG' else 'image/jpeg'
        new_ext = '.png' if format_type == 'PNG' else '.jpg'

        base_name, _ = os.path.splitext(avatar_file.name)
        final_name = f"{base_name}{new_ext}"

        img_file = BytesIO()
        img.save(img_file, format=format_type)
        img_file.seek(0)

        content_file = ContentFile(img_file.read(), name=final_name)
        content_file.content_type = content_type

        return content_file


class UsersListAPIView(PublicGetMixin, generics.ListAPIView):
    
    serializer_class = ShortInfoUserSerializer
    permission_classes = (AllowAny,)

    @staticmethod
    def _get_filter_fields() -> Dict[str, str]:
        return {
            "id": "id",
            "username": "username__icontains",
            "email": "email__icontains",
            "city": "client__educations__city__icontains",
            "university": "client__educations__university__icontains",
            "faculty": "client__educations__faculty__icontains",
        }

    def _apply_filters(self, queryset, search_data: Dict[str, Any]):
        filter_fields = self._get_filter_fields()
        
        for field, lookup in filter_fields.items():
            if field in search_data and search_data[field]:
                queryset = queryset.filter(**{lookup: search_data[field]})
        
        return queryset

    def get_queryset(self):
        search_data = self.request.query_params
        queryset = CustomUser.objects.filter(client__isnull=False, client__is_banned=False)
        
        return self._apply_filters(queryset, search_data).order_by("-id")

    @staticmethod
    def _validate_pagination_params(page: int, page_size: int) -> bool:
        return page >= 1 and page_size > 0

    @catch_and_log_exceptions
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        total_count = queryset.count()

        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", DEFAULT_PAGE_SIZE))

        if not self._validate_pagination_params(page, page_size):
            raise ValidationError({"user_list_api": "Неверные данные пагинации"})

        paginator = Paginator(queryset, page_size)

        paginated_queryset = paginator.page(page)

        serializer = self.get_serializer(paginated_queryset, many=True)
        users_data = serializer.data

        for user_data in users_data:
            avatar = user_data.get('avatar')
            if avatar:
                user_data['avatar'] = self.handle_get_file(object_key=avatar)

        return Response({
            "total_count": total_count,
            "page_data": users_data,
            "has_next": paginated_queryset.has_next(),
            "has_previous": paginated_queryset.has_previous(),
        })

