import json

from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework_simplejwt.authentication import JWTAuthentication

from studium_backend.decorators import catch_and_log_exceptions
from studium_backend.exceptions import AppException

from .serializers import *
from .tasks import create_order_task_with_files

from django.core.paginator import Paginator
from storage.mixins import  PublicGetMixin


class OrderTaskCreateAPIView(generics.CreateAPIView):
    serializer_class = OrderTaskCreateSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    keys_to_remove = ["education", "file_names", "file_sizes", "file_paths", "file_is_public"]

    @catch_and_log_exceptions
    def create(self, request, *args, **kwargs):
        print("==> OrderTaskCreateAPIView.create() called")
        user = request.user
        print("User:", user)

        if user.client.is_banned:
            print("User is banned!")
            return Response({'detail': 'Пользователь заблокирован'}, status=423)

        data = request.data
        print("Raw request data:", data)

        file_data = self._prepare_file_data(data)
        print("Prepared file_data:", file_data)

        education_data = self._prepare_education_data(data=data, user=user)
        print("Prepared education_data:", education_data)

        upload_data = education_data | file_data
        print("Combined upload_data (before _add_other_data):", upload_data)

        self._add_other_data(data, upload_data)
        print("Upload_data (after _add_other_data):", upload_data)

        self._validate_task_data(upload_data)
        print("Validation successful")

        return self._handle_task_creation(upload_data)

    @staticmethod
    def _get_user_education(user, data):
        print("==> _get_user_education() called")
        try:
            education_index = int(data.get("education"))
            education = user.client.educations.all()[education_index]
            print("Selected education:", education)
            return education
        except (IndexError, ValueError) as e:
            print("Error in _get_user_education:", e)
            raise ValidationError({"create_ready_task_get_user_education": "Неверно указано образование"})

    @staticmethod
    def _prepare_file_data(data):
        print("==> _prepare_file_data() called")
        file_names = data.getlist("file_names", [])
        file_sizes = data.getlist("file_sizes", [])
        file_paths = data.getlist("file_paths", [])
        file_is_public = data.getlist("file_is_public", [])
        print("File lists:", file_names, file_sizes, file_paths, file_is_public)

        if not (len(file_names) == len(file_sizes) == len(file_is_public) == len(file_paths)):
            print("File data mismatch in lengths!")
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
            except (ValueError, AttributeError) as e:
                print("Error in file loop:", e)
                continue

        print("Prepared files:", files)
        return {'files': files}

    def _prepare_education_data(self, data: dict, user):
        print("==> _prepare_education_data() called")
        is_recreate = data.get("is_recreate")
        print("is_recreate raw:", is_recreate)

        if isinstance(is_recreate, str):
            is_recreate = is_recreate.strip().lower() == 'true'
        elif isinstance(is_recreate, list) and len(is_recreate) > 0:
            is_recreate = is_recreate[0].strip().lower() == 'true'
        else:
            is_recreate = bool(is_recreate)
        print("is_recreate parsed:", is_recreate)

        if is_recreate:
            education = data.get('education')
            print("Education raw:", education)
            if isinstance(education, str):
                try:
                    education = json.loads(education)
                except json.JSONDecodeError as e:
                    print("Error decoding education JSON:", e)
                    education = None
        else:
            education = self._get_user_education(user, data)

        print("Education final:", education)

        city = education.get("city") if isinstance(education, dict) else getattr(education, "city", None)
        university = education.get("university") if isinstance(education, dict) else getattr(education, "university", None)
        faculty = education.get("faculty") if isinstance(education, dict) else getattr(education, "faculty", None)
        direction = education.get("direction") if isinstance(education, dict) else getattr(education, "direction", None)
        level = education.get("level") if isinstance(education, dict) else getattr(education, "level", None)

        print("Extracted fields:", city, university, faculty, direction, level)

        for field in ["city", "university", "faculty", "direction", "level"]:
            if not locals().get(field):
                print(f"Missing field {field}")
                raise ValidationError({"create_ready_task_prepare_main_data": f"Нет требуемого поля {field}"})

        upload_data = {
            "user": user.id,
            "city": city,
            "university": university,
            "faculty": faculty,
            "direction": direction,
            "level": level
        }
        print("Prepared upload_data:", upload_data)
        return upload_data

    @staticmethod
    def _validate_task_data(data):
        print("==> _validate_task_data() called with:", data)
        required_fields = ["name", "type", "discipline", "description", "tutor"]
        for field in required_fields:
            if not data.get(field):
                print(f"Missing required field: {field}")
                raise AppException(message='Не все обязательные поля заполнены',
                                   status_code=status.HTTP_400_BAD_REQUEST)

        if data.get('price', 0) <= 0:
            print("Invalid price:", data.get('price'))
            raise AppException(message='Цена покупки должна быть положительной',
                               status_code=status.HTTP_400_BAD_REQUEST)
        print("Validation OK")

    def _add_other_data(self, data, upload_data):
        print("==> _add_other_data() called")
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
        print("Upload data after adding other fields:", upload_data)

    def _handle_task_creation(self, upload_data):
        print("==> _handle_task_creation() called with:", upload_data)
        serializer = self.get_serializer(data=upload_data)
        if serializer.is_valid():
            print("Serializer is valid. Launching Celery task...")
            create_order_task_with_files.delay(task_data=upload_data)
            return Response({'message': 'Данные приняты, идет обработка.'}, status=status.HTTP_202_ACCEPTED)

        print("Serializer errors:", serializer.errors)
        raise AppException(message='Данные не прошли проверку', status_code=status.HTTP_400_BAD_REQUEST)


class OrderTaskListAPIView(generics.ListAPIView):
    serializer_class = ShortInfoOrderTaskSerializer
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
        print("==> OrderTaskListAPIView.get_queryset() called")
        queryset = OrderTask.objects.filter(status="active").select_related("owner")
        search_data = self.request.query_params
        print("Search params:", search_data)

        sort_value = search_data.get("sort") if isinstance(search_data, dict) else None
        print("Sort value:", sort_value)

        if sort_value in self.SORT_MAP:
            queryset = queryset.order_by(self.SORT_MAP[sort_value])
        else:
            queryset = queryset.order_by("-views")
        print("After sorting:", queryset.query)

        if isinstance(search_data, dict):
            for lookup_type, fields in self.SEARCH_FIELDS.items():
                for field in fields:
                    value = search_data.get(field)
                    if value:
                        print(f"Filtering by {field}__{lookup_type}={value}")
                        queryset = queryset.filter(**{f"{field}__{lookup_type}": value})

        print("Final queryset SQL:", queryset.query)
        return queryset

    @catch_and_log_exceptions
    def get(self, request, *args, **kwargs):
        print("==> OrderTaskListAPIView.get() called")
        queryset = self.get_queryset()
        total_count = queryset.count()
        print("Total count:", total_count)

        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 10))
        print(f"Pagination: page={page}, page_size={page_size}")

        paginator = Paginator(queryset, page_size)
        paginated_queryset = paginator.page(page)

        serializer = self.get_serializer(paginated_queryset, many=True)
        print("Serialized data count:", len(serializer.data))

        return Response({
            "total_count": total_count,
            "page_data": serializer.data,
            "has_next": paginated_queryset.has_next(),
            "has_previous": paginated_queryset.has_previous(),
        })


class OrderTaskDetailAPIView(generics.RetrieveAPIView, PublicGetMixin):
    queryset = OrderTask.objects.all()
    serializer_class = OrderTaskCreateSerializer
    permission_classes = (AllowAny,)

    @catch_and_log_exceptions
    def get(self, request, *args, **kwargs):
        print("==> OrderTaskDetailAPIView.get() called")
        task = self.get_object()
        print("Task retrieved:", task)

        task.increment_views()
        print("Views incremented")

        task_data = self.get_serializer(task).data
        user = request.user
        print("User:", user)

        response_data = self._prepare_response_data(task, user, task_data)
        print("Response data prepared:", response_data)
        return Response(response_data, status=status.HTTP_200_OK)

    def _prepare_response_data(self, task, user, task_data):
        print("==> _prepare_response_data() called")
        user_id = getattr(user, 'id', None)
        is_owner = user_id is not None and user_id == task.owner_id
        print("Is owner:", is_owner)

        files = task.files.all()
        print("Files found:", files.count())

        owner = task.owner
        print("Owner:", owner)

        response_data = {
            **self._filter_task_data(task_data),
            "owner_id": owner.id if owner else None,
            "owner_name": owner.name if owner else None,
            "owner_rating": round(owner.client.average_rating, 2) if owner and hasattr(owner, 'client') else 0.0,
            "is_owner": is_owner,
            "views": task.views,
        }

        if files.exists():
            response_data["files"] = self._get_files_data(files)

        print("Prepared response_data:", response_data)
        return response_data

    @staticmethod
    def _filter_task_data(task_data):
        print("==> _filter_task_data() called")
        fields_to_remove = ["owner", "create_date", "update_date"]
        filtered = {k: v for k, v in task_data.items() if k not in fields_to_remove}
        print("Filtered task_data:", filtered)
        return filtered

    def _get_files_data(self, files):
        print("==> _get_files_data() called")
        serializer = FilesSerializer(files, many=True)
        files_data = serializer.data
        print("Serialized files:", files_data)

        result = []
        for file_data in files_data:
            print("Handling file:", file_data)
            res = self.handle_get_file(object_key=file_data)
            print("GET FILE RESULT", res)
            result.append(res)

        print("Final files result:", result)
        return result
