import json

from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework_simplejwt.authentication import JWTAuthentication

from studium_backend.decorators import catch_and_log_exceptions
from studium_backend.exceptions import AppException

from .serializers import *
from .tasks import create_ready_task_with_files
from payments.models import PurchasedReadyTask

from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q
from storage.object_storage import S3Client
from studium_backend.settings import AWS_PRIVATE_STORAGE_BUCKET_NAME, AWS_PRIVATE_ENDPOINT_URL, \
    AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY


class ReadyTaskCreateAPIView(generics.CreateAPIView):
    serializer_class = ReadyTaskSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    keys_to_remove = ["education", "file_names", "file_sizes", "file_paths", "file_is_public"]

    @catch_and_log_exceptions
    def create(self, request, *args, **kwargs):
        user = request.user

        if user.client.is_banned:
            return Response({'detail': 'Пользователь заблокирован'}, status=423)

        data = request.data

        is_foreign = bool(getattr(user.client, 'is_foreign_citizen', False))
        has_inn = bool(getattr(user.client, 'has_inn', False))
        if not (is_foreign ^ has_inn):
            raise AppException(
                message='Введите ИНН или отметьте что вы иностранец',
                status_code=status.HTTP_400_BAD_REQUEST
            )

        is_recreate = data.get("is_recreate")

        if not is_recreate:
            self._check_free_slots(user=user)

        file_data = self._prepare_file_data(data)

        upload_data = self._prepare_main_data(data=data, user=user)

        upload_data = upload_data | file_data

        self._add_other_data(data, upload_data)

        self._validate_task_data(upload_data)

        return self._handle_task_creation(upload_data)

    @staticmethod
    def _check_free_slots(user):
        slots = getattr(user.client, "free_slots", 0) or 0
        if slots <= 0:
            raise AppException(message='Недостаточно слотов для размещения', status_code=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def _get_user_education(user, data):
        try:
            education_index = int(data.get("education"))
            return user.client.educations.all()[education_index]
        except (IndexError, ValueError):
            raise ValidationError({"create_ready_task_get_user_education": "Неверно указано образование"})

    @staticmethod
    def _prepare_file_data(data):
        file_names = data.getlist("file_names", [])
        file_sizes = data.getlist("file_sizes", [])
        file_paths = data.getlist("file_paths", [])
        file_is_public = data.getlist("file_is_public", [])

        if not (len(file_names) == len(file_sizes) == len(file_is_public) == len(file_paths)):
            raise ValidationError({"create_ready_task_prepare_file_data": "Несоответствие данных о файлах"})

        files = []
        for is_public, name, path, size in zip(file_is_public, file_names, file_paths, file_sizes):
            try:
                files.append({
                    'name': name,
                    'size': int(size),
                    'path': path,
                    'is_public': is_public.lower() == 'true'
                })
            except (ValueError, AttributeError):
                continue

        return {'files': files}

    def _prepare_main_data(self, data: dict, user):
        is_recreate = data.get("is_recreate")
        if isinstance(is_recreate, str):
            is_recreate = is_recreate.strip().lower() == 'true'
        elif isinstance(is_recreate, list) and len(is_recreate) > 0:
            is_recreate = is_recreate[0].strip().lower() == 'true'
        else:
            is_recreate = bool(is_recreate)
        
        print("RECREATE DATA", data)
        if is_recreate:
            education = data.get('education')
            if isinstance(education, str):
                try:
                    education = json.loads(education)
                except json.JSONDecodeError:
                    education = None
        else:
            education = self._get_user_education(user, data)

        city = education.get("city") if isinstance(education, dict) else getattr(education, "city", None)
        university = education.get("university") if isinstance(education, dict) else getattr(education,
                                                                                             "university", None)
        faculty = education.get("faculty") if isinstance(education, dict) else getattr(education, "faculty", None)
        direction = education.get("direction") if isinstance(education, dict) else getattr(education, "direction",
                                                                                           None)
        level = education.get("level") if isinstance(education, dict) else getattr(education, "level", None)

        required_fields = ["city", "university", "faculty", "direction", "level"]

        for field in required_fields:
            if not locals().get(field):
                raise ValidationError({"create_ready_task_prepare_main_data": f"Нет требуемого поля {field}"})

        upload_data = {
            "user": user.id,
            "city": city,
            "university": university,
            "faculty": faculty,
            "direction": direction,
            "level": level
        }

        return upload_data

    @staticmethod
    def _validate_task_data(data):
        required_fields = ["name", "type", "discipline", "description", "tutor"]
        for field in required_fields:
            if not data.get(field):
                raise AppException(message='Не все обязательные поля заполнены',
                                   status_code=status.HTTP_400_BAD_REQUEST)

        if data.get('price', 0) <= 0:
            raise AppException(message='Цена покупки должна быть положительной',
                               status_code=status.HTTP_400_BAD_REQUEST)

    def _add_other_data(self, data, upload_data):
        for key in data:
            if data[key] and key not in self.keys_to_remove:
                if key == "id":
                    upload_data[key] = abs(int(data[key]))
                elif key in ["score", "price"]:
                    upload_data[key] = abs(float(data[key]))
                elif key == "is_recreate":
                    upload_data[key] = data[key].strip().lower() == 'true'
                else:
                    upload_data[key] = data[key]

    def _handle_task_creation(self, upload_data):
        serializer = self.get_serializer(data=upload_data)
        if serializer.is_valid():
            create_ready_task_with_files.delay(task_data=upload_data)
            return Response({'message': 'Данные приняты, идет обработка.'}, status=status.HTTP_202_ACCEPTED)

        raise AppException(message='Данные не прошли проверку', status_code=status.HTTP_400_BAD_REQUEST)


class ReadyTaskListAPIView(generics.ListAPIView):
    serializer_class = ShortInfoReadyTaskSerializer
    permission_classes = (AllowAny,)

    SORT_MAP = {
        "По популярности": "-views",
        "По новизне": "-id",
        "По цене (сначала дешевые)": "price",
        "По цене (сначала дорогие)": "-price",
        "По оценке": "-score",
        "По алфавиту (А-Я)": "name",
        "По алфавиту (Я-А)": "-name",
        "По дате добавления": "-create_date",
    }

    SEARCH_FIELDS = {
        "icontains": ["name", "discipline", "tutor", "city",
                      "university", "faculty", "direction", "level"],
        "exact": ["type", "owner_id"],
    }

    def get_queryset(self):
        queryset = ReadyTask.objects.filter(status="active").select_related("owner")
        search_data = self.request.query_params

        sort_value = search_data.get("sort") if isinstance(search_data, dict) else None
        if sort_value in self.SORT_MAP:
            queryset = queryset.order_by(self.SORT_MAP[sort_value])
        else:
            queryset = queryset.order_by("-views")

        if isinstance(search_data, dict):
            for lookup_type, fields in self.SEARCH_FIELDS.items():
                for field in fields:
                    value = search_data.get(field)
                    if value:
                        queryset = queryset.filter(**{f"{field}__{lookup_type}": value})

        return queryset

    @catch_and_log_exceptions
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        total_count = queryset.count()

        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 10))

        paginator = Paginator(queryset, page_size)
        paginated_queryset = paginator.page(page)

        serializer = self.get_serializer(paginated_queryset, many=True)

        return Response({
            "total_count": total_count,
            "page_data": serializer.data,
            "has_next": paginated_queryset.has_next(),
            "has_previous": paginated_queryset.has_previous(),
        })


class ReadyTaskSoldListAPIView(generics.ListAPIView):
    serializer_class = ShortInfoReadyTaskSerializer
    permission_classes = (AllowAny,)

    SORT_MAP = {
        "По популярности": "-views",
        "По новизне": "-id",
        "По цене (сначала дешевые)": "price",
        "По цене (сначала дорогие)": "-price",
        "По оценке": "-score",
        "По алфавиту (А-Я)": "name",
        "По алфавиту (Я-А)": "-name",
        "По дате добавления": "-create_date",
    }

    SEARCH_FIELDS = {
        "icontains": ["id", "name", "discipline", "tutor", "city",
                      "university", "faculty", "direction", "level"],
        "exact": ["type", "owner_id"],
    }

    def get_queryset(self):
        search_data = self.request.query_params
        queryset = ReadyTask.objects.all().select_related("owner")

        pk = self.kwargs.get("pk")
        user = getattr(self.request, "user", None)
        is_owner = user and user.is_authenticated and str(user.id) == str(pk)

        if is_owner:
            queryset = queryset.filter(owner=pk)
        else:
            queryset = queryset.filter(owner=pk, status="active")

        sort_value = search_data.get("sort") if isinstance(search_data, dict) else None
        if sort_value and sort_value in self.SORT_MAP:
            queryset = queryset.order_by(self.SORT_MAP[sort_value])
        else:
            queryset = queryset.order_by("id") 

        if isinstance(search_data, dict):
            for lookup_type, fields in self.SEARCH_FIELDS.items():
                for field in fields:
                    value = search_data.get(field)
                    if value:
                        queryset = queryset.filter(**{f"{field}__{lookup_type}": value})

        return queryset

    @catch_and_log_exceptions
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        total_count = queryset.count()

        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 10))

        paginator = Paginator(queryset, page_size)
        paginated_queryset = paginator.page(page)

        serializer = self.get_serializer(paginated_queryset, many=True)

        return Response({
            "total_count": total_count,
            "page_data": serializer.data,
            "has_next": paginated_queryset.has_next(),
            "has_previous": paginated_queryset.has_previous(),
        })


class ReadyTaskBoughtListAPIView(generics.GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ShortInfoReadyTaskSerializer

    SEARCH_FIELDS = {
        "icontains": [
            "ready_task__name",
            "ready_task__type",
            "ready_task__discipline",
            "ready_task__city",
            "ready_task__university",
            "ready_task__faculty",
            "ready_task__direction",
            "ready_task__level",
            "ready_task__tutor",
        ],
        "exact": [
            "ready_task__id",
        ],
    }

    def get_queryset(self):
        user = self.request.user
        search_data = self.request.query_params

        queryset = (
            PurchasedReadyTask.objects
            .filter(
                Q(buyer_transaction__wallet__user__id=user.id, status="paid") |
                Q(buyer_transaction__wallet__user__id=user.id, status="refunded", is_gift=True)
            )
            .select_related("ready_task")
            .order_by("-created_at")
        )

        for lookup_type, fields in self.SEARCH_FIELDS.items():
            for field in fields:
                query_key = field.split("__")[-1]
                value = search_data.get(query_key)
                if value:
                    queryset = queryset.filter(**{f"{field}__{lookup_type}": value})

        if not queryset.query.order_by:
            queryset = queryset.order_by("id")

        return queryset

    @catch_and_log_exceptions
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        total_count = queryset.count()

        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 10))

        paginator = Paginator(queryset, page_size)
        try:
            paginated_queryset = paginator.page(page)
        except EmptyPage:
            paginated_queryset = paginator.page(paginator.num_pages)

        ready_tasks = [item.ready_task for item in paginated_queryset]
        serializer = self.get_serializer(ready_tasks, many=True)

        return Response({
            "total_count": total_count,
            "page_data": serializer.data,
            "has_next": paginated_queryset.has_next(),
            "has_previous": paginated_queryset.has_previous(),
        })


class ReadyTaskDetailAPIView(generics.RetrieveAPIView):
    queryset = ReadyTask.objects.all()
    serializer_class = ReadyTaskSerializer
    permission_classes = (AllowAny,)

    @catch_and_log_exceptions
    def get(self, request, *args, **kwargs):
        task = self.get_object()

        task.increment_views()

        task_data = self.get_serializer(task).data
        user = request.user

        response_data = self._prepare_response_data(task, user, task_data)
        return Response(response_data, status=status.HTTP_200_OK)

    def _prepare_response_data(self, task, user, task_data):
        user_id = getattr(user, 'id', None)
        is_owner = user_id is not None and user_id == task.owner_id
        purchased = self._check_if_purchased(user_id, task.id)

        can_view_all_files = is_owner or purchased
        files = task.files.all()

        owner = task.owner

        response_data = {
            **self._filter_task_data(task_data),
            "owner_id": owner.id if owner else None,
            "owner_name": owner.name if owner else None,
            "owner_rating": round(owner.client.average_rating, 2) if owner and hasattr(owner, 'client') else 0.0,
            "is_purchased": purchased,
            "is_owner": is_owner,
            "views": task.views,
        }

        if files.exists():
            response_data["files"] = self._get_files_data(files, can_view_all_files)
            
        return response_data

    @staticmethod
    def _check_if_purchased(user_id, task_id):
        if user_id is None:
            return False

        return PurchasedReadyTask.objects.filter(
            Q(buyer_transaction__wallet__user__id=user_id, status='paid', ready_task_id=task_id) |
            Q(buyer_transaction__wallet__user__id=user_id, status='refunded', is_gift=True,
              ready_task_id=task_id)
        ).exists()

    @staticmethod
    def _filter_task_data(task_data):
        fields_to_remove = ["owner", "create_date", "update_date"]
        return {k: v for k, v in task_data.items() if k not in fields_to_remove}

    def _get_files_data(self, files, can_view_all_urls=False):
        s3_client = S3Client(
            access_key=AWS_ACCESS_KEY_ID,
            secret_key=AWS_SECRET_ACCESS_KEY,
            endpoint_url=AWS_PRIVATE_ENDPOINT_URL,
            bucket_name=AWS_PRIVATE_STORAGE_BUCKET_NAME
        )

        serializer = FilesSerializer(files, many=True)
        files_data = serializer.data

        result = []
        for file_data in files_data:
            result.append(self._prepare_file_info(file_data, can_view_all_urls, s3_client))

        return result

    @staticmethod
    def _prepare_file_info(file_data, can_view, s3_client):
        is_public = file_data.get("is_public", False)
        can_view = can_view or is_public

        file_info = {
            "name": file_data.get("name"),
            "url": None,
            "is_locked": not can_view,
            "is_public": is_public,
        }

        if can_view:
            file_info["url"] = s3_client.generate_temp_url([file_data])[0]
            file_info["size"] = file_data.get("size")

        return file_info


class ReadyTaskPrepareForRecreateAPIView(generics.RetrieveAPIView):
    queryset = ReadyTask.objects.all()
    serializer_class = ReadyTaskSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @catch_and_log_exceptions
    def get(self, request, *args, **kwargs):
        task = self.get_object()
        task_data = self.get_serializer(task).data

        is_owner = request.user.id == task.owner_id

        if not is_owner:
            raise ValidationError("Пользователь не владелец")

        for field in ["create_date", "number_buyers", "previous_version", "is_recreate", "owner"]:
            task_data.pop(field, None)

        files = task_data.pop('files', None)
        if files and hasattr(self, 'move_files'):
            files = self.move_files(files, request.user.id)
            task_data['files'] = files

        task_data["is_recreate"] = True

        return Response(task_data, status=status.HTTP_200_OK)

    @staticmethod
    def move_files(files, user_id):
        return_file_data = []

        s3Client = S3Client(
            access_key=AWS_ACCESS_KEY_ID,
            secret_key=AWS_SECRET_ACCESS_KEY,
            endpoint_url=AWS_PRIVATE_ENDPOINT_URL,
            bucket_name=AWS_PRIVATE_STORAGE_BUCKET_NAME
        )

        for file_data in files:
            old_path = file_data["path"]
            new_path = f"temp_storage/{user_id}/{file_data['name']}"

            is_move = s3Client.copy_between_folders(old_path=old_path, new_path=new_path)
            url = s3Client.single_generate_temp_url(file_path=new_path)
            if is_move and url:
                return_file_data.append({
                    'url': url,
                    'name': file_data['name'],
                    'size': file_data['size'],
                    'path': new_path,
                    'is_load': True,
                    'is_public': file_data['is_public']
                })

        return return_file_data


class ReadyTaskHideAPIView(generics.UpdateAPIView):
    queryset = ReadyTask.objects.all()
    lookup_field = 'id'
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @catch_and_log_exceptions
    def update(self, request, *args, **kwargs):
        task = self.get_object()

        if task.owner_id != request.user.id:
            raise ValidationError("Пользователь не владелец")

        task.status = 'unpublished'
        task.save()

        return Response(
            {"message": "Работа успешно скрыта"},
            status=status.HTTP_200_OK
        )

