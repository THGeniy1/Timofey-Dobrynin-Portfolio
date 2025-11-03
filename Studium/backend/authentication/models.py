from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from .managers import *
from users.models import Education


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=200, blank=True, null=True, default="")
    avatar = models.TextField(max_length=1000, blank=True, null=True)

    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    def get_short_name(self):
        return self.name or f"Пользователь {self.id}"

    def get_full_name(self):
        return self.name or f"Пользователь {self.id}"

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


class Client(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='client')
    gender = models.CharField(max_length=10, blank=True, null=True)
    educations = models.ManyToManyField(Education, blank=True)
    description = models.TextField(blank=True, null=True)
    free_slots = models.PositiveIntegerField(blank=True, null=True, default=5)
    reviews_count = models.PositiveIntegerField(default=0)
    average_rating = models.FloatField(default=0.0)

    inn = models.TextField(blank=True, null=True, help_text="ИНН пользователя")

    is_foreign_citizen = models.BooleanField(default=False, help_text="Пользователь является иностранным гражданином")

    has_inn = models.BooleanField(default=False, help_text="У пользователя введён ИНН (не хранится в открытом виде)")
    is_inn_locked = models.BooleanField(default=False, help_text="Запрет изменения ИНН")

    is_admin_seller_account = models.BooleanField(default=False, help_text="Это аккаунт админа для продажи")
    is_banned = models.BooleanField(default=False, help_text="Заблокирован ли пользователь")
    ban_reason = models.TextField(blank=True, null=True, help_text="Причина блокировки пользователя")

    def __str__(self):
        return self.user.email if self.user else "Без пользователя"

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"


class Staff(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.SET_NULL, null=True, related_name='staff')
    role = models.CharField(max_length=50, choices=[("moderator", "Moderator"), ("superadmin", "Super Admin")])

    def __str__(self):
        return self.user.email if self.user else "No User"

    class Meta:
        verbose_name = "Сотрудника"
        verbose_name_plural = "Сотрудники"


class AdminPasswordResetRequest(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, related_name='admin_reset_actions')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='password_reset_requests')
    token = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"Сброс для {self.client.user.email} (админ: {self.staff.user.email if self.staff else 'неизвестно'})"

    class Meta:
        verbose_name = "Сброс пароля"
        verbose_name_plural = "Запросы на сброс пароля"


class UserChangeLog(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    field_name = models.CharField(max_length=255)
    old_value = models.TextField(null=True, blank=True)
    new_value = models.TextField(null=True, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

