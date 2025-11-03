import json
import secrets
from datetime import timedelta
from django.utils import timezone

from django.contrib import admin
from django.http import JsonResponse
from django.urls import path

from .forms import AdminPasswordResetForm
from .models import CustomUser, Client, Staff, AdminPasswordResetRequest, UserChangeLog

from django import forms
from .utils import encrypt_text


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('email', 'name')
    list_filter = ('is_staff', 'is_active', 'date_joined')
    ordering = ('-date_joined',)

    fieldsets = (
        ("Основная информация", {"fields": ("email", "name", "avatar")}),
        ("Статус", {"fields": ("is_staff", "is_active")}),
        ("Даты", {"fields": ("date_joined", "last_login"), "classes": ("collapse",)}),
    )

    readonly_fields = ('date_joined', 'last_login')


class ClientAdminForm(forms.ModelForm):
    inn_input = forms.CharField(
        required=False,
        max_length=12,
        label="Новый ИНН",
        help_text="Введите 12-значный ИНН пользователя",
        widget=forms.TextInput(attrs={'size': 15})
    )

    class Meta:
        model = Client
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['inn_input'].initial = ""

    def clean(self):
        cleaned_data = super().clean()
        inn_input = cleaned_data.get('inn_input', '').strip()
        is_foreign = cleaned_data.get('is_foreign_citizen', False)

        if is_foreign:
            cleaned_data['inn'] = ""
            cleaned_data['has_inn'] = False
        else:
            if inn_input:
                if not inn_input.isdigit() or len(inn_input) != 12:
                    self.add_error('inn_input', "ИНН должен содержать 12 цифр")
                else:
                    cleaned_data['inn'] = encrypt_text(inn_input)
                    cleaned_data['has_inn'] = True
            else:
                cleaned_data['inn'] = self.instance.inn
                cleaned_data['has_inn'] = self.instance.has_inn

        return cleaned_data


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    form = ClientAdminForm

    list_display = (
        'user', 'role', 'gender', 'is_foreign_citizen', 'has_inn',
        'is_admin_seller_account', 'is_banned', 'free_slots',
        'reviews_count', 'average_rating'
    )
    search_fields = ('user__id', 'user__email', 'gender')
    list_filter = (
        'gender', 'free_slots', 'is_foreign_citizen', 'has_inn',
        'is_admin_seller_account', 'is_banned'
    )

    fieldsets = (
        ("Основная информация", {
            "fields": (
                "user", "gender", "is_foreign_citizen",
                "current_inn", "inn_input", "has_inn",
                "is_admin_seller_account", "is_banned", "description"
            )
        }),
        ("Образование", {"fields": ("educations",)}),
        ("Слоты и статистика", {"fields": ("free_slots", "reviews_count", "average_rating")}),
    )

    readonly_fields = ('reviews_count', 'average_rating', 'has_inn', 'current_inn')

    def current_inn(self, obj):
        return obj.inn if obj.inn else "—"
    current_inn.short_description = "Текущий ИНН"

    def save_model(self, request, obj, form, change):
        old_values = {
            "inn": obj.inn,
            "is_foreign_citizen": obj.is_foreign_citizen,
            "is_banned": obj.is_banned,
            "has_inn": obj.has_inn,
            "is_admin_seller_account": obj.is_admin_seller_account
        }

        obj.has_inn = form.cleaned_data.get('has_inn', obj.has_inn)
        obj.inn = form.cleaned_data.get('inn', obj.inn)

        super().save_model(request, obj, form, change)

        if (obj.has_inn or obj.is_foreign_citizen) and not obj.is_inn_locked:
            obj.is_inn_locked = True
            obj.save(update_fields=['is_inn_locked'])
    
        new_values = {
            "inn": obj.inn,
            "is_foreign_citizen": obj.is_foreign_citizen,
            "is_banned": obj.is_banned,
            "has_inn": obj.has_inn,
            "is_admin_seller_account": obj.is_admin_seller_account
        }

        for field, old_val in old_values.items():
            new_val = new_values[field]
            if old_val != new_val:
                UserChangeLog.objects.create(
                    user=obj.user,
                    field_name=field,
                    old_value=str(old_val),
                    new_value=str(new_val)
                )

    def role(self, obj):
        return obj.user.staff.role if hasattr(obj.user, 'staff') else "Нет роли"
    role.admin_order_field = 'user__staff__role'
    role.short_description = 'Роль'


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'user_email', 'user_name')
    search_fields = ('user__email', 'user__name', 'role')
    list_filter = ('role',)
    
    fieldsets = (
        ("Основная информация", {"fields": ("user", "role")}),
    )
    
    def user_email(self, obj):
        return obj.user.email if obj.user else "Нет пользователя"
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'
    
    def user_name(self, obj):
        return obj.user.name if obj.user else "Нет имени"
    user_name.short_description = 'Имя'
    user_name.admin_order_field = 'user__name'


@admin.register(AdminPasswordResetRequest)
class AdminPasswordResetRequestAdmin(admin.ModelAdmin):
    form = AdminPasswordResetForm
    list_display = ('client_email', 'staff_email', 'is_used', 'created_at')
    list_filter = ('is_used', 'created_at')
    search_fields = ('client__user__email', 'staff__user__email')
    readonly_fields = ('created_at',)
    change_form_template = 'admin/reset_password/reset_password_form.html'
    fields = []

    def client_email(self, obj):
        return obj.client.user.email if obj.client and obj.client.user else "Нет клиента"
    client_email.short_description = 'Email клиента'
    client_email.admin_order_field = 'client__user__email'
    
    def staff_email(self, obj):
        return obj.staff.user.email if obj.staff and obj.staff.user else "Нет сотрудника"
    staff_email.short_description = 'Email сотрудника'
    staff_email.admin_order_field = 'staff__user__email'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "check-email/",
                self.admin_site.admin_view(self.check_email),
                name="check_email"
            ),
            path(
                "generate-url/",
                self.admin_site.admin_view(self.generate_url),
                name="generate_url"
            ),
        ]
        return custom_urls + urls

    def check_email(self, request):
        email = request.GET.get("email", "").strip()
        if not email:
            return JsonResponse({"error": "Email обязателен"}, status=400)

        try:
            user = CustomUser.objects.get(email=email)
            client = Client.objects.get(user=user)
            return JsonResponse({
                "exists": True,
                "client_id": client.id,
                "client_name": str(client)
            })
        except (CustomUser.DoesNotExist, Client.DoesNotExist):
            return JsonResponse({"exists": False})

    def generate_url(self, request):
        try:
            data = json.loads(request.body)
            email = data.get("email")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Некорректный JSON"}, status=400)

        if not email:
            return JsonResponse({"error": "Email обязателен"}, status=400)

        try:
            user = CustomUser.objects.get(email=email)
            client = Client.objects.get(user=user)
            staff = Staff.objects.filter(user=request.user).first()

            token = secrets.token_urlsafe(32)
            expiration = timezone.now() + timedelta(hours=24)

            AdminPasswordResetRequest.objects.create(
                staff=staff,
                client=client,
                token=token,
                is_used=False
            )

            base_url = request.build_absolute_uri('/')
            reset_url = f"{base_url}?token={token}&auth_type=recovery"

            return JsonResponse({
                "success": True,
                "reset_url": reset_url,
                "expires_at": expiration.strftime("%Y-%m-%d %H:%M:%S"),
                "client_email": user.email
            })

        except CustomUser.DoesNotExist:
            return JsonResponse({"error": "Пользователь с таким email не найден"}, status=404)
        except Client.DoesNotExist:
            return JsonResponse({"error": "Клиент не найден для данного пользователя"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    def save_model(self, request, obj, form, change):
        if not obj.staff:
            obj.staff = Staff.objects.filter(user=request.user).first()
        super().save_model(request, obj, form, change)
