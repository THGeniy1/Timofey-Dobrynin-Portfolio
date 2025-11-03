from rest_framework import serializers
from authentication.models import CustomUser, Education, UserChangeLog
from authentication.utils import encrypt_text
from payments.serializers import WalletSerializer

from ready_tasks.models import ReadyTask

from storage.object_storage import S3Client
from studium_backend.settings import AWS_PUBLIC_STORAGE_BUCKET_NAME, AWS_PUBLIC_ENDPOINT_URL, \
    AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY


class EducationSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Education
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    wallet = WalletSerializer(required=True)
    educations = EducationSerializer(many=True, source="client.educations", required=False)
    gender = serializers.CharField(source="client.gender", allow_null=True, required=False)
    free_slots = serializers.CharField(source="client.free_slots", allow_null=True, required=False)
    description = serializers.CharField(source="client.description", allow_null=True, allow_blank=True, required=False)
    reviews_count = serializers.IntegerField(source="client.reviews_count", read_only=True)
    average_rating = serializers.FloatField(source="client.average_rating", read_only=True)

    inn = serializers.CharField(source="client.inn", write_only=True, allow_null=True,
                                allow_blank=True, required=False, max_length=12)

    is_foreign_citizen = serializers.BooleanField(source="client.is_foreign_citizen", write_only=True, required=False)
    has_inn = serializers.BooleanField(source="client.has_inn", write_only=True)
    is_inn_locked = serializers.BooleanField(source="client.is_inn_locked", read_only=True)

    posted_tasks_count = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            "id", "name", "date_joined", "avatar", "wallet", "free_slots",
            "is_foreign_citizen", "has_inn", "inn", "is_inn_locked",
            "gender", "educations", "description", "reviews_count",
            "average_rating", "posted_tasks_count"
        )

    def update(self, instance, validated_data):
        old_values = self._get_old_values(instance)

        self._update_user_fields(instance, validated_data)
        self._update_client_fields(instance, validated_data.pop('client', {}))
        instance.save()
        instance.client.save()

        self._log_changes(instance, old_values)

        return instance

    @staticmethod
    def _get_old_values(instance):
        return {
            "name": instance.name,
            "avatar": instance.avatar,
            "description": instance.client.description,
            "gender": instance.client.gender,
            "is_foreign_citizen": instance.client.is_foreign_citizen,
            "inn": instance.client.inn
        }

    def _update_user_fields(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        new_avatar = validated_data.get('avatar')
        if new_avatar and instance.avatar != new_avatar:
            self.delete_old_avatar(instance.avatar)
            instance.avatar = new_avatar

    def _update_client_fields(self, instance, client_data):
        client = instance.client
        client.description = client_data.get('description', client.description)
        client.gender = client_data.get('gender', client.gender)

        if 'is_foreign_citizen' in client_data:
            client.is_foreign_citizen = client_data.get('is_foreign_citizen', client.is_foreign_citizen)

        self._update_inn(client, self.initial_data.get('inn'))

        if (client.has_inn or client.is_foreign_citizen) and not client.is_inn_locked:
            client.is_inn_locked = True

        educations_data = client_data.pop('educations', [])
        self.update_educations(instance, educations_data)

    @staticmethod
    def _update_inn(client, raw_inn):
        if client.is_foreign_citizen:
            client.inn = ""
            client.has_inn = False
        elif raw_inn is not None:
            raw_inn_str = (raw_inn or "").strip()
            if raw_inn_str == "":
                client.inn = ""
                client.has_inn = False
            else:
                if not raw_inn_str.isdigit() or len(raw_inn_str) != 12:
                    raise serializers.ValidationError({"inn": "ИНН должен содержать 12 цифр"})
                client.inn = encrypt_text(raw_inn_str)
                client.has_inn = True

    @staticmethod
    def _log_changes(instance, old_values):
        changes = []
        fields = ["name", "avatar", "description", "gender", "is_foreign_citizen", "inn"]
        for field in fields:
            old = old_values[field]
            new = getattr(instance if field in ["name", "avatar"] else instance.client, field)
            if old != new:
                changes.append((field, old, new))

        for field_name, old, new in changes:
            UserChangeLog.objects.create(
                user=instance,
                field_name=field_name,
                old_value=str(old),
                new_value=str(new)
            )

    @staticmethod
    def delete_old_avatar(object_key):
        s3Client = S3Client(
            access_key=AWS_ACCESS_KEY_ID,
            secret_key=AWS_SECRET_ACCESS_KEY,
            endpoint_url=AWS_PUBLIC_ENDPOINT_URL,
            bucket_name=AWS_PUBLIC_STORAGE_BUCKET_NAME
        )
        s3Client.delete_file(path=object_key)

    @staticmethod
    def update_educations(instance, educations_data):
        client = instance.client
        existing_educations = {edu.id: edu for edu in client.educations.all()}

        updated_ids = []

        for education_data in educations_data:
            edu_id = education_data.get("id")
            if edu_id and edu_id in existing_educations:
                education_instance = existing_educations[edu_id]

                if education_instance not in client.educations.all():
                    raise serializers.ValidationError("Образование не принадлежит текущему пользователю.")

                serializer = EducationSerializer(education_instance, data=education_data, partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                updated_ids.append(edu_id)

            else:
                serializer = EducationSerializer(data=education_data)
                serializer.is_valid(raise_exception=True)
                new_education = serializer.save()
                client.educations.add(new_education)

        for edu_id, edu_obj in existing_educations.items():
            if edu_id not in updated_ids:
                edu_obj.delete()

    @staticmethod
    def get_posted_tasks_count(obj):
        return ReadyTask.objects.filter(owner=obj, status='active').count()


class PublicUserSerializer(serializers.ModelSerializer):
    educations = EducationSerializer(many=True, source="client.educations")
    gender = serializers.CharField(source="client.gender")
    description = serializers.CharField(source="client.description")
    reviews_count = serializers.IntegerField(source="client.reviews_count")
    average_rating = serializers.FloatField(source="client.average_rating")
    posted_tasks_count = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            "id", "name", "date_joined", "avatar",
            "gender", "educations", "description",
            "reviews_count", "average_rating", "posted_tasks_count"
        )

    @staticmethod
    def get_posted_tasks_count(obj):
        return ReadyTask.objects.filter(owner=obj, status='active').count()


class ShortInfoUserSerializer(serializers.ModelSerializer):
    reviews_count = serializers.IntegerField(source='client.reviews_count')
    average_rating = serializers.FloatField(source='client.average_rating')
    description = serializers.CharField(source='client.description')

    class Meta:
        model = CustomUser
        fields = ('id', 'name', 'reviews_count', 'average_rating', 'description', 'avatar')


class FeedbackUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'name', 'email')
